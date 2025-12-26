-- ============================================================================
-- Database Migration: File Upload Module Tables
-- ============================================================================
-- Purpose: Create tables and sequences for File Upload Module
--          Supports multiple RDBMS platforms for both metadata and target databases
--          Supported databases: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, etc.
-- 
-- Date: 2025-01-XX
-- Version: 1.0
-- ============================================================================
-- Note: Table and column names follow DMS naming convention (vowels removed)
--       DMS_FLUPLD = File Upload
--       DMS_FLUPLDDTL = File Upload Detail
-- 
-- Multi-Database Support:
--   - Metadata databases: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, etc.
--   - Target databases: All supported RDBMS platforms
--   - Database-specific syntax differences handled automatically
-- ============================================================================

-- ============================================================================
-- POSTGRESQL VERSION (Metadata Database)
-- ============================================================================
-- Run this section for PostgreSQL metadata database

-- Main Table: DMS_FLUPLD (File Upload Definition)
CREATE TABLE IF NOT EXISTS dms_flupld (
    flupldid      SERIAL PRIMARY KEY,
    flupldref     VARCHAR(100) UNIQUE NOT NULL,  -- Reference name (e.g., CUSTOMER_IMPORT)
    fluplddesc    VARCHAR(500),                  -- Description
    flnm          VARCHAR(255),                  -- Original filename only (without path)
    flpth         VARCHAR(2000),                 -- Full file path (directory + filename)
    fltyp         VARCHAR(50),                   -- CSV, XLSX, JSON, XML, PARQUET, TSV, PDF, GOOGLESHEETS, etc.
    trgconid      INTEGER,                       -- Target DB connection ID
    trgschm       VARCHAR(100),                  -- Target schema
    trgtblnm      VARCHAR(100),                  -- Target table name
    trnctflg      CHAR(1) DEFAULT 'N',          -- Truncate before load (Y/N)
    hdrrwcnt      INTEGER DEFAULT 0,            -- Number of header rows to skip
    ftrrwcnt      INTEGER DEFAULT 0,            -- Number of footer rows to skip
    hdrrwpttrn    VARCHAR(500),                  -- Header row pattern (regex) to identify header rows
    ftrrwpttrn    VARCHAR(500),                  -- Footer row pattern (regex) to identify footer rows
    frqcd         VARCHAR(10),                   -- Frequency code (DL, WK, etc.)
    stflg         CHAR(1) DEFAULT 'N',           -- Status flag (A=Active, N=Inactive)
    curflg        CHAR(1) DEFAULT 'Y',           -- Current flag
    crtdby        VARCHAR(100),                   -- Created by
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Created date
    uptdby        VARCHAR(100),                   -- Updated by
    uptdt         TIMESTAMP,                     -- Updated date
    lstrundt      TIMESTAMP,                     -- Last run date
    nxtrundt      TIMESTAMP                      -- Next run date
);

-- Add comments for PostgreSQL
COMMENT ON TABLE dms_flupld IS 'File Upload Configuration - Main table storing file upload definitions';
COMMENT ON COLUMN dms_flupld.flupldid IS 'Primary key - File upload ID';
COMMENT ON COLUMN dms_flupld.flupldref IS 'Unique reference name for the file upload configuration';
COMMENT ON COLUMN dms_flupld.fluplddesc IS 'Description of the file upload configuration';
COMMENT ON COLUMN dms_flupld.flnm IS 'Original filename only (without directory path)';
COMMENT ON COLUMN dms_flupld.flpth IS 'Full file path including directory and filename (up to 2000 chars)';
COMMENT ON COLUMN dms_flupld.fltyp IS 'File type: CSV, XLSX, JSON, XML, PARQUET, TSV, PDF, GOOGLESHEETS, etc.';
COMMENT ON COLUMN dms_flupld.trgconid IS 'Target database connection ID (from DMS_DBCONDTLS)';
COMMENT ON COLUMN dms_flupld.trgschm IS 'Target schema name where data will be loaded';
COMMENT ON COLUMN dms_flupld.trgtblnm IS 'Target table name where data will be loaded';
COMMENT ON COLUMN dms_flupld.trnctflg IS 'Truncate flag: Y=Truncate before load, N=Append';
COMMENT ON COLUMN dms_flupld.hdrrwcnt IS 'Number of header rows to skip from the beginning of file';
COMMENT ON COLUMN dms_flupld.ftrrwcnt IS 'Number of footer rows to skip from the end of file';
COMMENT ON COLUMN dms_flupld.hdrrwpttrn IS 'Regex pattern to identify header rows (e.g., "Report|Title|Date Range")';
COMMENT ON COLUMN dms_flupld.ftrrwpttrn IS 'Regex pattern to identify footer rows (e.g., "Total|Page|Summary")';
COMMENT ON COLUMN dms_flupld.frqcd IS 'Frequency code: DL=Daily, WK=Weekly, MN=Monthly, etc.';
COMMENT ON COLUMN dms_flupld.stflg IS 'Status flag: A=Active, N=Inactive';
COMMENT ON COLUMN dms_flupld.curflg IS 'Current flag: Y=Current record, N=Historical';
COMMENT ON COLUMN dms_flupld.lstrundt IS 'Last execution date and time for this file upload';
COMMENT ON COLUMN dms_flupld.nxtrundt IS 'Next scheduled execution date and time';

