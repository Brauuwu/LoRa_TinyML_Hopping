**BỘ GIÁO DỤC VÀ ĐÀO TẠO — TRƯỜNG ĐẠI HỌC KỸ THUẬT  
KHOA ĐIỆN TỬ VIỄN THÔNG / CÔNG NGHỆ THÔNG TIN**

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**BÁO CÁO PHÁT BIỂU BÀI TOÁN  
VÀ MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG**

*Đề tài: Tối Ưu Hóa Kênh Truyền LoRa Dựa Trên Học Máy Siêu Nhẹ (TinyML Channel Hopping)  
Hệ thống Nhảy Kênh Thông Minh Thời Gian Thực Trên Vi Điều Khiển ESP32*

**MỤC TIÊU VĂN BẢN**  
*Tóm tắt định hướng: Tài liệu này cung cấp cơ sở khoa học, công thức toán học và phát biểu hình thức hóa (Formal Problem Formulation) cho bài toán tối ưu hóa kênh truyền mạng LoRa. Hệ thống kết hợp lý thuyết truyền thông vô tuyến, mô hình suy hao kênh truyền, cơ chế giải quyết xung đột ALOHA và mô hình mạng nơ-ron học máy nhúng (TinyML) chạy trực tiếp tại biên trên vi điều khiển ESP32.*

**1. BỐI CẢNH THỰC TIỄN VÀ BẢN CHẤT VẤN ĐỀ KỸ THUẬT**

Trong kỷ nguyên Internet Vạn Vật (IoT), công nghệ mạng diện rộng công suất thấp (LPWAN - Low-Power Wide-Area Network), đặc biệt là kỹ thuật điều chế trải phổ LoRa (Long Range), đã trở thành chuẩn kết nối vượt trội nhờ khả năng phủ sóng cự ly từ vài kilomet đến hàng chục kilomet với mức tiêu thụ năng lượng cực thấp. Tuy nhiên, khi mật độ các thiết bị đầu cuối (End-Nodes) gia tăng nhanh chóng trong cùng một khu vực địa lý, mạng LoRa phải đối mặt với những thách thức nghiêm trọng về hiệu năng truyền thông:

1. Cơ chế truy cập kênh Pure ALOHA mặc định: Theo chuẩn LoRa và LoRaWAN lớp A, thiết bị đầu cuối hoạt động theo nguyên lý Pure ALOHA: bất cứ khi nào có dữ liệu cảm biến, node sẽ lập tức phát sóng mà không có cơ chế lắng nghe trước kênh truyền (Listen-Before-Talk - LBT thường không khả thi hoặc kém hiệu quả do độ nhạy thu của LoRa nằm sâu dưới mức nhiễu nền).

2. Thời gian phát sóng trên không (Time-on-Air - ToA) kéo dài: Đặc thù của kỹ thuật trải phổ Chirp Spread Spectrum (CSS) là tốc độ truyền dữ liệu thấp (vài trăm bps đến vài kbps). Khi kích thước tải trọng (Payload) tăng từ 30 Bytes lên 250 Bytes, thời gian phát sóng của một gói tin kéo dài từ vài chục mili-giây lên gần 400 mili-giây.

3. Bùng nổ xác suất va chạm xung đột (Packet Collision): Khi hai hoặc nhiều nút cùng truyền đồng thời trên cùng một kênh tần số, sóng điện từ bị giao thoa triệt tiêu lẫn nhau trên không (destructive interference). Hệ quả là trạm thu Gateway không thể giải mã được khung truyền, dẫn đến rớt gói tin hàng loạt, làm suy sụt nghiêm trọng Tỷ lệ nhận gói thành công (PDR - Packet Delivery Ratio).

**1.1. Hạn chế của Kênh Cố Định (Fixed Channel)**

