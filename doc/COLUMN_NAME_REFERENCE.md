# Checkpoint Column Names Reference

## ✅ Actual Column Names Used in Your Database

The checkpoint feature uses **shortened column names** as implemented in your database:

| Original Design | Your Database | Description |
|----------------|---------------|-------------|
| `CHKPNTSTRATEGY` | **`CHKPNTSTRTGY`** | Checkpoint strategy ('AUTO', 'KEY', 'PYTHON', 'NONE') |
| `CHKPNTCOLUMN` | **`CHKPNTCLNM`** | Source column name for KEY strategy |
| `CHKPNTENABLED` | **`CHKPNTENBLD`** | Enable/disable checkpoint ('Y'/'N') |

---

## 📋 Quick Configuration Examples

### Example 1: Fact Table with Transaction ID (KEY Strategy)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRTGY = 'KEY',
    CHKPNTCLNM = 'TRANSACTION_ID',
    CHKPNTENBLD = 'Y'
WHERE MAPREF = 'SALES_FACT_LOAD';
```

### Example 2: Dimension with Timestamp (KEY Strategy)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRTGY = 'KEY',
    CHKPNTCLNM = 'MODIFIED_DATE',
    CHKPNTENBLD = 'Y'
WHERE MAPREF = 'CUSTOMER_DIM';
```

### Example 3: Complex Query without Unique Key (PYTHON Strategy)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRTGY = 'PYTHON',
    CHKPNTCLNM = NULL,
    CHKPNTENBLD = 'Y'
WHERE MAPREF = 'AGGREGATED_VIEW_LOAD';
```

### Example 4: Small Lookup Table (Disable Checkpoint)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRTGY = 'NONE',
    CHKPNTENBLD = 'N'
WHERE MAPREF = 'COUNTRY_LOOKUP';
```

### Example 5: AUTO Strategy (Let System Decide)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRTGY = 'AUTO',
    CHKPNTCLNM = 'ORDER_ID',  -- Will use KEY since column specified
    CHKPNTENBLD = 'Y'
WHERE MAPREF = 'ORDER_PROCESSING';
```

---

## 🔍 Quick Checks

### View Checkpoint Configuration
```sql
SELECT MAPREF, CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
FROM DMS_MAPR
WHERE MAPREF = 'YOUR_MAPPING';
```

### View All Configured Checkpoints
```sql
SELECT MAPREF, CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD, CURFLG
FROM DMS_MAPR
WHERE CHKPNTENBLD = 'Y'
  AND CURFLG = 'Y'
ORDER BY MAPREF;
```

### View Current Checkpoint Value
```sql
SELECT PARAM1 as checkpoint_value, STATUS
FROM DMS_PRCLOG
WHERE MAPREF = 'YOUR_MAPPING'
  AND STATUS = 'IP'
ORDER BY RECCRDT DESC
FETCH FIRST 1 ROW ONLY;
```

### Clear Checkpoint (Force Full Reload)
```sql
UPDATE DMS_PRCLOG
SET PARAM1 = NULL
WHERE MAPREF = 'YOUR_MAPPING'
  AND SESSIONID = :current_session;
