# BÀI BÁO GỐC: TÓM TẮT TOÀN VĂN & HỆ THỐNG CÔNG THỨC TOÁN HỌC (IEEE / arXiv:2412.01609v1)

> **Tên bài báo**: *Optimizing LoRa for Edge Computing with TinyML Pipeline for Channel Hopping*  
> **Nguồn trích dẫn gốc**: arXiv:2412.01609v1 [cs.NI], December 2024.  
> **Trích xuất tự động & số hóa**: Sử dụng **Docling** (IBM/LF AI) và **Marker**.

---

## I. MỤC TIÊU & TỔNG QUAN HỆ THỐNG

Bài báo giải quyết bài toán suy giảm chất lượng mạng LoRaWAN khi mật độ thiết bị đầu cuối (*End-Nodes - EN*) tăng cao, gây ra va chạm gói tin trầm trọng do cơ chế truyền ALOHA thuần túy và hiện tượng thắt cổ chai vô tuyến.

Giải pháp đề xuất:
1. **Mô hình hóa bài toán tối ưu hóa chuyển kênh (Channel Hopping Optimization)**: Tối thiểu hóa đồng thời tỷ lệ va chạm gói tin ($O_1$) và tần suất chuyển kênh không cần thiết gây tiêu hao năng lượng ($O_2$).
2. **Pipeline học máy nhúng (TinyML Pipeline for Channel Hopping)**: Thu thập thông tin trạng thái kênh (*CSI - Channel State Information*) gồm lịch sử bận kênh $\hat{\Delta}$, cường độ tín hiệu $RSSI$ và tỷ số tín hiệu trên nhiễu $SNR$ qua cửa sổ thời gian trượt ($w=10$, $t_s$).
3. **Triển khai biên thực tế (Edge Computing)**: Huấn luyện mô hình mạng nơ-ron nhỏ gọn (*Dense Neural Network*) và nạp lên vi điều khiển ESP32 / SX1262 với độ trễ suy luận siêu thấp ($131.3\,\mu\text{s}$).

---

## II. BẢNG KÝ HIỆU TOÁN HỌC (TABLE I)

| Ký hiệu | Định nghĩa toán học | Ý nghĩa vật lý / Kỹ thuật |
| :--- | :--- | :--- |
| $\mathcal{E}$ | Tập hợp các nút mạng đầu cuối | $\{EN_1, EN_2, \dots, EN_N\}$ |
| $\mathcal{G}$ | Tập hợp các trạm thu (Gateway) | $\{GW_1, GW_2, \dots, GW_G\}$ |
| $\mathcal{F}$ | Tập hợp các kênh tần số cho phép | $\{f_1, f_2, \dots, f_F\}$ (vd: 3 kênh 868.0, 868.2, 868.4 MHz) |
| $N, G, F$ | Số lượng $EN$, số lượng $GW$, số lượng tần số | Các tham số kích thước hệ thống |
| $B_f$ | Số lượng ký hiệu cực đại trên kênh $f$ | Giới hạn băng thông trong một đơn vị thời gian |
| $B_{min}$ | Số lượng ký hiệu tối thiểu của 1 gói tin | Kích thước gói tin nhỏ nhất |
| $D_i$ | Tổng lượng dữ liệu nút $EN_i$ cần truyền | Nhu cầu truyền thông trong chu kỳ |
| $\tau$ | Chỉ số khe thời gian rời rạc | $\tau \in \{1, 2, \dots, T\}$ |
| $t_s$ | Thời lượng / bước trượt của mỗi khe thời gian | Khoảng cách thời gian giữa 2 lần lấy mẫu |
| $x_{i,g,f}(\tau)$ | **Biến quyết định nhị phân** ($\{0, 1\}$) | $x_{i,g,f}(\tau) = 1$ nếu $EN_i$ truyền tới $GW_g$ trên tần số $f$ tại khe $\tau$ |
| $s_{i,g,f}(\tau)$ | **Biến quyết định nguyên** ($\mathbb{Z}^+$) | Số lượng ký hiệu $EN_i$ gửi tới $GW_g$ trên tần số $f$ tại khe $\tau$ |
| $c_{i,j,g,f}(\tau)$ | **Biến chỉ thị va chạm** | $c_{i,j,g,f}(\tau) = 1$ khi xảy ra va chạm giữa nút $i$ và nút $j$ |
| $z_i(\tau)$ | **Biến nhị phân chuyển kênh** | $z_i(\tau) = 1$ nếu nút $EN_i$ đổi kênh tần số tại khe $\tau$ |
| $\delta_{g,f}(\tau)$ | Biến phụ trợ tuyến tính hóa | Dùng để ràng buộc biến đổi kênh |

