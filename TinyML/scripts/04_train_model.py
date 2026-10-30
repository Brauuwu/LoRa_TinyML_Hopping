#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_train_model.py
Huấn luyện mô hình FCNN phân loại kênh LoRa tối ưu (Channel Hopping),
chuyển đổi sang TensorFlow Lite và xuất mã C header (model.h) cho ESP32.

Phương pháp luận đúng theo bài báo LoRaEdgeTinyML:
  - Đọc dữ liệu từ data/MLdataready/ABC/{channel}.csv
  - Cửa sổ trượt SAMPLES_PER_CHANNEL = 10 bước, 8 đặc trưng/bước = 80 input
  - One-hot encoding cho NUM_CHANNELS lớp
  - Chuẩn hóa StandardScaler
  - FCNN: Dense(10, relu) → Dense(10, relu, L1=1e-4) → Dense(3, softmax)
  - Huấn luyện: loss='mse', metrics=['mae', 'accuracy'], batch_size=1, epochs=500
  - Không dùng EarlyStopping (đúng theo bài báo gốc)
  - Chia tập: Train 60% / Test 20% / Val 20%

Cách chạy:
  python 04_train_model.py
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

from sklearn.preprocessing import StandardScaler

import tensorflow as tf
from tensorflow.keras import regularizers

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MLDATA_READY_DIR = os.path.join(SCRIPT_DIR, "../data/MLdataready")
READY_FILE = os.path.join(SCRIPT_DIR, "../data/ready/dataset_ready.csv")
MODELS_DIR = os.path.join(SCRIPT_DIR, "../models")
FIGURES_DIR = os.path.join(SCRIPT_DIR, "../figures")
MCU_SRC_DIR = os.path.join(SCRIPT_DIR, "../../MCUCode/LoRaEN_TinyMLHopping/src")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Tham số huấn luyện (đúng theo bài báo gốc)
SAMPLES_PER_CHANNEL = 10
EPOCHS = 500
BATCH_SIZE = 1

headers = ['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']


def detect_channels():
    """
    Tự động nhận dạng cấu hình kênh từ dữ liệu thực tế trong MLdataready/ABC/.
    Trả về danh sách tên kênh (ví dụ: ['433_175', '433_375', '433_575'] hoặc ['868', '869', '870']).
    """
    abc_dir = os.path.join(MLDATA_READY_DIR, "ABC")
    if not os.path.isdir(abc_dir):
        return None

    channel_names = sorted([
        os.path.splitext(f)[0]
        for f in os.listdir(abc_dir) if f.endswith(".csv")
    ])
    return channel_names if channel_names else None


