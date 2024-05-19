# Imports
import json
import pandas as pd # type: ignore

dict_list = []

# Open the file in read mode
with open('store/nifty_50.txt', 'r') as file:
    # Reading line by line
    for line in file:
        data_dict = json.loads(line)
        dict_list.append(data_dict)

# Converting data into excel
df = pd.DataFrame(dict_list)
df.to_excel('store/output.xlsx', index=False)