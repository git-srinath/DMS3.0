# Mapper Module Parallel Processing (MPP) Design & Implementation Plan

## Executive Summary

This document outlines the design and implementation plan for introducing parallel processing (MPP) capabilities to the mapper module to significantly improve performance when handling large data volumes. The design focuses on chunking data, parallel extraction, transformation, and loading while maintaining minimal UI changes and preserving existing functionality.

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Design Goals & Requirements](#design-goals--requirements)
3. [Proposed Architecture](#proposed-architecture)
4. [Implementation Strategy](#implementation-strategy)
5. [Technical Design](#technical-design)
6. [Configuration & Tuning](#configuration--tuning)
7. [Error Handling & Recovery](#error-handling--recovery)
8. [Testing Strategy](#testing-strategy)
9. [Performance Expectations](#performance-expectations)
10. [Implementation Phases](#implementation-phases)
11. [Risks & Mitigation](#risks--mitigation)

---

## Current Architecture Analysis

### Current Data Flow

```
1. User triggers job execution (immediate/scheduled)
2. Execution Engine loads job flow configuration
3. Source SQL query executed (single query, fetchall)
4. All data loaded into memory (DataFrame/pandas or cursor results)
5. Data transformation applied (row by row or vectorized)
6. Data inserted into target table (batch inserts, typically 1000 rows)
7. Progress tracking and error logging
```

### Current Limitations

1. **Single-threaded extraction**: Source data is fetched in one operation, limited by memory
2. **Sequential processing**: Transformation and loading happen sequentially
3. **Memory constraints**: Large datasets must fit entirely in memory
4. **No parallelization**: CPU and I/O resources underutilized
5. **No chunking at extraction level**: Only batch inserts are chunked

### Current Code Locations

- **Execution Engine**: `backend/modules/jobs/execution_engine.py`
- **Mapper Package**: `backend/modules/mapper/pkgdwmapr_python.py`
- **File Upload Loader** (reference): `backend/modules/file_upload/data_loader.py` (has batch processing)

---

## Design Goals & Requirements

### Functional Requirements

1. **Support both database and file sources**
   - Database sources: Parallel chunk extraction from source queries
   - File sources: Parallel file reading/parsing (if applicable)

2. **Maintain backward compatibility**
   - Existing jobs must work without modification
   - Same UI/UX for users
   - Same error reporting and logging

3. **Configurable parallelism**
   - Enable/disable parallel processing per job
   - Configurable worker thread count
   - Configurable chunk sizes

4. **Transparent operation**
   - No UI changes required
   - Same progress reporting mechanism
   - Same error handling interface

### Performance Requirements

1. **Scalability**: Handle datasets from 1M to 100M+ rows efficiently
2. **Resource efficiency**: Utilize available CPU cores and I/O bandwidth
3. **Memory efficiency**: Process data in chunks without loading entire dataset
4. **Fault tolerance**: Continue processing even if some chunks fail

### Non-Functional Requirements

1. **Minimal code changes**: Leverage existing infrastructure
2. **Maintainability**: Clean, well-documented code
3. **Testability**: Unit and integration tests
4. **Monitoring**: Enhanced logging and metrics

---

## Proposed Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Job Execution Request                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Parallel Processing Coordinator                    │
│  - Determines chunking strategy                                 │
│  - Manages worker pool                                          │
│  - Coordinates extraction → transformation → loading            │
│  - Aggregates results                                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Chunk 1    │  │   Chunk 2    │  │   Chunk N    │
│              │  │              │  │              │
│ Extract ────▶│  │ Extract ────▶│  │ Extract ────▶│
│ Transform ──▶│  │ Transform ──▶│  │ Transform ──▶│
│ Load ───────▶│  │ Load ───────▶│  │ Load ───────▶│
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Result Aggregation & Status Reporting              │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Parallel Processing Coordinator**
   - Main orchestrator for parallel execution
   - Manages worker thread pool
   - Handles chunking strategy
   - Coordinates Extract-Transform-Load (ETL) pipeline

#### 2. **Chunk Manager**
   - Divides source data into logical chunks
   - For database: Uses ROW_NUMBER() or OFFSET/LIMIT with keys
   - For files: Divides file into byte ranges or logical sections

#### 3. **Worker Pool**
   - Thread pool executor for parallel processing
   - Configurable worker count (default: CPU cores - 1)
   - Each worker handles one chunk end-to-end

#### 4. **Chunk Processor**
   - Extracts chunk data from source
   - Applies transformations
   - Loads into target database
   - Returns chunk statistics

#### 5. **Result Aggregator**
   - Combines results from all chunks
   - Tracks overall progress
   - Aggregates error logs
   - Updates job status

---

## Implementation Strategy

### Strategy: Chunk-Based Parallel Processing

#### Phase 1: Chunked Extraction
- Source SQL modified to support chunking (OFFSET/LIMIT or ROW_NUMBER)
- Each worker extracts a different chunk
- Chunks processed in parallel

#### Phase 2: Parallel Transformation
- Each chunk transformed independently
- Transformation logic remains unchanged (reused)
- Parallel execution across chunks

#### Phase 3: Parallel Loading
- Each chunk loaded independently
- Database connection pooling per worker
- Transaction management per chunk

### Chunking Strategies

#### For Database Sources

**Option A: OFFSET/LIMIT (PostgreSQL/MySQL)**
```sql
-- Original query wrapped
SELECT * FROM (
    SELECT ..., ROW_NUMBER() OVER (ORDER BY <key_column>) as rn
    FROM (<original_query>) subq
) WHERE rn BETWEEN :start_row AND :end_row
```

**Option B: Key-Based Chunking (Better performance)**
```sql
-- Requires ordered key column
SELECT * FROM (<original_query>)
WHERE <key_column> >= :chunk_start_key 
  AND <key_column> < :chunk_end_key
ORDER BY <key_column>
```

**Option C: ROWID-based (Oracle)**
```sql
SELECT * FROM (<original_query>)
WHERE ROWID BETWEEN :start_rowid AND :end_rowid
```

#### For File Sources
- **CSV/Excel**: Split by byte ranges, parse independently
- **JSON**: Stream parsing with chunk boundaries
- **Parquet**: Native columnar chunks

---

## Technical Design

### Component Design

#### 1. Parallel Processing Service

**File**: `backend/modules/mapper/parallel_processor.py`

```python
class ParallelProcessor:
    """Manages parallel processing of mapper jobs"""
    
    def __init__(
        self,
        max_workers: int = None,
        chunk_size: int = 50000,
        enable_parallel: bool = True
    ):
        self.max_workers = max_workers or (os.cpu_count() - 1 or 1)
        self.chunk_size = chunk_size
        self.enable_parallel = enable_parallel
    
    def process_mapper_job(
        self,
        source_conn,
        target_conn,
        source_sql: str,
        transformation_logic,
        target_schema: str,
        target_table: str,
        db_type: str
    ) -> Dict[str, Any]:
        """Main entry point for parallel processing"""
        
        if not self.enable_parallel:
            return self._process_sequential(...)
        
        # 1. Determine chunking strategy
        chunk_strategy = self._determine_chunk_strategy(source_conn, source_sql)
        
        # 2. Calculate total chunks
        total_rows = self._estimate_total_rows(source_conn, source_sql)
        num_chunks = (total_rows + self.chunk_size - 1) // self.chunk_size
        
        # 3. Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for chunk_id in range(num_chunks):
                future = executor.submit(
                    self._process_chunk,
                    chunk_id=chunk_id,
                    source_conn=source_conn,
                    source_sql=source_sql,
                    chunk_strategy=chunk_strategy,
                    transformation_logic=transformation_logic,
                    target_conn=target_conn,
                    target_schema=target_schema,
                    target_table=target_table,
                    db_type=db_type
                )
                futures.append((chunk_id, future))
            
            # 4. Aggregate results
            results = self._aggregate_results(futures)
        
        return results
```

#### 2. Chunk Manager

**File**: `backend/modules/mapper/chunk_manager.py`

```python
class ChunkManager:
    """Manages chunking strategies for different data sources"""
    
    def create_chunked_query(
        self,
        original_sql: str,
        chunk_id: int,
        chunk_size: int,
        db_type: str,
        key_column: Optional[str] = None
    ) -> str:
        """Creates a chunked version of the source SQL"""
        
        if db_type == "POSTGRESQL":
            return self._create_postgresql_chunk_query(
                original_sql, chunk_id, chunk_size, key_column
            )
        elif db_type == "ORACLE":
            return self._create_oracle_chunk_query(
                original_sql, chunk_id, chunk_size, key_column
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _create_postgresql_chunk_query(
        self, sql: str, chunk_id: int, chunk_size: int, key_column: Optional[str]
    ) -> str:
        """Creates PostgreSQL chunk query using OFFSET/LIMIT"""
        offset = chunk_id * chunk_size
        return f"""
            SELECT * FROM (
                {sql}
            ) subq
            ORDER BY {key_column or '1'}
            LIMIT {chunk_size} OFFSET {offset}
        """
```

#### 3. Chunk Processor

**File**: `backend/modules/mapper/chunk_processor.py`

```python
class ChunkProcessor:
    """Processes a single chunk of data"""
    
    def process_chunk(
        self,
        chunk_id: int,
        source_conn,
        chunk_sql: str,
        transformation_logic,
        target_conn,
        target_schema: str,
        target_table: str,
        db_type: str
    ) -> ChunkResult:
        """Process a single chunk end-to-end"""
        
        try:
            # 1. Extract chunk data
            source_cursor = source_conn.cursor()
            source_cursor.execute(chunk_sql)
            chunk_data = source_cursor.fetchall()
            columns = [desc[0] for desc in source_cursor.description]
            source_cursor.close()
            
            if not chunk_data:
                return ChunkResult(chunk_id=chunk_id, rows_processed=0)
            
            # 2. Transform data
            transformed_data = self._apply_transformation(
                chunk_data, columns, transformation_logic
            )
            
            # 3. Load to target
            load_result = self._load_chunk(
                target_conn,
                target_schema,
                target_table,
                transformed_data,
                db_type
            )
            
            return ChunkResult(
                chunk_id=chunk_id,
                rows_processed=len(transformed_data),
                rows_successful=load_result['rows_successful'],
                rows_failed=load_result['rows_failed'],
                errors=load_result.get('errors', [])
            )
            
        except Exception as e:
            return ChunkResult(
                chunk_id=chunk_id,
                rows_processed=0,
                error=str(e)
            )
```

### Integration Points

#### Modified Execution Engine

**File**: `backend/modules/jobs/execution_engine.py`

```python
# In _execute_job_flow method, add parallel processing option

from backend.modules.mapper.parallel_processor import ParallelProcessor

def _execute_job_flow(self, mapref: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # ... existing code ...
    
    # Check if parallel processing is enabled (from job config or params)
    enable_parallel = params.get("enable_parallel", True)  # Default enabled
    max_workers = params.get("max_workers", None)  # Auto-detect
    chunk_size = params.get("chunk_size", 50000)  # 50K rows per chunk
    
    if enable_parallel and total_estimated_rows > chunk_size * 2:
        # Use parallel processing
        processor = ParallelProcessor(
            max_workers=max_workers,
            chunk_size=chunk_size,
            enable_parallel=True
        )
        
        result = processor.process_mapper_job(
            source_conn=source_conn or conn,
            target_conn=target_conn or conn,
            source_sql=source_sql,
            transformation_logic=transformation_function,
            target_schema=target_schema,
            target_table=target_table,
            db_type=target_db_type
        )
    else:
        # Use existing sequential processing
        result = self._process_sequential(...)
    
    return result
```

### Configuration

#### Job Configuration (DMS_JOBFLW or parameters)

Add optional fields:
- `ENABLE_PARALLEL`: Y/N (default: Y)
- `MAX_WORKERS`: Number (default: auto-detect)
- `CHUNK_SIZE`: Number (default: 50000)

#### Environment Variables

```env
# Parallel Processing Configuration
MAPPER_PARALLEL_ENABLED=true
MAPPER_MAX_WORKERS=4  # Optional, auto-detected if not set
MAPPER_CHUNK_SIZE=50000
MAPPER_MIN_ROWS_FOR_PARALLEL=100000  # Enable parallel only for large datasets
```

---

## Configuration & Tuning

### Tuning Parameters

1. **Chunk Size** (`chunk_size`)
   - **Small chunks (10K-25K)**: Better memory usage, more overhead
   - **Medium chunks (50K-100K)**: Balanced (recommended default)
   - **Large chunks (200K+)**: Better throughput, higher memory usage

2. **Worker Count** (`max_workers`)
   - **Default**: `CPU cores - 1`
   - **Database-bound**: Match to connection pool size
   - **CPU-bound**: Match to CPU cores
   - **I/O-bound**: Can exceed CPU cores

3. **Connection Pooling**
   - Each worker needs database connections
   - Source connection pool: `max_workers + 1`
   - Target connection pool: `max_workers + 1`

### Performance Tuning Guidelines

| Scenario | Recommended Settings |
|----------|---------------------|
| Small datasets (<100K rows) | Parallel disabled |
| Medium datasets (100K-1M rows) | 2-4 workers, 50K chunk size |
| Large datasets (1M-10M rows) | 4-8 workers, 50K-100K chunk size |
| Very large datasets (>10M rows) | 8-16 workers, 100K chunk size |
| Database on same server | Fewer workers (2-4) |
| Network latency high | Larger chunks (100K+) |
| High memory availability | More workers, larger chunks |

---

## Error Handling & Recovery

### Error Handling Strategy

1. **Chunk-Level Errors**: Individual chunk failures don't stop entire job
   - Failed chunks logged with details
   - Other chunks continue processing
   - Final report includes failed chunk summary

2. **Retry Mechanism**: Optional retry for transient failures
   - Configurable retry count (default: 0)
   - Exponential backoff for retries

3. **Error Aggregation**:
   ```python
   {
       "total_rows_processed": 1000000,
       "total_rows_successful": 995000,
       "total_rows_failed": 5000,
       "chunks_succeeded": 19,
       "chunks_failed": 1,
       "chunk_errors": [
           {
               "chunk_id": 5,
               "error": "Connection timeout",
               "rows_in_chunk": 50000
           }
       ]
   }
   ```

4. **Transaction Management**:
   - Each chunk processed in its own transaction
   - Failed chunks rollback automatically
   - Successful chunks commit independently
   - Partial success is acceptable

### Recovery Options

1. **Continue on Error**: Process remaining chunks
2. **Stop on First Error**: Abort entire job (configurable)
3. **Resume from Failure**: Track processed chunks, resume from failed chunk (future enhancement)

---

## Testing Strategy

### Unit Tests

1. **Chunk Manager Tests**
   - Verify chunk query generation for different databases
   - Test chunk boundary calculations
   - Test key column detection

2. **Chunk Processor Tests**
   - Test single chunk processing
   - Test transformation application
   - Test error handling

3. **Parallel Processor Tests**
   - Test worker pool management
   - Test result aggregation
   - Test concurrent access patterns

### Integration Tests

1. **End-to-End Tests**
   - Small dataset (sequential fallback)
   - Medium dataset (parallel enabled)
   - Large dataset (full parallel processing)

2. **Database Compatibility Tests**
   - PostgreSQL chunking
   - Oracle chunking
   - Different source/target combinations

3. **Error Scenario Tests**
   - Connection failures
   - Query timeouts
   - Transformation errors
   - Target table constraints

### Performance Tests

1. **Benchmark Tests**
   - Compare sequential vs parallel for various dataset sizes
   - Measure speedup ratios
   - Monitor resource usage (CPU, memory, I/O)

2. **Load Tests**
   - Concurrent job execution
   - Database connection pool limits
   - Memory usage under load

---

## Performance Expectations

### Expected Performance Improvements

| Dataset Size | Sequential Time | Parallel Time (4 workers) | Speedup |
|-------------|----------------|---------------------------|---------|
| 100K rows   | 30s            | 25s                       | 1.2x    |
| 500K rows   | 150s           | 50s                       | 3x      |
| 1M rows     | 300s           | 85s                       | 3.5x    |
| 5M rows     | 1500s          | 350s                      | 4.3x    |
| 10M rows    | 3000s          | 650s                      | 4.6x    |

**Note**: Actual performance depends on:
- Database performance (source and target)
- Network latency
- Transformation complexity
- Available CPU cores and memory
- I/O bandwidth

### Resource Usage

- **CPU**: Higher utilization (good - utilizing available cores)
- **Memory**: Slightly higher (chunks in memory simultaneously)
- **Database Connections**: Increases with worker count
- **Network**: Higher bandwidth utilization

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals**: Core infrastructure without integration

1. Create `parallel_processor.py` skeleton
2. Implement `ChunkManager` with basic chunking strategies
3. Implement `ChunkProcessor` for single chunk processing
4. Unit tests for core components

**Deliverables**:
- Core parallel processing classes
- Unit test suite
- Documentation

### Phase 2: Integration (Week 2-3)

**Goals**: Integrate with existing mapper execution

1. Modify `execution_engine.py` to use parallel processor
2. Add configuration parameters
3. Implement connection pooling for workers
4. Integration tests

**Deliverables**:
- Integrated parallel processing
- Configuration options
- Integration test suite

### Phase 3: Error Handling & Optimization (Week 3-4)

**Goals**: Robust error handling and performance tuning

1. Implement comprehensive error handling
2. Add retry mechanisms
3. Performance optimization
4. Memory usage optimization

**Deliverables**:
- Robust error handling
- Performance benchmarks
- Tuning guidelines

### Phase 4: Testing & Documentation (Week 4-5)

**Goals**: Comprehensive testing and documentation

1. Full integration testing
2. Performance testing
3. User documentation
4. Operational runbooks

**Deliverables**:
- Complete test coverage
- User guide
- Operations guide
- Performance tuning guide

### Phase 5: File Source Support (Week 5-6, Optional)

**Goals**: Extend parallel processing to file sources

1. File chunking strategies
2. Parallel file parsing
3. Integration with file upload module

**Deliverables**:
- File source parallel processing
- Updated documentation

---

## Risks & Mitigation

### Risk 1: Database Connection Exhaustion

**Risk**: Too many parallel workers exhaust connection pool

**Mitigation**:
- Limit max_workers based on connection pool size
- Implement connection pooling per worker
- Add connection pool monitoring

### Risk 2: Memory Usage

**Risk**: Multiple chunks in memory simultaneously cause OOM

**Mitigation**:
- Limit concurrent chunks processed
- Implement streaming processing where possible
- Monitor memory usage and adjust chunk size

### Risk 3: Transaction Conflicts

**Risk**: Parallel inserts cause deadlocks or constraint violations

**Mitigation**:
- Process chunks in separate transactions
- Use appropriate isolation levels
- Design target table without contention (avoid hotspots)

### Risk 4: Source Query Compatibility

**Risk**: Complex source queries cannot be chunked easily

**Mitigation**:
- Fallback to sequential processing for complex queries
- Support multiple chunking strategies
- Allow manual chunking hints in job configuration

### Risk 5: Performance Regression for Small Datasets

**Risk**: Overhead of parallel processing slows down small jobs

**Mitigation**:
- Auto-disable parallel for small datasets (<100K rows)
- Configurable threshold
- Fast path for sequential processing

---

## Additional Considerations

### Monitoring & Observability

1. **Enhanced Logging**:
   - Per-chunk processing times
   - Worker utilization
   - Chunk success/failure rates
   - Overall throughput metrics

2. **Metrics**:
   - Rows processed per second
   - Chunk processing time distribution
   - Worker idle time
   - Error rates

### Future Enhancements

1. **Dynamic Worker Scaling**: Adjust worker count based on load
2. **Resume Capability**: Resume from last successful chunk
3. **Distributed Processing**: Scale across multiple servers
4. **Streaming Processing**: Process chunks as they arrive (no waiting)
5. **Adaptive Chunking**: Adjust chunk size based on performance

---

## Conclusion

This design provides a comprehensive approach to introducing parallel processing to the mapper module while maintaining backward compatibility and minimal UI changes. The phased implementation approach allows for incremental development and testing, reducing risk while delivering value early.

The key benefits:
- **Significant performance improvements** for large datasets (3-5x speedup expected)
- **Minimal code changes** to existing execution flow
- **No UI changes required** - transparent to users
- **Configurable and tunable** for different scenarios
- **Robust error handling** with partial success support

Implementation can begin immediately with Phase 1, and the system can continue to operate with sequential processing until parallel processing is fully tested and validated.