def load_data_from_mldataready(channel_names):
    """
    Đọc dữ liệu từ MLdataready/ABC/ theo đúng phương pháp bài báo gốc.
    Mỗi file CSV tương ứng 1 kênh → one-hot label.
    Cửa sổ trượt SAMPLES_PER_CHANNEL = 10 bước, 8 đặc trưng/bước.
    """
    NUM_CHANNELS = len(channel_names)
    ONE_HOT = np.eye(NUM_CHANNELS)

    inputs = []
    outputs = []

    for ch_idx, ch_name in enumerate(channel_names):
        csv_path = os.path.join(MLDATA_READY_DIR, "ABC", f"{ch_name}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(MLDATA_READY_DIR, "A", f"{ch_name}.csv")
        if not os.path.exists(csv_path):
            print(f"  [WARN] Không tìm thấy file cho kênh {ch_name}, bỏ qua.")
            continue

        output = ONE_HOT[ch_idx]
        df = pd.read_csv(csv_path, names=headers, skiprows=1)

        num_recordings = int(df.shape[0] / SAMPLES_PER_CHANNEL)
        print(f"  Kênh '{ch_name}': {num_recordings} recording(s) (tổng {df.shape[0]} dòng)")

        for i in range(num_recordings):
            tensor = []
            for j in range(SAMPLES_PER_CHANNEL):
                idx = i * SAMPLES_PER_CHANNEL + j
                tensor += [
                    float(df['CH1'][idx]),
                    float(df['CH2'][idx]),
                    float(df['CH3'][idx]),
                    float(df['SNR'][idx]),
                    float(df['RSSI'][idx]),
                    float(df['size_of_message'][idx]),
                    float(df['packet_ID'][idx]),
                    float(df['frequency'][idx])
                ]
            inputs.append(tensor)
            outputs.append(output)

    return np.array(inputs), np.array(outputs)


def load_data_from_dataset_ready():
    """
    Fallback: Đọc từ dataset_ready.csv (nếu MLdataready chưa có dữ liệu).
    """
    if not os.path.exists(READY_FILE):
        return None, None, 3

    df = pd.read_csv(READY_FILE)
    feat_cols = [c for c in df.columns if c.startswith("feat_")]
    if len(feat_cols) == 0 or 'target_channel' not in df.columns:
        return None, None, 3

    X = df[feat_cols].values
    y = df['target_channel'].values
    num_ch = len(np.unique(y))
    y_onehot = tf.keras.utils.to_categorical(y, num_classes=num_ch)
    return X, y_onehot, num_ch


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
    print("=" * 72)
    print(" BƯỚC 4: HUẤN LUYỆN MÔ HÌNH TINYML FCNN (PHƯƠNG PHÁP BÀI BÁO GỐC)")
    print("=" * 72)

    # Ưu tiên đọc từ MLdataready/ABC/ (phương pháp bài báo gốc)
    channel_names = detect_channels()
    use_mldataready = False

    if channel_names:
        print(f"\n[DATA] Đang đọc từ MLdataready/ABC/ ({len(channel_names)} kênh: {channel_names})")
        inputs, outputs = load_data_from_mldataready(channel_names)
        if len(inputs) > 0:
            use_mldataready = True
            NUM_CHANNELS = len(channel_names)
        else:
            print("[WARN] Không nạp được dữ liệu từ MLdataready. Fallback sang dataset_ready.csv...")

    if not use_mldataready:
        print("\n[DATA] Đang đọc từ dataset_ready.csv...")
        inputs, outputs, NUM_CHANNELS = load_data_from_dataset_ready()
        if inputs is None or len(inputs) == 0:
            print("[ERROR] Không tìm thấy dữ liệu. Hãy chạy các bước 01 → 02 → 03 trước!")
            return

    print(f"\n[DATA] Tổng: {len(inputs)} mẫu, Input: {inputs.shape[1]} chiều, Output: {NUM_CHANNELS} kênh")

    # Chuẩn hóa StandardScaler (đúng bài báo gốc)
    scaler = StandardScaler()
    inputs = scaler.fit_transform(inputs)

    # Shuffle ngẫu nhiên (đúng bài báo gốc)
    num_inputs = len(inputs)
    randomize = np.arange(num_inputs)
    np.random.shuffle(randomize)
    inputs = inputs[randomize]
    outputs = outputs[randomize]

    # Chia tập: 60% Train / 20% Test / 20% Val (đúng bài báo gốc)
    TRAIN_SPLIT = int(0.6 * num_inputs)
    TEST_SPLIT = int(0.2 * num_inputs + TRAIN_SPLIT)

    inputs_train, inputs_test, inputs_val = np.split(inputs, [TRAIN_SPLIT, TEST_SPLIT])
    outputs_train, outputs_test, outputs_val = np.split(outputs, [TRAIN_SPLIT, TEST_SPLIT])

    print(f"Train: {len(inputs_train)} (60%) | Test: {len(inputs_test)} (20%) | Val: {len(inputs_val)} (20%)")

    # Kiến trúc FCNN Baseline (đúng bài báo gốc)
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(10, activation='relu'),
        tf.keras.layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(l1=1e-4)),
        tf.keras.layers.Dense(NUM_CHANNELS, activation='softmax')
    ])

    # Compile (đúng bài báo gốc: MSE loss, Adam mặc định lr=0.001)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss='mse',
        metrics=['mae', 'accuracy']
    )

    print(f"\n[TRAINING] FCNN Baseline: epochs={EPOCHS}, batch_size={BATCH_SIZE}, loss=MSE")
    print(f"           Kiến trúc: Dense(10,relu) → Dense(10,relu,L1) → Dense({NUM_CHANNELS},softmax)")
    print("-" * 72)

    history = model.fit(
        inputs_train, outputs_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(inputs_val, outputs_val),
        verbose=1
    )

    # Đánh giá trên tập Test
    test_loss, test_mae, test_acc = model.evaluate(inputs_test, outputs_test, verbose=0)
    print(f"\n{'='*55}")
    print(f" Test Accuracy: {test_acc * 100:.2f}% | Test Loss (MSE): {test_loss:.4f} | Test MAE: {test_mae:.4f}")
    print(f"{'='*55}")

    # Dự đoán và in kết quả
    predictions = model.predict(inputs_test)
    print("predictions =\n", np.round(predictions, decimals=3))
    print("actual =\n", outputs_test)

    from tensorflow.keras import backend as K
    best_epoch_acc = history.history['accuracy'][int(np.argmin(history.history['loss']))]
    print(f"Accuracy at best loss epoch: {best_epoch_acc:.4f}")

    # ═══════════ VẼ BIỂU ĐỒ HUẤN LUYỆN (đúng bài báo gốc) ═══════════
    plt.rcParams["figure.figsize"] = (20, 10)
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    acc = history.history['accuracy']
    mae = history.history['mae']
    val_mae = history.history['val_mae']
    epochs_range = range(1, len(loss) + 1)

    # Plot 1: Training accuracy + Training loss + Validation loss
    plt.figure(figsize=(14, 7))
    plt.plot(epochs_range, acc, 'g.', markersize=2, label='Training accuracy')
    plt.plot(epochs_range, loss, 'r.', markersize=2, label='Training loss')
    plt.plot(epochs_range, val_loss, 'b', linewidth=1.5, label='Validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Metrics')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    fig1_path = os.path.join(FIGURES_DIR, "training_accuracy_loss.png")
    plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 2: Training loss + Validation loss only
    plt.figure(figsize=(14, 7))
    plt.plot(epochs_range, loss, 'r.', markersize=2, label='Training loss')
    plt.plot(epochs_range, val_loss, 'b', linewidth=1.5, label='Validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    fig2_path = os.path.join(FIGURES_DIR, "training_loss.png")
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 3: Training accuracy only
    plt.figure(figsize=(14, 7))
    plt.plot(epochs_range, acc, 'g.', markersize=2, label='Training accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    fig3_path = os.path.join(FIGURES_DIR, "training_accuracy.png")
    plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 4: Loss sau SKIP epoch đầu (loại bỏ nhiễu ban đầu)
    SKIP = 20
    plt.figure(figsize=(14, 7))
    plt.plot(epochs_range[SKIP:], loss[SKIP:], 'g.', markersize=2, label='Training loss')
    plt.plot(epochs_range[SKIP:], val_loss[SKIP:], 'b', linewidth=1.5, label='Validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    fig4_path = os.path.join(FIGURES_DIR, "training_loss_skip20.png")
    plt.savefig(fig4_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 5: MAE sau SKIP epoch đầu
    plt.figure(figsize=(14, 7))
    plt.plot(epochs_range[SKIP:], mae[SKIP:], 'g.', markersize=2, label='Training MAE')
    plt.plot(epochs_range[SKIP:], val_mae[SKIP:], 'b', linewidth=1.5, label='Validation MAE')
    plt.xlabel('Epochs')
    plt.ylabel('MAE')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    fig5_path = os.path.join(FIGURES_DIR, "training_mae.png")
    plt.savefig(fig5_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[PLOT] Đã lưu 5 biểu đồ huấn luyện vào: {FIGURES_DIR}")

    # ═══════════ CHUYỂN ĐỔI VÀ XUẤT MÔ HÌNH ═══════════

    # Lưu mô hình Keras
    keras_path = os.path.join(MODELS_DIR, f"complete_TFmodel_ch_{NUM_CHANNELS}.keras")
    model.save(keras_path)
    print(f"[EXPORT] Keras model: {keras_path}")

    # Lưu trọng số HDF5
    weights_path = os.path.join(MODELS_DIR, f"my_model_weights_ch_{NUM_CHANNELS}.weights.h5")
    model.save_weights(weights_path)
    print(f"[EXPORT] Weights H5: {weights_path}")

    # Chuyển đổi sang TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    tflite_path = os.path.join(MODELS_DIR, "channel_model.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    basic_model_size = len(tflite_model)
    print(f"[EXPORT] TFLite: {tflite_path} ({basic_model_size} bytes ~ {basic_model_size/1024:.2f} KB)")

    # Xuất C Header
    header_path = os.path.join(MODELS_DIR, "model.h")
    convert_bytes_to_c_header(tflite_model, header_path, array_name="model")
    print(f"[EXPORT] C Header: {header_path} ({os.path.getsize(header_path):,} bytes)")

    # Đồng bộ sang MCU nếu có
    if os.path.exists(MCU_SRC_DIR):
        dest_header = os.path.join(MCU_SRC_DIR, "model.h")
        shutil.copyfile(header_path, dest_header)
        print(f"[SYNC] Đã đồng bộ model.h → {dest_header}")

    print("\n" + "=" * 72)
    print(" HOÀN TẤT HUẤN LUYỆN MÔ HÌNH TINYML")
    print("=" * 72)


if __name__ == "__main__":
    main()
