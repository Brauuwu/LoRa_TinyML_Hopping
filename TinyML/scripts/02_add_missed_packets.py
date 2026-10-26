#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_add_missed_packets.py
Chức năng: Phát hiện các gói tin bị mất do va chạm sóng hoặc suy hao nghiêm trọng,
           bổ sung các dòng dữ liệu với RSSI = -1000, SNR = -1000 theo đúng công thức
           và thuật toán trong bài báo LoRaEdgeTinyML (Equation 14 & adding_missed_packets_all.py).
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

# Số lượng gói chuẩn trong một đợt phát (burst) cho mỗi kích thước payload
EXPECTED_BURST_PACKETS = 100

def process_file(input_file, output_file):
    df = pd.read_csv(input_file)
    df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce')
    df = df.dropna(subset=['packet_ID'])
    df['packet_ID'] = df['packet_ID'].astype(int)

    # Xác định các trường phân nhóm: Nếu file có nhiều kênh thì nhóm cả theo frequency
    has_multiple_freqs = len(df['frequency'].dropna().unique()) > 1
    group_cols = ['frequency', 'source', 'size_of_message'] if has_multiple_freqs else ['source', 'size_of_message']

    new_rows = []

    for keys, subset in df.groupby(group_cols):
        if subset.empty:
            continue

        if has_multiple_freqs:
            freq, source, size = keys
        else:
            source, size = keys
            freq = subset.iloc[0]['frequency']

        # Dải packet_ID kỳ vọng (0..99 cho đợt 100 gói, hoặc mở rộng nếu id thực tế lớn hơn)
        min_id = int(subset['packet_ID'].min())
        max_id = max(int(subset['packet_ID'].max()), EXPECTED_BURST_PACKETS - 1)
        all_ids = set(range(min(0, min_id), max_id + 1))
        existing_ids = set(subset['packet_ID'])
        missing_ids = all_ids - existing_ids

        for m_id in missing_ids:
            # 1. Theo chuẩn bài báo: Tìm mốc thời gian từ các node khác trong cùng thời điểm nếu có
            match_row = df[(df['packet_ID'] == m_id) & (df['source'] != source)]
            time_slot = None

            if not match_row.empty and pd.notna(match_row.iloc[0].get('time_slot')):
                time_slot = match_row.iloc[0]['time_slot']
            else:
                # 2. Nếu là kịch bản đơn Node (không có Node khác để mượn giờ):
                # Nội suy mốc thời gian từ gói liền trước + chu kỳ phát cơ sở (~3.0 giây)
                prev_row = subset[subset['packet_ID'] < m_id].sort_values('packet_ID').tail(1)
                if not prev_row.empty and pd.notna(prev_row.iloc[0].get('time_slot')):
                    try:
                        import datetime
                        prev_ts_str = str(prev_row.iloc[0]['time_slot']).strip()
                        prev_dt = datetime.datetime.strptime(prev_ts_str, "%H:%M:%S.%f")
                        delta_steps = m_id - int(prev_row.iloc[0]['packet_ID'])
                        new_dt = prev_dt + datetime.timedelta(seconds=3.0 * delta_steps)
                        time_slot = new_dt.strftime("%H:%M:%S.%f")[:-3]
                    except Exception:
                        time_slot = '00:00:00.000'
                if not time_slot:
                    time_slot = '00:00:00.000'

            # Gán nhãn gói mất do va chạm / rớt sóng theo bài báo: RSSI = -1000, SNR = -1000
            new_rows.append({
                'time_slot': time_slot,
                'source': source,
                'packet_ID': m_id,
                'size_of_message': size,
                'RSSI': -1000,
                'SNR': -1000,
                'frequency': round(float(freq), 3)
            })

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    sort_cols = ['frequency', 'source', 'size_of_message', 'packet_ID'] if has_multiple_freqs else ['source', 'size_of_message', 'packet_ID']
    df['frequency'] = df['frequency'].round(3)
    df = df.sort_values(by=sort_cols).reset_index(drop=True)
    df.to_csv(output_file, index=False, float_format='%.3f')
    print(f"[OK] Bổ sung {len(new_rows)} gói tin mất vào: {os.path.basename(output_file)} (Tổng {len(df)} dòng)")

def main():
    print("=== BƯỚC 2: PHÁT HIỆN VÀ GÁN NHÃN GÓI MẤT (02_add_missed_packets) ===")
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
