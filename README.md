# Tối ưu hóa kênh truyền LoRa với TinyML (Channel Hopping Optimization)

Dự án đồ án tốt nghiệp phát triển dựa trên bài báo khoa học:  
**"Optimizing LoRa for Edge Computing with TinyML Pipeline for Channel Hopping" (arXiv:2412.01609v1)**  
Mã nguồn gốc tham khảo: [GitLab M4RL4/loraedgetinyml](https://gitlab.com/M4RL4/loraedgetinyml)

---

## 1. Cấu trúc thư mục dự án

```text
LoRa_TinyML_Hopping/
├── MCUCode/                             # Firmware nạp cho các End-Node (PlatformIO)
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
- **SPI LoRa Ra-02**:
  - `SCK`  $\rightarrow$ GPIO 18
  - `MISO` $\rightarrow$ GPIO 19
  - `MOSI` $\rightarrow$ GPIO 27
  - `NSS`  $\rightarrow$ GPIO 5
  - `RST`  $\rightarrow$ GPIO 14
  - `DIO0` $\rightarrow$ GPIO 26
- **I2C OLED SSD1306 (128x64)**:
  - `SDA` $\rightarrow$ GPIO 21
  - `SCL` $\rightarrow$ GPIO 22
- **Nguồn**: 3.3V và GND.

### B. Gateway (Raspberry Pi CM4 + 3 Module Ra-02)
Dùng chung đường bus SPI0 của Raspberry Pi CM4:
- `MOSI`: GPIO 10 (WiringPi 12)
- `MISO`: GPIO 9 (WiringPi 13)
- `SCLK`: GPIO 11 (WiringPi 14)

Phân bố chân Chip Select (CS), Reset, DIO0 độc lập cho 3 Module:
| Module Ra-02 | Kênh tần số | Chân CS (NSS) | Chân RST | Chân DIO0 |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **433.175 MHz** | GPIO 8 (WiringPi 10) | GPIO 22 (WiringPi 3) | GPIO 25 (WiringPi 6) |
| **Module 2** | **433.375 MHz** | GPIO 7 (WiringPi 11) | GPIO 23 (WiringPi 4) | GPIO 24 (WiringPi 5) |
| **Module 3** | **433.575 MHz** | GPIO 27 (WiringPi 2) | GPIO 18 (WiringPi 1) | GPIO 17 (WiringPi 0) |

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
   sudo ./lora_gw_3ch
   ```
   Gateway sẽ lắng nghe đồng thời 3 kênh và tự động sinh file `gateway_log_YYYYMMDD_HHMMSS.csv`.
3. Cho 3 Node phát đồng thời ở các khoảng cách khác nhau trong ~15 - 30 phút để tạo ra các hiện tượng suy hao và va chạm sóng tự nhiên.

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
   - Script 04 sẽ huấn luyện mạng nơ-ron FCNN theo bài báo (Dense 10 $\rightarrow$ Dense 10 L1 $\rightarrow$ Dense 3 Softmax).
   - Vẽ đường cong Loss / Accuracy lưu vào `TinyML/figures/training_trends.png`.
   - Xuất file `.tflite` và tự động sinh mã nguồn C `model.h` đồng bộ sang thư mục Node TinyML.

---

### Bước 3: Đánh giá so sánh & Xuất kết quả báo cáo
Chạy script đánh giá đối chứng:
```bash
python scripts/05_evaluate_comparison.py
```
Script sẽ sinh biểu đồ `TinyML/figures/comparison_metrics_fig10.png` gồm 3 tiêu chí:
1. **Average RSSI**: So sánh RSSI giữa Random Hopping và TinyML.
2. **Average SNR**: So sánh chất lượng tín hiệu.
3. **PDR (Packet Delivery Ratio)**: Minh chứng TinyML duy trì tỷ lệ nhận gói cao (95% - 99%) vượt trội so với Kênh cố định (Fixed) và Nhảy ngẫu nhiên (Random).

---

### Bước 4: Triển khai kiểm chứng thời gian thực trên Node
Mở project [MCUCode/LoRaEN_TinyMLHopping](file:///e:/DATN/LoRa_TinyML_Hopping/MCUCode/LoRaEN_TinyMLHopping), nạp vào ESP32 để quan sát trực tiếp kết quả PDR và trạng thái nhảy kênh trên màn hình OLED.
