# Tối ưu hóa kênh truyền LoRa với TinyML (Channel Hopping Optimization)

Hệ thống nhảy kênh thông minh dựa trên học máy siêu nhẹ (TinyML) trên vi điều khiển ESP32 và Gateway Raspberry Pi lắng nghe đa kênh thời gian thực (Dải tần 433 MHz).

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
│           └── model.h                  # Header chứa mô hình nơ-ron nhúng (FlatBuffer byte array)
├── GatewayCode/                         # Mã nguồn Gateway trên Raspberry Pi CM4 (WiringPi C++)
│   ├── Makefile                         # Biên dịch bằng g++ với -lwiringPi -lpthread
│   ├── setup_webserver.sh               # Script tự động cấu hình Nginx Port 80 & Web Dashboard
│   ├── nginx/
│   │   └── loragw.conf                  # File cấu hình Nginx Reverse Proxy (Port 80 -> Daemon 8080)
│   ├── web/                             # Giao diện Web Dashboard Router-style
│   │   ├── index.html                   # Giao diện quản trị, điều khiển phát, OTA Tuning
│   │   ├── style.css                    # Giao diện hiện đại, tối ưu hiển thị
│   │   └── app.js                       # Logic REST API, trạng thái sóng & console real-time
│   ├── include/
│   │   ├── config.h                     # Cấu hình chân GPIO & tần số 3 kênh 433 MHz
│   │   ├── http_server.h                # Khai báo REST/HTTP server nhúng
│   │   └── sx1278_wiringpi.h            # Driver SX1278
│   └── src/
│       ├── http_server.cpp              # Web Server API đa luồng phục vụ điều khiển và OTA
│       ├── sx1278_wiringpi.cpp          # Driver điều khiển SX1278 qua SPI
│       ├── test_comm.cpp                # Chương trình kiểm tra đường truyền RF & phản hồi ACK
│       └── main_gw.cpp                  # Luồng lắng nghe đồng thời 3 module Ra-02 & bộ lọc Control
├── TinyML/                              # Pipeline AI và phân tích dữ liệu (Python)
│   ├── LoRa_TinyML_Pipeline.ipynb       # Jupyter Notebook hoàn chỉnh, đồng bộ 100% với các scripts
│   ├── requirements.txt                 # Thư viện: TensorFlow, Scikit-learn, Pandas, Matplotlib, Seaborn
│   ├── data/                            # Kiến trúc thư mục chuẩn bị cho thu thập dữ liệu thực tế
│   │   ├── logs/                        # Nơi đặt các file log thô (.txt, .csv) thu thập từ Gateway
│   │   ├── parsed/                      # Output bước 1: CSV đã chuẩn hóa các trường dữ liệu
│   │   ├── imputed/                     # Output bước 2: Đã phát hiện và gán nhãn gói mất (-1000 dBm)
│   │   └── ready/                       # Output bước 3: Dataset chuỗi thời gian (Sliding Window)
│   ├── scripts/
│   │   ├── 01_data_parser.py            # Trích xuất và chuẩn hóa log Gateway sang CSV
│   │   ├── 02_add_missed_packets.py     # Phát hiện va chạm & điền nhãn gói mất
│   │   ├── 03_generate_dataset.py       # Tạo cửa sổ thời gian (Sliding Window ts = 10 bước)
│   │   ├── 04_train_model.py            # Huấn luyện FCNN Baseline + EarlyStopping, xuất model.h
│   │   ├── 05_evaluate_comparison.py    # Đánh giá so sánh: Fixed vs Random vs TinyML
│   │   ├── 06_benchmark_models.py       # So sánh 5 kiến trúc: FCNN, 1D-CNN, GRU, SepCNN, ResNet
│   │   ├── 07_evaluate_best_model.py    # Đánh giá chuyên sâu mô hình tốt nhất (Confusion Matrix, PDR)
│   │   └── build_notebook.py            # Trình sinh tự động Jupyter Notebook từ các scripts
│   ├── models/                          # Chứa mô hình tflite, model.h và checkpoint so sánh
│   └── figures/                         # Biểu đồ PDR, RSSI, SNR, biểu đồ huấn luyện và ma trận nhầm lẫn
├── docs/                                # Tài liệu kỹ thuật, kịch bản thực nghiệm & pipeline chi tiết
│   ├── KICH_BAN_THU_THAP_DU_LIEU.md     # Danh mục 21 kịch bản đo kiểm đa Node
│   ├── PIPELINE_THUC_HIEN_DU_AN.md      # Quy trình tổng thể 6 giai đoạn của ĐATN
│   └── SO_DO_KET_NOI_PHAN_CUNG_VA_FIRMWARE.md # Sơ đồ đấu nối & hoạt động firmware
├── img/                                 # Hình ảnh sơ đồ phần cứng thực tế (Fritzing Breadboard)
│   ├── LoRa Node_bb.png                 # Sơ đồ đấu nối End-Node ESP32
│   └── LoRa GW_bb.png                   # Sơ đồ đấu nối Gateway CM4 3 kênh
└── README.md
```

---

## 2. Sơ đồ đấu nối phần cứng

### A. 3 End-Nodes (ESP32 DevKit V1 + Ra-02 433MHz + OLED SSD1306)

<p align="center">
  <img src="img/LoRa%20Node_bb.png" alt="Sơ đồ kết nối phần cứng LoRa End-Node (ESP32 + Ra-02 + OLED)" width="680"/>
  <br><em>Hình 1: Sơ đồ đấu nối phần cứng chi tiết của LoRa End-Node (ESP32 DevKit V1 + Module LoRa SX1278 Ra-02 + Màn hình OLED 0.96" SSD1306)</em>
</p>

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

<p align="center">
  <img src="img/LoRa%20GW_bb.png" alt="Sơ đồ kết nối phần cứng Multi-Channel Gateway CM4 + 3x Ra-02" width="750"/>
  <br><em>Hình 2: Sơ đồ đấu nối phần cứng trạm Gateway 3 kênh (Raspberry Pi CM4 / Pi 4 + 3 Module LoRa SX1278 Ra-02 433 MHz)</em>
</p>

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

### Bước 1: Thu thập dữ liệu thực tế (Data Collection)
1. **Nạp firmware cho 3 Node**:
   - Mở [MCUCode/LoRaEN_DataCollection/src/main.cpp](file:///e:/DATN/LoRa_TinyML_Hopping/MCUCode/LoRaEN_DataCollection/src/main.cpp).
   - Đặt `#define NODE_ID 'A'`, nạp cho Node 1 qua cổng COM tương ứng.
   - Đổi thành `#define NODE_ID 'B'`, nạp cho Node 2.
   - Đổi thành `#define NODE_ID 'C'`, nạp cho Node 3.
   - *Khi vừa cấp điện, các Node sẽ ở chế độ **CHỜ LỆNH** (màn hình OLED báo `NODE [x] - CHO LENH`), sẵn sàng nhận lệnh từ Web Gateway hoặc nút bấm.*

