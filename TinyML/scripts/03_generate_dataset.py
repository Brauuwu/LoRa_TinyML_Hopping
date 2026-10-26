#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_dataset.py
Chức năng: Xây dựng đặc trưng chuỗi thời gian (Sliding Window / Temporal Memory ts = 10 bước)
           và gán nhãn kênh tối ưu (Best Channel C_i có RSSI cao nhất) theo đúng phương pháp
           trong bài báo LoRaEdgeTinyML (Mục III.C.1, Công thức 14-19 & Table II).
"""

import os
import sys
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/imputed")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/ready")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3 tần số làm việc của hệ thống (433 MHz ISM Band tại Việt Nam)
CHANNELS = [433.175, 433.375, 433.575]
NUM_CHANNELS = len(CHANNELS)

# Kích thước cửa sổ trượt bộ nhớ thời gian (ts = 10 bước theo Table II & train_model_hopping.py)
WINDOW_SIZE = 10

def assign_channel_flags(row):
    """
    Xác định vector trạng thái kênh [CH1, CH2, CH3] theo công thức (14) của bài báo:
    - Kênh đang phát: flag = 0 (khả dụng nếu thu tốt, hoặc 1 nếu bị va chạm RSSI = -1000)
    - Kênh không phát ở slot này: flag = 1
    """
    freq = row['frequency']
    is_loss = (row['RSSI'] == -1000)

    # Tìm index kênh gần nhất
    ch_idx = 0
    min_diff = abs(freq - CHANNELS[0])
    for idx, c in enumerate(CHANNELS[1:], 1):
        diff = abs(freq - c)
        if diff < min_diff:
            min_diff = diff
            ch_idx = idx

    ch_flags = [1, 1, 1]
    ch_flags[ch_idx] = 1 if is_loss else 0
    return pd.Series(ch_flags, index=['CH1', 'CH2', 'CH3'])

def build_features_and_labels(df):
    # Gán các cột CH1, CH2, CH3
    flags_df = df.apply(assign_channel_flags, axis=1)
    df = pd.concat([df, flags_df], axis=1)

    # Bảng tra cứu gói tin để tìm kênh tốt nhất ở mỗi mốc (packet_ID, size_of_message)
    # Theo công thức (19) của bài báo: "we label the data point with the channel that has highest RSSI"
    best_channel_lookup = {}
    for (src, size, pid), group in df.groupby(['source', 'size_of_message', 'packet_ID']):
        # Lọc các bản ghi thành công (RSSI != -1000)
        valid = group[group['RSSI'] > -900]
        if not valid.empty:
            # Chọn bản ghi có RSSI cao nhất
            best_row = valid.loc[valid['RSSI'].idxmax()]
            best_freq = best_row['frequency']
            # Tìm chỉ số kênh
            best_ch = int(np.argmin([abs(best_freq - c) for c in CHANNELS]))
        else:
            # Nếu cả 3 kênh đều mất ở slot này, chọn ngẫu nhiên kênh xoay vòng
            best_ch = int((pid) % NUM_CHANNELS)
        best_channel_lookup[(src, size, pid)] = best_ch

    samples = []

    # Quét qua từng node để đảm bảo tính liên tục của chuỗi thời gian
    for (source, size), group in df.groupby(['source', 'size_of_message']):
        group = group.sort_values(by=['packet_ID']).reset_index(drop=True)
        n = len(group)
        if n <= WINDOW_SIZE:
            continue

        for i in range(n - WINDOW_SIZE):
            window = group.iloc[i : i + WINDOW_SIZE]
            target_row = group.iloc[i + WINDOW_SIZE]

            # Vector đặc trưng gồm 8 thông số mỗi bước thời gian (tổng 8 * 10 = 80 đặc trưng)
            # Theo đúng dòng 64-73 file train_model_hopping.py của bài báo
            features = []
            for _, r in window.iterrows():
                features.extend([
                    float(r['CH1']),
                    float(r['CH2']),
                    float(r['CH3']),
                    float(r['SNR']),
                    float(r['RSSI']),
                    float(r['size_of_message']),
                    float(r['packet_ID']),
                    float(r['frequency'])
                ])

            # Nhãn mục tiêu C_i: kênh tối ưu ở bước tiếp theo
            target_pid = int(target_row['packet_ID'])
            label_ch = best_channel_lookup.get((source, size, target_pid), int(target_pid % NUM_CHANNELS))

            sample_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
            sample_dict['target_channel'] = label_ch
            sample_dict['source'] = source
            sample_dict['size_of_message'] = size
            samples.append(sample_dict)

    return pd.DataFrame(samples)

def main():
    print("=== BƯỚC 3: TẠO DATASET CHUỖI THỜI GIAN & GÁN NHÃN KÊNH (03_generate_dataset) ===")
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
    dataset = build_features_and_labels(combined)

    out_file = os.path.join(OUTPUT_DIR, "dataset_ready.csv")
    dataset.to_csv(out_file, index=False)
    print(f"[SUCCESS] Đã tạo dataset chuẩn bài báo: {len(dataset)} mẫu, mỗi mẫu {WINDOW_SIZE * 8} đặc trưng -> {out_file}")

if __name__ == "__main__":
    main()
