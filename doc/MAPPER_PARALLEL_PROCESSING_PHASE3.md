# Mapper Parallel Processing - Phase 3 Implementation

## Overview

Phase 3 adds robust error handling and optimization features to the parallel processing implementation:
- **Retry Handler**: Automatic retry with exponential backoff for failed chunks
- **Progress Tracking**: Real-time progress monitoring with estimated completion time
- **Enhanced Error Handling**: Distinguishes retryable vs non-retryable errors

## Components

### 1. Retry Handler (`parallel_retry_handler.py`)

Handles retry logic for failed chunk processing with exponential backoff.

**Key Classes:**
- `RetryConfig`: Configuration for retry behavior
- `RetryHandler`: Handles retry logic and exponential backoff

**Features:**
- Exponential backoff with configurable base and delays
- Jitter support to prevent thundering herd
- Smart error detection (skips non-retryable errors like syntax errors)
- Configurable max retries and delay caps

**Usage:**
```python
from backend.modules.mapper import RetryHandler, RetryConfig

# Create retry handler with default config
retry_handler = RetryHandler()

# Or with custom config
config = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
)
retry_handler = RetryHandler(config)

# Use with parallel processor
processor = ParallelProcessor(
    max_workers=4,
    retry_handler=retry_handler
)
```

**Configuration Options:**
- `max_retries`: Maximum number of retry attempts (default: 3)
- `initial_delay`: Initial delay in seconds (default: 1.0)
- `max_delay`: Maximum delay cap in seconds (default: 60.0)
- `exponential_base`: Base for exponential backoff (default: 2.0)
- `jitter`: Add random jitter to delays (default: True)

### 2. Progress Tracker (`parallel_progress.py`)

Provides real-time progress tracking during parallel processing.

**Key Classes:**
- `ProgressSnapshot`: Snapshot of current progress state
- `ProgressTracker`: Tracks progress across all chunks

**Features:**
- Real-time progress percentage
- Row-level statistics (processed, successful, failed)
- Estimated remaining time calculation
- Thread-safe updates
- Optional callback for progress updates

**Usage:**
```python
from backend.modules.mapper import ProgressTracker, create_progress_callback

# Create progress tracker with logging callback
progress_tracker = ProgressTracker(
    total_chunks=10,
    callback=create_progress_callback("My Job"),
    update_interval=2.0  # Update every 2 seconds
)

# Or with custom callback
def my_callback(snapshot):
    print(f"Progress: {snapshot.progress_percentage:.1f}%")
    print(f"Rows: {snapshot.total_rows_processed:,}")

progress_tracker = ProgressTracker(
    total_chunks=10,
    callback=my_callback
)

# Use with parallel processor
processor = ParallelProcessor(
    max_workers=4,
    progress_tracker=progress_tracker
)
```

**Progress Snapshot Properties:**
- `total_chunks`: Total number of chunks
- `completed_chunks`: Number of completed chunks
- `failed_chunks`: Number of failed chunks
- `total_rows_processed`: Total rows processed
- `total_rows_successful`: Total rows successfully processed
- `total_rows_failed`: Total rows that failed
- `elapsed_time`: Time elapsed since start
- `estimated_remaining_time`: Estimated time to completion
- `progress_percentage`: Progress percentage (0-100)
- `chunks_in_progress`: Number of chunks currently processing

### 3. Integration with ParallelProcessor

Both retry handler and progress tracker are integrated into `ParallelProcessor`:

```python
from backend.modules.mapper import (
    ParallelProcessor,
    RetryHandler,
    RetryConfig,
    ProgressTracker,
    create_progress_callback
)

# Create retry handler
retry_handler = RetryHandler(RetryConfig(max_retries=3))

# Create progress tracker
progress_tracker = ProgressTracker(
    total_chunks=10,  # Will be set automatically by processor
    callback=create_progress_callback("Parallel Job")
)

# Create processor with retry and progress
processor = ParallelProcessor(
    max_workers=4,
    chunk_size=50000,
    retry_handler=retry_handler,
    progress_tracker=progress_tracker  # Optional, will be created if None
)
```

