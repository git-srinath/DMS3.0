"""
CREATE_JOB_FLOW implementation - Dynamic Python code generator with hash-based change detection.
This module handles the complex logic of generating ETL Python code.

This is extracted from pkgdms_job_python.py for better maintainability.
"""

import os
from typing import Dict, List, Tuple
from datetime import datetime
from modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name


def _get_postgresql_table_name(cursor, schema_name: str, table_name: str) -> str:
    """Wrapper for backward compatibility - delegates to common utility"""
    return get_postgresql_table_name(cursor, schema_name, table_name)


def build_job_flow_code(
    connection,
    mapref: str,
    jobid: int,
    trgschm: str,
    trgtbnm: str,
    trgtbtyp: str,
    tbnam: str,
    blkprcrows: int,
    w_limit: int,
    chkpntstrtgy: str = 'AUTO',
    chkpntclnm: str = None,
    chkpntenbld: str = 'Y'
) -> str:
    """
    Build the complete Python code for job execution with hash-based change detection
    and checkpoint/restart capability.
    
    Args:
        connection: Database connection
        mapref: Mapping reference
        jobid: Job ID
        trgschm: Target schema
        trgtbnm: Target table name
        trgtbtyp: Target table type (DIM, FCT, MRT)
        tbnam: Full table name (schema.table)
        blkprcrows: Bulk processing rows
        w_limit: Default limit for bulk processing
        chkpntstrtgy: Checkpoint strategy ('AUTO', 'KEY', 'PYTHON', 'NONE')
        chkpntclnm: Column name for KEY strategy (sequential/monotonic)
        chkpntenbld: Enable checkpoint ('Y'/'N')
        
    Returns:
        Complete Python code as string
    """
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    
    # Determine bind variable syntax and timestamp function based on database type
    if db_type == "POSTGRESQL":
        bind_var_prefix = "%s"
        timestamp_func = "CURRENT_TIMESTAMP"
        # For PostgreSQL, we'll use positional parameters in execute()
        checkpoint_update_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET PARAM1 = %s
                                WHERE sessionid = %s
                                  AND prcid = %s
                            """
        progress_update_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET SRCROWS = %s,
                                    TRGROWS = %s,
                                    RECUPDT = CURRENT_TIMESTAMP
                                WHERE sessionid = %s
                                  AND prcid = %s
                            """
        checkpoint_complete_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET PARAM1 = 'COMPLETED'
                                WHERE sessionid = %s
                                  AND prcid = %s
                            """
    else:  # Oracle
        bind_var_prefix = ":param"
        timestamp_func = "SYSTIMESTAMP"
        checkpoint_update_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET PARAM1 = :checkpoint_value
                                WHERE sessionid = :sessionid
                                  AND prcid = :prcid
                            """
        progress_update_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET SRCROWS = :srcrows,
                                    TRGROWS = :trgrows,
                                    RECUPDT = SYSTIMESTAMP
                                WHERE sessionid = :sessionid
                                  AND prcid = :prcid
                            """
        checkpoint_complete_query = """
                                UPDATE {table_prefix}DMS_PRCLOG
                                SET PARAM1 = 'COMPLETED'
                                WHERE sessionid = :sessionid
                                  AND prcid = :prcid
                            """
    
    # Get metadata schema name from environment (for DMS_JOB, DMS_JOBDTL, DMS_PARAMS)
    # The target schema will come from job configuration (trgschm)
    schema = os.getenv('DMS_SCHEMA', 'TRG')
    
    # For PostgreSQL, detect actual table name format (could be lowercase or uppercase)
    # For Oracle, keep as-is (case-insensitive)
    if db_type == "POSTGRESQL":
        schema_quoted = schema.lower()
        # Detect actual table names as stored in PostgreSQL (handles both quoted and unquoted)
        # Try to detect table names, but handle errors gracefully
        try:
            dms_job_table = _get_postgresql_table_name(cursor, schema_quoted, 'DMS_JOB')
            dms_jobdtl_table = _get_postgresql_table_name(cursor, schema_quoted, 'DMS_JOBDTL')
            dms_maprsql_table = _get_postgresql_table_name(cursor, schema_quoted, 'DMS_MAPRSQL')
            dms_params_table = _get_postgresql_table_name(cursor, schema_quoted, 'DMS_PARAMS')
            # Quote table names if they contain uppercase letters (were created with quotes)
            dms_job_ref = f'"{dms_job_table}"' if dms_job_table != dms_job_table.lower() else dms_job_table
            dms_jobdtl_ref = f'"{dms_jobdtl_table}"' if dms_jobdtl_table != dms_jobdtl_table.lower() else dms_jobdtl_table
            dms_maprsql_ref = f'"{dms_maprsql_table}"' if dms_maprsql_table != dms_maprsql_table.lower() else dms_maprsql_table
            dms_params_ref = f'"{dms_params_table}"' if dms_params_table != dms_params_table.lower() else dms_params_table
        except Exception:
            # If detection fails, fall back to lowercase (most common case)
            dms_job_ref = 'dms_job'
            dms_jobdtl_ref = 'dms_jobdtl'
            dms_maprsql_ref = 'dms_maprsql'
            dms_params_ref = 'dms_params'
        # Build table prefix/suffix for dynamic queries
        table_prefix = f'{schema_quoted}.'
        table_suffix = ''
    else:
        schema_quoted = schema
        table_prefix = f'{schema}.'
        table_suffix = ''
        # For Oracle, use uppercase table names (case-insensitive, but convention is uppercase)
        dms_job_ref = 'DMS_JOB'
        dms_jobdtl_ref = 'DMS_JOBDTL'
        dms_maprsql_ref = 'DMS_MAPRSQL'
        dms_params_ref = 'DMS_PARAMS'
    
    # Get primary key columns
    # Get primary key columns with their source column mappings
    # trgclnm = target column name (e.g., ACNT_NO)
    # keyclnm = source column name (e.g., COD_ACCT_NO) that maps to the target PK
    if db_type == "POSTGRESQL":
        cursor.execute(f"""
            SELECT jd.trgclnm, jd.keyclnm
            FROM {table_prefix}{dms_jobdtl_ref}{table_suffix} jd
            WHERE jd.mapref = %s
              AND jd.curflg = 'Y'
              AND jd.trgkeyflg = 'Y'
            ORDER BY jd.trgkeyseq
        """, (mapref,))
    else:  # Oracle
        cursor.execute(f"""
            SELECT jd.trgclnm, jd.keyclnm
            FROM {schema}.{dms_jobdtl_ref} jd
            WHERE jd.mapref = :mapref
              AND jd.curflg = 'Y'
              AND jd.trgkeyflg = 'Y'
            ORDER BY jd.trgkeyseq
        """, {'mapref': mapref})
    
    pk_mappings = cursor.fetchall()
    pk_columns = [row[0] for row in pk_mappings]  # Target column names
    # Build mapping: target_col -> source_col
    pk_source_mapping = {row[0]: (row[1] if row[1] else row[0]) for row in pk_mappings}
    # If keyclnm is None/empty, use trgclnm as fallback (assumes same name)
    
    # Get all target columns in execution order
    if db_type == "POSTGRESQL":
        cursor.execute(f"""
            SELECT j.jobid, j.mapref, j.trgschm, j.trgtbnm, j.trgtbtyp, jd.trgclnm
            FROM {table_prefix}{dms_job_ref}{table_suffix} j
            JOIN {table_prefix}{dms_jobdtl_ref}{table_suffix} jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
            WHERE j.mapref = %s
              AND j.stflg = 'A'
              AND j.curflg = 'Y'
            ORDER BY jd.excseq
        """, (mapref,))
    else:  # Oracle
        cursor.execute(f"""
            SELECT j.jobid, j.mapref, j.trgschm, j.trgtbnm, j.trgtbtyp, jd.trgclnm
            FROM {schema}.{dms_job_ref} j
            JOIN {schema}.{dms_jobdtl_ref} jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
            WHERE j.mapref = :mapref
              AND j.stflg = 'A'
              AND j.curflg = 'Y'
            ORDER BY jd.excseq
        """, {'mapref': mapref})
    
    all_columns = [row[5] for row in cursor.fetchall()]
    
    # Build mapping from target columns to source columns (VALCLNM holds source column names)
    if db_type == "POSTGRESQL":
        cursor.execute(f"""
            SELECT jd.trgclnm, jd.valclnm
            FROM {table_prefix}{dms_jobdtl_ref}{table_suffix} jd
            WHERE jd.mapref = %s
              AND jd.curflg = 'Y'
        """, (mapref,))
    else:  # Oracle
        cursor.execute(f"""
            SELECT jd.trgclnm, jd.valclnm
            FROM {schema}.{dms_jobdtl_ref} jd
            WHERE jd.mapref = :mapref
              AND jd.curflg = 'Y'
        """, {'mapref': mapref})
    column_source_mapping = {}
    for target_col, source_col in cursor.fetchall():
        column_source_mapping[target_col] = source_col if source_col else target_col
    
    # Ensure mandatory columns (hash + dimension audit columns) are present even
    # if they are not listed in DMS_JOBDTL metadata
    mandatory_columns = ['RWHKEY']
    if trgtbtyp.upper() == 'DIM':
        mandatory_columns.extend(['CURFLG', 'FROMDT', 'TODT'])
    for mandatory in mandatory_columns:
        if mandatory not in all_columns:
            all_columns.append(mandatory)
        column_source_mapping.setdefault(mandatory, mandatory)
    
    # Get combination codes (mapping logic groups)
    if db_type == "POSTGRESQL":
        cursor.execute(f"""
            SELECT jd.mapcmbcd, 
                   MIN(COALESCE(jd.trgkeyseq, 9999)) as kseq,
                   COALESCE(jd.scdtyp, 1) as scdtyp,
                   MAX(jd.excseq) as maxexcseq
            FROM {table_prefix}{dms_jobdtl_ref}{table_suffix} jd
            WHERE jd.mapref = %s
              AND jd.curflg = 'Y'
              AND jd.mapcmbcd IS NOT NULL
            GROUP BY jd.mapcmbcd, COALESCE(jd.scdtyp, 1)
            ORDER BY MIN(CASE WHEN jd.trgkeyseq IS NOT NULL THEN 1 ELSE 2 END),
                     MAX(jd.excseq),
                     COALESCE(jd.scdtyp, 1) DESC
        """, (mapref,))
    else:  # Oracle
        cursor.execute(f"""
            SELECT jd.mapcmbcd, 
                   MIN(NVL(jd.trgkeyseq, 9999)) as kseq,
                   NVL(jd.scdtyp, 1) as scdtyp,
                   MAX(jd.excseq) as maxexcseq
            FROM {schema}.{dms_jobdtl_ref} jd
            WHERE jd.mapref = :mapref
              AND jd.curflg = 'Y'
              AND jd.mapcmbcd IS NOT NULL
            GROUP BY jd.mapcmbcd, NVL(jd.scdtyp, 1)
            ORDER BY MIN(CASE WHEN jd.trgkeyseq IS NOT NULL THEN 1 ELSE 2 END),
                     MAX(jd.excseq),
                     NVL(jd.scdtyp, 1) DESC
        """, {'mapref': mapref})
    
    combinations = cursor.fetchall()
    
    # Build the Python code
    code_parts = []
    
    # Determine effective checkpoint strategy
    effective_strategy = chkpntstrtgy if chkpntstrtgy else 'AUTO'
    if effective_strategy == 'AUTO':
        # Auto-detect: Use KEY if column specified, else PYTHON
        effective_strategy = 'KEY' if chkpntclnm else 'PYTHON'
    
    checkpoint_enabled = (chkpntenbld == 'Y')
    
    # Ensure schema name is uppercase for Oracle (schema names are case-sensitive)
    trgschm_upper = trgschm.upper()
    full_table_name = f"{trgschm_upper}.{trgtbnm}"
    
    # Header
    code_parts.append(f'''"""
