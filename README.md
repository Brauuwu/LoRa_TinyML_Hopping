# Tối ưu hóa kênh truyền LoRa với TinyML (Channel Hopping Optimization)

Hệ thống nhảy kênh thông minh dựa trên học máy siêu nhẹ (TinyML) trên vi điều khiển ESP32 và Gateway Raspberry Pi lắng nghe đa kênh thời gian thực.

---

## 1. Cấu trúc thư mục dự án

```text
LoRa_TinyML_Hopping/
├── MCUCode/                             # Firmware nạp cho các End-Node (PlatformIO)
│   ├── LoRaEN_CommTest/                 # Firmware kiểm tra truyền thông 2 chiều & đo PDR
│   │   ├── platformio.ini
│   │   └── src/main.cpp
│   ├── LoRaEN_DataCollection/           # Firmware nạp cho 3 ESP32 để thu thập dữ liệu
│   │   ├── platformio.ini
│   │   └── src/main.cpp
│   └── LoRaEN_TinyMLHopping/            # Firmware nạp cho ESP32 thực hiện suy luận TinyML
│       ├── platformio.ini
│       └── src/
│           ├── main.cpp
│           └── model.h                  # Header chứa mô hình nơ-ron nhúng
├── GatewayCode/                         # Mã nguồn Gateway trên Raspberry Pi CM4 (WiringPi C++)
│   ├── Makefile                         # Biên dịch bằng g++ với -lwiringPi
│   ├── include/
│   │   ├── config.h                     # Cấu hình chân GPIO & tần số 3 kênh
│   │   └── sx1278_wiringpi.h
│   └── src/
│       ├── sx1278_wiringpi.cpp          # Driver điều khiển SX1278 qua SPI
│       ├── test_comm.cpp                # Chương trình kiểm tra đường truyền RF & phản hồi ACK
│       └── main_gw.cpp                  # Luồng lắng nghe đồng thời 3 module Ra-02
├── TinyML/                              # Pipeline AI và phân tích dữ liệu (Python)
│   ├── requirements.txt                 # Thư viện: TensorFlow, Scikit-learn, Pandas, Matplotlib
│   ├── data/
│   │   ├── logs/                        # Nơi chứa log thô xuất từ Gateway
│   │   ├── parsed/                      # Dữ liệu sau khi trích xuất
│   │   ├── imputed/                     # Dữ liệu sau khi điền gói mất (-1000 dBm)
│   │   └── ready/                       # Dataset gắn nhãn sẵn sàng huấn luyện
│   ├── scripts/
│   │   ├── 01_data_parser.py            # Trích xuất dữ liệu log
│   │   ├── 02_add_missed_packets.py     # Phát hiện va chạm & điền gói mất
│   │   ├── 03_generate_dataset.py       # Tạo cửa sổ thời gian (Sliding Window)
│   │   ├── 04_train_model.py            # Huấn luyện FCNN & xuất model.h
│   │   └── 05_evaluate_comparison.py    # Đánh giá so sánh: Fixed vs Random vs TinyML
│   ├── models/                          # Chứa channel_model.tflite và model.h
│   └── figures/                         # Biểu đồ PDR, RSSI, SNR cho báo cáo đồ án
└── README.md
```

---

## 2. Sơ đồ đấu nối phần cứng

### A. 3 End-Nodes (ESP32 DevKit V1 + Ra-02 433MHz + OLED SSD1306)

| Thiết bị ngoại vi | Chân Module | Chân ESP32 (GPIO) | Ghi chú |
| :--- | :--- | :--- | :--- |
| **LoRa Ra-02 (SX1278)** | `MOSI` | **GPIO 27** | Bus SPI cứng (VSPI) |
| | `MISO` | **GPIO 19** | Bus SPI cứng |
| | `SCK` | **GPIO 18** | Bus SPI cứng |
| | `NSS` (CS) | **GPIO 5** | Chip Select |
| | `RST` | **GPIO 14** | Reset module LoRa |
| | `DIO0` | **GPIO 26** | Ngắt thu/phát gói tin |
| | `VCC` | **3.3V** | Dòng đỉnh khi phát ~120mA |
| | `GND` | **GND** | Nối chung mass |
| **OLED 0.96" SSD1306** | `SDA` | **GPIO 21** | Bus I2C |
| | `SCL` | **GPIO 22** | Bus I2C |
| | `VCC` | **3.3V** | Nguồn màn hình |
| | `GND` | **GND** | Mass chung |
| **Trạng thái LED** | `LED` | **GPIO 2** | Onboard LED báo truyền gói tin |

---

### B. Gateway (Raspberry Pi CM4 / Pi 4 + 3 Module Ra-02 433MHz)

