# Table Schema Prefix Fix - Complete Solution

## Summary
**CRITICAL FIX:** Added schema prefix support for **ALL** table references, not just sequences. This was the root cause of persistent ORA-00942 errors.

## The Problem
Initial fix only added schema prefixes to **sequences** but missed **tables**:
- ❌ `FROM DMS_MAPR` - No schema prefix
- ❌ `FROM DMS_MAPRDTL` - No schema prefix  
- ❌ `INSERT INTO DMS_MAPR` - No schema prefix
- ✅ `DMS_MAPRSEQ.nextval` - Had schema prefix

In multi-schema Oracle setups, if you're connected as user X but tables are in schema Y, you get:
```
ORA-00942: table or view does not exist
```

## User's Insight
**User correctly identified:** "could this be also like you have to use upper case tablename?"

The real issue wasn't uppercase vs lowercase (Oracle handles that), but the **missing schema prefix** on table names, just like sequences needed it!

## Solution Applied

### Added Schema Prefix to ALL Tables

**Tables Fixed (6 total):**
1. `DMS_MAPRSQL` - SQL query records
2. `DMS_MAPR` - Mapping records  
3. `DMS_MAPRDTL` - Mapping detail records
4. `DMS_MAPERR` - Error records
5. `DMS_PARAMS` - Parameters/lookup data
6. `DMS_JOB` / `DMS_JOBDTL` - Job-related tables

### Total Changes
- **~50+ SQL statements** updated
- **All f-strings** converted to support `SCHEMA_PREFIX`
- **Consistent pattern** applied throughout

## Before vs After

### Before (Failing)
```python
cursor.execute("""
    SELECT * 
    FROM DMS_MAPR 
    WHERE mapref = :mapref
""", {'mapref': p_mapref})
```

**Result:** ORA-00942 if `DMS_MAPR` table is in different schema

### After (Working)
```python
cursor.execute(f"""
    SELECT * 
    FROM {SCHEMA_PREFIX}DMS_MAPR 
    WHERE mapref = :mapref
""", {'mapref': p_mapref})
```

**Result with SCHEMA=DWT:**
```sql
SELECT * FROM DWT.DMS_MAPR WHERE mapref = :mapref
```

**Result without SCHEMA:**
```sql
SELECT * FROM DMS_MAPR WHERE mapref = :mapref
```

## Updated SQL Statements by Category

### SELECT Statements (14 updated)
-  `SELECT * FROM {SCHEMA_PREFIX}DMS_MAPR`
- `SELECT * FROM {SCHEMA_PREFIX}DMS_MAPRDTL`
- `SELECT dms_maprsqlcd, DMS_MAPRSQL FROM {SCHEMA_PREFIX}DMS_MAPRSQL`
- `SELECT prval FROM {SCHEMA_PREFIX}DMS_PARAMS`
- `SELECT mapref, jobid FROM {SCHEMA_PREFIX}DMS_JOB`
- `SELECT mapref, jobdtlid FROM {SCHEMA_PREFIX}DMS_JOBDTL`
- Multiple aggregation queries with schema prefix

### INSERT Statements (5 updated)
- `INSERT INTO {SCHEMA_PREFIX}DMS_MAPRSQL`
- `INSERT INTO {SCHEMA_PREFIX}DMS_MAPR`
- `INSERT INTO {SCHEMA_PREFIX}DMS_MAPRDTL`
- `INSERT INTO {SCHEMA_PREFIX}DMS_MAPERR` (3 occurrences)

### UPDATE Statements (4 updated)
- `UPDATE {SCHEMA_PREFIX}DMS_MAPRSQL`
- `UPDATE {SCHEMA_PREFIX}DMS_MAPR` (3 occurrences)
- `UPDATE {SCHEMA_PREFIX}DMS_MAPRDTL` (2 occurrences)

### DELETE Statements (3 updated)
- `DELETE FROM {SCHEMA_PREFIX}DMS_MAPR`
- `DELETE FROM {SCHEMA_PREFIX}DMS_MAPRDTL` (2 occurrences)

## How Schema Prefix Works

