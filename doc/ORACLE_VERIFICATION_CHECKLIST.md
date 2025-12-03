# Oracle ID Provider - Quick Verification Checklist

## Pre-Verification

- [x] DMS_IDPOOL table created
- [x] DMS_PARAMS entries configured
- [x] Code changes deployed

## Quick Verification Steps

### 1. Verify DMS_PARAMS Configuration

```sql
SELECT PRCD, PRVAL, PRDESC 
FROM DMS_PARAMS 
WHERE PRTYP = 'DMSCONFIG' 
  AND PRCD IN ('ID_GENERATION_MODE', 'ID_BLOCK_SIZE');
```

**Expected Results:**
- `ID_GENERATION_MODE` = `SEQUENCE` (or `TABLE_COUNTER`)
- `ID_BLOCK_SIZE` = `500`

### 2. Verify Sequences Exist (if using SEQUENCE mode)

```sql
-- Check sequences in current schema
SELECT sequence_name, last_number 
FROM user_sequences 
WHERE sequence_name LIKE 'DW%SEQ'
ORDER BY sequence_name;

-- Check sequences in DWT schema (if using schema prefix)
SELECT sequence_owner, sequence_name, last_number 
FROM all_sequences 
WHERE sequence_name LIKE 'DW%SEQ'
  AND sequence_owner = 'DWT'
ORDER BY sequence_name;
```

**Required Sequences:**
- DMS_PRCLOGSEQ
- DMS_JOBLOGSEQ
- DMS_JOBERRSEQ
- DMS_JOBSCHSEQ
- DMS_MAPRSEQ
- DMS_MAPRDTLSEQ
- DMS_MAPRSQLSEQ
- DMS_MAPERRSEQ
- DWT.DMS_JOBSEQ (if using schema prefix)
- DWT.DMS_JOBDTLSEQ (if using schema prefix)
- DWT.DMS_JOBFLWSEQ (if using schema prefix)

### 3. Verify DMS_IDPOOL Table (if using TABLE_COUNTER mode)

```sql
-- Check table exists
SELECT table_name 
FROM user_tables 
WHERE table_name = 'DMS_IDPOOL';

-- Check table structure
DESC DMS_IDPOOL;

-- Check if seeded (optional)
SELECT entity_name, current_value, block_size 
FROM DMS_IDPOOL 
ORDER BY entity_name;
```

### 4. Test ID Generation

**Option A: Run Python Test Script**
```bash
python test_id_provider_oracle.py
```

**Option B: Manual SQL Test (if using SEQUENCE mode)**
```sql
-- Test each sequence
SELECT DMS_PRCLOGSEQ.NEXTVAL FROM dual;
SELECT DMS_JOBLOGSEQ.NEXTVAL FROM dual;
-- etc.
```

### 5. Test Application Functions

- [ ] **Create a Mapping**
  - Go to Mapper module
  - Create a new mapping
  - Verify no errors in logs
  - Check DMS_MAPR table for new record with valid ID

- [ ] **Create a Job**
  - Go to Jobs module
  - Create/update a job
  - Verify no errors in logs
  - Check DMS_JOB, DMS_JOBDTL, DMS_JOBFLW tables for valid IDs

- [ ] **Schedule a Job**
  - Schedule a job
  - Verify no errors
  - Check DMS_JOBSCH table for valid ID

- [ ] **Execute a Job**
  - Run a job
  - Verify no errors
  - Check DMS_PRCLOG, DMS_JOBLOG tables for valid IDs

### 6. Check Application Logs

Look for:
- ✓ "ID Provider config loaded" messages
- ✓ Successful ID generation
- ✗ Any "ID provider failed" warnings
- ✗ Any sequence-related errors

## Common Issues & Solutions

### Issue: "Sequence X returned no value"
**Solution:**
- Verify sequence exists: `SELECT * FROM user_sequences WHERE sequence_name = 'X'`
- Check permissions: `SELECT * FROM user_tab_privs WHERE table_name = 'X'`
- Try: `GRANT SELECT ON sequence_name TO your_user;`

### Issue: "Unsupported database type"
**Solution:**
- Verify connection is Oracle (not PostgreSQL)
- Check connection module in logs

### Issue: "DMS_IDPOOL table not found" (in TABLE_COUNTER mode)
**Solution:**
- Run DDL script: `doc/database_migration_id_provider.sql`
- Verify table exists: `SELECT * FROM user_tables WHERE table_name = 'DMS_IDPOOL'`

### Issue: IDs are not sequential
**Solution:**
- This is normal with TABLE_COUNTER mode (block allocation)
- If using SEQUENCE mode, IDs should be sequential
- Check if multiple applications are generating IDs

## Success Criteria

✅ All sequences accessible (if using SEQUENCE mode)  
✅ DMS_IDPOOL table exists (if using TABLE_COUNTER mode)  
✅ Test script runs without errors  
✅ Application functions work without ID-related errors  
✅ Generated IDs are valid (not null, positive integers)  
✅ No duplicate IDs in production tables  

## Next Steps (After Oracle Verification)

Once Oracle is verified:
1. Document any issues encountered
2. Test in production-like environment
3. Monitor for 24-48 hours
4. Plan PostgreSQL testing (when ready)

## PostgreSQL Testing (Later)

When ready to test PostgreSQL:
1. Set up PostgreSQL metadata database
2. Create DMS_IDPOOL table (PostgreSQL DDL)
3. Create sequences in PostgreSQL
4. Update connection settings
5. Run test script (modify for PostgreSQL)
6. Verify all functionality

See `doc/ID_PROVIDER_MIGRATION_GUIDE.md` for PostgreSQL-specific steps.




