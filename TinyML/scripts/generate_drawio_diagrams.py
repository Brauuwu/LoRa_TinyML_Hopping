#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_drawio_diagrams.py
Tạo tự động 13 tệp sơ đồ đồ họa định dạng .drawio (XML) chất lượng cao cho đồ án:
Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML.

Đặc tính thiết kế nâng cấp:
- Cỡ chữ lớn, chuẩn hóa theo yêu cầu: 24px - 30px (Tiêu đề 32px, Container 26px, Hộp nội dung 24px, Mũi tên 22px).
- Bố cục thông thoáng, khoảng cách giữa các ô/khối (gaps/margins) giãn cách rộng rãi (80px - 150px).
- Khung canvas mở rộng tương xứng (2100px - 2250px) để các khoảng cách thoáng đãng, tuyệt đối không chen chúc.
- Mũi tên định tuyến vuông góc (orthogonal), khoảng cách thoáng đãng, triệt tiêu giao cắt rối mắt.
- Chú thích cực kỳ súc tích: Chỉ nêu linh kiện, giao thức, kích thước dữ liệu; không có câu văn dài dòng hay đánh giá kết quả chủ quan.
"""

import os
import xml.etree.ElementTree as ET

DOCS_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/docs/figs")
ROOT_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/figs")
os.makedirs(DOCS_FIGS_DIR, exist_ok=True)
os.makedirs(ROOT_FIGS_DIR, exist_ok=True)


class DrawioBuilder:
    def __init__(self, title="Diagram", width=2100, height=1200):
        self.title = title
        self.width = width
        self.height = height
        self.cells = []
        self.cell_id = 2

        # Root elements
        self.cells.append('<mxCell id="0" />')
        self.cells.append('<mxCell id="1" parent="0" />')

    def add_title(self, text, x=60, y=25, w=None, h=65):
        if w is None:
            w = self.width - 2 * x
        style = (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;strokeColor=none;"
            "fontColor=#ffffff;fontStyle=1;fontSize=32;shadow=1;arcSize=10;fontFamily=Helvetica;"
        )
        self.add_box(text, x, y, w, h, style)

    def add_box(self, label, x, y, w, h, style=None):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
                "strokeWidth=2;fontColor=#1e293b;fontSize=24;fontFamily=Helvetica;"
            )
        escaped_label = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "&#xa;")
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
                "html=1;strokeColor=#334155;strokeWidth=2.5;endArrow=block;endFill=1;"
                "fontColor=#0f172a;fontSize=22;fontStyle=1;fontFamily=Helvetica;"
            )
        escaped_label = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "&#xa;")
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


# ── ĐỊNH NGHĨA PHONG CÁCH MATERIAL DESIGN CHUẨN (CỠ CHỮ 24PX - 30PX) ─────────
C_TITLE_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0284c7;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=28;arcSize=10;fontFamily=Helvetica;"
C_TITLE_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#16a34a;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=28;arcSize=10;fontFamily=Helvetica;"
C_TITLE_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#7c3aed;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=28;arcSize=10;fontFamily=Helvetica;"
C_TITLE_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d97706;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=28;arcSize=10;fontFamily=Helvetica;"
C_TITLE_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e11d48;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=28;arcSize=10;fontFamily=Helvetica;"

C_SKY   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#0284c7;strokeWidth=2;fontColor=#0369a1;fontSize=24;arcSize=8;fontFamily=Helvetica;"
C_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=2;fontColor=#15803d;fontSize=24;arcSize=8;fontFamily=Helvetica;"
C_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#faf5ff;strokeColor=#7c3aed;strokeWidth=2;fontColor=#5b21b6;fontSize=24;arcSize=8;fontFamily=Helvetica;"
C_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=2;fontColor=#92400e;fontSize=24;arcSize=8;fontFamily=Helvetica;"
C_ROSE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff1f2;strokeColor=#e11d48;strokeWidth=2;fontColor=#9f1239;fontSize=24;arcSize=8;fontFamily=Helvetica;"
C_SLATE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#64748b;strokeWidth=2;fontColor=#1e293b;fontSize=24;arcSize=8;fontFamily=Helvetica;"

C_CONTAINER_BLUE  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#38bdf8;strokeWidth=2;verticalAlign=top;fontStyle=1;fontSize=26;fontColor=#0369a1;arcSize=8;fontFamily=Helvetica;"
C_CONTAINER_GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#4ade80;strokeWidth=2;verticalAlign=top;fontStyle=1;fontSize=26;fontColor=#15803d;arcSize=8;fontFamily=Helvetica;"
C_CONTAINER_PURP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#faf5ff;strokeColor=#c084fc;strokeWidth=2;verticalAlign=top;fontStyle=1;fontSize=26;fontColor=#6b21a8;arcSize=8;fontFamily=Helvetica;"
C_CONTAINER_AMBER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#fcd34d;strokeWidth=2;verticalAlign=top;fontStyle=1;fontSize=26;fontColor=#92400e;arcSize=8;fontFamily=Helvetica;"
C_CONTAINER_SLATE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;strokeWidth=2;verticalAlign=top;fontStyle=1;fontSize=26;fontColor=#334155;arcSize=8;fontFamily=Helvetica;"

STYLE_EDGE_BLACK = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0f172a;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#0f172a;fontSize=22;fontStyle=1;fontFamily=Helvetica;"
STYLE_EDGE_RED   = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#dc2626;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#b91c1c;fontSize=22;fontStyle=1;fontFamily=Helvetica;"
STYLE_EDGE_GREEN = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#15803d;fontSize=22;fontStyle=1;fontFamily=Helvetica;"


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 1: KIẾN TRÚC PHÂN TẦNG IOT (4 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig01():
    d = DrawioBuilder("01_kien_truc_iot_4_lop", 2100, 1350)
    d.add_title("KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT (4 LỚP)")

    # 4 tầng với giãn cách giữa các tầng = 80px, giãn cách các ô trong hàng = 100px
    c1 = d.add_box("LỚP CẢM NHẬN (PERCEPTION LAYER)", 80, 120, 1940, 210, C_CONTAINER_GREEN)
    d.add_box("Cảm biến môi trường", 130, 185, 550, 115, C_GREEN)
    d.add_box("Vi điều khiển ESP32", 780, 185, 550, 115, C_GREEN)
    d.add_box("Transceiver LoRa SX1278 (433 MHz)", 1430, 185, 540, 115, C_GREEN)

    c2 = d.add_box("LỚP MẠNG TRUYỀN DẪN (NETWORK LAYER)", 80, 410, 1940, 210, C_CONTAINER_BLUE)
    d.add_box("Kênh sóng LoRa (433 MHz)", 130, 475, 550, 115, C_SKY)
    d.add_box("Gateway đa kênh (Raspberry Pi CM4)", 780, 475, 550, 115, C_SKY)
    d.add_box("Mạng kết nối IP (Ethernet / Wi-Fi)", 1430, 475, 540, 115, C_SKY)

    c3 = d.add_box("LỚP TRUNG GIAN (MIDDLEWARE LAYER)", 80, 700, 1940, 210, C_CONTAINER_PURP)
    d.add_box("Network Server (Điều phối khung truyền)", 130, 765, 550, 115, C_PURP)
    d.add_box("Message Broker (MQTT / REST API)", 780, 765, 550, 115, C_PURP)
    d.add_box("Cơ sở dữ liệu chuỗi thời gian", 1430, 765, 540, 115, C_PURP)

    c4 = d.add_box("LỚP ỨNG DỤNG (APPLICATION LAYER)", 80, 990, 1940, 210, C_CONTAINER_AMBER)
    d.add_box("Ứng dụng giám sát thông minh", 130, 1055, 550, 115, C_AMBER)
    d.add_box("Web Dashboard thời gian thực", 780, 1055, 550, 115, C_AMBER)
    d.add_box("Hệ thống quản lý dữ liệu đo", 1430, 1055, 540, 115, C_AMBER)

    d.add_edge(c1, c2, "LoRa RF (433 MHz)", STYLE_EDGE_BLACK)
    d.add_edge(c2, c3, "TCP/IP Socket", STYLE_EDGE_BLACK)
    d.add_edge(c3, c4, "HTTP / WebSockets", STYLE_EDGE_BLACK)

    d.save("01_kien_truc_iot_4_lop.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2: NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS
# ══════════════════════════════════════════════════════════════════════════
def build_fig02():
    d = DrawioBuilder("02_nguyen_ly_dieu_che_lora_css", 2150, 1200)
    d.add_title("NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS")

    # Hàng trên: 5 ô xử lý với giãn cách ngang 90px
    b1 = d.add_box("Dữ liệu nhị phân\n(Bitstream)", 80, 120, 310, 130, C_SLATE)
    b2 = d.add_box("Mã hóa Symbol\n(k = 0 .. 2^SF - 1)", 480, 120, 310, 130, C_SKY)
    b3 = d.add_box("Bộ tạo Chirp CSS\n(Quét tần số tuyến tính)", 880, 120, 330, 130, C_GREEN)
    b4 = d.add_box("Khuếch đại PA\n(+17 dBm)", 1300, 120, 310, 130, C_AMBER)
    b5 = d.add_box("Anten phát\n(433 MHz)", 1700, 120, 290, 130, C_ROSE)

    d.add_edge(b1, b2, "Nhóm SF bits", STYLE_EDGE_BLACK)
    d.add_edge(b2, b3, "Symbol k", STYLE_EDGE_BLACK)
    d.add_edge(b3, b4, "Chirp RF", STYLE_EDGE_BLACK)
    d.add_edge(b4, b5, "RF Power", STYLE_EDGE_BLACK)

    # Khung dưới: giãn cách từ hàng trên = 100px
    d.add_box("ĐẶC TÍNH DẠNG SÓNG CHIRP TRÊN MIỀN TẦN SỐ - THỜI GIAN", 80, 350, 1990, 780, C_CONTAINER_BLUE)
    d.add_box("Trục tần số (f)\n\nf0 + BW/2\n\nf0 (433.x MHz)\n\nf0 - BW/2", 130, 430, 310, 660, C_SLATE)
    d.add_box("UP-CHIRP CƠ SỞ (PREAMBLE)\n\n• Quét tần số tuyến tính f_min -> f_max\n• Chu kỳ ký hiệu: Ts = 2^SF / BW\n• Dùng cho đồng bộ khung truyền", 530, 430, 700, 660, C_GREEN)
    d.add_box("CHIRP ĐIỀU CHẾ MANG TIN\n\n• Bước nhảy tần số mang giá trị Symbol k\n• Băng thông kênh: BW = 125 kHz\n• Hệ số trải phổ: SF = 7 .. 12", 1320, 430, 700, 660, C_SKY)

    d.save("02_nguyen_ly_dieu_che_lora_css.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3: KIẾN TRÚC MẠNG LORAWAN HÌNH SAO
# ══════════════════════════════════════════════════════════════════════════
def build_fig03():
    d = DrawioBuilder("03_kien_truc_mang_lorawan_star", 2150, 1150)
    d.add_title("KIẾN TRÚC MẠNG LORAWAN HÌNH SAO")

    # Giãn cách giữa 3 cột container lớn = 120px
    d.add_box("THIẾT BỊ ĐẦU CUỐI (END-NODES)", 80, 110, 500, 980, C_CONTAINER_GREEN)
    # Giãn cách dọc giữa các node = 80px
    na = d.add_box("Node A (Tầng 1)\nESP32 + Ra-02", 130, 190, 400, 220, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + Ra-02", 130, 490, 400, 220, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + Ra-02", 130, 790, 400, 220, C_GREEN)

    d.add_box("MULTI-CHANNEL GATEWAY", 700, 110, 680, 980, C_CONTAINER_BLUE)
    gw = d.add_box("RASPBERRY PI CM4 GATEWAY\nBroadcom BCM2711 @ 1.5 GHz\n\n3x Module SX1278 (SPI0 Bus):\n• Kênh 1: 433.175 MHz\n• Kênh 2: 433.375 MHz\n• Kênh 3: 433.575 MHz\n\nThu song song đồng thời 3 kênh", 740, 200, 600, 800, C_SKY)

    d.add_box("MÁY CHỦ & GIAO DIỆN", 1500, 110, 570, 980, C_CONTAINER_PURP)
    # Giãn cách dọc giữa 2 server = 100px
    ns = d.add_box("Network Server\n• Điều phối khung truyền\n• Lọc gói tin trùng lặp", 1550, 250, 470, 300, C_PURP)
    as_srv = d.add_box("Application Server\n• Giải mã Payload gói tin\n• CSDL và Web Dashboard", 1550, 650, 470, 300, C_AMBER)

    d.add_edge(na, gw, "LoRa RF (433 MHz)", STYLE_EDGE_BLACK)
    d.add_edge(nb, gw, "LoRa RF (433 MHz)", STYLE_EDGE_BLACK)
    d.add_edge(nc, gw, "LoRa RF (433 MHz)", STYLE_EDGE_BLACK)
    d.add_edge(gw, ns, "TCP/IP Socket", STYLE_EDGE_BLACK)
    d.add_edge(ns, as_srv, "JSON Data", STYLE_EDGE_BLACK)

    d.save("03_kien_truc_mang_lorawan_star.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4: SO SÁNH CLOUD AI VÀ EDGE TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig04():
    d = DrawioBuilder("04_so_sanh_cloud_ai_vs_edge_tinyml", 2150, 1250)
    d.add_title("SO SÁNH MÔ HÌNH XỬ LÝ: CLOUD AI VÀ EDGE TINYML")

    # Phần 1: Cloud AI
    d.add_box("1. MÔ HÌNH CLOUD AI TẬP TRUNG", 80, 110, 1990, 490, C_CONTAINER_AMBER)
    # 4 khối ngang với giãn cách 100px
    c1 = d.add_box("End-Node Cảm biến", 130, 190, 380, 140, C_SLATE)
    c2 = d.add_box("Gateway Chuyển tiếp", 610, 190, 380, 140, C_SLATE)
    c3 = d.add_box("Cloud Server AI", 1090, 190, 380, 140, C_AMBER)
    c4 = d.add_box("Gói tin Downlink", 1570, 190, 440, 140, C_ROSE)

    d.add_edge(c1, c2, "Uplink RF", STYLE_EDGE_BLACK)
    d.add_edge(c2, c3, "Internet", STYLE_EDGE_BLACK)
    d.add_edge(c3, c4, "Suy luận đám mây", STYLE_EDGE_BLACK)
    d.add_edge(c4, c1, "Gửi kênh cấu hình", STYLE_EDGE_RED)
    d.add_box("Luồng dữ liệu: CSI gửi lên Cloud -> Máy chủ suy luận -> Gửi cấu hình kênh về qua gói Downlink", 130, 430, 1890, 90, C_SLATE)

    # Giãn cách giữa 2 container lớn = 110px
    d.add_box("2. MÔ HÌNH EDGE TINYML TRÊN THIẾT BỊ BIÊN", 80, 710, 1990, 490, C_CONTAINER_GREEN)
    e1 = d.add_box("Bộ đệm CSI (10x9)", 130, 790, 380, 140, C_GREEN)
    e2 = d.add_box("Mô hình TinyML (ESP32)\nBộ nhớ: 8.65 KB Flash", 610, 790, 420, 140, C_GREEN)
    e3 = d.add_box("Lựa chọn kênh (ArgMax)\nThời gian: < 15 ms", 1130, 790, 380, 140, C_GREEN)
    e4 = d.add_box("Phát sóng LoRa\n(Kênh đã chọn)", 1610, 790, 400, 140, C_SKY)

    d.add_edge(e1, e2, "Dữ liệu 10x9", STYLE_EDGE_GREEN)
    d.add_edge(e2, e3, "Softmax", STYLE_EDGE_GREEN)
    d.add_edge(e3, e4, "Cấu hình tần số", STYLE_EDGE_GREEN)
    d.add_box("Luồng dữ liệu: Suy luận và chọn kênh trực tiếp trên End-Node, hoàn toàn không cần gói tin Downlink", 130, 1030, 1890, 90, C_SLATE)

    d.save("04_so_sanh_cloud_ai_vs_edge_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 5: BÀI TOÁN LỰA CHỌN KÊNH TINYML (KIẾN TRÚC PHÂN TẦNG 3 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig05():
    d = DrawioBuilder("05_bai_toan_lua_chon_kenh_tinyml", 2250, 1450)
    d.add_title("KHUNG KIẾN TRÚC BÀI TOÁN LỰA CHỌN KÊNH TINYML CHO LORAWAN")

    # Khung chú giải (Legend)
    d.add_box("CHÚ GIẢI LUỒNG TƯƠNG TÁC", 80, 110, 430, 310, C_CONTAINER_AMBER)
    d.add_box("Luồng dữ liệu vô tuyến & CSI\n(End-Node -> Gateway -> Server)", 110, 170, 370, 60, C_SLATE)
    d.add_box("Luồng nạp mô hình TinyML\n(Server -> Biên dịch -> Flash)", 110, 245, 370, 60, C_ROSE)
    d.add_box("Vòng lặp suy luận tự chủ\n(Thực thi nội bộ trên ESP32)", 110, 320, 370, 60, C_GREEN)

    # Tầng 1: Server (giãn cách từ Legend = 100px)
    d.add_box("TẦNG 1: MÁY CHỦ HUẤN LUYỆN NGOẠI TUYẾN (SERVER / WORKSTATION)", 610, 110, 1560, 310, C_CONTAINER_PURP)
    s_data = d.add_box("Nhật ký kênh (CSV Logs)\n• Chuỗi thời gian CSI (10x9)\n• Lịch sử RSSI, SNR, mất gói", 650, 175, 430, 140, C_PURP)
    s_train = d.add_box("TensorFlow / Keras Training\n• Tiền xử lý & StandardScaler\n• Huấn luyện 5 kiến trúc nơ-ron\n• 500 Epochs hội tụ chuẩn", 1170, 175, 450, 140, C_PURP)
    s_tflite = d.add_box("TFLite Converter & Exporter\n• Lượng tử hóa FlatBuffer\n• Sinh mã C Header model.h\n• Căn chỉnh alignas(16)", 1710, 175, 410, 140, C_ROSE)

    d.add_edge(s_data, s_train, "Tập dữ liệu", STYLE_EDGE_BLACK)
    d.add_edge(s_train, s_tflite, "Trọng số tối ưu", STYLE_EDGE_RED)
    d.add_box("Quy trình ngoại tuyến: Phân tích dữ liệu thực tế, tối ưu hóa trọng số và xuất mã nguồn C nhúng", 650, 350, 1480, 50, C_SLATE)

    # Tầng 2: Gateway (giãn cách dọc từ Tầng 1 = 100px)
    d.add_box("TẦNG 2: TRẠM THU BIÊN ĐA KÊNH (MULTI-CHANNEL LORA GATEWAY - CM4)", 80, 520, 2090, 280, C_CONTAINER_BLUE)
    gw_rf = d.add_box("3x Module SX1278 (SPI0)\n• CH1: 433.175 MHz\n• CH2: 433.375 MHz\n• CH3: 433.575 MHz\nThu đồng thời 3 kênh", 130, 590, 550, 140, C_SKY)
    gw_mgr = d.add_box("Gateway Manager Daemon\n• Nhận ngắt DIO0 đa luồng\n• Bóc tách Header/Payload\n• Đọc thanh ghi đo RSSI, SNR", 780, 590, 590, 140, C_SKY)
    gw_db = d.add_box("CSDL Log & Data Dispatcher\n• Ghi nhật ký đo đạc CSV\n• Web Dashboard theo dõi\n• Stream dữ liệu sang Server", 1470, 590, 640, 140, C_PURP)

    d.add_edge(gw_rf, gw_mgr, "Tín hiệu RF", STYLE_EDGE_BLACK)
    d.add_edge(gw_mgr, gw_db, "Metadata & CSI", STYLE_EDGE_BLACK)
    d.add_edge(gw_db, s_data, "CSV Stream qua TCP/IP", STYLE_EDGE_BLACK)
    d.add_box("Vai trò trạm thu: Tiếp nhận gói tin từ mọi kênh, bóc tách chỉ số truyền thông và truyền về máy chủ phân tích", 130, 750, 1990, 40, C_SLATE)

    # Tầng 3: End-Node (giãn cách dọc từ Tầng 2 = 100px)
    d.add_box("TẦNG 3: THIẾT BỊ ĐẦU CUỐI IOT BIÊN (EDGE TINYML END-NODE - ESP32)", 80, 900, 2090, 490, C_CONTAINER_GREEN)
    node_mgr = d.add_box("Khối Quản Lý Dữ Liệu (Manager)\n• Cảm biến môi trường (Telemetry)\n• Bộ đệm trượt FIFO (10 bước x 9 đặc trưng)\n• Chuẩn hóa Z-Score O(1) theo SCALER tĩnh\n• Khóa Mutex đồng bộ FreeRTOS", 130, 970, 570, 270, C_GREEN)
    node_ml = d.add_box("Nhân Suy Luận Biên (TFLM Engine)\n• Mảng FlatBuffer model.h trong Flash\n• Vùng đệm Tensor Arena (10 KB RAM tĩnh)\n• Bộ tính toán mạng nơ-ron (Forward Pass)\n• Quyết định kênh tối ưu: k = ArgMax", 800, 970, 600, 270, C_GREEN)
    node_rf = d.add_box("Khối Truyền Thông Vô Tuyến\n• Module LoRa SX1278 (Ra-02)\n• Tự động chỉnh tần số sang kênh k\n• Khuếch đại công suất (+17 dBm)\n• Kích hoạt phát gói tin Uplink", 1500, 970, 610, 270, C_SKY)

    d.add_edge(node_mgr, node_ml, "Vector đặc trưng (90)", STYLE_EDGE_GREEN)
    d.add_edge(node_ml, node_rf, "Chỉ số kênh k", STYLE_EDGE_GREEN)
    d.add_edge(s_tflite, node_ml, "Nạp mã nguồn C header model.h vào Flash", STYLE_EDGE_RED)
    d.add_edge(node_rf, gw_rf, "Gói tin LoRa Uplink (RF 433 MHz)", STYLE_EDGE_BLACK)

    d.add_box("Đặc tính tự chủ: End-Node tự động dự đoán và chuyển kênh cục bộ trong < 15 ms, hoàn toàn không cần gói tin Downlink từ Gateway", 130, 1300, 1990, 65, C_SLATE)

    d.save("05_bai_toan_lua_chon_kenh_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 6: SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig06():
    d = DrawioBuilder("06_so_do_khoi_toan_he_thong", 2200, 1200)
    d.add_title("SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM LORA TINYML")

    # 3 cột container với giãn cách ngang 120px
    d.add_box("PHÂN HỆ TRẠM PHÁT (03 END-NODES)", 80, 110, 520, 1020, C_CONTAINER_GREEN)
    # Giãn cách dọc giữa 3 Node = 100px
    na = d.add_box("Node A (Tầng 1)\nESP32 + SX1278", 130, 200, 420, 190, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + SX1278", 130, 490, 420, 190, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + SX1278", 130, 780, 420, 190, C_GREEN)

    d.add_box("KÊNH TRUYỀN VÔ TUYẾN 433 MHz", 720, 110, 540, 1020, C_CONTAINER_AMBER)
    # Giãn cách dọc giữa các kênh = 110px
    ch1 = d.add_box("Kênh 1: 433.175 MHz (BW 125 kHz)", 770, 220, 440, 150, C_AMBER)
    ch2 = d.add_box("Kênh 2: 433.375 MHz (BW 125 kHz)", 770, 480, 440, 150, C_AMBER)
    ch3 = d.add_box("Kênh 3: 433.575 MHz (BW 125 kHz)", 770, 740, 440, 150, C_AMBER)
    d.add_box("Khoảng cách kênh: 200 kHz", 770, 940, 440, 70, C_SLATE)

    d.add_box("PHÂN HỆ TRẠM THU (GATEWAY CM4)", 1380, 110, 740, 1020, C_CONTAINER_BLUE)
    # Giãn cách dọc giữa các khối trạm thu = 60px
    rx_mod = d.add_box("3x Module SX1278 (SPI0 Bus)\nThu đồng thời 3 kênh", 1430, 190, 640, 160, C_SKY)
    d.add_box("Raspberry Pi CM4\n3 luồng Worker xử lý ngắt DIO0", 1430, 410, 640, 160, C_SKY)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 1430, 630, 640, 160, C_PURP)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 1430, 850, 640, 160, C_AMBER)

    d.add_edge(na, ch1, "RF 433 MHz", STYLE_EDGE_BLACK)
    d.add_edge(nb, ch2, "RF 433 MHz", STYLE_EDGE_BLACK)
    d.add_edge(nc, ch3, "RF 433 MHz", STYLE_EDGE_BLACK)
    d.add_edge(ch1, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK)
    d.add_edge(ch2, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK)
    d.add_edge(ch3, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK)

    d.save("06_so_do_khoi_toan_he_thong.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 7: ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA
# ══════════════════════════════════════════════════════════════════════════
def build_fig07():
    d = DrawioBuilder("07_dinh_dang_khung_truyen_goi_tin", 2150, 850)
    d.add_title("CẤU TRÚC ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA")

    # Hàng tiêu đề phân loại lớn: giãn cách ngang 50px
    d.add_box("HEADER (4 Bytes)", 80, 110, 680, 70, C_TITLE_BLUE)
    d.add_box("METADATA (5 Bytes)", 810, 110, 450, 70, C_TITLE_PURP)
    d.add_box("PAYLOAD (Biến thiên)", 1310, 110, 530, 70, C_TITLE_AMBER)
    d.add_box("CRC (2 Bytes)", 1890, 110, 180, 70, C_TITLE_ROSE)

    # Hàng trường dữ liệu chi tiết: giãn cách ngang 50px, giãn cách từ hàng trên = 50px
    d.add_box("Node_ID\n(1 Byte)\n'A', 'B', 'C'", 80, 230, 190, 180, C_SKY)
    d.add_box("Packet_ID\n(2 Bytes)\n0 - 65,535", 320, 230, 210, 180, C_SKY)
    d.add_box("Current_CH\n(1 Byte)\n0, 1, 2", 580, 230, 180, 180, C_SKY)
    d.add_box("Payload_Size\n(1 Byte)\n30 - 250 B", 810, 230, 200, 180, C_PURP)
    d.add_box("Timestamp\n(4 Bytes)\nmillis()", 1060, 230, 200, 180, C_PURP)
    d.add_box("Payload Data\n(21 - 241 Bytes)\nBộ đệm dữ liệu", 1310, 230, 530, 180, C_AMBER)
    d.add_box("CRC\n(2 Bytes)\nHardware", 1890, 230, 180, 180, C_ROSE)

    # Khung chú thích dưới: giãn cách dọc 70px và 40px
    d.add_box("Các mức kích thước gói tin khảo sát: 30B, 74B, 118B, 162B, 206B, 250B", 80, 480, 1990, 95, C_SLATE)
    d.add_box("Trích xuất tại trạm thu: Bóc tách gói tin và đọc thanh ghi phần cứng SX1278 (RSSI, SNR)", 80, 615, 1990, 95, C_SLATE)

    d.save("07_dinh_dang_khung_truyen_goi_tin.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 8: 5 KIẾN TRÚC MẠNG NƠ-RON TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig08():
    d = DrawioBuilder("08_5_kien_truc_tinyml", 2250, 1180)
    d.add_title("CẤU TRÚC 5 KIẾN TRÚC MẠNG NƠ-RON KHẢO SÁT")

    # Giãn cách giữa 5 card = 80px (rộng rãi gấp hơn 2 lần trước)
    w_card = 350
    gap = 80
    x_start = 90

    # Card 1: FCNN
    x1 = x_start
    d.add_box("1. BASELINE FCNN", x1, 110, w_card, 70, C_TITLE_BLUE)
    d.add_box("• Input: Vector (90)\n• Dense (16, ReLU)\n• Dropout (0.15)\n• Dense (12, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,699\nDung lượng: 8.84 KB", x1, 210, w_card, 770, C_SKY)

    # Card 2: 1D-CNN
    x2 = x1 + w_card + gap
    d.add_box("2. 1D-CNN", x2, 110, w_card, 70, C_TITLE_PURP)
    d.add_box("• Input: Chuỗi (10, 9)\n• Conv1D (16, k=3)\n• BatchNorm + Pool\n• Conv1D (32, k=3)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,659\nDung lượng: 16.34 KB", x2, 210, w_card, 770, C_PURP)

    # Card 3: GRU
    x3 = x2 + w_card + gap
    d.add_box("3. GRU RNN", x3, 110, w_card, 70, C_TITLE_AMBER)
    d.add_box("• Input: Chuỗi (10, 9)\n• GRU (16, unroll)\n• Dropout (0.15)\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,619\nDung lượng: 42.32 KB", x3, 210, w_card, 770, C_AMBER)

    # Card 4: Separable 1D-CNN
    x4 = x3 + w_card + gap
    d.add_box("4. SEPARABLE 1D-CNN", x4, 110, w_card, 70, C_TITLE_GREEN)
    d.add_box("• Input: Chuỗi (10, 9)\n• SepConv1D (16, k=3)\n• SepConv1D (32, k=3)\n• GlobalAvgPool1D\n• Dropout (0.15)\n• Dense (3, Softmax)\n\nTham số: 878\nDung lượng: 8.65 KB", x4, 210, w_card, 770, C_GREEN)

    # Card 5: ResNet-1D
    x5 = x4 + w_card + gap
    d.add_box("5. RESNET-1D", x5, 110, w_card, 70, C_TITLE_ROSE)
    d.add_box("• Input: Chuỗi (10, 9)\n• Conv1D (16, k=3)\n• Residual Block\n  Skip Connection (+x)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,339\nDung lượng: 14.73 KB", x5, 210, w_card, 770, C_ROSE)

    # Giãn cách từ thân card đến hộp tổng quan = 60px
    d.add_box("Cấu trúc lớp mạng và số lượng tham số của 5 mô hình nơ-ron đánh giá trên vi điều khiển ESP32", x_start, 1040, 2070, 95, C_SLATE)

    d.save("08_5_kien_truc_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 9: QUY TRÌNH XỬ LÝ DỮ LIỆU THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig09():
    d = DrawioBuilder("09_pipeline_xu_ly_du_lieu", 2200, 1120)
    d.add_title("QUY TRÌNH XỬ LÝ & CHUẨN HÓA DỮ LIỆU THỰC NGHIỆM")

    # 4 bước ngang với giãn cách 100px
    p1 = d.add_box("Bước 1: Trích xuất log\n• Thu thập dữ liệu Gateway\n• Tách theo Node (A, B, C)\n• Lọc các bản tin hợp lệ", 90, 110, 430, 210, C_CONTAINER_BLUE)
    p2 = d.add_box("Bước 2: Xử lý gói mất\n• Quét số thứ tự Packet_ID\n• Bổ sung các gói bị mất\n• Gán nhãn phạt: RSSI, SNR", 620, 110, 430, 210, C_CONTAINER_PURP)
    p3 = d.add_box("Bước 3: Chuỗi trượt\n• Tensor (10 bước x 9 feat)\n• Gán nhãn kênh mục tiêu\n• Loại bỏ trường rò rỉ nhãn", 1150, 110, 430, 210, C_CONTAINER_AMBER)
    p4 = d.add_box("Bước 4: Chuẩn hóa & Chia\n• StandardScaler: z=(x-μ)/σ\n• Xuất bảng SCALER cho C\n• Chia: 60% / 20% / 20%", 1680, 110, 430, 210, C_CONTAINER_GREEN)

    d.add_edge(p1, p2, "Dữ liệu thô", STYLE_EDGE_BLACK)
    d.add_edge(p2, p3, "Dữ liệu đầy đủ", STYLE_EDGE_BLACK)
    d.add_edge(p3, p4, "Chuỗi trượt", STYLE_EDGE_BLACK)

    # Giãn cách từ hàng trên đến container đầu ra = 100px
    d.add_box("ĐẦU RA QUY TRÌNH DỮ LIỆU", 90, 420, 2020, 640, C_CONTAINER_GREEN)
    # Giãn cách giữa 3 khối đầu ra = 100px
    d.add_box("dataset_ready.csv\n19,440 mẫu chuỗi thời gian\n90 đặc trưng đầu vào", 140, 510, 580, 220, C_GREEN)
    d.add_box("Phân chia tập mẫu\nTrain: 11,664 (60%)\nVal: 3,888 (20%) | Test: 3,888 (20%)", 820, 510, 580, 220, C_SKY)
    d.add_box("Mảng tham số nhúng C\nSCALER_MEAN[9] & SCALER_SCALE[9]\nĐồng bộ trong model.h", 1500, 510, 560, 220, C_AMBER)

    # Giãn cách từ 3 khối đầu ra đến chú thích kỹ thuật = 70px
    d.add_box("Đặc điểm kỹ thuật: Dữ liệu đồng nhất 3 kênh tần số, chuẩn hóa trực tiếp trên thiết bị với độ phức tạp O(1)", 140, 800, 1920, 95, C_SLATE)

    d.save("09_pipeline_xu_ly_du_lieu.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 10: SƠ ĐỒ BỐ TRÍ THỰC ĐỊA TRONG TÒA NHÀ
# ══════════════════════════════════════════════════════════════════════════
def build_fig10():
    d = DrawioBuilder("10_bo_tri_thuc_dia_toa_nha", 2200, 1150)
    d.add_title("SƠ ĐỒ BỐ TRÍ THỰC NGHIỆM KHÔNG GIAN")

    # Giãn cách ngang giữa Trong Nhà và Ngoài Trời = 120px
    d.add_box("KHÔNG GIAN TRONG NHÀ", 80, 110, 1360, 970, C_CONTAINER_BLUE)
    # Giãn cách dọc giữa Tầng 2 và Tầng 1 = 90px
    d.add_box("TẦNG 2: PHÒNG THÍ NGHIỆM VÀ HÀNH LANG", 120, 190, 1280, 360, C_SLATE)
    # Giãn cách ngang giữa GW và Node B = 100px
    gw = d.add_box("GATEWAY CM4\nRaspberry Pi CM4 + 3x SX1278\nVị trí trung tâm", 170, 265, 540, 220, C_SKY)
    nb = d.add_box("NODE B (TẦNG 2)\nCự ly 60m\n(Xuyên sàn bê tông)", 810, 265, 540, 220, C_AMBER)

    d.add_box("TẦNG 1: SẢNH VÀ PHÒNG HỌC", 120, 640, 1280, 390, C_SLATE)
    na = d.add_box("NODE A (TẦNG 1)\nCự ly 25m\n(Xuyên vách ngăn kính)", 170, 725, 560, 230, C_GREEN)

    # Ngoài trời
    d.add_box("KHÔNG GIAN NGOÀI TRỜI", 1560, 110, 560, 970, C_CONTAINER_GREEN)
    nc = d.add_box("NODE C (SÂN TRƯỜNG)\nCự ly 110m\nMôi trường ngoài trời", 1620, 420, 440, 340, C_ROSE)

    d.add_edge(na, gw, "25m (Trong nhà)", STYLE_EDGE_GREEN)
    d.add_edge(nb, gw, "60m (Xuyên tầng)", STYLE_EDGE_BLACK)
    d.add_edge(nc, gw, "110m (Ngoài trời)", STYLE_EDGE_RED)

    d.save("10_bo_tri_thuc_dia_toa_nha.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 11: KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS
# ══════════════════════════════════════════════════════════════════════════
def build_fig11():
    d = DrawioBuilder("11_kien_truc_freertos_da_nhiem", 2150, 1180)
    d.add_title("KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS TRÊN ESP32")

    # Giãn cách ngang giữa Core 0 và Core 1 = 150px
    d.add_box("CORE 0: THU THẬP & HIỂN THỊ", 80, 110, 920, 990, C_CONTAINER_BLUE)
    # Giãn cách dọc giữa các task = 80px
    t_samp = d.add_box("Task_Sampler (Ưu tiên 1)\nĐọc cảm biến -> Cập nhật bộ đệm trượt 10x9", 130, 200, 820, 200, C_SKY)
    d.add_box("Task_OLED (Ưu tiên 1)\nQuét bus I2C -> Hiển thị trạng thái kênh, RSSI, SNR", 130, 480, 820, 200, C_SKY)
    mutex = d.add_box("historyMutex\nKhóa bảo vệ truy cập bộ đệm trượt 10x9", 130, 760, 820, 200, C_AMBER)

    d.add_box("CORE 1: SUY LUẬN AI & TRUYỀN SÓNG RF", 1150, 110, 920, 990, C_CONTAINER_GREEN)
    t_ml = d.add_box("Task_TinyML (Ưu tiên 2)\nZ-Score -> Suy luận TFLM -> ArgMax chọn kênh", 1200, 200, 820, 200, C_GREEN)
    t_tx = d.add_box("Task_LoRaTX (Ưu tiên 3)\nCấu hình tần số -> Phát sóng RF (+17 dBm)", 1200, 480, 820, 200, C_GREEN)
    queue = d.add_box("channelQueue (Độ dài 1)\nHàng đợi truyền mã kênh sang Task TX", 1200, 760, 820, 200, C_PURP)

    d.add_edge(t_samp, mutex, "Ghi dữ liệu", STYLE_EDGE_BLACK)
    d.add_edge(mutex, t_ml, "Đọc bộ đệm", STYLE_EDGE_GREEN)
    d.add_edge(t_ml, queue, "Gửi mã kênh", STYLE_EDGE_GREEN)
    d.add_edge(queue, t_tx, "Nhận mã kênh", STYLE_EDGE_GREEN)

    d.save("11_kien_truc_freertos_da_nhiem.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 12: SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32
# ══════════════════════════════════════════════════════════════════════════
def build_fig12():
    d = DrawioBuilder("12_so_do_noi_chan_end_node_esp32", 2200, 1180)
    d.add_title("SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32")

    # Giãn cách ngang giữa 3 khối linh kiện chính = 120px
    rf = d.add_box("MODULE LORA SX1278 (RA-02)\n• MOSI: GPIO 27\n• MISO: GPIO 19\n• SCK:  GPIO 18\n• NSS:  GPIO 5 (CS)\n• RST:  GPIO 14\n• DIO0: GPIO 26 (TxDone)\n• Nguồn: 3.3V, GND", 90, 120, 560, 720, C_CONTAINER_GREEN)
    mcu = d.add_box("ESP32 DEVKIT V1\nDual-Core 240 MHz\nSRAM 520 KB | Flash 4 MB", 770, 120, 560, 720, C_CONTAINER_BLUE)
    oled = d.add_box("MÀN HÌNH OLED SSD1306\n• SDA: GPIO 21\n• SCL: GPIO 22\n• Nguồn: 3.3V, GND\n\nGiao tiếp bus I2C", 1450, 120, 560, 720, C_CONTAINER_PURP)

    # Giãn cách dọc đến khối nguồn = 100px
    pwr = d.add_box("MẠCH NGUỒN CẤP ĐIỆN\nTụ bù chống sụt áp (100 µF + 100 nF mắc song song đường nguồn 3.3V)", 300, 940, 1500, 130, C_AMBER)

    d.add_edge(rf, mcu, "Bus VSPI & DIO0", STYLE_EDGE_GREEN)
    d.add_edge(mcu, oled, "Bus I2C", STYLE_EDGE_BLACK)
    d.add_edge(pwr, mcu, "3.3V DC", STYLE_EDGE_BLACK)

    d.save("12_so_do_noi_chan_end_node_esp32.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 13: SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY CM4
# ══════════════════════════════════════════════════════════════════════════
def build_fig13():
    d = DrawioBuilder("13_so_do_noi_chan_gateway_cm4", 2250, 1250)
    d.add_title("SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY RASPBERRY PI CM4")

    # Giãn cách ngang giữa 3 cột = 130px
    # Cột 1: 3 module thu + chú thích SPI với giãn cách dọc 70px
    m1 = d.add_box("MODULE THU #1 (CH1 - 433.175 MHz)\nCE: GPIO 8 (CE0) | DIO0: GPIO 24", 80, 120, 540, 210, C_SKY)
    m2 = d.add_box("MODULE THU #2 (CH2 - 433.375 MHz)\nCE: GPIO 7 (CE1) | DIO0: GPIO 23", 80, 400, 540, 210, C_GREEN)
    m3 = d.add_box("MODULE THU #3 (CH3 - 433.575 MHz)\nCE: GPIO 25 (CS2) | DIO0: GPIO 22", 80, 680, 540, 210, C_AMBER)
    d.add_box("Đường SPI0 chung: MOSI=Pin 19, MISO=Pin 21, SCLK=Pin 23", 80, 960, 540, 140, C_SLATE)

    # Cột 2: CM4 trung tâm
    cm4 = d.add_box("RASPBERRY PI CM4\nQuad-Core Cortex-A72 @ 1.5 GHz\n40-Pin GPIO Header | Linux OS", 750, 120, 620, 1040, C_CONTAINER_BLUE)

    # Cột 3: Tiến trình phần mềm với giãn cách dọc 80px
    d.add_box("TIẾN TRÌNH PHẦN MỀM GATEWAY", 1500, 120, 640, 1040, C_CONTAINER_PURP)
    d.add_box("3 luồng Worker nhận ngắt DIO0\nThu đồng thời 3 kênh", 1550, 220, 540, 220, C_PURP)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 1550, 520, 540, 220, C_SLATE)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 1550, 820, 540, 220, C_AMBER)

    d.add_edge(m1, cm4, "SPI0 CE0", STYLE_EDGE_BLACK)
    d.add_edge(m2, cm4, "SPI0 CE1", STYLE_EDGE_BLACK)
    d.add_edge(m3, cm4, "SPI0 CS2", STYLE_EDGE_BLACK)

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
    print(" KHỞI TẠO BỘ SƠ ĐỒ ĐỒ HỌA (.DRAWIO) NÂNG CẤP VỚI KHOẢNG CÁCH RỘNG RÃI")
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
