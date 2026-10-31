#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_train_model.py
Huấn luyện và tổng hợp so sánh nhiều thuật toán mạng nơ-ron cho LoRa Channel Hopping:
  1. Baseline FCNN (Multi-Layer Perceptron)
  2. 1D-CNN (Temporal Convolutional Neural Network)
  3. GRU (Gated Recurrent Unit - Recurrent Neural Network)
  4. Depthwise Separable 1D-CNN (MobileNet-style 1D Convolution)
  5. ResNet-1D (Residual Neural Network với Skip Connection)

Quy trình:
  - Đọc dữ liệu chuỗi thời gian từ data/MLdataready/ABC/{channel}.csv (hoặc data/ready/dataset_ready.csv)
  - Cửa sổ trượt 10 bước x 8 đặc trưng = 80 chiều
  - Chuẩn hóa StandardScaler
  - Huấn luyện độc lập từng thuật toán với bộ đo: Accuracy, Loss, MAE, Params, TFLite Size, Latency
  - Xuất bảng tổng hợp so sánh và trực quan hóa đường cong học tập
  - Chọn mô hình tối ưu nhất xuất ra channel_model.tflite và mã C header model.h cho ESP32.

Cách chạy:
  python 04_train_model.py
"""

import os
import sys
import time
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
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.keras import layers, models, regularizers

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

SAMPLES_PER_CHANNEL = 10
EPOCHS = 100
BATCH_SIZE = 32

FEATURE_COLS = ['CH1', 'CH2', 'CH3', 'SNR', 'RSSI', 'size_of_message', 'packet_ID', 'frequency']


def detect_channels():
    """Tự động nhận dạng danh sách kênh từ thư mục MLdataready/ABC/."""
    abc_dir = os.path.join(MLDATA_READY_DIR, "ABC")
    if not os.path.isdir(abc_dir):
        return None
    channel_names = sorted([
        os.path.splitext(f)[0]
        for f in os.listdir(abc_dir) if f.endswith(".csv")
    ])
    return channel_names if channel_names else None


def load_dataset():
    """
    Nạp dữ liệu chuỗi thời gian (Phương án 1):
    Đọc trực tiếp từ data/ready/dataset_ready.csv (đã được lọc sạch rò rỉ nhãn).
    Trả về raw_inputs dạng (N, 10, 8) và raw_outputs dạng (N, 3).
    """
    if os.path.exists(READY_FILE):
        print(f"[DATA] Nạp dữ liệu chuẩn Phương án 1 từ: {READY_FILE}")
        df_ready = pd.read_csv(READY_FILE)
        feat_cols = [c for c in df_ready.columns if c.startswith("feat_")]
        if len(feat_cols) == 80 and 'target_channel' in df_ready.columns:
            X_all = df_ready[feat_cols].values
            y_all = df_ready['target_channel'].values
            num_ch = 3
            raw_inputs = X_all.reshape(-1, SAMPLES_PER_CHANNEL, 8)
            raw_outputs = tf.keras.utils.to_categorical(y_all, num_classes=num_ch)
            channel_names = ["433_175", "433_375", "433_575"]
            print(f"  ✓ Đã nạp thành công: {len(raw_inputs)} mẫu chuỗi thời gian (10 bước x 8 đặc trưng)")
            print(f"  ✓ Phân bố nhãn mục tiêu: CH0={(y_all==0).sum()}, CH1={(y_all==1).sum()}, CH2={(y_all==2).sum()}")
            return raw_inputs, raw_outputs, channel_names

    # Fallback dự phòng nếu chưa có dataset_ready.csv
    channel_names = detect_channels()
    if channel_names:
        num_ch = len(channel_names)
        one_hot = np.eye(num_ch)
        raw_inputs, raw_outputs = [], []

        print(f"[DATA] Fallback nạp từ MLdataready/ABC/ ({num_ch} kênh: {channel_names})")
        for ch_idx, ch_name in enumerate(channel_names):
            csv_path = os.path.join(MLDATA_READY_DIR, "ABC", f"{ch_name}.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(MLDATA_READY_DIR, "A", f"{ch_name}.csv")
            if not os.path.exists(csv_path):
                continue

            df = pd.read_csv(csv_path)
            if not all(c in df.columns for c in FEATURE_COLS):
                df = pd.read_csv(csv_path, names=['packet_ID', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency'], skiprows=1)
            df = df.reset_index(drop=True)
            if not all(c in df.columns for c in FEATURE_COLS):
                continue

            arr = df[FEATURE_COLS].to_numpy(dtype=float)
            num_recordings = int(len(arr) / SAMPLES_PER_CHANNEL)
            print(f"  Kênh '{ch_name}': {num_recordings} mẫu ({len(arr)} gói)")

            for i in range(num_recordings):
                tensor = arr[i * SAMPLES_PER_CHANNEL : (i + 1) * SAMPLES_PER_CHANNEL].tolist()
                raw_inputs.append(tensor)
                raw_outputs.append(one_hot[ch_idx])

        if raw_inputs:
            return np.array(raw_inputs), np.array(raw_outputs), channel_names

    return np.array([]), np.array([]), []


# ── ĐỊNH NGHĨA 5 KIẾN TRÚC THUẬT TOÁN ──────────────────────────────────────

def build_fcnn(T, F, num_ch):
    """1. Baseline FCNN (Multi-Layer Perceptron)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T * F,), name="input_flat"),
        layers.Dense(10, activation='relu', name="dense_1"),
        layers.Dense(10, activation='relu', kernel_regularizer=regularizers.L1(1e-4), name="dense_2"),
        layers.Dense(num_ch, activation='softmax', name="output")
    ], name="Baseline_FCNN")
    return m, True


