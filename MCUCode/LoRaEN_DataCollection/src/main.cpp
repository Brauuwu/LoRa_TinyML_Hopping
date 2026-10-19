/*
 * LoRa End-Node Traffic Generator & Data Collection (ESP32 + Ra-02 + OLED)
 * -------------------------------------------------------------------------
 * Nghiên cứu: Channel Hopping Optimization & TinyML
 * Dựa trên cấu trúc paper: arXiv:2412.01609v1
 *
 * Chức năng:
 *   - Phát các chùm gói tin (bursts) với kích thước thay đổi (30B -> 250B)
 *   - Quét qua 3 kênh tần số: 433.175 MHz, 433.375 MHz, 433.575 MHz
 *   - Định danh Node rõ ràng ('A', 'B' hoặc 'C') ở header gói tin
 *   - Hiển thị trực tiếp thông số RF, tiến trình trên OLED SSD1306
 * -------------------------------------------------------------------------
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <RadioLib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ═══════════════════════════════════════════════════════════════════════════
// CẤU HÌNH NODE: Thay đổi thành 'A', 'B' hoặc 'C' tương ứng khi nạp 3 node!
// ═══════════════════════════════════════════════════════════════════════════
#define NODE_ID             'A'

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

// ── 3 Kênh tần số thực nghiệm (dải 433 MHz) ─────────────────────────────────
const float CHANNELS[3] = {433.175, 433.375, 433.575};
const int NUM_CHANNELS = 3;
int currentChannelIndex = 0;

// Các thông số vô tuyến LoRa (đồng bộ với Gateway)
#define LORA_BW             125.0 // kHz
#define LORA_SF                 7 // Spreading Factor 7
#define LORA_CR                 5 // 4/5
#define LORA_SYNC_WORD       0x12 // Private/Experimental LoRa Sync Word
#define LORA_POWER             17 // dBm
#define LORA_PREAMBLE           8 // symbols

// ── Kịch bản truyền dữ liệu theo bài báo (arXiv:2412.01609v1) ────────────────
const int SAMPLES_PER_BURST = 50;  // 50 gói cho mỗi kích thước payload
const int PAYLOAD_SIZES[6]  = {30, 74, 118, 162, 206, 250}; // 6 bước kích thước
const int NUM_SIZES = 6;

int sizeIndex = 0;
uint32_t packetCount = 0;
unsigned long lastTxTime = 0;
const unsigned long TX_INTERVAL = 3000; // Khoảng thời gian phát giữa 2 gói: 3 giây

// ── Đối tượng phần cứng ─────────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

// ── Hàm cập nhật màn hình OLED ──────────────────────────────────────────────
void oledUpdate(int chIdx, int seq, int pSize, int status, unsigned long airTime) {
  if (!oledOk) return;

  display.clearDisplay();
  // Header bar
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.printf("NODE [%c] - DATA LOG", NODE_ID);
  display.setCursor(95, 2);
  display.printf("CH%d", chIdx + 1);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 15);
  display.printf("Freq: %.3f MHz", CHANNELS[chIdx]);
  display.setCursor(0, 27);
  display.printf("Pkt : #%d / %d", seq, SAMPLES_PER_BURST);
  display.setCursor(0, 39);
  display.printf("Size: %d B (ToA:%lums)", pSize, airTime);
  display.setCursor(0, 51);
  if (status == RADIOLIB_ERR_NONE) {
    display.print("Status: TX SUCCESS");
  } else {
    display.printf("Status: ERR %d", status);
  }

  display.display();
}

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  delay(500);
  Serial.println("\n==================================================");
  Serial.printf("   LoRa Traffic Generator - Node [%c]\n", NODE_ID);
  Serial.println("   Paper: arXiv:2412.01609v1 (LoRaEdgeTinyML)");
  Serial.println("==================================================");

  // Khởi động I2C & OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledOk = true;
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 5);
    display.printf("LoRa Node [%c] Init...\n", NODE_ID);
    display.println("Freq: 433 MHz (3 CH)");
    display.display();
  }

  // Khởi tạo SPI & LoRa Radio SX1278
  loRaSPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  Serial.printf("[INIT] Starting SX1278 on %.3f MHz...\n", CHANNELS[currentChannelIndex]);

  int state = radio.begin(CHANNELS[currentChannelIndex], LORA_BW, LORA_SF, LORA_CR,
                          LORA_SYNC_WORD, LORA_POWER, LORA_PREAMBLE);
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("[INIT] SX1278 Initialized Successfully!");
  } else {
    Serial.printf("[ERROR] SX1278 Init Failed! Error code: %d\n", state);
    if (oledOk) {
      display.println("SX1278 FAIL!");
      display.display();
    }
    while (true) { delay(1000); }
  }

  // Ngẫu nhiên hóa seed bằng nhiễu ADC chân không dùng
  randomSeed(analogRead(34) + (uint8_t)NODE_ID);
  delay(1500);
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  if (now - lastTxTime >= TX_INTERVAL || lastTxTime == 0) {
    lastTxTime = now;
    int currentPayloadSize = PAYLOAD_SIZES[sizeIndex];

    // Tạo payload với độ dài mong muốn
    // Cấu trúc gói tin:
    // [Byte 0]: Node ID ('A', 'B', 'C')
    // [Byte 1..2]: Packet ID (16-bit uint)
    // [Byte 3]: Payload Size
    // [Byte 4..N-2]: Padding bytes ('X')
    // [Byte N-1]: Ký tự kết thúc '\0'
    uint8_t txBuffer[256];
    memset(txBuffer, 'X', currentPayloadSize);
    txBuffer[0] = (uint8_t)NODE_ID;
    txBuffer[1] = (uint8_t)((packetCount >> 8) & 0xFF);
    txBuffer[2] = (uint8_t)(packetCount & 0xFF);
    txBuffer[3] = (uint8_t)currentPayloadSize;
    txBuffer[currentPayloadSize - 1] = '\0';

    digitalWrite(LED_PIN, HIGH);
    unsigned long t0 = millis();

    int state = radio.transmit(txBuffer, currentPayloadSize);

    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    // Xuất log Serial định dạng tương thích với parser
    Serial.printf("NODE:%c | CH:%.3fMHz | PKT_ID:%lu | SIZE:%d | ToA:%lums | Result:%d\n",
                  NODE_ID, CHANNELS[currentChannelIndex], (unsigned long)packetCount,
                  currentPayloadSize, airTime, state);

    oledUpdate(currentChannelIndex, packetCount, currentPayloadSize, state, airTime);

    packetCount++;

    // Khi đã gửi đủ 50 gói cho kích thước hiện tại
    if (packetCount >= SAMPLES_PER_BURST) {
      packetCount = 0;
      sizeIndex++;

      // Nếu đã xong tất cả 6 kích thước payload -> Chuyển sang kênh tần số tiếp theo
      if (sizeIndex >= NUM_SIZES) {
        sizeIndex = 0;
        currentChannelIndex = (currentChannelIndex + 1) % NUM_CHANNELS;
        
        Serial.printf("\n[CHANNEL SWITCH] Node [%c] changing to %.3f MHz...\n\n",
                      NODE_ID, CHANNELS[currentChannelIndex]);
        
        radio.setFrequency(CHANNELS[currentChannelIndex]);
        delay(2000); // Tạm dừng 2 giây giữa các đợt đổi kênh
      }
    }
  }
}
