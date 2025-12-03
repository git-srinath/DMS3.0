-- ================================================================
-- DATABASE MIGRATION: Add Connection Support to Manage SQL Module
-- ================================================================
-- Date: 2025-11-13
-- Purpose: Add SQLCONID column to DMS_MAPRSQL table to support 
--          source database connection strings similar to mapper module
-- ================================================================

-- Step 1: Add SQLCONID column to DMS_MAPRSQL table
-- This column will store the connection ID from DMS_DBCONDTLS table
-- NULL value means use the default metadata connection
ALTER TABLE DMS_MAPRSQL ADD (SQLCONID NUMBER);

-- Step 2: Add foreign key constraint to DMS_DBCONDTLS
ALTER TABLE DMS_MAPRSQL ADD CONSTRAINT FK_DMS_MAPRSQL_SQLCONID 
    FOREIGN KEY (SQLCONID) REFERENCES DMS_DBCONDTLS(CONID);

-- Step 3: Add comment to document the column
COMMENT ON COLUMN DMS_MAPRSQL.SQLCONID IS 'Source database connection ID from DMS_DBCONDTLS. NULL means use metadata connection.';

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify column was added
SELECT column_name, data_type, nullable 
FROM user_tab_columns 
WHERE table_name = 'DMS_MAPRSQL' 
AND column_name = 'SQLCONID';

-- Verify foreign key constraint
SELECT constraint_name, constraint_type, r_constraint_name
FROM user_constraints
WHERE table_name = 'DMS_MAPRSQL'
AND constraint_name = 'FK_DMS_MAPRSQL_SQLCONID';

-- Check existing SQL records (should all have NULL SQLCONID initially)
SELECT DMS_MAPRSQLCD, SQLCONID, CURFLG
FROM DMS_MAPRSQL
WHERE CURFLG = 'Y';

-- Verify connection table has active connections
SELECT CONID, CONNM, DBHOST, DBSRVNM, CURFLG
FROM DMS_DBCONDTLS
WHERE CURFLG = 'Y';

-- ================================================================
-- ROLLBACK (if needed)
-- ================================================================
-- Run these commands only if you need to undo the changes:
-- ALTER TABLE DMS_MAPRSQL DROP CONSTRAINT FK_DMS_MAPRSQL_SQLCONID;
-- ALTER TABLE DMS_MAPRSQL DROP COLUMN SQLCONID;

-- ================================================================
-- NOTES
-- ================================================================
-- 1. Existing SQL records will have NULL SQLCONID (using metadata connection)
-- 2. New SQL records can optionally specify a source connection
-- 3. The connection must exist in DMS_DBCONDTLS and have CURFLG = 'Y'
-- 4. This allows SQL queries to pull data from external databases
-- ================================================================

