# Imports
import os
from dhan import init
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()
CODE_VERSION=os.environ.get("CODE_VERSION")

init("NIFTY_INDEX") # NIFTY_COMPANIES | NIFTY_INDEX

print('APP RUNNING SUCCESSFULLY !')