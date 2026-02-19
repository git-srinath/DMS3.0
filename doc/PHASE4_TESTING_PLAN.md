# Phase 4: Comprehensive Testing & Validation Plan

**Status**: IN PROGRESS
**Date Started**: February 16, 2026
**Estimated Duration**: 6-8 hours
**Scope**: Validate all Phase 3 changes across Jobs, File Upload, and Mapper modules

---

## Phase 4 Objectives

1. ✅ Create comprehensive test infrastructure
2. ✅ Validate Phase 3 code changes work correctly
3. ✅ Ensure backward compatibility with existing systems
4. ✅ Test across multiple database types (PostgreSQL, Oracle)
5. ✅ Document test results and findings
6. ✅ Identify and fix any issues before deployment

---

## Testing Methodology

### Test Categories

| Category | Purpose | Location | Status |
|----------|---------|----------|--------|
| **Unit Tests** | Test individual Phase 3 functions in isolation | `backend/modules/*/tests/` | ⏳ WIP |
| **Integration Tests** | Test Phase 3 changes in realistic workflows | `backend/tests/phase3_integration_tests.py` | ⏳ WIP |
| **SQL Validation** | Verify DMS_PARAMS queries work correctly | SQL scripts + queries | ⏳ READY |
| **Regression Tests** | Ensure existing functionality unchanged | Test scripts | ⏳ READY |
| **Database Compatibility** | Test with PostgreSQL and Oracle | Multi-DB scripts | ⏳ READY |

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Ensure test databases are available
PostgreSQL: Available with metadata DMS setup
Oracle: Available with metadata DMS setup (if applicable)

# 2. Create test fixtures (if needed)
- Sample jobs with different target databases
- Sample file uploads with column mappings
- Sample mapper configurations

# 3. Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### Test Data Requirements

**Minimum Test Scenario**:
- ✅ Job with PostgreSQL target
- ✅ Job with Oracle target
- ✅ File upload to PostgreSQL table
- ✅ File upload to Oracle table
- ✅ Mapper SQL extraction with target_dbtype

---

## Detailed Test Scenarios

### Test Scenario 1: Jobs Module - PostgreSQL Target

**Test Case**: Phase 3A - create_target_table with PostgreSQL target

**Preconditions**:
```
- DMS_JOB with mapref='TEST_JOB_PG'
- DMS_DBCONNECT with DBTYP='POSTGRESQL'
- DMS_PARAMS has both POSTGRESQL and GENERIC datatypes
- Target PostgreSQL database available
```

**Test Steps**:
1. Call `create_target_table()` with test job mapping to PostgreSQL target
2. Verify target database type detected correctly (should be 'POSTGRESQL')
3. Verify query includes `(p.dbtyp = %s OR p.dbtyp = 'GENERIC')`
4. Verify returned datatypes include PostgreSQL-specific types first
5. Verify table created in PostgreSQL with correct datatypes

**Expected Result** ✅:
- Logger shows: `target_dbtype = 'POSTGRESQL'` detected
- Query executed with DBTYP filter
- Table created with PostgreSQL datatypes (e.g., `INTEGER`, `TEXT`, `TIMESTAMP`)

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 2: Jobs Module - Oracle Target

**Test Case**: Phase 3A - create_target_table with Oracle target

**Preconditions**:
```
- DMS_JOB with mapref='TEST_JOB_ORA'
- DMS_DBCONNECT with DBTYP='ORACLE'
- DMS_PARAMS has both ORACLE and GENERIC datatypes
- Target Oracle database available
```

**Test Steps**:
1. Call `create_target_table()` with test job mapping to Oracle target
2. Verify target database type detected correctly (should be 'ORACLE')
3. Verify Oracle-specific query syntax with `:dbtyp` parameter
4. Verify returned datatypes include Oracle-specific types first
5. Verify table created in Oracle with correct datatypes

**Expected Result** ✅:
- Logger shows: `target_dbtype = 'ORACLE'` detected
- Query executed with DBTYP filter (Oracle syntax)
- Table created with Oracle datatypes (e.g., `NUMBER`, `VARCHAR2`, `DATE`)

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 3: Jobs Module - Fallback to GENERIC

