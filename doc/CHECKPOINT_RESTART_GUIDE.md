# Checkpoint/Restart Feature - User Guide

## 🎯 Overview

The checkpoint/restart capability allows ETL jobs to resume from where they stopped instead of reprocessing already-committed data. This is critical for:

- **Long-running jobs** - Resume instead of starting over
- **Unreliable networks** - Handle connection failures gracefully
- **Resource constraints** - Process in smaller chunks over time
- **Development/Testing** - Stop and resume during testing

---

## 🔑 Key Concepts

### What is a Checkpoint?

A **checkpoint** is a marker that tracks progress during job execution. After each batch is successfully committed to the target, the checkpoint is updated. If the job fails, it can restart from the last checkpoint instead of the beginning.

### How It Works

```
Run 1:
├─ Batch 1 (1000 rows)  → Commit ✅ → Checkpoint = 1000
├─ Batch 2 (1000 rows)  → Commit ✅ → Checkpoint = 2000
├─ Batch 3 (1000 rows)  → Commit ✅ → Checkpoint = 3000
└─ Batch 4 (500 rows)   → FAIL ❌

Run 2 (Restart):
├─ Resume from Checkpoint = 3000
├─ Skip first 3000 rows
├─ Batch 4 (500 rows)   → Commit ✅ → Checkpoint = 3500
└─ Batch 5 (800 rows)   → Commit ✅ → Checkpoint = COMPLETED
```

---

## 📐 Checkpoint Strategies

### 1. **KEY Strategy** (Recommended)

Uses a sequential column from the source to track progress.

**Best For:**
- Tables with sequential IDs
- Data with timestamps
- Ordered transaction logs

**Requirements:**
- Source must have a **sequential/monotonic** column (ID, timestamp, etc.)
- Column values must be unique and increasing

**Example:**
```sql
-- Configure
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'KEY',
    CHKPNTCOLUMN = 'ORDER_ID',
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'SALES_FACT_LOAD';

-- Generated query
SELECT * FROM (
    -- Your source query
) source_data
WHERE ORDER_ID > :checkpoint_value  -- Resumes from last processed
ORDER BY ORDER_ID
```

**Advantages:**
✅ Most efficient - database filters data  
✅ Works with any RDBMS  
✅ Precise resume point  
✅ No memory of skipped rows needed  

**Disadvantages:**
❌ Requires sequential column  
❌ Won't work with unordered result sets  

---

### 2. **PYTHON Strategy** (Universal Fallback)

Tracks row count and skips rows in Python after fetching.

**Best For:**
- Complex queries without unique keys
- Views/joins without sequential columns
- When KEY strategy not possible

**Requirements:**
- None - works with any source

**Example:**
```python
# Configure
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'PYTHON',
    CHKPNTCOLUMN = NULL,
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'COMPLEX_VIEW_LOAD';

# Generated code
cursor.execute(source_query)
for skip_idx in range(rows_to_skip):  # Skip already processed
    cursor.fetchone()
# Continue processing from here
```

**Advantages:**
✅ Works with ANY source  
✅ No source modification needed  
✅ Database-agnostic  

**Disadvantages:**
❌ Must fetch and skip rows (network overhead)  
❌ Source must return consistent results  
❌ Slower on restart  

---

### 3. **AUTO Strategy** (Default)

System automatically selects the best strategy:
- If `CHKPNTCOLUMN` is specified → Use **KEY**
- If `CHKPNTCOLUMN` is NULL → Use **PYTHON**

---

### 4. **NONE Strategy** (Disable Checkpoint)

Always processes all data from the beginning.

**Best For:**
- Small lookup tables
- Delta/incremental loads (source has its own filtering)
- Jobs that must always run completely

---

## 🚀 Setup Guide

### Step 1: Run Migration Script

```bash
sqlplus your_username/your_password@your_database @doc/database_migration_add_checkpoint.sql
```

This adds three columns to DMS_MAPR:
- `CHKPNTSTRATEGY` - Strategy type ('AUTO', 'KEY', 'PYTHON', 'NONE')
- `CHKPNTCOLUMN` - Column name for KEY strategy
- `CHKPNTENABLED` - Enable/disable ('Y'/'N')

---

### Step 2: Configure Your Mappings

#### Example 1: Fact Table with Transaction ID

```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'KEY',
    CHKPNTCOLUMN = 'TRANSACTION_ID',  -- Sequential column
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'SALES_FACT_DAILY';
```

