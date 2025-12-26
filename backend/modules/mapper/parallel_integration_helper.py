"""
Integration helper for parallel processing in mapper execution engine.
This module provides utilities to integrate parallel processing into the
existing execution flow with minimal changes.
"""
import os
from typing import Dict, Any, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.parallel_processor import ParallelProcessor
    from backend.modules.mapper.parallel_models import ParallelProcessingResult
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.parallel_processor import ParallelProcessor  # type: ignore
    from modules.mapper.parallel_models import ParallelProcessingResult  # type: ignore
    from modules.logger import info, warning, error, debug  # type: ignore


def get_parallel_config_from_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract parallel processing configuration from execution parameters.
    
    Args:
        params: Execution parameters dictionary
        
    Returns:
        Dictionary with parallel processing configuration:
        {
            'enable_parallel': bool,
            'max_workers': Optional[int],
            'chunk_size': int,
            'min_rows_for_parallel': int
        }
    """
    # Check params first, then environment variables, then defaults
    enable_parallel = params.get('enable_parallel')
    if enable_parallel is None:
        enable_parallel = os.getenv('MAPPER_PARALLEL_ENABLED', 'true').lower() == 'true'
    elif isinstance(enable_parallel, str):
        enable_parallel = enable_parallel.upper() in ('Y', 'YES', 'TRUE', '1')
    else:
        enable_parallel = bool(enable_parallel)
    
    max_workers = params.get('max_workers')
    if max_workers is None:
        max_workers_str = os.getenv('MAPPER_MAX_WORKERS')
        max_workers = int(max_workers_str) if max_workers_str else None
    else:
        max_workers = int(max_workers) if max_workers else None
    
    chunk_size = params.get('chunk_size') or params.get('chunk_size')
    if chunk_size is None:
        chunk_size = int(os.getenv('MAPPER_CHUNK_SIZE', '50000'))
    else:
        chunk_size = int(chunk_size)
    
    min_rows_for_parallel = params.get('min_rows_for_parallel')
    if min_rows_for_parallel is None:
        min_rows_for_parallel = int(os.getenv('MAPPER_MIN_ROWS_FOR_PARALLEL', '100000'))
    else:
        min_rows_for_parallel = int(min_rows_for_parallel)
    
    return {
        'enable_parallel': enable_parallel,
        'max_workers': max_workers,
        'chunk_size': chunk_size,
        'min_rows_for_parallel': min_rows_for_parallel
    }


def should_use_parallel_processing(
    estimated_rows: int,
    config: Dict[str, Any]
) -> bool:
    """
    Determine if parallel processing should be used based on estimated rows and configuration.
    
    Args:
        estimated_rows: Estimated number of rows to process
        config: Parallel processing configuration
        
    Returns:
        True if parallel processing should be used
    """
    if not config['enable_parallel']:
        return False
    
    if estimated_rows < config['min_rows_for_parallel']:
        debug(f"Parallel processing disabled: estimated rows ({estimated_rows}) "
              f"below threshold ({config['min_rows_for_parallel']})")
        return False
    
    return True


def create_parallel_processor(config: Dict[str, Any]) -> ParallelProcessor:
    """
    Create a ParallelProcessor instance from configuration.
    
    Args:
        config: Parallel processing configuration dictionary
        
    Returns:
        Configured ParallelProcessor instance
    """
    return ParallelProcessor(
        max_workers=config['max_workers'],
        chunk_size=config['chunk_size'],
        enable_parallel=config['enable_parallel']
    )

