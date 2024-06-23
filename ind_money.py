# Imports
import os
import json
from bs4 import BeautifulSoup
import requests # type: ignore
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()

def getTechnicalAnalysis():
    IND_MONEY_TECHNICAL_URL=os.environ.get("IND_MONEY_TECHNICAL_URL")
    url = IND_MONEY_TECHNICAL_URL + 'rail-vikas-nigam-ltd-technical-analysis'
    print(url)

    indResponse = requests.get(url)
    indResponseData = indResponse.text

    soup = BeautifulSoup(indResponseData, 'html.parser')
    element = soup.find(id='__NEXT_DATA__')
    element_content = element.string if element else None
    data_json = json.loads(element_content)['props']['pageProps']['apiResponse']['catalog']['stock_details']
    return data_json

    # if data_json is not None:
    #     output_file = 'next_data.json'
    #     with open(output_file, 'w') as file:
    #         json.dump(data_json, file, indent=2)

getTechnicalAnalysis()