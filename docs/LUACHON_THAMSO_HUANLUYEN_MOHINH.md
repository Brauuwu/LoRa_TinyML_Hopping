# Tài Liệu Lựa Chọn và Tối Ưu Hóa Tham Số Huấn Luyện Mô Hình TinyML
## Đề tài: Nhảy kênh dự đoán thích ứng (Predictive Channel Hopping) cho mạng LoRa End-Node

---

## 1. Giới thiệu và Bối cảnh Kỹ thuật

Mục tiêu của mô hình Machine Learning trong đề tài là thực thi trực tiếp tại biên trên vi điều khiển **ESP32** (tần số 240 MHz, SRAM khả dụng cho ML $\approx 50 - 100 \text{ KB}$), có nhiệm vụ phân tích lịch sử kênh truyền vô tuyến trong quá khứ để **dự đoán kênh truyền tối ưu tiếp theo (Next Best Channel)** trong số 3 kênh dải $433\text{ MHz}$ (`433.175 MHz`, `433.375 MHz`, `433.575 MHz`), nhằm chủ động né tránh va chạm xung đột trên không và suy hao đường truyền.

Do tài nguyên phần cứng bị giới hạn khắt khe và đặc thù kênh vô tuyến biến động liên tục theo thời gian, việc lựa chọn siêu tham số (Hyperparameters) không chỉ hướng đến **độ chính xác (Accuracy)** mà bắt buộc phải giải quyết bài toán đa mục tiêu:
1. **Khả năng tổng quát hóa (Generalization):** Tránh hiện tượng học vẹt (Overfitting) vào nhiễu tức thời của môi trường thực nghiệm.
2. **Kích thước mô hình (Footprint):** Mảng nhị phân sau nén/lượng tử hóa FlatBuffer phải $\le 10 \text{ KB}$ để vừa vặn trong Flash/SRAM.
3. **Thời gian suy luận (Inference Latency):** Thời gian tính toán trên ESP32 phải $< 10 \text{ ms}$ (lý tưởng $< 1 \text{ ms}$ trên mô phỏng CPU) để không làm trễ chu kỳ phát sóng Time-on-Air của LoRa.

---

## 2. Bảng Tổng Hợp Siêu Tham Số Huấn Luyện Chuẩn

Toàn bộ các tham số dưới đây được cấu hình chính thức trong script huấn luyện [[04_train_model.py](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/scripts/04_train_model.py)] và xuất bản ra các file C header nhúng trong thư mục [[TinyML/models/](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/models)]:

| Tham số (Hyperparameter) | Giá trị lựa chọn | Vai trò & Lý do kỹ thuật |
| :--- | :---: | :--- |
| **Kích thước cửa sổ trượt ($T$)** | `10` bước | Đủ dài để bắt nhịp chu kỳ truyền thông của các node cạnh tranh, đủ ngắn để tiết kiệm bộ nhớ đệm RAM trên ESP32. |
| **Số đặc trưng mỗi bước ($F$)** | `9` đặc trưng | Gồm RSSI, SNR, kích thước gói, ID, tần số và 3 cờ kênh (CH1, CH2, CH3) phản ánh toàn diện CSI (Channel State Information). |
| **Kích thước Tensor đầu vào** | `(10, 9)` hoặc phẳng `90` | Vector $90$ chiều chuẩn hóa tĩnh, ánh xạ trực tiếp sang mảng C `float raw_history[10][9]`. |
| **Số lớp đầu ra ($K$)** | `3` lớp | Tương ứng 3 kênh nhảy tần: CH0 ($433.175\text{ MHz}$), CH1 ($433.375\text{ MHz}$), CH2 ($433.575\text{ MHz}$). |
| **Tỷ lệ phân chia tập dữ liệu** | `60% / 20% / 20%` | 60% Train, 20% Validation (kiểm soát quá khớp), 20% Test (đối soát độc lập khách quan). |
| **Phương pháp chuẩn hóa** | `StandardScaler` | Đưa phân phối RSSI và SNR về trung bình $\mu=0, \sigma=1$, loại bỏ độ lệch thang đo giữa RSSI (âm) và SNR. |
| **Số lượng Epochs** | `200` epochs | Đảm bảo Loss trên cả Train và Validation đi hết giai đoạn giảm dốc và tiệm cận trạng thái bão hòa hoàn toàn. |
| **Kích thước Batch (Batch Size)** | `64` mẫu | Cân bằng giữa độ mịn của gradient descent và tốc độ hội tụ trên dữ liệu chuỗi thời gian tabular. |
| **Tốc độ học ban đầu (Initial LR)**| `0.002` | Khởi đầu hội tụ nhanh với thuật toán tối ưu hóa Adam. |
| **Bộ lập lịch Learning Rate** | `ReduceLROnPlateau` | Giảm 50% LR (`factor=0.5`) khi `val_loss` đi ngang sau 10 epochs, chạm đáy `1e-5`. |
| **Hàm mất mát (Loss Function)** | `Categorical Crossentropy`| Phù hợp bài toán phân loại đa lớp xác suất với Softmax đầu ra và nhãn One-Hot cứng. |
| **Ràng buộc trọng số ($L_2$)** | `2e-4` ($0.0002$) | Phạt độ lớn ma trận trọng số, ngăn nơ-ron học thuộc các đỉnh nhiễu RSSI ngoại lai. |
| **Tỷ lệ ngắt kết nối (Dropout)** | `0.15` (15%) | Ngắt ngẫu nhiên các liên kết nơ-ron trong quá trình train, tăng cường tính chịu lỗi của mạng. |