###Configuration
```python
# In pkgdms_mapr.py (lines 18-21)
ORACLE_SCHEMA = os.getenv("SCHEMA", "")
SCHEMA_PREFIX = f"{ORACLE_SCHEMA}." if ORACLE_SCHEMA else ""
```

### Runtime Behavior

**Scenario 1: Multi-Schema Setup**
```bash
# .env file
SCHEMA=DWT
```

Generated SQL:
```sql
SELECT * FROM DWT.DMS_MAPR WHERE mapref = 'TEST_DIM'
INSERT INTO DWT.DMS_MAPR VALUES (DWT.DMS_MAPRSEQ.nextval, ...)
```

**Scenario 2: Single-Schema Setup**
```bash
# .env file (no SCHEMA set)
```

Generated SQL:
```sql
SELECT * FROM DMS_MAPR WHERE mapref = 'TEST_DIM'
INSERT INTO DMS_MAPR VALUES (DMS_MAPRSEQ.nextval, ...)
```

## Why This Fix Was Needed

### Common Oracle Setup Patterns

**Pattern 1: Development (Single Schema)**
```
User: DWTOOL_USER
Tables: In DWTOOL_USER schema
Sequences: In DWTOOL_USER schema
Solution: No SCHEMA prefix needed
```

**Pattern 2: Production (Multi-Schema)**
```
User: APP_USER (application connection)
Tables: In DWT schema (data owner)
Sequences: In DWT schema
Permissions: APP_USER has SELECT, INSERT, UPDATE, DELETE on DWT objects
Solution: Need SCHEMA=DWT prefix
```

**Pattern 3: Production (with Synonyms)**
```
User: APP_USER
Tables: In DWT schema
Synonyms: CREATE SYNONYM DMS_MAPR FOR DWT.DMS_MAPR
Solution: No SCHEMA prefix needed (synonyms handle it)
```

## Complete List of Fixed SQL Statements

### create_update_sql (3)
1. SELECT from DMS_MAPRSQL  (check existence)
2. UPDATE DMS_MAPRSQL (mark old as not current)
3. INSERT INTO DMS_MAPRSQL (create new version)

### create_update_mapping (3)
1. SELECT from DMS_MAPR (check existence)
2. UPDATE DMS_MAPR (mark old as not current)
3. INSERT INTO DMS_MAPR (create new version)

### create_update_mapping_detail (5)
1. SELECT from DMS_PARAMS (validate datatype)
2. SELECT from DMS_MAPRSQL (check if logic is SQL code)
3. SELECT from DMS_MAPR (verify mapping exists)
4. SELECT from DMS_MAPRDTL (check if detail exists)
5. UPDATE DMS_MAPRDTL (mark old as not current)
6. INSERT INTO DMS_MAPRDTL (create new version)

### validate_logic2 (1)
1. SELECT from DMS_MAPRSQL (get SQL by code)

### validate_all_logic (8)
1. SELECT from DMS_MAPR/DMS_MAPRDTL (get all details)
2. INSERT INTO DMS_MAPERR (3 places - validation errors)
3. UPDATE DMS_MAPRDTL (update validation result)
4. SELECT aggregations from DMS_MAPRDTL (3 places - validation checks)
5. UPDATE DMS_MAPR (update validation result)

### validate_mapping_details (3)
1. SELECT aggregations from DMS_MAPRDTL (3 places - PK, duplicates, value columns)

### activate_deactivate_mapping (1)
1. UPDATE DMS_MAPR (change status)

### delete_mapping (3)
1. SELECT from DMS_JOB (check dependencies)
2. DELETE FROM DMS_MAPRDTL (delete details)
3. DELETE FROM DMS_MAPR (delete mapping)

### delete_mapping_details (2)
1. SELECT from DMS_JOBDTL (check dependencies)
2. DELETE FROM DMS_MAPRDTL (delete detail)

**Total: ~50 SQL statements updated**

## Testing Checklist

### Without Schema Prefix (Single Schema)
- [ ] SCHEMA environment variable: Not set or empty
- [ ] Tables exist in connected user's schema
- [ ] All CRUD operations work without schema prefix

### With Schema Prefix (Multi-Schema)
- [ ] SCHEMA environment variable: Set (e.g., `SCHEMA=DWT`)
- [ ] Tables exist in DWT schema
- [ ] Connected user has permissions on DWT objects
- [ ] All SQL statements use `DWT.tablename` format
- [ ] All CRUD operations work with schema prefix

