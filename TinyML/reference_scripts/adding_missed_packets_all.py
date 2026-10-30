import os
import pandas as pd

# Define the input and output folders
input_folder = 'csv'  # Folder containing the input .csv files
output_folder = 'formattedCSV'  # Folder to save the processed .csv files

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Process each .csv file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, filename)

        # Read the CSV file into a DataFrame
        df = pd.read_csv(input_file)

        # Ensure packet_ID is numeric
        df['packet_ID'] = pd.to_numeric(df['packet_ID'], errors='coerce')

        # Get unique sources and size_of_message combinations
        sources = df['source'].unique()
        size_of_messages = df['size_of_message'].unique()

        # Create a list to store new rows for missing packet_IDs
        new_rows = []

        # Process each source and size_of_message
        for source in sources:
            for size in size_of_messages:
                # Filter DataFrame for the current source and size_of_message
                subset = df[(df['source'] == source) & (df['size_of_message'] == size)]

                # Determine the range of packet_IDs
                all_packet_IDs = set(range(subset['packet_ID'].min(), subset['packet_ID'].max() + 1))
                existing_packet_IDs = set(subset['packet_ID'])
                missing_packet_IDs = all_packet_IDs - existing_packet_IDs

                # Create rows for missing packet_IDs
                for packet_ID in missing_packet_IDs:
                    # Find matching time_slot and frequency from the other source
                    matching_row = df[(df['packet_ID'] == packet_ID) & (df['source'] != source)]

                    # Assign time_slot and frequency if a match exists
                    if not matching_row.empty:
                        time_slot = matching_row.iloc[0]['time_slot']
                        frequency = matching_row.iloc[0]['frequency']
                    else:
                        time_slot = None
                        frequency = None

                    # Append the new row
                    new_rows.append({
                        'time_slot': time_slot,
                        'source': source,
                        'packet_ID': packet_ID,
                        'size_of_message': size,
                        'RSSI': -1000,
                        'SNR': -1000,
                        'frequency': frequency
                    })

        # Append new rows to the DataFrame
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        # Sort by source, size_of_message, and packet_ID for better organization
        df = df.sort_values(by=['source', 'size_of_message', 'packet_ID']).reset_index(drop=True)

        # Save the updated DataFrame to a new CSV file
        df.to_csv(output_file, index=False)

        print(f"Processed {filename}: Updated file saved to {output_file}")