**Test Case**: Phase 3A - create_target_table with unknown database type

**Preconditions**:
```
- DMS_JOB with mapref='TEST_JOB_UNKNOWN'
- DMS_DBCONNECT has NULL or invalid DBTYP
- DMS_PARAMS has only GENERIC datatypes
```

**Test Steps**:
1. Call `create_target_table()` with job having invalid/NULL target DBTYP
2. Verify fallback to 'GENERIC' occurs
3. Verify warning logged about fallback
4. Verify query executes successfully with GENERIC filter
5. Verify table created with generic datatypes

**Expected Result** ✅:
- Logger shows: "Warning: Could not determine target database type, using GENERIC"
- Query executes with `(p.dbtyp = 'GENERIC' OR p.dbtyp = 'GENERIC')`
- Table created successfully with generic datatypes

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 4: Jobs Module - build_job_flow_code

**Test Case**: Phase 3B - build_job_flow_code with DBTYP filtering

**Preconditions**:
```
- DMS_JOB with jobid=1001, target=PostgreSQL
- DMS_JOBDTL with multiple combinations
- DMS_PARAMS with PostgreSQL and GENERIC types
```

**Test Steps**:
1. Call `build_job_flow_code()` for test job
2. Verify target database type detected before combinations loop
3. Verify combo_details query includes DBTYP filter
4. Verify generated Python code uses correct datatypes for PostgreSQL
5. Verify ordering: PostgreSQL types first, GENERIC as fallback

**Expected Result** ✅:
- Logger shows target_dbtype detected
- Generated code includes PostgreSQL-appropriate datatype handling
- No errors during code generation

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 5: File Upload - PostgreSQL Target

**Test Case**: Phase 3C - create_table_if_not_exists with PostgreSQL

**Preconditions**:
```
- File upload configuration with PostgreSQL target
- Column mappings defined
- Metadata connection available
```

**Test Steps**:
1. Call `create_table_if_not_exists()` with PostgreSQL connection and mappings
2. Verify _detect_db_type returns 'POSTGRESQL'
3. Verify _resolve_data_types filters by target_dbtype='POSTGRESQL'
4. Verify logger shows count of loaded PostgreSQL datatypes
5. Verify table created with correct PostgreSQL datatypes

**Expected Result** ✅:
- Logger: `"Loaded X data type mappings from DMS_PARAMS (metadata DB - PostgreSQL) for DBTYP=POSTGRESQL"`
- Table exists with correct structure
- Columns use PostgreSQL datatypes

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 6: File Upload - Oracle Target

**Test Case**: Phase 3C - create_table_if_not_exists with Oracle

**Preconditions**:
```
- File upload configuration with Oracle target
- Column mappings defined
- Metadata connection available
```

**Test Steps**:
1. Call `create_table_if_not_exists()` with Oracle connection and mappings
2. Verify _detect_db_type returns 'ORACLE'
3. Verify _resolve_data_types filters by target_dbtype='ORACLE'
4. Verify logger shows count of loaded Oracle datatypes
5. Verify table created with correct Oracle datatypes

**Expected Result** ✅:
- Logger: `"Loaded X data type mappings from DMS_PARAMS (metadata DB - Oracle) for DBTYP=ORACLE"`
- Table exists with correct structure
- Columns use Oracle datatypes

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 7: Mapper - With target_dbtype

**Test Case**: Phase 3D - extract_sql_columns with target_dbtype

**Preconditions**:
```
- SQL code/content available for extraction
- Metadata connection available
- target_dbtype='POSTGRESQL'
```

**Test Steps**:
1. Call extract_sql_columns endpoint with target_dbtype='POSTGRESQL'
2. Verify target_dbtype extracted from request
3. Verify get_parameter_mapping_datatype_for_db called (not fallback)
4. Verify logger shows: "Loaded X datatype options for target DBTYPE=POSTGRESQL"
5. Verify suggested_data_type_options include PostgreSQL types

**Expected Result** ✅:
- Endpoint returns filtered datatype suggestions
- Logger shows target DB type was used
- Suggestions appropriate for PostgreSQL

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 8: Mapper - Without target_dbtype (Fallback)

**Test Case**: Phase 3D - extract_sql_columns without target_dbtype

