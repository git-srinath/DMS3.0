# Error [132] Fix - Enhanced Error Messages

## Issue Fixed
Error messages were incomplete - showing only parameter info but not the actual database error.

**Before:**
```
Error: Error in PKGDWMAPR.CREATE_UPDATE_SQL [132]: SqlCode=Query_RPT_1
```
(No details about what went wrong)

**After:**
```
Error: Error in PKGDWMAPR.CREATE_UPDATE_SQL [132]: SqlCode=Query_RPT_1 - ORA-XXXXX: [actual error]
```
(Shows the real database error)

---

## Changes Made

### File: `pkgdwmapr.py`

**Enhanced 4 error messages in `create_update_sql()` method:**

| Line | Error Code | What Was Fixed |
|------|-----------|----------------|
| 117 | 131 | Added exception details when comparing SQL |
| 136 | 132 | Added exception details when updating existing SQL |
| 160 | 133 | Added exception details when inserting new SQL |
| 170 | 134 | Added exception details for general exceptions |

---

## Next Steps

### 1. Test Again
Try creating your SQL again in the Manage SQL module with code `Query_RPT_1`.

### 2. You Will Now See the Real Error
The error message will now show the actual database problem, for example:

**Common Error Messages You Might See:**

#### A. Table Doesn't Exist
```
Error: ... - ORA-00942: table or view does not exist
```
**Fix:** Create the `DWMAPRSQL` table:
```sql
-- Run from your DDL file
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql
```

#### B. Column Missing
```
Error: ... - ORA-00904: "CURFLG": invalid identifier
```
**Fix:** The table structure is incomplete. Run the full DDL to add missing columns.

#### C. Permission Denied
```
Error: ... - ORA-01031: insufficient privileges
```
**Fix:** Grant UPDATE permission:
```sql
GRANT UPDATE ON dwmaprsql TO your_username;
```

#### D. Trigger/Constraint Issue
```
Error: ... - ORA-04088: error during execution of trigger
```
**Fix:** Check if there are any triggers on DWMAPRSQL table that might be failing.

---

## How to Troubleshoot

### Step 1: Check if DWMAPRSQL Table Exists
```sql
SELECT table_name 
FROM user_tables 
WHERE table_name = 'DWMAPRSQL';
```

**If empty:** Create the table using your DDL file.

### Step 2: Check Table Structure
```sql
DESC DWMAPRSQL;
```

**Expected columns:**
- DWMAPRSQLID (NUMBER) - Primary key
- DWMAPRSQLCD (VARCHAR2) - SQL code
- DWMAPRSQL (CLOB) - SQL content
- RECCRDT (DATE) - Created date
- RECUPDT (DATE) - Updated date
- CURFLG (VARCHAR2) - Current flag

### Step 3: Check Data
```sql
SELECT dwmaprsqlcd, curflg 
FROM dwmaprsql 
WHERE dwmaprsqlcd = 'Query_RPT_1';
```

This shows if a record with that code already exists.

### Step 4: Check Permissions
```sql
-- Check what privileges you have on the table
SELECT privilege 
FROM user_tab_privs 
WHERE table_name = 'DWMAPRSQL';
```

**Should have:** SELECT, INSERT, UPDATE, DELETE

---

## Complete Database Setup

If you're setting up from scratch, run these in order:

```sql
-- 1. Create sequences
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql
-- (or just the sequence parts shown in SEQUENCE_FIX_QUICK_GUIDE.md)

-- 2. Create tables (if not already done)
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql

-- 3. If using multi-schema setup (DWT/CDR)
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT_grants.sql
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_CDR.sql

-- 4. Verify setup
SELECT 'Sequences' as object_type, sequence_name as name 
FROM user_sequences 
WHERE sequence_name LIKE 'DW%'
UNION ALL
SELECT 'Tables', table_name 
FROM user_tables 
WHERE table_name LIKE 'DW%';
```

---

## Test Case

After fixing any database issues, test with:

**SQL Code:** `TEST_SQL_001`  
**SQL Content:**
```sql
SELECT 
    customer_id,
    customer_name,
    email
FROM customers
WHERE status = 'ACTIVE'
```

**Expected Result:** ✅ "SQL saved successfully with ID: [number]"

---

## Common Solutions

### Solution 1: Missing DWMAPRSQL Table

**Run the DDL:**
```sql
-- From DWT_DDL_DWT.sql (around line 390-405)
CREATE TABLE dwmaprsql (
    dwmaprsqlid NUMBER NOT NULL,
    dwmaprsqlcd VARCHAR2(100) NOT NULL,
    dwmaprsql CLOB,
    reccrdt DATE,
    recupdt DATE,
    curflg VARCHAR2(1) DEFAULT 'Y'
);

ALTER TABLE dwmaprsql ADD CONSTRAINT dwmaprsql_pk PRIMARY KEY (dwmaprsqlid);
CREATE SEQUENCE dwmaprsqlseq START WITH 1 INCREMENT BY 1;
```

### Solution 2: CURFLG Column Missing

```sql
ALTER TABLE dwmaprsql ADD (curflg VARCHAR2(1) DEFAULT 'Y');
```

### Solution 3: Need to Clean Up Test Data

```sql
-- Delete test records
DELETE FROM dwmaprsql WHERE dwmaprsqlcd = 'Query_RPT_1';
COMMIT;
```

---

## Status

✅ **Error messages enhanced** - Now showing actual database errors  
🔍 **Next:** Run the test again to see the real error message  
📋 **Action:** Follow troubleshooting steps based on the actual error shown

---

*Fix applied: November 12, 2025*  
*File updated: pkgdwmapr.py*  
*Lines changed: 117, 136, 160, 170*

