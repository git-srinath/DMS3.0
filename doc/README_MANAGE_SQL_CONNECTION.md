# Manage SQL Connection Feature - README

## 🚀 Quick Start

### What This Is
Connection string support for the `manage_sql` module - allows SQL queries to pull data from external/source databases.

### What You Need to Do
1. Run the database migration script
2. Restart your backend
3. Test the feature

---

## 📋 Files Created

### 1. Database Migration
- **`database_migration_manage_sql_connection.sql`**
  - SQL script to add `SQLCONID` column to `DWMAPRSQL` table
  - **ACTION REQUIRED:** Run this script in your database

### 2. Documentation (Read These)
- **`IMPLEMENTATION_COMPLETE.md`** ⭐ **START HERE**
  - Complete summary of what was done
  - Step-by-step action items
  
- **`MANAGE_SQL_CONNECTION_SUMMARY.md`**
  - Quick reference guide
  - API examples
  - Testing commands
  
- **`MANAGE_SQL_CONNECTION_IMPLEMENTATION.md`**
  - Full technical documentation
  - Detailed implementation notes
  
- **`MANAGE_SQL_VS_MAPPER_COMPARISON.md`**
  - Visual diagrams
  - Feature comparison with mapper module

---

## ⚡ Quick Action Items

### 1. Database Migration (Required)
```bash
sqlplus your_user/your_pass@your_db
SQL> @database_migration_manage_sql_connection.sql
```

### 2. Restart Backend
```bash
cd backend
python app.py
```

### 3. Test It
```bash
# Test connections endpoint
curl http://localhost:5000/manage-sql/get-connections

# Test save with connection
curl -X POST http://localhost:5000/manage-sql/save-sql \
  -H "Content-Type: application/json" \
  -d '{"sql_code": "TEST", "sql_content": "SELECT 1", "connection_id": "1"}'
```

---

## 📊 What Changed

### Database
- Added `SQLCONID` column to `DWMAPRSQL` table
- Added foreign key to `DWDBCONDTLS` table

### Backend
- Updated `create_update_sql()` function
- Updated `/save-sql` endpoint
- Updated `/fetch-sql-logic` endpoint
- Added `/get-connections` endpoint

### No Changes Needed
- ✅ Backward compatible
- ✅ Existing SQL queries work unchanged
- ✅ No breaking changes

---

## 🎯 Core Concept

### Before:
```
SQL Query ─→ Always uses metadata connection
```

### After:
```
SQL Query ─→ Can use any registered connection from DWDBCONDTLS
              (or NULL for metadata connection)
```

---

## 📖 Documentation Guide

**If you have 2 minutes:**
- Read: `IMPLEMENTATION_COMPLETE.md`

**If you have 5 minutes:**
- Read: `IMPLEMENTATION_COMPLETE.md`
- Read: `MANAGE_SQL_CONNECTION_SUMMARY.md`

**If you want all details:**
- Read all 4 documentation files

**If you just want to see how it compares to mapper:**
- Read: `MANAGE_SQL_VS_MAPPER_COMPARISON.md`

---

## ✅ Status

| Component       | Status          |
|-----------------|-----------------|
| Backend Code    | ✅ Complete     |
| Database Script | ✅ Ready        |
| Documentation   | ✅ Complete     |
| Testing         | ⏳ Pending      |
| Deployment      | ⏳ Pending      |

---

## 🆘 Need Help?

### Common Issues:

**"Column SQLCONID does not exist"**
→ Run the database migration script

**"Connections dropdown is empty"**
→ Check `SELECT * FROM DWDBCONDTLS WHERE CURFLG='Y'`

**"Invalid connection ID error"**
→ Connection must exist in DWDBCONDTLS and have CURFLG='Y'

### More Help:
- Check `IMPLEMENTATION_COMPLETE.md` → Troubleshooting section
- Check `MANAGE_SQL_CONNECTION_IMPLEMENTATION.md` → Full details

---

## 📞 Quick Reference

### API Endpoints (New/Updated)
```
GET  /manage-sql/get-connections    - Get available connections
POST /manage-sql/save-sql           - Save SQL (accepts connection_id)
GET  /manage-sql/fetch-sql-logic    - Fetch SQL (returns connection_id)
```

### Request Format
```json
{
  "sql_code": "SQL_001",
  "sql_content": "SELECT * FROM table",
  "connection_id": "1"  // Optional: null = metadata connection
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "sql_code": "SQL_001",
    "sql_content": "SELECT * FROM table",
    "connection_id": "1"  // null if using metadata
  }
}
```

---

## 🎉 Summary

✅ **Backend is ready**  
⚠️ **Database needs migration**  
🔄 **Frontend may need updates**

**Action:** Run the database migration script and test!

---

**File:** `README_MANAGE_SQL_CONNECTION.md`  
**Date:** November 13, 2025  
**Feature:** Source connection support for manage_sql module

