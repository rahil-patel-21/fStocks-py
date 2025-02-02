# Imports
import os
import re
import json
import hashlib
import datetime
import requests # type: ignore
from database import injectQuery
from database import insertRecord
from dotenv import load_dotenv # type: ignore
from datetime import datetime, timedelta, timezone
from dhanhq import dhanhq, marketfeed # type: ignore
from custom_socket.monitoring import syncTargetIndex # type: ignore
from utils.file_service import xlsx_to_list_of_dicts, appendToDictList, list_of_dicts_to_xlsx

# Load .env file
load_dotenv()

DHAN_AUTH_TOKEN=os.environ.get("DHAN_AUTH_TOKEN")
DHAN_CLIENT_CODE=os.environ.get("DHAN_CLIENT_CODE")
DHAN_RTSCRDT_URL=os.environ.get("DHAN_RTSCRDT_URL")
DHAN_TICK_BASE_URL=os.environ.get("DHAN_TICK_BASE_URL")
DHAN_CHAIN_URL=os.environ.get("DHAN_CHAIN_URL")

cached_data = {}
current_date = datetime.now().strftime("%Y-%m-%d")

dhanClient = dhanhq(DHAN_CLIENT_CODE,DHAN_AUTH_TOKEN)

def init():
    syncIndexes()
    instruments = getIndexes()
    data = marketfeed.DhanFeed(DHAN_CLIENT_CODE, DHAN_AUTH_TOKEN, instruments, "v2")

    while True:
        try:
            data.run_forever()
            response = data.get_data()
            response_type = response['type']
        except Exception as e:
            print(e)
            print('Re starting ...')
            init()
            break

        if (response_type != 'Full Data'): continue
        del response['type']
        del response['exchange_segment']

        insertFullData(response)

def getIndexes():
    finalizedList = []
    with open('store/indexes.json', 'r') as file:
        companyData = json.load(file)
        for key in companyData:
            value = companyData[key]
            finalizedList.append((value['segment'],key, 21))

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
            indMoneyUrl = f"{IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
            params = { "catalog-required": "true", "params": "true", "response_format": "json" }
            indResponse = requests.get(indMoneyUrl, params=params)
            indResponseData = indResponse.json()
            # Unsuccessful response
            if 'success' not in indResponseData:
                if 'debug_info' in  indResponseData:
                    # Name is different on Dhan and IndMoney
                    if indResponseData['debug_info'] == 'record_not_found':
                        indMoneyUrl = os.environ.get('IND_MONEY_SEARCH_API')
                        params = { "platform": "web", "query": symbol, "filter": "IN_STOCKS", "offset": 0 }
                        indResponse = requests.get(indMoneyUrl, params=params)
                        indResponseData = indResponse.json()
                        searchResults = indResponseData['data']['search_results']['data'][1]['data'][0]
                        symbol_name = searchResults['title1']['text']
                        symbol_name = symbol_name.lower().replace('limited', 'ltd').replace('&', 'and')
                        symbol_name = re.sub(r'\s+', '-', symbol_name) 
                        indMoneyUrl = f"{IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
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

            indMoneyUrl = f"{IND_MONEY_BASE_URL}indian-stock-broker/catalog/v2/get-entity-details/{symbol_name}-share-price"
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
            value = { "price": responseData['data']['Ltp'], "market_cap": market_cap, "name": el['SM_SYMBOL_NAME'], "returns": stockReturns, "Secid": secId, "volume": responseData['data']['vol_t_td'] }
            target_dict[secId] = value
            appendToDictList('store/dhan_security_ids.json',value)
            print(len(target_dict))

        except Exception as err:
            print(f"An error occurred: {err}")
    # list_of_dicts_to_xlsx('store/finalized_dhan_ids.xlsx', raw_list)

