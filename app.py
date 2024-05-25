# Imports
import os
from dhan import *
from database import init_database, injectQuery
from dotenv import load_dotenv # type: ignore


# Load .env file
load_dotenv()
CODE_VERSION=os.environ.get("CODE_VERSION")

init_database()

injectQuery('SELECT * FROM "LiveData" LIMIT 5')

init("NIFTY_COMPANIES")

# app = FastAPI()

# @app.get('/init')
# def init():
#     feed.run_forever()
#     return {'code_version': CODE_VERSION}