2. **Cài đặt Nginx & Web Dashboard trên Raspberry Pi CM4 (Chỉ chạy 1 lần đầu)**:
   ```bash
   cd ~/LoRa_TinyML_Hopping/GatewayCode
   sudo chmod +x setup_webserver.sh
   sudo ./setup_webserver.sh
   ```
   *Script tự động cài đặt Nginx, cấu hình Virtual Host cổng 80, và copy giao diện Web Admin vào `/var/www/loragw`.*

3. **Khởi động Gateway Daemon trên Raspberry Pi CM4**:
   ```bash
   cd ~/LoRa_TinyML_Hopping/GatewayCode
   make clean && make
   sudo ./lora_gw_3ch
   ```

4. **Truy cập Giao diện Web Dashboard (Port 80 qua Wi-Fi)**:
   - Mở trình duyệt trên máy tính hoặc điện thoại kết nối cùng mạng Wi-Fi với CM4:
     `http://<ĐỊA_CHỈ_IP_WIFI_CỦA_CM4>/`
   - **Các chức năng chính trên Web Dashboard**:
     - **Quản lý phiên đo**: Đặt tên kịch bản đo ngay trên Web (ví dụ: `A_433_175`, `A_B_433_375`, `ALL_NODES`). Hệ thống tự động ghi nhật ký vào `logs/<TÊN>.txt` và `csv/<TÊN>.csv`.
     - **Gửi lệnh phát Downlink**: Tùy chọn kích hoạt riêng lẻ (A, B hoặc C), kích hoạt 2 Node đồng thời (A+B, B+C, A+C), hoặc kích hoạt TẤT CẢ (ALL).
     - **Dừng / Reset**: Gửi lệnh `CMD:STOP` để dừng phát và đưa các Node về trạng thái chờ lệnh tức thời.
     - **Cấu hình tần số OTA (Over-The-Air)**: Điều chỉnh tần số từ xa cho từng Node, hiển thị trạng thái xác nhận `ỔN ĐỊNH ✓` trước khi phát.
     - **Giám sát thời gian thực**: Trạng thái Online/Offline, chất lượng sóng 4 vạch RSSI, giá trị SNR, và Console log gói tin.
     - **Bộ lọc Control Traffic**: Các bản tin Ping/Pong, ACK, OTA Config chỉ dùng điều khiển và **tuyệt đối không bị ghi vào file dataset**.