### 4. Enhanced Query Executor

The `parallel_query_executor.py` utility function now supports retry and progress options:

```python
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

# With retry and progress enabled (default)
result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM large_table",
    target_conn=target_conn,
    target_schema="schema",
    target_table="table",
    enable_retry=True,      # Enable retry (default: True)
    max_retries=3,          # Max retries (default: 3)
    enable_progress=True    # Enable progress (default: True)
)

# With custom progress callback
def my_progress(snapshot):
    print(f"Progress: {snapshot.progress_percentage:.1f}%")

result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM large_table",
    progress_callback=my_progress
)
```

## Configuration

### Environment Variables

```env
# Retry configuration
MAPPER_PARALLEL_RETRY_ENABLED=true
MAPPER_PARALLEL_MAX_RETRIES=3

# Progress configuration
MAPPER_PARALLEL_PROGRESS_ENABLED=true
```

### Programmatic Configuration

```python
# Retry configuration
retry_config = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=120.0
)
retry_handler = RetryHandler(retry_config)

# Progress configuration
progress_tracker = ProgressTracker(
    total_chunks=10,
    callback=my_callback,
    update_interval=1.0
)
```

## Retry Behavior

### Retryable Errors

The retry handler automatically retries on:
- Connection errors
- Timeout errors
- Transient database errors
- Network errors

### Non-Retryable Errors

The retry handler does NOT retry on:
- Syntax errors
- Value errors
- Type errors
- Attribute errors
- Configuration errors

These errors are logged and the chunk fails immediately.

### Exponential Backoff

Retry delays follow exponential backoff:
- Attempt 1: `initial_delay * (base^0)` = `initial_delay`
- Attempt 2: `initial_delay * (base^1)` = `initial_delay * base`
- Attempt 3: `initial_delay * (base^2)` = `initial_delay * base^2`
- ...

Delays are capped at `max_delay` and include optional jitter to prevent synchronized retries.

**Example:**
- `initial_delay=1.0`, `base=2.0`, `max_delay=60.0`
- Retry delays: 1s, 2s, 4s, 8s, 16s, 32s, 60s (capped), 60s, ...

## Progress Tracking

### Progress Updates

Progress updates are provided via:
1. **Callback function**: Called periodically with `ProgressSnapshot`
2. **Log messages**: Automatic logging if using `create_progress_callback()`
3. **Direct access**: Call `tracker.get_snapshot()` at any time

### Progress Snapshot

The `ProgressSnapshot` provides comprehensive progress information:

```python
snapshot = progress_tracker.get_snapshot()

print(f"Progress: {snapshot.progress_percentage:.1f}%")
print(f"Completed: {snapshot.completed_chunks}/{snapshot.total_chunks} chunks")
print(f"Rows: {snapshot.total_rows_processed:,} processed")
print(f"Successful: {snapshot.total_rows_successful:,}")
print(f"Failed: {snapshot.total_rows_failed:,}")
print(f"Elapsed: {snapshot.elapsed_time:.1f}s")
if snapshot.estimated_remaining_time:
    print(f"Remaining: ~{snapshot.estimated_remaining_time:.1f}s")
```

### Estimated Remaining Time

The remaining time is calculated based on:
- Average time per completed chunk
- Number of remaining chunks

This provides a reasonable estimate, but actual time may vary based on:
- Chunk size variations
- Database load
- Network conditions

## Error Handling Strategy

### Chunk-Level Errors

- Individual chunk failures don't stop the entire job
- Failed chunks are logged with details
- Other chunks continue processing
- Final result includes failed chunk summary

### Retry Strategy

- Transient errors are automatically retried
- Non-retryable errors fail immediately
- Retry attempts are logged with delays
- Final error is logged if all retries fail

### Error Aggregation

Final results include:
- Total rows processed
- Rows successful vs failed
- Chunks succeeded vs failed
- Detailed error information for failed chunks

