#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08_pdr_calculation.py
Tính toán chi tiết tỉ lệ truyền thành công (Packet Delivery Ratio - PDR)
và thống kê chất lượng liên kết vô tuyến (RSSI, SNR) theo từng Node và kích thước gói tin.
Chuyển hóa từ PDR_calculation.py trong bài báo LoRaEdgeTinyML.

Cách chạy:
  python 08_pdr_calculation.py
  python 08_pdr_calculation.py [input_dir_or_file]
"""

import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/imputed")
FORMATTED_DIR = os.path.join(os.path.dirname(__file__), "../data/formattedCSV")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/ready")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data(source_path=None):
    if source_path and os.path.isfile(source_path):
        return pd.read_csv(source_path)

    target_dir = source_path if (source_path and os.path.isdir(source_path)) else (
        INPUT_DIR if os.path.exists(INPUT_DIR) and os.listdir(INPUT_DIR) else FORMATTED_DIR
    )

    if not os.path.exists(target_dir):
        return None

    csv_files = [f for f in os.listdir(target_dir) if f.endswith(".csv")]
    if not csv_files:
        return None

    dfs = [pd.read_csv(os.path.join(target_dir, f)) for f in csv_files]
    return pd.concat(dfs, ignore_index=True)


def calculate_pdr_metrics(df):
    if df is None or df.empty:
        print("[ERROR] Không có dữ liệu để tính toán PDR.")
        return None

    df['RSSI'] = pd.to_numeric(df['RSSI'], errors='coerce')
    df['SNR'] = pd.to_numeric(df['SNR'], errors='coerce')
    df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce')
    df['size_of_message'] = pd.to_numeric(df['size_of_message'], errors='coerce')

    # Phân loại gói nhận thành công và gói mất
    received_df = df[df['RSSI'] > -900]
    lost_df = df[df['RSSI'] <= -900]

    total_pkts = len(df)
    recv_pkts = len(received_df)
    lost_pkts = len(lost_df)
    overall_pdr = (recv_pkts / total_pkts * 100.0) if total_pkts > 0 else 0.0

    print("=" * 76)
    print(" BÁO CÁO TỔNG QUAN TỈ LỆ TRUYỀN THÀNH CÔNG (PDR - PACKET DELIVERY RATIO)")
    print("=" * 76)
    print(f" [+] Tổng số gói tin đã phát : {total_pkts:,} gói")
    print(f" [+] Số gói Gateway nhận được: {recv_pkts:,} gói")
    print(f" [+] Số gói bị mất (Collision): {lost_pkts:,} gói")
    print(f" [+] Tỉ lệ PDR toàn hệ thống : {overall_pdr:.2f} %")
    print(f" [+] Tỉ lệ mất gói (PLR)     : {100.0 - overall_pdr:.2f} %")
    print("-" * 76)

    # Thống kê chi tiết theo Source Node & Payload Size
    records = []
    grouped = df.groupby(['source', 'size_of_message'])

    for (src, size), grp in grouped:
        n_total = len(grp)
        grp_recv = grp[grp['RSSI'] > -900]
        n_recv = len(grp_recv)
        n_lost = n_total - n_recv
        pdr = (n_recv / n_total * 100.0) if n_total > 0 else 0.0

        mean_rssi = grp_recv['RSSI'].mean() if n_recv > 0 else np.nan
        mean_snr = grp_recv['SNR'].mean() if n_recv > 0 else np.nan

        records.append({
            'source': src,
            'size_of_message': int(size),
            'total_packets': n_total,
            'received_packets': n_recv,
            'lost_packets': n_lost,
            'PDR_percent': round(pdr, 2),
            'avg_RSSI': round(mean_rssi, 2) if not np.isnan(mean_rssi) else -1000.0,
            'avg_SNR': round(mean_snr, 2) if not np.isnan(mean_snr) else -1000.0
        })

    summary_df = pd.DataFrame(records).sort_values(by=['source', 'size_of_message']).reset_index(drop=True)

    print(f"{'Node':<6} | {'Kích thước':<10} | {'Tổng gói':<10} | {'Nhận':<8} | {'Mất':<6} | {'PDR (%)':<10} | {'RSSI TB':<10} | {'SNR TB':<10}")
    print("-" * 76)
    for _, r in summary_df.iterrows():
        print(f" {r['source']:<5} | {int(r['size_of_message']):<10} | {int(r['total_packets']):<10} | {int(r['received_packets']):<8} | {int(r['lost_packets']):<6} | {r['PDR_percent']:<10.2f} | {r['avg_RSSI']:<10.1f} | {r['avg_SNR']:<10.1f}")
    print("=" * 76)

    out_file = os.path.join(OUTPUT_DIR, "pdr_summary.csv")
    summary_df.to_csv(out_file, index=False)
    print(f"[OK] Bảng tổng kết PDR đã được lưu tại: {out_file}\n")
    return summary_df


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    df = load_data(target)
    calculate_pdr_metrics(df)


if __name__ == "__main__":
    main()
