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
    d = DrawioBuilder("01_kien_truc_iot_4_lop", 1000, 520)
    d.add_title("KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT", x=50, y=20, w=900, h=40)

    # 4 lớp xếp tầng
    c1 = d.add_box("LỚP CẢM NHẬN (PERCEPTION LAYER)", 60, 80, 880, 80, C_CONTAINER_GREEN)
    d.add_box("Cảm biến môi trường", 80, 110, 260, 38, C_GREEN)
    d.add_box("Vi điều khiển ESP32", 370, 110, 260, 38, C_GREEN)
    d.add_box("Transceiver LoRa SX1278 (433 MHz)", 660, 110, 260, 38, C_GREEN)

    c2 = d.add_box("LỚP MẠNG TRUYỀN DẪN (NETWORK LAYER)", 60, 180, 880, 80, C_CONTAINER_BLUE)
    d.add_box("Sóng vô tuyến LoRa (433 MHz)", 80, 210, 260, 38, C_SKY)
    d.add_box("Gateway đa kênh (Raspberry Pi CM4)", 370, 210, 260, 38, C_SKY)
    d.add_box("Mạng IP (Ethernet / Wi-Fi)", 660, 210, 260, 38, C_SKY)

    c3 = d.add_box("LỚP TRUNG GIAN (MIDDLEWARE LAYER)", 60, 280, 880, 80, C_CONTAINER_PURP)
    d.add_box("Network Server (Điều phối gói tin)", 80, 310, 260, 38, C_PURP)
    d.add_box("Message Broker (MQTT / REST API)", 370, 310, 260, 38, C_PURP)
    d.add_box("Cơ sở dữ liệu chuỗi thời gian", 660, 310, 260, 38, C_PURP)

    c4 = d.add_box("LỚP ỨNG DỤNG (APPLICATION LAYER)", 60, 380, 880, 80, C_CONTAINER_AMBER)
    d.add_box("Ứng dụng giám sát thông minh", 80, 410, 260, 38, C_AMBER)
    d.add_box("Web Dashboard thời gian thực", 370, 410, 260, 38, C_AMBER)
    d.add_box("Hệ thống quản lý dữ liệu đo", 660, 410, 260, 38, C_AMBER)

    # Arrows
    d.add_edge(c1, c2, "LoRa RF (433 MHz)")
    d.add_edge(c2, c3, "TCP/IP")
    d.add_edge(c3, c4, "HTTP / WebSockets")

    d.save("01_kien_truc_iot_4_lop.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2: NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS
# ══════════════════════════════════════════════════════════════════════════
def build_fig02():
    d = DrawioBuilder("02_nguyen_ly_dieu_che_lora_css", 1000, 440)
    d.add_title("NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS", x=50, y=20, w=900, h=40)

    b1 = d.add_box("Dữ liệu nhị phân\n(Bitstream đầu vào)", 60, 85, 150, 60, C_SLATE)
    b2 = d.add_box("Mã hóa Symbol\n(k = 0 .. 2^SF - 1)", 240, 85, 150, 60, C_SKY)
    b3 = d.add_box("Bộ tạo tín hiệu Chirp\n(Quét tần số tuyến tính)", 420, 85, 180, 60, C_GREEN)
    b4 = d.add_box("Khuếch đại công suất PA\n(+17 dBm)", 630, 85, 160, 60, C_AMBER)
    b5 = d.add_box("Anten 433 MHz\n(Sóng điện từ)", 820, 85, 120, 60, C_ROSE)

    d.add_edge(b1, b2, "Nhóm SF bits")
    d.add_edge(b2, b3, "Ký hiệu k")
    d.add_edge(b3, b4, "Chirp Signal")
    d.add_edge(b4, b5, "RF Power")

    # Spectrogram Box
    d.add_box("ĐẶC TÍNH DẠNG SÓNG CHIRP TRÊN MIỀN TẦN SỐ - THỜI GIAN", 60, 175, 880, 230, C_CONTAINER_BLUE)
    d.add_box("Tần số (f)\n\nf_0 + BW/2\n\nf_0\n\nf_0 - BW/2", 80, 215, 140, 170, C_SLATE)
    d.add_box("UP-CHIRP CƠ SỞ\n\n• Quét tần số tuyến tính từ f_min đến f_max\n• Chu kỳ ký hiệu: Ts = 2^SF / BW\n• Dùng cho đồng bộ khung truyền (Preamble)", 240, 215, 330, 170, C_GREEN)
    d.add_box("CHIRP ĐIỀU CHẾ MANG TIN\n\n• Bước nhảy tần số mang giá trị bit\n• Băng thông kênh: BW = 125 kHz\n• Hệ số trải phổ: SF = 7 .. 12", 590, 215, 330, 170, C_SKY)

    d.save("02_nguyen_ly_dieu_che_lora_css.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3: KIẾN TRÚC MẠNG LORAWAN HÌNH SAO
# ══════════════════════════════════════════════════════════════════════════
def build_fig03():
    d = DrawioBuilder("03_kien_truc_mang_lorawan_star", 1000, 500)
    d.add_title("KIẾN TRÚC MẠNG LORAWAN HÌNH SAO", x=50, y=20, w=900, h=40)

    # 3 Cột
    d.add_box("THIẾT BỊ ĐẦU CUỐI (END-NODES)", 50, 80, 220, 390, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + Ra-02", 70, 120, 180, 75, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + Ra-02", 70, 215, 180, 75, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + Ra-02", 70, 310, 180, 75, C_GREEN)

    d.add_box("GATEWAY ĐA KÊNH", 320, 80, 320, 390, C_CONTAINER_BLUE)
    gw = d.add_box("RASPBERRY PI CM4 GATEWAY\n\n3x Module SX1278 (SPI0 Bus):\n• Kênh 1: 433.175 MHz\n• Kênh 2: 433.375 MHz\n• Kênh 3: 433.575 MHz\n\nThu song song đồng thời 3 kênh", 340, 130, 280, 250, C_SKY)

    d.add_box("QUẢN TRỊ & ỨNG DỤNG", 690, 80, 260, 390, C_CONTAINER_PURP)
    ns = d.add_box("Network Server\n• Điều phối khung truyền\n• Lọc gói tin trùng lặp", 710, 130, 220, 95, C_PURP)
    as_srv = d.add_box("Application Server & Web\n• Giải mã Payload gói tin\n• CSDL và Web Dashboard", 710, 255, 220, 95, C_AMBER)

    # Connections
    d.add_edge(na, gw, "LoRa RF 433 MHz")
    d.add_edge(nb, gw, "LoRa RF 433 MHz")
    d.add_edge(nc, gw, "LoRa RF 433 MHz")
    d.add_edge(gw, ns, "TCP/IP")
    d.add_edge(ns, as_srv, "JSON Data")

    d.save("03_kien_truc_mang_lorawan_star.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4: SO SÁNH CLOUD AI VÀ EDGE TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig04():
    d = DrawioBuilder("04_so_sanh_cloud_ai_vs_edge_tinyml", 1000, 440)
    d.add_title("SO SÁNH MÔ HÌNH XỬ LÝ: CLOUD AI VÀ EDGE TINYML", x=50, y=20, w=900, h=40)

    # Top: Cloud AI
    d.add_box("1. MÔ HÌNH CLOUD AI TẬP TRUNG", 50, 80, 900, 140, C_CONTAINER_AMBER)
    c1 = d.add_box("End-Node Cảm biến", 70, 115, 160, 45, C_SLATE)
    c2 = d.add_box("Gateway Chuyển tiếp", 290, 115, 160, 45, C_SLATE)
    c3 = d.add_box("Cloud Server AI", 510, 115, 160, 45, C_AMBER)
    c4 = d.add_box("Gói tin Downlink", 730, 115, 190, 45, C_ROSE)

    d.add_edge(c1, c2, "Uplink RF")
    d.add_edge(c2, c3, "Internet")
    d.add_edge(c3, c4, "Suy luận đám mây")
    d.add_edge(c4, c1, "Gửi kênh cấu hình", "edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e11d48;dashed=1;")
    d.add_box("Luồng dữ liệu: CSI truyền lên Cloud -> Máy chủ suy luận -> Gửi cấu hình kênh về qua gói Downlink", 70, 175, 850, 30, C_SLATE)

    # Bottom: Edge TinyML
    d.add_box("2. MÔ HÌNH EDGE TINYML TRÊN THIẾT BỊ BIÊN", 50, 240, 900, 160, C_CONTAINER_GREEN)
    e1 = d.add_box("Bộ đệm CSI (10x9)", 70, 275, 180, 48, C_GREEN)
    e2 = d.add_box("Mô hình TinyML (ESP32)\nBộ nhớ Flash: 8.65 KB", 300, 275, 220, 48, C_GREEN)
    e3 = d.add_box("Lựa chọn kênh (ArgMax)\nThời gian: < 15 ms", 570, 275, 180, 48, C_GREEN)
    e4 = d.add_box("Phát sóng LoRa\n(Kênh đã chọn)", 800, 275, 160, 48, C_SKY)

    d.add_edge(e1, e2, "Dữ liệu 10x9")
    d.add_edge(e2, e3, "Xác suất Softmax")
    d.add_edge(e3, e4, "Cấu hình tần số")
    d.add_box("Luồng dữ liệu: Suy luận và chọn kênh trực tiếp trên End-Node, không cần gói tin Downlink", 70, 345, 890, 30, C_SLATE)

    d.save("04_so_sanh_cloud_ai_vs_edge_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 5: BÀI TOÁN LỰA CHỌN KÊNH TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig05():
    d = DrawioBuilder("05_bai_toan_lua_chon_kenh_tinyml", 1000, 440)
    d.add_title("QUY TRÌNH CHỌN KÊNH TRUYỀN DỰA TRÊN TINYML", x=50, y=20, w=900, h=40)

    # Top pipeline
    b1 = d.add_box("Bộ đệm trượt CSI (10x9)\n10 bước x 9 đặc trưng\n(RSSI, SNR, Payload, Freq)", 60, 80, 200, 90, C_CONTAINER_BLUE)
    b2 = d.add_box("Chuẩn hóa Z-Score\nz = (x - μ) / σ\nBảng SCALER tĩnh O(1)", 290, 80, 180, 90, C_SKY)
    b3 = d.add_box("Mạng nơ-ron TinyML\nĐầu vào: Vector (90)\nĐầu ra: 3 giá trị Logits", 500, 80, 220, 90, C_CONTAINER_GREEN)
    b4 = d.add_box("Hàm kích hoạt Softmax\nPhân phối xác suất\n[P(CH0), P(CH1), P(CH2)]", 750, 80, 190, 90, C_PURP)

    d.add_edge(b1, b2, "Ma trận (10, 9)")
    d.add_edge(b2, b3, "Vector (90)")
    d.add_edge(b3, b4, "Logits")

    # Bottom execution
    b5 = d.add_box("Tìm kênh xác suất lớn nhất (ArgMax)\nk = argmax(P0, P1, P2)", 450, 210, 280, 45, C_AMBER)
    b6 = d.add_box("Cài đặt tần số SX1278\nradio.setFrequency(f_k)", 450, 280, 280, 45, C_ROSE)
    b7 = d.add_box("Phát gói tin LoRa tại kênh k\nCông suất phát: +17 dBm", 450, 350, 280, 45, C_GREEN)

    d.add_edge(b4, b5, "Phân phối xác suất", "edgeStyle=orthogonalEdgeStyle;rounded=1;")
    d.add_edge(b5, b6, "Chỉ số kênh k")
    d.add_edge(b6, b7, "Kích hoạt phát")

    d.save("05_bai_toan_lua_chon_kenh_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 6: SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig06():
    d = DrawioBuilder("06_so_do_khoi_toan_he_thong", 1050, 520)
    d.add_title("SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM LORA TINYML", x=50, y=20, w=950, h=40)

    # 3 Khối
    d.add_box("PHÂN HỆ TRẠM PHÁT (03 END-NODES)", 50, 80, 280, 410, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + SX1278", 70, 120, 240, 75, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + SX1278", 70, 220, 240, 75, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + SX1278", 70, 320, 240, 75, C_GREEN)

    d.add_box("KÊNH TRUYỀN VÔ TUYẾN 433 MHz", 370, 80, 260, 410, C_CONTAINER_AMBER)
    ch1 = d.add_box("Kênh 1: 433.175 MHz (BW 125 kHz)", 390, 125, 220, 60, C_AMBER)
    ch2 = d.add_box("Kênh 2: 433.375 MHz (BW 125 kHz)", 390, 210, 220, 60, C_AMBER)
    ch3 = d.add_box("Kênh 3: 433.575 MHz (BW 125 kHz)", 390, 295, 220, 60, C_AMBER)
    d.add_box("Khoảng cách kênh: 200 kHz", 390, 390, 220, 35, C_SLATE)

    d.add_box("PHÂN HỆ TRẠM THU (GATEWAY CM4)", 670, 80, 330, 410, C_CONTAINER_BLUE)
    rx_mod = d.add_box("3x Module SX1278 (SPI0 Bus)\nThu song song đồng thời 3 kênh", 690, 120, 290, 65, C_SKY)
    d.add_box("Raspberry Pi CM4\n3 luồng Worker xử lý ngắt DIO0", 690, 205, 290, 65, C_SKY)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 690, 290, 290, 65, C_PURP)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 690, 375, 290, 65, C_AMBER)

    # Connections
    d.add_edge(na, ch1, "RF 433 MHz")
    d.add_edge(nb, ch2, "RF 433 MHz")
    d.add_edge(nc, ch3, "RF 433 MHz")
    d.add_edge(ch1, rx_mod, "Thu tín hiệu")
    d.add_edge(ch2, rx_mod, "Thu tín hiệu")
    d.add_edge(ch3, rx_mod, "Thu tín hiệu")

    d.save("06_so_do_khoi_toan_he_thong.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 7: ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA
# ══════════════════════════════════════════════════════════════════════════
def build_fig07():
    d = DrawioBuilder("07_dinh_dang_khung_truyen_goi_tin", 1000, 320)
    d.add_title("CẤU TRÚC ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA", x=50, y=20, w=900, h=40)

    # Category Headers
    d.add_box("HEADER (4 Bytes)", 60, 80, 340, 32, C_TITLE_BLUE)
    d.add_box("METADATA (5 Bytes)", 420, 80, 210, 32, C_TITLE_PURP)
    d.add_box("PAYLOAD (Biến thiên)", 650, 80, 200, 32, C_TITLE_AMBER)
    d.add_box("CRC (2 Bytes)", 870, 80, 90, 32, C_TITLE_ROSE)

    # Fields
    d.add_box("Node_ID\n(1 Byte)\n'A', 'B', 'C'", 60, 120, 100, 70, C_SKY)
    d.add_box("Packet_ID\n(2 Bytes)\n0 - 65,535", 170, 120, 110, 70, C_SKY)
    d.add_box("Current_CH\n(1 Byte)\n0, 1, 2", 290, 120, 110, 70, C_SKY)
    d.add_box("Payload_Size\n(1 Byte)\n30 - 250 B", 420, 120, 100, 70, C_PURP)
    d.add_box("Timestamp\n(4 Bytes)\nmillis()", 530, 120, 100, 70, C_PURP)
    d.add_box("Payload Data\n(21 - 241 Bytes)\nBộ đệm dữ liệu", 650, 120, 200, 70, C_AMBER)
    d.add_box("CRC\n(2 Bytes)\nHardware", 870, 120, 90, 70, C_ROSE)

    # Sub-banners
    d.add_box("Các mức kích thước gói tin: 30B, 74B, 118B, 162B, 206B, 250B", 60, 210, 900, 30, C_SLATE)
    d.add_box("Trích xuất tại trạm thu: Bóc tách gói tin và đọc thanh ghi phần cứng SX1278 (RSSI, SNR)", 60, 255, 900, 30, C_SLATE)

    d.save("07_dinh_dang_khung_truyen_goi_tin.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 8: 5 KIẾN TRÚC MẠNG NƠ-RON TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig08():
    d = DrawioBuilder("08_5_kien_truc_tinyml", 1080, 500)
    d.add_title("CẤU TRÚC 5 KIẾN TRÚC MẠNG NƠ-RON KHẢO SÁT", x=40, y=20, w=1000, h=40)

    w_card = 185
    gap = 18
    start_x = 42

    # Card 1: FCNN
    x1 = start_x
    d.add_box("1. BASELINE FCNN", x1, 80, w_card, 38, C_TITLE_BLUE)
    d.add_box("• Input: Vector (90)\n• Dense (16, ReLU)\n• Dropout (0.15)\n• Dense (12, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,699\nDung lượng: 8.84 KB", x1, 125, w_card, 300, C_SKY)

    # Card 2: 1D-CNN
    x2 = x1 + w_card + gap
    d.add_box("2. 1D-CNN", x2, 80, w_card, 38, C_TITLE_PURP)
    d.add_box("• Input: Chuỗi (10, 9)\n• Conv1D (16, k=3)\n• BatchNorm + Pool\n• Conv1D (32, k=3)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,659\nDung lượng: 16.34 KB", x2, 125, w_card, 300, C_PURP)

    # Card 3: GRU
    x3 = x2 + w_card + gap
    d.add_box("3. GRU RNN", x3, 80, w_card, 38, C_TITLE_AMBER)
    d.add_box("• Input: Chuỗi (10, 9)\n• GRU (16, unroll)\n• Dropout (0.15)\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 1,619\nDung lượng: 42.32 KB", x3, 125, w_card, 300, C_AMBER)

    # Card 4: Separable 1D-CNN
    x4 = x3 + w_card + gap
    d.add_box("4. SEPARABLE 1D-CNN", x4, 80, w_card, 38, C_TITLE_GREEN)
    d.add_box("• Input: Chuỗi (10, 9)\n• SepConv1D (16, k=3)\n• SepConv1D (32, k=3)\n• GlobalAvgPool1D\n• Dropout (0.15)\n• Dense (3, Softmax)\n\nTham số: 878\nDung lượng: 8.65 KB", x4, 125, w_card, 300, C_GREEN)

    # Card 5: ResNet-1D
    x5 = x4 + w_card + gap
    d.add_box("5. RESNET-1D", x5, 80, w_card, 38, C_TITLE_ROSE)
    d.add_box("• Input: Chuỗi (10, 9)\n• Conv1D (16, k=3)\n• Residual Block\n  Skip Connection (+x)\n• GlobalAvgPool1D\n• Dense (16, ReLU)\n• Dense (3, Softmax)\n\nTham số: 2,339\nDung lượng: 14.73 KB", x5, 125, w_card, 300, C_ROSE)

    d.add_box("Cấu trúc lớp mạng và số lượng tham số của 5 mô hình nơ-ron đánh giá trên vi điều khiển ESP32", 40, 445, 1000, 32, C_SLATE)

    d.save("08_5_kien_truc_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 9: QUY TRÌNH XỬ LÝ DỮ LIỆU THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig09():
    d = DrawioBuilder("09_pipeline_xu_ly_du_lieu", 1000, 420)
    d.add_title("QUY TRÌNH XỬ LÝ & CHUẨN HÓA DỮ LIỆU THỰC NGHIỆM", x=50, y=20, w=900, h=40)

    p1 = d.add_box("Bước 1: Trích xuất log\n• Thu thập dữ liệu Gateway\n• Tách theo Node (A, B, C)\n• Lọc các bản tin hợp lệ", 60, 80, 200, 80, C_CONTAINER_BLUE)
    p2 = d.add_box("Bước 2: Xử lý gói mất\n• Quét số thứ tự Packet_ID\n• Bổ sung các gói bị mất\n• Gán nhãn phạt: RSSI, SNR", 290, 80, 200, 80, C_CONTAINER_PURP)
    p3 = d.add_box("Bước 3: Chuỗi trượt\n• Tensor (10 bước x 9 feat)\n• Gán nhãn kênh mục tiêu\n• Loại bỏ trường rò rỉ nhãn", 520, 80, 200, 80, C_CONTAINER_AMBER)
    p4 = d.add_box("Bước 4: Chuẩn hóa & Chia tập\n• StandardScaler: z = (x - μ)/σ\n• Xuất bảng SCALER cho C\n• Chia tập: 60% / 20% / 20%", 750, 80, 200, 80, C_CONTAINER_GREEN)

    d.add_edge(p1, p2, "Dữ liệu thô")
    d.add_edge(p2, p3, "Dữ liệu đầy đủ")
    d.add_edge(p3, p4, "Chuỗi trượt")

    # Outputs
    d.add_box("ĐẦU RA QUY TRÌNH DỮ LIỆU", 60, 185, 890, 150, C_CONTAINER_GREEN)
    d.add_box("dataset_ready.csv\n19,440 mẫu chuỗi thời gian\n90 đặc trưng đầu vào", 80, 220, 260, 60, C_GREEN)
    d.add_box("Phân chia tập mẫu\nTrain: 11,664 (60%)\nVal: 3,888 (20%) | Test: 3,888 (20%)", 370, 220, 260, 60, C_SKY)
    d.add_box("Mảng tham số nhúng C\nSCALER_MEAN[9] & SCALER_SCALE[9]\nĐồng bộ trong model.h", 660, 220, 260, 60, C_AMBER)

    d.add_box("Đặc điểm kỹ thuật: Dữ liệu đồng nhất 3 kênh tần số, chuẩn hóa trực tiếp trên thiết bị với độ phức tạp O(1)", 80, 295, 840, 30, C_SLATE)

    d.save("09_pipeline_xu_ly_du_lieu.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 10: SƠ ĐỒ BỐ TRÍ THỰC ĐỊA TRONG TÒA NHÀ
# ══════════════════════════════════════════════════════════════════════════
def build_fig10():
    d = DrawioBuilder("10_bo_tri_thuc_dia_toa_nha", 1000, 460)
    d.add_title("SƠ ĐỒ BỐ TRÍ THỰC NGHIỆM KHÔNG GIAN", x=50, y=20, w=900, h=40)

    # Indoor Container
    d.add_box("KHÔNG GIAN TRONG NHÀ", 60, 80, 580, 350, C_CONTAINER_BLUE)
    d.add_box("TẦNG 2: PHÒNG THÍ NGHIỆM VÀ HÀNH LANG", 80, 115, 540, 130, C_SLATE)
    gw = d.add_box("GATEWAY CM4\nRaspberry Pi CM4 + 3x SX1278\nVị trí trung tâm", 100, 145, 230, 80, C_SKY)
    nb = d.add_box("NODE B (TẦNG 2)\nCự ly 60m (Xuyên sàn bê tông)", 370, 145, 230, 80, C_AMBER)

    d.add_box("TẦNG 1: SẢNH VÀ PHÒNG HỌC", 80, 260, 540, 150, C_SLATE)
    na = d.add_box("NODE A (TẦNG 1)\nCự ly 25m (Xuyên vách ngăn)", 100, 295, 250, 85, C_GREEN)

    # Outdoor Container
    d.add_box("KHÔNG GIAN NGOÀI TRỜI", 670, 80, 270, 350, C_CONTAINER_GREEN)
    nc = d.add_box("NODE C (SÂN TRƯỜNG)\nCự ly 110m\nMôi trường ngoài trời", 690, 180, 230, 110, C_ROSE)

    # Wireless links
    d.add_edge(na, gw, "25m (Trong nhà)", "strokeColor=#16a34a;strokeWidth=2;")
    d.add_edge(nb, gw, "60m (Xuyên tầng)", "strokeColor=#d97706;strokeWidth=2;")
    d.add_edge(nc, gw, "110m (Ngoài trời)", "strokeColor=#e11d48;strokeWidth=2;")

    d.save("10_bo_tri_thuc_dia_toa_nha.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 11: KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS
# ══════════════════════════════════════════════════════════════════════════
def build_fig11():
    d = DrawioBuilder("11_kien_truc_freertos_da_nhiem", 1000, 460)
    d.add_title("KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS TRÊN ESP32", x=50, y=20, w=900, h=40)

    # Core 0
    d.add_box("CORE 0: THU THẬP & HIỂN THỊ", 60, 80, 420, 350, C_CONTAINER_BLUE)
    t_samp = d.add_box("Task_Sampler (Ưu tiên 1)\nĐọc cảm biến -> Cập nhật bộ đệm trượt 10x9", 80, 120, 380, 65, C_SKY)
    d.add_box("Task_OLED (Ưu tiên 1)\nQuét bus I2C -> Hiển thị trạng thái kênh, RSSI, SNR", 80, 205, 380, 65, C_SKY)
    mutex = d.add_box("historyMutex\nKhóa bảo vệ truy cập bộ đệm trượt 10x9", 80, 290, 380, 55, C_AMBER)

    # Core 1
    d.add_box("CORE 1: SUY LUẬN AI & TRUYỀN SÓNG RF", 520, 80, 420, 350, C_CONTAINER_GREEN)
    t_ml = d.add_box("Task_TinyML (Ưu tiên 2)\nZ-Score -> Suy luận TFLM -> ArgMax chọn kênh", 540, 120, 380, 65, C_GREEN)
    t_tx = d.add_box("Task_LoRaTX (Ưu tiên 3)\nCấu hình tần số -> Phát sóng RF (+17 dBm)", 540, 205, 380, 65, C_GREEN)
    queue = d.add_box("channelQueue (Độ dài 1)\nHàng đợi truyền mã kênh sang Task TX", 540, 290, 380, 55, C_PURP)

    d.add_edge(t_samp, mutex, "Ghi dữ liệu")
    d.add_edge(mutex, t_ml, "Đọc bộ đệm")
    d.add_edge(t_ml, queue, "Gửi mã kênh")
    d.add_edge(queue, t_tx, "Nhận mã kênh")

    d.save("11_kien_truc_freertos_da_nhiem.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 12: SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32
# ══════════════════════════════════════════════════════════════════════════
def build_fig12():
    d = DrawioBuilder("12_so_do_noi_chan_end_node_esp32", 1000, 460)
    d.add_title("SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32", x=50, y=20, w=900, h=40)

    # ESP32 center
    mcu = d.add_box("ESP32 DEVKIT V1\nDual-Core 240 MHz | SRAM 520 KB | Flash 4 MB", 360, 80, 280, 270, C_CONTAINER_BLUE)

    # Left: SX1278
    rf = d.add_box("MODULE LORA SX1278 (RA-02)\n• MOSI: GPIO 27\n• MISO: GPIO 19\n• SCK:  GPIO 18\n• NSS:  GPIO 5 (CS)\n• RST:  GPIO 14\n• DIO0: GPIO 26 (TxDone)\n• Nguồn: 3.3V, GND", 60, 80, 260, 270, C_CONTAINER_GREEN)

    # Right: OLED
    oled = d.add_box("MÀN HÌNH OLED SSD1306\n• SDA: GPIO 21\n• SCL: GPIO 22\n• Nguồn: 3.3V, GND\n\nGiao tiếp bus I2C", 680, 80, 260, 270, C_CONTAINER_PURP)

    # Bottom: Power circuit
    pwr = d.add_box("MẠCH NGUỒN CẤP ĐIỆN\nTụ bù chống sụt áp (100 µF + 100 nF mắc song song đường nguồn 3.3V)", 160, 380, 680, 45, C_AMBER)

    d.add_edge(rf, mcu, "Bus VSPI & DIO0")
    d.add_edge(mcu, oled, "Bus I2C")
    d.add_edge(pwr, mcu, "3.3V DC")

    d.save("12_so_do_noi_chan_end_node_esp32.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 13: SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY CM4
# ══════════════════════════════════════════════════════════════════════════
def build_fig13():
    d = DrawioBuilder("13_so_do_noi_chan_gateway_cm4", 1000, 500)
    d.add_title("SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY RASPBERRY PI CM4", x=50, y=20, w=900, h=40)

    # 3 Receiver modules on left
    m1 = d.add_box("MODULE THU #1 (CH1 - 433.175 MHz)\nCE: GPIO 8 (CE0) | DIO0: GPIO 24", 60, 80, 260, 90, C_SKY)
    m2 = d.add_box("MODULE THU #2 (CH2 - 433.375 MHz)\nCE: GPIO 7 (CE1) | DIO0: GPIO 23", 60, 190, 260, 90, C_GREEN)
    m3 = d.add_box("MODULE THU #3 (CH3 - 433.575 MHz)\nCE: GPIO 25 (CS2) | DIO0: GPIO 22", 60, 300, 260, 90, C_AMBER)
    d.add_box("Đường SPI0 chung: MOSI=Pin 19, MISO=Pin 21, SCLK=Pin 23", 60, 410, 260, 40, C_SLATE)

    # CM4 center
    cm4 = d.add_box("RASPBERRY PI CM4\nQuad-Core Cortex-A72 @ 1.5 GHz\n40-Pin GPIO Header | Linux OS", 360, 80, 280, 370, C_CONTAINER_BLUE)

    # Software services on right
    d.add_box("TIẾN TRÌNH PHẦN MỀM GATEWAY", 680, 80, 260, 370, C_CONTAINER_PURP)
    d.add_box("3 luồng Worker nhận ngắt DIO0\nThu đồng thời 3 kênh", 700, 120, 220, 75, C_PURP)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 700, 215, 220, 75, C_SLATE)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 700, 310, 220, 75, C_AMBER)

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
