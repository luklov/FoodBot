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

def load_data():
    global all_data
    with open('combined_data/merged_data.json', 'r') as f:
        all_data = json.load(f)

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
        cardNum = peopleCard.lstrip('0')
        day = data.get('addTime').split(' ')[0]
        if cardNum not in weight_data:
            weight_data[cardNum] = {}
            weight_data[cardNum]['peopleName'] = data.get('peopleName')
            weight_data[cardNum]['house'] = data.get('house')
            weight_data[cardNum]['yeargroup'] = data.get('yeargroup')
            weight_data[cardNum]['formclass'] = data.get('formclass')
        if day not in weight_data[cardNum]:
            weight_data[cardNum][day] = []
        weight_data[cardNum][day].append(data['weight'])

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
    '''for key in list(weight_data.keys())[:10]:
        print(key, weight_data[key])'''
    for day, df in station_data.items():
        print("DAY: ", day)

        member_id = df['会员编号'] # Get list of IDs on each day
        pos_name = df['POS机名称'] # Get list of POS names on each day
        for i, cnt_id in enumerate(member_id):
            if cnt_id == 'No Match': # Skip if ID in June data not convertable
                continue
            api_id = convert_cnt_id(cnt_id) # short to long ID
            if not api_id: # Skip the person if the ID cannot be converted
                notFound.append(cnt_id) 
                continue 
            if api_id == 1634029292:
                print("ID 1634029292 found") # Me
            found.append(cnt_id)
            api_id = str(int(api_id))
            
            if cnt_id not in all_data:
                all_data[cnt_id] = {}
            if day not in all_data[cnt_id]:
                all_data[cnt_id][day] = {'stations': [], 'weights': []}

            all_data[cnt_id][day]['stations'].append(pos_name[i])
            
            
            if api_id in weight_data: # Check if the ID exists in the weight data
                #print("Weight data found :", weight_data[api_id])
                weight_info = weight_data[api_id]
                if day in weight_info:
                    #print("Weight data found :", weight_info[day])
                    all_data[cnt_id][day]['weights'].append(weight_info[day])
                if 'name' not in all_data[cnt_id]:
                    all_data[cnt_id]['name'] = weight_info['peopleName']
                    all_data[cnt_id]['house'] = weight_info['house']
                    all_data[cnt_id]['yeargroup'] = weight_info['yeargroup']
                    all_data[cnt_id]['formclass'] = weight_info['formclass']

    print(f"Found {len(found)} IDs and {len(notFound)} IDs were not found in the conversion table.")
    #print(notFound)
    # Save the dictionary to a JSON file
    with open('combined_data/merged_data.json', 'w') as f:
        json.dump(all_data, f, default=set_default) 

def categorize_data():
    categories = {
        'weights_no_counters': 0,
        'counters_no_weights': 0,
        'both': 0,
        'multiple_weights_no_counters': 0,
        'multiple_counters_no_weights': 0,
        'multiple_both': 0
    }

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue
            has_weights = 'weights' in day_data and day_data['weights']
            has_counters = 'stations' in day_data and day_data['stations']
            multiple_weights = has_weights and len(day_data['weights']) > 1
            multiple_counters = has_counters and len(day_data['stations']) > 1

            if multiple_weights and not has_counters:
                categories['multiple_weights_no_counters'] += 1
            elif multiple_counters and not has_weights:
                categories['multiple_counters_no_weights'] += 1
            elif multiple_counters and multiple_weights:
                categories['multiple_both'] += 1
            elif has_weights and not has_counters:
                categories['weights_no_counters'] += 1
            elif has_counters and not has_weights:
                categories['counters_no_weights'] += 1
            elif has_counters and has_weights:
                categories['both'] += 1

    return categories

def calculate_average_wastage():
    counter_wastage = {}
    counter_days = {}

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue
            has_weights = 'weights' in day_data and day_data['weights']
            has_counters = 'stations' in day_data and day_data['stations']

            if has_weights and has_counters:
                # Flatten the list of weights
                flat_weights = [item for sublist in day_data['weights'] for item in sublist]
                total_weight = sum(flat_weights)
                weight_per_counter = total_weight / len(day_data['stations'])

                for counter in day_data['stations']:
                    if counter not in counter_wastage:
                        counter_wastage[counter] = 0
                        counter_days[counter] = 0
                    counter_wastage[counter] += weight_per_counter
                    counter_days[counter] += 1

    average_wastage = {counter: total_wastage / counter_days[counter] for counter, total_wastage in counter_wastage.items()}

    return average_wastage, counter_wastage, counter_days

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def convert_cnt_id(cnt_id): # short ID to long ID
    #print(conversion_dict)
    api_id = conversion_dict.get(cnt_id, None)
    '''if not api_id:
        print(f"ID {cnt_id} not found in the conversion table.")
    else:
        print(f"Converted from {cnt_id} to {api_id}")'''
    return api_id

def convert_api_id(api_id): # long ID to short ID, REVERSE
    cnt_id = reverse_conversion_dict.get(api_id, None)
    '''if not cnt_id:
        print(f"API ID {api_id} not found in the conversion table.")
    else:
        print(f"Converted from {api_id} to {cnt_id}")'''
    return cnt_id

def rank_counters(average_wastage, total_wastage, counter_days):
    average_wastage_ranked = sorted(average_wastage.items(), key=lambda item: item[1], reverse=True)
    total_wastage_ranked = sorted(total_wastage.items(), key=lambda item: item[1], reverse=True)
    counter_days_ranked = sorted(counter_days.items(), key=lambda item: item[1], reverse=True)

    print("Average Wastage Ranking:")
    for counter, wastage in average_wastage_ranked:
        print(f"{counter}: {wastage} grams")

    print("\nTotal Wastage Ranking:")
    for counter, wastage in total_wastage_ranked:
        print(f"{counter}: {wastage} grams")

    print("\nCounter Days Ranking:")
    for counter, days in counter_days_ranked:
        print(f"{counter}: {days} grams")

if __name__ == "__main__":
    #current_date = getDate()
    #report("2024-05-13", "2024-06-19") # Start date, end date
    load_data()

    categories = categorize_data()
    for category, count in categories.items():
        print(f"{category}: {count} days")

    print("\n")
    
    average_wastage, total_wastage, counter_days = calculate_average_wastage()

    rank_counters(average_wastage, total_wastage, counter_days)