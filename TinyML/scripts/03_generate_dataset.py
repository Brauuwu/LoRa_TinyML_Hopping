#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_dataset.py
Tạo các tập dữ liệu Machine Learning từ dữ liệu đã qua bổ sung gói mất (imputed):

1. Tạo thư mục MLData/ (phân chia theo từng End-Node A, B, C và tách theo tần số):
   - data/MLData/A/ : Chứa các file đo của Node A tách riêng theo từng kênh tần số
   - data/MLData/B/ : Chứa các file đo của Node B tách riêng theo từng kênh tần số
   - data/MLData/C/ : Chứa các file đo của Node C tách riêng theo từng kênh tần số
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

        # Phân tách theo từng Node và theo từng KÊNH TẦN SỐ
        for node in ['A', 'B', 'C']:
            node_sub = df_flagged[df_flagged['source'] == node]
            if node_sub.empty:
                continue
            for ch_name, ch_freq in channels_cfg:
                node_ch_sub = node_sub[abs(node_sub['frequency'] - ch_freq) < 0.1]
                if not node_ch_sub.empty:
                    fname_out = f"{stem}_{node}.csv" if ch_name in stem else f"{stem}_{ch_name}_{node}.csv"
                    out_mldata = os.path.join(MLDATA_DIR, node, fname_out)
                    node_ch_sub[headers].to_csv(out_mldata, index=False)

    if not all_rows:
        return None

    combined_df = pd.concat(all_rows, ignore_index=True)

    # BƯỚC 2: TỔNG HỢP VÀO MLdataready THEO KÊNH TẦN SỐ
    print(" [2/3] Đang nhóm theo kênh tần số vào data/MLdataready/{A, B, C, ABC}...")
    ready_headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
    for ch_name, ch_freq in channels_cfg:
        # Lọc dữ liệu thuộc kênh tần số này
        ch_mask = (abs(combined_df['frequency'] - ch_freq) < 0.1)
        ch_df = combined_df[ch_mask]

        # 2a. Xuất cho từng Node
        for node in ['A', 'B', 'C']:
            node_ch = ch_df[ch_df['source'] == node]
            out_node_ch = os.path.join(MLDATAREADY_DIR, node, f"{ch_name}.csv")
            if not node_ch.empty:
                node_ch[ready_headers].to_csv(out_node_ch, index=False)
            else:
                pd.DataFrame(columns=ready_headers).to_csv(out_node_ch, index=False)

        # 2b. Xuất tổng hợp cho toàn mạng ABC
        out_abc = os.path.join(MLDATAREADY_DIR, "ABC", f"{ch_name}.csv")
        if not ch_df.empty:
            ch_df[ready_headers].to_csv(out_abc, index=False)
            print(f"       + Kênh {ch_name} ({ch_freq} MHz): {len(ch_df)} dòng -> MLdataready/ABC/{ch_name}.csv")

    return combined_df