Trong kiến trúc truyền thống, mỗi thiết bị thường được cấu hình cố định phát trên một kênh tần số vật lý xác định. Khi kênh tần số này xuất hiện can nhiễu cục bộ, suy hao sâu (deep fading) hoặc có nhiều node xung quanh cùng truyền dữ liệu lớn, toàn bộ đường truyền bị tê liệt hoàn toàn, tỷ lệ PDR sụt giảm tiệm cận 0% mà thiết bị không có cơ chế tự thích ứng né tránh.

**1.2. Hạn chế của Nhảy Kênh Ngẫu Nhiên (Random Channel Hopping)**

Để giải quyết bài toán kênh cố định, giải pháp sơ khai thường áp dụng là nhảy kênh ngẫu nhiên giả lập (Pseudo-Random Channel Hopping). Tuy nhiên, cơ chế này mang tính mù quáng (collision-blind) do hoàn toàn không có nhận thức về trạng thái kênh vô tuyến:

• Các node độc lập có thể ngẫu nhiên chọn trùng một kênh tần số tại cùng một thời điểm, tiếp tục gây ra xung đột đối đầu.

• Node có thể nhảy vào một kênh đang bị can nhiễu môi trường nặng hoặc suy hao công suất nghiêm trọng.

• Thực nghiệm cho thấy: khi kích thước gói tin tăng lên 250 Bytes, cơ chế Random Hopping bị sụt đổ tỷ lệ nhận gói PDR chỉ còn 63.7%.

**2. MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG VÔ TUYẾN**

**2.1. Mô hình Mạng và Không Gian Tần Số**

Xét hệ thống mạng cảm biến không dây gồm tập hợp N thiết bị đầu cuối End-Node và một trạm thu thập trung tâm Multi-Channel Gateway:

**N = {Node\_1, Node\_2, ..., Node\_N},  với N = 3 (Node A, Node B, Node C)**

Hệ thống hoạt động trên dải tần số 433 MHz ISM với tập hợp K kênh tần số trực giao độc lập:

**C = {c\_1, c\_2, ..., c\_K},  với K = 3 kênh vật lý**

Các kênh được phân bổ với khoảng cách bảo vệ (guard band) Δf = 200 kHz nhằm triệt tiêu can nhiễu kênh lân cận (Adjacent Channel Interference - ACI):

• Kênh 1 (c\_1): f\_1 = 433.175 MHz

• Kênh 2 (c\_2): f\_2 = 433.375 MHz

• Kênh 3 (c\_3): f\_3 = 433.575 MHz

**2.2. Mô hình Tính Toán Thời Gian Phát Trên Không (Time-on-Air - ToA)**

Thời gian chiếm dụng kênh vô tuyến ToA của một gói tin LoRa phụ thuộc vào cấu hình lớp vật lý: Băng thông (BW = 125 kHz), Hệ số trải phổ (SF = 7), Tốc độ mã hóa (CR = 4/5), Chiều dài mào đầu (N\_pre = 8 symbols) và Kích thước tải trọng (PL bytes).

Thời gian kéo dài của một symbol chirp:

**T\_sym = 2^SF / BW = 2^7 / 125,000 = 128 / 125,000 = 1.024 ms**

Thời gian phát chuỗi đồng bộ Preamble:

**T\_preamble = (N\_pre + 4.25) * T\_sym = (8 + 4.25) * 1.024 ms = 12.544 ms**

Số lượng biểu tượng của phần tải trọng dữ liệu (N\_payload):

**N\_payload = 8 + max( ceil( (8*PL - 4*SF + 28 + 16*CRC - 20*IH) / (4*(SF - 2*DE)) ) * (CR + 4), 0 )**

Trong đó: CRC = 1 (bật kiểm tra lỗi), IH = 0 (Explicit Header), DE = 0 (tắt Low Data Rate Optimization khi SF=7), CR = 1 (tương ứng Coding Rate 4/5).

Tổng thời gian trên không ToA:

**ToA = T\_preamble + N\_payload * T\_sym**

