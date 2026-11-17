# LỜI MỞ ĐẦU

---

## 1. Lý Do Chọn Đề Tài

Trong kỷ nguyên vạn vật kết nối Internet (Internet of Things - IoT) và chuyển đổi số mạnh mẽ, nhu cầu thu thập dữ liệu từ hàng triệu thiết bị cảm biến phân tán trên diện rộng ngày càng trở nên cấp thiết. Các ứng dụng như nông nghiệp thông minh, giám sát hạ tầng đô thị, quản lý năng lượng và quan trắc môi trường đòi hỏi công nghệ truyền thông không dây có khả năng truyền xa hàng kilômét, hoạt động bền bỉ trong nhiều năm bằng năng lượng pin và chi phí hạ tầng thấp. Trong số các công nghệ mạng diện rộng công suất thấp (Low Power Wide Area Network - LPWAN), công nghệ LoRa (Long Range) và giao thức mạng LoRaWAN đã nổi lên như một trong những giải pháp hàng đầu nhờ sử dụng kỹ thuật điều chế trải phổ Chirp (Chirp Spread Spectrum - CSS) trên các băng tần không cấp phép (ISM band).

Tuy nhiên, khi mật độ các thiết bị đầu cuối (End-Nodes) trong mạng LoRaWAN gia tăng với quy mô lớn, hệ thống phải đối mặt với thách thức suy giảm chất lượng nghiêm trọng do cơ chế truy cập kênh ngẫu nhiên không điều khiển Pure ALOHA. Ở cơ chế này, các node phát dữ liệu một cách độc lập ngay khi có gói tin mà không có bước lắng nghe kênh trước (Listen-Before-Talk - LBT) hoặc LBT kém hiệu quả do độ nhạy của sóng LoRa thấp hơn mức nhiễu nền vô tuyến. Hậu quả là xác suất va chạm xung đột gói tin (Packet Collision) trên không tăng vọt theo hàm mũ khi lưu lượng tải mạng tăng, đặc biệt khi các gói tin có kích thước tải trọng (Payload Size) lớn làm kéo dài thời gian chiếm dụng sóng (Time-on-Air - ToA).

Các giải pháp truyền thống hiện nay bộc lộ nhiều hạn chế cố hữu:
1. **Truyền trên kênh cố định (Fixed Channel):** Dễ bị nghẽn mạng cục bộ khi số lượng thiết bị trên kênh tăng, và hoàn toàn mất liên lạc nếu xuất hiện nguồn can nhiễu ngoại lai liên tục (fading sâu hoặc nhiễu băng tần).
2. **Nhảy kênh ngẫu nhiên (Random Channel Hopping):** Mặc dù phân tán được tải lưu lượng trên nhiều tần số, nhưng cơ chế này là "mù va chạm" (collision-blind) do không nhận thức được trạng thái môi trường truyền dẫn thời gian thực. Các node có thể cùng nhảy ngẫu nhiên vào cùng một kênh tại cùng một thời điểm, dẫn đến va chạm không thể tránh khỏi.
3. **Cơ chế tập trung tại Gateway / Network Server (Adaptive Data Rate - ADR):** Yêu cầu trao đổi nhiều bản tin điều khiển đường xuống (Downlink), làm tiêu hao năng lượng pin của node và bị giới hạn nghiêm ngặt bởi quy định chu kỳ hoạt động vô tuyến (Duty Cycle) của băng tần ISM.

Sự phát triển đột phá của Trí tuệ nhân tạo trên vi điều khiển (Tiny Machine Learning - TinyML) mở ra một hướng tiếp cận hoàn toàn mới: đưa khả năng suy luận trí tuệ nhân tạo trực tiếp xuống các vi điều khiển công suất thấp (End-Nodes). Thay vì nhảy kênh thụ động hay ngẫu nhiên, thiết bị đầu cuối có thể chủ động theo dõi lịch sử thông tin trạng thái kênh (Channel State Information - CSI) như RSSI, SNR, chuỗi thời gian gói tin, từ đó dự đoán kênh truyền ít va chạm nhất trước mỗi lượt phát sóng. Hướng giải pháp này hứa hẹn triệt tiêu va chạm, duy trì tỷ lệ phân phối gói tin thành công (Packet Delivery Ratio - PDR) ở mức cao vượt trội mà không làm tăng năng lượng tiêu thụ hay quá tải bộ nhớ vi điều khiển.

Xuất phát từ những yêu cầu khoa học và ứng dụng thực tiễn trên, đề tài **"Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML"** được nhóm nghiên cứu lựa chọn và phát triển nhằm xây dựng một giải pháp thực nghiệm toàn diện từ mô hình thuật toán đến triển khai phần cứng nhúng.

---

