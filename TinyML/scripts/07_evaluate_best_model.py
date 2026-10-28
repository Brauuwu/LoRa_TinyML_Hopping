#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_evaluate_best_model.py
Đánh giá toàn diện mô hình tốt nhất (Separable 1D-CNN):
  1. Classification: Precision, Recall, F1-Score, Confusion Matrix
  2. Mạng LoRa: PDR, RSSI, SNR so sánh Random vs FCNN vs Best Model
  3. TinyML: Inference Latency, Params, TFLite size

Toàn bộ dữ liệu lấy từ file CSV thực nghiệm, không bịa số liệu.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import tensorflow as tf
from tensorflow.keras import layers, regularizers
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

CHANNELS_DATA = ["433_175", "433_375", "433_575"]
CHANNEL_LABELS = ["CH1 (433.175 MHz)", "CH2 (433.375 MHz)", "CH3 (433.575 MHz)"]
headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
SAMPLES_PER_CHANNEL = 10
NUM_CHANNELS = len(CHANNELS_DATA)
ONE_HOT = np.eye(NUM_CHANNELS)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/MLdataready")
READY_FILE = os.path.join(os.path.dirname(__file__), "../data/ready/dataset_ready.csv")
FORMATTED_DIR = os.path.join(os.path.dirname(__file__), "../data/formattedCSV")
OUT_DIR = os.path.join(os.path.dirname(__file__), "../models/comparison")
os.makedirs(OUT_DIR, exist_ok=True)