---

## III. HỆ THỐNG CÔNG THỨC TOÁN HỌC TỐI ƯU HÓA (EQUATIONS 1 - 13)

### 1. Định nghĩa phân bổ kênh và va chạm
Biến phân bổ kênh nhị phân:
$$x_{i,g,f}(\tau) = \begin{cases} 1 & \text{nếu } EN_i \text{ gửi đến } GW_g \text{ qua tần số } f \text{ tại thời điểm } \tau \\ 0 & \text{ngược lại} \end{cases} \quad (1)$$

Sự kiện va chạm giữa hai nút $EN_i$ và $EN_j$ ($i \neq j$):
$$c_{i,j,g,f}(\tau) = x_{i,g,f}(\tau) \cdot x_{j,g,f}(\tau) \quad (2)$$

### 2. Hai mục tiêu tối ưu hóa ($O_1$ và $O_2$)
- **Mục tiêu 1 ($O_1$)**: Tối thiểu hóa tổng số vụ va chạm trên toàn mạng trong thời gian $T$:
  $$\min \left( O_1 = \sum_{\tau=1}^T \sum_{i=1}^N \sum_{j=1, j \neq i}^N \sum_{g=1}^G \sum_{f=1}^F c_{i,j,g,f}(\tau) \right) \quad (3)$$

- **Mục tiêu 2 ($O_2$)**: Tối thiểu hóa tổng số lần chuyển kênh để tiết kiệm năng lượng:
  $$\min \left( O_2 = \sum_{i=1}^N \sum_{\tau=2}^T z_i(\tau) \right) \quad (4)$$

### 3. Các ràng buộc kỹ thuật (Constraints)
- **Ràng buộc kênh phát duy nhất**: Mỗi nút chỉ được truyền trên đúng 1 tần số tại mỗi khe $\tau$:
  $$\sum_{f=1}^F x_{i,g,f}(\tau) = 1, \quad \forall EN_i \in \mathcal{E}, \forall GW_g \in \mathcal{G}, \forall \tau \quad (5)$$

- **Ràng buộc khả năng tiếp nhận của Gateway**: Trạm thu $GW_g$ không thể nhận vượt quá công suất đồng thời $M_g$:
  $$\sum_{i=1}^N \sum_{f=1}^F x_{i,g,f}(\tau) \le M_g, \quad \forall GW_g \in \mathcal{G}, \forall \tau \quad (6)$$

- **Ràng buộc thông lượng ký hiệu cực đại trên kênh $f$**:
  $$\sum_{i=1}^N s_{i,g,f}(\tau) \le B_f, \quad \forall GW_g \in \mathcal{G}, \forall \tau, \forall f \quad (7)$$

- **Ràng buộc kích thước gói tin hợp lệ**:
  $$B_{min} \le s_{i,g,f}(\tau) \le B_f, \quad \forall EN_i \in \mathcal{E}, \forall GW_g \in \mathcal{G}, \forall \tau, \forall f \quad (8)$$

