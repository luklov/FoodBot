import pandas as pd
import requests
import collections

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

directory = 'data'
prefix = '餐线消费数据-'

dataFilename = 'merged_data.json' #merged_data.json

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

def convert_cnt_id(conversion_dict, cnt_id): # short ID to long ID
    cnt_id = str(cnt_id) # int to string
    api_id = conversion_dict.get(str(cnt_id), None)

    return api_id

def convert_api_id(reverse_conversion_dict, api_id): # long ID to short ID, REVERSE
    api_id = str(int(api_id)) # float to int to string
    cnt_id = reverse_conversion_dict.get(api_id, None)

    return cnt_id

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

def load_data(file_path = 'combined_data/merged_data.json'):
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
                'formclass': data.get('formclass')
            }
        weight_data[day][cardNum]['weights'].append(data['weight']) # Add the weight to the dictionary

    return weight_data, member_info

def getStation(station_data, filename):

    file_path = os.path.join(directory, f'{prefix}{filename}.xlsx')
    excel_file = pd.read_excel(file_path, sheet_name=None)  # Read the Excel file
    if filename != 'June':
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

def report(startDate, endDate):

    station_data = getAllStations() # puts station data in dict
    weight_data, member_info = getWeightsbyDate(startDate, endDate) # puts weights in dict

    if not station_data: 
        print("No station data found for the given date range.")
        return
    if not weight_data:
        print("No weight data found for the given date range.")
        return

    #print(f"Station Data: {station_data}")
    #print(f"Weight Data: {weight_data}")›
    conversion_dict, reverse_conversion_dict = load_conversion_dicts()
    all_data = merge_data(station_data, weight_data, member_info, conversion_dict, reverse_conversion_dict, startDate, endDate)

    return all_data

def merge_data(station_data, weight_data, member_info, conversion_dict, reverse_conversion_dict, startDate, endDate):
    global dataFilename
    all_data = {} # Initializing dict to store merged data
    statF, weightF = 0, 0 # Counters for IDs found in the conversion table
    statNF, weightNF = 0, 0 # Counters for IDs not found in the conversion table
    memF, memNF = 0, 0 # Counters for members with and without info

    currentDate = startDate
    while currentDate <= endDate: # Iterate over the dates in between
        day = currentDate.strftime('%Y-%m-%d')  # Convert the date obj back to a string
  
        if day in station_data: # Station data present for that day
            df = station_data[day]
            member_id = df['会员编号']  # Get list of IDs on each day
            pos_name = df['POS机名称']  # Get list of POS names on each day

            for i, cnt_id in enumerate(member_id):
                if cnt_id == 'No Match':  # Skip if ID not convertable
                    continue
                api_id = convert_cnt_id(conversion_dict, cnt_id)  # short to long ID
                if not api_id:  # Skip the person if the ID cannot be converted
                    statNF += 1
                    continue
                api_id = int(api_id)
                statF += 1

                if cnt_id not in all_data: # Initializes ID key if it doesn't exist
                    all_data[cnt_id] = {}
                if day not in all_data[cnt_id]: # Then initializes day key for that ID if it doesn't exist
                    all_data[cnt_id][day] = {'stations': [], 'weights': []}

                all_data[cnt_id][day]['stations'].append(pos_name[i]) # Adds station name data to the dictionary
                if 'name' not in all_data[cnt_id]: # If member info not already in the dictionary
                    if api_id not in member_info: # Skip if member info not found
                        memNF += 1
                        continue
                    memF += 1
                    all_data[cnt_id]['name'] = member_info[api_id]['peopleName'] # Adds member info to the dictionary
                    all_data[cnt_id]['house'] = member_info[api_id]['house']
                    all_data[cnt_id]['yeargroup'] = member_info[api_id]['yeargroup']
                    all_data[cnt_id]['formclass'] = member_info[api_id]['formclass']

        # Process weight_data for the current day
        if day in weight_data: # Weight data present for that day
            for api_id, weight_info in weight_data[day].items():
                cnt_id = convert_api_id(reverse_conversion_dict, api_id)
                api_id = int(api_id)
                if not cnt_id:  # Skip the person if the ID cannot be converted
                    weightNF += 1
                    continue
                weightF += 1
                if cnt_id not in all_data: # Initializes ID key if it doesn't exist
                    all_data[cnt_id] = {}
                if day not in all_data[cnt_id]: # Then initializes day key for that ID if it doesn't exist
                    all_data[cnt_id][day] = {'stations': [], 'weights': []}

                for weight in weight_info['weights']: # Adds weight data to the dictionary
                    all_data[cnt_id][day]['weights'].append(weight)
                if 'name' not in all_data[cnt_id]: # If member info not already in the dictionary
                    memF += 1
                    all_data[cnt_id]['name'] = member_info[api_id]['peopleName'] # Adds member info to the dictionary
                    all_data[cnt_id]['house'] = member_info[api_id]['house']
                    all_data[cnt_id]['yeargroup'] = member_info[api_id]['yeargroup']
                    all_data[cnt_id]['formclass'] = member_info[api_id]['formclass']

        currentDate += timedelta(days=1)  # Move to the next day
    print(f"{memF}/{memF + memNF} members have info.")
    print(f"1: Found {statF} IDs and {statNF} IDs were not found in the conversion table.")
    print(f"2: Found {weightF} IDs and {weightNF} IDs were not found in the conversion table.")

    # Save the dictionary to a JSON file
    with open('combined_data/merged_data.json', 'w') as f:
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
            if day in ['name', 'house', 'yeargroup', 'formclass']:  # Skip non-day data
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

