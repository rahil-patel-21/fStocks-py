# Imports
import os
import math
from database import injectQuery
from datetime import datetime, date
from pytz import timezone # type: ignore
from dhanhq import dhanhq # type: ignore
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()

DHAN_CLIENT_CODE=os.environ.get("DHAN_CLIENT_CODE")
DHAN_AUTH_TOKEN=os.environ.get("DHAN_AUTH_TOKEN")
dhanClient = dhanhq(DHAN_CLIENT_CODE,DHAN_AUTH_TOKEN)

def buy_stock(securityId, currentPrice):
    try:
        now = datetime.now(timezone('UTC'))
        current_date = date.today()
        outputList = injectQuery(f'''SELECT * FROM "Transactions" WHERE "security_id" = '{securityId}' AND "initiated_at" >= '{current_date}' LIMIT 1''')
        if len(outputList) > 0:
            return {"valid": False, "message": "Target stock already bought today"}

        currentBalance = getCurrentBalance()
        totalQuantity = math.floor(currentBalance / currentPrice) - 1
        if (totalQuantity <= 2): return {"valid": False, "message": "There is an issue with the quantity"}
        elif (currentBalance < 2500): return {"valid": False, "message": "Insufficient wallet balance"}
        
        uniqueId  = f"{current_date}-{securityId}"
        injectQuery(f'''INSERT INTO
        "Transactions" ("security_id", "type", "quantity", "initiated_at", "unique_id")
         VALUES        ('{securityId}','1','1', '{now}', '{uniqueId}'); ''')
        
        orderData = dhanClient.place_order(
        tag='',
        transaction_type=dhanClient.BUY,
        exchange_segment=dhanClient.NSE,
        product_type=dhanClient.INTRA,
        order_type=dhanClient.MARKET,
        validity='DAY',
        security_id=f"{securityId}",
        quantity=totalQuantity,
        disclosed_quantity=0,
        price=0,
        trigger_price=0,
        after_market_order=False,
        amo_time='OPEN',
        bo_profit_value=0,
        bo_stop_loss_Value=0,
        drv_expiry_date=None,
        drv_options_type=None,
        drv_strike_price=None)
        print(orderData)


    except Exception as e:
        print(e)
        return {"valid": False, "message": "Internal server error"}
    
def getCurrentBalance():
        walletData = dhanClient.get_fund_limits()
        data = walletData['data']
        currentBalance = data['availabelBalance'] - data['blockedPayoutAmount']
        return currentBalance