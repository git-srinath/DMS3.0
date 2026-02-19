"""
Mapper job execution framework.
Generic execution framework for mapper jobs.
No job-specific code - all job data passed as parameters.
"""
import sys
from typing import Dict, Any, List, Callable, Optional, Tuple
from datetime import datetime

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.database_sql_adapter import create_adapter, detect_database_type
    from backend.modules.mapper.mapper_transformation_utils import (
        map_row_to_target_columns,
        generate_hash,
        build_primary_key_values,
        build_primary_key_where_clause
    )
    from backend.modules.mapper.mapper_progress_tracker import (
        check_stop_request,
        log_batch_progress,
        update_process_log_progress
    )
    from backend.modules.mapper.mapper_checkpoint_handler import (
        parse_checkpoint_value,
        apply_checkpoint_to_query,
        update_checkpoint,
        complete_checkpoint
    )
    from backend.modules.mapper.mapper_scd_handler import (
        process_scd_batch,
        prepare_row_for_scd
    )
    from backend.modules.logger import info, warning, error, debug
    from backend.modules.mapper.chunk_manager import ChunkManager
    from backend.modules.mapper.parallel_integration_helper import (
        get_parallel_config_from_params,
        should_use_parallel_processing
    )
    from backend.modules.mapper.parallel_processor import ParallelProcessor
    from backend.modules.mapper.parallel_models import ParallelProcessingResult, ChunkResult
    from backend.modules.mapper.parallel_retry_handler import create_retry_handler
    from backend.modules.mapper.parallel_progress import ProgressTracker, create_progress_callback
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.database_sql_adapter import create_adapter, detect_database_type  # type: ignore
    from modules.mapper.mapper_transformation_utils import (  # type: ignore
        map_row_to_target_columns,
        generate_hash,
        build_primary_key_values,
        build_primary_key_where_clause
    )
    from modules.mapper.mapper_progress_tracker import (  # type: ignore
        check_stop_request,
        log_batch_progress,
        update_process_log_progress
    )
    from modules.mapper.mapper_checkpoint_handler import (  # type: ignore
        parse_checkpoint_value,
        apply_checkpoint_to_query,
        update_checkpoint,
        complete_checkpoint
    )
    from modules.mapper.mapper_scd_handler import (  # type: ignore
        process_scd_batch,
        prepare_row_for_scd
    )
    from modules.logger import info, warning, error, debug  # type: ignore
    from modules.mapper.chunk_manager import ChunkManager  # type: ignore
    from modules.mapper.parallel_integration_helper import (  # type: ignore
        get_parallel_config_from_params,
        should_use_parallel_processing
    )
    from modules.mapper.parallel_processor import ParallelProcessor  # type: ignore
    from modules.mapper.parallel_models import ParallelProcessingResult, ChunkResult  # type: ignore
    from modules.mapper.parallel_retry_handler import create_retry_handler  # type: ignore
    from modules.mapper.parallel_progress import ProgressTracker, create_progress_callback  # type: ignore


