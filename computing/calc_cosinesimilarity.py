import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from numpy import nan

# Load the data
alldata_panda = pd.read_csv('sparseMatrix_10.csv', sep=',')
print(alldata_panda)

# Handling the 'Unnamed: 0' column and selecting columns for processing
if "Unnamed: 0" in alldata_panda.columns:
    alldata_panda = alldata_panda.drop(columns=['Unnamed: 0'])
    selected_columns = alldata_panda.columns[5:1.tolist()
    ratings = alldata_panda.iloc[:, 5:]
    soils = alldata_panda.iloc[:, :5]
else:
    selected_columns = alldata_panda.columns[5:].tolist()
    ratings = alldata_panda.iloc[:, 5:]
    soils = alldata_panda.iloc[:, :5]

print("Selected columns for ratings:", selected_columns)
print("Ratings DataFrame:\n", ratings)
print("Soil properties DataFrame:\n", soils)

# Processing the ratings DataFrame
sparse_df = ratings[selected_columns]
sparse_df.replace(0, nan, inplace=True)
print("Sparse DataFrame (with NaNs):\n", sparse_df)

# Convert DataFrame to sparse format and compute cosine similarity
sparse_matrix = csr_matrix(sparse_df.fillna(0).values)
cosine_sim_matrix = cosine_similarity(sparse_matrix.T)
cosine_sim_df = pd.DataFrame(cosine_sim_matrix, index=sparse_df.columns, columns=sparse_df.columns)
print("Cosine Similarity DataFrame:\n", cosine_sim_df)

# Function to predict ratings
def predict_ratings(ratings_df, similarity_df):
    predictions = ratings_df.copy()
    print(" prediciotns", predictions)
    print(" ratings df", ratings_df)
    # Iterate through all cells that have missing values
    for row, col in zip(*np.where(ratings_df.isna())):
        #print(f"Processing missing value at row: {row}, column: {col}")
        
        try:
            col_name = ratings_df.columns[col]
            #print(f"Column name for index {col}: {col_name}")
            
            # Find similar items (columns) and their similarity scores
            similar_items = similarity_df.loc[:, col_name].drop(col_name).sort_values(ascending=False)            
            similar_items_indices = similar_items.index
            similar_scores = similar_items.values
        
            # Find the ratings given by the user to similar items
            user_ratings = ratings_df.loc[row, similar_items_indices]
            valid_ratings = user_ratings[~user_ratings.isna()]
            
            # Predict the rating using weighted average of valid ratings
            if not valid_ratings.empty:
                sim_scores = similar_scores[:len(valid_ratings)]
                if np.abs(sim_scores).sum() != 0:
                    val = predictions.iloc[row,col]
                    #print(val)
                    predicted_value = (valid_ratings * sim_scores).sum() / np.abs(sim_scores).sum()
                    predictions.at[row, col_name] = np.round(predicted_value, 1)
                    #print("row", row)
                else:
                    predictions.at[row, col_name] = np.round(ratings_df.mean(axis=0)[col_name], 1)
            else:
                predictions.at[row, col_name] = np.round(ratings_df.mean(axis=0)[col_name], 1)
        except KeyError as ke:
            print(f"KeyError: {ke} at row: {row}, column: {col}")
        
    return predictions

# Predict the missing ratings
predicted_ratings = predict_ratings(sparse_df, cosine_sim_df)
print("Predicted Ratings DataFrame:\n", predicted_ratings)

# Save the results
predicted_ratings.to_csv('CosineRatingsNew.csv', sep=',')
soilandratings = pd.concat([soils, predicted_ratings], axis=1)
soilandratings.to_csv('CosineRatingsWithSOILS.csv', sep=',')
print("Soils and ratings combined DataFrame:\n", soilandratings)