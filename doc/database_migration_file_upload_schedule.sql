-- ============================================================================
-- Database Migration Script: File Upload Schedule Metadata
-- ============================================================================
-- Purpose:
--   Define DMS_FLUPLD_SCHD to store schedules for file uploads, similar to
--   DMS_RPRT_SCHD for report scheduling.
--
--   This table lives in the METADATA database and is used by the scheduler
--   service to decide when to trigger file upload executions.
--
-- Naming conventions:
--   - Table:  DMS_FLUPLD_SCHD
--   - Columns avoid vowels in the core schedule-related names (FRQNCY, TM_PRM)
--   - Re‑use existing flag/audit patterns: CRTDBY, CRTDT, UPTDBY, UPTDT, CURFLG
-- ============================================================================

-- ============================================================================
-- PostgreSQL
-- ============================================================================

CREATE TABLE IF NOT EXISTS dms_flupld_schd (
    schdid     BIGSERIAL PRIMARY KEY,
    flupldref  VARCHAR(50) NOT NULL,      -- FK to DMS_FLUPLD.FLUPLDREF
    frqncy     VARCHAR(10) NOT NULL,      -- DL, WK, MN, HY, YR, ID, etc.
    tm_prm     VARCHAR(100),              -- e.g. DL_10:30, WK_MON_10:30, MN_15_10:30
    nxt_run_dt TIMESTAMP,                 -- Next scheduled run timestamp
    lst_run_dt TIMESTAMP,                 -- Last run timestamp
    stts       VARCHAR(20) NOT NULL,      -- ACTIVE, PAUSED, etc.
    crtdby     VARCHAR(100),
    crtdt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby     VARCHAR(100),
    uptdt      TIMESTAMP,
    curflg     CHAR(1)  DEFAULT 'Y'       -- Y=current, N=historical
);

COMMENT ON TABLE dms_flupld_schd IS 'File upload schedule definitions (metadata)';
COMMENT ON COLUMN dms_flupld_schd.schdid     IS 'Schedule ID';
COMMENT ON COLUMN dms_flupld_schd.flupldref  IS 'File upload reference (links to DMS_FLUPLD.FLUPLDREF)';
COMMENT ON COLUMN dms_flupld_schd.frqncy     IS 'Frequency code (DL, WK, MN, HY, YR, ID)';
COMMENT ON COLUMN dms_flupld_schd.tm_prm     IS 'Time parameter (e.g., DL_10:30, WK_MON_10:30, MN_15_10:30)';
COMMENT ON COLUMN dms_flupld_schd.nxt_run_dt IS 'Next scheduled run timestamp';
COMMENT ON COLUMN dms_flupld_schd.lst_run_dt IS 'Last run timestamp';
COMMENT ON COLUMN dms_flupld_schd.stts       IS 'Schedule status (ACTIVE, PAUSED, etc.)';
COMMENT ON COLUMN dms_flupld_schd.curflg     IS 'Current flag: Y=active row, N=historical version';

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_flupld_schd_flupldref ON dms_flupld_schd(flupldref);
CREATE INDEX IF NOT EXISTS idx_flupld_schd_frqncy    ON dms_flupld_schd(frqncy);
CREATE INDEX IF NOT EXISTS idx_flupld_schd_nxtrun   ON dms_flupld_schd(nxt_run_dt);


-- ============================================================================
-- Oracle
-- ============================================================================
/*
CREATE TABLE dms_flupld_schd (
    schdid     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flupldref  VARCHAR2(50)   NOT NULL,  -- FK to DMS_FLUPLD.FLUPLDREF
    frqncy     VARCHAR2(10)   NOT NULL,  -- DL, WK, MN, HY, YR, ID, etc.
    tm_prm     VARCHAR2(100),            -- e.g., DL_10:30, WK_MON_10:30, MN_15_10:30
    nxt_run_dt TIMESTAMP(6),             -- Next scheduled run
    lst_run_dt TIMESTAMP(6),             -- Last run
    stts       VARCHAR2(20)   NOT NULL,  -- ACTIVE, PAUSED, etc.
    crtdby     VARCHAR2(100),
    crtdt      TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    uptdby     VARCHAR2(100),
    uptdt      TIMESTAMP(6),
    curflg     CHAR(1)      DEFAULT 'Y'  -- Y=current, N=historical
);

COMMENT ON TABLE dms_flupld_schd IS 'File upload schedule definitions (metadata)';
COMMENT ON COLUMN dms_flupld_schd.schdid     IS 'Schedule ID';
COMMENT ON COLUMN dms_flupld_schd.flupldref  IS 'File upload reference (links to DMS_FLUPLD.FLUPLDREF)';
COMMENT ON COLUMN dms_flupld_schd.frqncy     IS 'Frequency code (DL, WK, MN, HY, YR, ID)';
COMMENT ON COLUMN dms_flupld_schd.tm_prm     IS 'Time parameter (e.g., DL_10:30, WK_MON_10:30)';
COMMENT ON COLUMN dms_flupld_schd.nxt_run_dt IS 'Next scheduled run timestamp';
COMMENT ON COLUMN dms_flupld_schd.lst_run_dt IS 'Last run timestamp';
COMMENT ON COLUMN dms_flupld_schd.stts       IS 'Schedule status (ACTIVE, PAUSED, etc.)';
COMMENT ON COLUMN dms_flupld_schd.curflg     IS 'Current flag: Y=active row, N=historical version';

CREATE INDEX idx_flupld_schd_flupldref ON dms_flupld_schd(flupldref);
CREATE INDEX idx_flupld_schd_frqncy    ON dms_flupld_schd(frqncy);
CREATE INDEX idx_flupld_schd_nxtrun   ON dms_flupld_schd(nxt_run_dt);
*/

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This table is part of the METADATA schema (same DB as DMS_FLUPLD).
-- 2. The scheduler service will be extended to:
--      - Read ACTIVE rows from DMS_FLUPLD_SCHD
--      - Enqueue file upload executions when NXT_RUN_DT is due
--      - Update LST_RUN_DT / NXT_RUN_DT / STTS after each run
-- 3. Frontend scheduling UI for file uploads will call a dedicated FastAPI
--    endpoint to insert/update rows in this table (similar to report schedules).
-- ============================================================================