| **Kích thước Payload (PL)**   | **Số Symbol Payload**   | **ToA Lý Thuyết (ms)**   | **Cửa Sổ Xung Đột (2*ToA)**   | **Tỷ Lệ Mở Rộng ToA**   |
|-------------------------------|-------------------------|--------------------------|-------------------------------|-------------------------|
| 30 Bytes                      | 53 symbols              | 66.82 ms                 | 133.64 ms                     | 1.00x (Gốc)             |
| 74 Bytes                      | 128 symbols             | 143.62 ms                | 287.24 ms                     | 2.15x                   |
| 118 Bytes                     | 203 symbols             | 220.42 ms                | 440.84 ms                     | 3.30x                   |
| 162 Bytes                     | 278 symbols             | 297.22 ms                | 594.44 ms                     | 4.45x                   |
| 206 Bytes                     | 353 symbols             | 374.02 ms                | 748.04 ms                     | 5.60x                   |
| 250 Bytes                     | 428 symbols             | 450.82 ms                | 901.64 ms                     | **6.75x (Cực đại)**     |

Nhận xét định lượng: Khi kích thước gói tin tăng từ 30B lên 250B, cửa sổ thời gian xung đột (Vulnerable Window) nở rộng gấp 6.75 lần (từ 133 ms lên tới hơn 900 ms), lý giải tại sao mạng ALOHA thuần túy bị suy giảm PDR nghiêm trọng ở các gói tin kích thước lớn.

**2.3. Xác Suất Va Chạm Xung Đột Theo Pure ALOHA**

Trong giao thức Pure ALOHA, giả sử quá trình phát sinh gói tin của toàn mạng tuân theo phân phối Poisson với tốc độ λ (gói/giây). Tải lượng mạng chuẩn hóa G được định nghĩa:

**G = N * lambda * ToA**

Cửa sổ thời gian dễ bị tổn thương (Vulnerable Period) bằng hai lần thời gian truyền: V = 2 * ToA. Do đó, xác suất truyền thành công không bị va chạm sóng:

**P\_succ = e^(-2 * G) = e^(-2 * N * lambda * ToA)**

Xác suất va chạm gói tin:

**P\_collision = 1 - P\_succ = 1 - e^(-2 * N * lambda * ToA)**

Hệ quả toán học: Khi kích thước payload tăng (ToA tăng) hoặc số lượng node cạnh tranh N tăng, xác suất va chạm P\_collision tăng tiệm cận 100%.

**2.4. Mô Hình Suy Hao Đường Truyền (Path Loss) &amp; Hiệu Ứng Bắt Sóng (Capture Effect)**

Công suất tín hiệu thu được RSSI tại Gateway từ node thứ i cách khoảng cách d\_i tuân theo mô hình Log-Distance Path Loss:

**RSSI\_i(d\_i) [dBm] = P\_tx + G\_tx + G\_rx - PL(d\_0) - 10 * n * log10( d\_i / d\_0 ) - WAF - X\_sigma**

Trong đó: P\_tx = 17 dBm (công suất phát), d\_0 = 1m (khoảng cách chuẩn), n ≈ 3.0 (hệ số suy hao trong nhà), WAF là hệ số suy hao xuyên tường (Wall Attenuation Factor), X\_sigma là biến ngẫu nhiên Gauss phản ánh hiệu ứng che bóng (Shadowing).

Khi hai node i và j cùng phát đồng thời trên cùng một kênh, hiện tượng bắt sóng vô tuyến (Capture Effect) xảy ra tại Gateway nếu chênh lệch công suất thu thỏa mãn ngưỡng giải điều chế:

**RSSI\_i - RSSI\_j &gt;= gamma\_cap  (với gamma\_cap ≈ 6 dB đối với LoRa CSS SF7)**

