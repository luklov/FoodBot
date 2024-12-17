import pandas as pd
import requests
import collections
from collections import defaultdict

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from matplotlib.colors import to_rgba

import json
import os
from datetime import datetime, timedelta

from matplotlib.font_manager import FontProperties

font = FontProperties(fname="/System/Library/Fonts/PingFang.ttc")

directory = 'activeData'
prefix = '餐线消费数据-'

dataFilename = 'combined_data/new_merged_data.json' #merged_data.json

# Set Seaborn theme with the red background and appropriate axis styling
sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#9B0532", "figure.facecolor": "#9B0532", "grid.color": "gray", "axes.edgecolor": "lightgray"})

def make_conversion_dicts():
    
    conversion_table = pd.read_excel('conversion.xls') # Load the Excel file

    conversion_table['卡号'] = conversion_table['卡号'].apply(lambda x: str(int(x)) if pd.notnull(x) else 'NaN') # Convert all the '卡号' values from floats to integers

    conversion_dict = dict(zip(conversion_table['会员编号'], conversion_table['卡号'])) # Create a dictionary mapping the two ID systems
    reverse_conversion_dict = {v: str(k) for k, v in conversion_dict.items()} # Create a reverse dictionary mapping the two ID systems

    if not os.path.exists('conversion_dict'): # Create the directory if it doesn't exist
        os.makedirs('conversion_dict')

    # Save the dictionaries as JSON files
    with open('conversion_dict/conversion_dict.json', 'w') as f:
        json.dump(conversion_dict, f)
    with open('conversion_dict/reverse_conversion_dict.json', 'w') as f:
        json.dump(reverse_conversion_dict, f)

    return conversion_dict, reverse_conversion_dict

def load_conversion_dicts():
    if not os.path.exists('conversion_dict'):
        print("Conversion dictionaries not found. Creating new dictionaries...")
        conversion_dict, reverse_conversion_dict = make_conversion_dicts()

    # Load the dictionaries from the JSON files
    with open('conversion_dict/conversion_dict.json', 'r') as f:
        conversion_dict = json.load(f)
    with open('conversion_dict/reverse_conversion_dict.json', 'r') as f:
        reverse_conversion_dict = json.load(f)

    return conversion_dict, reverse_conversion_dict



def getDate():
    # Return the current date
    return datetime.now().strftime('%Y-%m-%d')

def load_data(file_path = dataFilename):
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return all_data

def getWeightsbyDate(startDate, endDate):
    weight_data = {} # Initialize dictionary to store weight data
    member_info = {}

    api_url = "http://10.10.0.44/beijingdev/dev/getrecord"
    startDateForm = startDate.strftime('%Y-%m-%d') # Convert the date objects to strings
    endDateForm = endDate.strftime('%Y-%m-%d')
    params = { # Parameters for the API request
        "beginTime": startDateForm,
        "endTime": endDateForm
    }
    try:
        response = requests.get(api_url, params=params) # Send a GET request to the API
        response.raise_for_status() # Check for any errors in the response
        api_data = response.json() # Parse the JSON response
    except requests.exceptions.JSONDecodeError: # Handle JSON decoding errors
        print(f"Error: Unable to decode JSON response from API. Response text: {response.text}")
        api_data = []
    except requests.exceptions.RequestException as e: # Handle other request exceptions
        print(f"API request error: {e}")
        api_data = []

    # Store API data into the global dictionary
    for data in api_data: # Iterate over the data from the API
        peopleCard = data.get('peopleCard') # Gets card ID of the person
        cardNum = peopleCard.lstrip('0') # Removes leading zeros from the card ID
        day = data.get('addTime').split(' ')[0] # Gets the date from the 'addTime' field
        if day not in weight_data: # If the date is not in the dictionary, add it
            weight_data[day] = {}
        if cardNum not in weight_data[day]: # If the card ID is not in the weights dictionary, add it
            weight_data[day][cardNum] = {
                'weights': []
            }
        cardInt = int(cardNum)
        if cardInt not in member_info: # If the card ID is not in the member info dictionary, add it
            member_info[cardInt] = {
                'peopleName': data.get('peopleName'),
                'house': data.get('house'),
                'yeargroup': data.get('yeargroup'),
                'formclass': data.get('formclass'),
                'balance': data.get('balance')
            }
        weight_data[day][cardNum]['weights'].append(data['weight']) # Add the weight to the dictionary

    return weight_data, member_info

