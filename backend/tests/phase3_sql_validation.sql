-- ============================================================================
-- Phase 4: SQL Validation Queries for Phase 3 DBTYP Filtering
-- ============================================================================
-- Purpose: Verify that DMS_PARAMS has DBTYP column and datatype distribution
--          is correct for Phase 3 implementation.
-- 
-- Usage: Run these queries in PostgreSQL and Oracle to validate setup
-- ============================================================================

-- ============================================================================
-- SECTION 1: POSTGRESQL VALIDATION QUERIES
-- ============================================================================

-- Query 1.1: Verify DBTYP column exists in dms_params
-- Expected: Should return one row with column_name='dbtyp' (case-insensitive match)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'dms_params'
  AND column_name ILIKE '%dbtyp%'
ORDER BY column_name;

-- Expected result sample:
-- column_name | data_type | is_nullable
-- -----------+-----------+------------
-- dbtyp       | character | true

---

-- Query 1.2: Verify datatype distribution across DBTYP values
-- Expected: Shows how many datatypes available for each database type
SELECT 
    COALESCE(dbtyp, 'NULL') as database_type,
    COUNT(*) as datatype_count,
    string_agg(DISTINCT prcd, ', ' ORDER BY prcd) as included_types
FROM dms_params
WHERE prtyp = 'Datatype'
GROUP BY dbtyp
ORDER BY database_type;

-- Expected result sample:
-- database_type | datatype_count | included_types
-- --------------|----------------|--------------------------------------------
-- GENERIC       | 8              | DATE, DECIMAL, INTEGER, TIMESTAMP, ...
-- ORACLE        | 12             | DATE, INTERVAL DAY, NUMBER, TIMESTAMP, ...
-- POSTGRESQL    | 10             | BIGINT, DECIMAL, INTEGER, JSON, ...

---

-- Query 1.3: Test the Phase 3 filtering pattern for PostgreSQL
-- This is the exact query pattern used in Phase 3A/3B code
-- Expected: Should return PostgreSQL datatypes first, then GENERIC as fallback
SELECT 
    prcd, 
    prval, 
    dbtyp,
    CASE WHEN dbtyp='POSTGRESQL' THEN 1 WHEN dbtyp='GENERIC' THEN 2 ELSE 3 END as priority
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'POSTGRESQL' OR dbtyp = 'GENERIC')
ORDER BY CASE WHEN dbtyp='POSTGRESQL' THEN 1 ELSE 2 END, prcd
LIMIT 20;

-- Expected result sample (PostgreSQL types first):
-- prcd        | prval              | dbtyp      | priority
-- ------------|--------------------|-----------+----------
-- BIGINT      | BIGINT             | POSTGRESQL | 1
-- DATE        | DATE               | POSTGRESQL | 1
-- DECIMAL     | DECIMAL(18,2)      | POSTGRESQL | 1
-- INTEGER     | INTEGER            | POSTGRESQL | 1
-- JSON        | JSON               | POSTGRESQL | 1
-- TIMESTAMP   | TIMESTAMP          | POSTGRESQL | 1
-- VARCHAR     | VARCHAR(255)       | POSTGRESQL | 1
-- DATE        | DATE               | GENERIC    | 2
-- DECIMAL     | DECIMAL(18,2)      | GENERIC    | 2
-- INTEGER     | INTEGER            | GENERIC    | 2

---

-- Query 1.4: Test filtering for Oracle datatypes with GENERIC fallback
-- Expected: Oracle types prioritized over GENERIC
SELECT 
    prcd, 
    prval, 
    dbtyp
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'ORACLE' OR dbtyp = 'GENERIC')
ORDER BY CASE WHEN dbtyp='ORACLE' THEN 1 ELSE 2 END, prcd
LIMIT 20;

