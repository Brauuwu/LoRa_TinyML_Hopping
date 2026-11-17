#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_drawio_diagrams.py
Tạo tự động 13 tệp sơ đồ đồ họa định dạng .drawio (XML) chất lượng cao cho đồ án:
Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML.

Đặc tính thiết kế:
- Trực quan, hiện đại, màu sắc hài hòa (Flat / Material palette).
- Chú thích tinh gọn, súc tích, tập trung vào cấu trúc, thông số chính và luồng dữ liệu.
- Không sử dụng các đoạn văn bản dài dòng, giúp sơ đồ thoáng đãng, dễ theo dõi.
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
    def __init__(self, title="Diagram", width=1000, height=600):
        self.title = title
        self.width = width
        self.height = height
        self.cells = []
        self.cell_id = 2

        # Root elements
        self.cells.append('<mxCell id="0" />')
        self.cells.append('<mxCell id="1" parent="0" />')

    def add_title(self, text, x=50, y=20, w=900, h=40):
        style = (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=none;"
            "fontColor=#ffffff;fontStyle=1;fontSize=14;shadow=1;arcSize=10;"
        )
        self.add_box(text, x, y, w, h, style)

    def add_box(self, label, x, y, w, h, style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
                "strokeWidth=1.5;fontColor=#1e293b;fontSize=11;fontFamily=Helvetica;"
            )
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

    def add_edge(self, source_id, target_id, label="", style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#475569;strokeWidth=1.8;endArrow=block;endFill=1;"
                "fontColor=#334155;fontSize=10;"
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

    def to_diagram_xml(self, diagram_id="page_1", diagram_name=None):
        name = diagram_name or self.title
        cells_xml = "\n        ".join(self.cells)
        return f"""  <diagram id="{diagram_id}" name="{name}">
    <mxGraphModel dx="{self.width}" dy="{self.height}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" background="#ffffff" math="0" shadow="0">
      <root>
        {cells_xml}
      </root>
    </mxGraphModel>
  </diagram>"""

    def to_xml(self):
        diag_xml = self.to_diagram_xml("diagram_page", self.title)
        return f"""<mxfile host="app.diagrams.net" agent="Antigravity" version="21.0.0" type="device">
{diag_xml}
</mxfile>"""

    def save(self, filename):
        xml_str = self.to_xml()
        path1 = os.path.join(DOCS_FIGS_DIR, filename)
        path2 = os.path.join(ROOT_FIGS_DIR, filename)
        with open(path1, "w", encoding="utf-8") as f:
            f.write(xml_str)
        with open(path2, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"  [OK] Saved: {filename}")


# ── ĐỊNH NGHĨA BẢNG MÀU MATERIAL GỌN ĐẸP ──────────────────────────────────
C_TITLE_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0284c7;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;arcSize=10;"
C_TITLE_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#16a34a;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;arcSize=10;"
C_TITLE_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#7c3aed;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;arcSize=10;"
C_TITLE_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d97706;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;arcSize=10;"
C_TITLE_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e11d48;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;arcSize=10;"

C_SKY   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2fe;strokeColor=#0284c7;strokeWidth=1.5;fontColor=#0369a1;fontSize=11;arcSize=8;"
C_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#15803d;fontSize=11;arcSize=8;"
C_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#6366f1;strokeWidth=1.5;fontColor=#4338ca;fontSize=11;arcSize=8;"
C_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#d97706;strokeWidth=1.5;fontColor=#b45309;fontSize=11;arcSize=8;"
C_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe4e6;strokeColor=#e11d48;strokeWidth=1.5;fontColor=#be123c;fontSize=11;arcSize=8;"
C_SLATE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;strokeWidth=1.5;fontColor=#334155;fontSize=11;arcSize=8;"

C_CONTAINER_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#bae6fd;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=11;fontColor=#0369a1;arcSize=6;"
C_CONTAINER_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#bbf7d0;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=11;fontColor=#15803d;arcSize=6;"
C_CONTAINER_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#faf5ff;strokeColor=#e9d5ff;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=11;fontColor=#6b21a8;arcSize=6;"
C_CONTAINER_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#fde68a;strokeWidth=1.5;verticalAlign=top;fontStyle=1;fontSize=11;fontColor=#92400e;arcSize=6;"


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 1: KIẾN TRÚC PHÂN TẦNG IOT (4 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig01():
    d = DrawioBuilder("01_kien_truc_iot_4_lop", 1000, 540)
    d.add_title("KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT (4 LỚP)", x=50, y=20, w=900, h=40)

    # 4 lớp xếp tầng
    c1 = d.add_box("LỚP CẢM NHẬN (PERCEPTION LAYER)", 60, 80, 880, 85, C_CONTAINER_GREEN)
    d.add_box("Cảm biến Môi trường\n(Nhiệt độ, Độ ẩm)", 80, 110, 260, 42, C_GREEN)
    d.add_box("ESP32 MCU\n(240 MHz, Dual-Core)", 370, 110, 260, 42, C_GREEN)
    d.add_box("Transceiver LoRa SX1278\n(433 MHz, Ra-02)", 660, 110, 260, 42, C_GREEN)

    c2 = d.add_box("LỚP MẠNG TRUYỀN DẪN (NETWORK LAYER)", 60, 185, 880, 85, C_CONTAINER_BLUE)
    d.add_box("Sóng LoRa CSS\n(433 MHz, BW 125 kHz)", 80, 215, 260, 42, C_SKY)
    d.add_box("Gateway Đa Kênh\n(Raspberry Pi CM4 + 3x SX1278)", 370, 215, 260, 42, C_SKY)
    d.add_box("Mạng IP / Viễn thông\n(Ethernet / Wi-Fi / LTE)", 660, 215, 260, 42, C_SKY)

    c3 = d.add_box("LỚP TRUNG GIAN & ĐIỆN TOÁN (MIDDLEWARE LAYER)", 60, 290, 880, 85, C_CONTAINER_PURP)
    d.add_box("Network Server (NS)\n(Điều phối MAC, Lọc trùng)", 80, 320, 260, 42, C_PURP)
    d.add_box("Message Broker\n(MQTT / REST API)", 370, 320, 260, 42, C_PURP)
    d.add_box("CSDL Chuỗi Thời Gian\n(Time-Series Database)", 660, 320, 260, 42, C_PURP)

    c4 = d.add_box("LỚP ỨNG DỤNG (APPLICATION LAYER)", 60, 395, 880, 85, C_CONTAINER_AMBER)
    d.add_box("Smart City & Hạ Tầng\n(Giám sát tự động)", 80, 425, 260, 42, C_AMBER)
    d.add_box("Web Dashboard\n(Giám sát thời gian thực)", 370, 425, 260, 42, C_AMBER)
    d.add_box("Logistics & Nông Nghiệp\n(Theo dõi tài sản)", 660, 425, 260, 42, C_AMBER)

    # Arrows
    d.add_edge(c1, c2, "LoRa CSS RF")
    d.add_edge(c2, c3, "TCP/IP Socket")
    d.add_edge(c3, c4, "REST API / WebSockets")

    d.save("01_kien_truc_iot_4_lop.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2: NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS
# ══════════════════════════════════════════════════════════════════════════
def build_fig02():
    d = DrawioBuilder("02_nguyen_ly_dieu_che_lora_css", 1000, 460)
    d.add_title("NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS", x=50, y=20, w=900, h=40)

    b1 = d.add_box("Dữ liệu Nhị phân\n(Bitstream 1 0 1 1 0...)", 60, 85, 150, 65, C_SLATE)
    b2 = d.add_box("Mã hóa Symbol\n(k ∈ [0, 2^SF - 1])", 240, 85, 150, 65, C_SKY)
    b3 = d.add_box("Bộ tạo Chirp CSS\n(Quét tần số tuyến tính)", 420, 85, 180, 65, C_GREEN)
    b4 = d.add_box("Khuếch đại PA_BOOST\n(+17 dBm)", 630, 85, 160, 65, C_AMBER)
    b5 = d.add_box("Anten 433 MHz\n(Sóng điện từ)", 820, 85, 120, 65, C_ROSE)

    d.add_edge(b1, b2, "Nhóm SF bits")
    d.add_edge(b2, b3, "Ký hiệu k")
    d.add_edge(b3, b4, "Chirp Signal")
    d.add_edge(b4, b5, "RF Power")

    # Spectrogram Box
    d.add_box("ĐẶC TÍNH DẠNG SÓNG CHIRP THEO THỜI GIAN (SPECTROGRAM)", 60, 185, 880, 230, C_CONTAINER_BLUE)
    d.add_box("Tần số (f)\n\nf_0 + BW/2\n\nf_0 (433.x MHz)\n\nf_0 - BW/2", 80, 225, 140, 175, C_SLATE)
    d.add_box("CHIRP CƠ SỞ (UP-CHIRP)\n\n• Quét tần số tuyến tính từ f_min đến f_max\n• Chu kỳ: Ts = 2^SF / BW (1.024 ms với SF7)\n• Đồng bộ khung & Báo hiệu đường truyền", 240, 225, 330, 175, C_GREEN)
    d.add_box("CHIRP ĐIỀU CHẾ (MODULATED CHIRP)\n\n• Bước nhảy tần tức thời mang giá trị bit\n• Khả năng giải điều chế dưới nhiễu nền\n• Ngưỡng SNR giải mã: -7.5 dB đến -20 dB", 590, 225, 330, 175, C_SKY)

    d.save("02_nguyen_ly_dieu_che_lora_css.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3: KIẾN TRÚC MẠNG LORAWAN HÌNH SAO
# ══════════════════════════════════════════════════════════════════════════
def build_fig03():
    d = DrawioBuilder("03_kien_truc_mang_lorawan_star", 1000, 520)
    d.add_title("KIẾN TRÚC MẠNG LORAWAN HÌNH SAO (STAR-OF-STARS)", x=50, y=20, w=900, h=40)

    # 3 Cột
    d.add_box("THIẾT BỊ ĐẦU CUỐI (END-NODES)", 50, 80, 220, 410, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + Ra-02 + OLED", 70, 125, 180, 85, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + Ra-02 + OLED", 70, 235, 180, 85, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + Ra-02 + OLED", 70, 345, 180, 85, C_GREEN)

    d.add_box("MULTI-CHANNEL GATEWAY", 320, 80, 320, 410, C_CONTAINER_BLUE)
    gw = d.add_box("RASPBERRY PI CM4 GATEWAY\n(Broadcom BCM2711 @ 1.5 GHz)\n\n3x Semtech SX1278 (SPI0 Bus):\n• CH1: 433.175 MHz\n• CH2: 433.375 MHz\n• CH3: 433.575 MHz\n\nKiến trúc Zero-Blindness", 340, 140, 280, 250, C_SKY)

    d.add_box("QUẢN TRỊ & ỨNG DỤNG", 690, 80, 260, 410, C_CONTAINER_PURP)
    ns = d.add_box("Network Server (NS)\n• Khử trùng lặp bản tin\n• Kiểm tra tính toàn vẹn MIC", 710, 135, 220, 105, C_PURP)
    as_srv = d.add_box("Application Server & Web\n• Giải mã Payload dữ liệu\n• CSDL CSV & Web Dashboard", 710, 275, 220, 105, C_AMBER)

    # Connections
    d.add_edge(na, gw, "LoRa RF (433.x MHz)")
    d.add_edge(nb, gw, "LoRa RF (433.x MHz)")
    d.add_edge(nc, gw, "LoRa RF (433.x MHz)")
    d.add_edge(gw, ns, "TCP/IP Socket")
    d.add_edge(ns, as_srv, "JSON Data")

    d.save("03_kien_truc_mang_lorawan_star.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4: SO SÁNH CLOUD AI VÀ EDGE TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig04():
    d = DrawioBuilder("04_so_sanh_cloud_ai_vs_edge_tinyml", 1000, 480)
    d.add_title("SO SÁNH CLOUD AI TRUYỀN THỐNG VÀ EDGE TINYML BIÊN", x=50, y=20, w=900, h=40)

    # Top: Cloud AI
    d.add_box("1. MÔ HÌNH TRUYỀN THỐNG: CLOUD AI TẬP TRUNG", 50, 80, 900, 160, C_CONTAINER_AMBER)
    c1 = d.add_box("Node Cảm biến", 70, 120, 160, 50, C_SLATE)
    c2 = d.add_box("Gateway Chuyển tiếp", 290, 120, 160, 50, C_SLATE)
    c3 = d.add_box("Cloud Server AI", 510, 120, 160, 50, C_AMBER)
    c4 = d.add_box("Lệnh Downlink RF", 730, 120, 190, 50, C_ROSE)

    d.add_edge(c1, c2, "Uplink RF")
    d.add_edge(c2, c3, "Internet / LTE")
    d.add_edge(c3, c4, "Điện toán mây")
    d.add_edge(c4, c1, "Downlink trễ cao", "edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e11d48;dashed=1;")
    d.add_box("Hạn chế: Độ trễ cao (> 2-5s) | Tốn pin mở cửa sổ thu RX | Phụ thuộc Internet", 70, 185, 850, 35, C_ROSE)

    # Bottom: Edge TinyML
    d.add_box("2. MÔ HÌNH HIỆN ĐẠI: EDGE TINYML TRÊN THIẾT BỊ BIÊN", 50, 260, 900, 180, C_CONTAINER_GREEN)
    e1 = d.add_box("Cảm biến / CSI\n(Cửa sổ trượt 10x9)", 70, 300, 180, 55, C_GREEN)
    e2 = d.add_box("Mô hình TinyML (ESP32)\nFlash: 8.65 KB | RAM: 10 KB", 300, 300, 220, 55, C_GREEN)
    e3 = d.add_box("Quyết định tại chỗ\nTrễ suy luận: 9.3 ms", 570, 300, 180, 55, C_GREEN)
    e4 = d.add_box("Phát sóng Kênh sạch\nPDR: 95% - 100%", 800, 300, 160, 55, C_SKY)

    d.add_edge(e1, e2, "Dữ liệu 10x9")
    d.add_edge(e2, e3, "Softmax")
    d.add_edge(e3, e4, "Chuyển kênh RF")
    d.add_box("Ưu thế: Tự chủ 100% (Offline) | Trễ cực thấp (< 10 ms) | Không tốn Downlink | Tiết kiệm năng lượng", 70, 375, 890, 35, C_GREEN)

    d.save("04_so_sanh_cloud_ai_vs_edge_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 5: BÀI TOÁN LỰA CHỌN KÊNH TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig05():
    d = DrawioBuilder("05_bai_toan_lua_chon_kenh_tinyml", 1000, 460)
    d.add_title("CƠ CHẾ DỰ ĐOÁN VÀ NHẢY KÊNH THÍCH ỨNG TINYML", x=50, y=20, w=900, h=40)

    # Top pipeline
    b1 = d.add_box("Cửa sổ trượt FIFO (10x9)\n10 bước x 9 đặc trưng CSI\n(RSSI, SNR, Payload, Freq)", 60, 80, 200, 95, C_CONTAINER_BLUE)
    b2 = d.add_box("Chuẩn hóa Z-Score\nz = (x - μ) / σ\nBảng SCALER tĩnh O(1)", 290, 80, 180, 95, C_SKY)
    b3 = d.add_box("Mô hình Separable 1D-CNN\n878 params | 10 KB RAM\nThời gian suy luận: 9.3 ms", 500, 80, 220, 95, C_CONTAINER_GREEN)
    b4 = d.add_box("Xác suất Softmax\n[P(CH0), P(CH1), P(CH2)]\nPhân loại kênh sạch", 750, 80, 190, 95, C_PURP)

    d.add_edge(b1, b2, "Ma trận 10x9")
    d.add_edge(b2, b3, "Vector (90)")
    d.add_edge(b3, b4, "Logits")

    # Bottom execution
    b5 = d.add_box("Quyết định ArgMax\nk_opt = argmax(P0, P1, P2)", 450, 220, 280, 50, C_AMBER)
    b6 = d.add_box("Chuyển tần số SX1278\nradio.setFrequency(f_opt)", 450, 300, 280, 50, C_ROSE)
    b7 = d.add_box("Phát gói tin LoRa\nCông suất: +17 dBm | PDR ≥ 95%", 450, 380, 280, 50, C_GREEN)

    d.add_edge(b4, b5, "Chỉ số xác suất", "edgeStyle=orthogonalEdgeStyle;rounded=1;")
    d.add_edge(b5, b6, "Kênh tối ưu (0, 1, 2)")
    d.add_edge(b6, b7, "Kích hoạt phát RF")

    d.save("05_bai_toan_lua_chon_kenh_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 6: SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig06():
    d = DrawioBuilder("06_so_do_khoi_toan_he_thong", 1050, 550)
    d.add_title("SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM LORA TINYML", x=50, y=20, w=950, h=40)

    # 3 Khối
    d.add_box("PHÂN HỆ TRẠM PHÁT (03 END-NODES)", 50, 80, 280, 440, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + SX1278 + OLED", 70, 120, 240, 85, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + SX1278 + OLED", 70, 230, 240, 85, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + SX1278 + OLED", 70, 340, 240, 85, C_GREEN)

    d.add_box("MÔI TRƯỜNG VÔ TUYẾN 433 MHz", 370, 80, 260, 440, C_CONTAINER_AMBER)
    ch1 = d.add_box("Kênh 1: 433.175 MHz (BW 125 kHz)", 390, 130, 220, 65, C_AMBER)
    ch2 = d.add_box("Kênh 2: 433.375 MHz (BW 125 kHz)", 390, 220, 220, 65, C_AMBER)
    ch3 = d.add_box("Kênh 3: 433.575 MHz (BW 125 kHz)", 390, 310, 220, 65, C_AMBER)
    d.add_box("Khoảng cách bảo vệ: 200 kHz", 390, 410, 220, 40, C_SLATE)

    d.add_box("PHÂN HỆ TRẠM THU (GATEWAY CM4)", 670, 80, 330, 440, C_CONTAINER_BLUE)
    rx_mod = d.add_box("3x Module SX1278 (SPI0 Bus)\nThu đồng thời 3 kênh (Zero-Blindness)", 690, 120, 290, 70, C_SKY)
    d.add_box("Raspberry Pi CM4 (Quad-Core)\n3 Luồng Worker xử lý ngắt DIO0", 690, 210, 290, 70, C_SKY)
    d.add_box("CSDL & Ghi Log CSV\nLưu trữ Timestamp, RSSI, SNR, PDR", 690, 300, 290, 70, C_PURP)
    d.add_box("Router-Style Web Dashboard\nGiám sát hệ thống thời gian thực", 690, 390, 290, 70, C_AMBER)

    # Connections
    d.add_edge(na, ch1, "RF 433.x MHz")
    d.add_edge(nb, ch2, "RF 433.x MHz")
    d.add_edge(nc, ch3, "RF 433.x MHz")
    d.add_edge(ch1, rx_mod, "Thu đồng thời")
    d.add_edge(ch2, rx_mod, "Thu đồng thời")
    d.add_edge(ch3, rx_mod, "Thu đồng thời")

    d.save("06_so_do_khoi_toan_he_thong.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 7: ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA
# ══════════════════════════════════════════════════════════════════════════
def build_fig07():
    d = DrawioBuilder("07_dinh_dang_khung_truyen_goi_tin", 1000, 340)
    d.add_title("CẤU TRÚC ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA", x=50, y=20, w=900, h=40)

    # Category Headers
    d.add_box("HEADER (4 Bytes)", 60, 80, 340, 35, C_TITLE_BLUE)
    d.add_box("METADATA (5 Bytes)", 420, 80, 210, 35, C_TITLE_PURP)
    d.add_box("PAYLOAD (Biến thiên)", 650, 80, 200, 35, C_TITLE_AMBER)
    d.add_box("CRC (2 Bytes)", 870, 80, 90, 35, C_TITLE_ROSE)

    # Fields
    d.add_box("Node_ID\n(1 Byte)\n'A', 'B', 'C'", 60, 125, 100, 75, C_SKY)
    d.add_box("Packet_ID\n(2 Bytes)\n0 - 65,535", 170, 125, 110, 75, C_SKY)
    d.add_box("Current_CH\n(1 Byte)\n0, 1, 2", 290, 125, 110, 75, C_SKY)
    d.add_box("Payload_Size\n(1 Byte)\n30 - 250 B", 420, 125, 100, 75, C_PURP)
    d.add_box("Timestamp\n(4 Bytes)\nmillis()", 530, 125, 100, 75, C_PURP)
    d.add_box("Payload Data\n(21 - 241 Bytes)\nBuffer mở rộng", 650, 125, 200, 75, C_AMBER)
    d.add_box("CRC\n(2 Bytes)\nHardware", 870, 125, 90, 75, C_ROSE)

    # Sub-banners
    d.add_box("Dải Tải Trọng Quét Thực Nghiệm: 30B, 74B, 118B, 162B, 206B, 250B", 60, 220, 900, 35, C_CONTAINER_GREEN)
    d.add_box("Gateway Logger: Bóc tách gói tin + Đọc thanh ghi phần cứng SX1278 (RSSI, SNR) -> Ghi log CSV", 60, 265, 900, 35, C_SLATE)

    d.save("07_dinh_dang_khung_truyen_goi_tin.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 8: 5 KIẾN TRÚC MẠNG NƠ-RON TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig08():
    d = DrawioBuilder("08_5_kien_truc_tinyml", 1080, 520)
    d.add_title("ĐỐI SÁNH 5 KIẾN TRÚC MẠNG NƠ-RON TINYML", x=40, y=20, w=1000, h=40)

    w_card = 185
    gap = 18
    start_x = 42

    # Card 1: FCNN
    x1 = start_x
    d.add_box("1. BASELINE FCNN", x1, 80, w_card, 40, C_TITLE_BLUE)
    d.add_box("• Input Flat (90D)\n• Dense (16, ReLU)\n• Dropout (0.15)\n• Dense (12, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,699\nFlash: 8.84 KB\nLatency: 5.5 ms\nAccuracy: 90.41%", x1, 130, w_card, 320, C_SKY)

    # Card 2: 1D-CNN
    x2 = x1 + w_card + gap
    d.add_box("2. 1D-CNN", x2, 80, w_card, 40, C_TITLE_PURP)
    d.add_box("• Input Seq (10, 9)\n• Conv1D (16, k=3)\n• BatchNorm + Pool\n• Conv1D (32, k=3)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,659\nFlash: 16.34 KB\nLatency: 12.7 ms\nAccuracy: 90.30%", x2, 130, w_card, 320, C_PURP)

    # Card 3: GRU
    x3 = x2 + w_card + gap
    d.add_box("3. GRU RNN", x3, 80, w_card, 40, C_TITLE_AMBER)
    d.add_box("• Input Seq (10, 9)\n• GRU (16, unroll)\n• Dropout (0.15)\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,619\nFlash: 42.32 KB\nLatency: 68.5 ms\nAccuracy: 90.12%", x3, 130, w_card, 320, C_AMBER)

    # Card 4: Separable 1D-CNN (TỐI ƯU NHẤT)
    x4 = x3 + w_card + gap
    d.add_box("4. SEPARABLE 1D-CNN", x4, 80, w_card, 40, C_TITLE_GREEN)
    d.add_box("★ TỐI ƯU NHẤT ★\n• Input Seq (10, 9)\n• SepConv1D (16, k=3)\n• SepConv1D (32, k=3)\n• GlobalAvgPool1D\n• Dropout (0.15)\n• Dense (3, Softmax)\n\nTham số: 878 (Nhỏ nhất)\nFlash: 8.65 KB\nLatency: 10.6 ms\nAccuracy: 90.51%", x4, 130, w_card, 320, C_GREEN)

    # Card 5: ResNet-1D
    x5 = x4 + w_card + gap
    d.add_box("5. RESNET-1D", x5, 80, w_card, 40, C_TITLE_ROSE)
    d.add_box("• Input Seq (10, 9)\n• Conv1D (16, k=3)\n• Residual Block\n  Skip Connection (+x)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,339\nFlash: 14.73 KB\nLatency: 16.3 ms\nAccuracy: 90.30%", x5, 130, w_card, 320, C_ROSE)

    d.add_box("LỰA CHỌN TỐI ƯU CHO ESP32: Separable 1D-CNN đạt hiệu năng cao nhất (90.51% Acc), tham số ít nhất (878 params) và tiết kiệm 63% phép toán FLOPs.", 40, 465, 1000, 35, C_CONTAINER_GREEN)

    d.save("08_5_kien_truc_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 9: QUY TRÌNH XỬ LÝ DỮ LIỆU THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig09():
    d = DrawioBuilder("09_pipeline_xu_ly_du_lieu", 1000, 440)
    d.add_title("QUY TRÌNH XỬ LÝ & CHUẨN HÓA DỮ LIỆU THỰC NGHIỆM", x=50, y=20, w=900, h=40)

    p1 = d.add_box("Bước 1: Trích Xuất Log\n• 21,600 gói tin Gateway\n• Tách theo Node (A, B, C)\n• Lọc bỏ bản tin lỗi CRC", 60, 80, 200, 85, C_CONTAINER_BLUE)
    p2 = d.add_box("Bước 2: Bù Đắp Gói Mất\n• Quét Packet_ID liên tục\n• Phát hiện gói mất (Δ > 1)\n• Phạt RSSI=-120, SNR=-15", 290, 80, 200, 85, C_CONTAINER_PURP)
    p3 = d.add_box("Bước 3: Cửa Sổ Trượt\n• Tạo tensor (10 bước x 9)\n• Gán nhãn kênh kế tiếp\n• Khử rò rỉ nhãn mục tiêu", 520, 80, 200, 85, C_CONTAINER_AMBER)
    p4 = d.add_box("Bước 4: Chuẩn Hóa & Split\n• StandardScaler Z-Score\n• Xuất bảng SCALER tĩnh\n• 60% Train / 20% Val / 20% Test", 750, 80, 200, 85, C_CONTAINER_GREEN)

    d.add_edge(p1, p2, "Dữ liệu thô")
    d.add_edge(p2, p3, "Dữ liệu liên tục")
    d.add_edge(p3, p4, "Chuỗi trượt")

    # Outputs
    d.add_box("ĐẦU RA QUY TRÌNH DỮ LIỆU (DATASET & FIRMWARE ASSETS)", 60, 195, 890, 160, C_CONTAINER_GREEN)
    d.add_box("dataset_ready.csv\n19,440 mẫu chuỗi thời gian\n90 đặc trưng | Cân bằng 3 nhãn", 80, 230, 260, 65, C_GREEN)
    d.add_box("Phân Chia Mẫu\nTrain: 11,664 (60%)\nVal: 3,888 (20%) | Test: 3,888 (20%)", 370, 230, 260, 65, C_SKY)
    d.add_box("Hệ Số SCALER Nhúng C\nSCALER_MEAN[9] & SCALER_SCALE[9]\nĐồng bộ trong model.h", 660, 230, 260, 65, C_AMBER)

    d.add_box("BẢO ĐẢM KHOA HỌC: Không rò rỉ nhãn (No Leakage) | Cân bằng dữ liệu 3 kênh | Chuẩn hóa O(1) trên ESP32", 80, 310, 840, 35, C_SLATE)

    d.save("09_pipeline_xu_ly_du_lieu.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 10: SƠ ĐỒ BỐ TRÍ THỰC ĐỊA TRONG TÒA NHÀ
# ══════════════════════════════════════════════════════════════════════════
def build_fig10():
    d = DrawioBuilder("10_bo_tri_thuc_dia_toa_nha", 1000, 480)
    d.add_title("SƠ ĐỒ BỐ TRÍ THỰC NGHIỆM TRONG TÒA NHÀ ĐẠI HỌC", x=50, y=20, w=900, h=40)

    # Indoor Container
    d.add_box("KHÔNG GIAN TRONG NHÀ (INDOOR)", 60, 80, 580, 370, C_CONTAINER_BLUE)
    d.add_box("TẦNG 2: PHÒNG THÍ NGHIỆM & HÀNH LANG", 80, 115, 540, 140, C_SLATE)
    gw = d.add_box("MULTI-CHANNEL GATEWAY\nRaspberry Pi CM4 + 3x SX1278\nVị trí trung tâm trên cao", 100, 145, 230, 90, C_SKY)
    nb = d.add_box("NODE B (TẦNG 2)\n60m | NLOS (Xuyên 2 sàn bê tông)", 370, 145, 230, 90, C_AMBER)

    d.add_box("TẦNG 1: SẢNH VÀ PHÒNG HỌC", 80, 275, 540, 155, C_SLATE)
    na = d.add_box("NODE A (TẦNG 1)\n25m | LOS / NLOS nhẹ (Xuyên vách kính)", 100, 310, 250, 95, C_GREEN)

    # Outdoor Container
    d.add_box("NGOÀI TRỜI (OUTDOOR)", 670, 80, 270, 370, C_CONTAINER_GREEN)
    nc = d.add_box("NODE C (SÂN TRƯỜNG)\n110m | Tán cây & Tường bao\nSuy hao truyền sóng cao nhất", 690, 190, 230, 120, C_ROSE)

    # Wireless links
    d.add_edge(na, gw, "25m (LOS/NLOS nhẹ)", "strokeColor=#16a34a;strokeWidth=2;")
    d.add_edge(nb, gw, "60m (NLOS)", "strokeColor=#d97706;strokeWidth=2;")
    d.add_edge(nc, gw, "110m (Fading)", "strokeColor=#e11d48;strokeWidth=2;")

    d.save("10_bo_tri_thuc_dia_toa_nha.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 11: KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS
# ══════════════════════════════════════════════════════════════════════════
def build_fig11():
    d = DrawioBuilder("11_kien_truc_freertos_da_nhiem", 1000, 480)
    d.add_title("KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS TRÊN ESP32", x=50, y=20, w=900, h=40)

    # Core 0
    d.add_box("CORE 0: CẢM BIẾN & HIỂN THỊ HMI", 60, 80, 420, 370, C_CONTAINER_BLUE)
    t_samp = d.add_box("Task_Sampler (Prio 1)\nĐọc cảm biến -> Cập nhật bộ đệm FIFO (10x9)", 80, 125, 380, 75, C_SKY)
    d.add_box("Task_OLED (Prio 1)\nQuét I2C 10 Hz -> Hiển thị PDR, RSSI, SNR", 80, 225, 380, 75, C_SKY)
    mutex = d.add_box("historyMutex\nBảo vệ an toàn mảng FIFO 10x9", 80, 335, 380, 65, C_AMBER)

    # Core 1
    d.add_box("CORE 1: SUY LUẬN AI & TRUYỀN THÔNG RF", 520, 80, 420, 370, C_CONTAINER_GREEN)
    t_ml = d.add_box("Task_TinyML (Prio 2)\nZ-Score -> Suy luận TFLM (< 10 ms) -> ArgMax", 540, 125, 380, 75, C_GREEN)
    t_tx = d.add_box("Task_LoRaTX (Prio 3 - Cao nhất)\nCài đặt tần số -> Phát sóng RF (+17 dBm)", 540, 225, 380, 75, C_GREEN)
    queue = d.add_box("channelQueue (Độ dài 1)\nChuyển giao kênh tối ưu sang Task TX", 540, 335, 380, 65, C_PURP)

    d.add_edge(t_samp, mutex, "Ghi dữ liệu")
    d.add_edge(mutex, t_ml, "Đọc an toàn")
    d.add_edge(t_ml, queue, "xQueueOverwrite(k_opt)")
    d.add_edge(queue, t_tx, "xQueueReceive(k_opt)")

    d.save("11_kien_truc_freertos_da_nhiem.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 12: SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32
# ══════════════════════════════════════════════════════════════════════════
def build_fig12():
    d = DrawioBuilder("12_so_do_noi_chan_end_node_esp32", 1000, 480)
    d.add_title("SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32", x=50, y=20, w=900, h=40)

    # ESP32 center
    mcu = d.add_box("ESP32 DEVKIT V1\nDual-Core 240 MHz | SRAM 520 KB | Flash 4 MB", 360, 80, 280, 290, C_CONTAINER_BLUE)

    # Left: SX1278
    rf = d.add_box("MODULE LORA SX1278 (RA-02)\n• MOSI: GPIO 27\n• MISO: GPIO 19\n• SCK:  GPIO 18\n• NSS:  GPIO 5 (CS)\n• RST:  GPIO 14\n• DIO0: GPIO 26 (TxDone)\n• Nguồn: 3.3V + GND", 60, 80, 260, 290, C_CONTAINER_GREEN)

    # Right: OLED
    oled = d.add_box("MÀN HÌNH OLED SSD1306\n• SDA: GPIO 21\n• SCL: GPIO 22\n• Nguồn: 3.3V + GND\n\nGiao tiếp I2C Fast Mode (400 kHz)", 680, 80, 260, 290, C_CONTAINER_PURP)

    # Bottom: Power circuit
    pwr = d.add_box("MẠCH NGUỒN VÀ TỤ BÙ CHỐNG SỤT ÁP (100 µF + 100 nF)\nTriệt tiêu dòng đỉnh 130 mA khi phát sóng LoRa, chống Brownout Reset ESP32", 160, 400, 680, 55, C_AMBER)

    d.add_edge(rf, mcu, "Bus VSPI & DIO0")
    d.add_edge(mcu, oled, "Bus I2C")
    d.add_edge(pwr, mcu, "3.3V DC")

    d.save("12_so_do_noi_chan_end_node_esp32.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 13: SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY CM4
# ══════════════════════════════════════════════════════════════════════════
def build_fig13():
    d = DrawioBuilder("13_so_do_noi_chan_gateway_cm4", 1000, 520)
    d.add_title("SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY RASPBERRY PI CM4", x=50, y=20, w=900, h=40)

    # 3 Receiver modules on left
    m1 = d.add_box("MODULE THU #1 (CH1 - 433.175 MHz)\nCE: GPIO 8 (CE0) | DIO0: GPIO 24", 60, 80, 260, 95, C_SKY)
    m2 = d.add_box("MODULE THU #2 (CH2 - 433.375 MHz)\nCE: GPIO 7 (CE1) | DIO0: GPIO 23", 60, 200, 260, 95, C_GREEN)
    m3 = d.add_box("MODULE THU #3 (CH3 - 433.575 MHz)\nCE: GPIO 25 (CS2) | DIO0: GPIO 22", 60, 320, 260, 95, C_AMBER)
    d.add_box("Bus SPI0 Chung: MOSI=Pin 19, MISO=Pin 21, SCLK=Pin 23", 60, 435, 260, 45, C_SLATE)

    # CM4 center
    cm4 = d.add_box("RASPBERRY PI CM4\nQuad-Core Cortex-A72 @ 1.5 GHz\n40-Pin GPIO Header | Linux OS", 360, 80, 280, 400, C_CONTAINER_BLUE)

    # Software services on right
    d.add_box("PHẦN MỀM ĐIỀU HÀNH GATEWAY", 680, 80, 260, 400, C_CONTAINER_PURP)
    d.add_box("3 Luồng Worker (Zero-Blindness)\nThu song song 100% 3 kênh", 700, 125, 220, 85, C_PURP)
    d.add_box("CSDL & Ghi Log CSV\nLưu trữ Timestamp, RSSI, SNR, PDR", 700, 235, 220, 85, C_SLATE)
    d.add_box("Nginx & REST API Dashboard\nGiám sát hệ thống thời gian thực", 700, 345, 220, 85, C_AMBER)

    d.add_edge(m1, cm4, "SPI0 CE0")
    d.add_edge(m2, cm4, "SPI0 CE1")
    d.add_edge(m3, cm4, "SPI0 CS2")

    d.save("13_so_do_noi_chan_gateway_cm4.drawio")
    return d


def build_full_project_diagram(builders):
    """Gộp toàn bộ 13 sơ đồ thành một tệp drawio đa trang duy nhất"""
    diag_xmls = []
    for b in builders:
        diag_xmls.append(b.to_diagram_xml(f"page_{b.title}", b.title))

    full_xml = f"""<mxfile host="app.diagrams.net" agent="Antigravity" version="21.0.0" type="device">
{"\n".join(diag_xmls)}
</mxfile>"""

    path1 = os.path.join(DOCS_FIGS_DIR, "full_project_diagrams.drawio")
    path2 = os.path.join(ROOT_FIGS_DIR, "full_project_diagrams.drawio")
    with open(path1, "w", encoding="utf-8") as f:
        f.write(full_xml)
    with open(path2, "w", encoding="utf-8") as f:
        f.write(full_xml)
    print("  [OK] Saved: full_project_diagrams.drawio (Multi-page)")


def validate_all_diagrams():
    """Kiểm tra cú pháp XML của toàn bộ tệp .drawio sinh ra"""
    print("\n[*] Đang kiểm tra tính hợp lệ cú pháp XML...")
    all_valid = True
    for fname in os.listdir(DOCS_FIGS_DIR):
        if fname.endswith(".drawio"):
            fpath = os.path.join(DOCS_FIGS_DIR, fname)
            try:
                tree = ET.parse(fpath)
                root = tree.getroot()
                if root.tag != "mxfile":
                    print(f"  [ERROR] {fname}: Thẻ gốc không phải mxfile!")
                    all_valid = False
                else:
                    pages = root.findall("diagram")
                    print(f"  ✓ {fname}: Hợp lệ ({len(pages)} trang)")
            except Exception as e:
                print(f"  [ERROR] {fname}: Lỗi XML: {e}")
                all_valid = False
    return all_valid


def main():
    print("=" * 72)
    print(" KHỞI TẠO TỰ ĐỘNG BỘ SƠ ĐỒ ĐỒ HỌA (.DRAWIO) CHO TOÀN BỘ ĐỒ ÁN")
    print("=" * 72)

    builders = [
        build_fig01(),
        build_fig02(),
        build_fig03(),
        build_fig04(),
        build_fig05(),
        build_fig06(),
        build_fig07(),
        build_fig08(),
        build_fig09(),
        build_fig10(),
        build_fig11(),
        build_fig12(),
        build_fig13(),
    ]

    build_full_project_diagram(builders)

    success = validate_all_diagrams()
    if success:
        print("\n[THÀNH CÔNG] Toàn bộ 13 tệp sơ đồ .drawio và tệp master đã sẵn sàng!")
    else:
        print("\n[CẢNH BÁO] Có tệp XML bị lỗi, vui lòng kiểm tra lại.")


if __name__ == "__main__":
    main()
