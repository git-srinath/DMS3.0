"""
Parallel Processor for mapper jobs.
Coordinates parallel processing of data chunks for improved performance.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, Callable

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.common.db_table_utils import _detect_db_type  # type: ignore
    from modules.logger import info, warning, error, debug  # type: ignore

from .parallel_models import ParallelProcessingResult, ChunkConfig
from .chunk_manager import ChunkManager
from .chunk_processor import ChunkProcessor
from .parallel_retry_handler import RetryHandler, RetryConfig, create_retry_handler
from .parallel_progress import ProgressTracker, create_progress_callback
from .parallel_connection_pool import ConnectionPoolManager


class ParallelProcessor:
    """Manages parallel processing of mapper jobs"""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: int = 50000,
        enable_parallel: bool = True,
        retry_handler: Optional[RetryHandler] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads (default: CPU cores - 1)
            chunk_size: Number of rows per chunk (default: 50000)
            enable_parallel: Enable parallel processing (default: True)
            retry_handler: Optional retry handler for failed chunks
            progress_tracker: Optional progress tracker for monitoring
        """
        self.max_workers = max_workers or max(1, (os.cpu_count() or 1) - 1)
        self.chunk_size = chunk_size
        self.enable_parallel = enable_parallel
        self.retry_handler = retry_handler
        self.progress_tracker = progress_tracker
    
    def process_mapper_job(
        self,
        source_conn,
        source_sql: str,
        transformation_logic: Optional[Callable] = None,
        target_conn = None,
        target_schema: Optional[str] = None,
        target_table: Optional[str] = None,
        source_schema: Optional[str] = None,
        min_rows_for_parallel: int = 100000,
        source_conn_factory: Optional[Callable] = None,
        target_conn_factory: Optional[Callable] = None
    ) -> ParallelProcessingResult:
        """
        Main entry point for parallel processing of mapper job.
        
        Args:
            source_conn: Source database connection (used if factories not provided)
            source_sql: Source SQL query
            transformation_logic: Optional transformation function
            target_conn: Optional target database connection (used if factories not provided)
            target_schema: Optional target schema name
            target_table: Optional target table name
            source_schema: Optional source schema name
            min_rows_for_parallel: Minimum rows to enable parallel processing
            source_conn_factory: Optional factory function to create source connections for workers
            target_conn_factory: Optional factory function to create target connections for workers
            
        Returns:
            ParallelProcessingResult with aggregated statistics
        """
        start_time = time.time()
        result = ParallelProcessingResult()
        
        # Detect database type
        db_type = _detect_db_type(source_conn)
        chunk_manager = ChunkManager(db_type)
        
        # Calculate chunk configuration
        debug("Calculating chunk configuration...")
        chunk_config = chunk_manager.calculate_chunk_config(
            source_conn, source_sql, self.chunk_size, source_schema
        )
        
        total_rows = chunk_config.total_rows or 0
        num_chunks = chunk_config.num_chunks or 1
        
        info(f"Estimated total rows: {total_rows}, Number of chunks: {num_chunks}")
        
        # Check if parallel processing should be enabled
        if not self.enable_parallel or total_rows < min_rows_for_parallel or num_chunks <= 1:
            info(f"Parallel processing disabled or not needed (rows: {total_rows}, chunks: {num_chunks})")
            # Fallback to sequential processing (caller should handle this)
            return self._process_sequential(
                source_conn, source_sql, transformation_logic,
                target_conn, target_schema, target_table, db_type
            )
        
        info(f"Starting parallel processing with {self.max_workers} workers, {num_chunks} chunks")
        
        # Process chunks in parallel
        chunk_processor = ChunkProcessor(db_type)
        
        # Initialize progress tracker if not provided
        progress_tracker = self.progress_tracker
        if progress_tracker is None and num_chunks > 1:
            progress_tracker = ProgressTracker(
                total_chunks=num_chunks,
                callback=create_progress_callback("Parallel Processing"),
                update_interval=2.0  # Update every 2 seconds
            )
        
        # Setup retry handler if not provided (use default)
        retry_handler = self.retry_handler
        
        # Setup connection pool if factories provided
        connection_pool = None
        if source_conn_factory and target_conn_factory:
            connection_pool = ConnectionPoolManager(
                source_conn_factory=source_conn_factory,
                target_conn_factory=target_conn_factory
            )
            info(f"Using connection pool for parallel processing ({self.max_workers} workers)")
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all chunk processing tasks
                futures = {}
                for chunk_id in range(num_chunks):
                    # Wrap chunk processing with retry logic if retry handler is configured
                    # Submit chunk processing task
                    # Retry is handled at chunk level (in ChunkProcessor), not here
                    future = executor.submit(
                        chunk_processor.process_chunk,
                        chunk_id=chunk_id,
                        source_conn=source_conn,
                        original_sql=source_sql,
                        chunk_size=self.chunk_size,
                        transformation_logic=transformation_logic,
                        target_conn=target_conn,
                        target_schema=target_schema,
                        target_table=target_table,
                        key_column=chunk_config.key_column,
                        retry_handler=retry_handler  # Pass retry handler to chunk processor
                    )
                    futures[future] = chunk_id
                    
                    # Update progress tracker
                    if progress_tracker:
                        progress_tracker.update_chunk_started(chunk_id)
                
                # Collect results as they complete
                chunk_results = [None] * num_chunks  # Pre-allocate list to maintain order
                
                for future in as_completed(futures):
                    chunk_id = futures[future]
                    try:
                        chunk_result = future.result()
                        chunk_results[chunk_id] = chunk_result
                        
                        # Update progress tracker
                        if progress_tracker:
                            if chunk_result.error:
                                progress_tracker.update_chunk_failed(chunk_id, chunk_result.error)
                            else:
                                progress_tracker.update_chunk_completed(
                                    chunk_id,
                                    chunk_result.rows_processed,
                                    chunk_result.rows_successful,
                                    chunk_result.rows_failed
                                )
                        
                        info(f"Chunk {chunk_id} completed: {chunk_result.rows_processed} rows, "
                             f"{chunk_result.rows_successful} successful, {chunk_result.rows_failed} failed")
                    except Exception as e:
                        error(f"Chunk {chunk_id} failed with exception: {e}", exc_info=True)
                        # Create error result
                        from .parallel_models import ChunkResult
                        chunk_results[chunk_id] = ChunkResult(
                            chunk_id=chunk_id,
                            error=str(e),
                            rows_failed=0
                        )
                        
                        # Update progress tracker
                        if progress_tracker:
                            progress_tracker.update_chunk_failed(chunk_id, str(e))
        finally:
            # Cleanup connection pool if used
            if connection_pool:
                connection_pool.close_all_connections()
                debug("Connection pool closed")
        
        # Aggregate results
        result = self._aggregate_results(chunk_results)
        result.processing_time = time.time() - start_time
        
        # Log final progress if tracker was used
        if progress_tracker:
            final_snapshot = progress_tracker.get_snapshot()
            info(f"Parallel processing complete: {result.total_rows_processed:,} rows processed "
                 f"({result.total_rows_successful:,} successful, {result.total_rows_failed:,} failed) "
                 f"in {result.processing_time:.2f}s. "
                 f"Chunks: {final_snapshot.completed_chunks}/{final_snapshot.total_chunks} completed, "
                 f"{final_snapshot.failed_chunks} failed")
        else:
            info(f"Parallel processing complete: {result.total_rows_processed:,} rows processed "
                 f"({result.total_rows_successful:,} successful, {result.total_rows_failed:,} failed) "
                 f"in {result.processing_time:.2f}s")
        
        return result
    
    def _aggregate_results(
        self,
        chunk_results: list
    ) -> ParallelProcessingResult:
        """
        Aggregate results from all chunks.
        
        Args:
            chunk_results: List of ChunkResult objects
            
        Returns:
            Aggregated ParallelProcessingResult
        """
        result = ParallelProcessingResult()
        result.chunks_total = len(chunk_results)
        
        for chunk_result in chunk_results:
            if chunk_result is None:
                continue
            
            result.chunk_results.append(chunk_result)
            
            if chunk_result.error:
                result.chunks_failed += 1
                result.chunk_errors.append({
                    'chunk_id': chunk_result.chunk_id,
                    'error': chunk_result.error,
                    'rows_in_chunk': chunk_result.rows_processed
                })
            else:
                result.chunks_succeeded += 1
            
            result.total_rows_processed += chunk_result.rows_processed
            result.total_rows_successful += chunk_result.rows_successful
            result.total_rows_failed += chunk_result.rows_failed
        
        return result
    
    def _process_sequential(
        self,
        source_conn,
        source_sql: str,
        transformation_logic: Optional[Callable] = None,
        target_conn = None,
        target_schema: Optional[str] = None,
        target_table: Optional[str] = None,
        db_type: str = "ORACLE"
    ) -> ParallelProcessingResult:
        """
        Process data sequentially (fallback when parallel is disabled).
        This is a placeholder - actual implementation should use existing sequential logic.
        
        Args:
            source_conn: Source database connection
            source_sql: Source SQL query
            transformation_logic: Optional transformation function
            target_conn: Optional target database connection
            target_schema: Optional target schema name
            target_table: Optional target table name
            db_type: Database type
            
        Returns:
            ParallelProcessingResult (will be converted from sequential result)
        """
        # This is a placeholder - the actual sequential processing
        # should be handled by the existing execution engine
        # This method is here for completeness but should rarely be called
        # as the caller should decide whether to use parallel or sequential
        
        warning("Sequential processing called from parallel processor - "
                "caller should use existing sequential logic instead")
        
        result = ParallelProcessingResult()
        result.chunks_total = 1
        result.chunks_succeeded = 0
        result.chunks_failed = 1
        result.error = "Sequential processing not implemented in parallel processor"
        
        return result

