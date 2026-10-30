import pandas as pd
import numpy as np
import random

# to generate ratingsfirst time
alldata_panda = pd.read_csv('soillavels100000.csv', sep=',')
#to run on cosine generated data:
#alldata_panda = pd.read_csv('CosineRatingsWithSOILS.csv', sep=',')
#alldata_panda = pd.read_csv('NoZeros_2.csv', sep=',')


# try with sparse matrix to have the same size at the end
#alldata_panda = pd.read_csv('resultsCollab/sparseMatrix_90.csv', sep=',')
if 'Unnamed: 0' in alldata_panda.columns:
    alldata_panda = alldata_panda.drop(columns=['Unnamed: 0'])
alldata_panda.iloc[:, 5:] = np.nan

evendist = False
print("alldata", alldata_panda)
ideal = pd.read_csv("optplants2.csv")
alldata_panda = alldata_panda.fillna(0.0)

def calc_rating(soil, plant):
    sum = 0
    tolerance = 15
    temp_tol = 5
    ph_tol = 1
    for _ , row in ideal.iterrows():
        if row['Plant'] == plant:
            if row['N_min']-temp_tol <= soil['N'] <= row['N_max']+ temp_tol:
                sum += 1
            if row['P_min']-temp_tol <= soil['P'] <= row['P_max']+ temp_tol:
                sum += 1
            if row['K_min']-temp_tol <= soil['K'] <= row['K_max']+ temp_tol:
                sum += 1
            # temperature:
            if row['temp_min']-temp_tol <= soil['temp'] <= row['temp_max']+ temp_tol:
                sum += 1
            # pH value
            if row['ph_min'] - ph_tol<= soil['ph'] <= row['ph_max'] +  ph_tol:
                    sum += 1
            if sum == 0 or sum == 0.0:
                return pd.NA   
            return int(sum)
        
    if sum == 0 or sum == 0.0:
                return pd.NA   
    return int(sum)

def is_distribution_uneven(counts_df, threshold):
    for column in counts_df.columns:
        max_count = counts_df[column].max()
        min_count = counts_df[column].min()
        if max_count - min_count > threshold:
            return True
    return False

rating_range = range(6)

def clean_df(df):
    df_cleaned = df.dropna(subset=df.iloc[:, 6:].columns, how='all')
    column_index = 20
    return df_cleaned

# Check for issues
print("info",alldata_panda.info())
print("describe", alldata_panda.describe())
print("head", alldata_panda.head())

# Ensure correct data types
print(alldata_panda.dtypes)

# Ensure no NaN values
print(alldata_panda.isna().sum())

filtered_df = alldata_panda.copy()
print("filterdf", filtered_df, alldata_panda.shape)

# Dynamic calculation of amount of columns
amountofcolumns = filtered_df.shape[1] 
print("amount of columns: ", amountofcolumns,type(amountofcolumns))

# Initializing counts DataFrame; 
rating_range = range(6)  # 0-5
print("ratingrange: ", rating_range, type(rating_range))
columns_to_check = filtered_df.columns[5:amountofcolumns]
counts_df = pd.DataFrame(0, index=rating_range, columns=columns_to_check)


# Define a function to count occurrences of numbers from 0 to 5
def count_numbers(column):
    counts = {i: 0 for i in range(6)}
    for value in column:
        if value in counts:
            counts[value] += 1
    return counts



# Iterate through DataFrame and update counts while filtering rows
filtered_rows = []
# Iterate through filtered_df, calculate ratings, and update the counts DataFrame
index_to_remove = []
for index, row in filtered_df.iterrows():
        for x in range(5,amountofcolumns):
            filtered_df.at[index, filtered_df.columns[x]] = calc_rating(row[:5], filtered_df.columns[x])

if evendist == False:

            
    filtered_df = filtered_df.fillna(0.0)
    filtered_df.to_csv('filtered_data.csv', index=False)
    # Create a new DataFrame to store the counts
    count_df = pd.DataFrame(index=range(6), columns=columns_to_check)

    # Count the numbers from 0 to 5 for each column and update count_df
    for col in columns_to_check:
        counts = count_numbers(filtered_df[col])
        for number in counts:
            count_df.at[number, col] = counts[number]


    # Count how many times each number from 0 to 5 appears in each column
    df_counter= filtered_df[columns_to_check]
    counts = df_counter.apply(pd.Series.value_counts).fillna(0).astype(int)
    totalratings = alldata_panda.size
    print("Filtered DataFrame:")
    print(filtered_df)
    print("\nCounts DataFrame:")
    print(count_df)
    print("total amount of ratings: ", totalratings)

    # used for plotting data distribution
    count_df.to_csv('distribuiton_ratings.csv', index=False)

    print("total amount of ratings: ", totalratings)