-- Detail Table: DMS_FLUPLDDTL (File Upload Column Mapping)
CREATE TABLE IF NOT EXISTS dms_fluplddtl (
    fluplddtlid   SERIAL PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,        -- Reference to DMS_FLUPLD
    srcclnm       VARCHAR(100),                  -- Source column name (from file)
    trgclnm       VARCHAR(100) NOT NULL,         -- Target column name (in DB)
    trgcldtyp     VARCHAR(50),                   -- Target column data type
    trgkyflg      CHAR(1) DEFAULT 'N',          -- Is primary key (Y/N)
    trgkyseq      INTEGER,                       -- Primary key sequence
    trgcldesc     VARCHAR(500),                  -- Column description
    drvlgc        TEXT,                          -- Value derivation logic (SQL/Python)
    drvlgcflg     CHAR(1) DEFAULT 'N',          -- Logic verified flag (Y/N)
    excseq        INTEGER,                       -- Execution sequence
    isaudit       CHAR(1) DEFAULT 'N',          -- Is audit column (Y/N)
    audttyp       VARCHAR(20),                  -- CREATED_DATE, UPDATED_DATE, CREATED_BY, etc.
    dfltval       VARCHAR(500),                  -- Default value
    isrqrd        CHAR(1) DEFAULT 'N',          -- Is required (Y/N)
    curflg        CHAR(1) DEFAULT 'Y',           -- Current flag
    crtdby        VARCHAR(100),                  -- Created by
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Created date
    uptdby        VARCHAR(100),                  -- Updated by
    uptdt         TIMESTAMP                      -- Updated date
);

-- Add comments for detail table
COMMENT ON TABLE dms_fluplddtl IS 'File Upload Column Mapping - Detail table storing column mappings';
COMMENT ON COLUMN dms_fluplddtl.fluplddtlid IS 'Primary key - File upload detail ID';
COMMENT ON COLUMN dms_fluplddtl.flupldref IS 'Reference to DMS_FLUPLD table';
COMMENT ON COLUMN dms_fluplddtl.srcclnm IS 'Source column name from the uploaded file';
COMMENT ON COLUMN dms_fluplddtl.trgclnm IS 'Target column name in the database table';
COMMENT ON COLUMN dms_fluplddtl.trgcldtyp IS 'Target column data type (VARCHAR, NUMBER, TIMESTAMP, etc.)';
COMMENT ON COLUMN dms_fluplddtl.trgkyflg IS 'Primary key flag: Y=Primary key, N=Not a key';
COMMENT ON COLUMN dms_fluplddtl.trgkyseq IS 'Primary key sequence number (for composite keys)';
COMMENT ON COLUMN dms_fluplddtl.drvlgc IS 'Value derivation logic (SQL expression or Python code)';
COMMENT ON COLUMN dms_fluplddtl.drvlgcflg IS 'Derivation logic verified flag: Y=Verified, N=Not verified';
COMMENT ON COLUMN dms_fluplddtl.excseq IS 'Execution sequence for column processing order';
COMMENT ON COLUMN dms_fluplddtl.isaudit IS 'Audit column flag: Y=Audit column, N=Regular column';
COMMENT ON COLUMN dms_fluplddtl.audttyp IS 'Audit type: CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY';
COMMENT ON COLUMN dms_fluplddtl.dfltval IS 'Default value for the column if source is null';
COMMENT ON COLUMN dms_fluplddtl.isrqrd IS 'Required flag: Y=Required, N=Optional';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_flupld_ref ON dms_flupld(flupldref);
CREATE INDEX IF NOT EXISTS idx_flupld_trgconid ON dms_flupld(trgconid);
CREATE INDEX IF NOT EXISTS idx_flupld_curflg ON dms_flupld(curflg);
CREATE INDEX IF NOT EXISTS idx_fluplddtl_ref ON dms_fluplddtl(flupldref);
CREATE INDEX IF NOT EXISTS idx_fluplddtl_curflg ON dms_fluplddtl(curflg);

