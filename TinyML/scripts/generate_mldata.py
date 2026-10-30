#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_mldata.py
Script chuyên biệt tự động hóa toàn diện quá trình sinh thư mục MLData và MLdataready.
Chức năng:
  1. Quét toàn bộ file trong data/imputed/ (hoặc data/formattedCSV/).
  2. Tách dữ liệu theo từng Node (A, B, C), gắn cờ kênh CH1, CH2, CH3
     -> Lưu vào data/MLData/{A, B, C}/
  3. Gom nhóm toàn bộ dữ liệu theo từng kênh tần số
     -> Lưu vào data/MLdataready/{A, B, C, ABC}/{433_175.csv, 433_375.csv, 433_575.csv}
        (hoặc {868.csv, 869.csv, 870.csv} nếu sử dụng băng tần 868 MHz).

Cách chạy:
  python generate_mldata.py
  python generate_mldata.py [duong_dan_thu_muc_imputed]
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
DEFAULT_INPUT_DIR = os.path.join(SCRIPT_DIR, "../data/imputed")
FORMATTED_DIR = os.path.join(SCRIPT_DIR, "../data/formattedCSV")
MLDATA_DIR = os.path.join(SCRIPT_DIR, "../data/MLData")
MLDATAREADY_DIR = os.path.join(SCRIPT_DIR, "../data/MLdataready")

# Tạo sẵn cấu trúc thư mục
for node in ['A', 'B', 'C']:
    os.makedirs(os.path.join(MLDATA_DIR, node), exist_ok=True)
    os.makedirs(os.path.join(MLDATAREADY_DIR, node), exist_ok=True)
os.makedirs(os.path.join(MLDATAREADY_DIR, "ABC"), exist_ok=True)

CHANNELS_433 = [("433_175", 433.175), ("433_375", 433.375), ("433_575", 433.575)]
CHANNELS_868 = [("868", 868.0), ("869", 869.0), ("870", 870.0)]


def detect_channel_config(df):
    freqs = df['frequency'].dropna().values
    if len(freqs) == 0:
        return CHANNELS_433
    mean_f = np.mean(freqs)
    return CHANNELS_868 if mean_f > 600.0 else CHANNELS_433


def assign_channel_flags(df, channels_cfg):
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


def generate_all(input_dir=None):
    target_dir = input_dir if (input_dir and os.path.isdir(input_dir)) else (
        DEFAULT_INPUT_DIR if os.path.exists(DEFAULT_INPUT_DIR) and os.listdir(DEFAULT_INPUT_DIR) else FORMATTED_DIR
    )

    if not os.path.exists(target_dir):
        print(f"[ERROR] Thư mục nguồn {target_dir} chưa tồn tại!")
        return

    files = [f for f in sorted(os.listdir(target_dir)) if f.endswith(".csv")]
    if not files:
        print(f"[INFO] Không tìm thấy file CSV nào trong {target_dir}")
        print("       Vui lòng chạy 01_data_parser.py và 02_add_missed_packets.py trước!")
        return

    # Nhận diện tần số
    sample_p = os.path.join(target_dir, files[0])
    sample_df = pd.read_csv(sample_p)
    channels_cfg = detect_channel_config(sample_df)

    print("=" * 74)
    print(" SCRIPT TỰ ĐỘNG SINH DỮ LIỆU: MLData & MLdataready")
    print("=" * 74)
    print(f" [+] Thư mục nguồn (Input)  : {target_dir} ({len(files)} files)")
    print(f" [+] Hệ thống kênh nhận diện: {[c[0] for c in channels_cfg]}")
    print(f" [+] Thư mục MLData         : {MLDATA_DIR}")
    print(f" [+] Thư mục MLdataready    : {MLDATAREADY_DIR}")
    print("-" * 74)

    headers = ['packet_ID', 'source', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
    all_dfs = []
    file_counts = {'A': 0, 'B': 0, 'C': 0}

    # BƯỚC 1: XUẤT RA MLData/{A, B, C}/
    print(" [1/2] Đang tách dữ liệu theo Node và gắn cờ kênh vào MLData/{A, B, C}...")
    for fname in files:
        fpath = os.path.join(target_dir, fname)
        stem = os.path.splitext(fname)[0]

        try:
            df = pd.read_csv(fpath)
            df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce').astype(int)
            df['size_of_message'] = pd.to_numeric(df['size_of_message'], errors='coerce').astype(int)
            df['RSSI'] = pd.to_numeric(df['RSSI'], errors='coerce').astype(int)
            df['SNR'] = pd.to_numeric(df['SNR'], errors='coerce').astype(float)
            df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce').astype(float).round(3)
        except Exception:
            continue

        df_flagged = assign_channel_flags(df, channels_cfg)
        all_dfs.append(df_flagged)

        for node in ['A', 'B', 'C']:
            node_data = df_flagged[df_flagged['source'] == node]
            if not node_data.empty:
                out_path = os.path.join(MLDATA_DIR, node, f"{stem}_{node}.csv")
                node_data[headers].to_csv(out_path, index=False)
                file_counts[node] += 1

    print(f"       + Node A: {file_counts['A']} files trong data/MLData/A/")
    print(f"       + Node B: {file_counts['B']} files trong data/MLData/B/")
    print(f"       + Node C: {file_counts['C']} files trong data/MLData/C/")

    if not all_dfs:
        print("[ERROR] Không trích xuất được dòng dữ liệu nào.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)

    # BƯỚC 2: XUẤT RA MLdataready/{A, B, C, ABC}/ THEO TỪNG KÊNH
    print("\n [2/2] Đang gom nhóm theo kênh tần số vào MLdataready/{A, B, C, ABC}...")
    for ch_name, ch_freq in channels_cfg:
        ch_data = combined[abs(combined['frequency'] - ch_freq) < 0.1]

        # Cho từng Node A, B, C
        for node in ['A', 'B', 'C']:
            node_ch = ch_data[ch_data['source'] == node]
            out_node_file = os.path.join(MLDATAREADY_DIR, node, f"{ch_name}.csv")
            if not node_ch.empty:
                node_ch[headers].to_csv(out_node_file, index=False)
            else:
                pd.DataFrame(columns=headers).to_csv(out_node_file, index=False)

        # Cho toàn mạng ABC
        out_abc_file = os.path.join(MLDATAREADY_DIR, "ABC", f"{ch_name}.csv")
        if not ch_data.empty:
            ch_data[headers].to_csv(out_abc_file, index=False)
            print(f"       + Kênh {ch_name} ({ch_freq} MHz): {len(ch_data):,} dòng -> data/MLdataready/ABC/{ch_name}.csv")

    print("-" * 74)
    print("[HOÀN THÀNH] Toàn bộ cấu trúc MLData và MLdataready đã được sinh thành công!")
    print("=" * 74)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    generate_all(target)


if __name__ == "__main__":
    main()
