# PHỤ LỤC

---

## Phụ Lục A: Sơ Đồ Phần Cứng Và Ánh Xạ Chân Tín Hiệu

### A.1. Sơ đồ kết nối phần cứng End-Node (ESP32 DevKit V1)
Hệ thống thiết bị đầu cuối End-Node sử dụng vi điều khiển ESP32 DevKit V1 (30 chân) kết nối trực tiếp với module thu phát sóng Semtech SX1278 (Ra-02 $433\text{ MHz}$) qua bus phần cứng VSPI và màn hình OLED SSD1306 ($0.96\text{ inch}$, $128 \times 64$) qua giao tiếp I2C.

```
                  SƠ ĐỒ NGUYÊN LÝ KẾT NỐI END-NODE ESP32
                  ┌─────────────────────────────────────┐
                  │          ESP32 DevKit V1            │
                  │        (Xtensa 32-bit LX6)          │
                  │                                     │
                  │  [VSPI]                             │
                  │   GPIO 27 (MOSI) ─────────> MOSI   │
                  │   GPIO 19 (MISO) <───────── MISO   │
                  │   GPIO 18 (SCK)  ─────────> SCK    │  Semtech SX1278
                  │   GPIO 5  (NSS)  ─────────> NSS    │  (Ai-Thinker Ra-02)
                  │   GPIO 14 (RST)  ─────────> RESET  │  Băng tần 433 MHz
                  │   GPIO 26 (DIO0) <───────── DIO0   │
                  │                                     │
                  │  [I2C - 400 kHz]                    │
                  │   GPIO 21 (SDA)  <=======> SDA     │  Màn hình OLED
                  │   GPIO 22 (SCL)  ─────────> SCL    │  SSD1306 0.96"
                  │                                     │
                  │  [Nguồn cấp 3.3V]                   │
                  │   3V3 ──────────────┬─────> VCC(RF)│  (Kèm mạch tụ lọc
                  │                     └─────> VCC(OL)│   100uF + 100nF)
                  │   GND ────────────────────> GND     │
                  └─────────────────────────────────────┘
```

*Bảng A.1: Bảng ánh xạ chân vi xử lý ESP32 với các khối ngoại vi*

| Chân ESP32 | Tên ngoại vi | Chân ngoại vi | Mức logic | Mô tả chức năng kỹ thuật |
| :---: | :---: | :---: | :---: | :--- |
| **GPIO 27** | SX1278 Ra-02 | **MOSI** | $3.3\text{V}$ | Tuyến dữ liệu Master-Out Slave-In của bus SPI |
| **GPIO 19** | SX1278 Ra-02 | **MISO** | $3.3\text{V}$ | Tuyến dữ liệu Master-In Slave-Out của bus SPI |
| **GPIO 18** | SX1278 Ra-02 | **SCK** | $3.3\text{V}$ | Xung đồng hồ SPI Serial Clock (Cấu hình $10\text{ MHz}$) |
| **GPIO 5** | SX1278 Ra-02 | **NSS (CS)** | Active Low | Chân chọn chip SPI (Kéo xuống $0\text{V}$ khi truyền nhận) |
| **GPIO 14** | SX1278 Ra-02 | **RESET** | Active Low | Chân reset cứng phần cứng của SX1278 |
| **GPIO 26** | SX1278 Ra-02 | **DIO0** | Ngắt cạnh lên | Ngắt ngoài báo hoàn tất phát gói tin (TxDone Interrupt) |
| **GPIO 21** | SSD1306 OLED | **SDA** | Open-Drain | Đường truyền dữ liệu bus I2C (I2C Fast Mode) |
| **GPIO 22** | SSD1306 OLED | **SCL** | Open-Drain | Đường truyền xung đồng hồ bus I2C |
| **3V3** | Ra-02 / OLED | **VCC** | $3.3\text{V DC}$ | Đường nguồn nuôi chính (Có hàn tụ bù chống sụt áp) |
| **GND** | Ra-02 / OLED | **GND** | $0\text{V}$ | Mặt phẳng nối đất chung toàn hệ thống |

---

### A.2. Sơ đồ kết nối phần cứng Multi-Channel Gateway (Raspberry Pi CM4)
Trạm Gateway sử dụng bo mạch Raspberry Pi Compute Module 4 (CM4) điều khiển đồng thời **03 module thu SX1278 độc lập** trên bus `SPI0` nhằm đạt tính năng thu song song không điểm mù (Zero-Blindness).

