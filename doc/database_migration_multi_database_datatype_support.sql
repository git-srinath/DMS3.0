-- ================================================================
-- DATABASE MIGRATION: Add DBTYP Column and Multi-Database Support
-- ================================================================
-- Date: February 16, 2026
-- Purpose: Enable database-specific datatype management for multi-database support
-- Version: 1.0
-- ================================================================

-- CRITICAL: Back up metadata database before running this migration!

-- ================================================================
-- PART 1: Add DBTYP Column to DMS_PARAMS Table
-- ================================================================

-- For ORACLE
-- ALTER TABLE DMS_PARAMS ADD (DBTYP VARCHAR2(50) DEFAULT 'GENERIC');
-- 
-- For PostgreSQL
-- ALTER TABLE dms_params ADD COLUMN dbtyp VARCHAR(50) DEFAULT 'GENERIC';

-- Note: Execute the appropriate statement based on your database type above


-- ================================================================
-- PART 2: Create DMS_SUPPORTED_DATABASES Table (ORACLE VERSION)
-- ================================================================

CREATE TABLE DMS_SUPPORTED_DATABASES (
    DBID NUMBER PRIMARY KEY,
    DBTYP VARCHAR2(50) UNIQUE NOT NULL,
    DBDESC VARCHAR2(200),
    DBVRSN VARCHAR2(50),
    STATUS VARCHAR2(20) DEFAULT 'ACTIVE',
    CRTDBY VARCHAR2(100),
    CRTDT TIMESTAMP DEFAULT SYSDATE,
    UPDTDBY VARCHAR2(100),
    UPDTDT TIMESTAMP
);

-- Create sequence for DBID
CREATE SEQUENCE DMS_SUPPORTED_DATABASES_SEQ START WITH 1 INCREMENT BY 1;

-- Create trigger for auto-increment DBID (Oracle specific)
CREATE OR REPLACE TRIGGER DMS_SUPPORTED_DATABASES_TRG
BEFORE INSERT ON DMS_SUPPORTED_DATABASES
FOR EACH ROW
BEGIN
    IF :NEW.DBID IS NULL THEN
        SELECT DMS_SUPPORTED_DATABASES_SEQ.NEXTVAL INTO :NEW.DBID FROM DUAL;
    END IF;
END;
/

-- Add comments for Oracle
COMMENT ON TABLE DMS_SUPPORTED_DATABASES IS 'Database type registry for multi-database datatype support (Oracle version)';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.DBID IS 'Primary key - Database type ID';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.DBTYP IS 'Unique database type identifier (ORACLE, POSTGRESQL, MYSQL, SNOWFLAKE, etc.)';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.DBDESC IS 'Human-readable database description';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.DBVRSN IS 'Database version information';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.STATUS IS 'ACTIVE or INACTIVE status';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.CRTDBY IS 'Created by user/system';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.CRTDT IS 'Creation timestamp';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.UPDTDBY IS 'Last updated by user/system';
COMMENT ON COLUMN DMS_SUPPORTED_DATABASES.UPDTDT IS 'Last update timestamp';


-- ================================================================
-- PART 3: Create DMS_SUPPORTED_DATABASES Table (PostgreSQL VERSION)
-- ================================================================

-- For PostgreSQL, uncomment and use this version instead:
/*
CREATE TABLE IF NOT EXISTS dms_supported_databases (
    dbid SERIAL PRIMARY KEY,
    dbtyp VARCHAR(50) UNIQUE NOT NULL,
    dbdesc VARCHAR(200),
    dbvrsn VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    crtdby VARCHAR(100),
    crtdt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updtdby VARCHAR(100),
    updtdt TIMESTAMP
);

-- Add comments for PostgreSQL
COMMENT ON TABLE dms_supported_databases IS 'Database type registry for multi-database datatype support (PostgreSQL version)';
COMMENT ON COLUMN dms_supported_databases.dbid IS 'Primary key - Database type ID';
COMMENT ON COLUMN dms_supported_databases.dbtyp IS 'Unique database type identifier (ORACLE, POSTGRESQL, MYSQL, SNOWFLAKE, etc.)';
COMMENT ON COLUMN dms_supported_databases.dbdesc IS 'Human-readable database description';
COMMENT ON COLUMN dms_supported_databases.dbvrsn IS 'Database version information';
COMMENT ON COLUMN dms_supported_databases.status IS 'ACTIVE or INACTIVE status';
COMMENT ON COLUMN dms_supported_databases.crtdby IS 'Created by user/system';
COMMENT ON COLUMN dms_supported_databases.crtdt IS 'Creation timestamp';
COMMENT ON COLUMN dms_supported_databases.updtdby IS 'Last updated by user/system';
COMMENT ON COLUMN dms_supported_databases.updtdt IS 'Last update timestamp';
*/


-- ================================================================
-- PART 4: Add Constraints and Indexes
-- ================================================================

-- Unique constraint on PRTYP + DBTYP + PRCD (Oracle version)
ALTER TABLE DMS_PARAMS 
ADD CONSTRAINT UK_DMS_PARAMS_TYPE_DB_CODE 
UNIQUE (PRTYP, DBTYP, PRCD);

-- Index for fast datatype lookups (Oracle version)
CREATE INDEX IDX_DMS_PARAMS_DATATYPE_DB 
ON DMS_PARAMS(PRTYP, DBTYP, PRCD);

-- Index for database status lookup
CREATE INDEX IDX_DMS_SUPPORTED_DB_STATUS 
ON DMS_SUPPORTED_DATABASES(STATUS, DBTYP);

