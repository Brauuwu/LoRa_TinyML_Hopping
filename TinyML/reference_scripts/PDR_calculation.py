import pandas as pd



file_names = ["A_B_C_868.csv"]#,"A_868.csv",    "A_C_868.csv",  "B_868.csv",  "B_C_868.csv",  "C_868.csv",
            #  "A_869.csv",  "A_B_869.csv",  "A_C_869.csv",  "B_869.csv",  "B_C_869.csv",  "C_869.csv",
            #  "A_870.csv", "A_B_870.csv",  "A_C_870.csv",  "B_870.csv",  "B_C_870.csv",  "C_870.csv",
            #  ]
for _file in file_names:
    
    
    # Input CSV file path
    input_file = 'formattedCSV/'+_file

    # Read the CSV file
    df = pd.read_csv(input_file)

    # Filter rows where RSSI = -1000
    filtered_df = df[df["RSSI"] == -1000]
    filtered_df2 = df[df["RSSI"] != -1000]

    # Group by source and size_of_message, and count rows
    counts = filtered_df.groupby(["source", "size_of_message"]).size().to_dict()
    # Group by source and size_of_message and calculate the mean for RSSI and SNR
    averages = (
        filtered_df2.groupby(["source", "size_of_message"])[["RSSI", "SNR"]]
        .mean()
        .reset_index()
    )

    # Display the resulting DataFrame
    print("Average RSSI and SNR grouped by source and size_of_message:")
    print(averages)

    # Display the resulting dictionary
    print("Counts of rows with RSSI = -1000, grouped by source and size_of_message:")
    print(counts)
