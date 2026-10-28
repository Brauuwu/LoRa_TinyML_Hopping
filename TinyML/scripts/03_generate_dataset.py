#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_dataset.py
Tạo dataset huấn luyện từ dữ liệu đã imputed:
- Gán cờ trạng thái kênh CH1, CH2, CH3 (0 = khả dụng, 1 = bận/mất)
- Xây dựng đặc trưng chuỗi thời gian (Sliding Window, ts = 10 bước)
- Gán nhãn kênh tối ưu (kênh có RSSI cao nhất tại bước tiếp theo)
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

# 3 tần số làm việc hệ thống (433 MHz ISM Band)
CHANNELS = [433.175, 433.375, 433.575]
NUM_CHANNELS = len(CHANNELS)

# Kích thước cửa sổ trượt bộ nhớ thời gian
WINDOW_SIZE = 10


def assign_channel_flags(row):
    """
    Xác định vector trạng thái kênh [CH1, CH2, CH3]:
    - Kênh đang phát và thu tốt: flag = 0
    - Kênh đang phát nhưng mất gói: flag = 1
    - Kênh không phát ở slot này: flag = 1
    """
    freq = row['frequency']
    is_loss = (row['RSSI'] == -1000)

    ch_idx = int(np.argmin([abs(freq - c) for c in CHANNELS]))

    ch_flags = [1, 1, 1]
    ch_flags[ch_idx] = 1 if is_loss else 0
    return pd.Series(ch_flags, index=['CH1', 'CH2', 'CH3'])


def build_features_and_labels(df):
    # Gán cờ kênh
    flags_df = df.apply(assign_channel_flags, axis=1)
    df = pd.concat([df, flags_df], axis=1)

    # Tìm kênh tốt nhất tại từng mốc (kênh có RSSI cao nhất)
    best_channel_lookup = {}
    for (src, size, pid), group in df.groupby(['source', 'size_of_message', 'packet_ID']):
        valid = group[group['RSSI'] > -900]
        if not valid.empty:
            best_row = valid.loc[valid['RSSI'].idxmax()]
            best_ch = int(np.argmin([abs(best_row['frequency'] - c) for c in CHANNELS]))
        else:
            best_ch = int(pid % NUM_CHANNELS)
        best_channel_lookup[(src, size, pid)] = best_ch

    samples = []

    for (source, size), group in df.groupby(['source', 'size_of_message']):
        group = group.sort_values(by=['packet_ID']).reset_index(drop=True)
        n = len(group)
        if n <= WINDOW_SIZE:
            continue

        for i in range(n - WINDOW_SIZE):
            window = group.iloc[i: i + WINDOW_SIZE]
            target_row = group.iloc[i + WINDOW_SIZE]

            # 8 đặc trưng mỗi bước: CH1, CH2, CH3, SNR, RSSI, size, pkt_id, freq
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

            target_pid = int(target_row['packet_ID'])
            label_ch = best_channel_lookup.get(
                (source, size, target_pid),
                int(target_pid % NUM_CHANNELS)
            )

            sample_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
            sample_dict['target_channel'] = label_ch
            sample_dict['source'] = source
            sample_dict['size_of_message'] = size
            samples.append(sample_dict)

    return pd.DataFrame(samples)


def main():
    print("=== BƯỚC 3: TẠO DATASET CHUỖI THỜI GIAN & GÁN NHÃN KÊNH ===")
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Thư mục {INPUT_DIR} chưa tồn tại!")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("[WARN] Chưa có file dữ liệu trong imputed/.")
        return

    all_dfs = []
    for f in files:
        p = os.path.join(INPUT_DIR, f)
        all_dfs.append(pd.read_csv(p))

    combined = pd.concat(all_dfs, ignore_index=True)
    dataset = build_features_and_labels(combined)

    out_file = os.path.join(OUTPUT_DIR, "dataset_ready.csv")
    dataset.to_csv(out_file, index=False)
    print(f"[SUCCESS] Đã tạo dataset: {len(dataset)} mẫu, "
          f"mỗi mẫu {WINDOW_SIZE * 8} đặc trưng -> {out_file}")


if __name__ == "__main__":
    main()
