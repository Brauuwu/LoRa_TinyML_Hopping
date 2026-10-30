import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, f1_score, precision_score, accuracy_score, confusion_matrix, recall_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import balanced_accuracy_score
from sklearn.linear_model import LinearRegression
import seaborn as sns
import matplotlib.pyplot as plt
import time

# List to store the execution times
execution_times_training = []
execution_times_inference = []

# sample sizes the model should run on 

samples_number = [i for i in range(100, 22000, 2000)]

# lists for measured metrics for analysis later
accuracy_list = []
f1score_list = []
precision_list = []
recall_list = []
mse_list = []
mae_list = []
rmse_list = []
r2_score_list = []

def mark_specific_values(list_of_lists, values=[1, 2, 3, 4, 5]):
    # Resultant list of lists (one sublist for each sublist in the input list_of_lists)
    all_marked_lists = []

    # Iterate over each sublist in the list of lists
    for sublist in list_of_lists:
        # Initialize a list to hold the marked lists for the current sublist
        marked_lists = []

        # Iterate over each value we are interested in (1 to 5)
        for value in values:
            # Create a new list marking 1 where the value is found, and 0 otherwise
            marked_list = [1 if element == value else 0 for element in sublist]
            # Append this marked list to the marked_lists for the current sublist
            marked_lists.append(marked_list)

        # Append the list of marked lists (for current sublist) to all_marked_lists
        all_marked_lists.append(marked_lists)

    return all_marked_lists


def flatten(nested_list):
    # Initialize an empty list to hold the flattened elements
    flat_list = []

    # Define a recursive function to process each element
    def _flatten(sublist):
        for element in sublist:
            if isinstance(element, list):
                _flatten(element)
            else:
                flat_list.append(element)

    # Start the flattening process
    _flatten(nested_list)

    return flat_list