-- Expected result sample (Oracle types first):
-- prcd             | prval              | dbtyp
-- -----------------|--------------------|----------
-- BLOB             | BLOB               | ORACLE
-- CHAR             | CHAR(100)          | ORACLE
-- CLOB             | CLOB               | ORACLE
-- DATE             | DATE               | ORACLE
-- NUMBER           | NUMBER(10)         | ORACLE
-- TIMESTAMP        | TIMESTAMP(6)       | ORACLE
-- VARCHAR2         | VARCHAR2(255)      | ORACLE
-- DATE             | DATE               | GENERIC
-- DECIMAL          | DECIMAL(18,2)      | GENERIC
-- INTEGER          | INTEGER            | GENERIC

---

-- Query 1.5: Verify GENERIC datatypes available as fallback
-- Critical for backward compatibility
-- Expected: Should return at least 5-10 GENERIC types
SELECT COUNT(*) as generic_datatype_count
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'GENERIC' OR dbtyp IS NULL);

-- Expected: generic_datatype_count = [8 or more]

---

-- Query 1.6: Verify all required database types have entries
-- Expected: Should show POSTGRESQL, ORACLE, SNOWFLAKE (optional), and GENERIC
SELECT DISTINCT dbtyp
FROM dms_params
WHERE prtyp = 'Datatype'
ORDER BY dbtyp;

-- Expected result:
-- dbtyp
-- -----------
-- GENERIC
-- ORACLE
-- POSTGRESQL

---

-- Query 1.7: Check for any duplicate datatype definitions per DBTYP
-- Expected: Should return no rows (no duplicates)
SELECT prcd, dbtyp, COUNT(*) as count
FROM dms_params
WHERE prtyp = 'Datatype'
GROUP BY prcd, dbtyp
HAVING COUNT(*) > 1
ORDER BY prcd;

-- Expected: No rows returned (no duplicates)

---

-- Query 1.8: Verify table structure matches expectations
-- Expected: Shows all columns in dms_params including DBTYP, PRCD, PRVAL, PRTYP
SELECT 
    column_name,
    data_type,
    is_nullable,
    ordinal_position
FROM information_schema.columns
WHERE table_name = 'dms_params'
ORDER BY ordinal_position;

-- Expected columns include: PRCD, PRDESC, PRVAL, PRTYP, DBTYP

---

-- Query 1.9: Count total datatypes available (all types)
-- Useful for regression testing
SELECT COUNT(*) as total_datatype_entries
FROM dms_params
WHERE prtyp = 'Datatype';

-- Expected: [20 or more] entries

---

-- Query 1.10: Performance test - DBTYP filter query execution time
-- Run this to ensure Phase 3 queries don't degrade performance
-- Expected: Query should complete in <100ms
EXPLAIN ANALYZE
SELECT prcd, prval, dbtyp
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (dbtyp = 'POSTGRESQL' OR dbtyp = 'GENERIC')
ORDER BY CASE WHEN dbtyp='POSTGRESQL' THEN 1 ELSE 2 END;

-- Expected: Planning Time: <5ms, Execution Time: <10ms

---

-- ============================================================================
-- SECTION 2: ORACLE VALIDATION QUERIES
-- ============================================================================

-- Query 2.1: Verify DBTYP column exists in DMS_PARAMS
-- Expected: Should return one row
SELECT column_name, data_type
FROM user_tab_columns
WHERE table_name = 'DMS_PARAMS'
  AND UPPER(column_name) LIKE '%DBTYP%'
ORDER BY column_name;

-- Expected result:
-- COLUMN_NAME | DATA_TYPE
-- ------------|----------
-- DBTYP       | VARCHAR2

---

-- Query 2.2: Verify datatype distribution across DBTYP values (Oracle)
-- Expected: Shows distribution of datatypes
SELECT 
    COALESCE(DBTYP, 'NULL') as DATABASE_TYPE,
    COUNT(*) as DATATYPE_COUNT,
    LISTAGG(DISTINCT PRCD, ', ') WITHIN GROUP (ORDER BY PRCD) as INCLUDED_TYPES
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
GROUP BY DBTYP
ORDER BY DATABASE_TYPE;

