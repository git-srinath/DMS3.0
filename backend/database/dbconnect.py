import os
import oracledb
import sqlite3
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
import traceback

# Load environment variables
# Try backend/.env first, then fall back to project root/.env
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fall back to default behavior (searches from current directory upward)
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

def create_target_connection(connection_id):
    """
    Create a database connection for target data operations
    based on connection ID from DWDBCONDTLS
    
    Args:
        connection_id: CONID from DWDBCONDTLS table
    
    Returns:
        Oracle connection object
    """
    try:
        from modules.logger import info, error
        
        # Get metadata connection first
        metadata_conn = create_oracle_connection()
        cursor = metadata_conn.cursor()
        
        # Fetch connection details from DWDBCONDTLS
        cursor.execute("""
            SELECT connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr
            FROM DWDBCONDTLS
            WHERE conid = :1 AND curflg = 'Y'
        """, [connection_id])
        
        row = cursor.fetchone()
        if not row:
            cursor.close()
            metadata_conn.close()
            raise Exception(f"Connection ID {connection_id} not found or inactive")
        
        connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr = row
        
        # Close metadata connection
        cursor.close()
        metadata_conn.close()
        
        # Create target connection
        if constr and constr.strip():  # Use connection string if provided
            target_conn = oracledb.connect(dsn=constr)
        else:  # Build from components
            target_conn = oracledb.connect(
                user=usrnm,
                password=passwd,
                dsn=f"{dbhost}:{dbport}/{dbsrvnm}"
            )
        
        info(f"Target connection '{connm}' (ID: {connection_id}) established successfully")
        return target_conn
        
    except Exception as e:
        from modules.logger import error
        error(f"Error establishing target connection (ID: {connection_id}): {str(e)}")
        raise

def get_connection_for_mapping(mapref):
    """
    Get the appropriate database connection for a mapping
    If mapping has a target connection ID, use that; otherwise use metadata connection
    
    Args:
        mapref: Mapping reference code
    
    Returns:
        Tuple: (connection, is_target_connection, trgconid)
            - connection: Database connection object
            - is_target_connection: Boolean indicating if this is a target connection
            - trgconid: Target connection ID (None if using metadata connection)
    """
    try:
        from modules.logger import info
        
        # Get metadata connection
        metadata_conn = create_oracle_connection()
        cursor = metadata_conn.cursor()
        
        # Check if mapping has a target connection
        cursor.execute("""
            SELECT trgconid
            FROM DWMAPR
            WHERE mapref = :1 AND curflg = 'Y'
        """, [mapref])
        
        row = cursor.fetchone()
        cursor.close()
        
        if row and row[0]:  # Has target connection
            trgconid = row[0]
            metadata_conn.close()
            target_conn = create_target_connection(trgconid)
            info(f"Using target connection (ID: {trgconid}) for mapping {mapref}")
            return target_conn, True, trgconid
        else:  # Use metadata connection
            info(f"Using metadata connection for mapping {mapref}")
            return metadata_conn, False, None
            
    except Exception as e:
        from modules.logger import error
        error(f"Error getting connection for mapping {mapref}: {str(e)}")
        raise 