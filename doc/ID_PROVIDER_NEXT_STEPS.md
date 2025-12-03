# ID Provider Implementation - Next Steps Checklist

## ✅ Completed

- [x] Created ID provider module (`modules/common/id_provider.py`)
- [x] Updated `pkgdms_job_python.py` to use ID provider
- [x] Updated `pkgdms_mapr_python.py` to use ID provider
- [x] Updated `execution_engine.py` to use ID provider
- [x] Updated `pkgdms_job_create_job_flow.py` to use ID provider
- [x] Updated `pkgdwprc_python.py` to use ID provider
- [x] Added database detection (Oracle/PostgreSQL)
- [x] Created migration guide documentation
- [x] Created DDL scripts for DMS_IDPOOL table

## 🔄 Remaining Tasks

### 1. Database Setup

- [ ] **Create DMS_IDPOOL table in Oracle**
  - [ ] Run Oracle DDL from `doc/database_migration_id_provider.sql`
  - [ ] Verify table created successfully
  - [ ] Grant necessary permissions to application user

- [ ] **Create DMS_IDPOOL table in PostgreSQL** (if using PostgreSQL)
  - [ ] Run PostgreSQL DDL from `doc/database_migration_id_provider.sql`
  - [ ] Verify table created successfully
  - [ ] Grant necessary permissions to application user

- [ ] **Verify/Create Sequences** (if using SEQUENCE mode)
  - [ ] Oracle: Verify all required sequences exist
  - [ ] PostgreSQL: Create sequences if they don't exist
  - [ ] Test sequence access with application user

### 2. Configuration

- [ ] **Verify DMS_PARAMS entries exist**
  ```sql
  SELECT * FROM DMS_PARAMS 
  WHERE PRTYP = 'DMSCONFIG' 
    AND PRCD IN ('ID_GENERATION_MODE', 'ID_BLOCK_SIZE');
  ```
  - [ ] `ID_GENERATION_MODE` = 'SEQUENCE' or 'TABLE_COUNTER'
  - [ ] `ID_BLOCK_SIZE` = '500' (or desired value)

- [ ] **Test configuration loading**
  - [ ] Run test script to verify ID provider reads DMS_PARAMS correctly
  - [ ] Check application logs for config loading messages

### 3. Testing

- [ ] **Unit Testing**
  - [ ] Test ID generation with Oracle connection
  - [ ] Test ID generation with PostgreSQL connection
  - [ ] Test SEQUENCE mode
  - [ ] Test TABLE_COUNTER mode
  - [ ] Test error handling and fallbacks

- [ ] **Integration Testing**
  - [ ] Create a mapping (uses DMS_MAPRSEQ, DMS_MAPRDTLSEQ)
  - [ ] Create a job (uses DMS_JOBSEQ, DMS_JOBDTLSEQ, DMS_JOBFLWSEQ)
  - [ ] Schedule a job (uses DMS_JOBSCHSEQ)
  - [ ] Execute a job (uses DMS_PRCLOGSEQ, DMS_JOBLOGSEQ, DMS_JOBERRSEQ)
  - [ ] Verify all IDs are generated correctly
  - [ ] Verify no duplicate IDs

- [ ] **Performance Testing**
  - [ ] Test ID generation speed with SEQUENCE mode
  - [ ] Test ID generation speed with TABLE_COUNTER mode
  - [ ] Compare performance if both modes available
  - [ ] Monitor database load during ID generation

### 4. Production Deployment

- [ ] **Pre-deployment Checklist**
  - [ ] Backup current database
  - [ ] Document current sequence values (for rollback if needed)
  - [ ] Plan deployment window
  - [ ] Prepare rollback plan

- [ ] **Deployment Steps**
  - [ ] Deploy code changes
  - [ ] Run DDL scripts (DMS_IDPOOL table)
  - [ ] Verify DMS_PARAMS configuration
  - [ ] Test ID generation in staging/pre-production
  - [ ] Monitor application logs

- [ ] **Post-deployment Verification**
  - [ ] Verify all operations generate IDs correctly
  - [ ] Check for any ID-related errors in logs
  - [ ] Monitor for 24-48 hours
  - [ ] Verify no duplicate IDs in production tables

### 5. Documentation

- [ ] **Update Team Documentation**
  - [ ] Share migration guide with team
  - [ ] Document configuration options
  - [ ] Create runbook for troubleshooting

- [ ] **Update API/User Documentation** (if applicable)
  - [ ] Document any user-visible changes
  - [ ] Update configuration guides

### 6. Optional Enhancements

- [ ] **Per-Entity Configuration**
  - [ ] Consider if any entities need different ID generation modes
  - [ ] Add per-entity overrides in DMS_PARAMS if needed

- [ ] **Monitoring & Alerting**
  - [ ] Add monitoring for ID generation failures
  - [ ] Set up alerts for duplicate ID detection
  - [ ] Monitor DMS_IDPOOL table growth (if using TABLE_COUNTER)

- [ ] **Optimization**
  - [ ] Tune `ID_BLOCK_SIZE` based on usage patterns
  - [ ] Consider caching strategies if needed
  - [ ] Optimize DMS_IDPOOL queries if performance issues arise

## Testing Scripts

### Quick Test Script

Create `test_id_provider.py`:
```python
from database.dbconnect import create_oracle_connection
from modules.common.id_provider import next_id, refresh_id_config

def test_id_generation():
    conn = create_oracle_connection()
    cursor = conn.cursor()
    
    try:
        # Test each entity
        entities = [
            "DMS_PRCLOGSEQ",
            "DMS_JOBLOGSEQ", 
            "DMS_JOBERRSEQ",
            "DMS_JOBSCHSEQ",
            "DMS_MAPRSEQ",
            "DMS_MAPRDTLSEQ",
            "DMS_MAPRSQLSEQ",
            "DMS_MAPERRSEQ"
        ]
        
        print("Testing ID Generation:")
        for entity in entities:
            try:
                id_val = next_id(cursor, entity)
                print(f"  ✓ {entity}: {id_val}")
            except Exception as e:
                print(f"  ✗ {entity}: ERROR - {e}")
        
        # Test multiple IDs
        print("\nTesting sequential IDs:")
        for i in range(5):
            id_val = next_id(cursor, "DMS_PRCLOGSEQ")
            print(f"  ID {i+1}: {id_val}")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_id_generation()
```

## Rollback Plan

If issues occur:

1. **Immediate Rollback:**
   - Revert code to previous version from git
   - Restart application
   - Monitor for stability

2. **Data Integrity:**
   - Check for any duplicate IDs
   - Verify all operations completed successfully
   - Review application logs

3. **Investigation:**
   - Review error logs
   - Check DMS_PARAMS configuration
   - Verify database connectivity
   - Test ID generation in isolation

## Support Contacts

- **Technical Lead**: [Your contact]
- **Database Admin**: [DBA contact]
- **Documentation**: See `doc/ID_PROVIDER_MIGRATION_GUIDE.md`

## Notes

- All code changes have been committed to DMS repository
- Migration guide is available in `doc/ID_PROVIDER_MIGRATION_GUIDE.md`
- DDL scripts are in `doc/database_migration_id_provider.sql`
- Test thoroughly in non-production environment first