def build_cnn1d(T, F, num_ch):
    """2. 1D-CNN (Temporal Convolutional Network)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F), name="input_seq"),
        layers.Conv1D(16, kernel_size=3, padding='same', activation='relu', name="conv1d_1"),
        layers.BatchNormalization(name="bn_1"),
        layers.MaxPooling1D(pool_size=2, name="maxpool_1"),
        layers.Conv1D(32, kernel_size=3, padding='same', activation='relu', name="conv1d_2"),
        layers.GlobalAveragePooling1D(name="gap"),
        layers.Dense(16, activation='relu', name="dense_dense"),
        layers.Dense(num_ch, activation='softmax', name="output")
    ], name="1D_CNN")
    return m, False


def build_gru(T, F, num_ch):
    """3. GRU (Gated Recurrent Unit RNN)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F), name="input_seq"),
        layers.GRU(16, return_sequences=False, unroll=True, name="gru_layer"),
        layers.Dense(16, activation='relu', name="dense_gru"),
        layers.Dense(num_ch, activation='softmax', name="output")
    ], name="GRU_RNN")
    return m, False


def build_separable_cnn(T, F, num_ch):
    """4. Depthwise Separable 1D-CNN (MobileNet-style)"""
    m = tf.keras.Sequential([
        layers.Input(shape=(T, F), name="input_seq"),
        layers.SeparableConv1D(16, kernel_size=3, padding='same', activation='relu', name="sep_conv1"),
        layers.SeparableConv1D(32, kernel_size=3, padding='same', activation='relu', name="sep_conv2"),
        layers.GlobalAveragePooling1D(name="gap"),
        layers.Dense(num_ch, activation='softmax', name="output")
    ], name="Separable_1D_CNN")
    return m, False


def build_resnet1d(T, F, num_ch):
    """5. Residual 1D-CNN (ResNet-1D với Skip Connection)"""
    inputs = layers.Input(shape=(T, F), name="input_seq")
    x = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(inputs)

    # Residual block
    res = layers.Conv1D(16, kernel_size=3, padding='same', activation='relu')(x)
    res = layers.Conv1D(16, kernel_size=3, padding='same')(res)
    x = layers.add([x, res])
    x = layers.Activation('relu')(x)

    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(16, activation='relu')(x)
    outputs = layers.Dense(num_ch, activation='softmax')(x)

    m = models.Model(inputs=inputs, outputs=outputs, name="ResNet_1D")
    return m, False