def build_sliding_window_dataset(files, target_dir, channels_cfg):
    """
    BƯỚC 3 (PHƯƠNG ÁN 1): Xây dựng vector 80 chiều đặc trưng chuỗi thời gian sạch (10 bước x 8 đặc trưng)
    Loại bỏ hoàn toàn rò rỉ nhãn (Target Leakage):
    - Không chứa cột tần số tuyệt đối (frequency)
    - Không chứa cờ nhãn tĩnh (CH1, CH2, CH3)
    8 đặc trưng thực tế:
      1. channel_idx (0, 1, 2)
      2. is_loss (1.0 nếu mất/va chạm, 0.0 nếu nhận tốt)
      3. rssi (-120 dBm nếu mất gói)
      4. snr (-20 dB nếu mất gói)
      5. payload_size (30..250 byte)
      6. rolling_loss (tỷ lệ mất gói 5 bước gần nhất)
      7. consecutive_losses (số gói mất liên tiếp)
      8. channel_streak (số bước liên tiếp trên kênh)
    """
    print(" [3/3] Đang xây dựng tập đặc trưng cửa sổ trượt Phương án 1 (Sliding Window ts=10, 8 đặc trưng/bước)...")
    freqs = [c[1] for c in channels_cfg]

    def get_channel_idx(f):
        return int(np.argmin([abs(f - target_f) for target_f in freqs]))

    samples = []
    for filename in files:
        in_path = os.path.join(target_dir, filename)
        stem = os.path.splitext(filename)[0]
        parts = stem.split('_')
        freq_str = parts[-1]
        freq = float(freq_str[:3] + '.' + freq_str[3:]) if len(freq_str) == 6 else float(freq_str)
        cur_ch = get_channel_idx(freq)

        try:
            df = pd.read_csv(in_path)
        except Exception:
            continue

        for (src, sz), grp in df.groupby(['source', 'size_of_message']):
            grp = grp.sort_values(by='packet_ID').reset_index(drop=True)
            if len(grp) < WINDOW_SIZE:
                continue

            is_loss_arr = (grp['RSSI'] <= -900).astype(float).values
            rssi_arr = np.where(grp['RSSI'] <= -900, -120.0, grp['RSSI'].astype(float).values)
            snr_arr = np.where(grp['SNR'] <= -900, -20.0, grp['SNR'].astype(float).values)
            sz_arr = grp['size_of_message'].astype(float).values

            rolling_loss = pd.Series(is_loss_arr).rolling(window=5, min_periods=1).mean().values

            consec_losses = np.zeros(len(grp))
            count = 0
            for idx, l in enumerate(is_loss_arr):
                count = count + 1 if l == 1.0 else 0
                consec_losses[idx] = count
            streak_arr = np.arange(1, len(grp) + 1, dtype=float)

            for i in range(len(grp) - WINDOW_SIZE):
                features = []
                for k in range(i, i + WINDOW_SIZE):
                    features.extend([
                        float(cur_ch),
                        is_loss_arr[k],
                        rssi_arr[k],
                        snr_arr[k],
                        sz_arr[k],
                        rolling_loss[k],
                        consec_losses[k],
                        streak_arr[k]
                    ])

                w_loss = np.mean(is_loss_arr[i + 5 : i + WINDOW_SIZE])
                if w_loss <= 0.1 and consec_losses[i + WINDOW_SIZE - 1] == 0:
                    target = cur_ch
                else:
                    alt = [c for c in [0, 1, 2] if c != cur_ch]
                    target = alt[0] if src == 'A' else (alt[1] if src == 'B' else (alt[0] if i % 2 == 0 else alt[1]))

                s_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
                s_dict['target_channel'] = target
                s_dict['current_channel'] = cur_ch
                s_dict['source'] = src
                s_dict['size_of_message'] = sz
                samples.append(s_dict)

    dataset_df = pd.DataFrame(samples)
    out_file = os.path.join(READY_DIR, "dataset_ready.csv")
    dataset_df.to_csv(out_file, index=False)
    print(f"       + Đã lưu dataset_ready.csv: {len(dataset_df)} mẫu ({WINDOW_SIZE * 8} đặc trưng/mẫu)")
    print(f"       + Phân bố nhãn Kênh: CH0={sum(dataset_df['target_channel']==0)}, CH1={sum(dataset_df['target_channel']==1)}, CH2={sum(dataset_df['target_channel']==2)}")
    stay_pct = (dataset_df['target_channel'] == dataset_df['current_channel']).mean() * 100
    print(f"       + Tỷ lệ giữ nguyên kênh (Stay): {stay_pct:.1f}% | Nhảy kênh (Hop): {100 - stay_pct:.1f}%")
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
    if files:
        build_sliding_window_dataset(files, target_dir, channels_cfg)

    print("-" * 74)
    print("[HOÀN THÀNH] Đã tạo thành công cấu trúc MLData và MLdataready!")
    print("=" * 74)


if __name__ == "__main__":
    main()
