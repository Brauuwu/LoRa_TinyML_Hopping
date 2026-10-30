import pandas as pd
import numpy as np


# Load the CSV file
alldata = pd.read_csv('filtered_data_uneven.csv', sep=',')

# Select columns from index 5 to index 20 (column indices are zero-based)
columns_to_inspect = alldata.columns[5:]
calculatedratings = alldata[columns_to_inspect]

# Print the selected columns to inspect
print("Selected columns to inspect:")
print(calculatedratings)

# Identify rows that contain one or more zeros in the specified columns
one_or_more_zeros = (calculatedratings == 0).any(axis=1)
print("\nRows that contain one or more zeros in the specified columns:")
print(one_or_more_zeros)

# Filter the original DataFrame to show only rows that have no zeros in the specified columns
rows_with_no_zeros = alldata[~one_or_more_zeros]
print("\nRows with no zeros in the specified columns:")
print(rows_with_no_zeros)
rows_with_no_zeros.to_csv('NoZeros_2.csv', index=False)