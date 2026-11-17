# BỘ TÀI LIỆU THUYẾT MINH ĐỒ ÁN TỐT NGHIỆP

---

## 🎓 THÔNG TIN ĐỀ TÀI & TÁC GIẢ THỰC HIỆN

* **Tên đề tài:** **LỰA CHỌN KÊNH TRUYỀN TỐI ƯU CHO HỆ THỐNG LORAWAN DỰA TRÊN TINYML**
* **Sinh viên thực hiện (Nhóm 62):**
  1. **Vi Minh Hiếu**
  2. **Hoàng Đức Đạt**
* **Đơn vị đào tạo:** Khoa Điện Tử Viễn Thông / Chuyên ngành Hệ thống Nhúng & IoT
* **Nền tảng phần cứng thực nghiệm:**
  * **03 End-Nodes:** Vi điều khiển ESP32 DevKit V1 (Xtensa Dual-Core 32-bit LX6 @ $240\text{ MHz}$, $520\text{ KB}$ SRAM) + Module Semtech SX1278 (Ai-Thinker Ra-02 $433\text{ MHz}$) + Màn hình OLED SSD1306.
  * **01 Multi-Channel Gateway:** Raspberry Pi Compute Module 4 (CM4) tích hợp 03 module thu SX1278 độc lập lắng nghe song song trên 3 kênh tần số ($433.175\text{ MHz}$, $433.375\text{ MHz}$, $433.575\text{ MHz}$) với kiến trúc không điểm mù (Zero-Blindness).
* **Môi trường phần mềm & Framework:** FreeRTOS, TensorFlow Lite for Microcontrollers (TFLM), Python 3.12 (Conda `iot_ml`), ESP-IDF / Arduino Core.

---

## 📑 MỤC LỤC CHI TIẾT CÁC CHƯƠNG ĐỒ ÁN

