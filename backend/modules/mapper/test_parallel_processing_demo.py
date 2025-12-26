"""
Test script to demonstrate and verify parallel processing functionality.
This script can be run independently to test Phase 2 implementation.

Usage:
    python -m backend.modules.mapper.test_parallel_processing_demo

Requirements:
    - Database connections configured (source and optionally target)
    - Test table with data
    - Environment variables or .env file configured
"""
import os
import sys
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from backend.database.dbconnect import create_metadata_connection, create_target_connection
    from backend.modules.mapper.parallel_query_executor import execute_query_parallel, get_parallel_config
    from backend.modules.mapper.parallel_integration_helper import get_parallel_config_from_params
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.logger import info, warning, error, debug
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


def print_config():
    """Print current parallel processing configuration"""
    print("\n" + "="*80)
    print("PARALLEL PROCESSING CONFIGURATION")
    print("="*80)
    
    config = get_parallel_config()
    print(f"Enabled: {config['enabled']}")
    print(f"Max Workers: {config['max_workers'] or 'Auto-detect'}")
    print(f"Chunk Size: {config['chunk_size']:,} rows")
    print(f"Min Rows for Parallel: {config['min_rows_for_parallel']:,} rows")
    
    # Show environment variables
    print("\nEnvironment Variables:")
    print(f"  MAPPER_PARALLEL_ENABLED: {os.getenv('MAPPER_PARALLEL_ENABLED', 'Not set')}")
    print(f"  MAPPER_MAX_WORKERS: {os.getenv('MAPPER_MAX_WORKERS', 'Not set')}")
    print(f"  MAPPER_CHUNK_SIZE: {os.getenv('MAPPER_CHUNK_SIZE', 'Not set')}")
    print(f"  MAPPER_MIN_ROWS_FOR_PARALLEL: {os.getenv('MAPPER_MIN_ROWS_FOR_PARALLEL', 'Not set')}")
    print("="*80 + "\n")


def test_simple_query(source_conn, test_sql: str):
    """Test parallel processing with a simple query (read-only)"""
    print("\n" + "="*80)
    print("TEST 1: Simple Query (Read-Only)")
    print("="*80)
    print(f"SQL: {test_sql}\n")
    
    try:
        result = execute_query_parallel(
            source_conn=source_conn,
            source_sql=test_sql,
            enable_parallel=True,
            chunk_size=10000,  # Smaller chunk size for testing
            min_rows_for_parallel=1000  # Lower threshold for testing
        )
        
        print("\nResults:")
        print(f"  Total Rows Processed: {result.total_rows_processed:,}")
        print(f"  Rows Successful: {result.total_rows_successful:,}")
        print(f"  Rows Failed: {result.total_rows_failed:,}")
        print(f"  Chunks Total: {result.chunks_total}")
        print(f"  Chunks Succeeded: {result.chunks_succeeded}")
        print(f"  Chunks Failed: {result.chunks_failed}")
        print(f"  Processing Time: {result.processing_time:.2f} seconds")
        
        if result.chunk_errors:
            print(f"\n  Chunk Errors: {len(result.chunk_errors)}")
            for err in result.chunk_errors[:5]:  # Show first 5
                print(f"    Chunk {err['chunk_id']}: {err['error']}")
        
        print("\n✓ Test 1 completed successfully!")
        return True
        
    except Exception as e:
        error(f"Test 1 failed: {e}", exc_info=True)
        return False


def test_with_transformation(source_conn, test_sql: str):
    """Test parallel processing with transformation function"""
    print("\n" + "="*80)
    print("TEST 2: Query with Transformation")
    print("="*80)
    print(f"SQL: {test_sql}\n")
    
    def transform_rows(rows):
        """Example transformation: convert to uppercase if string"""
        transformed = []
        for row in rows:
            if isinstance(row, dict):
                new_row = {}
                for k, v in row.items():
                    if isinstance(v, str):
                        new_row[k] = v.upper()
                    else:
                        new_row[k] = v
                transformed.append(new_row)
            else:
                transformed.append(row)
        return transformed
    
    try:
        result = execute_query_parallel(
            source_conn=source_conn,
            source_sql=test_sql,
            transformation_func=transform_rows,
            enable_parallel=True,
            chunk_size=10000,
            min_rows_for_parallel=1000
        )
        
        print("\nResults:")
        print(f"  Total Rows Processed: {result.total_rows_processed:,}")
        print(f"  Processing Time: {result.processing_time:.2f} seconds")
        
        print("\n✓ Test 2 completed successfully!")
        return True
        
    except Exception as e:
        error(f"Test 2 failed: {e}", exc_info=True)
        return False


def test_with_target_table(source_conn, source_sql: str, target_conn, target_schema: str, target_table: str):
    """Test parallel processing with target table (if provided)"""
    print("\n" + "="*80)
    print("TEST 3: Query with Target Table (Insert)")
    print("="*80)
    print(f"Source SQL: {source_sql}")
    print(f"Target: {target_schema}.{target_table}\n")
    print("WARNING: This test will INSERT data into the target table!")
    
    response = input("Do you want to proceed with this test? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Test 3 skipped.")
        return None
    
    try:
        result = execute_query_parallel(
            source_conn=source_conn,
            source_sql=source_sql,
            target_conn=target_conn,
            target_schema=target_schema,
            target_table=target_table,
            enable_parallel=True,
            chunk_size=5000,  # Smaller chunks for insert testing
            min_rows_for_parallel=1000
        )
        
        print("\nResults:")
        print(f"  Total Rows Processed: {result.total_rows_processed:,}")
        print(f"  Rows Successful: {result.total_rows_successful:,}")
        print(f"  Rows Failed: {result.total_rows_failed:,}")
        print(f"  Processing Time: {result.processing_time:.2f} seconds")
        
        if result.chunk_errors:
            print(f"\n  Chunk Errors: {len(result.chunk_errors)}")
        
        print("\n✓ Test 3 completed successfully!")
        return True
        
    except Exception as e:
        error(f"Test 3 failed: {e}", exc_info=True)
        return False


