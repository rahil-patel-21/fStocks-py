# Imports
import os
from dhan import init
from dotenv import load_dotenv # type: ignore
from database import init_database, injectQuery

print('APP STARTED SUCCESSFULLY !')

# Load .env file
load_dotenv()
CODE_VERSION=os.environ.get("CODE_VERSION")

init_database()

init("NIFTY_COMPANIES")

print('APP RUNNING SUCCESSFULLY !')