# ID Provider Migration Guide

## Overview

This guide covers the migration steps required to use the new database-agnostic ID provider system that supports both Oracle and PostgreSQL for metadata operations.

## What Changed

- **Before**: Direct Oracle sequence calls (`sequence.NEXTVAL`)
- **After**: ID provider that supports Oracle sequences, PostgreSQL sequences, or table-based counters

## Prerequisites

1. **DMS_PARAMS Configuration** (Already completed):
   - `PRTYP='DMSCONFIG'`, `PRCD='ID_GENERATION_MODE'`, `PRVAL='SEQUENCE'` (or `'TABLE_COUNTER'`)
   - `PRTYP='DMSCONFIG'`, `PRCD='ID_BLOCK_SIZE'`, `PRVAL='500'`

2. **Database Access**: Ensure your application user has necessary permissions

## Migration Steps

### Step 1: Create DMS_IDPOOL Table (Required for TABLE_COUNTER mode)

Run the appropriate DDL script from `doc/database_migration_id_provider.sql`:

**For Oracle:**
```sql
CREATE TABLE DMS_IDPOOL (
    entity_name    VARCHAR2(64) PRIMARY KEY,
    current_value  NUMBER(20)   NOT NULL,
    block_size     NUMBER(10)   DEFAULT 500,
    updated_at     TIMESTAMP(6) DEFAULT SYSTIMESTAMP
);
```

**For PostgreSQL:**
```sql
CREATE TABLE DMS_IDPOOL (
    entity_name    VARCHAR(64) PRIMARY KEY,
    current_value  BIGINT      NOT NULL,
    block_size     INTEGER     DEFAULT 500,
    updated_at     TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP
);
```

### Step 2: Verify Sequences Exist (For SEQUENCE mode)

If using `ID_GENERATION_MODE='SEQUENCE'`, ensure all required sequences exist:

**Oracle Sequences:**
```sql
-- Check existing sequences
SELECT sequence_name FROM user_sequences 
WHERE sequence_name LIKE 'DW%SEQ' OR sequence_name LIKE '%DW%SEQ';

-- Required sequences:
-- DMS_PRCLOGSEQ, DMS_JOBLOGSEQ, DMS_JOBERRSEQ, DMS_JOBSCHSEQ
-- DMS_MAPRSEQ, DMS_MAPRDTLSEQ, DMS_MAPRSQLSEQ, DMS_MAPERRSEQ
-- DWT.DMS_JOBSEQ, DWT.DMS_JOBDTLSEQ, DWT.DMS_JOBFLWSEQ (if using schema prefix)
```

**PostgreSQL Sequences:**
```sql
-- Check existing sequences
SELECT sequence_name FROM information_schema.sequences 
WHERE sequence_name LIKE 'dw%seq' OR sequence_name LIKE '%dw%seq';

-- Create if missing (example):
CREATE SEQUENCE DMS_PRCLOGSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DMS_JOBLOGSEQ START WITH 1 INCREMENT BY 1;
-- ... etc
```

### Step 3: Choose ID Generation Mode

#### Option A: Use SEQUENCE Mode (Default - Recommended if sequences exist)

**Oracle:**
- Sequences must exist and be accessible
- No additional setup required
- Fastest performance

**PostgreSQL:**
- Sequences must exist (create if needed)
- Uses `nextval('sequence_name')` syntax
- Fastest performance

#### Option B: Use TABLE_COUNTER Mode (Fallback)

**When to use:**
- Sequences don't exist or can't be created
- Need database-agnostic solution
- PostgreSQL without sequences

**Configuration:**
```sql
-- Update DMS_PARAMS
UPDATE DMS_PARAMS 
SET PRVAL = 'TABLE_COUNTER' 
WHERE PRTYP = 'DMSCONFIG' AND PRCD = 'ID_GENERATION_MODE';

COMMIT;
```

**Seed DMS_IDPOOL (if migrating from sequences):**
```sql
-- Get current sequence values first
SELECT sequence_name, last_number FROM user_sequences 
WHERE sequence_name LIKE 'DW%SEQ';

-- Then seed DMS_IDPOOL with current values (example):
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) 
VALUES ('DMS_PRCLOGSEQ', <current_value>, 500);
-- Repeat for all entities
```

