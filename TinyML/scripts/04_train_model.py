#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_train_model.py
Chức năng: Huấn luyện mạng Nơ-ron FCNN phân loại kênh LoRa tối ưu (Channel Hopping),
           đối sánh các chỉ số độ chính xác theo Figure 9 của bài báo,
           chuyển đổi sang TensorFlow Lite và xuất mã nguồn C array (model.h) cho ESP32.
Theo đúng kiến trúc và thông số trong Table II & Listing 1, 2 bài báo LoRaEdgeTinyML.
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
    """Xuất mảng byte TFLite sang định dạng mảng C trong file header (Listing 2 trong bài báo)"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// ==========================================================================\n")
        f.write("// Tự động sinh từ mô hình TinyML LoRa Channel Hopping (LoRaEdgeTinyML)\n")
        f.write(f"// Kích thước mô hình FlatBuffer: {len(tflite_bytes)} bytes (~{len(tflite_bytes)/1024:.1f} KB)\n")
        f.write("// ==========================================================================\n\n")
        f.write(f"const unsigned char {array_name}[] = {{\n  ")
        for i, b in enumerate(tflite_bytes):
            f.write(f"0x{b:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n  ")
        f.write("\n};\n\n")
        f.write(f"const unsigned int {array_name}_len = {len(tflite_bytes)};\n")

def main():
    print("=== BƯỚC 4: HUẤN LUYỆN MÔ HÌNH TINYML CHO CHANNEL HOPPING (04_train_model) ===")
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Không tìm thấy {DATA_FILE}. Vui lòng chạy 03_generate_dataset.py trước!")
        return

    df = pd.read_csv(DATA_FILE)
    feat_cols = [c for c in df.columns if c.startswith("feat_")]
    X = df[feat_cols].values
    y = df['target_channel'].values

    # One-hot encoding cho nhãn đầu ra (3 kênh tương ứng với softmax)
    y_onehot = tf.keras.utils.to_categorical(y, num_classes=NUM_CHANNELS)

    # Chuẩn hóa dữ liệu đầu vào bằng StandardScaler (dòng 84 train_model_hopping.py)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Phân chia dữ liệu theo đúng tỷ lệ bài báo: 60% Train, 20% Val, 20% Test (Section V.A.2)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y_onehot, test_size=0.4, random_state=SEED, shuffle=True)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=SEED, shuffle=True)

    print(f"Tổng số mẫu: {len(X)} | Input dimension: {X.shape[1]}")
    print(f"Phân chia tập: Train={len(X_train)} (60%), Val={len(X_val)} (20%), Test={len(X_test)} (20%)")

    # ── Kiến trúc mạng FCNN nguyên bản theo Table II của bài báo ─────────────
    # Sequential:
    #   - Dense(10, activation='relu')
    #   - Dense(10, activation='relu', kernel_regularizer=L1(1e-4))
    #   - Dense(NUM_CHANNELS, activation='softmax')
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

    # Huấn luyện mô hình 500 epochs (theo đồ thị Figure 9 trong bài báo)
    EPOCHS = 500
    BATCH_SIZE = 16
    print(f"\n[TRAINING] Bắt đầu huấn luyện {EPOCHS} Epochs (batch_size={BATCH_SIZE})...")
    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_val, y_val),
        verbose=1
    )

    # Đánh giá trên tập kiểm thử độc lập (Test Set)
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n=======================================================")
    print(f" [KẾT QUẢ ĐÁNH GIÁ] Test Accuracy: {test_acc * 100:.2f}% | Test Loss: {test_loss:.4f}")
    print(f"=======================================================")

    # ── Vẽ biểu đồ Figure 9 (Trends: Accuracy, Training Loss, and Validation Loss) ──
    epochs_range = range(1, EPOCHS + 1)
    train_acc = history.history['accuracy']
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']

    plt.figure(figsize=(10, 6))
    plt.plot(epochs_range, train_acc, 'g.', markersize=2, label='Training accuracy')
    plt.plot(epochs_range, train_loss, 'r.', markersize=2, label='Training loss')
    plt.plot(epochs_range, val_loss, 'b-', linewidth=1.5, label='Validation loss')
    plt.title('Figure 9: TinyML Model Performance Trends: Accuracy, Training Loss, and Validation Loss by Epoch')
    plt.xlabel('Epochs')
    plt.ylabel('Metrics')
    plt.ylim([0.0, 1.05])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='center right')

    fig9_path = os.path.join(FIGURES_DIR, "figure9_training_trends.png")
    plt.savefig(fig9_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[PLOT] Đã xuất biểu đồ Figure 9: {fig9_path}")

    # ── Chuyển đổi sang TensorFlow Lite (FlatBuffer) theo Listing 1 bài báo ───
    # Listing 1: "converter = tf.lite.TFLiteConverter.from_keras_model(model)"
    # Không áp dụng quantization ép kiểu để tránh lỗi op incompatibilities trên ESP32
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    tflite_path = os.path.join(MODELS_DIR, "channel_model.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    tflite_kb = len(tflite_model) / 1024.0
    print(f"[EXPORT] TFLite Model: {tflite_path} ({len(tflite_model)} bytes ~ {tflite_kb:.2f} KB - khớp Figure 11: ~5.8 KB)")

    # ── Xuất sang C Header file (model.h) theo Listing 2 ─────────────────────
    header_path = os.path.join(MODELS_DIR, "model.h")
    convert_bytes_to_c_header(tflite_model, header_path, array_name="model")
    print(f"[EXPORT] Header file C: {header_path} ({os.path.getsize(header_path)} bytes)")

    # Tự động đồng bộ sang thư mục nguồn của End-Node nếu có
    if os.path.exists(MCU_SRC_DIR):
        dest_header = os.path.join(MCU_SRC_DIR, "model.h")
        shutil.copyfile(header_path, dest_header)
        print(f"[SYNC] Đã đồng bộ model.h sang: {dest_header}")

if __name__ == "__main__":
    main()
