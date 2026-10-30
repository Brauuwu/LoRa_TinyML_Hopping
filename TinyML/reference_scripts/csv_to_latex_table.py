import pandas as pd
from tabulate import tabulate

# Path to your CSV file
csv_file = "output_statistics_random.csv"  # Replace with your CSV file path

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file)

# Convert the DataFrame to a LaTeX table using tabulate
latex_table = tabulate(df, headers='keys', tablefmt='latex', showindex=False)

# Save the LaTeX table to a .tex file
output_file = "output_statistics_random.tex"
with open(output_file, "w") as f:
    f.write(latex_table)

print(f"LaTeX table saved to {output_file}")
