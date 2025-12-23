-- ============================================================================
-- Database Migration Script: File Upload Execution History
-- ============================================================================
-- Purpose: Create tables to track file upload execution history and error rows
-- 
-- Tables:
--   1. DMS_FLUPLD_RUN (metadata DB) - Execution history/run records
--   2. DMS_FLUPLD_ERR (target DB) - Invalid rows that failed to load
--
-- ============================================================================

-- ============================================================================
-- METADATA DATABASE: DMS_FLUPLD_RUN
-- ============================================================================
-- Stores execution history for file upload jobs
-- Location: Metadata database (same as DMS_FLUPLD, DMS_FLUPLDDTL, etc.)

-- PostgreSQL
CREATE TABLE IF NOT EXISTS dms_flupld_run (
    runid      BIGSERIAL PRIMARY KEY,
    flupldref  VARCHAR(50) NOT NULL,
    strttm     TIMESTAMP   NOT NULL,           -- start_time
    ndtm       TIMESTAMP,                      -- end_time
    rwsprcssd  INTEGER    DEFAULT 0,           -- rows_processed
    rwsstccssfl INTEGER   DEFAULT 0,           -- rows_successful
    rwsfld     INTEGER    DEFAULT 0,           -- rows_failed
    stts       VARCHAR(20) NOT NULL,           -- status (SUCCESS, FAILED, PARTIAL)
    mssg       TEXT,                           -- message
    ldmde      VARCHAR(20),                    -- load_mode (INSERT, TRUNCATE_LOAD, UPSERT)
    flpth      TEXT,                           -- file_path
    crtdby     VARCHAR(100),
    crtdt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby     VARCHAR(100),
    uptdt      TIMESTAMP,
    curflg     CHAR(1)   DEFAULT 'Y'
);

COMMENT ON TABLE dms_flupld_run IS 'File upload execution history - tracks each run of a file upload job';
COMMENT ON COLUMN dms_flupld_run.runid IS 'Primary key - unique run identifier';
COMMENT ON COLUMN dms_flupld_run.flupldref IS 'File upload reference (FK to DMS_FLUPLD)';
COMMENT ON COLUMN dms_flupld_run.strttm IS 'Execution start timestamp';
COMMENT ON COLUMN dms_flupld_run.ndtm IS 'Execution end timestamp';
COMMENT ON COLUMN dms_flupld_run.rwsprcssd IS 'Total number of rows processed';
COMMENT ON COLUMN dms_flupld_run.rwsstccssfl IS 'Number of rows successfully loaded';
COMMENT ON COLUMN dms_flupld_run.rwsfld IS 'Number of rows that failed to load';
COMMENT ON COLUMN dms_flupld_run.stts IS 'Execution status: SUCCESS, FAILED, PARTIAL';
COMMENT ON COLUMN dms_flupld_run.mssg IS 'Optional summary message or top error';
COMMENT ON COLUMN dms_flupld_run.ldmde IS 'Load mode used: INSERT, TRUNCATE_LOAD, UPSERT';
COMMENT ON COLUMN dms_flupld_run.flpth IS 'Path to the file that was processed (if applicable)';
COMMENT ON COLUMN dms_flupld_run.curflg IS 'Current flag: Y=active, N=historical';

-- Create index on flupldref for faster lookups
CREATE INDEX IF NOT EXISTS idx_flupld_run_flupldref ON dms_flupld_run(flupldref);
CREATE INDEX IF NOT EXISTS idx_flupld_run_start_time ON dms_flupld_run(strttm DESC);

