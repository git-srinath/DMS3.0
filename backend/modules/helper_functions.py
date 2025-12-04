import os
import oracledb
import dotenv

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import logger, info, warning, error
    from backend.modules.mapper import pkgdwmapr_python as pkgdwmapr
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import logger, info, warning, error
    from modules.mapper import pkgdwmapr_python as pkgdwmapr
dotenv.load_dotenv()

ORACLE_SCHEMA = os.getenv("DMS_SCHEMA")

def get_parameter_mapping(conn):
    cursor = None
    try:
        # Detect DB type from connection module (no queries needed)
        module_name = type(conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            db_type = "ORACLE"
        else:
            # Fallback to query-based detection
            db_type = _detect_db_type_from_connection(conn)
        
        # Ensure clean transaction state for PostgreSQL
        if db_type == "POSTGRESQL":
            try:
                conn.rollback()  # Rollback any previous failed transaction
            except Exception:
                pass  # Ignore if no transaction exists
        
        cursor = conn.cursor()
        
        # Get table reference for PostgreSQL (handles case sensitivity)
        dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS') if db_type == "POSTGRESQL" else 'DMS_PARAMS'
        query = f"SELECT PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT FROM {dms_params_ref}"
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency
        columns_upper = _normalize_column_names(columns)
        
        # Fetch all rows and convert to dictionaries with uppercase keys
        result = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns_upper, row))
            result.append(row_dict)
        
        cursor.close()
        cursor = None
        
        # No need to commit if autocommit is enabled (which we set in dbconnect.py)
        # Oracle auto-commits by default
        
        return result
    except Exception as e:
        # Rollback on error for PostgreSQL
        try:
            if db_type == "POSTGRESQL":
                conn.rollback()
        except Exception:
            pass
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def _get_table_ref(cursor, db_type, table_name, schema_name=None):
    """
    Get table reference for use in SQL queries, handling PostgreSQL case sensitivity.
    
    Args:
        cursor: Database cursor
        db_type: Database type ('POSTGRESQL' or 'ORACLE')
        table_name: Base table name (e.g., 'DMS_PARAMS')
        schema_name: Optional schema name (for PostgreSQL, will be lowercased)
        
    Returns:
        Formatted table reference (e.g., 'dms_params' or 'DMS_PARAMS' or 'schema."DMS_PARAMS"')
    """
    if db_type == "POSTGRESQL":
        # Get schema name if provided (default to current schema)
        if schema_name:
            schema_lower = schema_name.lower()
        else:
            # Try to get current schema from cursor
            try:
                cursor.execute("SELECT current_schema()")
                schema_lower = cursor.fetchone()[0].lower()
            except Exception:
                schema_lower = 'public'  # Default fallback
        
        # Detect actual table name format
        try:
            from backend.modules.common.db_table_utils import get_postgresql_table_name as pg_get_table_name
            actual_table_name = pg_get_table_name(cursor, schema_lower, table_name)
            # Quote if uppercase (was created with quotes)
            if actual_table_name != actual_table_name.lower():
                table_ref = f'"{actual_table_name}"'
            else:
                table_ref = actual_table_name
        except Exception:
            # Fallback to lowercase if detection fails
            table_ref = table_name.lower()
        
        # Add schema prefix if schema was provided
        if schema_name:
            return f'{schema_lower}.{table_ref}'
        else:
            return table_ref
    else:
        # Oracle: use uppercase convention, add schema if provided
        if schema_name:
            return f'{schema_name}.{table_name}'
        else:
            return table_name


def _detect_db_type_from_connection(conn):
    """Detect database type from connection object"""
    # First check connection module (fastest, no query needed)
    module_name = type(conn).__module__
    if "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    
    # If module check didn't work, try queries with proper error handling
    cursor = None
    try:
        cursor = conn.cursor()
        # Try Oracle-specific query
        cursor.execute("SELECT 1 FROM dual")
        cursor.close()
        return "ORACLE"
    except Exception:
        # Rollback any failed transaction (important for PostgreSQL)
        try:
            conn.rollback()
        except Exception:
            pass
        
        try:
            if cursor:
                cursor.close()
            cursor = conn.cursor()
            # Try PostgreSQL-specific query
            cursor.execute("SELECT version()")
            cursor.close()
            return "POSTGRESQL"
        except Exception:
            # Rollback again if this also fails
            try:
                conn.rollback()
            except Exception:
                pass
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            # Default to ORACLE if we can't determine
            return "ORACLE"

