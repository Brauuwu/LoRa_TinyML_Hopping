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

Đọc dữ liệu thực tế từ data/MLdataready/, huấn luyện đồng thời,
so sánh Accuracy/Params/TFLite size.
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

# Các kênh tần số làm việc của hệ thống (433 MHz Band)
CHANNELS_DATA = ["433_175", "433_375", "433_575"]

headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
SAMPLES_PER_CHANNEL = 10
NUM_CHANNELS = len(CHANNELS_DATA)
ONE_HOT = np.eye(NUM_CHANNELS)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/MLdataready")
READY_FILE = os.path.join(os.path.dirname(__file__), "../data/ready/dataset_ready.csv")
OUT_DIR = os.path.join(os.path.dirname(__file__), "../models/comparison")
os.makedirs(OUT_DIR, exist_ok=True)


def load_data():
    """Nạp dữ liệu từ data/ready/dataset_ready.csv hoặc MLdataready"""
    if os.path.exists(READY_FILE):
        try:
            df_ready = pd.read_csv(READY_FILE)
            feat_cols = [c for c in df_ready.columns if c.startswith("feat_")]
            if len(feat_cols) == 80 and 'target_channel' in df_ready.columns:
                X_all = df_ready[feat_cols].values
                y_all = df_ready['target_channel'].values
                raw_inputs = X_all.reshape(-1, SAMPLES_PER_CHANNEL, 8)
                raw_outputs = tf.keras.utils.to_categorical(y_all, num_classes=NUM_CHANNELS)
                return raw_inputs, raw_outputs
        except Exception:
            pass

    raw_inputs = []
    raw_outputs = []

    for ch_idx in range(NUM_CHANNELS):
        ch = CHANNELS_DATA[ch_idx]

        csv_path = os.path.join(DATA_DIR, "ABC", f"{ch}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(DATA_DIR, "A", f"{ch}.csv")
        if not os.path.exists(csv_path):
            continue

        try:
            df = pd.read_csv(csv_path, names=headers, skiprows=1)
            num_recordings = int(df.shape[0] / SAMPLES_PER_CHANNEL)
            target = ONE_HOT[ch_idx]

            for i in range(num_recordings):
                tensor = []
                for j in range(SAMPLES_PER_CHANNEL):
                    idx = i * SAMPLES_PER_CHANNEL + j
                    tensor.append([
                        float(df['CH1'][idx]),
                        float(df['CH2'][idx]),
                        float(df['CH3'][idx]),
                        float(df['SNR'][idx]),
                        float(df['RSSI'][idx]),
                        float(df['size_of_message'][idx]),
                        float(df['packet_ID'][idx]),
                        float(df['frequency'][idx])
                    ])
                raw_inputs.append(tensor)
                raw_outputs.append(target)
        except Exception:
            pass

    if not raw_inputs:
        print("[INFO] Chưa có dữ liệu huấn luyện. Hãy đặt file log vào data/logs/ và chạy các bước 01 -> 02 -> 03 trước.")
        return np.array([]), np.array([])

    return np.array(raw_inputs), np.array(raw_outputs)


# Định nghĩa các kiến trúc mô hình
def build_fcnn(T, F):
    m = tf.keras.Sequential([
        layers.Input(shape=(T * F,)),
        layers.Dense(10, activation='relu'),
        layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4)),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Baseline_FCNN")
    return m, True


def build_cnn1d(T, F):
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.Conv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling1D(pool_size=2),
        layers.Conv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(16, activation='relu'),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="1D_CNN")
    return m, False


def build_gru(T, F):
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.GRU(16, return_sequences=False),
        layers.Dense(16, activation='relu'),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="GRU_RNN")
    return m, False


def build_separable_cnn(T, F):
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.SeparableConv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.SeparableConv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Separable_1D_CNN")
    return m, False


def build_resnet1d(T, F):
    inputs = layers.Input(shape=(T, F))
    x = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(inputs)

    res = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(x)
    res = layers.Conv1D(16, kernel_size=3, padding='same')(res)
    x = layers.add([x, res])
    x = layers.Activation('relu')(x)

    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(16, activation='relu')(x)
    outputs = layers.Dense(NUM_CHANNELS, activation='softmax')(x)

    m = models.Model(inputs=inputs, outputs=outputs, name="ResNet_1D")
    return m, False


def main():
    print("=== BƯỚC 6: SO SÁNH KIẾN TRÚC MẠNG NƠ-RON ===")

    raw_inputs, raw_outputs = load_data()
    if len(raw_inputs) == 0:
        print("[ERROR] Không nạp được dữ liệu!")
        return

    N, T, F = raw_inputs.shape
    print(f"[DATA] {N} mẫu, chuỗi {T} bước x {F} đặc trưng")

    # Chuẩn hóa
    flattened = raw_inputs.reshape(N * T, F)
    scaler = StandardScaler()
    flattened_scaled = scaler.fit_transform(flattened)
    X_seq = flattened_scaled.reshape(N, T, F)
    X_flat = X_seq.reshape(N, T * F)

    # Chia tập cố định
    idx_train, idx_temp = train_test_split(np.arange(N), test_size=0.4, random_state=SEED)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=SEED)

    y_train = raw_outputs[idx_train]
    y_val = raw_outputs[idx_val]
    y_test = raw_outputs[idx_test]

    model_factories = [build_fcnn, build_cnn1d, build_gru, build_separable_cnn, build_resnet1d]
    results = []
    EPOCHS = 150
    BATCH_SIZE = 8

    for factory in model_factories:
        model, is_flat = factory(T, F)
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

        model.fit(X_tr, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE,
                  validation_data=(X_v, y_val), verbose=0)

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

    # Vẽ biểu đồ
    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    bars = plt.bar(df_res['Model'], df_res['Test_Accuracy'], color=colors)
    plt.title('Test Accuracy (%)', fontsize=12)
    plt.ylabel('Accuracy (%)')
    plt.xticks(rotation=25, ha='right')
    plt.ylim(min(df_res['Test_Accuracy']) - 5, 102)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5,
                 f"{yval:.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.subplot(1, 3, 2)
    bars = plt.bar(df_res['Model'], df_res['Params'], color=colors)
    plt.title('Parameters Count', fontsize=12)
    plt.ylabel('Parameters')
    plt.xticks(rotation=25, ha='right')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 10,
                 f"{yval}", ha='center', va='bottom', fontsize=9)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.subplot(1, 3, 3)
    bars = plt.bar(df_res['Model'], df_res['TFLite_Size_KB'], color=colors)
    plt.title('TFLite Size on MCU (KB)', fontsize=12)
    plt.ylabel('Size (KB)')
    plt.xticks(rotation=25, ha='right')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1,
                 f"{yval:.1f} KB", ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, "architectures_comparison.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"\n[OK] Biểu đồ so sánh: {fig_path}")


if __name__ == "__main__":
    main()
