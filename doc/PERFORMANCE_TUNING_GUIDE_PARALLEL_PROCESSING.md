# Performance Tuning Guide: Parallel Processing

## Overview

This guide provides detailed information on tuning parallel processing for optimal performance.

## Performance Factors

### 1. Chunk Size

**Impact:** Controls balance between parallelism and overhead

**Guidelines:**

| Dataset Size | Recommended Chunk Size | Rationale |
|--------------|------------------------|-----------|
| 100K - 1M rows | 25,000 - 50,000 | More chunks = better parallelism |
| 1M - 10M rows | 50,000 - 100,000 | Balanced parallelism and overhead |
| 10M - 100M rows | 100,000 - 200,000 | Fewer chunks = less overhead |
| 100M+ rows | 200,000+ | Maximum efficiency for very large datasets |

**Tuning Process:**

1. Start with default (50,000)
2. Test with 25,000, 50,000, 100,000
3. Measure execution time for each
4. Choose size with best performance

**Considerations:**
- Smaller chunks = more database round trips
- Larger chunks = more memory per chunk
- Network latency affects optimal chunk size

### 2. Worker Count

**Impact:** Controls level of parallelism

**Guidelines:**

| Workload Type | Recommended Workers | Rationale |
|---------------|---------------------|-----------|
| CPU-bound | CPU cores - 1 | Maximize CPU utilization |
| I/O-bound | 2-4 × CPU cores | Hide I/O latency |
| Database-bound | Connection pool size / 2 | Match database capacity |

**Tuning Process:**

1. Start with CPU cores - 1
2. Test with ±2 workers
3. Monitor database load
4. Choose count with best throughput

**Considerations:**
- More workers = more database connections needed
- Too many workers = context switching overhead
- Database connection limits constrain maximum workers

### 3. Minimum Rows Threshold

**Impact:** Determines when parallel processing activates

**Default:** 100,000 rows

**Guidelines:**

| Environment | Recommended Threshold | Rationale |
|-------------|----------------------|-----------|
| Fast network, powerful DB | 50,000 - 75,000 | Lower overhead |
| Standard environment | 100,000 | Balanced |
| Slow network, limited DB | 150,000 - 200,000 | Higher overhead |

**Tuning Process:**

1. Test with small dataset (50K rows)
2. Measure sequential vs. parallel time
3. Adjust threshold based on crossover point
4. Set threshold where parallel is faster

## Performance Benchmarks

### Baseline Measurement

Before tuning, establish baseline:

```python
import time
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def measure_performance(source_conn, source_sql, target_conn, target_schema, target_table):
    # Sequential baseline (disable parallel)
    start = time.time()
    result_seq = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema=target_schema,
        target_table=target_table,
        enable_parallel=False
    )
    sequential_time = time.time() - start
    sequential_throughput = result_seq.total_rows_processed / sequential_time
    
    # Parallel baseline (default settings)
    start = time.time()
    result_par = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema=target_schema,
        target_table=target_table,
        enable_parallel=True
    )
    parallel_time = time.time() - start
    parallel_throughput = result_par.total_rows_processed / parallel_time
    
    speedup = sequential_time / parallel_time
    efficiency = speedup / result_par.chunks_total
    
    print(f"Sequential: {sequential_time:.2f}s ({sequential_throughput:.0f} rows/s)")
    print(f"Parallel: {parallel_time:.2f}s ({parallel_throughput:.0f} rows/s)")
    print(f"Speedup: {speedup:.2f}x")
    print(f"Efficiency: {efficiency:.2f}")
    
    return {
        'sequential_time': sequential_time,
        'parallel_time': parallel_time,
        'speedup': speedup,
        'throughput': parallel_throughput
    }
```

### Tuning Test Matrix

Test different configurations:

```python
chunk_sizes = [25000, 50000, 100000, 200000]
worker_counts = [2, 4, 6, 8]

results = {}
for chunk_size in chunk_sizes:
    for workers in worker_counts:
        start = time.time()
        result = execute_query_parallel(
            source_conn=source_conn,
            source_sql=source_sql,
            target_conn=target_conn,
            target_schema=target_schema,
            target_table=target_table,
            chunk_size=chunk_size,
            max_workers=workers
        )
        elapsed = time.time() - start
        results[(chunk_size, workers)] = {
            'time': elapsed,
            'throughput': result.total_rows_processed / elapsed
        }
```

