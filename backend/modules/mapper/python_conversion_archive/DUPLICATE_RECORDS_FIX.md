# Fix: Duplicate SQL Records Being Created

## ✅ Issue Resolved

**Problem:** The Manage SQL module was creating new records every time, even when the SQL hadn't changed.

**Root Cause:** The code wasn't properly reading and comparing Oracle CLOB (large text) values.

---

## 🔍 Technical Details

### What Was Wrong

When comparing an existing SQL query (stored as a CLOB in Oracle) with a new submission:

```python
# BEFORE (BROKEN)
if w_rec[2] == p_dms_maprsql:  # ❌ Comparing CLOB object with string
    w_res = 0  # Same
else:
    w_res = 1  # Different
```

**Problem:** `w_rec[2]` is a CLOB object from Oracle, not a string. This comparison always returned `False`, making the system think the SQL was always different.

### What Was Fixed

```python
# AFTER (FIXED)
# Read CLOB value properly
existing_sql = w_rec[2]
if hasattr(existing_sql, 'read'):
    # It's a CLOB object, read it
    existing_sql = existing_sql.read()
elif existing_sql is not None:
    # Convert to string
    existing_sql = str(existing_sql)

# Remove trailing semicolons from both for comparison
existing_sql_clean = re.sub(r';$', '', existing_sql.strip())
new_sql_clean = re.sub(r';$', '', p_dms_maprsql.strip())

# Compare the cleaned SQL
if existing_sql_clean == new_sql_clean:
    w_res = 0  # Same - REUSE existing record
else:
    w_res = 1  # Different - CREATE new record
```

---

## 🎯 What Happens Now

### Scenario 1: Creating New SQL (First Time)
**Input:**
- SQL Code: `CUSTOMER_QUERY`
- SQL: `SELECT * FROM customers`

**Result:**
```
✅ New record created
Log: "SQL code 'CUSTOMER_QUERY' is new - will create first version"
SQL ID: 1
```

### Scenario 2: Saving Unchanged SQL
**Input:**
- SQL Code: `CUSTOMER_QUERY` (already exists)
- SQL: `SELECT * FROM customers` (exactly the same)

**Result:**
```
✅ Existing record reused - NO new record created
Log: "SQL code 'CUSTOMER_QUERY' unchanged - reusing existing ID: 1"
SQL ID: 1 (same as before)
```

### Scenario 3: Updating SQL with Changes
**Input:**
- SQL Code: `CUSTOMER_QUERY` (already exists)
- SQL: `SELECT * FROM customers WHERE active = 1` (changed!)

**Result:**
```
✅ New version created (historization)
Log: "SQL code 'CUSTOMER_QUERY' has changes - will create new version"
Old record: curflg = 'N' (marked as historical)
New record: curflg = 'Y', SQL ID: 2
```

---

## 📊 Database Impact

### Before Fix
```sql
-- Every save created a new record
SELECT dms_maprsqlid, dms_maprsqlcd, curflg 
FROM DMS_MAPRSQL 
WHERE dms_maprsqlcd = 'CUSTOMER_QUERY';

-- Result:
ID    CODE              CURFLG
1     CUSTOMER_QUERY    N      -- ❌ Old (should be Y)
2     CUSTOMER_QUERY    N      -- ❌ Duplicate
3     CUSTOMER_QUERY    N      -- ❌ Duplicate
4     CUSTOMER_QUERY    Y      -- Current
```

### After Fix
```sql
-- Only creates new records when SQL actually changes
SELECT dms_maprsqlid, dms_maprsqlcd, curflg 
FROM DMS_MAPRSQL 
WHERE dms_maprsqlcd = 'CUSTOMER_QUERY';

-- Result:
ID    CODE              CURFLG
1     CUSTOMER_QUERY    N      -- ✅ Version 1 (historical)
2     CUSTOMER_QUERY    Y      -- ✅ Version 2 (current)
```

---

## 🎨 Enhanced Features

### 1. Smart Comparison
- **Strips whitespace** before comparing
- **Removes trailing semicolons** (so `SELECT *;` equals `SELECT *`)
- **Handles CLOB objects** properly
- **Case-sensitive comparison** (as SQL should be)

### 2. Logging
The system now logs what it's doing:

```
[INFO] SQL code 'CUSTOMER_QUERY' unchanged - reusing existing ID: 1
[INFO] SQL code 'REPORT_SQL' has changes - will create new version
[INFO] SQL code 'NEW_QUERY' is new - will create first version
```

Check your application logs to see these messages!

---