Bộ tài liệu thuyết minh được biên soạn đầy đủ, học thuật và chi tiết theo đúng cấu trúc của [Đề cương chi tiết Đồ án tốt nghiệp](file:///E:/DATN/De_cuong_N62_chi_tiet.docx):

### 📌 [LỜI MỞ ĐẦU](file:///E:/DATN/LoRa_TinyML_Hopping/docs/CH0_MO_DAU.md)
* 1. Lý do chọn đề tài
* 2. Mục tiêu nghiên cứu
* 3. Phạm vi nghiên cứu
* 4. Phương pháp nghiên cứu
* 5. Bố cục đồ án

---

### 📌 [CHƯƠNG 1: TỔNG QUAN VỀ HỆ THỐNG LORAWAN](file:///E:/DATN/LoRa_TinyML_Hopping/docs/CH1_TONG_QUAN_LORAWAN.md)
* **1.1. Sự ra đời của LoRaWAN**
  * 1.1.1. Giới thiệu hệ thống IoT
  * 1.1.2. Công nghệ mạng diện rộng công suất thấp (LPWAN)
  * 1.1.3. Vai trò của LoRaWAN trong IoT
* **1.2. Cấu trúc và hoạt động của LoRaWAN**
  * 1.2.1. Công nghệ LoRa (Kỹ thuật điều chế trải phổ CSS, Symbol Duration, Chip Rate, Bitrate, Noise Floor)
  * 1.2.2. Các thành phần trong hệ thống LoRaWAN (End-Nodes, Gateways, Network Server, Application Server, Device Classes A/B/C)
  * 1.2.3. Cơ chế truyền dữ liệu và quản lý kênh (Tính toán thời gian truyền sóng trên không $ToA$)
* **1.3. Chất lượng kênh truyền LoRaWAN**
  * 1.3.1. Các yếu tố ảnh hưởng đến kênh truyền (Path Loss, Can nhiễu, Xung đột Pure ALOHA)
  * 1.3.2. Các chỉ số đánh giá chất lượng kênh (RSSI, SNR, Packet Delivery Ratio - PDR)
  * 1.3.3. Các phương pháp lựa chọn kênh (Kênh cố định, Nhảy ngẫu nhiên, Nhảy thích ứng TinyML)
* **1.4. Ứng dụng TinyML trong lựa chọn kênh truyền LoRaWAN**
  * 1.4.1. Giới thiệu về Edge AI
  * 1.4.2. Khả năng triển khai học máy trên vi điều khiển (TinyML & TensorFlow Lite Micro)
  * 1.4.3. Tiềm năng của TinyML trong tối ưu hóa kênh truyền vô tuyến
* **1.5. Kết luận chương 1**

---

### 📌 [CHƯƠNG 2: MÔ HÌNH HỌC MÁY TINYML CHO HỆ THỐNG LORAWAN](file:///E:/DATN/LoRa_TinyML_Hopping/docs/CH2_MO_HINH_HOC_MAY_TINYML.md)
* **2.1. Bài toán lựa chọn kênh**
  * 2.1.1. Mục tiêu bài toán (Mô hình hóa toán học bài toán phân loại chuỗi thời gian CSI)
  * 2.1.2. Yêu cầu của hệ thống (Ràng buộc bộ nhớ Flash/RAM, độ trễ $< 20\text{ ms}$, tính tự chủ, độ tin cậy $\text{PDR} \ge 95\%$)
* **2.2. Xây dựng hệ thống thu thập dữ liệu**
  * 2.2.1. Sơ đồ khối hệ thống
  * 2.2.2. Triển khai phần cứng hệ thống (ESP32 DevKit V1, SX1278 Ra-02, OLED SSD1306, RPi CM4 Multi-Receiver)
  * 2.2.3. Định dạng gói tin dữ liệu (Cấu trúc byte chặt chẽ 9 trường)
  * 2.2.4. Kịch bản thu thập dữ liệu (Quét tải trọng $30\text{B} - 250\text{B}$, $21,600\text{ gói tin}$)
* **2.3. Các thuật toán học máy TinyML phù hợp cho lựa chọn kênh tối ưu**
  * 2.3.1. Baseline Multi-Layer Perceptron (FCNN)
  * 2.3.2. Temporal Convolutional Neural Network (1D-CNN)
  * 2.3.3. Gated Recurrent Unit (GRU RNN)
  * 2.3.4. Depthwise Separable 1D-CNN (MobileNet-style - Tối ưu giảm 63% phép tính)
  * 2.3.5. Residual Neural Network (ResNet-1D với Skip Connection)
* **2.4. Kết luận chương 2**

---

### 📌 [CHƯƠNG 3: TRIỂN KHAI THỰC NGHIỆM TRÊN VI XỬ LÝ LORA ESP32 VÀ ĐÁNH GIÁ](file:///E:/DATN/LoRa_TinyML_Hopping/docs/CH3_TRIEN_KHAI_THUC_NGHIEM_VA_DANH_GIA.md)
* **3.1. Xây dựng mô hình TinyML lựa chọn kênh tối ưu**
  * 3.1.1. Tiền xử lý dữ liệu (Bù đắp gói mất, cửa sổ trượt $W=10$ bước, chuẩn hóa Z-Score, chia tập Train/Val/Test)
  * 3.1.2. Huấn luyện mô hình học máy (Điều chuẩn $L_2$, Dropout, đường cong học tập với điểm gồ ghề và bão hòa thực sự)
  * 3.1.3. Kết quả đánh giá mô hình (Bảng đối sánh 5 mô hình, phân tích đánh đổi Accuracy - Flash - RAM - Latency)
* **3.2. Xây dựng môi trường kiểm thử thực nghiệm**
  * 3.2.1. Thiết lập môi trường thực nghiệm (Bố trí đa tầng trong khuôn viên đại học LOS & NLOS)
  * 3.2.2. Nhúng mô hình lên vi điều khiển ESP32 (Xuất header `model.h`, Tensor Arena $10\text{ KB}$, Firmware đa nhiệm FreeRTOS)
* **3.3. Đánh giá hiệu năng**
  * 3.3.1. Kết quả mô phỏng mô hình (Khả năng mở rộng từ 3 kênh lên 16 kênh)
  * 3.3.2. Kết quả thực nghiệm trên ESP32 (Đối sánh trực tiếp Random Hopping vs TinyML Hopping: PDR đạt $95\% - 100\%$, mức tăng tới $+31.3\%$ PDR, cải thiện RSSI $+22.9\text{ dBm}$)
* **3.4. Kết luận chương 3**

---

### 📌 [KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN](file:///E:/DATN/LoRa_TinyML_Hopping/docs/CH4_KET_LUAN.md)
* 1. Kết quả đạt được của đề tài (Lý thuyết, phần cứng, mô hình TinyML, hiệu năng thực nghiệm)
* 2. Hạn chế của đề tài (Quy mô node, số lượng kênh, kịch bản di động, học trực tuyến)
* 3. Hướng nghiên cứu & phát triển tiếp theo (On-device Incremental TinyML, Intelligent ADR, Băng tần 868/915 MHz, Federated Learning)

---

### 📌 [TÀI LIỆU THAM KHẢO](file:///E:/DATN/LoRa_TinyML_Hopping/docs/TAI_LIEU_THAM_KHAO.md)
* Danh mục 15 tài liệu khoa học chuẩn mực quốc tế định dạng IEEE (Semtech, LoRa Alliance, IEEE Comms Surveys, IEEE IoT Journal, ACM MLSys, arXiv, v.v.).

---

### 📌 [PHỤ LỤC](file:///E:/DATN/LoRa_TinyML_Hopping/docs/PHU_LUC.md)
* **Phụ lục A:** Sơ đồ phần cứng và ánh xạ chân tín hiệu chi tiết (ESP32 DevKit V1 & Raspberry Pi CM4).
* **Phụ lục B:** Cấu hình tham số thực nghiệm vô tuyến RF và đặc tả bộ dữ liệu `dataset_ready.csv`.
* **Phụ lục C:** Trích đoạn mã nguồn nhúng C/C++ (`model.h`, FreeRTOS tasks) và pipeline TinyML.

---

## 📊 TỔNG HỢP CÁC KẾT QUẢ THỰC NGHIỆM CỐT LÕI

*Bảng đối sánh hiệu năng tổng thể của đề tài:*

| Tiêu chí kỹ thuật | Cơ chế Kênh Cố Định (Fixed Channel) | Cơ chế Nhảy Ngẫu Nhiên (Random Hopping) | Cơ chế Nhảy Thích Ứng TinyML (Đề tài) |
| :--- | :---: | :---: | :---: |
| **Độ nhận thức kênh (Awareness)** | Không có | Hoàn toàn mù va chạm (Collision-blind) | **Nhận thức lịch sử CSI qua cửa sổ trượt** |
| **Tỷ lệ nhận gói PDR (Gói 30B)** | $\approx 80\% - 85\%$ | $88.0\%$ | **$99.0\%$ ($+11.0\%$ gain)** |
| **Tỷ lệ nhận gói PDR (Gói 250B)**| Sụt giảm nghiêm trọng | $63.7\%$ (Va chạm nghiêm trọng) | **$95.0\%$ ($+31.3\%$ gain)** |
| **PDR Trung bình toàn dải** | $< 70\%$ | $79.9\%$ | **$97.8\%$ ($+17.9\%$ gain)** |
| **Chỉ số RSSI trung bình** | $-95.0\text{ dBm}$ | $-94.4\text{ dBm}$ | **$-71.5\text{ dBm}$ ($+22.9\text{ dBm}$)** |
| **Kiến trúc mô hình tối ưu** | — | — | **Separable 1D-CNN (878 tham số)** |
| **Dung lượng bộ nhớ Flash** | — | — | **$8.65\text{ KB}$ TFLite FlatBuffer** |
| **Dung lượng RAM Tensor Arena**| — | — | **$10\text{ KB}$ SRAM** |
| **Độ trễ suy luận thời gian thực**| — | — | **$9.3\text{ ms}$ trên ESP32 @ 240 MHz** |

---

## 🎨 THƯ MỤC SƠ ĐỒ ĐỒ HỌA GỐC (.DRAWIO)

Toàn bộ các hình vẽ kiến trúc, lưu đồ và sơ đồ phần cứng trong đồ án đã được xây dựng dưới định dạng **.drawio (Diagrams.net)** trực quan, tinh gọn, ít chú thích rườm rà và lưu trữ tại [docs/figs](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs) cũng như [figs](file:///E:/DATN/LoRa_TinyML_Hopping/figs):

* 📁 **Tệp tích hợp toàn bộ các trang (Master Multi-Page):**
  * [full_project_diagrams.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/full_project_diagrams.drawio) (Bao gồm đầy đủ 13 tab sơ đồ trong một tệp duy nhất).
* 📄 **Từng sơ đồ độc lập:**
  1. [01_kien_truc_iot_4_lop.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/01_kien_truc_iot_4_lop.drawio): Kiến trúc phân tầng hệ thống IoT (4 lớp).
  2. [02_nguyen_ly_dieu_che_lora_css.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/02_nguyen_ly_dieu_che_lora_css.drawio): Nguyên lý điều chế trải phổ Chirp (LoRa CSS).
  3. [03_kien_truc_mang_lorawan_star.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/03_kien_truc_mang_lorawan_star.drawio): Kiến trúc mạng LoRaWAN hình sao lồng nhau (Star-of-Stars).
  4. [04_so_sanh_cloud_ai_vs_edge_tinyml.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/04_so_sanh_cloud_ai_vs_edge_tinyml.drawio): So sánh mô hình Cloud AI truyền thống và Edge TinyML biên.
  5. [05_bai_toan_lua_chon_kenh_tinyml.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/05_bai_toan_lua_chon_kenh_tinyml.drawio): Cơ chế dự đoán và nhảy kênh thích ứng dựa trên TinyML.
  6. [06_so_do_khoi_toan_he_thong.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/06_so_do_khoi_toan_he_thong.drawio): Sơ đồ khối toàn hệ thống thực nghiệm (3 End-Nodes, Kênh RF, Multi-Receiver Gateway).
  7. [07_dinh_dang_khung_truyen_goi_tin.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/07_dinh_dang_khung_truyen_goi_tin.drawio): Cấu trúc định dạng khung truyền gói tin LoRa (Payload Structure).
  8. [08_5_kien_truc_tinyml.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/08_5_kien_truc_tinyml.drawio): Đối sánh cấu trúc 5 kiến trúc mạng nơ-ron TinyML.
  9. [09_pipeline_xu_ly_du_lieu.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/09_pipeline_xu_ly_du_lieu.drawio): Quy trình kỹ thuật xử lý & chuẩn hóa dữ liệu thực nghiệm.
  10. [10_bo_tri_thuc_dia_toa_nha.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/10_bo_tri_thuc_dia_toa_nha.drawio): Sơ đồ bố trí thực địa trong khuôn viên tòa nhà đại học.
  11. [11_kien_truc_freertos_da_nhiem.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/11_kien_truc_freertos_da_nhiem.drawio): Kiến trúc firmware đa nhiệm thời gian thực FreeRTOS trên ESP32.
  12. [12_so_do_noi_chan_end_node_esp32.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/12_so_do_noi_chan_end_node_esp32.drawio): Sơ đồ đấu nối chi tiết phần cứng thiết bị đầu cuối End-Node ESP32.
  13. [13_so_do_noi_chan_gateway_cm4.drawio](file:///E:/DATN/LoRa_TinyML_Hopping/docs/figs/13_so_do_noi_chan_gateway_cm4.drawio): Sơ đồ đấu nối Multi-Receiver Gateway trên Raspberry Pi CM4.