def getChartData(targetTimeStr = ''):
    # Define the start and end times as datetime objects
    start_time = datetime(2024, 7, 12, 9, 15, 00) 
    end_time = datetime(2024, 7, 12, 15, 15, 00)
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    url = DHAN_TICK_BASE_URL + 'getDataS'
    headers = {'Content-Type': 'application/json'}
    data = {
    "EXCH": "NSE",
    "SEG": "D",
    "INST": "OPTIDX",
    "SEC_ID": 72149,
    "START": 1724354479,
    "END": 1724436155,
    "START_TIME": "Fri Aug 23 2024 00:51:19 GMT+0530 (India Standard Time)",
    "END_TIME": "Fri Aug 23 2024 23:32:35 GMT+0530 (India Standard Time)",
    "INTERVAL": "30S"
}

    chartResponse = requests.post(url, headers=headers, data=json.dumps(data))
    chartData = chartResponse.json()
    del chartData['data']['oi']
    
    totalClosingValue = 0
    minValue = 1000000000
    finalizedList = []
    firstCloseValue = None
    for index, _ in enumerate(chartData['data']['o']):
        openValue = chartData['data']['o'][index]
        closeValue = chartData['data']['c'][index]
        ocDiff = (chartData['data']['c'][index] * 100 / chartData['data']['o'][index]) - 100
        timeStr = chartData['data']['Time'][index]

        if timeStr == '2024-08-23T09:29:30+05:30': break
        # volume = chartData['data']['v'][index]
        volume = 1
        totalClosingValue = totalClosingValue + closeValue
        avgCloseValue = totalClosingValue / (index + 1)
        isAboveAvg = avgCloseValue < closeValue
        prediction = 'NOT_DECIDED'
        print(isAboveAvg)

        if closeValue < minValue:
            minValue = closeValue
        minToCurrentRatio = (closeValue * 100 / minValue) - 100

        if index == 0: 
            firstCloseValue = closeValue
            finalizedList.append({"openValue": openValue, "closeValue": closeValue, "avgCloseValue": avgCloseValue, "isAboveAvg": isAboveAvg, "prevCloseDiff": 0, "ocDiff": ocDiff, "timeStr": timeStr, "volume": volume, "prevVolumeDiff": 0,  "positiveCount": 0, "negativeCount": 0, "minToCurrentRatio": minToCurrentRatio, "prediction": prediction})
            continue

        prevCloseValue = chartData['data']['c'][index - 1]
        prevCloseDiff = (closeValue * 100 / prevCloseValue) - 100
        # prevVolume = chartData['data']['v'][index - 1]
        # prevVolumeDiff = (volume * 100 / prevVolume) - 100
        prevVolumeDiff = 1

        if index <= 4: 
            finalizedList.append({"openValue": openValue, "closeValue": closeValue, "avgCloseValue": avgCloseValue, "isAboveAvg": isAboveAvg, "prevCloseDiff": prevCloseDiff, "ocDiff": ocDiff, "timeStr": timeStr, "volume": volume, "prevVolumeDiff": prevVolumeDiff,  "positiveCount": 0, "negativeCount": 0, "minToCurrentRatio": minToCurrentRatio, "prediction": prediction})
            continue

        negativeCount = 0
        positiveCount = 0
        maxValue = 0
        canPrevBuy = False
        for i in range(0, 5):
            targetIndex = index - (i + 1)
            targetData = finalizedList[targetIndex]
            if (targetData['isAboveAvg'] == True and targetData['prevCloseDiff'] > 0 and targetData['ocDiff'] > 0 and targetData['minToCurrentRatio'] > 2.5):
                positiveCount = positiveCount + 1
            else: negativeCount = negativeCount + 1
            if targetData['closeValue'] > maxValue:
                maxValue = targetData['closeValue']
            if (targetData['prediction'] == 'CAN_BUY'): canPrevBuy = True
        maxDiff = (closeValue * 100 / maxValue) - 100

        if (negativeCount > 2 or positiveCount <= 2 or isAboveAvg == False): prediction = 'RISKY'
        elif (positiveCount >= 3 and prevCloseDiff > 0 and ocDiff > 0 and isAboveAvg == True and maxDiff > 0 and canPrevBuy == False and firstCloseValue < closeValue and firstCloseValue < openValue):
            prediction = 'CAN_BUY'  
        else:
            prediction = 'RISKY_BUY'

        # Last check
        if (prediction == 'CAN_BUY'):
            last_5_mins_list = filter_last_8_minutes(finalizedList, chartData['data']['Time'][index])
            maxValue = 0
            canPrevBuy = False
            for el in last_5_mins_list:
                if (el['closeValue'] > maxValue):
                    maxValue = el['closeValue']
                if (el['prediction'] == 'CAN_BUY'): canPrevBuy = True
            maxDiff = (closeValue * 100 / maxValue) - 100
            firstCloseDiff = (closeValue * 100 / firstCloseValue) - 100
            target_time = parse_time(timeStr)
            hours = target_time.hour
            if (maxDiff <= 0.3 or canPrevBuy == True or firstCloseDiff > 60): prediction = 'SLIGHTLY_RISKY'
            elif (hours >= 13): prediction = 'RISKY_TIME'
            else: print({"maxDiff": maxValue, "time": timeStr})

        finalizedList.append({"openValue": openValue, "closeValue": closeValue, "avgCloseValue": avgCloseValue, "isAboveAvg": isAboveAvg, "prevCloseDiff": prevCloseDiff, "ocDiff": ocDiff, "timeStr": timeStr, "volume": volume, "prevVolumeDiff": prevVolumeDiff, "positiveCount": positiveCount, "negativeCount": negativeCount, "minToCurrentRatio": minToCurrentRatio, "prediction": prediction})
    list_of_dicts_to_xlsx('store/test.xlsx', finalizedList)

