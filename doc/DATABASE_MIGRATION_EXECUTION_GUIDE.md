# Database Migration Execution Guide

**Phase 1 Status:** ✅ COMPLETE  
**Database Migration Status:** ⏳ READY FOR EXECUTION  
**Created:** February 16, 2026

---

## Quick Summary

Phase 1 backend implementation is **100% complete** and all code has been committed to Git (commit `0bd3296` and `9e288b4`).

The database migration script is ready to execute and will:
1. Add `DBTYP` column to `DMS_PARAMS` table
2. Create new `DMS_SUPPORTED_DATABASES` table
3. Create performance indexes

**⚠️ IMPORTANT:** This must be executed BEFORE Phase 2A work begins.

---

## Migration Script Location

**File:** `doc/database_migration_multi_database_datatype_support.sql`  
**Size:** ~270 lines  
**Time to Execute:** 2-5 minutes  
**Downtime Required:** Minimal (non-blocking operations)

---

## Pre-Execution Checklist

Before running the migration:

- [ ] Backup your metadata database (CRITICAL!)
- [ ] Identify your database type (Oracle or PostgreSQL)
- [ ] Have database admin credentials ready
- [ ] Stop any DMS services that access the metadata database
- [ ] Reserve 15-30 minutes for execution + verification

---

## Step-by-Step Execution

### For Oracle Database Users

1. **Open SQL*Plus or SQL Developer**
   ```
   sqlplus METADATA_USER/PASSWORD@database_name
   or
   Tools > SQL Worksheet in SQL Developer
   ```

2. **Navigate to migration script**
   ```
   File > Open > backend/doc/database_migration_multi_database_datatype_support.sql
   ```

3. **Review and Execute Part 1 (Add DBTYP Column)**
   - Section: "PART 1: Add DBTYP Column to DMS_PARAMS Table"
   - Uncomment the Oracle ALTER TABLE statement:
     ```sql
     ALTER TABLE DMS_PARAMS ADD (DBTYP VARCHAR2(50) DEFAULT 'GENERIC');
     ```
   - Execute this statement

4. **Execute Part 2 (Create DMS_SUPPORTED_DATABASES)**
   - Section: "PART 2: Create DMS_SUPPORTED_DATABASES Table (ORACLE VERSION)"
   - Execute these statements in order:
     - CREATE TABLE DMS_SUPPORTED_DATABASES
     - CREATE SEQUENCE DMS_SUPPORTED_DATABASES_SEQ
     - CREATE TRIGGER DMS_SUPPORTED_DATABASES_TRG
     - COMMENT statements

5. **Execute Part 4 (Create Constraints and Indexes)**
   - Section: "PART 4: Add Constraints and Indexes"
   - Execute the Oracle-specific statements only:
     - ALTER TABLE for unique constraint
     - CREATE INDEX statements (Oracle version)

6. **Execute Part 5 (Seed Initial Data)**
   - Section: "PART 5: Seed Initial Data"
   - Execute Oracle-specific INSERT statements:
     ```sql
     INSERT INTO DMS_SUPPORTED_DATABASES...
     UPDATE DMS_PARAMS SET DBTYP = 'GENERIC'...
     COMMIT;
     ```

7. **Execute Part 6 (Verification Queries)**
   - Section: "PART 6: Verification Queries"
   - Run all Oracle verification queries
   - Verify output shows:
     - DBTYP column exists in DMS_PARAMS
     - DMS_SUPPORTED_DATABASES table exists
     - GENERIC database entry was created
     - All DATATYPE parameters have DBTYP = 'GENERIC'

### For PostgreSQL Database Users

1. **Open psql or PgAdmin**
   ```
   psql -U METADATA_USER -d metadata_database
   or
   PgAdmin > Tools > Query Tool
   ```

2. **Navigate to migration script**
   ```
   File > Open > backend/doc/database_migration_multi_database_datatype_support.sql
   ```

3. **Review and Execute Part 1 (Add DBTYP Column)**
   - Section: "PART 1: Add DBTYP Column to DMS_PARAMS Table"
   - Uncomment the PostgreSQL ALTER TABLE statement:
     ```sql
     ALTER TABLE dms_params ADD COLUMN dbtyp VARCHAR(50) DEFAULT 'GENERIC';
     ```
   - Execute this statement

