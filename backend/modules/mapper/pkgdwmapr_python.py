"""
Python conversion of PKGDMS_MAPR PL/SQL Package
This module provides Python equivalents of the Oracle PL/SQL package functions
for mapping validation and processing.

Change history:
date        who              Remarks
----------- ---------------- ----------------------------------------------------------------------------------------
13-Nov-2025 Converted        Converted from PL/SQL to Python
"""

import os
import re
from datetime import datetime
from modules.logger import logger, info, warning, error
import oracledb
from modules.common.id_provider import next_id as get_next_id
from modules.common.db_table_utils import get_postgresql_table_name
import builtins

# Package constants
G_NAME = 'PKGDMS_MAPR_PY'
G_VER = 'V001'
G_USER = None

class PKGDMS_MAPRError(Exception):
    """Custom exception for PKGDMS_MAPR errors"""
    pass

def version():
    """Return package version"""
    return f"{G_NAME}:{G_VER}"

def _nvl(value, default):
    """Python equivalent of Oracle's NVL function"""
    return default if value is None else value

def _detect_db_type(connection):
    """Detect database type from connection"""
    module_name = builtins.type(connection).__module__
    connection_type = builtins.type(connection).__name__
    info(f"Detecting DB type - module: {module_name}, type: {connection_type}")
    
    if "psycopg" in module_name or "pg8000" in module_name:
        detected = "POSTGRESQL"
    elif "oracledb" in module_name or "cx_Oracle" in module_name:
        detected = "ORACLE"
    else:
        detected = "ORACLE"  # Default fallback
    
    info(f"Detected database type: {detected}")
    return detected


def _get_table_ref(cursor, db_type, table_name, schema_name=None):
    """
    Get table reference for use in SQL queries, handling PostgreSQL case sensitivity.
    
    Args:
        cursor: Database cursor
        db_type: Database type ('POSTGRESQL' or 'ORACLE')
        table_name: Base table name (e.g., 'DMS_MAPR')
        schema_name: Optional schema name (for PostgreSQL, will be lowercased)
        
    Returns:
        Formatted table reference (e.g., 'dms_mapr' or 'DMS_MAPR' or 'schema."DMS_MAPR"')
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
            actual_table_name = get_postgresql_table_name(cursor, schema_lower, table_name)
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

def _raise_error(proc_name, error_code, param_info, exception=None):
    """Raise an error with formatted message"""
    if exception:
        msg = f"{G_NAME}.{proc_name} - Error {error_code}: {param_info} - {str(exception)}"
    else:
        msg = f"{G_NAME}.{proc_name} - Error {error_code}: {param_info}"
    error(msg)
    raise PKGDMS_MAPRError(msg)

def create_update_sql(connection, p_dwmaprsqlcd, p_dwmaprsql, p_sqlconid=None):
    """
    Function to record SQL query
    Returns: maprsqlid
    
    Args:
        connection: Database connection
        p_dwmaprsqlcd: SQL code identifier
        p_dwmaprsql: SQL query content
        p_sqlconid: Source database connection ID (from DMS_DBCONDTLS). 
                    If None, uses metadata connection.
    """
    w_procnm = 'CREATE_UPDATE_SQL'
    w_parm = f'SqlCode={p_dwmaprsqlcd}'[:100]
    
    cursor = None
    try:
        info(f"Starting create_update_sql for code: {p_dwmaprsqlcd}, connection_id: {p_sqlconid}")
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        info(f"Database type detected: {db_type}")
        
        # Validation
        info(f"Validating SQL code: {p_dwmaprsqlcd}")
        if not p_dwmaprsqlcd or p_dwmaprsqlcd.strip() == '':
            w_msg = 'The mapping SQL Code cannot be null.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        if ' ' in p_dwmaprsqlcd:
            w_msg = 'Space(s) not allowed to form mapping SQL Code.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        info(f"Validating SQL content length: {len(str(p_dwmaprsql)) if p_dwmaprsql else 0}")
        if not p_dwmaprsql or len(str(p_dwmaprsql).strip()) == 0:
            w_msg = 'The SQL Query cannot be blank.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        info(f"Validation passed. Checking connection ID: {p_sqlconid}")
        # Validate connection ID if provided
        sqlconid_val = None
        if p_sqlconid is not None and str(p_sqlconid).strip() != '':
            try:
                sqlconid_val = int(p_sqlconid)
                info(f"Validating connection ID {sqlconid_val} exists and is active")
                # Validate connection exists and is active
                try:
                    dms_dbcondtls_ref = _get_table_ref(cursor, db_type, 'DMS_DBCONDTLS')
                    if db_type == "POSTGRESQL":
                        cursor.execute(f"""
                            SELECT conid FROM {dms_dbcondtls_ref} 
                            WHERE conid = %s AND curflg = 'Y'
                        """, (sqlconid_val,))
                    else:  # Oracle
                        cursor.execute("""
                            SELECT conid FROM DMS_DBCONDTLS 
                            WHERE conid = :1 AND curflg = 'Y'
                        """, [sqlconid_val])
                    conn_row = cursor.fetchone()
                    if not conn_row:
                        w_msg = f'Invalid or inactive source connection ID: {sqlconid_val}'
                        error(f"Connection ID validation failed: {w_msg}")
                        _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
                    info(f"Connection ID {sqlconid_val} validated successfully")
                except Exception as db_error:
                    error(f"Database error validating connection ID: {str(db_error)}", exc_info=True)
                    raise
            except ValueError as ve:
                w_msg = f'Source connection ID must be numeric: {p_sqlconid}'
                error(f"ValueError validating connection ID: {str(ve)}")
                _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
            except Exception as e:
                error(f"Unexpected error validating connection ID: {str(e)}", exc_info=True)
                raise
        else:
            info(f"No connection ID provided, skipping validation")
        
        # Check if SQL code already exists
        info(f"Checking if SQL code '{p_dwmaprsqlcd}' already exists")
        try:
            dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT maprsqlid, maprsqlcd, maprsql, sqlconid
                    FROM {dms_maprsql_ref}
                    WHERE maprsqlcd = %s
                    AND curflg = 'Y'
                """
                cursor.execute(query, (p_dwmaprsqlcd,))
            else:  # Oracle
                query = """
                    SELECT maprsqlid, maprsqlcd, maprsql, sqlconid
                    FROM DMS_MAPRSQL
                    WHERE maprsqlcd = :1
                    AND curflg = 'Y'
                """
                cursor.execute(query, [p_dwmaprsqlcd])
            row = cursor.fetchone()
            info(f"SQL code lookup result: {'Found existing' if row else 'New SQL code'}")
        except Exception as e:
            error(f"Error checking if SQL code exists: {str(e)}", exc_info=True)
            raise
        
        info(f"Processing row data. Row is: {row}")
        w_return = None
        w_res = 1  # Assume different
        
        if row:
            info(f"Found existing SQL code. Unpacking row data...")
            try:
                w_rec_maprsqlid, w_rec_maprsqlcd, w_rec_maprsql, w_rec_sqlconid = row
                info(f"Unpacked: maprsqlid={w_rec_maprsqlid}, maprsqlcd={w_rec_maprsqlcd}, sqlconid={w_rec_sqlconid}")
                # Compare the SQL text and connection ID
                sql_matches = w_rec_maprsql == p_dwmaprsql
                conn_matches = w_rec_sqlconid == sqlconid_val
                info(f"SQL content match: {sql_matches}, Connection ID match: {conn_matches}")
                if sql_matches and conn_matches:
                    w_res = 0  # Same
                    info(f"SQL and connection ID are the same, no update needed")
                else:
                    info(f"SQL or connection ID differs, will update")
                w_return = w_rec_maprsqlid
            except Exception as e:
                error(f"Error unpacking row data: {str(e)}", exc_info=True)
                raise
        else:
            info(f"No existing SQL code found, will insert new record")
        
        info(f"w_res = {w_res}, will proceed with {'update' if row and w_res != 0 else 'insert' if w_res != 0 else 'no action'}")
        
        if w_res != 0:  # SQL is different or new
            if row:  # Update existing to set curflg = 'N'
                info(f"Updating existing SQL record to set curflg = 'N'")
                try:
                    dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
                    if db_type == "POSTGRESQL":
                        cursor.execute(f"""
                            UPDATE {dms_maprsql_ref}
                            SET curflg = 'N', recupdt = CURRENT_TIMESTAMP
                            WHERE maprsqlcd = %s
                            AND curflg = 'Y'
                        """, (p_dwmaprsqlcd,))
                    else:  # Oracle
                        cursor.execute("""
                            UPDATE DMS_MAPRSQL
                            SET curflg = 'N', recupdt = sysdate
                            WHERE maprsqlcd = :1
                            AND curflg = 'Y'
                        """, [p_dwmaprsqlcd])
                    info(f"Updated existing record successfully")
                except Exception as e:
                    error(f"Error updating existing SQL record: {str(e)}", exc_info=True)
                    _raise_error(w_procnm, '132', w_parm, e)
            
            # Insert new record
            info(f"Preparing to insert new SQL record")
            try:
                # Remove trailing semicolons
                clean_sql = re.sub(r';+$', '', str(p_dwmaprsql).strip())
                info(f"Cleaned SQL (length: {len(clean_sql)}), sqlconid_val: {sqlconid_val}")
                
                # Generate SQL ID using ID provider (supports Oracle/PostgreSQL)
                info(f"Generating next SQL ID from sequence DMS_MAPRSQLSEQ")
                info(f"Cursor type: {type(cursor)}, Connection type: {type(connection)}")
                
                # For PostgreSQL, ensure cursor is in a clean state
                # Create a fresh cursor for ID generation to avoid transaction issues
                try:
                    # Try to use the existing cursor first
                    info(f"Attempting to generate ID with existing cursor...")
                    sql_id = get_next_id(cursor, "DMS_MAPRSQLSEQ")
                    info(f"Generated SQL ID: {sql_id}")
                except Exception as e:
                    error(f"Error generating SQL ID with existing cursor: {str(e)}", exc_info=True)
                    # If it fails, try with a new cursor
                    info(f"Trying with a fresh cursor...")
                    try:
                        fresh_cursor = connection.cursor()
                        sql_id = get_next_id(fresh_cursor, "DMS_MAPRSQLSEQ")
                        fresh_cursor.close()
                        info(f"Generated SQL ID with fresh cursor: {sql_id}")
                    except Exception as e2:
                        error(f"Error generating SQL ID with fresh cursor: {str(e2)}", exc_info=True)
                        raise
                
                info(f"Executing INSERT statement for SQL code: {p_dwmaprsqlcd}, ID: {sql_id}")
                info(f"INSERT parameters: sql_id={sql_id}, sql_code={p_dwmaprsqlcd}, sql_length={len(clean_sql)}, sqlconid={sqlconid_val}")
                try:
                    dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
                    if db_type == "POSTGRESQL":
                        cursor.execute(f"""
                            INSERT INTO {dms_maprsql_ref} (maprsqlid, maprsqlcd, maprsql, sqlconid, reccrdt, recupdt, curflg)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y')
                        """, (sql_id, p_dwmaprsqlcd, clean_sql, sqlconid_val))
                    else:  # Oracle
                        cursor.execute("""
                            INSERT INTO DMS_MAPRSQL (maprsqlid, maprsqlcd, maprsql, sqlconid, reccrdt, recupdt, curflg)
                            VALUES (:1, :2, :3, :4, sysdate, sysdate, 'Y')
                        """, [sql_id, p_dwmaprsqlcd, clean_sql, sqlconid_val])
                    w_return = sql_id
                    info(f"INSERT statement executed successfully. SQL ID: {sql_id}")
                except Exception as insert_error:
                    error(f"INSERT statement failed: {str(insert_error)}", exc_info=True)
                    raise
            except Exception as e:
                error(f"Error inserting SQL record: {str(e)}", exc_info=True)
                _raise_error(w_procnm, '133', w_parm, e)
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
            connection.commit()
            info(f"Committed SQL save for code: {p_dwmaprsqlcd}, ID: {w_return}")
        elif db_type == "ORACLE":
            connection.commit()
            info(f"Committed SQL save for code: {p_dwmaprsqlcd}, ID: {w_return}")
        else:
            # PostgreSQL with autocommit=True - no commit needed, but log it
            info(f"SQL saved with autocommit for code: {p_dwmaprsqlcd}, ID: {w_return}")
        
        info(f"create_update_sql completed successfully. Returning SQL ID: {w_return}")
        return w_return
        
    except PKGDMS_MAPRError as e:
        error(f"PKGDMS_MAPRError in create_update_sql: {w_parm} - {str(e)}")
        raise
    except Exception as e:
        error(f"Unexpected error in create_update_sql: {str(e)}", exc_info=True)
        _raise_error(w_procnm, '134', w_parm, e)
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass

def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
                         p_stflg, p_blkprcrows, p_trgconid=None, p_user=None,
                         p_chkpntstrtgy='AUTO', p_chkpntclnm=None, p_chkpntenbld='Y'):
    """
    Function to create or update mappings, returns mapping ID
    Any change is historised.
    
    Args:
        p_trgconid: Target database connection ID (from DMS_DBCONDTLS). 
                    If None, uses metadata connection.
        p_chkpntstrtgy: Checkpoint strategy ('AUTO', 'KEY', 'PYTHON', 'NONE')
        p_chkpntclnm: Checkpoint column name for KEY strategy (stored as chkpntcolumn in DB)
        p_chkpntenbld: Enable checkpoint ('Y'/'N') (stored as chkpntenabled in DB)
    """
    w_procnm = 'CREATE_UPDATE_MAPPING'
    w_parm = f'Mapref={p_mapref}-{p_mapdesc}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref}-{p_mapdesc} User={p_user}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        
        # Validation
        w_msg = None
        if not p_mapref or p_mapref.strip() == '':
            w_msg = 'Mapping reference not provided.'
        elif _nvl(p_trgtbtyp, 'X') not in ('NRM', 'DIM', 'FCT', 'MRT'):
            w_msg = 'Invalid target table type (valid: NRM,DIM,FCT,MRT).'
        elif _nvl(p_frqcd, 'NA') not in ('NA', 'ID', 'DL', 'WK', 'FN', 'MN', 'HY', 'YR'):
            w_msg = 'Invalid frequency code (Valid: ID,DL,WK,FN,MN,HY,YR).'
        elif _nvl(p_stflg, 'N') not in ('A', 'N'):
            w_msg = 'Invalid status (Valid: A,N).'
        elif _nvl(p_lgvrfyflg, 'N') not in ('Y', 'N'):
            w_msg = 'Invalid verification flag (Valid: Y,N).'
        elif not p_srcsystm:
            w_msg = 'Source system not provided.'
        elif not p_trgschm:
            w_msg = 'Target Schema name not provided.'
        elif ' ' in p_trgschm:
            w_msg = 'Target schema name must not contain blank spaces'
        elif re.search(r'[^A-Za-z0-9_]', p_trgschm):
            w_msg = 'Special characters not allowed to form target schema name.'
        elif re.match(r'^\d', p_trgschm):
            w_msg = 'Target schema name must not start with number.'
        elif ' ' in p_trgtbnm:
            w_msg = 'Target table name must not contain blank spaces'
        elif re.search(r'[^A-Za-z0-9_]', p_trgtbnm):
            w_msg = 'Special characters not allowed to form target table name.'
        elif re.match(r'^\d', p_trgtbnm):
            w_msg = 'Target table must not start with number.'
        elif (p_lgvrfyflg and not p_lgvrfydt) or (not p_lgvrfyflg and p_lgvrfydt):
            w_msg = 'Both logic verification flag and date must be provide or both must be blank.'
        
        # Validate p_blkprcrows (may come as string from frontend)
        if not w_msg and p_blkprcrows is not None:
            try:
                blkprcrows_int = int(p_blkprcrows)
                if blkprcrows_int < 0:
                    w_msg = 'The number of Bulk Processing Rows cannot be negative.'
            except (ValueError, TypeError):
                w_msg = f'Invalid Bulk Processing Rows value "{p_blkprcrows}" - must be numeric.'
        
        # Validate p_trgconid (target connection ID) if provided
        if not w_msg and p_trgconid is not None:
            try:
                trgconid_int = int(p_trgconid)
                # Validate connection exists and is active
                dms_dbcondtls_ref = _get_table_ref(cursor, db_type, 'DMS_DBCONDTLS')
                if db_type == "POSTGRESQL":
                    cursor.execute(f"""
                        SELECT conid FROM {dms_dbcondtls_ref} 
                        WHERE conid = %s AND curflg = 'Y'
                    """, (trgconid_int,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT conid FROM DMS_DBCONDTLS 
                        WHERE conid = :1 AND curflg = 'Y'
                    """, [trgconid_int])
                if not cursor.fetchone():
                    w_msg = f'Invalid target connection ID "{p_trgconid}". Connection not found or inactive.'
            except (ValueError, TypeError):
                w_msg = f'Invalid target connection ID "{p_trgconid}" - must be numeric.'
        
        # Validate checkpoint parameters
        if not w_msg and p_chkpntstrtgy not in ('AUTO', 'KEY', 'PYTHON', 'NONE'):
            w_msg = 'Invalid checkpoint strategy (Valid: AUTO, KEY, PYTHON, NONE).'
        if not w_msg and p_chkpntenbld not in ('Y', 'N'):
            w_msg = 'Invalid checkpoint enabled flag (Valid: Y, N).'
        
        if w_msg:
            _raise_error(w_procnm, '103', f'{w_parm}::{w_msg}')
        
        # Check if mapping already exists
        # First, check if checkpoint columns exist in the table
        checkpoint_columns_exist = False
        try:
            if db_type == "POSTGRESQL":
                # PostgreSQL: table and column names are case-insensitive when unquoted
                # Check using LOWER() for case-insensitive comparison
                check_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE LOWER(table_name) = LOWER('DMS_MAPR') 
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
        
        # Get table reference for PostgreSQL (handles case sensitivity)
        dms_mapr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPR')
        
        # Build query based on whether checkpoint columns exist
        if checkpoint_columns_exist:
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
                           srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid,
                           chkpntstrtgy, chkpntclnm, chkpntenbld
                    FROM {dms_mapr_ref}
                    WHERE mapref = %s
                    AND curflg = 'Y'
                """
                cursor.execute(query, (p_mapref,))
            else:  # Oracle
                query = """
                    SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
                           srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid,
                           CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
                    FROM DMS_MAPR
                    WHERE mapref = :1
                    AND curflg = 'Y'
                """
                cursor.execute(query, [p_mapref])
        else:
            # Query without checkpoint columns
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
                           srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid
                    FROM {dms_mapr_ref}
                    WHERE mapref = %s
                    AND curflg = 'Y'
                """
                cursor.execute(query, (p_mapref,))
            else:  # Oracle
                query = """
                    SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
                           srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid
                    FROM DMS_MAPR
                    WHERE mapref = :1
                    AND curflg = 'Y'
                """
                cursor.execute(query, [p_mapref])
        row = cursor.fetchone()
        
        w_chg = 'Y'
        w_mapid = None
        
        if row:
            # Build record dictionary based on whether checkpoint columns exist
            w_mapr_rec = {
                'mapid': row[0], 'mapref': row[1], 'mapdesc': row[2],
                'trgschm': row[3], 'trgtbtyp': row[4], 'trgtbnm': row[5],
                'frqcd': row[6], 'srcsystm': row[7], 'lgvrfyflg': row[8],
                'lgvrfydt': row[9], 'stflg': row[10], 'blkprcrows': row[11],
                'trgconid': row[12]
            }
            
            # Add checkpoint columns if they exist
            if checkpoint_columns_exist and len(row) > 13:
                w_mapr_rec['chkpntstrtgy'] = row[13] if len(row) > 13 else 'AUTO'
                w_mapr_rec['chkpntclnm'] = row[14] if len(row) > 14 else None
                w_mapr_rec['chkpntenbld'] = row[15] if len(row) > 15 else 'Y'
            else:
                # Use defaults if columns don't exist
                w_mapr_rec['chkpntstrtgy'] = 'AUTO'
                w_mapr_rec['chkpntclnm'] = None
                w_mapr_rec['chkpntenbld'] = 'Y'
            
            # Check if there are any changes (convert numeric fields to int for comparison)
            p_blkprcrows_int = int(p_blkprcrows) if p_blkprcrows is not None else 0
            p_trgconid_int = int(p_trgconid) if p_trgconid is not None else None
            
            # Normalize checkpoint column name for comparison (handle None vs empty string)
            existing_chkpntclnm = w_mapr_rec['chkpntclnm'] if w_mapr_rec['chkpntclnm'] else None
            new_chkpntclnm = p_chkpntclnm if p_chkpntclnm and p_chkpntclnm.strip() else None
            
            # Compare all fields including checkpoint fields
            if (w_mapr_rec['mapdesc'] == p_mapdesc and
                w_mapr_rec['trgschm'] == p_trgschm and
                w_mapr_rec['trgtbtyp'] == p_trgtbtyp and
                w_mapr_rec['trgtbnm'] == p_trgtbnm and
                w_mapr_rec['frqcd'] == p_frqcd and
                w_mapr_rec['srcsystm'] == p_srcsystm and
                _nvl(w_mapr_rec['blkprcrows'], 0) == p_blkprcrows_int and
                w_mapr_rec['trgconid'] == p_trgconid_int and
                _nvl(w_mapr_rec['chkpntstrtgy'], 'AUTO') == _nvl(p_chkpntstrtgy, 'AUTO') and
                existing_chkpntclnm == new_chkpntclnm and
                _nvl(w_mapr_rec['chkpntenbld'], 'Y') == _nvl(p_chkpntenbld, 'Y')):
                # No changes
                w_chg = 'N'
                w_mapid = w_mapr_rec['mapid']
            
            if w_chg == 'Y':
                # Mark old record as not current
                try:
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            UPDATE DMS_MAPR
                            SET curflg = 'N', recupdt = CURRENT_TIMESTAMP, uptdby = %s
                            WHERE mapid = %s
                        """, (G_USER, w_mapr_rec['mapid']))
                    else:  # Oracle
                        cursor.execute("""
                            UPDATE DMS_MAPR
                            SET curflg = 'N', recupdt = sysdate, uptdby = :1
                            WHERE mapid = :2
                        """, [G_USER, w_mapr_rec['mapid']])
                except Exception as e:
                    _raise_error(w_procnm, '101', f'{w_parm} mapid={w_mapr_rec["mapid"]}', e)
        
        # Insert new record if changes detected
        if w_chg == 'Y':
            try:
                # Generate mapping ID using ID provider (supports Oracle/PostgreSQL)
                map_id = get_next_id(cursor, "DMS_MAPRSEQ")
                
                # Ensure numeric fields are integers (may come as strings from frontend)
                blkprcrows_val = int(p_blkprcrows) if p_blkprcrows is not None else None
                trgconid_val = int(p_trgconid) if p_trgconid is not None else None
                
                # Normalize empty strings to None for date fields (PostgreSQL doesn't accept empty strings for timestamps)
                lgvrfydt_val = None if (p_lgvrfydt is None or p_lgvrfydt == '') else p_lgvrfydt
                
                if checkpoint_columns_exist:
                    # Insert with checkpoint columns
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            INSERT INTO DMS_MAPR 
                            (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                             lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, trgconid, crtdby, uptdby,
                             chkpntstrtgy, chkpntclnm, chkpntenbld)
                            VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s,
                             %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s, %s, %s, %s,
                             %s, %s, %s)
                        """, (map_id, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
                              _nvl(p_lgvrfyflg, 'N'), lgvrfydt_val, _nvl(p_stflg, 'N'), blkprcrows_val,
                              trgconid_val, G_USER, G_USER, _nvl(p_chkpntstrtgy, 'AUTO'), 
                              p_chkpntclnm, _nvl(p_chkpntenbld, 'Y')))
                    else:  # Oracle
                        cursor.execute("""
                            INSERT INTO DMS_MAPR 
                            (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                             lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, trgconid, crtdby, uptdby,
                             CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD)
                            VALUES 
                            (:1, :2, :3, :4, :5, :6, :7, :8,
                             :9, :10, :11, sysdate, sysdate, 'Y', :12, :13, :14, :15,
                             :16, :17, :18)
                        """, [map_id, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
                              _nvl(p_lgvrfyflg, 'N'), lgvrfydt_val, _nvl(p_stflg, 'N'), blkprcrows_val,
                              trgconid_val, G_USER, G_USER, _nvl(p_chkpntstrtgy, 'AUTO'), 
                              p_chkpntclnm, _nvl(p_chkpntenbld, 'Y')])
                else:
                    # Insert without checkpoint columns
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            INSERT INTO DMS_MAPR 
                            (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                             lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, trgconid, crtdby, uptdby)
                            VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s,
                             %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s, %s, %s, %s)
                        """, (map_id, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
                              _nvl(p_lgvrfyflg, 'N'), lgvrfydt_val, _nvl(p_stflg, 'N'), blkprcrows_val,
                              trgconid_val, G_USER, G_USER))
                    else:  # Oracle
                        cursor.execute("""
                            INSERT INTO DMS_MAPR 
                            (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                             lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, trgconid, crtdby, uptdby)
                            VALUES 
                            (:1, :2, :3, :4, :5, :6, :7, :8,
                             :9, :10, :11, sysdate, sysdate, 'Y', :12, :13, :14, :15)
                        """, [map_id, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
                              _nvl(p_lgvrfyflg, 'N'), lgvrfydt_val, _nvl(p_stflg, 'N'), blkprcrows_val,
                              trgconid_val, G_USER, G_USER])
                w_mapid = map_id
            except Exception as e:
                _raise_error(w_procnm, '102', w_parm, e)
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
            connection.commit()
        elif db_type == "ORACLE":
            connection.commit()
        
        return w_mapid
        
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '103', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def create_update_mapping_detail(connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg,
                                 p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm,
                                 p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp,
                                 p_lgvrfyflg, p_lgvrfydt, p_user=None):
    """
    Function to create or update mapping details, returns mapping detail ID
    Any change is historised.
    """
    w_procnm = 'CREATE_UPDATE_MAPPING_DETAIL'
    w_parm = f'Mapref={p_mapref} Trgcol={p_trgclnm}'[:400]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref}-{p_trgclnm} User={p_user}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        
        # Validation
        w_msg = None
        if not p_mapref:
            w_msg = 'Mapping reference not provided.'
        elif not p_trgclnm:
            w_msg = 'Target column name not provided.'
        elif ' ' in p_trgclnm:
            w_msg = 'Target column name must not contain blank spaces'
        elif re.search(r'[^A-Za-z0-9_]', p_trgclnm):
            w_msg = 'Special characters not allowed to form target column name.'
        elif re.match(r'^\d', p_trgclnm):
            w_msg = 'Target column name must not start with number.'
        elif not p_trgcldtyp:
            w_msg = 'Target column data type is not provided.'
        elif _nvl(p_trgkeyflg, 'N') not in ('Y', 'N'):
            w_msg = 'Invalid value for Key flag (valid: Y or blank).'
        elif p_trgkeyflg == 'Y' and not p_trgkeyseq:
            w_msg = 'Key sequence must be provided for Primary key columns.'
        elif not p_maplogic:
            w_msg = 'Mapping logic must be provided.'
        elif p_maplogic and (not p_keyclnm or not p_valclnm):
            w_msg = 'Key column and value column must be provided.'
        
        # Convert and validate numeric fields (they may come as strings from frontend)
        if not w_msg:
            try:
                # Validate p_scdtyp
                scdtyp_int = int(_nvl(p_scdtyp, 1))
                if scdtyp_int not in (1, 2, 3):
                    w_msg = 'Invalid values for SCD type (valid: 1, 2, or 3).'
            except (ValueError, TypeError):
                w_msg = f'Invalid SCD type value "{p_scdtyp}" - must be numeric: 1, 2, or 3.'
        
        if not w_msg and p_trgkeyseq is not None:
            try:
                int(p_trgkeyseq)
            except (ValueError, TypeError):
                w_msg = f'Invalid key sequence value "{p_trgkeyseq}" - must be numeric.'
        
        if not w_msg and p_excseq is not None:
            try:
                int(p_excseq)
            except (ValueError, TypeError):
                w_msg = f'Invalid execution sequence value "{p_excseq}" - must be numeric.'
        
        if not w_msg and ((p_lgvrfyflg and not p_lgvrfydt) or (not p_lgvrfyflg and p_lgvrfydt)):
            w_msg = 'Both logic verification flag and date must be provide or both must be blank.'
        
        # Check if datatype is valid
        if not w_msg:
            try:
                # Trim whitespace from datatype value
                p_trgcldtyp_trimmed = p_trgcldtyp.strip() if p_trgcldtyp else p_trgcldtyp
                
                # Use case-insensitive comparison for PostgreSQL (case-sensitive for Oracle)
                if db_type == "POSTGRESQL":
                    # PostgreSQL: use uppercase column names to match helper_functions.py, UPPER for case-insensitive comparison
                    dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
                    info(f"Validating datatype: prtyp='Datatype', prcd='{p_trgcldtyp_trimmed}' (PostgreSQL)")
                    cursor.execute(f"""
                        SELECT PRVAL
                        FROM {dms_params_ref}
                        WHERE UPPER(TRIM(PRTYP)) = UPPER(TRIM(%s))
                        AND UPPER(TRIM(PRCD)) = UPPER(TRIM(%s))
                    """, ('Datatype', p_trgcldtyp_trimmed))
                else:  # Oracle
                    info(f"Validating datatype: prtyp='Datatype', prcd='{p_trgcldtyp}' (Oracle)")
                    cursor.execute("""
                        SELECT prval
                        FROM DMS_PARAMS
                        WHERE prtyp = :1
                        AND prcd = :2
                    """, ['Datatype', p_trgcldtyp])
                dtyp_row = cursor.fetchone()
                
                if dtyp_row:
                    info(f"Datatype validation successful: {p_trgcldtyp} found in DMS_PARAMS")
                else:
                    # Log what datatypes are actually available for debugging
                    dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
                    if db_type == "POSTGRESQL":
                        cursor.execute(f"""
                            SELECT PRCD, PRVAL
                            FROM {dms_params_ref}
                            WHERE UPPER(PRTYP) = UPPER(%s)
                            ORDER BY PRCD
                        """, ('Datatype',))
                    else:
                        cursor.execute("""
                            SELECT prcd, prval
                            FROM DMS_PARAMS
                            WHERE prtyp = :1
                            ORDER BY prcd
                        """, ['Datatype'])
                    available_dtypes = cursor.fetchall()
                    available_list = ', '.join([str(row[0]) for row in available_dtypes]) if available_dtypes else 'none'
                    warning(f"Datatype '{p_trgcldtyp}' not found. Available datatypes: {available_list}")
                    
                    # Suggest similar datatypes if the requested one is close
                    suggested = []
                    requested_lower = p_trgcldtyp.lower().strip()
                    for dtype_row in available_dtypes:
                        dtype = str(dtype_row[0])
                        dtype_lower = dtype.lower()
                        # Check for common variations
                        if (requested_lower in dtype_lower or 
                            dtype_lower in requested_lower or
                            (requested_lower == 'date' and 'timestamp' in dtype_lower) or
                            (requested_lower == 'date' and 'time' in dtype_lower)):
                            suggested.append(dtype)
                    
                    if suggested:
                        suggestion_text = f'\nDid you mean: {", ".join(suggested)}?'
                    else:
                        suggestion_text = f'\nAvailable datatypes: {available_list}'
                    
                    w_msg = f'The datatype "{p_trgcldtyp}" for {p_trgclnm} is invalid.{suggestion_text}\nPlease verify parameters for "Datatype".'
            except Exception as e:
                error(f"Error validating datatype '{p_trgcldtyp}': {str(e)}", exc_info=True)
                w_msg = f'Error validating datatype {p_trgcldtyp} for {p_trgclnm}: {str(e)}'
        
        if w_msg:
            _raise_error(w_procnm, '107', f'{w_parm}::{w_msg}')
        
        # Check if maplogic is a SQL code reference (length <= 100)
        w_msql_rec = None
        if p_maplogic and len(p_maplogic) <= 100:
            try:
                dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
                if db_type == "POSTGRESQL":
                    cursor.execute(f"""
                        SELECT maprsqlid, maprsqlcd
                        FROM {dms_maprsql_ref}
                        WHERE maprsqlcd = %s
                        AND curflg = 'Y'
                    """, (p_maplogic,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT maprsqlid, maprsqlcd
                        FROM DMS_MAPRSQL
                        WHERE maprsqlcd = :1
                        AND curflg = 'Y'
                    """, [p_maplogic])
                msql_row = cursor.fetchone()
                if msql_row:
                    w_msql_rec = {'maprsqlid': msql_row[0], 'maprsqlcd': msql_row[1]}
            except Exception as e:
                _raise_error(w_procnm, '135', w_parm, e)
        
        # Check if mapping reference exists
        try:
            dms_mapr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPR')
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    SELECT mapref, mapid
                    FROM {dms_mapr_ref}
                    WHERE mapref = %s
                    AND curflg = 'Y'
                """, (p_mapref,))
            else:  # Oracle
                cursor.execute("""
                    SELECT mapref, mapid
                    FROM DMS_MAPR
                    WHERE mapref = :1
                    AND curflg = 'Y'
                """, [p_mapref])
            mapr_row = cursor.fetchone()
            
            if not mapr_row:
                w_msg = 'Invalid mapping reference.'
                _raise_error(w_procnm, '107', f'{w_parm}::{w_msg}')
        except PKGDMS_MAPRError:
            raise
        except Exception as e:
            _raise_error(w_procnm, '136', w_parm, e)
        
        # Check if mapping detail already exists
        if db_type == "POSTGRESQL":
            dms_maprdtl_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRDTL')
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    SELECT mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq,
                           trgcldesc, maplogic, keyclnm, valclnm, mapcmbcd, excseq, scdtyp
                    FROM {dms_maprdtl_ref}
                    WHERE mapref = %s
                    AND trgclnm = %s
                    AND curflg = 'Y'
                """, (p_mapref, p_trgclnm))
            else:
                cursor.execute("""
                    SELECT mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq,
                           trgcldesc, maplogic, keyclnm, valclnm, mapcmbcd, excseq, scdtyp
                    FROM DMS_MAPRDTL
                    WHERE mapref = :1
                    AND trgclnm = :2
                    AND curflg = 'Y'
                """, [p_mapref, p_trgclnm])
        else:  # Oracle
            cursor.execute("""
                SELECT mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq,
                       trgcldesc, maplogic, keyclnm, valclnm, mapcmbcd, excseq, scdtyp
                FROM DMS_MAPRDTL
                WHERE mapref = :1
                AND trgclnm = :2
                AND curflg = 'Y'
            """, [p_mapref, p_trgclnm])
        row = cursor.fetchone()
        
        w_chg = 'Y'
        w_mapdtlid = None
        
        if row:
            w_maprdtl_rec = {
                'mapdtlid': row[0], 'mapref': row[1], 'trgclnm': row[2],
                'trgcldtyp': row[3], 'trgkeyflg': row[4], 'trgkeyseq': row[5],
                'trgcldesc': row[6], 'maplogic': row[7], 'keyclnm': row[8],
                'valclnm': row[9], 'mapcmbcd': row[10], 'excseq': row[11],
                'scdtyp': row[12]
            }
            
            # Check if there are any changes (convert numeric fields to int for comparison)
            p_trgkeyseq_int = int(p_trgkeyseq) if p_trgkeyseq is not None else None
            p_excseq_int = int(p_excseq) if p_excseq is not None else None
            p_scdtyp_int = int(p_scdtyp) if p_scdtyp is not None else None
            
            if (w_maprdtl_rec['mapref'] == p_mapref and
                w_maprdtl_rec['trgclnm'] == p_trgclnm and
                w_maprdtl_rec['trgcldtyp'] == p_trgcldtyp and
                _nvl(w_maprdtl_rec['trgkeyflg'], 'N') == _nvl(p_trgkeyflg, 'N') and
                _nvl(w_maprdtl_rec['trgkeyseq'], -1) == _nvl(p_trgkeyseq_int, -1) and
                w_maprdtl_rec['trgcldesc'] == p_trgcldesc and
                w_maprdtl_rec['maplogic'] == p_maplogic and
                w_maprdtl_rec['keyclnm'] == p_keyclnm and
                w_maprdtl_rec['valclnm'] == p_valclnm and
                w_maprdtl_rec['mapcmbcd'] == p_mapcmbcd and
                w_maprdtl_rec['excseq'] == p_excseq_int and
                w_maprdtl_rec['scdtyp'] == p_scdtyp_int):
                # No changes
                w_chg = 'N'
                w_mapdtlid = w_maprdtl_rec['mapdtlid']
            
            if w_chg == 'Y':
                # Mark old record as not current
                try:
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            UPDATE DMS_MAPRDTL
                            SET curflg = 'N', recupdt = CURRENT_TIMESTAMP, uptdby = %s
                            WHERE mapref = %s
                            AND mapdtlid = %s
                            AND curflg = 'Y'
                        """, (G_USER, w_maprdtl_rec['mapref'], w_maprdtl_rec['mapdtlid']))
                    else:  # Oracle
                        cursor.execute("""
                            UPDATE DMS_MAPRDTL
                            SET curflg = 'N', recupdt = sysdate, uptdby = :1
                            WHERE mapref = :2
                            AND mapdtlid = :3
                            AND curflg = 'Y'
                        """, [G_USER, w_maprdtl_rec['mapref'], w_maprdtl_rec['mapdtlid']])
                except Exception as e:
                    _raise_error(w_procnm, '105', f'{w_parm} Mapref={w_maprdtl_rec["mapref"]} Trgclnm={w_maprdtl_rec["trgclnm"]}', e)
        
        # Insert new record if changes detected
        if w_chg == 'Y':
            try:
                maprsqlcd_val = w_msql_rec['maprsqlcd'] if w_msql_rec else None
                # Generate mapping detail ID using ID provider (supports Oracle/PostgreSQL)
                mapdtlid = get_next_id(cursor, "DMS_MAPRDTLSEQ")
                
                # Ensure numeric fields are integers (they may come as strings from frontend)
                trgkeyseq_val = int(p_trgkeyseq) if p_trgkeyseq is not None else None
                excseq_val = int(p_excseq) if p_excseq is not None else None
                scdtyp_val = int(_nvl(p_scdtyp, 1))
                
                # Normalize empty strings to None for date fields (PostgreSQL doesn't accept empty strings for timestamps)
                lgvrfydt_val = None if (p_lgvrfydt is None or p_lgvrfydt == '') else p_lgvrfydt
                
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        INSERT INTO DMS_MAPRDTL
                        (mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, trgcldesc,
                         maplogic, maprsqlcd, keyclnm, valclnm, mapcmbcd, excseq, scdtyp, lgvrfyflg,
                         lgvrfydt, reccrdt, recupdt, curflg, crtdby, uptdby)
                        VALUES
                        (%s, %s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s, %s, %s,
                         %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s, %s)
                    """, (mapdtlid, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, trgkeyseq_val, p_trgcldesc,
                          p_maplogic, maprsqlcd_val, p_keyclnm, p_valclnm, p_mapcmbcd, excseq_val,
                          scdtyp_val, p_lgvrfyflg, lgvrfydt_val, G_USER, G_USER))
                else:  # Oracle
                    cursor.execute("""
                        INSERT INTO DMS_MAPRDTL
                        (mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, trgcldesc,
                         maplogic, maprsqlcd, keyclnm, valclnm, mapcmbcd, excseq, scdtyp, lgvrfyflg,
                         lgvrfydt, reccrdt, recupdt, curflg, crtdby, uptdby)
                        VALUES
                        (:1, :2, :3, :4, :5, :6, :7,
                         :8, :9, :10, :11, :12, :13, :14,
                         :15, :16, sysdate, sysdate, 'Y', :17, :18)
                    """, [mapdtlid, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, trgkeyseq_val, p_trgcldesc,
                          p_maplogic, maprsqlcd_val, p_keyclnm, p_valclnm, p_mapcmbcd, excseq_val,
                          scdtyp_val, p_lgvrfyflg, lgvrfydt_val, G_USER, G_USER])
                w_mapdtlid = mapdtlid
            except Exception as e:
                _raise_error(w_procnm, '106', w_parm, e)
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
            connection.commit()
        elif db_type == "ORACLE":
            connection.commit()
        
        return w_mapdtlid
        
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '107', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def _validate_sql(connection, p_logic, p_keyclnm, p_valclnm, p_flg='Y'):
    """
    Private procedure to validate SQL
    Returns: error message (None if valid)
    """
    w_procnm = 'VALIDATE_SQL'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}'[:400]
    
    p_error = None
    w_cursor = None
    
    try:
        # Detect database type
        db_type = _detect_db_type(connection)
        
        if p_flg == 'Y':
            if not p_keyclnm:
                return 'Key column(s) not provided.'
            if not p_valclnm:
                return 'Value column(s) not provided.'
        
        if not p_logic or len(str(p_logic).strip()) == 0:
            return 'SQL provided is empty.'
        
        # Build SQL to validate
        if p_flg == 'Y':
            if db_type == "POSTGRESQL":
                w_sql = f'select {p_keyclnm},{p_valclnm} from ({p_logic}) sql1 limit 1'
            else:  # Oracle
                w_sql = f'select {p_keyclnm},{p_valclnm} from ({p_logic}) sql1 where rownum = 1'
        else:
            w_sql = str(p_logic)
        
        # Replace DWT_PARAM placeholders with NULL for validation
        w_sql = re.sub(r'DWT_PARAM\d+', 'NULL', w_sql, flags=re.IGNORECASE)
        w_sql = re.sub(r';+$', '', w_sql)  # Remove trailing semicolons
        
        # Try to validate the SQL
        cursor = connection.cursor()
        try:
            if db_type == "POSTGRESQL":
                # PostgreSQL: Use EXPLAIN to validate SQL syntax without executing
                explain_sql = f"EXPLAIN {w_sql}"
                info(f"Validating SQL with PostgreSQL EXPLAIN: {explain_sql[:200]}")
                cursor.execute(explain_sql)
            else:  # Oracle
                # Oracle: Try EXPLAIN PLAN first, fallback to parse() if needed
                try:
                    explain_sql = f"EXPLAIN PLAN FOR {w_sql}"
                    info(f"Validating SQL with Oracle EXPLAIN PLAN: {explain_sql[:200]}")
                    cursor.execute(explain_sql)
                    # EXPLAIN PLAN creates entries in PLAN_TABLE, we can ignore that
                    # No commit needed for validation
                except Exception as explain_error:
                    # Fallback to parse() method if EXPLAIN PLAN fails
                    info(f"EXPLAIN PLAN failed, trying parse() method: {str(explain_error)[:200]}")
                    try:
                        cursor.parse(w_sql)
                    except Exception as parse_error:
                        # If both fail, use the original EXPLAIN PLAN error
                        raise explain_error
        except Exception as e:
            p_error = str(e)
            error(f"SQL validation failed on {db_type}: {p_error}")
        finally:
            cursor.close()
        
        return p_error
        
    except Exception as e:
        _raise_error(w_procnm, '138', w_parm, e)

def validate_sql(connection, p_logic):
    """
    Function to validate SQL
    Returns: 'Y' if valid, 'N' if invalid
    """
    w_procnm = 'VALIDATE_SQL'
    w_parm = 'SQL Validate with Clob.'
    
    try:
        # Log database type for debugging
        db_type = _detect_db_type(connection)
        info(f"Validating SQL on {db_type} connection")
        
        w_err = _validate_sql(connection, p_logic, None, None, 'N')
        
        if w_err:
            error(f"SQL validation error on {db_type}: {w_err}")
            return w_err  # Return the actual error message instead of just 'N'
        else:
            return 'Y'
    except Exception as e:
        error(f"Exception during SQL validation: {str(e)}")
        _raise_error(w_procnm, '139', w_parm, e)

def validate_logic(connection, p_logic, p_keyclnm, p_valclnm):
    """
    Function to validate mapping logic
    Returns: 'Y' if valid, 'N' if invalid
    """
    w_procnm = 'VALIDATE_LOGIC'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        
        # Check if this is a SQL code reference
        # Note: This queries the metadata database, so we need metadata connection
        # But this function receives the target connection. This might need refactoring.
        # For now, we'll try to query using the provided connection (assuming it can access metadata)
        w_rec = None
        if p_logic and len(p_logic) <= 100:
            dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    SELECT maprsqlcd, maprsql
                    FROM {dms_maprsql_ref}
                    WHERE maprsqlcd = %s
                    AND curflg = 'Y'
                """, (p_logic[:100],))
            else:  # Oracle
                cursor.execute("""
                    SELECT maprsqlcd, maprsql
                    FROM DMS_MAPRSQL
                    WHERE maprsqlcd = :1
                    AND curflg = 'Y'
                """, [p_logic[:100]])
            row = cursor.fetchone()
            if row:
                w_rec = {'maprsqlcd': row[0], 'maprsql': row[1]}
        
        # Get the actual SQL logic
        if w_rec:
            w_logic = w_rec['maprsql']
        else:
            w_logic = p_logic
        
        # Validate the SQL
        w_error = _validate_sql(connection, w_logic, p_keyclnm, p_valclnm, 'Y')
        
        if w_error:
            return 'N'
        else:
            return 'Y'
    
    except Exception as e:
        _raise_error(w_procnm, '109', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_logic2(metadata_connection, p_logic, p_keyclnm, p_valclnm, target_connection=None):
    """
    Function to validate mapping logic with error output
    Args:
        metadata_connection: Connection to metadata database (for querying DMS_MAPRSQL)
        p_logic: SQL logic or SQL code reference
        p_keyclnm: Key column name
        p_valclnm: Value column name
        target_connection: Connection to target database (for SQL validation). If None, uses metadata_connection.
    Returns: (is_valid, error_message)
    """
    w_procnm = 'VALIDATE_LOGIC2'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
    
    # Use target_connection for SQL validation if provided, otherwise use metadata_connection
    sql_validation_connection = target_connection if target_connection else metadata_connection
    
    cursor = None
    try:
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        
        # Check if this is a SQL code reference (query metadata database)
        w_rec = None
        if p_logic and len(p_logic) <= 100:
            dms_maprsql_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRSQL')
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    SELECT maprsqlcd, maprsql
                    FROM {dms_maprsql_ref}
                    WHERE maprsqlcd = %s
                    AND curflg = 'Y'
                """, (p_logic[:100],))
            else:  # Oracle
                cursor.execute("""
                    SELECT maprsqlcd, maprsql
                    FROM DMS_MAPRSQL
                    WHERE maprsqlcd = :1
                    AND curflg = 'Y'
                """, [p_logic[:100]])
            row = cursor.fetchone()
            if row:
                w_rec = {'maprsqlcd': row[0], 'maprsql': row[1]}
        
        # Get the actual SQL logic
        if w_rec:
            w_logic = w_rec['maprsql']
        else:
            w_logic = p_logic
        
        # Validate the SQL using target_connection (for executing SQL against source/target tables)
        # Log which connection is being used for SQL validation
        validation_db_type = _detect_db_type(sql_validation_connection)
        info(f"validate_logic2: Using {validation_db_type} connection for SQL validation (target_connection provided: {target_connection is not None})")
        p_err = _validate_sql(sql_validation_connection, w_logic, p_keyclnm, p_valclnm, 'Y')
        
        if p_err:
            return 'N', p_err
        else:
            return 'Y', None
    
    except Exception as e:
        _raise_error(w_procnm, '110', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_logic_for_mapref(metadata_connection, p_mapref, p_user=None, target_connection=None):
    """
    Function to validate all mapping logic for a mapping reference
    Args:
        metadata_connection: Connection to metadata database (for querying DMS_* tables)
        p_mapref: Mapping reference
        p_user: User ID (optional)
        target_connection: Connection to target database (for SQL validation). If None, uses metadata_connection.
    Returns: 'Y' if all valid, 'N' if any invalid
    """
    w_procnm = 'VALIDATE_LOGIC'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref} User={p_user}'[:200]
    
    # Use target_connection for SQL validation if provided, otherwise use metadata_connection
    sql_validation_connection = target_connection if target_connection else metadata_connection
    info(f"validate_logic_for_mapref: target_connection provided: {target_connection is not None}, will use {'target' if target_connection else 'metadata'} connection for SQL validation")
    
    cursor = None
    try:
        cursor = metadata_connection.cursor()
        
        # Detect database type for parameter binding
        db_type = _detect_db_type(cursor)
        
        # Get all mapping details
        if db_type == "POSTGRESQL":
            dms_mapr_ref = _get_table_ref(cursor, db_type, 'DMS_MAPR')
            dms_maprdtl_ref = _get_table_ref(cursor, db_type, 'DMS_MAPRDTL')
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    SELECT m.mapref, md.mapdtlid, m.trgtbnm, md.trgclnm,
                           md.keyclnm, md.valclnm, md.maplogic
                    FROM {dms_mapr_ref} m, {dms_maprdtl_ref} md
                    WHERE m.mapref = %s
                    AND m.curflg = 'Y'
                    AND md.mapref = m.mapref
                    AND md.curflg = 'Y'
                """, (p_mapref,))
            else:
                cursor.execute("""
                    SELECT m.mapref, md.mapdtlid, m.trgtbnm, md.trgclnm,
                           md.keyclnm, md.valclnm, md.maplogic
                    FROM DMS_MAPR m, DMS_MAPRDTL md
                    WHERE m.mapref = :1
                    AND m.curflg = 'Y'
                    AND md.mapref = m.mapref
                    AND md.curflg = 'Y'
                """, [p_mapref])
        else:  # Oracle
            cursor.execute("""
                SELECT m.mapref, md.mapdtlid, m.trgtbnm, md.trgclnm,
                       md.keyclnm, md.valclnm, md.maplogic
                FROM DMS_MAPR m, DMS_MAPRDTL md
                WHERE m.mapref = :1
                AND m.curflg = 'Y'
                AND md.mapref = m.mapref
                AND md.curflg = 'Y'
            """, [p_mapref])
        
        rows = cursor.fetchall()
        w_return = 'Y'
        
        for row in rows:
            mapref, mapdtlid, trgtbnm, trgclnm, keyclnm, valclnm, maplogic = row
            
            w_pm = f'TB:{trgtbnm}-TC:{trgclnm}:Key:{keyclnm}-Val:{valclnm}-{maplogic}'[:400]
            
            try:
                # Use target_connection for SQL validation, metadata_connection for metadata queries
                w_res, w_err = validate_logic2(metadata_connection, maplogic, keyclnm, valclnm, sql_validation_connection)
                
                if w_res == 'N' and w_err:
                    # Insert error record
                    try:
                        # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                        err_id = get_next_id(cursor, "DMS_MAPERRSEQ")
                        if db_type == "POSTGRESQL":
                            cursor.execute("""
                                INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                                VALUES (%s, %s, %s, %s, 'ERR', %s, CURRENT_TIMESTAMP)
                            """, (err_id, mapdtlid, mapref, maplogic, w_err))
                        else:  # Oracle
                            cursor.execute("""
                                INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                                VALUES (:1, :2, :3, :4, 'ERR', :5, sysdate)
                            """, [err_id, mapdtlid, mapref, maplogic, w_err])
                    except Exception as e:
                        _raise_error(w_procnm, '111', w_pm, e)
                
                if w_return == 'Y':
                    w_return = w_res
                
                # Update mapping detail with verification result
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        UPDATE DMS_MAPRDTL
                        SET lgvrfydt = CURRENT_TIMESTAMP, lgvrfyflg = %s
                        WHERE mapref = %s
                        AND mapdtlid = %s
                        AND curflg = 'Y'
                    """, (w_res, mapref, mapdtlid))
                else:  # Oracle
                    cursor.execute("""
                        UPDATE DMS_MAPRDTL
                        SET lgvrfydt = sysdate, lgvrfyflg = :1
                        WHERE mapref = :2
                        AND mapdtlid = :3
                        AND curflg = 'Y'
                    """, [w_res, mapref, mapdtlid])
                
            except Exception as e:
                _raise_error(w_procnm, '112', w_pm, e)
        
        # Additional validation: Check for duplicate value columns within mapping code
        if w_return == 'Y':
            if db_type == "POSTGRESQL":
                cursor.execute("""
                    SELECT valclnm, mapcmbcd, count(*) cnt
                    FROM DMS_MAPRDTL
                    WHERE curflg = 'Y'
                    AND mapref = %s
                    GROUP BY valclnm, mapcmbcd
                    HAVING count(*) > 1
                """, (p_mapref,))
            else:  # Oracle
                cursor.execute("""
                    SELECT valclnm, mapcmbcd, count(*) cnt
                    FROM DMS_MAPRDTL
                    WHERE curflg = 'Y'
                    AND mapref = :1
                    GROUP BY valclnm, mapcmbcd
                    HAVING count(*) > 1
                """, [p_mapref])
            c2_row = cursor.fetchone()
            
            if c2_row and c2_row[2] > 1:
                w_err = f'Target value column name ({c2_row[0]}) cannot repeat within a mapping code({c2_row[1]}). Please use alias if required.'
                w_return = 'N'
                
                try:
                    # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                    err_id = get_next_id(cursor, "DMS_MAPERRSEQ")
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES (%s, null, %s, null, 'ERR', %s, CURRENT_TIMESTAMP)
                        """, (err_id, p_mapref, w_err))
                    else:  # Oracle
                        cursor.execute("""
                            INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES (:1, null, :2, null, 'ERR', :3, sysdate)
                        """, [err_id, p_mapref, w_err])
                except Exception as e:
                    _raise_error(w_procnm, '127', w_parm, e)
        
        # Additional validation: Check for SQL code and mapping combination consistency
        if w_return == 'Y':
            if db_type == "POSTGRESQL":
                cursor.execute("""
                    SELECT maprsqlcd, mapcmbcd, count(*) cnt
                    FROM (SELECT DISTINCT maprsqlcd, mapcmbcd
                          FROM DMS_MAPRDTL
                          WHERE curflg = 'Y'
                          AND mapref = %s) x
                    GROUP BY maprsqlcd, mapcmbcd
                    HAVING count(*) > 1
                """, (p_mapref,))
            else:  # Oracle
                cursor.execute("""
                    SELECT maprsqlcd, mapcmbcd, count(*) cnt
                    FROM (SELECT DISTINCT maprsqlcd, mapcmbcd
                          FROM DMS_MAPRDTL
                          WHERE curflg = 'Y'
                          AND mapref = :1) x
                    GROUP BY maprsqlcd, mapcmbcd
                    HAVING count(*) > 1
                """, [p_mapref])
            c2_row = cursor.fetchone()
            
            if c2_row and c2_row[2] > 1:
                w_err = 'For a "Mapping Combination"/"SQL Query Code", more than 1 "SQL Query Code"/"Mapping Combination" is not allowed'
                w_return = 'N'
                
                try:
                    # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                    err_id = get_next_id(cursor, "DMS_MAPERRSEQ")
                    if db_type == "POSTGRESQL":
                        cursor.execute("""
                            INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES (%s, null, %s, null, 'ERR', %s, CURRENT_TIMESTAMP)
                        """, (err_id, p_mapref, w_err))
                    else:  # Oracle
                        cursor.execute("""
                            INSERT INTO DMS_MAPERR(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES (:1, null, :2, null, 'ERR', :3, sysdate)
                        """, [err_id, p_mapref, w_err])
                except Exception as e:
                    _raise_error(w_procnm, '140', w_parm, e)
        
        # Update mapping record if all validations passed
        if w_return == 'Y':
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        UPDATE DMS_MAPR
                        SET lgvrfydt = CURRENT_TIMESTAMP, lgvrfyflg = %s, lgvrfby = %s
                        WHERE mapref = %s
                        AND curflg = 'Y'
                    """, (w_return, G_USER, p_mapref))
                else:  # Oracle
                    cursor.execute("""
                        UPDATE DMS_MAPR
                        SET lgvrfydt = sysdate, lgvrfyflg = :1, lgvrfby = :2
                        WHERE mapref = :3
                        AND curflg = 'Y'
                    """, [w_return, G_USER, p_mapref])
            except Exception as e:
                _raise_error(w_procnm, '113', f'MapRef={p_mapref}', e)
        
        # Commit changes if autocommit is disabled (for PostgreSQL)
        db_type = _detect_db_type(metadata_connection)
        if db_type == "POSTGRESQL" and not getattr(metadata_connection, 'autocommit', False):
            metadata_connection.commit()
        elif db_type == "ORACLE":
            metadata_connection.commit()
        
        return w_return
        
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '129', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_mapping_details(metadata_connection, p_mapref, p_user=None, target_connection=None):
    """
    Function to validate mapping details
    Args:
        metadata_connection: Connection to metadata database (for querying DMS_* tables)
        p_mapref: Mapping reference
        p_user: User ID (optional)
        target_connection: Connection to target database (for SQL validation). If None, uses metadata_connection.
    Returns: (is_valid, error_message)
    """
    w_procnm = 'VALIDATE_MAPPING_DETAILS'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
    
    # Use target_connection for SQL validation if provided, otherwise use metadata_connection
    sql_validation_connection = target_connection if target_connection else metadata_connection
    
    cursor = None
    try:
        cursor = metadata_connection.cursor()
        
        # Detect database type for parameter binding
        db_type = _detect_db_type(metadata_connection)
        
        w_msg = None
        w_return = 'Y'
        
        # Validate logic first
        try:
            w_flg = validate_logic_for_mapref(metadata_connection, p_mapref, G_USER, sql_validation_connection)
            
            if _nvl(w_flg, 'N') == 'N':
                w_msg = 'Some/All target columns logic validation failed, please verify logic(SQL).'
                w_return = 'N'
        except Exception as e:
            _raise_error(w_procnm, '115', w_parm, e)
        
        # Check primary key
        if not w_msg:
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        SELECT trgkeyseq, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = %s
                        AND trgkeyflg = 'Y'
                        GROUP BY trgkeyseq
                    """, (p_mapref,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT trgkeyseq, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = :1
                        AND trgkeyflg = 'Y'
                        GROUP BY trgkeyseq
                    """, [p_mapref])
                pk_row = cursor.fetchone()
                
                if not pk_row or pk_row[1] == 0:
                    w_msg = 'Primary key not specified, primary key(s) is mandatory.'
                    w_return = 'N'
                elif pk_row[0] and pk_row[1] > 1:
                    w_msg = 'Primary sequence cannot repeat within mapping.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '125', w_parm, e)
        
        # Check for duplicate column names
        if not w_msg:
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        SELECT trgclnm, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = %s
                        GROUP BY trgclnm
                        HAVING count(*) > 1
                    """, (p_mapref,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT trgclnm, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = :1
                        GROUP BY trgclnm
                        HAVING count(*) > 1
                    """, [p_mapref])
                cl_row = cursor.fetchone()
                
                if cl_row and cl_row[1] > 1:
                    w_msg = 'Target column name cannot repeat within mapping.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '126', w_parm, e)
        
        # Check for duplicate value columns
        if not w_msg:
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        SELECT valclnm, mapcmbcd, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = %s
                        GROUP BY valclnm, mapcmbcd
                        HAVING count(*) > 1
                    """, (p_mapref,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT valclnm, mapcmbcd, count(*) cnt
                        FROM DMS_MAPRDTL
                        WHERE curflg = 'Y'
                        AND mapref = :1
                        GROUP BY valclnm, mapcmbcd
                        HAVING count(*) > 1
                    """, [p_mapref])
                c2_row = cursor.fetchone()
                
                if c2_row and c2_row[2] > 1:
                    w_msg = f'Target value column name ({c2_row[0]}) cannot repeat within a mapping code({c2_row[1]}). Please use alias if required.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '130', w_parm, e)
        
        return w_return, w_msg
        
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '116', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def activate_deactivate_mapping(connection, p_mapref, p_stflg, p_user=None):
    """
    Procedure to activate or deactivate a mapping
    Returns: error_message (None if successful)
    """
    w_procnm = 'ACTIVATE_DEACTIVATE_MAPPING'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
    
    cursor = None
    target_connection = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        
        w_msg = None
        
        # Validation
        if _nvl(p_stflg, 'N') not in ('A', 'N'):
            w_msg = 'Invalid status flag (valid: A or N).'
        
        # If activating, validate mappings first
        if p_stflg == 'A' and not w_msg:
            # Get target connection ID from mapping
            trgconid = None
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        SELECT trgconid
                        FROM DMS_MAPR
                        WHERE mapref = %s
                        AND curflg = 'Y'
                    """, (p_mapref,))
                else:  # Oracle
                    cursor.execute("""
                        SELECT trgconid
                        FROM DMS_MAPR
                        WHERE mapref = :1
                        AND curflg = 'Y'
                    """, [p_mapref])
                row = cursor.fetchone()
                if row and row[0]:
                    trgconid = row[0]
            except Exception as e:
                info(f"Error fetching target connection ID: {str(e)}")
            
            # Create target connection if trgconid exists
            if trgconid:
                try:
                    from database.dbconnect import create_target_connection
                    target_connection = create_target_connection(trgconid)
                    info(f"Using target connection (ID: {trgconid}) for validation")
                except Exception as e:
                    info(f"Could not create target connection (ID: {trgconid}): {str(e)}, will use metadata connection")
                    target_connection = None
            
            try:
                # Pass target_connection to validate_mapping_details for SQL validation
                w_flg, w_val_msg = validate_mapping_details(connection, p_mapref, G_USER, target_connection)
                
                if _nvl(w_flg, 'N') == 'N':
                    w_msg = f'{w_val_msg}\nCannot activate mapping few columns logic failed.'
            except Exception as e:
                _raise_error(w_procnm, '118', w_parm, e)
            
            # If validation passed, update mapping status
            if not w_msg:
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        UPDATE DMS_MAPR
                        SET stflg = %s, actby = %s, actdt = CURRENT_TIMESTAMP
                        WHERE mapref = %s
                        AND curflg = 'Y'
                    """, (p_stflg, G_USER, p_mapref))
                else:  # Oracle
                    cursor.execute("""
                        UPDATE DMS_MAPR
                        SET stflg = :1, actby = :2, actdt = sysdate
                        WHERE mapref = :3
                        AND curflg = 'Y'
                    """, [p_stflg, G_USER, p_mapref])
                
                # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
                if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
                    connection.commit()
                elif db_type == "ORACLE":
                    connection.commit()
        
        return w_msg
        
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '119', w_parm, e)
    finally:
        if cursor:
            cursor.close()
        # Close target connection if it was created
        if target_connection:
            try:
                target_connection.close()
            except Exception:
                pass  # Ignore errors when closing

def delete_mapping(connection, p_mapref):
    """
    Procedure to delete mapping
    Returns: error_message (None if successful)
    """
    w_procnm = 'DELETE_MAPPING'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Detect database type
        db_type = _detect_db_type(cursor)
        
        # Check if job exists for this mapping
        if db_type == "POSTGRESQL":
            cursor.execute("""
                SELECT mapref, jobid
                FROM DMS_JOB
                WHERE mapref = %s
                AND curflg = 'Y'
            """, (p_mapref,))
        else:  # Oracle
            cursor.execute("""
                SELECT mapref, jobid
                FROM DMS_JOB
                WHERE mapref = :1
                AND curflg = 'Y'
            """, [p_mapref])
        job_row = cursor.fetchone()
        
        if job_row:
            return f'The mapping "{p_mapref}" cannot be deleted because related job exists.'
        else:
            try:
                # Delete mapping details
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        DELETE FROM DMS_MAPRDTL
                        WHERE mapref = %s
                    """, (p_mapref,))
                    
                    # Delete mapping
                    cursor.execute("""
                        DELETE FROM DMS_MAPR
                        WHERE mapref = %s
                    """, (p_mapref,))
                else:  # Oracle
                    cursor.execute("""
                        DELETE FROM DMS_MAPRDTL
                        WHERE mapref = :1
                    """, [p_mapref])
                    
                    # Delete mapping
                    cursor.execute("""
                        DELETE FROM DMS_MAPR
                        WHERE mapref = :1
                    """, [p_mapref])
                
                # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
                if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
                    connection.commit()
                elif db_type == "ORACLE":
                    connection.commit()
                return None
                
            except Exception as e:
                _raise_error(w_procnm, '121', w_parm, e)
    
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '122', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def delete_mapping_details(connection, p_mapref, p_trgclnm):
    """
    Procedure to delete mapping details
    Returns: error_message (None if successful)
    """
    w_procnm = 'DELETE_MAPPING_DETAILS'
    w_parm = f'Mapref={p_mapref} Trgclnm={p_trgclnm}'[:200]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Detect database type
        db_type = _detect_db_type(cursor)
        
        # Check if job detail exists for this mapping detail
        if db_type == "POSTGRESQL":
            cursor.execute("""
                SELECT mapref, jobdtlid
                FROM DMS_JOBDTL
                WHERE mapref = %s
                AND trgclnm = %s
                AND curflg = 'Y'
            """, (p_mapref, p_trgclnm))
        else:  # Oracle
            cursor.execute("""
                SELECT mapref, jobdtlid
                FROM DMS_JOBDTL
                WHERE mapref = :1
                AND trgclnm = :2
                AND curflg = 'Y'
            """, [p_mapref, p_trgclnm])
        jd_row = cursor.fetchone()
        
        if jd_row:
            return f'The mapping detail for "{p_mapref}-{p_trgclnm}" cannot be deleted because related job detail exists.'
        else:
            try:
                # Delete mapping detail
                if db_type == "POSTGRESQL":
                    cursor.execute("""
                        DELETE FROM DMS_MAPRDTL
                        WHERE mapref = %s
                        AND trgclnm = %s
                    """, (p_mapref, p_trgclnm))
                else:  # Oracle
                    cursor.execute("""
                        DELETE FROM DMS_MAPRDTL
                        WHERE mapref = :1
                        AND trgclnm = :2
                    """, [p_mapref, p_trgclnm])
                
                # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
                if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
                    connection.commit()
                elif db_type == "ORACLE":
                    connection.commit()
                return None
                
            except Exception as e:
                _raise_error(w_procnm, '123', w_parm, e)
    
    except PKGDMS_MAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '124', w_parm, e)
    finally:
        if cursor:
            cursor.close()

