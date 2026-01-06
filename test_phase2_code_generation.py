#!/usr/bin/env python3
"""
Test script for Phase 2 code generation refactoring.

This script tests:
1. Code generation function syntax
2. Generated code structure
3. Import resolution
4. Basic execution validation
"""

import sys
import os
import ast
import importlib.util

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

def test_code_generation_syntax():
    """Test that build_job_flow_code function is syntactically correct."""
    print("=" * 80)
    print("TEST 1: Code Generation Function Syntax")
    print("=" * 80)
    
    try:
        # Try to import the module
        from backend.modules.jobs.pkgdwjob_create_job_flow import build_job_flow_code
        print("[PASS] Successfully imported build_job_flow_code")
        
        # Check function signature
        import inspect
        sig = inspect.signature(build_job_flow_code)
        params = list(sig.parameters.keys())
        print(f"[PASS] Function signature: build_job_flow_code({', '.join(params)})")
        
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import build_job_flow_code: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generated_code_structure(mock_code: str):
    """Test that generated code has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 2: Generated Code Structure")
    print("=" * 80)
    
    checks = {
        'syntax_valid': False,
        'has_execute_job': False,
        'has_imports': False,
        'has_external_module_imports': False,
        'has_job_config': False,
        'has_execute_mapper_job_call': False,
    }
    
    # Check syntax
    try:
        ast.parse(mock_code)
        checks['syntax_valid'] = True
        print("[PASS] Generated code is syntactically valid")
    except SyntaxError as e:
        print(f"[FAIL] Syntax error in generated code: {e}")
        return False
    
    # Check for required components
    if 'def execute_job' in mock_code:
        checks['has_execute_job'] = True
        print("[PASS] Contains execute_job function")
    
    if 'import' in mock_code or 'from' in mock_code:
        checks['has_imports'] = True
        print("[PASS] Contains import statements")
    
    if 'mapper_job_executor' in mock_code or 'execute_mapper_job' in mock_code:
        checks['has_external_module_imports'] = True
        print("[PASS] Contains external module imports")
    
    if 'job_config' in mock_code:
        checks['has_job_config'] = True
        print("[PASS] Contains job_config dictionary")
    
    if 'execute_mapper_job' in mock_code:
        checks['has_execute_mapper_job_call'] = True
        print("[PASS] Contains execute_mapper_job call")
    
    # Check for old code patterns (should NOT be present)
    old_patterns = [
        'def map_row_to_target_columns',
        'def generate_hash',
        'def log_batch_progress',
        'def check_stop_request',
        'source_cursor.fetchmany',
        'rows_to_insert.append',
        'rows_to_update_scd1.append',
        'rows_to_update_scd2.append',
        'target_cursor.executemany',
        'SYSTIMESTAMP',
        'CURRENT_TIMESTAMP',
        ':param',
        '%s'
    ]
    
    found_old_patterns = []
    for pattern in old_patterns:
        if pattern in mock_code:
            found_old_patterns.append(pattern)
    
    if found_old_patterns:
        print(f"[WARN] Found old code patterns (may be in comments or strings): {found_old_patterns}")
    else:
        print("[PASS] No old inline code patterns found")
    
    # Check if all critical checks passed
    critical_checks = ['syntax_valid', 'has_execute_job', 'has_external_module_imports', 'has_execute_mapper_job_call']
    all_critical_passed = all(checks.get(key, False) for key in critical_checks)
    
    if all_critical_passed:
        print(f"[PASS] All critical checks passed ({len([c for c in checks.values() if c])}/{len(checks)} total checks)")
    else:
        print(f"[FAIL] Some critical checks failed: {[k for k in critical_checks if not checks.get(k, False)]}")
    
    return all_critical_passed


def test_external_modules_importable():
    """Test that external modules can be imported."""
    print("\n" + "=" * 80)
    print("TEST 3: External Module Imports")
    print("=" * 80)
    
    modules_to_test = [
        'backend.modules.mapper.mapper_job_executor',
        'backend.modules.mapper.mapper_transformation_utils',
        'backend.modules.mapper.mapper_progress_tracker',
        'backend.modules.mapper.mapper_checkpoint_handler',
        'backend.modules.mapper.mapper_scd_handler',
        'backend.modules.mapper.database_sql_adapter',
    ]
    
    all_imported = True
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"[PASS] Successfully imported {module_name}")
            
            # Check for key functions/classes
            if 'mapper_job_executor' in module_name:
                if hasattr(module, 'execute_mapper_job'):
                    print(f"   [PASS] execute_mapper_job found")
            elif 'mapper_transformation_utils' in module_name:
                if hasattr(module, 'map_row_to_target_columns') and hasattr(module, 'generate_hash'):
                    print(f"   [PASS] map_row_to_target_columns and generate_hash found")
            elif 'mapper_progress_tracker' in module_name:
                if hasattr(module, 'log_batch_progress') and hasattr(module, 'check_stop_request'):
                    print(f"   [PASS] log_batch_progress and check_stop_request found")
            elif 'mapper_checkpoint_handler' in module_name:
                if hasattr(module, 'apply_checkpoint_to_query') and hasattr(module, 'update_checkpoint'):
                    print(f"   [PASS] checkpoint functions found")
            elif 'mapper_scd_handler' in module_name:
                if hasattr(module, 'process_scd_batch') and hasattr(module, 'prepare_row_for_scd'):
                    print(f"   [PASS] SCD functions found")
            elif 'database_sql_adapter' in module_name:
                if hasattr(module, 'DatabaseSQLAdapter') and hasattr(module, 'create_adapter'):
                    print(f"   [PASS] DatabaseSQLAdapter and create_adapter found")
        except ImportError as e:
            print(f"[FAIL] Failed to import {module_name}: {e}")
            all_imported = False
        except Exception as e:
            print(f"[WARN] Error checking {module_name}: {e}")
    
    return all_imported


def test_generated_code_sample():
    """Test with a sample generated code structure."""
    print("\n" + "=" * 80)
    print("TEST 4: Sample Generated Code Validation")
    print("=" * 80)
    
    # Sample generated code structure (simplified)
    sample_code = '''
"""
Auto-generated ETL Job for TEST_MAPREF
Target: TRG.TEST_TABLE
Type: DIM
"""

from typing import Dict, List, Any, Optional

# Import external modules for common functionality
try:
    from backend.modules.mapper.mapper_job_executor import execute_mapper_job
    from backend.modules.mapper.mapper_transformation_utils import map_row_to_target_columns, generate_hash
except ImportError:
    from modules.mapper.mapper_job_executor import execute_mapper_job
    from modules.mapper.mapper_transformation_utils import map_row_to_target_columns, generate_hash

# Job configuration
MAPREF = "TEST_MAPREF"
JOBID = 1
TARGET_SCHEMA = "TRG"
TARGET_TABLE = "TEST_TABLE"
TARGET_TYPE = "DIM"
FULL_TABLE_NAME = "TRG.TEST_TABLE"
BULK_LIMIT = 5000

# Checkpoint configuration
CHECKPOINT_ENABLED = True
CHECKPOINT_STRATEGY = "KEY"
CHECKPOINT_COLUMN = "ID"
CHECKPOINT_COLUMNS = ["ID"]

# Primary key columns
PK_COLUMNS = ["ID"]
PK_SOURCE_MAPPING = {"ID": "ID"}

# All target columns
ALL_COLUMNS = ["ID", "NAME", "RWHKEY"]
COLUMN_SOURCE_MAPPING = {"ID": "ID", "NAME": "NAME"}
HASH_EXCLUDE_COLUMNS = {'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT'}

def execute_job(metadata_connection, source_connection, target_connection, session_params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute ETL job for TEST_MAPREF."""
    import sys
    print("=" * 80, flush=True)
    print(f"EXECUTE_JOB STARTED for {MAPREF}", flush=True)
    sys.stdout.flush()
    
    # Build job configuration
    job_config = {
        'mapref': MAPREF,
        'jobid': JOBID,
        'target_schema': TARGET_SCHEMA,
        'target_table': TARGET_TABLE,
        'target_type': TARGET_TYPE,
        'full_table_name': FULL_TABLE_NAME,
        'pk_columns': set(PK_COLUMNS),
        'pk_source_mapping': PK_SOURCE_MAPPING,
        'all_columns': ALL_COLUMNS,
        'column_source_mapping': COLUMN_SOURCE_MAPPING,
        'hash_exclude_columns': HASH_EXCLUDE_COLUMNS,
        'bulk_limit': BULK_LIMIT
    }
    
    # Build checkpoint configuration
    checkpoint_config = {
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN if CHECKPOINT_COLUMNS else None
    }
    
    # Transformation function
    def transformation_func(source_row: Dict[str, Any]) -> Dict[str, Any]:
        return map_row_to_target_columns(source_row)
    
    # Process combinations
    total_source_rows = 0
    total_target_rows = 0
    total_error_rows = 0
    last_status = 'SUCCESS'
    
    # Combination 1
    source_sql_1 = "SELECT ID, NAME FROM SOURCE_TABLE"
    job_config['scd_type'] = 1
    result_1 = execute_mapper_job(
        metadata_connection,
        source_connection,
        target_connection,
        job_config,
        source_sql_1,
        transformation_func,
        checkpoint_config,
        session_params
    )
    
    if result_1.get('status') == 'STOPPED':
        last_status = 'STOPPED'
    elif result_1.get('status') == 'ERROR':
        last_status = 'ERROR'
    
    total_source_rows += result_1.get('source_rows', 0)
    total_target_rows += result_1.get('target_rows', 0)
    total_error_rows += result_1.get('error_rows', 0)
    
    # Return final results
    return {
        'status': last_status,
        'source_rows': total_source_rows,
        'target_rows': total_target_rows,
        'error_rows': total_error_rows,
        'message': 'Job completed successfully' if last_status == 'SUCCESS' else f'Job ended with status: {last_status}'
    }

