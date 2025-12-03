# Oracle Sequence Missing - Fix Guide

## Issue

**Error:** `ORA-02289: sequence does not exist`

**Full Error Message:**
```
Error: Error in PKGDMS_MAPR.CREATE_UPDATE_SQL [133]: SqlCode=testsqlcd123 - 
ORA-02289: sequence does not exist
```

## Root Cause

The Python PKGDMS_MAPR module requires **4 Oracle sequences** to generate unique IDs for database records. These sequences don't exist in your database yet.

### Required Sequences:

| Sequence Name | Purpose | Used In |
|--------------|---------|---------|
| `DMS_MAPRSQLSEQ` | Generate SQL mapping IDs | CREATE_UPDATE_SQL |
| `DMS_MAPRSEQ` | Generate mapping IDs | CREATE_UPDATE_MAPPING |
| `DMS_MAPRDTLSEQ` | Generate mapping detail IDs | CREATE_UPDATE_MAPPING_DETAIL |
| `DMS_MAPERRSEQ` | Generate error log IDs | VALIDATE_LOGIC (error logging) |

## Solution

### Option 1: Run the Provided SQL Script (Recommended)

1. **Open SQL*Plus, SQL Developer, or your Oracle client**

2. **Connect to your database** as the schema owner:
   ```sql
   sqlplus your_username/your_password@your_database
   ```

3. **Run the CREATE_SEQUENCES.sql script**:
   ```sql
   @D:\CursorTesting\DWTOOL\backend\modules\mapper\CREATE_SEQUENCES.sql
   ```

   Or copy and paste the contents of `CREATE_SEQUENCES.sql` into your SQL tool and execute.

4. **Verify sequences were created**:
   ```sql
   SELECT sequence_name, last_number 
   FROM user_sequences 
   WHERE sequence_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ');
   ```

   **Expected Output:**
   ```
   SEQUENCE_NAME      LAST_NUMBER
   ------------------ -----------
   DMS_MAPRSQLSEQ                 1
   DMS_MAPRSEQ                    1
   DMS_MAPRDTLSEQ                 1
   DMS_MAPERRSEQ                  1
   ```

### Option 2: Create Sequences Manually

If you prefer to create them one by one:

```sql
-- SQL Mapping sequence
CREATE SEQUENCE DMS_MAPRSQLSEQ START WITH 1 INCREMENT BY 1;

-- Mapping sequence
CREATE SEQUENCE DMS_MAPRSEQ START WITH 1 INCREMENT BY 1;

-- Mapping Detail sequence
CREATE SEQUENCE DMS_MAPRDTLSEQ START WITH 1 INCREMENT BY 1;

-- Mapping Error sequence
CREATE SEQUENCE DMS_MAPERRSEQ START WITH 1 INCREMENT BY 1;

COMMIT;
```

### Option 3: Check if PL/SQL Package Created Them

If you previously had the PL/SQL PKGDMS_MAPR package installed, the sequences might exist but in a different schema. Check:

```sql
-- Check all schemas
SELECT owner, sequence_name 
FROM all_sequences 
WHERE sequence_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ');
```

If they exist in another schema, you have two options:
1. **Grant SELECT** permission on sequences to your current schema
2. **Create synonyms** pointing to those sequences

## After Creating Sequences

### Test 1: Verify Sequence Access
```sql
-- Test all sequences
SELECT DMS_MAPRSQLSEQ.NEXTVAL FROM DUAL;
SELECT DMS_MAPRSEQ.NEXTVAL FROM DUAL;
SELECT DMS_MAPRDTLSEQ.NEXTVAL FROM DUAL;
SELECT DMS_MAPERRSEQ.NEXTVAL FROM DUAL;
```

Each should return a number (starting from 1 if just created).

### Test 2: Try Creating SQL Again

Go back to your application's Manage SQL module and try creating SQL again:

