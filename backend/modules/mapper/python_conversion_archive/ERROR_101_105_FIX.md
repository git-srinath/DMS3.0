# Error Code [101] and [105] Fix

## Summary
Fixed missing exception details in error codes [101] and [105] which occur when updating existing mapping and mapping detail records. The error messages were not including the actual database exception, making it impossible to diagnose the root cause of failures.

## Issue Reported
**User Error Message:**
```
Operation failed: An error occurred while saving the mapping data 
Error in PKGDMS_MAPR.CREATE_UPDATE_MAPPING [101]: Mapref=TEST_DIM-Test dimension table mapid=42
```

**Context:** User was trying to update column description in the Mapper Module.

## Root Cause
When updating existing mapping or mapping detail records (setting `curflg = 'N'` before inserting a new version), the exception handling was not including the actual database error message.

### Error Code [101] - `create_update_mapping`
**Before:**
```python
except Exception as e:
    raise PKGDMS_MAPRError(self.G_NAME, w_procnm, '101', 
                       f"{w_parm} mapid={w_mapr_dict['MAPID']}")
```

**After:**
```python
except Exception as e:
    raise PKGDMS_MAPRError(self.G_NAME, w_procnm, '101', 
                       f"{w_parm} mapid={w_mapr_dict['MAPID']} - {str(e)}")
```

### Error Code [105] - `create_update_mapping_detail`
**Before:**
```python
except Exception as e:
    raise PKGDMS_MAPRError(self.G_NAME, w_procnm, '105',
                       f"{w_parm} Mapref={w_maprdtl_dict['MAPREF']} "
                       f"Trgclnm={w_maprdtl_dict['TRGCLNM']}")
```

**After:**
```python
except Exception as e:
    raise PKGDMS_MAPRError(self.G_NAME, w_procnm, '105',
                       f"{w_parm} Mapref={w_maprdtl_dict['MAPREF']} "
                       f"Trgclnm={w_maprdtl_dict['TRGCLNM']} - {str(e)}")
```

## What These Errors Mean

### Error [101] - UPDATE DMS_MAPR Failed
This error occurs when trying to update an existing mapping record to set `curflg = 'N'` (marking it as not current) before inserting a new version.

**Possible causes:**
1. **Database constraint violation** - Foreign key, check constraint, or trigger failure
2. **Lock contention** - Another session is updating the same record
3. **Permission issues** - User lacks UPDATE privilege on `DMS_MAPR` table
4. **Missing columns** - The table structure doesn't match expectations

### Error [105] - UPDATE DMS_MAPRDTL Failed
This error occurs when trying to update an existing mapping detail record to set `curflg = 'N'` (marking it as not current) before inserting a new version.

**Possible causes:**
1. **Database constraint violation** - Foreign key, check constraint, or trigger failure
2. **Lock contention** - Another session is updating the same record
3. **Permission issues** - User lacks UPDATE privilege on `DMS_MAPRDTL` table
4. **Missing columns** - The table structure doesn't match expectations

## Next Steps for Debugging

With this fix in place, when the user encounters the error again, the error message will now include the actual Oracle error. For example:

```
Error in PKGDMS_MAPR.CREATE_UPDATE_MAPPING [101]: Mapref=TEST_DIM-Test dimension table mapid=42 - ORA-02292: integrity constraint violated - child record found
```

## Common Oracle Errors to Look For

1. **ORA-00001: unique constraint violated**
   - A unique index or constraint is preventing the update
   
2. **ORA-02292: integrity constraint violated - child record found**
   - Cannot update because child records exist
   
3. **ORA-00054: resource busy and acquire with NOWAIT specified**
   - Record is locked by another session
   
4. **ORA-01407: cannot update to NULL**
   - Trying to set a NOT NULL column to NULL
   
5. **ORA-00942: table or view does not exist**
   - Table doesn't exist or user lacks SELECT privilege
   
6. **ORA-01031: insufficient privileges**
   - User lacks UPDATE privilege

## Testing Instructions

1. **Reproduce the error** - Try to update column description in the Mapper Module again
2. **Check the new error message** - The error should now include the Oracle error code and message
3. **Share the complete error message** - This will help identify the actual root cause

## Related Files
- `backend/modules/mapper/pkgdms_mapr.py` - Fixed error handling in `create_update_mapping` and `create_update_mapping_detail`

## Related Fixes
- `ERROR_132_FIX.md` - Similar fix for error code [132] in `create_update_sql`
- `BUGFIX_SUMMARY.md` - Overall bug fix summary
- `CLOB_COMPARISON_FIX.md` - CLOB handling fixes to prevent duplicate records

## Date
November 12, 2025

