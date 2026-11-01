#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_plot_hopping_comparison.py
Vẽ biểu đồ cột trực quan hóa so sánh hiệu năng thực nghiệm giữa 2 cơ chế:
  - Random Channel Hopping (Nhảy kênh ngẫu nhiên - Baseline)
  - TinyML Predictive Hopping (Nhảy kênh thích nghi bằng mô hình học máy)

Các biểu đồ xuất bản khoa học (DPI 300, Academic Style):
  1. Average SNR Chart (dB) theo kích thước gói tin
  2. Average RSSI Chart (dBm) theo kích thước gói tin
  3. Packet Delivery Ratio (PDR %) theo kích thước gói tin
  4. Multi-panel Chart tổng hợp 3 chỉ tiêu (performance_comparison.png)

Dữ liệu được nạp 100% từ bảng tính thực nghiệm (TinyML/data/ready/comparison_metrics.csv).
Hoàn toàn dựa trên 100% dữ liệu đo đạc thực nghiệm.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
READY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/ready"))
FIGURES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../figures"))

os.makedirs(FIGURES_DIR, exist_ok=True)


def load_metrics():
    """Nạp bảng thống kê thực nghiệm từ Bước 05."""
    comp_file = os.path.join(READY_DIR, "comparison_metrics.csv")
    if not os.path.exists(comp_file):
        comp_file = os.path.join(FIGURES_DIR, "comparison_results_table.csv")

    if not os.path.exists(comp_file):
        print(f"[WARN] Chưa có {comp_file}. Đang gọi tự động Bước 05 để tính toán từ dữ liệu thực tế...")
        import subprocess
        script_05 = os.path.join(SCRIPT_DIR, "05_evaluate_comparison.py")
        subprocess.run([sys.executable, script_05], check=True)

    df = pd.read_csv(comp_file)
    print(f"[DATA] Đã nạp dữ liệu đối sánh thực nghiệm từ: {comp_file}")
    return df


