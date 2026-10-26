/*
 * LoRa Communication Test - Raspberry Pi (3-Channel RX Only)
 * -------------------------------------------------------------------------
 * Mục đích: Test truyền thông ESP32 → Raspberry Pi qua LoRa
 *           Lắng nghe đồng thời 3 kênh, chỉ nhận, không gửi ACK
 *
 * Kiến trúc:
 *   - 3 luồng Task_RX: mỗi luồng lắng nghe 1 module Ra-02
 *   - 1 luồng Task_Logger: in log và thống kê
 *
 * Biên dịch & chạy:
 *   cd GatewayCode && make test
 *   sudo ./test_comm
 *
 * Cấu trúc gói tin nhận (từ ESP32):
 *   [Byte 0]   : 'T' (Test marker)
 *   [Byte 1]   : NODE_ID ('A', 'B', 'C')
 *   [Byte 2..3]: Packet ID (16-bit, big-endian)
 *   [Byte 4]   : Payload size
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

// ── Cấu hình số lượng gói test ─────────────────────────────────────────────
#define TARGET_TEST_PACKETS 100       // Mục tiêu test: 100 gói (trước đây là 50)

// ── Cấu trúc gói tin nhận được ──────────────────────────────────────────────
struct TestPacket {
    char     timestamp[32];
    int      channelId;     // 1, 2, 3
    double   frequency;
    char     nodeId;        // 'A', 'B', 'C' hoặc '?' nếu CRC error
    uint16_t packetId;
    uint8_t  payloadSize;
    int      rssi;
    float    snr;
    bool     crcError;
    uint8_t  payload[256];
    uint8_t  rawLen;
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
        { std::lock_guard<std::mutex> lock(m_mutex); m_queue.push(item); }
        m_cv.notify_one();
    }
    bool pop(T& item, int timeout_ms = 100) {
        std::unique_lock<std::mutex> lock(m_mutex);
        if (!m_cv.wait_for(lock, std::chrono::milliseconds(timeout_ms),
                           [this]{ return !m_queue.empty(); }))
            return false;
        item = m_queue.front(); m_queue.pop();
        return true;
    }
    bool empty() { std::lock_guard<std::mutex> lock(m_mutex); return m_queue.empty(); }
};

// ── Điều khiển dừng ─────────────────────────────────────────────────────────
static std::atomic<bool> g_running(true);

void sigintHandler(int sig) {
    printf("\n\n[CTRL+C] Đang dừng (Signal %d)...\n", sig);
    g_running = false;
}

// ── Timestamp HH:MM:SS.mmm ─────────────────────────────────────────────────
void getTimeStamp(char* buffer, size_t size) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm* tm_info = localtime(&tv.tv_sec);
    char timeStr[16];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", tm_info);
    snprintf(buffer, size, "%s.%03ld", timeStr, tv.tv_usec / 1000);
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

std::string toHexString(const uint8_t* data, size_t len, size_t maxLen = 16) {
    char buf[8];
    std::string s;
    size_t n = (len < maxLen) ? len : maxLen;
    for (size_t i = 0; i < n; i++) {
        snprintf(buf, sizeof(buf), "%02X ", data[i]);
        s += buf;
    }
    if (!s.empty() && s.back() == ' ') s.pop_back();
    if (len > maxLen) s += "...";
    return s;
}

// ── Real-Time Priority ─────────────────────────────────────────────────────
bool setRealtimePriority(pthread_t thread, int priority) {
    struct sched_param param;
    param.sched_priority = priority;
    return (pthread_setschedparam(thread, SCHED_FIFO, &param) == 0);
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK RX: Lắng nghe 1 module, đẩy gói vào hàng đợi
// ═══════════════════════════════════════════════════════════════════════════
void task_rx(int channelId, SX1278_WiringPi* radio, SafeQueue<TestPacket>* queue) {
    pthread_t thisThread = pthread_self();
    if (setRealtimePriority(thisThread, 80)) {
        printf("[RTOS] Task_RX_%d (%.3f MHz) → SCHED_FIFO Priority 80 ✓\n",
               channelId, radio->getFrequency());
    } else {
        printf("[INFO] Task_RX_%d (%.3f MHz) → SCHED_OTHER (chạy 'sudo' để bật RT)\n",
               channelId, radio->getFrequency());
    }

    uint8_t rxBuffer[256];

    while (g_running.load()) {
        if (radio->isPacketAvailable()) {
            int rssi = 0;
            float snr = 0.0f;
            int len = radio->readPacket(rxBuffer, sizeof(rxBuffer), rssi, snr);

            TestPacket pkt;
            getTimeStamp(pkt.timestamp, sizeof(pkt.timestamp));
            pkt.channelId = channelId;
            pkt.frequency = radio->getFrequency();
            pkt.rssi      = rssi;
            pkt.snr       = snr;

            if (len == -1) {
                pkt.crcError    = true;
                pkt.nodeId      = '?';
                pkt.packetId    = 0;
                pkt.payloadSize = 0;
                pkt.rawLen      = 0;
                queue->push(pkt);
                continue;
            }

            if (len >= 4) {
                pkt.rawLen = (uint8_t)(len > 255 ? 255 : len);
                memcpy(pkt.payload, rxBuffer, pkt.rawLen);

                // Hỗ trợ cả 2 chuẩn gói tin:
                // 1. Chuẩn Comm Test:      [Byte 0]: 'T', [Byte 1]: Node ('A'..'C'), [Byte 2..3]: PktID, [Byte 4]: Size
                // 2. Chuẩn Data Collection: [Byte 0]: Node ('A'..'C'), [Byte 1..2]: PktID, [Byte 3]: Size
                if (rxBuffer[0] == 'T' && len >= 5 && rxBuffer[1] >= 'A' && rxBuffer[1] <= 'C') {
                    pkt.crcError    = false;
                    pkt.nodeId      = (char)rxBuffer[1];
                    pkt.packetId    = ((uint16_t)rxBuffer[2] << 8) | rxBuffer[3];
                    pkt.payloadSize = rxBuffer[4];
                    queue->push(pkt);
                } else if (rxBuffer[0] >= 'A' && rxBuffer[0] <= 'C') {
                    pkt.crcError    = false;
                    pkt.nodeId      = (char)rxBuffer[0];
                    pkt.packetId    = ((uint16_t)rxBuffer[1] << 8) | rxBuffer[2];
                    pkt.payloadSize = rxBuffer[3];
                    queue->push(pkt);
                }
            }
        }
        usleep(1000);
    }
    printf("[RTOS] Task_RX_%d kết thúc.\n", channelId);
}

// ═══════════════════════════════════════════════════════════════════════════
// TASK LOGGER: In log + thống kê
// ═══════════════════════════════════════════════════════════════════════════
void task_logger(SafeQueue<TestPacket>* queue) {
    printf("\n");
    printf(" Timestamp    | CH | Freq(MHz) | Node | Pkt ID | Size | RSSI(dBm) | SNR(dB)\n");
    printf("──────────────┼────┼───────────┼──────┼────────┼──────┼───────────┼────────\n");

    uint32_t totalOk     = 0;
    uint32_t totalCrc    = 0;
    uint32_t chCount[3]  = {0, 0, 0};
    int64_t  rssiSum     = 0;
    float    snrSum      = 0.0f;
    int      rssiMin = 0, rssiMax = -200;
    float    snrMin = 100.0f, snrMax = -100.0f;
    struct timeval startTime;
    gettimeofday(&startTime, NULL);

    while (g_running.load() || !queue->empty()) {
        TestPacket pkt;
        if (queue->pop(pkt, 100)) {
            if (pkt.crcError) {
                totalCrc++;
                printf(" %-12s | %2d | %9.3f | ---- | ------ | ---- | --------- | CRC!\n",
                       pkt.timestamp, pkt.channelId, pkt.frequency);
                continue;
            }

            totalOk++;
            if (pkt.channelId >= 1 && pkt.channelId <= 3)
                chCount[pkt.channelId - 1]++;

            rssiSum += pkt.rssi;
            snrSum  += pkt.snr;
            if (pkt.rssi < rssiMin) rssiMin = pkt.rssi;
            if (pkt.rssi > rssiMax) rssiMax = pkt.rssi;
            if (pkt.snr  < snrMin)  snrMin  = pkt.snr;
            if (pkt.snr  > snrMax)  snrMax  = pkt.snr;

            printf(" %-12s | %2d | %9.3f |   %c  | %6u | %4u | %9d | %7.1f\n",
                   pkt.timestamp, pkt.channelId, pkt.frequency,
                   pkt.nodeId, pkt.packetId, pkt.payloadSize,
                   pkt.rssi, pkt.snr);

            // Hiển thị nội dung Payload (ASCII + HEX)
            size_t dataOffset = (pkt.payload[0] == 'T') ? 5 : 4;
            std::string hexStr = toHexString(pkt.payload, pkt.rawLen, 16);
            if (pkt.rawLen > dataOffset) {
                std::string dataStr = toAsciiString(pkt.payload + dataOffset, pkt.rawLen - dataOffset, 40);
                printf("   └─ [Payload %uB] Data: \"%s\" | Raw Hex: [%s]\n",
                       pkt.rawLen, dataStr.c_str(), hexStr.c_str());
            } else {
                std::string fullAscii = toAsciiString(pkt.payload, pkt.rawLen, 40);
                printf("   └─ [Payload %uB] Text: \"%s\" | Raw Hex: [%s]\n",
                       pkt.rawLen, fullAscii.c_str(), hexStr.c_str());
            }

            // Thống kê nhanh mỗi 20 gói
            if (totalOk % 20 == 0) {
                double avgRssi = (double)rssiSum / totalOk;
                float  avgSnr  = snrSum / totalOk;
                printf("──────────────┼────┼───────────┼──────┼────────┼──────┼───────────┼────────\n");
                printf(" [STATS] Tổng:%u/%d | CH1:%u CH2:%u CH3:%u | RSSI:%.1f | SNR:%.1f | CRC:%u\n",
                       totalOk, TARGET_TEST_PACKETS, chCount[0], chCount[1], chCount[2],
                       avgRssi, avgSnr, totalCrc);
                if (totalOk % TARGET_TEST_PACKETS == 0) {
                    printf(" >>> ĐÃ ĐẠT MỤC TIÊU TEST %d GÓI (Nhấn Ctrl+C để xem tổng kết) <<<\n", TARGET_TEST_PACKETS);
                }
                printf("──────────────┼────┼───────────┼──────┼────────┼──────┼───────────┼────────\n");
            }
        }
    }

    // ── Thống kê cuối ──
    struct timeval now;
    gettimeofday(&now, NULL);
    double elapsed = (now.tv_sec - startTime.tv_sec) +
                     (now.tv_usec - startTime.tv_usec) / 1000000.0;

    printf("\n");
    printf("╔══════════════════════════════════════════════════════════╗\n");
    printf("║            THỐNG KÊ KẾT QUẢ TEST TRUYỀN THÔNG         ║\n");
    printf("╠══════════════════════════════════════════════════════════╣\n");
    printf("║  Thời gian chạy     : %10.1f giây                  ║\n", elapsed);
    printf("║  Tổng gói nhận      : %10u                        ║\n", totalOk);
    printf("║  Lỗi CRC            : %10u                        ║\n", totalCrc);
    printf("╠──────────────────────────────────────────────────────────╣\n");
    printf("║  Kênh 1 (%.3f MHz): %10u gói                     ║\n", MODULE1_FREQ, chCount[0]);
    printf("║  Kênh 2 (%.3f MHz): %10u gói                     ║\n", MODULE2_FREQ, chCount[1]);
    printf("║  Kênh 3 (%.3f MHz): %10u gói                     ║\n", MODULE3_FREQ, chCount[2]);
    if (totalOk > 0) {
        double avgRssi = (double)rssiSum / totalOk;
        float  avgSnr  = snrSum / totalOk;
        printf("╠──────────────────────────────────────────────────────────╣\n");
        printf("║  RSSI trung bình   : %10.1f dBm                    ║\n", avgRssi);
        printf("║  RSSI (min / max)  : %4d / %4d dBm                ║\n", rssiMin, rssiMax);
        printf("║  SNR trung bình    : %10.1f dB                     ║\n", avgSnr);
        printf("║  SNR  (min / max)  : %5.1f / %5.1f dB               ║\n", snrMin, snrMax);
        printf("║  Throughput        : %10.2f gói/phút               ║\n",
               totalOk / (elapsed / 60.0));
    }
    printf("╚══════════════════════════════════════════════════════════╝\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════
int main() {
    signal(SIGINT, sigintHandler);
    signal(SIGTERM, sigintHandler);

    printf("\n");
    printf("╔══════════════════════════════════════════════════════════╗\n");
    printf("║   LoRa Comm Test - Raspberry Pi (3-Channel RX)         ║\n");
    printf("║   Kênh: %.3f | %.3f | %.3f MHz                ║\n",
           MODULE1_FREQ, MODULE2_FREQ, MODULE3_FREQ);
    printf("║   Nhấn Ctrl+C để dừng và xem thống kê                  ║\n");
    printf("╚══════════════════════════════════════════════════════════╝\n\n");

    // Khởi tạo WiringPi & SPI
    if (wiringPiSetup() < 0) {
        fprintf(stderr, "[FATAL] Không thể khởi tạo WiringPi!\n");
        return 1;
    }
    if (wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED) < 0) {
        fprintf(stderr, "[FATAL] Không thể mở SPI0!\n");
        return 1;
    }

    // Tắt điều khiển phần cứng CS tự động của kernel (chống xung đột bus với 3 module)
    SX1278_WiringPi::configureSpiNoCs();

    // Kéo CS lên HIGH
    pinMode(MODULE1_CS_PIN, OUTPUT); digitalWrite(MODULE1_CS_PIN, HIGH);
    pinMode(MODULE2_CS_PIN, OUTPUT); digitalWrite(MODULE2_CS_PIN, HIGH);
    pinMode(MODULE3_CS_PIN, OUTPUT); digitalWrite(MODULE3_CS_PIN, HIGH);

    // Khởi tạo 3 module
    SX1278_WiringPi radio1(MODULE1_CS_PIN, MODULE1_RST_PIN, MODULE1_DIO0_PIN, MODULE1_FREQ);
    SX1278_WiringPi radio2(MODULE2_CS_PIN, MODULE2_RST_PIN, MODULE2_DIO0_PIN, MODULE2_FREQ);
    SX1278_WiringPi radio3(MODULE3_CS_PIN, MODULE3_RST_PIN, MODULE3_DIO0_PIN, MODULE3_FREQ);

    printf("[INIT] Module 1 (%.3f MHz)... ", MODULE1_FREQ); radio1.begin(); printf("OK\n");
    printf("[INIT] Module 2 (%.3f MHz)... ", MODULE2_FREQ); radio2.begin(); printf("OK\n");
    printf("[INIT] Module 3 (%.3f MHz)... ", MODULE3_FREQ); radio3.begin(); printf("OK\n\n");

    // Kích hoạt 4 luồng
    SafeQueue<TestPacket> packetQueue;

    printf("[RTOS] Kích hoạt 3 Task_RX + 1 Task_Logger...\n");
    std::thread tLogger(task_logger, &packetQueue);
    std::thread tRx1(task_rx, 1, &radio1, &packetQueue);
    std::thread tRx2(task_rx, 2, &radio2, &packetQueue);
    std::thread tRx3(task_rx, 3, &radio3, &packetQueue);

    printf("[RTOS] Sẵn sàng! Đang chờ gói tin từ ESP32...\n");

    tRx1.join();
    tRx2.join();
    tRx3.join();
    tLogger.join();

    printf("\n[SUCCESS] Test dừng an toàn.\n");
    return 0;
}
