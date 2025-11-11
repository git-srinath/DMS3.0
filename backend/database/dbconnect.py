import os
import oracledb
import sqlite3
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
import traceback

# Load environment variables
load_dotenv()

# Database connection parameters
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_sid = os.getenv("DB_SID")

# SQLite connection
sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database_instance', 'sqlite_app.db')
sqlite_engine = create_engine(f'sqlite:///{sqlite_db_path}')

def create_oracle_connection():
    try:
        # Import logger inside the function to avoid circular imports
        from modules.logger import info, error
        
        connection = oracledb.connect(
            user=db_user,
            password=db_password,
            dsn=f"{db_host}:{db_port}/{db_sid}"
        )
        info("Oracle connection established successfully")
        return connection
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        from modules.logger import error
        error(f"Error establishing Oracle connection: {str(e)}")
        raise

def create_oracle_connection_dwapp():
    try:
        # Import logger inside the function to avoid circular imports
        from modules.logger import info, error
        
        connection = oracledb.connect(
            user=db_user,
            password=db_password,
            dsn=f"{db_host}:{db_port}/{db_sid}"
        )
        info("Oracle connection established successfully")
        return connection
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        from modules.logger import error
        error(f"Error establishing Oracle connection: {str(e)}")
        raise 