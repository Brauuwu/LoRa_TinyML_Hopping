import pandas as pd
import numpy as np
import random


alldata_panda = pd.read_csv('NoZeros_2.csv', sep = ',')
ideal = pd.read_csv("optplants2.csv")
print("alldata panda", alldata_panda)

amountofcolumns = alldata_panda.shape[1] 
#set max value for the percentage of values that should be set to NaN. there it would be 30 percent and therefor in line 26 thr min value is set to 29 
amountofratings = 31

# Specify the range of column indices to set to NaN 
indices_to_set_nan = range(5, 105)

# Get the column names from the range of indices
columns_to_set_nan = alldata_panda.columns[indices_to_set_nan]

#use copy 
data_copy = alldata_panda.copy()

print( "data copy",data_copy, " data panda", alldata_panda)
for index, row in alldata_panda.iterrows():
    my_list = [i for i in range(5,amountofcolumns)]
    my_size =  np.random.randint(29, amountofratings)
    my_prob = [1/len(my_list) for _ in range(len(my_list))]
    choices_list = np.random.choice(my_list, my_size,replace = False, p=my_prob)
    #print("choice list", choices_list)
    
    for x in choices_list:
        data_copy.at[index, alldata_panda.columns[x]] = np.nan
    
    # for testing
    if index >= 50000:
        break

df_ratings = data_copy.iloc[:,5:]
print("df ratings", df_ratings)
# Total number of elements in the DataFrame
total_elements = df_ratings.size

# Number of NaN values in the DataFrame
nan_count = df_ratings.isna().sum().sum()

# Percentage of NaN values in the DataFrame
nan_percentage = (nan_count / total_elements) * 100

print(f"Percentage of NaN values in the DataFrame: {nan_percentage:.2f}%")
print(data_copy)
data_copy.to_csv('cosine30.csv', sep = ',')