def ALTgetWeightsbyDate(startDate, endDate): # Get weights from local JSON file
    weight_data = {} # Initialize dictionary to store weight data
    member_info = {}

    startDateForm = startDate.strftime('%Y-%m-%d') # Convert the date objects to strings
    endDateForm = endDate.strftime('%Y-%m-%d')

    try:
        with open('1106data.json', 'r') as file:
            api_data = json.load(file) # Load data from the JSON file
    except json.JSONDecodeError: # Handle JSON decoding errors
        print(f"Error: Unable to decode JSON data from file.")
        api_data = []
    except FileNotFoundError: # Handle file not found error
        print(f"Error: File '1106data.json' not found.")
        api_data = []
    except Exception as e: # Handle other exceptions
        print(f"Error: {e}")
        api_data = []

    # Store API data into the global dictionary
    for data in api_data: # Iterate over the data from the JSON file
        peopleCard = data.get('peopleCard') # Gets card ID of the person
        cardNum = peopleCard.lstrip('0') # Removes leading zeros from the card ID
        day = data.get('addTime').split(' ')[0] # Gets the date from the 'addTime' field
        if day not in weight_data: # If the date is not in the dictionary, add it
            weight_data[day] = {}
        if cardNum not in weight_data[day]: # If the card ID is not in the weights dictionary, add it
            weight_data[day][cardNum] = {
                'weights': []
            }
        cardInt = int(cardNum)
        if cardInt not in member_info: # If the card ID is not in the member info dictionary, add it
            member_info[cardInt] = {
                'peopleName': data.get('peopleName'),
                'house': data.get('house'),
                'yeargroup': data.get('yeargroup'),
                'formclass': data.get('formclass'),
                'balance': data.get('balance')
            }
        weight_data[day][cardNum]['weights'].append(data['weight']) # Add the weight to the dictionary

    return weight_data, member_info

def getStation(station_data, filename):

    file_path = os.path.join(directory, f'{prefix}{filename}.xlsx')
    excel_file = pd.read_excel(file_path, sheet_name=None)  # Read the Excel file
    if filename not in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']: 
        station_data[filename] = list(excel_file.values())[0]  # Store the DataFrame in the dictionary
    else:
        for sheet_name, sheet_data in excel_file.items():
            # convert 'Jun 3' to date format
            date_object = datetime.strptime(sheet_name, '%b %d').date()
            # set the year
            new_date_object = date_object.replace(year=2024)
            new_sheet_name = new_date_object.strftime('%Y-%m-%d')
            
            station_data[new_sheet_name] = sheet_data  # Store the DataFrame in the dictionary
    return station_data

def getAllStations():
    station_data = {}

    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(".xlsx"):
            station_data = getStation(station_data, filename.replace('.xlsx', '').replace('餐线消费数据-', ''))
    return station_data

def report():

    station_data = getAllStations() # puts station data in dict
    #station_data = {}

    initDate = datetime.strptime("2024-05-13", '%Y-%m-%d')
    currentDate = datetime.today()
    weight_data, member_info = getWeightsbyDate(initDate, currentDate) # puts weights in dict

    '''if not station_data:
        print("No station data found for the given date range.")
        return'''
    if not weight_data:
        print("No weight data found for the given date range.")
        return

    #print(f"Station Data: {station_data}")
    #print(f"Weight Data: {weight_data}")

    all_data = merge_data(station_data, weight_data, member_info, initDate, currentDate)

    return all_data

