#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_add_missed_packets.py
Phát hiện gói tin bị mất và bổ sung dòng dữ liệu với RSSI = -1000, SNR = -1000.
Gói bị mất là gói có packet_ID nằm trong khoảng min..max nhưng không xuất hiện.
"""

import os
import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/parsed")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/imputed")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_file(input_file, output_file):
    df = pd.read_csv(input_file)
    df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce')
    df = df.dropna(subset=['packet_ID'])
    df['packet_ID'] = df['packet_ID'].astype(int)

    # Lọc bỏ các gói rác/nhiễu ngoại lai
    valid_sizes = [30, 74, 118, 162, 206, 250]
    df = df[(df['size_of_message'].isin(valid_sizes)) & (df['packet_ID'] >= 0) & (df['packet_ID'] < 100)]

    new_rows = []

    # Nhóm theo (source, size_of_message) để xác định gói mất
    for (source, size), subset in df.groupby(['source', 'size_of_message']):
        if subset.empty:
            continue

        freq = subset.iloc[0]['frequency']
        all_ids = set(range(0, 100))
        existing_ids = set(subset['packet_ID'])
        missing_ids = all_ids - existing_ids

        for m_id in missing_ids:
            # Tìm mốc thời gian và tần số từ node khác nếu có
            match_row = df[(df['packet_ID'] == m_id) & (df['source'] != source)]

            if not match_row.empty:
                time_slot = match_row.iloc[0]['time_slot']
                frequency = match_row.iloc[0]['frequency']
            else:
                time_slot = None
                frequency = freq

            new_rows.append({
                'time_slot': time_slot,
                'source': source,
                'packet_ID': m_id,
                'size_of_message': size,
                'RSSI': -1000,
                'SNR': -1000,
                'frequency': frequency
            })

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    df = df.sort_values(by=['source', 'size_of_message', 'packet_ID']).reset_index(drop=True)
    df['frequency'] = df['frequency'].round(3)
    df.to_csv(output_file, index=False, float_format='%.3f')
    print(f"[OK] Bổ sung {len(new_rows)} gói mất -> {os.path.basename(output_file)} (Tổng {len(df)} dòng)")


def main():
    print("=== BƯỚC 2: PHÁT HIỆN VÀ GÁN NHÃN GÓI MẤT ===")
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Chưa có thư mục {INPUT_DIR}. Chạy 01_data_parser.py trước!")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("[WARN] Chưa có file CSV trong parsed/.")
        return

    for filename in files:
        in_path = os.path.join(INPUT_DIR, filename)
        out_path = os.path.join(OUTPUT_DIR, filename)
        process_file(in_path, out_path)


if __name__ == "__main__":
    main()
