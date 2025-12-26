# Mapper Parallel Processing - Phase 2 Implementation

## Overview

Phase 2 integrates parallel processing capabilities with the existing mapper execution engine, adding configuration support and connection pooling infrastructure.

## Components Created/Modified

### 1. Connection Pool Manager (`parallel_connection_pool.py`)

Manages database connections for parallel worker threads:

- **Thread-local connections**: Each worker thread gets its own database connection
- **Connection factories**: Supports custom connection creation functions
- **Automatic cleanup**: Connections are closed when threads complete or on errors
- **Thread-safe**: Uses locks to manage connection dictionary

**Key Features:**
- `get_source_connection()`: Context manager for source database connections
- `get_target_connection()`: Context manager for target database connections
- `close_all_connections()`: Cleanup method for all connections

### 2. Parallel Query Executor Utility (`parallel_query_executor.py`)

Utility function that can be imported and used by generated mapper code:

- **Simple API**: Single function call for parallel query execution
- **Configuration**: Reads from environment variables or parameters
- **Flexible**: Can be used with or without transformation functions

**Usage Example:**
```python
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

result = execute_query_parallel(
    source_conn=source_connection,
    source_sql="SELECT * FROM large_table ORDER BY id",
    target_conn=target_connection,
    target_schema="target_schema",
    target_table="target_table"
)
```

### 3. Integration Helper (`parallel_integration_helper.py`)

Utilities for integrating parallel processing into execution engine:

- **Configuration extraction**: Reads parallel config from job parameters
- **Decision logic**: Determines when to use parallel processing
- **Factory functions**: Creates configured processor instances

**Functions:**
- `get_parallel_config_from_params()`: Extract config from execution params
- `should_use_parallel_processing()`: Determine if parallel should be used
- `create_parallel_processor()`: Create configured processor instance

## Configuration

### Environment Variables

Parallel processing can be configured via environment variables:

```env
# Enable/disable parallel processing (default: true)
MAPPER_PARALLEL_ENABLED=true

# Number of worker threads (default: auto-detect, CPU cores - 1)
MAPPER_MAX_WORKERS=4

# Rows per chunk (default: 50000)
MAPPER_CHUNK_SIZE=50000

# Minimum rows to enable parallel processing (default: 100000)
MAPPER_MIN_ROWS_FOR_PARALLEL=100000
```

### Job Parameters

Parallel processing can also be configured per-job via execution parameters:

```python
params = {
    'enable_parallel': True,  # or 'Y'/'N'
    'max_workers': 4,
    'chunk_size': 50000,
    'min_rows_for_parallel': 100000
}
```

### Configuration Priority

1. Job execution parameters (highest priority)
2. Environment variables
3. Default values (lowest priority)

## Integration Points

### Current Status

Phase 2 provides the infrastructure for parallel processing but does not yet automatically integrate it into the execution flow. This is intentional to allow:

1. **Testing**: Components can be tested independently
2. **Gradual adoption**: Code can be updated incrementally
3. **Backward compatibility**: Existing jobs continue to work unchanged

### How to Use

#### Option 1: Use in Generated Mapper Code

Generated mapper code can import and use the parallel query executor:

```python
# In generated mapper code (DWLOGIC)
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    source_sql = "SELECT * FROM large_source_table ORDER BY id"
    
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema="target_schema",
        target_table="target_table"
    )
    
    print(f"Processed {result.total_rows_processed} rows")
    return {"status": "SUCCESS", "rows_processed": result.total_rows_processed}
```

#### Option 2: Execution Engine Integration (Future)

The execution engine can be modified to automatically use parallel processing for large queries. This would require:

1. Detecting SQL queries in generated code
2. Estimating row counts
3. Optionally wrapping queries with parallel execution

This is planned for future phases.

## Connection Pooling

The `ConnectionPoolManager` provides thread-safe connection management:

- Each worker thread gets its own connection
- Connections are created on-demand
- Connections are automatically cleaned up
- Errors in one thread don't affect others

**Usage:**
```python
from backend.modules.mapper.parallel_connection_pool import ConnectionPoolManager

def source_conn_factory():
    return create_source_connection()

def target_conn_factory():
    return create_target_connection()

with ConnectionPoolManager(source_conn_factory, target_conn_factory) as pool:
    # Workers can use pool.get_source_connection() and pool.get_target_connection()
    pass
```

## Testing

### Unit Tests

Test files for Phase 2 components:
- `test_parallel_connection_pool.py` (to be created)
- `test_parallel_query_executor.py` (to be created)
- `test_parallel_integration_helper.py` (to be created)

### Integration Testing

Integration tests should verify:
1. Configuration reading from environment and parameters
2. Connection pool creation and cleanup
3. Parallel query executor functionality
4. Integration helper utilities

## Next Steps (Phase 3)

1. **Enhanced Error Handling**: Implement retry mechanisms and better error recovery
2. **Connection Pool Optimization**: Improve connection reuse and management
3. **Performance Optimization**: Fine-tune chunk sizes and worker counts
4. **Automatic Integration**: Integrate into execution engine automatically
5. **Progress Tracking**: Real-time progress updates during parallel processing

## Backward Compatibility

All Phase 2 components are **additive** - they don't modify existing functionality:

- ✅ Existing jobs continue to work unchanged
- ✅ No changes to existing execution flow
- ✅ Parallel processing is opt-in only
- ✅ Default behavior is unchanged

## Notes

- Connection pooling is implemented but not yet fully integrated into parallel processor (Phase 3)
- The parallel query executor can be used immediately in generated code
- Configuration is flexible and supports multiple sources
- All components are well-documented and testable