## 2. Mục Tiêu Nghiên Cứu

Đề tài hướng tới các mục tiêu nghiên cứu học thuật và kỹ thuật thực nghiệm cụ thể sau:

1. **Nghiên cứu cơ sở lý thuyết viễn thông và cơ chế đa truy cập:** Phân tích bản chất vật lý của công nghệ điều chế LoRa CSS, mô hình hóa toán học xác suất va chạm trong cơ chế Pure ALOHA, đánh giá ảnh hưởng của các siêu tham số vô tuyến ($SF, BW, CR, ToA$) và kích thước tải trọng ($30\text{B} - 250\text{B}$) đến chất lượng kênh truyền.
2. **Thiết kế và triển khai kiến trúc phần cứng thực nghiệm:**
   - Xây dựng hệ thống 03 End-Nodes sử dụng vi điều khiển ESP32 kết hợp module vô tuyến Semtech SX1278 (Ra-02 $433\text{ MHz}$) và màn hình hiển thị OLED SSD1306.
   - Phát triển trạm thu đa kênh (Multi-Channel Gateway) sử dụng máy tính nhúng Raspberry Pi Compute Module 4 (CM4) tích hợp 03 module thu SX1278 độc lập lắng nghe song song trên 3 kênh tần số, đảm bảo thu thập dữ liệu với tính toàn vẹn cao (Zero-Blindness).
3. **Xây dựng quy trình xử lý dữ liệu và trích xuất đặc trưng chuỗi thời gian:** Thiết kế Pipeline kỹ thuật dữ liệu hoàn chỉnh, phát hiện và bù đắp các gói tin bị mất mát, tạo bộ dữ liệu chuỗi thời gian trượt (Sliding Window $W = 10$ bước) phản ánh chính xác trạng thái vô tuyến đa kênh mà không bị rò rỉ nhãn (Label Leakage).
4. **Nghiên cứu, huấn luyện và đối sánh đa kiến trúc mạng nơ-ron TinyML:** Thiết kế, kiểm thử và so sánh 5 kiến trúc mạng nơ-ron:
   - *Baseline Multi-Layer Perceptron (FCNN)*
   - *Temporal Convolutional Neural Network (1D-CNN)*
   - *Gated Recurrent Unit (GRU RNN)*
   - *Depthwise Separable 1D-CNN (MobileNet-style)*
   - *Residual Neural Network (ResNet-1D)*
   Đánh giá đa mục tiêu dựa trên các tiêu chí: Độ chính xác (Accuracy), Hàm mất mát (Loss), Sai số tuyệt đối trung bình (MAE), Dung lượng bộ nhớ Flash/RAM (TFLite Model Size), và Thời gian suy luận (Inference Latency).
5. **Nhúng mô hình TinyML tối ưu lên firmware vi điều khiển ESP32:** Tối ưu hóa mô hình bằng TensorFlow Lite for Microcontrollers (TFLM), cấu hình quản lý bộ nhớ đệm Tensor Arena, phát triển firmware nhúng thời gian thực đa nhiệm trên nền tảng FreeRTOS.
6. **Đánh giá hiệu năng thực nghiệm trên mạng vô tuyến thực tế:** Thực hiện đối sánh toàn diện giữa cơ chế nhảy kênh dựa trên TinyML và cơ chế nhảy kênh ngẫu nhiên (Random Hopping) trong các điều kiện kích thước gói tin biến thiên từ $30\text{ Bytes}$ đến $250\text{ Bytes}$.

---

## 3. Phạm Vi Nghiên Cứu

* **Băng tần và thông số vật lý vô tuyến:** Hệ thống được thử nghiệm trên băng tần ISM $433\text{ MHz}$ với 3 kênh tần số phân tách: $CH1 = 433.175\text{ MHz}$, $CH2 = 433.375\text{ MHz}$, và $CH3 = 433.575\text{ MHz}$. Băng thông $BW = 125\text{ kHz}$, hệ số trải phổ $SF = 7$, tốc độ mã hóa $CR = 4/5$, công suất phát $17\text{ dBm}$. Khoảng cách bảo vệ giữa các kênh lân cận được thiết lập là $200\text{ kHz}$ nhằm ngăn chặn triệt để can nhiễu lân kênh (Adjacent Channel Interference).
* **Quy mô hệ thống thử nghiệm:** Gồm 03 End-Nodes phát dữ liệu đồng thời với các kịch bản kích thước gói tin khác nhau nhằm tạo ra áp lực lưu lượng và xác suất va chạm cao, cùng 01 Multi-Channel Gateway thu thập và phân tích dữ liệu tập trung.
* **Nền tảng vi điều khiển biên:** Mô hình học máy được tối ưu hóa nhúng trực tiếp trên chip ESP32 DevKit V1 (kiến trúc Xtensa Dual-Core 32-bit LX6 @ $240\text{ MHz}$, $520\text{ KB}$ SRAM), chạy độc lập mà không cần kết nối máy chủ đám mây để ra quyết định nhảy kênh.

