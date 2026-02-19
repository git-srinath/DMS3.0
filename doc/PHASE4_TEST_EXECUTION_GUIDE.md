# Phase 4: Test Execution Guide

**Date**: February 16, 2026
**Status**: READY FOR TESTING
**Duration**: 6-8 hours estimated

---

## Quick Start: Phase 4 Testing

This guide walks through Phase 4 testing step-by-step. All test artifacts have been created in the workspace.

### Test Artifacts Created

✅ **Test Documentation**
- `doc/PHASE4_TESTING_PLAN.md` - Comprehensive testing plan with 10 test scenarios

✅ **Test Code**
- `backend/tests/test_phase3_jobs_datatypes.py` - Unit tests for Jobs module
- `backend/tests/test_phase3_integration.py` - Integration tests with real database connections

✅ **SQL Validation**
- `backend/tests/phase3_sql_validation.sql` - 40+ validation queries for PostgreSQL and Oracle

---

## Phase 4 Testing Timeline

### Step 1: Environment Validation (15 minutes)

**Objective**: Verify test environment is ready

**Tasks**:
1. [ ] Verify PostgreSQL metadata database available
2. [ ] Verify PostgreSQL or Oracle target database available
3. [ ] Run DMS_PARAMS validation (Check Step 2 below)
4. [ ] Verify Python test dependencies installed

**Commands**:
```bash
# Check Python environment
python --version  # Should be 3.10+

# Install test dependencies (if needed)
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Verify database connectivity
python -c "
from backend.database.dbconnect import create_metadata_connection
conn = create_metadata_connection()
print('✓ Metadata connection successful')
conn.close()
"
```

---

### Step 2: SQL Validation Queries (20 minutes)

**Objective**: Verify DMS_PARAMS has DBTYP column and proper setup

**Prerequisites**:
- PostgreSQL metadata database running
- SQL client available (psql, DBeaver, SQL*Plus, etc.)

**Execution**:

```bash
# PostgreSQL: Run validation queries
psql -h <host> -U <user> -d <metadata_db> -f backend/tests/phase3_sql_validation.sql

# Oracle: Run validation queries (subset for Oracle client)
sqlplus <user>/<password>@<tnsname> < backend/tests/phase3_sql_validation.sql
```

**Expected Results**:
- Query 1.1/2.1: ✅ DBTYP column found
- Query 1.2/2.2: ✅ Datatype distribution shows POSTGRESQL, ORACLE, GENERIC
- Query 1.3/2.3: ✅ Filtering pattern returns correct datatypes
- Query 1.4/2.4: ✅ GENERIC fallback types available
- Query 1.5-1.9: ✅ All validation checks pass

**If any check fails**:
- [ ] Review DMS_PARAMS table structure
- [ ] Verify DBTYP column exists and has values
- [ ] Check that Phase 3 implementation plan was reviewed
- [ ] Contact development team for database setup issues

---

### Step 3: Unit Testing (15 minutes)

**Objective**: Test Phase 3 code changes in isolation

**Files Tested**:
- `backend/modules/jobs/pkgdwjob_python.py` (create_target_table)
- `backend/modules/jobs/pkgdwjob_create_job_flow.py` (build_job_flow_code)

**Execution**:

```bash
# Run unit tests
cd d:\DMS\DMSTOOL

# Run all Phase 3 unit tests
pytest backend/tests/test_phase3_jobs_datatypes.py -v

# Run specific test class
pytest backend/tests/test_phase3_jobs_datatypes.py::TestPhase3A_CreateTargetTable -v

# Run with coverage report
pytest backend/tests/test_phase3_jobs_datatypes.py --cov=backend/modules/jobs --cov-report=html
```

**Expected Results**:
- ✅ test_postgresql_target_dbtype_detection: PASS
- ✅ test_oracle_target_dbtype_detection: PASS
- ✅ test_fallback_to_generic_on_detection_error: PASS
- ✅ test_combo_details_query_includes_dbtyp_filter: PASS
- ✅ test_datatype_ordering: PASS
- ✅ test_backward_compatibility: PASS