def merge_data(station_data, weight_data, member_info, startDate, endDate):
    global dataFilename
    all_data = {} # Initializing dict to store merged data

    currentDate = startDate
    while currentDate <= endDate: # Iterate over the dates in between
        day = currentDate.strftime('%Y-%m-%d')  # Convert the date obj back to a string
  
        if day in station_data: # Station data present for that day
            df = station_data[day]
            member_id = df['卡号']  # Get list of IDs on each day
            pos_name = df['POS机名称']  # Get list of POS names on each day

            for i, stu_id in enumerate(member_id):
                
                stu_id = int(stu_id)

                if stu_id not in all_data: # Initializes ID key if it doesn't exist
                    all_data[stu_id] = {}
                if day not in all_data[stu_id]: # Then initializes day key for that ID if it doesn't exist
                    all_data[stu_id][day] = {'stations': [], 'weights': []}

                all_data[stu_id][day]['stations'].append(pos_name[i]) # Adds station name data to the dictionary
        
        # Process weight_data for the current day
        if day in weight_data: # Weight data present for that day
            for stu_id, weight_info in weight_data[day].items():
                stu_id = int(stu_id)
                if stu_id not in all_data: # Initializes ID key if it doesn't exist
                    all_data[stu_id] = {}
                if day not in all_data[stu_id]: # Then initializes day key for that ID if it doesn't exist
                    all_data[stu_id][day] = {'stations': [], 'weights': []}

                for weight in weight_info['weights']: # Adds weight data to the dictionary
                    all_data[stu_id][day]['weights'].append(weight)
                if 'name' not in all_data[stu_id]: # If member info not already in the dictionary
                    all_data[stu_id]['name'] = member_info[stu_id]['peopleName'] # Adds member info to the dictionary
                    all_data[stu_id]['house'] = member_info[stu_id]['house']
                    all_data[stu_id]['yeargroup'] = member_info[stu_id]['yeargroup']
                    all_data[stu_id]['formclass'] = member_info[stu_id]['formclass']
                    all_data[stu_id]['balance'] = member_info[stu_id]['balance']

        currentDate += timedelta(days=1)  # Move to the next day
    
    # Save the dictionary to a JSON file
    with open(dataFilename, 'w') as f:
        json.dump(all_data, f, default=set_default)

    return all_data

def categorize_data(all_data):
    categories = {
        'weights_no_counters': 0,
        'counters_no_weights': 0,
        'both': 0,
        'multiple_weights_no_counters': 0,
        'multiple_counters_no_weights': 0,
        'multiple_both': 0
    }

    both_counter_weights = {}

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass' or day == 'balance': # Skip non-day data
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
                if day in both_counter_weights:
                    both_counter_weights[day] += 1
                else:
                    both_counter_weights[day] = 1

    return categories, both_counter_weights

def calculate_totals_and_daily_average_wastage(all_data, startDate, endDate):
    counter_wastage = {}
    counter_tally = {}
    counter_purchases = {}
    daily_counter_wastage = {}
    counter_totals = {}
    counter_counts = {}

    for member, member_data in all_data.items(): # Iterate over the members in the data
        for day, day_data in member_data.items(): # Iterate over the days for each member
            if day in ['name', 'house', 'yeargroup', 'formclass', 'balance']:  # Skip non-day data
                continue

            day_date = datetime.strptime(day, "%Y-%m-%d").date() # Convert the date string to a date object
            if day_date < startDate or day_date > endDate:  # Skip days outside the date range
                continue

            has_weights = 'weights' in day_data and day_data['weights'] # Check if the day data has weights and counters
            has_counters = 'stations' in day_data and day_data['stations'] 

            if has_weights and has_counters:
                total_weight = sum(day_data['weights']) # Calculate the total wastage for the user on that day
                weight_per_counter = total_weight / len(day_data['stations']) # Find average weight per counter, distributed evenly

                for counter in day_data['stations']: # Iterate over the counters for the day
                    if counter not in counter_wastage: # Initialize counter key in all the dictionaries if not present
                        counter_wastage[counter] = 0
                        counter_tally[counter] = 0
                        counter_purchases[counter] = {}
                        counter_totals[counter] = {}
                        counter_counts[counter] = {}

                    if day not in counter_purchases[counter]: # Then initialize day key in the nested dictionaries if not present
                        counter_purchases[counter][day] = 0
                        counter_totals[counter][day] = 0
                        counter_counts[counter][day] = 0

                    counter_wastage[counter] += weight_per_counter # Update data for all the dictionaries
                    counter_tally[counter] += 1
                    counter_purchases[counter][day] += 1
                    counter_totals[counter][day] += weight_per_counter
                    counter_counts[counter][day] += 1

    average_wastage = {counter: total_wastage / counter_tally[counter] for counter, total_wastage in counter_wastage.items()} # Calculate average wastage for each counter

    for counter, days in counter_totals.items(): # Calculate average wastage for each counter for each day
        for day, total in days.items():
            if counter not in daily_counter_wastage: # Initialize counter key in the daily wastage dictionary if not present
                daily_counter_wastage[counter] = {}
            daily_counter_wastage[counter][day] = total / counter_counts[counter][day]

    return average_wastage, counter_wastage, counter_tally, counter_purchases, daily_counter_wastage

def get_last_date():
    all_data = load_data()
    last_date = datetime.strptime('2024-01-01', '%Y-%m-%d')
    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass', 'balance']:
                continue
            day_date = datetime.strptime(day, "%Y-%m-%d")
            if day_date > last_date:
                last_date = day_date
    return last_date

