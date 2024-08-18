import pandas as pd
import requests
import collections

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import json
import os
from datetime import datetime, timedelta

from matplotlib.font_manager import FontProperties

font = FontProperties(fname="/System/Library/Fonts/PingFang.ttc")

directory = 'data'
prefix = '餐线消费数据-'

def make_conversion_dicts():
    # Merge the Excel data and API data based on user ID (peopleCard)
    conversion_table = pd.read_excel('conversion.xls')
    conversion_dict = dict(zip(conversion_table['会员编号'], conversion_table['卡号']))
    reverse_conversion_dict = {v: k for k, v in conversion_dict.items()}
    return conversion_dict, reverse_conversion_dict

def getDate():
    # Return the current date
    return datetime.now().strftime('%Y-%m-%d')

def load_data(file_path = 'combined_data/merged_data.json'):
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return all_data

def getWeightsbyDate(startDate, endDate): # PASS IN WEIGHT DATA + MEMBER INFO
    weight_data = {}
    member_info = {}

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
        if day not in weight_data:
            weight_data[day] = {}
        if cardNum not in weight_data[day]:
            weight_data[day][cardNum] = {
                'peopleName': data.get('peopleName'),
                'house': data.get('house'),
                'yeargroup': data.get('yeargroup'),
                'formclass': data.get('formclass'),
                'weights': []
            }
        cardInt = int(cardNum)
        if cardInt not in member_info:
            member_info[cardInt] = {
                'peopleName': data.get('peopleName'),
                'house': data.get('house'),
                'yeargroup': data.get('yeargroup'),
                'formclass': data.get('formclass')
            }
        weight_data[day][cardNum]['weights'].append(data['weight'])

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
    #print(f"Weight Data: {weight_data}")
    conversion_dict, reverse_conversion_dict = make_conversion_dicts()
    all_data = merge_data(station_data, weight_data, member_info, conversion_dict, reverse_conversion_dict, startDate, endDate)

    return all_data

def merge_data(station_data, weight_data, member_info, conversion_dict, reverse_conversion_dict, startDate, endDate):
    all_data = {}
    found1, found2 = 0, 0
    statCount, weightCount = 0, 0
    counter, goodcount = 0, 0

    # Iterate over the dates in between
    currentDate = startDate
    while currentDate <= endDate:
        day = currentDate.strftime('%Y-%m-%d')  # Convert the date back to a string

        # Process station_data for the current day
        if day in station_data:
            df = station_data[day]
            member_id = df['会员编号']  # Get list of IDs on each day
            pos_name = df['POS机名称']  # Get list of POS names on each day

            for i, cnt_id in enumerate(member_id):
                if cnt_id == 'No Match':  # Skip if ID in June data not convertable
                    continue
                api_id = convert_cnt_id(conversion_dict, cnt_id)  # short to long ID
                if not api_id:  # Skip the person if the ID cannot be converted
                    statCount += 1
                    continue
                api_id = int(api_id)
                found1 += 1

                if cnt_id not in all_data:
                    all_data[cnt_id] = {}
                if day not in all_data[cnt_id]:
                    all_data[cnt_id][day] = {'stations': [], 'weights': []}

                all_data[cnt_id][day]['stations'].append(pos_name[i])
                if 'name' not in all_data[cnt_id]:
                    if api_id not in member_info:
                        counter += 1
                        continue
                    goodcount += 1
                    all_data[cnt_id]['name'] = member_info[api_id]['peopleName']
                    all_data[cnt_id]['house'] = member_info[api_id]['house']
                    all_data[cnt_id]['yeargroup'] = member_info[api_id]['yeargroup']
                    all_data[cnt_id]['formclass'] = member_info[api_id]['formclass']

                # add code to set the name house etc

        # Process weight_data for the current day
        if day in weight_data:
            for api_id, weight_info in weight_data[day].items():
                cnt_id = convert_api_id(reverse_conversion_dict, api_id)
                api_id = int(api_id)
                if not cnt_id:  # Skip the person if the ID cannot be converted
                    weightCount += 1
                    continue
                found2 += 1
                if cnt_id not in all_data:
                    all_data[cnt_id] = {}
                if day not in all_data[cnt_id]:
                    all_data[cnt_id][day] = {'stations': [], 'weights': []}

                for weight in weight_info['weights']:
                    all_data[cnt_id][day]['weights'].append(weight)
                if 'name' not in all_data[cnt_id]:
                    goodcount += 1
                    all_data[cnt_id]['name'] = member_info[api_id]['peopleName']
                    all_data[cnt_id]['house'] = member_info[api_id]['house']
                    all_data[cnt_id]['yeargroup'] = member_info[api_id]['yeargroup']
                    all_data[cnt_id]['formclass'] = member_info[api_id]['formclass']

        currentDate += timedelta(days=1)  # Move to the next day
    print(f"{goodcount}/{goodcount + counter} members have info.")
    print(f"1: Found {found1} IDs and {statCount} IDs were not found in the conversion table.")
    print(f"2: Found {found2} IDs and {weightCount} IDs were not found in the conversion table.")

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

