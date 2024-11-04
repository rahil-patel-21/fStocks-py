# Instructions

## Installation (Ubuntu)

```
sudo apt install python3-pip
pip3 install dhanhq
pip3 install websockets
pip3 install python-dotenv
pip3 install fastapi uvicorn
pip3 install pandas
pip3 install openpyxl
pip3 install urllib3==1.26.6
pip3 install pymongo
pip3 install sqlalchemy
```

```
CREATE TABLE RawStuffs (
    date TIMESTAMPTZ NOT NULL,
    type SMALLINT NOT NULL,
    raw_data JSONB NOT NULL
);
```

## Run project

```
sh py.sh
```