def parse_time(time_str):
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z").time()

def filter_last_8_minutes(data, time_str):
    target_time = parse_time(time_str)
    # Get the current date
    today = datetime.today().date()
    five_minutes_ago = (datetime.combine(today, target_time) - timedelta(minutes=8)).time()

    def is_within_last_8_minutes(item):
        ltt_time = parse_time(item["timeStr"])
        return five_minutes_ago <= ltt_time <= target_time

    return [item for item in data if is_within_last_8_minutes(item)]

def get_rtscrdt_data():
    headers = {'Content-Type': 'application/json'}
    data = { "Data": { "Seg": 2, "Secid": 36750 } }

    apiResponse = requests.post(DHAN_RTSCRDT_URL, headers=headers, data=json.dumps(data))
    responseData = apiResponse.json()
    finalData = responseData['data']
    insertRecord(data=finalData, collectionName='rtscrdt')

def getCandleData(targetTimeStr=""):
    url = DHAN_TICK_BASE_URL + 'getDataS'
    headers = {'Content-Type': 'application/json'}
    data = {
    "EXCH": "NSE",
    "SEG": "D",
    "INST": "OPTIDX",
    "SEC_ID": 72149,
    "START": 1724354479,
    "END": 1724436155,
    "START_TIME": "Fri Aug 23 2024 00:51:19 GMT+0530 (India Standard Time)",
    "END_TIME": "Fri Aug 23 2024 23:32:35 GMT+0530 (India Standard Time)",
    "INTERVAL": "30S"
    }

    chartResponse = requests.post(url, headers=headers, data=json.dumps(data))
    chartData = chartResponse.json()
    del chartData['data']['oi']

    finalizedList = []
    for index, _ in enumerate(chartData['data']['o']):
        timeStr = chartData['data']['Time'][index]
        if (targetTimeStr == timeStr): break

        open = chartData['data']['o'][index]
        close = chartData['data']['c'][index]
        high = chartData['data']['h'][index]
        low = chartData['data']['l'][index]
        finalizedList.append({"open": open, "close": close, "high": high, "low": low, "timeStr": timeStr})

    return finalizedList