-- Create sequences for ID provider system (if using SEQUENCE mode)
-- Note: SERIAL columns auto-create sequences, but ID provider expects these specific names
CREATE SEQUENCE IF NOT EXISTS dms_flupldseq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS dms_fluplddtlseq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

COMMENT ON SEQUENCE dms_flupldseq IS 'Sequence for generating file upload IDs (for ID provider system)';
COMMENT ON SEQUENCE dms_fluplddtlseq IS 'Sequence for generating file upload detail IDs (for ID provider system)';

-- Add foreign key constraint (optional, if DMS_DBCONDTLS exists)
-- ALTER TABLE dms_flupld ADD CONSTRAINT fk_flupld_trgconid 
--     FOREIGN KEY (trgconid) REFERENCES dms_dbcondtls(conid);

-- ============================================================================
-- ORACLE VERSION (Metadata Database)
-- ============================================================================
-- Run this section for Oracle metadata database

/*
-- Main Table: DMS_FLUPLD (File Upload Definition)
CREATE TABLE DMS_FLUPLD (
    FLUPLDID      NUMBER PRIMARY KEY,
    FLUPLDREF     VARCHAR2(100) UNIQUE NOT NULL,  -- Reference name (e.g., CUSTOMER_IMPORT)
    FLUPLDDESC    VARCHAR2(500),                   -- Description
    FLNM          VARCHAR2(255),                   -- Original filename only (without path)
    FLPTH         VARCHAR2(2000),                  -- Full file path (directory + filename)
    FLTYP         VARCHAR2(50),                    -- CSV, XLSX, JSON, XML, PARQUET, TSV, PDF, GOOGLESHEETS, etc.
    TRGCONID      NUMBER,                          -- Target DB connection ID
    TRGSCHM       VARCHAR2(100),                   -- Target schema
    TRGTBLNM      VARCHAR2(100),                   -- Target table name
    TRNCTFLG      CHAR(1) DEFAULT 'N',            -- Truncate before load (Y/N)
    HDRRWCNT      NUMBER DEFAULT 0,              -- Number of header rows to skip
    FTRRWCNT      NUMBER DEFAULT 0,              -- Number of footer rows to skip
    HDRRWPTTRN    VARCHAR2(500),                 -- Header row pattern (regex) to identify header rows
    FTRRWPTTRN    VARCHAR2(500),                 -- Footer row pattern (regex) to identify footer rows
    FRQCD         VARCHAR2(10),                    -- Frequency code (DL, WK, etc.)
    STFLG         CHAR(1) DEFAULT 'N',             -- Status flag (A=Active, N=Inactive)
    CURFLG        CHAR(1) DEFAULT 'Y',             -- Current flag
    CRTDBY        VARCHAR2(100),                    -- Created by
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,  -- Created date
    UPTDBY        VARCHAR2(100),                    -- Updated by
    UPTDATE       TIMESTAMP(6),                    -- Updated date
    LSTRUNDT      TIMESTAMP(6),                    -- Last run date
    NXTRUNDT      TIMESTAMP(6)                     -- Next run date
);

-- Create sequence for Oracle
CREATE SEQUENCE DMS_FLUPLDSEQ
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- Add comments for Oracle
COMMENT ON TABLE DMS_FLUPLD IS 'File Upload Configuration - Main table storing file upload definitions';
COMMENT ON COLUMN DMS_FLUPLD.FLUPLDID IS 'Primary key - File upload ID';
COMMENT ON COLUMN DMS_FLUPLD.FLUPLDREF IS 'Unique reference name for the file upload configuration';
COMMENT ON COLUMN DMS_FLUPLD.FLUPLDDESC IS 'Description of the file upload configuration';
COMMENT ON COLUMN DMS_FLUPLD.FLNM IS 'Original filename only (without directory path)';
COMMENT ON COLUMN DMS_FLUPLD.FLPTH IS 'Full file path including directory and filename (up to 2000 chars)';
COMMENT ON COLUMN DMS_FLUPLD.FLTYP IS 'File type: CSV, XLSX, JSON, XML, PARQUET, TSV, PDF, GOOGLESHEETS, etc.';
COMMENT ON COLUMN DMS_FLUPLD.TRGCONID IS 'Target database connection ID (from DMS_DBCONDTLS)';
COMMENT ON COLUMN DMS_FLUPLD.TRGSCHM IS 'Target schema name where data will be loaded';
COMMENT ON COLUMN DMS_FLUPLD.TRGTBLNM IS 'Target table name where data will be loaded';
COMMENT ON COLUMN DMS_FLUPLD.TRNCTFLG IS 'Truncate flag: Y=Truncate before load, N=Append';
COMMENT ON COLUMN DMS_FLUPLD.FRQCD IS 'Frequency code: DL=Daily, WK=Weekly, MN=Monthly, etc.';
COMMENT ON COLUMN DMS_FLUPLD.STFLG IS 'Status flag: A=Active, N=Inactive';
COMMENT ON COLUMN DMS_FLUPLD.CURFLG IS 'Current flag: Y=Current record, N=Historical';
COMMENT ON COLUMN DMS_FLUPLD.LSTRUNDT IS 'Last execution date and time for this file upload';
COMMENT ON COLUMN DMS_FLUPLD.NXTRUNDT IS 'Next scheduled execution date and time';

-- Detail Table: DMS_FLUPLDDTL (File Upload Column Mapping)
CREATE TABLE DMS_FLUPLDDTL (
    FLUPLDDTLID   NUMBER PRIMARY KEY,
    FLUPLDREF     VARCHAR2(100) NOT NULL,          -- Reference to DMS_FLUPLD
    SRCCLNM       VARCHAR2(100),                   -- Source column name (from file)
    TRGCLNM       VARCHAR2(100) NOT NULL,           -- Target column name (in DB)
    TRGCLDTYP     VARCHAR2(50),                    -- Target column data type
    TRGKYFLG      CHAR(1) DEFAULT 'N',             -- Is primary key (Y/N)
    TRGKYSEQ      NUMBER,                           -- Primary key sequence
    TRGCLDESC     VARCHAR2(500),                    -- Column description
    DRVLGC        CLOB,                             -- Value derivation logic (SQL/Python)
    DRVLGCFLG     CHAR(1) DEFAULT 'N',             -- Logic verified flag (Y/N)
    EXCSEQ        NUMBER,                           -- Execution sequence
    ISAUDIT       CHAR(1) DEFAULT 'N',              -- Is audit column (Y/N)
    AUDTTYP       VARCHAR2(20),                     -- CREATED_DATE, UPDATED_DATE, CREATED_BY, etc.
    DFLTVAL       VARCHAR2(500),                    -- Default value
    ISRQRD        CHAR(1) DEFAULT 'N',              -- Is required (Y/N)
    CURFLG        CHAR(1) DEFAULT 'Y',              -- Current flag
    CRTDBY        VARCHAR2(100),                    -- Created by
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,  -- Created date
    UPTDBY        VARCHAR2(100),                    -- Updated by
    UPTDATE       TIMESTAMP(6)                     -- Updated date
);

-- Create sequence for detail table
CREATE SEQUENCE DMS_FLUPLDDTLSEQ
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- Add comments for detail table
COMMENT ON TABLE DMS_FLUPLDDTL IS 'File Upload Column Mapping - Detail table storing column mappings';
COMMENT ON COLUMN DMS_FLUPLDDTL.FLUPLDDTLID IS 'Primary key - File upload detail ID';
COMMENT ON COLUMN DMS_FLUPLDDTL.FLUPLDREF IS 'Reference to DMS_FLUPLD table';
COMMENT ON COLUMN DMS_FLUPLDDTL.SRCCLNM IS 'Source column name from the uploaded file';
COMMENT ON COLUMN DMS_FLUPLDDTL.TRGCLNM IS 'Target column name in the database table';
COMMENT ON COLUMN DMS_FLUPLDDTL.TRGCLDTYP IS 'Target column data type (VARCHAR2, NUMBER, TIMESTAMP, etc.)';
COMMENT ON COLUMN DMS_FLUPLDDTL.TRGKYFLG IS 'Primary key flag: Y=Primary key, N=Not a key';
COMMENT ON COLUMN DMS_FLUPLDDTL.TRGKYSEQ IS 'Primary key sequence number (for composite keys)';
COMMENT ON COLUMN DMS_FLUPLDDTL.DRVLGC IS 'Value derivation logic (SQL expression or Python code)';
COMMENT ON COLUMN DMS_FLUPLDDTL.DRVLGCFLG IS 'Derivation logic verified flag: Y=Verified, N=Not verified';
COMMENT ON COLUMN DMS_FLUPLDDTL.EXCSEQ IS 'Execution sequence for column processing order';
COMMENT ON COLUMN DMS_FLUPLDDTL.ISAUDIT IS 'Audit column flag: Y=Audit column, N=Regular column';
COMMENT ON COLUMN DMS_FLUPLDDTL.AUDTTYP IS 'Audit type: CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY';
COMMENT ON COLUMN DMS_FLUPLDDTL.DFLTVAL IS 'Default value for the column if source is null';
COMMENT ON COLUMN DMS_FLUPLDDTL.ISRQRD IS 'Required flag: Y=Required, N=Optional';

-- Create indexes for performance
CREATE INDEX IDX_FLUPLD_REF ON DMS_FLUPLD(FLUPLDREF);
CREATE INDEX IDX_FLUPLD_TRGCONID ON DMS_FLUPLD(TRGCONID);
CREATE INDEX IDX_FLUPLD_CURFLG ON DMS_FLUPLD(CURFLG);
CREATE INDEX IDX_FLUPLDDTL_REF ON DMS_FLUPLDDTL(FLUPLDREF);
CREATE INDEX IDX_FLUPLDDTL_CURFLG ON DMS_FLUPLDDTL(CURFLG);

-- Add foreign key constraint (optional, if DMS_DBCONDTLS exists)
-- ALTER TABLE DMS_FLUPLD ADD CONSTRAINT FK_FLUPLD_TRGCONID 
--     FOREIGN KEY (TRGCONID) REFERENCES DMS_DBCONDTLS(CONID);
*/

