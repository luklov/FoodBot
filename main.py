import pandas as pd
import requests

import os
from datetime import datetime, timedelta
station_df = []

station_names = []

all_data = {}
weight_data = {}
station_data = {}

directory = 'data'
prefix = '餐线消费数据-'

def getDate():
    # Return the current date
    return datetime.now().strftime('%Y-%m-%d')

def getWeights(startDate, endDate):
    global weight_data

    api_url = "http://10.10.0.44/beijingdev/dev/getrecord"
    startDateForm = startDate.strftime('%Y-%m-%d')
    endDateForm = endDate.strftime('%Y-%m-%d')
    params = {
        "beginTime": startDateForm,
        "endTime": endDateForm
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        api_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error: Unable to decode JSON response from API. Response text: {response.text}")
        api_data = []
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        api_data = []

    # Store API data into the global dictionary
    for data in api_data:
        peopleCard = data.get('peopleCard')
        if peopleCard:
            weight_data[peopleCard] = data

    return weight_data

def getStation(filename):
    global station_data

    file_path = os.path.join(directory, f'{prefix}{filename}.xlsx')
    excel_file = pd.read_excel(file_path, sheet_name=None)  # Read the Excel file
    if filename != 'June':
        station_data[filename] = list(excel_file.values())[0]  # Store the DataFrame in the dictionary
    else:
        print(f"Filename: {filename}")
        for sheet_name, sheet_data in excel_file.items():
            station_data[sheet_name] = sheet_data  # Store the DataFrame in the dictionary
    return station_data

def getAllStations():
    global station_data
    station_data = {}

    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(".xlsx"):
            getStation(filename.replace('.xlsx', '').replace('餐线消费数据-', ''))


def makeReport(stationRanks):
    for station, count in stationRanks.items():
        print(f"Station: {station}, Count: {count}")
    return

def analyze():
    stationRanks = station_df['POS机名称'].value_counts().to_dict()
    return stationRanks


def report(startDateStr, endDateStr):
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d')
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d')

    #getAllStations()
    #getWeights(startDate, endDate) # puts weights in dict
    getStation(startDateStr)
    getWeights(startDate, endDate) # puts weights in dict

    if not station_data:
        print("No station data found for the given date range.")
        return
    if not weight_data:
        print("No weight data found for the given date range.")
        return

    print(f"Station Data: {station_data}")
    print(f"Weight Data: {weight_data}")
    # Merge the Excel data and API data based on user ID (peopleCard)

    #merge_data()
    '''
    if merged_data.empty:
        print("No matching data found between station data and weight data.")
        return
    
    # Save merged file
    if (startDate == endDate):
        output_file_path = f"merges/merged_data_{startDate.strftime('%Y-%m-%d')}.xlsx"
    else:
        output_file_path = f"merges/merged_data_{startDate.strftime('%Y-%m-%d')}_{endDate.strftime('%Y-%m-%d')}.xlsx"

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    merged_data.to_excel(output_file_path, index=False)

    stationRanks = analyze(merged_data)
    makeReport(stationRanks)'''
    return

def merge_data():
    global all_data
    conversion_table = pd.read_excel('conversion.xls')
    # Save or further process the result
    all_data.to_csv('merged_data.csv', index=False)
    
current_date = getDate()
print(f"Current Date: {current_date}")
report("2024-05-15", "2024-05-15")