def plot_charts(df):
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    sizes = df['size_of_message'].values
    x = np.arange(len(sizes))
    width = 0.35

    color_random = '#1f77b4'
    color_tinyml = '#2ca02c'

    # ──────────────────────────────────────────────────────────────────────────
    # 1. BIỂU ĐỒ AVERAGE SNR (dB)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    b_rnd = ax.bar(x - width / 2, df['SNR_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_ml  = ax.bar(x + width / 2, df['SNR_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)

    ax.set_xlabel('Payload Size (Bytes)', fontsize=10.5, fontweight='bold')
    ax.set_ylabel('Average SNR (dB)', fontsize=10.5, fontweight='bold')
    ax.set_title('Average SNR vs Payload Size', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sizes, fontsize=10)
    ax.set_ylim(0, 13.5)
    ax.legend(fontsize=9.5, loc='upper right', framealpha=0.95)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in b_rnd:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.15, f"{yval:.1f}", ha='center', va='bottom', fontsize=8)
    for bar in b_ml:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.15, f"{yval:.1f}", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    snr_path = os.path.join(FIGURES_DIR, "Average_SNR_Chart.png")
    plt.savefig(snr_path)
    plt.close()
    print(f"  [OK] Đã lưu biểu đồ SNR : {snr_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. BIỂU ĐỒ AVERAGE RSSI (dBm)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    b_rnd = ax.bar(x - width / 2, df['RSSI_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_ml  = ax.bar(x + width / 2, df['RSSI_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)

    ax.set_xlabel('Payload Size (Bytes)', fontsize=10.5, fontweight='bold')
    ax.set_ylabel('Average RSSI (dBm)', fontsize=10.5, fontweight='bold')
    ax.set_title('Average RSSI vs Payload Size', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sizes, fontsize=10)
    ax.set_ylim(-125, -10)
    ax.legend(fontsize=9.5, loc='lower left', framealpha=0.95)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in b_rnd:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval - 2.2, f"{yval:.1f}", ha='center', va='top', fontsize=8)
    for bar in b_ml:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval - 2.2, f"{yval:.1f}", ha='center', va='top', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    rssi_path = os.path.join(FIGURES_DIR, "Average_RSSI_Chart.png")
    plt.savefig(rssi_path)
    plt.close()
    print(f"  [OK] Đã lưu biểu đồ RSSI: {rssi_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. BIỂU ĐỒ PACKET DELIVERY RATIO (PDR %)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    b_rnd = ax.bar(x - width / 2, df['PDR_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_ml  = ax.bar(x + width / 2, df['PDR_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)

    ax.set_xlabel('Payload Size (Bytes)', fontsize=10.5, fontweight='bold')
    ax.set_ylabel('PDR (%)', fontsize=10.5, fontweight='bold')
    ax.set_title('Packet Delivery Ratio (PDR) vs Payload Size', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sizes, fontsize=10)
    ax.set_ylim(0, 130)
    ax.legend(fontsize=9.5, loc='upper left', framealpha=0.95)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in b_rnd:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8)
    for bar in b_ml:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    pdr_path = os.path.join(FIGURES_DIR, "PDR_Chart.png")
    plt.savefig(pdr_path)
    plt.close()
    print(f"  [OK] Đã lưu biểu đồ PDR : {pdr_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. BIỂU ĐỒ TỔNG HỢP MULTI-PANEL (performance_comparison.png)
    # ──────────────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.0), dpi=300)

    # Panel 1: RSSI
    b_r0 = axes[0].bar(x - width / 2, df['RSSI_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_m0 = axes[0].bar(x + width / 2, df['RSSI_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)
    axes[0].set_title('(a) Average RSSI (dBm)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Payload Size (Bytes)', fontsize=10)
    axes[0].set_ylabel('RSSI (dBm)', fontsize=10)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(sizes, fontsize=9.5)
    axes[0].set_ylim(-125, -10)
    axes[0].legend(loc='lower left', fontsize=9.5, framealpha=0.95)
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)
    for bar in b_r0:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width() / 2.0, yval - 2.2, f"{yval:.1f}", ha='center', va='top', fontsize=8)
    for bar in b_m0:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width() / 2.0, yval - 2.2, f"{yval:.1f}", ha='center', va='top', fontsize=8.5, fontweight='bold')

    # Panel 2: SNR
    b_r1 = axes[1].bar(x - width / 2, df['SNR_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_m1 = axes[1].bar(x + width / 2, df['SNR_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)
    axes[1].set_title('(b) Average SNR (dB)', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Payload Size (Bytes)', fontsize=10)
    axes[1].set_ylabel('SNR (dB)', fontsize=10)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(sizes, fontsize=9.5)
    axes[1].set_ylim(0, 13.5)
    axes[1].legend(loc='upper right', fontsize=9.5, framealpha=0.95)
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)
    for bar in b_m1:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width() / 2.0, yval + 0.15, f"{yval:.1f}", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    # Panel 3: PDR
    b_r2 = axes[2].bar(x - width / 2, df['PDR_Random'], width, label='Random Hopping', color=color_random, alpha=0.9)
    b_m2 = axes[2].bar(x + width / 2, df['PDR_TinyML'], width, label='TinyML Hopping', color=color_tinyml, alpha=0.9)
    axes[2].set_title('(c) Packet Delivery Ratio (PDR %)', fontsize=11, fontweight='bold')
    axes[2].set_xlabel('Payload Size (Bytes)', fontsize=10)
    axes[2].set_ylabel('PDR (%)', fontsize=10)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(sizes, fontsize=9.5)
    axes[2].set_ylim(0, 130)
    axes[2].legend(loc='upper left', fontsize=9.5, framealpha=0.95)
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)
    for bar in b_m2:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    multi_path = os.path.join(FIGURES_DIR, "performance_comparison.png")
    plt.savefig(multi_path)
    plt.close()
    print(f"  [OK] Đã lưu biểu đồ tổng hợp 3 panels: {multi_path}")


def main():
    print("=" * 76)
    print(" BƯỚC 9: TRỰC QUAN HÓA SO SÁNH HIỆU NĂNG NHẢY KÊNH (RANDOM VS TINYML)")
    print("=" * 76)

    df = load_metrics()
    plot_charts(df)
    print("\n[HOÀN TẤT] Bước 9 đã xuất bản thành công 4 biểu đồ khoa học!")


if __name__ == "__main__":
    main()
