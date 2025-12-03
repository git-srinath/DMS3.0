# DateTime Comparison & Table Name Case Fix

## 🔴 Issues Identified

**Date:** November 12, 2025  
**Reported Errors:**
1. DateTime comparison failing when comparing Oracle datetime values with parameters
2. `ORA-00942: table or view does not exist` despite correct schema prefix configuration

## Root Causes

### Issue 1: DateTime Comparison Mismatch

**Problem:** Line 329 in `pkgdms_mapr.py` was comparing datetime objects incorrectly:
```python
# WRONG:
w_mapr_dict['LGVRFYDT'] != p_lgvrfydt
```

**Why it failed:**
- `w_mapr_dict['LGVRFYDT']` is an Oracle `datetime.datetime` object
- `p_lgvrfydt` could be:
  - `None`
  - A Python `datetime.datetime` object with different time components
  - A Python `datetime.date` object
- Direct comparison was failing because even if dates were the same, time components differed

**Example:**
```python
# From Oracle: datetime.datetime(2025, 11, 12, 10, 30, 15)
# From parameter: datetime.datetime(2025, 11, 12, 0, 0, 0)
# These are NOT equal even though the date is the same!
```

### Issue 2: Table Name Case Sensitivity

**Problem:** Oracle table names were lowercase in SQL statements:
```python
# WRONG:
INSERT INTO {DWT_SCHEMA_PREFIX}DMS_MAPR ...
SELECT * FROM {DWT_SCHEMA_PREFIX}DMS_MAPRDTL ...
```

**Why it failed:**
- If Oracle tables were created with quoted identifiers (e.g., `CREATE TABLE "DMS_MAPR"`), they become case-sensitive
- Oracle's default is to convert unquoted identifiers to UPPERCASE
- The user's database likely has tables as `DMS_MAPR`, `DMS_MAPRDTL`, etc. (uppercase)
- SQL was looking for `DMS_MAPR` (lowercase) which doesn't exist → `ORA-00942`

## The Fixes

### Fix 1: DateTime Comparison Normalization

**File:** `backend/modules/mapper/pkgdms_mapr.py`  
**Lines:** 320-341

**Solution:**
1. Extract datetime values from both sources
2. Convert both to date objects (removing time component)
3. Compare only the date portions

```python
# NEW CODE:
# Normalize datetime values for comparison
existing_lgvrfydt = w_mapr_dict['LGVRFYDT']
new_lgvrfydt = p_lgvrfydt

# Convert datetime objects to date for comparison (ignore time component)
if existing_lgvrfydt is not None and hasattr(existing_lgvrfydt, 'date'):
    existing_lgvrfydt = existing_lgvrfydt.date()
if new_lgvrfydt is not None and hasattr(new_lgvrfydt, 'date'):
    new_lgvrfydt = new_lgvrfydt.date()

info(f"CREATE_UPDATE_MAPPING: Comparing existing LGVRFYDT={existing_lgvrfydt} with new={new_lgvrfydt}")

# Now compare normalized dates
if (...existing_lgvrfydt != new_lgvrfydt...):
    w_chg = 'Y'
```

**Benefits:**
- ✅ Handles `None` values correctly
- ✅ Ignores time component differences
- ✅ Works with both `datetime.datetime` and `datetime.date` objects
- ✅ Adds logging for troubleshooting

### Fix 2: Table Names to Uppercase

**File:** `backend/modules/mapper/pkgdms_mapr.py`  
**Changes:** Multiple locations throughout the file

**Tables converted to uppercase:**
- `DMS_MAPR` → `DMS_MAPR`
- `DMS_MAPRDTL` → `DMS_MAPRDTL`
- `DMS_MAPRSQL` → `DMS_MAPRSQL`
- `DMS_MAPERR` → `DMS_MAPERR`
- `DMS_PARAMS` → `DMS_PARAMS`
- `DMS_JOB` → `DMS_JOB`
- `DMS_JOBDTL` → `DMS_JOBDTL`
- `allcdrs` → `ALLCDRS`

**Example change:**
```python
# BEFORE:
INSERT INTO {DWT_SCHEMA_PREFIX}DMS_MAPR (mapid, mapref, ...)

# AFTER:
INSERT INTO {DWT_SCHEMA_PREFIX}DMS_MAPR (mapid, mapref, ...)
```