## 🧪 Test Cases

### Test 1: Save Same SQL Twice
```
Action 1: Create SQL with code "TEST_SQL_001"
Result 1: New record created, ID = 1

Action 2: Save exact same SQL again
Result 2: No new record, returns ID = 1 ✅

Verify:
SELECT COUNT(*) FROM DMS_MAPRSQL WHERE dms_maprsqlcd = 'TEST_SQL_001';
-- Should return: 1 (not 2!)
```

### Test 2: Modify SQL
```
Action 1: Create SQL with code "TEST_SQL_002"
SQL: "SELECT id FROM table1"
Result 1: ID = 2

Action 2: Modify and save
SQL: "SELECT id, name FROM table1"
Result 2: ID = 3 (new version created) ✅

Verify:
SELECT dms_maprsqlid, curflg FROM DMS_MAPRSQL 
WHERE dms_maprsqlcd = 'TEST_SQL_002';
-- Should return:
-- ID=2, curflg='N' (old version)
-- ID=3, curflg='Y' (current version)
```

### Test 3: Whitespace/Semicolon Differences
```
Action 1: Create SQL
SQL: "SELECT * FROM customers;"

Action 2: Save again with trailing space
SQL: "SELECT * FROM customers; "

Result: No new record ✅ (whitespace ignored)

Action 3: Save again without semicolon
SQL: "SELECT * FROM customers"

Result: No new record ✅ (semicolon ignored)
```

---

## 📝 Files Modified

| File | Lines Changed | What Changed |
|------|--------------|--------------|
| `pkgdms_mapr.py` | 108-137 | Fixed CLOB comparison logic |
| `pkgdms_mapr.py` | 127, 130, 136 | Added info logging |

---

## ⚙️ Configuration

No configuration changes needed! The fix works automatically.

---

## 🔄 Migration Notes

### Do You Have Duplicate Records?

If you have duplicate records from before this fix, you can clean them up:

```sql
-- Find SQL codes with duplicates
SELECT dms_maprsqlcd, COUNT(*) as versions
FROM DMS_MAPRSQL
WHERE curflg = 'Y'
GROUP BY dms_maprsqlcd
HAVING COUNT(*) > 1;

-- To keep only the latest version (be careful!):
-- First, verify what will be kept
SELECT * 
FROM DMS_MAPRSQL 
WHERE dms_maprsqlcd = 'your_sql_code'
ORDER BY dms_maprsqlid;

-- Then update old versions to curflg='N'
UPDATE DMS_MAPRSQL
SET curflg = 'N'
WHERE dms_maprsqlcd = 'your_sql_code'
AND dms_maprsqlid NOT IN (
    SELECT MAX(dms_maprsqlid) 
    FROM DMS_MAPRSQL 
    WHERE dms_maprsqlcd = 'your_sql_code'
);
COMMIT;
```

---

## 🎯 Benefits

✅ **No More Duplicates** - Only creates new records when SQL actually changes  
✅ **Better Performance** - Fewer database records to manage  
✅ **Cleaner Data** - Clear history of actual changes  
✅ **Proper Historization** - Old versions marked with curflg='N'  
✅ **Better Logging** - See what the system is doing  
✅ **Smart Comparison** - Ignores insignificant differences  

---

## 📊 Before vs After

### Before Fix
```
Save #1: CUSTOMER_QUERY → Record 1 created ✓
Save #2: CUSTOMER_QUERY (no change) → Record 2 created ❌ (duplicate!)
Save #3: CUSTOMER_QUERY (no change) → Record 3 created ❌ (duplicate!)
```

### After Fix
```
Save #1: CUSTOMER_QUERY → Record 1 created ✓
Save #2: CUSTOMER_QUERY (no change) → Reuses Record 1 ✓ (correct!)
Save #3: CUSTOMER_QUERY (no change) → Reuses Record 1 ✓ (correct!)
Save #4: CUSTOMER_QUERY (with change) → Record 2 created ✓ (new version!)
```

---

## 🎉 Result

The Manage SQL module now works correctly:
- ✅ Creates new records only when SQL is new or changed
- ✅ Reuses existing records when SQL is unchanged
- ✅ Maintains proper version history
- ✅ Logs all actions for visibility

---

**Status:** ✅ **FIXED AND TESTED**  
**Breaking Changes:** NO  
**Database Changes:** NO  
**Configuration Required:** NO  

---

*Fix Date: November 12, 2025*  
*Issue: Duplicate records being created*  
*Solution: Proper CLOB comparison with smart string matching*

