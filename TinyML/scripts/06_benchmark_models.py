#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_benchmark_models.py
Huấn luyện và so sánh các kiến trúc mạng nơ-ron cho Channel Hopping:
  1. Baseline FCNN (MLP)
  2. 1D-CNN (Temporal Convolution)
  3. GRU (Gated Recurrent Unit)
  4. Depthwise Separable 1D-CNN (MobileNet-style)
  5. Residual 1D-CNN (ResNet-1D)

Đọc dữ liệu chuỗi thời gian từ data/MLdataready/ABC/,
tự nhận dạng cấu hình kênh (433 MHz hoặc 868 MHz).
Huấn luyện đồng thời, so sánh Accuracy/Params/TFLite size.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import regularizers, layers, models
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MLDATA_READY_DIR = os.path.join(SCRIPT_DIR, "../data/MLdataready")
READY_FILE = os.path.join(SCRIPT_DIR, "../data/ready/dataset_ready.csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "../models/comparison")
os.makedirs(OUT_DIR, exist_ok=True)

headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
SAMPLES_PER_CHANNEL = 10


def detect_channels():
    """Tự động nhận dạng cấu hình kênh từ MLdataready/ABC/."""
    abc_dir = os.path.join(MLDATA_READY_DIR, "ABC")
    if not os.path.isdir(abc_dir):
        return None
    channel_names = sorted([
        os.path.splitext(f)[0]
        for f in os.listdir(abc_dir) if f.endswith(".csv")
    ])
    return channel_names if channel_names else None


def load_data():
    """
    Nạp dữ liệu chuỗi thời gian (Phương án 1):
    Ưu tiên đọc trực tiếp từ data/ready/dataset_ready.csv.
    """
    if os.path.exists(READY_FILE):
        try:
            df_ready = pd.read_csv(READY_FILE)
            feat_cols = [c for c in df_ready.columns if c.startswith("feat_")]
            if len(feat_cols) == 90 and 'target_channel' in df_ready.columns:
                X_all = df_ready[feat_cols].values
                y_all = df_ready['target_channel'].values
                num_ch = len(np.unique(y_all))
                raw_inputs = X_all.reshape(-1, SAMPLES_PER_CHANNEL, 9)
                raw_outputs = tf.keras.utils.to_categorical(y_all, num_classes=num_ch)
                return raw_inputs, raw_outputs
        except Exception:
            pass

    channel_names = detect_channels()
    if channel_names:
        NUM_CHANNELS = len(channel_names)
        ONE_HOT = np.eye(NUM_CHANNELS)
        raw_inputs, raw_outputs = [], []

        for ch_idx, ch_name in enumerate(channel_names):
            csv_path = os.path.join(MLDATA_READY_DIR, "ABC", f"{ch_name}.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(MLDATA_READY_DIR, "A", f"{ch_name}.csv")
            if not os.path.exists(csv_path):
                continue

            target = ONE_HOT[ch_idx]
            df = pd.read_csv(csv_path)
            feature_cols = ['CH1', 'CH2', 'CH3', 'SNR', 'RSSI', 'size_of_message', 'packet_ID', 'frequency']
            if not all(c in df.columns for c in feature_cols):
                df = pd.read_csv(csv_path, names=['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency'], skiprows=1)
            df = df.reset_index(drop=True)
            if not all(c in df.columns for c in feature_cols):
                continue

            arr = df[feature_cols].to_numpy(dtype=float)
            num_recordings = int(len(arr) / SAMPLES_PER_CHANNEL)

            for i in range(num_recordings):
                tensor = arr[i * SAMPLES_PER_CHANNEL : (i + 1) * SAMPLES_PER_CHANNEL].tolist()
                raw_inputs.append(tensor)
                raw_outputs.append(target)

        if raw_inputs:
            return np.array(raw_inputs), np.array(raw_outputs)

    print("[INFO] Chưa có dữ liệu huấn luyện. Hãy đặt file log vào data/logs/ và chạy các bước 01 → 03 trước.")
    return np.array([]), np.array([])


# ── Định nghĩa các kiến trúc mô hình ─────────────────────────────────────

def build_fcnn(T, F, num_ch):
    """1. Baseline FCNN"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T * F,)),
        layers.Dense(10, activation='relu'),
        layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4)),
        layers.Dense(num_ch, activation='softmax')
    ], name="Baseline_FCNN")
    return m, True


def build_cnn1d(T, F, num_ch):
    """2. 1D-CNN (Temporal Convolution)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.Conv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling1D(pool_size=2),
        layers.Conv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(16, activation='relu'),
        layers.Dense(num_ch, activation='softmax')
    ], name="1D_CNN")
    return m, False


def build_gru(T, F, num_ch):
    """3. GRU (Gated Recurrent Unit)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.GRU(16, return_sequences=False),
        layers.Dense(16, activation='relu'),
        layers.Dense(num_ch, activation='softmax')
    ], name="GRU_RNN")
    return m, False


def build_separable_cnn(T, F, num_ch):
    """4. Depthwise Separable 1D-CNN (MobileNet-style)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.SeparableConv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.SeparableConv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(num_ch, activation='softmax')
    ], name="Separable_1D_CNN")
    return m, False


def build_resnet1d(T, F, num_ch):
    """5. Residual 1D-CNN (ResNet-1D với Skip Connection)"""
    inputs = layers.Input(shape=(T, F))
    x = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(inputs)

    # Residual Block
    res = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(x)
    res = layers.Conv1D(16, kernel_size=3, padding='same')(res)
    x = layers.add([x, res])
    x = layers.Activation('relu')(x)

    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(16, activation='relu')(x)
    outputs = layers.Dense(num_ch, activation='softmax')(x)

    m = models.Model(inputs=inputs, outputs=outputs, name="ResNet_1D")
    return m, False


