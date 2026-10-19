/*
 * Multi-Channel LoRa Gateway on Raspberry Pi CM4 + 3 Module Ra-02 (SX1278)
 * -------------------------------------------------------------------------
 * Nghiên cứu: Channel Hopping Optimization & TinyML
 * Dựa trên cấu trúc paper: arXiv:2412.01609v1
 *
 * Chức năng:
 *   - Lắng nghe đồng thời 3 kênh tần số 433.175, 433.375, 433.575 MHz
 *   - Thu thập các trường: Node Source ('A', 'B', 'C'), Packet ID,
 *     Payload Size, RSSI, SNR, Tần số thu
 *   - Lưu trực tiếp vào file log CSV chuẩn hóa
 * -------------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <sys/time.h>

#include "config.h"
#include "sx1278_wiringpi.h"

// Hàm lấy chuỗi thời gian định dạng HH:MM:SS.mmm
void getTimeStamp(char* buffer, size_t size) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm* tm_info = localtime(&tv.tv_sec);
    char timeStr[16];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", tm_info);
    snprintf(buffer, size, "%s.%03ld", timeStr, tv.tv_usec / 1000);
}

int main(int argc, char* argv[]) {
    printf("=========================================================\n");
    printf("   LoRa Multi-Channel Gateway (Raspberry Pi CM4 + 3x Ra-02)\n");
    printf("   Paper: arXiv:2412.01609v1 (LoRaEdgeTinyML)\n");
    printf("   Channels: %.3f MHz, %.3f MHz, %.3f MHz\n", MODULE1_FREQ, MODULE2_FREQ, MODULE3_FREQ);
    printf("=========================================================\n\n");

    // Khởi tạo wiringPi & SPI
    if (wiringPiSetup() < 0) {
        fprintf(stderr, "[FATAL] Không thể khởi tạo WiringPi!\n");
        return 1;
    }

    if (wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED) < 0) {
        fprintf(stderr, "[FATAL] Không thể mở kết nối SPI0 (/dev/spidev0.0)!\n");
        return 1;
    }

    // Khởi tạo 3 module SX1278
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

    // Tạo file CSV để lưu log
    time_t rawtime;
    time(&rawtime);
    struct tm* timeinfo = localtime(&rawtime);
    char logFileName[64];
    strftime(logFileName, sizeof(logFileName), "gateway_log_%Y%m%d_%H%M%S.csv", timeinfo);

    FILE* logFile = fopen(logFileName, "w");
    if (!logFile) {
        fprintf(stderr, "[ERROR] Không thể tạo file log %s!\n", logFileName);
        return 1;
    }

    // Ghi header CSV chuẩn theo bài báo
    fprintf(logFile, "time_slot,source,packet_ID,size_of_message,RSSI,SNR,frequency\n");
    fflush(logFile);
    printf("[LOG] Bắt đầu ghi log vào file: %s\n\n", logFileName);

    SX1278_WiringPi* radios[3] = { &radio1, &radio2, &radio3 };
    uint8_t rxBuffer[256];

    printf("Đang chờ gói tin LoRa từ 3 kênh...\n");
    printf("-----------------------------------------------------------------------------\n");
    printf(" Timestamp    | Ch (MHz) | Node | Pkt ID | Size | RSSI (dBm) | SNR (dB)\n");
    printf("-----------------------------------------------------------------------------\n");

    while (1) {
        for (int i = 0; i < 3; i++) {
            if (radios[i]->isPacketAvailable()) {
                int rssi = 0;
                float snr = 0.0f;
                int len = radios[i]->readPacket(rxBuffer, sizeof(rxBuffer), rssi, snr);

                if (len >= 4) {
                    char timeStr[32];
                    getTimeStamp(timeStr, sizeof(timeStr));

                    // Giải mã header gói tin: [NodeID, Pkt_ID_H, Pkt_ID_L, Size]
                    char sourceNode = (char)rxBuffer[0];
                    uint16_t packetId = ((uint16_t)rxBuffer[1] << 8) | rxBuffer[2];
                    uint8_t sizeOfMessage = rxBuffer[3];
                    double freq = radios[i]->getFrequency();

                    // Hiển thị ra màn hình Terminal
                    printf(" %-12s | %8.3f |   %c  | %6u | %4u | %10d | %7.1f\n",
                           timeStr, freq, sourceNode, packetId, sizeOfMessage, rssi, snr);

                    // Ghi dòng dữ liệu vào file CSV
                    fprintf(logFile, "%s,%c,%u,%u,%d,%.1f,%.3f\n",
                            timeStr, sourceNode, packetId, sizeOfMessage, rssi, snr, freq);
                    fflush(logFile);
                }
            }
        }
        usleep(5000); // Polling delay 5ms
    }

    fclose(logFile);
    return 0;
}