def calculate_totals(all_data, startDate, endDate): # change to fit dates
    counter_wastage = {}
    counter_tally = {}
    counter_purchases = {}

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue

            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < startDate or day_date > endDate:  # Skip days outside the date range
                continue

            has_weights = 'weights' in day_data and day_data['weights']
            has_counters = 'stations' in day_data and day_data['stations']

            if has_weights and has_counters:
                total_weight = sum(day_data['weights'])
                weight_per_counter = total_weight / len(day_data['stations'])

                for counter in day_data['stations']:
                    if counter not in counter_wastage:
                        counter_wastage[counter] = 0
                        counter_tally[counter] = 0
                        counter_purchases[counter] = {}
                    if day not in counter_purchases[counter]:
                        counter_purchases[counter][day] = 0
                    counter_wastage[counter] += weight_per_counter
                    counter_tally[counter] += 1
                    counter_purchases[counter][day] += 1

    average_wastage = {counter: total_wastage / counter_tally[counter] for counter, total_wastage in counter_wastage.items()}

    return average_wastage, counter_wastage, counter_tally, counter_purchases

def calculate_daily_average_wastage(all_data, startDate, endDate):
    daily_counter_wastage = {}

    counter_totals = {}
    counter_counts = {}

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue

            day_date = datetime.strptime(day, "%Y-%m-%d").date() # Convert string to a date object
            if day_date < startDate or day_date > endDate:  # Skip days outside the date range
                continue

            has_weights = 'weights' in day_data and day_data['weights']
            has_counters = 'stations' in day_data and day_data['stations']

            if has_weights and has_counters:
                total_weight = sum(day_data['weights'])
                weight_per_counter = total_weight / len(day_data['stations'])

                for counter in day_data['stations']:
                    if counter not in counter_totals:
                        counter_totals[counter] = {}
                        counter_counts[counter] = {}
                    if day not in counter_totals[counter]:
                        counter_totals[counter][day] = 0
                        counter_counts[counter][day] = 0
                    counter_totals[counter][day] += weight_per_counter
                    counter_counts[counter][day] += 1

    for counter, days in counter_totals.items():
        for day, total in days.items():
            if counter not in daily_counter_wastage:
                daily_counter_wastage[counter] = {}
            daily_counter_wastage[counter][day] = total / counter_counts[counter][day]
    return daily_counter_wastage