## Best Practices

### Retry Configuration

1. **Use appropriate max_retries**: 3-5 retries is usually sufficient
2. **Set reasonable delays**: Start with 1-2 seconds, cap at 60-120 seconds
3. **Enable jitter**: Prevents synchronized retries across chunks
4. **Monitor retry patterns**: High retry rates may indicate underlying issues

### Progress Tracking

1. **Use callbacks for long jobs**: Provides user feedback during execution
2. **Adjust update interval**: Balance between responsiveness and overhead
3. **Log progress for monitoring**: Helps track long-running jobs
4. **Don't overload callbacks**: Keep callback functions lightweight

### Performance Considerations

1. **Retry overhead**: Retries add time - balance between reliability and performance
2. **Progress callback overhead**: Frequent callbacks can add overhead
3. **Memory usage**: Progress tracking uses minimal memory
4. **Thread safety**: All progress updates are thread-safe

## Examples

### Complete Example with Retry and Progress

```python
from backend.modules.mapper import (
    execute_query_parallel,
    RetryHandler,
    RetryConfig,
    create_progress_callback
)

# Custom progress callback
def log_progress(snapshot):
    print(f"[Progress] {snapshot.progress_percentage:.1f}% "
          f"({snapshot.completed_chunks}/{snapshot.total_chunks} chunks, "
          f"{snapshot.total_rows_processed:,} rows)")

# Execute with retry and progress
result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM large_table ORDER BY id",
    target_conn=target_conn,
    target_schema="target_schema",
    target_table="target_table",
    enable_retry=True,
    max_retries=3,
    enable_progress=True,
    progress_callback=log_progress
)

# Check results
print(f"Total rows: {result.total_rows_processed:,}")
print(f"Successful: {result.total_rows_successful:,}")
print(f"Failed: {result.total_rows_failed:,}")
print(f"Chunks succeeded: {result.chunks_succeeded}/{result.chunks_total}")
if result.chunk_errors:
    print(f"Chunks failed: {len(result.chunk_errors)}")
    for err in result.chunk_errors:
        print(f"  Chunk {err['chunk_id']}: {err['error']}")
```

### Advanced Configuration

```python
from backend.modules.mapper import (
    ParallelProcessor,
    RetryHandler,
    RetryConfig,
    ProgressTracker,
    create_progress_callback
)

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
)
retry_handler = RetryHandler(retry_config)

# Custom progress tracker
progress_tracker = ProgressTracker(
    total_chunks=10,  # Will be set by processor
    callback=create_progress_callback("My Parallel Job"),
    update_interval=1.0
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
    source_sql="SELECT * FROM large_table",
    target_conn=target_conn,
    target_schema="schema",
    target_table="table"
)
```

## Testing

Unit tests are available for:
- Retry handler: `test_parallel_retry_handler.py`
- Progress tracker: `test_parallel_progress.py`

Run tests with:
```bash
pytest backend/modules/mapper/tests/test_parallel_retry_handler.py -v
pytest backend/modules/mapper/tests/test_parallel_progress.py -v
```

## Migration from Phase 2

Phase 3 is **backward compatible**. Existing code continues to work:

- **Retry is enabled by default** (can be disabled)
- **Progress tracking is enabled by default** (can be disabled)
- **No code changes required** for existing implementations
- **Optional configuration** for advanced use cases

To disable retry or progress:
```python
result = execute_query_parallel(
    source_conn=source_conn,
    source_sql="SELECT * FROM table",
    enable_retry=False,
    enable_progress=False
)
```

## Summary

Phase 3 adds:
- ✅ Automatic retry with exponential backoff
- ✅ Real-time progress tracking
- ✅ Enhanced error handling
- ✅ Thread-safe progress updates
- ✅ Configurable retry and progress behavior
- ✅ Backward compatible with Phase 2
- ✅ Comprehensive unit tests
- ✅ Complete documentation

The parallel processing implementation is now production-ready with robust error handling and monitoring capabilities.

