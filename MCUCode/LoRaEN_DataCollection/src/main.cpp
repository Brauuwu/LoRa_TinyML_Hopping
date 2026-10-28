/*
 * LoRa End-Node Data Collection - Firmware Thực Nghiệm Thu Thập Dữ Liệu
 * -------------------------------------------------------------------------
 * Đề tài: Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML
 * Phần cứng: ESP32 DevKit V1 + Module LoRa Ra-02 (SX1278 433MHz) + OLED SSD1306
 *
 * TÍNH NĂNG TƯƠNG TÁC WEBSERVER GATEWAY:
 *   1. Nhận lệnh kích hoạt Downlink: Phát lẻ từng Node, 2 Node cùng lúc, hoặc Tất cả.
 *   2. Cấu hình tần số từ xa qua sóng vô tuyến (OTA Frequency Config).
 *   3. Phản hồi Ping kiểm tra trạng thái Online / Offline tức thời về Gateway.
 *   4. Nhận lệnh Dừng / Reset (CMD:STOP) ngay cả khi đang trong tiến trình phát.
 *   5. Các bản tin điều khiển (Ping, Config, Command) có tiền tố "CTRL:" để
 *      Gateway phân loại và LOẠI BỎ khỏi tập dữ liệu thu thập (CSV/TXT).
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
#define NODE_ID             'C'   // 'A', 'B', hoặc 'C'

// ═══════════════════════════════════════════════════════════════════════════
// 2. CẤU HÌNH TẦN SỐ KHỞI ĐỘNG MẶC ĐỊNH (DEFAULT STARTUP FREQUENCY)
//    1: Kênh 1 - 433.175 MHz
//    2: Kênh 2 - 433.375 MHz
//    3: Kênh 3 - 433.575 MHz
// Có thể thay đổi động từ xa qua giao diện Web Gateway (OTA Frequency Tuning)
// ═══════════════════════════════════════════════════════════════════════════
#define SELECTED_CHANNEL_NUM  1   // Đặt 1, 2, hoặc 3 mặc định khi mới cấp điện

// Bảng tra cứu tần số theo số kênh
const float CHANNELS[3] = {433.175, 433.375, 433.575};
float currentFrequency = CHANNELS[SELECTED_CHANNEL_NUM - 1];
int currentChannelNum = SELECTED_CHANNEL_NUM;

// ═══════════════════════════════════════════════════════════════════════════
// 3. THIẾT LẬP KỊCH BẢN PHÁT GÓI TIN DỮ LIỆU (TRAFFIC SCENARIO)
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

// ── Chân nút bấm BOOT tích hợp trên ESP32 (để kích hoạt thủ công khi cần) ───
#define BOOT_PIN              0

// ── Định nghĩa các trạng thái hoạt động của End-Node ────────────────────────
enum NodeState {
  STATE_WAIT_CMD,     // Chờ lệnh START từ Gateway (hoặc bấm nút BOOT)
  STATE_TRANSMITTING, // Đang phát dữ liệu theo kịch bản (600 gói)
  STATE_FINISHED      // Đã hoàn thành 600 gói, dừng hẳn
};

NodeState nodeState = STATE_WAIT_CMD;

// ── Biến điều khiển tiến trình phát ─────────────────────────────────────────
int sizeIndex = 0;              // Chỉ số kích thước payload hiện tại (0..5)
uint32_t packetCount = 0;       // Đếm số gói đã phát của kích thước hiện tại (0..99)
uint32_t totalPacketsSent = 0;  // Tổng số gói đã phát trên toàn bộ tiến trình (tối đa 600)
unsigned long lastTxTime = 0;
unsigned long currentInterval = TX_BASE_INTERVAL_MS;

// ── Đối tượng phần cứng ─────────────────────────────────────────────────────
SPIClass loRaSPI(VSPI);
SX1278 radio = new Module(LORA_NSS, LORA_DIO0, LORA_RST, RADIOLIB_NC, loRaSPI);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool oledOk = false;

// ── Cờ ngắt nhận gói tin LoRa từ DIO0 ───────────────────────────────────────
volatile bool g_rxFlag = false;

#if defined(ESP8266) || defined(ESP32)
  ICACHE_RAM_ATTR
#endif
void onDio0Interrupt() {
  g_rxFlag = true;
}

// ── Hàm hiển thị màn hình OLED khi ĐANG CHỜ LỆNH TỪ GATEWAY ─────────────────
void oledShowWaitingCommand(int dotCount) {
  if (!oledOk) return;

  display.clearDisplay();
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.printf("NODE [%c] - CHO LENH", NODE_ID);
  display.setCursor(95, 2);
  display.printf("CH%d", currentChannelNum);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 15);
  display.printf("Freq: %.3f MHz", currentFrequency);
  display.setCursor(0, 27);
  display.print("Trang thai: Cho GW");
  for (int i = 0; i < (dotCount % 4); i++) display.print(".");

  display.setCursor(0, 40);
  display.print(">> CHO LENH START <<");
  display.setCursor(0, 52);
  display.print("Hoac bam nut BOOT");
  display.display();
}

// ── Hàm hiển thị màn hình OLED khi NHẬN ĐƯỢC LỆNH KÍCH HOẠT ────────────────
void oledShowTriggered(const char* cmdText) {
  if (!oledOk) return;

  display.clearDisplay();
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(4, 2);
  display.printf("NODE [%c] - KICH HOAT!", NODE_ID);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 18);
  display.printf("Lenh: %s", cmdText);
  display.setCursor(0, 32);
  display.print("Khoi dong 600 goi...");
  display.setCursor(0, 46);
  display.printf("Kenh: %.3f MHz", currentFrequency);
  display.display();
}

// ── Hàm hiển thị màn hình OLED khi CẬP NHẬT TẦN SỐ OTA ──────────────────────
void oledShowConfigUpdated(float newFreq, int chNum) {
  if (!oledOk) return;

  display.clearDisplay();
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(4, 2);
  display.printf("NODE [%c] - OTA CONFIG", NODE_ID);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 18);
  display.print("Tan so moi thanh cong:");
  display.setCursor(0, 32);
  display.printf("%.3f MHz (CH%d)", newFreq, chNum);
  display.setCursor(0, 48);
  display.print("STABLE CONFIRMED OK");
  display.display();
}

// ── Hàm cập nhật màn hình OLED trong quá trình phát ─────────────────────────
void oledUpdateProgress(int seq, int pSize, int status, unsigned long airTime) {
  if (!oledOk) return;

  display.clearDisplay();
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.printf("NODE [%c] - RUNNING", NODE_ID);
  display.setCursor(95, 2);
  display.printf("CH%d", currentChannelNum);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 15);
  display.printf("Freq: %.3f MHz", currentFrequency);
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
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(4, 2);
  display.printf("NODE [%c] - HOAN THANH", NODE_ID);

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 16);
  display.printf("Freq : %.3f MHz (CH%d)", currentFrequency, currentChannelNum);
  display.setCursor(0, 28);
  display.printf("Tong : %u/600 Pkts", totalPacketsSent);
  display.setCursor(0, 40);
  display.print("Du 6 Sizes (30->250B)");
  display.setCursor(0, 52);
  display.print(">> DA DUNG PHAT <<");
  display.display();
}

// ── Hàm gửi phản hồi bản tin điều khiển tới Gateway ─────────────────────────
// Ghi chú: Mọi bản tin điều khiển có tiền tố "CTRL:" để Gateway phân loại
// và TUYỆT ĐỐI LOẠI BỎ khỏi tập dữ liệu thu thập (CSV & TXT).
void sendControlResponse(const String& ctrlMsg) {
  digitalWrite(LED_PIN, HIGH);
  radio.standby();
  delay(10);
  radio.transmit((uint8_t*)ctrlMsg.c_str(), ctrlMsg.length());
  digitalWrite(LED_PIN, LOW);
  delay(10);
  radio.startReceive();
  Serial.printf("[CTRL TX] Đã gửi phản hồi: \"%s\"\n", ctrlMsg.c_str());
}

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(BOOT_PIN, INPUT_PULLUP); // Nút BOOT kích hoạt thủ công

  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("   LORA END-NODE - DATA COLLECTION TRAFFIC GENERATOR");
  Serial.printf("   Node ID       : [%c]\n", NODE_ID);
  Serial.printf("   Tần số mặc định: %.3f MHz (Kênh %d)\n", currentFrequency, currentChannelNum);
  Serial.printf("   Số gói/mức    : %d gói tin\n", SAMPLES_PER_BURST);
  Serial.printf("   Tổng số gói   : %d mức x %d = %d gói tin\n", NUM_SIZES, SAMPLES_PER_BURST, NUM_SIZES * SAMPLES_PER_BURST);
  Serial.println("   CHẾ ĐỘ        : ĐANG CHỜ LỆNH TỪ WEBSERVER GATEWAY...");
  Serial.println("==================================================");

  // Khởi động I2C & OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledOk = true;
    oledShowWaitingCommand(0);
  }

  // Khởi tạo SPI & LoRa Radio SX1278 trên tần số ban đầu
  loRaSPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  Serial.printf("[INIT] Đang khởi động SX1278 trên tần số %.3f MHz...\n", currentFrequency);

  int state = radio.begin(currentFrequency, LORA_BW, LORA_SF, LORA_CR,
                          LORA_SYNC_WORD, LORA_POWER, LORA_PREAMBLE);
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("[INIT] SX1278 Khởi tạo THÀNH CÔNG!");
    // Đăng ký ngắt DIO0 và bắt đầu lắng nghe Downlink
    radio.setPacketReceivedAction(onDio0Interrupt);
    int rxState = radio.startReceive();
    if (rxState == RADIOLIB_ERR_NONE) {
      Serial.println("[INIT] Đang lắng nghe Downlink trên kênh...");
    } else {
      Serial.printf("[WARN] startReceive trả về mã: %d\n", rxState);
    }
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
  delay(500);

  Serial.println();
  Serial.println("[READY] Node đã sẵn sàng ở chế độ CHỜ LỆNH...");
}

// ── Hàm kiểm tra đích đến của lệnh Downlink ─────────────────────────────────
// targetStr: "ALL", "A", "B", "C", "A,B", "B,C", "A_B", "A+B", v.v.
static bool isTargetMatched(String targetStr, char myNodeId) {
  targetStr.trim();
  targetStr.toUpperCase();
  if (targetStr.length() == 0 || targetStr == "ALL" || targetStr == "*") {
    return true;
  }
  for (unsigned int i = 0; i < targetStr.length(); i++) {
    char c = targetStr.charAt(i);
    if (c == myNodeId) {
      return true;
    }
  }
  return false;
}

// ── Hàm xử lý toàn diện các gói tin Downlink từ Gateway ─────────────────────
// Trả về true nếu lệnh yêu cầu chuyển sang phát dữ liệu (START)
bool handleDownlinkPacket(const String& rxData, String& cmdReceived) {
  String rxClean = rxData;
  rxClean.trim();
  String rxUpper = rxClean;
  rxUpper.toUpperCase();

  // 0. BẢO VỆ CHỐNG DỘI / VÒNG LẶP ECHO:
  // Nếu gói tin là bản tin phản hồi từ Node khác (bắt đầu bằng "CTRL:") hoặc là gói dữ liệu (chứa ký tự phân tách '*')
  // thì bỏ qua ngay lập tức, TUYỆT ĐỐI không xử lý như lệnh Downlink từ Gateway!
  if (rxUpper.startsWith("CTRL:") || rxUpper.indexOf('*') >= 0) {
    return false;
  }

  float rssi = radio.getRSSI();
  float snr = radio.getSNR();
  Serial.println();
  Serial.printf("[RX DOWNLINK] \"%s\" (RSSI: %.1f dBm, SNR: %.1f dB)\n", rxData.c_str(), rssi, snr);

  // Chuẩn hóa loại bỏ tiền tố "CMD:" nếu có để tránh nhầm chữ 'C' trong "CMD"
  String payload = rxUpper;
  if (payload.startsWith("CMD:")) {
    payload = payload.substring(4);
    payload.trim();
  }

  // 1. XỬ LÝ LỆNH PING (KIỂM TRA TRẠNG THÁI ONLINE / OFFLINE)
  // Cú pháp: "CMD:PING:ALL", "CMD:PING:A", "PING:B", "PING"
  if (payload.startsWith("PING")) {
    String target = "ALL";
    int colon = payload.indexOf(':');
    if (colon >= 0) {
      target = payload.substring(colon + 1);
    }
    if (isTargetMatched(target, NODE_ID)) {
      String stateStr = (nodeState == STATE_WAIT_CMD) ? "WAIT" :
                        (nodeState == STATE_TRANSMITTING) ? "TX" : "DONE";
      // Phản hồi: CTRL:PONG:<NODE_ID>:<CHANNEL>:<FREQ>:<STATE>
      char pongMsg[64];
      snprintf(pongMsg, sizeof(pongMsg), "CTRL:PONG:%c:%d:%.3f:%s",
               NODE_ID, currentChannelNum, currentFrequency, stateStr.c_str());
      delay(random(20, 100)); // Tránh xung đột nếu nhiều node cùng trả lời
      sendControlResponse(pongMsg);
    }
    return false;
  }

  // 2. XỬ LÝ LỆNH CẤU HÌNH TẦN SỐ OTA (OTA FREQUENCY CONFIGURATION)
  // Cú pháp: "CMD:CFG:<NODE>:<FREQ>" (Ví dụ: "CMD:CFG:A:433.175" hoặc "CMD:CFG:ALL:433.375")
  if (payload.startsWith("CFG:")) {
    int firstColon = payload.indexOf(':');
    int secondColon = payload.indexOf(':', firstColon + 1);
    if (firstColon >= 0 && secondColon > firstColon) {
      String targetNode = payload.substring(firstColon + 1, secondColon);
      String freqStr = payload.substring(secondColon + 1);
      float newFreq = freqStr.toFloat();

      if (isTargetMatched(targetNode, NODE_ID) && newFreq > 400.0 && newFreq < 450.0) {
        Serial.printf("[OTA] Nhận yêu cầu đổi tần số sang %.3f MHz...\n", newFreq);

        // Cập nhật phần cứng SX1278
        radio.standby();
        int res = radio.setFrequency(newFreq);
        if (res == RADIOLIB_ERR_NONE) {
          currentFrequency = newFreq;
          if (fabs(newFreq - 433.175) < 0.05) currentChannelNum = 1;
          else if (fabs(newFreq - 433.375) < 0.05) currentChannelNum = 2;
          else if (fabs(newFreq - 433.575) < 0.05) currentChannelNum = 3;

          oledShowConfigUpdated(currentFrequency, currentChannelNum);

          // Gửi xác nhận cấu hình ổn định về Gateway
          // Định dạng: CTRL:ACK:CFG:<NODE>:<FREQ>
          char ackMsg[64];
          snprintf(ackMsg, sizeof(ackMsg), "CTRL:ACK:CFG:%c:%.3f", NODE_ID, currentFrequency);
          delay(50);
          sendControlResponse(ackMsg);

          delay(1500);
          if (nodeState == STATE_WAIT_CMD) oledShowWaitingCommand(0);
        } else {
          Serial.printf("[OTA FAIL] Không thể thiết lập tần số! Mã lỗi: %d\n", res);
        }
      }
    }
    return false;
  }

  // 3. XỬ LÝ LỆNH DỪNG / RESET (CMD:STOP / CMD:RESET)
  // Cú pháp: "CMD:STOP:ALL" hoặc "CMD:STOP:A", "CMD:STOP:A,B"
  if (payload.startsWith("STOP") || payload.startsWith("RESET")) {
    String target = "ALL";
    int colon = payload.indexOf(':');
    if (colon >= 0) {
      target = payload.substring(colon + 1);
    }
    if (isTargetMatched(target, NODE_ID)) {
      static unsigned long lastAckStopTime = 0;
      bool wasRunning = (nodeState != STATE_WAIT_CMD);

      nodeState = STATE_WAIT_CMD;
      packetCount = 0;
      sizeIndex = 0;
      totalPacketsSent = 0;
      lastTxTime = 0;
      oledShowWaitingCommand(0);

      // Chống spam: Chỉ gửi ACK nếu Node đang chạy hoặc lần gửi gần nhất cách đây > 2.0s
      if (wasRunning || millis() - lastAckStopTime > 2000) {
        lastAckStopTime = millis();
        Serial.println("[DOWNLINK] >>> NHẬN LỆNH DỪNG/RESET TỪ GATEWAY! <<<");
        char ackStop[64];
        snprintf(ackStop, sizeof(ackStop), "CTRL:ACK:STOP:%c", NODE_ID);
        delay(random(30, 100)); // Tránh xung đột nếu nhiều node cùng phản hồi
        sendControlResponse(ackStop);
      }
    }
    return false;
  }

  // 4. XỬ LÝ LỆNH PHÁT (CMD:START)
  // Cú pháp hỗ trợ:
  //   - "CMD:START:ALL"        -> Tất cả các Node phát
  //   - "CMD:START:A"          -> Chỉ Node A phát
  //   - "CMD:START:B"          -> Chỉ Node B phát
  //   - "CMD:START:C"          -> Chỉ Node C phát
  //   - "CMD:START:A,B"        -> Đồng thời Node A và Node B phát
  //   - "CMD:START:B,C"        -> Đồng thời Node B và Node C phát
  //   - "CMD:START:A,C"        -> Đồng thời Node A và Node C phát
  //   - "START"                -> Mặc định phát tất cả
  if (payload.startsWith("START")) {
    String target = "ALL";
    int colon = payload.indexOf(':');
    if (colon >= 0) {
      target = payload.substring(colon + 1);
      target.trim();
    }

    if (isTargetMatched(target, NODE_ID)) {
      cmdReceived = (target == "ALL" || target == "*") ? "START:ALL" : (String("START:") + NODE_ID);
      Serial.printf("[DOWNLINK] >>> KHỚP ĐÍCH ĐẾN! Node [%c] được yêu cầu phát (target='%s') <<<\n",
                    NODE_ID, target.c_str());

      // Gửi xác nhận bắt đầu về Gateway
      char ackStart[64];
      snprintf(ackStart, sizeof(ackStart), "CTRL:ACK:START:%c", NODE_ID);
      sendControlResponse(ackStart);
      return true; // Kích hoạt phát dữ liệu
    } else {
      Serial.printf("[DOWNLINK] Lệnh START cho Node khác (target='%s'), Node [%c] KHÔNG phát.\n",
                    target.c_str(), NODE_ID);
      return false;
    }
  }

  return false;
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  // TRƯỜNG HỢP 1: ĐÃ HOÀN THÀNH TOÀN BỘ 600 GÓI TIN
  if (nodeState == STATE_FINISHED) {
    digitalWrite(LED_PIN, LOW);

    // Vẫn lắng nghe Downlink để người dùng có thể bấm [RESET / PHÁT LẠI] từ Web Gateway
    if (g_rxFlag || digitalRead(LORA_DIO0) == HIGH) {
      g_rxFlag = false;
      String rxData;
      int rxState = radio.readData(rxData);
      if (rxState == RADIOLIB_ERR_NONE && rxData.length() > 0) {
        String cmdReceived = "";
        if (handleDownlinkPacket(rxData, cmdReceived)) {
          nodeState = STATE_TRANSMITTING;
          lastTxTime = 0;
          packetCount = 0;
          sizeIndex = 0;
          totalPacketsSent = 0;
          oledShowTriggered(cmdReceived.c_str());
          return;
        }
      }
      radio.startReceive();
    }
    delay(200);
    return;
  }

  // TRƯỜNG HỢP 2: ĐANG CHỜ LỆNH TỪ WEBSERVER GATEWAY HOẶC NÚT BOOT
  if (nodeState == STATE_WAIT_CMD) {
    bool triggered = false;
    String cmdReceived = "";

    // A. Kiểm tra nếu có cờ ngắt DIO0 hoặc chân DIO0 lên mức HIGH (có gói tin đến)
    if (g_rxFlag || digitalRead(LORA_DIO0) == HIGH) {
      g_rxFlag = false;

      String rxData;
      int rxState = radio.readData(rxData);

      if (rxState == RADIOLIB_ERR_NONE && rxData.length() > 0) {
        if (handleDownlinkPacket(rxData, cmdReceived)) {
          triggered = true;
        }
      } else {
        Serial.printf("[RX LORA] Lỗi đọc gói tin (Code: %d)\n", rxState);
      }

      // Nếu chưa kích hoạt, tiếp tục đưa SX1278 vào chế độ nhận
      if (!triggered) {
        radio.startReceive();
      }
    }

    // B. Kiểm tra nút nhấn BOOT (GPIO 0) để phát thủ công khi không có Gateway
    if (!triggered && digitalRead(BOOT_PIN) == LOW) {
      delay(50); // Chống dội
      if (digitalRead(BOOT_PIN) == LOW) {
        Serial.println("[MANUAL] >>> Nút BOOT được nhấn! Kích hoạt phát thủ công. <<<");
        triggered = true;
        cmdReceived = "NUT BOOT";
        while (digitalRead(BOOT_PIN) == LOW) delay(10); // Chờ nhả nút
      }
    }

    // C. Nếu nhận được lệnh kích hoạt: Bắt đầu phát dữ liệu
    if (triggered) {
      radio.standby();

      Serial.println();
      Serial.println("==================================================");
      Serial.printf(" >>> [KÍCH HOẠT THÀNH CÔNG] Node [%c] BẮT ĐẦU PHÁT DỮ LIỆU! <<<\n", NODE_ID);
      Serial.printf(" Nguồn kích hoạt : %s\n", cmdReceived.c_str());
      Serial.printf(" Tần số làm việc : %.3f MHz (Kênh %d)\n", currentFrequency, currentChannelNum);
      Serial.println("==================================================");

      oledShowTriggered(cmdReceived.c_str());

      // Nháy LED 3 lần báo hiệu nhận lệnh
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH); delay(80);
        digitalWrite(LED_PIN, LOW);  delay(80);
      }
      delay(500);

      // Chuyển sang trạng thái phát dữ liệu
      nodeState = STATE_TRANSMITTING;
      lastTxTime = 0; // Để phát ngay gói đầu tiên
      packetCount = 0;
      sizeIndex = 0;
      totalPacketsSent = 0;
      return;
    }

    // Watchdog định kỳ 2.0 giây: Re-arm chế độ nhận để đảm bảo SX1278 không bao giờ bị treo ở Standby
    static unsigned long lastRxWatchdog = 0;
    if (millis() - lastRxWatchdog >= 2000) {
      lastRxWatchdog = millis();
      radio.startReceive();
    }

    // Hiệu ứng chờ lệnh trên màn hình OLED và nhấp nháy LED nhẹ
    static unsigned long lastWaitTime = 0;
    static int dotCount = 0;
    if (millis() - lastWaitTime >= 600) {
      lastWaitTime = millis();
      dotCount++;
      oledShowWaitingCommand(dotCount);

      if (dotCount % 2 == 0) {
        digitalWrite(LED_PIN, HIGH);
        delay(30);
        digitalWrite(LED_PIN, LOW);
      }
    }

    delay(20);
    return;
  }

  // TRƯỜNG HỢP 3: STATE_TRANSMITTING - ĐANG PHÁT DỮ LIỆU THU THẬP
  // Trong thời gian nghỉ giữa các gói, vẫn lắng nghe lệnh STOP/RESET từ Gateway!
  if (g_rxFlag || digitalRead(LORA_DIO0) == HIGH) {
    g_rxFlag = false;
    String rxData;
    int rxState = radio.readData(rxData);
    if (rxState == RADIOLIB_ERR_NONE && rxData.length() > 0) {
      String unusedCmd = "";
      handleDownlinkPacket(rxData, unusedCmd);
      if (nodeState != STATE_TRANSMITTING) {
        // Đã bị dừng bởi lệnh STOP từ Gateway
        return;
      }
    }
    radio.startReceive();
  }

  unsigned long now = millis();
  if (now - lastTxTime >= currentInterval || lastTxTime == 0) {
    lastTxTime = now;
    currentInterval = TX_BASE_INTERVAL_MS + random(0, TX_JITTER_MS);

    int currentPayloadSize = PAYLOAD_SIZES[sizeIndex];

    // Xây dựng gói tin ASCII theo đúng định dạng bài báo LoRaEdgeTinyML:
    // "<NODE_ID><packetCount>*<chuỗi chữ số ngẫu nhiên '0'..'9'>"
    char txBuffer[256];
    int headerLen = snprintf(txBuffer, sizeof(txBuffer), "%c%u*", NODE_ID, packetCount);
    for (int i = headerLen; i < currentPayloadSize; i++) {
      txBuffer[i] = (char)random(48, 58);
    }
    txBuffer[currentPayloadSize] = '\0';

    digitalWrite(LED_PIN, HIGH);
    radio.standby();
    unsigned long t0 = millis();

    int state = radio.transmit((uint8_t*)txBuffer, currentPayloadSize);

    unsigned long airTime = millis() - t0;
    digitalWrite(LED_PIN, LOW);

    // Ngay sau khi truyền xong, chuyển lại sang chế độ nhận để bắt lệnh STOP nếu có
    radio.startReceive();

    totalPacketsSent++;

    Serial.printf("NODE:%c | FREQ:%.3fMHz | SIZE:%3dB (%d/%d) | PKT:#%02u/%d | TOTAL:%3u/600 | ToA:%lums | Result:%d | DATA:\"%s\"\n",
                  NODE_ID, currentFrequency, currentPayloadSize, sizeIndex + 1, NUM_SIZES,
                  packetCount, SAMPLES_PER_BURST, totalPacketsSent, airTime, state, txBuffer);

    oledUpdateProgress(packetCount, currentPayloadSize, state, airTime);

    packetCount++;

    if (packetCount >= SAMPLES_PER_BURST) {
      packetCount = 0;
      sizeIndex++;

      // KIỂM TRA ĐÃ GỬI XONG MỨC KÍCH THƯỚC CUỐI CÙNG CHƯA (250 BYTES)
      if (sizeIndex >= NUM_SIZES) {
        nodeState = STATE_FINISHED;

        Serial.println();
        Serial.println("==================================================");
        Serial.printf(" >>> [HOÀN THÀNH KỊCH BẢN] Node [%c] ĐÃ PHÁT ĐỦ %u GÓI TIN! <<<\n", NODE_ID, totalPacketsSent);
        Serial.printf(" Tần số làm việc : %.3f MHz (Kênh %d)\n", currentFrequency, currentChannelNum);
        Serial.printf(" Chi tiết        : 6 mức kích thước (30B -> 250B) x %d gói\n", SAMPLES_PER_BURST);
        Serial.println(" >>> NODE ĐÃ HOÀN THÀNH VÀ DỪNG PHÁT DỮ LIỆU! <<<");
        Serial.println(" (Tiếp tục lắng nghe lệnh RESET/START mới từ Web Gateway)");
        Serial.println("==================================================");

        oledShowFinished();
        return;
      }

      Serial.println();
      Serial.println("--------------------------------------------------");
      Serial.printf("[TIẾN TRÌNH] Chuyển sang kích thước tiếp theo: %d bytes (100 gói)...\n",
                    PAYLOAD_SIZES[sizeIndex]);
      Serial.println("--------------------------------------------------");
      delay(2000);
    }
  }
}
