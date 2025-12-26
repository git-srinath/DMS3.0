# User Guide: Parallel Processing for Mapper Module

## Overview

The parallel processing feature allows you to process large datasets more efficiently by splitting data into chunks and processing them concurrently. This guide explains how to use parallel processing in your mapper jobs.

## When to Use Parallel Processing

Parallel processing is beneficial when:
- ✅ Processing large datasets (100K+ rows)
- ✅ Source and target databases can handle concurrent connections
- ✅ Data can be split into independent chunks
- ✅ Network bandwidth allows parallel data transfer

Parallel processing is NOT recommended when:
- ❌ Small datasets (<100K rows) - overhead outweighs benefits
- ❌ Database connection limits are strict
- ❌ Source query has dependencies between rows
- ❌ Memory is limited (each chunk uses memory)

## Quick Start

### Option 1: Using the Utility Function (Recommended)

The easiest way to use parallel processing is through the `execute_query_parallel` function:

```python
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    # Your source SQL query
    source_sql = """
        SELECT * FROM large_source_table 
        WHERE load_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY id
    """
    
    # Execute in parallel
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema="target_schema",
        target_table="target_table"
    )
    
    # Check results
    print(f"Processed {result.total_rows_processed:,} rows")
    print(f"Successful: {result.total_rows_successful:,}")
    print(f"Failed: {result.total_rows_failed:,}")
    
    return {
        "status": "SUCCESS",
        "rows_processed": result.total_rows_processed
    }
```

### Option 2: Direct Usage (Advanced)

For more control, use `ParallelProcessor` directly:

```python
from backend.modules.mapper import (
    ParallelProcessor,
    RetryHandler,
    RetryConfig,
    ProgressTracker,
    create_progress_callback
)

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    # Configure retry
    retry_handler = RetryHandler(RetryConfig(max_retries=3))
    
    # Configure progress tracking
    progress_tracker = ProgressTracker(
        total_chunks=10,  # Will be calculated automatically
        callback=create_progress_callback("My Job")
    )
    
    # Create processor
    processor = ParallelProcessor(
        max_workers=4,
        chunk_size=50000,
        retry_handler=retry_handler,
        progress_tracker=progress_tracker
    )
    
    # Execute
    result = processor.process_mapper_job(
        source_conn=source_conn,
        source_sql="SELECT * FROM large_table ORDER BY id",
        target_conn=target_conn,
        target_schema="target_schema",
        target_table="target_table"
    )
    
    return {"status": "SUCCESS", "rows": result.total_rows_processed}
```

## Configuration

### Environment Variables

Set these in your `.env` file or environment:

```env
# Enable/disable parallel processing (default: true)
MAPPER_PARALLEL_ENABLED=true

# Number of worker threads (default: CPU cores - 1)
MAPPER_MAX_WORKERS=4

# Rows per chunk (default: 50000)
MAPPER_CHUNK_SIZE=50000

# Minimum rows to enable parallel (default: 100000)
MAPPER_MIN_ROWS_FOR_PARALLEL=100000

# Retry configuration
MAPPER_PARALLEL_RETRY_ENABLED=true
MAPPER_PARALLEL_MAX_RETRIES=3

# Progress tracking
MAPPER_PARALLEL_PROGRESS_ENABLED=true
```

### Job Parameters

You can also configure parallel processing per job via execution parameters:

```python
params = {
    'enable_parallel': True,
    'max_workers': 4,
    'chunk_size': 50000,
    'min_rows_for_parallel': 100000,
    'enable_retry': True,
    'max_retries': 3,
    'enable_progress': True
}
```

## Configuration Guidelines

### Chunk Size

**Recommended values:**
- **Small datasets (100K-1M rows)**: 25,000-50,000 rows per chunk
- **Medium datasets (1M-10M rows)**: 50,000-100,000 rows per chunk
- **Large datasets (10M+ rows)**: 100,000-200,000 rows per chunk

**Considerations:**
- Smaller chunks = more parallelism, more overhead
- Larger chunks = less overhead, less parallelism
- Balance based on your database and network

### Worker Count

**Recommended values:**
- **CPU-bound workloads**: Number of CPU cores - 1
- **I/O-bound workloads**: 2-4x CPU cores
- **Database-bound**: Match to connection pool size

**Considerations:**
- More workers = better utilization, more connections needed
- Too many workers = connection exhaustion, context switching overhead

### Minimum Rows Threshold

**Recommended:** 100,000 rows

Parallel processing overhead makes it inefficient for small datasets. The system automatically disables parallel processing for datasets below this threshold.

## Data Transformation

You can apply transformations to each chunk:

```python
def transform_rows(rows):
    """Transform rows before loading"""
    transformed = []
    for row in rows:
        # Convert dict to modified dict
        new_row = dict(row)
        new_row['processed_date'] = datetime.now()
        new_row['status'] = 'PROCESSED'
        transformed.append(new_row)
    return transformed

result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM source_table",
    transformation_func=transform_rows,
    target_conn=target_conn,
    target_schema="target_schema",
    target_table="target_table"
)
```

**Important:**
- Transformation function receives a list of dictionaries
- Must return a list of dictionaries
- Applied to each chunk independently
- Should be thread-safe

## Error Handling

### Automatic Retry

Parallel processing includes automatic retry for transient errors:

- **Retried:** Connection errors, timeouts, transient database errors
- **Not retried:** Syntax errors, type errors, configuration errors

