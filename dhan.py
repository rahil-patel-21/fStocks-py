# Imports
import os
import re
import json
import datetime
from datetime import datetime
import requests # type: ignore
from dotenv import load_dotenv # type: ignore
from dhanhq import dhanhq, marketfeed # type: ignore
from prediction import isBullish, isIndexBullish # type: ignore
from utils.file_service import xlsx_to_list_of_dicts, appendToDictList, list_of_dicts_to_xlsx

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
    print(instruments)

    # Ticker - Ticker Data | Quote - Quote Data | Depth - Market Depth
    feed = marketfeed.DhanFeed(DHAN_CLIENT_CODE, DHAN_AUTH_TOKEN, instruments, marketfeed.Quote, on_connect=on_connect, on_message=on_message)
    feed.run_forever()

async def on_connect(_):
    print("Connected to websocket")

async def on_message(_, message):
    try:
        print(message)
        # Default assign -> Cached data
        security_id = message['security_id']
        if str(security_id) not in cached_data:
            cached_data[str(security_id)] = {"open_price": 0, "risk": 100}

        target_data = cached_data[str(security_id)]
        if (target_data['open_price'] == 0 and message['type'] == 'Previous Close'):
            target_data['open_price'] = float(message['prev_close'])

        if 'LTT' not in message:
            if message['type'] == 'OI Data':
                message['LTT'] = datetime.now().strftime("%H:%M:%S")
            else: return
        if 'last_sync_time' not in cached_data[str(security_id)]:
            cached_data[str(security_id)]['last_sync_time'] = '09:15:00'
        diff_in_seconds = time_difference_in_seconds(cached_data[str(security_id)]['last_sync_time'], message['LTT'])
        if (diff_in_seconds < 5):
            return {} 
        cached_data[str(security_id)]['last_sync_time'] = message['LTT']
            
        # Read existing data from the file if it exists
        file_path = None
        if message['type'] == 'Quote Data':
            file_path = f"store/quote_data/{current_date}_{message['security_id']}" 
        elif message['type'] == 'OI Data':
            file_path = f"store/oi_data/{current_date}_{message['security_id']}" 
        else: file_path = f"store/ticker_data/nifty_50_{message['security_id']}_{current_date}" 

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
        result = isIndexBullish(file_path)
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

def syncSecurityIds():
    file_path = 'store/finalized_dhan_ids.xlsx'
    list = xlsx_to_list_of_dicts(file_path)

    target_dict = {}
    raw_list = []
    for el in list:
        try:
            if 'SEM_EXM_EXCH_ID' not in el: continue
            if (el['SEM_EXM_EXCH_ID'] != 'NSE'): continue
            if 'SEM_SMST_SECURITY_ID' not in el: continue
            if 'SEM_TRADING_SYMBOL' not in el: continue

            secId = el['SEM_SMST_SECURITY_ID']
            symbol = el['SEM_TRADING_SYMBOL']
        
            url = os.environ.get("DHAN_STOCK_DETAILS_URL")
            data = { "Data": { "Seg": 1, "Secid": secId } }
            response = requests.post(url, json=data)
            responseData = response.json()
            if 'data' not in responseData: continue
            if 'Ltp' not in responseData['data']: continue
            current_price = responseData['data']['Ltp']
            if (current_price < 50 or current_price > 10000): continue
            if (responseData['data']['vol_t_td'] < 100000): continue
            raw_list.append(el)

            symbol_name = el['SM_SYMBOL_NAME'].lower().replace('limited', 'ltd').replace('&', 'and')
            symbol_name = re.sub(r'\s+', '-', symbol_name) 
            IND_MONEY_BASE_URL=os.environ.get("IND_MONEY_API_BASE_URL")
            indMoneyUrl = f"${IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
            params = { "catalog-required": "true", "params": "true", "response_format": "json" }
            indResponse = requests.get(indMoneyUrl, params=params)
            indResponseData = indResponse.json()
            # Unsuccessful response
            if 'success' not in indResponseData:
                if 'debug_info' in  indResponseData:
                    # Name is different on Dhan and IndMoney
                    if indResponseData['debug_info'] == 'record_not_found':
                        indMoneyUrl = f"${IND_MONEY_BASE_URL}global-search/public/v2/global-search/"
                        params = { "platform": "web", "query": symbol, "filter": "IN_STOCKS", "offset": 0 }
                        indResponse = requests.get(indMoneyUrl, params=params)
                        indResponseData = indResponse.json()
                        searchResults = indResponseData['data']['search_results']['data'][1]['data'][0]
                        symbol_name = searchResults['title1']['text']
                        symbol_name = symbol_name.lower().replace('limited', 'ltd').replace('&', 'and')
                        symbol_name = re.sub(r'\s+', '-', symbol_name) 
                        indMoneyUrl = f"${IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
                        params = { "catalog-required": "true", "params": "true", "response_format": "json" }
                        indResponse = requests.get(indMoneyUrl, params=params)
                        indResponseData = indResponse.json()
                    else: continue
                else: continue
            if indResponseData['success'] != True: continue
            if 'catalog' not in indResponseData: continue
            if 'entity_stats' not in indResponseData['catalog']: continue
            if 'performance' not in indResponseData['catalog']['entity_stats']: continue
            stockReturns = indResponseData['catalog']['entity_stats']['performance']['returns']
            has_negative_value = any(item['value'] < 0 for item in stockReturns)
            if has_negative_value: continue

            indMoneyUrl = f"${IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
            indResponse = requests.get(indMoneyUrl)
            indResponseData = indResponse.json()
            json_string = json.dumps(indResponseData)
            market_cap = None
            if 'marketCap=SMALL' in json_string:
                market_cap='SMALL'
            elif 'marketCap=MID' in json_string:
                market_cap='MID'
            elif 'marketCap=LARGE' in json_string:
                market_cap='LARGE'
            value = { "price": responseData['data']['Ltp'], "market_cap": market_cap, "name": el['SM_SYMBOL_NAME'], "returns": stockReturns, "volume": responseData['data']['vol_t_td'] }
            target_dict[secId] = value
            appendToDictList('store/dhan_security_ids.json',value)
            print(len(target_dict))

        except Exception as e:
            print(e)
    # list_of_dicts_to_xlsx('store/finalized_dhan_ids.xlsx', raw_list)

syncSecurityIds()