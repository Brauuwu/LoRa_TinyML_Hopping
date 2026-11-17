#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_drawio_diagrams.py
Tạo tự động 13 tệp sơ đồ đồ họa định dạng .drawio (XML) chất lượng cao cho đồ án:
Lựa chọn kênh truyền tối ưu cho hệ thống LoRaWAN dựa trên TinyML.

Đặc tính thiết kế hoàn thiện:
- Cỡ chữ lớn chuẩn hóa: 24px - 32px (Tiêu đề 32px, Container 26px, Hộp nội dung 24px, Mũi tên 22px).
- Khoảng cách các ô/khối (gaps/margins) cực kỳ rộng rãi (80px - 220px), canvas mở rộng (2150px - 2350px).
- Chú thích trên mũi tên nằm rõ ràng PHÍA TRÊN hoặc BÊN CẠNH đường nối, có nền trắng mờ (labelBackgroundColor=#ffffff) triệt tiêu việc gạch ngang chữ.
- Định tuyến mũi tên (waypoints, ports) được quy định chặt chẽ: TUYỆT ĐỐI KHÔNG ĐI XUYÊN QUA BẤT KỲ Ô KHÁC NÀO.
- Không nhận định đánh giá kết quả chủ quan, chỉ nêu thông số và kiến trúc kỹ thuật thuần túy.
"""

import os
import xml.etree.ElementTree as ET

DOCS_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/docs/figs")
ROOT_FIGS_DIR = os.path.abspath("E:/DATN/LoRa_TinyML_Hopping/figs")
os.makedirs(DOCS_FIGS_DIR, exist_ok=True)
os.makedirs(ROOT_FIGS_DIR, exist_ok=True)


class DrawioBuilder:
    def __init__(self, title="Diagram", width=2200, height=1250):
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

    def add_edge(
        self,
        source_id,
        target_id,
        label="",
        style=None,
        waypoints=None,
        label_offset=(0, -18),
        exit_port=None,
        entry_port=None,
    ):
        cid = str(self.cell_id)
        self.cell_id += 1
        if style is None:
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#334155;strokeWidth=2.5;endArrow=block;endFill=1;"
                "fontColor=#0f172a;fontSize=22;fontStyle=1;fontFamily=Helvetica;"
                "labelBackgroundColor=#ffffff;labelBorderColor=none;"
            )

        # Gán cổng kết nối chính xác nếu có
        if exit_port is not None:
            style += f"exitX={exit_port[0]};exitY={exit_port[1]};exitDx=0;exitDy=0;"
        if entry_port is not None:
            style += f"entryX={entry_port[0]};entryY={entry_port[1]};entryDx=0;entryDy=0;"

        escaped_label = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "&#xa;")
        )

        geo_content = ""
        if waypoints:
            pts_xml = "\n".join([f'          <mxPoint x="{p[0]}" y="{p[1]}" />' for p in waypoints])
            geo_content += f"""        <Array as="points">
{pts_xml}
        </Array>\n"""

        ox, oy = label_offset
        if ox != 0 or oy != 0:
            geo_content += f'        <mxPoint as="offset" x="{ox}" y="{oy}" />\n'

        if geo_content:
            cell = (
                f'<mxCell id="{cid}" value="{escaped_label}" style="{style}" edge="1" parent="1" source="{source_id}" target="{target_id}">\n'
                f'  <mxGeometry relative="1" as="geometry">\n'
                f'{geo_content}'
                f'  </mxGeometry>\n'
                f'</mxCell>'
            )
        else:
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


# ── ĐỊNH NGHĨA PHONG CÁCH MATERIAL DESIGN CHUẨN (CỠ CHỮ 24PX - 32PX) ─────────
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

STYLE_EDGE_BLACK = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0f172a;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#0f172a;fontSize=22;fontStyle=1;fontFamily=Helvetica;labelBackgroundColor=#ffffff;labelBorderColor=none;"
STYLE_EDGE_RED   = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#dc2626;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#b91c1c;fontSize=22;fontStyle=1;fontFamily=Helvetica;labelBackgroundColor=#ffffff;labelBorderColor=none;"
STYLE_EDGE_GREEN = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;strokeWidth=2.5;endArrow=block;endFill=1;fontColor=#15803d;fontSize=22;fontStyle=1;fontFamily=Helvetica;labelBackgroundColor=#ffffff;labelBorderColor=none;"


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 1: KIẾN TRÚC PHÂN TẦNG IOT (4 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig01():
    d = DrawioBuilder("01_kien_truc_iot_4_lop", 2150, 1400)
    d.add_title("KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT (4 LỚP)")

    # 4 tầng với giãn cách giữa các tầng = 100px, giãn cách các ô trong hàng = 120px
    c1 = d.add_box("LỚP CẢM NHẬN (PERCEPTION LAYER)", 80, 120, 1990, 200, C_CONTAINER_GREEN)
    d.add_box("Cảm biến môi trường", 140, 185, 560, 110, C_GREEN)
    d.add_box("Vi điều khiển ESP32", 800, 185, 560, 110, C_GREEN)
    d.add_box("Transceiver LoRa SX1278 (433 MHz)", 1460, 185, 560, 110, C_GREEN)

    c2 = d.add_box("LỚP MẠNG TRUYỀN DẪN (NETWORK LAYER)", 80, 420, 1990, 200, C_CONTAINER_BLUE)
    d.add_box("Kênh sóng LoRa (433 MHz)", 140, 485, 560, 110, C_SKY)
    d.add_box("Gateway đa kênh (Raspberry Pi CM4)", 800, 485, 560, 110, C_SKY)
    d.add_box("Mạng kết nối IP (Ethernet / Wi-Fi)", 1460, 485, 560, 110, C_SKY)

    c3 = d.add_box("LỚP TRUNG GIAN (MIDDLEWARE LAYER)", 80, 720, 1990, 200, C_CONTAINER_PURP)
    d.add_box("Network Server (Điều phối khung truyền)", 140, 785, 560, 110, C_PURP)
    d.add_box("Message Broker (MQTT / REST API)", 800, 785, 560, 110, C_PURP)
    d.add_box("Cơ sở dữ liệu chuỗi thời gian", 1460, 785, 560, 110, C_PURP)

    c4 = d.add_box("LỚP ỨNG DỤNG (APPLICATION LAYER)", 80, 1020, 1990, 200, C_CONTAINER_AMBER)
    d.add_box("Ứng dụng giám sát thông minh", 140, 1085, 560, 110, C_AMBER)
    d.add_box("Web Dashboard thời gian thực", 800, 1085, 560, 110, C_AMBER)
    d.add_box("Hệ thống quản lý dữ liệu đo", 1460, 1085, 560, 110, C_AMBER)

    d.add_edge(c1, c2, "LoRa RF (433 MHz)", STYLE_EDGE_BLACK, exit_port=(0.5, 1), entry_port=(0.5, 0), label_offset=(20, 0))
    d.add_edge(c2, c3, "TCP/IP Socket", STYLE_EDGE_BLACK, exit_port=(0.5, 1), entry_port=(0.5, 0), label_offset=(20, 0))
    d.add_edge(c3, c4, "HTTP / WebSockets", STYLE_EDGE_BLACK, exit_port=(0.5, 1), entry_port=(0.5, 0), label_offset=(20, 0))

    d.save("01_kien_truc_iot_4_lop.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2: NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS
# ══════════════════════════════════════════════════════════════════════════
def build_fig02():
    d = DrawioBuilder("02_nguyen_ly_dieu_che_lora_css", 2300, 1250)
    d.add_title("NGUYÊN LÝ ĐIỀU CHẾ TRẢI PHỔ LORA CSS")

    # Hàng trên: 5 ô xử lý với giãn cách ngang 140px, nhãn nằm hoàn toàn phía trên đường mũi tên
    b1 = d.add_box("Dữ liệu nhị phân\n(Bitstream)", 100, 120, 300, 130, C_SLATE)
    b2 = d.add_box("Mã hóa Symbol\n(k = 0 .. 2^SF - 1)", 540, 120, 300, 130, C_SKY)
    b3 = d.add_box("Bộ tạo Chirp CSS\n(Quét tần số tuyến tính)", 980, 120, 300, 130, C_GREEN)
    b4 = d.add_box("Khuếch đại PA\n(+17 dBm)", 1420, 120, 300, 130, C_AMBER)
    b5 = d.add_box("Anten phát\n(433 MHz)", 1860, 120, 300, 130, C_ROSE)

    d.add_edge(b1, b2, "Nhóm SF bits", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(b2, b3, "Symbol k", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(b3, b4, "Chirp RF", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(b4, b5, "RF Power", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))

    # Khung dưới: giãn cách từ hàng trên = 120px
    d.add_box("ĐẶC TÍNH DẠNG SÓNG CHIRP TRÊN MIỀN TẦN SỐ - THỜI GIAN", 100, 370, 2060, 800, C_CONTAINER_BLUE)
    d.add_box("Trục tần số (f)\n\nf0 + BW/2\n\nf0 (433.x MHz)\n\nf0 - BW/2", 150, 450, 320, 680, C_SLATE)
    d.add_box("UP-CHIRP CƠ SỞ (PREAMBLE)\n\n• Quét tần số tuyến tính f_min -> f_max\n• Chu kỳ ký hiệu: Ts = 2^SF / BW\n• Dùng cho đồng bộ khung truyền", 580, 450, 730, 680, C_GREEN)
    d.add_box("CHIRP ĐIỀU CHẾ MANG TIN\n\n• Bước nhảy tần số mang giá trị Symbol k\n• Băng thông kênh: BW = 125 kHz\n• Hệ số trải phổ: SF = 7 .. 12", 1420, 450, 700, 680, C_SKY)

    d.save("02_nguyen_ly_dieu_che_lora_css.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3: KIẾN TRÚC MẠNG LORAWAN HÌNH SAO
# ══════════════════════════════════════════════════════════════════════════
def build_fig03():
    d = DrawioBuilder("03_kien_truc_mang_lorawan_star", 2300, 1200)
    d.add_title("KIẾN TRÚC MẠNG LORAWAN HÌNH SAO")

    # Giãn cách giữa 3 cột container lớn = 160px
    d.add_box("THIẾT BỊ ĐẦU CUỐI (END-NODES)", 80, 110, 520, 1020, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + Ra-02", 130, 200, 420, 220, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + Ra-02", 130, 500, 420, 220, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + Ra-02", 130, 800, 420, 220, C_GREEN)

    d.add_box("MULTI-CHANNEL GATEWAY", 760, 110, 720, 1020, C_CONTAINER_BLUE)
    gw = d.add_box("RASPBERRY PI CM4 GATEWAY\nBroadcom BCM2711 @ 1.5 GHz\n\n3x Module SX1278 (SPI0 Bus):\n• Kênh 1: 433.175 MHz\n• Kênh 2: 433.375 MHz\n• Kênh 3: 433.575 MHz\n\nThu song song đồng thời 3 kênh", 810, 200, 620, 820, C_SKY)

    d.add_box("MÁY CHỦ & GIAO DIỆN", 1640, 110, 580, 1020, C_CONTAINER_PURP)
    ns = d.add_box("Network Server\n• Điều phối khung truyền\n• Lọc gói tin trùng lặp", 1690, 250, 480, 300, C_PURP)
    as_srv = d.add_box("Application Server\n• Giải mã Payload gói tin\n• CSDL và Web Dashboard", 1690, 680, 480, 300, C_AMBER)

    # 3 mũi tên thẳng ngang song song từ 3 Node sang Gateway, hoàn toàn không chồng chéo hay cắt nhau
    d.add_edge(na, gw, "Kênh 1: 433.175 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.15), label_offset=(0, -18))
    d.add_edge(nb, gw, "Kênh 2: 433.375 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(nc, gw, "Kênh 3: 433.575 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.85), label_offset=(0, -18))

    # Mũi tên thẳng ngang từ Gateway sang Network Server
    d.add_edge(gw, ns, "TCP/IP Socket", STYLE_EDGE_BLACK, exit_port=(1, 0.25), entry_port=(0, 0.5), label_offset=(0, -18))
    # Mũi tên thẳng dọc từ Network Server xuống Application Server
    d.add_edge(ns, as_srv, "JSON Data", STYLE_EDGE_BLACK, exit_port=(0.5, 1), entry_port=(0.5, 0), label_offset=(20, 0))

    d.save("03_kien_truc_mang_lorawan_star.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4: SO SÁNH CLOUD AI VÀ EDGE TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig04():
    d = DrawioBuilder("04_so_sanh_cloud_ai_vs_edge_tinyml", 2200, 1350)
    d.add_title("SO SÁNH MÔ HÌNH XỬ LÝ: CLOUD AI VÀ EDGE TINYML")

    # Phần 1: Cloud AI
    d.add_box("1. MÔ HÌNH CLOUD AI TẬP TRUNG", 80, 110, 2040, 520, C_CONTAINER_AMBER)
    c1 = d.add_box("End-Node Cảm biến", 130, 200, 380, 140, C_SLATE)
    c2 = d.add_box("Gateway Chuyển tiếp", 610, 200, 380, 140, C_SLATE)
    c3 = d.add_box("Cloud Server AI", 1090, 200, 380, 140, C_AMBER)
    c4 = d.add_box("Gói tin Downlink", 1570, 200, 440, 140, C_ROSE)

    d.add_edge(c1, c2, "Uplink RF", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(c2, c3, "Internet", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(c3, c4, "Suy luận Cloud", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))

    # Mũi tên Downlink chạy vòng qua kênh rỗng phía dưới, tuyệt đối không xuyên qua các ô c2, c3
    d.add_edge(
        c4, c1, "Gói tin Downlink (Kênh mới)", STYLE_EDGE_RED,
        exit_port=(0.5, 1), entry_port=(0.5, 1),
        waypoints=[(1790, 410), (320, 410)],
        label_offset=(0, -18)
    )
    d.add_box("Luồng dữ liệu: CSI gửi lên Cloud -> Máy chủ suy luận -> Gửi cấu hình kênh về qua gói Downlink", 130, 480, 1940, 90, C_SLATE)

    # Giãn cách giữa 2 container lớn = 110px
    d.add_box("2. MÔ HÌNH EDGE TINYML TRÊN THIẾT BỊ BIÊN", 80, 740, 2040, 520, C_CONTAINER_GREEN)
    e1 = d.add_box("Bộ đệm CSI (10x9)", 130, 830, 380, 140, C_GREEN)
    e2 = d.add_box("Mô hình TinyML (ESP32)\nBộ nhớ: 8.65 KB Flash", 610, 830, 420, 140, C_GREEN)
    e3 = d.add_box("Lựa chọn kênh (ArgMax)\nThời gian: < 15 ms", 1130, 830, 380, 140, C_GREEN)
    e4 = d.add_box("Phát sóng LoRa\n(Kênh đã chọn)", 1610, 830, 400, 140, C_SKY)

    d.add_edge(e1, e2, "Dữ liệu 10x9", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(e2, e3, "Softmax", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(e3, e4, "Cấu hình tần số", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_box("Luồng dữ liệu: Suy luận và chọn kênh trực tiếp trên End-Node, hoàn toàn không cần gói tin Downlink", 130, 1080, 1940, 90, C_SLATE)

    d.save("04_so_sanh_cloud_ai_vs_edge_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 5: BÀI TOÁN LỰA CHỌN KÊNH TINYML (KIẾN TRÚC PHÂN TẦNG 3 LỚP)
# ══════════════════════════════════════════════════════════════════════════
def build_fig05():
    d = DrawioBuilder("05_bai_toan_lua_chon_kenh_tinyml", 2300, 1500)
    d.add_title("KHUNG KIẾN TRÚC BÀI TOÁN LỰA CHỌN KÊNH TINYML CHO LORAWAN")

    # Khung chú giải (Legend)
    d.add_box("CHÚ GIẢI LUỒNG TƯƠNG TÁC", 80, 110, 440, 320, C_CONTAINER_AMBER)
    d.add_box("Luồng dữ liệu vô tuyến & CSI\n(End-Node -> Gateway -> Server)", 110, 175, 380, 60, C_SLATE)
    d.add_box("Luồng nạp mô hình TinyML\n(Server -> Biên dịch -> Flash)", 110, 255, 380, 60, C_ROSE)
    d.add_box("Vòng lặp suy luận tự chủ\n(Thực thi nội bộ trên ESP32)", 110, 335, 380, 60, C_GREEN)

    # Tầng 1: Server
    d.add_box("TẦNG 1: MÁY CHỦ HUẤN LUYỆN NGOẠI TUYẾN (SERVER / WORKSTATION)", 600, 110, 1620, 320, C_CONTAINER_PURP)
    s_data = d.add_box("Nhật ký kênh (CSV Logs)\n• Chuỗi thời gian CSI (10x9)\n• Lịch sử RSSI, SNR, mất gói", 650, 180, 450, 150, C_PURP)
    s_train = d.add_box("TensorFlow / Keras Training\n• Tiền xử lý & StandardScaler\n• Huấn luyện 5 kiến trúc nơ-ron\n• 500 Epochs hội tụ chuẩn", 1190, 180, 460, 150, C_PURP)
    s_tflite = d.add_box("TFLite Converter & Exporter\n• Lượng tử hóa FlatBuffer\n• Sinh mã C Header model.h\n• Căn chỉnh alignas(16)", 1740, 180, 440, 150, C_ROSE)

    d.add_edge(s_data, s_train, "Tập dữ liệu", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(s_train, s_tflite, "Trọng số tối ưu", STYLE_EDGE_RED, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_box("Quy trình ngoại tuyến: Phân tích dữ liệu thực tế, tối ưu hóa trọng số và xuất mã nguồn C nhúng", 650, 360, 1530, 50, C_SLATE)

    # Tầng 2: Gateway (giãn cách từ Tầng 1 = 100px)
    d.add_box("TẦNG 2: TRẠM THU BIÊN ĐA KÊNH (MULTI-CHANNEL LORA GATEWAY - CM4)", 80, 530, 2140, 300, C_CONTAINER_BLUE)
    gw_db = d.add_box("CSDL Log & Data Dispatcher\n• Ghi nhật ký đo đạc CSV\n• Web Dashboard theo dõi\n• Stream dữ liệu sang Server", 140, 600, 600, 150, C_PURP)
    gw_mgr = d.add_box("Gateway Manager Daemon\n• Nhận ngắt DIO0 đa luồng\n• Bóc tách Header/Payload\n• Đọc thanh ghi đo RSSI, SNR", 830, 600, 620, 150, C_SKY)
    gw_rf = d.add_box("3x Module SX1278 (SPI0)\n• CH1: 433.175 MHz\n• CH2: 433.375 MHz\n• CH3: 433.575 MHz\nThu đồng thời 3 kênh", 1540, 600, 620, 150, C_SKY)

    d.add_edge(gw_rf, gw_mgr, "Tín hiệu RF", STYLE_EDGE_BLACK, exit_port=(0, 0.5), entry_port=(1, 0.5), label_offset=(0, -18))
    d.add_edge(gw_mgr, gw_db, "Metadata & CSI", STYLE_EDGE_BLACK, exit_port=(0, 0.5), entry_port=(1, 0.5), label_offset=(0, -18))
    # Stream dữ liệu từ Gateway lên Server qua luồng rỗng bên trái, tuyệt đối không xuyên qua ô nào
    d.add_edge(
        gw_db, s_data, "CSV Stream qua TCP/IP", STYLE_EDGE_BLACK,
        exit_port=(0.5, 0), entry_port=(0.5, 1),
        waypoints=[(440, 460), (875, 460)],
        label_offset=(0, -18)
    )
    d.add_box("Vai trò trạm thu: Tiếp nhận gói tin từ mọi kênh, bóc tách chỉ số truyền thông và truyền về máy chủ phân tích", 140, 775, 2020, 40, C_SLATE)

    # Tầng 3: End-Node (giãn cách từ Tầng 2 = 100px)
    d.add_box("TẦNG 3: THIẾT BỊ ĐẦU CUỐI IOT BIÊN (EDGE TINYML END-NODE - ESP32)", 80, 930, 2140, 500, C_CONTAINER_GREEN)
    node_mgr = d.add_box("Khối Quản Lý Dữ Liệu (Manager)\n• Cảm biến môi trường (Telemetry)\n• Bộ đệm trượt FIFO (10 bước x 9 đặc trưng)\n• Chuẩn hóa Z-Score O(1) theo SCALER tĩnh\n• Khóa Mutex đồng bộ FreeRTOS", 140, 1000, 600, 280, C_GREEN)
    node_ml = d.add_box("Nhân Suy Luận Biên (TFLM Engine)\n• Mảng FlatBuffer model.h trong Flash\n• Vùng đệm Tensor Arena (10 KB RAM tĩnh)\n• Bộ tính toán mạng nơ-ron (Forward Pass)\n• Quyết định kênh tối ưu: k = ArgMax", 830, 1000, 620, 280, C_GREEN)
    node_rf = d.add_box("Khối Truyền Thông Vô Tuyến\n• Module LoRa SX1278 (Ra-02)\n• Tự động chỉnh tần số sang kênh k\n• Khuếch đại công suất (+17 dBm)\n• Kích hoạt phát gói tin Uplink", 1540, 1000, 620, 280, C_SKY)

    d.add_edge(node_mgr, node_ml, "Vector đặc trưng (90)", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(node_ml, node_rf, "Chỉ số kênh k", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))

    # Gói tin Uplink truyền thẳng từ End-Node lên Gateway trên cùng cột bên phải, hoàn toàn thẳng hàng và thoáng đãng
    d.add_edge(node_rf, gw_rf, "Gói tin LoRa Uplink (RF 433 MHz)", STYLE_EDGE_BLACK, exit_port=(0.5, 0), entry_port=(0.5, 1), label_offset=(20, 0))

    # Luồng nạp model.h từ TFLite Exporter xuống End-Node chạy vòng ngoài cùng bên phải, không xuyên qua Gateway
    d.add_edge(
        s_tflite, node_ml, "Nạp mã nguồn C header model.h vào Flash", STYLE_EDGE_RED,
        exit_port=(1, 0.5), entry_port=(0.5, 0),
        waypoints=[(2240, 255), (2240, 870), (1140, 870)],
        label_offset=(0, -18)
    )

    d.add_box("Đặc tính tự chủ: End-Node tự động dự đoán và chuyển kênh cục bộ trong < 15 ms, hoàn toàn không cần gói tin Downlink từ Gateway", 140, 1350, 2020, 65, C_SLATE)

    d.save("05_bai_toan_lua_chon_kenh_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 6: SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig06():
    d = DrawioBuilder("06_so_do_khoi_toan_he_thong", 2300, 1250)
    d.add_title("SƠ ĐỒ KHỐI TOÀN HỆ THỐNG THỰC NGHIỆM LORA TINYML")

    # 3 cột container với giãn cách ngang 160px
    d.add_box("PHÂN HỆ TRẠM PHÁT (03 END-NODES)", 80, 110, 520, 1050, C_CONTAINER_GREEN)
    na = d.add_box("Node A (Tầng 1)\nESP32 + SX1278", 130, 200, 420, 190, C_GREEN)
    nb = d.add_box("Node B (Tầng 2)\nESP32 + SX1278", 130, 490, 420, 190, C_GREEN)
    nc = d.add_box("Node C (Ngoài trời)\nESP32 + SX1278", 130, 780, 420, 190, C_GREEN)

    d.add_box("KÊNH TRUYỀN VÔ TUYẾN 433 MHz", 760, 110, 540, 1050, C_CONTAINER_AMBER)
    ch1 = d.add_box("Kênh 1: 433.175 MHz (BW 125 kHz)", 810, 220, 440, 150, C_AMBER)
    ch2 = d.add_box("Kênh 2: 433.375 MHz (BW 125 kHz)", 810, 480, 440, 150, C_AMBER)
    ch3 = d.add_box("Kênh 3: 433.575 MHz (BW 125 kHz)", 810, 740, 440, 150, C_AMBER)
    d.add_box("Khoảng cách kênh: 200 kHz", 810, 960, 440, 70, C_SLATE)

    d.add_box("PHÂN HỆ TRẠM THU (GATEWAY CM4)", 1460, 110, 760, 1050, C_CONTAINER_BLUE)
    rx_mod = d.add_box("3x Module SX1278 (SPI0 Bus)\nThu đồng thời 3 kênh", 1510, 190, 660, 160, C_SKY)
    d.add_box("Raspberry Pi CM4\n3 luồng Worker xử lý ngắt DIO0", 1510, 410, 660, 160, C_SKY)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 1510, 630, 660, 160, C_PURP)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 1510, 850, 660, 160, C_AMBER)

    # 3 đường nối ngang thẳng từ Node sang Kênh tương ứng
    d.add_edge(na, ch1, "RF 433 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(nb, ch2, "RF 433 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(nc, ch3, "RF 433 MHz", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))

    # Từ Kênh thu vào trạm thu
    d.add_edge(ch1, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.3), label_offset=(0, -18))
    d.add_edge(ch2, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(ch3, rx_mod, "Thu tín hiệu", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.7), label_offset=(0, -18))

    d.save("06_so_do_khoi_toan_he_thong.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 7: ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA
# ══════════════════════════════════════════════════════════════════════════
def build_fig07():
    d = DrawioBuilder("07_dinh_dang_khung_truyen_goi_tin", 2200, 880)
    d.add_title("CẤU TRÚC ĐỊNH DẠNG KHUNG TRUYỀN GÓI TIN LORA")

    # Hàng tiêu đề phân loại lớn: giãn cách ngang 50px
    d.add_box("HEADER (4 Bytes)", 80, 110, 680, 70, C_TITLE_BLUE)
    d.add_box("METADATA (5 Bytes)", 820, 110, 460, 70, C_TITLE_PURP)
    d.add_box("PAYLOAD (Biến thiên)", 1340, 110, 540, 70, C_TITLE_AMBER)
    d.add_box("CRC (2 Bytes)", 1940, 110, 180, 70, C_TITLE_ROSE)

    # Hàng trường dữ liệu chi tiết: giãn cách ngang 40px, giãn cách từ hàng trên = 60px
    d.add_box("Node_ID\n(1 Byte)\n'A', 'B', 'C'", 80, 240, 190, 180, C_SKY)
    d.add_box("Packet_ID\n(2 Bytes)\n0 - 65,535", 310, 240, 220, 180, C_SKY)
    d.add_box("Current_CH\n(1 Byte)\n0, 1, 2", 570, 240, 190, 180, C_SKY)
    d.add_box("Payload_Size\n(1 Byte)\n30 - 250 B", 820, 240, 200, 180, C_PURP)
    d.add_box("Timestamp\n(4 Bytes)\nmillis()", 1060, 240, 220, 180, C_PURP)
    d.add_box("Payload Data\n(21 - 241 Bytes)\nBộ đệm dữ liệu", 1340, 240, 540, 180, C_AMBER)
    d.add_box("CRC\n(2 Bytes)\nHardware", 1940, 240, 180, 180, C_ROSE)

    # Khung chú thích dưới: giãn cách dọc 80px và 40px
    d.add_box("Các mức kích thước gói tin khảo sát: 30B, 74B, 118B, 162B, 206B, 250B", 80, 500, 2040, 95, C_SLATE)
    d.add_box("Trích xuất tại trạm thu: Bóc tách gói tin và đọc thanh ghi phần cứng SX1278 (RSSI, SNR)", 80, 635, 2040, 95, C_SLATE)

    d.save("07_dinh_dang_khung_truyen_goi_tin.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 8: 5 KIẾN TRÚC MẠNG NƠ-RON TINYML
# ══════════════════════════════════════════════════════════════════════════
def build_fig08():
    d = DrawioBuilder("08_5_kien_truc_tinyml", 2350, 1200)
    d.add_title("CẤU TRÚC 5 KIẾN TRÚC MẠNG NƠ-RON KHẢO SÁT")

    # Giãn cách giữa 5 card = 100px (cực kỳ thông thoáng)
    w_card = 350
    gap = 100
    x_start = 100

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

    # Giãn cách từ thân card đến hộp tổng quan = 70px
    d.add_box("Cấu trúc lớp mạng và số lượng tham số của 5 mô hình nơ-ron đánh giá trên vi điều khiển ESP32", x_start, 1050, 2150, 95, C_SLATE)

    d.save("08_5_kien_truc_tinyml.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 9: QUY TRÌNH XỬ LÝ DỮ LIỆU THỰC NGHIỆM
# ══════════════════════════════════════════════════════════════════════════
def build_fig09():
    d = DrawioBuilder("09_pipeline_xu_ly_du_lieu", 2300, 1200)
    d.add_title("QUY TRÌNH XỬ LÝ & CHUẨN HÓA DỮ LIỆU THỰC NGHIỆM")

    # 4 bước ngang với giãn cách 120px
    p1 = d.add_box("Bước 1: Trích xuất log\n• Thu thập dữ liệu Gateway\n• Tách theo Node (A, B, C)\n• Lọc các bản tin hợp lệ", 130, 110, 420, 210, C_CONTAINER_BLUE)
    p2 = d.add_box("Bước 2: Xử lý gói mất\n• Quét số thứ tự Packet_ID\n• Bổ sung các gói bị mất\n• Gán nhãn phạt: RSSI, SNR", 670, 110, 420, 210, C_CONTAINER_PURP)
    p3 = d.add_box("Bước 3: Chuỗi trượt\n• Tensor (10 bước x 9 feat)\n• Gán nhãn kênh mục tiêu\n• Loại bỏ trường rò rỉ nhãn", 1210, 110, 420, 210, C_CONTAINER_AMBER)
    p4 = d.add_box("Bước 4: Chuẩn hóa & Chia\n• StandardScaler: z=(x-μ)/σ\n• Xuất bảng SCALER cho C\n• Chia: 60% / 20% / 20%", 1750, 110, 420, 210, C_CONTAINER_GREEN)

    d.add_edge(p1, p2, "Dữ liệu thô", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(p2, p3, "Dữ liệu đầy đủ", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(p3, p4, "Chuỗi trượt", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))

    # Giãn cách từ hàng trên đến container đầu ra = 130px
    d.add_box("ĐẦU RA QUY TRÌNH DỮ LIỆU", 130, 450, 2040, 670, C_CONTAINER_GREEN)
    d.add_box("dataset_ready.csv\n19,440 mẫu chuỗi thời gian\n90 đặc trưng đầu vào", 180, 540, 580, 220, C_GREEN)
    d.add_box("Phân chia tập mẫu\nTrain: 11,664 (60%)\nVal: 3,888 (20%) | Test: 3,888 (20%)", 860, 540, 580, 220, C_SKY)
    d.add_box("Mảng tham số nhúng C\nSCALER_MEAN[9] & SCALER_SCALE[9]\nĐồng bộ trong model.h", 1540, 540, 580, 220, C_AMBER)

    d.add_box("Đặc điểm kỹ thuật: Dữ liệu đồng nhất 3 kênh tần số, chuẩn hóa trực tiếp trên thiết bị với độ phức tạp O(1)", 180, 830, 1940, 95, C_SLATE)

    d.save("09_pipeline_xu_ly_du_lieu.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 10: SƠ ĐỒ BỐ TRÍ THỰC ĐỊA TRONG TÒA NHÀ
# ══════════════════════════════════════════════════════════════════════════
def build_fig10():
    d = DrawioBuilder("10_bo_tri_thuc_dia_toa_nha", 2300, 1250)
    d.add_title("SƠ ĐỒ BỐ TRÍ THỰC NGHIỆM KHÔNG GIAN")

    # Giãn cách ngang giữa Trong Nhà và Ngoài Trời = 160px
    d.add_box("KHÔNG GIAN TRONG NHÀ", 80, 110, 1420, 1040, C_CONTAINER_BLUE)
    d.add_box("TẦNG 2: PHÒNG THÍ NGHIỆM VÀ HÀNH LANG", 120, 190, 1340, 380, C_SLATE)
    gw = d.add_box("GATEWAY CM4\nRaspberry Pi CM4 + 3x SX1278\nVị trí trung tâm", 150, 270, 550, 230, C_SKY)
    nb = d.add_box("NODE B (TẦNG 2)\nCự ly 60m\n(Xuyên sàn bê tông)", 850, 270, 550, 230, C_AMBER)

    d.add_box("TẦNG 1: SẢNH VÀ PHÒNG HỌC", 120, 670, 1340, 420, C_SLATE)
    na = d.add_box("NODE A (TẦNG 1)\nCự ly 25m\n(Xuyên vách ngăn kính)", 150, 760, 550, 240, C_GREEN)

    # Ngoài trời
    d.add_box("KHÔNG GIAN NGOÀI TRỜI", 1660, 110, 560, 1040, C_CONTAINER_GREEN)
    nc = d.add_box("NODE C (SÂN TRƯỜNG)\nCự ly 110m\nMôi trường ngoài trời", 1720, 460, 440, 340, C_ROSE)

    # Các đường nối chạy trên khoảng trống thoáng
    d.add_edge(na, gw, "25m (Trong nhà)", STYLE_EDGE_GREEN, exit_port=(0.5, 0), entry_port=(0.5, 1), label_offset=(20, 0))
    d.add_edge(nb, gw, "60m (Xuyên tầng)", STYLE_EDGE_BLACK, exit_port=(0, 0.5), entry_port=(1, 0.5), label_offset=(0, -18))
    d.add_edge(
        nc, gw, "110m (Ngoài trời)", STYLE_EDGE_RED,
        exit_port=(0, 0.5), entry_port=(1, 0.5),
        waypoints=[(1560, 630), (1560, 385)],
        label_offset=(0, -18)
    )

    d.save("10_bo_tri_thuc_dia_toa_nha.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 11: KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS
# ══════════════════════════════════════════════════════════════════════════
def build_fig11():
    d = DrawioBuilder("11_kien_truc_freertos_da_nhiem", 2300, 1250)
    d.add_title("KIẾN TRÚC FIRMWARE ĐA NHIỆM FREERTOS TRÊN ESP32")

    # Giãn cách ngang giữa Core 0 và Core 1 = 220px
    d.add_box("CORE 0: THU THẬP & HIỂN THỊ", 80, 110, 960, 1050, C_CONTAINER_BLUE)
    t_samp = d.add_box("Task_Sampler (Ưu tiên 1)\nĐọc cảm biến -> Cập nhật bộ đệm trượt 10x9", 140, 210, 840, 210, C_SKY)
    d.add_box("Task_OLED (Ưu tiên 1)\nQuét bus I2C -> Hiển thị trạng thái kênh, RSSI, SNR", 140, 510, 840, 210, C_SKY)
    mutex = d.add_box("historyMutex\nKhóa bảo vệ truy cập bộ đệm trượt 10x9", 140, 810, 840, 210, C_AMBER)

    d.add_box("CORE 1: SUY LUẬN AI & TRUYỀN SÓNG RF", 1260, 110, 960, 1050, C_CONTAINER_GREEN)
    t_ml = d.add_box("Task_TinyML (Ưu tiên 2)\nZ-Score -> Suy luận TFLM -> ArgMax chọn kênh", 1320, 210, 840, 210, C_GREEN)
    t_tx = d.add_box("Task_LoRaTX (Ưu tiên 3)\nCấu hình tần số -> Phát sóng RF (+17 dBm)", 1320, 510, 840, 210, C_GREEN)
    queue = d.add_box("channelQueue (Độ dài 1)\nHàng đợi truyền mã kênh sang Task TX", 1320, 810, 840, 210, C_PURP)

    # Đường nối tránh tuyệt đối đi xuyên qua Task_OLED
    d.add_edge(
        t_samp, mutex, "Ghi dữ liệu", STYLE_EDGE_BLACK,
        exit_port=(0, 0.5), entry_port=(0, 0.5),
        waypoints=[(110, 315), (110, 915)],
        label_offset=(-18, 0)
    )
    # Đường nối qua Core 1 trong khoảng không gian giữa 2 lõi
    d.add_edge(
        mutex, t_ml, "Đọc bộ đệm", STYLE_EDGE_GREEN,
        exit_port=(1, 0.5), entry_port=(0, 0.5),
        waypoints=[(1110, 915), (1110, 315)],
        label_offset=(0, -18)
    )
    # Đường nối tránh tuyệt đối đi xuyên qua Task_LoRaTX
    d.add_edge(
        t_ml, queue, "Gửi mã kênh", STYLE_EDGE_GREEN,
        exit_port=(1, 0.5), entry_port=(1, 0.5),
        waypoints=[(2190, 315), (2190, 915)],
        label_offset=(18, 0)
    )
    d.add_edge(queue, t_tx, "Nhận mã kênh", STYLE_EDGE_GREEN, exit_port=(0.5, 0), entry_port=(0.5, 1), label_offset=(20, 0))

    d.save("11_kien_truc_freertos_da_nhiem.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 12: SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32
# ══════════════════════════════════════════════════════════════════════════
def build_fig12():
    d = DrawioBuilder("12_so_do_noi_chan_end_node_esp32", 2300, 1250)
    d.add_title("SƠ ĐỒ ĐẤU NỐI PHẦN CỨNG END-NODE ESP32")

    # Giãn cách ngang giữa 3 khối linh kiện chính = 180px
    rf = d.add_box("MODULE LORA SX1278 (RA-02)\n• MOSI: GPIO 27\n• MISO: GPIO 19\n• SCK:  GPIO 18\n• NSS:  GPIO 5 (CS)\n• RST:  GPIO 14\n• DIO0: GPIO 26 (TxDone)\n• Nguồn: 3.3V, GND", 100, 120, 580, 760, C_CONTAINER_GREEN)
    mcu = d.add_box("ESP32 DEVKIT V1\nDual-Core 240 MHz\nSRAM 520 KB | Flash 4 MB", 860, 120, 580, 760, C_CONTAINER_BLUE)
    oled = d.add_box("MÀN HÌNH OLED SSD1306\n• SDA: GPIO 21\n• SCL: GPIO 22\n• Nguồn: 3.3V, GND\n\nGiao tiếp bus I2C", 1620, 120, 580, 760, C_CONTAINER_PURP)

    # Giãn cách dọc đến khối nguồn = 120px
    pwr = d.add_box("MẠCH NGUỒN CẤP ĐIỆN\nTụ bù chống sụt áp (100 µF + 100 nF mắc song song đường nguồn 3.3V)", 350, 1000, 1600, 140, C_AMBER)

    d.add_edge(rf, mcu, "Bus VSPI & DIO0", STYLE_EDGE_GREEN, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(mcu, oled, "Bus I2C", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(pwr, mcu, "3.3V DC", STYLE_EDGE_BLACK, exit_port=(0.5, 0), entry_port=(0.5, 1), label_offset=(20, 0))

    d.save("12_so_do_noi_chan_end_node_esp32.drawio")
    return d


# ══════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 13: SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY CM4
# ══════════════════════════════════════════════════════════════════════════
def build_fig13():
    d = DrawioBuilder("13_so_do_noi_chan_gateway_cm4", 2350, 1350)
    d.add_title("SƠ ĐỒ ĐẤU NỐI MULTI-RECEIVER GATEWAY RASPBERRY PI CM4")

    # Giãn cách ngang giữa 3 cột = 180px
    m1 = d.add_box("MODULE THU #1 (CH1 - 433.175 MHz)\nCE: GPIO 8 (CE0) | DIO0: GPIO 24", 80, 120, 560, 220, C_SKY)
    m2 = d.add_box("MODULE THU #2 (CH2 - 433.375 MHz)\nCE: GPIO 7 (CE1) | DIO0: GPIO 23", 80, 420, 560, 220, C_GREEN)
    m3 = d.add_box("MODULE THU #3 (CH3 - 433.575 MHz)\nCE: GPIO 25 (CS2) | DIO0: GPIO 22", 80, 720, 560, 220, C_AMBER)
    d.add_box("Đường SPI0 chung: MOSI=Pin 19, MISO=Pin 21, SCLK=Pin 23", 80, 1020, 560, 140, C_SLATE)

    cm4 = d.add_box("RASPBERRY PI CM4\nQuad-Core Cortex-A72 @ 1.5 GHz\n40-Pin GPIO Header | Linux OS", 820, 120, 680, 1040, C_CONTAINER_BLUE)

    d.add_box("TIẾN TRÌNH PHẦN MỀM GATEWAY", 1680, 120, 590, 1040, C_CONTAINER_PURP)
    d.add_box("3 luồng Worker nhận ngắt DIO0\nThu đồng thời 3 kênh", 1730, 220, 490, 220, C_PURP)
    d.add_box("Cơ sở dữ liệu log CSV\nLưu trữ Timestamp, RSSI, SNR", 1730, 530, 490, 220, C_SLATE)
    d.add_box("Web Dashboard giám sát\nHiển thị dữ liệu thu nhận", 1730, 840, 490, 220, C_AMBER)

    # 3 mũi tên thẳng song song sang CM4, nhãn nằm hoàn toàn phía trên đường nối
    d.add_edge(m1, cm4, "SPI0 CE0", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.2), label_offset=(0, -18))
    d.add_edge(m2, cm4, "SPI0 CE1", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.5), label_offset=(0, -18))
    d.add_edge(m3, cm4, "SPI0 CS2", STYLE_EDGE_BLACK, exit_port=(1, 0.5), entry_port=(0, 0.8), label_offset=(0, -18))

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
    print(" KHỞI TẠO BỘ SƠ ĐỒ ĐỒ HỌA (.DRAWIO) HOÀN THIỆN ĐỊNH TUYẾN & GIÃN CÁCH")
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