-- ============================================================================
-- MYSQL VERSION (Metadata Database)
-- ============================================================================
-- Run this section for MySQL metadata database

/*
-- Main Table: DMS_FLUPLD (File Upload Definition)
CREATE TABLE IF NOT EXISTS dms_flupld (
    flupldid      INT AUTO_INCREMENT PRIMARY KEY,
    flupldref     VARCHAR(100) UNIQUE NOT NULL,
    fluplddesc    VARCHAR(500),
    flnm          VARCHAR(255),
    flpth         VARCHAR(2000),
    fltyp         VARCHAR(50),
    trgconid      INT,
    trgschm       VARCHAR(100),
    trgtblnm      VARCHAR(100),
    trnctflg      CHAR(1) DEFAULT 'N',
    hdrrwcnt      INT DEFAULT 0,
    ftrrwcnt      INT DEFAULT 0,
    hdrrwpttrn    VARCHAR(500),
    ftrrwpttrn    VARCHAR(500),
    frqcd         VARCHAR(10),
    stflg         CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP NULL,
    lstrundt      TIMESTAMP NULL,
    nxtrundt      TIMESTAMP NULL
);

-- Detail Table: DMS_FLUPLDDTL (File Upload Column Mapping)
CREATE TABLE IF NOT EXISTS dms_fluplddtl (
    fluplddtlid   INT AUTO_INCREMENT PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    srcclnm       VARCHAR(100),
    trgclnm       VARCHAR(100) NOT NULL,
    trgcldtyp     VARCHAR(50),
    trgkyflg      CHAR(1) DEFAULT 'N',
    trgkyseq      INT,
    trgcldesc     VARCHAR(500),
    drvlgc        TEXT,
    drvlgcflg     CHAR(1) DEFAULT 'N',
    excseq        INT,
    isaudit       CHAR(1) DEFAULT 'N',
    audttyp       VARCHAR(20),
    dfltval       VARCHAR(500),
    isrqrd        CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP NULL
);

-- Create indexes
CREATE INDEX idx_flupld_ref ON dms_flupld(flupldref);
CREATE INDEX idx_flupld_trgconid ON dms_flupld(trgconid);
CREATE INDEX idx_flupld_curflg ON dms_flupld(curflg);
CREATE INDEX idx_fluplddtl_ref ON dms_fluplddtl(flupldref);
CREATE INDEX idx_fluplddtl_curflg ON dms_fluplddtl(curflg);
*/

