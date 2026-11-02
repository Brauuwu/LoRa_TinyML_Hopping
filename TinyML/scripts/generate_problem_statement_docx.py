#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_docx_problem_statement.py
Tạo file Word (.docx) chuyên nghiệp: Phát biểu bài toán & Mô hình hóa toán học
Đề tài: Tối ưu hóa kênh truyền LoRa dựa trên TinyML (LoRa TinyML Channel Hopping)
"""

import os
import sys
import docx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Đặt màu nền cho ô trong bảng"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Đặt padding cho ô trong bảng (đơn vị dxa, 1 pt = 20 dxa)"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    """Đặt đường viền thanh lịch cho bảng"""
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout_box(doc, text, title=None):
    """Tạo hộp ghi chú chuyên nghiệp (Callout box) với viền trái xanh đậm"""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F0F4F8")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Border: chỉ có viền trái dày 36 dxa (~2.5pt)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="1B365D"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if title:
        run_t = p.add_run(f"{title}\n")
        run_t.font.name = "Times New Roman"
        run_t.font.size = Pt(11)
        run_t.font.bold = True
        run_t.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        
    run_b = p.add_run(text)
    run_b.font.name = "Times New Roman"
    run_b.font.size = Pt(10.5)
    run_b.font.italic = True
    run_b.font.color.rgb = RGBColor(0x2B, 0x3E, 0x50)

def build_document():
    doc = Document()
    
    # ── Đặt lề trang chuẩn (Top: 2cm, Bottom: 2cm, Left: 2.5cm, Right: 2cm)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(0.8)
        
        # Header / Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Báo Cáo Phát Biểu Bài Toán — LoRa TinyML Channel Hopping")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Trang ")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(9)
        frun.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)
        # Thêm field page number
        fldSimple = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
        fp._p.append(fldSimple)

    # ── Thiết lập Style mặc định
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)

    # Helper format paragraph
    def add_p(text, before=2, after=4, line_spacing=1.2, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, color=(0x1A, 0x1A, 0x1A)):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = line_spacing
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(*color)
        return p

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Navy Dark Blue
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2C, 0x5E, 0x8A) # Slate Blue
        return p

    def add_math_block(formula_text, desc=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(formula_text)
        run.font.name = "Cambria Math"
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x11, 0x22, 0x33)
        if desc:
            p2 = doc.add_paragraph()
            p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p2.paragraph_format.space_before = Pt(0)
            p2.paragraph_format.space_after = Pt(6)
            run2 = p2.add_run(desc)
            run2.font.name = "Times New Roman"
            run2.font.size = Pt(11)
            run2.font.italic = True
            run2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # ═══════════════════════════════════════════════════════════════════════════
    # BÌA / TIÊU ĐỀ BÁO CÁO
    # ═══════════════════════════════════════════════════════════════════════════
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(2)
    r_meta = p_meta.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO — TRƯỜNG ĐẠI HỌC KỸ THUẬT\nKHOA ĐIỆN TỬ VIỄN THÔNG / CÔNG NGHỆ THÔNG TIN")
    r_meta.font.name = "Times New Roman"
    r_meta.font.size = Pt(11)
    r_meta.font.bold = True
    r_meta.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_div.paragraph_format.space_before = Pt(0)
    p_div.paragraph_format.space_after = Pt(14)
    r_div = p_div.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    r_div.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("BÁO CÁO PHÁT BIỂU BÀI TOÁN\nVÀ MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run("Đề tài: Tối Ưu Hóa Kênh Truyền LoRa Dựa Trên Học Máy Siêu Nhẹ (TinyML Channel Hopping)\nHệ thống Nhảy Kênh Thông Minh Thời Gian Thực Trên Vi Điều Khiển ESP32")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(0x2C, 0x5E, 0x8A)

    add_callout_box(doc, 
        "Tóm tắt định hướng: Tài liệu này cung cấp cơ sở khoa học, công thức toán học và phát biểu hình thức hóa (Formal Problem Formulation) cho bài toán tối ưu hóa kênh truyền mạng LoRa. Hệ thống kết hợp lý thuyết truyền thông vô tuyến, mô hình suy hao kênh truyền, cơ chế giải quyết xung đột ALOHA và mô hình mạng nơ-ron học máy nhúng (TinyML) chạy trực tiếp tại biên trên vi điều khiển ESP32.",
        "MỤC TIÊU VĂN BẢN")

    # ═══════════════════════════════════════════════════════════════════════════
    # PHẦN 1: BỐI CẢNH VÀ BẢN CHẤT VẤN ĐỀ KỸ THUẬT
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1("1. BỐI CẢNH THỰC TIỄN VÀ BẢN CHẤT VẤN ĐỀ KỸ THUẬT")

    add_p("Trong kỷ nguyên Internet Vạn Vật (IoT), công nghệ mạng diện rộng công suất thấp (LPWAN - Low-Power Wide-Area Network), đặc biệt là kỹ thuật điều chế trải phổ LoRa (Long Range), đã trở thành chuẩn kết nối vượt trội nhờ khả năng phủ sóng cự ly từ vài kilomet đến hàng chục kilomet với mức tiêu thụ năng lượng cực thấp. Tuy nhiên, khi mật độ các thiết bị đầu cuối (End-Nodes) gia tăng nhanh chóng trong cùng một khu vực địa lý, mạng LoRa phải đối mặt với những thách thức nghiêm trọng về hiệu năng truyền thông:")

    add_p("1. Cơ chế truy cập kênh Pure ALOHA mặc định: Theo chuẩn LoRa và LoRaWAN lớp A, thiết bị đầu cuối hoạt động theo nguyên lý Pure ALOHA: bất cứ khi nào có dữ liệu cảm biến, node sẽ lập tức phát sóng mà không có cơ chế lắng nghe trước kênh truyền (Listen-Before-Talk - LBT thường không khả thi hoặc kém hiệu quả do độ nhạy thu của LoRa nằm sâu dưới mức nhiễu nền).")

    add_p("2. Thời gian phát sóng trên không (Time-on-Air - ToA) kéo dài: Đặc thù của kỹ thuật trải phổ Chirp Spread Spectrum (CSS) là tốc độ truyền dữ liệu thấp (vài trăm bps đến vài kbps). Khi kích thước tải trọng (Payload) tăng từ 30 Bytes lên 250 Bytes, thời gian phát sóng của một gói tin kéo dài từ vài chục mili-giây lên gần 400 mili-giây.")

    add_p("3. Bùng nổ xác suất va chạm xung đột (Packet Collision): Khi hai hoặc nhiều nút cùng truyền đồng thời trên cùng một kênh tần số, sóng điện từ bị giao thoa triệt tiêu lẫn nhau trên không (destructive interference). Hệ quả là trạm thu Gateway không thể giải mã được khung truyền, dẫn đến rớt gói tin hàng loạt, làm suy sụt nghiêm trọng Tỷ lệ nhận gói thành công (PDR - Packet Delivery Ratio).")

    add_heading_2("1.1. Hạn chế của Kênh Cố Định (Fixed Channel)")
    add_p("Trong kiến trúc truyền thống, mỗi thiết bị thường được cấu hình cố định phát trên một kênh tần số vật lý xác định. Khi kênh tần số này xuất hiện can nhiễu cục bộ, suy hao sâu (deep fading) hoặc có nhiều node xung quanh cùng truyền dữ liệu lớn, toàn bộ đường truyền bị tê liệt hoàn toàn, tỷ lệ PDR sụt giảm tiệm cận 0% mà thiết bị không có cơ chế tự thích ứng né tránh.")

    add_heading_2("1.2. Hạn chế của Nhảy Kênh Ngẫu Nhiên (Random Channel Hopping)")
    add_p("Để giải quyết bài toán kênh cố định, giải pháp sơ khai thường áp dụng là nhảy kênh ngẫu nhiên giả lập (Pseudo-Random Channel Hopping). Tuy nhiên, cơ chế này mang tính mù quáng (collision-blind) do hoàn toàn không có nhận thức về trạng thái kênh vô tuyến:")
    add_p("• Các node độc lập có thể ngẫu nhiên chọn trùng một kênh tần số tại cùng một thời điểm, tiếp tục gây ra xung đột đối đầu.")
    add_p("• Node có thể nhảy vào một kênh đang bị can nhiễu môi trường nặng hoặc suy hao công suất nghiêm trọng.")
    add_p("• Thực nghiệm cho thấy: khi kích thước gói tin tăng lên 250 Bytes, cơ chế Random Hopping bị sụt đổ tỷ lệ nhận gói PDR chỉ còn 63.7%.")

    # ═══════════════════════════════════════════════════════════════════════════
    # PHẦN 2: MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG VÔ TUYẾN
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1("2. MÔ HÌNH HÓA TOÁN HỌC HỆ THỐNG VÔ TUYẾN")

    add_heading_2("2.1. Mô hình Mạng và Không Gian Tần Số")
    add_p("Xét hệ thống mạng cảm biến không dây gồm tập hợp N thiết bị đầu cuối End-Node và một trạm thu thập trung tâm Multi-Channel Gateway:")
    add_math_block("N = {Node_1, Node_2, ..., Node_N},  với N = 3 (Node A, Node B, Node C)")
    add_p("Hệ thống hoạt động trên dải tần số 433 MHz ISM với tập hợp K kênh tần số trực giao độc lập:")
    add_math_block("C = {c_1, c_2, ..., c_K},  với K = 3 kênh vật lý")
    add_p("Các kênh được phân bổ với khoảng cách bảo vệ (guard band) Δf = 200 kHz nhằm triệt tiêu can nhiễu kênh lân cận (Adjacent Channel Interference - ACI):")
    add_p("• Kênh 1 (c_1): f_1 = 433.175 MHz")
    add_p("• Kênh 2 (c_2): f_2 = 433.375 MHz")
    add_p("• Kênh 3 (c_3): f_3 = 433.575 MHz")

    add_heading_2("2.2. Mô hình Tính Toán Thời Gian Phát Trên Không (Time-on-Air - ToA)")
    add_p("Thời gian chiếm dụng kênh vô tuyến ToA của một gói tin LoRa phụ thuộc vào cấu hình lớp vật lý: Băng thông (BW = 125 kHz), Hệ số trải phổ (SF = 7), Tốc độ mã hóa (CR = 4/5), Chiều dài mào đầu (N_pre = 8 symbols) và Kích thước tải trọng (PL bytes).")
    
    add_p("Thời gian kéo dài của một symbol chirp:")
    add_math_block("T_sym = 2^SF / BW = 2^7 / 125,000 = 128 / 125,000 = 1.024 ms")

    add_p("Thời gian phát chuỗi đồng bộ Preamble:")
    add_math_block("T_preamble = (N_pre + 4.25) * T_sym = (8 + 4.25) * 1.024 ms = 12.544 ms")

    add_p("Số lượng biểu tượng của phần tải trọng dữ liệu (N_payload):")
    add_math_block("N_payload = 8 + max( ceil( (8*PL - 4*SF + 28 + 16*CRC - 20*IH) / (4*(SF - 2*DE)) ) * (CR + 4), 0 )")
    add_p("Trong đó: CRC = 1 (bật kiểm tra lỗi), IH = 0 (Explicit Header), DE = 0 (tắt Low Data Rate Optimization khi SF=7), CR = 1 (tương ứng Coding Rate 4/5).")

    add_p("Tổng thời gian trên không ToA:")
    add_math_block("ToA = T_preamble + N_payload * T_sym")

    # Bảng ToA
    table_toa = doc.add_table(rows=7, cols=5)
    table_toa.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_toa)
    
    headers_toa = ["Kích thước Payload (PL)", "Số Symbol Payload", "ToA Lý Thuyết (ms)", "Cửa Sổ Xung Đột (2*ToA)", "Tỷ Lệ Mở Rộng ToA"]
    for i, h in enumerate(headers_toa):
        cell = table_toa.cell(0, i)
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=120, bottom=120, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_toa = [
        ["30 Bytes", "53 symbols", "66.82 ms", "133.64 ms", "1.00x (Gốc)"],
        ["74 Bytes", "128 symbols", "143.62 ms", "287.24 ms", "2.15x"],
        ["118 Bytes", "203 symbols", "220.42 ms", "440.84 ms", "3.30x"],
        ["162 Bytes", "278 symbols", "297.22 ms", "594.44 ms", "4.45x"],
        ["206 Bytes", "353 symbols", "374.02 ms", "748.04 ms", "5.60x"],
        ["250 Bytes", "428 symbols", "450.82 ms", "901.64 ms", "6.75x (Cực đại)"],
    ]

    for row_idx, row_data in enumerate(data_toa):
        for col_idx, text in enumerate(row_data):
            cell = table_toa.cell(row_idx + 1, col_idx)
            if row_idx % 2 == 1:
                set_cell_background(cell, "F9FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            if col_idx == 4 and "6.75x" in text:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    add_p("\nNhận xét định lượng: Khi kích thước gói tin tăng từ 30B lên 250B, cửa sổ thời gian xung đột (Vulnerable Window) nở rộng gấp 6.75 lần (từ 133 ms lên tới hơn 900 ms), lý giải tại sao mạng ALOHA thuần túy bị suy giảm PDR nghiêm trọng ở các gói tin kích thước lớn.")

    add_heading_2("2.3. Xác Suất Va Chạm Xung Đột Theo Pure ALOHA")
    add_p("Trong giao thức Pure ALOHA, giả sử quá trình phát sinh gói tin của toàn mạng tuân theo phân phối Poisson với tốc độ λ (gói/giây). Tải lượng mạng chuẩn hóa G được định nghĩa:")
    add_math_block("G = N * lambda * ToA")
    add_p("Cửa sổ thời gian dễ bị tổn thương (Vulnerable Period) bằng hai lần thời gian truyền: V = 2 * ToA. Do đó, xác suất truyền thành công không bị va chạm sóng:")
    add_math_block("P_succ = e^(-2 * G) = e^(-2 * N * lambda * ToA)")
    add_p("Xác suất va chạm gói tin:")
    add_math_block("P_collision = 1 - P_succ = 1 - e^(-2 * N * lambda * ToA)")
    add_p("Hệ quả toán học: Khi kích thước payload tăng (ToA tăng) hoặc số lượng node cạnh tranh N tăng, xác suất va chạm P_collision tăng tiệm cận 100%.")

    add_heading_2("2.4. Mô Hình Suy Hao Đường Truyền (Path Loss) & Hiệu Ứng Bắt Sóng (Capture Effect)")
    add_p("Công suất tín hiệu thu được RSSI tại Gateway từ node thứ i cách khoảng cách d_i tuân theo mô hình Log-Distance Path Loss:")
    add_math_block("RSSI_i(d_i) [dBm] = P_tx + G_tx + G_rx - PL(d_0) - 10 * n * log10( d_i / d_0 ) - WAF - X_sigma")
    add_p("Trong đó: P_tx = 17 dBm (công suất phát), d_0 = 1m (khoảng cách chuẩn), n ≈ 3.0 (hệ số suy hao trong nhà), WAF là hệ số suy hao xuyên tường (Wall Attenuation Factor), X_sigma là biến ngẫu nhiên Gauss phản ánh hiệu ứng che bóng (Shadowing).")

    add_p("Khi hai node i và j cùng phát đồng thời trên cùng một kênh, hiện tượng bắt sóng vô tuyến (Capture Effect) xảy ra tại Gateway nếu chênh lệch công suất thu thỏa mãn ngưỡng giải điều chế:")
    add_math_block("RSSI_i - RSSI_j >= gamma_cap  (với gamma_cap ≈ 6 dB đối với LoRa CSS SF7)")
    add_p("Ý nghĩa vật lý: Node ở gần Gateway (Node B: d ≈ 1-3m, RSSI ≈ -35 dBm) sẽ át vía hoàn toàn tín hiệu của Node ở xa (Node C: d ≈ 35-45m, RSSI ≈ -110 dBm), khiến Gateway giải mã được gói của Node B nhưng hủy diệt hoàn toàn gói của Node C.")

    # ═══════════════════════════════════════════════════════════════════════════
    # PHẦN 3: PHÁT BIỂU TOÁN HỌC BÀI TOÁN TỐI ƯU HÓA
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1("3. PHÁT BIỂU TOÁN HỌC BÀI TOÁN TỐI ƯU HÓA")

    add_heading_2("3.1. Biểu Diễn Trạng Thái Kênh Truyền (Channel State Information - CSI)")
    add_p("Tại mỗi mốc thời gian truyền t, thiết bị đầu cuối thu thập vector đặc trưng kênh truyền x_t gồm 9 thông số vật lý:")
    add_math_block("x_t = [ RSSI_t,  SNR_t,  Size_t,  roll_loss_t,  consec_loss_t,  ΔRSSI_t,  ΔSNR_t,  ch_t,  seq_t ]^T  ∈ R^9")
    add_p("Trong đó:")
    add_p("• RSSI_t, SNR_t: Cường độ tín hiệu và tỷ số tín hiệu trên nhiễu phản hồi từ gói ACK gần nhất.")
    add_p("• Size_t: Kích thước tải trọng dữ liệu (30 - 250 Bytes).")
    add_p("• roll_loss_t: Tỷ lệ mất gói trượt trong cửa sổ cục bộ gần nhất.")
    add_p("• consec_loss_t: Số lượng gói tin bị mất liên tiếp (chỉ báo kênh đang bị tắc nghẽn nặng).")
    add_p("• ΔRSSI_t, ΔSNR_t: Đạo hàm bậc nhất phản ánh độ dốc biến thiên chất lượng kênh giữa 2 bước.")
    add_p("• ch_t: Kênh tần số hiện tại đang sử dụng (ch_t ∈ {0, 1, 2}).")
    add_p("• seq_t: Chỉ số tuần tự của gói tin.")

    add_p("Để nắm bắt tương quan phụ thuộc thời gian (Temporal Dynamics) của quá trình truyền sóng, hệ thống duy trì một ma trận cửa sổ trượt (Sliding Window) gồm W = 10 mốc thời gian liên tiếp:")
    add_math_block("S_t = [ x_{t - W + 1},  x_{t - W + 2},  ...,  x_t ]  ∈ R^{10 x 9}")
    add_p("Tensor đầu vào này có thể được biểu diễn dưới dạng ma trận 2D kích thước (10, 9) hoặc vector phẳng 90 chiều sau khi qua bộ chuẩn hóa tĩnh StandardScaler: z = (S_t - μ) / σ.")

    add_heading_2("3.2. Biến Quyết Định (Decision Variable)")
    add_p("Biến quyết định của hệ thống là hành động lựa chọn kênh tần số vô tuyến a_{t+1} cho lượt phát sóng tiếp theo:")
    add_math_block("a_{t+1} ∈ C = {c_1, c_2, c_3}  (tương ứng 433.175, 433.375, 433.575 MHz)")

    add_heading_2("3.3. Hàm Mục Tiêu Tối Ưu Hóa (Optimization Objective)")
    add_p("Mục tiêu của bài toán là tìm chính sách lựa chọn kênh π* sao cho tối đa hóa tỷ lệ nhận gói PDR toàn mạng, đồng thời tối ưu hóa chất lượng năng lượng thu và giảm thiểu chi phí chuyển đổi tần số:")
    add_math_block("max_π  E [  PDR(a_{t+1})  +  λ_1 * RSSI_norm(a_{t+1})  +  λ_2 * SNR_norm(a_{t+1})  -  λ_3 * I(a_{t+1} != a_t) * C_hop  ]")
    add_p("Trong đó:")
    add_p("• PDR(a_{t+1}) ∈ [0, 1]: Xác suất gói tin được Gateway giải mã thành công khi phát trên kênh a_{t+1}.")
    add_p("• RSSI_norm, SNR_norm: Điểm chất lượng tín hiệu thu chuẩn hóa.")
    add_p("• I(a_{t+1} != a_t): Hàm chỉ thị nhận giá trị 1 nếu thiết bị quyết định nhảy kênh, nhận 0 nếu giữ nguyên kênh cũ.")
    add_p("• C_hop: Chi phí năng lượng và thời gian trễ khóa pha PLL của module RF SX1278 khi chuyển kênh (~150 μs).")
    add_p("• λ_1, λ_2, λ_3: Các trọng số cân bằng đa mục tiêu.")

    add_heading_2("3.4. Các Ràng Buộc Kỹ Thuật Nghiêm Ngặt Tại Biên (Edge Constraints)")
    add_p("Do mô hình học máy được triển khai trực tiếp trên vi điều khiển nhúng ESP32 (Xtensa Dual-Core 240 MHz, SRAM khả dụng cho ML ≈ 50-80 KB), bài toán tối ưu phải tuân thủ nghiêm ngặt 4 ràng buộc vật lý:")
    add_p("1. Ràng buộc bộ nhớ Flash: Dung lượng nhị phân FlatBuffer và mảng byte C header của mô hình phải nhỏ hơn 100 KB (thực tế kiến trúc Separable 1D-CNN chỉ chiếm 8.65 KB TFLite và 60.18 KB C header).")
    add_p("2. Ràng buộc bộ nhớ động RAM (Tensor Arena): Vùng nhớ cấp phát tĩnh cho bộ giải thông dịch TFLM không được vượt quá 15 KB (thực tế cấu hình TINYML_TENSOR_ARENA_SIZE = 10 KB).")
    add_p("3. Ràng buộc độ trễ suy luận thời gian thực: Thời gian tính toán suy luận τ_infer trên ESP32 phải nhỏ hơn 20 ms (thực tế đo đạc đạt ~13.5 ms), không gây trễ chu kỳ phát sóng 3000 ms.")
    add_p("4. Ràng buộc phi tập trung (Decentralized Operation): Quyết định nhảy kênh được thực hiện hoàn toàn tự trị tại từng End-Node dựa trên lịch sử quan sát cục bộ, không phát sinh thêm lưu lượng điều khiển ngoài băng (Out-of-band Overhead) làm nghẽn mạng vô tuyến.")

    # ═══════════════════════════════════════════════════════════════════════════
    # PHẦN 4: GIẢI PHÁP ĐỀ XUẤT: HỌC MÁY SIÊU NHẸ (TINYML)
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1("4. GIẢI PHÁP ĐỀ XUẤT: MẠNG NƠ-RON HỌC MÁY SIÊU NHẸ (TINYML)")

    add_p("Bài toán tối ưu hóa được chuyển đổi thành bài toán phân loại chuỗi thời gian đa lớp (Multi-Class Time-Series Classification):")
    add_math_block("f_θ: R^{10 x 9} → [0, 1]^3,   sao cho   sum_{k=1}^3 P(c_k | S_t) = 1")
    add_p("Kênh tối ưu tiếp theo được lựa chọn theo nguyên lý xác suất cực đại (ArgMax):")
    add_math_block("a_{t+1}^* = argmax_{k ∈ {1, 2, 3}}  P(c_k | S_t)")

    add_heading_2("4.1. Kiến Trúc Quán Quân: Depthwise Separable 1D-CNN")
    add_p("Để dung hòa mâu thuẫn giữa độ chính xác dự báo cao và tài nguyên vi điều khiển cực kỳ eo hẹp, đề tài đề xuất kiến trúc tích chập tách biệt theo chiều sâu (Depthwise Separable 1D-CNN):")
    add_p("• Tách phép tích chập truyền thống thành 2 bước: Depthwise Convolution (lọc không gian độc lập từng kênh) và Pointwise Convolution (kết hợp các kênh bằng kernel 1x1).")
    add_p("• Tỷ số giảm khối lượng tính toán nhân-cộng (MACs):")
    add_math_block("Reduction Ratio = 1 / C_out + 1 / K = 1 / 32 + 1 / 3 ≈ 0.364  (Giảm tới 63.6% phép tính)")
    add_p("• Sử dụng GlobalAveragePooling1D thay cho Flatten: Triệt tiêu hoàn toàn ma trận trọng số khổng lồ nối với lớp Dense, giảm số tham số toàn mạng xuống mức kỷ lục: chỉ 878 tham số!")

    # Bảng Benchmark 5 mô hình
    table_bm = doc.add_table(rows=6, cols=6)
    table_bm.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_bm)

    headers_bm = ["Kiến trúc Mô hình", "Độ chính xác Test", "Test Loss", "Số tham số (Params)", "Dung lượng TFLite", "Độ trễ suy luận"]
    for i, h in enumerate(headers_bm):
        cell = table_bm.cell(0, i)
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=120, bottom=120, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_bm = [
        ["Baseline FCNN", "90.41%", "0.2939", "1,699", "8.84 KB", "5.50 ms"],
        ["1D-CNN", "90.30%", "0.2973", "2,659", "16.34 KB", "13.49 ms"],
        ["GRU RNN", "90.12%", "0.2870", "1,619", "42.32 KB", "59.39 ms"],
        ["Separable 1D-CNN (★)", "90.51%", "0.2881", "878", "8.65 KB", "13.56 ms"],
        ["ResNet-1D", "90.30%", "0.2927", "2,339", "14.73 KB", "15.47 ms"],
    ]

    for row_idx, row_data in enumerate(data_bm):
        for col_idx, text in enumerate(row_data):
            cell = table_bm.cell(row_idx + 1, col_idx)
            if row_idx == 3: # Separable CNN
                set_cell_background(cell, "EBF3FB")
            elif row_idx % 2 == 1:
                set_cell_background(cell, "F9FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if row_idx == 3:
                r.font.bold = True
                if col_idx == 0:
                    r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    # ═══════════════════════════════════════════════════════════════════════════
    # PHẦN 5: HIỆU QUẢ THỰC NGHIỆM VÀ ĐÓNG GÓP KHOA HỌC
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1("5. HIỆU QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC VÀ ĐÓNG GÓP ĐỀ TÀI")

    add_p("Hiệu quả của giải pháp nhảy kênh dự đoán TinyML được kiểm chứng thông qua 21 kịch bản thực nghiệm đo sóng thực tế trên hệ thống phần cứng gồm 3 End-Nodes ESP32 và Multi-Channel Gateway Raspberry Pi CM4:")

    # Bảng So sánh PDR
    table_pdr = doc.add_table(rows=7, cols=5)
    table_pdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_pdr)

    headers_pdr = ["Kích thước Payload", "PDR Random Hopping", "PDR TinyML Hopping", "Mức Tăng Trưởng PDR", "Cải Thiện Mức RSSI"]
    for i, h in enumerate(headers_pdr):
        cell = table_pdr.cell(0, i)
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=120, bottom=120, left=90, right=90)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_pdr = [
        ["30 Bytes", "88.0%", "99.0%", "+11.0%", "-89.5 → -68.0 dBm (+21.5 dBm)"],
        ["74 Bytes", "90.0%", "100.0%", "+10.0%", "-91.2 → -68.3 dBm (+22.9 dBm)"],
        ["118 Bytes", "86.7%", "99.0%", "+12.3%", "-90.9 → -70.8 dBm (+20.1 dBm)"],
        ["162 Bytes", "76.7%", "99.0%", "+22.3%", "-90.6 → -70.8 dBm (+19.8 dBm)"],
        ["206 Bytes", "85.0%", "100.0%", "+15.0%", "-93.0 → -73.1 dBm (+19.9 dBm)"],
        ["250 Bytes", "63.7%", "95.0%", "+31.3% (Đột phá)", "-94.3 → -74.5 dBm (+19.8 dBm)"],
    ]

    for row_idx, row_data in enumerate(data_pdr):
        for col_idx, text in enumerate(row_data):
            cell = table_pdr.cell(row_idx + 1, col_idx)
            if row_idx == 5: # 250 Bytes
                set_cell_background(cell, "FDEDEC")
            elif row_idx % 2 == 1:
                set_cell_background(cell, "F9FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if row_idx == 5 and col_idx == 3:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    add_p("\nĐóng góp khoa học và kỹ thuật cốt lõi của đề tài:")
    add_p("1. Xây dựng hoàn chỉnh mô hình hóa toán học cho bài toán nhảy kênh dự đoán phân tán trong mạng LoRa đa node cự ly ngắn.")
    add_p("2. Thiết kế thành công kiến trúc mạng nơ-ron Separable 1D-CNN siêu nhẹ (878 tham số, 8.65 KB TFLite), vượt qua rào cản tài nguyên hạn chế của vi điều khiển ESP32 với độ trễ suy luận chỉ 13.5 ms.")
    add_p("3. Chứng minh thực nghiệm mức tăng trưởng vượt trội: Tại kích thước gói tin lớn nhất (250 Bytes), mô hình TinyML giúp tăng PDR từ 63.7% lên 95.0% (cải thiện +31.3%), đồng thời nâng cao công suất thu RSSI trung bình thêm ~20 dBm.")
    add_p("4. Cung cấp nền tảng mã nguồn mở, tài liệu kỹ thuật hoàn chỉnh và khả năng ứng dụng thực tế cao cho các hệ thống giám sát môi trường, nông nghiệp thông minh và nhà máy IoT.")

    # ═══════════════════════════════════════════════════════════════════════════
    # CHỮ KÝ VÀ PHÊ DUYỆT
    # ═══════════════════════════════════════════════════════════════════════════
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(24)
    p_sign.paragraph_format.keep_with_next = True
    
    table_sign = doc.add_table(rows=2, cols=2)
    table_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_sign.cell(0, 0).width = Inches(3.25)
    table_sign.cell(0, 1).width = Inches(3.25)
    
    p_s1 = table_sign.cell(0, 0).paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s1 = p_s1.add_run("GIẢNG VIÊN HƯỚNG DẪN\n(Ký và ghi rõ họ tên)")
    r_s1.font.bold = True
    r_s1.font.size = Pt(11)
    
    p_s2 = table_sign.cell(0, 1).paragraphs[0]
    p_s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s2 = p_s2.add_run("SINH VIÊN THỰC HIỆN\n(Ký và ghi rõ họ tên)")
    r_s2.font.bold = True
    r_s2.font.size = Pt(11)
    
    p_space1 = table_sign.cell(1, 0).paragraphs[0]
    p_space1.paragraph_format.space_before = Pt(45)
    
    p_space2 = table_sign.cell(1, 1).paragraphs[0]
    p_space2.paragraph_format.space_before = Pt(45)

    # Lưu file
    output_docx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/PHAT_BIEU_BAI_TOAN.docx"))
    doc.save(output_docx_path)
    print(f"[OK] Đã tạo thành công file Word: {output_docx_path}")
    return output_docx_path

if __name__ == "__main__":
    build_document()
