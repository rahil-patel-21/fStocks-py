# Imports
import os
from datetime import datetime
from dotenv import load_dotenv # type: ignore
from pymongo import MongoClient # type: ignore
from sqlalchemy.pool import QueuePool # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy import create_engine, text # type: ignore

# Load .env file
load_dotenv()

connection = None
connection_pool = None
collection_rtscrdt = None
db_engine = None

def init_database():
    global collection_rtscrdt, db_engine
    try:
        # MongoDB connection
        mongo_uri = os.environ.get("MONGO_URI")
        client = MongoClient(mongo_uri)
        db = client['UAT']
        collection_rtscrdt = db['rtscrdt']
        print('MongoDB Connected Successfully!')

        # PostgreSQL connection pool using SQLAlchemy
        db_engine = create_engine(
            f"postgresql+psycopg2://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASS')}@"
            f"{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}",
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=0,
        )
        if db_engine:
            print("PostgreSQL Connection Pool created successfully")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Verify if both connections are established
        if collection_rtscrdt is None:
            print("Failed to connect to MongoDB")
        if db_engine is None:
            print("Failed to create PostgreSQL connection pool")

def injectQuery(query: str):
    global db_engine  # Ensure you use the global db_engine
    if db_engine is None:
        print("Database engine is not initialized.")
        return

    # Create a new session
    Session = sessionmaker(bind=db_engine)
    session = Session()

    try:
        # If the query is a SELECT
        if 'SELECT' in query:
            result = session.execute(text(query))  # Execute raw query
            return result.fetchall()  # Fetch all rows

        # For INSERT, UPDATE, DELETE
        session.execute(text(query))  # Execute raw query
        session.commit()  # Commit the transaction

    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()  # Rollback in case of error
    finally:
        session.close()  # Close the session

def insertRecord(data: any, collectionName):
    targetCollection = None
    if (collectionName == 'rtscrdt'): targetCollection = collection_rtscrdt

    if ('createdAt' not in data): data['createdAt'] = datetime.now()

    targetCollection.insert_one(data)
