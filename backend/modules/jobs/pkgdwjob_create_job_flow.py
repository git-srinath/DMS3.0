"""
CREATE_JOB_FLOW implementation - Dynamic Python code generator with hash-based change detection.
This module handles the complex logic of generating ETL Python code.

This is extracted from pkgdms_job_python.py for better maintainability.
"""

import os
from typing import Dict, List, Tuple
from datetime import datetime

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.common.db_table_utils import (
        _detect_db_type,
        get_postgresql_table_name,
    )
except ImportError:  # When running Flask app.py directly inside backend
    from modules.common.db_table_utils import (  # type: ignore
        _detect_db_type,
        get_postgresql_table_name,
    )


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
                                SET srcrows = %s,
                                    trgrows = %s,
                                    recupdt = CURRENT_TIMESTAMP
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
    
    # Header - Simplified with external module imports
    code_parts.append(f'''"""
Auto-generated ETL Job for {mapref}
Target: {full_table_name}
Type: {trgtbtyp}
Hash Algorithm: MD5 with pipe (|) delimiter
NULL Marker: <NULL>
Checkpoint Strategy: {effective_strategy}
Checkpoint Enabled: {checkpoint_enabled}

This code uses external modules for all common logic.
The dynamic code block is now minimal - only job-specific configuration.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal

# Import external modules for common functionality
try:
    from backend.modules.mapper.mapper_job_executor import execute_mapper_job
    from backend.modules.mapper.mapper_transformation_utils import map_row_to_target_columns, generate_hash
    from backend.modules.logger import debug
except ImportError:  # Fallback for Flask-style imports
    from modules.mapper.mapper_job_executor import execute_mapper_job  # type: ignore
    from modules.mapper.mapper_transformation_utils import map_row_to_target_columns, generate_hash  # type: ignore
    from modules.logger import debug  # type: ignore

# Note: Parallel processing is configured via job_config['parallel_config']
# The execute_mapper_job function will use parallel processing if enabled and conditions are met

# Job configuration
MAPREF = "{mapref}"
JOBID = {jobid}
TARGET_SCHEMA = "{trgschm}"
TARGET_TABLE = "{trgtbnm}"
TARGET_TYPE = "{trgtbtyp}"
FULL_TABLE_NAME = "{full_table_name}"
BULK_LIMIT = {blkprcrows if blkprcrows else w_limit}

# Checkpoint configuration
CHECKPOINT_ENABLED = {str(checkpoint_enabled)}
CHECKPOINT_STRATEGY = "{effective_strategy}"
CHECKPOINT_COLUMN = "{chkpntclnm if chkpntclnm else ''}"
CHECKPOINT_COLUMNS = [col.strip().upper() for col in CHECKPOINT_COLUMN.split(',')] if CHECKPOINT_COLUMN else []

# Primary key columns (target column names)
PK_COLUMNS = {pk_columns}
PK_SOURCE_MAPPING = {pk_source_mapping}

# All target columns (in execution order)
ALL_COLUMNS = {all_columns}

# Mapping from target columns to source columns
COLUMN_SOURCE_MAPPING = {column_source_mapping}

# Columns to exclude from hash calculation
HASH_EXCLUDE_COLUMNS = {{'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG', 'FROMDT', 'TODT', 'VALDFRM', 'VALDTO'}}


def execute_job(metadata_connection, source_connection, target_connection, session_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute ETL job for {mapref}.
    This is a thin wrapper that delegates to external modules for all common logic.
    
    Args:
        metadata_connection: Database connection for metadata tables
        source_connection: Database connection for source tables (SELECT queries)
        target_connection: Database connection for target tables (INSERT/UPDATE operations)
        session_params: Session parameters from DMS_PRCLOG
        
    Returns:
        Dictionary with execution results
    """
    debug("=" * 80)
    debug(f"EXECUTE_JOB STARTED for {{MAPREF}}")
    debug(f"  Target: {{FULL_TABLE_NAME}}")
    debug("=" * 80)
    
    # Initialize connection IDs (will be set from first combination)
    source_conn_id_var = None
    target_conn_id_var = None
    
    # Build job configuration
    job_config = {{
                    'mapref': MAPREF,
                    'jobid': JOBID,
        'target_schema': TARGET_SCHEMA,
        'target_table': TARGET_TABLE,
        'target_type': TARGET_TYPE,
        'full_table_name': FULL_TABLE_NAME,
        'pk_columns': set(PK_COLUMNS),
        'pk_source_mapping': PK_SOURCE_MAPPING,
        'all_columns': ALL_COLUMNS,
        'column_source_mapping': COLUMN_SOURCE_MAPPING,
        'hash_exclude_columns': HASH_EXCLUDE_COLUMNS,
        'bulk_limit': BULK_LIMIT,
        'source_conn_id': source_conn_id_var,
        'target_conn_id': target_conn_id_var
    }}
    
    # Build parallel processing configuration (optional, from session_params or environment)
    import os
    parallel_config = {{
        'enable_parallel': session_params.get('enable_parallel') or os.getenv('MAPPER_PARALLEL_ENABLED', 'false').lower() == 'true',
        'max_workers': session_params.get('max_workers') or (int(os.getenv('MAPPER_MAX_WORKERS')) if os.getenv('MAPPER_MAX_WORKERS') else None),
        'chunk_size': session_params.get('chunk_size') or int(os.getenv('MAPPER_CHUNK_SIZE', '50000')),
        'min_rows_for_parallel': session_params.get('min_rows_for_parallel') or int(os.getenv('MAPPER_MIN_ROWS_FOR_PARALLEL', '100000'))
    }}
    job_config['parallel_config'] = parallel_config
    debug(f"Parallel processing configuration loaded: enable_parallel={{parallel_config['enable_parallel']}}, "
          f"min_rows_for_parallel={{parallel_config['min_rows_for_parallel']}}, "
          f"chunk_size={{parallel_config['chunk_size']}}, "
          f"max_workers={{parallel_config['max_workers']}}")
    
    # Build checkpoint configuration
    checkpoint_config = {{
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN if CHECKPOINT_COLUMNS else None
    }}
    
    # Transformation function: maps source row to target columns
    def transformation_func(source_row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform source row to target column format"""
        return map_row_to_target_columns(source_row, COLUMN_SOURCE_MAPPING, ALL_COLUMNS)
    
    # Process each combination sequentially
    total_source_rows = 0
    total_target_rows = 0
    total_error_rows = 0
    last_status = 'SUCCESS'
    should_stop = False  # Flag to stop processing remaining combinations
    
    # Execute ETL logic for each combination
''')
    
    # Generate code for each combination - simplified to call external modules
    for idx, (mapcmbcd, kseq, scdtyp, maxexcseq) in enumerate(combinations, 1):
        # Get details for this combination
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                SELECT j.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm, j.trgconid,
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
                SELECT j.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm, j.trgconid,
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
        
        # Read trgconid (index 4) - this is the target connection ID from DMS_JOB
        # Read MAPRSQL (index 15) - this contains the actual SQL query  
        # Read sqlconid (index 16) - this is the source connection ID
        # Note: After adding j.trgconid, indices shifted:
        #   index 0-3: j.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm
        #   index 4: j.trgconid
        #   index 5-12: jd columns (trgclnm, trgcldtyp, maplogic, trgkeyflg, keyclnm, valclnm, mapcmbcd, excseq)
        #   index 13: p.prval, index 14: jd.maprsqlcd, index 15: s.MAPRSQL, index 16: s.sqlconid
        trgconid = combo_details[0][4] if len(combo_details[0]) > 4 else None
        dms_maprsql_lob = combo_details[0][15] if len(combo_details[0]) > 15 else None
        sqlconid = combo_details[0][16] if len(combo_details[0]) > 16 else None
        
        # Store connection IDs from first combination (they should be the same for all combinations)
        if idx == 1:
            source_conn_id_var = sqlconid
            target_conn_id_var = trgconid
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
    if not should_stop:
        debug("Processing combination: {mapcmbcd if mapcmbcd else 'DEFAULT'} (SCD Type {scdtyp})")
        
        # Set connection IDs from first combination (for thread-safe parallel processing)
        if {idx} == 1:
            job_config['source_conn_id'] = {repr(sqlconid) if sqlconid else 'None'}
            job_config['target_conn_id'] = {repr(trgconid) if trgconid else 'None'}
        
        # Source SQL for this combination
        source_sql_{idx} = """{maplogic_for_code}"""
        
        # Update job config with SCD type for this combination
        job_config['scd_type'] = {scdtyp}
        
        # Execute this combination using external module
        result_{idx} = execute_mapper_job(
            metadata_connection,
            source_connection,
            target_connection,
            job_config,
            source_sql_{idx},
            transformation_func,
            checkpoint_config,
            session_params
        )
        
        # Accumulate results
        if result_{idx}.get('status') == 'STOPPED':
            last_status = 'STOPPED'
            should_stop = True
        elif result_{idx}.get('status') == 'ERROR':
            last_status = 'ERROR'
            print(f"ERROR in combination {idx}: {{result_{idx}.get('error_message', 'Unknown error')}}")
            # Continue to next combination (don't set should_stop, allow next combination to run)
        else:
            total_source_rows += result_{idx}.get('source_rows', 0)
            total_target_rows += result_{idx}.get('target_rows', 0)
            total_error_rows += result_{idx}.get('error_rows', 0)
            
            print(f"Combination {idx} completed: {{result_{idx}.get('source_rows', 0)}} source, {{result_{idx}.get('target_rows', 0)}} target rows")
''')
    
    # Footer - simplified return statement (after all combinations processed)
    code_parts.append(f'''
    # All combinations processed
    print(f"All combinations completed for {{MAPREF}}")
    print(f"  Total source rows: {{total_source_rows}}")
    print(f"  Total target rows: {{total_target_rows}}")
    print(f"  Total error rows: {{total_error_rows}}")
    
    # Return final results
    return {{
        'status': last_status,
        'source_rows': total_source_rows,
        'target_rows': total_target_rows,
        'error_rows': total_error_rows,
        'message': 'Job completed successfully' if last_status == 'SUCCESS' else f'Job ended with status: {{last_status}}'
    }}


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
