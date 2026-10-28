#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_train_model.py
Huấn luyện mô hình FCNN phân loại kênh LoRa tối ưu (Channel Hopping),
chuyển đổi sang TensorFlow Lite và xuất mã C header (model.h) cho ESP32.
"""

import os
import sys
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import tensorflow as tf
from tensorflow.keras import regularizers

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/ready/dataset_ready.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "../figures")
MCU_SRC_DIR = os.path.join(os.path.dirname(__file__), "../../MCUCode/LoRaEN_TinyMLHopping/src")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

NUM_CHANNELS = 3


def convert_bytes_to_c_header(tflite_bytes, output_path, array_name="model"):
    """Xuất mảng byte TFLite sang mảng C header cho ESP32"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Tự động sinh từ mô hình TinyML LoRa Channel Hopping\n")
        f.write(f"// Kích thước FlatBuffer: {len(tflite_bytes)} bytes (~{len(tflite_bytes)/1024:.1f} KB)\n\n")
        f.write(f"const unsigned char {array_name}[] = {{\n  ")
        for i, b in enumerate(tflite_bytes):
            f.write(f"0x{b:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n  ")
        f.write("\n};\n\n")
        f.write(f"const unsigned int {array_name}_len = {len(tflite_bytes)};\n")


def main():
    print("=== BƯỚC 4: HUẤN LUYỆN MÔ HÌNH TINYML ===")
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Không tìm thấy {DATA_FILE}. Chạy 03_generate_dataset.py trước!")
        return

    df = pd.read_csv(DATA_FILE)
    feat_cols = [c for c in df.columns if c.startswith("feat_")]
    X = df[feat_cols].values
    y = df['target_channel'].values

    y_onehot = tf.keras.utils.to_categorical(y, num_classes=NUM_CHANNELS)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Phân chia: 60% Train, 20% Val, 20% Test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_onehot, test_size=0.4, random_state=SEED, shuffle=True
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=SEED, shuffle=True
    )

    print(f"Tổng mẫu: {len(X)} | Input: {X.shape[1]} chiều")
    print(f"Train: {len(X_train)} (60%) | Val: {len(X_val)} (20%) | Test: {len(X_test)} (20%)")

    # Kiến trúc FCNN Baseline
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(10, activation='relu', input_shape=(X.shape[1],), name="dense_1"),
        tf.keras.layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4), name="dense_2_l1"),
        tf.keras.layers.Dense(NUM_CHANNELS, activation='softmax', name="channel_output")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.005),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    EPOCHS = 200
    BATCH_SIZE = 16
    print(f"\n[TRAINING] Bắt đầu {EPOCHS} Epochs (batch_size={BATCH_SIZE}, EarlyStopping patience=25)...")

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=25,
        restore_best_weights=True,
        verbose=1
    )

    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        verbose=1
    )

    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n{'='*55}")
    print(f" Test Accuracy: {test_acc * 100:.2f}% | Test Loss: {test_loss:.4f}")
    print(f"{'='*55}")

    # Vẽ đường cong huấn luyện
    epochs_range = range(1, EPOCHS + 1)
    train_acc = history.history['accuracy']
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']

    plt.figure(figsize=(10, 6))
    plt.plot(epochs_range, train_acc, 'g.', markersize=2, label='Training Accuracy')
    plt.plot(epochs_range, train_loss, 'r.', markersize=2, label='Training Loss')
    plt.plot(epochs_range, val_loss, 'b-', linewidth=1.5, label='Validation Loss')
    plt.title('Training Trends: Accuracy & Loss by Epoch')
    plt.xlabel('Epochs')
    plt.ylabel('Metrics')
    plt.ylim([0.0, 1.05])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='center right')

    fig_path = os.path.join(FIGURES_DIR, "training_trends.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[PLOT] Đã lưu biểu đồ: {fig_path}")

    # Chuyển đổi sang TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    tflite_path = os.path.join(MODELS_DIR, "channel_model.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"[EXPORT] TFLite: {tflite_path} ({len(tflite_model)} bytes ~ {len(tflite_model)/1024:.2f} KB)")

    # Xuất C Header
    header_path = os.path.join(MODELS_DIR, "model.h")
    convert_bytes_to_c_header(tflite_model, header_path, array_name="model")
    print(f"[EXPORT] C Header: {header_path} ({os.path.getsize(header_path)} bytes)")

    # Đồng bộ sang MCU nếu có
    if os.path.exists(MCU_SRC_DIR):
        dest_header = os.path.join(MCU_SRC_DIR, "model.h")
        shutil.copyfile(header_path, dest_header)
        print(f"[SYNC] Đã đồng bộ model.h -> {dest_header}")


if __name__ == "__main__":
    main()