def _normalize_column_names(columns):
    """Normalize column names to uppercase for consistency between Oracle and PostgreSQL"""
    return [col.upper() if col else col for col in columns]

def add_parameter_mapping(conn, type, code, desc, value):
    cursor = None
    try:
        # Detect DB type from connection module (no queries needed)
        # Use __builtins__['type'] to avoid shadowing by parameter name
        import builtins
        module_name = builtins.type(conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            db_type = "ORACLE"
        else:
            # Fallback to query-based detection
            db_type = _detect_db_type_from_connection(conn)
        
        # Ensure clean transaction state for PostgreSQL
        if db_type == "POSTGRESQL":
            try:
                conn.rollback()  # Rollback any previous failed transaction
            except Exception:
                pass  # Ignore if no transaction exists or autocommit is enabled
        
        cursor = conn.cursor()
        
        if db_type == "POSTGRESQL":
            # PostgreSQL: use unquoted identifiers (will be lowercase in DB, but we normalize in SELECT)
            query = """
                INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            cursor.execute(query, (type, code, desc, value))
        else:  # Oracle
            query = """
                INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT)
                VALUES (:1, :2, :3, :4, sysdate, sysdate)
            """
            cursor.execute(query, [type, code, desc, value])
        
        cursor.close()
        cursor = None
        
        # Commit for PostgreSQL if autocommit is disabled (Oracle auto-commits)
        if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
            conn.commit()
        
        return "Parameter mapping added successfully."
    except Exception as e:
        # Rollback on error for PostgreSQL if autocommit is disabled
        try:
            if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
                conn.rollback()
        except Exception:
            pass
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        error(f"Error adding parameter mapping: {str(e)}")
        raise

def get_mapping_ref(conn, reference):
    """Fetch reference data from DMS_MAPR table"""
    try:
        # Detect DB type from connection module
        module_name = type(conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            db_type = "ORACLE"
        else:
            db_type = _detect_db_type_from_connection(conn)
        
        cursor = conn.cursor()
        
        # Get table reference for PostgreSQL (handles case sensitivity)
        dms_mapr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPR')
        
        # Check if checkpoint columns exist in the table
        checkpoint_columns_exist = False
        try:
            if db_type == "POSTGRESQL":
                # PostgreSQL: table and column names are case-insensitive when unquoted
                # Check using LOWER() for case-insensitive comparison
                table_name_only = dms_mapr_ref.split('.')[-1].strip('"')
                check_query = f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE LOWER(table_name) = LOWER('{table_name_only}') 
                    AND LOWER(column_name) = LOWER('chkpntstrtgy')
                """
            else:  # Oracle
                check_query = """
                    SELECT column_name 
                    FROM user_tab_columns 
                    WHERE table_name = 'DMS_MAPR' AND column_name = 'CHKPNTSTRTGY'
                """
            cursor.execute(check_query)
            checkpoint_columns_exist = cursor.fetchone() is not None
        except Exception as e:
            # If check fails, assume columns don't exist
            checkpoint_columns_exist = False
        
        # Build query based on whether checkpoint columns exist
        if checkpoint_columns_exist:
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT 
                    MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
                    TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID,
                    CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
                    FROM {dms_mapr_ref} WHERE MAPREF = %s  AND  CURFLG = 'Y'
                """
                cursor.execute(query, (reference,))
            else:  # Oracle
                query = """
                    SELECT 
                    MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
                    TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID,
                    CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
                    FROM DMS_MAPR WHERE MAPREF = :1  AND  CURFLG = 'Y'
                """
                cursor.execute(query, [reference])
        else:
            # Query without checkpoint columns
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT 
                    MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
                    TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID
                    FROM {dms_mapr_ref} WHERE MAPREF = %s  AND  CURFLG = 'Y'
                """
                cursor.execute(query, (reference,))
            else:  # Oracle
                query = """
                    SELECT 
                    MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
                    TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID
                    FROM DMS_MAPR WHERE MAPREF = :1  AND  CURFLG = 'Y'
                """
                cursor.execute(query, [reference])
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency (PostgreSQL returns lowercase)
        columns_upper = _normalize_column_names(columns)
        
        # Fetch one row and convert to dictionary
        row = cursor.fetchone()
        result = dict(zip(columns_upper, row)) if row else None
        
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching mapping reference: {str(e)}")
        raise

