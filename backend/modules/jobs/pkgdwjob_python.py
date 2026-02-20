"""
Python equivalent of PKGDMS_JOB PL/SQL package.
Handles job creation, target table creation, and dynamic code generation with hash-based change detection.

Author: AI Assistant
Date: 2025-11-14
Version: 1.0

Change History:
- 2025-11-14: Initial Python conversion with hash-based change detection using MD5
"""

import os
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import traceback
try:
    from backend.modules.logger import info, error, debug
    from backend.modules.common.id_provider import next_id as get_next_id
    from backend.modules.common.db_adapter import get_db_adapter
except ImportError:  # Fallback for Flask-style imports
    from modules.logger import info, error, debug  # type: ignore
    from modules.common.id_provider import next_id as get_next_id  # type: ignore
    from modules.common.db_adapter import get_db_adapter  # type: ignore

# Optional Oracle driver: allow scheduler to run even if oracledb is not installed.
# Oracle-specific features will check for this at runtime.
try:
    import oracledb  # type: ignore
except ModuleNotFoundError:
    oracledb = None  # type: ignore
    error("Oracle client 'oracledb' is not installed. Oracle-based jobs will not run.")

# Package metadata
G_NAME = 'PKGDMS_JOB_PYTHON'
G_VER = 'V001'

# Hash configuration
HASH_ALGORITHM = 'md5'  # Using MD5 for fast change detection
HASH_DELIMITER = '|'     # Delimiter for concatenating column values
NULL_MARKER = '<NULL>'   # Marker for NULL values in hash calculation

# Audit columns to exclude from hash calculation
HASH_EXCLUDE_COLUMNS = {
    'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 
    'CURFLG', 'FROMDT', 'TODT', 'VALDFRM', 'VALDTO'
}


def version() -> str:
    """Returns package version."""
    return f"{G_NAME}:{G_VER}"


def _detect_db_type(connection):
    """Detect database type from connection"""
    import builtins
    module_name = builtins.type(connection).__module__
    connection_type = builtins.type(connection).__name__
    info(f"Detecting DB type - module: {module_name}, type: {connection_type}")
    module_lower = module_name.lower()
    
    if "psycopg" in module_lower or "pg8000" in module_lower:
        detected = "POSTGRESQL"
    elif "oracledb" in module_lower or "cx_oracle" in module_lower:
        detected = "ORACLE"
    elif "mysql" in module_lower:
        detected = "MYSQL"
    else:
        detected = "ORACLE"  # Default fallback
    
    info(f"Detected database type: {detected}")
    return detected


def _raise_error(proc_name: str, error_code: str, param: str, exception: Exception = None):
    """
    Raises a formatted error similar to PKGERR.RAISE_ERROR in PL/SQL.
    
    Args:
        proc_name: Name of the procedure/function where error occurred
        error_code: Error code identifier
        param: Parameter information
        exception: Optional exception object
    """
    error_msg = f"{G_NAME}.{proc_name} Error {error_code}: {param}"
    if exception:
        error_msg += f" | DB Error: {str(exception)}"
    
    print(f"ERROR: {error_msg}")
    if exception:
        traceback.print_exc()
    
    raise Exception(error_msg)


def get_columns(column_string: str) -> List[str]:
    """
    Extract column names from a comma-delimited string.
    Python equivalent of GET_COLUMNS function.
    
    Args:
        column_string: Comma-delimited string of column names
        
    Returns:
        List of column names
        
    Example:
        'COL1,COL2,COL3' -> ['COL1', 'COL2', 'COL3']
    """
    w_procnm = 'get_columns'
    w_parm = column_string[:400] if column_string else ''
    
    try:
        if not column_string:
            return []
        
        # Remove trailing comma and trim
        clean_string = column_string.strip().rstrip(',')
        
        # Split by comma and trim each column name
        columns = [col.strip() for col in clean_string.split(',') if col.strip()]
        
        return columns
        
    except Exception as e:
        _raise_error(w_procnm, '001', w_parm, e)