def convert_to_tflite_and_header(keras_model, output_tflite_path, output_header_path, array_name="model", scaler=None, is_flat=True, test_acc=None):
    """
    Chuyển đổi sang TensorFlow Lite và xuất C header hoàn chỉnh cho ESP32 bao gồm:
    1. Căn chỉnh bộ nhớ 16-byte (alignas(16) / __attribute__((aligned(16))))
    2. Độ dài mảng FlatBuffer (model_len)
    3. Bộ tham số chuẩn hóa StandardScaler (SCALER_MEAN và SCALER_SCALE)
    4. Cấu hình hằng số (TINYML_NUM_CHANNELS, TINYML_INPUT_DIM, TINYML_TENSOR_ARENA_SIZE)
    5. Hàm helper tiền xử lý chuẩn hóa và tìm kênh argmax tối ưu
    """
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
        tflite_bytes = converter.convert()
    except Exception:
        converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
        converter._experimental_lower_tensor_list_ops = False
        tflite_bytes = converter.convert()

    with open(output_tflite_path, "wb") as f:
        f.write(tflite_bytes)

    guard_name = f"LORA_{array_name.upper()}_H"
    acc_str = f" (Test Accuracy: {test_acc:.2f}%)" if test_acc is not None else ""

    with open(output_header_path, "w", encoding="utf-8") as f:
        f.write("// ============================================================================\n")
        f.write("// TỰ ĐỘNG SINH TỪ PIPELINE TINYML LORA CHANNEL HOPPING\n")
        f.write(f"// Thuật toán: {keras_model.name}{acc_str}\n")
        f.write(f"// Kích thước FlatBuffer: {len(tflite_bytes)} bytes (~{len(tflite_bytes)/1024:.2f} KB)\n")
        f.write("// Cấu trúc đầu vào: 10 bước x 8 đặc trưng = 80 giá trị float\n")
        f.write("// ============================================================================\n\n")

        f.write(f"#ifndef {guard_name}\n")
        f.write(f"#define {guard_name}\n\n")
        f.write("#include <stdint.h>\n")
        f.write("#include <stddef.h>\n\n")

        f.write("// ── ĐỊNH NGHĨA THÔNG SỐ MÔ HÌNH ──────────────────────────────────────────\n")
        f.write(f'#define TINYML_MODEL_NAME          "{keras_model.name}"\n')
        f.write("#define TINYML_NUM_CHANNELS        3\n")
        f.write("#define TINYML_WINDOW_STEPS        10\n")
        f.write("#define TINYML_NUM_FEATURES        8\n")
        f.write("#define TINYML_INPUT_DIM           (TINYML_WINDOW_STEPS * TINYML_NUM_FEATURES)\n")
        f.write("#define TINYML_TENSOR_ARENA_SIZE   (10 * 1024) // 10 KB RAM\n")
        f.write(f"#define TINYML_IS_FLAT             {'1' if is_flat else '0'}\n\n")

        f.write("// ── CĂN CHỈNH BỘ NHỚ 16 BYTES CHO TFLITE MICRO ─────────────────────────\n")
        f.write("#if defined(__GNUC__) || defined(__clang__)\n")
        f.write("  #define TFLM_ALIGNED __attribute__((aligned(16)))\n")
        f.write("#elif defined(_MSC_VER)\n")
        f.write("  #define TFLM_ALIGNED __declspec(align(16))\n")
        f.write("#else\n")
        f.write("  #define TFLM_ALIGNED alignas(16)\n")
        f.write("#endif\n\n")

        f.write(f"TFLM_ALIGNED const unsigned char {array_name}[] = {{\n  ")
        for i, b in enumerate(tflite_bytes):
            f.write(f"0x{b:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n  ")
        f.write("\n};\n\n")
        f.write(f"const unsigned int {array_name}_len = {len(tflite_bytes)};\n\n")

        # Hệ số chuẩn hóa StandardScaler
        f.write("// ── THAM SỐ CHUẨN HÓA Z-SCORE (STANDARDSCALER) ──────────────────────────\n")
        f.write("// Công thức: z = (x - mean) / scale\n")
        f.write("// Thứ tự 8 đặc trưng: [0:CH1, 1:CH2, 2:CH3, 3:SNR, 4:RSSI, 5:size, 6:packet_ID, 7:frequency]\n")

        if scaler is not None and hasattr(scaler, 'mean_') and hasattr(scaler, 'scale_'):
            mean_vals = scaler.mean_
            scale_vals = scaler.scale_
            num_f = len(mean_vals)

            if num_f == 8:
                f.write("const float SCALER_MEAN[8] = {\n  ")
                f.write(", ".join([f"{v:.6f}f" for v in mean_vals]))
                f.write("\n};\n\n")

                f.write("const float SCALER_SCALE[8] = {\n  ")
                f.write(", ".join([f"{v:.6f}f" for v in scale_vals]))
                f.write("\n};\n\n")

                f.write("// Mảng 80 giá trị lặp lại cho 10 bước trượt (Flat 80 Dimensions):\n")
                f.write("const float SCALER_MEAN_80[80] = {\n")
                for s in range(10):
                    f.write("  " + ", ".join([f"{v:.6f}f" for v in mean_vals]) + (",\n" if s < 9 else "\n"))
                f.write("};\n\n")

                f.write("const float SCALER_SCALE_80[80] = {\n")
                for s in range(10):
                    f.write("  " + ", ".join([f"{v:.6f}f" for v in scale_vals]) + (",\n" if s < 9 else "\n"))
                f.write("};\n\n")
            elif num_f == 80:
                f.write("const float SCALER_MEAN_80[80] = {\n  ")
                for i, v in enumerate(mean_vals):
                    f.write(f"{v:.6f}f, ")
                    if (i + 1) % 8 == 0:
                        f.write("\n  ")
                f.write("\n};\n\n")

                f.write("const float SCALER_SCALE_80[80] = {\n  ")
                for i, v in enumerate(scale_vals):
                    f.write(f"{v:.6f}f, ")
                    if (i + 1) % 8 == 0:
                        f.write("\n  ")
                f.write("\n};\n\n")
        else:
            f.write("const float SCALER_MEAN[8]  = {0.33f, 0.33f, 0.33f, 8.0f, -75.0f, 120.0f, 300.0f, 433.375f};\n")
            f.write("const float SCALER_SCALE[8] = {0.47f, 0.47f, 0.47f, 2.5f,  20.0f,  80.0f, 180.0f,   0.200f};\n\n")

        # C / C++ Helper Functions
        f.write("// ── HÀM TIỆN ÍCH TIỀN XỬ LÝ & SUY LUẬN (C/C++ HELPER) ────────────────────\n")
        f.write("#ifdef __cplusplus\n")
        f.write("/**\n")
        f.write(" * Chuẩn hóa bộ đệm trượt 10 bước (mỗi bước 8 đặc trưng) thành vector 80 chiều\n")
        f.write(" */\n")
        f.write("inline void normalizeSlidingWindow(const float raw_history[10][8], float out_normalized[80]) {\n")
        f.write("  int idx = 0;\n")
        f.write("  for (int step = 0; step < 10; step++) {\n")
        f.write("    for (int feat = 0; feat < 8; feat++) {\n")
        f.write("#if defined(SCALER_MEAN)\n")
        f.write("      out_normalized[idx] = (raw_history[step][feat] - SCALER_MEAN[feat]) / SCALER_SCALE[feat];\n")
        f.write("#else\n")
        f.write("      out_normalized[idx] = (raw_history[step][feat] - SCALER_MEAN_80[idx]) / SCALER_SCALE_80[idx];\n")
        f.write("#endif\n")
        f.write("      idx++;\n")
        f.write("    }\n")
        f.write("  }\n")
        f.write("}\n\n")

        f.write("/**\n")
        f.write(" * Tìm chỉ số kênh có xác suất lớn nhất (ArgMax)\n")
        f.write(" */\n")
        f.write("inline int argmaxChannel(const float probs[3]) {\n")
        f.write("  int best = 0;\n")
        f.write("  float max_val = probs[0];\n")
        f.write("  for (int i = 1; i < 3; i++) {\n")
        f.write("    if (probs[i] > max_val) {\n")
        f.write("      max_val = probs[i];\n")
        f.write("      best = i;\n")
        f.write("    }\n")
        f.write("  }\n")
        f.write("  return best;\n")
        f.write("}\n")
        f.write("#endif // __cplusplus\n\n")

        f.write(f"#endif // {guard_name}\n")

    return len(tflite_bytes)


