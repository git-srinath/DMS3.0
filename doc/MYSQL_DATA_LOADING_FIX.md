# MySQL Data Loading Fix - Complete Summary

**Date**: 2026-02-18  
**Issue**: MySQL job creates table but no data is loaded  
**Mapref**: MYSQL_DIM_ACNT_LN2

## Root Cause

The mapper module's `database_sql_adapter.py` was still using `schema.table` format for MySQL in INSERT/UPDATE statements, even though we had fixed the DB adapter for CREATE TABLE.

### Example of the Problem:
```sql
-- Table creation (FIXED in previous session)
CREATE TABLE DIM_ACNT_LN2 (...);  -- ✓ Works (no schema prefix)

-- Data insertion (BROKEN - now fixed)
INSERT INTO CDR.DIM_ACNT_LN2 (...);  -- ✗ Failed with "Unknown database 'CDR'"
```

MySQL interprets `CDR.DIM_ACNT_LN2` as `database.table`, but the connection is already made to a specific database, so the schema prefix should not be used.

## Files Fixed

### 1. `backend/modules/mapper/database_sql_adapter.py`
**Function**: `format_table_name()`

**Before:**
```python
elif self.db_type == "MYSQL":
    return f'`{schema}`.`{table}`'
```

**After:**
```python
elif self.db_type == "MYSQL":
    # MySQL: database is selected in connection, so only use table name
    # Use backticks for identifier quoting (MySQL standard)
    return f'`{table}`'
```

### 2. `backend/modules/mapper/mapper_scd_handler.py`
**Functions**: `process_scd_batch()`, `_insert_records()`

**Changes:**
- Added adapter-based table name formatting
- Pass formatted table name to all DML operations (INSERT, UPDATE)
- Use `adapter.format_table_name(target_schema, target_table)` instead of raw `full_table_name`

**Result:**
```python
# Now generates correct SQL for MySQL:
adapter = create_adapter_from_type(db_type)
formatted_table_name = adapter.format_table_name(target_schema, target_table)
# For MySQL with CDR.DIM_ACNT_LN2: formatted_table_name = '`DIM_ACNT_LN2`'

query = f"INSERT INTO {formatted_table_name} (...)"
# Generates: INSERT INTO `DIM_ACNT_LN2` (...) ✓ Correct!
```

### 3. `backend/modules/jobs/execution_engine.py`
**Function**: `_execute_job_flow()` - TRUNCATE TABLE handling

**Issue**: TRUNCATE TABLE was using hardcoded PostgreSQL-style formatting

**Before:**
```python
if target_db_type == "POSTGRESQL":
    full_name = f'"{target_schema}"."{target_table}"'
    t_cursor.execute(f"TRUNCATE TABLE {full_name}")
else:  # Oracle - but MySQL fell into this!
    full_name = f"{target_schema}.{target_table}"
    t_cursor.execute(f"TRUNCATE TABLE {full_name}")
```

**After:**
```python
# Use database adapter to format table name correctly for each DB type
adapter = get_db_adapter(target_db_type)
full_name = adapter.format_table_ref(target_schema, target_table)
t_cursor.execute(f"TRUNCATE TABLE {full_name}")
```

**Result:**
- MySQL: `TRUNCATE TABLE DIM_ACNT_LN2` ✓
- Oracle: `TRUNCATE TABLE DW.FACT_SALES` ✓
- PostgreSQL: `TRUNCATE TABLE "public"."dim_customer"` ✓

### 4. `backend/modules/common/db_table_utils.py`
**Function**: `_detect_db_type()` - Database connection type detection

**Issue**: Function only detected PostgreSQL and Oracle, defaulting MySQL to Oracle

**Before:**
```python
def _detect_db_type(connection):
    # Only checked for psycopg and oracledb modules
    # MySQL connections would default to "ORACLE"
    if "psycopg" in module_name:
        return "POSTGRESQL"
    elif "oracledb" in module_name:
        return "ORACLE"
    return "ORACLE"  # MySQL fell into this!
```

**After:**
```python
def _detect_db_type(connection):
    # Check module name first (most reliable)
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    elif "mysql" in module_name.lower():
        return "MYSQL"
    elif "pyodbc" in module_name:
        return "MSSQL"
    elif "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    # ...additional checks...
```

**Result:**
- MySQL connections detected as "MYSQL" ✓
- Correct adapter selected (MysqlAdapter) ✓
- Correct SQL formatting (no schema prefix) ✓

## Test Results

### Table Name Formatting (All Fixed)
```
MySQL format_table_name('CDR', 'DIM_ACNT_LN2') = '`DIM_ACNT_LN2`'
Expected: `DIM_ACNT_LN2` (no schema prefix)
Match: True ✓
```

### TRUNCATE TABLE Formatting (All Fixed)
```
MYSQL        | TRUNCATE TABLE DIM_ACNT_LN2
ORACLE       | TRUNCATE TABLE DW.FACT_SALES
POSTGRESQL   | TRUNCATE TABLE "public"."dim_customer"
MSSQL        | TRUNCATE TABLE dbo.Orders
```