**Troubleshooting**:
```bash
# If tests fail, run with detailed output
pytest backend/tests/test_phase3_jobs_datatypes.py -v -s --tb=short

# Check test imports
python -c "import pytest; print(f'pytest {pytest.__version__}')"
```

---

### Step 4: Integration Testing (60 minutes)

**Objective**: Test Phase 3 changes with actual database connections

**Prerequisites**:
- Metadata database connection working
- Target PostgreSQL database available (or Oracle for full testing)
- Test fixtures created (optional - queries create test data)

**Execution**:

```bash
# Run integration tests
pytest backend/tests/test_phase3_integration.py -v -s

# Run specific test class
pytest backend/tests/test_phase3_integration.py::TestPhase3IntegrationJobs -v

# Run with detailed output for debugging
pytest backend/tests/test_phase3_integration.py -v -s --tb=long
```

**Test Scenarios Covered**:

| Test # | Scenario | Time |
|--------|----------|------|
| 1 | DMS_PARAMS has DBTYP column | 2 min |
| 2 | Datatype distribution validated | 2 min |
| 3 | Filter query returns correct types | 3 min |
| 4 | PostgreSQL table created with PG types | 5 min |
| 5 | File upload uses target_dbtype | 5 min |
| 6 | Default target_dbtype to GENERIC | 5 min |
| 7 | GENERIC types available (backward compat) | 2 min |
| 8 | Query performance < 100ms | 2 min |

**Expected Results**:
```
test_phase3_integration.py::TestPhase3IntegrationJobs::test_verify_dms_params_has_dbtyp_column PASSED
test_phase3_integration.py::TestPhase3IntegrationJobs::test_verify_datatype_distribution_by_dbtype PASSED
test_phase3_integration.py::TestPhase3IntegrationJobs::test_filter_query_returns_correct_types PASSED
test_phase3_integration.py::TestPhase3IntegrationJobs::test_postgres_table_created_with_db_specific_types PASSED
test_phase3_integration.py::TestPhase3IntegrationFileUpload::test_file_upload_uses_target_dbtype_parameter PASSED
test_phase3_integration.py::TestPhase3IntegrationFileUpload::test_default_target_dbtype_to_generic PASSED
test_phase3_integration.py::TestPhase3BackwardCompatibility::test_generic_datatypes_still_available PASSED
test_phase3_integration.py::TestPhase3PerformanceValidation::test_dbtyp_filter_query_performance PASSED

====== 8 passed in 45.23s ======
```

**If tests fail**:
```bash
# Get detailed error information
pytest backend/tests/test_phase3_integration.py::TestName -vv --tb=long

# Check database connection
python -c "
from backend.database.dbconnect import create_metadata_connection, create_target_connection
try:
    meta = create_metadata_connection()
    print('✓ Metadata connection OK')
    meta.close()
except Exception as e:
    print(f'✗ Metadata connection failed: {e}')

try:
    target = create_target_connection(connection_id=1)
    print('✓ Target connection OK')
    target.close()
except Exception as e:
    print(f'✗ Target connection failed: {e}')
"
```

---

### Step 5: Manual Testing (60-90 minutes)

**Objective**: Validate Phase 3 changes in real application workflows

#### Test Scenario 5.1: Jobs Module - PostgreSQL Target

**Preconditions**:
- Test job configured with PostgreSQL target (mapref='TEST_JOB_PG')
- DMS_PARAMS has both POSTGRESQL and GENERIC datatypes
- PostgreSQL target database available

