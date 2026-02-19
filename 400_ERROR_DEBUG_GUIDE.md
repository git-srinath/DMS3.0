# Database Wizard - 400 Error Debugging Guide

## Recent Changes

### 1. ✓ Simplified Suggestions Display
Changed the suggestions list in Step 3 to show only:
- **PRCD** (Parameter Code) - as primary text
- **PRDESC** (Parameter Description) - as secondary text

Removed:
- SUGGESTED_VALUE 
- CONFIDENCE percentage
- Other metadata

File: `frontend/src/app/parameters/DatabaseWizard.js` (Lines 225-250)

### 2. ✓ Enhanced Input Validation
Added comprehensive validation on Step 0 to prevent bad requests:
- Database type required (non-empty)
- Database description required (non-empty)
- Database type must be 2-30 characters
- Database type can only contain: letters, numbers, underscores
- Database type automatically converted to uppercase

These validations prevent invalid 400 errors before they reach the backend.

### 3. ✓ Added Console Logging
Added detailed console logging to help debug the 400 error:
- Each API call is logged with request/response
- Error messages are logged with context

File: `frontend/src/app/parameters/DatabaseWizard.js` (Lines 133-168)

## Debugging the 400 Error

If you still get a 400 error when clicking CREATE:

### Step 1: Check Browser Console
1. **Open browser console**: Press `F12` or right-click → "Inspect" → "Console" tab
2. **Look for messages starting with `[DatabaseWizard]`**:
   ```
   [DatabaseWizard] Adding database: MYDB
   [DatabaseWizard] Add database response: {status: 'success', ...}
   ```
3. **Note which step fails** (Adding database or Cloning datatypes)
4. **Copy the exact error message shown**

### Step 2: Common Causes of 400 Errors

#### A) Database Already Exists
**Error**: `Database type 'MYDB' already exists`
**Solution**: Use a different database name that hasn't been created before

#### B) Database Name Contains Invalid Characters
**Error**: `DBTYP and DBDESC are required`
**Solution**: Ensure name uses only letters, numbers, underscores (A-Z, 0-9, _)

#### C) Invalid or Special Characters in Description
**Solution**: Use simple ASCII text for description (letters, numbers, spaces, punctuation)

#### D) Clone Datatypes Failed
**Error** (on clone step): `Database created but failed to clone datatypes`
**Solution**: 
- The database was created successfully
- But copying datatype mappings failed
- Usually means GENERIC database doesn't have compatible datatypes
- Database is still usable, datatypes can be added manually later

### Step 3: Test with Server Logs
When the backend server is running, check its logs for more details:

1. **Backend logs** will show:
   ```
   INFO:     127.0.0.1:XXXX - "POST /mapping/supported_database_add HTTP/1.1" 400 Bad Request
   ```

2. **Check what the actual error detail is** in the response

## Test Script

Run this command to test if the endpoints are working:

```powershell
# Make sure backend is running first
cd d:\DMS\DMSTOOL
python test_create_flow.py
```

This will:
1. Create a test database
2. Clone datatypes
3. Report any errors

## Files Modified

### Frontend
- `frontend/src/app/parameters/DatabaseWizard.js`
  - Simplified suggestion display (PRCD + PRDESC only)
  - Enhanced input validation on Step 0
  - Added console logging for debugging
  - Better error message handling

### API Hook
- `frontend/src/hooks/useDatatypeAPI.js`
  - Improved error propagation

## Quick Checklist Before Creating

- [ ] Backend server is running (`python start_fastapi.bat` or similar)
- [ ] Database name is 2-30 characters
- [ ] Database name uses only: A-Z, 0-9, _ (underscores)
- [ ] Database description is not empty
- [ ] Database name doesn't already exist in system
- [ ] No special characters in database name
- [ ] Browser cache cleared (Ctrl+Shift+Delete)
- [ ] Page refreshed (Ctrl+R)

## How to Fix the Most Common 400 Error

**Most common cause**: Database name already exists

1. Open browser console (F12)
2. Check the error message
3. If it says "already exists", try a different name:
   - `SNOWFLAKE_DEV` 
   - `POSTGRES_TEST2401`
   - `MYSQL_PROD_01`
4. Try creating again

## Still Having Issues?

Please provide:
1. **Exact error message** shown in wizard
2. **Browser console output** (F12 → Console tab)
3. **Database name you tried to create**
4. **Description you used**
5. **Backend server log output** (if available)
