-- ================================================================
-- DATABASE MIGRATION: Add Connection Support to Manage SQL Module
-- ================================================================
-- Date: 2025-11-13
-- Purpose: Add SQLCONID column to DWMAPRSQL table to support 
--          source database connection strings similar to mapper module
-- ================================================================

-- Step 1: Add SQLCONID column to DWMAPRSQL table
-- This column will store the connection ID from DWDBCONDTLS table
-- NULL value means use the default metadata connection
ALTER TABLE DWMAPRSQL ADD (SQLCONID NUMBER);

-- Step 2: Add foreign key constraint to DWDBCONDTLS
ALTER TABLE DWMAPRSQL ADD CONSTRAINT FK_DWMAPRSQL_SQLCONID 
    FOREIGN KEY (SQLCONID) REFERENCES DWDBCONDTLS(CONID);

-- Step 3: Add comment to document the column
COMMENT ON COLUMN DWMAPRSQL.SQLCONID IS 'Source database connection ID from DWDBCONDTLS. NULL means use metadata connection.';

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify column was added
SELECT column_name, data_type, nullable 
FROM user_tab_columns 
WHERE table_name = 'DWMAPRSQL' 
AND column_name = 'SQLCONID';

-- Verify foreign key constraint
SELECT constraint_name, constraint_type, r_constraint_name
FROM user_constraints
WHERE table_name = 'DWMAPRSQL'
AND constraint_name = 'FK_DWMAPRSQL_SQLCONID';

-- Check existing SQL records (should all have NULL SQLCONID initially)
SELECT DWMAPRSQLCD, SQLCONID, CURFLG
FROM DWMAPRSQL
WHERE CURFLG = 'Y';

-- Verify connection table has active connections
SELECT CONID, CONNM, DBHOST, DBSRVNM, CURFLG
FROM DWDBCONDTLS
WHERE CURFLG = 'Y';

-- ================================================================
-- ROLLBACK (if needed)
-- ================================================================
-- Run these commands only if you need to undo the changes:
-- ALTER TABLE DWMAPRSQL DROP CONSTRAINT FK_DWMAPRSQL_SQLCONID;
-- ALTER TABLE DWMAPRSQL DROP COLUMN SQLCONID;

-- ================================================================
-- NOTES
-- ================================================================
-- 1. Existing SQL records will have NULL SQLCONID (using metadata connection)
-- 2. New SQL records can optionally specify a source connection
-- 3. The connection must exist in DWDBCONDTLS and have CURFLG = 'Y'
-- 4. This allows SQL queries to pull data from external databases
-- ================================================================

