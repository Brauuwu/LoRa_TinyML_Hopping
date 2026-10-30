import pandas as pd
import matplotlib.pyplot as plt

# Load CSV files (for Random and Best models)
random_df = pd.read_csv("output_statistics_random_ABC.csv")  # Replace with the actual file path for random
best_df = pd.read_csv("output_statistics_best_ABC.csv")      # Replace with the actual file path for best

# Merge both dataframes on 'size_of_message' to compare random and best results
merged_df = pd.merge(random_df, best_df, on="size_of_message", suffixes=('_random', '_best'))

# Plot the bar charts
fig = plt.figure() #subplots(1, 3, figsize=(18, 6))

# Define the new bar width for larger bars
bar_width = 8  # Increase this value to make bars wider

# Plot 1: average_SNR_excluding_neg_1000
plt.bar(merged_df['size_of_message'] - bar_width / 2, merged_df['average_SNR_excluding_neg_1000_random'], 
            width=bar_width, label='Random', color='b')
plt.bar(merged_df['size_of_message'] + bar_width / 2, merged_df['average_SNR_excluding_neg_1000_best'], 
            width=bar_width, label='TinyML', color='g')
#axes[0].set_title('Average SNR', fontsize=14)
plt.xlabel('Size of Message', fontsize=20)
plt.ylabel('Average SNR', fontsize=20)

plt.xticks(merged_df['size_of_message'], fontsize=16)
plt.yticks(fontsize=16)

plt.legend(fontsize=16)
plt.grid(True)
plt.tight_layout()
plt.savefig("Average_SNR_Chart.pdf")
plt.show()


# Plot 2: average_RSSI_excluding_neg_1000
plt.bar(merged_df['size_of_message'] - bar_width / 2, merged_df['average_RSSI_excluding_neg_1000_random'], 
            width=bar_width, label='Random', color='b')
plt.bar(merged_df['size_of_message'] + bar_width / 2, merged_df['average_RSSI_excluding_neg_1000_best'], 
            width=bar_width, label='TinyML', color='g')
#axes[1].set_title('Average RSSI', fontsize=14)
plt.xlabel('Size of Message', fontsize=20)
plt.ylabel('Average RSSI', fontsize=20)

plt.xticks(merged_df['size_of_message'], fontsize=16)
plt.yticks(fontsize=16)

plt.legend(fontsize=16)
plt.grid(True)
plt.tight_layout()
plt.savefig("Average_RSSI_Chart.pdf")
plt.show()

# Plot 3: fraction_of_RSSI_neg_1000
plt.bar(merged_df['size_of_message'] - bar_width / 2, 1-merged_df['fraction_of_RSSI_neg_1000_random'], 
            width=bar_width, label='Random', color='b')
plt.bar(merged_df['size_of_message'] + bar_width / 2, 1-merged_df['fraction_of_RSSI_neg_1000_best'], 
            width=bar_width, label='TinyML', color='g')
#axes[2].set_title('PSR', fontsize=14)
plt.xlabel('Size of Message', fontsize=20)
plt.ylabel('PDR', fontsize=20)

plt.xticks(merged_df['size_of_message'], fontsize=16)
plt.yticks(fontsize=16)

plt.legend(fontsize=16)
plt.grid(True)
plt.tight_layout()
plt.savefig("PSR_Chart.pdf")
plt.show()
'''
# Resize the x-ticks for all subplots for better readability
for ax in axes:
    ax.set_xticks(merged_df['size_of_message'])
    ax.set_xticklabels(merged_df['size_of_message'], rotation=45, ha="right", fontsize=14)

    # Resize y-ticks
    ax.tick_params(axis='y', labelsize=14)  # Adjust the font size for y-ticks
'''


