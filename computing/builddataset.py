import pandas as pd
import numpy as np


df_opt = pd.read_csv('optplants2.csv')


def find_min_max(df):
    # Find the maximum value of the 'N' column
    max_n_ppm = df_opt['N_max'].max()
    min_n_ppm = df_opt['N_min'].min()

    print("\nMaximum value in 'N' column:", max_n_ppm)
    print("\nMin value in 'N' column:", min_n_ppm)

    # Find the maximum value of the 'P' column
    max_p_ppm = df_opt['P_max'].max()
    min_p_ppm = df_opt['P_min'].min()

    print("Maximum value in 'P' column:", max_p_ppm)
    print("\nMin value in 'P' column:", min_p_ppm)

    # Find the maximum value of the 'K' column
    max_k_ppm = df_opt['K_max'].max()
    min_k_ppm = df_opt['K_min'].min()

    print("Maximum value in 'K' column:", max_k_ppm)
    print("\nMin value in 'K' column:", min_k_ppm)


    # Find the maximum value of the 'K' column
    max_pH_min = df_opt['ph_min'].min()
    min_pH_max = df_opt['ph_max'].max()

    print("Maximum value in 'pH_min' column:", max_pH_min)
    print("\nMin value in 'pH_max' column:", min_pH_max)


    # Find the maximum value of the 'K' column
    max_temp_max = df_opt['temp_max'].max()
    min_temp_min = df_opt['temp_min'].min()

    print("Maximum value in 'temp_max' column:", max_temp_max)
    print("\nMin value in temp_min' column:", min_temp_min)

find_min_max(df_opt)

#Create a random dataset with specified ranges for each column.
def create_random_dataset(num_rows, column_ranges):
    data = {}
    for i, (min_val, max_val) in enumerate(column_ranges):
        if i == 3:  # Column 4 (index 3) will have float values
            # Generate random floats for Column 4 in the specified range and round to 1 decimal place
            data[f'Column {i+1}'] = np.round(np.random.uniform(min_val, max_val, size=num_rows), 1)
        else:
            # Generate random integers for other columns based on their range
            data[f'Column {i+1}'] = np.random.randint(min_val, max_val + 1, size=num_rows)

    return pd.DataFrame(data)

if __name__ == "__main__":
    # Number of rows to generate
    num_rows = 100000  

    # Define the ranges for each of the 5 columns (min, max)
    column_ranges = [
        (0, 200),  
        (0, 100), 
        (0, 300), 
        (4.5, 8.0), 
        (-5, 50) 
    ]

    # Create the random dataset
    random_dataset = create_random_dataset(num_rows, column_ranges)
     # Save the DataFrame to a new CSV file
    csv_file_path = 'soillevels100000.csv'  
    random_dataset.to_csv(csv_file_path, index=False)

    # Display the resulting DataFrame
    print(random_dataset)