Auto-generated ETL Job for {mapref}
Target: {full_table_name}
Type: {trgtbtyp}
Hash Algorithm: MD5 with pipe (|) delimiter
NULL Marker: <NULL>
Checkpoint Strategy: {effective_strategy}
Checkpoint Enabled: {checkpoint_enabled}
"""

import oracledb
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from modules.common.id_provider import next_id as get_next_id

# Job configuration
MAPREF = "{mapref}"
JOBID = {jobid}
TARGET_SCHEMA = "{trgschm}"
TARGET_TABLE = "{trgtbnm}"
TARGET_TYPE = "{trgtbtyp}"
# Full table name with uppercase schema for Oracle
FULL_TABLE_NAME = "{full_table_name}"
BULK_LIMIT = {blkprcrows if blkprcrows else w_limit}
# Commit frequency: commit target connection every N batches to avoid long transactions
# Default: commit every 5 batches (or every 25,000 rows if BULK_LIMIT is 5,000)
COMMIT_FREQUENCY = max(1, 5)  # Commit every 5 batches

# Checkpoint configuration
CHECKPOINT_ENABLED = {str(checkpoint_enabled)}
CHECKPOINT_STRATEGY = "{effective_strategy}"
CHECKPOINT_COLUMN = "{chkpntclnm if chkpntclnm else ''}"
# Parse checkpoint columns (supports comma-separated composite keys)
CHECKPOINT_COLUMNS = [col.strip().upper() for col in CHECKPOINT_COLUMN.split(',')] if CHECKPOINT_COLUMN else []

# Primary key columns (target column names)
PK_COLUMNS = {pk_columns}
# Mapping from target PK column names to source column names
# Format: {{'TARGET_COL': 'SOURCE_COL', ...}}
PK_SOURCE_MAPPING = {pk_source_mapping}

# All target columns (in execution order)
ALL_COLUMNS = {all_columns}

# Mapping from target columns to source columns
COLUMN_SOURCE_MAPPING = {column_source_mapping}

# Columns to exclude from hash calculation
HASH_EXCLUDE_COLUMNS = {{'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG', 'FROMDT', 'TODT', 'VALDFRM', 'VALDTO'}}

def map_row_to_target_columns(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a source row dictionary so keys match target column names.
    Maps ALL target columns (from ALL_COLUMNS) to their source values.
    Uses COLUMN_SOURCE_MAPPING for preferred source column names and falls back
    to case-insensitive matches on both source and target column names.
    """
    normalized = dict()
    upper_row = dict((k.upper(), v) for k, v in row_dict.items() if isinstance(k, str))
    
    # Process ALL target columns, not just those in COLUMN_SOURCE_MAPPING
    for target_col in ALL_COLUMNS:
        # First, try to get source column name from mapping
        source_col = COLUMN_SOURCE_MAPPING.get(target_col, target_col)
        
        # Try to get value using source column name
        value = row_dict.get(source_col)
        if value is None and isinstance(source_col, str):
            value = upper_row.get(source_col.upper())
        
        # If still None, try target column name directly (for columns with same name)
        if value is None:
            value = row_dict.get(target_col)
            if value is None and isinstance(target_col, str):
                value = upper_row.get(target_col.upper())
        
        # Store the value (even if None) - this ensures all target columns are present
        normalized[target_col] = value
    
    return normalized