4. **Execute Part 3 (Create DMS_SUPPORTED_DATABASES)**
   - Section: "PART 3: Create DMS_SUPPORTED_DATABASES Table (PostgreSQL VERSION)"
   - Uncomment and execute:
     - CREATE TABLE IF NOT EXISTS dms_supported_databases
     - COMMENT ON TABLE and COLUMN statements

5. **Execute Part 4 (Create Constraints and Indexes)**
   - Section: "PART 4: Add Constraints and Indexes"
   - Execute the PostgreSQL-specific statements only (from commented section):
     - ALTER TABLE for unique constraint
     - CREATE INDEX statements (PostgreSQL version)

6. **Execute Part 5 (Seed Initial Data)**
   - Section: "PART 5: Seed Initial Data"
   - Execute PostgreSQL-specific INSERT statements (from commented section):
     ```sql
     INSERT INTO dms_supported_databases...
     UPDATE dms_params SET dbtyp = 'GENERIC'...
     COMMIT;
     ```

7. **Execute Part 6 (Verification Queries)**
   - Section: "PART 6: Verification Queries"
   - Run all PostgreSQL verification queries (from commented section)
   - Verify output shows:
     - dbtyp column exists in dms_params
     - dms_supported_databases table exists
     - GENERIC database entry was created
     - All DATATYPE parameters have dbtyp = 'GENERIC'

---

## What Each Migration Part Does

| Part | Description | Oracle | PostgreSQL | Mandatory |
|------|-------------|--------|----------|-----------|
| 1 | Add DBTYP column | ✅ | ✅ | YES |
| 2 | Create table (Oracle) | ✅ | ─ | Conditional |
| 3 | Create table (PostgreSQL) | ─ | ✅ | Conditional |
| 4 | Indexes & constraints | ✅/✅ | ✅/✅ | YES |
| 5 | Seed GENERIC data | ✅ | ✅ | YES |
| 6 | Verification queries | ✅ | ✅ | Recommended |

---

## Expected Results

After successful execution:

### Database State
- [ ] `DBTYP` column added to `DMS_PARAMS` table
- [ ] All existing DATATYPE parameters have `DBTYP = 'GENERIC'`
- [ ] `DMS_SUPPORTED_DATABASES` table created with GENERIC entry
- [ ] Indexes created for performance
- [ ] Unique constraint prevents duplicate datatypes per database

### Verification Query Output (Oracle)

```sql
DBTYP       Column Type         Nullable
─────────────────────────────────────────
DBTYP       VARCHAR2(50)        YES (default 'GENERIC')

TABLE_NAME
─────────────────────────────────────────
DMS_SUPPORTED_DATABASES

DBID  DBTYP    DBDESC                           STATUS
──────────────────────────────────────────────────────
1     GENERIC  Generic/Universal Datatypes      ACTIVE

PRTYP     DBTYP    PRCD          PRDESC         PRVAL
──────────────────────────────────────────────────────
Datatype  GENERIC  INT           Integer        INT
Datatype  GENERIC  VARCHAR       Variable Char  VARCHAR
... (all datatypes with DBTYP = 'GENERIC')
```

### Verification Query Output (PostgreSQL)

```sql
column_name  data_type         is_nullable
───────────────────────────────────────────
dbtyp        character varying  YES (default 'GENERIC')

table_name
───────────────────────────────────────────
dms_supported_databases

dbid  dbtyp    dbdesc                           status
────────────────────────────────────────────────────
1     GENERIC  Generic/Universal Datatypes      ACTIVE

prtyp     dbtyp    prcd          prdesc         prval
────────────────────────────────────────────────────
Datatype  GENERIC  INT           Integer        INT
Datatype  GENERIC  VARCHAR       Variable Char  VARCHAR
... (all datatypes with dbtyp = 'GENERIC')
```

---

## Troubleshooting

### Error: "Column already exists"
- **Cause:** DBTYP column already added in previous attempt
- **Solution:** Run verification queries to check if DBTYP column exists
- **Status:** Safe to skip PART 1 and proceed with remaining parts