*Bảng A.2: Bảng ánh xạ chân Raspberry Pi CM4 với 3 module thu SX1278 độc lập*

| Chân vật lý RPi | Tên tín hiệu GPIO | Kết nối tới Module #1 (CH1 433.175 MHz) | Kết nối tới Module #2 (CH2 433.375 MHz) | Kết nối tới Module #3 (CH3 433.575 MHz) |
| :---: | :---: | :---: | :---: | :---: |
| **Pin 19** | **GPIO 10 (MOSI)** | MOSI | MOSI | MOSI |
| **Pin 21** | **GPIO 9 (MISO)** | MISO | MISO | MISO |
| **Pin 23** | **GPIO 11 (SCLK)** | SCK | SCK | SCK |
| **Pin 24** | **GPIO 8 (CE0)** | **NSS (CS #1)** | — | — |
| **Pin 26** | **GPIO 7 (CE1)** | — | **NSS (CS #2)** | — |
| **Pin 22** | **GPIO 25** | — | — | **NSS (CS #3)** |
| **Pin 18** | **GPIO 24** | **DIO0 (RxDone #1)**| — | — |
| **Pin 16** | **GPIO 23** | — | **DIO0 (RxDone #2)**| — |
| **Pin 15** | **GPIO 22** | — | — | **DIO0 (RxDone #3)**|
| **Pin 1, 17** | **3.3V Power** | VCC | VCC | VCC |
| **Pin 6, 9, 14**| **Ground** | GND | GND | GND |

---

## Phụ Lục B: Cấu Hình Tham Số Thực Nghiệm & Đặc Tả Bộ Dữ Liệu

### B.1. Bảng tham số cấu hình vô tuyến chuẩn (RF PHY Configuration)
Toàn bộ các thiết bị End-Node và Gateway hoạt động đồng bộ với cấu hình tầng vật lý:

*Bảng B.1: Cấu hình tham số vô tuyến RF của hệ thống*

| Tham số vô tuyến | Ký hiệu | Giá trị thiết lập | Đơn vị / Ý nghĩa |
| :--- | :---: | :---: | :--- |
| **Dải tần số hoạt động** | $f_{ISM}$ | $433.050 - 434.790$ | $\text{MHz}$ (Băng tần ISM không cấp phép) |
| **Tần số Kênh 1 (CH1)** | $f_{c1}$ | $433.175$ | $\text{MHz}$ |
| **Tần số Kênh 2 (CH2)** | $f_{c2}$ | $433.375$ | $\text{MHz}$ |
| **Tần số Kênh 3 (CH3)** | $f_{c3}$ | $433.575$ | $\text{MHz}$ |
| **Khoảng cách bảo vệ kênh** | $B_{guard}$ | $200.0$ | $\text{kHz}$ (Ngăn chặn can nhiễu lân kênh) |
| **Băng thông tín hiệu** | $BW$ | $125.0$ | $\text{kHz}$ |
| **Hệ số trải phổ** | $SF$ | $7$ | ($2^7 = 128\text{ chips/symbol}$) |
| **Tốc độ mã hóa kênh** | $CR$ | $4/5$ ($CR=1$) | Khả năng tự sửa lỗi Forward Error Correction |
| **Công suất phát sóng** | $P_{tx}$ | $+17.0$ | $\text{dBm}$ ($\approx 50\text{ mW}$) |
| **Độ dài chuỗi Preamble** | $N_{pre}$ | $8$ | Ký hiệu (Symbols) |
| **Từ khóa đồng bộ mạng** | SyncWord | `0x12` | Mã định danh mạng thử nghiệm riêng biệt |
| **Thời gian nghỉ giữa 2 gói** | $T_{interval}$ | $1.5$ | $\text{giây}$ |

---

### B.2. Cấu trúc và đặc tả bộ dữ liệu thực nghiệm (Dataset Specification)

Bộ dữ liệu sau khi tiền xử lý và trích xuất đặc trưng được lưu trữ trong tệp `data/ready/dataset_ready.csv` với tổng cộng **$19,440\text{ dòng dữ liệu}$**, gồm 90 cột đặc trưng đầu vào (`feat_0` đến `feat_89`) và các cột nhãn:

*Bảng B.2: Cấu trúc các trường dữ liệu trong tệp dataset_ready.csv*

| Nhóm trường | Tên cột đại diện | Số lượng cột | Kiểu dữ liệu | Ý nghĩa kỹ thuật |
| :--- | :--- | :---: | :---: | :--- |
| **Lịch sử cửa sổ trượt** | `feat_0` đến `feat_89` | $90\text{ cột}$ | `float32` | 10 bước trượt liên tiếp ($t-9$ đến $t$), mỗi bước gồm 9 thuộc tính: [CH1, CH2, CH3, SNR, RSSI, Size, Packet_ID, Frequency, Current_CH]. |
| **Nhãn kênh mục tiêu** | `target_channel` | $1\text{ cột}$ | `int64` | Giá trị nhãn phân loại: `0` (Kênh 433.175 MHz), `1` (Kênh 433.375 MHz), `2` (Kênh 433.575 MHz). |
| **Kênh hiện tại** | `current_channel` | $1\text{ cột}$ | `int64` | Chỉ số kênh mà node đang phát ở bước hiện tại. |
| **Kích thước tải trọng** | `size_of_message` | $1\text{ cột}$ | `float64` | Kích thước gói tin thực nghiệm ($30, 74, 118, 162, 206, 250\text{ Bytes}$). |
| **Định danh trạm phát** | `node_id` | $1\text{ cột}$ | `string` | Định danh trạm phát (`A`, `B`, hoặc `C`). |

*Bảng B.3: Thống kê mô tả các đặc trưng đầu vào trước khi chuẩn hóa Z-Score*

| Thuộc tính đặc trưng | Giá trị nhỏ nhất (Min) | Giá trị lớn nhất (Max) | Giá trị trung bình ($\mu$) | Độ lệch chuẩn ($\sigma$) | Đơn vị đo |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cường độ tín hiệu thu (RSSI)** | $-120.0$ | $-35.0$ | $-75.24$ | $18.42$ | $\text{dBm}$ |
| **Tỷ số tín hiệu / tạp âm (SNR)** | $-15.0$ | $+11.5$ | $+7.85$ | $2.61$ | $\text{dB}$ |
| **Kích thước tải trọng (Size)** | $30.0$ | $250.0$ | $140.00$ | $74.62$ | $\text{Bytes}$ |
| **Số thứ tự gói (Packet_ID)** | $0$ | $1,199$ | $599.50$ | $346.41$ | Số nguyên |
| **Tần số phát sóng (Frequency)** | $433.175$ | $433.575$ | $433.375$ | $0.163$ | $\text{MHz}$ |

---

## Phụ Lục C: Mã Nguồn Nhúng Tiêu Biểu

### C.1. Tệp mã nguồn C Header `model.h` sinh tự động từ Pipeline TinyML
```c
// ============================================================================
// TỰ ĐỘNG SINH TỪ PIPELINE TINYML LORA CHANNEL HOPPING
// Thuật toán: Separable_1D_CNN (Test Accuracy: 90.51%)
// Kích thước FlatBuffer: 8856 bytes (~8.65 KB)
// Cấu trúc đầu vào: 10 bước x 9 đặc trưng = 90 giá trị float
// ============================================================================

#ifndef LORA_MODEL_H
#define LORA_MODEL_H

#include <stdint.h>
#include <stddef.h>

#define TINYML_MODEL_NAME          "Separable_1D_CNN"
#define TINYML_NUM_CHANNELS        3
#define TINYML_WINDOW_STEPS        10
#define TINYML_NUM_FEATURES        9
#define TINYML_INPUT_DIM           (TINYML_WINDOW_STEPS * TINYML_NUM_FEATURES)
#define TINYML_TENSOR_ARENA_SIZE   (10 * 1024) // 10 KB RAM
#define TINYML_IS_FLAT             0

#if defined(__GNUC__) || defined(__clang__)
  #define TFLM_ALIGNED __attribute__((aligned(16)))
#elif defined(_MSC_VER)
  #define TFLM_ALIGNED __declspec(align(16))
#else
  #define TFLM_ALIGNED alignas(16)
#endif

TFLM_ALIGNED const unsigned char model[] = {
  0x1c, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4c, 0x33, 0x14, 0x00, 0x20, 0x00,
  0x04, 0x00, 0x08, 0x00, 0x0c, 0x00, 0x10, 0x00, 0x14, 0x00, 0x00, 0x00,
  // ... [Mảng byte nén FlatBuffer 8,856 bytes] ...
  0x00, 0x00, 0x06, 0x00, 0x08, 0x00, 0x04, 0x00, 0x06, 0x00, 0x00, 0x00
};
const unsigned int model_len = 8856;

// Mảng tham số chuẩn hóa Z-Score: z = (x - mean) / scale
const float SCALER_MEAN[9]  = {0.334120f, 0.331205f, 0.334675f, 7.852410f, -75.24102f, 140.0000f, 599.5000f, 433.3750f, 1.0000f};
const float SCALER_SCALE[9] = {0.471682f, 0.470648f, 0.471878f, 2.610542f,  18.42150f,  74.6214f, 346.4101f,   0.1633f, 0.8165f};

#ifdef __cplusplus
/**
 * Chuẩn hóa cửa sổ trượt 10 bước (mỗi bước 9 đặc trưng) thành mảng đầu vào mô hình
 */
inline void normalizeSlidingWindow(const float raw_history[10][9], float out_normalized[10][9]) {
  for (int step = 0; step < 10; step++) {
    for (int feat = 0; feat < 9; feat++) {
      out_normalized[step][feat] = (raw_history[step][feat] - SCALER_MEAN[feat]) / SCALER_SCALE[feat];
    }
  }
}

/**
 * Tìm chỉ số kênh có xác suất lớn nhất (ArgMax)
 */
inline int argmaxChannel(const float probs[3]) {
  int best = 0;
  float max_val = probs[0];
  for (int i = 1; i < 3; i++) {
    if (probs[i] > max_val) {
      max_val = probs[i];
      best = i;
    }
  }
  return best;
}
#endif // __cplusplus

#endif // LORA_MODEL_H
```

---

### C.2. Trích đoạn tác vụ suy luận TinyML và phát sóng FreeRTOS trên ESP32
```cpp
#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "model.h"

// Bảng tần số 3 kênh
const long CHANNELS_FREQ[3] = {433175000, 433375000, 433575000};

// Cấu trúc hàng đợi chuyển kênh
QueueHandle_t channelQueue;
SemaphoreHandle_t historyMutex;
float raw_history[10][9];

// Tác vụ suy luận TinyML trên Core 1
void Task_TinyML(void *pvParameters) {
  // 1. Khởi tạo TensorFlow Lite Micro
  const tflite::Model* tflite_model = tflite::GetModel(model);
  tflite::AllOpsResolver resolver;
  uint8_t tensor_arena[TINYML_TENSOR_ARENA_SIZE];
  tflite::MicroInterpreter interpreter(tflite_model, resolver, tensor_arena, TINYML_TENSOR_ARENA_SIZE);
  interpreter.AllocateTensors();

  TfLiteTensor* input = interpreter.input(0);
  TfLiteTensor* output = interpreter.output(0);

  float norm_window[10][9];

  while (true) {
    // Chờ tín hiệu chu kỳ phát
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // Sao chép an toàn dữ liệu lịch sử cửa sổ trượt
    xSemaphoreTake(historyMutex, portMAX_DELAY);
    normalizeSlidingWindow(raw_history, norm_window);
    xSemaphoreGive(historyMutex);

    // Nạp dữ liệu vào Tensor đầu vào
    memcpy(input->data.f, norm_window, sizeof(norm_window));

    // Thực thi suy luận (Forward Pass)
    uint32_t t_start = micros();
    interpreter.Invoke();
    uint32_t lat_us = micros() - t_start;

    // Đọc kết quả phân loại xác suất
    float p0 = output->data.f[0];
    float p1 = output->data.f[1];
    float p2 = output->data.f[2];
    int best_ch = argmaxChannel(output->data.f);

    // Gửi chỉ số kênh vào hàng đợi cho Task_LoRaTX
    xQueueOverwrite(channelQueue, &best_ch);
  }
}

// Tác vụ điều khiển phát vô tuyến LoRa trên Core 1
void Task_LoRaTX(void *pvParameters) {
  int target_ch = 0;
  while (true) {
    // Đọc quyết định kênh từ Task_TinyML
    if (xQueueReceive(channelQueue, &target_ch, portMAX_DELAY) == pdPASS) {
      // 1. Chuyển tần số phần cứng SX1278
      LoRa.setFrequency(CHANNELS_FREQ[target_ch]);

      // 2. Đóng gói bản tin và phát sóng
      LoRa.beginPacket();
      LoRa.write(NODE_ID);
      LoRa.write((uint8_t)(packet_counter >> 8));
      LoRa.write((uint8_t)(packet_counter & 0xFF));
      LoRa.write((uint8_t)target_ch);
      // Ghi payload dữ liệu...
      LoRa.endPacket(false); // Phát đồng bộ có kiểm tra TxDone

      packet_counter++;
    }
  }
}
```
