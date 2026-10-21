/*
 * Multi-Channel LoRa Gateway on Raspberry Pi CM4 + 3x Ra-02 (SX1278)
 * -------------------------------------------------------------------------
 * Kiến trúc Thời gian thực (RTOS Multi-Tasking Architecture):
 *   - Lập trình đa luồng POSIX (std::thread / pthread)
 *   - Điều phối Real-Time Priority: SCHED_FIFO (Ưu tiên cao cho RF Tasks)
 *   - Đồng bộ bus phần cứng SPI bằng Mutex an toàn (std::recursive_mutex)
 *   - Truyền nhận gói tin bất đồng bộ qua Hàng đợi Thread-Safe (PacketQueue)
 *   - Tách biệt hoàn toàn luồng I/O Lưu trữ (Task_Logger) khỏi các luồng RF
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
#include <pthread.h>

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <atomic>
#include <chrono>
#include <string>

#include <wiringPi.h>
#include <wiringPiSPI.h>

#include "config.h"
#include "sx1278_wiringpi.h"

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
};

// ── Hàng đợi Thread-Safe (Thread-Safe Queue tương tự FreeRTOS Queue) ────────
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

// ── Biến điều khiển dừng chương trình an toàn ──────────────────────────────
static std::atomic<bool> g_running(true);

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
// TASK 1, 2, 3: Task_LoRa_RX (Luồng thu thập sóng vô tuyến thời gian thực)
// Chạy độc lập cho mỗi Module LoRa với Real-Time Priority cao (SCHED_FIFO)
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

            // Đọc gói tin có bảo vệ Mutex bus SPI bên trong driver
            int len = radio->readPacket(rxBuffer, sizeof(rxBuffer), rssi, snr);

            if (len >= 4) {
                char node = (char)rxBuffer[0];
                // Chỉ nhận các gói hợp lệ từ 3 Node thử nghiệm ('A', 'B', 'C')
                if (node < 'A' || node > 'C') {
                    continue;
                }

                LoRaPacket pkt;
                getTimeStamp(pkt.timestamp, sizeof(pkt.timestamp));
                pkt.channelId = channelId;
                pkt.frequency = radio->getFrequency();
                pkt.sourceNode = node;
                pkt.packetId = ((uint16_t)rxBuffer[1] << 8) | rxBuffer[2];
                pkt.payloadSize = rxBuffer[3];
                pkt.rssi = rssi;
                pkt.snr = snr;
                pkt.crcError = false;

                // Đẩy vào hàng đợi để Task_Logger xử lý (Non-blocking I/O)
                queue->push(pkt);
            } else if (len == -1) {
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
                queue->push(pkt);
            }
        }

        // Tạm nghỉ 1ms nhường chu kỳ CPU cho các luồng khác
        usleep(1000);
    }

    printf("[RTOS] Task_RX_%d kết thúc an toàn.\n", channelId);
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK 4: Task_Logger (Luồng xử lý I/O, Lưu trữ CSV & Hiển thị Console)
// Chạy ở Priority bình thường, hoàn toàn không gây tắc nghẽn luồng RF
// ═══════════════════════════════════════════════════════════════════════════
void task_logger(SafeQueue<LoRaPacket>* queue, const std::string& logFileName) {
    FILE* logFile = fopen(logFileName.c_str(), "w");
    if (!logFile) {
        fprintf(stderr, "[FATAL] Task_Logger không thể mở file log: %s\n", logFileName.c_str());
        return;
    }

    // Ghi Header CSV chuẩn hóa cho Pipeline TinyML
    fprintf(logFile, "time_slot,source,packet_ID,size_of_message,RSSI,SNR,frequency\n");
    fflush(logFile);

    printf("[RTOS] Task_Logger đã kích hoạt. Đang ghi dữ liệu vào: %s\n\n", logFileName.c_str());
    printf(" Timestamp    | Ch (MHz) | Node | Pkt ID | Size | RSSI (dBm) | SNR (dB)\n");
    printf("--------------+----------+------+--------+------+------------+---------\n");

    uint32_t totalPackets = 0;
    uint32_t totalCrcErrors = 0;
    uint32_t channelCounts[3] = {0, 0, 0};
    uint32_t nodeCounts[3] = {0, 0, 0}; // Node A, B, C

    while (g_running.load() || !queue->empty()) {
        LoRaPacket pkt;
        // Chờ gói tin từ hàng đợi với timeout 100ms
        if (queue->pop(pkt, 100)) {
            if (pkt.crcError) {
                totalCrcErrors++;
                printf(" %-12s | %8.3f |   ?  | ------ | ---- | ---------- | CRC ERROR!\n",
                       pkt.timestamp, pkt.frequency);
                continue;
            }

            totalPackets++;
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

            // 2. Ghi trực tiếp vào file CSV
            fprintf(logFile, "%s,%c,%u,%u,%d,%.1f,%.3f\n",
                    pkt.timestamp, pkt.sourceNode, pkt.packetId,
                    pkt.payloadSize, pkt.rssi, pkt.snr, pkt.frequency);
            fflush(logFile);

            // Thống kê nhanh mỗi 25 gói
            if (totalPackets % 25 == 0) {
                printf("--------------+----------+------+--------+------+------------+---------\n");
                printf(" [STATS] Ghi nhận:%u | CH1:%u CH2:%u CH3:%u | A:%u B:%u C:%u | CRC:%u\n",
                       totalPackets, channelCounts[0], channelCounts[1], channelCounts[2],
                       nodeCounts[0], nodeCounts[1], nodeCounts[2], totalCrcErrors);
                printf("--------------+----------+------+--------+------+------------+---------\n");
            }
        }
    }

    fclose(logFile);
    printf("=============================================================================\n");
    printf("[RTOS] Đã đóng file CSV an toàn: %s\n", logFileName.c_str());
    printf("[THỐNG KÊ KẾT THÚC]\n");
    printf("  - Tổng gói hợp lệ ghi nhận : %u\n", totalPackets);
    printf("  - Tổng gói lỗi CRC         : %u\n", totalCrcErrors);
    printf("  - Phân bổ theo Kênh        : CH1: %u | CH2: %u | CH3: %u\n",
           channelCounts[0], channelCounts[1], channelCounts[2]);
    printf("  - Phân bổ theo Node        : Node A: %u | Node B: %u | Node C: %u\n",
           nodeCounts[0], nodeCounts[1], nodeCounts[2]);
    printf("=============================================================================\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN THREAD (Hàm khởi tạo hệ thống & Điều phối các Task RTOS)
// ═══════════════════════════════════════════════════════════════════════════
int main(int argc, char* argv[]) {
    // Đăng ký bắt tín hiệu Ctrl+C để thoát an toàn
    signal(SIGINT, sigintHandler);
    signal(SIGTERM, sigintHandler);

    printf("=========================================================\n");
    printf("   LoRa Multi-Channel Gateway (Raspberry Pi CM4 + 3x Ra-02)\n");
    printf("   Kiến trúc Đa nhiệm Thời gian thực (RTOS Multi-Tasking)\n");
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

    // Tắt điều khiển CS phần cứng của kernel (chống xung đột bus SPI giữa 3 module)
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
    radio1.begin();
    printf("OK\n");

    printf("[INIT] Đang khởi động Module 2 (%.3f MHz)... ", MODULE2_FREQ);
    radio2.begin();
    printf("OK\n");

    printf("[INIT] Đang khởi động Module 3 (%.3f MHz)... ", MODULE3_FREQ);
    radio3.begin();
    printf("OK\n\n");

    // 4. Tạo tên file log theo ngày giờ
    time_t rawtime;
    time(&rawtime);
    struct tm* timeinfo = localtime(&rawtime);
    char logFileName[64];
    strftime(logFileName, sizeof(logFileName), "gateway_log_%Y%m%d_%H%M%S.csv", timeinfo);

    // 5. Khởi tạo hàng đợi và kích hoạt các Task thời gian thực
    SafeQueue<LoRaPacket> packetQueue;

    printf("[RTOS] Đang kích hoạt 4 Task thời gian thực...\n");
    std::thread tLogger(task_logger, &packetQueue, std::string(logFileName));
    std::thread tRx1(task_lora_rx, 1, &radio1, &packetQueue);
    std::thread tRx2(task_lora_rx, 2, &radio2, &packetQueue);
    std::thread tRx3(task_lora_rx, 3, &radio3, &packetQueue);

    printf("[RTOS] Toàn bộ hệ thống Gateway đã sẵn sàng hoạt động!\n\n");

    // 6. Chờ cho tới khi các luồng kết thúc (khi người dùng bấm Ctrl+C)
    tRx1.join();
    tRx2.join();
    tRx3.join();
    tLogger.join();

    printf("\n[SUCCESS] Gateway đã tắt an toàn. Tạm biệt!\n");
    return 0;
}