-- ============================================================================
-- MS SQL SERVER / SQL SERVER VERSION (Metadata Database)
-- ============================================================================
-- Run this section for MS SQL Server metadata database

/*
-- Main Table: DMS_FLUPLD (File Upload Definition)
CREATE TABLE dms_flupld (
    flupldid      INT IDENTITY(1,1) PRIMARY KEY,
    flupldref     VARCHAR(100) UNIQUE NOT NULL,
    fluplddesc    VARCHAR(500),
    flnm          VARCHAR(255),
    flpth         VARCHAR(2000),
    fltyp         VARCHAR(50),
    trgconid      INT,
    trgschm       VARCHAR(100),
    trgtblnm      VARCHAR(100),
    trnctflg      CHAR(1) DEFAULT 'N',
    hdrrwcnt      INT DEFAULT 0,
    ftrrwcnt      INT DEFAULT 0,
    hdrrwpttrn    VARCHAR(500),
    ftrrwpttrn    VARCHAR(500),
    frqcd         VARCHAR(10),
    stflg         CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME2 DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME2 NULL,
    lstrundt      DATETIME2 NULL,
    nxtrundt      DATETIME2 NULL
);

-- Detail Table: DMS_FLUPLDDTL (File Upload Column Mapping)
CREATE TABLE dms_fluplddtl (
    fluplddtlid   INT IDENTITY(1,1) PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    srcclnm       VARCHAR(100),
    trgclnm       VARCHAR(100) NOT NULL,
    trgcldtyp     VARCHAR(50),
    trgkyflg      CHAR(1) DEFAULT 'N',
    trgkyseq      INT,
    trgcldesc     VARCHAR(500),
    drvlgc        VARCHAR(MAX),
    drvlgcflg     CHAR(1) DEFAULT 'N',
    excseq        INT,
    isaudit       CHAR(1) DEFAULT 'N',
    audttyp       VARCHAR(20),
    dfltval       VARCHAR(500),
    isrqrd        CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME2 DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME2 NULL
);

-- Create indexes
CREATE INDEX idx_flupld_ref ON dms_flupld(flupldref);
CREATE INDEX idx_flupld_trgconid ON dms_flupld(trgconid);
CREATE INDEX idx_flupld_curflg ON dms_flupld(curflg);
CREATE INDEX idx_fluplddtl_ref ON dms_fluplddtl(flupldref);
CREATE INDEX idx_fluplddtl_curflg ON dms_fluplddtl(curflg);
*/

