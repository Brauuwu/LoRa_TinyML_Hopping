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
    BƯỚC 3: Xây dựng tập dữ liệu Chuỗi thời gian Ground-Truth Tối ưu Đa kênh (Cross-Channel Ground-Truth):
    - Đồng bộ hoá theo (kịch bản, node phát, kích thước tải, packet_ID) trên cả 3 kênh.
    - 9 đặc trưng chuỗi thời gian (10 bước x 9 đặc trưng = 90 chiều):
        1. is_loss (1.0 nếu mất gói/va chạm, 0.0 nếu nhận tốt)
        2. rssi (cường độ tín hiệu, -120 dBm nếu mất gói)
        3. snr (tỷ số tín hiệu trên nhiễu, -20 dB nếu mất gói)
        4. payload_size (30..250 byte)
        5. rolling_loss_5 (tỷ lệ mất gói 5 bước gần nhất)
        6. consecutive_losses (số gói mất liên tiếp)
        7. delta_rssi (độ biến thiên RSSI so với gói trước)
        8. delta_snr (độ biến thiên SNR so với gói trước)
        9. current_channel (chỉ số kênh đang phát hiện tại của Node: 0, 1, 2)
    - Gán nhãn mục tiêu thực tế (Ground-Truth Target Label at t+1):
        + Nếu kênh hiện tại truyền tốt: target = cur_ch (duy trì kênh, tối thiểu hóa phụ phí)
        + Nếu kênh hiện tại bị va chạm/mất gói: target = argmax_{c != cur_ch} (RSSI_c + SNR_c)
          (nhảy sang kênh thay thế có phẩm chất đo lường thực tế tốt nhất tại bước tiếp theo)
    """
    print(" [3/3] Đang xây dựng tập đặc trưng cửa sổ trượt Ground-Truth Đa kênh (Cross-Channel Ground-Truth)...")
    
    # Nhận dạng các kịch bản đo từ danh sách file
    scenarios_set = set()
    for f in files:
        parts = os.path.splitext(f)[0].split('_')
        sc_name = "_".join(parts[:-1]) if len(parts) > 1 else parts[0]
        scenarios_set.add(sc_name)
    scenarios = sorted(list(scenarios_set))

    freq_tags = [c[0].replace("_", "") for c in channels_cfg]
    samples = []

    for sc in scenarios:
        f_paths = [os.path.join(target_dir, f"{sc}_{ft}.csv") for ft in freq_tags]
        if not all(os.path.exists(p) for p in f_paths):
            continue

        dfs = [pd.read_csv(p) for p in f_paths]
        df0 = dfs[0]

        for (src, sz), grp0 in df0.groupby(['source', 'size_of_message']):
            grp0 = grp0.sort_values('packet_ID').set_index('packet_ID')
            grp1 = dfs[1][(dfs[1]['source'] == src) & (dfs[1]['size_of_message'] == sz)].sort_values('packet_ID').set_index('packet_ID')
            grp2 = dfs[2][(dfs[2]['source'] == src) & (dfs[2]['size_of_message'] == sz)].sort_values('packet_ID').set_index('packet_ID')

            common_pids = sorted(list(grp0.index.intersection(grp1.index).intersection(grp2.index)))
            if len(common_pids) <= WINDOW_SIZE:
                continue

            dfs_ch = [grp0.loc[common_pids], grp1.loc[common_pids], grp2.loc[common_pids]]

            for cur_ch in range(3):
                cur_df = dfs_ch[cur_ch]
                is_loss_arr = (cur_df['RSSI'] <= -900).astype(float).values
                rssi_arr = np.where(cur_df['RSSI'] <= -900, -120.0, cur_df['RSSI'].astype(float).values)
                snr_arr = np.where(cur_df['SNR'] <= -900, -20.0, cur_df['SNR'].astype(float).values)
                sz_arr = cur_df['size_of_message'].astype(float).values

                rolling_loss = pd.Series(is_loss_arr).rolling(window=5, min_periods=1).mean().values
                consec_losses = np.zeros(len(common_pids))
                count = 0
                for idx, l in enumerate(is_loss_arr):
                    count = count + 1 if l == 1.0 else 0
                    consec_losses[idx] = count

                delta_rssi = np.diff(rssi_arr, prepend=rssi_arr[0])
                delta_snr = np.diff(snr_arr, prepend=snr_arr[0])

                for i in range(len(common_pids) - WINDOW_SIZE):
                    features = []
                    for k in range(i, i + WINDOW_SIZE):
                        features.extend([
                            is_loss_arr[k],
                            rssi_arr[k],
                            snr_arr[k],
                            sz_arr[k],
                            rolling_loss[k],
                            consec_losses[k],
                            delta_rssi[k],
                            delta_snr[k],
                            float(cur_ch)
                        ])

                    target_pid = common_pids[i + WINDOW_SIZE]
                    cur_loss = (dfs_ch[cur_ch].loc[target_pid, 'RSSI'] <= -900)

                    if not cur_loss:
                        target = cur_ch
                    else:
                        alt_channels = [c for c in range(3) if c != cur_ch]
                        scores = []
                        for c in alt_channels:
                            r_c = dfs_ch[c].loc[target_pid, 'RSSI']
                            s_c = dfs_ch[c].loc[target_pid, 'SNR']
                            score = -1000.0 if r_c <= -900 else (r_c + s_c)
                            scores.append(score)

                        best_alt_idx = int(np.argmax(scores))
                        target = alt_channels[best_alt_idx]

                    s_dict = {f"feat_{idx}": val for idx, val in enumerate(features)}
                    s_dict['target_channel'] = target
                    s_dict['current_channel'] = cur_ch
                    s_dict['source'] = src
                    s_dict['size_of_message'] = sz
                    samples.append(s_dict)

    dataset_df = pd.DataFrame(samples)
    out_file = os.path.join(READY_DIR, "dataset_ready.csv")
    dataset_df.to_csv(out_file, index=False)
    print(f"       + Đã lưu dataset_ready.csv: {len(dataset_df)} mẫu ({WINDOW_SIZE * 9} đặc trưng/mẫu: 10 bước x 9 đặc trưng)")
    print(f"       + Phân bố nhãn Kênh: CH0={sum(dataset_df['target_channel']==0)}, CH1={sum(dataset_df['target_channel']==1)}, CH2={sum(dataset_df['target_channel']==2)}")
    stay_pct = (dataset_df['target_channel'] == dataset_df['current_channel']).mean() * 100
    print(f"       + Tỷ lệ giữ nguyên kênh (Stay): {stay_pct:.1f}% | Nhảy kênh tránh va chạm (Hop): {100 - stay_pct:.1f}%")
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
