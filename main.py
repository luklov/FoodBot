import pandas as pd
import requests

import os
from datetime import datetime, timedelta


def getDate():
    # Return the current date
    return datetime.now().strftime('%Y-%m-%d')

def getWeights(startDate, endDate):
    api_url = "http://10.10.0.44/beijingdev/dev/getrecord"
    startDateForm = startDate.strftime('%Y-%m-%d')
    endDateForm = endDate.strftime('%Y-%m-%d')
    params = {
        "beginTime": startDateForm,
        "endTime": endDateForm
    }
    # Fetch data from the API
    response = requests.get(api_url, params=params)
    try:
        api_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error: Unable to decode JSON response from API. Response text: {response.text}")
        api_data = []

    # Convert API data to DataFrame
    api_df = pd.DataFrame(api_data)
    return api_df

def getStations(startDate, endDate):
    excel_data = []
    current_date = startDate
    
    while current_date <= endDate:
        file_path = f"data/线消费数据-{current_date.strftime('%Y-%m-%d')}.xlsx"
        if os.path.exists(file_path):
            excel_data.append(pd.read_excel(file_path))
        current_date += timedelta(days=1)
    
    # Concatenate all data into a single DataFrame
    if excel_data:
        combined_excel_data = pd.concat(excel_data, ignore_index=True)
    else:
        combined_excel_data = pd.DataFrame()
    
    return combined_excel_data

def makeReport(stationRanks):
    print(stationRanks)
    return

def rangeReport(startDate, endDate):
    startDate = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = datetime.strptime(endDate, '%Y-%m-%d')

    excel_data = getStations(startDate, endDate)
    api_df = getWeights(startDate, endDate)

    # Merge the Excel data and API data based on user ID (peopleCard)
    merged_data = pd.merge(excel_data, api_df, left_on="UserID", right_on="peopleCard", how="inner")
        
    # Save merged file
    if (startDate == endDate):
        output_file_path = f"merges/merged_data_{startDate.strftime('%Y-%m-%d')}.xlsx"
    else:
        output_file_path = f"merges/merged_data_{startDate.strftime('%Y-%m-%d')}_{endDate.strftime('%Y-%m-%d')}.xlsx"

    merged_data.to_excel(output_file_path, index=False)
    stationRanks = analyze(merged_data)
    makeReport(stationRanks)
    return

def analyze(merged_data): # Analyze data and save into lists
    stationRanks = {33}
    return stationRanks

current_date = getDate()
rangeReport("2024-5-15", "2024-5-15")