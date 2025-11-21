# PKGDWJOB Python - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Add RWHKEY Column

```bash
cd D:\CursorTesting\DWTOOL
sqlplus your_username/your_password@your_database @doc/database_migration_add_rwhkey.sql
```

### Step 2: Test Single Mapping

```python
from database.dbconnect import create_oracle_connection
from modules.jobs import pkgdwjob_python as pkgdwjob

connection = create_oracle_connection()
job_id = pkgdwjob.create_update_job(connection, 'YOUR_MAPREF')
print(f"Job created: {job_id}")
connection.close()
```

### Step 3: Regenerate All Jobs

```python
from database.dbconnect import create_oracle_connection
from modules.jobs import pkgdwjob_python as pkgdwjob

connection = create_oracle_connection()
pkgdwjob.create_all_jobs(connection)
connection.close()
```

---

## 📋 Checklist

- [ ] Run migration script (`database_migration_add_rwhkey.sql`)
- [ ] Verify RWHKEY column added to all DIM/FCT tables
- [ ] Test on one mapping first
- [ ] Regenerate all job flows
- [ ] Verify generated Python code in DWJOBFLW
- [ ] Test job execution

---

## ⚡ Key Commands

### Check RWHKEY Column

```sql
SELECT table_name, column_name, data_type, data_length
FROM user_tab_columns
WHERE column_name = 'RWHKEY'
ORDER BY table_name;
```

### View Generated Code

```sql
SELECT mapref, LENGTH(dwlogic) as code_length, recrdt
FROM DWJOBFLW
WHERE CURFLG = 'Y'
ORDER BY recrdt DESC;
```

### Regenerate Single Job

```python
job_id = pkgdwjob.create_update_job(connection, 'CUSTOMER_DIM_LOAD')
```

---

## 🔍 Verify Hash-Based Detection

```sql
-- Sample table with RWHKEY
SELECT 
    SKEY,
    RWHKEY,
    CUSTOMER_ID,
    NAME,
    CURFLG,
    RECUPDT
FROM CUSTOMER_DIM
WHERE CURFLG = 'Y'
  AND ROWNUM <= 5;
```

Expected: RWHKEY should be a 32-character hex string like `3a52ce780950d4d969792a2559cd519d`

---

## 📊 Before vs After

### Before (PL/SQL with Column Comparison)

```plsql
IF NVL(w_trgrec.COL1, '-1') != NVL(w_src.COL1, '-1')
OR NVL(w_trgrec.COL2, '-1') != NVL(w_src.COL2, '-1')
-- ... repeat for every column
```

### After (Python with Hash)

```python
if src_hash != tgt_hash:
    # Data changed
```

**Result:** Up to 85% faster for wide tables!

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "RWHKEY column not found" | Run migration script |
| "Module pkgdwjob_python not found" | Check `backend/modules/jobs/` path |
| "Job flow not generated" | Check mapping is active (STFLG='A') |
| "Hash always different" | Verify column order in EXCSEQ |

---

## 📚 Full Documentation

- **Implementation Guide:** `doc/PKGDWJOB_PYTHON_IMPLEMENTATION.md`
- **Hash Algorithm Details:** `doc/HASH_BASED_CHANGE_DETECTION.md`
- **Migration Script:** `doc/database_migration_add_rwhkey.sql`
- **Code Modules:**
  - `backend/modules/jobs/pkgdwjob_python.py`
  - `backend/modules/jobs/pkgdwjob_create_job_flow.py`

---

## 💡 Pro Tips

1. **Test First:** Always test on a single mapping before batch processing
2. **Check Logs:** Monitor Python console output for generation details
3. **Backup:** Keep backup of DWJOBFLW before regenerating
4. **Performance:** Hash-based detection is fastest for tables with 50+ columns
5. **Verification:** Compare old vs new job execution results

---

## ✅ Success Criteria

You're done when:
- ✅ All dimension/fact tables have RWHKEY column
- ✅ All job flows regenerated (check DWJOBFLW.RECRDT)
- ✅ Generated code uses `generate_hash()` function
- ✅ Sample job executes successfully
- ✅ Performance improvement observed

---

## 🎯 Next Steps

1. **Monitor Performance:** Track job execution times
2. **Optimize:** Adjust BULKPRC parameter if needed
3. **Document:** Note any custom modifications
4. **Train Team:** Share knowledge with team members

---

**Need Help?** Review the full documentation in `doc/PKGDWJOB_PYTHON_IMPLEMENTATION.md`

