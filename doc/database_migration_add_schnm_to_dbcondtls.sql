-- ================================================================
-- DATABASE MIGRATION: Add SCHNM (Schema Name) to DMS_DBCONDTLS
-- ================================================================
-- Date: 2026-02-19
-- Purpose: Capture explicit schema name for each DB connection.
--          SCHNM is mandatory for all connections.
--
-- Rollout policy:
--   1) Add SCHNM nullable
--   2) Backfill from existing USRNM
--   3) Enforce NOT NULL
-- ================================================================

-- ================================================================
-- ORACLE METADATA DATABASE
-- ================================================================
-- 1) Add column (nullable)
ALTER TABLE DMS_DBCONDTLS ADD (SCHNM VARCHAR2(128));

-- 2) Backfill existing rows from USRNM
UPDATE DMS_DBCONDTLS
SET SCHNM = USRNM
WHERE SCHNM IS NULL;

-- 3) Enforce mandatory
ALTER TABLE DMS_DBCONDTLS MODIFY (SCHNM NOT NULL);

-- 4) Add documentation
COMMENT ON COLUMN DMS_DBCONDTLS.SCHNM IS 'Schema name for this connection (mandatory). Use USRNM value when schema is not separately applicable.';

-- 5) Verify
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'DMS_DBCONDTLS'
AND COLUMN_NAME = 'SCHNM';

SELECT CONID, CONNM, USRNM, SCHNM, CURFLG
FROM DMS_DBCONDTLS
ORDER BY CONID;

COMMIT;


-- ================================================================
-- POSTGRESQL METADATA DATABASE
-- ================================================================
-- NOTE: Run this section instead of Oracle section when metadata DB is PostgreSQL.

-- 1) Add column (nullable)
-- ALTER TABLE dms_dbcondtls ADD COLUMN IF NOT EXISTS schnm VARCHAR(128);

-- 2) Backfill existing rows from usrnm
-- UPDATE dms_dbcondtls
-- SET schnm = usrnm
-- WHERE schnm IS NULL;

-- 3) Enforce mandatory
-- ALTER TABLE dms_dbcondtls
-- ALTER COLUMN schnm SET NOT NULL;

-- 4) Add documentation
-- COMMENT ON COLUMN dms_dbcondtls.schnm IS 'Schema name for this connection (mandatory). Use usrnm value when schema is not separately applicable.';

-- 5) Verify
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE lower(table_name) = 'dms_dbcondtls'
-- AND lower(column_name) = 'schnm';

-- SELECT conid, connm, usrnm, schnm, curflg
-- FROM dms_dbcondtls
-- ORDER BY conid;

-- COMMIT;
