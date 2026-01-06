import os
import importlib
import sqlite3
from urllib.parse import urlparse, parse_qsl
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

# Database type (ORACLE or POSTGRESQL)
db_type = os.getenv("DB_TYPE", "ORACLE").upper()

# Database connection parameters
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_sid = os.getenv("DB_SID")  # Oracle
db_name = os.getenv("DB_NAME")  # PostgreSQL
db_connection_string = os.getenv("DB_CONNECTION_STRING")  # Optional connection string

# SQLite connection
sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database_instance', 'sqlite_app.db')
sqlite_engine = create_engine(f'sqlite:///{sqlite_db_path}')

DRIVER_REGISTRY = {
    "ORACLE": {"module": "oracledb", "install_hint": "pip install oracledb"},
    "POSTGRESQL": {"module": "psycopg2", "install_hint": "pip install psycopg2-binary"},
    "POSTGRES": {"module": "psycopg2", "install_hint": "pip install psycopg2-binary"},
    "MSSQL": {"module": "pyodbc", "install_hint": "pip install pyodbc"},
    "SQL_SERVER": {"module": "pyodbc", "install_hint": "pip install pyodbc"},
    "MYSQL": {"module": "mysql.connector", "install_hint": "pip install mysql-connector-python"},
    "SYBASE": {"module": "pyodbc", "install_hint": "pip install pyodbc"},
    "REDSHIFT": {"module": "psycopg2", "install_hint": "pip install psycopg2-binary"},
    "HIVE": {"module": "pyhive.hive", "install_hint": "pip install pyhive"},
    "SNOWFLAKE": {"module": "snowflake.connector", "install_hint": "pip install snowflake-connector-python"},
    "DB2": {"module": "ibm_db", "install_hint": "pip install ibm_db"},
}

_driver_cache = {}
SQLSERVER_ODBC_DRIVER = os.getenv("SQLSERVER_ODBC_DRIVER", "{ODBC Driver 17 for SQL Server}")
SYBASE_ODBC_DRIVER = os.getenv("SYBASE_ODBC_DRIVER", "{FreeTDS}")

def _load_db_driver(db_type_key: str):
    """
    Lazily import and cache the driver module for the requested database type.
    """
    normalized_type = (db_type_key or "").upper()
    registry_entry = DRIVER_REGISTRY.get(normalized_type)
    
    if not registry_entry:
        raise ValueError(f"Unsupported database type '{db_type_key}'. Please verify the configuration.")
    
    if normalized_type in _driver_cache:
        return _driver_cache[normalized_type]
    
    module_name = registry_entry["module"]
    try:
        module = importlib.import_module(module_name)
        _driver_cache[normalized_type] = module
        return module
    except ImportError as exc:
        # Support both FastAPI (package import) and legacy Flask (relative import)
        try:
            from backend.modules.logger import error
        except ImportError:  # Flask app.py context
            from modules.logger import error
        install_hint = registry_entry.get("install_hint", f"pip install {module_name}")
        error(f"Missing driver for {normalized_type}: {module_name}. Install it via '{install_hint}'. Error: {exc}")
        raise

def _parse_standard_connection_url(connection_url: str, expected_scheme: str = None):
    """
    Parse URLs like mysql://user:pass@host:3306/dbname into components.
    """
    parsed = urlparse(connection_url.strip())
    if not parsed.scheme:
        raise ValueError("Connection string must include a scheme (e.g., mysql://)")
    if expected_scheme and parsed.scheme.lower() != expected_scheme.lower():
        raise ValueError(f"Expected connection string starting with {expected_scheme}://")
    
    username = parsed.username or ""
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = parsed.port
    database = parsed.path.lstrip("/") if parsed.path else ""
    
    if not username or not password:
        raise ValueError("Connection string must include username and password.")
    if not database:
        raise ValueError("Connection string must include a database/schema name in the path segment.")
    
    return {
        "scheme": parsed.scheme,
        "username": username,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
        "query": dict(parse_qsl(parsed.query)) if parsed.query else {},
    }

