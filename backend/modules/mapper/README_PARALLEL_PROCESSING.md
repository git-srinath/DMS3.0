# Mapper Parallel Processing - Phase 1 Implementation

## Overview

This document describes the Phase 1 implementation of parallel processing for the mapper module. Phase 1 focuses on building the core infrastructure components without integration into the main execution flow.

## Components Created

### 1. Data Models (`parallel_models.py`)

Defines the data structures used throughout the parallel processing system:

- **`ChunkingStrategy`**: Enum for different chunking strategies (OFFSET_LIMIT, KEY_BASED, ROWID_BASED)
- **`ChunkResult`**: Result from processing a single chunk
- **`ParallelProcessingResult`**: Aggregated result from all chunks
- **`ChunkConfig`**: Configuration for chunking parameters

### 2. Chunk Manager (`chunk_manager.py`)

Responsible for:
- Estimating total rows in source query
- Detecting key columns for efficient chunking
- Creating chunked SQL queries (OFFSET/LIMIT or key-based)
- Calculating chunk configuration

**Key Methods:**
- `estimate_total_rows()`: Wraps source SQL in COUNT query
- `create_chunked_query()`: Creates SQL for specific chunk
- `detect_key_column()`: Attempts to find key column from ORDER BY clause
- `calculate_chunk_config()`: Determines chunking strategy and number of chunks

**Supported Databases:**
- PostgreSQL (OFFSET/LIMIT, key-based)
- Oracle (ROWNUM-based, key-based with ROW_NUMBER)

### 3. Chunk Processor (`chunk_processor.py`)

Handles end-to-end processing of a single chunk:

1. **Extract**: Executes chunked SQL query
2. **Transform**: Applies transformation logic (if provided)
3. **Load**: Inserts data into target table (if specified)

**Key Methods:**
- `process_chunk()`: Main entry point for chunk processing
- `_load_chunk()`: Handles database insertion for chunk data

### 4. Parallel Processor (`parallel_processor.py`)

Main coordinator for parallel processing:

- Manages worker thread pool
- Submits chunk processing tasks
- Aggregates results from all chunks
- Provides fallback to sequential processing

**Key Methods:**
- `process_mapper_job()`: Main entry point for parallel processing
- `_aggregate_results()`: Combines results from all chunks
- `_process_sequential()`: Placeholder for sequential fallback

**Configuration:**
- `max_workers`: Number of parallel workers (default: CPU cores - 1)
- `chunk_size`: Rows per chunk (default: 50,000)
- `enable_parallel`: Enable/disable parallel processing

## Usage Example

```python
from backend.modules.mapper import ParallelProcessor

# Initialize processor
processor = ParallelProcessor(
    max_workers=4,
    chunk_size=50000,
    enable_parallel=True
)

# Process mapper job
result = processor.process_mapper_job(
    source_conn=source_connection,
    source_sql="SELECT * FROM source_table ORDER BY id",
    transformation_logic=lambda rows: transform_data(rows),
    target_conn=target_connection,
    target_schema="target_schema",
    target_table="target_table"
)

# Check results
print(f"Total rows processed: {result.total_rows_processed}")
print(f"Successful: {result.total_rows_successful}")
print(f"Failed: {result.total_rows_failed}")
print(f"Chunks succeeded: {result.chunks_succeeded}/{result.chunks_total}")
```

## Testing

Unit tests are provided in `tests/` directory:

- `test_chunk_manager.py`: Tests for chunking logic and SQL generation
- `test_parallel_processor.py`: Tests for result aggregation and configuration

Run tests with:
```bash
pytest backend/modules/mapper/tests/ -v
```

## Next Steps (Phase 2)

1. Integrate with `execution_engine.py`
2. Add configuration parameters to job flow
3. Implement connection pooling for workers
4. Add comprehensive error handling
5. Integration tests with real databases

## Notes

- Phase 1 components are independent and can be tested in isolation
- No changes to existing execution flow yet
- Sequential processing fallback is a placeholder - actual integration will use existing sequential logic
- Chunking strategies can be extended for file sources in Phase 5