Configure retry behavior:

```python
result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM table",
    enable_retry=True,
    max_retries=3  # Retry up to 3 times
)
```

### Handling Failures

Check results for failures:

```python
result = execute_query_parallel(...)

if result.total_rows_failed > 0:
    print(f"Warning: {result.total_rows_failed:,} rows failed")
    print(f"Failed chunks: {result.chunks_failed}")
    
    # Check individual chunk errors
    for error in result.chunk_errors:
        print(f"Chunk {error['chunk_id']}: {error['error']}")

if result.chunks_failed > 0:
    print(f"Error: {result.chunks_failed} chunks failed completely")
```

## Progress Tracking

Monitor progress during execution:

```python
def progress_callback(snapshot):
    print(f"Progress: {snapshot.progress_percentage:.1f}%")
    print(f"Rows: {snapshot.total_rows_processed:,}")
    if snapshot.estimated_remaining_time:
        print(f"Estimated remaining: {snapshot.estimated_remaining_time:.1f}s")

result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM large_table",
    progress_callback=progress_callback
)
```

## Best Practices

### 1. Order Your Source Query

Always include `ORDER BY` in your source SQL when possible:

```sql
SELECT * FROM table ORDER BY id
```

This enables efficient key-based chunking.

### 2. Avoid Dependencies Between Rows

Parallel processing works best when chunks are independent:

- ✅ Good: Simple SELECT queries
- ❌ Bad: Queries with window functions that depend on previous rows
- ❌ Bad: Queries with self-joins that create dependencies

### 3. Monitor Connection Usage

Ensure your database can handle the number of connections:

```python
# If you have 4 workers, you need at least 4 connections
# (plus one for metadata, plus buffer)
# Total: ~6-8 connections per parallel job
```

### 4. Test with Smaller Datasets First

Before running on production data:
1. Test with a subset (use LIMIT in SQL)
2. Verify correct results
3. Monitor performance
4. Gradually increase dataset size

### 5. Check Database Compatibility

- **PostgreSQL:** Full support (OFFSET/LIMIT, key-based chunking)
- **Oracle:** Full support (ROWNUM, ROW_NUMBER)
- **Other databases:** Basic support (OFFSET/LIMIT)

## Troubleshooting

### Problem: Parallel processing not enabled

**Symptoms:** Processing runs sequentially despite large dataset

**Solutions:**
- Check `MAPPER_PARALLEL_ENABLED=true`
- Verify dataset size exceeds `MAPPER_MIN_ROWS_FOR_PARALLEL`
- Check logs for "Parallel processing disabled" messages

### Problem: Connection errors

**Symptoms:** Frequent connection timeouts or "too many connections" errors

**Solutions:**
- Reduce `max_workers` to match connection pool size
- Increase database connection limit
- Use connection pooling (Phase 2 feature)

### Problem: Memory errors

**Symptoms:** Out of memory errors during processing

**Solutions:**
- Reduce `chunk_size` to process smaller chunks
- Reduce `max_workers` to limit concurrent chunks
- Ensure sufficient available memory

### Problem: Slow performance

**Symptoms:** Parallel processing is slower than sequential

**Possible causes:**
- Dataset too small (below threshold)
- Too many workers causing contention
- Network bandwidth limitations
- Database unable to handle concurrent load

**Solutions:**
- Verify dataset size
- Reduce worker count
- Increase chunk size
- Check database performance

## Examples

### Example 1: Simple Parallel Load

```python
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql="SELECT * FROM orders WHERE order_date >= '2024-01-01' ORDER BY order_id",
        target_conn=target_conn,
        target_schema="dw",
        target_table="fact_orders"
    )
    
    return {
        "status": "SUCCESS" if result.total_rows_failed == 0 else "PARTIAL",
        "rows_processed": result.total_rows_processed,
        "rows_successful": result.total_rows_successful,
        "rows_failed": result.total_rows_failed
    }
```

### Example 2: With Transformation

```python
from datetime import datetime
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def transform_order_data(rows):
    """Add processing metadata to each row"""
    transformed = []
    process_time = datetime.now()
    
    for row in rows:
        new_row = dict(row)
        new_row['processed_at'] = process_time
        new_row['process_batch_id'] = session_params.get('batch_id')
        transformed.append(new_row)
    
    return transformed

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql="SELECT * FROM orders ORDER BY order_id",
        transformation_func=transform_order_data,
        target_conn=target_conn,
        target_schema="dw",
        target_table="fact_orders"
    )
    
    return {"status": "SUCCESS", "rows": result.total_rows_processed}
```

### Example 3: Custom Configuration

```python
from backend.modules.mapper import (
    execute_query_parallel,
    RetryHandler,
    RetryConfig
)

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    # Custom retry configuration for unreliable network
    retry_handler = RetryHandler(RetryConfig(
        max_retries=5,
        initial_delay=2.0,
        max_delay=120.0
    ))
    
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql="SELECT * FROM remote_table ORDER BY id",
        target_conn=target_conn,
        target_schema="target",
        target_table="table",
        max_workers=2,  # Conservative for unreliable network
        chunk_size=25000,  # Smaller chunks for network issues
        enable_retry=True,
        max_retries=5
    )
    
    return {"status": "SUCCESS", "rows": result.total_rows_processed}
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Consult the operations guide for advanced configuration
4. Contact your system administrator

