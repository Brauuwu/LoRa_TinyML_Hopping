import pandas as pd
import random

# Define file paths
file1 = "data/formattedCSV/"+ "A_B_C_868.csv"
file2 = "data/formattedCSV/"+ "A_B_C_869.csv"
file3 = "data/formattedCSV/"+ "A_B_C_870.csv"
files = [file1, file2, file3]
# Step 1: Read the CSV files and create the initial dictionary
data_dict = {}

for file in files:
    df = pd.read_csv(file)
    for _, row in df.iterrows():
        key = (row['packet_ID'], row['size_of_message'])
        value = {
            'RSSI': row['RSSI'],
            'SNR': row['SNR'],
            'frequency': row['frequency'],
            'time_slot': row['time_slot'],
        }
        if key not in data_dict:
            data_dict[key] = []
        data_dict[key].append(value)

# Step 2: Create a new dictionary where for each key, a random row is selected
randomized_dict = {}
for key, values in data_dict.items():
    # Select a random value for each key
    randomized_dict[key] = random.choice(values)

# Step 3: Compute the statistics for each unique `size_of_message`
results = []

# We will compute these for each unique size_of_message
unique_sizes = set([key[1] for key in randomized_dict.keys()])

for size in unique_sizes:
    rssi_total = 0
    snr_total = 0
    rssi_excluding_neg_1000 = 0
    snr_excluding_neg_1000 = 0
    count_rssi = 0
    count_rssi_excluding_neg_1000 = 0
    count_neg_1000 = 0

    # Collect values for each size_of_message
    for key, value in randomized_dict.items():
        if key[1] == size:
            rssi = value['RSSI']
            snr = value['SNR']
            rssi_total += rssi
            snr_total += snr
            count_rssi += 1

            if rssi != -1000:
                rssi_excluding_neg_1000 += rssi
                snr_excluding_neg_1000 += snr
                count_rssi_excluding_neg_1000 += 1
            else:
                count_neg_1000 += 1

    # Calculate the averages
    average_rssi = rssi_total / count_rssi if count_rssi > 0 else 0
    average_rssi_excluding_neg_1000 = (
        rssi_excluding_neg_1000 / count_rssi_excluding_neg_1000
        if count_rssi_excluding_neg_1000 > 0
        else 0
    )
    average_snr = snr_total / count_rssi if count_rssi > 0 else 0
    average_snr_excluding_neg_1000 = (
        snr_excluding_neg_1000 / count_rssi_excluding_neg_1000
        if count_rssi_excluding_neg_1000 > 0
        else 0
    )
    fraction_neg_1000 = (
        count_neg_1000 / count_rssi if count_rssi > 0 else 0
    )

    # Append the result for this size_of_message
    results.append({
        'size_of_message': size,
        'average_SNR_excluding_neg_1000': average_snr_excluding_neg_1000,
        'average_SNR_including_neg_1000': average_snr,
        'average_RSSI_excluding_neg_1000': average_rssi_excluding_neg_1000,
        'average_RSSI_including_neg_1000': average_rssi,
        'fraction_of_RSSI_neg_1000': fraction_neg_1000
    })

# Step 4: Save the results to a CSV file
results_df = pd.DataFrame(results)
results_df.to_csv("output_statistics_random_ABC.csv", index=False)

print("Results saved to 'output_statistics_random.csv'")