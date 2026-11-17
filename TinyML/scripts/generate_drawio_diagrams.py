#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_drawio_diagrams.py
Tạo tự động 13 tệp sơ đồ đồ họa định dạng .drawio (XML) chất lượng cao cho đồ án:
Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML.

Đặc tính thiết kế:
- Trực quan, hiện đại, màu sắc hài hòa (Flat / Material palette).
- Không chú thích quá nhiều, tinh gọn, tập trung vào cấu trúc và luồng dữ liệu.
- Định dạng XML chuẩn mở của Diagrams.net / draw.io, mở được trực tiếp trên VSCode / App / Web.
"""

import os
import shutil
import xml.etree.ElementTree as ET

DOCS_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/docs/figs")
ROOT_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/figs")
os.makedirs(DOCS_FIGS_DIR, exist_ok=True)
os.makedirs(ROOT_FIGS_DIR, exist_ok=True)


class DrawioBuilder:
    def __init__(self, title="Diagram", width=1200, height=800):
        self.title = title
        self.width = width
        self.height = height
        self.cells = []
        self.cell_id = 2

        # Root elements
        self.cells.append('<mxCell id="0" />')
        self.cells.append('<mxCell id="1" parent="0" />')

    def add_title(self, text, x=40, y=20, w=1040, h=45):
        style = (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=none;"
            "fontColor=#ffffff;fontStyle=1;fontSize=15;shadow=1;arcSize=10;"
        )
        self.add_box(text, x, y, w, h, style)

    def add_box(self, label, x, y, w, h, style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
                "strokeWidth=1.5;fontColor=#1e293b;fontSize=12;fontFamily=Helvetica;"
            )
        # Escape XML entities in label
        escaped_label = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        cell = (
            f'<mxCell id="{cid}" value="{escaped_label}" style="{style}" vertex="1" parent="1">\n'
            f'  <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n'
            f'</mxCell>'
        )
        self.cells.append(cell)
        return cid

    def add_html_box(self, html_content, x, y, w, h, style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
                "strokeWidth=1.5;fontColor=#1e293b;fontSize=12;fontFamily=Helvetica;"
            )
        # In draw.io, html content in value can have simple tags if escaped properly
        escaped = (
            html_content.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        cell = (
            f'<mxCell id="{cid}" value="{escaped}" style="{style}" vertex="1" parent="1">\n'
            f'  <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n'
            f'</mxCell>'
        )
        self.cells.append(cell)
        return cid

    def add_edge(self, source_id, target_id, label="", style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#475569;strokeWidth=1.8;endArrow=block;endFill=1;"
                "fontColor=#334155;fontSize=11;"
            )
        escaped_label = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        cell = (
            f'<mxCell id="{cid}" value="{escaped_label}" style="{style}" edge="1" parent="1" source="{source_id}" target="{target_id}">\n'
            f'  <mxGeometry relative="1" as="geometry" />\n'
            f'</mxCell>'
        )
        self.cells.append(cell)
        return cid

    def to_xml(self):
        cells_xml = "\n        ".join(self.cells)
        xml_content = f"""<mxfile host="app.diagrams.net" agent="Antigravity" version="21.0.0" type="device">
  <diagram id="diagram_page" name="{self.title}">
    <mxGraphModel dx="{self.width}" dy="{self.height}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" background="#ffffff" math="0" shadow="0">
      <root>
        {cells_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
        return xml_content

    def save(self, filename):
        xml_str = self.to_xml()
        path1 = os.path.join(DOCS_FIGS_DIR, filename)
        path2 = os.path.join(ROOT_FIGS_DIR, filename)
        with open(path1, "w", encoding="utf-8") as f:
            f.write(xml_str)
        with open(path2, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"  [OK] Saved: {filename}")


# ── ĐỊNH NGHĨA BẢNG MÀU MATERIAL ──────────────────────────────────────────
C_TITLE_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0284c7;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=13;arcSize=10;"
C_TITLE_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#16a34a;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=13;arcSize=10;"
C_TITLE_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#7c3aed;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=13;arcSize=10;"
C_TITLE_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d97706;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=13;arcSize=10;"
C_TITLE_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e11d48;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=13;arcSize=10;"

C_SKY   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2fe;strokeColor=#0284c7;strokeWidth=1.5;fontColor=#0369a1;fontSize=11;arcSize=8;"
C_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#15803d;fontSize=11;arcSize=8;"
C_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#6366f1;strokeWidth=1.5;fontColor=#4338ca;fontSize=11;arcSize=8;"
C_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#d97706;strokeWidth=1.5;fontColor=#b45309;fontSize=11;arcSize=8;"
C_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe4e6;strokeColor=#e11d48;strokeWidth=1.5;fontColor=#be123c;fontSize=11;arcSize=8;"
C_SLATE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;strokeWidth=1.5;fontColor=#334155;fontSize=11;arcSize=8;"

C_CONTAINER_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#bae6fd;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=12;fontColor=#0369a1;arcSize=6;"
C_CONTAINER_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#bbf7d0;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=12;fontColor=#15803d;arcSize=6;"
C_CONTAINER_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#faf5ff;strokeColor=#e9d5ff;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=12;fontColor=#6b21a8;arcSize=6;"
C_CONTAINER_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#fde68a;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=12;fontColor=#92400e;arcSize=6;"


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 1: KIẾN TRÚC PHÂN TẦNG IOT (4 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig01():
    d = DrawioBuilder("Kiến Trúc Phân Tầng Hệ Thống IoT", 1000, 600)
    d.add_title("KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT", x=50, y=20, w=900, h=40)

    # 4 lớp xếp tầng từ dưới lên trên
    # Lớp 1: Cảm nhận
    c1 = d.add_box("LỚP CẢM NHẬN (PERCEPTION LAYER)", 60, 80, 880, 95, C_CONTAINER_GREEN)
    d.add_box("Cảm biến môi trường / Công nghiệp\n(Nhiệt độ, Độ ẩm, Khí ga, Dòng điện)", 80, 115, 260, 45, C_GREEN)
    d.add_box("Vi điều khiển nhúng biên\n(ESP32 Xtensa LX6 @ 240 MHz)", 370, 115, 260, 45, C_GREEN)
    d.add_box("Transceiver vô tuyến LoRa\n(Semtech SX1278 - Ra-02 433 MHz)", 660, 115, 260, 45, C_GREEN)

    # Lớp 2: Mạng truyền dẫn
    c2 = d.add_box("LỚP MẠNG TRUYỀN DẪN (NETWORK TRANSMISSION LAYER)", 60, 205, 880, 95, C_CONTAINER_BLUE)
    d.add_box("Sóng vô tuyến LoRa CSS\n(Băng tần ISM 433 MHz, BW 125 kHz)", 80, 240, 260, 45, C_SKY)
    d.add_box("Trạm Gateway Đa Kênh\n(Raspberry Pi CM4 + 3x SX1278)", 370, 240, 260, 45, C_SKY)
    d.add_box("Giao thức mạng IP / Viễn thông\n(Ethernet / Wi-Fi / 4G LTE)", 660, 240, 260, 45, C_SKY)

    # Lớp 3: Trung gian & Điện toán
    c3 = d.add_box("LỚP TRUNG GIAN & ĐIỆN TOÁN (MIDDLEWARE & CLOUD LAYER)", 60, 330, 880, 95, C_CONTAINER_PURP)
    d.add_box("Network Server (NS)\n(Điều phối MAC, Khử trùng lặp)", 80, 365, 260, 45, C_PURP)
    d.add_box("Message Broker & Cache\n(MQTT Broker / REST API)", 370, 365, 260, 45, C_PURP)
    d.add_box("Cơ sở dữ liệu chuỗi thời gian\n(Time-Series Database / Cloud Storage)", 660, 365, 260, 45, C_PURP)

    # Lớp 4: Ứng dụng
    c4 = d.add_box("LỚP ỨNG DỤNG (APPLICATION LAYER)", 60, 455, 880, 95, C_CONTAINER_AMBER)
    d.add_box("Giám sát đô thị thông minh\n(Smart City Infrastructure)", 80, 490, 260, 45, C_AMBER)
    d.add_box("Router-style Web Dashboard\n(Giao diện điều hành thời gian thực)", 370, 490, 260, 45, C_AMBER)
    d.add_box("Nông nghiệp chính xác & Logistics\n(Smart Agriculture & Asset Tracking)", 660, 490, 260, 45, C_AMBER)

    # Arrows giữa các lớp
    d.add_edge(c1, c2, "LoRa CSS Wireless Link")
    d.add_edge(c2, c3, "TCP/IP Socket / MQTT")
    d.add_edge(c3, c4, "REST API / WebSockets")

    d.save("01_kien_truc_iot_4_lop.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2: NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS
# ══════════════════════════════════════════════════════════════════════════
def build_fig02():
    d = DrawioBuilder("Nguyên Lý Điều Chế LoRa CSS", 1000, 500)
    d.add_title("NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ CHIRP (LORA CHIRP SPREAD SPECTRUM)", x=50, y=20, w=900, h=40)

    b1 = d.add_box("DỮ LIỆU NHỊ PHÂN\n(Binary Bitstream)\n1 0 1 1 0 ...", 60, 110, 150, 75, C_SLATE)
    b2 = d.add_box("NHÓM SF BIT\n(Mã hóa Symbol)\nKý hiệu k ∈ [0, 2^SF - 1]", 250, 110, 160, 75, C_SKY)
    b3 = d.add_box("BỘ TẠO CHIRP CSS\n(Frequency Sweeping)\nf(t) = f_start + (BW / T_s) * t", 450, 110, 180, 75, C_GREEN)
    b4 = d.add_box("KHUẾCH ĐẠI CÔNG SUẤT\n(RF Power Amplifier)\nPA_BOOST = +17 dBm", 670, 110, 160, 75, C_AMBER)
    b5 = d.add_box("ANTEN PHÁT 433 MHz\n(Sóng điện từ lan truyền\ntrong không gian)", 860, 110, 140, 75, C_ROSE)

    d.add_edge(b1, b2, "Nhóm SF bits")
    d.add_edge(b2, b3, "Ký hiệu điều chế")
    d.add_edge(b3, b4, "Tín hiệu Chirp")
    d.add_edge(b4, b5, "RF Power")

    # Khung trực quan dạng sóng Chirp ở dưới
    box_wave = d.add_box("ĐẶC TÍNH TẦN SỐ THEO THỜI GIAN CỦA TÍN HIỆU LORA CHIRP (SPECTROGRAM)", 60, 230, 940, 220, C_CONTAINER_BLUE)
    d.add_box("Tần số cao (f_0 + BW/2)\n\n\nTần số tâm (f_0 = 433.x MHz)\n\n\nTần số thấp (f_0 - BW/2)", 80, 270, 180, 150, C_SLATE)
    d.add_box("CHIRP CƠ SỞ (UP-CHIRP)\nQuét tần số tuyến tính từ thấp lên cao\nThời gian Symbol T_s = 2^SF / BW\n(Với SF=7, BW=125kHz: T_s = 1.024 ms)", 290, 270, 310, 150, C_GREEN)
    d.add_box("CHIRP DỊCH TẦN (MODULATED CHIRP)\nĐiểm bắt đầu nhảy tần số xác định giá trị bit\nKhả năng giải điều chế dưới nhiễu nền\nNgưỡng SNR giải mã: -7.5 dB đến -20 dB", 630, 270, 350, 150, C_SKY)

    d.save("02_nguyen_ly_dieu_che_lora_css.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3: KIẾN TRÚC MẠNG LORAWAN HÌNH SAO (STAR-OF-STARS)
# ══════════════════════════════════════════════════════════════════════════
def build_fig03():
    d = DrawioBuilder("Kiến Trúc Mạng LoRaWAN", 1000, 600)
    d.add_title("KIẾN TRÚC MẠNG LORAWAN HÌNH SAO LỒNG NHAU (STAR-OF-STARS)", x=50, y=20, w=900, h=40)

    # 3 Khối chính theo cột
    # Cột 1: End-Nodes
    d.add_box("THIẾT BỊ ĐẦU CUỐI (END-NODES)", 50, 80, 220, 480, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + Ra-02 433 MHz\nOLED SSD1306", 70, 120, 180, 100, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + Ra-02 433 MHz\nOLED SSD1306", 70, 260, 180, 100, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + Ra-02 433 MHz\nOLED SSD1306", 70, 400, 180, 100, C_GREEN)

    # Cột 2: Gateway
    d.add_box("TRẠM CỔNG (MULTI-CHANNEL GATEWAY)", 330, 80, 310, 480, C_CONTAINER_BLUE)
    gw = d.add_box("RASPBERRY PI CM4 GATEWAY\n(Broadcom BCM2711 Quad-Core @ 1.5 GHz)\n\n3x Semtech SX1278 trên bus SPI0:\n- Module #1: CH1 433.175 MHz\n- Module #2: CH2 433.375 MHz\n- Module #3: CH3 433.575 MHz\n\nKiến trúc Zero-Blindness (Không điểm mù)", 350, 160, 270, 290, C_SKY)

    # Cột 3: Servers
    d.add_box("MÁY CHỦ QUẢN TRỊ & ỨNG DỤNG", 700, 80, 250, 480, C_CONTAINER_PURP)
    ns = d.add_box("NETWORK SERVER (NS)\n- Khử bản tin trùng lặp\n- Kiểm tra tính toàn vẹn MIC\n- Quản lý cửa sổ nhận RX1/RX2", 720, 150, 210, 120, C_PURP)
    as_srv = d.add_box("APPLICATION SERVER & WEB\n- Giải mã AppSKey Payload\n- Cơ sở dữ liệu CSV / Logs\n- Router-style Web Dashboard", 720, 340, 210, 130, C_AMBER)

    # Connections
    d.add_edge(na, gw, "LoRa RF 433.x MHz")
    d.add_edge(nb, gw, "LoRa RF 433.x MHz")
    d.add_edge(nc, gw, "LoRa RF 433.x MHz")
    d.add_edge(gw, ns, "TCP/IP / MQTT")
    d.add_edge(ns, as_srv, "JSON Data")

    d.save("03_kien_truc_mang_lorawan_star.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4: SO SÁNH CLOUD AI VÀ EDGE TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig04():
    d = DrawioBuilder("So Sánh Cloud AI vs Edge TinyML", 1000, 550)
    d.add_title("SO SÁNH MÔ HÌNH CLOUD AI TRUYỀN THỐNG VÀ EDGE TINYML BIÊN", x=50, y=20, w=900, h=40)

    # Top: Cloud AI (Nhược điểm)
    d.add_box("1. MÔ HÌNH TRUYỀN THỐNG: CLOUD AI (ĐIỆN TOÁN ĐÁM MÂY TẬP TRUNG)", 50, 80, 900, 190, C_CONTAINER_AMBER)
    c1 = d.add_box("Node Cảm biến\n(Thu thập đặc trưng RF)", 70, 125, 160, 60, C_SLATE)
    c2 = d.add_box("Gateway Chuyển tiếp\n(Thu và đẩy gói tin)", 290, 125, 160, 60, C_SLATE)
    c3 = d.add_box("Máy chủ Cloud AI\n(Thực thi học máy lớn)", 510, 125, 160, 60, C_AMBER)
    c4 = d.add_box("Bản tin Downlink RF\n(Gửi lệnh nhảy kênh về Node)", 730, 125, 190, 60, C_ROSE)

    d.add_edge(c1, c2, "Uplink RF")
    d.add_edge(c2, c3, "Internet / LTE")
    d.add_edge(c3, c4, "Tính toán đám mây")
    d.add_edge(c4, c1, "Downlink (Trễ cao & Tốn pin)", "edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e11d48;dashed=1;")

    d.add_box("HẠN CHẾ CHÍ MẠNG: Độ trễ phản hồi lớn (> 2-5 giây), tiêu tốn năng lượng pin của Node do mở cửa sổ thu Downlink, phụ thuộc đường truyền Internet.", 70, 205, 850, 45, C_ROSE)

    # Bottom: Edge TinyML (Ưu điểm)
    d.add_box("2. MÔ HÌNH HIỆN ĐẠI: EDGE TINYML (HỌC MÁY TRỰC TIẾP TRÊN VI ĐIỀU KHIỂN BIÊN)", 50, 290, 900, 210, C_CONTAINER_GREEN)
    e1 = d.add_box("Cảm biến / Bộ đệm CSI\n(Cửa sổ trượt 10 bước)", 70, 340, 180, 65, C_GREEN)
    e2 = d.add_box("Mô hình TinyML Nhúng\n(Separable 1D-CNN trên ESP32)\nFlash: 8.65 KB | RAM: 10 KB", 310, 340, 230, 65, C_GREEN)
    e3 = d.add_box("Quyết định nhảy kênh tại chỗ\n(ArgMax Kênh tối ưu)\nĐộ trễ suy luận < 10 ms", 600, 340, 190, 65, C_GREEN)
    e4 = d.add_box("Phát sóng trên kênh sạch\n(PDR đạt 95% - 100%)", 840, 340, 160, 65, C_SKY)

    d.add_edge(e1, e2, "Dữ liệu 10x9")
    d.add_edge(e2, e3, "Softmax")
    d.add_edge(e3, e4, "Chuyển tần số RF")

    d.add_box("ƯU ĐIỂM VƯỢT TRỘI: Tự chủ hoàn toàn (Offline Autonomy), độ trễ cực thấp (< 10 ms), không tốn năng lượng Downlink, bảo mật tuyệt đối.", 70, 425, 850, 45, C_GREEN)

    d.save("04_so_sanh_cloud_ai_vs_edge_tinyml.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 5: BÀI TOÁN LỰA CHỌN KÊNH DỰA TRÊN TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig05():
    d = DrawioBuilder("Cơ Chế Nhảy Kênh TinyML", 1000, 520)
    d.add_title("CƠ CHẾ DỰ ĐOÁN VÀ NHẢY KÊNH THÍCH ỨNG DỰA TRÊN TINYML", x=50, y=20, w=900, h=40)

    # Khung các bước từ trái sang phải
    b1 = d.add_box("CỬA SỔ TRƯỢT FIFO (W = 10)\n10 bước thời gian gần nhất\n(Mỗi bước 9 đặc trưng CSI:\nCH1-3, RSSI, SNR, Size, Freq)", 60, 100, 200, 110, C_CONTAINER_BLUE)
    b2 = d.add_box("CHUẨN HÓA Z-SCORE\nz = (x - mean) / scale\nBảng hệ số tĩnh SCALER\nNhúng trong model.h", 300, 110, 180, 90, C_SKY)
    b3 = d.add_box("BỘ SUY LUẬN TINYML\n(TensorFlow Lite Micro)\nSeparable 1D-CNN (878 params)\nTensor Arena = 10 KB\nThời gian suy luận: 9.3 ms", 520, 100, 200, 110, C_CONTAINER_GREEN)
    b4 = d.add_box("XÁC SUẤT SOFTMAX\n[P0, P1, P2]\nKênh 0: 433.175 MHz\nKênh 1: 433.375 MHz\nKênh 2: 433.575 MHz", 760, 110, 180, 90, C_PURP)

    d.add_edge(b1, b2, "Ma trận 10x9")
    d.add_edge(b2, b3, "Vector chuẩn hóa")
    d.add_edge(b3, b4, "Logits")

    # Quyết định và phát sóng ở hàng dưới
    b5 = d.add_box("QUYẾT ĐỊNH ARGMAX\nbest_channel = argmax(P0, P1, P2)\nChọn kênh có xác suất va chạm thấp nhất", 450, 260, 280, 65, C_AMBER)
    b6 = d.add_box("CHUYỂN TẦN SỐ PHẦN CỨNG\nLoRa.setFrequency(CH_FREQ[best_channel])\nModule Semtech SX1278 Ra-02", 450, 360, 280, 65, C_ROSE)
    b7 = d.add_box("PHÁT GÓI TIN LORA (TX)\nCông suất: +17 dBm | SF=7 | BW=125 kHz\nTỷ lệ nhận gói PDR đạt 95% - 100%", 450, 455, 280, 50, C_GREEN)

    d.add_edge(b4, b5, "Chỉ số xác suất", "edgeStyle=orthogonalEdgeStyle;rounded=1;")
    d.add_edge(b5, b6, "Kênh tối ưu (0, 1, 2)")
    d.add_edge(b6, b7, "Kích hoạt PA_BOOST")

    d.save("05_bai_toan_lua_chon_kenh_tinyml.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 6: SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig06():
    d = DrawioBuilder("Sơ Đồ Khối Toàn Hệ Thống", 1100, 650)
    d.add_title("SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM LORA TINYML CHANNEL HOPPING", x=50, y=20, w=1000, h=40)

    # 3 Khối chính: Trạm phát, Kênh truyền, Trạm thu
    # Khối 1: 3 End-Nodes
    d.add_box("PHÂN HỆ TRẠM PHÁT: 03 END-NODES ĐỘC LẬP", 50, 80, 310, 530, C_CONTAINER_GREEN)
    na = d.add_box("NODE A (TẦNG 1)\n- ESP32 DevKit V1 (Core 0: Sampler / Core 1: TinyML)\n- Semtech SX1278 Ra-02 (VSPI 10 MHz)\n- Màn hình OLED SSD1306 (I2C 400 kHz)", 70, 120, 270, 120, C_GREEN)
    nb = d.add_box("NODE B (TẦNG 2)\n- ESP32 DevKit V1 (Core 0: Sampler / Core 1: TinyML)\n- Semtech SX1278 Ra-02 (VSPI 10 MHz)\n- Màn hình OLED SSD1306 (I2C 400 kHz)", 70, 270, 270, 120, C_GREEN)
    nc = d.add_box("NODE C (NGOÀI TRỜI)\n- ESP32 DevKit V1 (Core 0: Sampler / Core 1: TinyML)\n- Semtech SX1278 Ra-02 (VSPI 10 MHz)\n- Màn hình OLED SSD1306 (I2C 400 kHz)", 70, 420, 270, 120, C_GREEN)

    # Khối 2: Môi trường vô tuyến
    d.add_box("MÔI TRƯỜNG VÔ TUYẾN 433 MHz ISM", 400, 80, 250, 530, C_CONTAINER_AMBER)
    ch1 = d.add_box("KÊNH 1: 433.175 MHz\n(BW 125 kHz / SF7 / CR 4/5)", 420, 150, 210, 80, C_AMBER)
    ch2 = d.add_box("KÊNH 2: 433.375 MHz\n(BW 125 kHz / SF7 / CR 4/5)", 420, 270, 210, 80, C_AMBER)
    ch3 = d.add_box("KÊNH 3: 433.575 MHz\n(BW 125 kHz / SF7 / CR 4/5)", 420, 390, 210, 80, C_AMBER)
    d.add_box("Khoảng cách bảo vệ: 200 kHz\n(Ngăn chặn can nhiễu lân kênh)", 420, 500, 210, 50, C_SLATE)

    # Khối 3: Gateway
    d.add_box("PHÂN HỆ TRẠM THU: MULTI-RECEIVER GATEWAY", 690, 80, 360, 530, C_CONTAINER_BLUE)
    rx_mod = d.add_box("3 MODULE THU SX1278 TRÊN BUS SPI0\n- Module 1: CS=GPIO 8, DIO0=GPIO 24\n- Module 2: CS=GPIO 7, DIO0=GPIO 23\n- Module 3: CS=GPIO 25, DIO0=GPIO 22", 710, 120, 320, 95, C_SKY)
    cm4_box = d.add_box("RASPBERRY PI COMPUTE MODULE 4 (CM4)\n- Quad-Core Cortex-A72 @ 1.5 GHz, 2 GB LPDDR4\n- 3 Luồng Python RX Worker độc lập\n- Thu song song 3 kênh (Zero-Blindness)", 710, 235, 320, 105, C_SKY)
    d.add_box("HỆ THỐNG GHI NHẬN & QUẢN TRỊ DỮ LIỆU\n- Tệp lưu trữ CSV: logs/ & csv/\n- Nginx Reverse Proxy (Port 80)\n- Embedded REST API Server (Port 8080)", 710, 360, 320, 95, C_PURP)
    d.add_box("ROUTER-STYLE WEB DASHBOARD\n- Trực quan hóa Telemetry thời gian thực\n- Giám sát RSSI, SNR, PDR, Trạng thái Kênh", 710, 475, 320, 90, C_AMBER)

    # Arrows
    d.add_edge(na, ch1, "Chuyển kênh linh hoạt")
    d.add_edge(nb, ch2, "Chuyển kênh linh hoạt")
    d.add_edge(nc, ch3, "Chuyển kênh linh hoạt")
    d.add_edge(ch1, rx_mod, "Thu đồng thời")
    d.add_edge(ch2, rx_mod, "Thu đồng thời")
    d.add_edge(ch3, rx_mod, "Thu đồng thời")

    d.save("06_so_do_khoi_toan_he_thong.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 7: ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA
# ══════════════════════════════════════════════════════════════════════════
def build_fig07():
    d = DrawioBuilder("Định Dạng Gói Tin LoRa", 1000, 450)
    d.add_title("CẤU TRÚC ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA (PAYLOAD STRUCTURE)", x=50, y=20, w=900, h=40)

    # Thanh các trường gói tin tuần tự
    d.add_box("TIÊU ĐỀ & ĐỊNH DANH (HEADER)", 60, 90, 350, 40, C_TITLE_BLUE)
    d.add_box("THÔNG SỐ & MỐC THỜI GIAN (METADATA)", 430, 90, 210, 40, C_TITLE_PURP)
    d.add_box("TẢI TRỌNG THỰC NGHIỆM (PAYLOAD)", 660, 90, 200, 40, C_TITLE_AMBER)
    d.add_box("KIỂM TRA LỖI", 880, 90, 80, 40, C_TITLE_ROSE)

    # Từng ô trường byte
    f1 = d.add_box("Node_ID\n(1 Byte)\n'A', 'B', 'C'", 60, 140, 100, 80, C_SKY)
    f2 = d.add_box("Packet_ID\n(2 Bytes)\n0 - 65,535", 170, 140, 110, 80, C_SKY)
    f3 = d.add_box("Current_CH\n(1 Byte)\n0, 1, 2", 290, 140, 120, 80, C_SKY)

    f4 = d.add_box("Payload_Size\n(1 Byte)\n30 - 250 Bytes", 430, 140, 100, 80, C_PURP)
    f5 = d.add_box("Timestamp\n(4 Bytes)\nmillis()", 540, 140, 100, 80, C_PURP)

    f6 = d.add_box("Dummy_Data\n(Biến thiên: 21 đến 241 Bytes)\nMảng đệm mở rộng kích thước gói", 660, 140, 200, 80, C_AMBER)
    f7 = d.add_box("CRC\n(2 Bytes)\nHardware", 880, 140, 80, 80, C_ROSE)

    # Chú thích ở dưới
    d.add_box("TỔNG CHIỀU DÀI GÓI TIN THỰC NGHIỆM QUÉT (PAYLOAD SWEEPING): 30B, 74B, 118B, 162B, 206B, 250B", 60, 250, 900, 40, C_CONTAINER_GREEN)
    d.add_box("CƠ CHẾ GIẢI MÃ TẠI GATEWAY:\nKhi nhận gói tin toàn vẹn CRC, Gateway giải mã các trường trên và đồng thời đọc thanh ghi phần cứng SX1278 để lấy:\n1. RSSI_pkt (dBm): Cường độ tín hiệu thu\n2. SNR_pkt (dB): Tỷ số tín hiệu trên tạp âm\nGhi lại bản ghi log chuẩn: <Timestamp, Node_ID, Packet_ID, Frequency, RSSI, SNR, Size, Current_CH, CRC_Status>", 60, 310, 900, 100, C_SLATE)

    d.save("07_dinh_dang_khung_truyen_goi_tin.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 8: 5 KIẾN TRÚC MẠNG NƠ-RON TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig08():
    d = DrawioBuilder("5 Kiến Trúc TinyML", 1100, 600)
    d.add_title("ĐỐI SÁNH 5 KIẾN TRÚC MẠNG NƠ-RON TINYML CHO BÀI TOÁN LỰA CHỌN KÊNH", x=50, y=20, w=1000, h=40)

    # 5 cột tương ứng 5 mô hình
    w_card = 185
    gap = 20
    start_x = 55

    # Card 1: FCNN
    x1 = start_x
    d.add_box("1. BASELINE FCNN\n(Multi-Layer Perceptron)", x1, 80, w_card, 45, C_TITLE_BLUE)
    d.add_box("Kiến trúc:\n- Input Flat (90D)\n- Dense (16, ReLU)\n- Dropout (0.15)\n- Dense (12, ReLU)\n- Dense (3, Softmax)\n\nTham số: 1,699\nFlash: 8.84 KB\nĐộ trễ: 6.9 ms\nAccuracy: 90.46%", x1, 135, w_card, 380, C_SKY)

    # Card 2: 1D-CNN
    x2 = x1 + w_card + gap
    d.add_box("2. 1D-CNN\n(Temporal ConvNet)", x2, 80, w_card, 45, C_TITLE_PURP)
    d.add_box("Kiến trúc:\n- Input Seq (10, 9)\n- Conv1D (16, k=3)\n- BatchNorm\n- MaxPool1D (2)\n- Conv1D (32, k=3)\n- GlobalAvgPool1D\n- Dense (16, ReLU)\n- Dense (3, Softmax)\n\nTham số: 2,659\nFlash: 16.34 KB\nĐộ trễ: 14.2 ms\nAccuracy: 90.25%", x2, 135, w_card, 380, C_PURP)

    # Card 3: GRU
    x3 = x2 + w_card + gap
    d.add_box("3. GRU RNN\n(Gated Recurrent Unit)", x3, 80, w_card, 45, C_TITLE_AMBER)
    d.add_box("Kiến trúc:\n- Input Seq (10, 9)\n- GRU (16, unroll)\n- Dropout (0.15)\n- Dense (16, ReLU)\n- Dense (3, Softmax)\n\nĐặc điểm:\nNắm bắt ngữ cảnh dài\nhạn, nhưng chi phí\ntính toán tuần tự cao\n\nTham số: 1,619\nFlash: 42.32 KB\nĐộ trễ: 61.6 ms\nAccuracy: 90.15%", x3, 135, w_card, 380, C_AMBER)

    # Card 4: Separable 1D-CNN (TỐI ƯU NHẤT)
    x4 = x3 + w_card + gap
    d.add_box("4. SEPARABLE 1D-CNN\n(MobileNet-style)", x4, 80, w_card, 45, C_TITLE_GREEN)
    d.add_box("KIẾN TRÚC TỐI ƯU NHẤT:\n- Input Seq (10, 9)\n- SepConv1D (16, k=3)\n  (Depthwise+Pointwise)\n- SepConv1D (32, k=3)\n- GlobalAvgPool1D\n- Dropout (0.15)\n- Dense (3, Softmax)\n\nGiảm 63% phép tính\nTham số: 878 (Nhỏ nhất)\nFlash: 8.65 KB\nĐộ trễ: 9.3 ms\nAccuracy: 90.51%", x4, 135, w_card, 380, C_GREEN)

    # Card 5: ResNet-1D
    x5 = x4 + w_card + gap
    d.add_box("5. RESNET-1D\n(Residual Network)", x5, 80, w_card, 45, C_TITLE_ROSE)
    d.add_box("Kiến trúc:\n- Input Seq (10, 9)\n- Conv1D (16, k=3)\n- Residual Block:\n  [Conv1D + Conv1D]\n  Skip Connection (+x)\n- GlobalAvgPool1D\n- Dense (16, ReLU)\n- Dense (3, Softmax)\n\nChống triệt tiêu gradient\nTham số: 2,339\nFlash: 14.73 KB\nĐộ trễ: 15.2 ms\nAccuracy: 90.56%", x5, 135, w_card, 380, C_ROSE)

    d.add_box("KẾT LUẬN LỰA CHỌN: Depthwise Separable 1D-CNN được chọn để triển khai thực tế trên ESP32 nhờ cân bằng tối ưu tuyệt đối: dung lượng nhỏ nhất (8.65 KB), số tham số ít nhất (878), độ trễ dưới 10 ms và độ chính xác đạt 90.51%.", 55, 530, 990, 45, C_CONTAINER_GREEN)

    d.save("08_5_kien_truc_tinyml.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 9: QUY TRÌNH XỬ LÝ DỮ LIỆU THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig09():
    d = DrawioBuilder("Pipeline Xử Lý Dữ Liệu", 1000, 500)
    d.add_title("QUY TRÌNH KỸ THUẬT XỬ LÝ & CHUẨN HÓA DỮ LIỆU THỰC NGHIỆM", x=50, y=20, w=900, h=40)

    p1 = d.add_box("BƯỚC 1: TRÍCH XUẤT RAW LOGS\n- 21,600 gói tin từ Gateway\n- Phân tách theo Node (A, B, C)\n- Lọc bản tin lỗi CRC", 60, 90, 200, 90, C_CONTAINER_BLUE)
    p2 = d.add_box("BƯỚC 2: BÙ ĐẮP GÓI MẤT\n- Quét chuỗi Packet_ID\n- Phát hiện gián đoạn Delta > 1\n- Gán phạt: RSSI=-120 dBm, SNR=-15", 290, 90, 200, 90, C_CONTAINER_PURP)
    p3 = d.add_box("BƯỚC 3: CỬA SỔ TRƯỢT W=10\n- Tạo tensor (10 bước x 9 đặc trưng)\n- Gán nhãn kênh mục tiêu\n- Khử hoàn toàn rò rỉ nhãn", 520, 90, 200, 90, C_CONTAINER_AMBER)
    p4 = d.add_box("BƯỚC 4: CHUẨN HÓA & SPLIT\n- Chuẩn hóa Z-Score StandardScaler\n- Lưu bộ tham số SCALER\n- Phân chia: 60% Train / 20% Val / 20% Test", 750, 90, 210, 90, C_CONTAINER_GREEN)

    d.add_edge(p1, p2, "Dữ liệu thô")
    d.add_edge(p2, p3, "Dữ liệu liên tục")
    d.add_edge(p3, p4, "Bộ dữ liệu chuỗi")

    # Đầu ra ở hàng dưới
    d.add_box("ĐẦU RA CỦA QUY TRÌNH XỬ LÝ DỮ LIỆU (READY DATASET & FIRMWARE ASSETS)", 60, 220, 900, 240, C_CONTAINER_GREEN)
    d.add_box("dataset_ready.csv\n19,440 mẫu chuỗi thời gian\n90 cột đặc trưng (feat_0..89)\nCân bằng 3 kênh nhãn", 80, 260, 260, 80, C_GREEN)
    d.add_box("Tập Train / Val / Test\nTrain: 11,664 mẫu (60%)\nVal: 3,888 mẫu (20%)\nTest: 3,888 mẫu (20%)", 370, 260, 260, 80, C_SKY)
    d.add_box("Hệ số SCALER nhúng C\nSCALER_MEAN[9]\nSCALER_SCALE[9]\nĐồng bộ trong model.h", 660, 260, 270, 80, C_AMBER)

    d.add_box("ĐẶC TÍNH BẢO ĐẢM KHOA HỌC: Không có rò rỉ thông tin nhãn mục tiêu vào các bước trượt quá khứ; bảo toàn tính quy luật vật lý của kênh vô tuyến; phân phối nhãn cân bằng giữa 3 kênh tần số.", 80, 360, 850, 70, C_SLATE)

    d.save("09_pipeline_xu_ly_du_lieu.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 10: SƠ ĐỒ BỐ TRÍ THỰC ĐỊA TRONG TÒA NHÀ
# ══════════════════════════════════════════════════════════════════════════
def build_fig10():
    d = DrawioBuilder("Bố Trí Thực Địa Tòa Nhà", 1000, 600)
    d.add_title("SƠ ĐỒ BỐ TRÍ MÔI TRƯỜNG THỰC NGHIỆM TRONG KHUÔN VIÊN TÒA NHÀ ĐẠI HỌC", x=50, y=20, w=900, h=40)

    # Vẽ tòa nhà 2 tầng và khu ngoài trời
    d.add_box("TÒA NHÀ ĐẠI HỌC (KHÔNG GIAN THỰC ĐỊA TRONG NHÀ)", 60, 80, 580, 480, C_CONTAINER_BLUE)
    d.add_box("KHÔNG GIAN NGOÀI TRỜI (OUTDOOR)", 670, 80, 290, 480, C_CONTAINER_GREEN)

    # Tầng 2
    d.add_box("TẦNG 2: HÀNH LANG VÀ PHÒNG THÍ NGHIỆM", 80, 120, 540, 190, C_SLATE)
    gw = d.add_box("MULTI-CHANNEL GATEWAY\n(Raspberry Pi CM4 + 3x SX1278)\nVị trí trung tâm trên cao\nNguồn điện liên tục", 100, 160, 230, 110, C_SKY)
    nb = d.add_box("NODE B (TẦNG 2)\nCự ly: 60 mét đến Gateway\nĐiều kiện: Che khuất phi đường thẳng (NLOS)\nXuyên qua 2 lớp sàn & tường bê tông", 370, 160, 230, 110, C_AMBER)

    # Tầng 1
    d.add_box("TẦNG 1: SẢNH VÀ PHÒNG HỌC", 80, 340, 540, 190, C_SLATE)
    na = d.add_box("NODE A (TẦNG 1)\nCự ly: 25 mét đến Gateway\nĐiều kiện: LOS / NLOS nhẹ\nXuyên qua 1 vách ngăn kính và tường mỏng", 100, 380, 250, 120, C_GREEN)

    # Ngoài trời
    nc = d.add_box("NODE C (KHU VỰC SÂN TRƯỜNG)\nCự ly: 110 mét đến Gateway\nĐiều kiện: Tán cây rậm rạp, tường bao che khuất\nSuy hao truyền sóng cao nhất", 690, 240, 250, 150, C_ROSE)

    # Wireless links
    d.add_edge(na, gw, "LoRa RF 25m", "strokeColor=#16a34a;strokeWidth=2;")
    d.add_edge(nb, gw, "LoRa RF 60m (NLOS)", "strokeColor=#d97706;strokeWidth=2;")
    d.add_edge(nc, gw, "LoRa RF 110m (Fading)", "strokeColor=#e11d48;strokeWidth=2;")

    d.save("10_bo_tri_thuc_dia_toa_nha.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 11: KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS
# ══════════════════════════════════════════════════════════════════════════
def build_fig11():
    d = DrawioBuilder("Kiến Trúc Firmware FreeRTOS", 1000, 550)
    d.add_title("KIẾN TRÚC FIRMWARE ĐA NHIỆM THỜI GIAN THỰC FREERTOS TRÊN ESP32", x=50, y=20, w=900, h=40)

    # Nhân CPU 0
    d.add_box("CORE 0 (ESP32): THU THẬP CẢM BIẾN & HIỂN THỊ HMI", 60, 80, 420, 440, C_CONTAINER_BLUE)
    t_samp = d.add_box("Task_Sampler (Mức ưu tiên 1)\n- Đọc cảm biến mô phỏng\n- Ghi nhận thông số gói tin\n- Cập nhật bộ đệm trượt FIFO (10x9)", 80, 130, 380, 85, C_SKY)
    t_oled = d.add_box("Task_OLED (Mức ưu tiên 1)\n- Chu kỳ quét hiển thị 10 Hz\n- Cập nhật màn hình SSD1306 (I2C)\n- Hiển thị: Kênh hiện tại, PDR, RSSI, SNR", 80, 250, 380, 85, C_SKY)

    # Nhân CPU 1
    d.add_box("CORE 1 (ESP32): SUY LUẬN TINYML & TRUYỀN THÔNG RF", 520, 80, 420, 440, C_CONTAINER_GREEN)
    t_ml = d.add_box("Task_TinyML (Mức ưu tiên 2)\n- Chuẩn hóa Z-Score bộ đệm 10x9\n- Thực thi suy luận TFLite Micro (< 10 ms)\n- ArgMax xác định kênh sạch nhất", 540, 130, 380, 85, C_GREEN)
    t_tx = d.add_box("Task_LoRaTX (Mức ưu tiên 3 - Cao nhất)\n- Nhận chỉ số kênh từ Queue\n- Cấu hình tần số Ra-02 (LoRa.setFrequency)\n- Đóng gói bản tin và phát sóng RF (+17 dBm)", 540, 250, 380, 85, C_GREEN)

    # Cơ chế đồng bộ IPC ở giữa
    mutex = d.add_box("MUTEX BẢO VỆ DỮ LIỆU\n(historyMutex)\nBảo toàn tính nhất quán của mảng FIFO 10x9", 80, 380, 380, 70, C_AMBER)
    queue = d.add_box("FREE RTOS QUEUE\n(channelQueue - Độ dài 1)\nChuyển giao chỉ số kênh tối ưu (0, 1, 2)", 540, 380, 380, 70, C_PURP)

    d.add_edge(t_samp, mutex, "Khóa Mutex ghi")
    d.add_edge(mutex, t_ml, "Khóa Mutex đọc an toàn")
    d.add_edge(t_ml, queue, "xQueueOverwrite(best_ch)")
    d.add_edge(queue, t_tx, "xQueueReceive(target_ch)")

    d.save("11_kien_truc_freertos_da_nhiem.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 12: SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32
# ══════════════════════════════════════════════════════════════════════════
def build_fig12():
    d = DrawioBuilder("Sơ Đồ Đấu Nối End-Node", 1000, 580)
    d.add_title("SƠ ĐỒ ĐẤU NỐI CHI TIẾT PHẦN CỨNG THIẾT BỊ ĐẦU CUỐI END-NODE ESP32", x=50, y=20, w=900, h=40)

    # ESP32 ở giữa
    mcu = d.add_box("VI ĐIỀU KHIỂN ESP32 DEVKIT V1\n(Xtensa Dual-Core 32-bit LX6 @ 240 MHz)\nSRAM: 520 KB | Flash: 4 MB", 360, 90, 280, 390, C_CONTAINER_BLUE)

    # Module LoRa bên trái
    rf = d.add_box("MODULE SEMTECH SX1278 (RA-02)\nBăng tần: 433 MHz ISM\nCông suất: +17 dBm (PA_BOOST)\nGiao tiếp: VSPI Hardware Bus", 60, 120, 250, 220, C_CONTAINER_GREEN)
    d.add_box("Chân kết nối SX1278:\n- MOSI ──> GPIO 27\n- MISO <── GPIO 19\n- SCK  ──> GPIO 18 (10 MHz)\n- NSS  ──> GPIO 5 (CS)\n- RST  ──> GPIO 14\n- DIO0 <── GPIO 26 (Ngắt TxDone)\n- VCC  ──> 3.3V (Kèm tụ lọc)\n- GND  ──> GND chung", 75, 185, 220, 140, C_GREEN)

    # Màn hình OLED bên phải
    oled = d.add_box("MÀN HÌNH OLED SSD1306\nKích thước: 0.96 inch (128x64)\nGiao tiếp: I2C Fast Mode (400 kHz)", 690, 120, 250, 180, C_CONTAINER_PURP)
    d.add_box("Chân kết nối OLED:\n- SDA <==> GPIO 21\n- SCL ───> GPIO 22\n- VCC ───> 3.3V\n- GND ───> GND chung", 705, 185, 220, 100, C_PURP)

    # Khối nguồn & Mạch lọc ở dưới
    pwr = d.add_box("MẠCH NGUỒN VÀ BỘ TỤ BÙ CHỐNG SỤT ÁP ĐỈNH\n- Cấp nguồn 3.3V DC ổn định\n- Tụ hóa 100 µF song song tụ gốm 100 nF đặt sát chân VCC của module Ra-02\n- Triệt tiêu dòng đỉnh 130 mA khi phát sóng, chống Brownout Reset ESP32", 200, 480, 600, 70, C_AMBER)

    # Connections
    d.add_edge(rf, mcu, "Bus VSPI & Ngắt DIO0")
    d.add_edge(mcu, oled, "Bus I2C")
    d.add_edge(pwr, mcu, "3.3V / GND")

    d.save("12_so_do_noi_chan_end_node_esp32.drawio")


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 13: SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY CM4
# ══════════════════════════════════════════════════════════════════════════
def build_fig13():
    d = DrawioBuilder("Sơ Đồ Đấu Nối Gateway CM4", 1000, 600)
    d.add_title("SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY TRÊN RASPBERRY PI CM4", x=50, y=20, w=900, h=40)

    # CM4 ở giữa
    cm4 = d.add_box("RASPBERRY PI COMPUTE MODULE 4 (CM4)\n(Broadcom BCM2711 Quad-Core @ 1.5 GHz)\nĐầu cắm GPIO 40-Pin Header\nChạy hệ điều hành Linux 64-bit", 360, 90, 280, 470, C_CONTAINER_BLUE)

    # 3 Module thu SX1278
    m1 = d.add_box("MODULE THU #1 (KÊNH 1 - 433.175 MHz)\n- MOSI ──> Pin 19 (GPIO 10)\n- MISO <── Pin 21 (GPIO 9)\n- SCLK ──> Pin 23 (GPIO 11)\n- NSS  ──> Pin 24 (GPIO 8 - SPI CE0)\n- DIO0 <── Pin 18 (GPIO 24 - Ngắt RxDone)", 60, 100, 260, 130, C_SKY)

    m2 = d.add_box("MODULE THU #2 (KÊNH 2 - 433.375 MHz)\n- MOSI ──> Pin 19 (GPIO 10)\n- MISO <── Pin 21 (GPIO 9)\n- SCLK ──> Pin 23 (GPIO 11)\n- NSS  ──> Pin 26 (GPIO 7 - SPI CE1)\n- DIO0 <── Pin 16 (GPIO 23 - Ngắt RxDone)", 60, 260, 260, 130, C_GREEN)

    m3 = d.add_box("MODULE THU #3 (KÊNH 3 - 433.575 MHz)\n- MOSI ──> Pin 19 (GPIO 10)\n- MISO <── Pin 21 (GPIO 9)\n- SCLK ──> Pin 23 (GPIO 11)\n- NSS  ──> Pin 22 (GPIO 25 - Soft CS)\n- DIO0 <── Pin 15 (GPIO 22 - Ngắt RxDone)", 60, 420, 260, 130, C_AMBER)

    # Khối chức năng Gateway bên phải
    d.add_box("PHẦN MỀM ĐIỀU HÀNH GATEWAY TRÊN CM4", 680, 100, 270, 450, C_CONTAINER_PURP)
    d.add_box("3 LUỒNG WORKER THU ĐỘC LẬP\n- Thread 1: Lắng nghe CH1 433.175\n- Thread 2: Lắng nghe CH2 433.375\n- Thread 3: Lắng nghe CH3 433.575\nKhả năng thu 100% không nghẽn", 700, 150, 230, 110, C_PURP)
    d.add_box("GHI LOG & CSDL CHUỖI THỜI GIAN\n- Ghi tệp CSV thời gian thực\n- Trích xuất: Timestamp, Node_ID,\n  Packet_ID, Frequency, RSSI, SNR", 700, 280, 230, 110, C_SLATE)
    d.add_box("MẠNG VÀ WEB DASHBOARD\n- Nginx Reverse Proxy (Port 80)\n- Embedded REST API (Port 8080)\n- Kết nối Router Wi-Fi / Ethernet", 700, 410, 230, 110, C_AMBER)

    d.add_edge(m1, cm4, "SPI0 CE0")
    d.add_edge(m2, cm4, "SPI0 CE1")
    d.add_edge(m3, cm4, "SPI0 CS2")

    d.save("13_so_do_noi_chan_gateway_cm4.drawio")


def main():
    print("=" * 72)
    print(" KHỞI TẠO TỰ ĐỘNG BỘ SƠ ĐỒ ĐỒ HỌA (.DRAWIO) CHO TOÀN BỘ ĐỒ ÁN")
    print("=" * 72)

    build_fig01()
    build_fig02()
    build_fig03()
    build_fig04()
    build_fig05()
    build_fig06()
    build_fig07()
    build_fig08()
    build_fig09()
    build_fig10()
    build_fig11()
    build_fig12()
    build_fig13()

    print("\n[HOÀN TẤT] Đã sinh thành công toàn bộ 13 tệp sơ đồ .drawio!")
    print(f"  + Thư mục 1: {DOCS_FIGS_DIR}")
    print(f"  + Thư mục 2: {ROOT_FIGS_DIR}")


if __name__ == "__main__":
    main()