**Preconditions**:
```
- SQL code/content available
- Metadata connection available
- target_dbtype NOT provided
```

**Test Steps**:
1. Call extract_sql_columns endpoint WITHOUT target_dbtype parameter
2. Verify no target_dbtype in request data
3. Verify get_parameter_mapping_datatype called (all types)
4. Verify logger shows: "Loaded X datatype options (no target DB type specified)"
5. Verify suggested types include all database types

**Expected Result** ✅:
- Endpoint returns all datatype suggestions
- Logger shows fallback behavior
- All types returned (GENERIC + all databases)

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 9: Backward Compatibility - Old Code

**Test Case**: Existing code without Phase 3 changes still works

**Preconditions**:
```
- Legacy jobs configured with GENERIC only
- No target DBTYP specified
- GENERIC datatypes available in DMS_PARAMS
```

**Test Steps**:
1. Execute legacy job that doesn't use target database types
2. Verify GENERIC datatypes still returned
3. Verify table/code generated successfully
4. Verify no errors from unexpected NULL DBTYP values

**Expected Result** ✅:
- Legacy jobs execute without modification
- GENERIC types returned as fallback
- No breaking changes

**Actual Result**: [TO BE FILLED DURING TESTING]

---

### Test Scenario 10: Performance - No Degradation

**Test Case**: Phase 3 changes don't negatively impact performance

**Preconditions**:
```
- Large job with 100+ columns
- Complex combination logic
- Multiple file uploads
```

**Test Steps**:
1. Measure execution time before Phase 3 (baseline)
2. Measure execution time after Phase 3
3. Compare: < 5% increase acceptable
4. Verify additional query (target type detection) adds minimal overhead
5. Monitor memory usage

**Expected Result** ✅:
- Execution time within 5% of baseline
- Additional query completes in < 100ms
- Memory usage unchanged

**Actual Result**: [TO BE FILLED DURING TESTING]

---

## SQL Validation Queries

### Query 1: Verify DMS_PARAMS has DBTYP column

**PostgreSQL**:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'dms_params'
  AND column_name LIKE '%dbtyp%'
ORDER BY column_name;
```

**Expected Result**: DBTYP column exists and contains database type values

**Oracle**:
```sql
SELECT column_name, data_type
FROM user_tab_columns
WHERE table_name = 'DMS_PARAMS'
  AND column_name LIKE '%DBTYP%'
ORDER BY column_name;
```

---

### Query 2: Verify Datatype Distribution by DBTYP

**PostgreSQL**:
```sql
SELECT 
    dbtyp,
    COUNT(*) as datatype_count,
    STRING_AGG(DISTINCT prcd, ', ' ORDER BY prcd) as included_types
FROM dms_params
WHERE prtyp = 'Datatype'
GROUP BY dbtyp
ORDER BY dbtyp;
```

**Expected Result**: Shows distribution of datatypes across POSTGRESQL, ORACLE, GENERIC

**Oracle**:
```sql
SELECT 
    dbtyp,
    COUNT(*) as datatype_count,
    LISTAGG(DISTINCT prcd, ', ') WITHIN GROUP (ORDER BY prcd) as included_types
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
GROUP BY DBTYP
ORDER BY DBTYP;
```

---

### Query 3: Test Filtering by DBTYP

**PostgreSQL**:
```sql
-- Should return PostgreSQL types + GENERIC as fallback
SELECT prcd, prval, dbtyp
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'POSTGRESQL' OR dbtyp = 'GENERIC')
ORDER BY dbtyp DESC NULLS LAST, prcd
LIMIT 20;
```

**Expected Result**: PostgreSQL types first, then GENERIC types

**Oracle**:
```sql
-- Should return Oracle types + GENERIC as fallback
SELECT PRCD, PRVAL, DBTYP
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
  AND (DBTYP = 'ORACLE' OR DBTYP = 'GENERIC')
ORDER BY DBTYP DESC, PRCD
FETCH FIRST 20 ROWS ONLY;
```

---

### Query 4: Verify Table Created with Correct Datatypes

**PostgreSQL Target**:
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_schema = '<schema>'
  AND table_name = '<test_table>'
ORDER BY ordinal_position;
```

