import os
import re
import pandas as pd

# Define the input and output folders
input_folder = 'logs'  # Folder containing .txt files
output_folder = 'csv'  # Folder to save .csv files

# Make sure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Regular expression to capture the desired fields
pattern = (
    r"(?P<time_slot>\d{2}:\d{2}:\d{2}.\d{3})\s*->\s*"  # Capture time slot (e.g., 11:45:51.918)
    r"(?P<source>[A-Z])(?P<packet_ID>\d+)(?:\*.*?)\s*.*?"  # Capture source (A or B) and number separately
    r"size_of_message\s+(?P<size_of_message>\d+)\s*"  # Message size
    r"RSSI\s+(?P<RSSI>-?\d+)\s*"  # RSSI value
    r"SNR\s+(?P<SNR>-?\d+)\s*"  # SNR value
    r"Frequency\s+(?P<frequency>\d+\.\d+)"  # Frequency
)

# Process each .txt file in the 'logs' folder
for filename in os.listdir(input_folder):
    if filename.endswith('.txt'):
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.csv")
        
        # Initialize an empty list to store parsed rows
        data = []

        # Read the file and process line by line
        with open(input_file, 'r') as file:
            for line in file:
                # Attempt to match the pattern
                match = re.search(pattern, line)
                if match:
                    # Add the extracted fields to the data list
                    data.append(match.groupdict())

        # If data is found, convert it to DataFrame and save as CSV
        if data:
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            print(f"Data successfully extracted from {filename} and written to {output_file}")
        else:
            print(f"No matching data found in {filename}. Skipping.")