def get_mapping_details(conn, reference):
    """Fetch mapping details from DMS_MAPRDTL table"""
    try:
        # Detect DB type from connection module
        module_name = type(conn).__module__
        if "psycopg" in module_name or "pg8000" in module_name:
            db_type = "POSTGRESQL"
        elif "oracledb" in module_name or "cx_Oracle" in module_name:
            db_type = "ORACLE"
        else:
            db_type = _detect_db_type_from_connection(conn)
        
        cursor = conn.cursor()
        
        dms_maprdtl_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRDTL')
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT 
                    MAPDTLID, MAPREF, TRGCLNM, TRGCLDTYP, TRGKEYFLG, 
                    TRGKEYSEQ, TRGCLDESC, MAPLOGIC, KEYCLNM, 
                    VALCLNM, MAPCMBCD, EXCSEQ, SCDTYP, LGVRFYFLG
                FROM {dms_maprdtl_ref} 
                WHERE MAPREF = %s
                and CURFLG='Y'
         
                ORDER BY EXCSEQ NULLS LAST, MAPDTLID
            """
            cursor.execute(query, (reference,))
        else:  # Oracle
            query = """
                SELECT 
                    MAPDTLID, MAPREF, TRGCLNM, TRGCLDTYP, TRGKEYFLG, 
                    TRGKEYSEQ, TRGCLDESC, MAPLOGIC, KEYCLNM, 
                    VALCLNM, MAPCMBCD, EXCSEQ, SCDTYP, LGVRFYFLG
                FROM DMS_MAPRDTL 
                WHERE MAPREF = :1
                and CURFLG='Y'
         
                ORDER BY EXCSEQ NULLS LAST, MAPDTLID
            """
            cursor.execute(query, [reference])
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency (PostgreSQL returns lowercase)
        columns_upper = _normalize_column_names(columns)
        
        # Fetch all rows and convert to dictionaries with uppercase keys
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns_upper, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching mapping details: {str(e)}")
        raise

def check_if_job_already_created(connection, p_mapref):
    cursor = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type_from_connection(connection)
        dms_job_ref = _get_table_ref(cursor, db_type, 'DMS_JOB')
        if db_type == "POSTGRESQL":
            sql = f"""
            SELECT COUNT(*) FROM {dms_job_ref} WHERE CURFLG ='Y' AND MAPREF = %s    
            """
            cursor.execute(sql, (p_mapref,))
        else:
            sql = """
            SELECT COUNT(*) FROM DMS_JOB WHERE CURFLG ='Y' AND MAPREF = :p_mapref    
            """
            cursor.execute(sql, {'p_mapref': p_mapref})
        count = cursor.fetchone()[0]
        if count > 0:
            return 'Y'
        else:
            return 'N'
    except Exception as e:
        return 'N'
    finally:
        if cursor:
            cursor.close()  

def get_error_message(conn, map_detail_id):
    """ref: refernece of detail mapping table"""
    try:
        cursor = conn.cursor()
        db_type = _detect_db_type_from_connection(conn)
        
        dms_maperr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPERR')
        table_alias = dms_maperr_ref.split('.')[-1].strip('"') if '.' in dms_maperr_ref else dms_maperr_ref.strip('"')
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT errmsg FROM {dms_maperr_ref} maperr
                WHERE maperr.MAPDTLID = %s 
                ORDER BY maperr.MAPERRID DESC 
                LIMIT 1
            """
            cursor.execute(query, (map_detail_id,))
        else:  # Oracle
            query = """
                SELECT errmsg FROM DMS_MAPERR 
                WHERE DMS_MAPERR.MAPDTLID = :1 
                ORDER BY DMS_MAPERR.MAPERRID DESC 
                FETCH FIRST 1 ROWS ONLY 
            """
            cursor.execute(query, [map_detail_id])
        
        # Fetch one row
        row = cursor.fetchone()
        
        cursor.close()
        
        if not row:
            return "Logic is Verified"
        
        return row[0]  # Return the first column value
    except Exception as e:
        error(f"Error getting error message: {str(e)}")
        raise