def cumulative_plot_waste(all_data, ax, startDate, endDate):
    # Generate cumulative data for plotting
    daily_counter_wastage = {}
    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass', 'balance']:
                continue
            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < startDate or day_date > endDate:
                continue
            has_weights = 'weights' in day_data and day_data['weights']
            has_counters = 'stations' in day_data and day_data['stations']
            if has_weights and has_counters:
                total_weight = sum(day_data['weights'])
                for counter in day_data['stations']:
                    if counter not in daily_counter_wastage:
                        daily_counter_wastage[counter] = {}
                    if day not in daily_counter_wastage[counter]:
                        daily_counter_wastage[counter][day] = 0
                    daily_counter_wastage[counter][day] += total_weight

    cumulative_counter_wastage = {}
    for counter, daily_wastage in daily_counter_wastage.items():
        cumulative_counter_wastage[counter] = {}
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        cumulative_total = 0
        for date in sorted_dates:
            cumulative_total += daily_wastage[date]
            cumulative_counter_wastage[counter][date] = cumulative_total

    for counter, daily_wastage in cumulative_counter_wastage.items():
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_wastages = [daily_wastage[date] for date in sorted_dates]
        sns.lineplot(x=sorted_dates, y=sorted_wastages, ax=ax, label=counter)

    ax.set_title('Cumulative Food Waste Over Time', fontsize=16, color="white")
    ax.set_xlabel('Date', fontsize=12, color="white")
    ax.set_ylabel('Total Wastage (grams)', fontsize=12, color="white")
    ax.legend(loc='upper left', fontsize=10)

