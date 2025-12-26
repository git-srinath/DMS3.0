# Operations Guide: Parallel Processing

## Overview

This guide provides operational information for system administrators and DevOps teams managing parallel processing in production environments.

## Architecture

### Components

1. **ParallelProcessor**: Main coordinator
2. **ChunkManager**: Handles data chunking strategies
3. **ChunkProcessor**: Processes individual chunks
4. **ConnectionPoolManager**: Manages database connections
5. **RetryHandler**: Handles retry logic
6. **ProgressTracker**: Tracks execution progress

### Data Flow

```
Source Database
    ↓
ChunkManager (splits into chunks)
    ↓
ParallelProcessor (coordinates workers)
    ↓
ChunkProcessor × N workers (process chunks)
    ↓
Target Database
```

## Monitoring

### Key Metrics

Monitor these metrics for parallel processing jobs:

1. **Processing Time**
   - Total execution time
   - Time per chunk
   - Average vs. sequential time

2. **Throughput**
   - Rows processed per second
   - Chunks completed per second

3. **Resource Usage**
   - Database connections in use
   - Memory consumption
   - CPU utilization

4. **Error Rates**
   - Failed chunks percentage
   - Failed rows percentage
   - Retry success rate

### Logging

Parallel processing logs detailed information:

```
INFO: Starting parallel processing with 4 workers, 20 chunks
INFO: Parallel Processing: 25.0% complete (5/20 chunks, 250,000 rows, 10.5s elapsed, ~31.5s remaining)
INFO: Chunk 5 completed: 50,000 rows, 49,950 successful, 50 failed
WARNING: Chunk 10 failed with exception: Connection timeout, will retry (1/3)
INFO: Parallel processing complete: 1,000,000 rows processed (995,000 successful, 5,000 failed) in 42.3s
```

**Key log patterns to monitor:**
- `Starting parallel processing` - Job start
- `Parallel Processing: X% complete` - Progress updates
- `Chunk X completed` - Individual chunk completion
- `Chunk X failed` - Chunk failures
- `will retry` - Retry attempts
- `Parallel processing complete` - Job completion

### Performance Monitoring

Track performance over time:

```python
# Example monitoring code
import logging
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

logger = logging.getLogger(__name__)

def execute_with_monitoring(source_conn, source_sql, target_conn, target_schema, target_table):
    start_time = time.time()
    
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema=target_schema,
        target_table=target_table
    )
    
    elapsed_time = time.time() - start_time
    throughput = result.total_rows_processed / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"Performance metrics: {throughput:.0f} rows/sec, "
                f"{elapsed_time:.2f}s total, "
                f"{result.chunks_failed} chunks failed")
    
    return result
```

## Configuration Management

### Environment-Based Configuration

Use environment variables for different environments:

**Development:**
```env
MAPPER_PARALLEL_ENABLED=true
MAPPER_MAX_WORKERS=2
MAPPER_CHUNK_SIZE=25000
MAPPER_MIN_ROWS_FOR_PARALLEL=50000
```

**Staging:**
```env
MAPPER_PARALLEL_ENABLED=true
MAPPER_MAX_WORKERS=4
MAPPER_CHUNK_SIZE=50000
MAPPER_MIN_ROWS_FOR_PARALLEL=100000
```

**Production:**
```env
MAPPER_PARALLEL_ENABLED=true
MAPPER_MAX_WORKERS=8
MAPPER_CHUNK_SIZE=100000
MAPPER_MIN_ROWS_FOR_PARALLEL=200000
MAPPER_PARALLEL_RETRY_ENABLED=true
MAPPER_PARALLEL_MAX_RETRIES=5
```

### Dynamic Configuration

For runtime configuration changes, use job parameters:

```python
# In job execution
params = {
    'max_workers': get_config_from_db('parallel_workers'),
    'chunk_size': get_config_from_db('parallel_chunk_size'),
    'enable_retry': True,
    'max_retries': get_config_from_db('parallel_max_retries')
}
```

## Database Connection Management

### Connection Pool Sizing

**Formula:**
```
Required connections = (max_workers × 2) + metadata_connections + buffer
```

**Example:**
- 4 workers = 8 worker connections (source + target)
- 1 metadata connection
- 2 buffer connections
- **Total: 11 connections per parallel job**

### Connection Pool Monitoring

Monitor connection pool usage:

```sql
-- PostgreSQL
SELECT count(*), state 
FROM pg_stat_activity 
WHERE datname = 'your_database'
GROUP BY state;

-- Oracle
SELECT status, count(*) 
FROM v$session 
WHERE username = 'your_user'
GROUP BY status;
```

### Connection Pool Limits

Set appropriate limits based on:
- Available database connections
- Number of concurrent parallel jobs
- Other application connections

**Recommendation:**
- Reserve 20-30% of connections for parallel processing
- Limit max_workers to prevent connection exhaustion
- Use connection pooling (ConnectionPoolManager)

## Error Handling and Recovery

### Common Errors

#### 1. Connection Exhaustion

**Symptoms:**
- "too many connections" errors
- Connection timeout errors

**Solutions:**
- Reduce `max_workers`
- Implement connection pooling
- Increase database connection limit
- Stagger parallel job execution

#### 2. Memory Errors

**Symptoms:**
- Out of memory errors
- System becomes unresponsive

**Solutions:**
- Reduce `chunk_size`
- Reduce `max_workers`
- Monitor memory usage
- Add more system memory

#### 3. Deadlocks

**Symptoms:**
- Deadlock errors in database logs
- Chunks failing with lock errors