Ý nghĩa vật lý: Node ở gần Gateway (Node B: d ≈ 1-3m, RSSI ≈ -35 dBm) sẽ át vía hoàn toàn tín hiệu của Node ở xa (Node C: d ≈ 35-45m, RSSI ≈ -110 dBm), khiến Gateway giải mã được gói của Node B nhưng hủy diệt hoàn toàn gói của Node C.

**3. PHÁT BIỂU TOÁN HỌC BÀI TOÁN TỐI ƯU HÓA**

**3.1. Biểu Diễn Trạng Thái Kênh Truyền (Channel State Information - CSI)**

Tại mỗi mốc thời gian truyền t, thiết bị đầu cuối thu thập vector đặc trưng kênh truyền x\_t gồm 9 thông số vật lý:

**x\_t = [ RSSI\_t,  SNR\_t,  Size\_t,  roll\_loss\_t,  consec\_loss\_t,  ΔRSSI\_t,  ΔSNR\_t,  ch\_t,  seq\_t ]^T  ∈ R^9**

Trong đó:

• RSSI\_t, SNR\_t: Cường độ tín hiệu và tỷ số tín hiệu trên nhiễu phản hồi từ gói ACK gần nhất.

• Size\_t: Kích thước tải trọng dữ liệu (30 - 250 Bytes).

• roll\_loss\_t: Tỷ lệ mất gói trượt trong cửa sổ cục bộ gần nhất.

• consec\_loss\_t: Số lượng gói tin bị mất liên tiếp (chỉ báo kênh đang bị tắc nghẽn nặng).

• ΔRSSI\_t, ΔSNR\_t: Đạo hàm bậc nhất phản ánh độ dốc biến thiên chất lượng kênh giữa 2 bước.

• ch\_t: Kênh tần số hiện tại đang sử dụng (ch\_t ∈ {0, 1, 2}).

• seq\_t: Chỉ số tuần tự của gói tin.

Để nắm bắt tương quan phụ thuộc thời gian (Temporal Dynamics) của quá trình truyền sóng, hệ thống duy trì một ma trận cửa sổ trượt (Sliding Window) gồm W = 10 mốc thời gian liên tiếp:

**S\_t = [ x\_{t - W + 1},  x\_{t - W + 2},  ...,  x\_t ]  ∈ R^{10 x 9}**

Tensor đầu vào này có thể được biểu diễn dưới dạng ma trận 2D kích thước (10, 9) hoặc vector phẳng 90 chiều sau khi qua bộ chuẩn hóa tĩnh StandardScaler: z = (S\_t - μ) / σ.

**3.2. Biến Quyết Định (Decision Variable)**

Biến quyết định của hệ thống là hành động lựa chọn kênh tần số vô tuyến a\_{t+1} cho lượt phát sóng tiếp theo:

**a\_{t+1} ∈ C = {c\_1, c\_2, c\_3}  (tương ứng 433.175, 433.375, 433.575 MHz)**

**3.3. Hàm Mục Tiêu Tối Ưu Hóa (Optimization Objective)**

Mục tiêu của bài toán là tìm chính sách lựa chọn kênh π* sao cho tối đa hóa tỷ lệ nhận gói PDR toàn mạng, đồng thời tối ưu hóa chất lượng năng lượng thu và giảm thiểu chi phí chuyển đổi tần số:

**max\_π  E [  PDR(a\_{t+1})  +  λ\_1 * RSSI\_norm(a\_{t+1})  +  λ\_2 * SNR\_norm(a\_{t+1})  -  λ\_3 * I(a\_{t+1} != a\_t) * C\_hop  ]**

Trong đó:

• PDR(a\_{t+1}) ∈ [0, 1]: Xác suất gói tin được Gateway giải mã thành công khi phát trên kênh a\_{t+1}.

• RSSI\_norm, SNR\_norm: Điểm chất lượng tín hiệu thu chuẩn hóa.

• I(a\_{t+1} != a\_t): Hàm chỉ thị nhận giá trị 1 nếu thiết bị quyết định nhảy kênh, nhận 0 nếu giữ nguyên kênh cũ.

