"""
Mapper progress tracking and stop request checking.
Generic functions for logging progress and checking stop requests.
No job-specific code - all job data passed as parameters.
"""
from typing import Dict, Any, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.database_sql_adapter import create_adapter
    from backend.modules.common.id_provider import next_id as get_next_id
    from backend.modules.logger import warning, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.database_sql_adapter import create_adapter  # type: ignore
    from modules.common.id_provider import next_id as get_next_id  # type: ignore
    from modules.logger import warning, debug  # type: ignore


def check_stop_request(
    metadata_conn,
    mapref: str
) -> bool:
    """
    Check if a stop request exists for this job in DMS_PRCREQ.
    
    Args:
        metadata_conn: Metadata database connection
        mapref: Mapping reference (job identifier)
        
    Returns:
        True if stop request exists, False otherwise
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        # Build query with database-agnostic parameter placeholder
        placeholder = adapter.get_parameter_placeholder('mapref')
        params = adapter.format_parameters({'mapref': mapref}, use_named=True)
        
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM DMS_PRCREQ 
            WHERE mapref = {placeholder} 
              AND request_type = 'STOP' 
              AND status IN ('NEW', 'CLAIMED')
        """, params)
        
        stop_count = cursor.fetchone()[0]
        cursor.close()
        return stop_count > 0
    except Exception as e:
        warning(f"Could not check stop request for {mapref}: {e}")
        return False


def log_batch_progress(
    metadata_conn,
    mapref: str,
    jobid: int,
    batch_number: int,
    batch_source_rows: int,
    batch_target_rows: int,
    batch_error_rows: int,
    session_params: Dict[str, Any]
) -> None:
    """
    Insert batch-level statistics into DMS_JOBLOG so the UI can display accurate
    progress information. Each call records a single batch.
    
    Args:
        metadata_conn: Metadata database connection
        mapref: Mapping reference
        jobid: Job ID
        batch_number: Batch number (for logging)
        batch_source_rows: Number of source rows in this batch
        batch_target_rows: Number of target rows inserted/updated in this batch
        batch_error_rows: Number of error rows in this batch
        session_params: Session parameters from DMS_PRCLOG (must contain 'prcid' and 'sessionid')
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        
        joblog_id = get_next_id(cursor, "DMS_JOBLOGSEQ")
        
        # Get database-specific syntax
        timestamp = adapter.get_current_timestamp()
        placeholder = adapter.get_parameter_placeholder('joblogid')
        
        # Build parameters dictionary
        params_dict = {
            'joblogid': joblog_id,
            'mapref': mapref,
            'jobid': jobid,
            'srcrows': batch_source_rows,
            'trgrows': batch_target_rows,
            'errrows': batch_error_rows,
            'prcid': prcid,
            'sessionid': sessionid
        }
        
        # Format parameters for database
        params = adapter.format_parameters(params_dict, use_named=True)
        
        # Build query with database-agnostic syntax
        if adapter.supports_named_parameters():
            # Use named parameters
            query = f"""
                INSERT INTO DMS_JOBLOG (
                    joblogid, prcdt, mapref, jobid,
                    srcrows, trgrows, errrows,
                    reccrdt, prcid, sessionid
                ) VALUES (
                    :joblogid, {timestamp}, :mapref, :jobid,
                    :srcrows, :trgrows, :errrows,
                    {timestamp}, :prcid, :sessionid
                )
            """
        else:
            # Use positional parameters - need correct number of placeholders
            ph = adapter.get_parameter_placeholder()
            query = f"""
                INSERT INTO DMS_JOBLOG (
                    joblogid, prcdt, mapref, jobid,
                    srcrows, trgrows, errrows,
                    reccrdt, prcid, sessionid
                ) VALUES (
                    {ph}, {timestamp}, {ph}, {ph},
                    {ph}, {ph}, {ph},
                    {timestamp}, {ph}, {ph}
                )
            """
        
        cursor.execute(query, params)
        cursor.close()
        debug(f"Logged batch {batch_number} progress: {batch_source_rows} source, "
              f"{batch_target_rows} target, {batch_error_rows} errors")
    except Exception as log_err:
        warning(f"Could not log batch {batch_number} to DMS_JOBLOG: {log_err}")


def update_process_log_progress(
    metadata_conn,
    session_params: Dict[str, Any],
    source_rows: int,
    target_rows: int
) -> None:
    """
    Update progress timestamp in DMS_PRCLOG.
    
    Note: DMS_PRCLOG does not have srcrows/trgrows columns.
    Progress is tracked in DMS_JOBLOG via log_batch_progress().
    This function only updates the recupdt timestamp to indicate activity.
    
    Args:
        metadata_conn: Metadata database connection
        session_params: Session parameters (must contain 'prcid' and 'sessionid')
        source_rows: Total source rows processed so far (unused, kept for API compatibility)
        target_rows: Total target rows inserted/updated so far (unused, kept for API compatibility)
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        
        # Get database-specific syntax
        timestamp = adapter.get_current_timestamp()
        
        # Build parameters (only sessionid and prcid needed)
        params_dict = {
            'sessionid': sessionid,
            'prcid': prcid
        }
        params = adapter.format_parameters(params_dict, use_named=True)
        
        # Build query - only update recupdt timestamp
        # DMS_PRCLOG does not have srcrows/trgrows columns
        if adapter.supports_named_parameters():
            query = f"""
                UPDATE DMS_PRCLOG
                SET recupdt = {timestamp}
                WHERE sessionid = :sessionid
                  AND prcid = :prcid
            """
        else:
            ph = adapter.get_parameter_placeholder()
            query = f"""
                UPDATE DMS_PRCLOG
                SET recupdt = {timestamp}
                WHERE sessionid = {ph}
                  AND prcid = {ph}
            """
        
        cursor.execute(query, params)
        cursor.close()
    except Exception as e:
        warning(f"Could not update process log progress: {e}")

