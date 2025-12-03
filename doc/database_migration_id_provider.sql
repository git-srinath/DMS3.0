-- ============================================================================
-- ID Provider Migration Script
-- ============================================================================
-- This script creates the DMS_IDPOOL table required for TABLE_COUNTER mode
-- when sequences are not available or when using PostgreSQL.
--
-- Run the appropriate section based on your database type:
-- - Oracle: Run ORACLE section
-- - PostgreSQL: Run POSTGRESQL section
-- ============================================================================

-- ============================================================================
-- ORACLE VERSION
-- ============================================================================
CREATE TABLE DMS_IDPOOL (
    entity_name    VARCHAR2(64) PRIMARY KEY,
    current_value  NUMBER(20)   NOT NULL,
    block_size     NUMBER(10)   DEFAULT 500,
    updated_at     TIMESTAMP(6) DEFAULT SYSTIMESTAMP
);

COMMENT ON TABLE DMS_IDPOOL IS 'ID pool table for TABLE_COUNTER mode when sequences are unavailable';
COMMENT ON COLUMN DMS_IDPOOL.entity_name IS 'Entity/sequence name (e.g., DMS_PRCLOGSEQ)';
COMMENT ON COLUMN DMS_IDPOOL.current_value IS 'Last allocated ID value';
COMMENT ON COLUMN DMS_IDPOOL.block_size IS 'Block size for ID allocation (default: 500)';
COMMENT ON COLUMN DMS_IDPOOL.updated_at IS 'Last update timestamp';

-- Create index for faster lookups
CREATE INDEX IDX_DMS_IDPOOL_UPDATED ON DMS_IDPOOL(updated_at);

-- ============================================================================
-- POSTGRESQL VERSION
-- ============================================================================
/*
CREATE TABLE DMS_IDPOOL (
    entity_name    VARCHAR(64) PRIMARY KEY,
    current_value  BIGINT      NOT NULL,
    block_size     INTEGER     DEFAULT 500,
    updated_at     TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE DMS_IDPOOL IS 'ID pool table for TABLE_COUNTER mode when sequences are unavailable';
COMMENT ON COLUMN DMS_IDPOOL.entity_name IS 'Entity/sequence name (e.g., DMS_PRCLOGSEQ)';
COMMENT ON COLUMN DMS_IDPOOL.current_value IS 'Last allocated ID value';
COMMENT ON COLUMN DMS_IDPOOL.block_size IS 'Block size for ID allocation (default: 500)';
COMMENT ON COLUMN DMS_IDPOOL.updated_at IS 'Last update timestamp';

-- Create index for faster lookups
CREATE INDEX IDX_DMS_IDPOOL_UPDATED ON DMS_IDPOOL(updated_at);
*/

-- ============================================================================
-- SEED DATA (Optional - for initial setup)
-- ============================================================================
-- Uncomment and adjust starting values based on your current sequence values
-- This ensures no ID conflicts when switching from SEQUENCE to TABLE_COUNTER mode

/*
-- Oracle seed data
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_PRCLOGSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_JOBLOGSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_JOBERRSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_JOBSCHSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_MAPRSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_MAPRDTLSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_MAPRSQLSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DMS_MAPERRSEQ', 0, 500);
-- Add schema prefix if needed (e.g., 'DWT.DMS_JOBSEQ')
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DWT.DMS_JOBSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DWT.DMS_JOBDTLSEQ', 0, 500);
INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size) VALUES ('DWT.DMS_JOBFLWSEQ', 0, 500);

COMMIT;
*/