**Steps**:
1. [ ] Navigate to Jobs module
2. [ ] Trigger job execution for TEST_JOB_PG
3. [ ] Monitor job execution logs
4. [ ] Verify log message: "target_dbtype = 'POSTGRESQL' detected"
5. [ ] Check created table schema:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = '<target_table>'
   ORDER BY ordinal_position;
   ```
6. [ ] Verify PostgreSQL datatypes used (INTEGER, VARCHAR, TIMESTAMP, etc.)
7. [ ] Check for no errors in job execution
8. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ Job executes successfully
- ✅ PostgreSQL-specific datatypes in created table
- ✅ Log contains target_dbtype detection message
- ✅ No errors in execution

---

#### Test Scenario 5.2: Jobs Module - Oracle Target

**Preconditions**:
- Test job configured with Oracle target (mapref='TEST_JOB_ORA')
- DMS_PARAMS has both ORACLE and GENERIC datatypes
- Oracle target database available

**Steps**:
1. [ ] Navigate to Jobs module
2. [ ] Trigger job execution for TEST_JOB_ORA
3. [ ] Monitor job execution logs
4. [ ] Verify log message: "target_dbtype = 'ORACLE' detected"
5. [ ] Check created table schema:
   ```sql
   SELECT column_name, data_type 
   FROM user_tab_columns 
   WHERE table_name = '<TARGET_TABLE>'
   ORDER BY column_id;
   ```
6. [ ] Verify Oracle datatypes used (NUMBER, VARCHAR2, DATE, etc.)
7. [ ] Check for no errors
8. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ Job executes successfully
- ✅ Oracle-specific datatypes in created table
- ✅ Log contains target_dbtype detection message
- ✅ No errors in execution

---

#### Test Scenario 5.3: File Upload - PostgreSQL Target

**Preconditions**:
- Sample file ready for upload (CSV with test data)
- File upload configuration with PostgreSQL target
- Column mappings defined
- PostgreSQL target database available

**Steps**:
1. [ ] Navigate to File Upload module
2. [ ] Create/configure file upload (flupldref='TEST_FU_PG')
3. [ ] Upload sample file
4. [ ] Monitor upload logs
5. [ ] Verify log message: "Loaded X data type mappings... for DBTYP=POSTGRESQL"
6. [ ] Check created table schema in PostgreSQL:
   ```sql
   SELECT * FROM information_schema.columns 
   WHERE table_name = '<upload_table>';
   ```
7. [ ] Verify PostgreSQL datatypes used
8. [ ] Load data into target table
9. [ ] Verify all data loaded successfully
10. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ File uploaded successfully
- ✅ PostgreSQL datatypes in created table
- ✅ Data loaded correctly
- ✅ No schema mismatch errors

---

#### Test Scenario 5.4: Mapper Module - SQL Column Extraction

**Preconditions**:
- Mapper module accessible
- Sample SQL available for extraction
- target_dbtype parameter support available

**Steps**:
1. [ ] Navigate to Mapper SQL extraction endpoint
2. [ ] Provide SQL content to extract
3. [ ] **WITH target_dbtype**: Include target_dbtype='POSTGRESQL'
4. [ ] Verify response includes datatype suggestions
5. [ ] Check for PostgreSQL-specific types in suggestions
6. [ ] **WITHOUT target_dbtype**: Retry without target_dbtype parameter
7. [ ] Verify response includes all available types
8. [ ] Compare suggestions: with vs without target_dbtype
9. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ Extraction works with target_dbtype parameter
- ✅ Extraction works without target_dbtype (backward compatible)
- ✅ Suggestions appropriate for target database
- ✅ No errors

---

#### Test Scenario 5.5: Backward Compatibility - Legacy Job

**Preconditions**:
- Legacy job using GENERIC datatypes only (no target DB type)
- GENERIC datatypes available in DMS_PARAMS
- Target database (any type)

**Steps**:
1. [ ] Execute legacy job (no changes to configuration)
2. [ ] Monitor job execution
3. [ ] Verify execution completes successfully
4. [ ] Check that GENERIC datatypes used
5. [ ] Verify no errors or warnings
6. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ Legacy job executes without modification
- ✅ GENERIC datatypes used as fallback
- ✅ No breaking changes
- ✅ Table created successfully

---

### Step 6: Performance Testing (20 minutes)

**Objective**: Verify Phase 3 doesn't degrade performance

**Baseline**: Measure execution times before Phase 3 changes (if available)

**Tests**:

#### Test 6.1: Query Performance

```bash
# Run SQL validation query with timing
# PostgreSQL:
psql -h <host> -U <user> -d <db> -c "
EXPLAIN ANALYZE
SELECT prcd, prval, dbtyp
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'POSTGRESQL' OR dbtyp = 'GENERIC')
ORDER BY CASE WHEN dbtyp='POSTGRESQL' THEN 1 ELSE 2 END;"
```

**Expected Result**:
- Planning time: < 5ms
- Execution time: < 10ms per 1000 rows
- Total time: < 100ms

#### Test 6.2: Job Execution Time

**Steps**:
1. [ ] Execute Phase 3 job and record total time
2. [ ] Compare with baseline (if available)
3. [ ] Calculate difference: (Phase3 - Baseline) / Baseline * 100
4. [ ] Verify difference < 5% OR new execution time < 2 seconds
5. [ ] Mark as ✓ PASS or ✗ FAIL

**Expected Result**:
- ✅ Phase 3 execution time within 5% of baseline
- ✅ Additional database query adds < 100ms overhead
- ✅ Overall performance acceptable

---

## Test Results Documentation

### Create Test Results Report

Create file: `doc/PHASE4_TEST_RESULTS.md`

```markdown
# Phase 4: Test Results Report

