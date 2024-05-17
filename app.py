# Imports
import os
import json
from fastapi import FastAPI # type: ignore
from dhanhq import marketfeed # type: ignore
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()
DHAN_CLIENT_CODE=os.environ.get("DHAN_CLIENT_CODE")
DHAN_AUTH_TOKEN=os.environ.get("DHAN_AUTH_TOKEN")
CODE_VERSION=os.environ.get("CODE_VERSION")

async def on_connect(instance):
    print("Connected to websocket")

file_path = "store/nifty_50.txt"

cached_data = {}
async def on_message(instance, message):
    try:
        # Default assign -> Cached data
        security_id = message['security_id']
        if str(security_id) not in cached_data:
            cached_data[str(security_id)] = {"open_price": 0, "risk": 100}

        # Default assign -> Target data
        target_data = cached_data[str(security_id)]
        if (target_data['open_price'] == 0 and message['type'] == 'Previous Close'):
            target_data['open_price'] = float(message['prev_close'])

        if (message['type'] == 'Ticker Data' and message['LTP'] is not None):
            current_price = float(message['LTP'])
            print(current_price)
            # file = open(file_path, "a")
            # json_data = json.dumps(message)
            # file.write(json_data + "\n")
            # file.close()
    except Exception as e:
        print('ERROR')
        print(e)

instruments = [(1,"2031"),(1,"11532")]
feed = marketfeed.DhanFeed(DHAN_CLIENT_CODE,
    DHAN_AUTH_TOKEN,
    instruments,
    marketfeed.Ticker,
    on_connect=on_connect,
    on_message=on_message)
feed.run_forever()

# app = FastAPI()

# @app.get('/init')
# def init():
#     feed.run_forever()
#     return {'code_version': CODE_VERSION}