#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_data_parser.py
Trích xuất và chuẩn hóa log dữ liệu từ Gateway thành các file CSV chuẩn.
Mỗi file log .txt / .log đầu vào được parse thành một file .csv tương ứng (1-to-1 mapping).

Ví dụ:
  logs/A_433_175.txt     -> parsed/A_433_175.csv
  logs/A_B_433_175.txt   -> parsed/A_B_433_175.csv
  logs/A_B_C_433_575.txt -> parsed/A_B_C_433_575.csv

Hỗ trợ các định dạng:
  1. Log text Gateway txt file:
     "11:45:51.918 -> A0*152087041786616005564650518 size_of_message 30 RSSI -88 SNR 10 Frequency 433.175"
  2. Log console Gateway dạng pipe:
     " 12:00:00.123 |  433.175 |   A  |      0 |   30 |        -75 |     9.0"
     " 12:00:00.123 | A    | 0      |   30 B |  -75 |   9.0 | 433.175"
  3. File CSV thô (chuẩn hóa tên cột và kiểu dữ liệu).

Cách chạy:
  python 01_data_parser.py
  python 01_data_parser.py [input_dir] [output_dir]
"""

import os
import re
import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Regex patterns for log formats
# Cú pháp: "11:45:51.918 -> A0*... size_of_message 30 RSSI -88 SNR 10 Frequency 433.175"
PATTERN_TEXT_LOG = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}[.:]\d{3})\s*->\s*"
    r"(?P<source>[A-Za-z])(?P<packet_ID>\d+)(?:[* ].*?)?"
    r"\s+size_of_message\s+(?P<size_of_message>\d+)\s+"
    r"RSSI\s+(?P<RSSI>-?\d+)\s+"
    r"SNR\s+(?P<SNR>-?\d+(?:\.\d+)?)\s+"
    r"Frequency\s+(?P<frequency>\d+(?:\.\d+)?)",
    re.IGNORECASE
)

# Regex 2: Log console Gateway dạng pipe (chuẩn main_gw.cpp)
# " 12:00:00.123 |  433.175 |   A  |      0 |   30 |        -75 |     9.0"
PATTERN_PIPE_GW = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}[.:]\d{3})\s*\|\s*"
    r"(?P<frequency>\d{3}\.\d{3})\s*\|\s*"
    r"(?P<source>[A-Za-z])\s*\|\s*"
    r"(?P<packet_ID>\d+)\s*\|\s*"
    r"(?P<size_of_message>\d+)\s*(?:B)?\s*\|\s*"
    r"(?P<RSSI>-?\d+)\s*\|\s*"
    r"(?P<SNR>-?\d+(?:\.\d+)?)"
)

# Regex 3: Log console dạng pipe hoán đổi vị trí tần số
# " 12:00:00.123 | A    | 0      |   30 B |  -75 |   9.0 | 433.175"
PATTERN_PIPE_ALT = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}[.:]\d{3})\s*\|\s*"
    r"(?P<source>[A-Za-z])\s*\|\s*"
    r"(?P<packet_ID>\d+)\s*\|\s*"
    r"(?P<size_of_message>\d+)\s*(?:B)?\s*\|\s*"
    r"(?P<RSSI>-?\d+)\s*\|\s*"
    r"(?P<SNR>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<frequency>\d{3}\.\d{3})"
)

REQUIRED_COLUMNS = ['time_slot', 'source', 'packet_ID', 'size_of_message', 'RSSI', 'SNR', 'frequency']


def parse_single_file(input_path: str, output_path: str) -> int:
    """
    Parse một file log (.txt, .log hoặc .csv) và lưu thành file CSV tương ứng.
    Trả về số lượng bản ghi gói tin hợp lệ được trích xuất.
    """
    ext = os.path.splitext(input_path)[1].lower()

    # 1. Nếu đã là file CSV, đọc bằng pandas và chuẩn hóa cột
    if ext == ".csv":
        try:
            df_csv = pd.read_csv(input_path)
            df_csv.columns = [c.strip() for c in df_csv.columns]
            needed = ['source', 'packet_ID', 'size_of_message', 'RSSI', 'SNR', 'frequency']
            if all(col in df_csv.columns for col in needed):
                df_csv['source'] = df_csv['source'].astype(str).str.strip().str.upper()
                df_csv['packet_ID'] = pd.to_numeric(df_csv['packet_ID'], errors='coerce').astype(int)
                df_csv['size_of_message'] = pd.to_numeric(df_csv['size_of_message'], errors='coerce').astype(int)
                df_csv['RSSI'] = pd.to_numeric(df_csv['RSSI'], errors='coerce').astype(int)
                df_csv['SNR'] = pd.to_numeric(df_csv['SNR'], errors='coerce').astype(float)
                df_csv['frequency'] = pd.to_numeric(df_csv['frequency'], errors='coerce').astype(float).round(3)
                if 'time_slot' not in df_csv.columns:
                    df_csv['time_slot'] = '00:00:00.000'
                df_csv = df_csv[REQUIRED_COLUMNS]
                df_csv.to_csv(output_path, index=False, float_format='%.3f')
                return len(df_csv)
        except Exception:
            pass  # Nếu đọc CSV thất bại, tiếp tục thử parse dạng text

    # 2. Xử lý file Text log (.txt, .log) theo từng dòng
    data = []
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            # Bỏ qua các dòng phân cách, tiêu đề, dòng trống
            if not line_str or line_str.startswith("---") or line_str.startswith("===") or "Time" in line_str:
                continue

            match = PATTERN_TEXT_LOG.search(line_str)
            if not match:
                match = PATTERN_PIPE_GW.search(line_str)
            if not match:
                match = PATTERN_PIPE_ALT.search(line_str)

            if match:
                d = match.groupdict()
                try:
                    d["source"] = d["source"].upper()
                    d["packet_ID"] = int(d["packet_ID"])
                    d["size_of_message"] = int(d["size_of_message"])
                    d["RSSI"] = int(d["RSSI"])
                    d["SNR"] = float(d["SNR"])
                    d["frequency"] = round(float(d["frequency"]), 3)
                    data.append(d)
                except (ValueError, TypeError):
                    continue

    if data:
        df = pd.DataFrame(data)[REQUIRED_COLUMNS]
        df['frequency'] = df['frequency'].round(3)
        df.to_csv(output_path, index=False, float_format='%.3f')
        return len(df)

    return 0


def resolve_directories(input_arg=None, output_arg=None):
    """
    Xác định đường dẫn thư mục đầu vào và đầu ra dựa trên tham số hoặc cấu trúc dự án.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Xác định INPUT_DIR
    if input_arg:
        input_dir = os.path.abspath(input_arg)
    else:
        candidates = [
            os.path.join(script_dir, "../data/logs"),
            os.path.join(os.getcwd(), "TinyML/data/logs"),
            os.path.join(os.getcwd(), "data/logs"),
            os.path.join(os.getcwd(), "logs"),
        ]
        input_dir = candidates[0]
        for c in candidates:
            if os.path.exists(c):
                files = [f for f in os.listdir(c) if f.lower().endswith(('.txt', '.log', '.csv'))]
                if files:
                    input_dir = c
                    break

    # 2. Xác định OUTPUT_DIR tương ứng
    if output_arg:
        output_dir = os.path.abspath(output_arg)
    else:
        parent = os.path.dirname(input_dir)
        if os.path.basename(input_dir) == "logs" and os.path.basename(parent) == "data":
            output_dir = os.path.join(parent, "parsed")
        elif os.path.basename(input_dir) == "logs":
            output_dir = os.path.join(parent, "csv")
        else:
            output_dir = os.path.join(script_dir, "../data/parsed")

    return input_dir, output_dir


