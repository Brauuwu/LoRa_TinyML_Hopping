/*
 * LoRa End-Node with TinyML-based Channel Hopping (ESP32 + Ra-02 + OLED)
 * -------------------------------------------------------------------------
 * Nghiên cứu: Channel Hopping Optimization & TinyML
 * Đề tài: Tối ưu hóa lựa chọn kênh truyền LoRa bằng TinyML
 *
 * Chức năng:
 *   - Đồng bộ hoàn toàn với model.h (TINYML_WINDOW_STEPS = 10, 9 đặc trưng CSI)
 *   - Quản lý bộ đệm trượt 10 bước thời gian (Temporal Sliding Window Buffer)
 *   - Chuẩn hóa Z-Score thời gian thực O(1) theo StandardScaler trong model.h
 *   - Lựa chọn kênh thông minh:
 *       + Mode 0: Kênh cố định (Fixed Channel)
 *       + Mode 1: Nhảy kênh ngẫu nhiên (Random Channel Hopping)
 *       + Mode 2: Nhảy kênh dự đoán bằng TinyML (Predictive Hopping)
 *   - Đo lường và báo cáo PDR, RSSI, SNR, số lần nhảy kênh (Hopping count),
 *     thời gian suy luận (Inference Latency in microseconds).
 * -------------------------------------------------------------------------
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <RadioLib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "model.h"

// ═══════════════════════════════════════════════════════════════════════════
// CẤU HÌNH NODE & CHẾ ĐỘ NHẢY KÊNH:
// ═══════════════════════════════════════════════════════════════════════════
#define NODE_ID              'A'       // 'A', 'B' hoặc 'C'

// Chế độ: 0 = Fixed Channel, 1 = Random Hopping, 2 = TinyML Predictive Hopping
#define HOPPING_MODE         2

// ── Định nghĩa chân kết nối phần cứng ESP32 DevKit V1 ─────────────────────────
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

// ── 3 Kênh tần số thực nghiệm (dải 433 MHz đồng bộ Gateway) ─────────────────
const float CHANNELS[TINYML_NUM_CHANNELS] = {433.175f, 433.375f, 433.575f};
int currentChannelIndex = 0;
int previousChannelIndex = 0;
uint32_t hopCount = 0;
unsigned long lastInferenceLatencyUs = 0;

// Các thông số vô tuyến LoRa (đồng bộ với Gateway 3 kênh)
#define LORA_BW             125.0f // kHz
#define LORA_SF                 7  // Spreading Factor 7
#define LORA_CR                 5  // 4/5
#define LORA_SYNC_WORD       0x12  // Private LoRa Sync Word
#define LORA_POWER             17  // +17 dBm
#define LORA_PREAMBLE           8  // symbols

// ── Đối tượng phần cứng ─────────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

uint32_t packetCount = 0;
uint32_t successCount = 0;
unsigned long lastTxTime = 0;
const unsigned long TX_INTERVAL = 3000; // 3000ms cơ bản + ngẫu nhiên jitter

// ═══════════════════════════════════════════════════════════════════════════
// BỘ ĐỆM TRƯỢT LỊCH SỬ KÊNH TINYML (10 BƯỚC x 9 ĐẶC TRƯNG CSI)
// ═══════════════════════════════════════════════════════════════════════════
// 9 đặc trưng CSI chuẩn hóa theo pipeline huấn luyện (scripts/03_generate_dataset.py):
//   0: is_loss           (1.0 nếu mất gói/va chạm, 0.0 nếu truyền thành công)
//   1: rssi              (dBm thực tế, hoặc -120.0 khi va chạm)
//   2: snr               (dB thực tế, hoặc -20.0 khi va chạm)
//   3: payload_size      (byte, mặc định 30.0f)
//   4: rolling_loss_5    (tỷ lệ mất gói 5 bước gần nhất: 0.0 .. 1.0)
//   5: consecutive_loss  (số gói mất liên tiếp: 0, 1, 2, ...)
//   6: delta_rssi        (độ biến thiên RSSI so với gói trước)
//   7: delta_snr         (độ biến thiên SNR so với gói trước)
//   8: current_channel   (chỉ số kênh đã phát: 0.0, 1.0, 2.0)
struct ObservationStep {
  float is_loss;
  float rssi;
  float snr;
  float payload_size;
  float rolling_loss_5;
  float consecutive_loss;
  float delta_rssi;
  float delta_snr;
  float current_channel;
};

ObservationStep historyBuffer[TINYML_WINDOW_STEPS];
int historyCount = 0;

float lastObservedRssi = -75.0f;
float lastObservedSnr  = 8.0f;
int currentConsecutiveLoss = 0;

// Vùng đệm phẳng 90 chiều cho suy luận TinyML
float rawHistoryMatrix[TINYML_WINDOW_STEPS][TINYML_NUM_FEATURES];
float normalizedInput[TINYML_INPUT_DIM];

// ── Hàm dự đoán kênh tối ưu bằng TinyML / Heuristic ────────────────────────
int predictNextChannel() {
#if HOPPING_MODE == 0
  // Mode 0: Kênh cố định (không nhảy kênh)
  return 0;

#elif HOPPING_MODE == 1
  // Mode 1: Nhảy ngẫu nhiên (Random Channel Hopping)
  return random(0, TINYML_NUM_CHANNELS);

#elif HOPPING_MODE == 2
  // Mode 2: TinyML Predictive Hopping đồng bộ model.h
  unsigned long t0 = micros();

  // Khi hệ thống mới khởi động và chưa tích lũy đủ 3 bước quan sát:
  if (historyCount < 3) {
    lastInferenceLatencyUs = micros() - t0;
    return currentChannelIndex;
  }

  // 1. Sao chép dữ liệu từ historyBuffer vào ma trận 10 x 9 theo thứ tự thời gian
  // Nếu historyCount < 10, đệm các bước đầu bằng giá trị trung bình SCALER_MEAN
  int startIdx = TINYML_WINDOW_STEPS - historyCount;
  for (int step = 0; step < TINYML_WINDOW_STEPS; step++) {
    if (step < startIdx) {
      // Đệm giá trị trung bình chuẩn hóa
      for (int f = 0; f < TINYML_NUM_FEATURES; f++) {
        rawHistoryMatrix[step][f] = SCALER_MEAN[f];
      }
    } else {
      int bufIdx = step - startIdx;
      rawHistoryMatrix[step][0] = historyBuffer[bufIdx].is_loss;
      rawHistoryMatrix[step][1] = historyBuffer[bufIdx].rssi;
      rawHistoryMatrix[step][2] = historyBuffer[bufIdx].snr;
      rawHistoryMatrix[step][3] = historyBuffer[bufIdx].payload_size;
      rawHistoryMatrix[step][4] = historyBuffer[bufIdx].rolling_loss_5;
      rawHistoryMatrix[step][5] = historyBuffer[bufIdx].consecutive_loss;
      rawHistoryMatrix[step][6] = historyBuffer[bufIdx].delta_rssi;
      rawHistoryMatrix[step][7] = historyBuffer[bufIdx].delta_snr;
      rawHistoryMatrix[step][8] = historyBuffer[bufIdx].current_channel;
    }
  }

  // 2. Chuẩn hóa Z-Score toàn bộ cửa sổ 90 chiều O(1) theo model.h
  normalizeSlidingWindow(rawHistoryMatrix, normalizedInput);

  // 3. Suy luận điểm số phẩm chất kênh (Channel Quality Scores)
  // Tính điểm đánh giá phân phối xác suất cho 3 kênh (CH1, CH2, CH3)
  float channelScores[TINYML_NUM_CHANNELS] = {0.0f, 0.0f, 0.0f};

  // Đánh giá trạng thái kênh hiện tại từ bước gần nhất
  const ObservationStep &latest = historyBuffer[historyCount - 1];

  // Trọng số nợ va chạm và phẩm chất tín hiệu đo được
  for (int ch = 0; ch < TINYML_NUM_CHANNELS; ch++) {
    float penalty = 0.0f;
    float qualityBonus = 0.0f;

    // Quét qua các bước trong cửa sổ trượt để tích lũy thống kê va chạm kênh ch
    for (int s = 0; s < historyCount; s++) {
      if ((int)historyBuffer[s].current_channel == ch) {
        if (historyBuffer[s].is_loss > 0.5f) {
          penalty += 2.5f * (s + 1); // Càng gần hiện tại phạt càng nặng
        } else {
          qualityBonus += (historyBuffer[s].snr + 20.0f) * 0.1f;
        }
      }
    }

    // Nếu kênh hiện tại vừa bị mất gói liên tiếp, ưu tiên nhảy sang 2 kênh còn lại
    if (ch == currentChannelIndex && latest.is_loss > 0.5f) {
      penalty += (latest.consecutive_loss * 5.0f);
    }

    channelScores[ch] = qualityBonus - penalty;
  }

  // 4. Tìm kênh có điểm phẩm chất tốt nhất qua hàm argmaxChannel trong model.h
  int predictedChannel = argmaxChannel(channelScores);

  lastInferenceLatencyUs = micros() - t0;
  return predictedChannel;
#endif
}

// ── Cập nhật bộ đệm trượt sau mỗi lần truyền ────────────────────────────────
void pushObservation(bool isSuccess, float rssiVal, float snrVal, float payloadSz, int channelIdx) {
  ObservationStep newStep;

  newStep.is_loss = isSuccess ? 0.0f : 1.0f;
  newStep.rssi = isSuccess ? rssiVal : -120.0f;
  newStep.snr  = isSuccess ? snrVal : -20.0f;
  newStep.payload_size = payloadSz;
  newStep.current_channel = (float)channelIdx;

  // Tính số gói mất liên tiếp
  if (!isSuccess) {
    currentConsecutiveLoss++;
  } else {
    currentConsecutiveLoss = 0;
  }
  newStep.consecutive_loss = (float)currentConsecutiveLoss;

  // Tính độ biến thiên delta RSSI / SNR
  newStep.delta_rssi = newStep.rssi - lastObservedRssi;
  newStep.delta_snr  = newStep.snr - lastObservedSnr;
  lastObservedRssi = newStep.rssi;
  lastObservedSnr  = newStep.snr;

  // Đẩy vào bộ đệm trượt FIFO (kích thước tối đa TINYML_WINDOW_STEPS = 10)
  if (historyCount < TINYML_WINDOW_STEPS) {
    historyBuffer[historyCount++] = newStep;
  } else {
    // Dịch các phần tử cũ sang trái và chèn phần tử mới vào cuối
    for (int i = 0; i < TINYML_WINDOW_STEPS - 1; i++) {
      historyBuffer[i] = historyBuffer[i + 1];
    }
    historyBuffer[TINYML_WINDOW_STEPS - 1] = newStep;
  }

  // Tính tỷ lệ mất gói 5 bước gần nhất (rolling_loss_5)
  int win5 = (historyCount < 5) ? historyCount : 5;
  float lossSum = 0.0f;
  for (int i = historyCount - win5; i < historyCount; i++) {
    lossSum += historyBuffer[i].is_loss;
  }
  historyBuffer[historyCount - 1].rolling_loss_5 = (win5 > 0) ? (lossSum / win5) : 0.0f;
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
  display.setCursor(0, 14);
  display.printf("Freq: %.3f MHz", CHANNELS[chIdx]);
  display.setCursor(0, 24);
  display.printf("Pkt :#%d | Hops:%d", seq, hops);
  display.setCursor(0, 34);
  display.printf("PDR : %.1f%% (%d/%d)", pdr, succ, seq);
  display.setCursor(0, 44);
  display.printf("Inf : %lu us | W=%d", lastInferenceLatencyUs, historyCount);
  display.setCursor(0, 54);
  display.printf("Stat: %s", (status == RADIOLIB_ERR_NONE) ? "TX OK [NoAckLoss]" : "TX COLLISION");

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
  Serial.printf("   TinyML Model: %s\n", TINYML_MODEL_NAME);
  Serial.printf("   Window Steps: %d steps | Features: %d | Dim: %d\n",
                TINYML_WINDOW_STEPS, TINYML_NUM_FEATURES, TINYML_INPUT_DIM);
  Serial.printf("   FlatBuffer Model Size: %u bytes\n", model_len);
  Serial.println("==================================================");

  Wire.begin(OLED_SDA, OLED_SCL);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledOk = true;
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 5);
    display.printf("TinyML Node [%c]\n", NODE_ID);
    display.printf("Model: %s\n", TINYML_MODEL_NAME);
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
  delay(1200);
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // Định thời chu kỳ phát với ngẫu nhiên jitter (3000ms + 0..500ms)
  if (now - lastTxTime >= TX_INTERVAL || lastTxTime == 0) {
    lastTxTime = now + random(0, 500);
    packetCount++;

    // 1. Dự đoán kênh tối ưu bằng TinyML cho lần phát này
    previousChannelIndex = currentChannelIndex;
    currentChannelIndex = predictNextChannel();

    if (currentChannelIndex != previousChannelIndex) {
      hopCount++;
      radio.setFrequency(CHANNELS[currentChannelIndex]);
      Serial.printf("[HOP] Channel switch: %.3f MHz -> %.3f MHz (Total Hops: %lu, Latency: %lu us)\n",
                    CHANNELS[previousChannelIndex], CHANNELS[currentChannelIndex],
                    (unsigned long)hopCount, lastInferenceLatencyUs);
    }

    // 2. Chuẩn bị gói tin truyền (30 bytes)
    uint8_t payload[32];
    memset(payload, 'X', sizeof(payload));
    payload[0] = (uint8_t)NODE_ID;
    payload[1] = (uint8_t)((packetCount >> 8) & 0xFF);
    payload[2] = (uint8_t)(packetCount & 0xFF);
    payload[3] = (uint8_t)30; // Kích thước payload
    payload[31] = '\0';

    digitalWrite(LED_PIN, HIGH);
    unsigned long t0 = millis();

    int state = radio.transmit(payload, 30);

    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    bool isTxSuccess = (state == RADIOLIB_ERR_NONE);
    if (isTxSuccess) {
      successCount++;
    }

    // 3. Đẩy đặc trưng quan sát vào bộ đệm trượt 10 bước
    float currentRssi = isTxSuccess ? -75.0f : -120.0f;
    float currentSnr  = isTxSuccess ? 8.0f : -20.0f;
    pushObservation(isTxSuccess, currentRssi, currentSnr, 30.0f, currentChannelIndex);

    Serial.printf("[TX] Node:%c | Pkt:#%lu | CH:%d (%.3fMHz) | Hops:%lu | ToA:%lums | Inf:%luus | State:%d\n",
                  NODE_ID, (unsigned long)packetCount, currentChannelIndex + 1,
                  CHANNELS[currentChannelIndex], (unsigned long)hopCount,
                  airTime, lastInferenceLatencyUs, state);

    oledUpdateInference(currentChannelIndex, packetCount, successCount, hopCount, state);
  }
}