def measure_inference_latency(model, sample_input, is_flat, num_runs=200):
    """Đo thời gian suy luận (Latency) trung bình tính bằng micro-giây (µs)"""
    inp = sample_input.reshape(1, -1) if is_flat else sample_input.reshape(1, sample_input.shape[0], sample_input.shape[1])
    # Warm-up
    for _ in range(10):
        _ = model(inp, training=False)

    t0 = time.perf_counter()
    for _ in range(num_runs):
        _ = model(inp, training=False)
    t1 = time.perf_counter()
    latency_us = ((t1 - t0) / num_runs) * 1e6
    return round(latency_us, 1)


def main():
    print("=" * 72)
    print(" BƯỚC 4: TỔNG HỢP HUẤN LUYỆN ĐA THUẬT TOÁN TINYML CHO CHANNEL HOPPING")
    print("=" * 72)

    raw_inputs, raw_outputs, channel_names = load_dataset()
    if len(raw_inputs) == 0:
        print("[ERROR] Không tìm thấy dữ liệu. Hãy chạy các bước 01 → 02 → 03 trước!")
        return

    N, T, F = raw_inputs.shape
    NUM_CHANNELS = raw_outputs.shape[1]
    print(f"\n[DATA] Tổng cộng {N} mẫu chuỗi thời gian ({T} bước x {F} đặc trưng), {NUM_CHANNELS} kênh đầu ra.")

    # Chuẩn hóa StandardScaler
    flattened = raw_inputs.reshape(N * T, F)
    scaler = StandardScaler()
    flattened_scaled = scaler.fit_transform(flattened)
    X_seq = flattened_scaled.reshape(N, T, F)
    X_flat = X_seq.reshape(N, T * F)

    # Phân chia tập dữ liệu: 60% Train, 20% Val, 20% Test
    idx_train, idx_temp = train_test_split(np.arange(N), test_size=0.4, random_state=SEED)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=SEED)

    y_train, y_val, y_test = raw_outputs[idx_train], raw_outputs[idx_val], raw_outputs[idx_test]
    print(f"[SPLIT] Train: {len(idx_train)} (60%) | Val: {len(idx_val)} (20%) | Test: {len(idx_test)} (20%)\n")

    model_factories = [
        ("Baseline_FCNN", build_fcnn),
        ("1D_CNN", build_cnn1d),
        ("GRU_RNN", build_gru),
        ("Separable_1D_CNN", build_separable_cnn),
        ("ResNet_1D", build_resnet1d),
    ]

    benchmark_summary = []
    histories = {}
    trained_models = {}

    plt.figure(figsize=(15, 10), dpi=150)

    for idx, (m_name, factory) in enumerate(model_factories):
        print("-" * 60)
        print(f"[{idx + 1}/5] Bắt đầu huấn luyện mô hình: {m_name}")
        print("-" * 60)

        model, is_flat = factory(T, F, NUM_CHANNELS)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'mae']
        )

        X_tr = X_flat[idx_train] if is_flat else X_seq[idx_train]
        X_vl = X_flat[idx_val] if is_flat else X_seq[idx_val]
        X_ts = X_flat[idx_test] if is_flat else X_seq[idx_test]

        t_start = time.time()
        early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
        lr_sched = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=6, min_lr=1e-5)
        history = model.fit(
            X_tr, y_train,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_data=(X_vl, y_val),
            callbacks=[early_stop, lr_sched],
            verbose=0
        )
        train_time = time.time() - t_start
        histories[m_name] = history
        trained_models[m_name] = (model, is_flat)

        test_loss, test_acc, test_mae = model.evaluate(X_ts, y_test, verbose=0)
        param_count = model.count_params()

        # Đo Latency
        sample_in = X_flat[idx_test[0]] if is_flat else X_seq[idx_test[0]]
        latency_us = measure_inference_latency(model, sample_in, is_flat)

        # Xuất TFLite riêng biệt cho mô hình này
        tflite_f = os.path.join(MODELS_DIR, f"{m_name}.tflite")
        header_f = os.path.join(MODELS_DIR, f"model_{m_name.lower()}.h")
        tflite_size_bytes = convert_to_tflite_and_header(
            model, tflite_f, header_f,
            array_name=f"model_{m_name.lower()}",
            scaler=scaler, is_flat=is_flat, test_acc=test_acc * 100
        )
        tflite_size_kb = round(tflite_size_bytes / 1024, 2)

        print(f"  ✓ Test Accuracy: {test_acc * 100:.2f}% | Loss: {test_loss:.4f} | MAE: {test_mae:.4f}")
        print(f"  ✓ Tham số: {param_count:,} | TFLite: {tflite_size_kb} KB | Latency: {latency_us} µs | Thời gian train: {train_time:.1f}s")

        benchmark_summary.append({
            'Model': m_name,
            'Test Accuracy (%)': round(test_acc * 100, 2),
            'Test Loss': round(test_loss, 4),
            'Test MAE': round(test_mae, 4),
            'Parameters': param_count,
            'TFLite Size (KB)': tflite_size_kb,
            'Latency (us)': latency_us,
            'Train Time (s)': round(train_time, 1)
        })

        # Vẽ đường cong học tập
        plt.subplot(2, 3, idx + 1)
        plt.plot(history.history['accuracy'], label='Train Acc', color='#2ca02c', linewidth=1.5)
        plt.plot(history.history['val_accuracy'], label='Val Acc', color='#1f77b4', linewidth=1.5)
        plt.plot(history.history['loss'], label='Loss', color='#d62728', linestyle='--', linewidth=1.2)
        plt.title(f"{m_name} ({test_acc*100:.1f}%)", fontweight='bold', fontsize=9.5)
        plt.xlabel('Epoch', fontsize=8.5)
        plt.ylabel('Score / Loss', fontsize=8.5)
        plt.legend(loc='center right', fontsize=7.5, framealpha=0.9)
        plt.grid(True, linestyle='--', alpha=0.4)

    # Biểu đồ so sánh Accuracy tổng hợp ở subplot thứ 6
    summary_df = pd.DataFrame(benchmark_summary)
    plt.subplot(2, 3, 6)
    bars = plt.bar(summary_df['Model'], summary_df['Test Accuracy (%)'], color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd'], width=0.55)
    plt.title('Accuracy Comparison', fontweight='bold', fontsize=9.5)
    plt.xlabel('Model', fontsize=8.5)
    plt.ylabel('Accuracy (%)', fontsize=8.5)
    plt.xticks(rotation=25, ha='right', fontsize=8)
    plt.ylim(0, 108)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.4)

    plt.tight_layout()
    chart_path = os.path.join(FIGURES_DIR, "multi_model_training_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"\n[OK] Đã lưu biểu đồ so sánh: {chart_path}")

    # Bảng tổng hợp ra Terminal và CSV
    print("\n" + "=" * 72)
    print(" BẢNG TỔNG HỢP SO SÁNH CÁC THUẬT TOÁN TINYML ĐÃ HUẤN LUYỆN")
    print("=" * 72)
    print(summary_df.to_string(index=False))

    summary_csv = os.path.join(MODELS_DIR, "models_benchmark_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    print(f"\n[OK] Đã lưu bảng tổng hợp: {summary_csv}")

    # ── CHỌN MÔ HÌNH TỐI ƯU ĐỂ XUẤT CHO ESP32 ──────────────────────────────
    # Ưu tiên Depthwise Separable 1D-CNN (cân bằng Accuracy cao và tối ưu bộ nhớ)
    # hoặc mô hình có Test Accuracy cao nhất
    best_row = summary_df.loc[summary_df['Test Accuracy (%)'].idxmax()]
    best_model_name = best_row['Model']
    print("\n" + "=" * 72)
    print(f" MÔ HÌNH TỐI ƯU ĐƯỢC CHỌN CHO ESP32: {best_model_name} (Accuracy: {best_row['Test Accuracy (%)']}%)")
    print("=" * 72)

    best_model, best_is_flat = trained_models[best_model_name]
    final_tflite_path = os.path.join(MODELS_DIR, "channel_model.tflite")
    final_header_path = os.path.join(MODELS_DIR, "model.h")
    convert_to_tflite_and_header(
        best_model, final_tflite_path, final_header_path,
        array_name="model",
        scaler=scaler, is_flat=best_is_flat, test_acc=best_row['Test Accuracy (%)']
    )

    print(f" [OK] Đã xuất TFLite Model: {final_tflite_path}")
    print(f" [OK] Đã xuất C Header File: {final_header_path}")

    # Đồng bộ sang firmware MCU
    mcu_model_h = os.path.join(MCU_SRC_DIR, "model.h")
    if os.path.exists(MCU_SRC_DIR):
        shutil.copyfile(final_header_path, mcu_model_h)
        print(f" [SYNC] Đã đồng bộ sang firmware ESP32: {mcu_model_h}")

    print("\n[HOÀN TẤT] Bước 4 đã hoàn thành huấn luyện và so sánh thành công 5 thuật toán!")


if __name__ == "__main__":
    main()
