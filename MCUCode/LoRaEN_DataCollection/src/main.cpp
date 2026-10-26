/*
 * LoRa End-Node Data Collection - Firmware Thực Nghiệm Thu Thập Dữ Liệu
 * -------------------------------------------------------------------------
 * Đề tài: Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML
 * Phần cứng: ESP32 DevKit V1 + Module LoRa Ra-02 (SX1278 433MHz) + OLED SSD1306
 *
 * KỊCH BẢN THU THẬP DỮ LIỆU CHUẨN BÀI BÁO (LoRaEdgeTinyML):
 *   1. Tần số cố định: Cấu hình kênh phát cố định (CH1, CH2 hoặc CH3).
 *   2. Định danh cố định: Gán nhãn Node 'A', 'B', hoặc 'C'.
 *   3. Phát tuần tự 6 mức kích thước payload: 30, 74, 118, 162, 206, 250 bytes.
 *   4. Mỗi mức kích thước phát chính xác 100 gói (Packet ID từ 0 đến 99).
 *   5. Payload chứa chuỗi chữ số ngẫu nhiên '0'..'9' sau dấu '*' lấp đầy độ dài.
 *   6. KHI HOÀN THÀNH GÓI THỨ 100 CỦA KÍCH THƯỚC 250B -> NGỪNG PHÁT HOÀN TOÀN!
 * -------------------------------------------------------------------------
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <RadioLib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ═══════════════════════════════════════════════════════════════════════════
// 1. CẤU HÌNH ĐỊNH DANH NODE (NODE ID)
// Thay đổi thành 'A', 'B' hoặc 'C' tương ứng khi nạp code cho từng bo mạch!
// ═══════════════════════════════════════════════════════════════════════════
#define NODE_ID             'A'   // 'A', 'B', hoặc 'C'

// ═══════════════════════════════════════════════════════════════════════════
// 2. CẤU HÌNH TẦN SỐ CỐ ĐỊNH CHO ĐỢT ĐO (FIXED CHANNEL SELECTION)
//    1: Kênh 1 - 433.175 MHz
//    2: Kênh 2 - 433.375 MHz
//    3: Kênh 3 - 433.575 MHz
// Chọn kênh tương ứng cho kịch bản đo đạc (ví dụ: A_433.175, A_B_433.175, ...)
// ═══════════════════════════════════════════════════════════════════════════
#define SELECTED_CHANNEL_NUM  1   // Đặt 1, 2, hoặc 3

// Bảng tra cứu tần số theo số kênh
const float CHANNELS[3] = {433.175, 433.375, 433.575};
const float FIXED_FREQUENCY = CHANNELS[SELECTED_CHANNEL_NUM - 1];

// ═══════════════════════════════════════════════════════════════════════════
// 3. THIẾT LẬP KỊCH BẢN PHÁT GÓI TIN (TRAFFIC SCENARIO)
// ═══════════════════════════════════════════════════════════════════════════
#define SAMPLES_PER_BURST   100   // Mỗi kích thước phát đúng 100 gói (0..99)
const int PAYLOAD_SIZES[6]  = {30, 74, 118, 162, 206, 250}; // 6 mức kích thước
const int NUM_SIZES         = 6;

// Khoảng thời gian nghỉ giữa 2 lần phát liên tiếp
#define TX_BASE_INTERVAL_MS 3000  // Nghỉ 3.0 giây giữa 2 gói
#define TX_JITTER_MS        500   // Dao động ngẫu nhiên 0..500 ms (tổng 3.0s - 3.5s)

// ── Định nghĩa chân kết nối phần cứng ESP32 ─────────────────────────────────
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

// ── Các thông số vô tuyến LoRa (đồng bộ hoàn toàn với Gateway) ──────────────
#define LORA_BW             125.0 // kHz
#define LORA_SF                 7 // Spreading Factor 7
#define LORA_CR                 5 // 4/5
#define LORA_SYNC_WORD       0x12 // Private/Experimental LoRa Sync Word
#define LORA_POWER             17 // dBm (50 mW)
#define LORA_PREAMBLE           8 // symbols

// ── Biến điều khiển trạng thái phát ─────────────────────────────────────────
int sizeIndex = 0;              // Chỉ số kích thước payload hiện tại (0..5)
uint32_t packetCount = 0;       // Đếm số gói đã phát của kích thước hiện tại (0..99)
uint32_t totalPacketsSent = 0;  // Tổng số gói đã phát trên toàn bộ tiến trình (tối đa 600)
unsigned long lastTxTime = 0;
unsigned long currentInterval = TX_BASE_INTERVAL_MS;
bool isFinished = false;        // Cờ báo hiệu đã hoàn thành toàn bộ kịch bản

// ── Đối tượng phần cứng ─────────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

// ── Hàm cập nhật màn hình OLED trong quá trình phát ─────────────────────────
void oledUpdateProgress(int seq, int pSize, int status, unsigned long airTime) {
  if (!oledOk) return;

  display.clearDisplay();
  // Thanh tiêu đề phía trên
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.printf("NODE [%c] - ", NODE_ID);
  display.setCursor(95, 2);
  display.printf("CH%d", SELECTED_CHANNEL_NUM);

  // Nội dung thông số truyền
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 15);
  display.printf("Freq: %.3f MHz", FIXED_FREQUENCY);
  display.setCursor(0, 27);
  display.printf("Pkt : #%02d / %d", seq, SAMPLES_PER_BURST);
  display.setCursor(0, 39);
  display.printf("Size: %3dB (%d/%d)", pSize, sizeIndex + 1, NUM_SIZES);
  display.setCursor(0, 51);
  if (status == RADIOLIB_ERR_NONE) {
    display.printf("OK | ToA: %lums", airTime);
  } else {
    display.printf("FAIL: ERR %d", status);
  }

  display.display();
}

// ── Hàm hiển thị màn hình OLED khi hoàn thành và ngừng phát ─────────────────
void oledShowFinished() {
  if (!oledOk) return;

  display.clearDisplay();
  // Header hoàn thành
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(4, 2);
  display.printf("NODE [%c] - HOAN THANH", NODE_ID);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 16);
  display.printf("Freq : %.3f MHz (CH%d)", FIXED_FREQUENCY, SELECTED_CHANNEL_NUM);
  display.setCursor(0, 28);
  display.printf("Tong : %u/600 Pkts", totalPacketsSent);
  display.setCursor(0, 40);
  display.print("Du 6 Sizes (30->250B)");
  display.setCursor(0, 52);
  display.print(">> DA DUNG PHAT <<");
  display.display();
}

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("   LORA END-NODE - DATA COLLECTION TRAFFIC GENERATOR");
  Serial.printf("   Node ID      : [%c]\n", NODE_ID);
  Serial.printf("   Tần số cố định: %.3f MHz (Kênh %d)\n", FIXED_FREQUENCY, SELECTED_CHANNEL_NUM);
  Serial.printf("   Số gói/mức   : %d gói tin\n", SAMPLES_PER_BURST);
  Serial.printf("   Tổng số gói  : %d mức x %d = %d gói tin\n", NUM_SIZES, SAMPLES_PER_BURST, NUM_SIZES * SAMPLES_PER_BURST);
  Serial.println("   Khi gửi đủ gói cuối (250B x 100), Node sẽ DỪNG PHÁT.");
  Serial.println("==================================================");

  // Khởi động I2C & OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledOk = true;
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 5);
    display.printf("Node [%c] Khoi Dong...\n", NODE_ID);
    display.printf("Freq: %.3f MHz\n", FIXED_FREQUENCY);
    display.printf("Muc tieu: 600 Goi\n");
    display.display();
  }

  // Khởi tạo SPI & LoRa Radio SX1278 trên tần số cố định
  loRaSPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  Serial.printf("[INIT] Đang khởi động SX1278 trên tần số %.3f MHz...\n", FIXED_FREQUENCY);

  int state = radio.begin(FIXED_FREQUENCY, LORA_BW, LORA_SF, LORA_CR,
                          LORA_SYNC_WORD, LORA_POWER, LORA_PREAMBLE);
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("[INIT] SX1278 Khởi tạo THÀNH CÔNG!");
  } else {
    Serial.printf("[ERROR] SX1278 Khởi tạo THẤT BẠI! Mã lỗi: %d\n", state);
    if (oledOk) {
      display.clearDisplay();
      display.setCursor(0, 20);
      display.println("SX1278 INIT ERROR!");
      display.display();
    }
    while (true) { delay(1000); }
  }

  // Khởi tạo Seed ngẫu nhiên từ nhiễu điện từ ADC
  randomSeed(analogRead(34) + (uint8_t)NODE_ID + micros());
  delay(1500);

  Serial.println();
  Serial.println("BAT DAU KICH BAN PHAT GOI TIN...");
  Serial.println("--------------------------------------------------");
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  // NẾU ĐÃ HOÀN THÀNH TOÀN BỘ 600 GÓI TIN -> DỪNG PHÁT HOÀN TOÀN
  if (isFinished) {
    // Nhấp nháy nhẹ LED mỗi 3 giây để báo hiệu hệ thống đang ở trạng thái nghỉ
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(2950);
    return;
  }

  unsigned long now = millis();

  // Kiểm tra chu kỳ phát (Interval) có kèm ngẫu nhiên hóa (Jitter)
  if (now - lastTxTime >= currentInterval || lastTxTime == 0) {
    lastTxTime = now;
    currentInterval = TX_BASE_INTERVAL_MS + random(0, TX_JITTER_MS);

    int currentPayloadSize = PAYLOAD_SIZES[sizeIndex];

    // Xây dựng gói tin ASCII theo đúng định dạng bài báo LoRaEdgeTinyML:
    // Định dạng: "<NODE_ID><packetCount>*<chuỗi chữ số ngẫu nhiên '0'..'9'>"
    // Ví dụ kích thước 30 bytes: "A0*204036563877114581128047642" (đúng 30 ký tự)
    // - Byte đầu: Tên Node ('A', 'B', 'C')
    // - Các byte số: Số thứ tự gói tin (0 đến 99 dạng chuỗi ASCII)
    // - Ký tự '*': Phân cách (separator)
    // - Các byte còn lại: Chữ số ngẫu nhiên '0'..'9' (ASCII 48..57) cho đến đủ kích thước
    char txBuffer[256];
    int headerLen = snprintf(txBuffer, sizeof(txBuffer), "%c%u*", NODE_ID, packetCount);
    for (int i = headerLen; i < currentPayloadSize; i++) {
      txBuffer[i] = (char)random(48, 58); // Ký tự số ngẫu nhiên '0' -> '9'
    }
    txBuffer[currentPayloadSize] = '\0'; // Kết thúc chuỗi để in ra Serial an toàn

    // Bật LED chỉ báo đang truyền sóng
    digitalWrite(LED_PIN, HIGH);
    unsigned long t0 = millis();

    int state = radio.transmit((uint8_t*)txBuffer, currentPayloadSize);

    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    totalPacketsSent++;

    // In log chi tiết ra Serial Monitor
    Serial.printf("NODE:%c | FREQ:%.3fMHz | SIZE:%3dB (%d/%d) | PKT:#%02u/%d | TOTAL:%3u/600 | ToA:%lums | Result:%d | DATA:\"%s\"\n",
                  NODE_ID, FIXED_FREQUENCY, currentPayloadSize, sizeIndex + 1, NUM_SIZES,
                  packetCount, SAMPLES_PER_BURST, totalPacketsSent, airTime, state, txBuffer);

    // Cập nhật màn hình OLED
    oledUpdateProgress(packetCount, currentPayloadSize, state, airTime);

    packetCount++;

    // Khi đã gửi đủ 100 gói cho kích thước hiện tại
    if (packetCount >= SAMPLES_PER_BURST) {
      packetCount = 0;
      sizeIndex++;

      // KIỂM TRA ĐÃ GỬI XONG MỨC KÍCH THƯỚC CUỐI CÙNG CHƯA (250 BYTES)
      if (sizeIndex >= NUM_SIZES) {
        isFinished = true;

        // Đưa module LoRa vào chế độ Sleep để ngừng phát sóng hoàn toàn
        radio.sleep();

        Serial.println();
        Serial.println("==================================================");
        Serial.printf(" >>> [HOÀN THÀNH KỊCH BẢN] Node [%c] ĐÃ PHÁT ĐỦ %u GÓI TIN! <<<\n", NODE_ID, totalPacketsSent);
        Serial.printf(" Tần số cố định : %.3f MHz (Kênh %d)\n", FIXED_FREQUENCY, SELECTED_CHANNEL_NUM);
        Serial.printf(" Chi tiết       : 6 mức kích thước (30B -> 250B) x %d gói\n", SAMPLES_PER_BURST);
        Serial.println(" LoRa Radio đã chuyển sang chế độ SLEEP.");
        Serial.println(" >>> NODE ĐÃ NGỪNG PHÁT HOÀN TOÀN! <<<");
        Serial.println("==================================================");

        oledShowFinished();
        return;
      }

      Serial.println();
      Serial.println("--------------------------------------------------");
      Serial.printf("[TIẾN TRÌNH] Chuyển sang kích thước tiếp theo: %d bytes (100 gói)...\n",
                    PAYLOAD_SIZES[sizeIndex]);
      Serial.println("--------------------------------------------------");
      delay(2000); // Tạm dừng 2 giây giữa 2 đợt kích thước
    }
  }
}
