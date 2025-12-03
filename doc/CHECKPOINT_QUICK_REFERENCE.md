# Checkpoint/Restart - Quick Reference

## 🚀 Quick Setup (3 Steps)

### 1. Run Migration
```bash
sqlplus user/pass@db @doc/database_migration_add_checkpoint.sql
```

### 2. Configure Mapping
```sql
-- With unique key (RECOMMENDED)
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'KEY',
    CHKPNTCOLUMN = 'YOUR_KEY_COLUMN',
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'YOUR_MAPPING';

-- Without unique key (FALLBACK)
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'PYTHON',
    CHKPNTENABLED = 'Y'
WHERE MAPREF = 'YOUR_MAPPING';
```

### 3. Regenerate Job
```python
pkgdms_job.create_update_job(connection, 'YOUR_MAPPING')
```

---

## 📊 Strategy Comparison

| Strategy | Speed | Requirements | Database Support | Recommended |
|----------|-------|--------------|------------------|-------------|
| **KEY** | ⚡⚡⚡ | Sequential column | ✅ All | ⭐ YES |
| **PYTHON** | ⚡ | None | ✅ All | 🔄 Fallback |
| **NONE** | N/A | None | ✅ All | Small tables only |

---

## 🔍 Quick Checks

### View Current Checkpoint
```sql
SELECT param1 as checkpoint, status
FROM DMS_PRCLOG
WHERE mapref = 'YOUR_MAPREF'
  AND status = 'IP'
ORDER BY reccrdt DESC
FETCH FIRST 1 ROW ONLY;
```

### Clear Checkpoint (Force Full Reload)
```sql
UPDATE DMS_PRCLOG
SET PARAM1 = NULL
WHERE mapref = 'YOUR_MAPREF'
  AND sessionid = :current_session;
```

### Check Configuration
```sql
SELECT CHKPNTSTRATEGY, CHKPNTCOLUMN, CHKPNTENABLED
FROM DMS_MAPR
WHERE MAPREF = 'YOUR_MAPREF';
```

---

## ✅ Good Checkpoint Columns

```sql
-- ✅ Sequential IDs
CHKPNTCOLUMN = 'ORDER_ID'
CHKPNTCOLUMN = 'TRANSACTION_ID'
CHKPNTCOLUMN = 'CUSTOMER_KEY'

-- ✅ Timestamps
CHKPNTCOLUMN = 'CREATED_DATE'
CHKPNTCOLUMN = 'MODIFIED_TIMESTAMP'

-- ✅ Date partitions
CHKPNTCOLUMN = 'TRANSACTION_DATE'
```

---

## ❌ Bad Checkpoint Columns

```sql
-- ❌ Random/UUIDs (not sequential)
CHKPNTCOLUMN = 'GUID'

-- ❌ Non-unique
CHKPNTCOLUMN = 'STATUS'

-- ❌ Can decrease
CHKPNTCOLUMN = 'BALANCE'

-- ❌ Nullable
CHKPNTCOLUMN = 'OPTIONAL_DATE'
```

---

## 🎯 Usage Scenarios

### Scenario 1: Large Fact Table (1M+ rows)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'KEY',
    CHKPNTCOLUMN = 'TRANSACTION_ID',
    CHKPNTENABLED = 'Y',
    BLKPRCROWS = 5000  -- 5K per batch
WHERE MAPREF = 'SALES_FACT';
```

### Scenario 2: Dimension from Complex View
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'PYTHON',
    CHKPNTENABLED = 'Y',
    BLKPRCROWS = 1000  -- Smaller batches
WHERE MAPREF = 'CUSTOMER_DIM_VIEW';
```

### Scenario 3: Small Lookup (< 1000 rows)
```sql
UPDATE DMS_MAPR 
SET CHKPNTSTRATEGY = 'NONE',
    CHKPNTENABLED = 'N'
WHERE MAPREF = 'COUNTRY_LOOKUP';
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Job always starts fresh | Check `CHKPNTENABLED = 'Y'` in DMS_MAPR |
| "Checkpoint column not found" | Ensure column in source query result |
| Skips wrong rows (PYTHON) | Switch to KEY strategy or add ORDER BY |
| Slow restarts | Use KEY strategy, reduce batch size |

---

## 📐 How It Works

```
┌─────────────────────────────────────────────┐
│ KEY Strategy (Efficient)                     │
├─────────────────────────────────────────────┤
│ SELECT * FROM source                         │
│ WHERE transaction_id > :checkpoint           │
│ ORDER BY transaction_id                      │
│                                              │
│ ✅ Database filters data                     │
│ ✅ Fast restart                              │
│ ✅ Works with any RDBMS                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ PYTHON Strategy (Universal)                  │
├─────────────────────────────────────────────┤
│ cursor.execute(source_query)                 │
│ for i in range(rows_to_skip):                │
│     cursor.fetchone()  # Skip                │
│ # Process from here                          │
│                                              │
│ ✅ Works with any source                     │
│ ⚠️  Must fetch & skip (slower)               │
└─────────────────────────────────────────────┘
```

---

## 📋 Configuration Options

| Column | Values | Default | Description |
|--------|--------|---------|-------------|
| CHKPNTSTRATEGY | AUTO, KEY, PYTHON, NONE | AUTO | Strategy type |
| CHKPNTCOLUMN | Column name | NULL | Sequential column for KEY |
| CHKPNTENABLED | Y, N | Y | Enable/disable |

**AUTO behavior:**
- If CHKPNTCOLUMN specified → KEY
- If CHKPNTCOLUMN NULL → PYTHON

---

## 📚 Full Documentation

- **CHECKPOINT_RESTART_GUIDE.md** - Complete guide with examples
- **database_migration_add_checkpoint.sql** - Migration script
- **IMPLEMENTATION_SUMMARY.md** - Technical details

---

**Version:** 1.0 (Phase 1 - Minimal)  
**Database Support:** Oracle, SQL Server, PostgreSQL, MySQL, Snowflake, BigQuery  
**Status:** ✅ Production Ready

