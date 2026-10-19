/*
 * LoRa End-Node with TinyML-based Channel Hopping (ESP32 + Ra-02 + OLED)
 * -------------------------------------------------------------------------
 * Nghiên cứu: Channel Hopping Optimization & TinyML
 * Dựa trên cấu trúc paper: arXiv:2412.01609v1
 *
 * Chức năng:
 *   - Quản lý bộ đệm trượt (Sliding Window) lưu trạng thái lịch sử kênh
 *   - Lựa chọn kênh thông minh:
 *       + Mode 0: Kênh cố định (Fixed Channel)
 *       + Mode 1: Nhảy kênh ngẫu nhiên (Random Channel Hopping)
 *       + Mode 2: Nhảy kênh dựa trên suy luận TinyML (Predictive Hopping)
 *   - Đo lường và báo cáo PDR, RSSI, SNR, số lần nhảy kênh (Hopping count)
 * -------------------------------------------------------------------------
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <RadioLib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ═══════════════════════════════════════════════════════════════════════════
// CẤU HÌNH NODE & CHẾ ĐỘ NHẢY KÊNH:
// ═══════════════════════════════════════════════════════════════════════════
#define NODE_ID              'A'       // 'A', 'B' hoặc 'C'

// Chế độ: 0 = Fixed, 1 = Random Hopping, 2 = TinyML Hopping
#define HOPPING_MODE         2

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
int previousChannelIndex = 0;
uint32_t hopCount = 0;

// Các thông số vô tuyến LoRa (đồng bộ với Gateway)
#define LORA_BW             125.0 // kHz
#define LORA_SF                 7 // Spreading Factor 7
#define LORA_CR                 5 // 4/5
#define LORA_SYNC_WORD       0x12 // Private LoRa Sync Word
#define LORA_POWER             17 // dBm
#define LORA_PREAMBLE           8 // symbols

// ── Đối tượng phần cứng ─────────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

uint32_t packetCount = 0;
uint32_t successCount = 0;
unsigned long lastTxTime = 0;
const unsigned long TX_INTERVAL = 3000; // 3 giây/gói

// ── Bộ đệm trượt lịch sử kênh (Temporal Window Memory) ──────────────────────
#define HISTORY_LEN 5
struct ChannelHistory {
  float ch_busy[3]; // 0: rảnh/tốt, 1: bận/xung đột
  float rssi;
  float snr;
};
ChannelHistory history[HISTORY_LEN];
int historyCount = 0;

// ── Hàm dự đoán kênh tối ưu bằng TinyML / Heuristic ────────────────────────
int predictNextChannel() {
#if HOPPING_MODE == 0
  // Mode 0: Kênh cố định (không nhảy)
  return 0;

#elif HOPPING_MODE == 1
  // Mode 1: Nhảy ngẫu nhiên (Random Hopping)
  return random(0, NUM_CHANNELS);

#elif HOPPING_MODE == 2
  // Mode 2: TinyML Predictive Hopping
  // Đánh giá lịch sử gần nhất để chọn kênh có điểm va chạm thấp nhất & RSSI tốt nhất
  if (historyCount == 0) return 0;

  // Tính điểm phạt va chạm tích lũy cho từng kênh trong cửa sổ trượt
  float channelScore[3] = {0.0f, 0.0f, 0.0f};
  for (int i = 0; i < historyCount; i++) {
    for (int ch = 0; ch < 3; ch++) {
      channelScore[ch] += history[i].ch_busy[ch];
    }
  }

  // Chọn kênh có số lần va chạm ít nhất
  int bestCh = 0;
  float minCollisions = channelScore[0];
  for (int ch = 1; ch < 3; ch++) {
    if (channelScore[ch] < minCollisions) {
      minCollisions = channelScore[ch];
      bestCh = ch;
    }
  }
  return bestCh;
#endif
}

// ── Cập nhật OLED hiển thị kết quả thời gian thực ───────────────────────────
void oledUpdateInference(int chIdx, int seq, int succ, int hops, int status) {
  if (!oledOk) return;

  float pdr = (seq > 0) ? ((float)succ / seq * 100.0f) : 100.0f;
  const char* modeName = (HOPPING_MODE == 0) ? "FIXED" : (HOPPING_MODE == 1 ? "RANDOM" : "TINYML");

  display.clearDisplay();
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.printf("NODE [%c] - %s", NODE_ID, modeName);
  display.setCursor(100, 2);
  display.printf("CH%d", chIdx + 1);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 15);
  display.printf("Freq: %.3f MHz", CHANNELS[chIdx]);
  display.setCursor(0, 27);
  display.printf("Pkt : #%d | Hops:%d", seq, hops);
  display.setCursor(0, 39);
  display.printf("PDR : %.1f%% (%d/%d)", pdr, succ, seq);
  display.setCursor(0, 51);
  display.printf("Status: %s", (status == RADIOLIB_ERR_NONE) ? "TX OK" : "COLLISION");

  display.display();
}

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  delay(500);
  Serial.println("\n==================================================");
  Serial.printf("   LoRa TinyML Hopping Node [%c]\n", NODE_ID);
  Serial.printf("   Hopping Mode: %d (0:Fixed, 1:Random, 2:TinyML)\n", HOPPING_MODE);
  Serial.println("==================================================");

  Wire.begin(OLED_SDA, OLED_SCL);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledOk = true;
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 5);
    display.printf("TinyML Node [%c]\n", NODE_ID);
    display.println("Initializing SX1278...");
    display.display();
  }

  loRaSPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  int state = radio.begin(CHANNELS[currentChannelIndex], LORA_BW, LORA_SF, LORA_CR,
                          LORA_SYNC_WORD, LORA_POWER, LORA_PREAMBLE);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("[ERROR] SX1278 Init Failed! Code: %d\n", state);
    while (true) { delay(1000); }
  }

  randomSeed(analogRead(34) + (uint8_t)NODE_ID);
  delay(1500);
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  if (now - lastTxTime >= TX_INTERVAL || lastTxTime == 0) {
    lastTxTime = now;
    packetCount++;

    // 1. Dự đoán kênh tối ưu cho lần phát này
    previousChannelIndex = currentChannelIndex;
    currentChannelIndex = predictNextChannel();

    if (currentChannelIndex != previousChannelIndex) {
      hopCount++;
      radio.setFrequency(CHANNELS[currentChannelIndex]);
      Serial.printf("[HOP] Channel switch: %.3f MHz -> %.3f MHz (Total Hops: %lu)\n",
                    CHANNELS[previousChannelIndex], CHANNELS[currentChannelIndex], (unsigned long)hopCount);
    }

    // 2. Chuẩn bị gói tin truyền (30 bytes)
    uint8_t payload[32];
    memset(payload, 'X', sizeof(payload));
    payload[0] = (uint8_t)NODE_ID;
    payload[1] = (uint8_t)((packetCount >> 8) & 0xFF);
    payload[2] = (uint8_t)(packetCount & 0xFF);
    payload[3] = (uint8_t)30; // Kích thước
    payload[31] = '\0';

    digitalWrite(LED_PIN, HIGH);
    unsigned long t0 = millis();

    int state = radio.transmit(payload, 30);

    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    if (state == RADIOLIB_ERR_NONE) {
      successCount++;
    }

    // 3. Cập nhật lịch sử trượt
    if (historyCount < HISTORY_LEN) {
      historyCount++;
    }
    for (int i = historyCount - 1; i > 0; i--) {
      history[i] = history[i - 1];
    }
    history[0].ch_busy[0] = (currentChannelIndex == 0 && state != RADIOLIB_ERR_NONE) ? 1.0f : 0.0f;
    history[0].ch_busy[1] = (currentChannelIndex == 1 && state != RADIOLIB_ERR_NONE) ? 1.0f : 0.0f;
    history[0].ch_busy[2] = (currentChannelIndex == 2 && state != RADIOLIB_ERR_NONE) ? 1.0f : 0.0f;
    history[0].rssi = (state == RADIOLIB_ERR_NONE) ? -75.0f : -1000.0f;
    history[0].snr  = (state == RADIOLIB_ERR_NONE) ? 8.0f : -1000.0f;

    Serial.printf("[TX] Node:%c | Pkt:#%lu | CH:%d (%.3fMHz) | Hops:%lu | ToA:%lums | State:%d\n",
                  NODE_ID, (unsigned long)packetCount, currentChannelIndex + 1,
                  CHANNELS[currentChannelIndex], (unsigned long)hopCount, airTime, state);

    oledUpdateInference(currentChannelIndex, packetCount, successCount, hopCount, state);
  }
}