- **Ràng buộc hoàn thành dung lượng truyền $D_i$**:
  $$\sum_{\tau=1}^T \sum_{g=1}^G \sum_{f=1}^F x_{i,g,f}(\tau) \cdot s_{i,g,f}(\tau) = D_i, \quad \forall EN_i \in \mathcal{E} \quad (9)$$

- **Tuyến tính hóa hành vi chuyển kênh ($z_i(\tau)$)**:
  $$\sum_{i=1}^N x_{i,g,f}(\tau - 1) \ge 2 - M(1 - \delta_{g,f}(\tau)) \quad (10a)$$
  $$\sum_{i=1}^N x_{i,g,f}(\tau - 1) \le 2 + M\delta_{g,f}(\tau) \quad (10b)$$
  $$x_{i,g,f}(\tau) - x_{i,g,f}(\tau - 1) \le z_i(\tau), \quad \forall EN_i \in \mathcal{E} \quad (11)$$
  $$z_i(\tau) \le \sum_{g=1}^G \sum_{f=1}^F |x_{i,g,f}(\tau) - x_{i,g,f}(\tau - 1)|, \quad \forall EN_i \in \mathcal{E} \quad (12)$$

### 4. Hàm mục tiêu tổng quát (Multi-Objective Optimization)
Bài toán quy hoạch nguyên phi tuyến (MINLP) được kết hợp theo trọng số Pareto:
$$\min_{\mathbf{x}, \mathbf{s}} \left( \alpha \cdot O_1 + \beta \cdot O_2 \right) \quad (13)$$
$$\text{thỏa mãn các ràng buộc } (5), (6), (7), (8), (9), (10), (11), (12).$$
*(Trong đó $\alpha, \beta \ge 0$ là trọng số cân bằng giữa tỷ lệ va chạm và chi phí năng lượng chuyển kênh).*

---

## IV. TINYML PIPELINE CHO CHUYỂN KÊNH THÍCH ỨNG (EQUATIONS 14 - 19)

Vì bài toán (13) là bài toán NP-hard không thể giải tối ưu trên vi điều khiển theo thời gian thực, tác giả đề xuất thay thế bộ giải toán học bằng mạng nơ-ron học máy nhúng (**TinyML**):

### 1. Vector đặc trưng trạng thái kênh (Channel State Information - CSI)
- Mức độ bận của tần số $f$ tại thời điểm $\tau$:
  $$\Delta_{i,f}(\tau) = \sum_{j=1}^N \sum_{g=1}^G x_{j,g,f}(\tau) \quad (14)$$

- Vector quan sát bận kênh trong cửa sổ trượt $w$ bước thời gian ($t_s$):
  $$\Delta_i(\tau) = \{ \Delta_{i,f}(\tau) \}_{f \in [1..F]}, \quad \hat{\Delta}_i(t) = \{ \Delta_i(t - w \cdot t_s), \dots, \Delta_i(t - t_s), \Delta_i(t) \} \quad (15)$$

- Lịch sử cường độ tín hiệu thu nhận ($RSSI$) trong cửa sổ trượt:
  $$RSSI_i(t) = \{ RSSI_i(t - w \cdot t_s), \dots, RSSI_i(t - t_s), RSSI_i(t) \} \quad (16)$$

- Lịch sử tỷ số tín hiệu trên nhiễu ($SNR$) trong cửa sổ trượt:
  $$SNR_i(t) = \{ SNR_i(t - w \cdot t_s), \dots, SNR_i(t - t_s), SNR_i(t) \} \quad (17)$$

### 2. Không gian trạng thái đầu vào ($S$) và nhãn đầu ra ($C$)
- **Input State ($S$)**:
  $$\mathcal{S} = \{ s_i(t) = (\hat{\Delta}_i(t), RSSI_i(t), SNR_i(t)), \quad \forall EN_i, \forall t \} \quad (18)$$
  *(Khi triển khai với $w=10$ bước thời gian, vector đầu vào có số chiều $10 \times 9 = 90$ giá trị CSI hoặc qua thống kê rút gọn 9 giá trị).*