def cumulative_plot_buys(counter_purchases, ax):
    cumulative_counter_purchases = {}
    for counter, daily_purchases in counter_purchases.items():
        cumulative_counter_purchases[counter] = {}
        sorted_dates = sorted(daily_purchases.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        cumulative_total = 0
        for date in sorted_dates:
            cumulative_total += daily_purchases[date]
            cumulative_counter_purchases[counter][date] = cumulative_total

    for counter, daily_purchases in cumulative_counter_purchases.items():
        sorted_dates = sorted(daily_purchases.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_purchases = [daily_purchases[date] for date in sorted_dates]
        sns.lineplot(x=sorted_dates, y=sorted_purchases, ax=ax, label=counter)

    ax.set_title('Cumulative Purchases Over Time', fontsize=16, color="white")
    ax.set_xlabel('Date', fontsize=12, color="white")
    ax.set_ylabel('Total Buys', fontsize=12, color="white")
    ax.legend(loc='upper left', fontsize=10)

def plot_counter_averages(daily_counter_wastage, ax):
    averages = []
    counters = []
    for counter, daily_wastage in daily_counter_wastage.items():
        total_wastage = sum(daily_wastage.values())
        num_days = len(daily_wastage)
        average_wastage = total_wastage / num_days if num_days else 0
        averages.append(average_wastage)
        counters.append(counter)

    data = pd.DataFrame({'counter': counters, 'average_wastage': averages})
    sns.barplot(x='counter', y='average_wastage', data=data, ax=ax, palette="YlOrRd")

    ax.set_title('Counter Averages Over Time', fontsize=16, color="white")
    ax.set_xlabel('Counter', fontsize=12, color="white")
    ax.set_ylabel('Average Wastage (grams)', fontsize=12, color="white")

def spec_plot_weights(all_data, ax, ospec, start_date, end_date, cumulative, year_groups = []):
    house_colors = {
        'Owens': '#FFA500',      # Bright Orange
        'Soong': '#FF0000',      # Bright Red
        'Alleyn': '#9B30FF',     # Bright Purple
        'Johnson': '#1E90FF',    # Bright Blue
        'Wodehouse': '#32CD32'   # Lime Green
    }
    
    # Define primary colors for non-house categories
    primary_colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A5', '#FFC300', '#33FFF9', '#C70039', '#900C3F', '#581845', '#2ECC71']

    spec_wastage = {}
    member_count = {}  # To count members contributing to each day's average

    # Prepare data by member specification
    for member, member_data in all_data.items():
        if ospec == 'staff':
            member_spec = 'Student' if member_data.get('yeargroup', '') != '' else 'Staff'
        else:
            member_spec = member_data.get(ospec)
        
        if not member_spec:
            continue
        if ospec == 'formclass' and member_data.get('yeargroup') not in year_groups:
            continue
        if member_spec not in spec_wastage:
            spec_wastage[member_spec] = {}
            member_count[member_spec] = {}

        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass', 'balance']:
                continue
            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < start_date or day_date > end_date:
                continue
            has_weights = 'weights' in day_data and day_data['weights']
            if has_weights:
                total_weight = sum(day_data['weights'])
                if day not in spec_wastage[member_spec]:
                    spec_wastage[member_spec][day] = 0
                    member_count[member_spec][day] = 0
                spec_wastage[member_spec][day] += total_weight
                member_count[member_spec][day] += 1

    # Extract all dates within the range that have data
    all_dates = sorted({date for spec_data in spec_wastage.values() for date in spec_data})

    # Debugging output to check for collected data
    #print(f"Dates for plotting: {all_dates}")
    #print(f"Collected spec_wastage: {spec_wastage}")

    # Ensure all_dates has at least one date, or return early if empty
    if not all_dates:
        print(f"No data available for the specified date range ({start_date} to {end_date}).")
        return

    # Calculate and plot cumulative or daily average values based on the `cumulative` flag
    color_index = 0  # To alternate colors for non-house specs
    for spec, daily_wastage in spec_wastage.items():
        cumulative_spec_wastage = {}
        cumulative_total = 0
        averaged_daily_wastage = []

        if cumulative:
            # Compute cumulative wastage
            for date in all_dates:
                daily_wastage.setdefault(date, 0)
                cumulative_total += daily_wastage[date]
                cumulative_spec_wastage[date] = cumulative_total
            sorted_wastage = [cumulative_spec_wastage[date] for date in all_dates]
        else:
            # Compute daily average wastage per member
            for date in all_dates:
                if date in daily_wastage and member_count[spec].get(date, 0) > 0:
                    avg_wastage = daily_wastage[date] / member_count[spec][date]
                else:
                    avg_wastage = 0
                averaged_daily_wastage.append(avg_wastage)
            sorted_wastage = averaged_daily_wastage

        # Debugging output for calculated wastage
        #print(f"Spec: {spec}, Wastage Values: {sorted_wastage}")

        # Choose color based on ospec
        if ospec == 'house' and spec in house_colors:
            color = house_colors[spec]
        else:
            color = primary_colors[color_index % len(primary_colors)]
            color_index += 1

        # Plot
        sns.lineplot(x=all_dates, y=sorted_wastage, ax=ax, label=spec, color=color)

    # Set labels and legend
    title_type = "Cumulative" if cumulative else "Daily Average Per Member"
    ax.set_title(f'{title_type} Wastage Over Time by {ospec}', fontsize=16, color="white")
    ax.set_xlabel('Date', fontsize=12, color="white")
    ax.set_ylabel('Wastage (grams)', fontsize=12, color="white")

    # Apply consistent legend styling
    handles, labels = ax.get_legend_handles_labels()
    if handles and labels:
        if ospec == "yeargroup":
            sorted_legend = sorted(zip(labels, handles), key=lambda x: int(x[0]))
            labels, handles = zip(*sorted_legend)
        legend = ax.legend(handles, labels, loc='upper left', fontsize=14, frameon=True, facecolor='#333333', edgecolor='white')
        legend.set_title("Legend", prop={'size': 16, 'weight': 'bold'})
        legend.get_title().set_color("white")
        for text in legend.get_texts():
            text.set_color("white")

def plot_daily_average_wastage(all_data, ax, ospec, start_date, end_date, year_groups = []):
    house_colors = {
        'Owens': '#FFA500',      # Bright Orange
        'Soong': '#FF0000',      # Bright Red for Soong
        'Alleyn': '#9B30FF',     # Brightened Purple for Alleyn
        'Johnson': '#1E90FF',    # Bright Blue
        'Wodehouse': '#32CD32'   # Lime Green
    }
    
    # Define primary colors for non-house categories
    primary_colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A5', '#FFC300', '#33FFF9', '#FF5733', 
                      '#C70039', '#900C3F', '#581845', '#FFD700', '#8A2BE2', '#7FFF00', '#D2691E', 
                      '#FF7F50', '#6495ED', '#DC143C', '#00FFFF']
    
    daily_wastage = defaultdict(lambda: defaultdict(float))
    daily_items = defaultdict(lambda: defaultdict(int))

    # Prepare data by member specification
    for member, member_data in all_data.items():
        if ospec == 'staff':
            email = member_data.get('balance', '')
            if not email:
                continue
            if email.endswith('@stu.dulwich.org'):
                member_spec = 'Student'
            else: #email.endswith('@dulwich.org'):
                member_spec = 'Staff'
            
        else:
            member_spec = member_data.get(ospec)
        
        if not member_spec:
            continue
        
        if ospec == 'formclass' and member_data.get('yeargroup') not in year_groups:
            continue

        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass', 'balance']:
                continue
            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < start_date or day_date > end_date:
                continue
            
            has_weights = 'weights' in day_data and day_data['weights']
            if has_weights:
                total_weight = sum(day_data['weights'])
                daily_wastage[day_date][member_spec] += total_weight

            # Count the number of items purchased by all members in the category
            if 'stations' in day_data:
                daily_items[day_date][member_spec] += len(day_data['stations'])

    staff_nums = {'2024-11-19': 337, '2024-11-20': 339}
    # Calculate daily average wastage per item
    daily_avg_wastage = defaultdict(dict)
    for day_date in daily_wastage:
        for spec in daily_wastage[day_date]:
            if spec == 'Staff': 
                date_string = day_date.strftime('%Y-%m-%d')
                daily_items[day_date][spec] = staff_nums.get(date_string, 0)
            if daily_items[day_date][spec] > 0:
                daily_avg_wastage[day_date][spec] = daily_wastage[day_date][spec] / daily_items[day_date][spec]
            else:
                daily_avg_wastage[day_date][spec] = 0

            # Print the number of data points considered for each bar
            print(f"Date: {day_date}, Category: {spec}, Total Weight: {daily_wastage[day_date][spec]}, Total Items: {daily_items[day_date][spec]}")

    # Prepare data for plotting
    plot_data = []
    for day_date in sorted(daily_avg_wastage):
        for spec in daily_avg_wastage[day_date]:
            plot_data.append({
                'Date': day_date,
                'Category': spec,
                'Average Wastage': daily_avg_wastage[day_date][spec]
            })

    # Convert to DataFrame for seaborn
    plot_df = pd.DataFrame(plot_data)

    # Ensure there is data to plot
    if plot_df.empty:
        print(f"No data to plot for {ospec} in the specified date range.")
        return  # Exit the function if there is no data

    # Choose colors based on ospec
    if 'Category' in plot_df.columns:
        if ospec == 'house':
            palette = [house_colors.get(spec, "#4B0082") for spec in plot_df['Category'].unique()]  # Default to indigo if color not in house_colors
        else:
            palette = primary_colors[:len(plot_df['Category'].unique())]  # Use primary colors if not 'house'
    else:
        palette = primary_colors[:len(plot_df)]  # Use primary colors if no category

    # Plotting
    bars = sns.barplot(x='Date', y='Average Wastage', hue='Category' if 'Category' in plot_df.columns else None, data=plot_df, ax=ax, palette=palette, ci=None)
    ax.set_title(f'Daily Average Wastage per Item by {ospec}', fontsize=16, color="white")
    ax.set_xlabel('Date', fontsize=12, color="white")
    ax.set_ylabel('Average Wastage per Item (grams)', fontsize=12, color="white")

    # Remove bar borders by setting edge color to face color
    for bar in bars.patches:
        bar.set_edgecolor(bar.get_facecolor())

    # Add text annotations above the bars
    for bar in bars.patches:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', 
                    xy=(bar.get_x() + bar.get_width() / 2, height), 
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points", 
                    ha='center', 
                    color='white', 
                    fontsize=10)

    # Adjust colors and styling for readability
    ax.tick_params(axis='x', colors='white', labelsize=12, rotation=45)
    ax.tick_params(axis='y', colors='white', labelsize=12)
    for spine in ax.spines.values():
        spine.set_edgecolor('white')
    ax.yaxis.label.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.title.set_color('white')

    print(f"Plot for {ospec} from {start_date} to {end_date} is done.")
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def rank_counters(average_wastage, total_wastage, counter_days): # Prints ranks of counters
    average_wastage_ranked = sorted(average_wastage.items(), key=lambda item: item[1], reverse=True)
    total_wastage_ranked = sorted(total_wastage.items(), key=lambda item: item[1], reverse=True)
    counter_days_ranked = sorted(counter_days.items(), key=lambda item: item[1], reverse=True)

    print("Average Wastage Ranking:")
    for counter, wastage in average_wastage_ranked:
        print(f"{counter}: {wastage} grams")

    print("\nTotal Wastage Ranking:")
    for counter, wastage in total_wastage_ranked:
        print(f"{counter}: {wastage} grams")

    print("\nCounter Buys Ranking:")
    for counter, days in counter_days_ranked:
        print(f"{counter}: {days} buys")

