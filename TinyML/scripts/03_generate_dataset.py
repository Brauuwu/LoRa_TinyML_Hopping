#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_dataset.py
Chức năng: Xây dựng đặc trưng chuỗi thời gian (Sliding Window / Temporal Memory)
           và gán nhãn kênh tối ưu (Best Channel) cho bài toán nhảy kênh TinyML.
"""

import os
import numpy as np
import pandas as pd

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/imputed")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/ready")

os.makedirs(OUTPUT_DIR, exist_ok=True)

CHANNELS = [433.175, 433.375, 433.575]
WINDOW_SIZE = 5  # Số bước thời gian lịch sử dùng để suy luận (Temporal memory ts)

def build_features(df):
    # Tạo các cột cờ đánh dấu kênh bận / va chạm:
    # 0 = Kênh thành công, 1 = Kênh bị va chạm hoặc mất sóng (-1000)
    for i, ch in enumerate(CHANNELS, 1):
        df[f'CH{i}'] = df.apply(
            lambda r: 1 if (abs(r['frequency'] - ch) < 0.05 and r['RSSI'] == -1000) else 0,
            axis=1
        )

    samples = []
    # Quét qua từng node để đảm bảo tính liên tục của chuỗi thời gian
    for source, group in df.groupby('source'):
        group = group.sort_values(by=['packet_ID']).reset_index(drop=True)
        n = len(group)
        if n <= WINDOW_SIZE:
            continue

        for i in range(n - WINDOW_SIZE):
            window = group.iloc[i : i + WINDOW_SIZE]
            target_row = group.iloc[i + WINDOW_SIZE]

            features = []
            for _, row in window.iterrows():
                features.extend([
                    row['CH1'],
                    row['CH2'],
                    row['CH3'],
                    row['RSSI'] if row['RSSI'] != -1000 else -120.0,
                    row['SNR'] if row['SNR'] != -1000 else -20.0,
                    row['size_of_message'],
                    row['frequency']
                ])

            # Nhãn mục tiêu: Kênh nào có RSSI cao nhất mà không bị mất sóng
            # Mặc định theo tần số của gói tiếp theo nếu thành công, hoặc kênh thay thế
            freq = target_row['frequency']
            if abs(freq - CHANNELS[0]) < 0.05:
                label_ch = 0
            elif abs(freq - CHANNELS[1]) < 0.05:
                label_ch = 1
            else:
                label_ch = 2

            # Nếu gói này bị mất sóng -> phạt và đổi sang kênh khác
            if target_row['RSSI'] == -1000:
                label_ch = (label_ch + 1) % 3

            sample_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
            sample_dict['target_channel'] = label_ch
            sample_dict['source'] = source
            samples.append(sample_dict)

    return pd.DataFrame(samples)

def main():
    print("=== BƯỚC 3: TẠO DATASET CHUỖI THỜI GIAN & GÁN NHÃN KÊNH ===")
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Thư mục {INPUT_DIR} chưa tồn tại!")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("[WARN] Chưa có file dữ liệu trong imputed/. Hãy chạy bước 1 & 2 trước.")
        return

    all_dfs = []
    for f in files:
        p = os.path.join(INPUT_DIR, f)
        all_dfs.append(pd.read_csv(p))

    combined = pd.concat(all_dfs, ignore_index=True)
    dataset = build_features(combined)

    out_file = os.path.join(OUTPUT_DIR, "dataset_ready.csv")
    dataset.to_csv(out_file, index=False)
    print(f"[SUCCESS] Đã tạo dataset huấn luyện với {len(dataset)} mẫu -> {out_file}")

if __name__ == "__main__":
    main()