**Solutions:**
- Ensure proper indexing on target table
- Use appropriate isolation levels
- Process chunks in separate transactions
- Review target table design (avoid hotspots)

### Retry Strategy

Configure retry based on error patterns:

**For transient network errors:**
```python
RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=120.0
)
```

**For database timeout errors:**
```python
RetryConfig(
    max_retries=3,
    initial_delay=5.0,
    max_delay=60.0
)
```

**For stable environments:**
```python
RetryConfig(
    max_retries=2,
    initial_delay=1.0,
    max_delay=30.0
)
```

## Performance Tuning

### Baseline Measurement

Establish baseline performance:

```python
# Sequential baseline
start = time.time()
sequential_result = process_sequentially(...)
sequential_time = time.time() - start

# Parallel baseline
start = time.time()
parallel_result = execute_query_parallel(...)
parallel_time = time.time() - start

speedup = sequential_time / parallel_time
print(f"Speedup: {speedup:.2f}x")
```

### Tuning Parameters

**1. Chunk Size**

Test different chunk sizes:
- Start with default (50,000)
- Test 25,000 and 100,000
- Measure throughput
- Choose optimal size

**2. Worker Count**

Test different worker counts:
- Start with CPU cores - 1
- Test ±2 workers
- Monitor database load
- Choose optimal count

**3. Minimum Rows Threshold**

Adjust based on dataset characteristics:
- Lower for faster networks
- Higher for slower networks
- Consider overhead vs. benefit

### Performance Optimization Checklist

- [ ] Chunk size optimized for dataset
- [ ] Worker count matches available resources
- [ ] Database connections properly sized
- [ ] Network bandwidth sufficient
- [ ] Source query optimized (ORDER BY, indexes)
- [ ] Target table properly indexed
- [ ] Retry configuration appropriate
- [ ] Monitoring in place

## Capacity Planning

### Resource Requirements

**CPU:**
- Parallel processing is I/O-bound
- 2-4 workers per CPU core is typical
- Monitor CPU utilization, adjust if needed

**Memory:**
- Each chunk uses memory during processing
- Estimate: `chunk_size × avg_row_size × max_workers`
- Example: 50K rows × 1KB × 4 workers = ~200MB

**Network:**
- Bandwidth required: `(chunk_size × avg_row_size × max_workers) / processing_time`
- Monitor network utilization
- Consider network latency

**Database:**
- Connections: `(max_workers × 2) + overhead`
- I/O: Proportional to number of workers
- Monitor database load and connections

### Scaling Considerations

**Horizontal Scaling:**
- Parallel processing within single job
- Run multiple jobs concurrently (with connection limits)

**Vertical Scaling:**
- More CPU cores = more workers
- More memory = larger chunk sizes
- More network = faster data transfer

## Troubleshooting

### Diagnostic Steps

1. **Check Logs**
   - Review job execution logs
   - Look for error patterns
   - Identify failed chunks

2. **Monitor Resources**
   - Database connections
   - Memory usage
   - CPU utilization
   - Network bandwidth

3. **Verify Configuration**
   - Environment variables
   - Job parameters
   - Database settings

4. **Test Components**
   - Test chunking strategy
   - Test connection pooling
   - Test retry mechanism

### Common Issues and Solutions

#### Issue: Job Hangs

**Diagnosis:**
- Check database connections (may be exhausted)
- Check for deadlocks
- Review chunk processing logs

**Solution:**
- Reduce max_workers
- Check database locks
- Review chunk SQL queries

#### Issue: Inconsistent Results

**Diagnosis:**
- Compare row counts
- Check for missing chunks
- Review error logs

**Solution:**
- Verify source query is deterministic
- Check for failed chunks
- Review transformation logic

#### Issue: Performance Degradation

**Diagnosis:**
- Compare with baseline
- Check resource utilization
- Review database performance

**Solution:**
- Tune chunk size
- Adjust worker count
- Optimize source/target queries
- Check database indexes

## Maintenance

### Regular Tasks

1. **Monitor Performance Trends**
   - Track execution times
   - Identify degradation
   - Adjust configuration

2. **Review Error Logs**
   - Identify patterns
   - Address recurring issues
   - Update retry configuration

3. **Capacity Planning**
   - Monitor resource usage
   - Plan for growth
   - Adjust limits

4. **Configuration Updates**
   - Test new configurations
   - Update environment variables
   - Document changes

### Backup and Recovery

Parallel processing results should be:
- Logged in job execution history
- Tracked in DMS_PRCLOG table
- Included in backup strategy

Failed jobs can be:
- Re-run with same parameters
- Investigated using error details
- Recovered from checkpoints (if implemented)

## Security Considerations

1. **Connection Security**
   - Use encrypted connections
   - Limit connection privileges
   - Monitor connection activity

2. **Data Security**
   - Ensure data encryption in transit
   - Follow data privacy regulations
   - Audit data access

3. **Resource Security**
   - Limit resource usage per job
   - Prevent resource exhaustion
   - Monitor for abuse

## Best Practices

1. **Start Conservative**
   - Begin with default settings
   - Monitor performance
   - Gradually optimize

2. **Monitor Continuously**
   - Set up alerts
   - Review metrics regularly
   - Track trends

3. **Document Configuration**
   - Record configuration changes
   - Document performance characteristics
   - Maintain runbooks

4. **Test Changes**
   - Test in non-production first
   - Validate performance improvements
   - Verify correctness

5. **Plan for Failures**
   - Implement retry logic
   - Handle partial failures
   - Provide error recovery

