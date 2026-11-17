# KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

---

## 1. Kết Quả Đạt Được Của Đề Tài

Sau quá trình nghiên cứu lý thuyết, thiết kế kiến trúc phần cứng, xây dựng mô hình thuật toán và triển khai thực nghiệm toàn diện, đề tài **"Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML"** đã hoàn thành trọn vẹn tất cả các mục tiêu học thuật và kỹ thuật đã đề ra theo đúng đề cương chi tiết. Các đóng góp và kết quả cốt lõi của đề tài bao gồm:

### 1. Về mặt nghiên cứu lý thuyết và phương pháp luận
* Đã hệ thống hóa và phân tích sâu sắc cơ sở lý thuyết viễn thông của công nghệ điều chế trải phổ Chirp (LoRa CSS), kiến trúc mạng LoRaWAN và cơ chế đa truy cập ngẫu nhiên Pure ALOHA.
* Đã mô hình hóa toán học mối quan hệ giữa kích thước tải trọng ($PL = 30\text{B} - 250\text{B}$), thời gian chiếm dụng môi trường truyền dẫn ($ToA$), khoảng thời gian xung đột nguy hiểm ($T_v = 2 \times ToA$) và xác suất va chạm gói tin ($P_{coll} = 1 - e^{-2G}$). Qua đó, luận giải tường minh nguyên nhân gốc rễ gây sụt giảm nghiêm trọng tỷ lệ nhận gói (PDR) trong các mạng LoRa truyền thống sử dụng kênh cố định hoặc nhảy kênh ngẫu nhiên (Random Hopping).
* Đã chuyển hóa thành công bài toán tối ưu hóa kênh truyền thành bài toán phân loại đa lớp theo chuỗi thời gian dựa trên các chỉ số trạng thái kênh thực tế (CSI: $RSSI, SNR, ToA$), mở ra hướng giải quyết triệt để vấn đề va chạm thông qua trí tuệ nhân tạo nhúng biên (TinyML).

### 2. Về mặt thiết kế phần cứng và thu thập dữ liệu thực nghiệm
* Đã thiết kế, chế tạo và thử nghiệm thành công phân hệ 03 End-Nodes hoàn chỉnh sử dụng vi điều khiển ESP32 DevKit V1 kết hợp module vô tuyến Semtech SX1278 (Ra-02 $433\text{ MHz}$) và màn hình hiển thị OLED SSD1306. Thiết kế phần cứng đã giải quyết triệt để bài toán ổn định điện áp và triệt tiêu xung dòng đỉnh $130\text{ mA}$ bằng mạch phối hợp tụ lọc nguồn ($100\mu\text{F} + 100\text{nF}$).
* Đã xây dựng trạm Gateway đa kênh (Multi-Receiver Architecture) dựa trên máy tính nhúng Raspberry Pi Compute Module 4 (CM4) tích hợp đồng thời 03 module thu SX1278 độc lập lắng nghe song song trên 3 kênh tần số ($433.175\text{ MHz}$, $433.375\text{ MHz}$, $433.575\text{ MHz}$). Kiến trúc Zero-Blindness này đảm bảo khả năng thu trọn $100\%$ các gói tin phát ra từ các node mà không bị hiện tượng mù máy thu.
* Đã thực hiện kịch bản đo đạc quy chuẩn quét kích thước tải trọng (Payload Sweeping Protocol), thu thập thành công bộ dữ liệu gồm **$21,600\text{ gói tin thực tế}$** phản ánh chân thực môi trường truyền sóng qua nhiều lớp tường bê tông và hành lang tòa nhà đại học.

### 3. Về mặt xây dựng mô hình TinyML và tối ưu hóa phần mềm nhúng
* Đã thiết kế hoàn chỉnh Pipeline kỹ thuật dữ liệu tự động: phát hiện và bù đắp các gói tin bị mất mát, tạo cửa sổ trượt $W = 10\text{ bước}$ ($\times 9\text{ đặc trưng}$) và loại bỏ hoàn toàn hiện tượng rò rỉ nhãn (Label Leakage).
* Đã nghiên cứu, huấn luyện và đánh giá đối soát đa mục tiêu giữa 5 kiến trúc mạng nơ-ron:
  1. *Baseline FCNN (MLP)*
  2. *Temporal Convolutional Neural Network (1D-CNN)*
  3. *Gated Recurrent Unit (GRU RNN)*
  4. *Depthwise Separable 1D-CNN (MobileNet-style)*
  5. *Residual Neural Network (ResNet-1D)*
