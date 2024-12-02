import sys
from us_visa.exceptions import USvisaException
from us_visa.logger import logging
import os
from us_visa.constants import DB_NAME,MONGODB_URL_KEY
import pymongo
import certifi



ca = certifi.where()

class MongoDBClient:
    """
    Class Name :   export_data_into_feature_store
    Description :   This method exports the dataframe from mongodb feature store as dataframe 
    
    Output      :   connection to mongodb database
    On Failure  :   raises an exception
    """
    client = None

class MongoDBClient:
    client = None

    
    
    def __init__(self, database_name=DB_NAME) -> None:
        try:
            if MongoDBClient.client is None:
                raw_mongo_db_url = os.getenv(MONGODB_URL_KEY)
                logging.info(f"Raw MongoDB URI from environment variable: {repr(raw_mongo_db_url)}")

                # Remove unwanted spaces and quotes
                if raw_mongo_db_url:
                    mongo_db_url = raw_mongo_db_url.strip().strip('"').strip("'")
                else:
                    mongo_db_url = None

                logging.info(f"Processed MongoDB URI: {repr(mongo_db_url)}")

                if not mongo_db_url or not mongo_db_url.startswith(("mongodb://", "mongodb+srv://")):
                    logging.error(f"Invalid MongoDB URI: {repr(mongo_db_url)}")
                    raise Exception("Invalid or improperly formatted MongoDB URI.")

                MongoDBClient.client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

            self.client = MongoDBClient.client
            self.database = self.client[database_name]
            self.database_name = database_name
            logging.info("MongoDB connection successful")
        except Exception as e:
            raise USvisaException(e, sys)
