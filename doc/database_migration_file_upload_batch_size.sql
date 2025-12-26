-- ============================================================================
-- Migration: Add BATCH_SIZE column to DMS_FLUPLD table
-- Purpose: Allow users to configure batch size for file upload processing
-- Date: 2024
-- ============================================================================

-- PostgreSQL
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 1000;
COMMENT ON COLUMN dms_flupld.batch_size IS 'Number of rows to process per batch during data loading. Default: 1000. Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';

-- Update existing records to have default batch size
UPDATE dms_flupld SET batch_size = 1000 WHERE batch_size IS NULL;

-- Oracle
-- Note: Run this in Oracle SQL*Plus or SQL Developer
/*
ALTER TABLE DMS_FLUPLD ADD (BATCH_SIZE NUMBER DEFAULT 1000);
COMMENT ON COLUMN DMS_FLUPLD.BATCH_SIZE IS 'Number of rows to process per batch during data loading. Default: 1000. Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';

-- Update existing records to have default batch size
UPDATE DMS_FLUPLD SET BATCH_SIZE = 1000 WHERE BATCH_SIZE IS NULL;
COMMIT;
*/

