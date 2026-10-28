#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_data_parser.py
Trích xuất và chuẩn hóa log dữ liệu từ Gateway thành các file CSV chuẩn.
Hỗ trợ: file log CSV trực tiếp, log terminal pipe-separated, log text gốc.
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

# Regex cho log terminal pipe-separated (từ main_gw.cpp / test_comm.cpp):
# "12:00:00.123 | A    | 0      |   30 B |  -75 |   9.0 | 433.175"
PATTERN_TERMINAL_PIPE = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}\.\d{3})\s*\|\s*"
    r"(?P<source>[A-Z])\s*\|\s*"
    r"(?P<packet_ID>\d+)\s*\|\s*"
    r"(?P<size_of_message>\d+)\s*(?:B)?\s*\|\s*"
    r"(?P<RSSI>-?\d+)\s*\|\s*"
    r"(?P<SNR>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"(?P<frequency>\d{3}\.\d{3})"
)

# Regex cho log text:
# "11:45:51.918 -> A0* size_of_message 30 RSSI -88 SNR 10 Frequency 433.175"
PATTERN_TEXT_LOG = re.compile(
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
    # Thử đọc trực tiếp dưới dạng CSV
    try:
        df_csv = pd.read_csv(input_path)
        df_csv.columns = [c.strip() for c in df_csv.columns]
        if all(col in df_csv.columns for col in ['source', 'packet_ID', 'size_of_message', 'RSSI', 'SNR', 'frequency']):
            df_csv['packet_ID'] = pd.to_numeric(df_csv['packet_ID'], errors='coerce').astype(int)
            df_csv['size_of_message'] = pd.to_numeric(df_csv['size_of_message'], errors='coerce').astype(int)
            df_csv['RSSI'] = pd.to_numeric(df_csv['RSSI'], errors='coerce').astype(int)
            df_csv['SNR'] = pd.to_numeric(df_csv['SNR'], errors='coerce').astype(float)
            df_csv['frequency'] = pd.to_numeric(df_csv['frequency'], errors='coerce').astype(float).round(3)
            if 'time_slot' not in df_csv.columns:
                df_csv['time_slot'] = '00:00:00.000'
            df_csv = df_csv[REQUIRED_COLUMNS]
            df_csv.to_csv(output_path, index=False, float_format='%.3f')
            print(f"[OK] File CSV chuẩn: {len(df_csv)} dòng -> {os.path.basename(output_path)}")
            return
    except Exception:
        pass

    # Parse từng dòng văn bản
    data = []
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("---") or line_str.startswith("===") or "Time" in line_str:
                continue

            match = PATTERN_TERMINAL_PIPE.search(line_str)
            if not match:
                match = PATTERN_TEXT_LOG.search(line_str)

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
        print(f"[OK] Trích xuất {len(df)} dòng: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    else:
        print(f"[WARN] Không tìm thấy dữ liệu hợp lệ trong {os.path.basename(input_path)}")


def main():
    print("=== BƯỚC 1: TRÍCH XUẤT VÀ CHUẨN HÓA LOG GATEWAY ===")
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR, exist_ok=True)
        print(f"[INFO] Vui lòng đặt các file log vào: {INPUT_DIR}")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith((".csv", ".log", ".txt"))]
    if not files:
        print(f"[INFO] Chưa có file log trong {INPUT_DIR}.")
        return

    for filename in files:
        in_file = os.path.join(INPUT_DIR, filename)
        out_file = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + ".csv")
        parse_log_file(in_file, out_file)


if __name__ == "__main__":
    main()