### Error: "Table already exists"  
- **Cause:** DMS_SUPPORTED_DATABASES table already created
- **Solution:** DROP TABLE DMS_SUPPORTED_DATABASES; DROP SEQUENCE (Oracle only) and retry
- **Status:** Or skip table creation and proceed with constraints/indexes

### Error: "Unique constraint violation"
- **Cause:** Attempting to insert duplicate GENERIC entry
- **Solution:** Check if DMS_SUPPORTED_DATABASES already has GENERIC entry
- **Status:** Safe to skip PART 5 insert if GENERIC already exists

### Transaction Timeout
- **Cause:** Database operations taking too long
- **Solution:** Increase connection timeout, retry in off-peak hours
- **Status:** Safe to retry; migration is idempotent

### Permission Denied
- **Cause:** Logged in as non-admin user
- **Solution:** Use database admin account or get admin to execute script
- **Status:** Operations require ALTER TABLE and CREATE TABLE privileges

---

## Post-Execution Steps

After successful migration:

1. **Run all verification queries** to confirm changes

2. **Test the new API endpoints** using curl or Postman:
   ```bash
   curl http://localhost:8000/mapping/supported_databases
   ```
   Expected response:
   ```json
   {
     "status": "success",
     "count": 1,
     "databases": [
       {
         "DBTYP": "GENERIC",
         "DBDESC": "Generic/Universal Datatypes (Reference)",
         "DBVRSN": null,
         "STTS": "ACTIVE"
       }
     ]
   }
   ```

3. **Restart DMS services** if they were stopped

4. **Begin Phase 2A implementation** (API endpoints)

---

## Rollback Instructions

If the migration fails or needs to be undone:

### For Oracle

```sql
-- Drop indexes
DROP INDEX IDX_DMS_PARAMS_DATATYPE_DB;
DROP INDEX IDX_DMS_SUPPORTED_DB_STATUS;

-- Drop constraint
ALTER TABLE DMS_PARAMS DROP CONSTRAINT UK_DMS_PARAMS_TYPE_DB_CODE;

-- Drop table and sequence
DROP TABLE DMS_SUPPORTED_DATABASES;
DROP SEQUENCE DMS_SUPPORTED_DATABASES_SEQ;

-- Remove DBTYP column
ALTER TABLE DMS_PARAMS DROP COLUMN DBTYP;

COMMIT;
```

### For PostgreSQL

```sql
-- Drop indexes
DROP INDEX idx_dms_params_datatype_db;
DROP INDEX idx_dms_supported_db_status;

-- Drop constraint
ALTER TABLE dms_params DROP CONSTRAINT uk_dms_params_type_db_code;

-- Drop table (PostgreSQL auto-drops sequence)
DROP TABLE dms_supported_databases;

-- Remove DBTYP column
ALTER TABLE dms_params DROP COLUMN dbtyp;

COMMIT;
```

### If Needed: Rollback Code Changes

```bash
git checkout 4c313f6  # Returns to pre-Phase 1 state
```

**Estimated rollback time:** < 15 minutes

---

## Timeline

| Task | Estimated Time | Status |
|------|---|---|
| Backup database | 5-10 min | ⏳ TO DO |
| Execute migration | 2-5 min | ⏳ TO DO |
| Run verification | 2-3 min | ⏳ TO DO |
| Test new endpoints | 5 min | ⏳ TO DO |
| Restart services | 2 min | ⏳ TO DO |
| **Total** | **15-30 min** | ⏳ TO DO |

---

## Questions?

- **Migration Details:** See `doc/database_migration_multi_database_datatype_support.sql`
- **API Documentation:** See `doc/PHASE1_IMPLEMENTATION_COMPLETE.md`
- **Backend Code:** See `backend/modules/helper_functions.py`
- **API Endpoints:** See `backend/modules/parameters/fastapi_parameter_mapping.py`

---

## Sign-Off

Migration script: ✅ READY FOR EXECUTION  
Code implementation: ✅ COMPLETE  
Documentation: ✅ COMPLETE  
Remote backup: ✅ SECURE

**Next Step:** Execute this migration, then proceed to Phase 2A

---

*Migration Guide Created: February 16, 2026*  
*Git Commits: 0bd3296, 9e288b4*
