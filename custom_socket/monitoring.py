# Imports
import os
import json
import requests # type: ignore

DHAN_CHAIN_URL=os.environ.get("DHAN_CHAIN_URL")

def syncTargetIndex(exp: int, sec_id: int):
    body = { "Data": { "Seg": 0, "Sid": sec_id, "Exp": exp } } 
    headers = { "origin": "https://web.dhan.co", "referer": "https://web.dhan.co/" }
    apiResponse = requests.post(DHAN_CHAIN_URL, headers=headers, data=json.dumps(body))
    responseData = apiResponse.json()['data']
    current_ltp = responseData['sltp']
    opData = responseData['oc']

    targetData = {}
    index = 0
    for key in opData:
        premium_value = float(key)
        diff_value = abs(premium_value - current_ltp)
        if (diff_value <= 500):
            ce_data = opData[key]['ce']
            ce_sid = ce_data['sid']
            targetData[ce_sid] = { "index": index, "name": ce_data['sym'], "segment": 2 }
            index = index + 1

            pe_data = opData[key]['pe']
            pe_sid = pe_data['sid']
            targetData[pe_sid] = { "index": index, "name": pe_data['sym'], "segment": 2 }
            index = index + 1

    return targetData