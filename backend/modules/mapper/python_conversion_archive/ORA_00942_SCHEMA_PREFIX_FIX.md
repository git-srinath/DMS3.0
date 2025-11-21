# ORA-00942: Table or View Does Not Exist - Schema Prefix Fix

## Summary
Fixed **ORA-00942: table or view does not exist** error by adding support for Oracle schema prefixes on sequence references. The application uses a `SCHEMA` environment variable for PL/SQL calls but wasn't using it for sequence references in the Python code.

## Issue Reported
**User Error Message:**
```
Operation failed: An error occurred while saving the mapping data 
Error in PKGDWMAPR.CREATE_UPDATE_MAPPING [102]: Mapref=TEST_DIM-Test dimension table - ORA-00942: table or view does not exist
Help: https://docs.oracle.com/error-help/db/ora-00942/
```

**Context:** 
- User confirmed the `dwmapr` table exists and has all necessary permissions
- The error was occurring on INSERT statement

## Root Cause

### Discovery
The application uses an `ORACLE_SCHEMA` environment variable (from `os.getenv("SCHEMA")`) to prefix PL/SQL package calls in other modules:

```python
# From backend/modules/helper_functions.py
ORACLE_SCHEMA = os.getenv("SCHEMA")

# Used like:
:result := {ORACLE_SCHEMA}.PKGDWMAPR.CREATE_UPDATE_MAPPING(...)
```

However, the `pkgdwmapr.py` module was **not using** this schema prefix for sequence references.

### The Problem
When sequences are in a different schema than the one the user is connected to, they need to be prefixed with the schema name:
- ❌ `dwmaprseq.nextval` - fails if sequence is in another schema
- ✅ `SCHEMANAME.DWMAPRSEQ.nextval` - works with schema prefix

### Why ORA-00942 for Sequences?
Oracle throws **ORA-00942** (table or view does not exist) for sequences too, not just tables. This is because sequences are database objects that can be in different schemas.

### Additional Issue: Case Inconsistency
The original code had inconsistent casing:
- Line 165: `DWMAPRSQLSEQ.nextval` (UPPERCASE)
- Line 334: `dwmaprseq.nextval` (lowercase) ← The problematic one
- Other lines: lowercase

Oracle stores unquoted identifiers in UPPERCASE by default, so this inconsistency could also cause issues.

## Solution Implemented

### 1. Added Schema Configuration (Lines 11-21)
```python
import os
import re
import oracledb
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from modules.logger import logger, info, warning, error

# Get Oracle schema from environment (if set)
ORACLE_SCHEMA = os.getenv("SCHEMA", "")
# Add dot separator if schema is specified
SCHEMA_PREFIX = f"{ORACLE_SCHEMA}." if ORACLE_SCHEMA else ""
```

**Benefits:**
- Uses the same `SCHEMA` environment variable as other modules
- Automatically adds dot separator only if schema is specified
- Defaults to empty string if no schema is set (for single-schema setups)

### 2. Updated All 6 Sequence References

All sequence references were updated to:
1. Use the `SCHEMA_PREFIX` variable
2. Use UPPERCASE names for consistency
3. Use f-strings to include the prefix

#### Sequence 1: DWMAPRSQLSEQ (Line 168-172)
**Before:**
```python
cursor.execute("""
    INSERT INTO dwmaprsql
    VALUES (DWMAPRSQLSEQ.nextval, :sqlcd, :sql, SYSDATE, SYSDATE, 'Y')
    RETURNING dwmaprsqlid INTO :ret_id
""", {
```

**After:**
```python
cursor.execute(f"""
    INSERT INTO dwmaprsql
    VALUES ({SCHEMA_PREFIX}DWMAPRSQLSEQ.nextval, :sqlcd, :sql, SYSDATE, SYSDATE, 'Y')
    RETURNING dwmaprsqlid INTO :ret_id
""", {
```

#### Sequence 2: DWMAPRSEQ (Line 336-343)
**Before:**
```python
cursor.execute("""
    INSERT INTO dwmapr 
    VALUES (dwmaprseq.nextval, :mapref, ...)
    RETURNING mapid INTO :ret_id
""", {
```

**After:**
```python
cursor.execute(f"""
    INSERT INTO dwmapr 
    VALUES ({SCHEMA_PREFIX}DWMAPRSEQ.nextval, :mapref, ...)
    RETURNING mapid INTO :ret_id
""", {
```

#### Sequence 3: DWMAPRDTLSEQ (Line 577-586)
**Before:**
```python
cursor.execute("""
    INSERT INTO dwmaprdtl 
    VALUES (dwmaprdtlseq.nextval, :mapref, ...)
    RETURNING mapdtlid INTO :ret_id
""", {
```

**After:**
```python
cursor.execute(f"""
    INSERT INTO dwmaprdtl 
    VALUES ({SCHEMA_PREFIX}DWMAPRDTLSEQ.nextval, :mapref, ...)
    RETURNING mapdtlid INTO :ret_id
""", {
```