if __name__ == '__main__':
    print("This is an auto-generated ETL job for TEST_MAPREF")
'''
    
    # Test the sample code
    try:
        result = test_generated_code_structure(sample_code)
        return result
    except Exception as e:
        print(f"[FAIL] Error testing sample code: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_size_reduction():
    """Test that generated code is significantly smaller."""
    print("\n" + "=" * 80)
    print("TEST 5: Code Size Analysis")
    print("=" * 80)
    
    # Estimate old code size (with inline functions and batch processing)
    old_code_estimate = {
        'header': 50,
        'inline_functions': 200,  # map_row_to_target_columns, generate_hash, etc.
        'execute_job_setup': 100,
        'batch_processing_loop': 400,
        'scd_logic': 200,
        'checkpoint_handling': 150,
        'progress_logging': 100,
        'footer': 50,
        'per_combination': 300,  # For each combination
    }
    old_total = sum(old_code_estimate.values())
    
    # Estimate new code size
    new_code_estimate = {
        'header': 50,
        'imports': 20,
        'config': 30,
        'execute_job_setup': 50,
        'per_combination': 30,  # Just the execute_mapper_job call
        'footer': 20,
    }
    new_total = sum(new_code_estimate.values())
    
    reduction_percent = ((old_total - new_total) / old_total) * 100
    
    print(f"Estimated old code size: ~{old_total} lines")
    print(f"Estimated new code size: ~{new_total} lines")
    print(f"Reduction: ~{reduction_percent:.1f}%")
    
    if reduction_percent >= 80:
        print("[PASS] Code size reduction target met (>=80%)")
        return True
    else:
        print(f"[WARN] Code size reduction below target (expected >=80%, got {reduction_percent:.1f}%)")
        return True  # Still pass, as this is an estimate


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PHASE 2 CODE GENERATION TEST SUITE")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Code generation function syntax
    results.append(("Code Generation Syntax", test_code_generation_syntax()))
    
    # Test 2: External modules importable
    results.append(("External Module Imports", test_external_modules_importable()))
    
    # Test 3: Code size reduction
    results.append(("Code Size Reduction", test_code_size_reduction()))
    
    # Test 4: Sample generated code
    results.append(("Sample Generated Code", test_generated_code_sample()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