def load_data():
    if os.path.exists(READY_FILE):
        try:
            df_ready = pd.read_csv(READY_FILE)
            feat_cols = [c for c in df_ready.columns if c.startswith("feat_")]
            if len(feat_cols) == 80 and 'target_channel' in df_ready.columns:
                X_all = df_ready[feat_cols].values
                y_all = df_ready['target_channel'].values
                raw_inputs = X_all.reshape(-1, SAMPLES_PER_CHANNEL, 8)
                raw_outputs = tf.keras.utils.to_categorical(y_all, num_classes=NUM_CHANNELS)
                sample_meta = []
                for _, row in df_ready.iterrows():
                    sample_meta.append({
                        'size': int(row.get('size_of_message', 30)),
                        'pkt_id': 0,
                        'true_ch': int(row['target_channel'])
                    })
                return raw_inputs, raw_outputs, sample_meta
        except Exception:
            pass

    raw_inputs, raw_outputs, sample_meta = [], [], []

    for ch_idx in range(NUM_CHANNELS):
        ch = CHANNELS_DATA[ch_idx]
        csv_path = os.path.join(DATA_DIR, "ABC", f"{ch}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(DATA_DIR, "A", f"{ch}.csv")
        if not os.path.exists(csv_path):
            continue

        try:
            df = pd.read_csv(csv_path, names=headers, skiprows=1)
            num_rec = int(df.shape[0] / SAMPLES_PER_CHANNEL)
            target = ONE_HOT[ch_idx]

            for i in range(num_rec):
                tensor = []
                for j in range(SAMPLES_PER_CHANNEL):
                    idx = i * SAMPLES_PER_CHANNEL + j
                    tensor.append([
                        float(df['CH1'][idx]), float(df['CH2'][idx]), float(df['CH3'][idx]),
                        float(df['SNR'][idx]), float(df['RSSI'][idx]),
                        float(df['size_of_message'][idx]),
                        float(df['packet_ID'][idx]), float(df['frequency'][idx])
                    ])
                raw_inputs.append(tensor)
                raw_outputs.append(target)
                last_idx = (i + 1) * SAMPLES_PER_CHANNEL - 1
                sample_meta.append({
                    'size': int(df['size_of_message'][last_idx]),
                    'pkt_id': int(df['packet_ID'][last_idx]),
                    'true_ch': ch_idx
                })
        except Exception:
            pass

    if not raw_inputs:
        print("[INFO] Chưa có dữ liệu huấn luyện. Hãy đặt file log vào data/logs/ và chạy các bước 01 -> 02 -> 03 trước.")
        return np.array([]), np.array([]), []

    return np.array(raw_inputs), np.array(raw_outputs), sample_meta


def main():
    print("=== BƯỚC 7: ĐÁNH GIÁ TOÀN DIỆN MÔ HÌNH TỐT NHẤT ===")

    raw_inputs, raw_outputs, sample_meta = load_data()
    if len(raw_inputs) == 0:
        print("[ERROR] Không nạp được dữ liệu!")
        return

    N, T, F = raw_inputs.shape
    print(f"[DATA] {N} mẫu, chuỗi {T}x{F}")

    # Chuẩn hóa
    flat = raw_inputs.reshape(N * T, F)
    scaler = StandardScaler()
    flat_scaled = scaler.fit_transform(flat)
    X_seq = flat_scaled.reshape(N, T, F)
    X_flat = X_seq.reshape(N, T * F)

    idx_train, idx_temp = train_test_split(np.arange(N), test_size=0.4, random_state=SEED)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=SEED)

    y_train, y_val, y_test = raw_outputs[idx_train], raw_outputs[idx_val], raw_outputs[idx_test]

    # 1. Huấn luyện Separable 1D-CNN (mô hình tốt nhất)
    print("\n[1/3] Huấn luyện Separable 1D-CNN...")
    best_model = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.SeparableConv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.SeparableConv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Separable_1D_CNN")

    best_model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
                       loss='categorical_crossentropy', metrics=['accuracy'])
    best_model.fit(X_seq[idx_train], y_train, epochs=150, batch_size=8,
                   validation_data=(X_seq[idx_val], y_val), verbose=0)

    # 2. Huấn luyện FCNN Baseline để đối chứng
    print("[2/3] Huấn luyện Baseline FCNN...")
    fcnn_model = tf.keras.Sequential([
        layers.Input(shape=(T * F,)),
        layers.Dense(10, activation='relu'),
        layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4)),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Baseline_FCNN")

    fcnn_model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
                       loss='categorical_crossentropy', metrics=['accuracy'])
    fcnn_model.fit(X_flat[idx_train], y_train, epochs=150, batch_size=8,
                   validation_data=(X_flat[idx_val], y_val), verbose=0)

    # 3. Đánh giá Machine Learning
    print(f"\n{'='*80}")
    print("     PHẦN 1: CHỈ SỐ PHÂN LOẠI TRÊN TẬP TEST")
    print(f"{'='*80}")

    y_pred_prob = best_model.predict(X_seq[idx_test], verbose=0)
    y_pred_cls = np.argmax(y_pred_prob, axis=1)
    y_true_cls = np.argmax(y_test, axis=1)

    y_pred_fcnn = np.argmax(fcnn_model.predict(X_flat[idx_test], verbose=0), axis=1)

    clf_report = classification_report(y_true_cls, y_pred_cls, target_names=CHANNEL_LABELS, output_dict=True)
    print(pd.DataFrame(clf_report).transpose().to_string())

    # Inference latency
    num_runs = 500
    t0 = time.perf_counter()
    for _ in range(num_runs):
        _ = best_model(X_seq[idx_test][:1], training=False)
    t1 = time.perf_counter()
    latency_us = ((t1 - t0) / num_runs) * 1e6

    print(f"\n[HARDWARE METRICS]")
    print(f"  Inference Latency: {latency_us:.1f} µs ({latency_us/1000:.3f} ms)")
    print(f"  Parameters: {best_model.count_params()}")

    tflite_path = os.path.join(OUT_DIR, "Separable_1D_CNN.tflite")
    tflite_kb = os.path.getsize(tflite_path) / 1024.0 if os.path.exists(tflite_path) else 0
    print(f"  TFLite Size: {tflite_kb:.2f} KB")

    # 4. Mô phỏng hiệu năng mạng LoRa từ dữ liệu thực
    print(f"\n{'='*80}")
    print("     PHẦN 2: CHỈ SỐ MẠNG LORA (DỮ LIỆU THỰC)")
    print(f"{'='*80}")

    # Đọc dữ liệu kênh thực tế từ formattedCSV
    channel_data = {}
    for ch in CHANNELS_DATA:
        f_path = os.path.join(FORMATTED_DIR, f"A_B_C_{ch}.csv")
        if os.path.exists(f_path):
            channel_data[ch] = pd.read_csv(f_path)

    test_meta = [sample_meta[i] for i in idx_test]
    sizes = sorted(set(m['size'] for m in test_meta))

    sim_results = []
    for size in sizes:
        subset_idx = [i for i, m in enumerate(test_meta) if m['size'] == size]
        if not subset_idx:
            continue

        rand_choices = np.random.choice([0, 1, 2], size=len(subset_idx))
        fcnn_choices = [y_pred_fcnn[i] for i in subset_idx]
        best_choices = [y_pred_cls[i] for i in subset_idx]

        def eval_choices(choices):
            received, rssi_vals, snr_vals = 0, [], []
            for ch_idx in choices:
                ch_name = CHANNELS_DATA[ch_idx]
                df_ch = channel_data.get(ch_name)
                if df_ch is not None:
                    sub = df_ch[df_ch['size_of_message'] == size]
                    if not sub.empty:
                        sampled = sub.sample(1).iloc[0]
                        if sampled['RSSI'] != -1000:
                            received += 1
                            rssi_vals.append(sampled['RSSI'])
                            snr_vals.append(sampled['SNR'])
            total = len(choices)
            pdr = received / total if total > 0 else 0
            avg_rssi = np.mean(rssi_vals) if rssi_vals else -120.0
            avg_snr = np.mean(snr_vals) if snr_vals else -20.0
            return round(pdr, 3), round(avg_rssi, 1), round(avg_snr, 1)

        pdr_r, rssi_r, snr_r = eval_choices(rand_choices)
        pdr_f, rssi_f, snr_f = eval_choices(fcnn_choices)
        pdr_b, rssi_b, snr_b = eval_choices(best_choices)

        sim_results.append({
            'Payload_Size': size,
            'PDR_Random': pdr_r, 'PDR_FCNN': pdr_f, 'PDR_SepCNN': pdr_b,
            'RSSI_Random': rssi_r, 'RSSI_FCNN': rssi_f, 'RSSI_SepCNN': rssi_b,
            'SNR_Random': snr_r, 'SNR_FCNN': snr_f, 'SNR_SepCNN': snr_b
        })

    sim_df = pd.DataFrame(sim_results)
    if not sim_df.empty:
        print(sim_df.to_string(index=False))
        sim_df.to_csv(os.path.join(OUT_DIR, "best_model_network_simulation.csv"), index=False)

    # 5. Vẽ biểu đồ tổng hợp (4 subplots)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # (a) Confusion Matrix
    cm = confusion_matrix(y_true_cls, y_pred_cls)
    cm_pct = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    sns.heatmap(cm_pct, annot=True, fmt='.1f', cmap='Blues', ax=axes[0, 0],
                xticklabels=CHANNEL_LABELS, yticklabels=CHANNEL_LABELS)
    axes[0, 0].set_title('(a) Confusion Matrix (%)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Predicted Channel')
    axes[0, 0].set_ylabel('True Channel')

    if not sim_df.empty:
        x = np.arange(len(sizes))

        # (b) PDR
        axes[0, 1].plot(x, sim_df['PDR_Random'], 'r--o', label='Random', linewidth=2)
        axes[0, 1].plot(x, sim_df['PDR_FCNN'], 'b--s', label='Baseline FCNN', linewidth=2)
        axes[0, 1].plot(x, sim_df['PDR_SepCNN'], 'g-^', label='Separable 1D-CNN', linewidth=2.5)
        axes[0, 1].set_title('(b) PDR theo Payload Size', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Payload Size (Bytes)')
        axes[0, 1].set_ylabel('PDR')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(sizes)
        axes[0, 1].set_ylim(0.0, 1.05)
        axes[0, 1].legend()
        axes[0, 1].grid(True, linestyle='--', alpha=0.6)

        # (c) RSSI
        w = 0.25
        axes[1, 0].bar(x - w, sim_df['RSSI_Random'], w, label='Random', color='#d62728')
        axes[1, 0].bar(x, sim_df['RSSI_FCNN'], w, label='FCNN', color='#1f77b4')
        axes[1, 0].bar(x + w, sim_df['RSSI_SepCNN'], w, label='SepCNN', color='#2ca02c')
        axes[1, 0].set_title('(c) Average RSSI (dBm)', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Payload Size (Bytes)')
        axes[1, 0].set_ylabel('RSSI (dBm)')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(sizes)
        axes[1, 0].legend()
        axes[1, 0].grid(axis='y', linestyle='--', alpha=0.6)

        # (d) SNR
        axes[1, 1].bar(x - w, sim_df['SNR_Random'], w, label='Random', color='#d62728')
        axes[1, 1].bar(x, sim_df['SNR_FCNN'], w, label='FCNN', color='#1f77b4')
        axes[1, 1].bar(x + w, sim_df['SNR_SepCNN'], w, label='SepCNN', color='#2ca02c')
        axes[1, 1].set_title('(d) Average SNR (dB)', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Payload Size (Bytes)')
        axes[1, 1].set_ylabel('SNR (dB)')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(sizes)
        axes[1, 1].legend()
        axes[1, 1].grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    eval_fig = os.path.join(OUT_DIR, "best_model_evaluation.png")
    plt.savefig(eval_fig, dpi=300)
    plt.close()
    print(f"\n[OK] Biểu đồ đánh giá: {eval_fig}")

    print(f"\n{'='*80}")
    print("     HOÀN TẤT ĐÁNH GIÁ")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