- **Output Decision ($C$)**:
  $$\mathcal{C} = \{ C_i = c_i(t), \quad \forall EN_i, \forall t \} \quad (19)$$
  *(Xác suất lựa chọn kênh $f \in \{1..F\}$ tối ưu để truyền gói tin tiếp theo mà không bị va chạm).*

---

## V. BẢNG THÔNG SỐ THỰC NGHIỆM & ĐỐI SÁNH KẾT QUẢ

### 1. Cấu hình phần cứng & tham số truyền LoRa (Table II)
- **Tần số**: 868.0 MHz, 869.0 MHz, 870.0 MHz (3 kênh)
- **Băng thông (BW)**: 125 kHz
- **Hệ số trải phổ (SF)**: 7
- **Tỷ lệ mã hóa (CR)**: 4/5
- **Phần cứng nút End-Node**: Heltec WiFi LoRa 32 (V3) (ESP32-S3 + SX1262)
- **Phần cứng Gateway**: Adafruit Feather M0 (SX1276)
- **Kiến trúc TinyML**: Dense(10) $\rightarrow$ Dense(10, L1 Reg) $\rightarrow$ Dense(3, Softmax)

### 2. So sánh hiệu năng các thuật toán học máy (Table VI)

| Mô hình thuật toán | Độ chính xác (Accuracy) | Sai số MSE | Thời gian huấn luyện (ms) | Thời gian suy luận trên Edge ($\mu\text{s}$) | Đánh giá tính khả thi nhúng |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Neural Network (TinyML)** | **95.6%** | **0.09** | **30,676.7** | **131.3 $\mu\text{s}$** | **Tối ưu nhất cho MCU (Siêu nhanh, ít RAM)** |
| **K-Nearest Neighbors (KNN)** | 92.2% | 0.15 | 5.6 | 216.2 $\mu\text{s}$ | Tốn RAM lưu trữ điểm lân cận |
| **Linear Regression** | 77.7% | 0.67 | 13.3 | 40.3 $\mu\text{s}$ | Độ chính xác thấp, không mô hình hóa phi tuyến |
| **Decision Tree** | 96.8% | 0.08 | 135.7 | 36.7 $\mu\text{s}$ | Dễ bị quá khớp (overfitting) khi nhiễu |
| **Random Forest** | 97.6% | 0.05 | 8,803.8 | 1,520.3 $\mu\text{s}$ (1.5 ms) | Tốn Flash/RAM để lưu cây |
| **Gradient Boosting** | 99.92% | 0.003 | 74,146.1 | 11,669.6 $\mu\text{s}$ (11.6 ms) | Quá nặng đối với MCU thời gian thực |
| **Extreme Gradient Boost (XGB)** | 99.96% | 0.0008 | 7,526.9 | 15,841.7 $\mu\text{s}$ (15.8 ms) | Không phù hợp chạy trên vi điều khiển |

---

## VI. BẢNG ĐO THỰC TẾ SUY HAO TÍN HIỆU & PDR THEO KHOẢNG CÁCH

Các bảng trích xuất chi tiết theo 3 cự ly thực nghiệm:
- **Cự ly 1m**: [table_3_experiment_1m.md](file:///e:/DATN/LoRa_TinyML_Hopping/docs/tables/table_3.md)
- **Cự ly 15m**: [table_4_experiment_15m.md](file:///e:/DATN/LoRa_TinyML_Hopping/docs/tables/table_4.md)
- **Cự ly 30m**: [table_5_experiment_30m.md](file:///e:/DATN/LoRa_TinyML_Hopping/docs/tables/table_5.md)

*Bản tài liệu này được biên soạn và lưu trữ làm chuẩn tham chiếu học thuật cho Đồ án Tốt nghiệp `LoRa_TinyML_Hopping`.*