1. Enter SQL Code: `testsqlcd123`
2. Enter SQL Query: `SELECT * FROM your_table`
3. Click **Create/Save**

**Expected Result:** ✅ Success! SQL saved with an ID

## Common Issues

### Issue 1: "Insufficient Privileges"

**Error:** `ORA-01031: insufficient privileges`

**Solution:** Connect as a user with CREATE SEQUENCE privilege:
```sql
-- As DBA or schema owner
GRANT CREATE SEQUENCE TO your_username;
```

### Issue 2: Sequences Exist but Not Accessible

**Error:** `ORA-02289: sequence does not exist` (even though they exist)

**Solution:** Create public synonyms or grant access:
```sql
-- Option A: Grant to specific user
GRANT SELECT ON schema_owner.DMS_MAPRSQLSEQ TO your_username;
GRANT SELECT ON schema_owner.DMS_MAPRSEQ TO your_username;
GRANT SELECT ON schema_owner.DMS_MAPRDTLSEQ TO your_username;
GRANT SELECT ON schema_owner.DMS_MAPERRSEQ TO your_username;

-- Option B: Create synonyms
CREATE SYNONYM DMS_MAPRSQLSEQ FOR schema_owner.DMS_MAPRSQLSEQ;
CREATE SYNONYM DMS_MAPRSEQ FOR schema_owner.DMS_MAPRSEQ;
CREATE SYNONYM DMS_MAPRDTLSEQ FOR schema_owner.DMS_MAPRDTLSEQ;
CREATE SYNONYM DMS_MAPERRSEQ FOR schema_owner.DMS_MAPERRSEQ;
```

### Issue 3: Want to Start from a Specific Number

If you have existing data and need sequences to start from a higher number:

```sql
-- Find the maximum ID from existing data
SELECT MAX(dms_maprsqlid) FROM DMS_MAPRSQL;  -- Example: returns 1500

-- Drop and recreate sequence starting from 1501
DROP SEQUENCE DMS_MAPRSQLSEQ;
CREATE SEQUENCE DMS_MAPRSQLSEQ START WITH 1501 INCREMENT BY 1;
```

Repeat for other sequences based on your existing data.

## Verification Checklist

Before testing your application:

- [ ] Connected to correct Oracle database/schema
- [ ] All 4 sequences created successfully
- [ ] Can query `user_sequences` and see all 4 sequences
- [ ] Can successfully call `.NEXTVAL` on each sequence
- [ ] Application user has SELECT permission on sequences
- [ ] No errors when running verification queries

## Environment-Specific Notes

### Development Environment
- Sequences typically start from 1
- OK to drop and recreate sequences

### Production Environment
- **DO NOT drop sequences** if they already exist
- Check current `last_number` before making changes
- Consider starting new sequences from a number higher than existing data
- Test in a non-production environment first

## File Locations

- **SQL Script:** `D:\CursorTesting\DWTOOL\backend\modules\mapper\CREATE_SEQUENCES.sql`
- **This Guide:** `D:\CursorTesting\DWTOOL\backend\modules\mapper\SEQUENCE_ISSUE_FIX.md`

## Quick Test After Fix

After creating sequences, test the complete flow:

1. **Test SQL Creation:**
   ```
   Manage SQL → Create SQL → Enter code and query → Save
   ```

2. **Test Mapping Creation:**
   ```
   Mapper → Create Mapping → Fill form → Save
   ```

3. **Test Mapping Detail:**
   ```
   Mapper → Add Column Detail → Fill form → Save
   ```

4. **Test Validation:**
   ```
   Mapper → Validate Mapping → Should show results
   ```

All should work without sequence errors!

---

**Status:** 🔧 **Action Required**  
**Priority:** **HIGH** (Application won't work without sequences)  
**Estimated Time:** 2-5 minutes to create sequences

---

*Issue identified: November 12, 2025*
*Solution provided: November 12, 2025*