---

## 4. Phương Pháp Nghiên Cứu

Đề tài áp dụng kết hợp chặt chẽ giữa nghiên cứu lý thuyết, mô phỏng tính toán và thực nghiệm phần cứng thực tế:

1. **Phương pháp mô hình hóa toán học:** Sử dụng lý thuyết xác suất và quá trình ngẫu nhiên để mô hình hóa quá trình truyền tin Pure ALOHA, tính toán thời gian truyền sóng trên không $ToA$, ước lượng chu kỳ xung đột $T_v$ và xác suất va chạm gói tin.
2. **Phương pháp thực nghiệm viễn thông (Empirical RF Measurement):** Bố trí kịch bản thực nghiệm đo đạc thực tế, ghi nhận các đặc trưng vật lý truyền sóng (RSSI, SNR, Packet Delivery Ratio - PDR, Packet ID) từ các module Semtech SX1278 trong môi trường thực địa.
3. **Phương pháp học máy và tối ưu hóa nhúng (TinyML Optimization):** Sử dụng các kỹ thuật tiền xử lý chuẩn hóa Z-Score, phân chia dữ liệu Train/Validation/Test khách quan, áp dụng kỹ thuật điều chuẩn $L_2$ Regularization và Dropout để chống quá khớp (Overfitting), lượng tử hóa mô hình và biên dịch sang mảng byte C header (`model.h`) tối ưu cho bộ xử lý nhúng.
4. **Phương pháp so sánh đối chứng (Comparative Benchmark):** Đánh giá hiệu quả cải tiến bằng cách đo đạc song song giữa cơ chế nhảy kênh ngẫu nhiên (Random Hopping) và cơ chế nhảy kênh thích ứng dựa trên TinyML trong cùng điều kiện thực nghiệm vô tuyến.

---

## 5. Bố Cục Đồ Án

Nội dung đồ án được kết cấu thành 3 chương chính cùng phần mở đầu, kết luận, tài liệu tham khảo và phụ lục:

* **LỜI MỞ ĐẦU:** Giới thiệu bối cảnh, lý do chọn đề tài, mục tiêu, phạm vi, phương pháp nghiên cứu và bố cục tổng thể.
* **CHƯƠNG 1: TỔNG QUAN VỀ HỆ THỐNG LORAWAN:** Trình bày tổng quan về mạng IoT, công nghệ LPWAN và vị thế của LoRaWAN; cấu trúc phân tầng vật lý và giao thức MAC LoRaWAN; phân tích các yếu tố ảnh hưởng đến chất lượng kênh truyền, các chỉ số đánh giá ($RSSI, SNR, PDR$); giới thiệu xu hướng Edge AI và tiềm năng đột phá của TinyML trên vi điều khiển.
* **CHƯƠNG 2: MÔ HÌNH HỌC MÁY TINYML CHO HỆ THỐNG LORAWAN:** Định nghĩa toán học bài toán lựa chọn kênh tối ưu; thiết kế sơ đồ khối và triển khai phần cứng trạm phát và trạm thu Gateway; đặc tả cấu trúc gói tin và kịch bản thực nghiệm thu thập dữ liệu; phân tích chi tiết 5 kiến trúc mạng nơ-ron TinyML phù hợp cho thiết bị biên.
* **CHƯƠNG 3: TRIỂN KHAI THỰC NGHIỆM TRÊN VI XỬ LÝ LORA ESP32 VÀ ĐÁNH GIÁ:** Trình bày chi tiết pipeline tiền xử lý dữ liệu chuỗi thời gian, quy trình huấn luyện 5 mô hình nơ-ron và đối sánh hiệu năng; thiết lập môi trường kiểm thử thực nghiệm và quy trình nhúng mô hình lên vi điều khiển ESP32 với FreeRTOS; phân tích kết quả mô phỏng và thực nghiệm so sánh với Random Hopping.
* **KẾT LUẬN & HƯỚNG PHÁT TRIỂN:** Tổng kết các kết quả khoa học đạt được, chỉ ra những hạn chế còn tồn tại và đề xuất các hướng mở rộng trong tương lai.
* **TÀI LIỆU THAM KHẢO:** Danh mục tài liệu khoa học chuẩn mực quốc tế và tài liệu kỹ thuật chuyên ngành.
* **PHỤ LỤC:** Sơ đồ nguyên lý phần cứng, đặc tả cấu hình chi tiết, mô tả bộ dữ liệu và trích đoạn mã nguồn firmware/pipeline.
