import logging
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    MONGODB_URL = os.getenv('MONGODB_URL')
    logging.info(f"DEBUG: MongoDB URL → {MONGODB_URL}")
    DATABASE_NAME = os.getenv('DATABASE_NAME')
    logging.info(f"DEBUG: MongoDB URL → {DATABASE_NAME}")