def create_metadata_connection():
    """
    Create a database connection for metadata operations.
    Supports both Oracle and PostgreSQL based on DB_TYPE environment variable.
    
    Returns:
        Database connection object (Oracle or PostgreSQL)
    """
    # Import logger inside the function to avoid circular imports
    try:
        from backend.modules.logger import info, error, debug
    except ImportError:
        from modules.logger import info, error, debug
    
    # Check environment variable each time to ensure we get the current value
    current_db_type = os.getenv("DB_TYPE", "ORACLE").upper()
    
    debug(f"[create_metadata_connection] DB_TYPE from environment: {current_db_type}")
    
    if current_db_type == "POSTGRESQL":
        debug("[create_metadata_connection] Creating PostgreSQL connection")
        return create_postgresql_connection()
    else:
        debug("[create_metadata_connection] Creating Oracle connection")
        return create_oracle_connection()

def create_oracle_connection():
    """Create Oracle database connection"""
    try:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import info, error
        except ImportError:
            from modules.logger import info, error
        oracledb = _load_db_driver("ORACLE")
        
        if db_connection_string:
            connection = oracledb.connect(dsn=db_connection_string)
        else:
            connection = oracledb.connect(
                user=db_user,
                password=db_password,
                dsn=f"{db_host}:{db_port}/{db_sid}"
            )
        info("Oracle connection established successfully")
        return connection
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error
        error(f"Error establishing Oracle connection: {str(e)}")
        raise

def create_postgresql_connection():
    """Create PostgreSQL database connection"""
    try:
        psycopg2 = _load_db_driver("POSTGRESQL")
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import info, error
        except ImportError:
            from modules.logger import info, error
        
        # Verify we have required parameters
        if not db_connection_string and not all([db_host, db_name, db_user, db_password]):
            error("PostgreSQL connection requires DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD environment variables")
            raise ValueError("Missing required PostgreSQL connection parameters")
        
        if db_connection_string:
            info(f"[create_postgresql_connection] Using connection string")
            connection = psycopg2.connect(db_connection_string)
        else:
            info(f"[create_postgresql_connection] Connecting to {db_host}:{db_port or 5432}/{db_name} as {db_user}")
            connection = psycopg2.connect(
                host=db_host,
                port=int(db_port) if db_port else 5432,
                database=db_name,
                user=db_user,
                password=db_password
            )
        # Set autocommit mode to avoid transaction issues
        # This ensures each query is automatically committed
        connection.autocommit = True
        info("PostgreSQL connection established successfully")
        return connection
    except ImportError:
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error
        error("psycopg2 is required for PostgreSQL connections. Install it with: pip install psycopg2-binary")
        raise
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error
        error(f"Error establishing PostgreSQL connection: {str(e)}")
        import traceback
        error(f"Traceback: {traceback.format_exc()}")
        raise

def create_oracle_connection_dwapp():
    try:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import info, error
        except ImportError:
            from modules.logger import info, error
        oracledb = _load_db_driver("ORACLE")
        
        connection = oracledb.connect(
            user=db_user,
            password=db_password,
            dsn=f"{db_host}:{db_port}/{db_sid}"
        )
        info("Oracle connection established successfully")
        return connection
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error
        error(f"Error establishing Oracle connection: {str(e)}")
        raise

