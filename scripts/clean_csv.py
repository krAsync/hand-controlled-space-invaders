import csv
import os

input_file = '../data/numbers/left.csv'
output_file = '../data/numbers/left_cleaned.csv'
expected_columns = 43

if not os.path.exists(input_file):
    print(f"Input file not found: {input_file}")
else:
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for i, row in enumerate(reader):
            if len(row) == expected_columns:
                writer.writerow(row)
            else:
                print(f"Skipping malformed row {i+1} with {len(row)} columns.")

    os.replace(output_file, input_file)
    print("CSV cleaning complete for left.csv")