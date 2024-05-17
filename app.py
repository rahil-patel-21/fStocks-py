# Imports
import os
import time
import json
import requests # type: ignore
import schedule # type: ignore
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
async def on_message(instance, message):
    try:
        print(message)
        if (message['type'] == 'Ticker Data'):
            file = open(file_path, "a")
            json_data = json.dumps(message)
            file.write(json_data + "\n")
            file.close()
    except Exception as e:
        print(e)

instruments = [(0,"13")]
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

# def cronJob():
#     # Define the URL and payload data
#     url = 'https://scanx.dhan.co/scanx/optchain'
#     payload = {
#         "Data": {
#             "Seg": 0,
#             "Sid": 13,
#             "Exp": 1400265000
#         }
#     }
#     headers = {'Content-Type': 'text/plain'}

#     # Send a POST request with the payload data
#     response = requests.post(url, json=payload, headers=headers)

#     # Print the response content
#     print(response.text)

# # Scheduling the job to run every 5 seconds
# schedule.every(5).seconds.do(cronJob)

# while True:
#     schedule.run_pending()
#     time.sleep(1)