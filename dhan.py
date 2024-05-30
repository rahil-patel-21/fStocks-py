# Imports
import os
import json
import datetime
from datetime import datetime, timedelta
from dotenv import load_dotenv # type: ignore
from prediction import isBullish # type: ignore
from dhanhq import dhanhq, marketfeed # type: ignore

# Load .env file
load_dotenv()

DHAN_CLIENT_CODE=os.environ.get("DHAN_CLIENT_CODE")
DHAN_AUTH_TOKEN=os.environ.get("DHAN_AUTH_TOKEN")

cached_data = {}
current_date = datetime.now().strftime("%Y-%m-%d")

dhanClient = dhanhq(DHAN_CLIENT_CODE,DHAN_AUTH_TOKEN)

def init(type):
    instruments = []
    if (type == 'NIFTY_COMPANIES'):
        instruments = getNiftyCompanies()
    elif (type == 'NIFTY_INDEX'):
        instruments = getNiftyIndexes()
    else: instruments = []

    feed = marketfeed.DhanFeed(DHAN_CLIENT_CODE, DHAN_AUTH_TOKEN, instruments, marketfeed.Ticker, on_connect=on_connect, on_message=on_message)
    feed.run_forever()

async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    try:
        # print(message)
        # Default assign -> Cached data
        security_id = message['security_id']
        if str(security_id) not in cached_data:
            cached_data[str(security_id)] = {"open_price": 0, "risk": 100}

        target_data = cached_data[str(security_id)]
        if (target_data['open_price'] == 0 and message['type'] == 'Previous Close'):
            target_data['open_price'] = float(message['prev_close'])

        if 'LTT' not in message:
            return
        if 'last_sync_time' not in cached_data[str(security_id)]:
            cached_data[str(security_id)]['last_sync_time'] = '09:15:00'
        diff_in_seconds = time_difference_in_seconds(cached_data[str(security_id)]['last_sync_time'], message['LTT'])
        if (diff_in_seconds < 5):
            return {} 
        cached_data[str(security_id)]['last_sync_time'] = message['LTT']
            
        # Read existing data from the file if it exists
        file_path = f"store/ticker_data/nifty_50_{message['security_id']}_{current_date}" 
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    existing_data = []
        else: existing_data = []
        existing_data.append(message)
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

        # isBullish(file_path)

    except Exception as e:
        print('ERROR')
        print(e)

def getNiftyCompanies():
    finalizedList = []
    with open('store/nifty_companies.json', 'r') as file:
        companyData = json.load(file)
        for key in companyData:
            value = companyData[key]
            finalizedList.append((value['segment'],key))

    return finalizedList

def getNiftyIndexes():
    finalizedList = []
    with open('store/nifty_index.json', 'r') as file:
        companyData = json.load(file)
        for key in companyData:
            value = companyData[key]
            finalizedList.append((value['segment'],key))

    return finalizedList

def time_difference_in_seconds(time1_str, time2_str):
    # Define the time format
    time_format = "%H:%M:%S"
    
    # Convert string times to datetime objects
    time1 = datetime.strptime(time1_str, time_format)
    time2 = datetime.strptime(time2_str, time_format)
    
    # Calculate the difference
    time_difference = time2 - time1
    
    # Extract the difference in seconds
    difference_in_seconds = time_difference.total_seconds()
    
    return difference_in_seconds