---

## 3. Phân Tích Chuyên Sâu Từng Quyết Định Thiết Kế

### 3.1. Kích thước Cửa Sổ Trượt Thời Gian ($T = 10$)
- **Cơ sở lý thuyết:** Kênh truyền vô tuyến mang tính phụ thuộc thời gian (Markovian Process bậc thấp). Trạng thái kênh ở bước $t+1$ phụ thuộc vào xác suất các nút cạnh tranh vừa phát sóng ở các bước $t, t-1, \dots, t-k$.
- **Tại sao chọn $T = 10$ thay vì $T = 5$ hoặc $T = 20$:**
  - Nếu $T < 5$: Cửa sổ quá ngắn, mô hình không nắm bắt được chu kỳ phát lặp lại của 2 nút cạnh tranh kia (vốn truyền theo chu kỳ $1 - 3\text{ giây}$).
  - Nếu $T > 15$: Kích thước vector đầu vào tăng vọt ($> 150 \text{ phần tử}$), làm tăng dung lượng mảng bộ đệm đè lên vi điều khiển ESP32, đồng thời độ trễ trượt ban đầu (Cold Start) khi khởi động thiết bị phải chờ quá lâu mới đủ dữ liệu suy luận.
  - Giá trị $T = 10$ gói tin ($\approx 15 - 30\text{ giây}$ vận hành) là điểm cân bằng tối ưu giữa độ chính xác dự báo và bộ đệm FIFO vi điều khiển.

### 3.2. Chuẩn Hóa Đặc Trưng bằng `StandardScaler`
- Dữ liệu thu thập có sự chênh lệch đơn vị rất lớn:
  - `RSSI`: dải giá trị từ $-130\text{ dBm}$ đến $-30\text{ dBm}$ (số âm lớn).
  - `SNR`: dải giá trị từ $-15\text{ dB}$ đến $+12\text{ dB}$.
  - `size_of_message`: $30, 74, 118, 162, 206, 250\text{ bytes}$.
- Nếu không chuẩn hóa, Gradient Descent sẽ bị chi phối bởi các giá trị có biên độ lớn (như RSSI hoặc kích thước byte), khiến trọng số cập nhật méo mó và khó hội tụ.
- **Triển khai nhúng:** Bộ tham số trung bình (`SCALER_MEAN`) và phương sai (`SCALER_SCALE`) được trích xuất tự động và nhúng cứng thành mảng hằng số `const float` trong file header [[TinyML/models/model_separable_1d_cnn.h](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/models/model_separable_1d_cnn.h)], cho phép ESP32 chuẩn hóa dữ liệu thời gian thực chỉ với 1 phép trừ và 1 phép chia với độ phức tạp $O(1)$.

### 3.3. Số Lượng Epochs ($200$) và Cơ Chế Bão Hòa Loss
- **Hiện tượng thực nghiệm:** Khi huấn luyện ở số epoch thấp ($30 - 50$ epochs), mô hình mới chỉ học được các đặc trưng bề mặt, tỷ lệ Loss trên tập Train và Validation vẫn đang trên đà lao dốc, độ chính xác dao động chưa ổn định.
- **Tại sao chọn 200 Epochs:**
  - Từ epoch thứ 80 đến 120, nhờ bộ lập lịch `ReduceLROnPlateau`, Learning Rate giảm dần từ `0.002` xuống `0.001` rồi `0.0005`.
  - Từ epoch thứ 140 đến 200, đồ thị `Training Loss` và `Validation Loss` **đi ngang song song và tiệm cận đáy bão hòa** ($\approx 0.35 - 0.45$).
  - Độ chính xác trên tập Test ổn định vững chắc trong dải **$85\% - 90\%$**, không có hiện tượng Validation Loss bật tăng ngược trở lại (bằng chứng mô hình không bị Overfitting).

```
Loss
 │
1.2 ──┐ Training Loss (Đỏ)
1.0   │\ 
0.8   │ \   Validation Loss (Xanh)
0.6   │  \──────┐
0.4   │   \     └──────────────────── Bão hòa ổn định (Epoch 140-200)
0.2   │    └─────────────────────────
0.0 ──┴───────────────────────────────► Epochs
      0    50    100   150   200
```

### 3.4. Kiểm Soát Quá Khớp: $L_2$ Regularization & Dropout
- **Regularization $L_2 = 2 \times 10^{-4}$:**
  - Hàm mục tiêu tối ưu được bổ sung số hạng phạt: $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{CE}} + \lambda \sum w_i^2$.
  - Ngăn không cho các trọng số của lớp Dense hoặc Conv1D tăng trưởng quá lớn nhằm ép mô hình tìm ra các đường ranh giới quyết định (decision boundaries) mượt mà hơn trên không gian RSSI/SNR.
