import matplotlib.pyplot as plt
import numpy as np

# Data
channels = ["2", "3", "4", "5", "6", "7", "8", "9"]  # X-axis labels
model_types = ["C array format (.h)", "TF weights only (.h5)", "TF model (.h5)", "TFLite model (.tflite)"]
model_sizes_kb = [
    [52.2, 52.2, 52.2, 52.2, 52.2, 52.2, 52.2, 52.2],  # Sizes for "model.h"
    [27.8, 29.0, 30.2, 31.9, 33.2, 34.4, 36.0, 37.2],  # Sizes for "TF weights only (.h5)"
    [37.1, 38.3, 39.5, 43.0, 44.2, 45.4, 46.6, 47.8],  # Sizes for "TF model (.h5)"
    [5.3, 5.8, 6.2, 6.7, 7.1, 7.6, 8.0, 8.5]   # Sizes for "TFLite model (.tflite)"
]

# Set up the bar width and x positions
bar_width = 0.2
x = np.arange(len(channels))

# Plot each model type
plt.figure(figsize=(10, 6))
for i, (model_type, sizes) in enumerate(zip(model_types, model_sizes_kb)):
    plt.bar(x + i * bar_width, sizes, width=bar_width, label=model_type)

# Customizing the plot
plt.xlabel("Number of channels", fontsize=22)
plt.ylabel("Size [KB]", fontsize=22)
plt.xticks(x + bar_width * (len(model_types) - 1) / 2, channels, fontsize=18)
plt.yticks(fontsize=18)

# Adjust legend with a larger title font size
plt.legend(
    title="Model Type", 
    title_fontsize=20,  # Font size for the title
    fontsize=16         # Font size for the legend labels
)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Annotate bar values (align closely with the top of each bar)
for i, sizes in enumerate(model_sizes_kb):
    for j, size in enumerate(sizes):
        plt.text(x[j] + i * bar_width, size + 0.5, f"{size}", ha='center', va='bottom', fontsize=14)

# Set y-axis limits
plt.ylim(0, 80)

# Display the plot
plt.tight_layout()
plt.show()