def generate_hash(row_dict: Dict[str, Any], column_order: List[str] = None) -> str:
    """
    Generate MD5 hash from row data.
    
    Args:
        row_dict: Dictionary of column_name -> value
        column_order: Order of columns for hash (uses execution order if None)
        
    Returns:
        32-character MD5 hash
    """
    if column_order is None:
        column_order = ALL_COLUMNS
    
    # Filter out audit columns and build concatenated string
    parts = []
    for col in column_order:
        if col.upper() not in HASH_EXCLUDE_COLUMNS:
            val = row_dict.get(col)
            if val is None:
                parts.append('<NULL>')
            elif isinstance(val, datetime):
                parts.append(val.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                parts.append(str(val))
    
    concat_str = '|'.join(parts)
    return hashlib.md5(concat_str.encode('utf-8')).hexdigest()


def execute_job(metadata_connection, source_connection, target_connection, session_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute ETL job for {mapref}.
    
    Args:
        metadata_connection: Oracle database connection for metadata tables (DMS_JOBLOG, DMS_PRCLOG, DMS_JOBERR)
        source_connection: Oracle database connection for source tables (SELECT queries)
        target_connection: Oracle database connection for target tables (INSERT/UPDATE operations)
        session_params: Session parameters from DMS_PRCLOG
        
    Returns:
        Dictionary with execution results
    """
    import sys
    print("=" * 80, flush=True)
    print(f"EXECUTE_JOB STARTED for {{MAPREF}}", flush=True)
    print(f"  metadata_connection: {{type(metadata_connection).__name__}}", flush=True)
    print(f"  source_connection: {{type(source_connection).__name__}}", flush=True)
    print(f"  target_connection: {{type(target_connection).__name__}}", flush=True)
    print(f"  session_params keys: {{list(session_params.keys())}}", flush=True)
    print("=" * 80, flush=True)
    sys.stdout.flush()
    
    metadata_cursor = None
    source_cursor = None
    target_cursor = None
    
    try:
        # Validate connections before use
        print("Validating connections...", flush=True)
        sys.stdout.flush()
        if not metadata_connection:
            raise RuntimeError("metadata_connection is None or invalid")
        if not source_connection:
            raise RuntimeError("source_connection is None or invalid")
        if not target_connection:
            raise RuntimeError("target_connection is None or invalid")
        print("All connections validated successfully", flush=True)
        sys.stdout.flush()
        
        # Create separate cursors for metadata, source, and target operations
        print("Creating cursors for metadata, source, and target connections...", flush=True)
        sys.stdout.flush()
        metadata_cursor = metadata_connection.cursor()
        print("Metadata cursor created successfully", flush=True)
        sys.stdout.flush()
        
        source_cursor = source_connection.cursor()
        print("Source cursor created successfully", flush=True)
        sys.stdout.flush()
        
        target_cursor = target_connection.cursor()
        print("Target cursor created successfully", flush=True)
        sys.stdout.flush()
        
        # Initialize counters
        source_count = 0
        target_count = 0
        error_count = 0
        
        # Get session information
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        joblogid = None  # Maintained for backward compatibility in return payload
        
        print(f"Session info - PRCID: {{prcid}}, SESSIONID: {{sessionid}}")
        
        # Log target table information for debugging
        print(f"Target Schema: {{TARGET_SCHEMA}}")
        print(f"Target Table: {{TARGET_TABLE}}")
        print(f"Full Table Name: {{FULL_TABLE_NAME}}")
        
        def log_batch_progress(batch_number: int, batch_source_rows: int, batch_target_rows: int, batch_error_rows: int):
            """
            Insert batch-level statistics into DMS_JOBLOG so the UI can display accurate
            progress information. Each call records a single batch.
            """
            try:
                joblog_id = get_next_id(metadata_cursor, "DMS_JOBLOGSEQ")
                metadata_cursor.execute("""
                    INSERT INTO DMS_JOBLOG (
                        joblogid, prcdt, mapref, jobid,
                        srcrows, trgrows, errrows,
                        reccrdt, prcid, sessionid
                    ) VALUES (
                        :joblogid, SYSTIMESTAMP, :mapref, :jobid,
                        :srcrows, :trgrows, :errrows,
                        SYSTIMESTAMP, :prcid, :sessionid
                    )
                """, {{
                    'joblogid': joblog_id,
                    'mapref': MAPREF,
                    'jobid': JOBID,
                    'srcrows': batch_source_rows,
                    'trgrows': batch_target_rows,
                    'errrows': batch_error_rows,
                    'prcid': prcid,
                    'sessionid': sessionid
                }})
            except Exception as log_err:
                print(f"WARNING: Could not log batch {{batch_number}} to DMS_JOBLOG: {{log_err}}")
        
        # Check for stop request immediately at start
        try:
            metadata_cursor.execute("""
                SELECT COUNT(*) FROM DMS_PRCREQ
                WHERE mapref = :mapref
                  AND request_type = 'STOP'
                  AND status IN ('NEW', 'CLAIMED')
            """, {{'mapref': MAPREF}})
            stop_count = metadata_cursor.fetchone()[0]
            if stop_count > 0:
                print(f"STOP request detected for {{MAPREF}} at job start. Exiting immediately.")
                return {{
                    'status': 'STOPPED',
                    'source_rows': 0,
                    'target_rows': 0,
                    'error_rows': 0,
                    'message': 'Job stopped by user request before processing started'
                }}
        except Exception as e:
            print(f"WARNING: Could not check stop request at start: {{e}}")
        
        # Verify table exists and is accessible (using target connection)
        try:
            check_table_query = f"""
                SELECT COUNT(*) 
                FROM {{FULL_TABLE_NAME}}
                WHERE ROWNUM <= 1
            """
            target_cursor.execute(check_table_query)
            print(f"Table {{FULL_TABLE_NAME}} is accessible via target connection")
        except Exception as e:
            error_msg = f"Table {{FULL_TABLE_NAME}} is not accessible: {{str(e)}}"
            print(f"ERROR: {{error_msg}}")
            # Try alternative: check if table exists in all_tables (using target connection)
            try:
                target_cursor.execute("""
                    SELECT owner, table_name 
                    FROM all_tables 
                    WHERE owner = UPPER(:owner) AND table_name = UPPER(:tname)
                """, {{
                    'owner': TARGET_SCHEMA,
                    'tname': TARGET_TABLE
                }})
                alt_result = target_cursor.fetchone()
                if alt_result:
                    print(f"Table exists: {{alt_result[0]}}.{{alt_result[1]}}")
                else:
                    print(f"ERROR: Table {{TARGET_SCHEMA}}.{{TARGET_TABLE}} not found in all_tables")
            except Exception as e2:
                print(f"ERROR: Could not check all_tables: {{str(e2)}}")
            raise RuntimeError(error_msg) from e
        
        # Check for checkpoint (resume from previous run)
        checkpoint_value = session_params.get('param1')
        rows_to_skip = 0
        checkpoint_values = []  # For composite keys
        
        if CHECKPOINT_ENABLED and checkpoint_value:
            if checkpoint_value == 'COMPLETED':
                print("Job already completed successfully. Restarting from beginning.")
                checkpoint_value = None
            else:
                if CHECKPOINT_STRATEGY == 'PYTHON':
                    try:
                        rows_to_skip = int(checkpoint_value)
                        print(f"Resuming: Will skip {{rows_to_skip}} already-processed rows")
                    except ValueError:
                        print(f"Invalid checkpoint value: {{checkpoint_value}}. Starting fresh.")
                        checkpoint_value = None
                elif CHECKPOINT_STRATEGY == 'KEY' and CHECKPOINT_COLUMNS:
                    # Parse checkpoint value for composite keys (pipe-separated)
                    if len(CHECKPOINT_COLUMNS) > 1:
                        checkpoint_values = checkpoint_value.split('|')
                        if len(checkpoint_values) != len(CHECKPOINT_COLUMNS):
                            print(f"Invalid composite checkpoint value: {{checkpoint_value}}. Expected {{len(CHECKPOINT_COLUMNS)}} values separated by '|'. Starting fresh.")
                            checkpoint_value = None
                            checkpoint_values = []
                        else:
                            print(f"Resuming: Checkpoint at composite key {{CHECKPOINT_COLUMNS}} > {{checkpoint_values}}")
                    else:
                        print(f"Resuming: Checkpoint at {{CHECKPOINT_COLUMN}} > {{checkpoint_value}}")
        else:
            if CHECKPOINT_ENABLED:
                print("No checkpoint found. Starting fresh.")
            else:
                print("Checkpoint disabled. Processing all data.")
        
        # Execute ETL logic
''')
    
    # Generate code for each combination
    for idx, (mapcmbcd, kseq, scdtyp, maxexcseq) in enumerate(combinations, 1):
        # Get details for this combination
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                SELECT j.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
                       jd.trgclnm, jd.trgcldtyp, jd.maplogic, jd.trgkeyflg,
                       jd.keyclnm, jd.valclnm, jd.mapcmbcd, jd.excseq,
                       p.prval, jd.maprsqlcd, s.MAPRSQL, s.sqlconid
                FROM {table_prefix}{dms_job_ref}{table_suffix} j
                JOIN {table_prefix}{dms_jobdtl_ref}{table_suffix} jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
                LEFT JOIN {table_prefix}{dms_maprsql_ref}{table_suffix} s ON s.maprsqlcd = jd.maprsqlcd AND s.curflg = 'Y'
                JOIN {table_prefix}{dms_params_ref}{table_suffix} p ON p.prtyp = 'Datatype' AND p.prcd = jd.trgcldtyp
                WHERE j.jobid = %s
                  AND j.stflg = 'A'
                  AND j.curflg = 'Y'
                  AND COALESCE(jd.scdtyp, 1) = %s
                  AND COALESCE(jd.mapcmbcd, '#') = COALESCE(%s, '#')
                ORDER BY CASE WHEN jd.trgkeyseq IS NOT NULL THEN 1 ELSE 2 END, jd.excseq
            """, (jobid, scdtyp, mapcmbcd))
        else:  # Oracle
            cursor.execute(f"""
                SELECT j.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
                       jd.trgclnm, jd.trgcldtyp, jd.maplogic, jd.trgkeyflg,
                       jd.keyclnm, jd.valclnm, jd.mapcmbcd, jd.excseq,
                       p.prval, jd.maprsqlcd, s.MAPRSQL, s.sqlconid
                FROM {schema}.DMS_JOB j
                JOIN {schema}.DMS_JOBDTL jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
                LEFT JOIN {schema}.DMS_MAPRSQL s ON s.maprsqlcd = jd.maprsqlcd AND s.curflg = 'Y'
                JOIN {schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' AND p.prcd = jd.trgcldtyp
                WHERE j.jobid = :jobid
                  AND j.stflg = 'A'
                  AND j.curflg = 'Y'
                  AND NVL(jd.scdtyp, 1) = :scdtyp
                  AND NVL(jd.mapcmbcd, '#') = NVL(:mapcmbcd, '#')
                ORDER BY CASE WHEN jd.trgkeyseq IS NOT NULL THEN 1 ELSE 2 END, jd.excseq
            """, {'jobid': jobid, 'scdtyp': scdtyp, 'mapcmbcd': mapcmbcd})
        
        combo_details = cursor.fetchall()
        
        if not combo_details:
            continue
        
        # Read maplogic from first detail (index 6) - it might be a code reference or actual SQL
        maplogic_lob = combo_details[0][6]
        maplogic_value = ''
        if maplogic_lob:
            # Handle LOB reading
            if hasattr(maplogic_lob, 'read'):
                maplogic_value = maplogic_lob.read()
                if isinstance(maplogic_value, bytes):
                    maplogic_value = maplogic_value.decode('utf-8')
            else:
                maplogic_value = str(maplogic_lob) if maplogic_lob else ''
        
        # Read MAPRSQL (index 14) - this contains the actual SQL query
        # Read sqlconid (index 15) - this is the source connection ID
        # Note: index 13 is jd.maprsqlcd (the code), index 14 is s.MAPRSQL (the actual SQL), index 15 is s.sqlconid (source connection ID)
        dms_maprsql_lob = combo_details[0][14] if len(combo_details[0]) > 14 else None
        sqlconid = combo_details[0][15] if len(combo_details[0]) > 15 else None
        dms_maprsql_value = ''
        if dms_maprsql_lob:
            # Handle LOB reading
            if hasattr(dms_maprsql_lob, 'read'):
                dms_maprsql_value = dms_maprsql_lob.read()
                if isinstance(dms_maprsql_value, bytes):
                    dms_maprsql_value = dms_maprsql_value.decode('utf-8')
            else:
                dms_maprsql_value = str(dms_maprsql_lob) if dms_maprsql_lob else ''
        
        # Determine which SQL to use:
        # - If maplogic looks like actual SQL (contains SELECT, FROM, etc.), use it
        # - Otherwise, maplogic is likely a code reference, so use MAPRSQL
        maplogic_upper = maplogic_value.upper().strip() if maplogic_value else ''
        is_actual_sql = any(keyword in maplogic_upper for keyword in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'MERGE'])
        
        if is_actual_sql:
            # maplogic contains actual SQL
            maplogic_sql = maplogic_value.strip()
        elif dms_maprsql_value and dms_maprsql_value.strip():
            # maplogic is a code reference, use MAPRSQL
            maplogic_sql = dms_maprsql_value.strip()
        elif maplogic_value and maplogic_value.strip():
            # Fallback: use maplogic even if it doesn't look like SQL (might be valid)
            maplogic_sql = maplogic_value.strip()
        else:
            raise ValueError(
                f"No SQL query found for combination {mapcmbcd} (mapref={mapref}). "
                f"maplogic='{maplogic_value[:50] if maplogic_value else 'None'}', "
                f"MAPRSQL={'present' if dms_maprsql_lob else 'None'}"
            )
        
        # Escape triple quotes in SQL if present (to avoid breaking Python string)
        maplogic_sql_escaped = maplogic_sql.replace('"""', '\\"\\"\\"')
        
        # Generate code for this combination
        # Escape the SQL properly for Python string literal
        # Replace newlines and handle special characters
        maplogic_for_code = maplogic_sql_escaped.replace('\\', '\\\\').replace('"', '\\"')
        
        code_parts.append(f'''
        # ===== Combination {idx}: {mapcmbcd if mapcmbcd else 'DEFAULT'} (SCD Type {scdtyp}) =====
        print("Processing combination: {mapcmbcd if mapcmbcd else 'DEFAULT'}")
        CURRENT_SCD_TYPE = {scdtyp}
        print(f"SCD Type for this combination: {{CURRENT_SCD_TYPE}}")
        
        # Build source query with checkpoint support
        base_source_query = """{maplogic_for_code}"""
        print(f"Base source query prepared (length: {{len(base_source_query)}} characters)")
        
        # Apply checkpoint strategy
        print(f"Checkpoint config - ENABLED: {{CHECKPOINT_ENABLED}}, STRATEGY: {{CHECKPOINT_STRATEGY}}, COLUMNS: {{CHECKPOINT_COLUMNS}}")
        if CHECKPOINT_ENABLED and CHECKPOINT_STRATEGY == 'KEY' and CHECKPOINT_COLUMNS:
            if len(CHECKPOINT_COLUMNS) > 1:
                # Composite key: Use tuple comparison
                if checkpoint_values:
                    # Build WHERE clause for composite key using tuple comparison
                    # Format: WHERE (COL1, COL2, ...) > (val1, val2, ...)
                    columns_str = ', '.join(CHECKPOINT_COLUMNS)
                    placeholders = ', '.join([f':checkpoint_val_{{i}}' for i in range(len(CHECKPOINT_COLUMNS))])
                    order_by_str = ', '.join(CHECKPOINT_COLUMNS)
                    
                    source_query = "SELECT * FROM (\\n" + base_source_query + "\\n) source_data\\n" + \\
                        "WHERE (" + columns_str + ") > (" + placeholders + ")\\n" + \\
                        "ORDER BY " + order_by_str
                    
                    # Build bind parameters for composite key
                    bind_params = {{f'checkpoint_val_{{i}}': checkpoint_values[i] for i in range(len(CHECKPOINT_COLUMNS))}}
                    print(f"Executing source query with composite checkpoint...")
                    try:
                        source_cursor.execute(source_query, bind_params)
                        print(f"Applied KEY checkpoint (composite): ({{columns_str}}) > ({{checkpoint_values}})")
                    except Exception as query_err:
                        error_msg = f"Failed to execute source query with composite checkpoint: {{str(query_err)}}"
                        print(f"ERROR: {{error_msg}}")
                        raise RuntimeError(error_msg) from query_err
                else:
                    # No checkpoint value yet, process all data
                    source_query = base_source_query
                    print(f"Executing source query (no checkpoint value yet)...")
                    try:
                        source_cursor.execute(source_query)
                        print("Source query executed successfully (no checkpoint)")
                    except Exception as query_err:
                        error_msg = f"Failed to execute source query: {{str(query_err)}}"
                        print(f"ERROR: {{error_msg}}")
                        raise RuntimeError(error_msg) from query_err
            else:
                # Single column key
                if checkpoint_value:
                    source_query = "SELECT * FROM (\\n" + base_source_query + "\\n) source_data\\n" + \\
                        "WHERE " + CHECKPOINT_COLUMNS[0] + " > :checkpoint_value\\n" + \\
                        "ORDER BY " + CHECKPOINT_COLUMNS[0]
                    print(f"Executing source query with single column checkpoint...")
                    try:
                        source_cursor.execute(source_query, {{'checkpoint_value': checkpoint_value}})
                        print(f"Applied KEY checkpoint: {{CHECKPOINT_COLUMNS[0]}} > {{checkpoint_value}}")
                    except Exception as query_err:
                        error_msg = f"Failed to execute source query with checkpoint: {{str(query_err)}}"
                        print(f"ERROR: {{error_msg}}")
                        raise RuntimeError(error_msg) from query_err
                else:
                    # No checkpoint value yet, process all data
                    source_query = base_source_query
                    print(f"Executing source query (no checkpoint value yet, single column)...")
                    try:
                        source_cursor.execute(source_query)
                        print("Source query executed successfully (no checkpoint, single column)")
                    except Exception as query_err:
                        error_msg = f"Failed to execute source query: {{str(query_err)}}"
                        print(f"ERROR: {{error_msg}}")
                        raise RuntimeError(error_msg) from query_err
        else:
            # No checkpoint or PYTHON strategy (skip rows after fetch)
            source_query = base_source_query
            print(f"Executing source query (no checkpoint, PYTHON strategy or skip after fetch)...")
            print(f"Source query length: {{len(source_query)}} characters")
            try:
                source_cursor.execute(source_query)
                print("Source query executed successfully")
            except Exception as query_err:
                error_msg = f"Failed to execute source query: {{str(query_err)}}"
                print(f"ERROR: {{error_msg}}")
                print(f"Source query (first 500 chars): {{source_query[:500]}}")
                raise RuntimeError(error_msg) from query_err
        
        print(f"Source query executed successfully. Fetching column descriptions...")
        try:
            source_columns = [desc[0] for desc in source_cursor.description]
            print(f"Source columns identified: {{len(source_columns)}} columns")
        except Exception as desc_err:
            error_msg = f"Failed to get source cursor description: {{str(desc_err)}}"
            print(f"ERROR: {{error_msg}}")
            raise RuntimeError(error_msg) from desc_err
        
        # Set array size for batch fetching
        # Note: arraysize affects how many rows are fetched at a time internally
        # It doesn't limit the total rows, just optimizes network round trips
        source_cursor.arraysize = BULK_LIMIT
        
        # Skip rows for PYTHON checkpoint strategy
        if CHECKPOINT_ENABLED and CHECKPOINT_STRATEGY == 'PYTHON' and rows_to_skip > 0:
            print(f"Skipping {{rows_to_skip}} rows (PYTHON strategy)...")
            for skip_idx in range(rows_to_skip):
                row = source_cursor.fetchone()
                if not row:
                    print("Reached end of data while skipping. Nothing to process.")
                    break
        
        print(f"Fetching source data in batches of {{BULK_LIMIT}} rows...")
        print(f"Cursor arraysize set to {{BULK_LIMIT}} for optimized fetching")
        
        # Memory-efficient approach: Use fetchmany() to process batches without loading all rows into memory
        # This is critical for large datasets (hundreds of thousands or millions of rows)
        # Strategy:
        # 1. Use fetchmany() to get batches incrementally
        # 2. Process each batch immediately (insert/update operations)
        # 3. Commit metadata connection every batch (for checkpoint tracking)
        # 4. Commit target connection periodically (every COMMIT_FREQUENCY batches)
        # 5. Handle cursor invalidation gracefully - if cursor becomes invalid after commit,
        #    we'll detect it and handle appropriately
        
        # Helper function to check if stop has been requested for this job
        def check_stop_request():
            \"\"\"Check if a stop request exists for this job in DMS_PRCREQ\"\"\"
            try:
                metadata_cursor.execute("""
                    SELECT COUNT(*) 
                    FROM DMS_PRCREQ 
                    WHERE mapref = :mapref 
                      AND request_type = 'STOP' 
                      AND status IN ('NEW', 'CLAIMED')
                """, {{
                    'mapref': MAPREF
                }})
                stop_count = metadata_cursor.fetchone()[0]
                return stop_count > 0
            except Exception as e:
                print(f"WARNING: Could not check stop request: {{e}}")
                return False
        
        # Process source data in batches using fetchmany()
        batch_num = rows_to_skip // BULK_LIMIT if CHECKPOINT_STRATEGY == 'PYTHON' else 0
        total_fetched = 0
        consecutive_empty_batches = 0
        max_consecutive_empty = 3  # Safety check: if 3 consecutive empty batches, stop
        stop_requested = False
        
        print(f"Starting batch processing loop (BULK_LIMIT={{BULK_LIMIT}}, batch_num={{batch_num}})...")
        
        while True:
            # Check for stop request before processing each batch
            if check_stop_request():
                print(f"STOP request detected for {{MAPREF}}. Stopping job gracefully...")
                stop_requested = True
                break
            
            # Fetch batch of rows
            try:
                # Verify cursor is still valid before fetching
                if source_cursor.description is None:
                    print(f"WARNING: Source cursor description is None. Cursor may have been closed.")
                    print(f"Total rows processed before cursor issue: {{total_fetched}}")
                    break
                
                print(f"About to fetch batch {{batch_num + 1}} (BULK_LIMIT={{BULK_LIMIT}})...")
                source_rows = source_cursor.fetchmany(BULK_LIMIT)
                print(f"Fetched {{len(source_rows) if source_rows else 0}} rows in batch {{batch_num + 1}}")
                
                if not source_rows:
                    consecutive_empty_batches += 1
                    if consecutive_empty_batches >= max_consecutive_empty:
                        print(f"No more rows to fetch ({{consecutive_empty_batches}} consecutive empty batches).")
                        print(f"Total rows processed: {{total_fetched}}")
                        break
                    else:
                        # Sometimes fetchmany() can return empty list temporarily, try again
                        continue
                else:
                    consecutive_empty_batches = 0  # Reset counter on successful fetch
                    
            except Exception as fetch_err:
                error_msg = str(fetch_err)
                error_type = type(fetch_err).__name__
                
                # Check for cursor-related errors
                if "does not return rows" in error_msg or "DPY-1003" in error_msg:
                    print(f"Cursor exhausted or invalid: {{error_type}}: {{error_msg}}")
                    print(f"Total rows processed before cursor error: {{total_fetched}}")
                    # This typically means we've processed all rows, so break
                    break
                elif "invalid" in error_msg.lower() or "closed" in error_msg.lower():
                    print(f"Cursor error detected: {{error_type}}: {{error_msg}}")
                    print(f"Total rows processed before cursor error: {{total_fetched}}")
                    # Cursor became invalid - this shouldn't happen with proper commit strategy
                    # but if it does, we'll stop processing
                    break
                else:
                    # Unexpected error - log and break
                    print(f"Unexpected error fetching batch: {{error_type}}: {{error_msg}}")
                    import traceback
                    print(traceback.format_exc())
                    break
            
            # Process this batch
            batch_num += 1
            batch_size = len(source_rows)
            source_count += batch_size
            total_fetched += batch_size
            batch_source_rows = batch_size
            batch_target_rows = 0
            batch_error_start = error_count
            print(f"Processing batch {{batch_num}}: {{batch_size}} rows (total fetched: {{total_fetched}})")
            
            # Check for stop request again before processing batch
            if check_stop_request():
                print(f"STOP request detected for {{MAPREF}} before processing batch {{batch_num}}. Stopping job gracefully...")
                stop_requested = True
                break
            
            # Process current batch
            rows_to_insert = []
            rows_to_update_scd1 = []
            rows_to_update_scd2 = []
            
            for src_row in source_rows:
                # Check for stop request periodically during row processing (every 100 rows)
                if len(rows_to_insert) + len(rows_to_update_scd1) > 0 and (len(rows_to_insert) + len(rows_to_update_scd1)) % 100 == 0:
                    if check_stop_request():
                        print(f"STOP request detected for {{MAPREF}} during row processing. Stopping job gracefully...")
                        stop_requested = True
                        break
                raw_src_dict = dict(zip(source_columns, src_row))
                src_dict = map_row_to_target_columns(raw_src_dict)
                
                # Debug: Log column mapping for first row of first batch
                if batch_num == 1 and len(rows_to_insert) + len(rows_to_update_scd1) + len(rows_to_update_scd2) == 0:
                    print(f"DEBUG: First row column mapping - Source columns: {{list(raw_src_dict.keys())[:5]}}..., Target columns: {{list(src_dict.keys())[:5]}}...")
                    # Show a sample of mapped values for key columns
                    sample_cols = PK_COLUMNS[:3] if PK_COLUMNS else list(src_dict.keys())[:3]
                    for col in sample_cols:
                        src_val = raw_src_dict.get(COLUMN_SOURCE_MAPPING.get(col, col), 'NOT_FOUND')
                        tgt_val = src_dict.get(col, 'NOT_FOUND')
                        print(f"DEBUG: Column {{col}} - Source value: {{src_val}}, Mapped value: {{tgt_val}}")
                
                # Build primary key for target lookup
                # Map PK_COLUMNS (target column names) to source column names using PK_SOURCE_MAPPING
                pk_values = {{}}
                pk_where_parts = []
                
                for pk_col in PK_COLUMNS:
                    # Get source column name from mapping (fallback to target name if not mapped)
                    source_col = PK_SOURCE_MAPPING.get(pk_col, pk_col)
                    
                    # Try to get value from source data using source column name
                    pk_value = raw_src_dict.get(source_col)
                    if pk_value is None:
                        # Try case-insensitive match on source column name
                        pk_value = next((raw_src_dict[k] for k in raw_src_dict.keys() if isinstance(k, str) and k.upper() == source_col.upper()), None)
                    
                    if pk_value is None:
                        # Still not found - try target column name as fallback
                        pk_value = raw_src_dict.get(pk_col)
                        if pk_value is None:
                            # Try case-insensitive match on target column name
                            pk_value = next((raw_src_dict[k] for k in raw_src_dict.keys() if isinstance(k, str) and k.upper() == pk_col.upper()), None)
                    
                    if pk_value is None:
                        # Column not found in source - log warning with mapping info
                        print(f"WARNING: Primary key column {{pk_col}} (source: {{source_col}}) not found in source data. Available columns: {{list(raw_src_dict.keys())[:10]}}...")
                        pk_value = None
                    
                    # Use target column name for the WHERE clause (target table uses target column names)
                    pk_values[pk_col] = pk_value
                    pk_where_parts.append(f"{{pk_col}} = :{{pk_col}}")
                
                # Check if any PK values are None - this would cause lookup to fail
                null_pk_cols = [col for col, val in pk_values.items() if val is None]
                if null_pk_cols:
                    print(f"WARNING: NULL primary key values found for columns: {{null_pk_cols}}. Skipping row.")
                    continue  # Skip this row - can't lookup without valid PK
                
                # Check if record exists in target (using target cursor)
                pk_where = " AND ".join(pk_where_parts)
                target_query = f"""
                    SELECT * FROM {tbnam}
                    WHERE CURFLG = 'Y' AND {{pk_where}}
                """
                
                target_cursor.execute(target_query, pk_values)
                target_row = target_cursor.fetchone()
                
                # Debug: Log lookup result for first few rows
                if batch_num == 1 and len(rows_to_insert) + len(rows_to_update_scd1) < 3:
                    print(f"DEBUG: PK lookup result - Found existing record: {{target_row is not None}}")
                
                if target_row:
                    # Record exists - check for changes using hash
                    target_columns = [desc[0] for desc in target_cursor.description]
                    target_dict = dict(zip(target_columns, target_row))
                    
                    # Generate hash for source and target using aligned column set
                    src_hash = generate_hash(src_dict, ALL_COLUMNS)
                    tgt_hash = target_dict.get('RWHKEY', '')
                    
                    if src_hash != tgt_hash:
                        # Data changed
                        if CURRENT_SCD_TYPE == 2:
                            # SCD Type 2 - Insert new version, expire old
                            new_version = dict(src_dict)
                            new_version['SKEY'] = None  # Will be generated
                            new_version['RWHKEY'] = src_hash
                            new_version['CURFLG'] = 'Y'
                            new_version['FROMDT'] = datetime.now()
                            new_version['TODT'] = datetime(9999, 12, 31)
                            rows_to_insert.append(new_version)
                            rows_to_update_scd2.append(target_dict['SKEY'])
                        else:
                            # SCD Type 1 - Update existing
                            updated_row = dict(src_dict)
                            updated_row['SKEY'] = target_dict['SKEY']
                            updated_row['RWHKEY'] = src_hash
                            rows_to_update_scd1.append(updated_row)
                else:
                    # New record
                    src_hash = generate_hash(src_dict, ALL_COLUMNS)
                    new_row = dict(src_dict)
                    new_row['RWHKEY'] = src_hash
                    if TARGET_TYPE == 'DIM':
                        new_row['CURFLG'] = 'Y'
                        new_row['FROMDT'] = datetime.now()
                        new_row['TODT'] = datetime(9999, 12, 31)
                    rows_to_insert.append(new_row)
                
            # If stop was requested during row processing, break out of batch
            if stop_requested:
                break
            
            # Execute bulk operations for this batch (once per batch)
            if rows_to_update_scd2:
                    # Expire old SCD Type 2 records using bulk update
                    scd2_params = []
                    for skey in rows_to_update_scd2:
                        if check_stop_request():
                            stop_requested = True
                            break
                        scd2_params.append({{'skey': skey}})
                    if stop_requested:
                        break
                    expired_count = 0
                    if scd2_params:
                        try:
                            target_cursor.executemany(f"""
                                UPDATE {tbnam}
                                SET CURFLG = 'N', TODT = TRUNC(SYSDATE), RECUPDT = SYSDATE
                                WHERE SKEY = :skey
                            """, scd2_params)
                            expired_count = target_cursor.rowcount if target_cursor.rowcount is not None else len(scd2_params)
                        except Exception as update_err:
                            print(f"ERROR expiring SCD Type 2 records: {{update_err}}")
                            error_count += len(scd2_params)
                            expired_count = 0
                    print(f"Batch {{batch_num}}: Expired {{expired_count}} SCD Type 2 records (out of {{len(rows_to_update_scd2)}} attempted)")
                    rows_to_update_scd2.clear()
                    rows_to_update_scd2.clear()
                
            if stop_requested:
                break
            
            if rows_to_update_scd1:
                    # Update SCD Type 1 records using bulk update
                    update_cols = [col for col in ALL_COLUMNS if col not in {{'SKEY', 'RECCRDT'}}]
                    set_clause = ", ".join([f"{{col}} = :{{col}}" for col in update_cols])
                    update_params = []
                    for row in rows_to_update_scd1:
                        if check_stop_request():
                            stop_requested = True
                            break
                        param_row = {{col: row.get(col) for col in update_cols}}
                        param_row['SKEY'] = row.get('SKEY')
                        update_params.append(param_row)
                    if stop_requested:
                        break
                    updated_count = 0
                    if update_params:
                        try:
                            target_cursor.executemany(f"""
                                UPDATE {tbnam}
                                SET {{set_clause}}, RECUPDT = SYSDATE
                                WHERE SKEY = :SKEY
                            """, update_params)
                            updated_count = target_cursor.rowcount if target_cursor.rowcount is not None else len(update_params)
                        except Exception as update_err:
                            print(f"ERROR updating SCD Type 1 records: {{update_err}}")
                            error_count += len(update_params)
                            updated_count = 0
                    print(f"Batch {{batch_num}}: Updated {{updated_count}} SCD Type 1 records (out of {{len(rows_to_update_scd1)}} attempted)")
                    target_count += updated_count
                    batch_target_rows += updated_count
                    rows_to_update_scd1.clear()
                    rows_to_update_scd1.clear()
                
            if stop_requested:
                break
            
            if rows_to_insert:
                    # Insert new records
                    # rows_to_insert contains dictionaries with TARGET column names as keys (from map_row_to_target_columns)
                    # So we must use ALL_COLUMNS (target columns) for the INSERT statement
                    # Exclude SKEY, RECCRDT, RECUPDT (handled separately)
                    insert_cols = [col for col in ALL_COLUMNS if col != 'SKEY' and col != 'RECCRDT' and col != 'RECUPDT']
                    
                    cols_str = ", ".join(insert_cols)
                    vals_str = ", ".join([f":{{col}}" for col in insert_cols])
                    
                    # Sequence name: use schema.table_SEQ format
                    # If tbnam is "CDR.DIM_ACNT_LN", sequence should be "CDR.DIM_ACNT_LN_SEQ"
                    seq_name = FULL_TABLE_NAME + "_SEQ"
                    
                    filtered_rows = []
                    for row in rows_to_insert:
                        # Check for stop request during insert preparation
                        if check_stop_request():
                            print(f"STOP request detected during INSERT operations. Stopping job gracefully...")
                            stop_requested = True
                            break
                        
                        filtered_row = {{col: row.get(col) for col in insert_cols}}
                        filtered_rows.append(filtered_row)
                    
                    if stop_requested:
                        break  # Break out of batch processing if stop was requested
                    
                    inserted_count = 0
                    if filtered_rows:
                        try:
                            target_cursor.executemany(f"""
                                INSERT INTO {tbnam} (SKEY, {{cols_str}}, RECCRDT, RECUPDT)
                                VALUES ({{seq_name}}.nextval, {{vals_str}}, SYSDATE, SYSDATE)
                            """, filtered_rows)
                            inserted_count = target_cursor.rowcount if target_cursor.rowcount is not None else len(filtered_rows)
                        except Exception as insert_err:
                            error_count += len(filtered_rows)
                            inserted_count = 0
                            print(f"ERROR inserting batch: {{insert_err}}")
                    
                    print(f"Batch {{batch_num}}: Inserted {{inserted_count}} new records (out of {{len(rows_to_insert)}} attempted)")
                    target_count += inserted_count
                    batch_target_rows += inserted_count
                    rows_to_insert.clear()
                    rows_to_insert.clear()
                
            # Update DMS_PRCLOG progress before checkpoint handling
            try:
                # Detect database type for query syntax
                from modules.common.db_table_utils import _detect_db_type
                import os
                metadata_db_type = _detect_db_type(metadata_connection)
                schema = (os.getenv("DMS_SCHEMA", "")).strip()
                schema_prefix = f"{{schema}}." if schema else ""
                
                if metadata_db_type == "POSTGRESQL":
                    metadata_cursor.execute(f"""
                        UPDATE {{schema_prefix}}DMS_PRCLOG
                        SET SRCROWS = %s,
                            TRGROWS = %s,
                            RECUPDT = CURRENT_TIMESTAMP
                        WHERE sessionid = %s
                          AND prcid = %s
                    """, (
                        source_count,
                        target_count,
                        sessionid,
                        prcid
                    ))
                else:  # Oracle
                    metadata_cursor.execute(f"""
                        UPDATE {{schema_prefix}}DMS_PRCLOG
                        SET SRCROWS = :srcrows,
                            TRGROWS = :trgrows,
                            RECUPDT = SYSTIMESTAMP
                        WHERE sessionid = :sessionid
                          AND prcid = :prcid
                    """, {{
                        'srcrows': source_count,
                        'trgrows': target_count,
                        'sessionid': sessionid,
                        'prcid': prcid
                    }})
                batch_error_rows = error_count - batch_error_start
                log_batch_progress(batch_num, batch_source_rows, batch_target_rows, batch_error_rows)
                metadata_connection.commit()
                print(f"DMS_PRCLOG progress updated (source_rows={{source_count}}, target_rows={{target_count}})")
            except Exception as progress_err:
                print(f"WARNING: Could not update DMS_PRCLOG progress: {{progress_err}}")
            
            # Check for stop request before updating checkpoint
            if stop_requested:
                break
            
            # Update checkpoint after successful batch processing
            if CHECKPOINT_ENABLED:
                    if CHECKPOINT_STRATEGY == 'KEY' and CHECKPOINT_COLUMNS:
                        # Update checkpoint to last processed key value(s)
                        last_row = source_rows[-1]
                        last_row_dict = dict(zip(source_columns, last_row))
                        
                        # Extract checkpoint value(s) - support composite keys
                        if len(CHECKPOINT_COLUMNS) > 1:
                            # Composite key: Extract all column values and join with pipe separator
                            checkpoint_values_list = []
                            for col in CHECKPOINT_COLUMNS:
                                val = last_row_dict.get(col)
                                if val is None:
                                    val = ''  # Handle NULL values
                                checkpoint_values_list.append(str(val))
                            checkpoint_value = '|'.join(checkpoint_values_list)
                            checkpoint_display = f"({{', '.join(CHECKPOINT_COLUMNS)}}) = ({{', '.join(checkpoint_values_list)}})"
                        else:
                            # Single column key
                            checkpoint_value = last_row_dict.get(CHECKPOINT_COLUMNS[0])
                            checkpoint_display = f"{{CHECKPOINT_COLUMNS[0]}} = {{checkpoint_value}}"
                        
                        if checkpoint_value:
                            # Detect database type for query syntax
                            from modules.common.db_table_utils import _detect_db_type
                            import os
                            metadata_db_type = _detect_db_type(metadata_connection)
                            schema = (os.getenv("DMS_SCHEMA", "")).strip()
                            schema_prefix = f"{{schema}}." if schema else ""
                            
                            if metadata_db_type == "POSTGRESQL":
                                metadata_cursor.execute(f"""
                                    UPDATE {{schema_prefix}}DMS_PRCLOG
                                    SET PARAM1 = %s
                                    WHERE sessionid = %s
                                      AND prcid = %s
                                """, (
                                    str(checkpoint_value),
                                    sessionid,
                                    prcid
                                ))
                            else:  # Oracle
                                metadata_cursor.execute(f"""
                                    UPDATE {{schema_prefix}}DMS_PRCLOG
                                    SET PARAM1 = :checkpoint_value
                                    WHERE sessionid = :sessionid
                                      AND prcid = :prcid
                                """, {{
                                    'checkpoint_value': str(checkpoint_value),
                                    'sessionid': sessionid,
                                    'prcid': prcid
                                }})
                            metadata_connection.commit()
                            print(f"Checkpoint updated: {{checkpoint_display}}")
                    elif CHECKPOINT_STRATEGY == 'PYTHON':
                        # Update checkpoint to row count
                        total_processed = total_fetched
                        # Detect database type for query syntax
                        from modules.common.db_table_utils import _detect_db_type
                        import os
                        metadata_db_type = _detect_db_type(metadata_connection)
                        schema = (os.getenv("DMS_SCHEMA", "")).strip()
                        schema_prefix = f"{{schema}}." if schema else ""
                        
                        if metadata_db_type == "POSTGRESQL":
                            metadata_cursor.execute(f"""
                                UPDATE {{schema_prefix}}DMS_PRCLOG
                                SET PARAM1 = %s
                                WHERE sessionid = %s
                                  AND prcid = %s
                            """, (
                                str(total_processed),
                                sessionid,
                                prcid
                            ))
                        else:  # Oracle
                            metadata_cursor.execute(f"""
                                UPDATE {{schema_prefix}}DMS_PRCLOG
                                SET PARAM1 = :checkpoint_value
                                WHERE sessionid = :sessionid
                                  AND prcid = :prcid
                            """, {{
                                'checkpoint_value': str(total_processed),
                                'sessionid': sessionid,
                                'prcid': prcid
                            }})
                        print(f"Checkpoint updated: {{total_processed}} rows processed")
                
            # Commit strategy: 
            # - Metadata connection: commit every batch (for checkpoint updates)
            # - Target connection: commit every COMMIT_FREQUENCY batches to balance:
            #   * Transaction size (avoid long-running transactions)
            #   * Cursor validity (in Oracle, commits on a connection don't invalidate open SELECT cursors)
            #   * Recovery (if job fails, we don't lose all work)
            metadata_connection.commit()
            
            # Commit target connection periodically (every COMMIT_FREQUENCY batches)
            # In Oracle, commits on a connection do NOT invalidate open SELECT cursors
            # The cursor remains valid and can continue fetching rows
            if batch_num % COMMIT_FREQUENCY == 0:
                try:
                    # Verify cursor is still valid before committing
                    cursor_valid_before = target_cursor.description is not None
                    
                    target_connection.commit()
                    print(f"Batch {{batch_num}}: Committed target connection (batch={{batch_size}}, total processed: {{total_fetched}})")
                    
                    # Verify cursor is still valid after commit (should be True in Oracle)
                    cursor_valid_after = target_cursor.description is not None
                    if not cursor_valid_after:
                        print(f"WARNING: Cursor became invalid after commit at batch {{batch_num}}!")
                        print(f"This is unexpected in Oracle - SELECT cursors should remain valid after commits.")
                        print(f"Will attempt to continue fetching, but may encounter errors.")
                except Exception as commit_err:
                    print(f"ERROR committing target connection at batch {{batch_num}}: {{commit_err}}")
                    # Don't break - continue processing, but log the error
            else:
                print(f"Batch {{batch_num}}: Committed metadata only (batch={{batch_size}}, total processed: {{total_fetched}})")
        
        # End of batch processing loop
        if stop_requested:
            print(f"Job stopped by user request. Processed {{total_fetched}} rows before stop.")
            
            # Commit any remaining work before stopping
            try:
                if batch_num % COMMIT_FREQUENCY != 0:
                    target_connection.commit()
                    print(f"Committed target connection work up to batch {{batch_num}} before stop")
            except Exception as stop_commit_err:
                print(f"WARNING: Error committing target work before stop: {{stop_commit_err}}")
            
            # Mark stop request as processed
            try:
                metadata_cursor.execute("""
                    UPDATE DMS_PRCREQ 
                    SET status = 'DONE', 
                        result_payload = '{{"status": "STOPPED", "rows_processed": ' + str(total_fetched) + '}}',
                        completed_at = SYSTIMESTAMP
                    WHERE mapref = :mapref 
                      AND request_type = 'STOP' 
                      AND status IN ('NEW', 'CLAIMED')
                """, {{
                    'mapref': MAPREF
                }})
                metadata_connection.commit()
                print(f"Stop request marked as processed")
            except Exception as e:
                print(f"WARNING: Could not update stop request status: {{e}}")
            
            # Return early with stopped status
            return {{
                'status': 'STOPPED',
                'source_rows': source_count,
                'target_rows': target_count,
                'error_rows': error_count,
                'message': f'Job stopped by user request after processing {{total_fetched}} rows'
            }}
        
        print(f"Completed processing all batches for combination {mapcmbcd if mapcmbcd else 'DEFAULT'}")
''')
    
    # Footer
    code_parts.append(f'''
        # Mark checkpoint as COMPLETED on successful finish (using metadata connection)
        if CHECKPOINT_ENABLED:
            # Detect database type for query syntax
            from modules.common.db_table_utils import _detect_db_type
            import os
            metadata_db_type = _detect_db_type(metadata_connection)
            schema = (os.getenv("DMS_SCHEMA", "")).strip()
            schema_prefix = f"{{schema}}." if schema else ""
            
            if metadata_db_type == "POSTGRESQL":
                metadata_cursor.execute(f"""
                    UPDATE {{schema_prefix}}DMS_PRCLOG
                    SET PARAM1 = 'COMPLETED'
                    WHERE sessionid = %s
                      AND prcid = %s
                """, (
                    sessionid,
                    prcid
                ))
            else:  # Oracle
                metadata_cursor.execute(f"""
                    UPDATE {{schema_prefix}}DMS_PRCLOG
                    SET PARAM1 = 'COMPLETED'
                    WHERE sessionid = :sessionid
                      AND prcid = :prcid
                """, {{
                    'sessionid': sessionid,
                    'prcid': prcid
                }})
            print("Checkpoint marked as COMPLETED")
        
        # Final commit: commit any remaining uncommitted work
        # Only commit if job wasn't stopped (if stopped, commits already handled in stop section)
        if not stop_requested:
            # Check if there are uncommitted batches (if last batch wasn't a commit frequency boundary)
            if batch_num % COMMIT_FREQUENCY != 0:
                try:
                    target_connection.commit()
                    print(f"Final commit: Committed remaining target connection work (last batch was {{batch_num}}, not a commit boundary)")
                except Exception as final_commit_err:
                    print(f"WARNING: Error during final target commit: {{final_commit_err}}")
            else:
                print(f"Final commit: No remaining target work (last commit was at batch {{batch_num}})")
            
            # Always commit metadata connection at the end
            try:
                metadata_connection.commit()
                print(f"Final commit: Committed metadata connection")
            except Exception as metadata_commit_err:
                print(f"WARNING: Error during final metadata commit: {{metadata_commit_err}}")
            
            print(f"Job {{MAPREF}} completed successfully")
        print(f"  Source rows: {{source_count}}")
        print(f"  Target rows: {{target_count}}")
        print(f"  Error rows: {{error_count}}")
        
        return {{
            'status': 'SUCCESS',
            'source_rows': source_count,
            'target_rows': target_count,
            'error_rows': error_count,
            'joblogid': joblogid
        }}
        
    except Exception as e:
        # Rollback all connections on error
        if source_connection:
            try:
                source_connection.rollback()
            except Exception:
                pass
        if target_connection:
            try:
                target_connection.rollback()
            except Exception:
                pass
        if metadata_connection:
            try:
                metadata_connection.rollback()
            except Exception:
                pass
        
        error_msg = f"Job {{MAPREF}} failed: {{str(e)}}"
        print(f"ERROR: {{error_msg}}")
        
        # Log error (using metadata connection)
        try:
            error_id = get_next_id(metadata_cursor, "DMS_JOBERRSEQ")
            metadata_cursor.execute("""
                INSERT INTO DMS_JOBERR (
                    errid, prcid, sessionid, jobid, mapref, prcdt,
                    errtyp, errmsg, dberrmsg
                )
                VALUES (
                    :errid, :prcid, :sessionid, :jobid, :mapref, SYSDATE,
                    'ERR', :errmsg, :dberrmsg
                )
            """, {{
                'errid': error_id,
                'prcid': session_params.get('prcid'),
                'sessionid': session_params.get('sessionid'),
                'jobid': JOBID,
                'mapref': MAPREF,
                'errmsg': 'Job execution failed',
                'dberrmsg': str(e)[:4000]
            }})
            metadata_connection.commit()
        except:
            pass
        
        return {{
            'status': 'ERROR',
            'error_message': error_msg,
            'source_rows': source_count,
            'target_rows': target_count,
            'error_rows': error_count
        }}
    
    finally:
        # Close all cursors
        if source_cursor:
            try:
                source_cursor.close()
            except Exception:
                pass
        if target_cursor:
            try:
                target_cursor.close()
            except Exception:
                pass
        if metadata_cursor:
            try:
                metadata_cursor.close()
            except Exception:
                pass


if __name__ == '__main__':
    # This allows testing the generated job independently
    print("This is an auto-generated ETL job for {mapref}")
    print("To execute, call: execute_job(metadata_connection, source_connection, target_connection, session_params)")
    print("  - metadata_connection: For DMS_JOBLOG, DMS_PRCLOG, DMS_JOBERR operations")
    print("  - source_connection: For source table operations (SELECT queries)")
    print("  - target_connection: For target table operations (INSERT/UPDATE operations)")
''')
    
    cursor.close()
    return ''.join(code_parts)

