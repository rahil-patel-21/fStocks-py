# Imports
import os
from dhan import init
from datetime import datetime
from pytz import timezone # type: ignore
from dotenv import load_dotenv # type: ignore
from database import init_database, injectQuery


# Load .env file
load_dotenv()
CODE_VERSION=os.environ.get("CODE_VERSION")

init_database()

now = datetime.now(timezone('UTC'))
injectQuery(f'''
INSERT INTO
    "Transactions" ("security_id", "type", "quantity", "initiated_at", "completed_at", "unique_id")
VALUES
  ('1','1','1', '{now}', '{now}', '2');
            ''')

init("NIFTY_COMPANIES")