-- Oracle
/*
CREATE TABLE dms_flupld_run (
    runid      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flupldref  VARCHAR2(50)   NOT NULL,
    strttm     TIMESTAMP(6)   NOT NULL,        -- start_time
    ndtm       TIMESTAMP(6),                   -- end_time
    rwsprcssd  NUMBER        DEFAULT 0,        -- rows_processed
    rwsstccssfl NUMBER       DEFAULT 0,        -- rows_successful
    rwsfld     NUMBER        DEFAULT 0,        -- rows_failed
    stts       VARCHAR2(20)   NOT NULL,        -- status
    mssg       CLOB,                           -- message
    ldmde      VARCHAR2(20),                   -- load_mode
    flpth      VARCHAR2(4000),                 -- file_path
    crtdby     VARCHAR2(100),
    crtdt      TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    uptdby     VARCHAR2(100),
    uptdt      TIMESTAMP(6),
    curflg     CHAR(1)      DEFAULT 'Y'
);

COMMENT ON TABLE dms_flupld_run IS 'File upload execution history - tracks each run of a file upload job';
COMMENT ON COLUMN dms_flupld_run.runid IS 'Primary key - unique run identifier';
COMMENT ON COLUMN dms_flupld_run.flupldref IS 'File upload reference (FK to DMS_FLUPLD)';
COMMENT ON COLUMN dms_flupld_run.strttm IS 'Execution start timestamp';
COMMENT ON COLUMN dms_flupld_run.ndtm IS 'Execution end timestamp';
COMMENT ON COLUMN dms_flupld_run.rwsprcssd IS 'Total number of rows processed';
COMMENT ON COLUMN dms_flupld_run.rwsstccssfl IS 'Number of rows successfully loaded';
COMMENT ON COLUMN dms_flupld_run.rwsfld IS 'Number of rows that failed to load';
COMMENT ON COLUMN dms_flupld_run.stts IS 'Execution status: SUCCESS, FAILED, PARTIAL';
COMMENT ON COLUMN dms_flupld_run.mssg IS 'Optional summary message or top error';
COMMENT ON COLUMN dms_flupld_run.ldmde IS 'Load mode used: INSERT, TRUNCATE_LOAD, UPSERT';
COMMENT ON COLUMN dms_flupld_run.flpth IS 'Path to the file that was processed (if applicable)';
COMMENT ON COLUMN dms_flupld_run.curflg IS 'Current flag: Y=active, N=historical';

-- Create index on flupldref for faster lookups
CREATE INDEX idx_flupld_run_flupldref ON dms_flupld_run(flupldref);
CREATE INDEX idx_flupld_run_start_time ON dms_flupld_run(strttm DESC);
*/

-- ============================================================================
-- TARGET DATABASE: DMS_FLUPLD_ERR
-- ============================================================================
-- Stores invalid rows that failed to load into the target table
-- Location: Target database (same database where data is being loaded)
-- Schema: Target schema (same schema as specified in DMS_FLUPLD.trgschm)
-- Note: This table will be created in the target schema specified in the file upload config
--       The application will create this table automatically if it doesn't exist