def cal():
    targetList = getCandleData(targetTimeStr="2024-08-23T09:29:30+05:30")

    positiveRallyCount = 0
    for index, item in enumerate(targetList):
        open = item['open']
        close = item['close']
        high = item['high']
        low = item['low']
        isLastEl = (len(targetList) - 1) == index

        ocDiff = (close * 100 / open) - 100
        print(ocDiff)
        if (isLastEl and ocDiff <= 0): return False
        if (ocDiff < 0): positiveRallyCount = 0
        else: positiveRallyCount = positiveRallyCount + 1

        print(positiveRallyCount)

def syncIndexes():
    nifty_50_data = syncTargetIndex(1415385000, 13) # 07 NOV 24
    nifty_bank_data = syncTargetIndex(1415298600, 25) # 06 NOV 24
    finnifty_data = syncTargetIndex(1415817000, 27) # 12 NOV 24

    # Merge all derivatives
    finalizedData = {}
    for key in nifty_50_data:
        finalizedData[key] = nifty_50_data[key]
    for key in nifty_bank_data:
        finalizedData[key] = nifty_bank_data[key]
    for key in finnifty_data:
        finalizedData[key] = finnifty_data[key]


    file_path = f"store/indexes.json" 
    with open(file_path, 'w') as json_file:
        json.dump(finalizedData, json_file, indent=4)

def insertFullData(raw_response):
    market_depth = raw_response['depth']
    current_buy_q = 0
    current_sell_q = 0
    for el in market_depth:
        current_buy_q += el['bid_quantity']
        current_sell_q += el['ask_quantity']
    current_buy_dominance = 0
    if ((current_buy_q + current_sell_q) != 0):
        current_buy_dominance = round((current_buy_q * 100) / (current_buy_q  + current_sell_q), 2)
    total_buy_dominance = 0
    if ((raw_response['total_buy_quantity'] + raw_response['total_sell_quantity']) != 0):
        total_buy_dominance = round((raw_response['total_buy_quantity'] * 100) / (raw_response['total_buy_quantity']  + raw_response['total_sell_quantity']), 2)
    
    md5_hash = hashlib.md5()
    md5_hash.update(json.dumps(raw_response).encode('utf-8'))
    datetime_obj = datetime.strptime(raw_response['LTT'], "%H:%M:%S").replace(
    year=datetime.today().year,
    month=datetime.today().month,
    day=datetime.today().day)
    datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)
    iso_with_tz = datetime_obj.isoformat()

    creation_data = {
        "id": md5_hash.hexdigest(),
        "sec_id": raw_response['security_id'],
        "trading_time": iso_with_tz,
        "current_value": float(raw_response['LTP']),
        "avg_value": float(raw_response['volume']),
        "high": float(raw_response['high']),
        "open": float(raw_response['open']),
        "low": float(raw_response['low']),
        "close": float(raw_response['close']),
        "current_buy_dominance": current_buy_dominance,
        "current_buy_q": current_buy_q,
        "current_sell_q": current_sell_q,
        "total_buy_dominance": total_buy_dominance,
        "total_buy_q": raw_response['total_buy_quantity'],
        "total_sell_q": raw_response['total_sell_quantity'],
        "volume": raw_response['volume'],
        "current_oi": raw_response['OI'],
        "oi_day_low": raw_response['oi_day_low'],
        "oi_day_high": raw_response['oi_day_high']
    }
    columns_to_insert = []
    values_to_insert = []

    for key, value in creation_data.items():
        columns_to_insert.append(f'"{key}"')  # Quote column names to avoid SQL syntax issues
        # Format values, adding single quotes around strings
        if isinstance(value, str):
            values_to_insert.append(f"'{value}'")
        else:
            values_to_insert.append(str(value))

    # Join columns and values with commas
    columns_str = ', '.join(columns_to_insert)
    values_str = ', '.join(values_to_insert)

    # Construct the raw query
    raw_query = f"""
        INSERT INTO "FullData" ({columns_str})
        VALUES ({values_str})
    """
    try:
        injectQuery(raw_query)
    except Exception as e:
        if "unique constraint" in str(e):
            pass
        else: print(e)