### Connection Type Detection (CRITICAL FIX)
```
MySQL        | Detected: MYSQL        | Adapter: MysqlAdapter         | Table: DIM_ACNT_LN2
PostgreSQL   | Detected: POSTGRESQL   | Adapter: PostgresAdapter      | Table: "cdr"."dim_acnt_ln2"
Oracle       | Detected: ORACLE       | Adapter: OracleAdapter        | Table: CDR.DIM_ACNT_LN2
```

> **CRITICAL**: Without the detection fix, MySQL connections were misidentified as ORACLE, causing all adapters to use Oracle formatting!

## Next Steps to Fix Your Job

### Method 1: Regenerate via Python Script (Quickest)

```bash
cd D:\DMS\DMSTOOL
python regenerate_mysql_job.py
```

This will regenerate the job flow code with the correct table formatting.

### Method 2: Regenerate via UI

1. Open DMS web interface
2. Navigate to Jobs → MYSQL_DIM_ACNT_LN2
3. Click **Edit** or **Save** button to trigger job flow regeneration
4. The system will automatically regenerate the job with the fixes

### Method 3: Manual SQL Update (If needed)

If you want to verify the fix was applied, check the generated code:

```sql
-- Oracle metadata DB:
SELECT DBMS_LOB.SUBSTR(dwlogic, 4000, 1)
FROM DMS_JOBFLW
WHERE mapref = 'MYSQL_DIM_ACNT_LN2' AND curflg = 'Y';

-- PostgreSQL metadata DB:
SELECT dwlogic
FROM dms_jobflw
WHERE mapref = 'MYSQL_DIM_ACNT_LN2' AND curflg = 'Y';
```

Look for INSERT statements - they should now use backticks with table name only:
```python
# OLD (broken):
query = f"INSERT INTO CDR.DIM_ACNT_LN2 ..."

# NEW (fixed):
query = f"INSERT INTO `DIM_ACNT_LN2` ..."
```

## Verification Queries

After regenerating and running the job:

### 1. Check job execution log:
```sql
-- Oracle:
SELECT prcid, mapref, srcrows, trgrows, stflg, ermsg, 
       TO_CHAR(reccrdt, 'YYYY-MM-DD HH24:MI:SS') as run_time
FROM DMS_PRCLOG
WHERE mapref = 'MYSQL_DIM_ACNT_LN2'
ORDER BY reccrdt DESC
FETCH FIRST 5 ROWS ONLY;

-- PostgreSQL:
SELECT prcid, mapref, srcrows, trgrows, stflg, ermsg, reccrdt as run_time
FROM dms_prclog
WHERE mapref = 'MYSQL_DIM_ACNT_LN2'
ORDER BY reccrdt DESC
LIMIT 5;
```

**Expected result after fix:**
- `srcrows` > 0 (source rows fetched)
- `trgrows` > 0 (target rows inserted)
- `stflg` = 'S' (success)

### 2. Verify data in MySQL target table:
```sql
-- Connect to MySQL database 'CDR'
USE CDR;
SELECT COUNT(*) FROM DIM_ACNT_LN2;
SELECT * FROM DIM_ACNT_LN2 LIMIT 10;
```

## Summary of All MySQL Fixes

| Component | Issue | Fix | Status |
|-----------|-------|-----|--------|
| DB Adapter (DDL) | CREATE TABLE CDR.DIM_ACNT_LN2 failed | Return table name only in `mysql_adapter.py` | ✅ Fixed (previous session) |
| Mapper SQL Adapter (DML) | INSERT INTO CDR.DIM_ACNT_LN2 failed | Return table name only in `database_sql_adapter.py` | ✅ Fixed (session 1) |
| SCD Handler | Used full_table_name directly | Format table name via adapter | ✅ Fixed (session 1) |
| Execution Engine (TRUNCATE) | TRUNCATE TABLE "CDR"."DIM_ACNT_LN2" failed | Use adapter for table formatting | ✅ Fixed (session 2) |
| DB Type Detection | MySQL detected as ORACLE | Add MySQL detection in `_detect_db_type()` | ✅ Fixed (session 3 - CRITICAL) |

## Technical Details

### Why MySQL is Different

**MySQL**:
- Schema = Database (synonymous)
- Connection: `mysql.connector.connect(database='CDR', ...)`
- Already in database context
- SQL: `INSERT INTO DIM_ACNT_LN2` ✓

**PostgreSQL/Oracle/MSSQL**:
- Schema ≠ Database (hierarchical)
- Connection: Selected database, can reference multiple schemas
- Need schema prefix in SQL
- SQL: `INSERT INTO schema.table` ✓

### Adapter Pattern Ensures Consistency

```python
# All databases now use the same code:
adapter = create_adapter_from_type(db_type)
table_ref = adapter.format_table_name(schema, table)

# Adapter returns correct format for each DB:
# - MySQL: `table`
# - Oracle: schema.table
# - PostgreSQL: "schema"."table"
# - MSSQL: [schema].[table]
```

## Files Created for Testing/Verification

1. `test_mysql_mapper_fix.py` - Test table name formatting
2. `regenerate_mysql_job.py` - Regenerate job flow
3. `doc/MYSQL_DATA_LOADING_FIX.md` - This documentation

---

**Status**: ✅ **READY FOR TESTING**

Please regenerate the job flow and run the job again. Data should now be loaded successfully!