def plot_counter_averages(daily_counter_wastage, ax):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']  # Extended list of colors for the plot lines
    for i, (counter, daily_wastage) in enumerate(daily_counter_wastage.items()):
        # Sort the dates
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_wastages = [daily_wastage[date] for date in sorted_dates]
        color = colors[i % len(colors)]  # Choose a color from the list
        ax.plot(sorted_dates, sorted_wastages, '-', label=counter, color=color)

        # Calculate the net average wastage
        total_wastage = sum(sorted_wastages)
        num_days = len(sorted_wastages)
        average_wastage = total_wastage / num_days if num_days else 0

        # Plot the average wastage as a horizontal line
        ax.axhline(average_wastage, color=color, linestyle='--', alpha=1)

    plt.gcf().autofmt_xdate()
    ax.set_title('Counter Averages Over Time')  # Add a title
    ax.set_xlabel('Date')  # Add x-axis label
    ax.set_ylabel('Average Wastage (grams)')  # Add y-axis label
    ax.legend(prop = font)

def cumulative_plot_waste(all_data, ax, startDate, endDate):
    daily_counter_wastage = {}

    for member, member_data in all_data.items():
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue

            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < startDate or day_date > endDate:  # Skip days outside the date range
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

    # Create a new dictionary to hold the cumulative wastage data
    cumulative_counter_wastage = {}

    for counter, daily_wastage in daily_counter_wastage.items():
        cumulative_counter_wastage[counter] = {}
        # Sort the dates
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        # Initialize the cumulative total
        cumulative_total = 0
        for date in sorted_dates:
            # Add the wastage for the current day to the cumulative total
            cumulative_total += daily_wastage[date]
            # Store the cumulative total for the current day
            cumulative_counter_wastage[counter][date] = cumulative_total

    for counter, daily_wastage in cumulative_counter_wastage.items():
        # Sort the dates
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_wastages = [daily_wastage[date] for date in sorted_dates]
        # Plot the data
        ax.plot(sorted_dates, sorted_wastages, '-', label=counter)
    
    plt.gcf().autofmt_xdate()  # Optional: for better formatting of date labels
    ax.set_title('Cumulative Food Waste Over Time')  # Add a title
    ax.set_xlabel('Date')  # Add x-axis label
    ax.set_ylabel('Total Wastage (grams)')  # Add y-axis label
    ax.legend(prop=font)

    return daily_counter_wastage