#### Example 2: Dimension with Timestamp

```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'KEY',
    CHKPNTCOLUMN = 'LAST_MODIFIED_DATE',  -- Timestamp column
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'CUSTOMER_DIM';
```

#### Example 3: Complex Query (No Unique Key)

```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'PYTHON',
    CHKPNTCOLUMN = NULL,
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'SALES_SUMMARY_VIEW';
```

#### Example 4: Small Lookup Table (Disable)

```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'NONE',
    CHKPNTENABLED = 'N'
WHERE MAPREF = 'COUNTRY_LOOKUP';
```

---

### Step 3: Regenerate Job Flows

```python
from database.dbconnect import create_oracle_connection
from modules.jobs import pkgdms_job_python as pkgdms_job

connection = create_oracle_connection()

# For specific mapping
job_id = pkgdms_job.create_update_job(connection, 'YOUR_MAPREF')

# Or for all mappings
pkgdms_job.create_all_jobs(connection)

connection.close()
```

---

## 📊 Usage Examples

### Normal Execution

```python
# Job runs and completes normally
Job SALES_FACT_DAILY started - JobLogID: 12345
No checkpoint found. Starting fresh.
Processing combination: DEFAULT
Fetching source data in batches of 1000 rows...
Processing batch 1: 1000 rows
Checkpoint updated: TRANSACTION_ID = 98765
Batch 1: Committed 1000 source rows
...
Processing batch 10: 850 rows
Checkpoint updated: TRANSACTION_ID = 107615
Batch 10: Committed 850 source rows
Checkpoint marked as COMPLETED
Job SALES_FACT_DAILY completed successfully
```

---

### Restart After Failure

```python
# First Run (Fails at batch 4)
Job SALES_FACT_DAILY started - JobLogID: 12345
Processing batch 1: 1000 rows → Checkpoint = 98765
Processing batch 2: 1000 rows → Checkpoint = 99765
Processing batch 3: 1000 rows → Checkpoint = 100765
Processing batch 4: 500 rows  → FAILED ❌

# Restart (Resumes from batch 4)
Job SALES_FACT_DAILY started - JobLogID: 12346
Resuming: Checkpoint at TRANSACTION_ID > 100765
Applied KEY checkpoint: TRANSACTION_ID > 100765
Processing batch 1: 500 rows → Checkpoint = 101265  # Continues from 100765
Processing batch 2: 1000 rows → Checkpoint = 102265
...
Checkpoint marked as COMPLETED
Job SALES_FACT_DAILY completed successfully
```

---

## 🔍 Monitoring Checkpoints

### View Current Checkpoint

```sql
SELECT sessionid, prcid, mapref, status, param1 as checkpoint
FROM DMS_PRCLOG
WHERE mapref = 'YOUR_MAPREF'
  AND status = 'IP'  -- In Progress
ORDER BY reccrdt DESC;
```

### View Checkpoint History

```sql
SELECT reccrdt, mapref, status, param1 as checkpoint, strtdt, enddt
FROM DMS_PRCLOG
WHERE mapref = 'YOUR_MAPREF'
ORDER BY reccrdt DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## 🛠️ Advanced Topics

### Force Full Reload

To ignore checkpoint and force full reload:

**Option 1: Clear checkpoint before run**
```sql
UPDATE DMS_PRCLOG
SET PARAM1 = NULL
WHERE mapref = 'YOUR_MAPREF'
  AND sessionid = :current_session;
```

**Option 2: Temporarily disable**
```sql
UPDATE DMS_MAPR
SET CHKPNTENABLED = 'N'
WHERE MAPREF = 'YOUR_MAPREF';

-- Regenerate job
-- Run job
-- Re-enable
UPDATE DMS_MAPR SET CHKPNTENABLED = 'Y' WHERE MAPREF = 'YOUR_MAPREF';
```

---

### Checkpoint Column Selection

**Good Checkpoint Columns:**
✅ Sequential primary key (`ORDER_ID`, `CUSTOMER_ID`)  
✅ Auto-incrementing numbers  
✅ Timestamps (`CREATED_DATE`, `MODIFIED_DATE`)  
✅ Date partitions (`TRANSACTION_DATE`)  

**Bad Checkpoint Columns:**
❌ Random/UUID keys (not sequential)  
❌ Non-unique columns  
❌ Columns that can decrease  
❌ Nullable columns  

---

### Handling Source Data Changes

If source data changes between runs (rows added/removed before checkpoint):

**KEY Strategy:**
- ✅ Handles new rows correctly (based on key value)
- ❌ May miss updates to older rows

**PYTHON Strategy:**
- ❌ May skip wrong rows if row count changes
- ⚠️ Best for stable/frozen source data

**Best Practice:** Use KEY strategy whenever possible.

---

## 🐛 Troubleshooting

### Issue: Job Always Starts from Beginning

**Cause:** Checkpoint not being saved

**Solution:**
```sql
-- Check if checkpoint enabled
SELECT CHKPNTENABLED FROM DMS_MAPR WHERE MAPREF = 'YOUR_MAPREF';

