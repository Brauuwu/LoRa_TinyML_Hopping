/*
 * LoRa Communication Test - ESP32 (TX Only, No ACK)
 * -------------------------------------------------------------------------
 * Mục đích: Gửi gói tin test liên tục để Raspberry Pi nhận và đo RSSI/SNR
 *
 * Chức năng:
 *   - Gửi gói tin test có đánh số thứ tự mỗi 2 giây
 *   - Hiển thị trạng thái trên OLED SSD1306
 *   - In log chi tiết ra Serial Monitor
 *
 * Cấu trúc gói tin:
 *   [Byte 0]   : 'T' (Test marker)
 *   [Byte 1]   : NODE_ID ('A')
 *   [Byte 2..3]: Packet ID (16-bit, big-endian)
 *   [Byte 4]   : Payload size
 *   [Byte 5..N]: Padding 'X'
 * -------------------------------------------------------------------------
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <RadioLib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ═══════════════════════════════════════════════════════════════════════════
// CẤU HÌNH TEST
// ═══════════════════════════════════════════════════════════════════════════
#define NODE_ID             'C'

// Tần số test - đồng bộ với 1 trong 3 kênh RPi
// #define TEST_FREQ           433.175  // MHz (Kênh 1)
// #define TEST_FREQ        433.375  // MHz (Kênh 2)
#define TEST_FREQ        433.575  // MHz (Kênh 3)

#define TX_INTERVAL_MS      2000     // Gửi mỗi 2 giây
#define TEST_PAYLOAD_SIZE   100      // Kích thước gói (bytes)
#define TEST_TOTAL_PACKETS  100      // Mục tiêu đợt test: 100 gói

// ── Chân phần cứng ESP32 ────────────────────────────────────────────────
#define LORA_MOSI            27
#define LORA_MISO            19
#define LORA_SCK             18
#define LORA_NSS              5
#define LORA_RST             14
#define LORA_DIO0            26

#define OLED_SDA             21
#define OLED_SCL             22
#define OLED_WIDTH          128
#define OLED_HEIGHT          64
#define LED_PIN               2

// ── Thông số RF (đồng bộ Gateway) ──────────────────────────────────────
#define LORA_BW             125.0
#define LORA_SF                 7
#define LORA_CR                 5
#define LORA_SYNC_WORD       0x12
#define LORA_POWER             17
#define LORA_PREAMBLE           8

// ── Đối tượng phần cứng ────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

// ── Biến thống kê ──────────────────────────────────────────────────────
uint16_t packetId = 0;
uint32_t totalSent = 0;
uint32_t totalFailed = 0;
unsigned long lastTxTime = 0;

// ═══════════════════════════════════════════════════════════════════════════
// CẬP NHẬT OLED
// ═══════════════════════════════════════════════════════════════════════════
void oledUpdate(int pktId, int state, unsigned long airTime) {
    if (!oledOk) return;

    display.clearDisplay();

    // Header bar
    display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(2, 2);
    display.printf(" COMM TEST [%c] TX", NODE_ID);

    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 15);
    display.printf("Freq: %.3f MHz", TEST_FREQ);
    display.setCursor(0, 27);
    display.printf("Pkt : #%d/%d Size:%dB", pktId + 1, TEST_TOTAL_PACKETS, TEST_PAYLOAD_SIZE);
    display.setCursor(0, 39);
    display.printf("ToA : %lu ms", airTime);
    display.setCursor(0, 51);
    if (state == RADIOLIB_ERR_NONE) {
        display.printf("Sent:%lu  Fail:%lu", totalSent, totalFailed);
    } else {
        display.printf("TX ERROR: %d", state);
    }

    display.display();
}

// ═══════════════════════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════════════════════
void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    Serial.begin(115200);
    delay(500);

    Serial.println();
    Serial.println("==================================================");
    Serial.printf( "   LoRa Comm Test - Node [%c] TX Only\n", NODE_ID);
    Serial.printf( "   Freq: %.3f MHz | Size: %d bytes\n", TEST_FREQ, TEST_PAYLOAD_SIZE);
    Serial.println("==================================================");
    Serial.println();

    // Khởi động OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        oledOk = true;
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 5);
        display.printf("Node [%c] Init...\n", NODE_ID);
        display.display();
    }

    // Khởi tạo LoRa
    loRaSPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
    Serial.printf("[INIT] SX1278 trên %.3f MHz...\n", TEST_FREQ);

    int state = radio.begin(TEST_FREQ, LORA_BW, LORA_SF, LORA_CR,
                            LORA_SYNC_WORD, LORA_POWER, LORA_PREAMBLE);
    if (state == RADIOLIB_ERR_NONE) {
        Serial.println("[INIT] SX1278 OK!");
    } else {
        Serial.printf("[FATAL] SX1278 lỗi: %d\n", state);
        while (true) { delay(1000); }
    }

    Serial.println();
    Serial.println(" PKT_ID | SIZE | ToA(ms) | STATUS");
    Serial.println("--------|------|---------|-------");

    delay(1000);
}

// ═══════════════════════════════════════════════════════════════════════════
// LOOP: Gửi gói liên tục
// ═══════════════════════════════════════════════════════════════════════════
void loop() {
    unsigned long now = millis();
    if (now - lastTxTime < TX_INTERVAL_MS && lastTxTime != 0) return;
    lastTxTime = now;

    // Xây dựng gói tin với payload ngẫu nhiên theo chuẩn bài báo
    uint8_t txBuffer[256];
    txBuffer[0] = 'T';
    txBuffer[1] = (uint8_t)NODE_ID;
    txBuffer[2] = (uint8_t)((packetId >> 8) & 0xFF);
    txBuffer[3] = (uint8_t)(packetId & 0xFF);
    txBuffer[4] = (uint8_t)TEST_PAYLOAD_SIZE;
    if (TEST_PAYLOAD_SIZE > 5) {
        txBuffer[5] = '*'; // Dấu phân cách như trong bài báo
        // Điền toàn bộ phần thân payload còn lại bằng chữ số ngẫu nhiên ('0'..'9')
        for (int i = 6; i < TEST_PAYLOAD_SIZE - 1; i++) {
            txBuffer[i] = (uint8_t)random(48, 58); // ASCII 48 ('0') -> 57 ('9')
        }
        txBuffer[TEST_PAYLOAD_SIZE - 1] = '\0';
    }

    // Truyền
    digitalWrite(LED_PIN, HIGH);
    unsigned long t0 = millis();
    int state = radio.transmit(txBuffer, TEST_PAYLOAD_SIZE);
    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    if (state == RADIOLIB_ERR_NONE) {
        totalSent++;
        Serial.printf(" %5u  | %4d | %7lu | OK\n", packetId, TEST_PAYLOAD_SIZE, airTime);
    } else {
        totalFailed++;
        Serial.printf(" %5u  | %4d | %7lu | ERR=%d\n", packetId, TEST_PAYLOAD_SIZE, airTime, state);
    }

    oledUpdate(packetId, state, airTime);

    // Thống kê mỗi 10 gói
    if ((totalSent + totalFailed) % 10 == 0 && (totalSent + totalFailed) > 0) {
        Serial.println("--------|------|---------|-------");
        Serial.printf(" [STATS] Sent: %lu | Failed: %lu\n", totalSent, totalFailed);
        Serial.println("--------|------|---------|-------");
    }

    packetId++;
}
