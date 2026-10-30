import pandas as pd

# Input and output file paths
input_file = 'formattedCSV/C_869.csv'  # Replace with your CSV file path
output_file = 'MLData/C/C_869_B.csv'  # Replace with your desired output file path

# Read the CSV file
df = pd.read_csv(input_file)

# Filter rows where source is 'A'
filtered_df = df[df['source'] == 'C']

# Create the new columns CH1, CH2, and CH3 based on the frequency
filtered_df['CH1'] = filtered_df['frequency'].apply(lambda x: 0 if x == 868.0 else 1)
filtered_df['CH2'] = filtered_df['frequency'].apply(lambda x: 0 if x == 869.0 else 1)
filtered_df['CH3'] = filtered_df['frequency'].apply(lambda x: 0 if x == 870.0 else 1)

# Select the desired columns: packet_ID, source, CH1, CH2, CH3, size_of_message, RSSI, SNR, frequency
final_df = filtered_df[['packet_ID', 'source', 'CH1', 'CH2', 'CH3', 'size_of_message', 'RSSI', 'SNR', 'frequency']]

# Save the result to a new CSV file
final_df.to_csv(output_file, index=False)

print(f"Filtered and updated data saved to {output_file}")