def get_error_messages_list(conn, map_detail_ids):
    try:
        result_dict = {}
        cursor = conn.cursor()
        db_type = _detect_db_type_from_connection(conn)
        
        dms_maperr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPERR')
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT errmsg FROM {dms_maperr_ref} maperr
                WHERE maperr.MAPDTLID = %s
                ORDER BY maperr.MAPERRID DESC
                LIMIT 1
            """
            for map_detail_id in map_detail_ids:
                cursor.execute(query, (map_detail_id,))
                row = cursor.fetchone()
                if not row:
                    result_dict[map_detail_id] = "Logic is Verified"
                else:
                    result_dict[map_detail_id] = row[0]
        else:  # Oracle
            query = """
                SELECT errmsg FROM DMS_MAPERR
                WHERE DMS_MAPERR.MAPDTLID = :1
                ORDER BY DMS_MAPERR.MAPERRID DESC
                FETCH FIRST 1 ROWS ONLY
            """
            for map_detail_id in map_detail_ids:
                cursor.execute(query, [map_detail_id])
                row = cursor.fetchone()
                if not row:
                    result_dict[map_detail_id] = "Logic is Verified"
                else:
                    result_dict[map_detail_id] = row[0]
       
        cursor.close()
        return result_dict
       
    except Exception as e:
        error(f"Error getting error messages: {str(e)}")
        raise
def get_parameter_mapping_datatype(conn):
    try:
        cursor = conn.cursor()
        db_type = _detect_db_type_from_connection(conn)
        
        dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
        if db_type == "POSTGRESQL":
            query = f"SELECT PRCD, PRDESC, PRVAL FROM {dms_params_ref} WHERE PRTYP = 'Datatype'"
        else:  # Oracle
            query = "SELECT PRCD, PRDESC ,PRVAL FROM DMS_PARAMS WHERE PRTYP = 'Datatype'"
        
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency
        columns_upper = _normalize_column_names(columns)
        
        # Fetch all rows and convert to dictionaries with uppercase keys
        result = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns_upper, row))
            result.append(row_dict)
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def get_parameter_mapping_scd_type(conn):
    try:
        cursor = conn.cursor()
        db_type = _detect_db_type_from_connection(conn)
        
        dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
        if db_type == "POSTGRESQL":
            query = f"SELECT PRCD, PRDESC, PRVAL FROM {dms_params_ref} WHERE PRTYP = 'SCD'"
        else:  # Oracle
            query = "SELECT PRCD, PRDESC , PRVAL FROM DMS_PARAMS WHERE PRTYP = 'SCD'"
        
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency
        columns_upper = _normalize_column_names(columns)
        
        # Fetch all rows and convert to dictionaries with uppercase keys
        result = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns_upper, row))
            result.append(row_dict)
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def call_activate_deactivate_mapping(connection, p_mapref, p_stflg):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.activate_deactivate_mapping(connection, p_mapref, p_stflg)
        
        if error_message:
            return False, f"Error: {error_message}"
        else:
            action = "activated" if p_stflg == "A" else "deactivated"
            return True, f"Mapping {p_mapref} successfully {action}"
    
    except Exception as e:
        error_message = f"Exception while activating/deactivating mapping: {str(e)}"
        return False, error_message

# mapping function

def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, 
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, p_stflg, p_blkprcrows, 
                         p_trgconid=None, p_user=None, p_chkpntstrtgy='AUTO', p_chkpntclnm=None, p_chkpntenbld='Y'):

    try:
        # Call Python function instead of PL/SQL package
        mapid = pkgdwmapr.create_update_mapping(
            connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
            p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
            p_stflg, p_blkprcrows, p_trgconid=p_trgconid, p_user=p_user,
            p_chkpntstrtgy=p_chkpntstrtgy, p_chkpntclnm=p_chkpntclnm, p_chkpntenbld=p_chkpntenbld
        )
        
        return mapid
        
    except Exception as e:
        error(f"Error creating/updating mapping: {str(e)}")
        raise


def create_update_mapping_detail(connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, 
                               p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm, 
                               p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp, p_lgvrfyflg, p_lgvrfydt,user_id):
 
    try:
        # Call Python function instead of PL/SQL package
        mapdtlid = pkgdwmapr.create_update_mapping_detail(
            connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg,
            p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm,
            p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp,
            p_lgvrfyflg, p_lgvrfydt, user_id
        )
        
        return mapdtlid
        
    except Exception as e:
        error(f"Error creating/updating mapping detail: {str(e)}")
        raise

def validate_logic_in_db(connection, p_logic, p_keyclnm, p_valclnm):
    
    try:
        # Call Python function instead of PL/SQL package
        is_valid = pkgdwmapr.validate_logic(connection, p_logic, p_keyclnm, p_valclnm)
        return is_valid
        
    except Exception as e:
        error(f"Error validating logic: {str(e)}")
        raise



def validate_logic2(connection, p_logic, p_keyclnm, p_valclnm):

    try:
        # Call Python function instead of PL/SQL package
        is_valid, error_message = pkgdwmapr.validate_logic2(connection, p_logic, p_keyclnm, p_valclnm)
        
        return is_valid, error_message
    
    except Exception as e:
        error(f"Error validating logic: {str(e)}")
        raise

def validate_all_mapping_details(metadata_connection, p_mapref, target_connection=None):

    try:
        # Call Python function instead of PL/SQL package
        # If target_connection is provided, use it for SQL validation; otherwise use metadata_connection
        result, error_message = pkgdwmapr.validate_mapping_details(metadata_connection, p_mapref, target_connection=target_connection)
        
        return result, error_message
        
    except Exception as e:
        error(f"Error validating mapping details: {str(e)}")
        raise


# job function

def get_job_list(conn):
    try:
        cursor = conn.cursor()
        db_type = _detect_db_type_from_connection(conn)
        
        # Get schema name from environment
        schema = os.getenv('DMS_SCHEMA', 'TRG')
        
        # Get table reference with schema for PostgreSQL (handles case sensitivity)
        dms_job_ref = _get_table_ref(cursor, db_type, 'DMS_JOB', schema_name=schema)
        
        # Build query with CURFLG filter and database-specific syntax
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT JOBID, MAPID, MAPREF, FRQCD, TRGSCHM, TRGTBTYP, TRGTBNM, SRCSYSTM, STFLG, 
                       RECCRDT, RECUPDT, CURFLG, BLKPRCROWS, CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD, TRGCONID
                FROM {dms_job_ref}
                WHERE CURFLG = 'Y'
                ORDER BY RECCRDT DESC
            """
            cursor.execute(query)
        else:  # Oracle
            query = f"""
                SELECT JOBID, MAPID, MAPREF, FRQCD, TRGSCHM, TRGTBTYP, TRGTBNM, SRCSYSTM, STFLG, 
                       RECCRDT, RECUPDT, CURFLG, BLKPRCROWS, CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD, TRGCONID
                FROM {dms_job_ref}
                WHERE CURFLG = 'Y'
                ORDER BY RECCRDT DESC
            """
            cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Normalize column names to uppercase for consistency
        columns_upper = _normalize_column_names(columns)
        
        # Fetch all rows and convert to dictionaries with uppercase keys
        result = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns_upper, row))
            result.append(row_dict)
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching job list: {str(e)}")
        raise