-- ============================================================================
-- SYBASE VERSION (Metadata Database)
-- ============================================================================
-- Run this section for Sybase metadata database

/*
-- Main Table: DMS_FLUPLD (File Upload Definition)
CREATE TABLE dms_flupld (
    flupldid      INT IDENTITY PRIMARY KEY,
    flupldref     VARCHAR(100) UNIQUE NOT NULL,
    fluplddesc    VARCHAR(500),
    flnm          VARCHAR(255),
    flpth         VARCHAR(2000),
    fltyp         VARCHAR(50),
    trgconid      INT,
    trgschm       VARCHAR(100),
    trgtblnm      VARCHAR(100),
    trnctflg      CHAR(1) DEFAULT 'N',
    hdrrwcnt      INT DEFAULT 0,
    ftrrwcnt      INT DEFAULT 0,
    hdrrwpttrn    VARCHAR(500),
    ftrrwpttrn    VARCHAR(500),
    frqcd         VARCHAR(10),
    stflg         CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME NULL,
    lstrundt      DATETIME NULL,
    nxtrundt      DATETIME NULL
);

-- Detail Table: DMS_FLUPLDDTL (File Upload Column Mapping)
CREATE TABLE dms_fluplddtl (
    fluplddtlid   INT IDENTITY PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    srcclnm       VARCHAR(100),
    trgclnm       VARCHAR(100) NOT NULL,
    trgcldtyp     VARCHAR(50),
    trgkyflg      CHAR(1) DEFAULT 'N',
    trgkyseq      INT,
    trgcldesc     VARCHAR(500),
    drvlgc        TEXT,
    drvlgcflg     CHAR(1) DEFAULT 'N',
    excseq        INT,
    isaudit       CHAR(1) DEFAULT 'N',
    audttyp       VARCHAR(20),
    dfltval       VARCHAR(500),
    isrqrd        CHAR(1) DEFAULT 'N',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME NULL
);

-- Create indexes
CREATE INDEX idx_flupld_ref ON dms_flupld(flupldref);
CREATE INDEX idx_flupld_trgconid ON dms_flupld(trgconid);
CREATE INDEX idx_flupld_curflg ON dms_flupld(curflg);
CREATE INDEX idx_fluplddtl_ref ON dms_fluplddtl(flupldref);
CREATE INDEX idx_fluplddtl_curflg ON dms_fluplddtl(curflg);
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- PostgreSQL Verification
/*
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name IN ('dms_flupld', 'dms_fluplddtl')
ORDER BY table_name, ordinal_position;
*/

