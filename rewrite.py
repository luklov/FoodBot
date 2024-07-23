import os
import re
from datetime import datetime
from main import convert_api_id, make_conversion_dicts
import pandas as pd

# Function to convert date string from "Month Day" to "YYYY-MM-DD"
def convert_date_string(date_str):
    try:
        # Parse the date string to a datetime object
        date_obj = datetime.strptime(date_str, "%b %d")
        # Set the correct year
        date_obj = date_obj.replace(year=2024)
        # Convert to the desired format
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None
def rename_files(folder_path):
    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the filename matches the pattern "餐线消费数据-May 13.xlsx"
        match = re.match(r"餐线消费数据-(\w+ \d+).xlsx", filename)
        if match:
            # Extract the date part from the filename
            date_part = match.group(1)
            # Convert the date part to the desired format
            new_date_part = convert_date_string(date_part)
            if new_date_part:
                # Create the new filename
                new_filename = f"餐线消费数据-{new_date_part}.xlsx"
                # Get the full file paths
                old_file_path = os.path.join(folder_path, filename)
                new_file_path = os.path.join(folder_path, new_filename)
                
                # Check if the new filename already exists
                if not os.path.exists(new_file_path):
                    # Rename the file
                    os.rename(old_file_path, new_file_path)
                    print(f"Renamed: {filename} -> {new_filename}")
                else:
                    print(f"File {new_filename} already exists. Skipping renaming {filename}.")
            else:
                print(f"Failed to convert date for file: {filename}")
        else:
            print(f"Filename does not match pattern: {filename}")

    print("Renaming completed.")

def convert_ids_in_excel(file_path, sheet_name):
    # Load the Excel file
    xls = pd.ExcelFile(file_path)

    # Check if the sheet exists
    if sheet_name in xls.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(xls, sheet_name)

        # Check if the "会员编号" column exists
        if "会员编号" in df.columns:
            # Replace the values in the "会员编号" column
            for i in range(len(df["会员编号"])):
                converted_id = convert_api_id(df.loc[i, "会员编号"])
                df.loc[i, "会员编号"] = converted_id if converted_id else 'No Match'

            # Write the modified DataFrame back to the Excel file
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            print(f"Sheet '{sheet_name}' does not contain '会员编号' column.")
    else:
        print(f"Sheet '{sheet_name}' does not exist in the Excel file.")

#rename_files("data")
make_conversion_dicts()
convert_ids_in_excel("data/餐线消费数据-June.xlsx", "Jun 19")