def main():
    print("=" * 72)
    print(" BƯỚC 1: TRÍCH XUẤT VÀ CHUẨN HÓA LOG GATEWAY (1 FILE TXT -> 1 FILE CSV)")
    print("=" * 72)

    in_arg = sys.argv[1] if len(sys.argv) > 1 else None
    out_arg = sys.argv[2] if len(sys.argv) > 2 else None

    input_dir, output_dir = resolve_directories(in_arg, out_arg)

    print(f" [+] Thư mục Input  (chứa file .txt/.log): {input_dir}")
    print(f" [+] Thư mục Output (chứa file .csv)    : {output_dir}")
    print("-" * 72)

    if not os.path.exists(input_dir):
        os.makedirs(input_dir, exist_ok=True)
        print(f"[INFO] Thư mục nguồn chưa tồn tại. Đã tự động tạo: {input_dir}")
        print(f"[INFO] Vui lòng chép các file log (.txt, .log) vào thư mục trên rồi chạy lại script.")
        return

    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in sorted(os.listdir(input_dir)) if f.lower().endswith((".txt", ".log", ".csv"))]

    if not files:
        print(f"[INFO] Không tìm thấy file log (.txt, .log, .csv) nào trong: {input_dir}")
        print(f"[INFO] Vui lòng copy các file log từ Gateway vào thư mục trên.")
        return

    total_parsed_files = 0
    total_records = 0

    for filename in files:
        in_file = os.path.join(input_dir, filename)
        stem = os.path.splitext(filename)[0]
        out_file = os.path.join(output_dir, f"{stem}.csv")

        count = parse_single_file(in_file, out_file)
        if count > 0:
            total_parsed_files += 1
            total_records += count
            print(f"  [OK] Đã chuyển đổi: {filename} -> {os.path.basename(out_file)} ({count} gói tin)")
        else:
            print(f"  [CẢNH BÁO] Bỏ qua file do không có dữ liệu hợp lệ: {filename}")

    print("-" * 72)
    print(f"[HOÀN THÀNH] Đã xử lý thành công: {total_parsed_files}/{len(files)} file log")
    print(f"             Tổng số gói tin thu được: {total_records:,} gói tin")
    print(f"             Toàn bộ file CSV lưu tại: {output_dir}")
    print("=" * 72)


if __name__ == "__main__":
    main()