**Expected Result**: Shows PostgreSQL-style datatypes (INTEGER, VARCHAR, TIMESTAMP, etc.)

**Oracle Target**:
```sql
SELECT 
    column_name,
    data_type,
    data_length,
    data_precision,
    data_scale
FROM user_tab_columns
WHERE table_name = '<test_table>'
ORDER BY column_id;
```

**Expected Result**: Shows Oracle-style datatypes (NUMBER, VARCHAR2, DATE, etc.)

---

## Test Execution Scripts

### Script 1: Unit Test for Phase 3A

**File**: `backend/tests/test_phase3a_jobs_datatypes.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.modules.jobs.pkgdwjob_python import create_target_table

class TestPhase3A_CreateTargetTable:
    """Test Phase 3A: create_target_table with DBTYP filtering"""
    
    def test_postgres_target_datatype_detection(self):
        """Verify PostgreSQL target datatypes are used"""
        # Mock connections and cursors
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        
        # Mock database type detection
        with patch('backend.modules.jobs.pkgdwjob_python._detect_db_type', return_value='POSTGRESQL'):
            # Mock target DB type detection from DMS_DBCONNECT
            cursor.fetchone.side_effect = [
                ('POSTGRESQL',),  # First query: target_dbtype
                # ... additional mock results
            ]
            
            # Call function
            result = create_target_table(
                connection, 'test_mapref', 'test_schema', 'test_table'
            )
            
            # Verify DBTYP filter was applied
            sql_calls = cursor.execute.call_args_list
            assert any('dbtyp' in str(call).lower() for call in sql_calls), \
                "DBTYP filter not found in executed queries"
    
    def test_oracle_target_datatype_detection(self):
        """Verify Oracle target datatypes are used"""
        # Test for Oracle database type detection
        # Similar structure to PostgreSQL test above
        pass
    
    def test_fallback_to_generic_on_detection_failure(self):
        """Verify fallback to GENERIC when target detection fails"""
        # Test exception handling and fallback logic
        pass
    
    def test_backward_compatibility_generic_only(self):
        """Verify GENERIC datatypes still work without target type"""
        # Test systems using GENERIC only still function
        pass

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
```

---

### Script 2: Integration Test for Phase 3 End-to-End

**File**: `backend/tests/test_phase3_integration.py`

```python
import pytest
from backend.database.dbconnect import (
    create_metadata_connection,
    create_target_connection
)
from backend.modules.jobs.pkgdwjob_python import create_target_table
from backend.modules.file_upload.table_creator import create_table_if_not_exists

class TestPhase3Integration:
    """Integration tests for Phase 3 changes across modules"""
    
    @pytest.fixture
    def metadata_conn(self):
        """Create metadata connection for testing"""
        conn = create_metadata_connection()
        yield conn
        conn.close()
    
    @pytest.fixture
    def postgres_target_conn(self):
        """Create PostgreSQL target connection"""
        conn = create_target_connection(connection_id=1)  # Adjust ID
        yield conn
        conn.close()
    
    def test_job_to_postgres_table_creation(self, metadata_conn, postgres_target_conn):
        """Test: Job execution creates table with PostgreSQL datatypes"""
        # 1. Execute job that creates table
        result = create_target_table(
            postgres_target_conn,
            'TEST_MAPREF',
            'public',
            'test_table_phase3'
        )
        
        # 2. Verify table was created
        assert result, "Table creation failed"
        
        # 3. Query created table schema
        cursor = postgres_target_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'test_table_phase3'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        # 4. Verify PostgreSQL datatypes used
        datatypes = [col[1] for col in columns]
        assert len(datatypes) > 0, "No columns found in created table"
        
        # Check for PostgreSQL-specific types (not Oracle types)
        pg_types = ['integer', 'character varying', 'timestamp', 'text']
        assert any(dt.lower() in pg_types for dt in datatypes), \
            f"PostgreSQL datatypes not found. Got: {datatypes}"
        
        cursor.close()
    
    def test_file_upload_respects_target_dbtype(self, metadata_conn, postgres_target_conn):
        """Test: File upload creates table with correct target datatypes"""
        column_mappings = [
            {'trgclnm': 'ID', 'trgcldtyp': 'INTEGER', 'trgkeyflg': 'Y'},
            {'trgclnm': 'NAME', 'trgcldtyp': 'VARCHAR', 'trgkeyflg': 'N'},
        ]
        
        result = create_table_if_not_exists(
            postgres_target_conn,
            'public',
            'upload_test_table',
            column_mappings,
            metadata_conn,
            target_dbtype='POSTGRESQL'
        )
        
        assert result, "Table creation failed"
        
        # Verify correct datatypes in created table
        cursor = postgres_target_conn.cursor()
        cursor.execute("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'upload_test_table'
        """)
        result_types = cursor.fetchall()
        assert len(result_types) > 0, "Table not created correctly"
        cursor.close()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
```

