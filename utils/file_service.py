# Imports
import os
import json
import pandas as pd
import openpyxl # type: ignore

def appendToDictList(file_path, dict):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                        existing_data = []
    else: existing_data = []

    existing_data.append(dict)
    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)

# Reads the XLSX file and convert the raw data into list of dict
def xlsx_to_list_of_dicts(file_path, sheet_name=None):
    workbook = openpyxl.load_workbook(file_path)
    
    # If no sheet name is provided, use the active sheet
    if sheet_name is None:
        sheet = workbook.active
    else:
        sheet = workbook[sheet_name]
    
    data_list = []
    headers = [cell.value for cell in sheet[1]]  # Assuming first row is headers
    
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Starting from second row
        row_dict = {headers[i]: row[i] for i in range(len(headers))}
        data_list.append(row_dict)
    
    return data_list

def list_of_dicts_to_xlsx(file_path, dicts):
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(dicts)
    # Save the DataFrame to an Excel file
    df.to_excel(file_path, index=False)