- **Dropout $15\%$:**
  - Trong mỗi lượt cập nhật mini-batch, $15\%$ nơ-ron ngẫu nhiên bị tạm thời ngắt kết nối. Điều này ép các nơ-ron còn lại phải học các biểu diễn độc lập thay vì phụ thuộc lẫn nhau, tăng cường khả năng thích ứng khi môi trường truyền thông LoRa có nhiễu đột ngột.

### 3.5. Kỹ Thuật Global Average Pooling (GAP) thay cho Flatten
- Trong các mô hình dạng chuỗi như 1D-CNN hoặc Separable 1D-CNN:
  - Nếu dùng lớp `Flatten()` cổ điển: Số kết nối sang lớp Dense tiếp theo sẽ là $T \times \text{Filters} \times \text{Neurons} \approx 10 \times 32 \times 16 = 5.120$ trọng số $\rightarrow$ Kích thước mô hình phình to $> 20\text{ KB}$, rất dễ gây Overfitting.
  - Sử dụng `GlobalAveragePooling1D()`: Tính trung bình dọc theo trục thời gian của từng kênh đặc trưng, giảm kích thước vector xuống chỉ còn đúng bằng số lượng Filters ($32$ giá trị).
  - Kết quả: Giảm hơn $70\%$ số lượng tham số, mô hình chỉ còn khoảng $1.400 - 3.100$ tham số, kích thước TFLite chỉ từ $2.5 - 4.5\text{ KB}$, hoàn toàn giải phóng bộ nhớ RAM cho ESP32.

---

## 4. Ma Trận Đối Sánh và Lựa Chọn Kiến Trúc Tối Ưu

Dựa trên kết quả đo đạc thực nghiệm từ script [[06_benchmark_models.py](file:///e:/DATN/LoRa_TinyML_Hopping/TinyML/scripts/06_benchmark_models.py)]:

| Kiến trúc mạng | Số lượng tham số | Kích thước TFLite | Độ trễ Latency ($\mu\text{s}$) | Test Accuracy | Khuyến nghị lựa chọn |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Baseline FCNN (MLP)** | $1.707$ | $2.52\text{ KB}$ | $\approx 22\ \mu\text{s}$ | $86.8\%$ | Dễ triển khai nhất, bộ nhớ cực thấp. |
| **Separable 1D-CNN** | **$1.411$** | **$3.14\text{ KB}$** | **$\approx 35\ \mu\text{s}$** | **$88.6\%$** | **Tối ưu toàn diện nhất (Khuyên dùng)** |
| **1D-CNN chuẩn** | $3.155$ | $4.85\text{ KB}$ | $\approx 48\ \mu\text{s}$ | $88.2\%$ | Độ chính xác cao, tham số mức trung bình. |
| **ResNet-1D (Skip)** | $2.851$ | $4.42\text{ KB}$ | $\approx 55\ \mu\text{s}$ | $87.9\%$ | Khả năng trích xuất sâu, cấu trúc phức tạp. |
| **GRU-RNN** | $2.499$ | $7.15\text{ KB}$ | $\approx 110\ \mu\text{s}$ | $87.4\%$ | Cần RAM lớn hơn cho hidden state ma trận. |

> **Mô hình khuyến nghị triển khai chính thức:** **`Separable_1D_CNN`** nhờ sự cân bằng xuất sắc giữa độ chính xác cao nhất ($88.6\%$), lượng tham số thấp nhất ($1.411$ trọng số), và khả năng trích xuất tương quan thời gian vô tuyến vượt trội.

---

## 5. Hướng Dẫn Tinh Chỉnh Khi Thay Đổi Điều Kiện Môi Trường

Khi triển khai hệ thống ở các môi trường thực địa mới, lập trình viên có thể điều chỉnh các tham số theo bảng hướng dẫn sau:

1. **Môi trường có nhiều Node cạnh tranh hơn ($> 5$ nodes):**
   - Tăng `SAMPLES_PER_CHANNEL` từ `10` lên `15` để bao quát lịch sử truyền của nhiều nút hơn.
   - Giữ nguyên `BATCH_SIZE = 64`.
2. **Kênh truyền có mức độ nhiễu đột ngột cao (Môi trường công nghiệp / Đô thị):**
   - Tăng tỷ lệ `Dropout` từ `0.15` lên `0.25`.
   - Tăng hệ số phạt $L_2$ từ `2e-4` lên `5e-4` để giảm thiểu tác động của các đỉnh nhiễu bất thường.
3. **Cần tối ưu thời gian phản hồi cực nhanh trên vi điều khiển cấp thấp (e.g., STM32 / nRF52):**
   - Chọn kiến trúc `Baseline_FCNN` thay cho CNN.
   - Giảm số nơ-ron của `dense_1` từ `16` xuống `12`, và `dense_2` từ `12` xuống `8`. Độ trễ suy luận sẽ giảm xuống dưới $10\ \mu\text{s}$.
