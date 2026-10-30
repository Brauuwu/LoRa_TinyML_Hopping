#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark_models.py
Huấn luyện và so sánh các kiến trúc mạng nơ-ron khác nhau cho bài toán LoRa Channel Hopping:
1. Baseline FCNN (MLP - Bài báo gốc)
2. 1D-CNN (Temporal Convolutional Neural Network)
3. GRU (Gated Recurrent Unit - RNN)
4. Depthwise Separable 1D-CNN (MobileNet-1D)
5. Residual 1D-CNN (ResNet-1D)
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

headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']
CHANNELS = ["868", "869", "870"]
SAMPLES_PER_CHANNEL = 10
NUM_CHANNELS = len(CHANNELS)
ONE_HOT_ENCODED_CHANNELS = np.eye(NUM_CHANNELS)

# 1. Đọc dữ liệu từ dataset thực tế của bài báo (thư mục ABC)
raw_inputs = []
raw_outputs = []

for channel_index in range(NUM_CHANNELS):
    channel = CHANNELS[channel_index]
    csv_path = os.path.join(os.path.dirname(__file__), "data/MLdataready/ABC", f"{channel}.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), "data/MLdataready/A", f"{channel}.csv")
    
    df = pd.read_csv(csv_path, names=headers, skiprows=1)
    num_recordings = int(df.shape[0] / SAMPLES_PER_CHANNEL)
    target = ONE_HOT_ENCODED_CHANNELS[channel_index]

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

raw_inputs = np.array(raw_inputs)  # Shape: (N, 10, 8)
raw_outputs = np.array(raw_outputs) # Shape: (N, 3)

print(f"[DATA] Đã nạp {len(raw_inputs)} mẫu. Kích thước chuỗi: {raw_inputs.shape[1]} bước x {raw_inputs.shape[2]} đặc trưng")

# Chuẩn hóa StandardScaler cho từng đặc trưng
N, T, F = raw_inputs.shape
flattened = raw_inputs.reshape(N * T, F)
scaler = StandardScaler()
flattened_scaled = scaler.fit_transform(flattened)
X_seq = flattened_scaled.reshape(N, T, F) # Cho 1D-CNN, GRU, ResNet
X_flat = X_seq.reshape(N, T * F)           # Cho FCNN (80 chiều)

# Phân chia train/val/test cố định
idx_train, idx_temp = train_test_split(np.arange(N), test_size=0.4, random_state=SEED, shuffle=True)
idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=SEED, shuffle=True)

y_train, y_val, y_test = raw_outputs[idx_train], raw_outputs[idx_val], raw_outputs[idx_test]

# ── Định nghĩa các kiến trúc mô hình ─────────────────────────────────────────

def build_fcnn():
    """1. Baseline FCNN (Bài báo gốc)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T * F,)),
        layers.Dense(10, activation='relu'),
        layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4)),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Baseline_FCNN")
    return m, True

def build_cnn1d():
    """2. 1D-CNN (Temporal Convolutional Network)"""
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

def build_gru():
    """3. GRU (Gated Recurrent Unit - RNN)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.GRU(16, return_sequences=False),
        layers.Dense(16, activation='relu'),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="GRU_RNN")
    return m, False

def build_depthwise_separable_cnn():
    """4. Depthwise Separable 1D-CNN (MobileNet-style siêu nhẹ)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F)),
        layers.SeparableConv1D(16, kernel_size=3, padding='same', activation='relu'),
        layers.SeparableConv1D(32, kernel_size=3, padding='same', activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(NUM_CHANNELS, activation='softmax')
    ], name="Separable_1D_CNN")
    return m, False

def build_resnet1d():
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
    outputs = layers.Dense(NUM_CHANNELS, activation='softmax')(x)
    
    m = models.Model(inputs=inputs, outputs=outputs, name="ResNet_1D")
    return m, False

model_factories = [
    build_fcnn,
    build_cnn1d,
    build_gru,
    build_depthwise_separable_cnn,
    build_resnet1d
]

results = []
EPOCHS = 150
BATCH_SIZE = 8

os.makedirs("models_comparison", exist_ok=True)

for factory in model_factories:
    model, is_flat = factory()
    name = model.name
    print(f"\n=======================================================")
    print(f" Đang huấn luyện: {name}")
    print(f"=======================================================")
    
    X_tr = X_flat[idx_train] if is_flat else X_seq[idx_train]
    X_v  = X_flat[idx_val]   if is_flat else X_seq[idx_val]
    X_te = X_flat[idx_test]  if is_flat else X_seq[idx_test]

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history = model.fit(
        X_tr, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_v, y_val),
        verbose=0
    )

    # Đánh giá trên tập test
    loss, acc = model.evaluate(X_te, y_test, verbose=0)
    params_count = model.count_params()

    # Chuyển đổi sang TFLite để đo dung lượng nhúng thực tế
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    try:
        tflite_bytes = converter.convert()
        tflite_size_kb = len(tflite_bytes) / 1024.0
        tflite_path = f"models_comparison/{name}.tflite"
        with open(tflite_path, "wb") as f:
            f.write(tflite_bytes)
    except Exception as e:
        print(f"[WARN] TFLite convert error: {e}")
        tflite_size_kb = -1

    results.append({
        'Model': name,
        'Test_Accuracy': round(acc * 100, 2),
        'Test_Loss': round(loss, 4),
        'Params': params_count,
        'TFLite_Size_KB': round(tflite_size_kb, 2),
        'Input_Type': 'Flat 80D' if is_flat else 'Sequence (10, 8)',
        'history': history
    })
    print(f"--> [KẾT QUẢ] {name:<22} | Acc: {acc*100:.2f}% | Loss: {loss:.4f} | Params: {params_count} | TFLite: {tflite_size_kb:.2f} KB")

# Lưu bảng tổng hợp
df_res = pd.DataFrame([{k: v for k, v in r.items() if k != 'history'} for r in results])
print("\n" + "="*80)
print("             BẢNG SO SÁNH CÁC KIẾN TRÚC MẠNG NƠ-RON (TINYML LORA)")
print("="*80)
print(df_res.to_string(index=False))
df_res.to_csv("models_comparison/comparison_summary.csv", index=False)

# Vẽ biểu đồ so sánh Accuracy và TFLite Size
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
bars1 = plt.bar(df_res['Model'], df_res['Test_Accuracy'], color=colors)
plt.title('Độ chính xác trên tập Test (%)', fontsize=12)
plt.ylabel('Accuracy (%)')
plt.xticks(rotation=25, ha='right')
plt.ylim(min(df_res['Test_Accuracy']) - 5, 102)
for bar in bars1:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.6)

plt.subplot(1, 3, 2)
bars2 = plt.bar(df_res['Model'], df_res['Params'], color=colors)
plt.title('Số lượng tham số (Parameters)', fontsize=12)
plt.ylabel('Parameters count')
plt.xticks(rotation=25, ha='right')
for bar in bars2:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 10, f"{yval}", ha='center', va='bottom', fontsize=9)
plt.grid(axis='y', linestyle='--', alpha=0.6)

plt.subplot(1, 3, 3)
bars3 = plt.bar(df_res['Model'], df_res['TFLite_Size_KB'], color=colors)
plt.title('Kích thước tệp TFLite trên MCU (KB)', fontsize=12)
plt.ylabel('File Size (KB)')
plt.xticks(rotation=25, ha='right')
for bar in bars3:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.1f} KB", ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig("models_comparison/model_architectures_comparison.png", dpi=300)
print("\n[OK] Đã lưu biểu đồ so sánh vào: models_comparison/model_architectures_comparison.png")
