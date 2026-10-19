#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_data_parser.py
Chức năng: Trích xuất và chuẩn hóa log dữ liệu từ Gateway thành các file CSV.
Dựa trên paper: arXiv:2412.01609v1 (LoRaEdgeTinyML)
"""

import os
import re
import pandas as pd

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/logs")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/parsed")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex phân tích log từ Serial hoặc file log của Gateway
LOG_PATTERN = re.compile(
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}\.\d{3})\s*\|\s*"
    r"(?P<frequency>\d{3}\.\d{3})\s*\|\s*"
    r"(?P<source>[A-Z])\s*\|\s*"
    r"(?P<packet_ID>\d+)\s*\|\s*"
    r"(?P<size_of_message>\d+)\s*\|\s*"
    r"(?P<RSSI>-?\d+)\s*\|\s*"
    r"(?P<SNR>-?\d+(?:\.\d+)?)"
)

def parse_log_file(input_path, output_path):
    data = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            match = LOG_PATTERN.search(line)
            if match:
                d = match.groupdict()
                d["packet_ID"] = int(d["packet_ID"])
                d["size_of_message"] = int(d["size_of_message"])
                d["RSSI"] = int(d["RSSI"])
                d["SNR"] = float(d["SNR"])
                d["frequency"] = float(d["frequency"])
                data.append(d)

    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"[OK] Trích xuất {len(df)} dòng từ {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    else:
        # Nếu là file CSV thuần thì sao chép và chuẩn hóa cột
        try:
            df = pd.read_csv(input_path)
            if "packet_ID" in df.columns:
                df.to_csv(output_path, index=False)
                print(f"[OK] Đã chuyển đổi trực tiếp {len(df)} dòng: {os.path.basename(output_path)}")
        except Exception as e:
            print(f"[WARN] Không tìm thấy dữ liệu phù hợp trong {os.path.basename(input_path)}: {e}")

def main():
    print("=== BƯỚC 1: TRÍCH XUẤT VÀ CHUẨN HÓA LOG GATEWAY ===")
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR, exist_ok=True)
        print(f"[INFO] Vui lòng đặt các file log từ Gateway (.csv hoặc .log) vào thư mục: {INPUT_DIR}")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith((".csv", ".log", ".txt"))]
    if not files:
        print(f"[INFO] Chưa có file log trong {INPUT_DIR}. Bạn có thể copy file gateway_log_*.csv vào đây.")
        return

    for filename in files:
        in_file = os.path.join(INPUT_DIR, filename)
        out_file = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + "_parsed.csv")
        parse_log_file(in_file, out_file)

if __name__ == "__main__":
    main()
