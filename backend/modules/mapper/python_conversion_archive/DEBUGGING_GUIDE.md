# Debugging Guide - ORA-00942 and Insert Issues

## Issue Summary
You're experiencing:
1. **ORA-00942** error persisting even after schema prefix fix
2. **Unexpected INSERT** - Application trying to insert into DWMAPR even though you only updated column description

## Why Is INSERT Happening?

### The Application Flow
When you update a column description, the application (`mapper.py` line 542):
1. **Always calls `create_update_mapping` FIRST** with all form data
2. Then calls `create_update_mapping_detail` for each column

This is by design - it ensures the mapping record is up-to-date before updating details.

### The Logic Should Prevent Unnecessary Inserts
The `create_update_mapping` function:
- Checks if the mapping exists
- Compares all fields to see if anything changed
- **If no changes:** Returns existing mapid (no INSERT)
- **If changes detected:** Creates new version (INSERT)

## Diagnostic Steps

### Step 1: Run the Diagnostic Script
```bash
cd D:\CursorTesting\DWTOOL\backend
python -m modules.mapper.test_schema_sequences
```

This will check:
- ✓ SCHEMA environment variable configuration
- ✓ Database connection
- ✓ Which schema owns the sequences
- ✓ Table accessibility
- ✓ Sequence accessibility

### Step 2: Check Application Logs
I've added debug logging to help identify the issue. Look for these messages in your logs:

```
PKGDWMAPR: Using schema prefix 'SCHEMANAME.'
CREATE_UPDATE_MAPPING: Mapping 'TEST_DIM' exists
CREATE_UPDATE_MAPPING: No changes detected for 'TEST_DIM', returning existing mapid=42
```

OR

```
PKGDWMAPR: Using schema prefix 'SCHEMANAME.'
CREATE_UPDATE_MAPPING: Mapping 'TEST_DIM' exists
CREATE_UPDATE_MAPPING: Changes detected for 'TEST_DIM', will create new version
CREATE_UPDATE_MAPPING: Inserting into dwmapr using sequence 'SCHEMANAME.DWMAPRSEQ'
```

### Step 3: Verify SCHEMA Environment Variable

**Check if it's set:**
```python
import os
print(f"SCHEMA: {os.getenv('SCHEMA')}")
```

**Common Issues:**
- ❌ Not set at all (returns `None`)
- ❌ Set in one place but not loaded by the application
- ❌ Set with wrong value
- ✓ Should be the schema name where sequences exist (e.g., `DWT`)

### Step 4: Test Sequence Access Manually

Connect to your database and run:

```sql
-- Check current user
SELECT USER FROM dual;

-- Find all DWT sequences
SELECT owner, sequence_name 
FROM all_sequences 
WHERE sequence_name LIKE 'DW%SEQ';

-- Test accessing the sequence (use the actual owner from above)
SELECT SCHEMANAME.DWMAPRSEQ.nextval FROM dual;
```

## Common Problems and Solutions

### Problem 1: SCHEMA Environment Variable Not Set

**Symptoms:**
- Log shows: `PKGDWMAPR: No SCHEMA environment variable set`
- ORA-00942 error

**Solution:**
```bash
# Add to your .env file
SCHEMA=DWT

# OR set in environment
export SCHEMA=DWT  # Linux/Mac
set SCHEMA=DWT     # Windows CMD
$env:SCHEMA="DWT"  # Windows PowerShell
```

**Then restart your application!**

### Problem 2: Sequences in Different Schema

**Symptoms:**
- SCHEMA variable is set correctly
- Still getting ORA-00942
- `all_sequences` query shows sequences in different schema than you're connected to

**Solution Option A - Grant Permissions:**
```sql
-- Run as DBA or schema owner
GRANT SELECT ON DWT.DWMAPRSQLSEQ TO your_username;
GRANT SELECT ON DWT.DWMAPRSEQ TO your_username;
GRANT SELECT ON DWT.DWMAPRDTLSEQ TO your_username;
GRANT SELECT ON DWT.DWMAPERRSEQ TO your_username;
```

