# ORA-01745: Invalid Host/Bind Variable Name Fix

## Summary
Fixed **ORA-01745: invalid host/bind variable name** error caused by using `:user` as a bind variable name. Oracle reserves `USER` as a keyword, which conflicts with bind variable names. All occurrences of `:user` have been renamed to `:p_user`.

## Issue Reported
**User Error Message:**
```
Operation failed: An error occurred while saving the mapping data 
Error in PKGDMS_MAPR.CREATE_UPDATE_MAPPING [101]: Mapref=TEST_DIM-Test dimension table mapid=42 - ORA-01745: invalid host/bind variable name
Help: https://docs.oracle.com/error-help/db/ora-01745/
```

**Context:** User was trying to update column description in the Mapper Module.

## Root Cause
Oracle has a built-in function `USER` that returns the current user's name. When we use `:user` as a bind variable name in SQL statements, Oracle cannot distinguish between the bind variable and the built-in function, resulting in **ORA-01745**.

### Oracle Reserved Keywords
Common reserved keywords that cannot be used as bind variables include:
- `USER` - Returns current user
- `SYSDATE` - Returns current date/time
- `ROWNUM` - Row number
- `LEVEL` - Hierarchical level
- `ROWID` - Row identifier

## Changes Made

All bind variables named `:user` were renamed to `:p_user` in the following locations:

### 1. `create_update_mapping` - UPDATE Statement (Line 315)
**Before:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET curflg = 'N',
        recupdt = SYSDATE,
        uptdby = :user
    WHERE mapid = :mapid
""", {
    'user': self.g_user,
    'mapid': w_mapr_dict['MAPID']
})
```

**After:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET curflg = 'N',
        recupdt = SYSDATE,
        uptdby = :p_user
    WHERE mapid = :mapid
""", {
    'p_user': self.g_user,
    'mapid': w_mapr_dict['MAPID']
})
```

### 2. `create_update_mapping` - INSERT Statement (Line 336)
**Before:**
```python
VALUES (DMS_MAPRSEQ.nextval, :mapref, :mapdesc, :trgschm, :trgtbtyp, :trgtbnm, 
       :frqcd, :srcsystm, :lgvrfyflg, :lgvrfydt, :stflg, SYSDATE, SYSDATE, 'Y', 
       :blkprcrows, :user, :user)
```

**After:**
```python
VALUES (DMS_MAPRSEQ.nextval, :mapref, :mapdesc, :trgschm, :trgtbtyp, :trgtbnm, 
       :frqcd, :srcsystm, :lgvrfyflg, :lgvrfydt, :stflg, SYSDATE, SYSDATE, 'Y', 
       :blkprcrows, :p_user, :p_user)
```

### 3. `create_update_mapping_detail` - UPDATE Statement (Line 550)
**Before:**
```python
cursor.execute("""
    UPDATE DMS_MAPRDTL
    SET curflg = 'N',
        recupdt = SYSDATE,
        uptdby = :user
    WHERE mapref = :mapref
    AND mapdtlid = :mapdtlid
    AND curflg = 'Y'
""", {
    'user': self.g_user,
    'mapref': w_maprdtl_dict['MAPREF'],
    'mapdtlid': w_maprdtl_dict['MAPDTLID']
})
```

**After:**
```python
cursor.execute("""
    UPDATE DMS_MAPRDTL
    SET curflg = 'N',
        recupdt = SYSDATE,
        uptdby = :p_user
    WHERE mapref = :mapref
    AND mapdtlid = :mapdtlid
    AND curflg = 'Y'
""", {
    'p_user': self.g_user,
    'mapref': w_maprdtl_dict['MAPREF'],
    'mapdtlid': w_maprdtl_dict['MAPDTLID']
})
```

### 4. `create_update_mapping_detail` - INSERT Statement (Line 579)
**Before:**
```python
VALUES (DMS_MAPRDTLSEQ.nextval, :mapref, :trgclnm, :trgcldtyp, :trgkeyflg, 
       :trgkeyseq, :trgcldesc, :maplogic, :maprsqlcd, :keyclnm, :valclnm, 
       :mapcmbcd, :excseq, :scdtyp, :lgvrfyflg, :lgvrfydt, SYSDATE, SYSDATE, 
       'Y', :user, :user)
```

**After:**
```python
VALUES (DMS_MAPRDTLSEQ.nextval, :mapref, :trgclnm, :trgcldtyp, :trgkeyflg, 
       :trgkeyseq, :trgcldesc, :maplogic, :maprsqlcd, :keyclnm, :valclnm, 
       :mapcmbcd, :excseq, :scdtyp, :lgvrfyflg, :lgvrfydt, SYSDATE, SYSDATE, 
       'Y', :p_user, :p_user)
```

### 5. `validate_all_logic` - UPDATE Statement (Line 935)
**Before:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET lgvrfydt = SYSDATE,
        lgvrfyflg = :lgvrfyflg,
        lgvrfby = :user
    WHERE mapref = :mapref
    AND curflg = 'Y'
""", {
    'lgvrfyflg': w_return,
    'user': self.g_user,
    'mapref': p_mapref
})
```

**After:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET lgvrfydt = SYSDATE,
        lgvrfyflg = :lgvrfyflg,
        lgvrfby = :p_user
    WHERE mapref = :mapref
    AND curflg = 'Y'
""", {
    'lgvrfyflg': w_return,
    'p_user': self.g_user,
    'mapref': p_mapref
})
```

### 6. `activate_deactivate_mapping` - UPDATE Statement (Line 1102)
**Before:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET stflg = :stflg,
        actby = :user,
        actdt = SYSDATE
    WHERE mapref = :mapref
    AND curflg = 'Y'
""", {
    'stflg': p_stflg,
    'user': self.g_user,
    'mapref': p_mapref
})
```

**After:**
```python
cursor.execute("""
    UPDATE DMS_MAPR
    SET stflg = :stflg,
        actby = :p_user,
        actdt = SYSDATE
    WHERE mapref = :mapref
    AND curflg = 'Y'
""", {
    'stflg': p_stflg,
    'p_user': self.g_user,
    'mapref': p_mapref
})
```

## Total Changes
- **6 SQL statements updated**
- **4 functions affected:**
  - `create_update_mapping` (2 statements)
  - `create_update_mapping_detail` (2 statements)
  - `validate_all_logic` (1 statement)
  - `activate_deactivate_mapping` (1 statement)

## Best Practices for Bind Variables
1. **Prefix bind variables** with `p_` or `v_` to avoid conflicts with reserved keywords
2. **Avoid common Oracle keywords** like:
   - `user`, `date`, `time`, `level`, `count`, `rownum`, `rowid`, `sequence`
3. **Use descriptive names** that clearly indicate what the variable represents
4. **Test with Oracle** to ensure no naming conflicts

## Testing Instructions
1. **Test Update Operation** - Try to update column description in the Mapper Module
2. **Test Insert Operation** - Create new mapping and mapping details
3. **Test Validation** - Validate mapping logic
4. **Test Activation** - Activate/deactivate mappings

All operations should now work without ORA-01745 errors.

## Related Files
- `backend/modules/mapper/pkgdms_mapr.py` - Fixed all bind variable names

## Related Documentation
- `ERROR_101_105_FIX.md` - Enhanced error messages for [101] and [105]
- `BUGFIX_SUMMARY.md` - Overall bug fix summary
- `CLOB_COMPARISON_FIX.md` - CLOB handling fixes

## Date
November 12, 2025

