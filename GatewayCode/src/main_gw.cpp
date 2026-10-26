/*
 * Multi-Channel LoRa Gateway on Raspberry Pi CM4 + 3x Ra-02 (SX1278)
 * -------------------------------------------------------------------------
 * Kiến trúc Thời gian thực (RTOS Multi-Tasking Architecture) kết hợp
 * Webserver Daemon tích hợp điều khiển tương tác qua Nginx (Port 80):
 *   - Lập trình đa luồng POSIX (std::thread / pthread)
 *   - Điều phối Real-Time Priority: SCHED_FIFO (Ưu tiên cao cho RF Tasks)
 *   - Đồng bộ bus phần cứng SPI bằng Mutex an toàn (std::recursive_mutex)
 *   - Truyền nhận gói tin bất đồng bộ qua Hàng đợi Thread-Safe (PacketQueue)
 *   - Tách biệt hoàn toàn luồng I/O Lưu trữ (Task_Logger) khỏi các luồng RF
 *   - Tích hợp HTTP REST API Server (Task_WebServer) phục vụ Web Dashboard
 *   - Giám sát Online/Offline, Cấu hình tần số OTA, Phát lệnh theo nhóm Node
 *   - Bộ lọc Control Traffic: Loại bỏ các gói PING, ACK, CFG khỏi dữ liệu TinyML
 * -------------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <pthread.h>
#include <cmath>

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <deque>
#include <atomic>
#include <chrono>
#include <string>
#include <vector>
#include <sstream>

#include <wiringPi.h>
#include <wiringPiSPI.h>

#include "config.h"
#include "sx1278_wiringpi.h"
#include "http_server.h"

// ── Cấu hình số lượng gói tin ──────────────────────────────────────────────
#define SAMPLES_PER_BURST   100       // Số gói mỗi mức payload (100 gói)

// ── Cấu trúc dữ liệu gói tin nhận được ──────────────────────────────────────
struct LoRaPacket {
    char timestamp[32];
    double frequency;
    char sourceNode;
    uint16_t packetId;
    uint8_t payloadSize;
    int rssi;
    float snr;
    int channelId; // 1, 2, hoặc 3
    bool crcError;
    uint8_t payload[256];
    uint8_t rawLen;
};

// ── Cấu trúc thông tin trạng thái từng End-Node ─────────────────────────────
struct NodeStateInfo {
    char id;                  // 'A', 'B', 'C'
    bool online;              // true nếu có gói tin trong vòng 15 giây
    std::string state;        // "WAIT" (Chờ lệnh), "TX" (Đang phát), "FINISHED" (Xong)
    double frequency;         // Tần số hiện tại của Node
    int channelId;            // Kênh 1, 2, hoặc 3
    int rssi;                 // RSSI gần nhất (dBm)
    float snr;                // SNR gần nhất (dB)
    time_t lastSeen;          // Thời điểm nhận gói tin cuối cùng
    uint32_t packetsReceived; // Số gói dữ liệu đã nhận từ Node này trong phiên
    bool cfgConfirmed;        // Đã xác nhận cấu hình tần số OTA ổn định
};

// ── Cấu trúc sự kiện hiển thị trên Web Console ──────────────────────────────
struct EventLogEntry {
    std::string timestamp;
    std::string type;         // "DATA", "DOWNLINK", "CTRL", "OTA", "SYSTEM"
    std::string message;
    char node;
    double freq;
    int rssi;
    float snr;
    int size;
    int pktId;
};

// ── Hàng đợi Thread-Safe ────────────────────────────────────────────────────
template <typename T>
class SafeQueue {
private:
    std::queue<T> m_queue;
    std::mutex m_mutex;
    std::condition_variable m_cv;

public:
    void push(const T& item) {
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            m_queue.push(item);
        }
        m_cv.notify_one();
    }

    bool pop(T& item, int timeout_ms = 100) {
        std::unique_lock<std::mutex> lock(m_mutex);
        if (!m_cv.wait_for(lock, std::chrono::milliseconds(timeout_ms), [this] { return !m_queue.empty(); })) {
            return false;
        }
        item = m_queue.front();
        m_queue.pop();
        return true;
    }

    bool empty() {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_queue.empty();
    }

    size_t size() {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_queue.size();
    }
};

// ── Biến toàn cục hệ thống ──────────────────────────────────────────────────
static std::atomic<bool> g_running(true);
static std::atomic<uint32_t> g_totalPackets(0);
static std::atomic<uint32_t> g_totalCrcErrors(0);
static std::atomic<uint32_t> g_totalControlPackets(0);
static time_t g_startTime = time(NULL);

// Quản lý phiên đo đạc (Session Name)
static std::mutex g_sessionMutex;
static std::string g_sessionName = "A_433.175";
static std::atomic<bool> g_sessionChanged(false);

// Bảng thông tin trạng thái 3 Node A, B, C
static std::mutex g_nodesMutex;
static NodeStateInfo g_nodes[3] = {
    {'A', false, "WAIT", MODULE1_FREQ, 1, -120, 0.0f, 0, 0, true},
    {'B', false, "WAIT", MODULE2_FREQ, 2, -120, 0.0f, 0, 0, true},
    {'C', false, "WAIT", MODULE3_FREQ, 3, -120, 0.0f, 0, 0, true}
};

// Thống kê gói theo 3 kênh phần cứng
static std::atomic<uint32_t> g_channelPackets[3] = {0, 0, 0};

// Nhật ký sự kiện phục vụ Web Dashboard (lưu tối đa 50 sự kiện gần nhất)
static std::mutex g_eventsMutex;
static std::deque<EventLogEntry> g_eventsLog;

// Con trỏ tới 3 module radio để phát Downlink từ API
static SX1278_WiringPi* g_radio1 = nullptr;
static SX1278_WiringPi* g_radio2 = nullptr;
static SX1278_WiringPi* g_radio3 = nullptr;

// ── Bắt tín hiệu ngắt an toàn ───────────────────────────────────────────────
void sigintHandler(int sig) {
    printf("\n\n[RTOS] Nhận tín hiệu ngắt (Signal %d). Đang thu dọn các Task và đóng file an toàn...\n", sig);
    g_running = false;
}

// ── Hàm tiện ích lấy thời gian mili-giây định dạng HH:MM:SS.mmm ──────────────
void getTimeStamp(char* buffer, size_t size) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm* tm_info = localtime(&tv.tv_sec);
    char timeStr[16];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", tm_info);
    snprintf(buffer, size, "%s.%03ld", timeStr, tv.tv_usec / 1000);
}

// ── Ghi nhận sự kiện vào bộ đệm Web Console ─────────────────────────────────
void addEventLog(const std::string& timeStr, const std::string& type, const std::string& msg,
                 char node = '?', double freq = 0.0, int rssi = 0, float snr = 0.0f, int size = 0, int pktId = -1) {
    std::lock_guard<std::mutex> lock(g_eventsMutex);
    EventLogEntry entry;
    entry.timestamp = timeStr;
    entry.type = type;
    entry.message = msg;
    entry.node = node;
    entry.freq = freq;
    entry.rssi = rssi;
    entry.snr = snr;
    entry.size = size;
    entry.pktId = pktId;

    g_eventsLog.push_back(entry);
    if (g_eventsLog.size() > 50) {
        g_eventsLog.pop_front();
    }
}

// ── Hàm tiện ích định dạng chuỗi hiển thị Payload ────────────────────────────
std::string toAsciiString(const uint8_t* data, size_t len, size_t maxLen = 40) {
    std::string s;
    size_t n = (len < maxLen) ? len : maxLen;
    for (size_t i = 0; i < n; i++) {
        char c = (char)data[i];
        if (c >= 32 && c <= 126) {
            s += c;
        } else {
            s += '.';
        }
    }
    if (len > maxLen) s += "...";
    return s;
}

// ── Thiết lập Real-Time Scheduling (SCHED_FIFO) cho Thread ──────────────────
bool setRealtimePriority(pthread_t thread, int priority) {
    struct sched_param param;
    param.sched_priority = priority;
    if (pthread_setschedparam(thread, SCHED_FIFO, &param) != 0) {
        return false;
    }
    return true;
}

// ═══════════════════════════════════════════════════════════════════════════
// HÀM PHÁT LỆNH DOWNLINK TỔNG QUÁT TỚI CÁC END-NODE
// ═══════════════════════════════════════════════════════════════════════════
void broadcastCommand(const std::string& cmd) {
    if (!g_radio1 || !g_radio2 || !g_radio3) return;

    printf("\n[DOWNLINK] >>> ĐANG GỬI LỆNH: \"%s\" TỚI CÁC END-NODE... <<<\n", cmd.c_str());
    char timeStr[32];
    getTimeStamp(timeStr, sizeof(timeStr));
    addEventLog(timeStr, "DOWNLINK", cmd);

    bool ok1 = false, ok2 = false, ok3 = false;
    for (int rep = 0; rep < 2; rep++) {
        ok1 = g_radio1->sendPacket((const uint8_t*)cmd.c_str(), cmd.length(), 250);
        ok2 = g_radio2->sendPacket((const uint8_t*)cmd.c_str(), cmd.length(), 250);
        ok3 = g_radio3->sendPacket((const uint8_t*)cmd.c_str(), cmd.length(), 250);
        usleep(25000); // 25ms giữa các đợt phát
    }
    printf("[DOWNLINK] Trạng thái phát: CH1 (%.3f MHz): %s | CH2 (%.3f MHz): %s | CH3 (%.3f MHz): %s\n\n",
           g_radio1->getFrequency(), ok1 ? "OK" : "TIMEOUT",
           g_radio2->getFrequency(), ok2 ? "OK" : "TIMEOUT",
           g_radio3->getFrequency(), ok3 ? "OK" : "TIMEOUT");
}

// ═══════════════════════════════════════════════════════════════════════════
// BỘ XỬ LÝ BẢN TIN ĐIỀU KHIỂN (CONTROL TRAFFIC FILTER & HANDLER)
// Ghi chú: Toàn bộ bản tin PING, PONG, ACK, CFG được phân tích để cập nhật
// trạng thái Node và Web UI, TUYỆT ĐỐI LOẠI BỎ khỏi file CSV/TXT dataset!
// ═══════════════════════════════════════════════════════════════════════════
void handleControlPacket(const char* payload, int len, int channelId, double freq, int rssi, float snr) {
    g_totalControlPackets.fetch_add(1);
    std::string text(payload, len);
    char timeStr[32];
    getTimeStamp(timeStr, sizeof(timeStr));

    // 1. Bản tin phản hồi Ping (CTRL:PONG:<node>:<ch>:<freq>:<state>)
    if (text.find("CTRL:PONG:") == 0 && text.length() >= 12) {
        char nodeId = text[10];
        int idx = nodeId - 'A';
        std::string stateStr = "WAIT";
        size_t lastColon = text.rfind(':');
        if (lastColon != std::string::npos && lastColon + 1 < text.length()) {
            stateStr = text.substr(lastColon + 1);
        }

        if (idx >= 0 && idx < 3) {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            g_nodes[idx].online = true;
            g_nodes[idx].lastSeen = time(NULL);
            g_nodes[idx].rssi = rssi;
            g_nodes[idx].snr = snr;
            g_nodes[idx].channelId = channelId;
            g_nodes[idx].frequency = freq;
            g_nodes[idx].state = stateStr;
        }

        addEventLog(timeStr, "CTRL", "PONG từ Node " + std::string(1, nodeId) + " (" + stateStr + ")",
                    nodeId, freq, rssi, snr);
        printf(" %-12s | %8.3f |   %c  | [CTRL PONG] RSSI:%d SNR:%.1f | Node State: %s\n",
               timeStr, freq, nodeId, rssi, snr, stateStr.c_str());
        return;
    }

    // 2. Bản tin xác nhận cấu hình tần số OTA (CTRL:ACK:CFG:<node>:<freq>)
    if (text.find("CTRL:ACK:CFG:") == 0 && text.length() >= 15) {
        char nodeId = text[13];
        int idx = nodeId - 'A';
        if (idx >= 0 && idx < 3) {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            g_nodes[idx].online = true;
            g_nodes[idx].lastSeen = time(NULL);
            g_nodes[idx].cfgConfirmed = true;
            g_nodes[idx].frequency = freq;
            g_nodes[idx].channelId = channelId;
            g_nodes[idx].rssi = rssi;
            g_nodes[idx].snr = snr;
        }

        addEventLog(timeStr, "OTA", "Xác nhận đổi tần số Node " + std::string(1, nodeId) + " -> " + text.substr(15) + " MHz OK",
                    nodeId, freq, rssi, snr);
        printf("\n[OTA SUCCESS] >>> Node [%c] đã xác nhận cấu hình tần số mới STABLE OK! <<<\n\n", nodeId);
        return;
    }

    // 3. Bản tin xác nhận bắt đầu phát (CTRL:ACK:START:<node>)
    if (text.find("CTRL:ACK:START:") == 0 && text.length() >= 16) {
        char nodeId = text[15];
        int idx = nodeId - 'A';
        if (idx >= 0 && idx < 3) {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            g_nodes[idx].online = true;
            g_nodes[idx].lastSeen = time(NULL);
            g_nodes[idx].state = "TX";
        }
        addEventLog(timeStr, "CTRL", "Node " + std::string(1, nodeId) + " xác nhận START", nodeId, freq, rssi, snr);
        return;
    }

    // 4. Bản tin xác nhận dừng / reset (CTRL:ACK:STOP:<node>)
    if (text.find("CTRL:ACK:STOP:") == 0 && text.length() >= 15) {
        char nodeId = text[14];
        int idx = nodeId - 'A';
        if (idx >= 0 && idx < 3) {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            g_nodes[idx].online = true;
            g_nodes[idx].lastSeen = time(NULL);
            g_nodes[idx].state = "WAIT";
        }
        addEventLog(timeStr, "CTRL", "Node " + std::string(1, nodeId) + " xác nhận STOP / RESET", nodeId, freq, rssi, snr);
        return;
    }

    // Các bản tin điều khiển khác
    addEventLog(timeStr, "CTRL", text, '?', freq, rssi, snr);
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK 1, 2, 3: Task_LoRa_RX (Luồng thu thập sóng vô tuyến thời gian thực)
// ═══════════════════════════════════════════════════════════════════════════
void task_lora_rx(int channelId, SX1278_WiringPi* radio, SafeQueue<LoRaPacket>* queue) {
    pthread_t thisThread = pthread_self();
    if (setRealtimePriority(thisThread, 80)) {
        printf("[RTOS] Task_RX_%d (%.3f MHz) khởi tạo thành công với SCHED_FIFO (Priority 80)\n",
               channelId, radio->getFrequency());
    } else {
        printf("[INFO] Task_RX_%d (%.3f MHz) khởi tạo dưới SCHED_OTHER (Chạy 'sudo' để bật RT Priority)\n",
               channelId, radio->getFrequency());
    }

    uint8_t rxBuffer[256];

    while (g_running.load()) {
        // Kiểm tra nhanh ngắt DIO0 trên chân GPIO phần cứng (Zero SPI overhead)
        if (radio->isPacketAvailable()) {
            int rssi = 0;
            float snr = 0.0f;

            int len = radio->readPacket(rxBuffer, sizeof(rxBuffer), rssi, snr);

            if (len >= 4) {
                // ── BƯỚC 1: BỘ LỌC BẢN TIN ĐIỀU KHIỂN (CONTROL PACKETS) ─────
                // Kiểm tra nếu là bản tin điều khiển PING, PONG, ACK, CFG, CMD
                if (memcmp(rxBuffer, "CTRL:", 5) == 0 || memcmp(rxBuffer, "ACK:", 4) == 0 || memcmp(rxBuffer, "CMD:", 4) == 0) {
                    handleControlPacket((const char*)rxBuffer, len, channelId, radio->getFrequency(), rssi, snr);
                    // TUYỆT ĐỐI KHÔNG ĐẨY VÀO HÀNG ĐỢI GHI CSV/TXT!
                    continue;
                }

                // ── BƯỚC 2: XỬ LÝ GÓI TIN DỮ LIỆU THỰC NGHIỆM (DATA PACKETS)
                LoRaPacket pkt;
                getTimeStamp(pkt.timestamp, sizeof(pkt.timestamp));
                pkt.channelId = channelId;
                pkt.frequency = radio->getFrequency();
                pkt.rssi = rssi;
                pkt.snr = snr;
                pkt.crcError = false;
                pkt.rawLen = (uint8_t)(len > 255 ? 255 : len);
                memcpy(pkt.payload, rxBuffer, pkt.rawLen);

                // Cập nhật trạng thái Node vào bảng in-memory
                char sourceNode = (char)rxBuffer[0];
                if (sourceNode >= 'A' && sourceNode <= 'C') {
                    int nIdx = sourceNode - 'A';
                    std::lock_guard<std::mutex> lock(g_nodesMutex);
                    g_nodes[nIdx].online = true;
                    g_nodes[nIdx].lastSeen = time(NULL);
                    g_nodes[nIdx].rssi = rssi;
                    g_nodes[nIdx].snr = snr;
                    g_nodes[nIdx].state = "TX";
                    g_nodes[nIdx].packetsReceived++;
                }

                // Phân tích định dạng bài báo LoRaEdgeTinyML: "<Node><PktID>*<data>"
                if (sourceNode >= 'A' && sourceNode <= 'C') {
                    pkt.sourceNode = sourceNode;
                    const char* starPos = (const char*)memchr(rxBuffer, '*', len);
                    if (starPos != nullptr) {
                        pkt.packetId = (uint16_t)atoi((const char*)&rxBuffer[1]);
                        pkt.payloadSize = (uint8_t)len;
                    } else if (len >= 4) {
                        pkt.packetId = ((uint16_t)rxBuffer[1] << 8) | rxBuffer[2];
                        pkt.payloadSize = rxBuffer[3];
                    } else {
                        pkt.packetId = 0;
                        pkt.payloadSize = (uint8_t)len;
                    }
                } else if (rxBuffer[0] == 'T' && len >= 5 && rxBuffer[1] >= 'A' && rxBuffer[1] <= 'C') {
                    pkt.sourceNode = (char)rxBuffer[1];
                    pkt.packetId = ((uint16_t)rxBuffer[2] << 8) | rxBuffer[3];
                    pkt.payloadSize = rxBuffer[4];
                } else {
                    continue;
                }

                // Thống kê kênh
                if (channelId >= 1 && channelId <= 3) {
                    g_channelPackets[channelId - 1].fetch_add(1);
                }

                // Ghi vào bộ đệm Web Console
                addEventLog(pkt.timestamp, "DATA", "Nhận gói #" + std::to_string(pkt.packetId),
                            pkt.sourceNode, pkt.frequency, pkt.rssi, pkt.snr, pkt.payloadSize, pkt.packetId);

                // Đẩy vào hàng đợi để Task_Logger ghi CSV/TXT (Non-blocking)
                queue->push(pkt);
            } else if (len == -1) {
                // Lỗi CRC
                g_totalCrcErrors.fetch_add(1);
                LoRaPacket pkt;
                getTimeStamp(pkt.timestamp, sizeof(pkt.timestamp));
                pkt.channelId = channelId;
                pkt.frequency = radio->getFrequency();
                pkt.sourceNode = '?';
                pkt.packetId = 0;
                pkt.payloadSize = 0;
                pkt.rssi = rssi;
                pkt.snr = snr;
                pkt.crcError = true;
                pkt.rawLen = 0;
                addEventLog(pkt.timestamp, "SYSTEM", "CRC ERROR!", '?', pkt.frequency);
                queue->push(pkt);
            }
        }

        usleep(1000); // 1ms
    }

    printf("[RTOS] Task_RX_%d kết thúc an toàn.\n", channelId);
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK 4: Task_Logger (Luồng chuyên trách ghi File CSV & TXT độc lập)
// ═══════════════════════════════════════════════════════════════════════════
void task_logger(SafeQueue<LoRaPacket>* queue, std::string initialCsvPath, std::string initialTxtPath) {
    std::string csvFilePath = initialCsvPath;
    std::string txtFilePath = initialTxtPath;

    FILE* csvFile = fopen(csvFilePath.c_str(), "w");
    if (!csvFile) {
        fprintf(stderr, "[FATAL] Task_Logger không thể mở file CSV: %s\n", csvFilePath.c_str());
    } else {
        fprintf(csvFile, "time_slot,source,packet_ID,size_of_message,RSSI,SNR,frequency\n");
        fflush(csvFile);
    }

    FILE* txtFile = fopen(txtFilePath.c_str(), "w");
    if (!txtFile) {
        fprintf(stderr, "[FATAL] Task_Logger không thể mở file TXT log: %s\n", txtFilePath.c_str());
    }

    printf("[RTOS] Task_Logger đã kích hoạt.\n");
    printf("       CSV : %s\n", csvFilePath.c_str());
    printf("       TXT : %s\n\n", txtFilePath.c_str());
    printf(" Timestamp    | Ch (MHz) | Node | Pkt ID | Size | RSSI (dBm) | SNR (dB)\n");
    printf("--------------+----------+------+--------+------+------------+---------\n");

    uint32_t sessionPackets = 0;
    uint32_t channelCounts[3] = {0, 0, 0};
    uint32_t nodeCounts[3] = {0, 0, 0};

    while (g_running.load() || !queue->empty()) {
        // Kiểm tra nếu người dùng đổi tên phiên đo đạc từ Web Dashboard
        if (g_sessionChanged.load()) {
            g_sessionChanged.store(false);

            if (csvFile) { fflush(csvFile); fclose(csvFile); }
            if (txtFile) { fflush(txtFile); fclose(txtFile); }

            std::string currentSession;
            {
                std::lock_guard<std::mutex> lock(g_sessionMutex);
                currentSession = g_sessionName;
            }

            csvFilePath = "csv/" + currentSession + ".csv";
            txtFilePath = "logs/" + currentSession + ".txt";

            csvFile = fopen(csvFilePath.c_str(), "w");
            if (csvFile) {
                fprintf(csvFile, "time_slot,source,packet_ID,size_of_message,RSSI,SNR,frequency\n");
                fflush(csvFile);
            }
            txtFile = fopen(txtFilePath.c_str(), "w");

            sessionPackets = 0;
            g_totalPackets.store(0);
            memset(channelCounts, 0, sizeof(channelCounts));
            memset(nodeCounts, 0, sizeof(nodeCounts));

            printf("\n=============================================================================\n");
            printf("[SESSION] >>> ĐÃ ĐỔI PHIÊN ĐO ĐẠC MỚI: \"%s\" <<<\n", currentSession.c_str());
            printf("          CSV : %s\n", csvFilePath.c_str());
            printf("          TXT : %s\n", txtFilePath.c_str());
            printf("=============================================================================\n\n");
        }

        LoRaPacket pkt;
        if (queue->pop(pkt, 100)) {
            if (pkt.crcError) {
                printf(" %-12s | %8.3f |   ?  | ------ | ---- | ---------- | CRC ERROR!\n",
                       pkt.timestamp, pkt.frequency);
                continue;
            }

            sessionPackets++;
            g_totalPackets.fetch_add(1);

            if (pkt.channelId >= 1 && pkt.channelId <= 3) {
                channelCounts[pkt.channelId - 1]++;
            }
            if (pkt.sourceNode >= 'A' && pkt.sourceNode <= 'C') {
                nodeCounts[pkt.sourceNode - 'A']++;
            }

            // 1. Hiển thị thông số ra Terminal Console
            printf(" %-12s | %8.3f |   %c  | %6u | %4u | %10d | %7.1f\n",
                   pkt.timestamp, pkt.frequency, pkt.sourceNode,
                   pkt.packetId, pkt.payloadSize, pkt.rssi, pkt.snr);

            std::string payloadStr((const char*)pkt.payload, pkt.rawLen);
            std::string previewStr = toAsciiString(pkt.payload, pkt.rawLen, 40);
            printf("   └─ [Payload %uB] \"%s\"\n", pkt.rawLen, previewStr.c_str());

            // 2. Ghi trực tiếp vào file CSV
            if (csvFile) {
                fprintf(csvFile, "%s,%c,%u,%u,%d,%.1f,%.3f\n",
                        pkt.timestamp, pkt.sourceNode, pkt.packetId,
                        pkt.payloadSize, pkt.rssi, pkt.snr, pkt.frequency);
                fflush(csvFile);
            }

            // 3. Ghi vào file TXT log chuẩn bài báo LoRaEdgeTinyML:
            // "HH:MM:SS.mmm -> <Payload> size_of_message <Size> RSSI <RSSI> SNR <SNR> Frequency <Freq>"
            if (txtFile) {
                int snrInt = (int)std::round(pkt.snr);
                fprintf(txtFile, "%s -> %s size_of_message %u RSSI %d SNR %d Frequency %.3f\n",
                        pkt.timestamp, payloadStr.c_str(), pkt.payloadSize, pkt.rssi, snrInt, pkt.frequency);
                fflush(txtFile);
            }

            // Thống kê mỗi 100 gói
            if (sessionPackets % SAMPLES_PER_BURST == 0) {
                printf("--------------+----------+------+--------+------+------------+---------\n");
                printf(" [STATS %d PKTS] Ghi nhận:%u | CH1:%u CH2:%u CH3:%u | A:%u B:%u C:%u | CRC:%u\n",
                       SAMPLES_PER_BURST, sessionPackets, channelCounts[0], channelCounts[1], channelCounts[2],
                       nodeCounts[0], nodeCounts[1], nodeCounts[2], g_totalCrcErrors.load());
                printf("--------------+----------+------+--------+------+------------+---------\n");
            }
        }
    }

    if (csvFile) fclose(csvFile);
    if (txtFile) fclose(txtFile);

    printf("=============================================================================\n");
    printf("[RTOS] Đã đóng các file log an toàn: %s | %s\n", csvFilePath.c_str(), txtFilePath.c_str());
    printf("[THỐNG KÊ KẾT THÚC] Tổng gói dữ liệu ghi nhận: %u\n", sessionPackets);
    printf("=============================================================================\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK 5: Task_Node_Monitor (Luồng kiểm tra thời gian thực trạng thái Online/Offline)
// ═══════════════════════════════════════════════════════════════════════════
void task_node_monitor() {
    while (g_running.load()) {
        time_t now = time(NULL);
        {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            for (int i = 0; i < 3; i++) {
                if (g_nodes[i].lastSeen > 0 && (now - g_nodes[i].lastSeen > 15)) {
                    g_nodes[i].online = false;
                }
            }
        }

        // Định kỳ mỗi 10 giây nếu hệ thống chưa nhận gói dữ liệu, tự động gửi PING
        // để cập nhật trạng thái Online/Offline phục vụ Web UI
        static time_t lastPing = 0;
        if (now - lastPing >= 10 && g_totalPackets.load() == 0) {
            lastPing = now;
            broadcastCommand("CMD:PING:ALL");
        }

        sleep(2);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// TẠO PHẢN HỒI JSON CHO REST API: GET /api/status
// ═══════════════════════════════════════════════════════════════════════════
std::string buildStatusJson() {
    std::stringstream ss;
    time_t uptime = time(NULL) - g_startTime;

    std::string session;
    {
        std::lock_guard<std::mutex> lock(g_sessionMutex);
        session = g_sessionName;
    }

    ss << "{\n";
    // Gateway info
    ss << "  \"gateway\": {\n";
    ss << "    \"status\": \"ONLINE\",\n";
    ss << "    \"uptime_sec\": " << uptime << ",\n";
    ss << "    \"session_name\": \"" << session << "\",\n";
    ss << "    \"total_packets\": " << g_totalPackets.load() << ",\n";
    ss << "    \"total_crc_errors\": " << g_totalCrcErrors.load() << ",\n";
    ss << "    \"control_packets\": " << g_totalControlPackets.load() << ",\n";
    ss << "    \"channels\": [\n";
    ss << "      {\"id\": 1, \"freq\": " << MODULE1_FREQ << ", \"packets\": " << g_channelPackets[0].load() << "},\n";
    ss << "      {\"id\": 2, \"freq\": " << MODULE2_FREQ << ", \"packets\": " << g_channelPackets[1].load() << "},\n";
    ss << "      {\"id\": 3, \"freq\": " << MODULE3_FREQ << ", \"packets\": " << g_channelPackets[2].load() << "}\n";
    ss << "    ]\n";
    ss << "  },\n";

    // Nodes info
    ss << "  \"nodes\": [\n";
    {
        std::lock_guard<std::mutex> lock(g_nodesMutex);
        time_t now = time(NULL);
        for (int i = 0; i < 3; i++) {
            long lastSeenSec = (g_nodes[i].lastSeen > 0) ? (long)(now - g_nodes[i].lastSeen) : -1;
            ss << "    {\n";
            ss << "      \"id\": \"" << g_nodes[i].id << "\",\n";
            ss << "      \"online\": " << (g_nodes[i].online ? "true" : "false") << ",\n";
            ss << "      \"state\": \"" << g_nodes[i].state << "\",\n";
            ss << "      \"frequency\": " << g_nodes[i].frequency << ",\n";
            ss << "      \"channel_id\": " << g_nodes[i].channelId << ",\n";
            ss << "      \"rssi\": " << g_nodes[i].rssi << ",\n";
            ss << "      \"snr\": " << g_nodes[i].snr << ",\n";
            ss << "      \"last_seen_sec\": " << lastSeenSec << ",\n";
            ss << "      \"packets\": " << g_nodes[i].packetsReceived << ",\n";
            ss << "      \"cfg_confirmed\": " << (g_nodes[i].cfgConfirmed ? "true" : "false") << "\n";
            ss << "    }" << (i < 2 ? "," : "") << "\n";
        }
    }
    ss << "  ],\n";

    // Recent events log
    ss << "  \"recent_events\": [\n";
    {
        std::lock_guard<std::mutex> lock(g_eventsMutex);
        for (size_t i = 0; i < g_eventsLog.size(); i++) {
            const auto& ev = g_eventsLog[i];
            ss << "    {\n";
            ss << "      \"time\": \"" << ev.timestamp << "\",\n";
            ss << "      \"type\": \"" << ev.type << "\",\n";
            ss << "      \"msg\": \"" << ev.message << "\",\n";
            ss << "      \"node\": \"" << std::string(1, ev.node) << "\",\n";
            ss << "      \"freq\": " << ev.freq << ",\n";
            ss << "      \"rssi\": " << ev.rssi << ",\n";
            ss << "      \"snr\": " << ev.snr << ",\n";
            ss << "      \"size\": " << ev.size << ",\n";
            ss << "      \"pkt_id\": " << ev.pktId << "\n";
            ss << "    }" << (i + 1 < g_eventsLog.size() ? "," : "") << "\n";
        }
    }
    ss << "  ]\n";
    ss << "}\n";

    return ss.str();
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK BÀN PHÍM CỤC BỘ (CONSOLE CONTROLLER - DỰ PHÒNG KHI KHÔNG CÓ WEB)
// ═══════════════════════════════════════════════════════════════════════════
void task_console_controller() {
    usleep(1500000);
    printf("=============================================================================\n");
    printf(" [HỆ THỐNG ĐIỀU KHIỂN GATEWAY - HỖ TRỢ ĐỒNG THỜI BÀN PHÍM & WEB]\n");
    printf("   • Web Dashboard : http://<IP_CM4>/ (Port 80 qua Nginx) hoặc :8080\n");
    printf("   • Nhấn [ENTER]  : Phát kích hoạt TẤT CẢ các Node (START:ALL)\n");
    printf("   • Gõ 'start A'  : Phát kích hoạt riêng Node A\n");
    printf("   • Gõ 'stop'     : Dừng / Reset toàn bộ các Node về chế độ chờ\n");
    printf("   • Gõ 'ping'     : Kiểm tra trạng thái Online các Node\n");
    printf("   • Gõ 'q'/'exit' : Dừng Gateway an toàn\n");
    printf("=============================================================================\n\n");

    std::string line;
    while (g_running.load()) {
        if (!std::getline(std::cin, line)) break;

        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();

        if (line == "q" || line == "exit") {
            printf("[INFO] Người dùng yêu cầu dừng Gateway...\n");
            g_running.store(false);
            break;
        }

        if (line.empty() || line == "start" || line == "START") {
            broadcastCommand("CMD:START:ALL");
        } else if (line == "stop" || line == "STOP" || line == "reset") {
            broadcastCommand("CMD:STOP:ALL");
        } else if (line == "ping" || line == "PING") {
            broadcastCommand("CMD:PING:ALL");
        } else if (line == "start A" || line == "A") {
            broadcastCommand("CMD:START:A");
        } else if (line == "start B" || line == "B") {
            broadcastCommand("CMD:START:B");
        } else if (line == "start C" || line == "C") {
            broadcastCommand("CMD:START:C");
        } else {
            broadcastCommand(line);
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN THREAD
// ═══════════════════════════════════════════════════════════════════════════
int main(int argc, char* argv[]) {
    signal(SIGINT, sigintHandler);
    signal(SIGTERM, sigintHandler);

    printf("=========================================================\n");
    printf("   LoRa Multi-Channel Gateway (Raspberry Pi CM4 + 3x Ra-02)\n");
    printf("   Hệ điều hành: Webserver Nginx (Port 80) + POSIX RTOS\n");
    printf("   Kênh: %.3f MHz | %.3f MHz | %.3f MHz\n", MODULE1_FREQ, MODULE2_FREQ, MODULE3_FREQ);
    printf("=========================================================\n\n");

    // 1. Khởi tạo WiringPi & bus SPI0
    if (wiringPiSetup() < 0) {
        fprintf(stderr, "[FATAL] Không thể khởi tạo WiringPi!\n");
        return 1;
    }

    if (wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED) < 0) {
        fprintf(stderr, "[FATAL] Không thể mở kết nối SPI0 (/dev/spidev0.0)!\n");
        return 1;
    }

    SX1278_WiringPi::configureSpiNoCs();

    // 2. Kéo toàn bộ 3 chân CS lên mức HIGH trước để giải phóng bus SPI
    pinMode(MODULE1_CS_PIN, OUTPUT); digitalWrite(MODULE1_CS_PIN, HIGH);
    pinMode(MODULE2_CS_PIN, OUTPUT); digitalWrite(MODULE2_CS_PIN, HIGH);
    pinMode(MODULE3_CS_PIN, OUTPUT); digitalWrite(MODULE3_CS_PIN, HIGH);

    // 3. Khởi tạo 3 đối tượng driver SX1278
    SX1278_WiringPi radio1(MODULE1_CS_PIN, MODULE1_RST_PIN, MODULE1_DIO0_PIN, MODULE1_FREQ);
    SX1278_WiringPi radio2(MODULE2_CS_PIN, MODULE2_RST_PIN, MODULE2_DIO0_PIN, MODULE2_FREQ);
    SX1278_WiringPi radio3(MODULE3_CS_PIN, MODULE3_RST_PIN, MODULE3_DIO0_PIN, MODULE3_FREQ);

    printf("[INIT] Đang khởi động Module 1 (%.3f MHz)... ", MODULE1_FREQ);
    radio1.begin(); printf("OK\n");

    printf("[INIT] Đang khởi động Module 2 (%.3f MHz)... ", MODULE2_FREQ);
    radio2.begin(); printf("OK\n");

    printf("[INIT] Đang khởi động Module 3 (%.3f MHz)... ", MODULE3_FREQ);
    radio3.begin(); printf("OK\n\n");

    g_radio1 = &radio1;
    g_radio2 = &radio2;
    g_radio3 = &radio3;

    // 4. Quản lý thư mục và tên phiên đo đạc ban đầu
    mkdir("csv", 0777);
    mkdir("logs", 0777);

    if (argc > 1) {
        g_sessionName = argv[1];
    } else {
        time_t rawtime;
        time(&rawtime);
        struct tm* timeinfo = localtime(&rawtime);
        char buf[64];
        strftime(buf, sizeof(buf), "gw_%Y%m%d_%H%M%S", timeinfo);
        g_sessionName = buf;
    }

    std::string csvPath = "csv/" + g_sessionName + ".csv";
    std::string txtPath = "logs/" + g_sessionName + ".txt";

    // 5. Khởi tạo Hàng đợi và kích hoạt các Task thời gian thực
    SafeQueue<LoRaPacket> packetQueue;

    printf("[RTOS] Đang kích hoạt các Task thời gian thực...\n");
    std::thread tLogger(task_logger, &packetQueue, csvPath, txtPath);
    std::thread tRx1(task_lora_rx, 1, &radio1, &packetQueue);
    std::thread tRx2(task_lora_rx, 2, &radio2, &packetQueue);
    std::thread tRx3(task_lora_rx, 3, &radio3, &packetQueue);
    std::thread tMonitor(task_node_monitor);

    // 6. Khởi động Webserver Daemon tích hợp trên cổng 8080
    HttpServer webServer(8080);

    // Đăng ký Handler cho REST API
    webServer.setStatusHandler([]() {
        return buildStatusJson();
    });

    webServer.setSessionHandler([](const std::string& newName, std::string& msg) {
        if (newName.empty()) {
            msg = "Tên phiên đo không được để trống";
            return false;
        }
        {
            std::lock_guard<std::mutex> lock(g_sessionMutex);
            g_sessionName = newName;
        }
        g_sessionChanged.store(true);
        char timeStr[32];
        getTimeStamp(timeStr, sizeof(timeStr));
        addEventLog(timeStr, "SYSTEM", "Đổi phiên đo thành: " + newName);
        msg = "Đã cập nhật phiên đo thành công: " + newName;
        return true;
    });

    webServer.setTriggerHandler([](const std::string& target, const std::string& action, std::string& msg) {
        std::string cmd;
        if (action == "STOP" || action == "stop" || action == "RESET" || action == "reset") {
            cmd = "CMD:STOP:" + target;
            broadcastCommand(cmd);
            msg = "Đã gửi lệnh DỪNG / RESET tới Node: " + target;
        } else {
            cmd = "CMD:START:" + target;
            broadcastCommand(cmd);
            msg = "Đã gửi lệnh PHÁT DỮ LIỆU (START) tới Node: " + target;
        }
        return true;
    });

    webServer.setConfigHandler([](char node, double freq, std::string& msg) {
        int idx = node - 'A';
        if (idx >= 0 && idx < 3) {
            std::lock_guard<std::mutex> lock(g_nodesMutex);
            g_nodes[idx].cfgConfirmed = false;
            g_nodes[idx].pendingFreq = freq;
        }

        // Tạo lệnh cấu hình OTA: CMD:CFG:<node>:<freq>
        char cmdBuf[64];
        snprintf(cmdBuf, sizeof(cmdBuf), "CMD:CFG:%c:%.3f", node, freq);
        broadcastCommand(cmdBuf);

        msg = "Đang gửi lệnh cấu hình tần số " + std::to_string(freq) + " MHz tới Node " + std::string(1, node) + ". Chờ xác nhận...";
        return true;
    });

    webServer.setPingHandler([](const std::string& target, std::string& msg) {
        std::string cmd = "CMD:PING:" + target;
        broadcastCommand(cmd);
        msg = "Đã gửi yêu cầu Ping tới Node: " + target;
        return true;
    });

    webServer.start();

    // 7. Kích hoạt Task điều khiển Console chạy ngầm
    std::thread tCmd(task_console_controller);
    tCmd.detach();

    printf("\n[RTOS] Toàn bộ hệ thống Gateway & Web Server đã sẵn sàng!\n");
    printf("[WEB]  Truy cập giao diện quản trị tại: http://<IP_CM4>/ (Port 80)\n\n");

    // Gửi 1 bản tin Ping ban đầu để nhận diện các Node đang mở sẵn
    usleep(500000);
    broadcastCommand("CMD:PING:ALL");

    // 8. Chờ kết thúc
    tRx1.join();
    tRx2.join();
    tRx3.join();
    tMonitor.join();
    tLogger.join();
    webServer.stop();

    printf("\n[SUCCESS] Gateway đã tắt an toàn. Tạm biệt!\n");
    return 0;
}