## Optimization Strategies

### Strategy 1: Database-Bound Workloads

**Characteristics:**
- Database is the bottleneck
- High database CPU/IO usage
- Connection limits are constraint

**Optimization:**
```python
# Match workers to connection pool
max_workers = min(connection_pool_size // 2, cpu_cores)

# Larger chunks to reduce overhead
chunk_size = 100000  # or higher

# Conservative retry to avoid overload
max_retries = 2
```

### Strategy 2: Network-Bound Workloads

**Characteristics:**
- Network bandwidth is bottleneck
- High latency connections
- Network congestion

**Optimization:**
```python
# Fewer workers to reduce network contention
max_workers = 2  # or 4 for fast networks

# Larger chunks to amortize network overhead
chunk_size = 100000  # or higher

# More retries for network errors
max_retries = 5
initial_delay = 2.0
```

### Strategy 3: Memory-Constrained Environments

**Characteristics:**
- Limited available memory
- Memory errors occur
- Need to minimize memory usage

**Optimization:**
```python
# Smaller chunks to reduce memory per chunk
chunk_size = 25000  # or smaller

# Fewer workers to limit concurrent chunks
max_workers = 2

# Monitor memory usage
# Consider streaming processing for very large datasets
```

### Strategy 4: High-Throughput Requirements

**Characteristics:**
- Maximum throughput needed
- Resources are available
- Optimal performance required

**Optimization:**
```python
# Maximum workers (within connection limits)
max_workers = min(connection_pool_size // 2, cpu_cores * 2)

# Optimal chunk size (test to find)
chunk_size = 50000  # or 100000 for very large datasets

# Enable all optimizations
enable_retry = True
enable_progress = True  # Minimal overhead
```

## Performance Metrics

### Key Metrics to Track

1. **Execution Time**
   - Total time
   - Time per chunk
   - Overhead time

2. **Throughput**
   - Rows per second
   - Chunks per second
   - Data transfer rate

3. **Efficiency**
   - Speedup factor
   - Parallel efficiency
   - Resource utilization

4. **Scalability**
   - Performance vs. dataset size
   - Performance vs. workers
   - Performance vs. chunk size

### Calculating Metrics

```python
def calculate_metrics(result, elapsed_time, sequential_time=None):
    metrics = {
        'total_time': elapsed_time,
        'rows_processed': result.total_rows_processed,
        'throughput': result.total_rows_processed / elapsed_time,
        'chunks_total': result.chunks_total,
        'chunks_per_second': result.chunks_total / elapsed_time,
        'avg_chunk_time': elapsed_time / result.chunks_total,
        'success_rate': result.total_rows_successful / result.total_rows_processed if result.total_rows_processed > 0 else 0
    }
    
    if sequential_time:
        metrics['speedup'] = sequential_time / elapsed_time
        metrics['efficiency'] = metrics['speedup'] / result.chunks_total
    
    return metrics
```

## Tuning Workflows

### Workflow 1: Initial Tuning

1. **Establish Baseline**
   - Measure sequential performance
   - Measure default parallel performance
   - Calculate speedup

2. **Tune Chunk Size**
   - Test 3-4 different chunk sizes
   - Measure execution time
   - Choose optimal size

3. **Tune Worker Count**
   - Test 3-4 different worker counts
   - Monitor database load
   - Choose optimal count

4. **Validate**
   - Test with production-like data
   - Verify correctness
   - Confirm performance improvement

### Workflow 2: Ongoing Optimization

1. **Monitor Performance**
   - Track execution times
   - Monitor resource usage
   - Identify degradation

2. **Analyze Trends**
   - Compare with historical data
   - Identify patterns
   - Detect anomalies

3. **Adjust Configuration**
   - Update based on findings
   - Test changes
   - Deploy improvements

### Workflow 3: Problem Investigation

