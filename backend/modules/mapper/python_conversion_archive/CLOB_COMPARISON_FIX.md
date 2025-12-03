# CLOB Comparison Issue Fix

## Summary
After fixing the CLOB comparison issue in `create_update_sql`, a comprehensive review identified **three additional CLOB handling issues** that could cause similar problems in other parts of the application.

## Issues Found and Fixed

### 1. Issue in `create_update_mapping_detail` (Line 519)
**Location:** `backend/modules/mapper/pkgdms_mapr.py` - Method: `create_update_mapping_detail`

**Problem:**
```python
# Direct comparison of CLOB without reading it first
if (... or
    w_maprdtl_dict['MAPLOGIC'] != p_maplogic or
    ...)
```

**Impact:** When updating mapping details, the system would always create a new record even if `MAPLOGIC` (a CLOB field) hadn't changed, because CLOB objects cannot be directly compared with strings.

**Fix:**
```python
# Read CLOB value for MAPLOGIC if needed
existing_maplogic = w_maprdtl_dict['MAPLOGIC']
if hasattr(existing_maplogic, 'read'):
    # It's a CLOB object, read it
    existing_maplogic = existing_maplogic.read()
elif existing_maplogic is not None:
    # Convert to string
    existing_maplogic = str(existing_maplogic)

# Now compare with the properly read value
if (... or
    existing_maplogic != p_maplogic or
    ...)
```

### 2. Issue in `validate_logic2` (Line 733)
**Location:** `backend/modules/mapper/pkgdms_mapr.py` - Method: `validate_logic2`

**Problem:**
```python
# Fetching SQL from DMS_MAPRSQL table
w_rec = cursor.fetchone()

# Direct use without checking if it's a CLOB
if w_rec:
    w_logic = w_rec[1]  # This could be a CLOB object!
else:
    w_logic = p_logic
```

**Impact:** When validating logic that references SQL codes, if the stored SQL is a CLOB, the validation would fail or behave unexpectedly because CLOB objects need to be read before use.

**Fix:**
```python
# Get actual SQL
if w_rec:
    # Read CLOB value properly
    w_logic = w_rec[1]
    if hasattr(w_logic, 'read'):
        # It's a CLOB object, read it
        w_logic = w_logic.read()
    elif w_logic is not None:
        # Convert to string
        w_logic = str(w_logic)
else:
    w_logic = p_logic  # Use provided logic
```

### 3. Issue in `validate_all_logic` (Line 803)
**Location:** `backend/modules/mapper/pkgdms_mapr.py` - Method: `validate_all_logic`

**Problem:**
```python
# Fetching mapping details including maplogic (CLOB)
for map_rec in map_records:
    mapref, mapdtlid, trgtbnm, trgclnm, keyclnm, valclnm, maplogic = map_rec
    
    # Direct use of maplogic without checking if it's a CLOB
    w_res, w_err = self.validate_logic2(maplogic, keyclnm, valclnm)
```

**Impact:** When validating all logic for a mapping reference, if any `maplogic` field is a CLOB, it would not be properly read, causing validation failures or incorrect behavior.

**Fix:**
```python
# Validate each mapping detail
for map_rec in map_records:
    mapref, mapdtlid, trgtbnm, trgclnm, keyclnm, valclnm, maplogic = map_rec
    
    # Read CLOB value for maplogic if needed
    if hasattr(maplogic, 'read'):
        # It's a CLOB object, read it
        maplogic = maplogic.read()
    elif maplogic is not None:
        # Convert to string
        maplogic = str(maplogic)
    
    w_res, w_err = self.validate_logic2(maplogic, keyclnm, valclnm)
```

## Root Cause
Oracle's `oracledb` driver returns CLOB columns as LOB objects that need to be explicitly read using the `.read()` method. These LOB objects cannot be directly:
- Compared with strings
- Used in string operations
- Inserted into SQL queries

The fix involves checking if the value has a `.read()` method (indicating it's a LOB object) and reading it before use.

## Pattern for CLOB Handling
All CLOB fields should be handled using this pattern:

```python
# Read CLOB value if needed
clob_value = some_record['CLOB_COLUMN']
if hasattr(clob_value, 'read'):
    # It's a CLOB object, read it
    clob_value = clob_value.read()
elif clob_value is not None:
    # Convert to string
    clob_value = str(clob_value)
```

## CLOB Columns in the Schema
Based on the code review, the following columns are CLOBs and require this handling:
- `DMS_MAPRSQL.DMS_MAPRSQL` - SQL query text
- `DMS_MAPRDTL.maplogic` - Mapping logic/SQL

## Testing Recommendations
After these fixes, test the following scenarios:
1. **Manage Mapping Details:**
   - Create a new mapping detail with SQL logic
   - Edit the mapping detail WITHOUT changing the logic - should NOT create a new version
   - Edit the mapping detail WITH changes to the logic - should create a new version

2. **Validate Logic:**
   - Validate mapping details that reference SQL codes (indirect SQL)
   - Validate mapping details with inline SQL (direct SQL)
   - Validate all mapping details for a mapping reference

3. **Manage SQL:**
   - Create new SQL (already tested and working)
   - Update SQL without changes (already tested and working)
   - Update SQL with changes (already tested and working)

## Files Modified
- `backend/modules/mapper/pkgdms_mapr.py` - Fixed CLOB handling in 3 methods

## Date
November 12, 2025

## Related Documentation
- `DUPLICATE_RECORDS_FIX.md` - Initial CLOB comparison fix for `create_update_sql`
- `ERROR_132_FIX.md` - Error message enhancement
- `BUGFIX_SUMMARY.md` - Overall bug fix summary