Được cấu hình chuẩn xác trong [`GatewayCode/include/config.h`](file:///e:/DATN/LoRa_TinyML_Hopping/GatewayCode/include/config.h):

#### 1. Bus SPI0 dùng chung cho cả 3 Module:
- **MOSI**: BCM GPIO 10 (WiringPi 12 / Chân vật lý Pin 19)
- **MISO**: BCM GPIO 9  (WiringPi 13 / Chân vật lý Pin 21)
- **SCLK**: BCM GPIO 11 (WiringPi 14 / Chân vật lý Pin 23)
- **Nguồn**: Chân vật lý 3.3V (Pin 1, Pin 17) và GND (Pin 6, 9, 14, 20, 25)

#### 2. Phân bố chân điều khiển độc lập cho từng Module:

| Module Ra-02 | Kênh tần số | Tín hiệu | BCM GPIO | WiringPi Pin (trong Code) | Chân vật lý (40-Pin Header) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **433.175 MHz** | **CS (NSS)** | GPIO 8 (CE0) | **10** | **Pin 24** |
| | (Kênh 1) | **RST** | GPIO 27 | **2** | **Pin 13** |
| | | **DIO0** | GPIO 22 | **3** | **Pin 15** |
| **Module 2** | **433.375 MHz** | **CS (NSS)** | GPIO 7 (CE1) | **11** | **Pin 26** |
| | (Kênh 2) | **RST** | GPIO 17 | **0** | **Pin 11** |
| | | **DIO0** | GPIO 18 | **1** | **Pin 12** |
| **Module 3** | **433.575 MHz** | **CS (NSS)** | GPIO 25 | **6** | **Pin 22** |
| | (Kênh 3) | **RST** | GPIO 24 | **5** | **Pin 18** |
| | | **DIO0** | GPIO 23 | **4** | **Pin 16** |

---

## 3. Quy trình thực hiện đồ án từng bước

### Bước 1: Thu thập dữ liệu thô (Data Collection)
1. **Nạp firmware cho 3 Node**:
   - Mở [MCUCode/LoRaEN_DataCollection/src/main.cpp](file:///e:/DATN/LoRa_TinyML_Hopping/MCUCode/LoRaEN_DataCollection/src/main.cpp).
   - Đặt `#define NODE_ID 'A'`, nạp cho Node 1 (Cổng COM tương ứng).
   - Đổi thành `#define NODE_ID 'B'`, nạp cho Node 2.
   - Đổi thành `#define NODE_ID 'C'`, nạp cho Node 3.
2. **Chạy Gateway trên Raspberry Pi CM4**:
   ```bash
   cd GatewayCode
   make
   # Chạy thu thập theo kịch bản đo cụ thể:
   sudo ./lora_gw_3ch A_433.175
   # Hoặc cho kịch bản 2 Node:
   sudo ./lora_gw_3ch A_B_433.175
   ```
   Gateway sẽ lắng nghe đồng thời 3 kênh và tự động sinh đồng thời 2 file:
   - `csv/<TÊN_KỊCH_BẢN>.csv`: File dữ liệu bảng cho Python Pandas.
   - `logs/<TÊN_KỊCH_BẢN>.txt`: File log thô theo chuẩn bài báo `LoRaEdgeTinyML`.
3. Cho các Node phát tuần tự 6 mức kích thước (30B -> 250B) x 100 gói. Node sẽ tự động dừng phát hoàn toàn sau khi gửi đủ gói cuối.

---

### Bước 2: Huấn luyện mô hình TinyML trên Python
1. Cài đặt môi trường:
   ```bash
   cd TinyML
   pip install -r requirements.txt
   ```
2. Copy file `gateway_log_*.csv` vào thư mục `TinyML/data/logs/`.
3. Chạy chuỗi script tiền xử lý và huấn luyện:
   ```bash
   python scripts/01_data_parser.py
   python scripts/02_add_missed_packets.py
   python scripts/03_generate_dataset.py
   python scripts/04_train_model.py
   ```
   - Script 04 sẽ huấn luyện mạng nơ-ron FCNN tối ưu cho MCU (Dense 10 $\rightarrow$ Dense 10 L1 $\rightarrow$ Dense 3 Softmax).
   - Vẽ đường cong Loss / Accuracy lưu vào `TinyML/figures/training_trends.png`.
   - Xuất file `.tflite` và tự động sinh mã nguồn C `model.h` đồng bộ sang thư mục Node TinyML.

---

### Bước 3: Đánh giá so sánh & Xuất kết quả báo cáo
Chạy script đánh giá đối chứng:
```bash
python scripts/05_evaluate_comparison.py
```
Script sẽ sinh biểu đồ `TinyML/figures/comparison_metrics.png` gồm 3 tiêu chí:
1. **Average RSSI**: So sánh RSSI giữa Random Hopping và TinyML.
2. **Average SNR**: So sánh chất lượng tín hiệu.
3. **PDR (Packet Delivery Ratio)**: Minh chứng TinyML duy trì tỷ lệ nhận gói cao (95% - 99%) vượt trội so với Kênh cố định (Fixed) và Nhảy ngẫu nhiên (Random).

---

### Bước 4: Triển khai kiểm chứng thời gian thực trên Node
Mở project [MCUCode/LoRaEN_TinyMLHopping](file:///e:/DATN/LoRa_TinyML_Hopping/MCUCode/LoRaEN_TinyMLHopping), nạp vào ESP32 để quan sát trực tiếp kết quả PDR và trạng thái nhảy kênh trên màn hình OLED.