def test_config_priority():
    """Test that configuration priority works correctly"""
    print("\n" + "="*80)
    print("TEST 4: Configuration Priority")
    print("="*80)
    
    # Test with params (should override env)
    params = {
        'enable_parallel': True,
        'max_workers': 2,
        'chunk_size': 25000
    }
    
    config = get_parallel_config_from_params(params)
    print(f"Config from params: {config}")
    
    print("\n✓ Test 4 completed successfully!")
    return True


def main():
    """Main test function"""
    print("\n" + "="*80)
    print("PARALLEL PROCESSING TEST SUITE")
    print("="*80)
    print("This script tests Phase 2 parallel processing implementation.")
    print("Make sure you have:")
    print("  1. Database connections configured")
    print("  2. Test data available")
    print("  3. Environment variables set in .env file")
    print("="*80)
    
    # Print configuration
    print_config()
    
    # Get database connections
    print("Connecting to databases...")
    try:
        source_conn = create_metadata_connection()
        print("✓ Source connection established (using metadata connection)")
    except Exception as e:
        error(f"Failed to create source connection: {e}")
        return 1
    
    target_conn = None
    try:
        # Try to get a target connection (optional)
        target_conid = os.getenv('TEST_TARGET_CONNECTION_ID')
        if target_conid:
            target_conn = create_target_connection(target_conid)
            print(f"✓ Target connection established (ID: {target_conid})")
        else:
            print("ℹ No target connection configured (TEST_TARGET_CONNECTION_ID not set)")
    except Exception as e:
        warning(f"Could not create target connection: {e}")
        print("ℹ Continuing without target connection (some tests will be skipped)")
    
    # Detect database type and use appropriate SQL
    db_type = _detect_db_type(source_conn)
    print(f"Detected database type: {db_type}")
    
    # Test SQL queries - generate based on database type
    # If custom SQL is provided via env vars, use that; otherwise use database-specific defaults
    if os.getenv('TEST_SQL_SMALL'):
        test_sql_small = os.getenv('TEST_SQL_SMALL')
    elif db_type == "POSTGRESQL":
        # PostgreSQL syntax - using generate_series to create test data
        test_sql_small = 'SELECT id, name FROM (SELECT generate_series(1, 100) as id, \'test\' || generate_series(1, 100)::text as name) t'
    else:
        # Oracle syntax (fallback)
        test_sql_small = 'SELECT * FROM (SELECT 1 as id, \'test\' as name FROM DUAL) WHERE ROWNUM <= 100'
    
    if os.getenv('TEST_SQL_LARGE'):
        test_sql_large = os.getenv('TEST_SQL_LARGE')
    elif db_type == "POSTGRESQL":
        # PostgreSQL syntax - using generate_series to create test data
        # For large dataset, we'll create 50K rows
        test_sql_large = 'SELECT id, name FROM (SELECT generate_series(1, 50000) as id, \'row\' || generate_series(1, 50000)::text as name) t ORDER BY id'
    else:
        # Oracle syntax (fallback)
        test_sql_large = 'SELECT * FROM (SELECT LEVEL as id, \'row\' || LEVEL as name FROM DUAL CONNECT BY LEVEL <= 50000) ORDER BY id'
    
    print(f"Using test SQL for {db_type} database")
    print(f"Small test SQL (first 200 chars): {test_sql_small[:200]}...")
    print(f"Large test SQL (first 200 chars): {test_sql_large[:200]}...")
    
    results = []
    
    # Test 1: Simple query
    try:
        results.append(("Test 1: Simple Query", test_simple_query(source_conn, test_sql_large)))
    except Exception as e:
        error(f"Test 1 error: {e}")
        results.append(("Test 1: Simple Query", False))
    
    # Test 2: With transformation
    try:
        results.append(("Test 2: With Transformation", test_with_transformation(source_conn, test_sql_large)))
    except Exception as e:
        error(f"Test 2 error: {e}")
        results.append(("Test 2: With Transformation", False))
    
    # Test 3: With target table (if configured)
    if target_conn:
        target_schema = os.getenv('TEST_TARGET_SCHEMA', '')
        target_table = os.getenv('TEST_TARGET_TABLE', '')
        if target_schema and target_table:
            try:
                results.append(("Test 3: With Target Table", 
                              test_with_target_table(source_conn, test_sql_large, target_conn, target_schema, target_table)))
            except Exception as e:
                error(f"Test 3 error: {e}")
                results.append(("Test 3: With Target Table", False))
    
    # Test 4: Configuration priority
    try:
        results.append(("Test 4: Configuration Priority", test_config_priority()))
    except Exception as e:
        error(f"Test 4 error: {e}")
        results.append(("Test 4: Configuration Priority", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print(f"✓ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"✗ {test_name}: FAILED")
            failed += 1
        else:
            print(f"- {test_name}: SKIPPED")
            skipped += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*80 + "\n")
    
    # Cleanup
    try:
        source_conn.close()
        if target_conn:
            target_conn.close()
    except Exception:
        pass
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

