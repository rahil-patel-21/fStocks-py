# Imports
import os
import psycopg2 # type: ignore
from psycopg2 import pool # type: ignore
from dotenv import load_dotenv # type: ignore

# Load .env file
load_dotenv()

connection = None
connection_pool = None

def init_database():
    try:
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
    try:
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
            for row in rows:
                print(row)

    except Exception as e:
        print('Error while injecting the query')
        print(e)