* Đã giải quyết thành công bài toán kiểm soát quá khớp (Overfitting) bằng việc kết hợp điều chuẩn trọng số $L_2$ Regularization ($\lambda = 2 \times 10^{-4}$), Dropout ($p = 0.15$) và bộ lập lịch tốc độ học thích ứng ReduceLROnPlateau. Quá trình huấn luyện $200\text{ epochs}$ thể hiện rõ ràng tiến trình học tập chuẩn mực: từ khởi tạo dần đều, xuất hiện **điểm dao động chuyển tiếp gồ ghề (Intermediate Perturbation)** tại epoch 60–75 khi mạng tái định hình không gian trọng số, cho đến khi đạt trạng thái bão hòa thực sự ổn định tại epoch 140–200.
* Đã xác định **Depthwise Separable 1D-CNN** là kiến trúc tối ưu vượt bậc cho phần cứng vi điều khiển biên:
  * Số lượng tham số ít nhất: **$878\text{ tham số}$** (tiết kiệm hơn $63\%$ phép tính so với CNN tiêu chuẩn).
  * Dung lượng tệp FlatBuffer TFLite cực kỳ nhỏ: **$8.65\text{ KB}$**.
  * Không gian bộ nhớ đệm Tensor Arena tĩnh chỉ: **$10\text{ KB}$ RAM**.
  * Độ trễ suy luận thời gian thực siêu nhanh: **$9.3\text{ ms}$** trên xung nhịp ESP32 $240\text{ MHz}$.
  * Độ chính xác kiểm thử độc lập cao nhất nhóm: **$90.51\%$**.
* Đã phát triển firmware nhúng thời gian thực đa nhiệm trên nền tảng FreeRTOS, phân bổ tối ưu các tác vụ thu thập cảm biến, hiển thị OLED, suy luận TFLM và phát sóng RF trên cả 2 nhân vi xử lý (Core 0 và Core 1).

### 4. Về mặt hiệu năng vô tuyến thực nghiệm đối chứng
* Kết quả thực nghiệm đối đầu trực tiếp với cơ chế nhảy kênh ngẫu nhiên (Random Hopping) đã khẳng định tính ưu việt vượt trội của giải pháp:
  * Duy trì tỷ lệ phân phối gói tin thành công **$\text{PDR} \ge 95.0\% - 100.0\%$** ổn định tuyệt đối xuyên suốt mọi kích thước tải trọng từ $30\text{ Bytes}$ đến $250\text{ Bytes}$ (trung bình toàn dải đạt **$97.8\%$**).
  * Khắc phục triệt để hiện tượng sụt giảm hiệu năng khi tải trọng mở rộng: trong khi Random Hopping bị rơi tự do xuống chỉ còn $63.7\%$ ở gói $250\text{B}$ do thời gian chiếm sóng ToA kéo dài, TinyML Hopping vẫn đạt $95.0\%$ (tạo mức tăng trưởng **$+31.3\%$ PDR**).
  * Nâng cao chất lượng kênh truyền vật lý: chỉ số RSSI trung bình được cải thiện hơn **$+22.9\text{ dBm}$** (từ $-94.4\text{ dBm}$ lên $-71.5\text{ dBm}$) và chỉ số SNR tăng thêm **$+2.1\text{ dB}$**, chứng minh mô hình học máy tự động ưu tiên lựa chọn những kênh truyền có đường truyền quang đãng và ít tạp âm nhất.

---

## 2. Hạn Chế Của Đề Tài

Mặc dù đã đạt được nhiều kết quả thực nghiệm ấn tượng, đề tài vẫn còn tồn tại một số hạn chế nhất định do giới hạn về thời gian và điều kiện cơ sở vật chất:

1. **Quy mô số lượng nút mạng thử nghiệm:** Hệ thống thực nghiệm hiện tại mới triển khai trên quy mô 03 End-Nodes đồng thời. Mặc dù các kịch bản kích thước gói tin lớn ($250\text{ Bytes}$) và chu kỳ phát dày đặc ($1.5\text{ s}$) đã tạo ra tải lưu lượng tương đương với hàng chục node trong điều kiện vận hành thông thường, nhưng việc kiểm thử trên quy mô hàng trăm hoặc hàng nghìn node thực tế vẫn chưa được thực hiện.
2. **Số lượng kênh tần số phân bổ:** Đề tài tập trung thử nghiệm trên 3 kênh tần số vô tuyến đặc trưng của dải $433\text{ MHz}$ ISM ($433.175, 433.375, 433.575\text{ MHz}$). Mặc dù mô phỏng mở rộng (Scalability Analysis) đã chứng minh tính khả thi của mô hình khi mở rộng lên $8$ hay $16\text{ kênh}$, nhưng việc xác thực phần cứng cho 16 kênh đòi hỏi hệ thống Gateway phải trang bị tới 16 module RF độc lập, vượt quá khả năng phần cứng hiện có.
3. **Môi trường đo đạc tĩnh (Static Environment):** Các node cảm biến trong thử nghiệm được đặt tại các vị trí cố định trong khuôn viên trường. Các kịch bản di động (Mobile Nodes) với hiệu ứng dịch chuyển Doppler và hiện tượng Fading biến thiên nhanh chưa được khảo sát sâu.
4. **Cơ chế cập nhật mô hình học máy (Online Learning / Federated Learning):** Mô hình TinyML hiện tại được huấn luyện theo phương thức Offline (huấn luyện trên máy tính và nạp cố định vào Flash của ESP32). Vi điều khiển chưa có khả năng tự tinh chỉnh trọng số (On-Device Incremental Learning) khi môi trường vô tuyến có sự thay đổi đột ngột dài hạn.

---

## 3. Hướng Nghiên Cứu Và Phát Triển Tiếp Theo

Từ những kết quả đã đạt được và các hạn chế nêu trên, nhóm nghiên cứu đề xuất các định hướng mở rộng tiềm năng trong tương lai:

1. **Nâng cấp cơ chế học trực tuyến trên thiết bị (On-Device Incremental TinyML):**
   * Nghiên cứu khả năng cập nhật lớp phân loại cuối cùng (Transfer Learning / Few-Shot Learning) trực tiếp trên ESP32 mà không cần nạp lại toàn bộ firmware.
   * Áp dụng kỹ thuật học tăng cường sâu (Deep Reinforcement Learning - DRL) dạng nhẹ như Deep Q-Network (DQN) hoặc Q-Learning lượng tử hóa để node tự động tương tác và tối ưu hóa chính sách nhảy kênh liên tục theo thời gian thực.
2. **Tích hợp cơ chế thích ứng tốc độ dữ liệu thông minh (Intelligent ADR):**
   * Kết hợp song song giữa việc lựa chọn kênh truyền tối ưu với việc tự động điều chỉnh Hệ số trải phổ ($SF7 - SF12$) và Công suất phát ($Tx\text{ Power}$) dựa trên dự đoán của TinyML, nhằm tối ưu hóa tối đa năng lượng tiêu thụ cho từng gói tin.
3. **Mở rộng sang các dải tần số chuẩn quốc tế:**
   * Mở rộng triển khai hệ thống trên các băng tần thương mại phổ biến của LoRaWAN như $868\text{ MHz}$ (châu Âu) và $915\text{ MHz}$ (Bắc Mỹ), tích hợp tuân thủ các quy định chu kỳ phát sóng (Duty Cycle $1\%$) và kiểm thử cơ chế nghe trước khi nói (Listen-Before-Talk - LBT) kết hợp TinyML.
4. **Phát triển mạng học liên hiệp phân tán (Federated TinyML for LoRaWAN):**
   * Thiết lập cơ chế Học liên hiệp (Federated Learning): các End-Node tự cập nhật gradient trọng số từ dữ liệu cục bộ và định kỳ gửi vector gradient nhỏ gọn về Gateway/Network Server để tổng hợp thành mô hình toàn cục (Global Model), sau đó phát quảng bá ngược lại cho toàn mạng. Cơ chế này vừa bảo vệ quyền riêng tư vừa nâng cao độ chính xác dự đoán cho toàn bộ hệ thống IoT diện rộng.
