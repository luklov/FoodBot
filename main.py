import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta

all_data = {}
weight_data = {}
station_data = {}

conversion_dict = {}
reverse_conversion_dict = {}

directory = 'data'
prefix = '餐线消费数据-'

def make_conversion_dicts():
    global conversion_dict, reverse_conversion_dict
    # Merge the Excel data and API data based on user ID (peopleCard)
    conversion_table = pd.read_excel('conversion.xls')
    conversion_dict = dict(zip(conversion_table['会员编号'], conversion_table['卡号']))
    reverse_conversion_dict = {v: k for k, v in conversion_dict.items()}

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
            weight_data[peopleCard.lstrip('0')] = data

    return weight_data

def getStation(filename):
    global station_data

    file_path = os.path.join(directory, f'{prefix}{filename}.xlsx')
    excel_file = pd.read_excel(file_path, sheet_name=None)  # Read the Excel file
    if filename != 'June':
        station_data[filename] = list(excel_file.values())[0]  # Store the DataFrame in the dictionary
    else:
        for sheet_name, sheet_data in excel_file.items():
            #api_id = convert_id(cnt_id) # short to long ID
            # insert code here
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
    
    return


def report(startDateStr, endDateStr):
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d')
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d')

    getAllStations()
    #getWeights(startDate, endDate) # puts weights in dict
    #getStation(startDateStr)
    getWeights(startDate, endDate) # puts weights in dict

    if not station_data:
        print("No station data found for the given date range.")
        return
    if not weight_data:
        print("No weight data found for the given date range.")
        return

    print(f"Station Data: {station_data}")
    #print(f"Weight Data: {weight_data}")
    make_conversion_dicts()
    merge_data()

    '''stationRanks = analyze(merged_data)
    makeReport(stationRanks)'''
    return

def merge_data():
    global all_data
    all_data = {}
    found, notFound = [], []
    # print first 10 entries in weight_data
    for key in list(weight_data.keys())[:10]:
        print(key, weight_data[key])
    for day, df in station_data.items():
        print("DAY: ", day)

        member_id = df['会员编号'] # Get list of IDs on each day
        pos_name = df['POS机名称'] # Get list of POS names on each day
        for i, cnt_id in enumerate(member_id):
            api_id = convert_cnt_id(cnt_id) # short to long ID
            if not api_id:
                notFound.append(cnt_id) 
                continue # Skip the person if the ID cannot be converted
            found.append(cnt_id)
            api_id = str(int(api_id))
            
            if cnt_id not in all_data:
                all_data[cnt_id] = {}
            if day not in all_data[cnt_id]:
                all_data[cnt_id][day] = {'station': [], 'weights': []}
            
            all_data[cnt_id][day]['station'].append(pos_name[i])
            
            
            if api_id in weight_data: # Check if the ID exists in the weight data
                print("Weight data found :", weight_data[api_id])
                weight_info = weight_data[api_id]
                all_data[cnt_id][day]['weights'].append(weight_info)

    print(f"Found {len(found)} IDs and {len(notFound)} IDs were not found in the conversion table.")
    print(notFound)
    # Save the dictionary to a JSON file
    with open('combined_data/merged_data.json', 'w') as f:
        json.dump(all_data, f, default=set_default) 

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def convert_cnt_id(cnt_id): # short ID to long ID
    #print(conversion_dict)
    api_id = conversion_dict.get(cnt_id, None)
    if not api_id:
        print(f"ID {cnt_id} not found in the conversion table.")
    else:
        print(f"Converted from {cnt_id} to {api_id}")
    return api_id

def convert_api_id(api_id): # long ID to short ID, REVERSE
    cnt_id = reverse_conversion_dict.get(api_id, None)
    if not cnt_id:
        print(f"API ID {api_id} not found in the conversion table.")
    else:
        print(f"Converted from {api_id} to {cnt_id}")
    return cnt_id

if __name__ == "__main__":
    current_date = getDate()
    print(f"Current Date: {current_date}")
    report("2024-05-13", "2024-05-14") # Start date, end date