5. **Tiến trình phát gói tin**:
   - Khi nhận lệnh `START`, các Node phát tuần tự 6 mức kích thước payload: `30B -> 74B -> 118B -> 162B -> 206B -> 250B` $\times$ 100 gói/mức (= 600 gói/phiên).
   - Khi hoàn thành, Node hiển thị `HOÀN THÀNH` trên OLED và tiếp tục duy trì lắng nghe lệnh cho phiên tiếp theo.

---

### Bước 2: Huấn luyện mô hình TinyML trên Python
1. **Cài đặt môi trường Python**:
   ```bash
   cd TinyML
   pip install -r requirements.txt
   ```

2. **Chuyển dữ liệu log thực tế vào pipeline**:
   - Copy các file log thu được từ Gateway vào thư mục [TinyML/data/logs/](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/data/logs).

3. **Chạy chuỗi script tiền xử lý và huấn luyện**:
   ```bash
   # Bước 1: Trích xuất log Gateway thành CSV chuẩn
   python scripts/01_data_parser.py

   # Bước 2: Phát hiện va chạm & gán nhãn gói mất (RSSI = -1000 dBm)
   python scripts/02_add_missed_packets.py

   # Bước 3: Tạo cửa sổ trượt bộ nhớ thời gian (ts = 10 bước x 8 đặc trưng = 80 chiều)
   python scripts/03_generate_dataset.py

   # Bước 4: Huấn luyện mô hình FCNN Baseline & xuất mã nhúng C
   python scripts/04_train_model.py
   ```
   - Script 04 huấn luyện mạng nơ-ron FCNN siêu nhẹ: `Dense(10, ReLU) -> Dense(10, ReLU, L1) -> Dense(3, Softmax)`.
   - Tích hợp `EarlyStopping(patience=25)` tránh overfitting.
   - Vẽ đường cong Loss / Accuracy lưu tại `TinyML/figures/training_trends.png`.
   - Xuất mô hình `TinyML/models/channel_model.tflite` (~5.8 KB) và tự động sinh mảng C byte `model.h` đồng bộ sang firmware ESP32.

4. **Sử dụng Jupyter Notebook (Tùy chọn)**:
   - Toàn bộ pipeline trên có thể chạy trực tiếp, trực quan từng bước qua file [LoRa_TinyML_Pipeline.ipynb](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/LoRa_TinyML_Pipeline.ipynb).
   - Nếu muốn tái tạo Notebook tự động: `python scripts/build_notebook.py`.

---

### Bước 3: Đánh giá so sánh & Benchmark kiến trúc nơ-ron
1. **So sánh 3 cơ chế quản lý kênh**:
   ```bash
   python scripts/05_evaluate_comparison.py
   ```
   Tính toán và vẽ biểu đồ đối chứng:
   - **Average RSSI**: So sánh cường độ tín hiệu giữa Random Hopping và TinyML.
   - **Average SNR**: So sánh chất lượng tín hiệu.
   - **PDR (Packet Delivery Ratio)**: So sánh tỷ lệ nhận gói tin thành công giữa **Fixed Channel** (kênh cố định), **Random Hopping** (nhảy ngẫu nhiên) và **TinyML Hopping**.

2. **Benchmark 5 kiến trúc mạng nơ-ron**:
   ```bash
   python scripts/06_benchmark_models.py
   ```
   Huấn luyện và so sánh:
   - **Baseline FCNN (MLP)**: Tối ưu cho Flash/RAM nhỏ nhất.
   - **1D-CNN (Temporal Convolution)**: Nắm bắt tương quan chuỗi thời gian cục bộ.
   - **GRU (Gated Recurrent Unit)**: Nắm bắt phụ thuộc thời gian dài hạn.
   - **Separable 1D-CNN**: Kiến trúc tích chập tách biệt theo chiều sâu (MobileNet-style), giảm 60% tham số.
   - **Residual 1D-CNN (ResNet-1D)**: Kết nối tắt giúp hội tụ ổn định.

3. **Đánh giá chuyên sâu mô hình tối ưu**:
   ```bash
   python scripts/07_evaluate_best_model.py
   ```
   - Xuất Confusion Matrix (Ma trận nhầm lẫn), Precision, Recall, F1-Score cho từng kênh tần số.
   - Phân tích chi tiết độ trễ suy luận (Inference Latency) và dung lượng bộ nhớ.

---

### Bước 4: Triển khai kiểm chứng thời gian thực trên Node
1. Mở project [MCUCode/LoRaEN_TinyMLHopping](file:///e:/DATN/LoRa_TinyML_Hopping/MCUCode/LoRaEN_TinyMLHopping) trên PlatformIO.
2. Kiểm tra file `src/model.h` (đã được sinh tự động từ Bước 2).
3. Nạp firmware vào ESP32 để kích hoạt chế độ nhảy kênh thông minh thời gian thực và theo dõi kết quả PDR trực tiếp trên màn hình OLED.
