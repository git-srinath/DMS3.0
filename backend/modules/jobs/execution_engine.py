from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import oracledb
from modules.common.db_table_utils import get_postgresql_table_name

from database.dbconnect import create_metadata_connection
from modules.common.id_provider import next_id as get_next_id
from modules.logger import info, warning, error, debug
from modules.jobs.pkgdwprc_python import JobRequestType, SchedulerRepositoryError
from modules.jobs.scheduler_models import QueueRequest


def _read_lob(value):
    if hasattr(value, "read"):
        data = value.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data
    return value


def _generate_numeric_id(cursor, entity_name: str) -> int:
    """Generate numeric ID using configured strategy, fallback to timestamp on error."""
    try:
        return int(get_next_id(cursor, entity_name))
    except Exception as exc:
        warning(f"ID provider failed for {entity_name}: {exc}. Falling back to timestamp.")
        return int(datetime.utcnow().timestamp() * 1000)


class JobExecutionEngine:
    """
    Executes queued job requests by running generated Python job flows or
    placeholder logic for other job types.
    """

    def execute(self, request: QueueRequest) -> Dict[str, Any]:
        if request.request_type == JobRequestType.IMMEDIATE:
            return self._execute_job_flow(request.mapref, request.payload)
        if request.request_type == JobRequestType.HISTORY:
            return self._execute_history_job(request)
        if request.request_type == JobRequestType.REPORT:
            return self._execute_report_job(request)
        if request.request_type == JobRequestType.STOP:
            return self._handle_stop_request(request)
        if request.request_type == JobRequestType.REFRESH_SCHEDULE:
            info("Refresh schedule request processed (no-op)")
            return {"status": "SUCCESS", "message": "Schedule refresh acknowledged"}
        raise ValueError(f"Unsupported request type: {request.request_type}")

    # ------------------------------------------------------------------ #
    # Job flow execution
    # ------------------------------------------------------------------ #
    def _execute_job_flow(self, mapref: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Handle both payload structures:
        # 1. payload = {"params": {...}} (nested)
        # 2. payload = {...} (params directly, for immediate jobs)
        if "params" in payload:
            params = payload.get("params", {})
        else:
            # If no "params" key, treat entire payload as params
            params = payload
        
        # Log parameters for debugging
        debug(f"Executing job flow for {mapref} with params: {params}")
        
        context = None
        source_conn = None
        target_conn = None
        
        with self._db_connection() as (conn, cursor):
            job_flow = self._load_job_flow(cursor, mapref)
            if not job_flow:
                raise SchedulerRepositoryError(f"No active job flow found for {mapref}")

            # Get source connection if SQLCONID is specified
            sqlconid = job_flow.get("SQLCONID")
            debug(f"SQLCONID from job flow: {sqlconid}")
            if sqlconid:
                try:
                    from database.dbconnect import create_target_connection
                    source_conn = create_target_connection(sqlconid)
                    if source_conn:
                        info(f"Using source connection (ID: {sqlconid}) for SELECT queries")
                    else:
                        warning(f"Source connection ID {sqlconid} not found, using metadata connection for source")
                except Exception as e:
                    error(f"Failed to create source connection {sqlconid}: {e}. Using metadata connection for source.")
                    import traceback
                    debug(f"Source connection creation traceback: {traceback.format_exc()}")
            else:
                debug("No SQLCONID specified in job flow, using metadata connection for source queries")
            
            # Get target connection if TRGCONID is specified
            trgconid = job_flow.get("TRGCONID")
            debug(f"TRGCONID from job flow: {trgconid}")
            if trgconid:
                try:
                    from database.dbconnect import create_target_connection
                    target_conn = create_target_connection(trgconid)
                    if target_conn:
                        # Verify the target connection can access the schema
                        try:
                            from modules.common.db_table_utils import _detect_db_type
                            target_db_type = _detect_db_type(target_conn)
                            test_cursor = target_conn.cursor()
                            
                            # Try to query the current user/schema with database-specific syntax
                            if target_db_type == "POSTGRESQL":
                                test_cursor.execute("SELECT current_user")
                                current_user = test_cursor.fetchone()[0]
                                test_cursor.execute("SELECT current_schema()")
                                current_schema = test_cursor.fetchone()[0]
                            else:  # Oracle
                                test_cursor.execute("SELECT USER FROM DUAL")
                                current_user = test_cursor.fetchone()[0]
                                test_cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL")
                                current_schema = test_cursor.fetchone()[0]
                            
                            test_cursor.close()
                            info(f"Using target connection (ID: {trgconid}) - Current user: {current_user}, Current schema: {current_schema}")
                        except Exception as test_e:
                            warning(f"Could not verify target connection schema: {test_e}")
                            info(f"Using target connection (ID: {trgconid}) for job execution")
                    else:
                        warning(f"Target connection ID {trgconid} not found, using metadata connection")
                except Exception as e:
                    error(f"Failed to create target connection {trgconid}: {e}. Using metadata connection.")
                    import traceback
                    debug(f"Target connection creation traceback: {traceback.format_exc()}")
            else:
                debug("No TRGCONID specified in job flow, using metadata connection for target operations")

            context = self._create_process_log(cursor, job_flow, params)
            conn.commit()

            # Prepare the code for execution
            # The code might be Python (new) or PL/SQL (legacy)
            code = job_flow["DWLOGIC"]
            if not code or not code.strip():
                raise RuntimeError(f"Empty or invalid DWLOGIC code for {mapref}")
            
            # Strip leading/trailing whitespace
            code = code.strip()
            
            # Detect code type: PL/SQL vs Python
            # Default to Python (new code generator creates Python)
            # Only treat as PL/SQL if it's clearly PL/SQL and NOT Python
            code_upper = code.upper()
            
            # Strong Python indicators (check first few lines and overall)
            first_lines = "\n".join(code.split("\n")[:10]).upper()
            is_python = any(
                indicator in first_lines or indicator in code_upper
                for indicator in [
                    "DEF EXECUTE_JOB", 
                    "DEF ", 
                    "IMPORT ", 
                    "FROM ", 
                    "EXECUTE_JOB(",
                    "HASHLIB",
                    "ORACLEDB",
                    "SESSION_PARAMS"
                ]
            )
            
            # Strong PL/SQL indicators - only if NOT Python
            is_plsql = (
                not is_python and  # Must not be Python
                code_upper.strip().startswith(("DECLARE", "BEGIN")) and  # Must start with PL/SQL keywords
                "DEF " not in code_upper  # Definitely not Python
            )
            
            debug(f"Code type detection - Python: {is_python}, PL/SQL: {is_plsql}")
            debug(f"First 500 chars of code: {code[:500]}")
            
            # Default to Python if unclear (new code is Python)
            if is_plsql:
                # Execute PL/SQL code using Oracle's execute immediate
                debug(f"Detected PL/SQL code, executing via Oracle (first 500 chars): {code[:500]}")
                debug(f"PL/SQL code length: {len(code)} characters")
                
                try:
                    code_to_execute = code.strip()
                    
                    # Check if it's already a complete PL/SQL block (starts with DECLARE or BEGIN)
                    code_upper_stripped = code_to_execute.upper().strip()
                    is_complete_block = (
                        code_upper_stripped.startswith("DECLARE") or
                        code_upper_stripped.startswith("BEGIN") or
                        code_upper_stripped.startswith("CREATE") or
                        code_upper_stripped.startswith("INSERT") or
                        code_upper_stripped.startswith("UPDATE") or
                        code_upper_stripped.startswith("DELETE") or
                        code_upper_stripped.startswith("MERGE")
                    )
                    
                    if not is_complete_block:
                        # Wrap in anonymous PL/SQL block
                        code_to_execute = f"BEGIN\n{code_to_execute}\nEND;"
                        debug("Wrapped PL/SQL code in anonymous block")
                    else:
                        # Ensure proper termination
                        if not code_to_execute.rstrip().endswith((';', '/')):
                            code_to_execute = code_to_execute.rstrip() + ';'
                    
                    # Execute PL/SQL using execute immediate within a wrapper block
                    # This mimics the original PL/SQL: execute immediate w_flw_rec.dwlogic;
                    plsql_wrapper = """
                    BEGIN
                        EXECUTE IMMEDIATE :code_block;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE;
                    END;
                    """
                    
                    debug(f"Executing PL/SQL block (last 200 chars): ...{code_to_execute[-200:]}")
                    cursor.execute(plsql_wrapper, {"code_block": code_to_execute})
                    
                    result = {}  # PL/SQL execution doesn't return Python dict
                    self._finalize_success(cursor, job_flow, context, result)
                    conn.commit()
                    return {
                        "status": "SUCCESS",
                        "result": result,
                        "prcid": context["PRCID"],
                    }
                except Exception as exc:
                    conn.rollback()
                    error_msg = str(exc)
                    error(f"PL/SQL execution failed for {mapref} (prcid={context['PRCID']}): {error_msg}")
                    error(f"PL/SQL code that failed (first 1000 chars): {code[:1000]}")
                    error(f"PL/SQL code that failed (last 500 chars): ...{code[-500:]}")
                    self._finalize_failure(cursor, context, error_msg)
                    conn.commit()
                    raise
            else:
                # Execute Python code
                # Handle indentation: if the code appears to be indented (starts with space/tab),
                # try to remove common leading whitespace
                lines = code.split("\n")
                if lines and lines[0].startswith((" ", "\t")):
                    # Find minimum leading whitespace among non-empty lines
                    non_empty_lines = [line for line in lines if line.strip()]
                    if non_empty_lines:
                        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
                        if min_indent > 0:
                            # Remove min_indent spaces from all lines (non-empty lines get dedented, empty lines stay empty)
                            code = "\n".join(
                                line[min_indent:] if line.strip() else line
                                for line in lines
                            )
                
                debug(f"Executing Python code (first 200 chars): {code[:200]}")
                
                namespace: Dict[str, Any] = {}
                try:
                    debug(f"Executing Python code (length: {len(code)} characters)")
                    exec(code, namespace)
                    debug(f"Python code executed successfully, checking for execute_job function...")
                except SyntaxError as e:
                    error(f"Syntax error in DWLOGIC for {mapref}: {e}")
                    error(f"Code snippet (lines {e.lineno-5 if e.lineno > 5 else 1}-{e.lineno+5}):")
                    code_lines = code.split("\n")
                    start = max(0, e.lineno - 5)
                    end = min(len(code_lines), e.lineno + 5)
                    for i in range(start, end):
                        marker = ">>> " if i == e.lineno - 1 else "    "
                        error(f"{marker}{i+1}: {code_lines[i]}")
                    raise RuntimeError(f"Syntax error in generated code for {mapref}: {e}") from e
                except Exception as e:
                    error(f"Error executing generated code for {mapref}: {type(e).__name__}: {e}")
                    error(f"First 500 chars of code:\n{code[:500]}")
                    import traceback
                    error(f"Traceback:\n{traceback.format_exc()}")
                    raise RuntimeError(f"Error executing generated code for {mapref}: {e}") from e
                
                execute_job = namespace.get("execute_job")
                if not execute_job:
                    error(f"execute_job not found in namespace. Available keys: {list(namespace.keys())}")
                    raise RuntimeError(f"execute_job not defined in DWLOGIC for {mapref}")
                
                debug(f"execute_job function found: {type(execute_job)}")

                # Build execution_args - the generated code expects param1, param2, etc. directly
                execution_args = {
                    "prcid": context["PRCID"],
                    "sessionid": context["SESSIONID"],
                    "mapref": mapref,
                }
                # Add param1-param10 directly to execution_args (as the generated code expects)
                for i in range(1, 11):
                    param_key = f"param{i}"
                    if param_key in params:
                        execution_args[param_key] = params[param_key]
                # Also include request_params for backward compatibility
                execution_args["request_params"] = params
                
                # Detect function signature to support both old and new code
                import inspect
                sig = inspect.signature(execute_job)
                param_count = len(sig.parameters)
                
                info(f"Starting job execution for {mapref} (PRCID: {context['PRCID']})")
                debug(f"execute_job signature: {param_count} parameters - {list(sig.parameters.keys())}")
                
                # Job execution timeout (default: 2 hours, configurable via environment variable)
                job_timeout_seconds = int(os.getenv('JOB_EXECUTION_TIMEOUT_SECONDS', '7200'))  # 2 hours default
                debug(f"Job execution timeout: {job_timeout_seconds} seconds")
                
                try:
                    # Capture stdout from the generated code (it uses print() statements)
                    import sys
                    from io import StringIO
                    import threading
                    
                    class StdoutCaptureLogger(StringIO):
                        """Capture stdout while streaming lines to the logger in real time."""
                        def __init__(self, map_reference: str):
                            super().__init__()
                            self._buffer = ""
                            self._lock = threading.Lock()
                            self._mapref = map_reference
                        
                        def write(self, text: str) -> int:
                            if not isinstance(text, str):
                                text = str(text)
                            with self._lock:
                                written = super().write(text)
                                self._buffer += text
                                
                                while "\n" in self._buffer:
                                    line, self._buffer = self._buffer.split("\n", 1)
                                    line_to_log = line.strip()
                                    if line_to_log:
                                        info(f"Job {self._mapref} output: {line_to_log}")
                            return len(text)
                        
                        def flush(self) -> None:
                            with self._lock:
                                pending = self._buffer.strip()
                                if pending:
                                    info(f"Job {self._mapref} output: {pending}")
                                self._buffer = ""
                            super().flush()
                    
                    # Create a string buffer to capture and stream print output
                    stdout_capture = StdoutCaptureLogger(mapref)
                    old_stdout = sys.stdout
                    
                    # Define execution function to run in thread with timeout
                    def execute_with_capture():
                        try:
                            # Redirect stdout to capture print statements from generated code
                            sys.stdout = stdout_capture
                            
                            # Log to captured output (will be visible in logs)
                            print(f"[EXECUTION ENGINE] About to call execute_job for {mapref}")
                            
                            # Determine which connection(s) to use based on function signature
                            if param_count == 2:
                                # Old signature: execute_job(connection, session_params)
                                # Use target connection if available, else metadata connection
                                execution_conn = target_conn if target_conn else conn
                                debug(f"Using old signature (2 params): execute_job(connection, session_params)")
                                if target_conn:
                                    debug(f"Using TARGET connection for old signature")
                                    # Verify target connection schema access
                                    try:
                                        from modules.common.db_table_utils import _detect_db_type
                                        target_db_type = _detect_db_type(target_conn)
                                        test_cursor = target_conn.cursor()
                                        
                                        # Use database-specific syntax
                                        if target_db_type == "POSTGRESQL":
                                            test_cursor.execute("SELECT current_user")
                                            conn_user = test_cursor.fetchone()[0]
                                            test_cursor.execute("SELECT current_schema()")
                                            conn_schema = test_cursor.fetchone()[0]
                                        else:  # Oracle
                                            test_cursor.execute("SELECT USER FROM DUAL")
                                            conn_user = test_cursor.fetchone()[0]
                                            test_cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL")
                                            conn_schema = test_cursor.fetchone()[0]
                                        
                                        test_cursor.close()
                                        debug(f"Target connection user: {conn_user}, schema: {conn_schema}")
                                    except Exception as e:
                                        debug(f"Could not verify target connection details: {e}")
                                else:
                                    debug(f"Using METADATA connection (no target connection available)")
                                return execute_job(execution_conn, execution_args) or {}
                            elif param_count == 3:
                                # Old signature: execute_job(metadata_connection, target_connection, session_params)
                                # Use source connection for source if available, else metadata
                                metadata_exec_conn = conn  # Always use metadata connection for logging
                                source_exec_conn = source_conn if source_conn else conn  # Use source if available, else metadata
                                target_exec_conn = target_conn if target_conn else conn  # Use target if available, else metadata
                                debug(f"Using signature (3 params): execute_job(metadata_connection, target_connection, session_params)")
                                debug(f"Note: This is backward compatibility mode - source and target may be same connection")
                                if target_conn:
                                    debug(f"Using separate connections: metadata for logging, target for data")
                                else:
                                    debug(f"Using metadata connection for both (no target connection specified)")
                                # For backward compatibility, pass metadata as source and target as target
                                return execute_job(metadata_exec_conn, target_exec_conn, execution_args) or {}
                            elif param_count == 4:
                                # New signature: execute_job(metadata_connection, source_connection, target_connection, session_params)
                                metadata_exec_conn = conn  # Always use metadata connection for logging
                                source_exec_conn = source_conn if source_conn else conn  # Use source if available, else metadata
                                target_exec_conn = target_conn if target_conn else conn  # Use target if available, else metadata
                                debug(f"Using new signature (4 params): execute_job(metadata_connection, source_connection, target_connection, session_params)")
                                if source_conn:
                                    debug(f"Using SOURCE connection (ID: {sqlconid}) for SELECT queries")
                                else:
                                    debug(f"Using metadata connection for source queries (no SQLCONID specified)")
                                if target_conn:
                                    debug(f"Using TARGET connection (ID: {trgconid}) for INSERT/UPDATE operations")
                                else:
                                    debug(f"Using metadata connection for target operations (no TRGCONID specified)")
                                return execute_job(metadata_exec_conn, source_exec_conn, target_exec_conn, execution_args) or {}
                            else:
                                raise RuntimeError(f"execute_job has unexpected signature: {param_count} parameters (expected 2, 3, or 4)")
                        except Exception as exec_err:
                            # Log the exception to captured output before restoring stdout
                            print(f"ERROR in execute_job: {type(exec_err).__name__}: {str(exec_err)}")
                            import traceback
                            print(f"Traceback:\n{traceback.format_exc()}")
                            raise
                        finally:
                            # Restore stdout
                            sys.stdout = old_stdout
                    
                    # Execute with timeout using ThreadPoolExecutor
                    result = None
                    execution_exception = None
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(execute_with_capture)
                        try:
                            result = future.result(timeout=job_timeout_seconds)
                            debug(f"Job execution completed within timeout")
                        except FutureTimeoutError:
                            error(f"Job {mapref} execution TIMED OUT after {job_timeout_seconds} seconds")
                            # Get any captured output before timeout
                            captured_output = stdout_capture.getvalue()
                            if captured_output:
                                error(f"Job {mapref} output before timeout:\n{captured_output}")
                            
                            # Mark the job as failed due to timeout
                            with self._db_connection() as (timeout_conn, timeout_cursor):
                                timeout_cursor.execute("""
                                    UPDATE DMS_PRCLOG 
                                    SET status = 'FAILED', 
                                        endtime = SYSTIMESTAMP,
                                        errmsg = :errmsg
                                    WHERE mapref = :mapref AND prcid = :prcid
                                """, {
                                    'errmsg': f'Job execution timed out after {job_timeout_seconds} seconds',
                                    'mapref': mapref,
                                    'prcid': context['PRCID']
                                })
                                timeout_conn.commit()
                            
                            # Try to cancel the future (though it may not work if stuck in DB call)
                            future.cancel()
                            raise RuntimeError(f"Job execution timed out after {job_timeout_seconds} seconds")
                        except Exception as exec_exc:
                            # Capture exception for logging
                            execution_exception = exec_exc
                            # Get captured output even if exception occurred
                            captured_output = stdout_capture.getvalue()
                            if captured_output:
                                error(f"Job {mapref} execution output before exception:\n{captured_output}")
                            raise
                    
                    # Get captured output (only if no exception occurred above)
                    if execution_exception is None:
                        captured_output = stdout_capture.getvalue()
                        
                        # Log captured output from generated code
                        if captured_output:
                            info(f"Job {mapref} execution output:\n{captured_output}")
                        else:
                            warning(f"Job {mapref} completed but produced no output. This may indicate the job didn't execute properly.")
                    
                    debug(f"Job execution completed. Result: {result}")
                    
                    # Log the results for debugging
                    if result:
                        source_rows = result.get('source_rows', 0)
                        target_rows = result.get('target_rows', 0)
                        error_rows = result.get('error_rows', 0)
                        status = result.get('status', 'UNKNOWN')
                        
                        info(
                            f"Job {mapref} completed - "
                            f"Status: {status}, "
                            f"Source: {source_rows}, Target: {target_rows}, Errors: {error_rows}"
                        )
                        
                        if target_rows == 0 and source_rows == 0:
                            warning(
                                f"Job {mapref} completed but processed 0 rows. "
                                f"Check source query and data availability."
                            )
                        elif target_rows == 0 and source_rows > 0:
                            warning(
                                f"Job {mapref} processed {source_rows} source rows but inserted 0 target rows. "
                                f"Check insert logic and target table constraints."
                            )
                    
                    # Finalize success using metadata connection for logging
                    with self._db_connection() as (log_conn, log_cursor):
                        self._finalize_success(log_cursor, job_flow, context, result)
                        log_conn.commit()
                    
                    # Commit source and target connections if used
                    if source_conn and source_conn != conn:
                        source_conn.commit()
                    if target_conn and target_conn != conn:
                        target_conn.commit()
                    
                    return {
                        "status": "SUCCESS",
                        "result": result,
                        "prcid": context["PRCID"],
                    }
                except Exception as exc:
                    # Get captured output even on exception
                    try:
                        captured_output = stdout_capture.getvalue()
                        if captured_output:
                            error(f"Job {mapref} execution output before failure:\n{captured_output}")
                    except Exception:
                        pass
                    
                    # Rollback all connections
                    try:
                        if source_conn and source_conn != conn:
                            source_conn.rollback()
                    except Exception:
                        pass
                    try:
                        if target_conn and target_conn != conn:
                            target_conn.rollback()
                    except Exception:
                        pass
                    try:
                        with self._db_connection() as (log_conn, log_cursor):
                            log_conn.rollback()
                    except Exception:
                        pass
                    
                    error_msg = str(exc)
                    import traceback
                    error(
                        f"Job execution failed for {mapref} (prcid={context['PRCID']}): {error_msg}\n"
                        f"Parameters passed: {params}\n"
                        f"Execution args: {execution_args}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    
                    # Finalize failure using metadata connection
                    with self._db_connection() as (log_conn, log_cursor):
                        self._finalize_failure(log_cursor, context, error_msg)
                        log_conn.commit()
                    raise
                finally:
                    # Close source connection if it was created
                    if source_conn and source_conn != conn:
                        try:
                            source_conn.close()
                        except Exception:
                            pass
                    
                    # Close target connection if it was created
                    if target_conn and target_conn != conn and target_conn != source_conn:
                        try:
                            target_conn.close()
                        except Exception:
                            pass

    def _execute_history_job(self, request: QueueRequest) -> Dict[str, Any]:
        start_date_str = request.payload.get("start_date")
        end_date_str = request.payload.get("end_date")
        truncate_flag = request.payload.get("truncate_flag", "N")
        if not start_date_str or not end_date_str:
            raise SchedulerRepositoryError("History job requires start_date and end_date")
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()

        current_date = start_date
        runs = 0
        while current_date <= end_date:
            params = {
                "param1": current_date.strftime("%d-%b-%Y"),
                "truncate_flag": truncate_flag if runs == 0 else "N",
            }
            info(
                f"Executing history slice {current_date} for {request.mapref} (truncate={params['truncate_flag']})"
            )
            self._execute_job_flow(request.mapref, {"params": params})
            current_date += timedelta(days=1)
            runs += 1
        return {"status": "SUCCESS", "runs": runs}

    def _execute_report_job(self, request: QueueRequest) -> Dict[str, Any]:
        from modules.reports.report_service import ReportMetadataService, ReportServiceError

        payload = request.payload or {}
        report_id = payload.get("reportId") or self._extract_report_id(request.mapref)
        if not report_id:
            raise SchedulerRepositoryError("Report ID missing in request payload")

        service = ReportMetadataService()
        try:
            result = service.execute_report(
                report_id=report_id,
                payload=payload,
                username=payload.get("requestedBy", "system"),
                request_id=request.request_id,
            )
            return {"status": "SUCCESS", **result}
        except ReportServiceError as exc:
            raise SchedulerRepositoryError(exc.message) from exc

    def _extract_report_id(self, mapref: Optional[str]) -> Optional[int]:
        if not mapref:
            return None
        if mapref.upper().startswith("REPORT:"):
            with suppress(Exception):
                return int(mapref.split(":", 1)[1])
        return None

    def _handle_stop_request(self, request: QueueRequest) -> Dict[str, Any]:
        """
        Handle stop request for a running job.
        The actual cancellation happens in the generated job code which checks for stop requests
        during batch processing. This handler just acknowledges the request.
        """
        info(
            f"Stop request received for {request.mapref} (request_id={request.request_id})"
        )
        
        # The stop request stays in DMS_PRCREQ with status 'CLAIMED' until the running job
        # acknowledges it and marks it as DONE. The generated job code polls for stop requests
        # and performs the actual cancellation.
        
        return {
            "status": "ACKNOWLEDGED",
            "message": f"Stop request acknowledged for {request.mapref}. Job will stop at next batch boundary.",
        }

    # ------------------------------------------------------------------ #
    # DB helpers
    # ------------------------------------------------------------------ #
    def _load_job_flow(self, cursor, mapref: str) -> Optional[Dict[str, Any]]:
        # Detect database type
        from modules.common.db_table_utils import _detect_db_type
        connection = cursor.connection
        db_type = _detect_db_type(connection)
        
        # Get schema from environment (default to no schema prefix if not set)
        schema = (os.getenv("DMS_SCHEMA", "")).strip()
        
        # Get table references for PostgreSQL (handles case sensitivity)
        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else 'public'
            dms_jobdtl_ref = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBDTL')
            dms_maprsql_ref = get_postgresql_table_name(cursor, schema_lower, 'DMS_MAPRSQL')
            dms_jobflw_ref = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBFLW')
            dms_job_ref = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOB')
            
            # Quote if uppercase (was created with quotes)
            dms_jobdtl_ref = f'"{dms_jobdtl_ref}"' if dms_jobdtl_ref != dms_jobdtl_ref.lower() else dms_jobdtl_ref
            dms_maprsql_ref = f'"{dms_maprsql_ref}"' if dms_maprsql_ref != dms_maprsql_ref.lower() else dms_maprsql_ref
            dms_jobflw_ref = f'"{dms_jobflw_ref}"' if dms_jobflw_ref != dms_jobflw_ref.lower() else dms_jobflw_ref
            dms_job_ref = f'"{dms_job_ref}"' if dms_job_ref != dms_job_ref.lower() else dms_job_ref
            
            schema_prefix = f'{schema_lower}.' if schema else ''
            dms_jobdtl_full = f'{schema_prefix}{dms_jobdtl_ref}'
            dms_maprsql_full = f'{schema_prefix}{dms_maprsql_ref}'
            dms_jobflw_full = f'{schema_prefix}{dms_jobflw_ref}'
            dms_job_full = f'{schema_prefix}{dms_job_ref}'
        else:
            schema_prefix = f"{schema}." if schema else ""
            dms_jobdtl_full = f"{schema_prefix}DMS_JOBDTL"
            dms_maprsql_full = f"{schema_prefix}DMS_MAPRSQL"
            dms_jobflw_full = f"{schema_prefix}DMS_JOBFLW"
            dms_job_full = f"{schema_prefix}DMS_JOB"
        
        # Query matches PL/SQL logic: curflg = 'Y' AND stflg = 'A'
        # Also get TRGCONID from DMS_JOB and SQLCONID FROM DMS_MAPRSQL to determine connections
        # Use LEFT JOINs to get job flow even if DMS_JOB/MAPRSQL don't match conditions
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT f.jobflwid, f.jobid, f.mapref, f.dwlogic, j.trgconid,
                       (SELECT s.sqlconid 
                        FROM {dms_jobdtl_full} jd
                        LEFT JOIN {dms_maprsql_full} s ON s.maprsqlcd = jd.maprsqlcd AND s.curflg = 'Y'
                        WHERE jd.mapref = f.mapref AND jd.curflg = 'Y'
                        LIMIT 1) as sqlconid
                FROM {dms_jobflw_full} f
                LEFT JOIN {dms_job_full} j ON j.mapref = f.mapref AND j.curflg = 'Y' AND j.stflg = 'A'
                WHERE f.mapref = %s
                  AND f.curflg = 'Y'
                  AND f.stflg = 'A'
            """
            cursor.execute(query, (mapref,))
        else:
            query = f"""
                SELECT f.jobflwid, f.jobid, f.mapref, f.dwlogic, j.trgconid,
                       (SELECT s.sqlconid 
                        FROM {dms_jobdtl_full} jd
                        LEFT JOIN {dms_maprsql_full} s ON s.maprsqlcd = jd.maprsqlcd AND s.curflg = 'Y'
                        WHERE jd.mapref = f.mapref AND jd.curflg = 'Y'
                        FETCH FIRST 1 ROW ONLY) as sqlconid
                FROM {dms_jobflw_full} f
                LEFT JOIN {dms_job_full} j ON j.mapref = f.mapref AND j.curflg = 'Y' AND j.stflg = 'A'
                WHERE f.mapref = :mapref
                  AND f.curflg = 'Y'
                  AND f.stflg = 'A'
            """
            cursor.execute(query, {"mapref": mapref})
        row = cursor.fetchone()
        
        # Debug: Check if DMS_JOB record exists for this mapref
        if row:
            debug(f"Found job flow record. Checking DMS_JOB for TRGCONID...")
            if db_type == "POSTGRESQL":
                check_dms_job_query = f"""
                    SELECT jobid, mapref, trgconid, curflg, stflg
                    FROM {dms_job_full}
                    WHERE mapref = %s
                """
                cursor.execute(check_dms_job_query, (mapref,))
            else:
                check_dms_job_query = f"""
                    SELECT jobid, mapref, trgconid, curflg, stflg
                    FROM {dms_job_full}
                    WHERE mapref = :mapref
                """
                cursor.execute(check_dms_job_query, {"mapref": mapref})
            dms_job_rows = cursor.fetchall()
            if dms_job_rows:
                debug(f"Found {len(dms_job_rows)} DMS_JOB record(s) for mapref={mapref}:")
                for dms_job_row in dms_job_rows:
                    debug(f"  JOBID={dms_job_row[0]}, MAPREF={dms_job_row[1]}, TRGCONID={dms_job_row[2]}, CURFLG={dms_job_row[3]}, STFLG={dms_job_row[4]}")
            else:
                debug(f"No DMS_JOB records found for mapref={mapref}")
        
        if not row:
            # Check if there are any records for this mapref (for debugging)
            if db_type == "POSTGRESQL":
                check_query = f"""
                    SELECT jobflwid, jobid, mapref, curflg, stflg
                    FROM {dms_jobflw_full}
                    WHERE mapref = %s
                """
                cursor.execute(check_query, (mapref,))
            else:
                check_query = f"""
                    SELECT jobflwid, jobid, mapref, curflg, stflg
                    FROM {dms_jobflw_full}
                    WHERE mapref = :mapref
                """
                cursor.execute(check_query, {"mapref": mapref})
            all_rows = cursor.fetchall()
            
            if all_rows:
                debug(f"Found {len(all_rows)} record(s) for mapref={mapref}, but none match curflg='Y' AND stflg='A':")
                for r in all_rows:
                    debug(f"  JOBFLWID={r[0]}, JOBID={r[1]}, MAPREF={r[2]}, CURFLG={r[3]}, STFLG={r[4]}")
                error(
                    f"No active job flow found for {mapref}. "
                    f"Found {len(all_rows)} record(s) but none with curflg='Y' AND stflg='A'. "
                    f"Please ensure at least one record has curflg='Y' AND stflg='A'"
                )
            else:
                error(f"No job flow records found at all for mapref={mapref}")
            return None
        
        job_flow = {
            "JOBFLWID": row[0],
            "JOBID": row[1],
            "MAPREF": row[2],
            "DWLOGIC": _read_lob(row[3]),
            "TRGCONID": row[4] if len(row) > 4 else None,  # Target connection ID
            "SQLCONID": row[5] if len(row) > 5 else None,  # Source connection ID
        }
        
        debug(f"Loaded job flow: JOBFLWID={job_flow['JOBFLWID']}, JOBID={job_flow['JOBID']}, MAPREF={job_flow['MAPREF']}, TRGCONID={job_flow['TRGCONID']}, SQLCONID={job_flow['SQLCONID']}")
        logic_length = len(job_flow['DWLOGIC']) if job_flow['DWLOGIC'] else 0
        debug(f"DWLOGIC length: {logic_length} characters")
        
        return job_flow

    def _create_process_log(self, cursor, job_flow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        # Detect database type
        from modules.common.db_table_utils import _detect_db_type
        connection = cursor.connection
        db_type = _detect_db_type(connection)
        schema = (os.getenv("DMS_SCHEMA", "")).strip()
        
        # Debug: Log database type detection
        debug(f"[_create_process_log] Detected database type: {db_type}")
        debug(f"[_create_process_log] Connection type: {type(connection).__name__}, module: {type(connection).__module__}")
        debug(f"[_create_process_log] Schema: {schema}")
        
        # Verify database type by attempting a database-specific query
        try:
            test_cursor = connection.cursor()
            if db_type == "POSTGRESQL":
                test_cursor.execute("SELECT 1")
            else:
                test_cursor.execute("SELECT 1 FROM DUAL")
            test_cursor.fetchone()
            test_cursor.close()
            debug(f"[_create_process_log] Database type verification successful: {db_type}")
        except Exception as verify_e:
            # If PostgreSQL query fails, try Oracle query to verify
            try:
                test_cursor = connection.cursor()
                test_cursor.execute("SELECT 1 FROM DUAL")
                test_cursor.fetchone()
                test_cursor.close()
                debug(f"[_create_process_log] Database type verification: Oracle query succeeded, switching to Oracle")
                db_type = "ORACLE"
            except Exception:
                # If both fail, check environment variable
                db_type_env = os.getenv("DB_TYPE", "ORACLE").upper()
                if db_type_env == "POSTGRESQL":
                    debug(f"[_create_process_log] Database type verification failed, using environment variable: POSTGRESQL")
                    db_type = "POSTGRESQL"
                else:
                    debug(f"[_create_process_log] Database type verification failed, defaulting to Oracle")
                    db_type = "ORACLE"
        
        prcid = _generate_numeric_id(cursor, "DMS_PRCLOGSEQ")
        # Ensure prcid is a valid integer
        if not isinstance(prcid, int):
            try:
                prcid = int(prcid)
            except (ValueError, TypeError) as e:
                error(f"Invalid PRCID generated: {prcid} (type: {type(prcid).__name__})")
                raise SchedulerRepositoryError(f"Failed to generate valid PRCID: {prcid}") from e
        debug(f"Generated PRCID: {prcid} (type: {type(prcid).__name__})")
        
        # Ensure jobid and jobflwid are integers (Oracle expects NUMBER type)
        # Oracle may return Decimal, int, float, or string - convert all to int
        def _to_int(value):
            """Convert various numeric types to int for Oracle NUMBER columns."""
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                # Try to convert string to int
                try:
                    return int(float(value))  # Handle "123.0" -> 123
                except ValueError:
                    raise ValueError(f"Cannot convert '{value}' to integer")
            # Handle Decimal and other numeric types
            try:
                return int(float(value))
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to integer")
        
        # Get session ID (NUMBER type, not UUID string)
        # DMS_PRCLOG.sessionid is NUMBER(30), matching PL/SQL: SYS_CONTEXT('USERENV','SESSIONID')
        try:
            if db_type == "POSTGRESQL":
                # PostgreSQL: Use pg_backend_pid() or generate a numeric ID
                cursor.execute("SELECT pg_backend_pid()")
                session_id_row = cursor.fetchone()
                if session_id_row and session_id_row[0] is not None:
                    session_id = _to_int(session_id_row[0])
                else:
                    session_id = int(datetime.utcnow().timestamp() * 1000000) % (10**30)
            else:  # Oracle
                cursor.execute("SELECT SYS_CONTEXT('USERENV','SESSIONID') FROM dual")
                session_id_row = cursor.fetchone()
                if session_id_row and session_id_row[0] is not None:
                    session_id = _to_int(session_id_row[0])
                else:
                    session_id = int(datetime.utcnow().timestamp() * 1000000) % (10**30)
            debug(f"Session ID: {session_id} (type: {type(session_id).__name__})")
        except Exception as e:
            error(f"Failed to get session ID: {e}")
            # Fallback: use a numeric ID
            session_id = int(datetime.utcnow().timestamp() * 1000000) % (10**30)
            debug(f"Using fallback session ID: {session_id}")
        
        param_values = [params.get(f"param{i}", None) for i in range(1, 11)]
        param_log = " | ".join(
            f"param{i}={value}" for i, value in enumerate(param_values, start=1) if value is not None
        )
        
        try:
            jobid_raw = job_flow.get("JOBID")
            jobid = _to_int(jobid_raw)
            debug(f"JOBID: raw={jobid_raw} (type={type(jobid_raw).__name__}), converted={jobid}")
        except Exception as e:
            error(f"Failed to convert JOBID: {job_flow.get('JOBID')} (type: {type(job_flow.get('JOBID')).__name__}): {e}")
            raise SchedulerRepositoryError(f"Invalid JOBID value: {job_flow.get('JOBID')}") from e
        
        try:
            jobflwid_raw = job_flow.get("JOBFLWID")
            jobflwid = _to_int(jobflwid_raw)
            debug(f"JOBFLWID: raw={jobflwid_raw} (type={type(jobflwid_raw).__name__}), converted={jobflwid}")
        except Exception as e:
            error(f"Failed to convert JOBFLWID: {job_flow.get('JOBFLWID')} (type: {type(job_flow.get('JOBFLWID')).__name__}): {e}")
            raise SchedulerRepositoryError(f"Invalid JOBFLWID value: {job_flow.get('JOBFLWID')}") from e

        # Prepare values with explicit type conversion
        # Ensure all numeric values are int (not Decimal or float)
        # String values can be passed as-is (they're already strings or None)
        insert_values = {
            "prcid": int(prcid) if prcid is not None else None,
            "jobid": int(jobid) if jobid is not None else None,
            "jobflwid": int(jobflwid) if jobflwid is not None else None,
            "prclog": param_log[:4000] if param_log else None,
            "mapref": job_flow.get("MAPREF"),
            "sessionid": session_id,
            "param1": param_values[0],
            "param2": param_values[1],
            "param3": param_values[2],
            "param4": param_values[3],
            "param5": param_values[4],
            "param6": param_values[5],
            "param7": param_values[6],
            "param8": param_values[7],
            "param9": param_values[8],
            "param10": param_values[9],
        }
        debug(f"Inserting into DMS_PRCLOG with values: {[(k, v, type(v).__name__) for k, v in insert_values.items()]}")
        debug(f"[_create_process_log] About to execute INSERT - db_type={db_type}, schema={schema}")
        
        # Get table reference for PostgreSQL (handles case sensitivity)
        if db_type == "POSTGRESQL":
            debug(f"[_create_process_log] Using PostgreSQL INSERT syntax")
            schema_lower = schema.lower() if schema else 'public'
            dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
            # Quote table name if it contains uppercase letters (was created with quotes)
            dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
            schema_prefix = f'{schema_lower}.' if schema else ''
            dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
            
            # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
            cursor.execute(
                f"""
                INSERT INTO {dms_prclog_full} (
                    prcid, jobid, jobflwid,
                    strtdt, status, reccrdt, recupdt,
                    prclog, mapref, sessionid,
                    param1, param2, param3, param4, param5,
                    param6, param7, param8, param9, param10
                ) VALUES (
                    %s, %s, %s,
                    CURRENT_TIMESTAMP, 'IP', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    insert_values["prcid"],
                    insert_values["jobid"],
                    insert_values["jobflwid"],
                    insert_values["prclog"],
                    insert_values["mapref"],
                    insert_values["sessionid"],
                    insert_values["param1"],
                    insert_values["param2"],
                    insert_values["param3"],
                    insert_values["param4"],
                    insert_values["param5"],
                    insert_values["param6"],
                    insert_values["param7"],
                    insert_values["param8"],
                    insert_values["param9"],
                    insert_values["param10"],
                ),
            )
        else:  # Oracle
            debug(f"[_create_process_log] Using Oracle INSERT syntax (db_type={db_type})")
            schema_prefix = f"{schema}." if schema else ""
            # Oracle: Use :param for bind variables and SYSTIMESTAMP
            cursor.execute(
                f"""
                INSERT INTO {schema_prefix}DMS_PRCLOG (
                    prcid, jobid, jobflwid,
                    strtdt, status, reccrdt, recupdt,
                    prclog, mapref, sessionid,
                    param1, param2, param3, param4, param5,
                    param6, param7, param8, param9, param10
                ) VALUES (
                    :prcid, :jobid, :jobflwid,
                    SYSTIMESTAMP, 'IP', SYSTIMESTAMP, SYSTIMESTAMP,
                    :prclog, :mapref, :sessionid,
                    :param1, :param2, :param3, :param4, :param5,
                    :param6, :param7, :param8, :param9, :param10
                )
                """,
                insert_values,
            )
        return {"PRCID": prcid, "SESSIONID": session_id}

    def _finalize_success(self, cursor, job_flow, context, result):
        # Detect database type for table reference
        from modules.common.db_table_utils import _detect_db_type
        connection = cursor.connection
        db_type = _detect_db_type(connection)
        schema = (os.getenv("DMS_SCHEMA", "")).strip()
        
        # Get table references for PostgreSQL (handles case sensitivity)
        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else 'public'
            dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
            dms_joblog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBLOG')
            # Quote table names if they contain uppercase letters (were created with quotes)
            dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
            dms_joblog_ref = f'"{dms_joblog_table}"' if dms_joblog_table != dms_joblog_table.lower() else dms_joblog_table
            schema_prefix = f'{schema_lower}.' if schema else ''
            dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
            dms_joblog_full = f'{schema_prefix}{dms_joblog_ref}'
            
            # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
            cursor.execute(
                f"""
                UPDATE {dms_prclog_full}
                SET enddt = CURRENT_TIMESTAMP,
                    status = 'PC',
                    recupdt = CURRENT_TIMESTAMP,
                    msg = NULL
                WHERE prcid = %s
                """,
                (context["PRCID"],),
            )
            
            cursor.execute(
                f"SELECT COUNT(1) FROM {dms_joblog_full} WHERE prcid = %s",
                (context["PRCID"],),
            )
        else:  # Oracle
            schema_prefix = f"{schema}." if schema else ""
            # Oracle: Use :param for bind variables and SYSTIMESTAMP
            cursor.execute(
                f"""
                UPDATE {schema_prefix}DMS_PRCLOG
                SET enddt = SYSTIMESTAMP,
                    status = 'PC',
                    recupdt = SYSTIMESTAMP,
                    msg = NULL
                WHERE prcid = :prcid
                """,
                {"prcid": context["PRCID"]},
            )
            
            cursor.execute(
                f"SELECT COUNT(1) FROM {schema_prefix}DMS_JOBLOG WHERE prcid = :prcid",
                {"prcid": context["PRCID"]},
            )
        existing_logs = cursor.fetchone()[0]
        if existing_logs:
            return

        joblogid = _generate_numeric_id(cursor, "DMS_JOBLOGSEQ")
        
        if db_type == "POSTGRESQL":
            # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
            cursor.execute(
                f"""
                INSERT INTO {dms_joblog_full} (
                    joblogid, prcdt, mapref, jobid,
                    srcrows, trgrows, errrows,
                    reccrdt, prcid, sessionid
                ) VALUES (
                    %s, CURRENT_TIMESTAMP, %s, %s,
                    %s, %s, %s,
                    CURRENT_TIMESTAMP, %s, %s
                )
                """,
                (
                    joblogid,
                    job_flow.get("MAPREF"),
                    job_flow["JOBID"],
                    result.get("source_rows"),
                    result.get("target_rows"),
                    result.get("error_rows"),
                    context["PRCID"],
                    context["SESSIONID"],
                ),
            )
        else:  # Oracle
            # Oracle: Use :param for bind variables and SYSTIMESTAMP
            cursor.execute(
                f"""
                INSERT INTO {schema_prefix}DMS_JOBLOG (
                    joblogid, prcdt, mapref, jobid,
                    srcrows, trgrows, errrows,
                    reccrdt, prcid, sessionid
                ) VALUES (
                    :joblogid, SYSTIMESTAMP, :mapref, :jobid,
                    :srcrows, :trgrows, :errrows,
                    SYSTIMESTAMP, :prcid, :sessionid
                )
                """,
                {
                    "joblogid": joblogid,
                    "mapref": job_flow.get("MAPREF"),
                    "jobid": job_flow["JOBID"],
                    "srcrows": result.get("source_rows"),
                    "trgrows": result.get("target_rows"),
                    "errrows": result.get("error_rows"),
                    "prcid": context["PRCID"],
                    "sessionid": context["SESSIONID"],
                },
            )

    def _finalize_failure(self, cursor, context, message: str):
        if not context:
            return
        
        # Detect database type for table reference
        from modules.common.db_table_utils import _detect_db_type
        connection = cursor.connection
        db_type = _detect_db_type(connection)
        schema = (os.getenv("DMS_SCHEMA", "")).strip()
        
        # Get table reference for PostgreSQL (handles case sensitivity)
        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else 'public'
            dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
            # Quote table name if it contains uppercase letters (was created with quotes)
            dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
            schema_prefix = f'{schema_lower}.' if schema else ''
            dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
            
            # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
            cursor.execute(
                f"""
                UPDATE {dms_prclog_full}
                SET enddt = CURRENT_TIMESTAMP,
                    status = 'FL',
                    recupdt = CURRENT_TIMESTAMP,
                    msg = %s
                WHERE prcid = %s
                """,
                (
                    message[:400] if message else None,
                    context["PRCID"],
                ),
            )
        else:  # Oracle
            schema_prefix = f"{schema}." if schema else ""
            # Oracle: Use :param for bind variables and SYSTIMESTAMP
            cursor.execute(
                f"""
                UPDATE {schema_prefix}DMS_PRCLOG
                SET enddt = SYSTIMESTAMP,
                    status = 'FL',
                    recupdt = SYSTIMESTAMP,
                    msg = :msg
                WHERE prcid = :prcid
                """,
                {
                    "msg": message[:400] if message else None,
                    "prcid": context["PRCID"],
                },
            )

    @contextmanager
    def _db_connection(self):
        connection = create_metadata_connection()
        cursor = connection.cursor()
        try:
            yield connection, cursor
        finally:
            try:
                cursor.close()
            finally:
                connection.close()

