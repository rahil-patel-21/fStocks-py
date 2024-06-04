# Imports
import json
import datetime
from transaction import buy_stock

class PredictionService:

    def canBuy(_self, message, targetData):
        if (message['type'] == 'Ticker Data' and message['LTP'] is not None):
            message['LTT'] = '09:24:55'
            current_price = float(message['LTP'])

            current_time = message['LTT']
            if (current_time is None): return False
            current_second = float(current_time.split(':')[2])
            if (current_second % 5 != 0):
                return False# Checking only for every 5th second

            # Check today's full day movement
            open_price = targetData['open_price'] or 3000
            open_diff = (current_price * 100 / open_price) - 100
            if (open_diff <= 0): return False# Continue only if bullish movement

            return False

        else: return False

def isIndexBullish(filePath):
    openValue = None
    maxValue = 0
    minValue = 1000000000000
    result = False

    isLevel1Clear = False
    targetSecurityId = None
    currentPrice = None

    # Open and read the JSON file
    with open(filePath, 'r') as file:
        data = json.load(file) # Parse JSON data into a Python object
        for index, el in enumerate(data):
            if 'type' in el and 'LTP' in el:
                if el['type'] == 'Ticker Data':
                    value = float(el['LTP'])
                    # Assign values as per current value
                    if (value > maxValue): maxValue = value
                    if (value < minValue): minValue = value
                    if (index == 0):
                        openValue = value
                        continue

                    # Check current position
                    if (index == len(data) - 1):
                        openDiff = (value * 100 / openValue) - 100
                        if (openDiff >= 2.5 and openDiff < 200): # Positive movement
                            downDiff = (minValue * 100 / openValue) - 100
                            if (downDiff >= -2.5): # Today no negative movement in past
                                upDiff = (maxValue * 100 / openValue) - 100
                                if (upDiff < 200): # Today no too high movement in past
                                    targetSecurityId = el['security_id']
                                    currentPrice = value
                                    isLevel1Clear = True
  
    # Check for level 2
    if isLevel1Clear == True:
        isLevel2Clear = False
        last_five_mins_list = filter_last_5_minutes(data, data[len(data) - 1])
        if len(last_five_mins_list) > 60 or len(last_five_mins_list) < 25:
            return False
        
        stable_count = 0
        up_count = 0
        low_count = 0
        first_el_of_five_min = None
        last_el_of_five_min = None
        max_value_of_five_min = -100000
        for index, el in enumerate(last_five_mins_list):
            if 'type' in el and 'LTP' in el:
                if el['type'] == 'Ticker Data':
                    value = float(el['LTP'])
                    if value > max_value_of_five_min:
                        max_value_of_five_min = value
                    if (index == 0): 
                        first_el_of_five_min = value 
                        continue
                    elif index == len(last_five_mins_list) - 1:
                        last_el_of_five_min = value

                    prev_el = last_five_mins_list[index - 1]
                    prev_value = float(prev_el['LTP'])
                    if (value == prev_value): stable_count = stable_count + 1 # Stable position
                    if (value > prev_value): up_count = up_count + 1 # Up position
                    if (value < prev_value): low_count = low_count + 1 # Lower position

        # Concluding level 2
        total_count = len(last_five_mins_list)
        stable_ratio = stable_count * 100 / total_count
        up_ratio = up_count * 100 / total_count
        low_ratio = low_count * 100 / total_count

        if (low_ratio >= up_ratio or low_ratio >= 50): # Downward movement in last 5 mins
            return False
        if (stable_ratio >= 20): # Stable movement, Scalping unpredictable
            return False
        if (up_ratio >= 50): # Too good time to buy the stock
            isLevel2Clear = True
        else: return False # Unpredictable   

        if (isLevel2Clear == True):
            five_min_diff = last_el_of_five_min * 100 / first_el_of_five_min - 100
            max_to_current_ratio = last_el_of_five_min * 100 / max_value_of_five_min - 100
            if (five_min_diff <= 5 or max_to_current_ratio <= 0): # No up movement for scalping
                return False;
            # Save data to check prediction later on 
            else: 
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f'store/prediction/data_{timestamp}.json'
                with open(filename, 'w') as file:
                    json.dump(data, file, indent=4)
                # buy_stock(targetSecurityId, currentPrice) # Buy stock
                return True # Too good time to buy the stock

