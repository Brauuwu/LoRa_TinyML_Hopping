import pandas as pd
import numpy as np
import time

# Load data
df_opt = pd.read_csv('optplants2.csv')
df_soils = pd.read_csv('soillavels100000.csv')

# Rename columns
df_soils.columns = ['N', 'P', 'K', 'ph', 'temp']

# Drop duplicates
df_soils = df_soils.drop_duplicates()

# Add new columns for each plant with initial values of 0
new_column_names = df_opt['Plant'].values
df_soils = pd.concat([df_soils, pd.DataFrame(0, index=df_soils.index, columns=new_column_names)], axis=1)

# Define rating calculation function
def calculate_rating(row):
    ratings = {}
    for plant_name in new_column_names:
        if plant_name in df_opt['Plant'].values:
            opt_conditions = df_opt[df_opt['Plant'] == plant_name].iloc[0]
            rating = sum([
                opt_conditions['N_min'] <= row['N'] <= opt_conditions['N_max'],
                opt_conditions['P_min'] <= row['P'] <= opt_conditions['P_max'],
                opt_conditions['K_min'] <= row['K'] <= opt_conditions['K_max'],
                opt_conditions['ph_min'] <= row['ph'] <= opt_conditions['ph_max'],
                opt_conditions['temp_min'] <= row['temp'] <= opt_conditions['temp_max']
            ])
            ratings[plant_name] = rating
    return pd.Series(ratings)

# Time the process
start_time = time.time()
ratings_df = df_soils.apply(calculate_rating, axis=1)

# Add ratings to original DataFrame
df_soils[new_column_names] = ratings_df

# Timing end
end_time = time.time()
print(f"\nTime taken for the rating computation: {end_time - start_time:.4f} seconds")
# Select columns from index 5 to index 20 (column indices are zero-based)
columns_to_inspect = df_soils.columns[5:]
calculatedratings = df_soils[columns_to_inspect]
# Identify rows that df_soils one or more zeros in the specified columns
one_or_more_zeros = (calculatedratings == 0).any(axis=1)
print("\nRows that contain one or more zeros in the specified columns:")
print(one_or_more_zeros)

# Filter the original DataFrame to show only rows that have no zeros in the specified columns
rows_with_no_zeros = df_soils[~one_or_more_zeros]
print("\nRows with no zeros in the specified columns:")
print(rows_with_no_zeros)
#safet to csv
rows_with_no_zeros.to_csv('NoZeros.csv', index=False)
# Save to CSV
#df_soils.to_csv('0_500000soils_tightsoil.csv', index=False)