# Testing Parallel Processing Implementation

## Overview

This guide explains how to test the parallel processing functionality implemented in Phase 2, before Phase 3 automatic integration is complete.

## Prerequisites

1. **Environment Variables Configured**
   Add to your `.env` file:
   ```env
   # Parallel Processing Configuration
   MAPPER_PARALLEL_ENABLED=true
   MAPPER_MAX_WORKERS=4
   MAPPER_CHUNK_SIZE=50000
   MAPPER_MIN_ROWS_FOR_PARALLEL=100000
   
   # Optional: For testing with target table
   TEST_TARGET_CONNECTION_ID=your_target_connection_id
   TEST_TARGET_SCHEMA=your_target_schema
   TEST_TARGET_TABLE=your_test_table
   ```

2. **Database Setup**
   - Source database connection configured (metadata connection is used by default)
   - Optional: Target database connection for insert testing
   - Test data available (or use the default test queries)

## Testing Options

### Option 1: Run the Test Script (Recommended)

The test script provides a comprehensive test suite for Phase 2 functionality:

```bash
# From project root
python -m backend.modules.mapper.test_parallel_processing_demo
```

**What it tests:**
1. Configuration reading from environment variables
2. Simple parallel query execution (read-only)
3. Query with transformation function
4. Query with target table insertion (optional, requires confirmation)
5. Configuration priority (params vs env vars)

**Customizing Test Queries:**

You can override default test queries via environment variables. The script automatically detects your database type (PostgreSQL or Oracle) and uses appropriate SQL syntax:

```env
# For small test (100 rows)
# PostgreSQL example:
TEST_SQL_SMALL=SELECT * FROM dms_mapr LIMIT 100

# Oracle example:
TEST_SQL_SMALL=SELECT * FROM dms_mapr WHERE rownum <= 100

# For large test (50,000 rows) - adjust based on your data
# PostgreSQL example:
TEST_SQL_LARGE=SELECT * FROM your_large_table ORDER BY id LIMIT 50000

# Oracle example:
TEST_SQL_LARGE=SELECT * FROM your_large_table WHERE rownum <= 50000 ORDER BY id
```

**Default Test SQL (if not specified):**
- **PostgreSQL**: Uses `generate_series()` to generate synthetic test data
- **Oracle**: Uses `CONNECT BY LEVEL` to generate synthetic test data

**Tip**: For real-world testing, use your actual tables with appropriate filters instead of synthetic data.

### Option 2: Unit Tests

Run the unit test suite:

```bash
# Run all mapper tests
pytest backend/modules/mapper/tests/ -v

# Run specific test file
pytest backend/modules/mapper/tests/test_parallel_connection_pool.py -v
pytest backend/modules/mapper/tests/test_parallel_query_executor.py -v
pytest backend/modules/mapper/tests/test_parallel_integration_helper.py -v
```

### Option 3: Manual Testing in Generated Code

You can manually test by using the parallel query executor in generated mapper code:

**Step 1: Create/Edit a Mapper Job**

In the mapper job's `DWLOGIC`, add:

```python
from backend.modules.mapper.parallel_query_executor import execute_query_parallel

def execute_job(metadata_conn, source_conn, target_conn, session_params):
    # Your source SQL query
    source_sql = """
        SELECT * FROM your_source_table 
        WHERE some_condition = 'value'
        ORDER BY id
    """
    
    # Execute in parallel
    result = execute_query_parallel(
        source_conn=source_conn,
        source_sql=source_sql,
        target_conn=target_conn,
        target_schema="your_target_schema",
        target_table="your_target_table"
    )
    
    # Log results
    print(f"Parallel processing complete:")
    print(f"  Rows processed: {result.total_rows_processed:,}")
    print(f"  Rows successful: {result.total_rows_successful:,}")
    print(f"  Rows failed: {result.total_rows_failed:,}")
    print(f"  Processing time: {result.processing_time:.2f}s")
    
    return {
        "status": "SUCCESS",
        "rows_processed": result.total_rows_processed,
        "rows_successful": result.total_rows_successful,
        "rows_failed": result.total_rows_failed
    }
```