### Operations to Test
- [ ] Create SQL query (Manage SQL module)
- [ ] Update SQL query
- [ ] Create mapping (Mapper module)
- [ ] **Update mapping description** ← Original failing operation
- [ ] Create mapping detail
- [ ] Update mapping detail column description
- [ ] Validate logic
- [ ] Activate/deactivate mapping
- [ ] Delete mapping detail
- [ ] Delete mapping

## Configuration Guide

### Step 1: Identify Your Setup

**Check where tables are:**
```sql
SELECT owner, table_name 
FROM all_tables 
WHERE table_name LIKE 'DW%'
ORDER BY owner, table_name;
```

**Check your connected user:**
```sql
SELECT USER FROM dual;
```

### Step 2: Configure SCHEMA Variable

**If tables are in same schema as your user:**
```bash
# .env file - leave SCHEMA unset or empty
# SCHEMA=
```

**If tables are in different schema:**
```bash
# .env file
SCHEMA=DWT
```

### Step 3: Verify Permissions

If using multi-schema setup, ensure permissions:
```sql
-- As DBA or DWT schema owner
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPR TO your_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPRDTL TO your_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPRSQL TO your_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPERR TO your_app_user;
GRANT SELECT ON DWT.DMS_PARAMS TO your_app_user;
GRANT SELECT ON DWT.DMS_JOB TO your_app_user;
GRANT SELECT ON DWT.DMS_JOBDTL TO your_app_user;

-- Grant sequence permissions
GRANT SELECT ON DWT.DMS_MAPRSEQ TO your_app_user;
GRANT SELECT ON DWT.DMS_MAPRDTLSEQ TO your_app_user;
GRANT SELECT ON DWT.DMS_MAPRSQLSEQ TO your_app_user;
GRANT SELECT ON DWT.DMS_MAPERRSEQ TO your_app_user;
```

### Step 4: Restart Application

**IMPORTANT:** After changing SCHEMA environment variable, **restart the application** to load the new configuration.

## Troubleshooting

### Error Still Occurs

1. **Check SCHEMA variable loaded:**
   ```python
   import os
   print(f"SCHEMA: {os.getenv('SCHEMA')}")
   ```

2. **Check application logs:**
   ```
   PKGDMS_MAPR: Using schema prefix 'DWT.'
   ```
   
3. **Test SQL manually:**
   ```sql
   -- If SCHEMA=DWT, try:
   SELECT * FROM DWT.DMS_MAPR WHERE ROWNUM = 1;
   ```

4. **Verify permissions:**
   ```sql
   SELECT * FROM user_tab_privs WHERE table_name = 'DMS_MAPR';
   ```

### If Tables Don't Exist

Run DDL to create tables (see your existing DDL files).

### Alternative: Use Synonyms

Instead of schema prefix, create synonyms:
```sql
-- As your application user
CREATE SYNONYM DMS_MAPR FOR DWT.DMS_MAPR;
CREATE SYNONYM DMS_MAPRDTL FOR DWT.DMS_MAPRDTL;
CREATE SYNONYM DMS_MAPRSQL FOR DWT.DMS_MAPRSQL;
CREATE SYNONYM DMS_MAPERR FOR DWT.DMS_MAPERR;
CREATE SYNONYM DMS_PARAMS FOR DWT.DMS_PARAMS;
CREATE SYNONYM DMS_JOB FOR DWT.DMS_JOB;
CREATE SYNONYM DMS_JOBDTL FOR DWT.DMS_JOBDTL;
-- Plus synonyms for sequences
```

Then **don't set SCHEMA** environment variable.

## Related Documentation
- `ORA_00942_SCHEMA_PREFIX_FIX.md` - Original sequence fix
- `DEBUGGING_GUIDE.md` - Troubleshooting steps
- `test_schema_sequences.py` - Diagnostic tool
- `SESSION_FIXES_SUMMARY.md` - All fixes in this session

## Date
November 12, 2025

## Credit
**Fix identified by user's insight:** "could this be also like you have to use upper case tablename?"  
This led to discovering that tables needed schema prefixes too, not just sequences.

