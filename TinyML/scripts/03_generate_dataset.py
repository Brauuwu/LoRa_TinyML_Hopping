#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_dataset.py
Tạo các tập dữ liệu Machine Learning từ dữ liệu đã qua bổ sung gói mất (imputed):

1. Tạo thư mục MLData/ (phân chia theo từng End-Node A, B, C):
   - data/MLData/A/ : Chứa các file đo liên quan đến Node A
   - data/MLData/B/ : Chứa các file đo liên quan đến Node B
   - data/MLData/C/ : Chứa các file đo liên quan đến Node C
   - Bổ sung các cờ kênh CH1, CH2, CH3 dựa trên tần số và chất lượng thu.

2. Tạo thư mục MLdataready/ (tổng hợp theo từng kênh tần số):
   - data/MLdataready/A/   : 433_175.csv, 433_375.csv, 433_575.csv (cho Node A)
   - data/MLdataready/B/   : 433_175.csv, 433_375.csv, 433_575.csv (cho Node B)
   - data/MLdataready/C/   : 433_175.csv, 433_375.csv, 433_575.csv (cho Node C)
   - data/MLdataready/ABC/ : 433_175.csv, 433_375.csv, 433_575.csv (tổng hợp cả 3 Node)

3. Tạo file dataset_ready.csv trong data/ready/:
   - Cửa sổ trượt chuỗi thời gian (Sliding Window, ts = 10 bước)
   - Vector 80 đặc trưng input, nhãn kênh tối ưu (target_channel)
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "../data/imputed")
FORMATTED_DIR = os.path.join(SCRIPT_DIR, "../data/formattedCSV")
MLDATA_DIR = os.path.join(SCRIPT_DIR, "../data/MLData")
MLDATAREADY_DIR = os.path.join(SCRIPT_DIR, "../data/MLdataready")
READY_DIR = os.path.join(SCRIPT_DIR, "../data/ready")

# Khởi tạo các thư mục đầu ra
for d in [MLDATA_DIR, MLDATAREADY_DIR, READY_DIR]:
    os.makedirs(d, exist_ok=True)

for node in ['A', 'B', 'C']:
    os.makedirs(os.path.join(MLDATA_DIR, node), exist_ok=True)
    os.makedirs(os.path.join(MLDATAREADY_DIR, node), exist_ok=True)
os.makedirs(os.path.join(MLDATAREADY_DIR, "ABC"), exist_ok=True)

# Cấu hình tần số các kênh (tự động nhận dạng 433 MHz hoặc 868 MHz)
CHANNELS_433 = [("433_175", 433.175), ("433_375", 433.375), ("433_575", 433.575)]
CHANNELS_868 = [("868", 868.0), ("869", 869.0), ("870", 870.0)]

WINDOW_SIZE = 10


def detect_channel_config(df):
    freqs = df['frequency'].dropna().values
    if len(freqs) == 0:
        return CHANNELS_433
    mean_f = np.mean(freqs)
    return CHANNELS_868 if mean_f > 600.0 else CHANNELS_433


def assign_channel_flags(df, channels_cfg):
    """Gán 3 cờ kênh CH1, CH2, CH3 cho DataFrame"""
    f1, f2, f3 = channels_cfg[0][1], channels_cfg[1][1], channels_cfg[2][1]

    def _get_flags(row):
        f = row['frequency']
        is_loss = (row['RSSI'] <= -900)
        c1 = 0 if (abs(f - f1) < 0.1 and not is_loss) else 1
        c2 = 0 if (abs(f - f2) < 0.1 and not is_loss) else 1
        c3 = 0 if (abs(f - f3) < 0.1 and not is_loss) else 1
        return pd.Series([c1, c2, c3], index=['CH1', 'CH2', 'CH3'])

    flags = df.apply(_get_flags, axis=1)
    return pd.concat([df, flags], axis=1)


