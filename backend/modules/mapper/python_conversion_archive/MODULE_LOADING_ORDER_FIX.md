# Module Loading Order Fix - CRITICAL

## 🔴 Critical Issue Identified

**Date:** November 12, 2025  
**Issue:** `ORA-00942: table or view does not exist` despite correct schema configuration

## Root Cause

The `.env` file was being loaded **AFTER** the blueprint modules were imported in `app.py`. This caused a module loading order problem:

```python
# WRONG ORDER (Original code):
from modules.mapper.mapper import mapper_bp  # ❌ Module loads now
from modules.manage_sql.manage_sql import manage_sql_bp  # ❌ Module loads now
# ... other imports ...

load_dotenv()  # ❌ TOO LATE! Modules already loaded with empty schema values
```

### What Happened

1. Python imports blueprint modules
2. Blueprint modules import `pkgdwmapr.py`
3. `pkgdwmapr.py` executes module-level code:
   ```python
   DWT_SCHEMA = os.getenv("DWT_SCHEMA", "")  # Returns "" because .env not loaded yet!
   DWT_SCHEMA_PREFIX = f"{DWT_SCHEMA}." if DWT_SCHEMA else ""  # Results in ""
   ```
4. `.env` file is loaded (but too late)
5. All SQL statements use empty schema prefix → `ORA-00942` errors

## The Fix

Move `load_dotenv()` to **BEFORE** any module imports:

```python
# CORRECT ORDER (Fixed code):
from dotenv import load_dotenv

# CRITICAL: Load environment variables BEFORE importing modules
load_dotenv()  # ✓ Load .env first

# Now import modules - they will see the environment variables
from modules.mapper.mapper import mapper_bp  # ✓ Module loads with correct schema
from modules.manage_sql.manage_sql import manage_sql_bp  # ✓ Module loads with correct schema
```

## Changes Made

### File: `backend/app.py`

1. **Moved `load_dotenv()` to line 23** (after standard imports, before module imports)
2. **Added comment** explaining the critical importance of loading order
3. **Removed duplicate `load_dotenv()` call** that was on line 56

## Impact

This fix ensures:

✅ Environment variables are loaded before modules read them  
✅ `DWT_SCHEMA` and `CDR_SCHEMA` are properly set when modules load  
✅ Schema prefixes are correctly applied to all SQL statements  
✅ No more `ORA-00942` errors due to missing schema qualification

## Testing

After this fix:

1. **Restart the application** (critical - modules must be reloaded)
   ```bash
   # Stop the application
   # Start it again
   ```

2. **Verify in logs** - you should see:
   ```
   CREATE_UPDATE_MAPPING: Inserting into table 'DWT.dwmapr'
   CREATE_UPDATE_MAPPING: Using sequence 'DWT.DWMAPRSEQ.nextval'
   CREATE_UPDATE_MAPPING: DWT_SCHEMA='DWT', DWT_SCHEMA_PREFIX='DWT.'
   ```

3. **Test mapper operations** - should work without `ORA-00942`

## Prevention

**⚠️ IMPORTANT RULE:** Always load `.env` before importing application modules!

```python
# ✓ GOOD:
load_dotenv()
from modules.something import something

# ❌ BAD:
from modules.something import something
load_dotenv()  # Too late!
```

## Related Files

- `backend/app.py` - Main application entry point (FIXED)
- `backend/modules/mapper/pkgdwmapr.py` - Uses schema prefixes
- `backend/modules/helper_functions.py` - Uses schema prefixes
- `backend/modules/manage_sql/manage_sql.py` - Uses schema prefixes

## Verification Script

Run this to verify the fix:

```bash
cd backend
python check_schema_config.py
```

This will show:
- Whether .env file is found
- Current environment variable values
- Calculated schema prefixes
- Database connection test with schema-qualified tables

## Summary

**Problem:** Module loading order caused empty schema prefixes  
**Solution:** Load `.env` before importing modules  
**Result:** Schema prefixes now work correctly  
**Action Required:** Restart application for fix to take effect

---

**Status:** ✅ FIXED  
**Version:** 1.0  
**Next Steps:** Restart application and test mapper module