**Step 2: Execute the Job**

Execute the job through the normal job execution flow (scheduler or immediate execution).

**Step 3: Check Results**

Check the job logs for parallel processing output and verify data in the target table.

## What to Look For

### Successful Test Indicators

1. **Configuration Loaded Correctly**
   - Test script shows correct configuration values
   - Environment variables are read properly

2. **Parallel Processing Executes**
   - Multiple chunks are created (check chunk count)
   - Processing completes without errors
   - Rows are processed successfully

3. **Performance**
   - Processing time is reasonable (depends on data size and database)
   - No connection errors or timeouts
   - Chunk processing is distributed across workers

### Common Issues

1. **"Parallel processing disabled or not needed"**
   - **Cause**: Estimated rows below threshold
   - **Solution**: Lower `MAPPER_MIN_ROWS_FOR_PARALLEL` or use larger test dataset

2. **Connection Errors**
   - **Cause**: Database connections not configured properly
   - **Solution**: Verify connection IDs and database accessibility

3. **Chunk Errors**
   - **Cause**: SQL query issues or database-specific limitations
   - **Solution**: Check query syntax, ensure ORDER BY exists for key-based chunking

4. **Import Errors**
   - **Cause**: Module path issues or missing dependencies
   - **Solution**: Ensure you're running from project root, check Python path

## Expected Behavior

### Phase 2 (Current)

- ✅ Configuration is read from environment variables
- ✅ Parallel processing can be invoked manually
- ✅ Connection pooling infrastructure exists
- ⚠️ **Not automatically integrated** - must be called explicitly

### Phase 3 (Future)

- ✅ Automatic integration into execution engine
- ✅ Automatic decision to use parallel vs sequential
- ✅ Enhanced error handling and retries
- ✅ Progress tracking and monitoring

## Recommendations

### For Phase 2 Testing

**Recommended Approach:**
1. Run the test script first (`test_parallel_processing_demo.py`)
2. Verify configuration is loaded correctly
3. Test with a moderate-sized dataset (10K-100K rows)
4. Verify chunks are created and processed
5. Check logs for any errors or warnings

**What to Test:**
- ✅ Configuration reading works
- ✅ Parallel processing executes
- ✅ Results are aggregated correctly
- ✅ No connection leaks
- ⚠️ Actual performance improvement (may vary)

### Should You Wait for Phase 3?

**Test Phase 2 if:**
- You want to verify the infrastructure works
- You need to use parallel processing in generated code now
- You want to understand how it works before automatic integration

**Wait for Phase 3 if:**
- You prefer automatic integration (no code changes needed)
- You want enhanced error handling and progress tracking
- You want to test with actual mapper jobs without modifying code

## Next Steps

After Phase 2 testing:

1. **If tests pass**: Phase 3 will integrate automatically
2. **If issues found**: Report them before Phase 3
3. **For production use**: Wait for Phase 3 for automatic integration

## Troubleshooting

### Debug Mode

Enable debug logging to see detailed parallel processing information:

```python
import logging
logging.getLogger('backend.modules.mapper').setLevel(logging.DEBUG)
```

### Verify Environment Variables

Check that environment variables are loaded:

```python
from backend.modules.mapper.parallel_query_executor import get_parallel_config
config = get_parallel_config()
print(config)
```

### Database-Specific Notes

**Oracle:**
- Uses ROWNUM-based chunking
- May need ORDER BY for efficient chunking
- Connection pooling recommended for multiple workers

**PostgreSQL:**
- Uses OFFSET/LIMIT chunking
- More efficient with key-based chunking (ORDER BY)
- Better performance with multiple connections

## Summary

Phase 2 provides the infrastructure for parallel processing. You can test it now using:
1. The provided test script (recommended)
2. Unit tests
3. Manual integration in generated code

Phase 3 will add automatic integration, making it easier to use without code changes. Testing Phase 2 now helps verify the foundation is solid before Phase 3 integration.

