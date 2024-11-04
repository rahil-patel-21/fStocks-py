# Imports
from dhan import init
from database import init_database

init_database() # Connect database (Postgresql)

init() # NIFTY_COMPANIES | NIFTY_INDEX | SMALL_CAP | HDFC_24_07_25