def generate_hash(values: Dict[str, Any], column_order: List[str] = None) -> str:
    """
    Generate MD5 hash from column values.
    
    Args:
        values: Dictionary of column_name -> value
        column_order: Optional list specifying the order of columns for hash calculation
                     If None, alphabetical order is used
    
    Returns:
        MD5 hash as 32-character hex string
    """
    try:
        # Determine column order
        if column_order:
            # Use specified order, but only include columns that exist in values
            cols = [c for c in column_order if c in values and c.upper() not in HASH_EXCLUDE_COLUMNS]
        else:
            # Use alphabetical order, excluding audit columns
            cols = sorted([k for k in values.keys() if k.upper() not in HASH_EXCLUDE_COLUMNS])
        
        # Build concatenated string with delimiter
        parts = []
        for col in cols:
            val = values.get(col)
            if val is None:
                parts.append(NULL_MARKER)
            elif isinstance(val, (datetime,)):
                # Format dates consistently
                parts.append(val.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                parts.append(str(val))
        
        concat_str = HASH_DELIMITER.join(parts)
        
        # Generate MD5 hash
        hash_obj = hashlib.md5(concat_str.encode('utf-8'))
        return hash_obj.hexdigest()
        
    except Exception as e:
        print(f"Error generating hash: {str(e)}")
        raise


def create_target_table(connection, p_mapref: str, p_trgconid: int = None) -> str:
    """
    Create target tables as per mapping configuration.
    Automatically adds RWHKEY column for hash-based change detection.
    
    Python equivalent of CREATE_TARGET_TABLE function.
    
    Args:
        connection: Oracle database connection (metadata connection)
        p_mapref: Mapping reference
        p_trgconid: Target database connection ID (from DMS_DBCONDTLS)
                   If None, uses metadata connection
        
    Returns:
        'Y' if successful, raises exception otherwise
    """
    w_procnm = 'create_target_table'
    w_parm = p_mapref[:200]
    
    cursor = None
    target_cursor = None
    target_connection = None
    w_return = 'Y'
    
    try:
        cursor = connection.cursor()
        
        # Detect metadata database type
        metadata_db_type = _detect_db_type(connection)
        
        # Get metadata schema name from environment (for DMS_JOB, DMS_JOBDTL, DMS_PARAMS)
        # The target schema will come from job configuration (trgschm)
        metadata_schema = os.getenv('DMS_SCHEMA', 'TRG')
        
        # Get database connection info to determine target database type for datatype lookup
        # Phase 3: Support database-specific datatypes
        target_dbtype = 'GENERIC'  # Default fallback
        try:
            if metadata_db_type == "POSTGRESQL":
                dbtype_query = f"""
                    SELECT COALESCE(dc.dbtyp, 'GENERIC')
                    FROM {metadata_schema}.DMS_JOB j
                    LEFT JOIN {metadata_schema}.DMS_DBCONNECT dc ON dc.conid = j.trgconid
                    WHERE j.mapref = %s
                """
                cursor.execute(dbtype_query, (p_mapref,))
            else:  # Oracle
                dbtype_query = f"""
                    SELECT COALESCE(dc.DBTYP, 'GENERIC')
                    FROM {metadata_schema}.DMS_JOB j
                    LEFT JOIN {metadata_schema}.DMS_DBCONNECT dc ON dc.CONID = j.TRGCONID
                    WHERE j.MAPREF = :mapref
                """
                cursor.execute(dbtype_query, {'mapref': p_mapref})
            
            dbtype_row = cursor.fetchone()
            if dbtype_row:
                target_dbtype = dbtype_row[0] or 'GENERIC'
        except Exception as dbtype_err:
            # Fallback to GENERIC if we can't determine target database type
            print(f"Warning: Could not determine target database type, using GENERIC: {str(dbtype_err)}")
            target_dbtype = 'GENERIC'
        
        # Query to get job details with column information
        # Phase 3: Updated to filter datatypes by target database type
        if metadata_db_type == "POSTGRESQL":
            query = f"""
                SELECT jd.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
                       jd.trgclnm, jd.trgcldtyp, jd.trgkeyflg, jd.trgkeyseq,
                       p.prval
                FROM {metadata_schema}.DMS_JOB j
                JOIN {metadata_schema}.DMS_JOBDTL jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
                JOIN {metadata_schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' 
                                                    AND p.prcd = jd.trgcldtyp
                                                    AND (p.dbtyp = %s OR p.dbtyp = 'GENERIC')
                WHERE j.mapref = %s
                  AND j.curflg = 'Y'
                ORDER BY jd.excseq, p.dbtyp DESC NULLS LAST
            """
            cursor.execute(query, (target_dbtype, p_mapref))
        else:  # Oracle
            query = f"""
                SELECT jd.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
                       jd.trgclnm, jd.trgcldtyp, jd.trgkeyflg, jd.trgkeyseq,
                       p.prval
                FROM {metadata_schema}.DMS_JOB j
                JOIN {metadata_schema}.DMS_JOBDTL jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
                JOIN {metadata_schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' 
                                                    AND p.prcd = jd.trgcldtyp
                                                    AND (p.dbtyp = :dbtyp OR p.dbtyp = 'GENERIC')
                WHERE j.mapref = :mapref
                  AND j.curflg = 'Y'
                ORDER BY jd.excseq, p.dbtyp DESC
            """
            cursor.execute(query, {'dbtyp': target_dbtype, 'mapref': p_mapref})
        rows = cursor.fetchall()
        
        if not rows:
            w_msg = 'No job details found for mapping'
            _raise_error(w_procnm, '101', f"{w_parm}::{w_msg}")
        
        # Extract table information from first row
        first_row = rows[0]
        mapref, trgschm, trgtbtyp, trgtbnm, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, prval = first_row
        
        w_trgtbnm = trgtbnm
        w_trgschm = trgschm
        w_tbtyp = trgtbtyp
        w_tbnm = f"{w_trgschm}.{w_trgtbnm}"
        
        # Get target connection for table operations
        if p_trgconid:
            try:
                # Support both FastAPI (package import) and legacy Flask (relative import) contexts
                try:
                    from backend.database.dbconnect import create_target_connection
                except ImportError:  # When running Flask app.py directly inside backend
                    from database.dbconnect import create_target_connection  # type: ignore
                target_connection = create_target_connection(p_trgconid)
                if target_connection is None:
                    raise Exception(f"Failed to create target connection for CONID {p_trgconid}")
                
                # Prefer DBTYP from metadata if available; fallback to connection detection
                if target_dbtype and str(target_dbtype).upper() != "GENERIC":
                    target_db_type = str(target_dbtype).upper()
                else:
                    target_db_type = _detect_db_type(target_connection)
                adapter = get_db_adapter(target_db_type)
                
                # Validate connection is active by pinging the database
                try:
                    test_cursor = target_connection.cursor()
                    test_cursor.execute(adapter.ping_sql())
                    test_cursor.fetchone()
                    test_cursor.close()
                    print(f"Target connection {p_trgconid} validated successfully")
                except Exception as ping_err:
                    target_connection.close()
                    raise Exception(f"Target connection {p_trgconid} created but not responsive: {str(ping_err)}")
                
                target_cursor = target_connection.cursor()
                print(f"Using target connection {p_trgconid} for table operations")
            except Exception as conn_err:
                error_msg = f"Error creating target connection for CONID {p_trgconid}: {str(conn_err)}"
                print(error_msg)
                _raise_error(w_procnm, '106', f"{w_parm}::{error_msg}", conn_err)
        else:
            # Use metadata connection if no target connection specified
            target_connection = connection
            target_cursor = cursor
            target_db_type = metadata_db_type  # Same as metadata when using metadata connection
            adapter = get_db_adapter(target_db_type)
            print(f"Using metadata connection for table operations (no target connection specified)")
        
        # Ensure target_cursor is set before use
        if target_cursor is None:
            raise Exception("Target cursor not initialized")
        
        # Check if table exists in target schema
        table_exists = adapter.table_exists(target_cursor, w_trgschm, w_trgtbnm)
        w_flg = 'Y' if table_exists else 'N'
        
        if w_flg == 'Y':
            print(f"Table {w_tbnm} already exists. Checking for missing columns...")
        else:
            print(f"Table {w_tbnm} does not exist. Will create new table...")
        
        # Collect column definitions
        w_ddl = ''
        missing_columns = []
        
        for row in rows:
            mapref, trgschm, trgtbtyp, trgtbnm, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, prval = row
            
            # Check if column exists in target table
            if w_flg == 'Y':  # Only check if table exists
                if not adapter.column_exists(target_cursor, w_trgschm, w_trgtbnm, trgclnm):
                    missing_columns.append((trgclnm, prval))
            else:
                # Table doesn't exist - collect all columns
                missing_columns.append((trgclnm, prval))
        
        # Build DDL for missing columns only
        if missing_columns:
            w_ddl = ''
            for trgclnm, prval in missing_columns:
                w_ddl += f"  {trgclnm} {prval},\n"
        
        # If table doesn't exist, we need to create it (even if no missing columns yet)
        if w_flg == 'N':
            if not missing_columns:
                w_msg = 'Target table not created (no columns defined), please verify mappings.'
                _raise_error(w_procnm, '102', f"{w_parm}::{w_msg}")
        
        # If table exists and no missing columns, skip DDL execution
        if w_flg == 'Y' and not missing_columns:
            print(f"Table {w_tbnm} exists and all columns are present. Skipping DDL execution.")
            if target_connection and target_connection != connection:
                target_connection.close()
            return w_return
        
        # Build CREATE or ALTER TABLE DDL
        if w_flg == 'N':
            # New table - add SKEY, RWHKEY, business columns, and audit columns
            if w_ddl:
                create_columns = []
                skey_col = adapter.get_skey_column(w_tbtyp)
                if skey_col:
                    create_columns.append(skey_col)
                rwhkey_col = adapter.get_rwhkey_column(w_tbtyp)
                if rwhkey_col:
                    create_columns.append(rwhkey_col)

                for trgclnm, prval in missing_columns:
                    create_columns.append(f"{trgclnm} {prval}")

                if w_tbtyp == 'DIM':
                    create_columns.extend(adapter.get_dim_scd_columns())

                create_columns.extend(adapter.get_audit_columns())

                w_ddl = adapter.build_create_table(w_trgschm, w_trgtbnm, create_columns)
        else:
            # Existing table - add missing columns
            if w_ddl:
                rwhkey_exists = adapter.column_exists(target_cursor, w_trgschm, w_trgtbnm, "RWHKEY")

                alter_columns = [f"{trgclnm} {prval}" for trgclnm, prval in missing_columns]

                if not rwhkey_exists and w_tbtyp in ('DIM', 'FCT', 'MRT'):
                    rwhkey_col = adapter.get_rwhkey_column(w_tbtyp)
                    if rwhkey_col:
                        alter_columns.append(rwhkey_col)

                if alter_columns:
                    w_ddl = adapter.build_alter_table(w_trgschm, w_trgtbnm, alter_columns)
                else:
                    w_ddl = None
        
        # Execute DDL if generated
        if w_ddl:
            try:
                target_cursor.execute(w_ddl)
                print(f"DDL executed successfully for {w_tbnm}")
            except Exception as e:
                w_return = 'N'
                _raise_error(w_procnm, '103', f"{w_parm}::DDL={w_ddl[:200]}", e)
        
        # Create sequence for SKEY if needed (Oracle uses sequences)
        if w_tbtyp in ('DIM', 'FCT', 'MRT') and adapter.supports_sequence():
            try:
                adapter.ensure_sequence(target_cursor, w_trgschm, w_trgtbnm, bool(p_trgconid))
            except Exception as e:
                _raise_error(w_procnm, '104', f"{w_parm}::SEQ={w_trgschm}.{w_trgtbnm}", e)
        
        # Commit on target connection
        if target_db_type == "POSTGRESQL" and not getattr(target_connection, 'autocommit', False):
            target_connection.commit()
        elif hasattr(target_connection, "commit"):
            target_connection.commit()
        return w_return
        
    except Exception as e:
        # Safely rollback target connection if it exists and is valid
        if target_connection and target_connection != connection:
            try:
                target_connection.rollback()
            except Exception:
                pass  # Ignore rollback errors during exception handling
        _raise_error(w_procnm, '105', w_parm, e)
    finally:
        # Safely close cursors and connections
        if target_cursor and target_connection and target_connection != connection:
            try:
                target_cursor.close()
            except Exception:
                pass  # Ignore close errors
        if target_connection and target_connection != connection:
            try:
                target_connection.close()
            except Exception:
                pass  # Ignore close errors
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass  # Ignore close errors


def create_update_job(connection, p_mapref: str) -> Optional[int]:
    """
    Create or update job based on mapping configuration.
    Python equivalent of CREATE_UPDATE_JOB function.
    
    Args:
        connection: Oracle database connection
        p_mapref: Mapping reference
        
    Returns:
        Job ID if successful, None otherwise
    """
    w_procnm = 'create_update_job'
    w_parm = p_mapref[:200]
    w_jobid = None
    
    cursor = None
    info(f"Create update job started for mapref: {p_mapref}")
    try:
        # Validate connection is valid before use
        if connection is None:
            raise Exception("Connection parameter is None")
        
        # Detect database type
        db_type = _detect_db_type(connection)
        
        # Test connection by creating a cursor
        try:
            test_cursor = connection.cursor()
            if db_type == "POSTGRESQL":
                test_cursor.execute("SELECT 1")
            else:  # Oracle
                test_cursor.execute("SELECT 1 FROM DUAL")
            test_cursor.fetchone()
            test_cursor.close()
        except Exception as conn_test_err:
            raise Exception(f"Connection is not valid or not connected to database: {str(conn_test_err)}")
        
        cursor = connection.cursor()
        schema = os.getenv('DMS_SCHEMA', 'TRG')
        
        # Get mapping details
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT * FROM {schema}.DMS_MAPR
                WHERE mapref = %s
                  AND curflg = 'Y'
                  AND lgvrfyflg = 'Y'
                  AND stflg = 'A'
            """
            cursor.execute(query, (p_mapref,))
        else:  # Oracle
            query = f"""
                SELECT * FROM {schema}.DMS_MAPR
                WHERE mapref = :mapref
                  AND curflg = 'Y'
                  AND lgvrfyflg = 'Y'
                  AND stflg = 'A'
            """
            cursor.execute(query, {'mapref': p_mapref})
        columns = [col[0].upper() for col in cursor.description]  # Normalize to uppercase
        map_row = cursor.fetchone()
        
        if not map_row:
            print(f"No active mapping found for {p_mapref}")
            return None
        
        map_rec = dict(zip(columns, map_row))
        
        # Check if job already exists
        if db_type == "POSTGRESQL":
            job_query = f"""
                SELECT * FROM {schema}.DMS_JOB
                WHERE mapref = %s
                  AND curflg = 'Y'
                  AND stflg = 'A'
            """
            cursor.execute(job_query, (p_mapref,))
        else:  # Oracle
            job_query = f"""
                SELECT * FROM {schema}.DMS_JOB
                WHERE mapref = :mapref
                  AND curflg = 'Y'
                  AND stflg = 'A'
            """
            cursor.execute(job_query, {'mapref': p_mapref})
        job_columns = [col[0].upper() for col in cursor.description]  # Normalize to uppercase
        job_row = cursor.fetchone()
        
        w_chg = 'Y'
        
        # Get target connection ID from mapping (if specified) - get it early for comparison
        trgconid = map_rec.get('TRGCONID')

        # Resolve target schema from connection metadata when target connection is provided.
        # Priority: SCHNM (new mandatory field) -> USRNM (legacy fallback).
        if trgconid is not None:
            try:
                if db_type == "POSTGRESQL":
                    cursor.execute(
                        f"""
                        SELECT COALESCE(schnm, usrnm)
                        FROM {schema}.DMS_DBCONDTLS
                        WHERE conid = %s
                          AND curflg = 'Y'
                        """,
                        (trgconid,),
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT COALESCE(schnm, usrnm)
                        FROM {schema}.DMS_DBCONDTLS
                        WHERE conid = :conid
                          AND curflg = 'Y'
                        """,
                        {"conid": trgconid},
                    )

                conn_schema_row = cursor.fetchone()
                if conn_schema_row and conn_schema_row[0]:
                    resolved_schema = str(conn_schema_row[0]).strip()
                    if resolved_schema:
                        map_rec['TRGSCHM'] = resolved_schema
                else:
                    raise Exception(
                        f"Could not resolve schema for target connection ID {trgconid}. "
                        "Ensure DMS_DBCONDTLS.SCHNM is populated."
                    )
            except Exception as schema_resolve_err:
                _raise_error(w_procnm, '103', f"{w_parm}::Invalid target schema resolution", schema_resolve_err)
        
        if job_row:
            job_rec = dict(zip(job_columns, job_row))
            
            # Check if job needs update - include TRGCONID and checkpoint columns in comparison
            job_trgconid = job_rec.get('TRGCONID')
            
            # Normalize checkpoint column name for comparison (handle None vs empty string)
            job_chkpntclnm = job_rec.get('CHKPNTCLNM') if job_rec.get('CHKPNTCLNM') else None
            map_chkpntclnm = map_rec.get('CHKPNTCLNM') if map_rec.get('CHKPNTCLNM') and map_rec.get('CHKPNTCLNM').strip() else None
            
            # Normalize checkpoint strategy (default to 'AUTO' if None)
            job_chkpntstrtgy = job_rec.get('CHKPNTSTRTGY') or 'AUTO'
            map_chkpntstrtgy = map_rec.get('CHKPNTSTRTGY') or 'AUTO'
            
            # Normalize checkpoint enabled (default to 'Y' if None)
            job_chkpntenbld = job_rec.get('CHKPNTENBLD') or 'Y'
            map_chkpntenbld = map_rec.get('CHKPNTENBLD') or 'Y'

            # Normalize key mapping attributes for robust change detection.
            job_trgschm = (str(job_rec.get('TRGSCHM') or '')).strip().upper()
            map_trgschm = (str(map_rec.get('TRGSCHM') or '')).strip().upper()
            job_trgtbtyp = (str(job_rec.get('TRGTBTYP') or '')).strip().upper()
            map_trgtbtyp = (str(map_rec.get('TRGTBTYP') or '')).strip().upper()
            job_trgtbnm = (str(job_rec.get('TRGTBNM') or '')).strip().upper()
            map_trgtbnm = (str(map_rec.get('TRGTBNM') or '')).strip().upper()
            job_srcsystm = (str(job_rec.get('SRCSYSTM') or '')).strip().upper()
            map_srcsystm = (str(map_rec.get('SRCSYSTM') or '')).strip().upper()
            
            if (job_rec['FRQCD'] == map_rec['FRQCD'] and
                job_rec['STFLG'] == map_rec['STFLG'] and
                job_trgschm == map_trgschm and
                job_trgtbtyp == map_trgtbtyp and
                job_trgtbnm == map_trgtbnm and
                job_srcsystm == map_srcsystm and
                job_rec.get('BLKPRCROWS', -1) == map_rec.get('BLKPRCROWS', -1) and
                (job_trgconid == trgconid or (job_trgconid is None and trgconid is None)) and
                job_chkpntstrtgy == map_chkpntstrtgy and
                job_chkpntclnm == map_chkpntclnm and
                job_chkpntenbld == map_chkpntenbld):
                w_chg = 'N'
                w_jobid = job_rec['JOBID']
            else:
                # Mark existing job as inactive
                if db_type == "POSTGRESQL":
                    cursor.execute(f"""
                        UPDATE {schema}.DMS_JOB
                        SET curflg = 'N', recupdt = CURRENT_TIMESTAMP
                        WHERE jobid = %s AND curflg = 'Y'
                    """, (job_rec['JOBID'],))
                else:  # Oracle
                    cursor.execute(f"""
                        UPDATE {schema}.DMS_JOB
                        SET curflg = 'N', recupdt = SYSDATE
                        WHERE jobid = :jobid AND curflg = 'Y'
                    """, {'jobid': job_rec['JOBID']})
        
        # Create new job if needed
        if w_chg == 'Y':
            # Generate job ID using ID provider (supports Oracle/PostgreSQL)
            job_id = get_next_id(cursor, f"{schema}.DMS_JOBSEQ")
            if db_type == "POSTGRESQL":
                cursor.execute(f"""
                    INSERT INTO {schema}.DMS_JOB (
                        jobid, mapid, mapref, frqcd, trgschm, trgtbtyp,
                        trgtbnm, srcsystm, stflg, reccrdt, recupdt, curflg, blkprcrows,
                        chkpntstrtgy, chkpntclnm, chkpntenbld, trgconid
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s,
                        %s, %s, %s, %s
                    )
                """, (
                    job_id,
                    map_rec['MAPID'],
                    map_rec['MAPREF'],
                    map_rec['FRQCD'],
                    map_rec['TRGSCHM'],
                    map_rec['TRGTBTYP'],
                    map_rec['TRGTBNM'],
                    map_rec['SRCSYSTM'],
                    map_rec['STFLG'],
                    map_rec.get('BLKPRCROWS'),
                    map_rec.get('CHKPNTSTRTGY', 'AUTO'),
                    map_rec.get('CHKPNTCLNM'),
                    map_rec.get('CHKPNTENBLD', 'Y'),
                    trgconid
                ))
            else:  # Oracle
                cursor.execute(f"""
                    INSERT INTO {schema}.DMS_JOB (
                        jobid, mapid, mapref, frqcd, trgschm, trgtbtyp,
                        trgtbnm, srcsystm, stflg, reccrdt, recupdt, curflg, blkprcrows,
                        CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD, trgconid
                    )
                    VALUES (
                        :jobid, :mapid, :mapref, :frqcd, :trgschm, :trgtbtyp,
                        :trgtbnm, :srcsystm, :stflg, SYSDATE, SYSDATE, 'Y', :blkprcrows,
                        :chkpntstrtgy, :chkpntclnm, :chkpntenbld, :trgconid
                    )
                """, {
                    'jobid': job_id,
                    'mapid': map_rec['MAPID'],
                    'mapref': map_rec['MAPREF'],
                    'frqcd': map_rec['FRQCD'],
                    'trgschm': map_rec['TRGSCHM'],
                    'trgtbtyp': map_rec['TRGTBTYP'],
                    'trgtbnm': map_rec['TRGTBNM'],
                    'srcsystm': map_rec['SRCSYSTM'],
                    'stflg': map_rec['STFLG'],
                    'blkprcrows': map_rec.get('BLKPRCROWS'),
                    'chkpntstrtgy': map_rec.get('CHKPNTSTRTGY', 'AUTO'),
                    'chkpntclnm': map_rec.get('CHKPNTCLNM'),
                    'chkpntenbld': map_rec.get('CHKPNTENBLD', 'Y'),
                    'trgconid': trgconid
                })
            w_jobid = job_id
        
        # Process job details
        if w_jobid:
            if db_type == "POSTGRESQL":
                mapdtl_query = f"""
                    SELECT * FROM {schema}.DMS_MAPRDTL
                    WHERE mapref = %s AND curflg = 'Y'
                """
                cursor.execute(mapdtl_query, (p_mapref,))
            else:  # Oracle
                mapdtl_query = f"""
                    SELECT * FROM {schema}.DMS_MAPRDTL
                    WHERE mapref = :mapref AND curflg = 'Y'
                """
                cursor.execute(mapdtl_query, {'mapref': p_mapref})
            mapdtl_columns = [col[0].upper() for col in cursor.description]  # Normalize to uppercase
            mapdtl_rows = cursor.fetchall()
            
            for mapdtl_row in mapdtl_rows:
                mapdtl_rec = dict(zip(mapdtl_columns, mapdtl_row))
                
                # Check if job detail exists
                if db_type == "POSTGRESQL":
                    jobdtl_query = f"""
                        SELECT * FROM {schema}.DMS_JOBDTL
                        WHERE mapref = %s
                          AND trgclnm = %s
                          AND curflg = 'Y'
                    """
                    cursor.execute(jobdtl_query, (
                        mapdtl_rec['MAPREF'],
                        mapdtl_rec['TRGCLNM']
                    ))
                else:  # Oracle
                    jobdtl_query = f"""
                        SELECT * FROM {schema}.DMS_JOBDTL
                        WHERE mapref = :mapref
                          AND trgclnm = :trgclnm
                          AND curflg = 'Y'
                    """
                    cursor.execute(jobdtl_query, {
                        'mapref': mapdtl_rec['MAPREF'],
                        'trgclnm': mapdtl_rec['TRGCLNM']
                    })
                jobdtl_columns = [col[0].upper() for col in cursor.description]  # Normalize to uppercase
                jobdtl_row = cursor.fetchone()
                
                w_dtl_chg = 'Y'
                
                if jobdtl_row:
                    jobdtl_rec = dict(zip(jobdtl_columns, jobdtl_row))
                    
                    # Compare job detail fields
                    if (jobdtl_rec['TRGCLDESC'] == mapdtl_rec['TRGCLDESC'] and
                        jobdtl_rec['MAPLOGIC'] == mapdtl_rec['MAPLOGIC'] and
                        jobdtl_rec['KEYCLNM'] == mapdtl_rec['KEYCLNM'] and
                        jobdtl_rec['VALCLNM'] == mapdtl_rec['VALCLNM'] and
                        jobdtl_rec['MAPCMBCD'] == mapdtl_rec['MAPCMBCD'] and
                        jobdtl_rec.get('MAPRSQLCD') == mapdtl_rec.get('MAPRSQLCD') and
                        jobdtl_rec['EXCSEQ'] == mapdtl_rec['EXCSEQ'] and
                        jobdtl_rec.get('TRGKEYSEQ', -1) == mapdtl_rec.get('TRGKEYSEQ', -1) and
                        jobdtl_rec.get('SCDTYP', 1) == mapdtl_rec.get('SCDTYP', 1)):
                        w_dtl_chg = 'N'
                    else:
                        # Mark existing detail as inactive
                        if db_type == "POSTGRESQL":
                            cursor.execute(f"""
                                UPDATE {schema}.DMS_JOBDTL
                                SET curflg = 'N', recupdt = CURRENT_TIMESTAMP
                                WHERE mapref = %s
                                  AND jobdtlid = %s
                                  AND curflg = 'Y'
                            """, (
                                jobdtl_rec['MAPREF'],
                                jobdtl_rec['JOBDTLID']
                            ))
                        else:  # Oracle
                            cursor.execute(f"""
                                UPDATE {schema}.DMS_JOBDTL
                                SET curflg = 'N', recupdt = SYSDATE
                                WHERE mapref = :mapref
                                  AND jobdtlid = :jobdtlid
                                  AND curflg = 'Y'
                            """, {
                                'mapref': jobdtl_rec['MAPREF'],
                                'jobdtlid': jobdtl_rec['JOBDTLID']
                            })
                
                # Insert new job detail if changed
                if w_dtl_chg == 'Y':
                    # Generate job detail ID using ID provider (supports Oracle/PostgreSQL)
                    jobdtlid = get_next_id(cursor, f"{schema}.DMS_JOBDTLSEQ")
                    if db_type == "POSTGRESQL":
                        cursor.execute(f"""
                            INSERT INTO {schema}.DMS_JOBDTL (
                                jobdtlid, mapref, mapdtlid, trgclnm, trgcldtyp,
                                trgkeyflg, trgkeyseq, trgcldesc, maplogic, maprsqlcd,
                                keyclnm, valclnm, mapcmbcd, excseq, scdtyp,
                                reccrdt, recupdt, curflg
                            )
                            VALUES (
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y'
                            )
                        """, (
                            jobdtlid,
                            mapdtl_rec['MAPREF'],
                            mapdtl_rec['MAPDTLID'],
                            mapdtl_rec['TRGCLNM'],
                            mapdtl_rec['TRGCLDTYP'],
                            mapdtl_rec['TRGKEYFLG'],
                            mapdtl_rec.get('TRGKEYSEQ'),
                            mapdtl_rec['TRGCLDESC'],
                            mapdtl_rec['MAPLOGIC'],
                            mapdtl_rec.get('MAPRSQLCD'),
                            mapdtl_rec['KEYCLNM'],
                            mapdtl_rec['VALCLNM'],
                            mapdtl_rec['MAPCMBCD'],
                            mapdtl_rec['EXCSEQ'],
                            mapdtl_rec.get('SCDTYP')
                        ))
                    else:  # Oracle
                        cursor.execute(f"""
                            INSERT INTO {schema}.DMS_JOBDTL (
                                jobdtlid, mapref, mapdtlid, trgclnm, trgcldtyp,
                                trgkeyflg, trgkeyseq, trgcldesc, maplogic, maprsqlcd,
                                keyclnm, valclnm, mapcmbcd, excseq, scdtyp,
                                reccrdt, recupdt, curflg
                            )
                            VALUES (
                                :jobdtlid, :mapref, :mapdtlid, :trgclnm, :trgcldtyp,
                                :trgkeyflg, :trgkeyseq, :trgcldesc, :maplogic, :maprsqlcd,
                                :keyclnm, :valclnm, :mapcmbcd, :excseq, :scdtyp,
                                SYSDATE, SYSDATE, 'Y'
                            )
                        """, {
                            'jobdtlid': jobdtlid,
                            'mapref': mapdtl_rec['MAPREF'],
                            'mapdtlid': mapdtl_rec['MAPDTLID'],
                            'trgclnm': mapdtl_rec['TRGCLNM'],
                            'trgcldtyp': mapdtl_rec['TRGCLDTYP'],
                            'trgkeyflg': mapdtl_rec['TRGKEYFLG'],
                            'trgkeyseq': mapdtl_rec.get('TRGKEYSEQ'),
                            'trgcldesc': mapdtl_rec['TRGCLDESC'],
                            'maplogic': mapdtl_rec['MAPLOGIC'],
                            'maprsqlcd': mapdtl_rec.get('MAPRSQLCD'),
                            'keyclnm': mapdtl_rec['KEYCLNM'],
                            'valclnm': mapdtl_rec['VALCLNM'],
                            'mapcmbcd': mapdtl_rec['MAPCMBCD'],
                            'excseq': mapdtl_rec['EXCSEQ'],
                            'scdtyp': mapdtl_rec.get('SCDTYP')
                        })
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
            connection.commit()
        elif db_type == "ORACLE":
            connection.commit()
        
        info(f"Before create target table for mapref: {p_mapref}")
        # Create target table using target connection
        # (trgconid was already retrieved above before INSERT)
        w_stat = create_target_table(connection, p_mapref, p_trgconid=trgconid)
        info(f"After target table creation for mapref: {p_mapref}")
        
        if w_stat == 'Y':
            # Create job flow
            debug(f"[DEBUG create_update_job] About to call create_job_flow for mapref: {p_mapref}")
            try:
                create_job_flow(connection, p_mapref)
                debug(f"[DEBUG create_update_job] Successfully completed create_job_flow for mapref: {p_mapref}")
            except Exception as flow_err:
                error(f"[DEBUG create_update_job] ERROR in create_job_flow for mapref: {p_mapref}")
                error(f"[DEBUG create_update_job] Error type: {type(flow_err).__name__}")
                error(f"[DEBUG create_update_job] Error message: {str(flow_err)}")
                error(f"[DEBUG create_update_job] Error traceback:")
                error(traceback.format_exc())
                raise  # Re-raise to be caught by outer exception handler
        
        return w_jobid
        
    except Exception as e:
        if connection:
            connection.rollback()
        _raise_error(w_procnm, '112', w_parm, e)
    finally:
        if cursor:
            cursor.close()