• C\_hop: Chi phí năng lượng và thời gian trễ khóa pha PLL của module RF SX1278 khi chuyển kênh (~150 μs).

• λ\_1, λ\_2, λ\_3: Các trọng số cân bằng đa mục tiêu.

**3.4. Các Ràng Buộc Kỹ Thuật Nghiêm Ngặt Tại Biên (Edge Constraints)**

Do mô hình học máy được triển khai trực tiếp trên vi điều khiển nhúng ESP32 (Xtensa Dual-Core 240 MHz, SRAM khả dụng cho ML ≈ 50-80 KB), bài toán tối ưu phải tuân thủ nghiêm ngặt 4 ràng buộc vật lý:

1. Ràng buộc bộ nhớ Flash: Dung lượng nhị phân FlatBuffer và mảng byte C header của mô hình phải nhỏ hơn 100 KB (thực tế kiến trúc Separable 1D-CNN chỉ chiếm 8.65 KB TFLite và 60.18 KB C header).

2. Ràng buộc bộ nhớ động RAM (Tensor Arena): Vùng nhớ cấp phát tĩnh cho bộ giải thông dịch TFLM không được vượt quá 15 KB (thực tế cấu hình TINYML\_TENSOR\_ARENA\_SIZE = 10 KB).

3. Ràng buộc độ trễ suy luận thời gian thực: Thời gian tính toán suy luận τ\_infer trên ESP32 phải nhỏ hơn 20 ms (thực tế đo đạc đạt ~13.5 ms), không gây trễ chu kỳ phát sóng 3000 ms.

4. Ràng buộc phi tập trung (Decentralized Operation): Quyết định nhảy kênh được thực hiện hoàn toàn tự trị tại từng End-Node dựa trên lịch sử quan sát cục bộ, không phát sinh thêm lưu lượng điều khiển ngoài băng (Out-of-band Overhead) làm nghẽn mạng vô tuyến.

**4. GIẢI PHÁP ĐỀ XUẤT: MẠNG NƠ-RON HỌC MÁY SIÊU NHẸ (TINYML)**

Bài toán tối ưu hóa được chuyển đổi thành bài toán phân loại chuỗi thời gian đa lớp (Multi-Class Time-Series Classification):

**f\_θ: R^{10 x 9} → [0, 1]^3,   sao cho   sum\_{k=1}^3 P(c\_k | S\_t) = 1**

Kênh tối ưu tiếp theo được lựa chọn theo nguyên lý xác suất cực đại (ArgMax):

**a\_{t+1}^* = argmax\_{k ∈ {1, 2, 3}}  P(c\_k | S\_t)**

**4.1. Kiến Trúc Quán Quân: Depthwise Separable 1D-CNN**

Để dung hòa mâu thuẫn giữa độ chính xác dự báo cao và tài nguyên vi điều khiển cực kỳ eo hẹp, đề tài đề xuất kiến trúc tích chập tách biệt theo chiều sâu (Depthwise Separable 1D-CNN):

• Tách phép tích chập truyền thống thành 2 bước: Depthwise Convolution (lọc không gian độc lập từng kênh) và Pointwise Convolution (kết hợp các kênh bằng kernel 1x1).

• Tỷ số giảm khối lượng tính toán nhân-cộng (MACs):

**Reduction Ratio = 1 / C\_out + 1 / K = 1 / 32 + 1 / 3 ≈ 0.364  (Giảm tới 63.6% phép tính)**

• Sử dụng GlobalAveragePooling1D thay cho Flatten: Triệt tiêu hoàn toàn ma trận trọng số khổng lồ nối với lớp Dense, giảm số tham số toàn mạng xuống mức kỷ lục: chỉ 878 tham số!