```

---

## 📊 Column Details

### `CHKPNTSTRTGY` (Checkpoint Strategy)

**Type:** VARCHAR2(20)  
**Default:** 'AUTO'  
**Values:**
- `'AUTO'` - System automatically selects KEY or PYTHON based on CHKPNTCLNM
- `'KEY'` - Use source key column for filtering (recommended)
- `'PYTHON'` - Python-side cursor skip (universal fallback)
- `'NONE'` - Disable checkpoint, always full reload

---

### `CHKPNTCLNM` (Checkpoint Column Name)

**Type:** VARCHAR2(100)  
**Default:** NULL  
**Purpose:** Source column name for KEY strategy  

**Requirements:**
- Must be sequential/monotonic (e.g., ORDER_ID, TRANSACTION_ID)
- Must be present in source query result
- Should be indexed for best performance
- Examples: 'TRANSACTION_ID', 'CREATED_DATE', 'ORDER_TIMESTAMP'

**✅ Good Columns:**
- Sequential IDs: `CUSTOMER_ID`, `ORDER_ID`, `TRANSACTION_ID`
- Timestamps: `CREATED_DATE`, `MODIFIED_TIMESTAMP`
- Date fields: `TRANSACTION_DATE`, `PROCESS_DATE`

**❌ Bad Columns:**
- Random UUIDs (not sequential)
- Non-unique columns (e.g., `STATUS`)
- Nullable columns
- Columns that can decrease (e.g., `BALANCE`)

---

### `CHKPNTENBLD` (Checkpoint Enabled)

**Type:** VARCHAR2(1)  
**Default:** 'Y'  
**Values:**
- `'Y'` - Checkpoint enabled (resume on failure)
- `'N'` - Checkpoint disabled (always full reload)

---

## 🎯 Strategy Selection Guide

| Scenario | CHKPNTSTRTGY | CHKPNTCLNM | CHKPNTENBLD |
|----------|--------------|------------|-------------|
| Fact table with ID | `'KEY'` | `'TRANSACTION_ID'` | `'Y'` |
| Dimension with timestamp | `'KEY'` | `'MODIFIED_DATE'` | `'Y'` |
| View without unique key | `'PYTHON'` | `NULL` | `'Y'` |
| Small lookup table | `'NONE'` | `NULL` | `'N'` |
| Let system decide | `'AUTO'` | `'ORDER_ID'` or `NULL` | `'Y'` |

---

## 📚 Code Alignment Status

✅ **All code has been updated to use your column names:**

### Python Files Updated:
- ✅ `backend/modules/jobs/pkgdms_job_python.py`
  - `create_update_job()` - INSERT and parameter mapping
  - `create_job_flow()` - SELECT and parameter passing

- ✅ `backend/modules/jobs/pkgdms_job_create_job_flow.py`
  - Function signature parameters
  - Strategy determination logic
  - Generated code constants

### Documentation Files Updated:
- ✅ `doc/database_migration_add_checkpoint.sql`
  - ALTER TABLE statements
  - COMMENT statements
  - Example configurations
  - Verification queries

- ✅ `doc/COLUMN_NAME_REFERENCE.md` (this file)

---

## 🚀 Next Steps

1. **Verify Database Columns:**
   ```sql
   SELECT column_name, data_type, data_length, data_default
   FROM user_tab_columns
   WHERE table_name = 'DMS_MAPR'
     AND column_name IN ('CHKPNTSTRTGY', 'CHKPNTCLNM', 'CHKPNTENBLD')
   ORDER BY column_name;
   ```

2. **Configure Your Mappings:**
   - Use the examples above
   - Choose appropriate strategy for each mapping

3. **Regenerate Job Flows:**
   ```python
   from modules.jobs import pkgdms_job_python as pkgdms_job
   job_id = pkgdms_job.create_update_job(connection, 'YOUR_MAPPING')
   ```

4. **Test Checkpoint:**
   - Run job
   - Cancel midway
   - Check `DMS_PRCLOG.PARAM1` for checkpoint value
   - Restart job - should resume from checkpoint

---

## ✅ Verification Checklist

- [x] Database columns created with correct names
- [x] Python code updated to use new column names
- [x] Documentation aligned with actual column names
- [x] No linter errors
- [x] All SQL examples updated
- [x] All verification queries updated

---

**Status:** ✅ All code aligned with your column names  
**Date:** 2025-11-14  
**Ready to Use:** YES

---

## 📞 Quick Help

**Problem:** Configuration not taking effect  
**Solution:** Make sure to regenerate job flow after updating DMS_MAPR

**Problem:** "Column not found" error  
**Solution:** Ensure CHKPNTCLNM column exists in source query result

**Problem:** Job always starts from beginning  
**Solution:** Check CHKPNTENBLD = 'Y' in DMS_MAPR

**For more help, see:** `doc/CHECKPOINT_RESTART_GUIDE.md`