def create_job_flow(connection, p_mapref: str):
    """
    Create dynamic Python code for job execution with hash-based change detection.
    Python equivalent of CREATE_JOB_FLOW procedure.
    
    This function generates Python code (not PL/SQL) and stores it in DMS_JOBFLW.DWLOGIC.
    The generated code uses MD5 hash for efficient change detection instead of
    column-by-column comparison.
    
    Args:
        connection: Oracle database connection
        p_mapref: Mapping reference
    """
    w_procnm = 'create_job_flow'
    w_parm = p_mapref[:200]
    
    print(f"\n{'='*80}")
    print(f"CREATE_JOB_FLOW: Generating dynamic Python code for {p_mapref}")
    print(f"{'='*80}\n")
    
    cursor = None
    
    try:
        cursor = connection.cursor()
        schema = os.getenv('DMS_SCHEMA', 'TRG')
        
        # Detect database type
        db_type = _detect_db_type(connection)
        
        # Get bulk processing limit
        try:
            if db_type == "POSTGRESQL":
                cursor.execute("""
                    SELECT prval FROM DMS_PARAMS
                    WHERE prtyp = 'BULKPRC' AND prcd = 'NOOFROWS'
                """)
            else:  # Oracle
                cursor.execute("""
                    SELECT prval FROM DMS_PARAMS
                    WHERE prtyp = 'BULKPRC' AND prcd = 'NOOFROWS'
                """)
            w_limit_row = cursor.fetchone()
            w_limit = int(w_limit_row[0]) if w_limit_row else 1000
        except:
            w_limit = 1000
        
        # Get job information including checkpoint configuration
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                SELECT jobid, mapref, trgschm, trgtbnm, trgtbtyp, 
                       trgschm||'.'||trgtbnm as tbnam, blkprcrows,
                       chkpntstrtgy, chkpntclnm, chkpntenbld
                FROM {schema}.DMS_JOB
                WHERE mapref = %s
                  AND stflg = 'A'
                  AND curflg = 'Y'
            """, (p_mapref,))
        else:  # Oracle
            cursor.execute(f"""
                SELECT jobid, mapref, trgschm, trgtbnm, trgtbtyp, 
                       trgschm||'.'||trgtbnm as tbnam, blkprcrows,
                       CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
                FROM {schema}.DMS_JOB
                WHERE mapref = :mapref
                  AND stflg = 'A'
                  AND curflg = 'Y'
            """, {'mapref': p_mapref})
        
        job_row = cursor.fetchone()
        if not job_row:
            _raise_error(w_procnm, '115', f"{w_parm}::No active job found")
        
        jobid, mapref, trgschm, trgtbnm, trgtbtyp, tbnam, blkprcrows, chkpntstrtgy, chkpntclnm, chkpntenbld = job_row
        
        # Generate complete Python code using the code builder
        debug(f"[DEBUG create_job_flow] About to import build_job_flow_code")
        # Support both FastAPI (package import) and legacy Flask (relative import) contexts
        try:
            from backend.modules.jobs.pkgdwjob_create_job_flow import build_job_flow_code
        except ImportError:  # When running Flask app.py directly inside backend
            from modules.jobs.pkgdwjob_create_job_flow import build_job_flow_code  # type: ignore
        debug(f"[DEBUG create_job_flow] Successfully imported build_job_flow_code")
        
        debug(f"[DEBUG create_job_flow] About to call build_job_flow_code with parameters:")
        debug(f"  mapref={mapref}, jobid={jobid}, trgschm={trgschm}, trgtbnm={trgtbnm}")
        debug(f"  trgtbtyp={trgtbtyp}, tbnam={tbnam}, blkprcrows={blkprcrows}, w_limit={w_limit}")
        debug(f"  chkpntstrtgy={chkpntstrtgy}, chkpntclnm={chkpntclnm}, chkpntenbld={chkpntenbld}")
        
        try:
            python_code = build_job_flow_code(
                connection=connection,
                mapref=mapref,
                jobid=jobid,
                trgschm=trgschm,
                trgtbnm=trgtbnm,
                trgtbtyp=trgtbtyp,
                tbnam=tbnam,
                blkprcrows=blkprcrows,
                w_limit=w_limit,
                chkpntstrtgy=chkpntstrtgy,
                chkpntclnm=chkpntclnm,
                chkpntenbld=chkpntenbld
            )
            debug(f"[DEBUG create_job_flow] Successfully generated {len(python_code)} characters of Python code")
        except Exception as code_gen_err:
            error(f"[DEBUG create_job_flow] ERROR in build_job_flow_code for mapref: {mapref}")
            error(f"[DEBUG create_job_flow] Error type: {type(code_gen_err).__name__}")
            error(f"[DEBUG create_job_flow] Error message: {str(code_gen_err)}")
            error(f"[DEBUG create_job_flow] Error traceback:")
            error(traceback.format_exc())
            raise  # Re-raise to be caught by outer exception handler
        
        # Store the generated Python code in DMS_JOBFLW
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                SELECT jobflwid, dwlogic
                FROM {schema}.DMS_JOBFLW
                WHERE mapref = %s
                  AND curflg = 'Y'
            """, (p_mapref,))
        else:  # Oracle
            cursor.execute(f"""
                SELECT jobflwid, dwlogic
                FROM {schema}.DMS_JOBFLW
                WHERE mapref = :mapref
                  AND curflg = 'Y'
            """, {'mapref': p_mapref})
        
        flw_row = cursor.fetchone()
        
        w_res = 1  # Assume change needed
        
        if flw_row:
            jobflwid, dwlogic = flw_row
            # Compare existing logic with new logic
            if dwlogic:
                existing_code = dwlogic.read() if hasattr(dwlogic, 'read') else str(dwlogic)
                if existing_code == python_code:
                    w_res = 0  # No change
        
        if w_res != 0:
            # Mark existing flow as inactive
            if flw_row:
                if db_type == "POSTGRESQL":
                    cursor.execute(f"""
                        UPDATE {schema}.DMS_JOBFLW
                        SET curflg = 'N'
                        WHERE curflg = 'Y'
                          AND jobflwid = %s
                    """, (flw_row[0],))
                else:  # Oracle
                    cursor.execute(f"""
                        UPDATE {schema}.DMS_JOBFLW
                        SET curflg = 'N'
                        WHERE curflg = 'Y'
                          AND jobflwid = :jobflwid
                    """, {'jobflwid': flw_row[0]})
            
            # Generate job flow ID using ID provider (supports Oracle/PostgreSQL)
            jobflwid = get_next_id(cursor, f"{schema}.DMS_JOBFLWSEQ")
            
            # Insert new job flow - handle PostgreSQL TEXT vs Oracle CLOB differently
            if db_type == "POSTGRESQL":
                # PostgreSQL: Use TEXT type directly
                cursor.execute(f"""
                    INSERT INTO {schema}.DMS_JOBFLW (
                        jobflwid, jobid, mapref, trgschm, trgtbtyp, trgtbnm,
                        dwlogic, stflg, recrdt, recupdt, curflg
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, 'A', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y'
                    )
                """, (
                    jobflwid,
                    jobid,
                    mapref,
                    trgschm,
                    trgtbtyp,
                    trgtbnm,
                    python_code if python_code else ''
                ))
                print(f"Python code ({len(python_code) if python_code else 0} chars) written to TEXT field for jobflwid={jobflwid}")
            else:  # Oracle
                # Oracle: Use CLOB with RETURNING clause
                clob_var = cursor.var(oracledb.DB_TYPE_CLOB)
                
                # Insert the record first without the CLOB
                cursor.execute(f"""
                    INSERT INTO {schema}.DMS_JOBFLW (
                        jobflwid, jobid, mapref, trgschm, trgtbtyp, trgtbnm,
                        dwlogic, stflg, recrdt, recupdt, curflg
                    )
                    VALUES (
                        :jobflwid, :jobid, :mapref, :trgschm, :trgtbtyp, :trgtbnm,
                        EMPTY_CLOB(), 'A', SYSDATE, SYSDATE, 'Y'
                    )
                    RETURNING dwlogic INTO :clob_var
                """, {
                    'jobflwid': jobflwid,
                    'jobid': jobid,
                    'mapref': mapref,
                    'trgschm': trgschm,
                    'trgtbtyp': trgtbtyp,
                    'trgtbnm': trgtbnm,
                    'clob_var': clob_var
                })
                
                # Now write the Python code to the CLOB
                if python_code:
                    clob_obj = clob_var.getvalue()[0]
                    if clob_obj:
                        # Write the Python code to CLOB
                        clob_obj.write(python_code)
                        print(f"Python code ({len(python_code)} chars) written to CLOB for jobflwid={jobflwid}")
            
            print(f"Job flow created successfully for {p_mapref}")
        else:
            print(f"Job flow unchanged for {p_mapref}")
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(connection, 'autocommit', False):
            connection.commit()
        elif db_type == "ORACLE":
            connection.commit()
        
    except Exception as e:
        if connection:
            connection.rollback()
        _raise_error(w_procnm, '141', w_parm, e)
    finally:
        if cursor:
            cursor.close()


def create_all_jobs(connection):
    """
    Create jobs for all active mappings.
    Python equivalent of CREATE_ALL_JOBS procedure.
    
    Args:
        connection: Oracle database connection
    """
    w_procnm = 'create_all_jobs'
    
    cursor = None
    
    try:
        cursor = connection.cursor()
        schema = os.getenv('DMS_SCHEMA', 'TRG')
        
        # Get all active mappings
        query = f"""
            SELECT mapref FROM {schema}.DMS_MAPR
            WHERE curflg = 'Y'
              AND lgvrfyflg = 'Y'
              AND stflg = 'A'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            mapref = row[0]
            try:
                print(f"\nProcessing mapping: {mapref}")
                jobid = create_update_job(connection, mapref)
                print(f"Job created/updated for {mapref}: JobID={jobid}")
            except Exception as e:
                print(f"Error processing {mapref}: {str(e)}")
                # Continue with next mapping
        
        print(f"\nProcessed {len(rows)} mappings")
        
    except Exception as e:
        _raise_error(w_procnm, '114', '', e)
    finally:
        if cursor:
            cursor.close()

