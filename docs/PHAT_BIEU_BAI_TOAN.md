# BÁO CÁO PHÁT BIỂU BÀI TOÁN & MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG
## Đề tài: Tối Ưu Hóa Kênh Truyền LoRa Dựa Trên Học Máy Siêu Nhẹ (TinyML Channel Hopping)
### Hệ thống Nhảy Kênh Thông Minh Thời Gian Thực Trên Vi Điều Khiển ESP32

---

> **FILE WORD XUẤT BẢN:**
> Tài liệu này đã được tự động định dạng và biên dịch thành file Microsoft Word chuyên nghiệp (chuẩn font Times New Roman, dãn dòng 1.25, bảng biểu màu Navy sang trọng, header/footer và khung ký duyệt) tại:
> 📄 **[docs/PHAT_BIEU_BAI_TOAN.docx](file:///e:/DATN/LoRa_TinyML_Hopping/docs/PHAT_BIEU_BAI_TOAN.docx)**

---

## 1. BỐI CẢNH THỰC TIỄN VÀ BẢN CHẤT VẤN ĐỀ KỸ THUẬT

### 1.1. Đặt Vấn Đề
Trong kỷ nguyên Internet Vạn Vật (IoT), công nghệ mạng diện rộng công suất thấp (**LPWAN** - *Low-Power Wide-Area Network*), đặc biệt là kỹ thuật điều chế trải phổ **LoRa** (*Long Range*), đã trở thành giải pháp kết nối vượt trội nhờ khả năng phủ sóng cự ly xa từ vài kilomet đến hàng chục kilomet với mức tiêu thụ năng lượng cực thấp.

Tuy nhiên, khi mật độ các thiết bị đầu cuối (**End-Nodes**) gia tăng nhanh chóng trong cùng một khu vực địa lý, mạng LoRa phải đối mặt với những thách thức nghiêm trọng về hiệu năng truyền thông:

1. **Cơ chế truy cập kênh Pure ALOHA mặc định:** Theo chuẩn LoRa và LoRaWAN lớp A, thiết bị đầu cuối hoạt động theo nguyên lý Pure ALOHA: bất cứ khi nào có dữ liệu cảm biến, node sẽ lập tức phát sóng mà không có cơ chế lắng nghe trước kênh truyền (*Listen-Before-Talk* - LBT thường không khả thi hoặc kém hiệu quả do độ nhạy thu của LoRa nằm sâu dưới mức nhiễu nền).
2. **Thời gian phát sóng trên không (Time-on-Air - ToA) kéo dài:** Đặc thù của kỹ thuật trải phổ Chirp Spread Spectrum (CSS) là tốc độ truyền dữ liệu thấp. Khi kích thước tải trọng (Payload) tăng từ $30\text{ Bytes}$ lên $250\text{ Bytes}$, thời gian phát sóng của một gói tin kéo dài từ vài chục mili-giây lên gần $400\text{ ms}$.
3. **Bùng nổ xác suất va chạm xung đột (Packet Collision):** Khi hai hoặc nhiều nút cùng truyền đồng thời trên cùng một kênh tần số, sóng điện từ bị giao thoa triệt tiêu lẫn nhau trên không (*destructive interference*). Hệ quả là trạm thu Gateway không thể giải mã được khung truyền, dẫn đến rớt gói tin hàng loạt, làm suy sụt nghiêm trọng Tỷ lệ nhận gói thành công (**PDR** - *Packet Delivery Ratio*).

### 1.2. Hạn Chế của Kênh Cố Định (Fixed Channel)
Trong kiến trúc truyền thống, mỗi thiết bị thường được cấu hình cố định phát trên một kênh tần số vật lý xác định. Khi kênh tần số này xuất hiện can nhiễu cục bộ, suy hao sâu (*deep fading*) hoặc có nhiều node xung quanh cùng truyền dữ liệu lớn, toàn bộ đường truyền bị tê liệt hoàn toàn, tỷ lệ PDR sụt giảm tiệm cận $0\%$ mà thiết bị không có cơ chế tự thích ứng né tránh.

### 1.3. Hạn Chế của Nhảy Kênh Ngẫu Nhiên (Random Channel Hopping)
Để giải quyết bài toán kênh cố định, giải pháp sơ khai thường áp dụng là nhảy kênh ngẫu nhiên giả lập (*Pseudo-Random Channel Hopping*). Tuy nhiên, cơ chế này mang tính mù quáng (*collision-blind*) do hoàn toàn không có nhận thức về trạng thái kênh vô tuyến:
- Các node độc lập có thể ngẫu nhiên chọn trùng một kênh tần số tại cùng một thời điểm, tiếp tục gây ra xung đột đối đầu.
- Node có thể nhảy vào một kênh đang bị can nhiễu môi trường nặng hoặc suy hao công suất nghiêm trọng.
- **Thực nghiệm chứng minh:** Khi kích thước gói tin tăng lên $250\text{ Bytes}$, cơ chế Random Hopping bị sụt đổ tỷ lệ nhận gói PDR chỉ còn **$63.7\%$**.

---

## 2. MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG VÔ TUYẾN

### 2.1. Mô Hình Mạng và Không Gian Tần Số
Xét hệ thống mạng cảm biến không dây gồm tập hợp $N$ thiết bị đầu cuối End-Node và một trạm thu thập trung tâm Multi-Channel Gateway:
$$\mathcal{N} = \{Node_1, Node_2, \dots, Node_N\}, \quad \text{với } N = 3 \text{ (Node A, Node B, Node C)}$$

Hệ thống hoạt động trên dải tần số $433\text{ MHz}$ ISM với tập hợp $K$ kênh tần số trực giao độc lập:
$$\mathcal{C} = \{c_1, c_2, \dots, c_K\}, \quad \text{với } K = 3 \text{ kênh vật lý}$$

Các kênh được phân bổ với khoảng cách bảo vệ (*guard band*) $\Delta f = 200\text{ kHz}$ nhằm triệt tiêu can nhiễu kênh lân cận (*Adjacent Channel Interference* - ACI):
- Kênh 1 ($c_1$): $f_1 = 433.175\text{ MHz}$
- Kênh 2 ($c_2$): $f_2 = 433.375\text{ MHz}$
- Kênh 3 ($c_3$): $f_3 = 433.575\text{ MHz}$

### 2.2. Mô Hình Tính Toán Thời Gian Phát Trên Không (Time-on-Air - ToA)
Thời gian chiếm dụng kênh vô tuyến $ToA$ của một gói tin LoRa phụ thuộc vào cấu hình lớp vật lý: Băng thông ($BW = 125\text{ kHz}$), Hệ số trải phổ ($SF = 7$), Tốc độ mã hóa ($CR = 4/5$), Chiều dài mào đầu ($N_{pre} = 8\text{ symbols}$) và Kích thước tải trọng ($PL\text{ bytes}$).

Thời gian kéo dài của một symbol chirp:
$$T_{sym} = \frac{2^{SF}}{BW} = \frac{2^7}{125,000} = \frac{128}{125,000} = 1.024\text{ ms}$$

Thời gian phát chuỗi đồng bộ Preamble:
$$T_{preamble} = (N_{pre} + 4.25) \times T_{sym} = (8 + 4.25) \times 1.024\text{ ms} = 12.544\text{ ms}$$

Số lượng biểu tượng của phần tải trọng dữ liệu ($N_{payload}$):
$$N_{payload} = 8 + \max\left( \left\lceil \frac{8PL - 4SF + 28 + 16CRC - 20IH}{4(SF - 2DE)} \right\rceil (CR + 4), 0 \right)$$
*(Trong đó: $CRC = 1$ (bật kiểm tra lỗi), $IH = 0$ (Explicit Header), $DE = 0$ (tắt Low Data Rate Optimization khi $SF=7$), $CR = 1$ (tương ứng Coding Rate $4/5$)).*

Tổng thời gian trên không $ToA$:
$$ToA = T_{preamble} + N_{payload} \times T_{sym}$$

#### Bảng Tính Toán Định Lượng ToA Theo Các Mức Payload Thực Nghiệm:
| Kích thước Payload ($PL$) | Số Symbol Payload ($N_{payload}$) | $ToA$ Lý Thuyết | Cửa Sổ Xung Đột ($2 \times ToA$) | Tỷ Lệ Mở Rộng So Với Gói 30B |
| :---: | :---: | :---: | :---: | :---: |
| **$30\text{ Bytes}$** | $53\text{ symbols}$ | **$66.82\text{ ms}$** | $133.64\text{ ms}$ | $1.00\times$ (Cơ sở) |
| **$74\text{ Bytes}$** | $128\text{ symbols}$ | **$143.62\text{ ms}$** | $287.24\text{ ms}$ | $2.15\times$ |
| **$118\text{ Bytes}$** | $203\text{ symbols}$ | **$220.42\text{ ms}$** | $440.84\text{ ms}$ | $3.30\times$ |
| **$162\text{ Bytes}$** | $278\text{ symbols}$ | **$297.22\text{ ms}$** | $594.44\text{ ms}$ | $4.45\times$ |
| **$206\text{ Bytes}$** | $353\text{ symbols}$ | **$374.02\text{ ms}$** | $748.04\text{ ms}$ | $5.60\times$ |
| **$250\text{ Bytes}$** | $428\text{ symbols}$ | **$450.82\text{ ms}$** | $901.64\text{ ms}$ | **$6.75\times$ (Cực đại)** |

> [!NOTE]
> **Nhận xét định lượng:** Khi kích thước tải tăng từ $30\text{B} \to 250\text{B}$, cửa sổ thời gian dễ bị tổn thương va chạm (*Vulnerable Window*) nở rộng gấp **$6.75$ lần** (từ $133.64\text{ ms}$ lên tới gần $1\text{ giây}$). Đây là nguyên nhân vật lý cốt lõi khiến các cơ chế ALOHA và Random Hopping bị sụp đổ hiệu năng.

### 2.3. Xác Suất Va Chạm Xung Đột Theo Pure ALOHA
Giả sử quá trình phát sinh gói tin của toàn mạng tuân theo phân phối Poisson với tốc độ $\lambda$ (gói/giây). Tải lượng mạng chuẩn hóa $G$ được định nghĩa:
$$G = N \cdot \lambda \cdot ToA$$

Khoảng thời gian dễ bị tổn thương xung đột: $V = 2 \times ToA$. Xác suất truyền thành công không bị va chạm sóng:
$$P_{succ} = e^{-2G} = e^{-2 \cdot N \cdot \lambda \cdot ToA}$$

Xác suất va chạm gói tin:
$$P_{collision} = 1 - P_{succ} = 1 - e^{-2 \cdot N \cdot \lambda \cdot ToA}$$

### 2.4. Mô Hình Suy Hao Đường Truyền (Path Loss) & Hiệu Ứng Bắt Sóng (Capture Effect)
Công suất tín hiệu thu được $RSSI$ tại Gateway từ node thứ $i$ cách khoảng cách $d_i$ tuân theo mô hình *Log-Distance Path Loss*:
$$RSSI_i(d_i)\text{ [dBm]} = P_{tx} + G_{tx} + G_{rx} - PL(d_0) - 10 \cdot n \cdot \log_{10}\left(\frac{d_i}{d_0}\right) - WAF - X_\sigma$$

*(với $P_{tx} = 17\text{ dBm}$, $d_0 = 1\text{m}$, $n \approx 3.0$, $WAF$ là hệ số suy hao xuyên tường, $X_\sigma$ là biến ngẫu nhiên Gauss do che bóng).*

Khi hai node $i$ và $j$ cùng phát đồng thời trên cùng một kênh, hiện tượng bắt sóng vô tuyến (**Capture Effect**) xảy ra tại Gateway nếu chênh lệch công suất thu thỏa mãn:
$$RSSI_i - RSSI_j \ge \gamma_{cap} \quad (\gamma_{cap} \approx 6\text{ dB})$$

**Hệ quả thực tế:** Node ở gần Gateway (Node B: $d \approx 1-3\text{m}$, $RSSI \approx -35\text{ dBm}$) áp đảo hoàn toàn tín hiệu của Node ở xa (Node C: $d \approx 35-45\text{m}$, $RSSI \approx -110\text{ dBm}$), khiến Gateway giải mã được gói của Node B nhưng hủy diệt hoàn toàn gói của Node C (PDR Node C tụt xuống $63.5\%$).

---

## 3. PHÁT BIỂU TOÁN HỌC BÀI TOÁN TỐI ƯU HÓA

### 3.1. Biểu Diễn Trạng Thái Kênh Truyền (Channel State Information - CSI)
Tại mỗi mốc thời gian truyền $t$, thiết bị đầu cuối thu thập vector đặc trưng kênh truyền $\mathbf{x}_t \in \mathbb{R}^9$:
$$\mathbf{x}_t = \left[ RSSI_t, \; SNR_t, \; Size_t, \; roll\_loss_t, \; consec\_loss_t, \; \Delta RSSI_t, \; \Delta SNR_t, \; ch_t, \; seq_t \right]^T$$

Để nắm bắt tương quan phụ thuộc thời gian (*Temporal Dynamics*), hệ thống duy trì ma trận cửa sổ trượt (*Sliding Window*) gồm $W = 10$ mốc thời gian liên tiếp:
$$\mathbf{S}_t = \left[ \mathbf{x}_{t - W + 1}, \; \mathbf{x}_{t - W + 2}, \; \dots, \; \mathbf{x}_t \right] \in \mathbb{R}^{10 \times 9}$$

### 3.2. Biến Quyết Định (Decision Variable)
Biến quyết định của hệ thống là hành động lựa chọn kênh tần số vô tuyến $a_{t+1}$ cho lượt phát sóng tiếp theo:
$$a_{t+1} \in \mathcal{C} = \{c_1, c_2, c_3\} \quad (\text{tương ứng } 433.175, \; 433.375, \; 433.575\text{ MHz})$$

### 3.3. Hàm Mục Tiêu Tối Ưu Hóa (Optimization Objective)
Mục tiêu là tìm chính sách lựa chọn kênh $\pi^*$ tối đa hóa tỷ lệ nhận gói PDR toàn mạng, tối ưu hóa công suất và tỷ số tín hiệu trên nhiễu thu được, đồng thời giảm thiểu chi phí chuyển đổi tần số:
$$\max_{\pi} \quad \mathbb{E} \left[ \text{PDR}(a_{t+1}) + \lambda_1 \cdot \overline{RSSI}_{norm}(a_{t+1}) + \lambda_2 \cdot \overline{SNR}_{norm}(a_{t+1}) - \lambda_3 \cdot \mathbb{I}(a_{t+1} \ne a_t) \cdot C_{hop} \right]$$

Trong đó:
- $\text{PDR}(a_{t+1}) \in [0, 1]$: Xác suất gói tin được giải mã thành công trên kênh $a_{t+1}$.
- $\overline{RSSI}_{norm}, \overline{SNR}_{norm}$: Điểm chất lượng tín hiệu thu chuẩn hóa.
- $\mathbb{I}(a_{t+1} \ne a_t)$: Hàm chỉ thị nhận giá trị $1$ nếu thiết bị nhảy kênh, $0$ nếu giữ nguyên kênh cũ.
- $C_{hop}$: Chi phí năng lượng và thời gian trễ khóa pha PLL khi chuyển kênh ($\approx 150\mu\text{s}$).
- $\lambda_1, \lambda_2, \lambda_3$: Các trọng số cân bằng đa mục tiêu.

### 3.4. Các Ràng Buộc Kỹ Thuật Nghiêm Ngặt Tại Biên (Edge Constraints)
1. **Ràng buộc bộ nhớ Flash:** $\text{Size}_{\text{Flash}}(\mathcal{M}) \le 100\text{ KB}$ (trong tổng số $4\text{ MB}$ của ESP32).
2. **Ràng buộc bộ nhớ RAM (Tensor Arena):** $\text{Size}_{\text{RAM}}(\mathcal{M}) \le 15\text{ KB}$ (thực tế cấp phát $10\text{ KB}$).
3. **Ràng buộc độ trễ suy luận thời gian thực:** $\tau_{\text{infer}} \le 20\text{ ms} \ll T_{\text{interval}} = 3000\text{ ms}$ (thực tế đo đạc $\approx 13.5\text{ ms}$).
4. **Ràng buộc phi tập trung (Decentralized Operation):** Quyết định nhảy kênh được thực hiện hoàn toàn tự trị tại từng End-Node dựa trên lịch sử quan sát cục bộ, không phát sinh thêm lưu lượng điều khiển ngoài băng (*No Out-of-band Overhead*).

---

## 4. GIẢI PHÁP ĐỀ XUẤT: HỌC MÁY SIÊU NHẸ (TINYML)

Bài toán tối ưu hóa được chuyển đổi thành bài toán phân loại chuỗi thời gian đa lớp:
$$f_\theta: \mathbb{R}^{10 \times 9} \to [0, 1]^3, \quad \sum_{k=1}^3 P(c_k | \mathbf{S}_t) = 1$$

Kênh tối ưu tiếp theo được lựa chọn theo nguyên lý xác suất cực đại (ArgMax):
$$a_{t+1}^* = \arg\max_{k \in \{1, 2, 3\}} P(c_k | \mathbf{S}_t)$$

### Kiến Trúc Quán Quân: Depthwise Separable 1D-CNN (Separable_1D_CNN)
- Áp dụng kỹ thuật tách biệt không gian và chiều sâu:
  $$\text{Tỷ lệ giảm khối lượng tính toán (MACs)} = \frac{1}{C_{out}} + \frac{1}{K} = \frac{1}{32} + \frac{1}{3} \approx 0.364 \quad (\text{Giảm } \mathbf{63.6\%} \text{ phép tính nhân-cộng})$$
- Áp dụng `GlobalAveragePooling1D` thay cho `Flatten`: Triệt tiêu hoàn toàn ma trận trọng số khổng lồ, đưa tổng số tham số xuống chỉ còn **$878$ tham số**.

#### Bảng So Sánh Đối Soát 5 Kiến Trúc AI:
| Kiến trúc Mô hình | Độ chính xác Test | Test Loss | Số lượng Tham số | Dung lượng TFLite | Độ trễ Suy luận (CPU) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline FCNN** | $90.41\%$ | $0.2939$ | $1,699$ | $8.84\text{ KB}$ | $5.50\text{ ms}$ |
| **1D-CNN** | $90.30\%$ | $0.2973$ | $2,659$ | $16.34\text{ KB}$ | $13.49\text{ ms}$ |
| **GRU RNN** | $90.12\%$ | $0.2870$ | $1,619$ | $42.32\text{ KB}$ | $59.39\text{ ms}$ |
| **Separable 1D-CNN (★)** | **$\mathbf{90.51\%}$** | **$\mathbf{0.2881}$** | **$\mathbf{878}$** | **$\mathbf{8.65\text{ KB}}$** | **$\mathbf{13.56\text{ ms}}$** |
| **ResNet-1D** | $90.30\%$ | $0.2927$ | $2,339$ | $14.73\text{ KB}$ | $15.47\text{ ms}$ |

---

## 5. HIỆU QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC VÀ ĐÓNG GÓP ĐỀ TÀI

### Bảng Kết Quả Đối Soát Hiệu Năng Vô Tuyến:
| Kích thước Payload | PDR Random Hopping | PDR TinyML Hopping | Mức Tăng Trưởng PDR | Cải Thiện Mức RSSI Thu |
| :---: | :---: | :---: | :---: | :---: |
| **$30\text{ Bytes}$** | $88.0\%$ | **$99.0\%$** | **$+11.0\%$** | $-89.5 \to -68.0\text{ dBm}$ ($+21.5\text{ dBm}$) |
| **$74\text{ Bytes}$** | $90.0\%$ | **$100.0\%$** | **$+10.0\%$** | $-91.2 \to -68.3\text{ dBm}$ ($+22.9\text{ dBm}$) |
| **$118\text{ Bytes}$** | $86.7\%$ | **$99.0\%$** | **$+12.3\%$** | $-90.9 \to -70.8\text{ dBm}$ ($+20.1\text{ dBm}$) |
| **$162\text{ Bytes}$** | $76.7\%$ | **$99.0\%$** | **$+22.3\%$** | $-90.6 \to -70.8\text{ dBm}$ ($+19.8\text{ dBm}$) |
| **$206\text{ Bytes}$** | $85.0\%$ | **$100.0\%$** | **$+15.0\%$** | $-93.0 \to -73.1\text{ dBm}$ ($+19.9\text{ dBm}$) |
| **$250\text{ Bytes}$** | $63.7\%$ | **$95.0\%$** | **$\mathbf{+31.3\%}$ (Đột phá)** | $-94.3 \to -74.5\text{ dBm}$ ($+19.8\text{ dBm}$) |

### Đóng Góp Khoa Học Cốt Lõi:
1. Xây dựng hoàn chỉnh khung mô hình hóa toán học cho bài toán nhảy kênh dự đoán phân tán trong mạng LoRa đa nút.
2. Thiết kế thành công kiến trúc mạng nơ-ron Separable 1D-CNN siêu nhẹ ($878$ tham số, $8.65\text{ KB}$ TFLite), vượt qua rào cản tài nguyên hạn chế của vi điều khiển ESP32 với độ trễ suy luận chỉ $13.5\text{ ms}$.
3. Chứng minh thực nghiệm mức tăng trưởng vượt trội: Tại kích thước gói tin lớn nhất ($250\text{ Bytes}$), mô hình TinyML giúp tăng PDR từ $63.7\%$ lên $95.0\%$ (cải thiện $+31.3\%$), đồng thời nâng cao công suất thu RSSI trung bình thêm $\approx 20\text{ dBm}$.
4. Cung cấp nền tảng mã nguồn mở, tài liệu kỹ thuật hoàn chỉnh và khả năng ứng dụng thực tế cao cho các hệ thống giám sát môi trường, nông nghiệp thông minh và nhà máy IoT.