def call_create_update_job(connection, p_mapref):
    """
    Create or update job using Python implementation with hash-based change detection.
    
    Args:
        connection: Oracle database connection
        p_mapref: Mapping reference
        
    Returns:
        Tuple of (job_id, error_message)
    """
    try:
        # Import Python implementation
        try:
            from backend.modules.jobs import pkgdwjob_python as pkgdms_job
        except ImportError:
            from modules.jobs import pkgdwjob_python as pkgdms_job  # type: ignore

        # Call Python version
        job_id = pkgdms_job.create_update_job(connection, p_mapref)
        
        if job_id:
            info(f"Job created/updated successfully for {p_mapref}: JobID={job_id}")
            return job_id, None
        else:
            error_message = f"Failed to create/update job for {p_mapref}"
            error(error_message)
            return None, error_message
    
    except Exception as e:
        error_message = f"Error creating/updating job: {str(e)}"
        error(error_message)
        return None, error_message

def call_delete_mapping(connection, p_mapref):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.delete_mapping(connection, p_mapref)
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping {p_mapref} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping: {str(e)}"
        return False, error_message

def call_delete_mapping_details(connection, p_mapref, p_trgclnm):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.delete_mapping_details(connection, p_mapref, p_trgclnm)
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping detail {p_mapref}-{p_trgclnm} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping detail: {str(e)}"
        return False, error_message






