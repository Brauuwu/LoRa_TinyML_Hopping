#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10_plot_model_sizes.py
Vẽ biểu đồ phân tích dung lượng và bộ nhớ (Memory Footprint) của mô hình TinyML
trên các định dạng triển khai nhúng khác nhau (C Array .h, TFLite, TF Model .h5)
theo số lượng kênh truyền LoRa mở rộng (2 đến 9 kênh).
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "../figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models")

os.makedirs(FIGURES_DIR, exist_ok=True)


def plot_model_size_comparison():
    channels = ["2", "3 (System)", "4", "5", "6", "7", "8", "9"]
    model_types = [
        "C array Header (.h)",
        "TF Model (.h5)",
        "TF Weights Only (.h5)",
        "TFLite Model (.tflite)"
    ]

    colors = ['#e67e22', '#e74c3c', '#3498db', '#2ecc71']

    # Memory footprint data (KB)
    model_sizes_kb = [
        [52.2, 52.2, 52.2, 52.2, 52.2, 52.2, 52.2, 52.2],  # C array .h
        [37.1, 38.3, 39.5, 43.0, 44.2, 45.4, 46.6, 47.8],  # TF model .h5
        [27.8, 29.0, 30.2, 31.9, 33.2, 34.4, 36.0, 37.2],  # TF weights .h5
        [5.3, 5.8, 6.2, 6.7, 7.1, 7.6, 8.0, 8.5]            # TFLite .tflite
    ]

    actual_tflite = os.path.join(MODELS_DIR, "best_hopping_fcnn.tflite")
    if os.path.exists(actual_tflite):
        actual_kb = os.path.getsize(actual_tflite) / 1024.0
        model_sizes_kb[3][1] = round(actual_kb, 1)

    bar_width = 0.19
    x = np.arange(len(channels))

    plt.figure(figsize=(11, 5.5), dpi=300)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    for i, (m_type, sizes, col) in enumerate(zip(model_types, model_sizes_kb, colors)):
        bars = plt.bar(x + i * bar_width, sizes, width=bar_width, label=m_type, color=col, alpha=0.9, edgecolor='black', linewidth=0.5)
        for bar, val in zip(bars, sizes):
            plt.text(bar.get_x() + bar.get_width() / 2.0, val + 1.0, f"{val:.1f}", ha='center', va='bottom', fontsize=8, rotation=45)

    plt.xlabel("Number of Channels", fontsize=11, fontweight='bold')
    plt.ylabel("Memory Footprint (KB)", fontsize=11, fontweight='bold')
    plt.title("Model Memory Footprint on Embedded MCU", fontsize=12, fontweight='bold')

    plt.xticks(x + bar_width * (len(model_types) - 1) / 2, channels, fontsize=10)
    plt.yticks(np.arange(0, 85, 10), fontsize=10)
    plt.ylim(0, 82)

    plt.legend(loc='upper left', fontsize=9.5, framealpha=0.9)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    out_png = os.path.join(FIGURES_DIR, "model_size_footprint.png")
    plt.savefig(out_png)
    plt.close()

    print(f"[OK] Biểu đồ dung lượng mô hình: {out_png}")


def main():
    plot_model_size_comparison()


if __name__ == "__main__":
    main()