def execute_mapper_job(
    metadata_conn,
    source_conn,
    target_conn,
    job_config: Dict[str, Any],
    source_sql: str,
    transformation_func: Callable,
    checkpoint_config: Dict[str, Any],
    session_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute mapper job with all common logic handled internally.
    
    This is the main execution framework that:
    - Validates connections
    - Handles checkpoints
    - Executes source queries
    - Processes data in batches
    - Applies transformations
    - Handles SCD logic
    - Logs progress
    - Returns results
    
    Args:
        metadata_conn: Metadata database connection (for DMS_JOBLOG, DMS_PRCLOG)
        source_conn: Source database connection (for SELECT queries)
        target_conn: Target database connection (for INSERT/UPDATE operations)
        job_config: Job-specific configuration dictionary with:
            - 'mapref': str - Mapping reference
            - 'jobid': int - Job ID
            - 'target_schema': str - Target schema name
            - 'target_table': str - Target table name
            - 'target_type': str - Target table type ('DIM', 'FCT', 'MRT')
            - 'full_table_name': str - Full table name (schema.table)
            - 'pk_columns': Set[str] - Primary key column names
            - 'pk_source_mapping': Dict[str, str] - PK target -> source mapping
            - 'all_columns': List[str] - All target columns
            - 'column_source_mapping': Dict[str, str] - Column target -> source mapping
            - 'hash_exclude_columns': Set[str] - Columns to exclude from hash
            - 'block_process_rows': int - Batch size
            - 'bulk_limit': int - Bulk processing limit
            - 'scd_type': int - SCD type (1 or 2)
            - 'parallel_config': Optional[Dict[str, Any]] - Parallel processing configuration:
                - 'enable_parallel': bool - Enable parallel processing
                - 'max_workers': Optional[int] - Number of worker threads
                - 'chunk_size': int - Rows per chunk
                - 'min_rows_for_parallel': int - Minimum rows to enable parallel
        source_sql: Source SQL query (job-specific)
        transformation_func: Function to transform source rows (job-specific)
                            Signature: (Dict[str, Any]) -> Dict[str, Any]
        checkpoint_config: Checkpoint configuration dictionary with:
            - 'enabled': bool
            - 'strategy': str ('KEY', 'PYTHON', 'AUTO', 'NONE')
            - 'columns': List[str] - Checkpoint column names
            - 'column': Optional[str] - Single checkpoint column name
        session_params: Session parameters from DMS_PRCLOG with:
            - 'prcid': int - Process ID
            - 'sessionid': int - Session ID
            - 'param1': Optional[str] - Checkpoint value (if any)
            
    Returns:
        Dictionary with execution results:
        {
            'status': 'SUCCESS' | 'FAILED' | 'STOPPED',
            'source_rows': int,
            'target_rows': int,
            'error_rows': int,
            'message': Optional[str]
        }
    """
    # Extract job configuration
    mapref = job_config['mapref']
    jobid = job_config['jobid']
    target_schema = job_config['target_schema']
    target_table = job_config['target_table']
    target_type = job_config['target_type']
    full_table_name = job_config['full_table_name']
    pk_columns = job_config['pk_columns']
    pk_source_mapping = job_config['pk_source_mapping']
    all_columns = job_config['all_columns']
    column_source_mapping = job_config['column_source_mapping']
    hash_exclude_columns = job_config.get('hash_exclude_columns', set())
    bulk_limit = job_config.get('bulk_limit', 50000)
    scd_type = job_config.get('scd_type', 1)
    parallel_config = job_config.get('parallel_config', {})
    
    # Log parallel config at the very start for debugging
    if parallel_config:
        debug(f"[execute_mapper_job] Parallel config found in job_config: enable_parallel={parallel_config.get('enable_parallel', False)}, "
             f"min_rows={parallel_config.get('min_rows_for_parallel', 'N/A')}")
    else:
        info(f"[execute_mapper_job] WARNING: No parallel_config in job_config. Available keys: {list(job_config.keys())[:10]}...")
    
    # Detect database types
    source_db_type = detect_database_type(source_conn)
    target_db_type = detect_database_type(target_conn)
    metadata_db_type = detect_database_type(metadata_conn)
    
    # Initialize
    debug("=" * 80)
    debug(f"EXECUTE_JOB STARTED for {mapref}")
    debug(f"  Target: {full_table_name}")
    debug(f"  SCD Type: {scd_type}")
    debug("=" * 80)
    
    metadata_cursor = None
    source_cursor = None
    target_cursor = None
    
    try:
        # Validate connections
        _validate_connections(metadata_conn, source_conn, target_conn)
        
        # Create cursors
        metadata_cursor = metadata_conn.cursor()
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Check for stop request at start
        if check_stop_request(metadata_conn, mapref):
            print(f"STOP request detected for {mapref} at job start. Exiting immediately.")
            return {
                'status': 'STOPPED',
                'source_rows': 0,
                'target_rows': 0,
                'error_rows': 0,
                'message': 'Job stopped by user request before processing started'
            }
        
        # Verify target table exists
        _verify_target_table(target_cursor, full_table_name, target_schema, target_table, target_db_type)
        
        # Parse checkpoint
        checkpoint_value = session_params.get('param1')
        checkpoint_value, checkpoint_values, rows_to_skip = parse_checkpoint_value(
            checkpoint_value,
            checkpoint_config.get('strategy', 'AUTO'),
            checkpoint_config.get('columns', [])
        )
        
        # Apply checkpoint to query
        source_query, query_bind_params = apply_checkpoint_to_query(
            source_sql,
            checkpoint_config,
            checkpoint_value,
            checkpoint_values,
            source_db_type
        )
        
        # Check if parallel processing should be used (Phase 4)
        use_parallel = False
        estimated_rows = 0
        
        # Always log parallel configuration for debugging (even if not enabled)
        info("=" * 80)
        info("PARALLEL PROCESSING EVALUATION")
        info("=" * 80)
        if parallel_config:
            info(f"Parallel config from job_config: enable_parallel={parallel_config.get('enable_parallel', False)}, "
                 f"min_rows_for_parallel={parallel_config.get('min_rows_for_parallel', 100000)}, "
                 f"chunk_size={parallel_config.get('chunk_size', 50000)}, "
                 f"max_workers={parallel_config.get('max_workers', 'default')}")
        else:
            info("WARNING: Parallel processing configuration not found in job_config - using sequential processing")
            info("  (Check if environment variables MAPPER_PARALLEL_ENABLED, MAPPER_MIN_ROWS_FOR_PARALLEL are set)")
        
        # Check checkpoint strategy
        checkpoint_strategy = checkpoint_config.get('strategy', 'AUTO')
        checkpoint_enabled = checkpoint_config.get('enabled', False)
        info(f"Checkpoint config: enabled={checkpoint_enabled}, strategy={checkpoint_strategy}")
        
        if parallel_config and parallel_config.get('enable_parallel', False):
            # PYTHON checkpoint strategy is not supported in parallel processing
            # (requires row skipping after fetch, which doesn't work with chunking)
            if checkpoint_enabled and checkpoint_strategy == 'PYTHON':
                info("=" * 80)
                info("PARALLEL PROCESSING DISABLED: PYTHON checkpoint strategy not supported in parallel mode")
                info("  Reason: PYTHON checkpoint requires row-by-row skipping which is incompatible with chunking")
                info("  Solution: Use KEY checkpoint strategy or disable checkpoints to enable parallel processing")
                info("=" * 80)
                use_parallel = False
            else:
                # Estimate row count to decide if parallel processing should be used
                try:
                    chunk_manager = ChunkManager(source_db_type)
                    # Use the checkpoint-modified query for estimation
                    estimated_rows = chunk_manager.estimate_total_rows(source_conn, source_query)
                    min_rows = parallel_config.get('min_rows_for_parallel', 100000)
                    
                    info(f"Row count estimation: {estimated_rows} rows (parallel threshold: {min_rows})")
                    
                    if estimated_rows >= min_rows:
                        use_parallel = True
                        info(f"*** PARALLEL PROCESSING ENABLED ***: {estimated_rows} rows >= {min_rows} threshold")
                    else:
                        info(f"Parallel processing disabled: {estimated_rows} rows below threshold ({min_rows}) - using sequential processing")
                except Exception as e:
                    warning(f"Failed to estimate row count for parallel processing: {e}. Using sequential processing.")
                    use_parallel = False
        else:
            if not parallel_config:
                info("Parallel processing disabled: parallel_config not provided")
            elif not parallel_config.get('enable_parallel', False):
                info("Parallel processing disabled: enable_parallel is False")
        
        # Extract source columns before parallel/sequential decision
        # We need column info for both paths
        # Execute query to get column descriptions (we'll close and re-execute in parallel path)
        if query_bind_params:
            source_cursor.execute(source_query, query_bind_params)
        else:
            source_cursor.execute(source_query)
        
        # Get source columns (needed for both parallel and sequential paths)
        source_columns = [desc[0] for desc in source_cursor.description]
        
        # Use parallel processing if enabled and conditions are met
        if use_parallel:
            # Close the cursor since parallel processing will create its own connections/cursors
            source_cursor.close()
            return _execute_mapper_job_parallel(
                metadata_conn, source_conn, target_conn,
                job_config, source_query, query_bind_params, transformation_func,
                checkpoint_config, session_params,
                source_columns, source_db_type, target_db_type,
                parallel_config, estimated_rows
            )
        source_cursor.arraysize = bulk_limit
        
        # Skip rows for PYTHON checkpoint strategy
        if checkpoint_config.get('enabled', False) and \
           checkpoint_config.get('strategy') == 'PYTHON' and \
           rows_to_skip > 0:
            print(f"Skipping {rows_to_skip} rows (PYTHON strategy)...")
            for _ in range(rows_to_skip):
                row = source_cursor.fetchone()
                if not row:
                    break
        
        # Initialize counters
        source_count = 0
        target_count = 0
        error_count = 0
        batch_num = rows_to_skip // bulk_limit if checkpoint_config.get('strategy') == 'PYTHON' else 0
        
        # Process batches
        print(f"Starting batch processing (bulk_limit={bulk_limit})...")
        
        while True:
            # Check for stop request
            if check_stop_request(metadata_conn, mapref):
                print(f"STOP request detected for {mapref}. Stopping job gracefully...")
                break
            
            # Fetch batch
            try:
                if source_cursor.description is None:
                    print("Source cursor exhausted.")
                    break
                
                source_rows = source_cursor.fetchmany(bulk_limit)
                if not source_rows:
                    print("No more rows to process.")
                    break
                
            except Exception as fetch_err:
                error_msg = str(fetch_err)
                if "does not return rows" in error_msg or "DPY-1003" in error_msg:
                    print("Cursor exhausted.")
                    break
                else:
                    error(f"Error fetching batch: {error_msg}")
                    break
            
            # Process batch
            batch_num += 1
            batch_size = len(source_rows)
            source_count += batch_size
            batch_target_rows = 0
            batch_error_start = error_count
            
            print(f"Processing batch {batch_num}: {batch_size} rows")
            
            # Prepare batch data
            rows_to_insert = []
            rows_to_update_scd1 = []
            rows_to_update_scd2 = []
            
            for src_row in source_rows:
                # Check for stop request periodically
                if len(rows_to_insert) + len(rows_to_update_scd1) > 0 and \
                   (len(rows_to_insert) + len(rows_to_update_scd1)) % 100 == 0:
                    if check_stop_request(metadata_conn, mapref):
                        print(f"STOP request detected during row processing.")
                        break
                
                try:
                    # Convert row to dictionary
                    raw_src_dict = dict(zip(source_columns, src_row))
                    
                    # Apply transformation (job-specific)
                    src_dict = transformation_func(raw_src_dict)
                    
                    # Build primary key for lookup
                    pk_values = build_primary_key_values(
                        raw_src_dict,
                        pk_columns,
                        pk_source_mapping
                    )
                    
                    # Check for NULL PK values
                    if any(v is None for v in pk_values.values()):
                        warning(f"NULL primary key values found. Skipping row.")
                        error_count += 1
                        continue
                    
                    # Lookup existing record
                    target_row = _lookup_target_record(
                        target_cursor,
                        full_table_name,
                        pk_values,
                        target_db_type,
                        target_schema,
                        target_table
                    )
                    
                    # Generate hash
                    src_hash = generate_hash(src_dict, all_columns, hash_exclude_columns)
                    
                    # Prepare for SCD processing
                    row_to_insert, row_to_update_scd1, skey_to_expire_scd2 = prepare_row_for_scd(
                        src_dict,
                        target_row,
                        src_hash,
                        scd_type,
                        target_type
                    )
                    
                    if row_to_insert:
                        rows_to_insert.append(row_to_insert)
                    if row_to_update_scd1:
                        rows_to_update_scd1.append(row_to_update_scd1)
                    if skey_to_expire_scd2:
                        rows_to_update_scd2.append(skey_to_expire_scd2)
                        
                except Exception as row_err:
                    error(f"Error processing row: {row_err}")
                    error_count += 1
                    continue
            
            # Process SCD batch
            try:
                inserted, updated, expired = process_scd_batch(
                    target_conn,
                    target_schema,
                    target_table,
                    full_table_name,
                    rows_to_insert,
                    rows_to_update_scd1,
                    rows_to_update_scd2,
                    all_columns,
                    scd_type,
                    target_type,
                    target_db_type
                )
                
                target_count += inserted + updated
                batch_target_rows = inserted + updated
                
            except Exception as scd_err:
                error(f"Error processing SCD batch: {scd_err}")
                error_count += len(rows_to_insert) + len(rows_to_update_scd1) + len(rows_to_update_scd2)
            
            # Commit target connection periodically
            if batch_num % 5 == 0:
                target_conn.commit()
                print(f"Committed target connection (batch {batch_num})")
            
            # Update progress
            update_process_log_progress(metadata_conn, session_params, source_count, target_count)
            
            batch_error_rows = error_count - batch_error_start
            log_batch_progress(
                metadata_conn,
                mapref,
                jobid,
                batch_num,
                batch_size,
                batch_target_rows,
                batch_error_rows,
                session_params
            )
            metadata_conn.commit()
            
            # Update checkpoint (KEY strategy)
            if checkpoint_config.get('enabled', False) and \
               checkpoint_config.get('strategy') == 'KEY' and \
               checkpoint_config.get('columns'):
                last_row = source_rows[-1]
                last_row_dict = dict(zip(source_columns, last_row))
                checkpoint_columns = checkpoint_config['columns']
                
                if len(checkpoint_columns) > 1:
                    # Composite key
                    checkpoint_values_list = [
                        str(last_row_dict.get(col, '')) for col in checkpoint_columns
                    ]
                    new_checkpoint_value = '|'.join(checkpoint_values_list)
                else:
                    # Single column
                    new_checkpoint_value = str(last_row_dict.get(checkpoint_columns[0], ''))
                
                if new_checkpoint_value:
                    update_checkpoint(metadata_conn, session_params, new_checkpoint_value)
                    metadata_conn.commit()
        
        # Mark checkpoint as completed
        if checkpoint_config.get('enabled', False):
            complete_checkpoint(metadata_conn, session_params)
            metadata_conn.commit()
        
        # Final commit
        target_conn.commit()
        metadata_conn.commit()
        
        print(f"Job completed: {source_count} source rows, {target_count} target rows, {error_count} errors")
        
        return {
            'status': 'SUCCESS',
            'source_rows': source_count,
            'target_rows': target_count,
            'error_rows': error_count
        }
        
    except Exception as e:
        error(f"Job execution failed: {e}", exc_info=True)
        try:
            if target_conn:
                target_conn.rollback()
            if metadata_conn:
                metadata_conn.rollback()
        except Exception:
            pass
        
        return {
            'status': 'FAILED',
            'source_rows': source_count if 'source_count' in locals() else 0,
            'target_rows': target_count if 'target_count' in locals() else 0,
            'error_rows': error_count if 'error_count' in locals() else 0,
            'message': str(e)
        }
        
    finally:
        # Close cursors
        try:
            if metadata_cursor:
                metadata_cursor.close()
            if source_cursor:
                source_cursor.close()
            if target_cursor:
                target_cursor.close()
        except Exception:
            pass


def _execute_mapper_job_parallel(
    metadata_conn,
    source_conn,
    target_conn,
    job_config: Dict[str, Any],
    source_query: str,
    query_bind_params: Optional[Dict[str, Any]],
    transformation_func: Callable,
    checkpoint_config: Dict[str, Any],
    session_params: Dict[str, Any],
    source_columns: List[str],
    source_db_type: str,
    target_db_type: str,
    parallel_config: Dict[str, Any],
    estimated_rows: int
) -> Dict[str, Any]:
    """
    Execute mapper job using parallel processing (Phase 4).
    
    This function processes data in parallel chunks while maintaining:
    - SCD Type 1 and Type 2 logic
    - Checkpoint handling
    - Progress tracking
    - Stop request handling
    - Error handling and retry
    
    Args:
        metadata_conn: Metadata database connection
        source_conn: Source database connection
        target_conn: Target database connection
        job_config: Job configuration
        source_query: Source SQL query (with checkpoint applied)
        query_bind_params: Query bind parameters
        transformation_func: Transformation function
        checkpoint_config: Checkpoint configuration
        session_params: Session parameters
        source_columns: Source column names
        source_db_type: Source database type
        target_db_type: Target database type
        parallel_config: Parallel processing configuration
        estimated_rows: Estimated total rows
        
    Returns:
        Execution result dictionary
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    mapref = job_config['mapref']
    jobid = job_config['jobid']
    target_schema = job_config['target_schema']
    target_table = job_config['target_table']
    target_type = job_config['target_type']
    full_table_name = job_config['full_table_name']
    pk_columns = job_config['pk_columns']
    pk_source_mapping = job_config['pk_source_mapping']
    all_columns = job_config['all_columns']
    hash_exclude_columns = job_config.get('hash_exclude_columns', set())
    scd_type = job_config.get('scd_type', 1)
    chunk_size = parallel_config.get('chunk_size', 50000)
    max_workers = parallel_config.get('max_workers')
    
    # Extract connection IDs for thread-safe parallel processing
    source_conn_id = job_config.get('source_conn_id')
    target_conn_id = job_config.get('target_conn_id')
    
    # Initialize counters
    total_source_rows = 0
    total_target_rows = 0
    total_error_rows = 0
    last_status = 'SUCCESS'
    
    try:
        # Calculate chunk configuration
        chunk_manager = ChunkManager(source_db_type)
        chunk_config = chunk_manager.calculate_chunk_config(
            source_conn, source_query, chunk_size
        )
        
        num_chunks = chunk_config.num_chunks or 1
        total_rows = chunk_config.total_rows or estimated_rows
        
        info(f"*** ENTERING PARALLEL PROCESSING MODE ***")
        info(f"Parallel processing configuration: {num_chunks} chunks, ~{total_rows} total rows, "
             f"chunk_size={chunk_size}, max_workers={max_workers}")
        
        # Edge case: If only 1 chunk, use sequential processing (parallel overhead not worth it)
        if num_chunks <= 1:
            info(f"Parallel processing disabled: Only {num_chunks} chunk(s), using sequential processing")
            # Fall back to sequential processing
            # This should not happen if row estimation is correct, but handle gracefully
            return {
                'status': 'SUCCESS',
                'source_rows': 0,
                'target_rows': 0,
                'error_rows': 0,
                'message': 'Parallel processing not needed (single chunk), use sequential processing'
            }
        
        # Check for stop request before starting
        if check_stop_request(metadata_conn, mapref):
            return {
                'status': 'STOPPED',
                'source_rows': 0,
                'target_rows': 0,
                'error_rows': 0,
                'message': 'Job stopped before parallel processing started'
            }
        
        # Create retry handler
        retry_handler = create_retry_handler(max_retries=3)
        
        # Create progress tracker
        progress_tracker = ProgressTracker(
            total_chunks=num_chunks,
            callback=create_progress_callback(f"Parallel Processing - {mapref}"),
            update_interval=2.0
        )
        
        # Process chunks in parallel
        chunk_results = []
        
        info(f"Starting parallel execution with ThreadPoolExecutor (max_workers={max_workers})")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            info(f"Submitting {num_chunks} chunks for parallel processing...")
            submitted_count = 0
            # Submit all chunks first (don't check stop request in loop to avoid blocking)
            try:
                stop_requested = check_stop_request(metadata_conn, mapref)
                if stop_requested:
                    info(f"Stop request detected before submitting chunks, aborting parallel processing")
                    return {
                        'status': 'STOPPED',
                        'source_rows': 0,
                        'target_rows': 0,
                        'error_rows': 0,
                        'message': 'Job stopped before chunks were submitted'
                    }
            except Exception as check_err:
                warning(f"Could not check stop request before submission: {check_err}")
            
            # Submit all chunks in batch
            info(f"Starting chunk submission loop for {num_chunks} chunks...")
            info(f"About to iterate through range({num_chunks})...")
            for chunk_id in range(num_chunks):
                try:
                    # Submit chunk processing (non-blocking)
                    if chunk_id == 0 or chunk_id % 10 == 0 or chunk_id == num_chunks - 1:
                        debug(f"Submitting chunk {chunk_id}...")
                    
                    # Create the future - this should be non-blocking
                    future = executor.submit(
                        _process_mapper_chunk,
                        chunk_id=chunk_id,
                        source_conn=source_conn,
                        source_query=source_query,
                        query_bind_params=query_bind_params,
                        chunk_size=chunk_size,
                        key_column=chunk_config.key_column,
                        source_columns=source_columns,
                        transformation_func=transformation_func,
                        target_conn=target_conn,
                        target_schema=target_schema,
                        target_table=target_table,
                        full_table_name=full_table_name,
                        pk_columns=pk_columns,
                        pk_source_mapping=pk_source_mapping,
                        all_columns=all_columns,
                        hash_exclude_columns=hash_exclude_columns,
                        scd_type=scd_type,
                        target_type=target_type,
                        source_db_type=source_db_type,
                        target_db_type=target_db_type,
                        metadata_conn=metadata_conn,
                        mapref=mapref,
                        checkpoint_columns=checkpoint_config.get('columns', []) if checkpoint_config.get('enabled') and checkpoint_config.get('strategy') == 'KEY' else None,
                        retry_handler=retry_handler,
                        source_conn_id=source_conn_id,
                        target_conn_id=target_conn_id
                    )
                    # Store the future immediately after submission
                    futures[future] = chunk_id
                    
                    # Update progress tracker (non-blocking, wrapped in try/except)
                    # Note: This was causing a deadlock with threading.Lock() because
                    # update_chunk_started() calls _maybe_trigger_callback() which calls
                    # get_snapshot(), both trying to acquire the same lock.
                    # Fixed by using threading.RLock() in parallel_progress.py
                    try:
                        progress_tracker.update_chunk_started(chunk_id)
                    except Exception as progress_err:
                        warning(f"Could not update progress tracker for chunk {chunk_id}: {progress_err}")
                    
                    # Increment counter and log progress
                    submitted_count += 1
                    if submitted_count % 10 == 0 or chunk_id == num_chunks - 1:
                        debug(f"Submitted {submitted_count}/{num_chunks} chunks so far...")
                        
                except Exception as submit_err:
                    error(f"Failed to submit chunk {chunk_id}: {submit_err}", exc_info=True)
                    # Continue with other chunks even if one fails to submit
                    # The continue statement is correct - it skips to the next iteration
                    continue
            
            # Log completion - this should always execute if the loop completes
            info(f"Chunk submission loop completed. Loop executed {num_chunks} iterations. Successfully submitted {len(futures)}/{num_chunks} chunks.")
            
            if len(futures) == 0:
                error(f"CRITICAL: No chunks were submitted! Expected {num_chunks} chunks.")
                return {
                    'status': 'FAILED',
                    'source_rows': 0,
                    'target_rows': 0,
                    'error_rows': 0,
                    'message': f'No chunks were submitted (expected {num_chunks})'
                }
            
            if len(futures) < num_chunks:
                warning(f"Only {len(futures)}/{num_chunks} chunks were submitted. Some chunks may have failed to submit.")
            
            info(f"Waiting for {len(futures)} chunks to complete...")
            completed_count = 0
            for future in as_completed(futures):
                chunk_id = futures[future]
                completed_count += 1
                info(f"Chunk {chunk_id} completed ({completed_count}/{len(futures)})")
                
                # Check for stop request
                if check_stop_request(metadata_conn, mapref):
                    info(f"Stop request detected, waiting for chunks to complete...")
                    # Cancel remaining futures if possible
                    for f in futures:
                        if f != future and not f.done():
                            f.cancel()
                    last_status = 'STOPPED'
                    break
                
                try:
                    # Get result with timeout to prevent indefinite hanging
                    # Timeout is chunk_size * 0.1 seconds per row (reasonable for most cases)
                    timeout_seconds = max(300, chunk_size * 0.1)  # At least 5 minutes, or 0.1s per row
                    info(f"Getting result for chunk {chunk_id} (timeout: {timeout_seconds}s)...")
                    chunk_result = future.result(timeout=timeout_seconds)
                    info(f"Got result for chunk {chunk_id}: status={chunk_result.get('status')}, source_rows={chunk_result.get('source_rows', 0)}, target_rows={chunk_result.get('target_rows', 0)}")
                    chunk_results.append(chunk_result)
                    
                    # Aggregate results
                    total_source_rows += chunk_result.get('source_rows', 0)
                    total_target_rows += chunk_result.get('target_rows', 0)
                    total_error_rows += chunk_result.get('error_rows', 0)
                    
                    # Log chunk completion
                    if chunk_result.get('status') == 'ERROR':
                        info(f"Chunk {chunk_id} completed with ERROR: {chunk_result.get('error_message', 'Unknown error')}")
                        progress_tracker.update_chunk_failed(chunk_id, chunk_result.get('error_message', 'Unknown error'))
                        last_status = 'FAILED'
                    else:
                        info(f"Chunk {chunk_id} completed: {chunk_result.get('source_rows', 0)} source rows, "
                             f"{chunk_result.get('target_rows', 0)} target rows, "
                             f"{chunk_result.get('error_rows', 0)} error rows")
                        progress_tracker.update_chunk_completed(
                            chunk_id,
                            chunk_result.get('source_rows', 0),
                            chunk_result.get('target_rows', 0),
                            chunk_result.get('error_rows', 0)
                        )
                    
                    # Update progress log periodically (less frequently to reduce lock contention)
                    if len(chunk_results) % 10 == 0 or len(chunk_results) == num_chunks:
                        try:
                            update_process_log_progress(metadata_conn, session_params, total_source_rows, total_target_rows)
                            metadata_conn.commit()
                            info(f"Parallel processing progress: {len(chunk_results)}/{num_chunks} chunks completed, "
                                 f"{total_source_rows} source rows, {total_target_rows} target rows processed so far")
                        except Exception as progress_err:
                            warning(f"Could not update progress log (non-fatal): {progress_err}")
                    
                except TimeoutError:
                    error(f"Chunk {chunk_id} timed out after {timeout_seconds} seconds")
                    total_error_rows += chunk_size
                    progress_tracker.update_chunk_failed(chunk_id, f"Timeout after {timeout_seconds} seconds")
                    last_status = 'FAILED'
                    # Cancel the future if possible
                    try:
                        future.cancel()
                    except Exception:
                        pass
                except Exception as e:
                    error(f"Chunk {chunk_id} failed with exception: {e}", exc_info=True)
                    total_error_rows += chunk_size  # Estimate error rows
                    progress_tracker.update_chunk_failed(chunk_id, str(e))
                    last_status = 'FAILED'
        
        # Final progress update
        update_process_log_progress(metadata_conn, session_params, total_source_rows, total_target_rows)
        
        # Handle checkpoint updates (KEY strategy)
        if checkpoint_config.get('enabled', False) and \
           checkpoint_config.get('strategy') == 'KEY' and \
           chunk_results:
            # Get maximum checkpoint value from all successful chunks
            # (not just the last one, as chunks may complete out of order)
            max_checkpoint_value = None
            checkpoint_columns = checkpoint_config.get('columns', [])
            
            for chunk_result in chunk_results:
                if chunk_result.get('status') != 'ERROR' and chunk_result.get('checkpoint_value'):
                    chunk_checkpoint = chunk_result.get('checkpoint_value')
                    
                    # Compare checkpoint values to find maximum
                    if max_checkpoint_value is None:
                        max_checkpoint_value = chunk_checkpoint
                    else:
                        # For single column, compare directly
                        if len(checkpoint_columns) == 1:
                            try:
                                # Try numeric comparison first
                                max_val = float(max_checkpoint_value) if max_checkpoint_value else 0
                                chunk_val = float(chunk_checkpoint) if chunk_checkpoint else 0
                                if chunk_val > max_val:
                                    max_checkpoint_value = chunk_checkpoint
                            except (ValueError, TypeError):
                                # Fallback to string comparison
                                if chunk_checkpoint > max_checkpoint_value:
                                    max_checkpoint_value = chunk_checkpoint
                        else:
                            # For composite keys, compare first column (assumed to be sequential)
                            max_parts = max_checkpoint_value.split('|')
                            chunk_parts = chunk_checkpoint.split('|')
                            if len(max_parts) > 0 and len(chunk_parts) > 0:
                                try:
                                    max_val = float(max_parts[0]) if max_parts[0] else 0
                                    chunk_val = float(chunk_parts[0]) if chunk_parts[0] else 0
                                    if chunk_val > max_val:
                                        max_checkpoint_value = chunk_checkpoint
                                except (ValueError, TypeError):
                                    if chunk_parts[0] > max_parts[0]:
                                        max_checkpoint_value = chunk_checkpoint
            
            if max_checkpoint_value:
                update_checkpoint(metadata_conn, session_params, max_checkpoint_value)
                metadata_conn.commit()
                debug(f"Checkpoint updated to maximum value: {max_checkpoint_value}")
        
        # Mark checkpoint as completed
        if checkpoint_config.get('enabled', False) and last_status != 'STOPPED':
            complete_checkpoint(metadata_conn, session_params)
            metadata_conn.commit()
        
        # Final commit
        target_conn.commit()
        metadata_conn.commit()
        
        info(f"*** PARALLEL PROCESSING COMPLETED ***: {num_chunks} chunks processed, "
             f"{total_source_rows} source rows, {total_target_rows} target rows, {total_error_rows} errors")
        
        return {
            'status': last_status,
            'source_rows': total_source_rows,
            'target_rows': total_target_rows,
            'error_rows': total_error_rows,
            'message': f'Parallel processing completed: {num_chunks} chunks processed'
        }
        
    except Exception as e:
        error(f"Parallel processing failed: {e}", exc_info=True)
        try:
            target_conn.rollback()
            metadata_conn.rollback()
        except Exception:
            pass
        
        return {
            'status': 'FAILED',
            'source_rows': total_source_rows,
            'target_rows': total_target_rows,
            'error_rows': total_error_rows,
            'message': f'Parallel processing failed: {str(e)}'
        }


def _process_mapper_chunk(
    chunk_id: int,
    source_conn,
    source_query: str,
    query_bind_params: Optional[Dict[str, Any]],
    chunk_size: int,
    key_column: Optional[str],
    source_columns: List[str],
    transformation_func: Callable,
    target_conn,
    target_schema: str,
    target_table: str,
    full_table_name: str,
    pk_columns: set,
    pk_source_mapping: Dict[str, str],
    all_columns: List[str],
    hash_exclude_columns: set,
    scd_type: int,
    target_type: str,
    source_db_type: str,
    target_db_type: str,
    metadata_conn,
    mapref: str,
    checkpoint_columns: Optional[List[str]] = None,
    retry_handler = None,
    source_conn_id: Optional[int] = None,
    target_conn_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process a single chunk with full mapper logic (SCD, checkpoints, etc.).
    
    This is called by parallel workers to process individual chunks.
    Each worker creates its own database connections to avoid thread-safety issues.
    """
    from backend.modules.mapper.chunk_manager import ChunkManager
    
    debug(f"[PARALLEL] Starting chunk {chunk_id} processing (chunk_size={chunk_size})")
    
    chunk_result = {
        'chunk_id': chunk_id,
        'source_rows': 0,
        'target_rows': 0,
        'error_rows': 0,
        'status': 'SUCCESS',
        'checkpoint_value': None
    }
    
    # Create separate connections for this thread to avoid thread-safety issues
    chunk_source_conn = None
    chunk_target_conn = None
    source_cursor = None
    target_cursor = None
    
    try:
        # Note: Stop request checking is handled by the main thread
        # Chunk workers should not check stop requests to avoid database lock contention
        
        # Create new connections for this chunk worker thread
        # This avoids thread-safety issues with shared connections
        try:
            if source_conn_id:
                from backend.database.dbconnect import create_target_connection
                chunk_source_conn = create_target_connection(source_conn_id)
                debug(f"[PARALLEL] Chunk {chunk_id}: Created source connection (ID: {source_conn_id})")
            else:
                # Fallback to using the provided connection (not ideal but works)
                chunk_source_conn = source_conn
                warning(f"[PARALLEL] Chunk {chunk_id}: Using shared source connection (not thread-safe)")
            
            if target_conn_id:
                from backend.database.dbconnect import create_target_connection
                chunk_target_conn = create_target_connection(target_conn_id)
                debug(f"[PARALLEL] Chunk {chunk_id}: Created target connection (ID: {target_conn_id})")
            else:
                # Fallback to using the provided connection (not ideal but works)
                chunk_target_conn = target_conn
                warning(f"[PARALLEL] Chunk {chunk_id}: Using shared target connection (not thread-safe)")
        except Exception as conn_err:
            error(f"[PARALLEL] Chunk {chunk_id}: Failed to create connections: {conn_err}", exc_info=True)
            chunk_result['status'] = 'ERROR'
            chunk_result['error_message'] = f"Connection creation failed: {str(conn_err)}"
            return chunk_result
        
        # Create chunked query
        chunk_manager = ChunkManager(source_db_type)
        chunk_sql = chunk_manager.create_chunked_query(
            source_query, chunk_id, chunk_size, key_column
        )
        
        # Execute chunk query
        source_cursor = chunk_source_conn.cursor()
        if query_bind_params:
            source_cursor.execute(chunk_sql, query_bind_params)
        else:
            source_cursor.execute(chunk_sql)
        
        # Fetch all rows for this chunk
        source_rows = source_cursor.fetchall()
        
        if not source_rows:
            return chunk_result
        
        chunk_result['source_rows'] = len(source_rows)
        
        # Get target cursor
        target_cursor = chunk_target_conn.cursor()
        
        # Prepare batch data
        rows_to_insert = []
        rows_to_update_scd1 = []
        rows_to_update_scd2 = []
        last_checkpoint_value = None
        
        # Process each row in chunk
        for src_row in source_rows:
            try:
                # Convert row to dictionary
                raw_src_dict = dict(zip(source_columns, src_row))
                
                # Apply transformation
                src_dict = transformation_func(raw_src_dict)
                
                # Build primary key
                pk_values = build_primary_key_values(
                    raw_src_dict,
                    pk_columns,
                    pk_source_mapping
                )
                
                # Check for NULL PK
                if any(v is None for v in pk_values.values()):
                    chunk_result['error_rows'] += 1
                    continue
                
                # Lookup existing record
                target_row = _lookup_target_record(
                    target_cursor,
                    full_table_name,
                    pk_values,
                    target_db_type,
                    target_schema,
                    target_table
                )
                
                # Generate hash
                src_hash = generate_hash(src_dict, all_columns, hash_exclude_columns)
                
                # Prepare for SCD processing
                row_to_insert, row_to_update_scd1, skey_to_expire_scd2 = prepare_row_for_scd(
                    src_dict,
                    target_row,
                    src_hash,
                    scd_type,
                    target_type
                )
                
                if row_to_insert:
                    rows_to_insert.append(row_to_insert)
                if row_to_update_scd1:
                    rows_to_update_scd1.append(row_to_update_scd1)
                if skey_to_expire_scd2:
                    rows_to_update_scd2.append(skey_to_expire_scd2)
                
                # Track checkpoint value (for KEY strategy)
                # Extract checkpoint value from checkpoint columns
                if checkpoint_columns:
                    if len(checkpoint_columns) > 1:
                        # Composite key
                        checkpoint_values_list = [
                            str(raw_src_dict.get(col, '')) for col in checkpoint_columns
                        ]
                        last_checkpoint_value = '|'.join(checkpoint_values_list)
                    else:
                        # Single column
                        last_checkpoint_value = str(raw_src_dict.get(checkpoint_columns[0], ''))
                
            except Exception as row_err:
                error(f"[Chunk {chunk_id}] Error processing row: {row_err}")
                chunk_result['error_rows'] += 1
                continue
        
        # Process SCD batch with retry logic
        def process_scd_batch_with_retry():
            return process_scd_batch(
                chunk_target_conn,
                target_schema,
                target_table,
                full_table_name,
                rows_to_insert,
                rows_to_update_scd1,
                rows_to_update_scd2,
                all_columns,
                scd_type,
                target_type,
                target_db_type
            )
        
        try:
            if retry_handler:
                result = retry_handler.execute_with_retry(
                    process_scd_batch_with_retry,
                    f"[Chunk {chunk_id}] SCD batch processing"
                )
                inserted, updated, expired = result
            else:
                inserted, updated, expired = process_scd_batch_with_retry()
            
            chunk_result['target_rows'] = inserted + updated
            
        except Exception as scd_err:
            error(f"[Chunk {chunk_id}] Error processing SCD batch: {scd_err}")
            chunk_result['error_rows'] += len(rows_to_insert) + len(rows_to_update_scd1)
            chunk_result['status'] = 'ERROR'
            chunk_result['error_message'] = str(scd_err)
        
        # Commit target connection for this chunk
        chunk_target_conn.commit()
        
        # Store checkpoint value if available
        if last_checkpoint_value:
            chunk_result['checkpoint_value'] = last_checkpoint_value
        
    except Exception as e:
        error(f"[Chunk {chunk_id}] Processing failed: {e}", exc_info=True)
        chunk_result['status'] = 'ERROR'
        chunk_result['error_message'] = str(e)
        chunk_result['error_rows'] = chunk_result.get('source_rows', 0)
        try:
            if chunk_target_conn:
                chunk_target_conn.rollback()
        except Exception:
            pass
    finally:
        # Clean up cursors and connections
        try:
            if source_cursor:
                source_cursor.close()
            if target_cursor:
                target_cursor.close()
        except Exception:
            pass
        
        # Close chunk-specific connections (if we created new ones)
        try:
            if chunk_source_conn and chunk_source_conn is not source_conn:
                chunk_source_conn.close()
                debug(f"[PARALLEL] Chunk {chunk_id}: Closed source connection")
        except Exception:
            pass
        
        try:
            if chunk_target_conn and chunk_target_conn is not target_conn:
                chunk_target_conn.close()
                debug(f"[PARALLEL] Chunk {chunk_id}: Closed target connection")
        except Exception:
            pass
    
    return chunk_result


def _validate_connections(metadata_conn, source_conn, target_conn) -> None:
    """Validate all connections."""
    if not metadata_conn:
        raise RuntimeError("metadata_connection is None or invalid")
    if not source_conn:
        raise RuntimeError("source_connection is None or invalid")
    if not target_conn:
        raise RuntimeError("target_connection is None or invalid")
    debug("All connections validated successfully")


def _verify_target_table(cursor, full_table_name: str, schema: str, table: str, db_type: str) -> None:
    """Verify target table exists and is accessible."""
    try:
        from backend.modules.mapper.database_sql_adapter import create_adapter_from_type
        adapter = create_adapter_from_type(db_type)
        limit_clause = adapter.get_limit_clause(1)
        
        # Format table name using adapter (important for MySQL which doesn't use schema prefix)
        formatted_table = adapter.format_table_name(schema, table)
        
        # Build query with database-agnostic LIMIT/ROWNUM
        if "LIMIT" in limit_clause or "FETCH" in limit_clause:
            # PostgreSQL, MySQL, SQL Server 2012+, etc.
            query = f"SELECT COUNT(*) FROM {formatted_table} {limit_clause}"
        else:
            # Oracle ROWNUM (embedded in WHERE)
            query = f"SELECT COUNT(*) FROM {formatted_table} {limit_clause}"
        
        debug(f"Verifying table accessibility with query: {query}")
        cursor.execute(query)
        cursor.fetchone()
        try:
            cursor.fetchall()
        except Exception:
            pass
        debug(f"Table {formatted_table} is accessible")
    except Exception as e:
        error_msg = f"Table {full_table_name} is not accessible: {str(e)}"
        error(error_msg)
        raise RuntimeError(error_msg) from e


def _lookup_target_record(cursor, full_table_name: str, pk_values: Dict[str, Any], db_type: str, schema: str = None, table: str = None) -> Optional[Dict[str, Any]]:
    """Lookup existing record in target table by primary key."""
    try:
        from backend.modules.mapper.database_sql_adapter import create_adapter_from_type
        adapter = create_adapter_from_type(db_type)
        
        # Format table name using adapter (important for MySQL which doesn't use schema prefix)
        if schema and table:
            formatted_table = adapter.format_table_name(schema, table)
        else:
            # Fallback to full_table_name if schema/table not provided
            formatted_table = full_table_name
        
        pk_where = build_primary_key_where_clause(set(pk_values.keys()), db_type)
        
        db_type_upper = (db_type or "").upper()
        if db_type_upper == "MYSQL":
            query = f"""
                SELECT * FROM {formatted_table}
                WHERE CURFLG = 'Y' AND {pk_where}
                LIMIT 1
            """
        else:
            query = f"""
                SELECT * FROM {formatted_table}
                WHERE CURFLG = 'Y' AND {pk_where}
            """
        
        # Format parameters for database
        params = adapter.format_parameters(pk_values, use_named=True)
        cursor.execute(query, params)
        
        target_row = cursor.fetchone()

        if db_type_upper == "MYSQL":
            try:
                cursor.fetchall()
            except Exception:
                pass

        if target_row:
            target_columns = [desc[0] for desc in cursor.description]
            return dict(zip(target_columns, target_row))
        return None
    except Exception as e:
        warning(f"Error looking up target record: {e}")
        return None

