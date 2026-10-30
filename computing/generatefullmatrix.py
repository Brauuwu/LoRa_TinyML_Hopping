import pandas as pd
import numpy as np
import time

df_opt = pd.read_csv('optplants2.csv')
df_soils = pd.read_csv('soillevels500000.csv')

df_soils.columns = ['N', 'P', 'K', 'ph','temp']
df_soils.drop_duplicates() 
new_column_names = df_opt['Plant'].values
print("plants? ",new_column_names)

# Add new columns to df_soils at position 5
for i, col_name in enumerate(new_column_names):
    # Initialize with zeros or any arbitrary value
    df_soils.insert(5 + i, col_name, 0)

# Display the updated DataFrame
print("\nUpdated DataFrame:")
print(df_soils)

#print( df_opt.head)

def calculate_new_value(row):
    print("row: ", row)
    return (row['N'] + row['P'] + row['K']) * row['temp']


# Rating calculation function
def calculate_rating(row):
    # Define the conditions based on the values at the first five columns
    N, P, K, pH, temp = row['N'], row['P'], row['K'], row['ph'], row['temp']
    # Initialize a dictionary to hold ratings for each plant
    ratings = {}  
    
    for plant_name in new_column_names:
        if plant_name in df_opt['Plant'].values:
            opt_conditions = df_opt[df_opt['Plant'] == plant_name].iloc[0]
            rating = 0
            # Check each parameter against its min and max
            if opt_conditions['N_min'] <= N <= opt_conditions['N_max']:
                rating += 1
            if opt_conditions['P_min'] <= P <= opt_conditions['P_max']:
                rating += 1
            if opt_conditions['K_min'] <= K <= opt_conditions['K_max']:
                rating += 1
            if opt_conditions['ph_min'] <= pH <= opt_conditions['ph_max']:
                rating += 1
            if opt_conditions['temp_min'] <= temp <= opt_conditions['temp_max']:
                rating += 1
            
            ratings[plant_name] = rating
            #ratings[plant_name] = rating if rating > 0 else np.nan
    return pd.Series(ratings)

# Apply the function to calculate ratings for each plant
start_time = time.time()  # Record the start time
ratings_df = df_soils.iloc[:1000000].apply(calculate_rating, axis=1)

# Now add these ratings to the original df_soils DataFrame at the correct positions
for plant_name in new_column_names:
    if plant_name in ratings_df.columns:
        df_soils.loc[0:1000000, plant_name] = ratings_df[plant_name]  

# Stop timing
end_time = time.time()  # Record the end time

# Calculate and print the time taken in seconds
print(f"\nTime taken for the rating computation: {end_time - start_time:.4f} seconds")

# Specify your desired file name
csv_file_path = '0_100000soils_tightsoil.csv'  
#df_soils.to_csv(csv_file_path, index=False)
df_soils.to_csv(csv_file_path, index=False)