### Step 4: Test ID Generation

**Test Script:**
```python
from database.dbconnect import create_oracle_connection
from modules.common.id_provider import next_id, refresh_id_config

conn = create_oracle_connection()
cursor = conn.cursor()

# Test ID generation
try:
    test_id = next_id(cursor, "DMS_PRCLOGSEQ")
    print(f"Generated ID: {test_id}")
    
    # Test multiple IDs
    for i in range(5):
        id_val = next_id(cursor, "DMS_PRCLOGSEQ")
        print(f"ID {i+1}: {id_val}")
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()
```

### Step 5: Verify Application Functionality

1. **Create a mapping** - Should generate DMS_MAPRSEQ ID
2. **Create a job** - Should generate DMS_JOBSEQ, DMS_JOBDTLSEQ, DMS_JOBFLWSEQ IDs
3. **Schedule a job** - Should generate DMS_JOBSCHSEQ ID
4. **Execute a job** - Should generate DMS_PRCLOGSEQ, DMS_JOBLOGSEQ IDs
5. **Check logs** - Verify IDs are sequential and correct

## Troubleshooting

### Error: "Unsupported database type"
- **Cause**: Database is not Oracle or PostgreSQL
- **Solution**: Metadata database must be Oracle or PostgreSQL

### Error: "Sequence X returned no value"
- **Cause**: Sequence doesn't exist or no access
- **Solution**: 
  - Create the sequence, OR
  - Switch to TABLE_COUNTER mode

### Error: "DMS_IDPOOL table not found" (in TABLE_COUNTER mode)
- **Cause**: DMS_IDPOOL table not created
- **Solution**: Run DDL script from Step 1

### IDs are not sequential
- **Cause**: Using TABLE_COUNTER with block allocation
- **Solution**: This is expected behavior - IDs are allocated in blocks of 500

### Performance issues with TABLE_COUNTER
- **Cause**: Frequent database commits for ID allocation
- **Solution**: 
  - Increase `ID_BLOCK_SIZE` in DMS_PARAMS (e.g., 1000 or 2000)
  - Consider using SEQUENCE mode if possible

## Rollback Plan

If you need to revert to direct sequence calls:

1. **Restore old code** from git history
2. **Update DMS_PARAMS** to remove ID provider config (optional)
3. **Keep DMS_IDPOOL table** (harmless if unused)

## PostgreSQL-Specific Notes

1. **Sequence Naming**: PostgreSQL sequences are case-sensitive. Use lowercase or quoted identifiers.
2. **Schema Support**: Use schema-qualified names: `schema.sequencename`
3. **Permissions**: Ensure `USAGE` permission on sequences:
   ```sql
   GRANT USAGE ON SEQUENCE DMS_PRCLOGSEQ TO app_user;
   ```

## Oracle-Specific Notes

1. **Schema Prefix**: If sequences are in a different schema, use `schema.SEQUENCENAME`
2. **Synonyms**: Can create synonyms for easier access:
   ```sql
   CREATE SYNONYM DMS_PRCLOGSEQ FOR DWT.DMS_PRCLOGSEQ;
   ```
3. **Permissions**: Ensure `SELECT` permission on sequences

## Next Steps After Migration

1. ✅ Monitor ID generation in production
2. ✅ Verify no duplicate IDs
3. ✅ Check performance metrics
4. ✅ Update documentation for your team
5. ✅ Consider per-entity overrides if needed:
   ```sql
   -- Example: Use TABLE_COUNTER for one entity, SEQUENCE for others
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT)
   VALUES ('DMSCONFIG', 'ID_MODE_DMS_PRCLOGSEQ', 'Override for DMS_PRCLOGSEQ', 'TABLE_COUNTER', SYSTIMESTAMP, SYSTIMESTAMP);
   ```

## Support

For issues or questions:
1. Check application logs for ID provider errors
2. Verify DMS_PARAMS configuration
3. Test ID generation in isolation (see Step 4)
4. Review this guide's troubleshooting section