-- Expected output format:
-- DATABASE_TYPE | DATATYPE_COUNT | INCLUDED_TYPES
-- --------------|----------------|--------------------------------------------
-- GENERIC       | 8              | DATE, DECIMAL, INTEGER, TIMESTAMP, ...
-- ORACLE        | 12             | DATE, INTERVAL, NUMBER, TIMESTAMP, ...

---

-- Query 2.3: Test Phase 3 filtering pattern for Oracle
-- This query pattern is used in Phase 3A/3B Oracle code
-- Expected: Oracle types first, GENERIC as fallback
SELECT 
    PRCD, 
    PRVAL, 
    DBTYP
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
  AND (DBTYP = 'ORACLE' OR DBTYP = 'GENERIC')
ORDER BY DBTYP DESC, PRCD
FETCH FIRST 20 ROWS ONLY;

-- Expected result (Oracle types first):
-- PRCD        | PRVAL              | DBTYP
-- ------------|--------------------|-----------
-- BLOB        | BLOB               | ORACLE
-- CHAR        | CHAR(100)          | ORACLE
-- DATE        | DATE               | ORACLE
-- NUMBER      | NUMBER(10)         | ORACLE
-- TIMESTAMP   | TIMESTAMP(6)       | ORACLE
-- VARCHAR2    | VARCHAR2(255)      | ORACLE
-- DATE        | DATE               | GENERIC
-- DECIMAL     | DECIMAL(18,2)      | GENERIC
-- INTEGER     | INTEGER            | GENERIC

---

-- Query 2.4: Verify GENERIC fallback availability
-- Expected: Should return count of GENERIC types
SELECT COUNT(*) as GENERIC_DATATYPE_COUNT
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
  AND (DBTYP = 'GENERIC' OR DBTYP IS NULL);

-- Expected: Count = [8 or more]

---

-- Query 2.5: List all unique database types
-- Expected: GENERIC, ORACLE, POSTGRESQL, and others
SELECT DISTINCT DBTYP
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
ORDER BY DBTYP;

-- Expected results:
-- DBTYP
-- -----------
-- GENERIC
-- ORACLE
-- POSTGRESQL

---

-- Query 2.6: Check execution plan for DBTYP filter
-- Expected: Should show efficient plan (no full table scans if indexed)
EXPLAIN PLAN FOR
SELECT PRCD, PRVAL, DBTYP
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
  AND (DBTYP = 'ORACLE' OR DBTYP = 'GENERIC')
ORDER BY DBTYP DESC;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY());

-- Expected: Should use index on (PRTYP, DBTYP) if available

---

-- ============================================================================
-- SECTION 3: POST-TABLE-CREATION VALIDATION (for actual Phase 3 testing)
-- ============================================================================

-- Query 3.1: Verify table created with PostgreSQL datatypes (PostgreSQL target)
-- Run after Phase 3A job creates table in PostgreSQL
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'test_phase3_table'
ORDER BY ordinal_position;

-- Expected columns with PostgreSQL datatypes:
-- Example for ID column (INTEGER):
--   column_name | data_type | chr_max_len | num_prec | num_scale
--   ------------|-----------|-------------|----------|----------
--   ID          | integer   |             | 32       |

---

-- Query 3.2: Verify table created with Oracle datatypes (Oracle target)
-- Run after Phase 3A job creates table in Oracle
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH,
    DATA_PRECISION,
    DATA_SCALE
FROM user_tab_columns
WHERE table_name = 'TEST_PHASE3_TABLE'
ORDER BY column_id;

-- Expected columns with Oracle datatypes:
-- Example for ID column (NUMBER):
--   COLUMN_NAME | DATA_TYPE | DATA_LENGTH | DATA_PRECISION | DATA_SCALE
--   ------------|-----------|-------------|----------------|----------
--   ID          | NUMBER    | 22          | 10             | 0

