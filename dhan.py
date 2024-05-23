# Imports
import os
import json
import datetime
from dhanhq import marketfeed # type: ignore
from dotenv import load_dotenv # type: ignore
from prediction import isBullish # type: ignore

# Load .env file
load_dotenv()

DHAN_CLIENT_CODE=os.environ.get("DHAN_CLIENT_CODE")
DHAN_AUTH_TOKEN=os.environ.get("DHAN_AUTH_TOKEN")

cached_data = {}
current_date = datetime.datetime.now().strftime("%Y-%m-%d")


def init(type):
    instruments = []
    if (type == 'NIFTY_COMPANIES'):
        instruments = getNiftyCompanies()
    else: instruments = [(1,"2031"),(1,"11532")]

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
        current_time = message['LTT']
        if (current_time is None): return
        current_second = float(current_time.split(':')[2])
        if (current_second % 5 != 0):
            return# Checking only for every 5th second
            
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

        result = isBullish(file_path)
        print(result)

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