def cumulative_plot_waste(all_data, ax, startDate, endDate):
    # Generate cumulative data for plotting
    daily_counter_wastage = {}
    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass']:
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

def cumulative_spec_plot_weights(all_data, ax, ospec, start_date=None, end_date=None, continuous=False, year_groups=None):
    house_colors = {
        'Owens': '#FFA500',      # Bright Orange
        'Soong': '#FF0000',      # Bright Red for Soong
        'Alleyn': '#9B30FF',     # Brightened Purple for Alleyn
        'Johnson': '#1E90FF',    # Bright Blue
        'Wodehouse': '#32CD32'   # Lime Green
    }
    spec_wastage = {}
    for member, member_data in all_data.items():
        member_spec = member_data.get(ospec)
        if not member_spec:
            continue
        if ospec == 'formclass' and member_data.get('yeargroup') not in year_groups:
            continue
        if member_spec not in spec_wastage:
            spec_wastage[member_spec] = {}
        for day, day_data in member_data.items():
            if day in ['name', 'house', 'yeargroup', 'formclass']:
                continue
            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < start_date or day_date > end_date:
                continue
            has_weights = 'weights' in day_data and day_data['weights']
            if has_weights:
                total_weight = sum(day_data['weights'])
                if day not in spec_wastage[member_spec]:
                    spec_wastage[member_spec][day] = 0
                spec_wastage[member_spec][day] += total_weight

    cumulative_spec_wastage = {}
    all_dates = sorted([date for spec_data in spec_wastage.values() for date in spec_data])
    for spec, daily_wastage in spec_wastage.items():
        cumulative_spec_wastage[spec] = {}
        cumulative_total = 0
        for date in all_dates:
            daily_wastage.setdefault(date, 0)
            cumulative_total += daily_wastage[date]
            cumulative_spec_wastage[spec][date] = cumulative_total

        sorted_wastage = [cumulative_spec_wastage[spec][date] for date in all_dates]
        if ospec == 'house' and spec in house_colors:
            sns.lineplot(x=all_dates, y=sorted_wastage, ax=ax, label=spec, color=house_colors[spec])
        else:
            sns.lineplot(x=all_dates, y=sorted_wastage, ax=ax, label=spec)

    ax.set_title(f'Cumulative Wastage Over Time by {ospec}', fontsize=16, color="white")
    ax.set_xlabel('Date', fontsize=12, color="white")
    ax.set_ylabel('Total Wastage (grams)', fontsize=12, color="white")
    ax.legend(loc='upper left', fontsize=10)


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
            cumulative_spec_plot_weights(metadata[0], ax, plots[i], startDate, endDate, continuous, year_groups) # all_data
        else:
            cumulative_spec_plot_weights(metadata[0], ax, plots[i], startDate, endDate, continuous) # all_data

    # Ensure the 'plots' folder exists
    os.makedirs('plots', exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')

    filepath = f'plots/plot_{filename}.png'
    plt.savefig(filepath)

    plt.show()

def plot_fullscreen(startDate, endDate, plots, metadata, continuous, year_groups=None):
    plt.close('all')  # Close all existing figures
    
    # Ensure the 'full_plots' folder exists
    os.makedirs('full_plots', exist_ok=True)

    for plot_type in plots:
        # Create a fullscreen 16:9 plot with enhanced styling
        fig, ax = plt.subplots(figsize=(16, 9))
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
        elif plot_type == 'formclass':
            cumulative_spec_plot_weights(metadata[0], ax, plot_type, startDate, endDate, continuous, year_groups)
            x_label = "Date"
            y_label = "Food Wastage (grams)"
        else:
            cumulative_spec_plot_weights(metadata[0], ax, plot_type, startDate, endDate, continuous)
        
        # Simulate a glow effect by layering lines with increasing opacity
        for line in ax.get_lines():
            line_color = line.get_color()  # Get the color of the primary line
            rgba_color = to_rgba(line_color)

            # Overlay multiple lines with decreasing opacity for glow
            for alpha, lw in zip([0.05, 0.1, 0.2, 0.3], [12, 10, 8, 6]):
                ax.plot(line.get_xdata(), line.get_ydata(),
                        color=(rgba_color[0], rgba_color[1], rgba_color[2], alpha),
                        linewidth=lw, zorder=-1)

        # Title and labels with enhanced styles to match the theme
        ax.set_title(f"{plot_type.title()} Food Waste Over Time", fontsize=18, color="white", weight='bold', pad=20)
        ax.set_xlabel(x_label, fontsize=14, color="white", labelpad=10)
        ax.set_ylabel(y_label, fontsize=14, color="white", labelpad=10)
        
        # Customize tick colors to fit the theme
        ax.tick_params(axis='x', colors='white', rotation=45)
        ax.tick_params(axis='y', colors='white')

        # Customize legend for larger size and white text
        legend = ax.legend(loc='upper left', fontsize=12, frameon=True, facecolor='#333333', edgecolor='white')
        
        # Update legend title separately
        legend.set_title("Legend", prop={'size': 14, 'weight': 'bold'})
        legend.get_title().set_color("white")  # Set title color to white
        
        # Set legend text color to white
        for text in legend.get_texts():
            text.set_color("white")  

        # Save each plot individually with the plot type name
        filename = f'full_plots/{plot_type}.png'
        plt.savefig(filename, bbox_inches='tight', dpi=300)  # High resolution for display quality
        plt.close(fig)  # Close figure to free up memory

    print("All plots have been saved in the 'full_plots' folder.")

def test(startDateStr, endDateStr):
    #current_date = getDate()
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()
    #all_data = report(startDate, endDate) # Start date, end date
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
    '''
    # STUDENT SIDE
    plots = ['counters', 'yeargroup', 'house']
    plot(startDate, endDate, plots, metadata, True, f"stu_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"stu_discrete{run}")
    # SODEXO SIDE
    plots = ['counters', 'buys', 'counter_avg']
    plot(startDate, endDate, plots, metadata, True, f"sod_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"sod_discrete{run}")
    '''

    #plots = ['counters', 'yeargroup', 'house', 'formclass', 'buys', 'counter_avg']
    plots = ['house']
    year_groups = ['12']

    plot_fullscreen(startDate, endDate, plots, metadata, False, year_groups)
if __name__ == "__main__":
    

    test("2024-05-13", "2024-06-19")
    #getWeightsbyDate(datetime.strptime("2024-05-13", '%Y-%m-%d'), datetime.strptime("2024-05-15", '%Y-%m-%d'))
    #print(weight_data)