def isBullish(filePath): # For large cap of 50 companies of nifty
    openValue = None
    maxValue = 0
    minValue = 1000000000000
    result = False

    isLevel1Clear = False
    targetSecurityId = None
    currentPrice = None
    # Open and read the JSON file
    with open(filePath, 'r') as file:
        data = json.load(file) # Parse JSON data into a Python object
        for index, el in enumerate(data):
            if 'type' in el and 'LTP' in el:
                if el['type'] == 'Ticker Data':
                    value = int(float(el['LTP']))
                    # Assign values as per current value
                    if (value > maxValue): maxValue = value
                    if (value < minValue): minValue = value
                    if (index == 0):
                        openValue = value
                        continue

                    # Check current position
                    if (index == len(data) - 1):
                        openDiff = (value * 100 / openValue) - 100
                        if (openDiff >= 0.15 and openDiff < 1.5): # Positive movement
                            downDiff = (minValue * 100 / openValue) - 100
                            if (downDiff >= -0.025): # Today no negative movement in past
                                upDiff = (maxValue * 100 / openValue) - 100
                                if (upDiff < 5): # Today no too high movement in past
                                    targetSecurityId = el['security_id']
                                    currentPrice = value
                                    isLevel1Clear = True
 
    # Check for level 2
    if isLevel1Clear == True:
        isLevel2Clear = False
        last_five_mins_list = filter_last_5_minutes(data, data[len(data) - 1])
        if len(last_five_mins_list) > 60 or len(last_five_mins_list) < 25:
            return False

        stable_count = 0
        up_count = 0
        low_count = 0
        first_el_of_five_min = None
        last_el_of_five_min = None
        for index, el in enumerate(last_five_mins_list):
            if 'type' in el and 'LTP' in el:
                if el['type'] == 'Ticker Data':
                    value = float(el['LTP'])
                    if (index == 0): 
                        first_el_of_five_min = value 
                        continue
                    elif index == len(last_five_mins_list) - 1:
                        last_el_of_five_min = value

                    prev_el = last_five_mins_list[index - 1]
                    prev_value = float(prev_el['LTP'])
                    if (value == prev_value): stable_count = stable_count + 1 # Stable position
                    if (value > prev_value): up_count = up_count + 1 # Up position
                    if (value < prev_value): low_count = low_count + 1 # Lower position
    
        # Concluding level 2
        total_count = len(last_five_mins_list)
        stable_ratio = stable_count * 100 / total_count
        up_ratio = up_count * 100 / total_count
        low_ratio = low_count * 100 / total_count

        if (low_ratio >= up_ratio or low_ratio >= 40): # Downward movement in last 5 mins
            return False
        if (stable_ratio >= 33): # Stable movement, Scalping unpredictable
            return False
        if (up_ratio >= 40): # Too good time to buy the stock
            isLevel2Clear = True
        else: return False # Unpredictable    

        if (isLevel2Clear == True):
            five_min_diff = last_el_of_five_min * 100 / first_el_of_five_min - 100
            if (five_min_diff <= 0.1): # No up movement for scalping
                return False;
            # Save data to check prediction later on 
            else: 
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f'store/prediction/data_{timestamp}.json'
                with open(filename, 'w') as file:
                    json.dump(data, file, indent=4)
                buy_stock(targetSecurityId, currentPrice) # Buy stock
                return True # Too good time to buy the stock

    return result

def parse_time(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S").time()

def filter_last_5_minutes(data, targetData):
    target_time = parse_time(targetData['LTT'])
    five_minutes_ago = (datetime.datetime.combine(datetime.date.today(), target_time) - datetime.timedelta(minutes=5)).time()

    def is_within_last_5_minutes(item):
        ltt_time = parse_time(item["LTT"])
        return five_minutes_ago <= ltt_time <= target_time

    return [item for item in data if is_within_last_5_minutes(item)]