1. **Identify Issue**
   - Review performance metrics
   - Check error logs
   - Identify bottleneck

2. **Diagnose Root Cause**
   - Analyze resource usage
   - Review configuration
   - Test hypotheses

3. **Implement Fix**
   - Adjust configuration
   - Test solution
   - Deploy fix

## Performance Targets

### Target Metrics

**Speedup:**
- Minimum: 1.5x (50% faster)
- Good: 2-4x
- Excellent: 4x+

**Efficiency:**
- Minimum: 0.5 (50% efficient)
- Good: 0.6-0.8
- Excellent: 0.8+

**Throughput:**
- Depends on dataset and environment
- Target: 2-10x sequential throughput
- Monitor and adjust based on requirements

### Performance Checklist

Before considering optimization complete:

- [ ] Speedup > 1.5x
- [ ] Efficiency > 0.5
- [ ] Error rate < 1%
- [ ] Resource usage within limits
- [ ] Performance consistent across runs
- [ ] No memory errors
- [ ] No connection exhaustion
- [ ] Throughput meets requirements

## Advanced Optimization

### Query Optimization

Optimize source query for chunking:

```sql
-- Good: Ordered query enables key-based chunking
SELECT * FROM large_table ORDER BY id

-- Better: Indexed column for efficient chunking
SELECT * FROM large_table ORDER BY indexed_column

-- Best: Specific range queries when possible
SELECT * FROM large_table 
WHERE id BETWEEN :start AND :end
ORDER BY id
```

### Database Tuning

Tune database for parallel processing:

1. **Connection Pool**
   - Size appropriately
   - Monitor usage
   - Adjust based on load

2. **Indexes**
   - Index ORDER BY columns
   - Index target table for inserts
   - Review index usage

3. **Transaction Settings**
   - Appropriate isolation levels
   - Commit frequency
   - Lock timeouts

### Network Optimization

Optimize network for data transfer:

1. **Bandwidth**
   - Ensure sufficient bandwidth
   - Monitor utilization
   - Plan for peak loads

2. **Latency**
   - Minimize network hops
   - Use fast connections
   - Consider compression

3. **Compression**
   - Enable if network is bottleneck
   - Test impact on CPU
   - Balance trade-offs

## Case Studies

### Case Study 1: Large Dataset Migration

**Scenario:**
- 100M rows to migrate
- PostgreSQL to PostgreSQL
- 1Gbps network
- 8 CPU cores, 32GB RAM

**Configuration:**
```python
max_workers = 6
chunk_size = 100000
min_rows_for_parallel = 200000
```

**Results:**
- Speedup: 3.2x
- Throughput: 450K rows/second
- Execution time: 3.7 minutes (vs. 11.8 minutes sequential)

### Case Study 2: Network-Limited Environment

**Scenario:**
- 10M rows to process
- Cross-region (high latency)
- 100Mbps network
- 4 CPU cores

**Configuration:**
```python
max_workers = 2
chunk_size = 200000
max_retries = 5
initial_delay = 2.0
```

**Results:**
- Speedup: 1.8x
- Throughput: 120K rows/second
- Stable execution with retries

## Monitoring and Alerts

### Key Performance Indicators (KPIs)

Monitor these KPIs:

1. **Execution Time**
   - Alert if > 2x baseline
   - Track trends over time

2. **Throughput**
   - Alert if < 50% of baseline
   - Monitor for degradation

3. **Error Rate**
   - Alert if > 5%
   - Track error patterns

4. **Resource Usage**
   - Alert if connections > 80% limit
   - Alert if memory > 80% available

### Alert Configuration

```python
# Example alert thresholds
ALERT_THRESHOLDS = {
    'execution_time_multiplier': 2.0,
    'throughput_degradation': 0.5,
    'error_rate': 0.05,
    'connection_usage': 0.8,
    'memory_usage': 0.8
}
```

## Conclusion

Performance tuning is an iterative process:

1. **Measure** - Establish baseline
2. **Tune** - Adjust configuration
3. **Validate** - Test and verify
4. **Monitor** - Track ongoing performance
5. **Optimize** - Continue improvement

Start with default settings and tune based on your specific environment and requirements.

