# Quick Setup Guide - Two Schema Architecture

## What Changed

Your application now supports **two separate schemas**:
- **DWT_SCHEMA** - For metadata (mappings, jobs, SQL queries)
- **CDR_SCHEMA** - For actual data (target tables)

This eliminates the need for synonyms and prevents "table does not exist" errors.

## Quick Setup (3 Steps)

### Step 1: Update `.env` File

Create `.env` file in your project root (copy from `env.template`):

```bash
# Database Connection
DB_HOST=your_host
DB_PORT=1521
DB_SERVICE=your_service
DB_USER=app_user
DB_PASSWORD=your_password

# Schema Configuration
DWT_SCHEMA=DWT
CDR_SCHEMA=CDR
```

### Step 2: Verify Permissions

Your `app_user` needs these grants:

```sql
-- On DWT Schema (Metadata)
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.dwmapr TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.dwmaprdtl TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.dwmaprsql TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.dwmaperr TO app_user;
GRANT SELECT ON DWT.dwparams TO app_user;
GRANT SELECT ON DWT.dwjob TO app_user;
GRANT SELECT ON DWT.dwjobdtl TO app_user;
GRANT SELECT ON DWT.DWMAPRSEQ TO app_user;
GRANT SELECT ON DWT.DWMAPRDTLSEQ TO app_user;
GRANT SELECT ON DWT.DWMAPRSQLSEQ TO app_user;
GRANT SELECT ON DWT.DWMAPERRSEQ TO app_user;

-- On CDR Schema (Data - for future use)
GRANT CREATE TABLE TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON CDR.* TO app_user;
```

### Step 3: Restart Application

```bash
# Stop the application
# Restart to load new environment variables
python app.py  # or your start command
```

## Verify It's Working

### Check Logs
You should see:
```
PKGDWMAPR: DWT metadata schema prefix: 'DWT.'
PKGDWMAPR: CDR data schema prefix: 'CDR.' (for future data operations)
```

### Test Operations
Try the operation that was failing before (updating column description).

It should now work without "table does not exist" errors!

## Files Changed

### Updated Files (5 total)
1. `backend/modules/mapper/pkgdwmapr.py`
2. `backend/modules/helper_functions.py`
3. `backend/modules/manage_sql/manage_sql.py`
4. `backend/modules/jobs/jobs.py`
5. `backend/modules/dashboard/dashboard.py`

### New Files Created
1. `env.template` - Environment configuration template
2. `TWO_SCHEMA_ARCHITECTURE.md` - Complete documentation
3. `TWO_SCHEMA_SETUP_GUIDE.md` - This file

## How It Works

### Before (Single Schema with Synonyms)
```
CDR Schema:
├── CREATE SYNONYM dwmapr FOR DWT.dwmapr  ❌ Required
├── CREATE SYNONYM dwmaprdtl FOR DWT.dwmaprdtl  ❌ Required
└── ... many more synonyms needed

Problems:
- Forget one synonym = "table does not exist" error
- Maintenance overhead
- Confusion about which schema owns what
```

### After (Two Schema Architecture)
```
Application Code:
├── Uses DWT_SCHEMA_PREFIX for metadata  ✅ Automatic
├── Uses CDR_SCHEMA_PREFIX for data  ✅ Automatic
└── No synonyms needed  ✅ Clean

Benefits:
- No synonyms to maintain
- Clear separation of concerns
- Explicit schema qualification
- Fewer errors
```

## Current vs Future Usage

### Current Implementation (Metadata Only)
All current operations use **DWT_SCHEMA** for metadata:
- Creating/updating mappings → `DWT.dwmapr`
- Managing SQL queries → `DWT.dwmaprsql`
- Job management → `DWT.dwjob`

### Future Implementation (Data Loading)
When implementing ETL, will use **CDR_SCHEMA** for data:
- Creating target tables → `CDR.DIM_CUSTOMER`
- Loading data → `INSERT INTO CDR.FACT_SALES`

## Common Scenarios

### Scenario 1: Using Two Separate Schemas (Your Case)
```bash
DWT_SCHEMA=DWT   # Metadata in DWT
CDR_SCHEMA=CDR   # Data in CDR
```
✅ Clean separation  
✅ No synonyms needed  
✅ Easy permission management

### Scenario 2: Using Single Schema (Development)
```bash
DWT_SCHEMA=DEV_SCHEMA
CDR_SCHEMA=DEV_SCHEMA
```
✅ Simpler for development  
✅ All in one schema  

### Scenario 3: User's Default Schema
```bash
DWT_SCHEMA=
CDR_SCHEMA=
```
✅ Tables in connected user's schema  
✅ No schema prefix needed  

## Troubleshooting

### Issue: Still getting ORA-00942

**Check 1:** Are environment variables set?
```python
import os
print(os.getenv("DWT_SCHEMA"))  # Should show: DWT
```

**Check 2:** Did you restart the application?
Old environment variables are cached until restart.

**Check 3:** Do you have permissions?
```sql
SELECT * FROM user_tab_privs WHERE table_schema = 'DWT';
```

### Issue: Application not loading .env

**Solution:** Ensure `dotenv.load_dotenv()` is called:
```python
import dotenv
dotenv.load_dotenv()
```

All updated modules already have this.

### Issue: Want to use old SCHEMA variable

**Good news:** Backward compatibility is built in!

If `DWT_SCHEMA` is not set, application falls back to `SCHEMA`:
```bash
# Old way still works
SCHEMA=DWT
```

Application automatically uses it as `DWT_SCHEMA`.

## What to Do Now

1. ✅ Create `.env` file with `DWT_SCHEMA=DWT` and `CDR_SCHEMA=CDR`
2. ✅ Verify Oracle permissions are granted
3. ✅ Restart your application
4. ✅ Test updating column description (should work now!)
5. ✅ Check logs to verify schema prefixes are applied

## No More Synonyms Needed! 🎉

You can now remove all synonyms from CDR schema:
```sql
-- No longer needed!
DROP SYNONYM dwmapr;
DROP SYNONYM dwmaprdtl;
DROP SYNONYM dwmaprsql;
DROP SYNONYM dwmaperr;
DROP SYNONYM dwparams;
-- etc...
```

The application handles schema qualification automatically.

## Questions?

See `TWO_SCHEMA_ARCHITECTURE.md` for complete documentation including:
- Detailed architecture explanation
- Migration guides
- Usage examples
- Advanced scenarios

## Date
November 12, 2025