---

-- ============================================================================
-- SECTION 4: REGRESSION TESTING QUERIES
-- ============================================================================

-- Query 4.1: Verify no data loss in DMS_PARAMS
-- Expected: Count should match baseline count (from before Phase 3)
SELECT COUNT(*) as total_params
FROM dms_params;

-- Expected: Same count as before Phase 3 implementation

---

-- Query 4.2: Verify DMS_JOB and related tables unchanged
-- Expected: All core tables should have unchanged row counts
SELECT 
    (SELECT COUNT(*) FROM dms_job) as job_count,
    (SELECT COUNT(*) FROM dms_jobdtl) as jobdetail_count,
    (SELECT COUNT(*) FROM dms_dbconnect) as connection_count;

-- Expected: Same counts as before Phase 3

---

-- Query 4.3: Verify datatype integrity
-- Expected: All PRCD values should have valid PRVAL
SELECT COUNT(*) as invalid_datatypes
FROM dms_params
WHERE prtyp = 'Datatype'
  AND (prcd IS NULL OR prval IS NULL OR prval = '');

-- Expected: 0 (no invalid entries)

---

-- ============================================================================
-- SECTION 5: PHASE 3 INTEGRATION QUERIES
-- ============================================================================

-- Query 5.1: Find datatypes available for specific job target database
-- Replace 'TEST_MAPREF' and 'POSTGRESQL' with actual values
SELECT 
    p.prcd,
    p.prval,
    p.dbtyp,
    j.mapref,
    j.trgschm,
    dc.dbtyp as target_dbtype
FROM dms_params p
JOIN dms_job j ON j.mapref = 'TEST_MAPREF'
LEFT JOIN dms_dbconnect dc ON dc.conid = j.trgconid
WHERE p.prtyp = 'Datatype'
  AND (p.dbtyp = 'POSTGRESQL' OR p.dbtyp = 'GENERIC')
ORDER BY p.dbtyp DESC NULLS LAST;

-- This simulates Phase 3A flow: get datatypes for target database

---

-- Query 5.2: Validate combo datatype selection
-- Simulates Phase 3B: build_job_flow_code combo_details query pattern
SELECT 
    j.jobid,
    jd.trgclnm,
    jd.trgcldtyp,
    p.prval as selected_datatype,
    p.dbtyp as datatype_source
FROM dms_job j
JOIN dms_jobdtl jd ON jd.mapref = j.mapref
JOIN dms_params p ON p.prtyp = 'Datatype' 
                  AND p.prcd = jd.trgcldtyp
                  AND (p.dbtyp = 'ORACLE' OR p.dbtyp = 'GENERIC')
WHERE j.jobid = 1001
ORDER BY jd.excseq, p.dbtyp DESC NULLS LAST
FETCH FIRST 10 ROWS ONLY;

-- Shows how Phase 3 selects database-specific datatypes for job columns

---

-- ============================================================================
-- EXECUTION SUMMARY CHECKLIST
-- ============================================================================
-- Run all queries above and verify:
-- 
-- [ ] Query 1.1 / 2.1: DBTYP column exists
-- [ ] Query 1.2 / 2.2: Datatype distribution shows all database types
-- [ ] Query 1.3 / 2.3: Filtering pattern works correctly
-- [ ] Query 1.4 / 2.4: GENERIC fallback available
-- [ ] Query 1.5-1.9 / 2.5: All validations pass
-- [ ] Query 3.1 / 3.2: Created tables have correct datatypes
-- [ ] Query 4.1-4.3: No regression in existing data
-- [ ] Query 5.1-5.2: Phase 3 integration queries work
--
-- If all checks pass: Phase 4 SQL validation SUCCESSFUL ✓
-- If any check fails: Review DMS_PARAMS setup before continuing
--
-- ============================================================================