-- PostgreSQL
CREATE TABLE IF NOT EXISTS dms_flupld_err (
    errid       BIGSERIAL PRIMARY KEY,
    flupldref   VARCHAR(50) NOT NULL,
    runid       BIGINT      NOT NULL,  -- Links to DMS_FLUPLD_RUN.runid in metadata DB
    rwndx       INTEGER     NOT NULL,  -- row_index
    rwdtjsn     JSONB,                 -- row_data_json
    rrcd        VARCHAR(50),           -- error_code
    rrmssg      TEXT       NOT NULL,   -- error_message
    crtdby      VARCHAR(100),
    crtdt       TIMESTAMP  DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dms_flupld_err IS 'File upload error rows - stores invalid rows that failed to load';
COMMENT ON COLUMN dms_flupld_err.errid IS 'Primary key - unique error record identifier';
COMMENT ON COLUMN dms_flupld_err.flupldref IS 'File upload reference (for filtering)';
COMMENT ON COLUMN dms_flupld_err.runid IS 'Execution run ID (links to DMS_FLUPLD_RUN.runid in metadata DB)';
COMMENT ON COLUMN dms_flupld_err.rwndx IS 'Row index in transformed DataFrame (0-based)';
COMMENT ON COLUMN dms_flupld_err.rwdtjsn IS 'Full row data as JSONB for easy querying';
COMMENT ON COLUMN dms_flupld_err.rrcd IS 'Parsed error code (e.g., ORA-01400, DPY-3002)';
COMMENT ON COLUMN dms_flupld_err.rrmssg IS 'Full error message from database';

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_flupld_err_flupldref ON dms_flupld_err(flupldref);
CREATE INDEX IF NOT EXISTS idx_flupld_err_runid ON dms_flupld_err(runid);
CREATE INDEX IF NOT EXISTS idx_flupld_err_rrcd ON dms_flupld_err(rrcd);

-- Oracle
/*
CREATE TABLE dms_flupld_err (
    errid       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flupldref   VARCHAR2(50) NOT NULL,
    runid       NUMBER       NOT NULL,  -- Links to DMS_FLUPLD_RUN.runid in metadata DB
    rwndx       NUMBER       NOT NULL,  -- Row number in transformed DataFrame (0-based)
    rwdtjsn     CLOB,                   -- Full row data as JSON (stored as CLOB, can be parsed)
    rrcd        VARCHAR2(50),           -- Parsed error code (e.g., ORA-01400, DPY-3002)
    rrmssg      CLOB        NOT NULL,   -- Full error message from database
    crtdby      VARCHAR2(100),
    crtdt       TIMESTAMP(6) DEFAULT SYSTIMESTAMP
);

COMMENT ON TABLE dms_flupld_err IS 'File upload error rows - stores invalid rows that failed to load';
COMMENT ON COLUMN dms_flupld_err.errid IS 'Primary key - unique error record identifier';
COMMENT ON COLUMN dms_flupld_err.flupldref IS 'File upload reference (for filtering)';
COMMENT ON COLUMN dms_flupld_err.runid IS 'Execution run ID (links to DMS_FLUPLD_RUN.runid in metadata DB)';
COMMENT ON COLUMN dms_flupld_err.rwndx IS 'Row index in transformed DataFrame (0-based)';
COMMENT ON COLUMN dms_flupld_err.rwdtjsn IS 'Full row data as JSON (stored as CLOB)';
COMMENT ON COLUMN dms_flupld_err.rrcd IS 'Parsed error code (e.g., ORA-01400, DPY-3002)';
COMMENT ON COLUMN dms_flupld_err.rrmssg IS 'Full error message from database';

-- Create indexes for faster lookups
CREATE INDEX idx_flupld_err_flupldref ON dms_flupld_err(flupldref);
CREATE INDEX idx_flupld_err_runid ON dms_flupld_err(runid);
CREATE INDEX idx_flupld_err_rrcd ON dms_flupld_err(rrcd);
*/

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. DMS_FLUPLD_RUN is created in the METADATA database
--    - Run this script in your metadata database
--    - This table tracks execution history across all file uploads
--
-- 2. DMS_FLUPLD_ERR is created in the TARGET database (in the target schema)
--    - This table should be created in EACH target database/schema where you load data
--    - The application will automatically create this table if it doesn't exist
--    - The table will be created in the schema specified by DMS_FLUPLD.trgschm
--
-- 3. The runid in DMS_FLUPLD_ERR is a reference to DMS_FLUPLD_RUN.runid,
--    but since they're in different databases, this is a logical reference only
--    (used for filtering/reporting, not a foreign key constraint)
--
-- 4. For Oracle, uncomment the Oracle sections and comment out the PostgreSQL sections
--
-- 5. To create DMS_FLUPLD_ERR in a specific target schema:
--    - PostgreSQL: Connect to the target database and run:
--        CREATE SCHEMA IF NOT EXISTS <target_schema>;
--        SET search_path TO <target_schema>;
--        -- Then run the DMS_FLUPLD_ERR CREATE TABLE statement
--    - Oracle: Connect as the target schema user and run the CREATE TABLE statement
--
-- 6. The application code will check for table existence and create it automatically
--    if needed, so manual creation is optional but recommended for initial setup
-- ============================================================================