def cumulative_spec_plot_weights(all_data, ax, ospec, start_date=None, end_date=None, continuous=False, year_groups=None):
    # Define the color mapping for houses
    house_colors = {'Owens': 'orange', 'Soong': 'red', 'Alleyn': 'purple', 'Johnson': 'blue', 'Wodehouse': 'green'}

    if continuous:
        # Create a list of all dates in the range
        all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        all_dates = [date.strftime('%Y-%m-%d') for date in all_dates]  # Convert dates back to strings

    spec_wastage = {}
    noncount = 0
    for member, member_data in all_data.items():
        member_spec = member_data.get(ospec)
        if not member_spec: # Skip members without the specified attribute
            noncount += 1
            continue
        if ospec == 'formclass' and member_data.get('yeargroup') not in year_groups: # Skip members not in the specified year groups
            continue

        if member_spec not in spec_wastage:
            spec_wastage[member_spec] = {}
        for day, day_data in member_data.items():
            if day == 'name' or day == 'house' or day == 'yeargroup' or day == 'formclass': # Skip non-day data
                continue

            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            if day_date < start_date or day_date > end_date:  # Skip days outside the date range
                continue

            has_weights = 'weights' in day_data and day_data['weights']

            if has_weights:
                total_weight = sum(day_data['weights'])
                if day not in spec_wastage[member_spec]:
                    spec_wastage[member_spec][day] = 0
                spec_wastage[member_spec][day] += total_weight 

    print(f"Skipped {noncount} members without a {ospec}.")            
    cumulative_spec_wastage = {}

    for spec, daily_wastage in spec_wastage.items():
        cumulative_spec_wastage[spec] = {}  # Initialize the dictionary for the spec
        if continuous:
            # Fill in missing dates with a wastage of 0
            for date in all_dates:
                if date not in daily_wastage:
                    daily_wastage[date] = 0

        # Sort the dates
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        # Initialize the cumulative total
        cumulative_total = 0
        for date in sorted_dates:
            # Add the wastage for the current day to the cumulative total
            cumulative_total += daily_wastage[date]
            # Store the cumulative total for the current day
            cumulative_spec_wastage[spec][date] = cumulative_total

    for spec, daily_wastage in cumulative_spec_wastage.items():
        # Sort the dates
        sorted_dates = sorted(daily_wastage.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_wastage = [daily_wastage[date] for date in sorted_dates]
        # Plot the data
        if ospec == 'house' and spec in house_colors:  # If the spec is 'house' and the house name is in the color mapping
            ax.plot(sorted_dates, sorted_wastage, '-', label=spec, color=house_colors[spec])  # Use the corresponding color
        else:
            ax.plot(sorted_dates, sorted_wastage, '-', label=spec)  # Use the default color

    plt.gcf().autofmt_xdate()  # Optional: for better formatting of date labels
    ax.set_title(f'Cumulative Wastage Over Time by {ospec}')  # Add a title
    ax.set_xlabel('Date')  # Add x-axis label
    ax.set_ylabel('Total Wastage (grams)')  # Add y-axis label
    ax.legend(prop=font)

def cumulative_plot_buys(counter_purchases, ax):
    cumulative_counter_purchases = {}

    for counter, daily_purchases in counter_purchases.items():
        cumulative_counter_purchases[counter] = {}
        # Sort the dates
        sorted_dates = sorted(daily_purchases.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        # Initialize the cumulative total
        cumulative_total = 0
        for date in sorted_dates:
            # Add the purchases for the current day to the cumulative total
            cumulative_total += daily_purchases[date]
            # Store the cumulative total for the current day
            cumulative_counter_purchases[counter][date] = cumulative_total

    for counter, daily_purchases in cumulative_counter_purchases.items():
        # Sort the dates
        sorted_dates = sorted(daily_purchases.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
        sorted_purchases = [daily_purchases[date] for date in sorted_dates]
        # Plot the data
        ax.plot(sorted_dates, sorted_purchases, '-', label=counter)
    
    plt.gcf().autofmt_xdate()  # Optional: for better formatting of date labels
    ax.set_title('Cumulative Purchases Over Time')  # Add a title
    ax.set_xlabel('Date')  # Add x-axis label
    ax.set_ylabel('Total Buys')  # Add y-axis label
    ax.legend(prop=font)

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError
    
def convert_cnt_id(conversion_dict, cnt_id): # short ID to long ID
    #print(conversion_dict)
    api_id = conversion_dict.get(cnt_id, None)
    '''if not api_id:
        print(f"ID {cnt_id} not found in the conversion table.")
    else:
        print(f"Converted from {cnt_id} to {api_id}")'''
    return api_id

def convert_api_id(reverse_conversion_dict, api_id): # long ID to short ID, REVERSE
    api_id = float(api_id)
    cnt_id = reverse_conversion_dict.get(api_id, None)

    return cnt_id

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
    average_wastage, total_wastage, counter_tally, counter_purchases = calculate_totals(all_data, startDate, endDate)
    daily_average_wastage = calculate_daily_average_wastage(all_data, startDate, endDate) 
    #rank_counters(average_wastage, total_wastage, counter_tally)
    metadata = [all_data, average_wastage, total_wastage, counter_tally, counter_purchases, daily_average_wastage] # Store all metadata in a list
    return metadata

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

    # STUDENT SIDE
    plots = ['counters', 'yeargroup', 'house']
    plot(startDate, endDate, plots, metadata, True, f"stu_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"stu_discrete{run}")
    # SODEXO SIDE
    plots = ['counters', 'buys', 'counter_avg']
    plot(startDate, endDate, plots, metadata, True, f"sod_continous{run}")
    plot(startDate, endDate, plots, metadata, False, f"sod_discrete{run}")

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

if __name__ == "__main__":
    

    test("2024-05-13", "2024-06-19")
    #getWeightsbyDate(datetime.strptime("2024-05-13", '%Y-%m-%d'), datetime.strptime("2024-05-15", '%Y-%m-%d'))
    #print(weight_data)