#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_data_parser.py
Chức năng: Trích xuất và chuẩn hóa log dữ liệu từ Gateway thành các file CSV chuẩn.
Hỗ trợ cả file log CSV trực tiếp, log terminal từ main_gw/test_comm và log dạng raw text.
Theo sát cấu trúc bài báo LoRaEdgeTinyML (Marla Grunewald et al., TU Braunschweig).
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

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/logs")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/parsed")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Regex cho log terminal xuất từ Gateway (main_gw.cpp / test_comm.cpp):
# Format: "12:00:00.123 | A    | 0      |   30 B |  -75 |   9.0 | 433.175"
PATTERN_TERMINAL_PIPE = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}\.\d{3})\s*\|\s*"
    r"(?P<source>[A-Z])\s*\|\s*"
    r"(?P<packet_ID>\d+)\s*\|\s*"
    r"(?P<size_of_message>\d+)\s*(?:B)?\s*\|\s*"
    r"(?P<RSSI>-?\d+)\s*\|\s*"
    r"(?P<SNR>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<frequency>\d{3}\.\d{3})"
)

# 2. Regex cho log nguyên bản từ bài báo tác giả (data_parser_all.py):
# Format: "11:45:51.918 -> A0* size_of_message 30 RSSI -88 SNR 10 Frequency 868.00"
PATTERN_ORIGINAL_PAPER = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}\.\d{3})\s*->\s*"
    r"(?P<source>[A-Z])(?P<packet_ID>\d+)(?:\*.*?)\s*.*?"
    r"size_of_message\s+(?P<size_of_message>\d+)\s*"
    r"RSSI\s+(?P<RSSI>-?\d+)\s*"
    r"SNR\s+(?P<SNR>-?\d+(?:\.\d+)?)\s*"
    r"Frequency\s+(?P<frequency>\d+\.\d+)",
    re.IGNORECASE
)

REQUIRED_COLUMNS = ['time_slot', 'source', 'packet_ID', 'size_of_message', 'RSSI', 'SNR', 'frequency']

def parse_log_file(input_path, output_path):
    # Cách 1: Thử đọc trực tiếp dưới dạng CSV (do main_gw.cpp ghi trực tiếp ra CSV)
    try:
        df_csv = pd.read_csv(input_path)
        # Chuẩn hóa tên cột (bỏ khoảng trắng thừa)
        df_csv.columns = [c.strip() for c in df_csv.columns]
        if all(col in df_csv.columns for col in ['source', 'packet_ID', 'size_of_message', 'RSSI', 'SNR', 'frequency']):
            # Ép kiểu dữ liệu chuẩn
            df_csv['packet_ID'] = pd.to_numeric(df_csv['packet_ID'], errors='coerce').astype(int)
            df_csv['size_of_message'] = pd.to_numeric(df_csv['size_of_message'], errors='coerce').astype(int)
            df_csv['RSSI'] = pd.to_numeric(df_csv['RSSI'], errors='coerce').astype(int)
            df_csv['SNR'] = pd.to_numeric(df_csv['SNR'], errors='coerce').astype(float)
            df_csv['frequency'] = pd.to_numeric(df_csv['frequency'], errors='coerce').astype(float).round(3)
            if 'time_slot' not in df_csv.columns:
                df_csv['time_slot'] = '00:00:00.000'
            df_csv = df_csv[REQUIRED_COLUMNS]
            df_csv.to_csv(output_path, index=False, float_format='%.3f')
            print(f"[OK] File CSV chuẩn: trích xuất {len(df_csv)} dòng -> {os.path.basename(output_path)}")
            return
    except Exception:
        pass

    # Cách 2: Parse từng dòng văn bản (text log hoặc pipe terminal log)
    data = []
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            # Bỏ qua các dòng header hoặc phân cách
            if line_str.startswith("---") or line_str.startswith("===") or "Time" in line_str:
                continue

            # Thử pattern terminal pipe (Gateway hiện tại)
            match = PATTERN_TERMINAL_PIPE.search(line_str)
            if not match:
                # Thử pattern gốc của bài báo
                match = PATTERN_ORIGINAL_PAPER.search(line_str)

            if match:
                d = match.groupdict()
                d["packet_ID"] = int(d["packet_ID"])
                d["size_of_message"] = int(d["size_of_message"])
                d["RSSI"] = int(d["RSSI"])
                d["SNR"] = float(d["SNR"])
                d["frequency"] = round(float(d["frequency"]), 3)
                data.append(d)

    if data:
        df = pd.DataFrame(data)[REQUIRED_COLUMNS]
        df['frequency'] = df['frequency'].round(3)
        df.to_csv(output_path, index=False, float_format='%.3f')
        print(f"[OK] Trích xuất {len(df)} dòng từ log {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    else:
        print(f"[WARN] Không tìm thấy dữ liệu hợp lệ trong {os.path.basename(input_path)}")

def main():
    print("=== BƯỚC 1: TRÍCH XUẤT VÀ CHUẨN HÓA LOG GATEWAY (01_data_parser) ===")
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR, exist_ok=True)
        print(f"[INFO] Vui lòng đặt các file log từ Gateway (.csv hoặc .log) vào thư mục: {INPUT_DIR}")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith((".csv", ".log", ".txt"))]
    if not files:
        print(f"[INFO] Chưa có file log trong {INPUT_DIR}. Đặt gateway_log_*.csv hoặc log vào đây.")
        return

    for filename in files:
        in_file = os.path.join(INPUT_DIR, filename)
        out_file = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + "_parsed.csv")
        parse_log_file(in_file, out_file)

if __name__ == "__main__":
    main()