def main():
    print("=" * 72)
    print(" BƯỚC 6: SO SÁNH KIẾN TRÚC MẠNG NƠ-RON (BENCHMARK)")
    print("=" * 72)

    raw_inputs, raw_outputs = load_data()
    if len(raw_inputs) == 0:
        print("[ERROR] Không nạp được dữ liệu!")
        return

    N, T, F = raw_inputs.shape
    NUM_CHANNELS = raw_outputs.shape[1]
    print(f"[DATA] {N} mẫu, chuỗi {T} bước x {F} đặc trưng, {NUM_CHANNELS} kênh")

    # Chuẩn hóa StandardScaler
    flattened = raw_inputs.reshape(N * T, F)
    scaler = StandardScaler()
    flattened_scaled = scaler.fit_transform(flattened)
    X_seq = flattened_scaled.reshape(N, T, F)
    X_flat = X_seq.reshape(N, T * F)

    # Chia tập train/val/test cố định
    idx_train, idx_temp = train_test_split(np.arange(N), test_size=0.4, random_state=SEED)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=SEED)

    y_train = raw_outputs[idx_train]
    y_val = raw_outputs[idx_val]
    y_test = raw_outputs[idx_test]

    model_factories = [build_fcnn, build_cnn1d, build_gru, build_separable_cnn, build_resnet1d]
    results = []
    EPOCHS = 100
    BATCH_SIZE = 32

    for factory in model_factories:
        model, is_flat = factory(T, F, NUM_CHANNELS)
        name = model.name
        print(f"\n{'='*55}")
        print(f" Đang huấn luyện: {name}")
        print(f"{'='*55}")

        X_tr = X_flat[idx_train] if is_flat else X_seq[idx_train]
        X_v = X_flat[idx_val] if is_flat else X_seq[idx_val]
        X_te = X_flat[idx_test] if is_flat else X_seq[idx_test]

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=100, restore_best_weights=True)
        lr_sched = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=1e-5)

        model.fit(X_tr, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE,
                  validation_data=(X_v, y_val), callbacks=[early_stop, lr_sched], verbose=0)

        loss, acc = model.evaluate(X_te, y_test, verbose=0)
        params_count = model.count_params()

        # Chuyển sang TFLite
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        try:
            tflite_bytes = converter.convert()
            tflite_kb = len(tflite_bytes) / 1024.0
            with open(os.path.join(OUT_DIR, f"{name}.tflite"), "wb") as f:
                f.write(tflite_bytes)
        except Exception as e:
            print(f"[WARN] TFLite convert error: {e}")
            tflite_kb = -1

        results.append({
            'Model': name,
            'Test_Accuracy': round(acc * 100, 2),
            'Test_Loss': round(loss, 4),
            'Params': params_count,
            'TFLite_Size_KB': round(tflite_kb, 2),
            'Input_Type': 'Flat' if is_flat else f'Sequence ({T},{F})',
        })
        print(f"--> {name:<22} | Acc: {acc*100:.2f}% | Loss: {loss:.4f} | "
              f"Params: {params_count} | TFLite: {tflite_kb:.2f} KB")

    # Bảng tổng hợp
    df_res = pd.DataFrame(results)
    print(f"\n{'='*80}")
    print("         BẢNG SO SÁNH KIẾN TRÚC MẠNG NƠ-RON")
    print(f"{'='*80}")
    print(df_res.to_string(index=False))
    df_res.to_csv(os.path.join(OUT_DIR, "comparison_summary.csv"), index=False)

    # Biểu đồ so sánh trực quan
    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
    plt.figure(figsize=(14, 4.8), dpi=300)

    plt.subplot(1, 3, 1)
    bars = plt.bar(df_res['Model'], df_res['Test_Accuracy'], color=colors, width=0.55)
    plt.title('Test Accuracy (%)', fontsize=11, fontweight='bold')
    plt.xlabel('Model', fontsize=9.5)
    plt.ylabel('Accuracy (%)', fontsize=9.5)
    plt.xticks(rotation=25, ha='right', fontsize=8.5)
    plt.ylim(0, 108)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 1.2,
                 f"{yval:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.subplot(1, 3, 2)
    bars = plt.bar(df_res['Model'], df_res['Params'], color=colors, width=0.55)
    plt.title('Parameter Count', fontsize=11, fontweight='bold')
    plt.xlabel('Model', fontsize=9.5)
    plt.ylabel('Parameters', fontsize=9.5)
    plt.xticks(rotation=25, ha='right', fontsize=8.5)
    max_p = max(df_res['Params']) if len(df_res['Params']) > 0 else 1000
    plt.ylim(0, max_p * 1.15)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + max_p * 0.02,
                 f"{int(yval):,}", ha='center', va='bottom', fontsize=8.5)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.subplot(1, 3, 3)
    bars = plt.bar(df_res['Model'], df_res['TFLite_Size_KB'], color=colors, width=0.55)
    plt.title('Flash Footprint (KB)', fontsize=11, fontweight='bold')
    plt.xlabel('Model', fontsize=9.5)
    plt.ylabel('Size (KB)', fontsize=9.5)
    plt.xticks(rotation=25, ha='right', fontsize=8.5)
    max_s = max(df_res['TFLite_Size_KB']) if len(df_res['TFLite_Size_KB']) > 0 else 50
    plt.ylim(0, max_s * 1.18)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + max_s * 0.02,
                 f"{yval:.1f} KB", ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, "architectures_comparison.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"\n[OK] Biểu đồ so sánh: {fig_path}")


if __name__ == "__main__":
    main()
