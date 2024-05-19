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
            print(open_diff)

            return False

        else: return False