-- Check if checkpoint being written
SELECT param1 FROM DMS_PRCLOG 
WHERE mapref = 'YOUR_MAPREF' 
ORDER BY reccrdt DESC 
FETCH FIRST 1 ROW ONLY;
```

---

### Issue: "Invalid Checkpoint Value" Error

**Cause:** Checkpoint column data type mismatch

**Solution:**
- Ensure checkpoint column is compatible (numeric or date)
- Check for NULL values in checkpoint column
- Verify column exists in source query result

---

### Issue: Skips Too Many/Few Rows (PYTHON Strategy)

**Cause:** Source query returns different row count between runs

**Solution:**
- Use KEY strategy instead
- Ensure source query has ORDER BY for consistency
- Add WHERE clause to make source stable (e.g., date filter)

---

### Issue: Performance Degradation on Restart

**Cause:** PYTHON strategy fetching and skipping many rows

**Solution:**
- Switch to KEY strategy if possible
- Reduce batch size to checkpoint more frequently
- Add index on checkpoint column

---

## 📋 Best Practices

### 1. **Choose the Right Strategy**
- Always prefer KEY strategy when source has sequential column
- Use PYTHON only when absolutely necessary
- Disable checkpoint for small tables (< 10,000 rows)

### 2. **Select Appropriate Batch Size**
- Smaller batches = more frequent checkpoints = better resume granularity
- Larger batches = fewer checkpoints = better performance
- Recommended: 1,000 - 10,000 rows per batch

### 3. **Monitor Checkpoint Progress**
- Check DMS_PRCLOG.PARAM1 during long-running jobs
- Alert on jobs stuck at same checkpoint
- Clean up old checkpoints periodically

### 4. **Test Restart Capability**
```python
# Test process:
# 1. Start job
# 2. Cancel midway (Ctrl+C)
# 3. Restart job
# 4. Verify it resumes correctly
```

### 5. **Document Checkpoint Configuration**
```sql
-- Add comments to your mappings
COMMENT ON COLUMN DMS_MAPR.CHKPNTCOLUMN IS 
'TRANSACTION_ID is sequential and indexed for efficient checkpoint filtering';
```

---

## 🔒 Limitations

1. **KEY Strategy:**
   - Requires sequential/monotonic column
   - Won't detect changes to already-processed rows
   - Source query must return checkpoint column

2. **PYTHON Strategy:**
   - Must fetch and discard skipped rows
   - Requires consistent source query results
   - Slower on restart with large checkpoints

3. **Both:**
   - No cross-session checkpoints (each session independent)
   - No automatic cleanup of orphaned checkpoints
   - Requires manual intervention if source schema changes

---

## 🎓 FAQ

**Q: Can I change strategy after job is created?**  
A: Yes, but you must regenerate the job flow. Update DMS_MAPR and call `create_update_job`.

**Q: What happens if checkpoint column is not in source query?**  
A: Job will fail with error. Ensure your source query includes the checkpoint column.

**Q: Can I use composite keys for checkpoint?**  
A: No. Use single sequential column only. For composite keys, create a surrogate sequential column.

**Q: Does checkpoint work across different databases?**  
A: Yes! Both KEY and PYTHON strategies are database-agnostic.

**Q: How do I clear all checkpoints?**  
A: `UPDATE DMS_PRCLOG SET PARAM1 = NULL WHERE mapref = 'YOUR_MAPREF';`

---

## 📚 Related Documentation

- **IMPLEMENTATION_SUMMARY.md** - Overall implementation details
- **PKGDMS_JOB_PYTHON_IMPLEMENTATION.md** - Technical documentation
- **CORRECTIONS_LOG.md** - Bug fixes and improvements

---

**Generated:** 2025-11-14  
**Version:** 1.0 (Phase 1 - Minimal)  
**Status:** ✅ Production Ready