**Solution Option B - Create Synonyms:**
```sql
-- Run as your user
CREATE SYNONYM DWMAPRSQLSEQ FOR DWT.DWMAPRSQLSEQ;
CREATE SYNONYM DWMAPRSEQ FOR DWT.DWMAPRSEQ;
CREATE SYNONYM DWMAPRDTLSEQ FOR DWT.DWMAPRDTLSEQ;
CREATE SYNONYM DWMAPERRSEQ FOR DWT.DWMAPERRSEQ;
```

If using synonyms, **clear the SCHEMA environment variable:**
```bash
# In .env file, comment out or remove:
# SCHEMA=DWT
```

### Problem 3: Sequences Don't Exist

**Symptoms:**
- `all_sequences` query returns no results
- ORA-02289 or ORA-00942

**Solution:**
Run the sequence creation script:
```sql
-- See CREATE_SEQUENCES.sql
CREATE SEQUENCE DWMAPRSQLSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPRSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPRDTLSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPERRSEQ START WITH 1 INCREMENT BY 1;
```

### Problem 4: Unexpected Changes Detected

**Symptoms:**
- Log shows: `CREATE_UPDATE_MAPPING: Changes detected`
- But you didn't change the mapping data
- INSERT is attempted

**Possible Causes:**
1. **Frontend sending different values** - Check what the frontend is sending
2. **Date/Time comparison issues** - `lgvrfydt` might have time component differences
3. **NULL vs empty string** - Some fields might be comparing NULL to ''
4. **Number vs string** - `blkprcrows` might be sent as string "0" vs number 0

**Debug:** Add this to see what's different:
```python
# In pkgdwmapr.py, around line 297-312, add:
if w_chg == 'Y':
    # Log what changed
    if w_mapr_dict['MAPDESC'] != p_mapdesc:
        info(f"  MAPDESC changed: '{w_mapr_dict['MAPDESC']}' -> '{p_mapdesc}'")
    if w_mapr_dict['TRGSCHM'] != p_trgschm:
        info(f"  TRGSCHM changed: '{w_mapr_dict['TRGSCHM']}' -> '{p_trgschm}'")
    # ... etc for each field
```

## Quick Fix Checklist

- [ ] Run diagnostic script: `python -m modules.mapper.test_schema_sequences`
- [ ] Check application logs for debug messages
- [ ] Verify SCHEMA environment variable is set correctly
- [ ] Test sequence access from SQL
- [ ] Grant permissions or create synonyms if needed
- [ ] Restart application after environment changes
- [ ] Test again and check logs

## Understanding the Error

**ORA-00942** means one of:
1. Object doesn't exist
2. Object exists but you don't have permission
3. Object name is wrong (typo, case sensitivity)
4. Object is in different schema and not qualified

For sequences, Oracle can throw ORA-00942 (not just ORA-02289), which is confusing!

## Next Steps

1. **Run the diagnostic script** to identify the exact issue
2. **Check your logs** with the new debug messages
3. **Share the output** of:
   - Diagnostic script results
   - Log messages from pkgdwmapr
   - SQL query results from `all_sequences`

This will help pinpoint whether it's:
- Configuration issue (SCHEMA variable)
- Permission issue (need GRANT)
- Synonym issue (need CREATE SYNONYM)
- Or something else

## Files to Reference

- `test_schema_sequences.py` - Diagnostic tool
- `ORA_00942_SCHEMA_PREFIX_FIX.md` - Detailed schema prefix documentation
- `CREATE_SEQUENCES.sql` - Sequence creation script
- `SESSION_FIXES_SUMMARY.md` - All fixes applied in this session

## Contact Information

If the issue persists after following these steps, please provide:
1. Output from diagnostic script
2. Relevant log entries (especially lines with "PKGDWMAPR:" or "CREATE_UPDATE_MAPPING:")
3. Results from the SQL queries above
4. Your environment setup (single-schema or multi-schema)

