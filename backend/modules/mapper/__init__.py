"""
Mapper module with parallel processing support and job execution framework.
"""
from .parallel_processor import ParallelProcessor
from .chunk_manager import ChunkManager
from .chunk_processor import ChunkProcessor
from .parallel_connection_pool import ConnectionPoolManager
from .parallel_query_executor import execute_query_parallel, get_parallel_config
from .parallel_retry_handler import RetryHandler, RetryConfig, create_retry_handler
from .parallel_progress import ProgressTracker, ProgressSnapshot, create_progress_callback
from .parallel_models import (
    ChunkingStrategy,
    ChunkResult,
    ParallelProcessingResult,
    ChunkConfig
)

# Database adapter
from .database_sql_adapter import (
    DatabaseSQLAdapter,
    detect_database_type,
    create_adapter,
    create_adapter_from_type
)

# Job execution framework modules
from .mapper_job_executor import execute_mapper_job
from .mapper_transformation_utils import (
    map_row_to_target_columns,
    generate_hash,
    build_primary_key_values,
    build_primary_key_where_clause
)
from .mapper_progress_tracker import (
    check_stop_request,
    log_batch_progress,
    update_process_log_progress
)
from .mapper_checkpoint_handler import (
    parse_checkpoint_value,
    apply_checkpoint_to_query,
    update_checkpoint,
    complete_checkpoint
)
from .mapper_scd_handler import (
    process_scd_batch,
    prepare_row_for_scd
)

__all__ = [
    # Parallel processing
    'ParallelProcessor',
    'ChunkManager',
    'ChunkProcessor',
    'ConnectionPoolManager',
    'execute_query_parallel',
    'get_parallel_config',
    'RetryHandler',
    'RetryConfig',
    'create_retry_handler',
    'ProgressTracker',
    'ProgressSnapshot',
    'create_progress_callback',
    'ChunkingStrategy',
    'ChunkResult',
    'ParallelProcessingResult',
    'ChunkConfig',
    # Database adapter
    'DatabaseSQLAdapter',
    'detect_database_type',
    'create_adapter',
    'create_adapter_from_type',
    # Job execution framework
    'execute_mapper_job',
    'map_row_to_target_columns',
    'generate_hash',
    'build_primary_key_values',
    'build_primary_key_where_clause',
    'check_stop_request',
    'log_batch_progress',
    'update_process_log_progress',
    'parse_checkpoint_value',
    'apply_checkpoint_to_query',
    'update_checkpoint',
    'complete_checkpoint',
    'process_scd_batch',
    'prepare_row_for_scd',
]