-- For PostgreSQL, uncomment index creation:
/*
-- Unique constraint on PRTYP + DBTYP + PRCD (PostgreSQL version)
ALTER TABLE dms_params 
ADD CONSTRAINT uk_dms_params_type_db_code 
UNIQUE (prtyp, dbtyp, prcd);

-- Index for fast datatype lookups (PostgreSQL version)
CREATE INDEX idx_dms_params_datatype_db 
ON dms_params(prtyp, dbtyp, prcd);

-- Index for database status lookup
CREATE INDEX idx_dms_supported_db_status 
ON dms_supported_databases(status, dbtyp);
*/


-- ================================================================
-- PART 5: Seed Initial Data - GENERIC Database Reference
-- ================================================================

-- Insert GENERIC database entry (Oracle syntax)
INSERT INTO DMS_SUPPORTED_DATABASES (DBTYP, DBDESC, DBVRSN, STATUS, CRTDBY)
VALUES ('GENERIC', 'Generic/Universal Datatypes (Reference)', NULL, 'ACTIVE', 'SYSTEM');

-- Add GENERIC tag to existing DATATYPE parameters for backward compatibility
UPDATE DMS_PARAMS 
SET DBTYP = 'GENERIC' 
WHERE PRTYP = 'Datatype' AND DBTYP IS NULL;

-- Commit changes
COMMIT;

-- For PostgreSQL, use:
/*
INSERT INTO dms_supported_databases (dbtyp, dbdesc, dbvrsn, status, crtdby)
VALUES ('GENERIC', 'Generic/Universal Datatypes (Reference)', NULL, 'ACTIVE', 'SYSTEM');

UPDATE dms_params 
SET dbtyp = 'GENERIC' 
WHERE prtyp = 'Datatype' AND dbtyp IS NULL;

COMMIT;
*/


-- ================================================================
-- PART 6: Verification Queries
-- ================================================================

-- Verify DBTYP column was added
SELECT column_name, data_type, nullable 
FROM user_tab_columns 
WHERE table_name = 'DMS_PARAMS' 
AND column_name = 'DBTYP';

-- Verify DMS_SUPPORTED_DATABASES table created
SELECT table_name 
FROM user_tables 
WHERE table_name = 'DMS_SUPPORTED_DATABASES';

-- Verify GENERIC database entry
SELECT DBID, DBTYP, DBDESC, STATUS 
FROM DMS_SUPPORTED_DATABASES
WHERE DBTYP = 'GENERIC';

-- Verify existing DATATYPE parameters have GENERIC tag
SELECT PRTYP, DBTYP, PRCD, PRDESC, PRVAL
FROM DMS_PARAMS
WHERE PRTYP = 'Datatype'
ORDER BY PRCD;

-- For PostgreSQL, use lowercase versions:
/*
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'dms_params'
AND column_name = 'dbtyp';

SELECT table_name
FROM information_schema.tables
WHERE table_name = 'dms_supported_databases';

SELECT dbid, dbtyp, dbdesc, status
FROM dms_supported_databases
WHERE dbtyp = 'GENERIC';

SELECT prtyp, dbtyp, prcd, prdesc, prval
FROM dms_params
WHERE prtyp = 'Datatype'
ORDER BY prcd;
*/


-- ================================================================
-- PART 7: Rollback Instructions (if needed)
-- ================================================================

-- If this migration needs to be undone:
--
-- 1. Drop new indexes:
--    DROP INDEX IDX_DMS_PARAMS_DATATYPE_DB;
--    DROP INDEX IDX_DMS_SUPPORTED_DB_STATUS;
--
-- 2. Drop constraints:
--    ALTER TABLE DMS_PARAMS DROP CONSTRAINT UK_DMS_PARAMS_TYPE_DB_CODE;
--
-- 3. Drop new table:
--    DROP TABLE DMS_SUPPORTED_DATABASES;
--    DROP SEQUENCE DMS_SUPPORTED_DATABASES_SEQ;
--
-- 4. Remove DBTYP column from DMS_PARAMS:
--    ALTER TABLE DMS_PARAMS DROP COLUMN DBTYP;
--
-- 5. Rollback to previous Git commit:
--    git checkout 2b04090


-- ================================================================
-- NOTES FOR IMPLEMENTATION
-- ================================================================

-- 1. Backup metadata database BEFORE running this migration
--
-- 2. Execute appropriate version based on your database type:
--    - Use ORACLE syntax if your metadata database is Oracle
--    - Use PostgreSQL syntax if your metadata database is PostgreSQL
--
-- 3. Run verification queries after migration to confirm success
--
-- 4. New database types can be added via DMS_SUPPORTED_DATABASES:
--    INSERT INTO DMS_SUPPORTED_DATABASES (DBTYP, DBDESC, STATUS, CRTDBY)
--    VALUES ('SNOWFLAKE', 'Snowflake Cloud DW', 'ACTIVE', 'username');
--
-- 5. New datatypes for new database can be pre-filled from GENERIC:
--    - Backend will provide pre-fill wizard
--    - User confirms mapping suggestions
--    - System creates new records with mapped types
--
-- 6. Deletion safeguards: Parameters cannot be deleted if in use
--    - Check referential integrity before allowing deletion
--    - Warn user if datatype used in mappings/jobs/uploads


-- ================================================================
-- Migration Status: Ready for Execution
-- ================================================================
-- Created: 2026-02-16
-- Tested: No (test in DEV environment first)
-- Ready for Production: After testing in DEV/QA
-- Estimated Execution Time: 2-5 minutes
-- Expected Downtime: Minimal (migration is non-breaking)
-- Rollback Time: < 5 minutes if issues occur
-- ================================================================