def analyze_data(all_data, startDate, endDate):
    average_wastage, total_wastage, counter_tally, counter_purchases, daily_average_wastage = calculate_totals_and_daily_average_wastage(all_data, startDate, endDate)
    #rank_counters(average_wastage, total_wastage, counter_tally)
    metadata = [all_data, average_wastage, total_wastage, counter_tally, counter_purchases, daily_average_wastage] # Store all metadata in a list
    return metadata



def plot(startDate, endDate, plots, metadata, continuous, filename, year_groups = None): # plots and metadata are lists
    plt.close('all')  # Close all existing figures

    # Create a 1x3 grid of subplots. The returned object is a Figure instance (f) and an array of Axes objects (ax1, ax2, ax3)
    f, axes = plt.subplots(1, len(plots), figsize=(18, 6))
    if not isinstance(axes, collections.abc.Iterable):
        axes = [axes]

    for i, ax in enumerate(axes):
        if plots[i] == 'counters':
            cumulative_plot_waste(metadata[0], ax, startDate, endDate) # all_data
        elif plots[i] == 'buys':
            cumulative_plot_buys(metadata[4], ax) # counter_purchases, date limited
        elif plots[i] == 'counter_avg':
            plot_counter_averages(metadata[5], ax) # daily_average_wastage, date limited
        elif plots[i] == 'formclass':
            spec_plot_weights(metadata[0], ax, plots[i], startDate, endDate, True, year_groups) # all_data
        else:
            spec_plot_weights(metadata[0], ax, plots[i], startDate, endDate, True) # all_data

    # Ensure the 'plots' folder exists
    os.makedirs('plots', exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')

    filepath = f'plots/plot_{filename}.png'
    plt.savefig(filepath)

    plt.show()

def plot_fullscreen(startDate, endDate, plots, metadata, line, cumulative, year_groups):
    plt.close('all')  # Close all existing figures
    
    # Ensure the 'full_plots' folder exists
    os.makedirs('full_plots', exist_ok=True)

    for plot_type in plots:
        # Create a fullscreen 16:9 plot with enhanced styling
        fig, ax = plt.subplots(figsize=(16, 9))
        plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.18)  # Increased bottom padding
        
        x_label = "Date"
        y_label = "Value"
        
        # Generate the plot based on the type by passing the ax and data to the specific functions
        if plot_type == 'counters':
            cumulative_plot_waste(metadata[0], ax, startDate, endDate)
            x_label = "Date"
            y_label = "Food Wastage (grams)"
        elif plot_type == 'buys':
            cumulative_plot_buys(metadata[4], ax)
            x_label = "Date"
            y_label = "Buys"
        elif plot_type == 'counter_avg':
            plot_counter_averages(metadata[5], ax)
            x_label = "Station"
            y_label = "Food Wastage (grams)"
        elif plot_type in ['formclass', 'house', 'yeargroup', 'staff']:
            if line:
                spec_plot_weights(metadata[0], ax, plot_type, start_date=startDate, end_date=endDate, cumulative=cumulative, year_groups=year_groups)
                x_label = "Date"
                y_label = "Food Wastage (grams)"
            else:
                plot_daily_average_wastage(metadata[0], ax, plot_type, startDate, endDate)
                x_label = "Date"
                y_label = "Food Wastage (grams)"

            if plot_type == 'yeargroup':
                # Sort the legend for yeargroup numerically and apply consistent styling
                handles, labels = ax.get_legend_handles_labels()
                if labels:  # Check if labels exist
                    sorted_legend = sorted(zip(labels, handles), key=lambda x: int(x[0]))
                    labels, handles = zip(*sorted_legend)
                    legend = ax.legend(handles, labels, loc='upper left', fontsize=14, frameon=True, facecolor='#333333', edgecolor='white')
                    legend.set_title("Legend", prop={'size': 16, 'weight': 'bold'})
                    legend.get_title().set_color("white")
                    for text in legend.get_texts():
                        text.set_color("white")
        else:
            spec_plot_weights(metadata[0], ax, plot_type, startDate, endDate, cumulative)

        if line:
            # Simulate a glow effect by layering lines with increasing opacity
            for line in ax.get_lines():
                line_color = line.get_color()  # Get the color of the primary line
                rgba_color = to_rgba(line_color)

                # Overlay multiple lines with decreasing opacity for glow
                for alpha, lw in zip([0.05, 0.1, 0.2, 0.3], [12, 10, 8, 6]):
                    ax.plot(line.get_xdata(), line.get_ydata(),
                            color=(rgba_color[0], rgba_color[1], rgba_color[2], alpha),
                            linewidth=lw, zorder=-1)

        desc = '' # Over Time
        year = f' (Year {year_groups[0]})' if plot_type == 'formclass' else ''
        if line:   
            if cumulative:
                ax.set_title(f"{plot_type.title()} Cumulative Food Waste {desc}{year}", fontsize=22, color="white", weight='bold', pad=20)
            else:
                ax.set_title(f"{plot_type.title()} Average Food Waste {desc}{year}", fontsize=22, color="white", weight='bold', pad=20)
        else:
            ax.set_title(f"Student vs Staff Average Food Waste {desc}", fontsize=22, color="white", weight='bold', pad=20)
            #ax.set_title(f"{plot_type.title()} Average Food Waste {desc}{year}", fontsize=22, color="white", weight='bold', pad=20)
        ax.set_xlabel(x_label, fontsize=18, color="white", labelpad=15)
        ax.set_ylabel(y_label, fontsize=18, color="white", labelpad=15)
        
        # Customize tick colors and font sizes to fit the theme
        ax.tick_params(axis='x', colors='white', rotation=45, labelsize=14)
        ax.tick_params(axis='y', colors='white', labelsize=14)

        # Customize legend for larger size and white text if not already done
        if plot_type != 'yeargroup' and ax.get_legend():
            legend = ax.legend(loc='upper left', fontsize=14, frameon=True, facecolor='#333333', edgecolor='white')
            legend.set_title("Legend", prop={'size': 16, 'weight': 'bold'})
            legend.get_title().set_color("white")
            for text in legend.get_texts():
                text.set_color("white")
        
        # Save each plot individually with the plot type name
        filename = f'full_plots/{plot_type}{year_groups[0] if plot_type == 'formclass' else ''}_{"line" if line else "bar"}_{"cumulative" if cumulative and line else "average"}.png'
        plt.savefig(filename, dpi=300)  # High resolution for display quality
        plt.close(fig)  # Close figure to free up memory

    print("All plots have been saved in the 'full_plots' folder.")

