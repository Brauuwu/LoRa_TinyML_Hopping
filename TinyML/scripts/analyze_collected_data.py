#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_collected_data.py
Script phân tích toàn diện bộ dữ liệu thực nghiệm đã thu thập từ Gateway:
1. Thống kê tổng số file, kịch bản, và tổng số gói tin thu được.
2. Thống kê theo từng Node (A, B, C) và từng tần số (433.175, 433.375, 433.575 MHz).
3. Đánh giá chất lượng đường truyền: RSSI, SNR (mean, min, max, std).
4. Phân tích xung đột & Tỷ lệ mất gói tin (Packet Loss Rate / PDR) theo từng kịch bản:
   - Đơn node (không xung đột)
   - 2 Node cùng phát (xung đột 2 bên)
   - 3 Node cùng phát (xung đột 3 bên)
5. Phát hiện hiệu ứng vô tuyến thực tế: Capture Effect, phân bố kích thước gói tin (Payload).
"""

import os
import glob
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(os.path.dirname(BASE_DIR), "GatewayCode", "csv")
LOG_DIR = os.path.join(os.path.dirname(BASE_DIR), "GatewayCode", "logs")

def analyze():
    csv_files = sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))
    if not csv_files:
        print(f"[LỖI] Không tìm thấy file CSV nào trong {CSV_DIR}")
        return

    all_dfs = []
    file_summaries = []

    for fpath in csv_files:
        fname = os.path.basename(fpath)
        name_no_ext = os.path.splitext(fname)[0]
        parts = name_no_ext.split("_")
        freq_str = parts[-1]
        freq = float(freq_str[:3] + "." + freq_str[3:]) if len(freq_str) == 6 else float(freq_str)
        scenario = "_".join(parts[:-1])

        try:
            df = pd.read_csv(fpath)
        except Exception as e:
            print(f"[CẢNH BÁO] Không thể đọc {fname}: {e}")
            continue

        df["file"] = fname
        df["scenario"] = scenario
        all_dfs.append(df)

        # Đánh giá theo từng node trong file: chuẩn thực nghiệm là 6 kích thước x 100 gói = 600 gói/node
        scenario_nodes = scenario.split("_")
        for src, grp in df.groupby("source"):
            if src not in scenario_nodes:
                continue  # Bỏ qua gói nhiễu ngoại lai không thuộc kịch bản đo
            # Lọc các gói tin hợp lệ
            valid_grp = grp[(grp["size_of_message"].isin([30, 74, 118, 162, 206, 250])) & (grp["packet_ID"] < 100)]
            received = len(valid_grp)
            expected = 600  # 6 sizes * 100 packets
            lost = max(0, expected - received)
            pdr = (received / expected * 100.0)

            file_summaries.append({
                "file": fname,
                "scenario": scenario,
                "frequency": freq,
                "source": src,
                "expected": expected,
                "received": received,
                "lost": lost,
                "pdr": pdr,
                "rssi_mean": valid_grp["RSSI"].mean(),
                "rssi_min": valid_grp["RSSI"].min(),
                "rssi_max": valid_grp["RSSI"].max(),
                "rssi_std": valid_grp["RSSI"].std() if len(valid_grp) > 1 else 0.0,
                "snr_mean": valid_grp["SNR"].mean(),
                "snr_min": valid_grp["SNR"].min(),
                "snr_max": valid_grp["SNR"].max(),
                "snr_std": valid_grp["SNR"].std() if len(valid_grp) > 1 else 0.0,
            })

    full_df = pd.concat(all_dfs, ignore_index=True)
    sum_df = pd.DataFrame(file_summaries)

    print("=" * 80)
    print("        BÁO CÁO PHÂN TÍCH TOÀN DIỆN DỮ LIỆU THỰC NGHIỆM THU THẬP TỪ GATEWAY       ")
    print("=" * 80)

    # 1. Tổng quan
    print("\n[1] TỔNG QUAN BỘ DỮ LIỆU (DATASET OVERVIEW)")
    print(f"  - Tổng số file kịch bản đo: {len(csv_files)} file CSV")
    print(f"  - Tổng số gói tin thu được hợp lệ: {len(full_df):,} gói tin")
    print(f"  - Các kênh tần số đã đo: {sorted(full_df['frequency'].unique())} MHz")
    print(f"  - Các Node tham gia: {sorted(full_df['source'].unique())}")
    print(f"  - Phân bố gói tin theo kích thước (Payload Sizes):")
    for sz, count in full_df["size_of_message"].value_counts().items():
        print(f"      + {sz} bytes: {count:,} gói ({count/len(full_df)*100:.1f}%)")

    # 2. Phân bố theo Node
    print("\n[2] PHÂN BỐ GÓI TIN VÀ TÍN HIỆU THEO TỪNG NODE")
    print(f"{'Node':<6} | {'Số gói thu':<12} | {'Tỷ lệ':<8} | {'RSSI Trung bình':<16} | {'SNR Trung bình':<16}")
    print("-" * 68)
    for src in sorted(full_df["source"].unique()):
        sub = full_df[full_df["source"] == src]
        cnt = len(sub)
        pct = cnt / len(full_df) * 100
        r_mean = sub["RSSI"].mean()
        r_std = sub["RSSI"].std()
        s_mean = sub["SNR"].mean()
        s_std = sub["SNR"].std()
        print(f"Node {src:<2} | {cnt:<12,} | {pct:<7.1f}% | {r_mean:6.2f} ± {r_std:4.2f} dBm  | {s_mean:5.2f} ± {s_std:4.2f} dB")

    # 3. Phân bố theo Tần số
    print("\n[3] CHẤT LƯỢNG KÊNH THEO TẦN SỐ (FREQUENCY CHANNELS)")
    print(f"{'Tần số (MHz)':<14} | {'Số gói thu':<12} | {'Tỷ lệ':<8} | {'RSSI Trung bình':<16} | {'SNR Trung bình':<16}")
    print("-" * 72)
    for fq in sorted(full_df["frequency"].unique()):
        sub = full_df[full_df["frequency"] == fq]
        cnt = len(sub)
        pct = cnt / len(full_df) * 100
        r_mean = sub["RSSI"].mean()
        r_std = sub["RSSI"].std()
        s_mean = sub["SNR"].mean()
        s_std = sub["SNR"].std()
        print(f"{fq:<14.3f} | {cnt:<12,} | {pct:<7.1f}% | {r_mean:6.2f} ± {r_std:4.2f} dBm  | {s_mean:5.2f} ± {s_std:4.2f} dB")

    # 4. Phân tích Xung đột & Tỷ lệ mất gói theo loại kịch bản
    print("\n[4] PHÂN TÍCH XUNG ĐỘT (COLLISION) & HIỆU SUẤT TRUYỀN (PDR) THEO KỊCH BẢN")
    def get_group_type(sc):
        nodes = sc.split("_")
        if len(nodes) == 1:
            return "1_Đơn Node (Không va chạm)"
        elif len(nodes) == 2:
            return "2_Đôi Node (Va chạm 2 bên)"
        elif len(nodes) == 3:
            return "3_Ba Node (Va chạm 3 bên)"
        return "Khác"

    sum_df["group_type"] = sum_df["scenario"].apply(get_group_type)

    for gtype, grp in sum_df.groupby("group_type"):
        total_exp = grp["expected"].sum()
        total_rec = grp["received"].sum()
        total_lost = grp["lost"].sum()
        avg_pdr = (total_rec / total_exp * 100) if total_exp > 0 else 0
        print(f"\n  ➤ Kịch bản: {gtype}")
        print(f"      - Tổng gói phát kỳ vọng : {total_exp:,}")
        print(f"      - Tổng gói thu được     : {total_rec:,}")
        print(f"      - Tổng gói bị mất/xung đột: {total_lost:,}")
        print(f"      - Tỷ lệ PDR trung bình  : {avg_pdr:.2f}% (Tỷ lệ mất gói: {100 - avg_pdr:.2f}%)")

    # 5. Chi tiết từng file kịch bản đo
    print("\n[5] BẢNG CHI TIẾT TỪNG PHIÊN ĐO (21 KỊCH BẢN)")
    print(f"{'Tên file':<18} | {'Node':<4} | {'Phát (kỳ vọng)':<15} | {'Thu (thành công)':<16} | {'Mất':<6} | {'PDR (%)':<8} | {'RSSI (dBm)':<11} | {'SNR (dB)':<9}")
    print("-" * 98)
    for _, row in sum_df.sort_values(by=["scenario", "frequency", "source"]).iterrows():
        print(f"{row['file']:<18} | {row['source']:<4} | {row['expected']:<15} | {row['received']:<16} | {row['lost']:<6} | {row['pdr']:<7.1f}% | {row['rssi_mean']:<11.1f} | {row['snr_mean']:<9.1f}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze()
