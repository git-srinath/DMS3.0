# Target Connection Feature - Quick Testing Guide 🧪

**Status:** ✅ Ready to Test  
**Date:** November 13, 2025

---

## 🚀 Quick Start

### 1. Start the Application

```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Access Mapper Module

1. Open browser to `http://localhost:3000` (or your frontend URL)
2. Login to the application
3. Navigate to **Mapper Module**

---

## 🎯 What to Look For

### New UI Element

You should see a new dropdown field in the Mapper form:
- **Label:** "Target Connection (Optional)"
- **Position:** After the "Bulk Process Rows" field
- **Default:** "Use Metadata Connection"

The dropdown will list all active database connections from your `DMS_DBCONDTLS` table.

---

## ✅ Test Scenarios (5 minutes)

### Test 1: View Connection Dropdown (30 seconds)
**Steps:**
1. Open Mapper Module
2. Create new mapping or open existing one
3. Scroll to form section

**Expected:**
- ✅ See "Target Connection (Optional)" dropdown
- ✅ Default shows "Use Metadata Connection"
- ✅ List shows your registered connections

**Screenshot Location:** After "Bulk Process Rows" field

---

### Test 2: Create Mapping WITH Target Connection (2 minutes)
**Steps:**
1. Click "New Mapping" or enter new reference
2. Fill in basic details:
   - Reference: `TEST_TRG_CONN_1`
   - Description: `Test with target connection`
   - Target Schema: `TEST_SCHEMA`
   - Table Name: `TEST_TABLE`
   - Table Type: `DIM`
   - Source System: `TEST_SYS`
3. **Select a connection** from "Target Connection" dropdown
4. Add at least one mapping detail row
5. Click Save

**Expected:**
- ✅ Save succeeds
- ✅ Success message appears
- ✅ Reload the mapping - selected connection should persist

**Database Verification:**
```sql
SELECT MAPREF, MAPDESC, TRGCONID 
FROM DMS_MAPR 
WHERE MAPREF = 'TEST_TRG_CONN_1' AND CURFLG = 'Y';
```
**Expected:** `TRGCONID` should have a numeric value (e.g., 1, 2, 3...)

---

### Test 3: Create Mapping WITHOUT Target Connection (2 minutes)
**Steps:**
1. Create new mapping: `TEST_NO_CONN_1`
2. Fill in basic details
3. **Leave** "Target Connection" as "Use Metadata Connection"
4. Add mapping details
5. Save

**Expected:**
- ✅ Save succeeds
- ✅ Reload - shows "Use Metadata Connection"

**Database Verification:**
```sql
SELECT MAPREF, MAPDESC, TRGCONID 
FROM DMS_MAPR 
WHERE MAPREF = 'TEST_NO_CONN_1' AND CURFLG = 'Y';
```
**Expected:** `TRGCONID` should be `NULL`

---

### Test 4: Update Existing Mapping (1 minute)
**Steps:**
1. Open mapping from Test 2 (`TEST_TRG_CONN_1`)
2. Change the target connection to a different one (or to "Use Metadata Connection")
3. Save
4. Reload

**Expected:**
- ✅ Save succeeds
- ✅ New connection is reflected in dropdown
- ✅ Database updated

---

### Test 5: Load Existing Mappings (30 seconds)
**Steps:**
1. Open a mapping that has a target connection set
2. Verify dropdown shows the correct connection
3. Open a mapping without target connection
4. Verify dropdown shows "Use Metadata Connection"

**Expected:**
- ✅ Correct connection displayed in both cases

---

## 🐛 Error Scenarios to Test (Optional)

### Invalid Connection ID
**Setup:**
```sql
-- Manually set invalid TRGCONID
UPDATE DMS_MAPR 
SET TRGCONID = 999999 
WHERE MAPREF = 'TEST_TRG_CONN_1' AND CURFLG = 'Y';
COMMIT;
```

**Test:**
1. Open the mapping
2. Try to save (make any small change first)

**Expected:**
- ❌ Error message: "Target connection ID 999999 not found or inactive"

**Cleanup:**
```sql
UPDATE DMS_MAPR 
SET TRGCONID = NULL 
WHERE MAPREF = 'TEST_TRG_CONN_1' AND CURFLG = 'Y';
COMMIT;
```

---

## 📊 Database Queries for Verification

### Check Your Connections
```sql
SELECT CONID, CONNM, DBHOST, DBSRVNM, CURFLG 
FROM DMS_DBCONDTLS 
ORDER BY CONNM;
```

### View All Mappings with Connections
```sql
SELECT 
    m.MAPREF,
    m.MAPDESC,
    m.TRGCONID,
    c.CONNM as CONNECTION_NAME,
    c.DBHOST || '/' || c.DBSRVNM as TARGET_DATABASE
FROM DMS_MAPR m
LEFT JOIN DMS_DBCONDTLS c ON m.TRGCONID = c.CONID AND c.CURFLG = 'Y'
WHERE m.CURFLG = 'Y'
ORDER BY m.MAPREF;
```

### Check Specific Mapping
```sql
SELECT 
    MAPREF, 
    MAPDESC, 
    TRGCONID,
    TRGSCHM,
    TRGTBNM
FROM DMS_MAPR 
WHERE MAPREF = 'YOUR_MAPPING_REF' AND CURFLG = 'Y';
```

---

## ✅ Success Criteria

The feature is working correctly if:

1. ✅ Connection dropdown appears in Mapper form
2. ✅ Dropdown lists active connections from database
3. ✅ Can save mapping WITH target connection (TRGCONID has value)
4. ✅ Can save mapping WITHOUT target connection (TRGCONID is NULL)
5. ✅ Selected connection persists after save/reload
6. ✅ Can change connection and save again
7. ✅ Invalid connection IDs are rejected with error message

---

## 🔍 Troubleshooting

### Dropdown is Empty
**Check:**
```sql
SELECT COUNT(*) FROM DMS_DBCONDTLS WHERE CURFLG = 'Y';
```
**If count is 0:** You need to register at least one database connection in the DB Connections module.

### Connection Doesn't Appear in Dropdown
**Check:**
```sql
SELECT CONID, CONNM, CURFLG FROM DMS_DBCONDTLS WHERE CONID = <your_id>;
```
**Fix:** Make sure `CURFLG = 'Y'`

### Save Fails with "Connection not found"
**Cause:** The selected connection was deactivated or deleted.  
**Fix:** Select a different connection or use "Use Metadata Connection"

### Dropdown Not Visible
**Check:**
1. Clear browser cache and reload
2. Check browser console for JavaScript errors
3. Verify frontend server is running
4. Check network tab - API call to `/mapper/get-connections` should succeed

---

## 📞 Support

If you encounter any issues:

1. **Check Backend Logs:** `backend/dwtool.log`
2. **Check Browser Console:** F12 → Console tab
3. **Check Network Tab:** F12 → Network tab → Look for failed API calls
4. **Database Verification:** Run the SQL queries above

---

## 🎉 Success!

If all tests pass, the target connection feature is working correctly! 

The application can now:
- Display available database connections
- Save target connection preference with mappings
- Load and display the selected connection
- Validate connection IDs

**Next Phase:** Update data processing logic to actually use these target connections for object creation and data loading.

---

**Testing Guide Version:** 1.0  
**Last Updated:** November 13, 2025  
**Status:** Ready for Testing ✅