**Date**: February 16, 2026
**Tester**: [Your Name]
**Duration**: [Total Testing Hours]

## Test Execution Summary

| Test Type | Count | Passed | Failed | Status |
|-----------|-------|--------|--------|--------|
| SQL Validation | 40 | [ ] | [ ] | [ ] |
| Unit Tests | 12 | [ ] | [ ] | [ ] |
| Integration Tests | 8 | [ ] | [ ] | [ ] |
| Manual Tests | 5 | [ ] | [ ] | [ ] |
| Performance Tests | 3 | [ ] | [ ] | [ ] |
| **TOTAL** | **68** | [ ] | [ ] | [ ] |

## Issues Found

| ID | Module | Severity | Description | Status |
|----|--------|----------|-------------|--------|
| [ID] | [Module] | [Critical/High/Medium/Low] | [Description] | [Open/Resolved] |

## Recommendations

[Any recommendations from testing]

## Sign-Off

- Tester: _______________________
- Date: _______________________
- Status: [ ] PASS  [ ] PASS WITH ISSUES  [ ] FAIL
```

---

## Troubleshooting Guide

### Issue: Database Connection Failed

**Solution**:
```bash
# Verify environment variables
echo $DATABASE_URL  # Should show database connection string

# Test connection directly
python -c "
from backend.database.dbconnect import create_metadata_connection
try:
    conn = create_metadata_connection()
    print('Connection successful')
    conn.close()
except Exception as e:
    print(f'Connection failed: {e}')
"
```

### Issue: DBTYP Column Not Found

**Solution**:
```sql
-- Check DMS_PARAMS structure
SELECT * FROM dms_params LIMIT 0;  -- Shows schema

-- If DBTYP column missing, run migration:
-- (Contact development team for migration script)
```

### Issue: Tests Can't Import Modules

**Solution**:
```bash
# Ensure working directory is correct
cd d:\DMS\DMSTOOL

# Verify Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Re-run tests
pytest backend/tests/test_phase3_*.py -v
```

---

## Sign-Off

**Phase 4 Testing Status**: [TO BE FILLED]

- [ ] All SQL validation queries pass
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All manual test scenarios pass
- [ ] Performance testing completed
- [ ] No critical issues found
- [ ] Ready for Phase 5 deployment

**Tester Name**: ________________________
**Date Completed**: ________________________
**Overall Result**: [ ] ✅ PASS  [ ] ✅ PASS WITH MINOR ISSUES  [ ] ❌ FAIL

---

## Next Steps (Phase 5)

Upon successful Phase 4 completion:

1. ✅ Review test results
2. ✅ Resolve any issues found
3. ✅ Obtain code review approval
4. ✅ Prepare deployment documentation
5. ✅ Schedule Phase 5 deployment
6. ✅ Deploy to production
7. ✅ Monitor in production

---

**Document Version**: 1.0
**Last Updated**: February 16, 2026
**Status**: READY FOR TESTING