def generate_mldata_and_ready(files, channels_cfg):
    """
    1. Tạo MLData/{A, B, C}/
    2. Tạo MLdataready/{A, B, C, ABC}/
    """
    headers = ['packet_ID', 'source', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
    all_rows = []

    # BƯỚC 1: XỬ LÝ MLData THEO TỪNG NODE
    print(" [1/3] Đang phân tách dữ liệu theo từng Node vào data/MLData/{A, B, C}...")
    for filename in files:
        in_path = os.path.join(INPUT_DIR, filename)
        stem = os.path.splitext(filename)[0]

        try:
            df = pd.read_csv(in_path)
            df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce').astype(int)
            df['size_of_message'] = pd.to_numeric(df['size_of_message'], errors='coerce').astype(int)
            df['RSSI'] = pd.to_numeric(df['RSSI'], errors='coerce').astype(int)
            df['SNR'] = pd.to_numeric(df['SNR'], errors='coerce').astype(float)
            df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce').astype(float).round(3)
        except Exception:
            continue

        df_flagged = assign_channel_flags(df, channels_cfg)
        all_rows.append(df_flagged)

        for node in ['A', 'B', 'C']:
            node_sub = df_flagged[df_flagged['source'] == node]
            if not node_sub.empty:
                out_mldata = os.path.join(MLDATA_DIR, node, f"{stem}_{node}.csv")
                node_sub[headers].to_csv(out_mldata, index=False)

    if not all_rows:
        return None

    combined_df = pd.concat(all_rows, ignore_index=True)

    # BƯỚC 2: TỔNG HỢP VÀO MLdataready THEO KÊNH TẦN SỐ
    print(" [2/3] Đang nhóm theo kênh tần số vào data/MLdataready/{A, B, C, ABC}...")
    for ch_name, ch_freq in channels_cfg:
        # Lọc dữ liệu thuộc kênh tần số này
        ch_mask = (abs(combined_df['frequency'] - ch_freq) < 0.1)
        ch_df = combined_df[ch_mask]

        # 2a. Xuất cho từng Node
        for node in ['A', 'B', 'C']:
            node_ch = ch_df[ch_df['source'] == node]
            out_node_ch = os.path.join(MLDATAREADY_DIR, node, f"{ch_name}.csv")
            if not node_ch.empty:
                node_ch[headers].to_csv(out_node_ch, index=False)
            else:
                pd.DataFrame(columns=headers).to_csv(out_node_ch, index=False)

        # 2b. Xuất tổng hợp cho toàn mạng ABC
        out_abc = os.path.join(MLDATAREADY_DIR, "ABC", f"{ch_name}.csv")
        if not ch_df.empty:
            ch_df[headers].to_csv(out_abc, index=False)
            print(f"       + Kênh {ch_name} ({ch_freq} MHz): {len(ch_df)} dòng -> MLdataready/ABC/{ch_name}.csv")

    return combined_df


def build_sliding_window_dataset(df, channels_cfg):
    """
    BƯỚC 3: Xây dựng vector 80 chiều đặc trưng cửa sổ trượt (Sliding Window, ts=10)
    """
    print(" [3/3] Đang xây dựng tập đặc trưng cửa sổ trượt (Sliding Window ts=10)...")
    num_ch = len(channels_cfg)
    freqs = [c[1] for c in channels_cfg]

    # Bảng tra cứu kênh tốt nhất
    best_lookup = {}
    for (src, sz, pid), grp in df.groupby(['source', 'size_of_message', 'packet_ID']):
        valid = grp[grp['RSSI'] > -900]
        if not valid.empty:
            best_r = valid.loc[valid['RSSI'].idxmax()]
            best_c = int(np.argmin([abs(best_r['frequency'] - f) for f in freqs]))
        else:
            best_c = int(pid % num_ch)
        best_lookup[(src, sz, pid)] = best_c

    samples = []
    for (source, size), group in df.groupby(['source', 'size_of_message']):
        group = group.sort_values(by=['packet_ID']).reset_index(drop=True)
        n = len(group)
        if n <= WINDOW_SIZE:
            continue

        for i in range(n - WINDOW_SIZE):
            window = group.iloc[i: i + WINDOW_SIZE]
            target_row = group.iloc[i + WINDOW_SIZE]

            features = []
            for _, r in window.iterrows():
                features.extend([
                    float(r['CH1']), float(r['CH2']), float(r['CH3']),
                    float(r['SNR']), float(r['RSSI']),
                    float(r['size_of_message']), float(r['packet_ID']), float(r['frequency'])
                ])

            t_pid = int(target_row['packet_ID'])
            label_c = best_lookup.get((source, size, t_pid), int(t_pid % num_ch))

            s_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
            s_dict['target_channel'] = label_c
            s_dict['source'] = source
            s_dict['size_of_message'] = size
            samples.append(s_dict)

    dataset_df = pd.DataFrame(samples)
    out_file = os.path.join(READY_DIR, "dataset_ready.csv")
    dataset_df.to_csv(out_file, index=False)
    print(f"       + Đã lưu dataset_ready.csv: {len(dataset_df)} mẫu ({WINDOW_SIZE * 8} đặc trưng/mẫu)")
    return dataset_df


def main():
    print("=" * 74)
    print(" BƯỚC 3: PHÂN CHIA VÀ TẠO TẬP DỮ LIỆU MACHINE LEARNING (MLData & MLdataready)")
    print("=" * 74)

    target_dir = INPUT_DIR if (os.path.exists(INPUT_DIR) and os.listdir(INPUT_DIR)) else FORMATTED_DIR
    if not os.path.exists(target_dir):
        print(f"[ERROR] Thư mục nguồn {target_dir} chưa tồn tại!")
        return

    files = [f for f in sorted(os.listdir(target_dir)) if f.endswith(".csv")]
    if not files:
        print(f"[INFO] Chưa có file CSV trong: {target_dir}")
        print("       Vui lòng chạy 01_data_parser.py và 02_add_missed_packets.py trước!")
        return

    # Xác định tần số
    sample_p = os.path.join(target_dir, files[0])
    sample_df = pd.read_csv(sample_p)
    channels_cfg = detect_channel_config(sample_df)

    print(f" [+] Thư mục nguồn (Imputed)      : {target_dir} ({len(files)} file)")
    print(f" [+] Cấu hình kênh nhận diện      : {[c[0] for c in channels_cfg]}")
    print(f" [+] Thư mục phân chia theo Node  : {MLDATA_DIR}")
    print(f" [+] Thư mục gom nhóm theo Kênh   : {MLDATAREADY_DIR}")
    print(f" [+] Thư mục tập huấn luyện chung : {READY_DIR}")
    print("-" * 74)

    combined_df = generate_mldata_and_ready(files, channels_cfg)
    if combined_df is not None:
        build_sliding_window_dataset(combined_df, channels_cfg)

    print("-" * 74)
    print("[HOÀN THÀNH] Đã tạo thành công cấu trúc MLData và MLdataready chuẩn bài báo!")
    print("=" * 74)


if __name__ == "__main__":
    main()
