"""
Parallel Query Executor utility for mapper generated code.
This utility can be imported and used by generated mapper code to execute
large SQL queries in parallel chunks.
"""
from typing import Dict, Any, Optional, Callable, List
import os

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.parallel_processor import ParallelProcessor
    from backend.modules.mapper.parallel_models import ParallelProcessingResult
    from backend.modules.mapper.parallel_retry_handler import RetryHandler, RetryConfig, create_retry_handler
    from backend.modules.mapper.parallel_progress import ProgressTracker, create_progress_callback
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.parallel_processor import ParallelProcessor  # type: ignore
    from modules.mapper.parallel_models import ParallelProcessingResult  # type: ignore
    from modules.mapper.parallel_retry_handler import RetryHandler, RetryConfig, create_retry_handler  # type: ignore
    from modules.mapper.parallel_progress import ProgressTracker, create_progress_callback  # type: ignore
    from modules.logger import info, warning, error, debug  # type: ignore


def execute_query_parallel(
    source_conn,
    source_sql: str,
    transformation_func: Optional[Callable] = None,
    target_conn = None,
    target_schema: Optional[str] = None,
    target_table: Optional[str] = None,
    source_schema: Optional[str] = None,
    enable_parallel: Optional[bool] = None,
    max_workers: Optional[int] = None,
    chunk_size: Optional[int] = None,
    min_rows_for_parallel: int = 100000,
    enable_retry: Optional[bool] = None,
    max_retries: Optional[int] = None,
    enable_progress: Optional[bool] = None,
    progress_callback: Optional[Callable] = None
) -> ParallelProcessingResult:
    """
    Execute a SQL query in parallel chunks.
    
    This is a utility function that can be called from generated mapper code
    to process large queries in parallel.
    
    Args:
        source_conn: Source database connection
        source_sql: SQL query to execute
        transformation_func: Optional function to transform each chunk's data
        target_conn: Optional target database connection for loading
        target_schema: Optional target schema name
        target_table: Optional target table name
        source_schema: Optional source schema name
        enable_parallel: Enable parallel processing (default: from env/config)
        max_workers: Number of worker threads (default: CPU cores - 1)
        chunk_size: Rows per chunk (default: 50000)
        min_rows_for_parallel: Minimum rows to enable parallel (default: 100000)
        enable_retry: Enable retry for failed chunks (default: True)
        max_retries: Maximum retry attempts (default: 3)
        enable_progress: Enable progress tracking (default: True)
        progress_callback: Optional callback function for progress updates
        
    Returns:
        ParallelProcessingResult with processing statistics
        
    Example usage in generated mapper code:
        from backend.modules.mapper.parallel_query_executor import execute_query_parallel
        
        result = execute_query_parallel(
            source_conn=source_connection,
            source_sql="SELECT * FROM large_table ORDER BY id",
            transformation_func=lambda rows: [transform_row(r) for r in rows],
            target_conn=target_connection,
            target_schema="target_schema",
            target_table="target_table"
        )
        
        print(f"Processed {result.total_rows_processed} rows")
        print(f"Successful: {result.total_rows_successful}, Failed: {result.total_rows_failed}")
    """
    # Get configuration from environment or use defaults
    if enable_parallel is None:
        enable_parallel = os.getenv('MAPPER_PARALLEL_ENABLED', 'true').lower() == 'true'
    
    if max_workers is None:
        max_workers_str = os.getenv('MAPPER_MAX_WORKERS')
        max_workers = int(max_workers_str) if max_workers_str else None
    
    if chunk_size is None:
        chunk_size = int(os.getenv('MAPPER_CHUNK_SIZE', '50000'))
    
    min_rows = int(os.getenv('MAPPER_MIN_ROWS_FOR_PARALLEL', str(min_rows_for_parallel)))
    
    # Setup retry handler if enabled
    retry_handler = None
    if enable_retry is None:
        enable_retry = os.getenv('MAPPER_PARALLEL_RETRY_ENABLED', 'true').lower() == 'true'
    
    if enable_retry:
        retry_max_retries = max_retries
        if retry_max_retries is None:
            retry_max_retries_str = os.getenv('MAPPER_PARALLEL_MAX_RETRIES')
            retry_max_retries = int(retry_max_retries_str) if retry_max_retries_str else None
        
        retry_handler = create_retry_handler(max_retries=retry_max_retries)
        debug("Retry handler enabled for parallel processing")
    
    # Setup progress tracker if enabled
    progress_tracker = None
    if enable_progress is None:
        enable_progress = os.getenv('MAPPER_PARALLEL_PROGRESS_ENABLED', 'true').lower() == 'true'
    
    if enable_progress:
        # Use provided callback or create default logging callback
        if progress_callback is None:
            progress_callback = create_progress_callback("Parallel Query Execution")
        
        # Progress tracker will be created by ParallelProcessor if needed
        # We'll pass it after we know the number of chunks
        debug("Progress tracking enabled for parallel processing")
    
    # Initialize processor
    processor = ParallelProcessor(
        max_workers=max_workers,
        chunk_size=chunk_size,
        enable_parallel=enable_parallel,
        retry_handler=retry_handler,
        progress_tracker=progress_tracker  # Will be created by processor if None and chunks > 1
    )
    
    # Execute parallel processing
    result = processor.process_mapper_job(
        source_conn=source_conn,
        source_sql=source_sql,
        transformation_logic=transformation_func,
        target_conn=target_conn,
        target_schema=target_schema,
        target_table=target_table,
        source_schema=source_schema,
        min_rows_for_parallel=min_rows
    )
    
    return result


def get_parallel_config() -> Dict[str, Any]:
    """
    Get parallel processing configuration from environment variables.
    
    Returns:
        Dictionary with configuration values
    """
    return {
        'enabled': os.getenv('MAPPER_PARALLEL_ENABLED', 'true').lower() == 'true',
        'max_workers': os.getenv('MAPPER_MAX_WORKERS'),
        'chunk_size': int(os.getenv('MAPPER_CHUNK_SIZE', '50000')),
        'min_rows_for_parallel': int(os.getenv('MAPPER_MIN_ROWS_FOR_PARALLEL', '100000'))
    }

