# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 17:12:20 2024

@author: lenovo
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, time
import re
import math 
import csv
import glob

def get_day_of_week(date_str):
    date_obj = datetime.strptime(date_str, '%d-%b-%Y')
    return date_obj.strftime('%A')

def extract_second_value(x):
    if isinstance(x, str):
        split_values = x.split(',')
        if len(split_values) > 1:
            return split_values[-2].strip()
        else:
            return np.nan
    else:
        return np.nan

def process_punch_log_file(filename, df_exemptedFaculty):
    pattern = r'(\d{2}-\w{3}-\d{4})'
    match = re.search(pattern, filename)

    if match:
        date_str = match.group(1)
        day_str  = get_day_of_week(date_str)

    df = pd.read_csv(filename)
    selected_columns = ['Employee Code','Employee Name','Last Punch','Punch Records']
    df_selected = df[selected_columns].copy()

    df_selected.loc[:,'Punch Records'] = df_selected['Punch Records'].apply(extract_second_value)

    def parse_time(x):
        if isinstance(x, str) and x.strip():
            return pd.to_datetime(x, format='%H:%M:%S').time()
        else:
            return np.nan

    df_selected['Last Punch'] = df_selected['Last Punch'].apply(parse_time)
    df_selected['Punch Records'] = df_selected['Punch Records'].apply(parse_time)

    df_selected['InTime'] = ''
        
    if day_str in df_exemptedFaculty.columns:
        for index, row in df_selected.iterrows():
            employee_code_value = row["Employee Code"]

            if employee_code_value in df_exemptedFaculty[day_str].values:
                logout_value = df_selected.loc[df_selected.index[df_selected["Employee Code"]==employee_code_value].item()].iloc[3]
                if not isinstance(logout_value, float):
                    if time(8,00,00) > logout_value:
                        logout_value = time(8,00,00)
            else:
                logout_value = df_selected.loc[df_selected.index[df_selected["Employee Code"]==employee_code_value].item()].iloc[3]
                if not isinstance(logout_value, float):
                    if time(8,00,00) > logout_value:
                        logout_value = time(8,00,00)
            df_selected.at[index, 'InTime'] = logout_value
            
    else:
        print(f"The column {day_str} does not exist in the DataFrame.")
                
    df_selected['OutTime'] = df_selected['Last Punch'].apply(
        lambda x: datetime.strptime('16:30:00', '%H:%M:%S').time() 
            if (not pd.isnull(x)) and x > datetime.strptime('16:30:00', '%H:%M:%S').time() 
                else x)

    df_selected['InTime'] = pd.to_datetime(df_selected['InTime'], format='%H:%M:%S', errors='coerce')
    df_selected['OutTime'] = pd.to_datetime(df_selected['OutTime'], format='%H:%M:%S', errors='coerce')
    
    def calculate_time_difference(row):
        if pd.isnull(row['InTime']):
            return None
        time_diff = row['OutTime'] - row['InTime']
        if (row['InTime'].time() > time(8,30,00)) and (row['InTime'].time() < time(10,00,00)):
            return "after 10"
        else:
            return str(time_diff)
    
    df_selected[date_str] = df_selected.apply(calculate_time_difference, axis=1)

    df_selected[date_str ] = df_selected[date_str ].astype(str).str[-8:]
    df_selected['InTime' ] = df_selected['InTime' ].astype(str).str[-8:]
    df_selected['OutTime'] = df_selected['OutTime'].astype(str).str[-8:]

    new_filename = filename.replace("Punch Log", "selvin")

    df_selected.to_csv(new_filename, index=False)

    print(f"Filtered data saved to '{new_filename}'")

def extract_last_column(file_path):
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [row[-1] for row in reader]
    return data

def main():
    df_exemptedFaculty = pd.read_csv('exemptedFaculty.csv')

    current_directory = os.getcwd()
    files = os.listdir(current_directory)

    for file in files:
        if file.endswith('Punch Log.csv'):
            process_punch_log_file(file, df_exemptedFaculty)

    files = glob.glob("*selvin.csv")
    if not files:
        print("No files found matching the pattern '*selvin.csv' in the current directory.")
        return
    
    employee_codes = [
        "Employee Code",
        109, 122, 128, 132, 133, 158, 159, 206, 211, 213,
        216, 230, 833, 270, 280, 281, 283, 277, 291, 292,
        294, 297, 298, 299, 300, 312, 315, 321, 322, 323,
        329, 330, 337, 338
    ]
    
    summary_data = {}
    for file_path in files:
        last_column_data = extract_last_column(file_path)
        file_name = os.path.basename(file_path)
        summary_data[file_name] = last_column_data
    
    df = pd.DataFrame(summary_data)
    
    df.insert(0, "Employee Code", employee_codes)
    
    df.to_csv("summary.csv", index_label="Index")

    print("Summary file 'summary.csv' has been created.")

if __name__ == "__main__":
    main()
