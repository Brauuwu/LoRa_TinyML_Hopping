#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_train_model.py
Chức năng: Huấn luyện mạng Nơ-ron FCNN phân loại kênh LoRa tối ưu,
           chuyển đổi sang TensorFlow Lite và xuất mã nguồn C array (model.h).
Dựa trên paper: arXiv:2412.01609v1 (LoRaEdgeTinyML)
"""

import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

NUM_CHANNELS = 3

def convert_bytes_to_c_header(tflite_bytes, output_path, array_name="model"):
    """Tự động chuyển mảng byte tflite sang mã nguồn C header (tương thích đa nền tảng)"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"// Tự động sinh từ mô hình TinyML LoRa Channel Hopping\n")
        f.write(f"// Kích thước mô hình: {len(tflite_bytes)} bytes\n\n")
        f.write(f"const unsigned char {array_name}[] = {{\n  ")
        for i, b in enumerate(tflite_bytes):
            f.write(f"0x{b:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n  ")
        f.write("\n};\n")
        f.write(f"const unsigned int {array_name}_len = {len(tflite_bytes)};\n")

def main():
    print("=== BƯỚC 4: HUẤN LUYỆN MÔ HÌNH TINYML CHO CHANNEL HOPPING ===")
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Không tìm thấy {DATA_FILE}. Vui lòng chạy 03_generate_dataset.py trước!")
        return

    df = pd.read_csv(DATA_FILE)
    feat_cols = [c for c in df.columns if c.startswith("feat_")]
    X = df[feat_cols].values
    y = df['target_channel'].values

    # One-hot encoding cho nhãn (3 kênh)
    y_onehot = tf.keras.utils.to_categorical(y, num_classes=NUM_CHANNELS)

    # Chuẩn hóa dữ liệu đầu vào
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Chia tập train (60%), val (20%), test (20%) theo đúng bài báo
    X_train, X_temp, y_train, y_temp = train_test_split(X, y_onehot, test_size=0.4, random_state=1337)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=1337)

    print(f"Dataset: Tổng {len(X)} mẫu | Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    # ── Xây dựng kiến trúc FCNN theo đúng Table II trong bài báo ─────────────
    # Model: Sequential: Dense(10, relu) -> Dense(10, L1) -> Dense(3, softmax)
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(10, activation='relu', input_shape=(X.shape[1],)),
        tf.keras.layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4)),
        tf.keras.layers.Dense(NUM_CHANNELS, activation='softmax')
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.005),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    # Huấn luyện mô hình
    history = model.fit(
        X_train, y_train,
        epochs=300,
        batch_size=16,
        validation_data=(X_val, y_val),
        verbose=1
    )

    # Đánh giá trên tập kiểm thử Test
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n[EVALUATION] Test Accuracy: {test_acc * 100:.2f}% | Test Loss: {test_loss:.4f}")

    # Vẽ và lưu biểu đồ Loss & Accuracy
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Train Accuracy', color='green')
    plt.plot(history.history['val_accuracy'], label='Val Accuracy', color='blue')
    plt.title('Độ chính xác theo Epoch')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Train Loss', color='red')
    plt.plot(history.history['val_loss'], label='Val Loss', color='orange')
    plt.title('Hàm mất mát (Loss) theo Epoch')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)

    fig_path = os.path.join(FIGURES_DIR, "training_trends.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[PLOT] Đã lưu biểu đồ huấn luyện: {fig_path}")

    # ── Chuyển đổi sang TensorFlow Lite (FlatBuffer) ──────────────────────────
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = os.path.join(MODELS_DIR, "channel_model.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"[EXPORT] Đã xuất model TFLite: {tflite_path} ({len(tflite_model)} bytes)")

    # ── Chuyển sang C Header file (model.h) cho ESP32 ────────────────────────
    header_path = os.path.join(MODELS_DIR, "model.h")
    convert_bytes_to_c_header(tflite_model, header_path, array_name="model")
    print(f"[EXPORT] Đã tạo header C: {header_path}")

    # Tự động đồng bộ sang thư mục src của Node ESP32 TinyML
    if os.path.exists(MCU_SRC_DIR):
        dest_header = os.path.join(MCU_SRC_DIR, "model.h")
        shutil.copyfile(header_path, dest_header)
        print(f"[SYNC] Đã đồng bộ model.h sang: {dest_header}")

if __name__ == "__main__":
    main()