def test(startDateStr, endDateStr):
    #current_date = getDate()
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()
    #all_data = report()
    all_data = load_data() # Load data from JSON file
    
    categories, both_counter_weights = categorize_data(all_data)
    for category, count in categories.items():
        print(f"{category}: {count} days")

    print("\nNumber of both counters and weights occurring on each day:")
    sorted_days = sorted(both_counter_weights.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
    for day in sorted_days:
        print(f"{day}: {both_counter_weights[day]} occurrences")

    print("\n")
    

    metadata = analyze_data(all_data, startDate, endDate)
    run = 2
    ''']
    # STUDENT SIDE
    plots = ['counters', 'yeargroup', 'house']
    plot(startDate, endDate, plots, metadata, True, f"stu_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"stu_discrete{run}")
    # SODEXO SIDE
    plots = ['counters', 'buys', 'counter_avg']
    plot(startDate, endDate, plots, metadata, True, f"sod_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"sod_discrete{run}")
    '''

    plots = ['counters', 'yeargroup', 'house', 'formclass', 'buys', 'counter_avg']
    #plots = ['staff']
    year_groups = ['9', '10', '11', '12', '13']

    plot_fullscreen(startDate, endDate, plots, metadata, True, True, year_groups) # Line? Cumulative? 
    plot_fullscreen(startDate, endDate, plots, metadata, True, False, year_groups)
    plot_fullscreen(startDate, endDate, plots, metadata, False, False, year_groups)

    '''plots = ['formclass']
    
    for year_group in year_groups:
        year_list = [year_group]
        plot_fullscreen(startDate, endDate, plots, metadata, True, False, year_list)
        plot_fullscreen(startDate, endDate, plots, metadata, True, True, year_list)
        plot_fullscreen(startDate, endDate, plots, metadata, False, False, year_list)
    '''

if __name__ == "__main__":
    
    test("2024-11-10", "2024-11-20")
    #getWeightsbyDate(datetime.strptime("2024-05-13", '%Y-%m-%d'), datetime.strptime("2024-05-15", '%Y-%m-%d'))
    #print(weight_data)