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
CREATE TABLE "FullData" (
    "id" VARCHAR(32) PRIMARY KEY, "sec_id" INTEGER,
	"trading_time" TIMESTAMPTZ,
	"current_value" DOUBLE PRECISION,
	"avg_value" DOUBLE PRECISION,
	"low" DOUBLE PRECISION, "high" DOUBLE PRECISION,
	"open" DOUBLE PRECISION, "close" DOUBLE PRECISION,
	"current_buy_q" INTEGER, "current_sell_q" INTEGER,
	"current_buy_dominance" DOUBLE PRECISION,
	"total_buy_q" INTEGER, "total_sell_q" INTEGER,
	"total_buy_dominance" DOUBLE PRECISION,
	"volume" INTEGER, "current_oi" INTEGER,
	"oi_day_low" INTEGER, "oi_day_high" INTEGER
);
```

## Run project

```
sh py.sh
```