def create_target_connection(connection_id):
    """
    Create a database connection for target data operations
    based on connection ID from DMS_DBCONDTLS
    
    Args:
        connection_id: CONID from DMS_DBCONDTLS table
    
    Returns:
        Database connection object (Oracle or PostgreSQL)
    """
    try:
        try:
            from backend.modules.logger import info, error
        except ImportError:
            from modules.logger import info, error
        import builtins
        
        # Get metadata connection first
        metadata_conn = create_metadata_connection()
        cursor = metadata_conn.cursor()
        
        # Detect database type from metadata connection
        module_name = builtins.type(metadata_conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            metadata_db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            metadata_db_type = "ORACLE"
        else:
            metadata_db_type = "ORACLE"  # Default fallback
        
        # Fetch connection details from DMS_DBCONDTLS
        if metadata_db_type == "POSTGRESQL":
            cursor.execute("""
                SELECT connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, dbtyp
                FROM DMS_DBCONDTLS
                WHERE conid = %s AND curflg = 'Y'
            """, (connection_id,))
        else:  # Oracle
            cursor.execute("""
                SELECT connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, dbtyp
                FROM DMS_DBCONDTLS
                WHERE conid = :1 AND curflg = 'Y'
            """, [connection_id])
        
        row = cursor.fetchone()
        if not row:
            cursor.close()
            metadata_conn.close()
            raise Exception(f"Connection ID {connection_id} not found or inactive")
        
        connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, dbtyp = row
        
        # Close metadata connection
        cursor.close()
        metadata_conn.close()
        
        # Determine target database type
        target_db_type = (dbtyp or "").upper() if dbtyp else "ORACLE"
        
        # Create target connection based on database type
        if target_db_type in ["POSTGRESQL", "POSTGRES"]:
            psycopg2 = _load_db_driver("POSTGRESQL")
            if constr and constr.strip():  # Use connection string if provided
                target_conn = psycopg2.connect(constr)
            else:  # Build from components
                target_conn = psycopg2.connect(
                    host=dbhost,
                    port=int(dbport) if dbport else 5432,
                    database=dbsrvnm,
                    user=usrnm,
                    password=passwd
                )
            target_conn.autocommit = True
        elif target_db_type in ["MSSQL", "SQL_SERVER"]:
            pyodbc = _load_db_driver("MSSQL")
            if constr and constr.strip():
                target_conn = pyodbc.connect(constr)
            else:
                server = dbhost or "localhost"
                if dbport:
                    server = f"{server},{dbport}"
                database = dbsrvnm or ""
                conn_str = (
                    f"DRIVER={SQLSERVER_ODBC_DRIVER};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"UID={usrnm};"
                    f"PWD={passwd};"
                    "Encrypt=no;TrustServerCertificate=yes;"
                )
                target_conn = pyodbc.connect(conn_str)
            target_conn.autocommit = True
        elif target_db_type == "MYSQL":
            mysql_connector = _load_db_driver("MYSQL")
            if constr and constr.strip():
                parsed = _parse_standard_connection_url(constr, expected_scheme="mysql")
                target_conn = mysql_connector.connect(
                    host=parsed["host"],
                    port=parsed["port"] or 3306,
                    database=parsed["database"],
                    user=parsed["username"],
                    password=parsed["password"]
                )
            else:
                target_conn = mysql_connector.connect(
                    host=dbhost,
                    port=int(dbport) if dbport else 3306,
                    database=dbsrvnm,
                    user=usrnm,
                    password=passwd
                )
            target_conn.autocommit = True
        elif target_db_type == "SYBASE":
            pyodbc = _load_db_driver("SYBASE")
            if constr and constr.strip():
                target_conn = pyodbc.connect(constr)
            else:
                server = dbhost or "localhost"
                database = dbsrvnm or ""
                conn_parts = [
                    f"DRIVER={SYBASE_ODBC_DRIVER}",
                    f"SERVER={server}",
                    f"DATABASE={database}",
                    f"UID={usrnm}",
                    f"PWD={passwd}",
                ]
                if dbport:
                    conn_parts.append(f"PORT={dbport}")
                conn_str = ";".join(conn_parts) + ";"
                target_conn = pyodbc.connect(conn_str)
            target_conn.autocommit = True
        else:  # Oracle (default)
            oracledb = _load_db_driver("ORACLE")
            if constr and constr.strip():  # Use connection string if provided
                target_conn = oracledb.connect(dsn=constr)
            else:  # Build from components
                target_conn = oracledb.connect(
                    user=usrnm,
                    password=passwd,
                    dsn=f"{dbhost}:{dbport}/{dbsrvnm}"
                )
        
        debug(f"Target connection '{connm}' (ID: {connection_id}, Type: {target_db_type}) established successfully")
        return target_conn
        
    except Exception as e:
        try:
            from backend.modules.logger import error
        except ImportError:
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
        try:
            from backend.modules.logger import info
        except ImportError:
            from modules.logger import info
        
        # Get metadata connection
        metadata_conn = create_metadata_connection()
        cursor = metadata_conn.cursor()
        
        # Detect database type from metadata connection
        import builtins
        module_name = builtins.type(metadata_conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            metadata_db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            metadata_db_type = "ORACLE"
        else:
            metadata_db_type = "ORACLE"  # Default fallback
        
        # Check if mapping has a target connection
        if metadata_db_type == "POSTGRESQL":
            cursor.execute("""
                SELECT trgconid
                FROM DMS_MAPR
                WHERE mapref = %s AND curflg = 'Y'
            """, (mapref,))
        else:  # Oracle
            cursor.execute("""
                SELECT trgconid
                FROM DMS_MAPR
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
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error
        error(f"Error getting connection for mapping {mapref}: {str(e)}")
        raise 