#### Sequences 4-6: DWMAPERRSEQ (Lines 843, 897, 926)
**Before:**
```python
cursor.execute("""
    INSERT INTO dwmaperr
    VALUES (dwmaperrseq.nextval, ...)
""", {
```

**After:**
```python
cursor.execute(f"""
    INSERT INTO dwmaperr
    VALUES ({SCHEMA_PREFIX}DWMAPERRSEQ.nextval, ...)
""", {
```

## How It Works

### With Schema Prefix (Multi-Schema Setup)
If `SCHEMA` environment variable is set to `DWT`:
```python
ORACLE_SCHEMA = "DWT"
SCHEMA_PREFIX = "DWT."

# Generated SQL:
INSERT INTO dwmapr VALUES (DWT.DWMAPRSEQ.nextval, ...)
```

### Without Schema Prefix (Single-Schema Setup)
If `SCHEMA` environment variable is not set or empty:
```python
ORACLE_SCHEMA = ""
SCHEMA_PREFIX = ""

# Generated SQL:
INSERT INTO dwmapr VALUES (DWMAPRSEQ.nextval, ...)
```

## Configuration

The schema prefix is controlled by the `SCHEMA` environment variable. Make sure it's set in your `.env` file or environment:

```bash
# In .env file
SCHEMA=DWT
```

Or in your environment:
```bash
export SCHEMA=DWT
```

## Sequences Affected

All four sequences used in the application are now schema-aware:

1. **DWMAPRSQLSEQ** - For SQL query records (`dwmaprsql` table)
2. **DWMAPRSEQ** - For mapping records (`dwmapr` table)
3. **DWMAPRDTLSEQ** - For mapping detail records (`dwmaprdtl` table)
4. **DWMAPERRSEQ** - For error records (`dwmaperr` table)

## Testing Instructions

1. **Verify environment variable** - Check that `SCHEMA` is set correctly:
   ```python
   import os
   print(f"SCHEMA: {os.getenv('SCHEMA')}")
   ```

2. **Test INSERT operations:**
   - Create new SQL query (uses DWMAPRSQLSEQ)
   - Create new mapping (uses DWMAPRSEQ)
   - Create new mapping detail (uses DWMAPRDTLSEQ)
   - Trigger validation error (uses DWMAPERRSEQ)

3. **Verify generated SQL** - Check application logs to see the actual SQL being executed

## Troubleshooting

### If error still occurs:

1. **Verify sequence exists:**
   ```sql
   -- Check in your schema
   SELECT sequence_name FROM user_sequences WHERE sequence_name LIKE 'DW%SEQ';
   
   -- Check in all schemas
   SELECT owner, sequence_name FROM all_sequences WHERE sequence_name LIKE 'DW%SEQ';
   ```

2. **Verify you have permissions:**
   ```sql
   -- Grant SELECT permission on sequences
   GRANT SELECT ON DWT.DWMAPRSQLSEQ TO your_username;
   GRANT SELECT ON DWT.DWMAPRSEQ TO your_username;
   GRANT SELECT ON DWT.DWMAPRDTLSEQ TO your_username;
   GRANT SELECT ON DWT.DWMAPERRSEQ TO your_username;
   ```

3. **Create synonyms (alternative to schema prefix):**
   ```sql
   CREATE SYNONYM DWMAPRSQLSEQ FOR DWT.DWMAPRSQLSEQ;
   CREATE SYNONYM DWMAPRSEQ FOR DWT.DWMAPRSEQ;
   CREATE SYNONYM DWMAPRDTLSEQ FOR DWT.DWMAPRDTLSEQ;
   CREATE SYNONYM DWMAPERRSEQ FOR DWT.DWMAPERRSEQ;
   ```

4. **Check if SCHEMA environment variable is set:**
   ```bash
   # Linux/Mac
   echo $SCHEMA
   
   # Windows
   echo %SCHEMA%
   ```

## Changes Summary

### Files Modified
- `backend/modules/mapper/pkgdwmapr.py`
  - Added `import os` (line 11)
  - Added `ORACLE_SCHEMA` and `SCHEMA_PREFIX` configuration (lines 18-21)
  - Updated 6 SQL INSERT statements to use `SCHEMA_PREFIX`
  - Standardized all sequence names to UPPERCASE

### Consistency
- All modules now use the same `SCHEMA` environment variable
- Sequence naming is now consistent (all UPPERCASE)
- Schema prefix handling is automatic and configuration-driven

## Related Files
- `backend/modules/helper_functions.py` - Uses `ORACLE_SCHEMA` for PL/SQL calls
- `backend/modules/manage_sql/manage_sql.py` - Uses `ORACLE_SCHEMA`
- `backend/modules/jobs/jobs.py` - Uses `ORACLE_SCHEMA`

## Related Documentation
- `ORA_01745_FIX.md` - Fix for bind variable name issue
- `ERROR_101_105_FIX.md` - Enhanced error messages
- `CREATE_SEQUENCES.sql` - Sequence creation script
- `SEQUENCE_ISSUE_FIX.md` - Original sequence troubleshooting guide

## Date
November 12, 2025