---

## Test Execution Instructions

### Run Phase 3 Tests

```bash
# Navigate to project root
cd d:\DMS\DMSTOOL

# Run all Phase 3 tests
pytest backend/tests/test_phase3*.py -v

# Run specific test module
pytest backend/tests/test_phase3a_jobs_datatypes.py -v

# Run with coverage report
pytest backend/tests/test_phase3*.py --cov=backend/modules --cov-report=html

# Run integration tests only
pytest backend/tests/test_phase3_integration.py -v -m integration
```

---

## Validation Checklist

### Pre-Testing

- [ ] All Phase 3 code changes committed
- [ ] Test environment configured (PostgreSQL + Oracle available)
- [ ] Test data prepared (sample jobs, file uploads)
- [ ] DMS_PARAMS table has DBTYP column and values
- [ ] Metadata connection working
- [ ] Target connections working (PostgreSQL + Oracle)

### During Testing

- [ ] Each test scenario executed in sequence
- [ ] Results recorded in this document
- [ ] Any failures investigated and root causes identified
- [ ] Screenshots/logs captured for evidence

### Post-Testing

- [ ] All test scenarios passed
- [ ] No regression issues found
- [ ] Performance acceptable (< 5% change)
- [ ] Backward compatibility verified
- [ ] Test results documented

---

## Test Results Summary

### Jobs Module Tests

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 1 | PostgreSQL target datatype detection | ⏳ PENDING | |
| 2 | Oracle target datatype detection | ⏳ PENDING | |
| 3 | Fallback to GENERIC | ⏳ PENDING | |
| 4 | build_job_flow_code DBTYP filtering | ⏳ PENDING | |

### File Upload Module Tests

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 5 | PostgreSQL target table creation | ⏳ PENDING | |
| 6 | Oracle target table creation | ⏳ PENDING | |

### Mapper Module Tests

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 7 | Extract SQL with target_dbtype | ⏳ PENDING | |
| 8 | Extract SQL without target_dbtype | ⏳ PENDING | |

### Cross-Cutting Tests

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 9 | Backward compatibility | ⏳ PENDING | |
| 10 | Performance impact | ⏳ PENDING | |

---

## Issue Tracking

### Found During Testing

| Issue ID | Module | Severity | Description | Status |
|----------|--------|----------|-------------|--------|
| P4-001 | [TBD] | [TBD] | [TBD] | ⏳ TBD |

---

## Sign-Off

**Test Execution Started**: [TO BE FILLED]
**Test Execution Completed**: [TO BE FILLED]
**Overall Status**: [TO BE FILLED - PASS/FAIL]
**Tester**: [TO BE FILLED]
**Reviewer**: [TO BE FILLED]

---

## Appendix: Reference Information

### Phase 3 Changes Summary
- Jobs: 2 functions enhanced (create_target_table, build_job_flow_code)
- File Upload: 3 files updated (_resolve_data_types enhanced, 2 callers updated)
- Mapper: 1 endpoint enhanced (extract_sql_columns with target_dbtype)
- Reports: No changes needed

### Key SQL Patterns Used
- Filter: `(DBTYP = :value OR DBTYP = 'GENERIC')`
- Order: `ORDER BY DBTYP DESC [NULLS LAST]`
- Default: `'GENERIC'` when target type unavailable

### Database Type Values
- POSTGRESQL
- ORACLE
- SNOWFLAKE (future)
- GENERIC (fallback for all)

---

**Document Version**: 1.0
**Last Updated**: February 16, 2026
**Status**: READY FOR TESTING
