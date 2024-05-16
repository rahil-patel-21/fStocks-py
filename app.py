# Imports
import os
import json
from dhanhq import marketfeed # type: ignore
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()
DHAN_CLIENT_CODE=db_host = os.environ.get("DHAN_CLIENT_CODE")
DHAN_AUTH_TOKEN=db_host = os.environ.get("DHAN_AUTH_TOKEN")

async def on_connect(instance):
    print("Connected to websocket")

file_path = "store/nifty_50.txt"
async def on_message(instance, message):
    try:
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