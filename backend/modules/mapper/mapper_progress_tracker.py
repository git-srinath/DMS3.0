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
    cursor = None
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)

        # First attempt: adapter-detected parameter style
        placeholder = adapter.get_parameter_placeholder('mapref')
        params = adapter.format_parameters({'mapref': mapref}, use_named=True)
        query_template = """
            SELECT COUNT(*) 
            FROM DMS_PRCREQ 
            WHERE mapref = {placeholder}
              AND request_type = 'STOP' 
              AND status IN ('NEW', 'CLAIMED')
        """

        try:
            cursor.execute(query_template.format(placeholder=placeholder), params)
        except Exception as primary_err:
            # Fallback for intermittent DB-type mis-detection (e.g., ':' on PostgreSQL)
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            cursor = metadata_conn.cursor()

            if placeholder == "%s":
                fallback_placeholder = ":mapref"
                fallback_params = {'mapref': mapref}
            else:
                fallback_placeholder = "%s"
                fallback_params = (mapref,)

            debug(
                f"Stop request check retry for {mapref}: primary placeholder '{placeholder}' failed "
                f"({primary_err}); retrying with '{fallback_placeholder}'"
            )
            cursor.execute(
                query_template.format(placeholder=fallback_placeholder),
                fallback_params
            )

        stop_count = cursor.fetchone()[0]
        return stop_count > 0
    except Exception as e:
        warning(f"Could not check stop request for {mapref}: {e}")
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass


def log_batch_progress(
    metadata_conn,
    mapref: str,
    jobid: int,
    batch_number: int,
    batch_source_rows: int,
    batch_target_rows: int,
    batch_error_rows: int,
    session_params: Dict[str, Any],
    joblogid: Optional[int] = None,
) -> Optional[int]:
    """
    Insert or update batch-level statistics in DMS_JOBLOG so the UI can display
    accurate progress information.
    
    Args:
        metadata_conn: Metadata database connection
        mapref: Mapping reference
        jobid: Job ID
        batch_number: Batch number (for logging)
        batch_source_rows: Number of source rows in this batch
        batch_target_rows: Number of target rows inserted/updated in this batch
        batch_error_rows: Number of error rows in this batch
        session_params: Session parameters from DMS_PRCLOG (must contain 'prcid' and 'sessionid')
        joblogid: Existing DMS_JOBLOG.JOBLOGID to update. If None, a new row is inserted.

    Returns:
        The joblogid used, or None if logging fails.
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        
        joblog_id = int(joblogid) if joblogid is not None else int(get_next_id(cursor, "DMS_JOBLOGSEQ"))
        
        # Get database-specific syntax
        timestamp = adapter.get_current_timestamp()
        
        # Build query with database-agnostic syntax
        if adapter.supports_named_parameters():
            if joblogid is None:
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
                query = f"""
                    UPDATE DMS_JOBLOG
                    SET srcrows = :srcrows,
                        trgrows = :trgrows,
                        errrows = :errrows
                    WHERE joblogid = :joblogid
                """
        else:
            ph = adapter.get_parameter_placeholder()
            if joblogid is None:
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
            else:
                query = f"""
                    UPDATE DMS_JOBLOG
                    SET srcrows = {ph},
                        trgrows = {ph},
                        errrows = {ph}
                    WHERE joblogid = {ph}
                """

        if joblogid is None:
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
        else:
            params_dict = {
                'srcrows': batch_source_rows,
                'trgrows': batch_target_rows,
                'errrows': batch_error_rows,
                'joblogid': joblog_id
            }

        # Format parameters for database
        params = adapter.format_parameters(params_dict, use_named=True)
        
        cursor.execute(query, params)
        cursor.close()
        if joblogid is None:
            debug(f"Logged batch {batch_number} progress: {batch_source_rows} source, "
                  f"{batch_target_rows} target, {batch_error_rows} errors")
        else:
            debug(f"Updated batch {batch_number} progress in JOBLOGID={joblog_id}: "
                  f"{batch_source_rows} source, {batch_target_rows} target, {batch_error_rows} errors")
        return joblog_id
    except Exception as log_err:
        warning(f"Could not log batch {batch_number} to DMS_JOBLOG: {log_err}")
        return None


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

