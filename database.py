# Imports
import os
from datetime import datetime
import psycopg2 # type: ignore
from dotenv import load_dotenv # type: ignore
from pymongo import MongoClient # type: ignore

# Load .env file
load_dotenv()

connection = None
connection_pool = None
collection_rtscrdt = None

def init_database():
    try:
        
        # Create a MongoClient object
        uri = os.environ.get("MONGO_URI")
        client = MongoClient(uri)
        # Connect to a specific database
        db = client['UAT']
        # Access a collection
        global collection_rtscrdt
        collection_rtscrdt = db['rtscrdt']
        print('MongoDB Connected Successfully !')

        # Create a connection pool
        global connection_pool
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USERNAME"),
            password=os.environ.get("DB_PASS"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT")
        )
        if connection_pool:
            print("Connection pool created successfully")

    except Exception as e:
        print(f"An error occurred: {e}")

def injectQuery(query: str):
    # Get a connection from the pool
    connection = connection_pool.getconn()

    cursor = connection.cursor()
    cursor.execute(query)
    if 'SELECT' in query:
        rows = cursor.fetchall()
    connection.commit()
    cursor.close()
    connection_pool.putconn(connection)
        
    if 'SELECT' in query:
        return rows

def insertRecord(data: any, collectionName):
    targetCollection = None
    if (collectionName == 'rtscrdt'): targetCollection = collection_rtscrdt

    if ('createdAt' not in data): data['createdAt'] = datetime.now()

    targetCollection.insert_one(data)

# init_database()