| **Kiến trúc Mô hình**    | **Độ chính xác Test**   | **Test Loss**   | **Số tham số (Params)**   | **Dung lượng TFLite**   | **Độ trễ suy luận**   |
|--------------------------|-------------------------|-----------------|---------------------------|-------------------------|-----------------------|
| Baseline FCNN            | 90.41%                  | 0.2939          | 1,699                     | 8.84 KB                 | 5.50 ms               |
| 1D-CNN                   | 90.30%                  | 0.2973          | 2,659                     | 16.34 KB                | 13.49 ms              |
| GRU RNN                  | 90.12%                  | 0.2870          | 1,619                     | 42.32 KB                | 59.39 ms              |
| **Separable 1D-CNN (★)** | **90.51%**              | **0.2881**      | **878**                   | **8.65 KB**             | **13.56 ms**          |
| ResNet-1D                | 90.30%                  | 0.2927          | 2,339                     | 14.73 KB                | 15.47 ms              |

**5. HIỆU QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC VÀ ĐÓNG GÓP ĐỀ TÀI**

Hiệu quả của giải pháp nhảy kênh dự đoán TinyML được kiểm chứng thông qua 21 kịch bản thực nghiệm đo sóng thực tế trên hệ thống phần cứng gồm 3 End-Nodes ESP32 và Multi-Channel Gateway Raspberry Pi CM4:

| **Kích thước Payload**   | **PDR Random Hopping**   | **PDR TinyML Hopping**   | **Mức Tăng Trưởng PDR**   | **Cải Thiện Mức RSSI**        |
|--------------------------|--------------------------|--------------------------|---------------------------|-------------------------------|
| 30 Bytes                 | 88.0%                    | 99.0%                    | +11.0%                    | -89.5 → -68.0 dBm (+21.5 dBm) |
| 74 Bytes                 | 90.0%                    | 100.0%                   | +10.0%                    | -91.2 → -68.3 dBm (+22.9 dBm) |
| 118 Bytes                | 86.7%                    | 99.0%                    | +12.3%                    | -90.9 → -70.8 dBm (+20.1 dBm) |
| 162 Bytes                | 76.7%                    | 99.0%                    | +22.3%                    | -90.6 → -70.8 dBm (+19.8 dBm) |
| 206 Bytes                | 85.0%                    | 100.0%                   | +15.0%                    | -93.0 → -73.1 dBm (+19.9 dBm) |
| 250 Bytes                | 63.7%                    | 95.0%                    | **+31.3% (Đột phá)**      | -94.3 → -74.5 dBm (+19.8 dBm) |

Đóng góp khoa học và kỹ thuật cốt lõi của đề tài:

1. Xây dựng hoàn chỉnh mô hình hóa toán học cho bài toán nhảy kênh dự đoán phân tán trong mạng LoRa đa node cự ly ngắn.

2. Thiết kế thành công kiến trúc mạng nơ-ron Separable 1D-CNN siêu nhẹ (878 tham số, 8.65 KB TFLite), vượt qua rào cản tài nguyên hạn chế của vi điều khiển ESP32 với độ trễ suy luận chỉ 13.5 ms.

3. Chứng minh thực nghiệm mức tăng trưởng vượt trội: Tại kích thước gói tin lớn nhất (250 Bytes), mô hình TinyML giúp tăng PDR từ 63.7% lên 95.0% (cải thiện +31.3%), đồng thời nâng cao công suất thu RSSI trung bình thêm ~20 dBm.

4. Cung cấp nền tảng mã nguồn mở, tài liệu kỹ thuật hoàn chỉnh và khả năng ứng dụng thực tế cao cho các hệ thống giám sát môi trường, nông nghiệp thông minh và nhà máy IoT.

| **GIẢNG VIÊN HƯỚNG DẪN   (Ký và ghi rõ họ tên)**   | **SINH VIÊN THỰC HIỆN   (Ký và ghi rõ họ tên)**   |
|----------------------------------------------------|---------------------------------------------------|
|                                                    |                                                   |