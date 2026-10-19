#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_add_missed_packets.py
Chức năng: Phát hiện các gói tin bị mất do va chạm hoặc suy hao sóng
           và bổ sung các dòng dữ liệu với RSSI = -1000, SNR = -1000.
Dựa trên paper: arXiv:2412.01609v1 (LoRaEdgeTinyML)
"""

import os
import pandas as pd

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/parsed")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/imputed")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_file(input_file, output_file):
    df = pd.read_csv(input_file)
    df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce')
    df = df.dropna(subset=['packet_ID'])
    df['packet_ID'] = df['packet_ID'].astype(int)

    sources = df['source'].unique()
    sizes = df['size_of_message'].unique()
    new_rows = []

    for source in sources:
        for size in sizes:
            subset = df[(df['source'] == source) & (df['size_of_message'] == size)]
            if subset.empty:
                continue

            # Dải gói tin thực tế (thường là 0..49 hoặc min..max)
            min_id = int(subset['packet_ID'].min())
            max_id = int(subset['packet_ID'].max())
            all_ids = set(range(min_id, max_id + 1))
            existing_ids = set(subset['packet_ID'])
            missing_ids = all_ids - existing_ids

            for m_id in missing_ids:
                # Tìm tần số và mốc thời gian ước lượng từ các node khác trong cùng nhịp
                match_row = df[(df['packet_ID'] == m_id) & (df['source'] != source)]
                if not match_row.empty:
                    time_slot = match_row.iloc[0].get('time_slot', '00:00:00.000')
                    freq = match_row.iloc[0].get('frequency', subset.iloc[0]['frequency'])
                else:
                    time_slot = '00:00:00.000'
                    freq = subset.iloc[0]['frequency']

                # Đánh dấu gói tin va chạm / mất sóng theo chuẩn bài báo
                new_rows.append({
                    'time_slot': time_slot,
                    'source': source,
                    'packet_ID': m_id,
                    'size_of_message': size,
                    'RSSI': -1000,
                    'SNR': -1000,
                    'frequency': freq
                })

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    df = df.sort_values(by=['source', 'size_of_message', 'packet_ID']).reset_index(drop=True)
    df.to_csv(output_file, index=False)
    print(f"[OK] Bổ sung {len(new_rows)} gói tin mất vào: {os.path.basename(output_file)}")

def main():
    print("=== BƯỚC 2: PHÁT HIỆN VÀ GÁN NHÃN GÓI MẤT (COLLISION DETECTION) ===")
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Chưa có thư mục {INPUT_DIR}. Vui lòng chạy 01_data_parser.py trước!")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("[WARN] Chưa có file CSV trong parsed/. Đang đợi dữ liệu...")
        return

    for filename in files:
        in_path = os.path.join(INPUT_DIR, filename)
        out_path = os.path.join(OUTPUT_DIR, filename)
        process_file(in_path, out_path)

if __name__ == "__main__":
    main()