for sample_nr in samples_number:
    # calculated data
    alldata = pd.read_csv('CosineRatingsNew_10.csv', sep=',')
    alldata = alldata[:sample_nr]
    num_rows = alldata.shape[0]

    # Extract features and target variables
    # Get the names of the first 5 columns
    soils = alldata.iloc[:, [0, 1, 2, 3, 4]]  # Replace indices with actual column indices if known
    print("soils", soils, type(soils),"should be df")

    # Get the names of the first 5 columns
    ratings = alldata.iloc[:, 5:]  

    # X and y extraction
    ratings = ratings.astype(int)
    X = soils.values
    y = ratings.values

    # Random data seed for reproducibility
    np.random.seed(42)
    
    # Normalize input data
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    #print("y_test", y_test, type(y_test))
    y_test_rounded = y_test.round(0)

    y_test_rounded_list = y_test_rounded.tolist()
    # Convert each element in the nested lists to an integer
    int_list_test = [[int(element) for element in sublist] for sublist in y_test_rounded_list]    # Iterate over each sublist

    y_test_binary = mark_specific_values(int_list_test)

    #measuring trainig time
    start_time = time.time()


    #KNN
    #model = KNeighborsRegressor(n_neighbors=5)
    #model.fit(X_train, y_train)
    # Neural Network 
    #model = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42)
    #model = MLPRegressor(hidden_layer_sizes=(50, 50, 50), activation='relu', solver='adam',alpha=0.0001,learning_rate='adaptive',learning_rate_init=0.001,max_iter=200, random_state=42)  # For reproducibility
    #model.fit(X_train, y_train) 
    # linear regression
    #model = LinearRegression()
    #model.fit(X_train, y_train)
    # Decsion tree
    model = DecisionTreeRegressor(random_state=42)
    model.fit(X_train, y_train)
    # random forest
    #model = RandomForestRegressor(n_estimators=100, random_state=42)
    #model.fit(X_train, y_train)
    # gradient boost SPAETER NACHMAL!! HAT NICHT FUNKTIONIERT
    #model = MultiOutputRegressor(GradientBoostingRegressor(n_estimators=100, random_state=42))
    #model.fit(X_train, y_train)
    # exterm gradient boosting
    #model = XGBRegressor(n_estimators=100, random_state=42)
    #model.fit(X_train, y_train)
 

    # Record the end time
    end_time = time.time()
    
    # Calculate the elapsed time
    elapsed_time = end_time - start_time
    
    # Append the elapsed time to the list
    execution_times_training.append(elapsed_time)

    # Example input data for a new object
    new_data = np.array([[99, 123, 201, 6.4, 22]])
    new_data_scaled = scaler.transform(new_data)

    y_pred = model.predict(X_test)
    
    # test data to measure mean inference time
    datalisttotest = np.array([[100, 870, 240, 6.7, 30],
                              [34, 428, 178, 6.5, 2],
                              [170, 60, 220, 6.3, 36],
                              [3, 7, 12, 6.2, 45],
                              [165, 47, 230, 6.8, 37],
                              [17, 15, 70, 6.1, 12],
                              [125, 37, 230, 6.2, 37],
                              [185, 12, 130, 7.5, 12],
                              [135, 47, 230, 8, 17],
                              [15, 37, 290, 6.2, 49]])
     # Example input data for a new object
    new_data = np.array([[105, 37, 230, 6.2, 37]])

    listofinftime = []
    new_data_scaled = scaler.transform(new_data)
    for x in datalisttotest:
        new_data_scaled = scaler.transform(x.reshape(1, -1))
        start_time_inf= time.time()
        predicted_ratings = model.predict(new_data_scaled)
        end_time_inf = time.time()
        rounded_ratings = np.round(predicted_ratings).astype(int)
        elapsed_time_individe = end_time_inf - start_time_inf
        listofinftime.append(elapsed_time_individe)


    average_elapsed_time = np.mean(listofinftime)
    print("Average Prediction Time: ", average_elapsed_time)
  
    # Append the elapsed time to the list
    execution_times_inference.append(average_elapsed_time)
    mae = mean_absolute_error(y_test, y_pred)
    print(f'\nMean Absolute Error on test data: {mae:.2f}')

    # Example input data for a new object
    new_data = np.array([[10, 30, 23, 6, 22]])
    new_data_scaled = scaler.transform(new_data)

    # Predict ratings
    predicted_ratings = model.predict(new_data_scaled)
    rounded_ratings = np.round(predicted_ratings).astype(int)

    print("Predicted ratings:", rounded_ratings, type(rounded_ratings))

    # Get the indices of the top N ratings
    top_n = 15
    recommended_indices = np.argsort(predicted_ratings[0])[-top_n:][::-1]
    print(f'Recommended ratings indices: {recommended_indices}')

    y_pred_rounded = y_pred.round(0)
    y_pred_rounded_list = y_pred_rounded.tolist()
    int_list = [[int(element) for element in sublist] for sublist in y_pred_rounded_list]    # Iterate over each sublist

    y_pred_binary = mark_specific_values(int_list)

    flattened_list_y_Test_bin = flatten(y_test_binary)
    flattened_list_y_pred_bin = flatten(y_pred_binary)

    # Calculate Accuracy
    accuracy = accuracy_score(flattened_list_y_Test_bin, flattened_list_y_pred_bin)
    print(f'\nAccuracy on test data: {accuracy:.2f}')
    accuracy_list.append(accuracy)

    # Calculate Recall
    recall = recall_score(flattened_list_y_Test_bin, flattened_list_y_pred_bin, average='micro')  # Use 'micro' to calculate metrics globally
    print(f'Recall on test data: {recall:.2f}')
    recall_list.append(recall)

    # Calculate Precision
    precision = precision_score(flattened_list_y_Test_bin, flattened_list_y_pred_bin, average='micro')  # Use 'micro' to calculate metrics globally
    print(f'Precision on test data: {precision:.2f}')
    precision_list.append(precision)
 
    # Calculate F1 Score
    f1 = f1_score(flattened_list_y_Test_bin, flattened_list_y_pred_bin, average='micro')  # Use 'micro' to aggregate the scores globally
    print(f'\nF1 Score on test data: {f1:.2f}')
    f1score_list.append(f1)

    # Calculate additional regression metrics
    mse = mean_squared_error(y_test, y_pred)
    print("mse: ", mse)
    mse_list.append(mse)
    mae = mean_absolute_error(y_test, y_pred)
    mae_list.append(mae)
    rmse = np.sqrt(mse)
    rmse_list.append(rmse)
    r2 = r2_score(y_test, y_pred)
    r2_score_list.append(r2)
  


#print("times taken for individual training: ", execution_times_training)
data = {
    'samplesize': samples_number,
    'accuracy': accuracy_list,
    'recall' : recall_list,
    'precision': precision_list,
    'F1Score': f1score_list,
    'mse': mse_list,
    'mae': mae_list,
    'rmse': rmse_list,
    'r2_score' : r2_score_list,
    'executiontimetraining': execution_times_training,
    'executiontimeinference': execution_times_inference
   
}

# Create DataFrame
parameters = pd.DataFrame(data)
# Write DataFrame to a CSV file
namefile = 'model_parameters_DT_10.csv'
parameters.to_csv(namefile, index=False)

print("DataFrame written to ", namefile)
plt.figure()
plt.plot(samples_number, accuracy_list,  marker='o', color= 'b',  label="Accuracy") 
plt.plot(samples_number, f1score_list , marker='+', color= 'g',label="F1 score") 
plt.xlabel(  'Number of soils', fontsize=22)
plt.ylabel(  'Prediction performance',  fontsize=22)
plt.xticks(fontsize=20)
plt.xticks(rotation=45)
plt.yticks(fontsize=20)
plt.legend(fontsize=20)
plt.grid(which='major', color='#DDDDDD', linewidth=0.8)   # draw grid for major ticks
plt.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.8)
plt.minorticks_on()
plt.ylim([0, 1.03])
plt.savefig('performance_vs_nr_of_samples.pdf', bbox_inches='tight')
plt.show()

print("DONE")