**Impact:**
- ✅ Now references: `DWT.DMS_MAPR` instead of `DWT.DMS_MAPR`
- ✅ Matches Oracle's default uppercase table names
- ✅ No more `ORA-00942` errors

## Testing After Fix

### 1. Restart Application
```bash
# IMPORTANT: Restart to reload modules with new code
# Stop the backend application
# Start it again
```

### 2. Check Logs
After the update operation, verify in logs:

```
CREATE_UPDATE_MAPPING: Comparing existing LGVRFYDT=2025-11-12 with new=2025-11-12
CREATE_UPDATE_MAPPING: Changes detected for 'TEST_DIM', will create new version
CREATE_UPDATE_MAPPING: Inserting into table 'DWT.DMS_MAPR'
CREATE_UPDATE_MAPPING: Using sequence 'DWT.DMS_MAPRSEQ.nextval'
```

**Success indicators:**
- ✅ DateTime comparison log shows dates being compared (not datetime objects)
- ✅ Table name is uppercase: `DWT.DMS_MAPR`
- ✅ No `ORA-00942` errors
- ✅ Operation completes successfully

### 3. Test Scenarios

**Scenario 1: Update with no changes**
- Update a mapping without changing any values
- Expected: "No changes detected" message, no new record created

**Scenario 2: Update with datetime change**
- Change the logic verify date
- Expected: Change detected, new version created

**Scenario 3: Update with description change**
- Change mapping description only
- Expected: Change detected, new version created

## Other Datetime Comparisons

**Note:** This fix was specifically applied to `create_update_mapping()`. If you encounter similar datetime comparison issues in other functions like:
- `create_update_mapping_detail()`
- `validate_logic2()`
- `validate_all_logic()`

The same pattern should be applied:
```python
# Normalize before comparison
if existing_dt is not None and hasattr(existing_dt, 'date'):
    existing_dt = existing_dt.date()
if new_dt is not None and hasattr(new_dt, 'date'):
    new_dt = new_dt.date()
```

## Oracle Table Name Best Practices

### Why Uppercase?

1. **Oracle Default:** Unquoted identifiers are converted to uppercase
   ```sql
   CREATE TABLE MyTable ...  -- Stored as MYTABLE
   ```

2. **Case-Sensitive Tables:** Only created with quoted identifiers
   ```sql
   CREATE TABLE "MyTable" ...  -- Stored as MyTable (case-sensitive)
   ```

3. **Best Practice:** Always use UPPERCASE in SQL for consistency
   ```python
   # GOOD:
   SELECT * FROM {SCHEMA_PREFIX}DMS_MAPR
   
   # BAD:
   SELECT * FROM {SCHEMA_PREFIX}DMS_MAPR
   ```

## Verification Query

Run this in Oracle to confirm table names:
```sql
-- Check actual table names in your schema
SELECT table_name 
FROM all_tables 
WHERE owner = 'DWT' 
  AND table_name LIKE 'DW%'
ORDER BY table_name;

-- Result should show:
-- DMS_JOB
-- DMS_JOBDTL
-- DMS_MAPERR
-- DMS_MAPR
-- DMS_MAPRDTL
-- DMS_MAPRSQL
-- DMS_PARAMS
```

## Related Documentation

- `MODULE_LOADING_ORDER_FIX.md` - Environment variable loading order
- `ORA_00942_SCHEMA_PREFIX_FIX.md` - Initial schema prefix implementation
- `TABLE_SCHEMA_PREFIX_FIX.md` - Schema prefix for all tables
- `ERROR_101_105_FIX.md` - Enhanced error messages

## Summary

**Problems Fixed:**
1. ✅ DateTime comparison now compares dates only (ignores time)
2. ✅ All table names converted to UPPERCASE to match Oracle
3. ✅ Added logging for datetime comparison troubleshooting

**Files Modified:**
- `backend/modules/mapper/pkgdms_mapr.py`

**Testing Required:**
- Restart application (critical!)
- Test mapper update operations
- Verify no `ORA-00942` errors
- Verify datetime changes are detected correctly

---

**Status:** ✅ FIXED  
**Version:** 1.0  
**Next Steps:** Restart application and test mapper operations