-- Oracle Verification
/*
SELECT 
    table_name,
    column_name,
    data_type,
    nullable,
    data_default
FROM user_tab_columns
WHERE table_name IN ('DMS_FLUPLD', 'DMS_FLUPLDDTL')
ORDER BY table_name, column_id;
*/

-- MySQL Verification
/*
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name IN ('dms_flupld', 'dms_fluplddtl')
ORDER BY table_name, ordinal_position;
*/

-- MS SQL Server Verification
/*
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name IN ('dms_flupld', 'dms_fluplddtl')
ORDER BY table_name, ordinal_position;
*/

-- Sybase Verification
/*
SELECT 
    table_name,
    column_name,
    data_type,
    nullable,
    default_value
FROM syscolumns sc
JOIN sysobjects so ON sc.id = so.id
WHERE so.name IN ('dms_flupld', 'dms_fluplddtl')
ORDER BY so.name, sc.colid;
*/

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- Only run this if you need to rollback the migration

-- PostgreSQL Rollback
/*
DROP TABLE IF EXISTS dms_fluplddtl CASCADE;
DROP TABLE IF EXISTS dms_flupld CASCADE;
*/

-- Oracle Rollback
/*
DROP TABLE DMS_FLUPLDDTL CASCADE CONSTRAINTS;
DROP SEQUENCE DMS_FLUPLDDTLSEQ;
DROP TABLE DMS_FLUPLD CASCADE CONSTRAINTS;
DROP SEQUENCE DMS_FLUPLDSEQ;
*/

-- MySQL Rollback
/*
DROP TABLE IF EXISTS dms_fluplddtl;
DROP TABLE IF EXISTS dms_flupld;
*/

-- MS SQL Server Rollback
/*
DROP TABLE dms_fluplddtl;
DROP TABLE dms_flupld;
*/

-- Sybase Rollback
/*
DROP TABLE dms_fluplddtl;
DROP TABLE dms_flupld;
*/

