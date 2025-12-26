-- ============================================================================
-- Database Migration: File Upload Module - Security Columns
-- ============================================================================
-- Purpose: Add security and control columns to DMS_FLUPLD table
--          Supports multiple RDBMS platforms: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, etc.
-- 
-- Date: 2025-01-XX
-- Version: 1.0
-- ============================================================================
-- Note: Run this AFTER creating the base DMS_FLUPLD table
-- 
-- Multi-Database Support:
--   - Metadata databases: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, etc.
--   - Database-specific syntax differences handled per database type
-- ============================================================================

-- ============================================================================
-- POSTGRESQL VERSION (Metadata Database)
-- ============================================================================

-- Add security columns to DMS_FLUPLD
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flhash VARCHAR(64);           -- SHA-256 file hash
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flsz BIGINT;                    -- File size in bytes
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flmimtyp VARCHAR(100);          -- MIME type
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flvrfyflg CHAR(1) DEFAULT 'N';  -- File verified (Y/N)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flvrfydt TIMESTAMP;             -- Verification date
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flvrfyby VARCHAR(100);           -- Verified by (user/system)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flqrnflg CHAR(1) DEFAULT 'N';  -- Quarantine flag (Y/N)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flqrnrsn VARCHAR(500);          -- Quarantine reason
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flscnflg CHAR(1) DEFAULT 'N';  -- Virus scanned (Y/N)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flscndt TIMESTAMP;             -- Scan date
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flscnrslt VARCHAR(50);          -- Scan result (CLEAN/INFECTED/ERROR)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flacclvl VARCHAR(20) DEFAULT 'PRIVATE';  -- Access level (PUBLIC/PRIVATE/RESTRICTED/CONFIDENTIAL)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flencflg CHAR(1) DEFAULT 'N';  -- Encrypted flag (Y/N)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flencalg VARCHAR(50);          -- Encryption algorithm
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flupldcnt INTEGER DEFAULT 0;   -- Upload attempt count
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS fllstacctm TIMESTAMP;          -- Last access time
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flacccnt INTEGER DEFAULT 0;    -- Access count
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flrtrntm TIMESTAMP;            -- Retention time (auto-delete after)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flrtrnplcy VARCHAR(50);         -- Retention policy (DAYS_30/DAYS_90/YEARS_1/etc.)

-- Add comments
COMMENT ON COLUMN dms_flupld.flhash IS 'SHA-256 hash of file for integrity verification';
COMMENT ON COLUMN dms_flupld.flsz IS 'File size in bytes';
COMMENT ON COLUMN dms_flupld.flmimtyp IS 'MIME type of the file';
COMMENT ON COLUMN dms_flupld.flvrfyflg IS 'File verification flag: Y=Verified, N=Not verified';
COMMENT ON COLUMN dms_flupld.flvrfydt IS 'Date and time when file was verified';
COMMENT ON COLUMN dms_flupld.flvrfyby IS 'User or system that verified the file';
COMMENT ON COLUMN dms_flupld.flqrnflg IS 'Quarantine flag: Y=Quarantined, N=Not quarantined';
COMMENT ON COLUMN dms_flupld.flqrnrsn IS 'Reason for quarantine';
COMMENT ON COLUMN dms_flupld.flscnflg IS 'Virus scan flag: Y=Scanned, N=Not scanned';
COMMENT ON COLUMN dms_flupld.flscndt IS 'Date and time when file was scanned';
COMMENT ON COLUMN dms_flupld.flscnrslt IS 'Virus scan result: CLEAN/INFECTED/ERROR';
COMMENT ON COLUMN dms_flupld.flacclvl IS 'Access level: PUBLIC/PRIVATE/RESTRICTED/CONFIDENTIAL';
COMMENT ON COLUMN dms_flupld.flencflg IS 'Encryption flag: Y=Encrypted, N=Not encrypted';
COMMENT ON COLUMN dms_flupld.flencalg IS 'Encryption algorithm used (e.g., AES256)';
COMMENT ON COLUMN dms_flupld.flupldcnt IS 'Number of upload attempts for this file';
COMMENT ON COLUMN dms_flupld.fllstacctm IS 'Last access time (download/view/execute)';
COMMENT ON COLUMN dms_flupld.flacccnt IS 'Total number of times file was accessed';
COMMENT ON COLUMN dms_flupld.flrtrntm IS 'Retention expiration time (file will be deleted after this)';
COMMENT ON COLUMN dms_flupld.flrtrnplcy IS 'Retention policy: DAYS_30/DAYS_90/YEARS_1/etc.';

-- Create File Access Audit Log table
CREATE TABLE IF NOT EXISTS dms_flupldacclg (
    acclgid       SERIAL PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,          -- Reference to DMS_FLUPLD
    usrid         INTEGER,                        -- User ID who accessed
    usrnm         VARCHAR(100),                   -- Username
    acctyp        VARCHAR(20),                    -- Access type: UPLOAD/DOWNLOAD/VIEW/DELETE/EXECUTE
    accdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Access date
    ipaddr        VARCHAR(45),                     -- IP address (supports IPv6)
    usragnt       VARCHAR(500),                    -- User agent
    accsts        VARCHAR(20),                    -- Access status: SUCCESS/FAILED/DENIED
    accrsn        VARCHAR(500),                   -- Access reason/error message
    flsz          BIGINT,                         -- File size at access time
    flhash        VARCHAR(64)                     -- File hash at access time (for integrity check)
);

CREATE INDEX IF NOT EXISTS idx_flupldacclg_ref ON dms_flupldacclg(flupldref);
CREATE INDEX IF NOT EXISTS idx_flupldacclg_usrid ON dms_flupldacclg(usrid);
CREATE INDEX IF NOT EXISTS idx_flupldacclg_accdt ON dms_flupldacclg(accdt);
CREATE INDEX IF NOT EXISTS idx_flupldacclg_acctyp ON dms_flupldacclg(acctyp);

COMMENT ON TABLE dms_flupldacclg IS 'File Upload Access Audit Log - Tracks all file access attempts';
COMMENT ON COLUMN dms_flupldacclg.acclgid IS 'Primary key - Access log ID';
COMMENT ON COLUMN dms_flupldacclg.flupldref IS 'Reference to DMS_FLUPLD table';
COMMENT ON COLUMN dms_flupldacclg.acctyp IS 'Access type: UPLOAD/DOWNLOAD/VIEW/DELETE/EXECUTE';
COMMENT ON COLUMN dms_flupldacclg.accsts IS 'Access status: SUCCESS/FAILED/DENIED';

-- Create File Validation Rules table
CREATE TABLE IF NOT EXISTS dms_flupldvld (
    vldid         SERIAL PRIMARY KEY,
    fltyp         VARCHAR(50) NOT NULL,           -- File type (CSV, XLSX, etc.)
    maxsz         BIGINT,                         -- Maximum file size in bytes
    alwdexns      TEXT,                           -- Allowed extensions (comma-separated)
    alwdmimtyps   TEXT,                           -- Allowed MIME types (comma-separated)
    blckdexns     TEXT,                           -- Blocked extensions (comma-separated)
    blckdpttrns   TEXT,                           -- Blocked filename patterns (regex, comma-separated)
    rqrvrfy       CHAR(1) DEFAULT 'Y',           -- Require verification (Y/N)
    rqrscn        CHAR(1) DEFAULT 'Y',            -- Require virus scan (Y/N)
    rqrenc        CHAR(1) DEFAULT 'N',            -- Require encryption (Y/N)
    maxclmcnt     INTEGER,                        -- Maximum column count (for structured files)
    maxrwcnt      BIGINT,                         -- Maximum row count (for structured files)
    vldcntnt      CHAR(1) DEFAULT 'Y',           -- Validate content structure (Y/N)
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_flupldvld_fltyp ON dms_flupldvld(fltyp);

COMMENT ON TABLE dms_flupldvld IS 'File Upload Validation Rules - Defines validation rules per file type';
COMMENT ON COLUMN dms_flupldvld.fltyp IS 'File type this rule applies to';
COMMENT ON COLUMN dms_flupldvld.maxsz IS 'Maximum file size in bytes for this file type';
COMMENT ON COLUMN dms_flupldvld.alwdexns IS 'Comma-separated list of allowed file extensions';
COMMENT ON COLUMN dms_flupldvld.blckdpttrns IS 'Comma-separated regex patterns for blocked filenames';

-- Create Security Configuration table
CREATE TABLE IF NOT EXISTS dms_flupldsec (
    secid         SERIAL PRIMARY KEY,
    scnngnbl      CHAR(1) DEFAULT 'Y',           -- Virus scanning enabled (Y/N)
    scnngprvd     VARCHAR(50),                    -- Scanning provider (CLAMAV/DEFENDER/CUSTOM)
    scnngcmd      VARCHAR(500),                   -- Custom scan command
    rqrvrfy       CHAR(1) DEFAULT 'Y',           -- Require verification (Y/N)
    rqrenc        CHAR(1) DEFAULT 'N',            -- Require encryption (Y/N)
    encalg        VARCHAR(50),                    -- Encryption algorithm (AES256/etc.)
    qrntnflg      CHAR(1) DEFAULT 'Y',           -- Quarantine enabled (Y/N)
    qrntndir      VARCHAR(1000),                  -- Quarantine directory path
    rtrntm        INTEGER DEFAULT 90,              -- Retention time in days
    maxflsz       BIGINT DEFAULT 104857600,       -- Maximum file size (default 100MB)
    maxupldhr     INTEGER DEFAULT 50,             -- Max uploads per hour per user
    maxszhr       BIGINT DEFAULT 524288000,        -- Max size per hour per user (500MB)
    alwdflexts    TEXT,                           -- Allowed file extensions (comma-separated)
    blckdflexts   TEXT,                           -- Blocked file extensions (comma-separated)
    alwdiprngs    TEXT,                           -- Allowed IP ranges (CIDR notation)
    blckdiprngs   TEXT,                           -- Blocked IP ranges
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP
);

COMMENT ON TABLE dms_flupldsec IS 'File Upload Security Configuration - Global security settings';
COMMENT ON COLUMN dms_flupldsec.scnngnbl IS 'Virus scanning enabled: Y=Enabled, N=Disabled';
COMMENT ON COLUMN dms_flupldsec.scnngprvd IS 'Virus scanner provider: CLAMAV/DEFENDER/CUSTOM';
COMMENT ON COLUMN dms_flupldsec.qrntnflg IS 'Quarantine enabled: Y=Enabled, N=Disabled';
COMMENT ON COLUMN dms_flupldsec.rtrntm IS 'Default retention time in days';

-- ============================================================================
-- ORACLE VERSION (Metadata Database)
-- ============================================================================

/*
-- Add security columns to DMS_FLUPLD
ALTER TABLE DMS_FLUPLD ADD (FLHASH VARCHAR2(64));           -- SHA-256 file hash
ALTER TABLE DMS_FLUPLD ADD (FLSZ NUMBER);                    -- File size in bytes
ALTER TABLE DMS_FLUPLD ADD (FLMIMTYP VARCHAR2(100));        -- MIME type
ALTER TABLE DMS_FLUPLD ADD (FLVRFYFLG CHAR(1) DEFAULT 'N');  -- File verified (Y/N)
ALTER TABLE DMS_FLUPLD ADD (FLVRFYDT TIMESTAMP(6));          -- Verification date
ALTER TABLE DMS_FLUPLD ADD (FLVRFYBY VARCHAR2(100));          -- Verified by (user/system)
ALTER TABLE DMS_FLUPLD ADD (FLQRNFLG CHAR(1) DEFAULT 'N');  -- Quarantine flag (Y/N)
ALTER TABLE DMS_FLUPLD ADD (FLQRNRSN VARCHAR2(500));        -- Quarantine reason
ALTER TABLE DMS_FLUPLD ADD (FLSCNFLG CHAR(1) DEFAULT 'N');  -- Virus scanned (Y/N)
ALTER TABLE DMS_FLUPLD ADD (FLSCNDT TIMESTAMP(6));           -- Scan date
ALTER TABLE DMS_FLUPLD ADD (FLSCNRSLT VARCHAR2(50));         -- Scan result (CLEAN/INFECTED/ERROR)
ALTER TABLE DMS_FLUPLD ADD (FLACCLVL VARCHAR2(20) DEFAULT 'PRIVATE');  -- Access level
ALTER TABLE DMS_FLUPLD ADD (FLENCFLG CHAR(1) DEFAULT 'N');  -- Encrypted flag (Y/N)
ALTER TABLE DMS_FLUPLD ADD (FLENCALG VARCHAR2(50));          -- Encryption algorithm
ALTER TABLE DMS_FLUPLD ADD (FLUPLDCNT NUMBER DEFAULT 0);     -- Upload attempt count
ALTER TABLE DMS_FLUPLD ADD (FLLSTACCTM TIMESTAMP(6));        -- Last access time
ALTER TABLE DMS_FLUPLD ADD (FLACCCNT NUMBER DEFAULT 0);      -- Access count
ALTER TABLE DMS_FLUPLD ADD (FLRTRNTM TIMESTAMP(6));          -- Retention time
ALTER TABLE DMS_FLUPLD ADD (FLRTRNPLCY VARCHAR2(50));         -- Retention policy

-- Create File Access Audit Log table
CREATE TABLE DMS_FLUPLDACCLG (
    ACCLGID       NUMBER PRIMARY KEY,
    FLUPLDREF     VARCHAR2(100) NOT NULL,
    USRID         NUMBER,
    USRNM         VARCHAR2(100),
    ACCTYP        VARCHAR2(20),
    ACCDT         TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    IPADDR        VARCHAR2(45),
    USRAGNT       VARCHAR2(500),
    ACCSTS        VARCHAR2(20),
    ACCRSN        VARCHAR2(500),
    FLSZ          NUMBER,
    FLHASH        VARCHAR2(64)
);

CREATE SEQUENCE DMS_FLUPLDACCLGSEQ;
CREATE INDEX IDX_FLUPLDACCLG_REF ON DMS_FLUPLDACCLG(FLUPLDREF);
CREATE INDEX IDX_FLUPLDACCLG_USRID ON DMS_FLUPLDACCLG(USRID);
CREATE INDEX IDX_FLUPLDACCLG_ACCDT ON DMS_FLUPLDACCLG(ACCDT);
CREATE INDEX IDX_FLUPLDACCLG_ACCTYP ON DMS_FLUPLDACCLG(ACCTYP);

-- Create File Validation Rules table
CREATE TABLE DMS_FLUPLDVLD (
    VLDID         NUMBER PRIMARY KEY,
    FLTYP         VARCHAR2(50) NOT NULL,
    MAXSZ         NUMBER,
    ALWDEXNS      CLOB,
    ALWDMIMTYPS   CLOB,
    BLCDEXNS      CLOB,
    BLCDPTTRNS    CLOB,
    RQRVRFY       CHAR(1) DEFAULT 'Y',
    RQRSCN        CHAR(1) DEFAULT 'Y',
    RQRENC        CHAR(1) DEFAULT 'N',
    MAXCLMCNT     NUMBER,
    MAXRWCNT      NUMBER,
    VLDCNTNT      CHAR(1) DEFAULT 'Y',
    CURFLG        CHAR(1) DEFAULT 'Y',
    CRTDBY        VARCHAR2(100),
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    UPTDBY        VARCHAR2(100),
    UPTDATE       TIMESTAMP(6)
);

CREATE SEQUENCE DMS_FLUPLDVLDSEQ;
CREATE INDEX IDX_FLUPLDVLD_FLTYP ON DMS_FLUPLDVLD(FLTYP);

-- Create Security Configuration table
CREATE TABLE DMS_FLUPLDSEC (
    SECID         NUMBER PRIMARY KEY,
    SCNNGNBL      CHAR(1) DEFAULT 'Y',
    SCNNGPRVD     VARCHAR2(50),
    SCNNGCMD      VARCHAR2(500),
    RQRVRFY       CHAR(1) DEFAULT 'Y',
    RQRENC        CHAR(1) DEFAULT 'N',
    ENCALG        VARCHAR2(50),
    QRNTNFLG      CHAR(1) DEFAULT 'Y',
    QRNTNDIR      VARCHAR2(1000),
    RTRNTM        NUMBER DEFAULT 90,
    MAXFLSZ       NUMBER DEFAULT 104857600,
    MAXUPLDHR     NUMBER DEFAULT 50,
    MAXSZHR       NUMBER DEFAULT 524288000,
    ALWDFLEXTS    CLOB,
    BLCDFLEXTS    CLOB,
    ALWDIPRNGS    CLOB,
    BLCDIPRNGS    CLOB,
    CURFLG        CHAR(1) DEFAULT 'Y',
    CRTDBY        VARCHAR2(100),
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    UPTDBY        VARCHAR2(100),
    UPTDATE       TIMESTAMP(6)
);

CREATE SEQUENCE DMS_FLUPLDSECSEQ;
*/

-- ============================================================================
-- MYSQL VERSION (Metadata Database)
-- ============================================================================

/*
-- Add security columns to DMS_FLUPLD
ALTER TABLE dms_flupld ADD COLUMN flhash VARCHAR(64);           -- SHA-256 file hash
ALTER TABLE dms_flupld ADD COLUMN flsz BIGINT;                  -- File size in bytes
ALTER TABLE dms_flupld ADD COLUMN flmimtyp VARCHAR(100);       -- MIME type
ALTER TABLE dms_flupld ADD COLUMN flvrfyflg CHAR(1) DEFAULT 'N';  -- File verified (Y/N)
ALTER TABLE dms_flupld ADD COLUMN flvrfydt TIMESTAMP NULL;      -- Verification date
ALTER TABLE dms_flupld ADD COLUMN flvrfyby VARCHAR(100);       -- Verified by (user/system)
ALTER TABLE dms_flupld ADD COLUMN flqrnflg CHAR(1) DEFAULT 'N';  -- Quarantine flag (Y/N)
ALTER TABLE dms_flupld ADD COLUMN flqrnrsn VARCHAR(500);        -- Quarantine reason
ALTER TABLE dms_flupld ADD COLUMN flscnflg CHAR(1) DEFAULT 'N';  -- Virus scanned (Y/N)
ALTER TABLE dms_flupld ADD COLUMN flscndt TIMESTAMP NULL;       -- Scan date
ALTER TABLE dms_flupld ADD COLUMN flscnrslt VARCHAR(50);        -- Scan result (CLEAN/INFECTED/ERROR)
ALTER TABLE dms_flupld ADD COLUMN flacclvl VARCHAR(20) DEFAULT 'PRIVATE';  -- Access level
ALTER TABLE dms_flupld ADD COLUMN flencflg CHAR(1) DEFAULT 'N';  -- Encrypted flag (Y/N)
ALTER TABLE dms_flupld ADD COLUMN flencalg VARCHAR(50);         -- Encryption algorithm
ALTER TABLE dms_flupld ADD COLUMN flupldcnt INT DEFAULT 0;      -- Upload attempt count
ALTER TABLE dms_flupld ADD COLUMN fllstacctm TIMESTAMP NULL;     -- Last access time
ALTER TABLE dms_flupld ADD COLUMN flacccnt INT DEFAULT 0;      -- Access count
ALTER TABLE dms_flupld ADD COLUMN flrtrntm TIMESTAMP NULL;      -- Retention time
ALTER TABLE dms_flupld ADD COLUMN flrtrnplcy VARCHAR(50);       -- Retention policy

-- Create File Access Audit Log table
CREATE TABLE IF NOT EXISTS dms_flupldacclg (
    acclgid       INT AUTO_INCREMENT PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    usrid         INT,
    usrnm         VARCHAR(100),
    acctyp        VARCHAR(20),
    accdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ipaddr        VARCHAR(45),
    usragnt       VARCHAR(500),
    accsts        VARCHAR(20),
    accrsn        VARCHAR(500),
    flsz          BIGINT,
    flhash        VARCHAR(64)
);

CREATE INDEX idx_flupldacclg_ref ON dms_flupldacclg(flupldref);
CREATE INDEX idx_flupldacclg_usrid ON dms_flupldacclg(usrid);
CREATE INDEX idx_flupldacclg_accdt ON dms_flupldacclg(accdt);
CREATE INDEX idx_flupldacclg_acctyp ON dms_flupldacclg(acctyp);

-- Create File Validation Rules table
CREATE TABLE IF NOT EXISTS dms_flupldvld (
    vldid         INT AUTO_INCREMENT PRIMARY KEY,
    fltyp         VARCHAR(50) NOT NULL,
    maxsz         BIGINT,
    alwdexns      TEXT,
    alwdmimtyps   TEXT,
    blckdexns     TEXT,
    blckdpttrns   TEXT,
    rqrvrfy       CHAR(1) DEFAULT 'Y',
    rqrscn        CHAR(1) DEFAULT 'Y',
    rqrenc        CHAR(1) DEFAULT 'N',
    maxclmcnt     INT,
    maxrwcnt      BIGINT,
    vldcntnt      CHAR(1) DEFAULT 'Y',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP NULL
);

CREATE INDEX idx_flupldvld_fltyp ON dms_flupldvld(fltyp);

-- Create Security Configuration table
CREATE TABLE IF NOT EXISTS dms_flupldsec (
    secid         INT AUTO_INCREMENT PRIMARY KEY,
    scnngnbl      CHAR(1) DEFAULT 'Y',
    scnngprvd     VARCHAR(50),
    scnngcmd      VARCHAR(500),
    rqrvrfy       CHAR(1) DEFAULT 'Y',
    rqrenc        CHAR(1) DEFAULT 'N',
    encalg        VARCHAR(50),
    qrntnflg      CHAR(1) DEFAULT 'Y',
    qrntndir      VARCHAR(1000),
    rtrntm        INT DEFAULT 90,
    maxflsz       BIGINT DEFAULT 104857600,
    maxupldhr     INT DEFAULT 50,
    maxszhr       BIGINT DEFAULT 524288000,
    alwdflexts    TEXT,
    blckdflexts   TEXT,
    alwdiprngs    TEXT,
    blckdiprngs   TEXT,
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP NULL
);
*/

-- ============================================================================
-- MS SQL SERVER / SQL SERVER VERSION (Metadata Database)
-- ============================================================================

/*
-- Add security columns to DMS_FLUPLD
ALTER TABLE dms_flupld ADD flhash VARCHAR(64);           -- SHA-256 file hash
ALTER TABLE dms_flupld ADD flsz BIGINT;                    -- File size in bytes
ALTER TABLE dms_flupld ADD flmimtyp VARCHAR(100);          -- MIME type
ALTER TABLE dms_flupld ADD flvrfyflg CHAR(1) DEFAULT 'N';  -- File verified (Y/N)
ALTER TABLE dms_flupld ADD flvrfydt DATETIME2 NULL;       -- Verification date
ALTER TABLE dms_flupld ADD flvrfyby VARCHAR(100);          -- Verified by (user/system)
ALTER TABLE dms_flupld ADD flqrnflg CHAR(1) DEFAULT 'N';  -- Quarantine flag (Y/N)
ALTER TABLE dms_flupld ADD flqrnrsn VARCHAR(500);          -- Quarantine reason
ALTER TABLE dms_flupld ADD flscnflg CHAR(1) DEFAULT 'N';  -- Virus scanned (Y/N)
ALTER TABLE dms_flupld ADD flscndt DATETIME2 NULL;         -- Scan date
ALTER TABLE dms_flupld ADD flscnrslt VARCHAR(50);          -- Scan result (CLEAN/INFECTED/ERROR)
ALTER TABLE dms_flupld ADD flacclvl VARCHAR(20) DEFAULT 'PRIVATE';  -- Access level
ALTER TABLE dms_flupld ADD flencflg CHAR(1) DEFAULT 'N';  -- Encrypted flag (Y/N)
ALTER TABLE dms_flupld ADD flencalg VARCHAR(50);          -- Encryption algorithm
ALTER TABLE dms_flupld ADD flupldcnt INT DEFAULT 0;       -- Upload attempt count
ALTER TABLE dms_flupld ADD fllstacctm DATETIME2 NULL;      -- Last access time
ALTER TABLE dms_flupld ADD flacccnt INT DEFAULT 0;         -- Access count
ALTER TABLE dms_flupld ADD flrtrntm DATETIME2 NULL;        -- Retention time
ALTER TABLE dms_flupld ADD flrtrnplcy VARCHAR(50);         -- Retention policy

-- Create File Access Audit Log table
CREATE TABLE dms_flupldacclg (
    acclgid       INT IDENTITY(1,1) PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    usrid         INT,
    usrnm         VARCHAR(100),
    acctyp        VARCHAR(20),
    accdt         DATETIME2 DEFAULT GETDATE(),
    ipaddr        VARCHAR(45),
    usragnt       VARCHAR(500),
    accsts        VARCHAR(20),
    accrsn        VARCHAR(500),
    flsz          BIGINT,
    flhash        VARCHAR(64)
);

CREATE INDEX idx_flupldacclg_ref ON dms_flupldacclg(flupldref);
CREATE INDEX idx_flupldacclg_usrid ON dms_flupldacclg(usrid);
CREATE INDEX idx_flupldacclg_accdt ON dms_flupldacclg(accdt);
CREATE INDEX idx_flupldacclg_acctyp ON dms_flupldacclg(acctyp);

-- Create File Validation Rules table
CREATE TABLE dms_flupldvld (
    vldid         INT IDENTITY(1,1) PRIMARY KEY,
    fltyp         VARCHAR(50) NOT NULL,
    maxsz         BIGINT,
    alwdexns      VARCHAR(MAX),
    alwdmimtyps   VARCHAR(MAX),
    blckdexns     VARCHAR(MAX),
    blckdpttrns   VARCHAR(MAX),
    rqrvrfy       CHAR(1) DEFAULT 'Y',
    rqrscn        CHAR(1) DEFAULT 'Y',
    rqrenc        CHAR(1) DEFAULT 'N',
    maxclmcnt     INT,
    maxrwcnt      BIGINT,
    vldcntnt      CHAR(1) DEFAULT 'Y',
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME2 DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME2 NULL
);

CREATE INDEX idx_flupldvld_fltyp ON dms_flupldvld(fltyp);

-- Create Security Configuration table
CREATE TABLE dms_flupldsec (
    secid         INT IDENTITY(1,1) PRIMARY KEY,
    scnngnbl      CHAR(1) DEFAULT 'Y',
    scnngprvd     VARCHAR(50),
    scnngcmd      VARCHAR(500),
    rqrvrfy       CHAR(1) DEFAULT 'Y',
    rqrenc        CHAR(1) DEFAULT 'N',
    encalg        VARCHAR(50),
    qrntnflg      CHAR(1) DEFAULT 'Y',
    qrntndir      VARCHAR(1000),
    rtrntm        INT DEFAULT 90,
    maxflsz       BIGINT DEFAULT 104857600,
    maxupldhr     INT DEFAULT 50,
    maxszhr       BIGINT DEFAULT 524288000,
    alwdflexts    VARCHAR(MAX),
    blckdflexts   VARCHAR(MAX),
    alwdiprngs    VARCHAR(MAX),
    blckdiprngs   VARCHAR(MAX),
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME2 DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME2 NULL
);
*/

-- ============================================================================
-- SYBASE VERSION (Metadata Database)
-- ============================================================================

/*
-- Add security columns to DMS_FLUPLD
ALTER TABLE dms_flupld ADD flhash VARCHAR(64);           -- SHA-256 file hash
ALTER TABLE dms_flupld ADD flsz BIGINT;                    -- File size in bytes
ALTER TABLE dms_flupld ADD flmimtyp VARCHAR(100);          -- MIME type
ALTER TABLE dms_flupld ADD flvrfyflg CHAR(1) DEFAULT 'N';  -- File verified (Y/N)
ALTER TABLE dms_flupld ADD flvrfydt DATETIME NULL;        -- Verification date
ALTER TABLE dms_flupld ADD flvrfyby VARCHAR(100);          -- Verified by (user/system)
ALTER TABLE dms_flupld ADD flqrnflg CHAR(1) DEFAULT 'N';  -- Quarantine flag (Y/N)
ALTER TABLE dms_flupld ADD flqrnrsn VARCHAR(500);          -- Quarantine reason
ALTER TABLE dms_flupld ADD flscnflg CHAR(1) DEFAULT 'N';  -- Virus scanned (Y/N)
ALTER TABLE dms_flupld ADD flscndt DATETIME NULL;         -- Scan date
ALTER TABLE dms_flupld ADD flscnrslt VARCHAR(50);          -- Scan result (CLEAN/INFECTED/ERROR)
ALTER TABLE dms_flupld ADD flacclvl VARCHAR(20) DEFAULT 'PRIVATE';  -- Access level
ALTER TABLE dms_flupld ADD flencflg CHAR(1) DEFAULT 'N';  -- Encrypted flag (Y/N)
ALTER TABLE dms_flupld ADD flencalg VARCHAR(50);          -- Encryption algorithm
ALTER TABLE dms_flupld ADD flupldcnt INT DEFAULT 0;       -- Upload attempt count
ALTER TABLE dms_flupld ADD fllstacctm DATETIME NULL;       -- Last access time
ALTER TABLE dms_flupld ADD flacccnt INT DEFAULT 0;         -- Access count
ALTER TABLE dms_flupld ADD flrtrntm DATETIME NULL;         -- Retention time
ALTER TABLE dms_flupld ADD flrtrnplcy VARCHAR(50);         -- Retention policy

-- Create File Access Audit Log table
CREATE TABLE dms_flupldacclg (
    acclgid       INT IDENTITY PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,
    usrid         INT,
    usrnm         VARCHAR(100),
    acctyp        VARCHAR(20),
    accdt         DATETIME DEFAULT GETDATE(),
    ipaddr        VARCHAR(45),
    usragnt       VARCHAR(500),
    accsts        VARCHAR(20),
    accrsn        VARCHAR(500),
    flsz          BIGINT,
    flhash        VARCHAR(64)
);

CREATE INDEX idx_flupldacclg_ref ON dms_flupldacclg(flupldref);
CREATE INDEX idx_flupldacclg_usrid ON dms_flupldacclg(usrid);
CREATE INDEX idx_flupldacclg_accdt ON dms_flupldacclg(accdt);
CREATE INDEX idx_flupldacclg_acctyp ON dms_flupldacclg(acctyp);

-- Create File Validation Rules table
CREATE TABLE dms_flupldvld (
    vldid         INT IDENTITY PRIMARY KEY,
    fltyp         VARCHAR(50) NOT NULL,
    maxsz         BIGINT,
    alwdexns       TEXT,
    alwdmimtyps    TEXT,
    blckdexns      TEXT,
    blckdpttrns    TEXT,
    rqrvrfy        CHAR(1) DEFAULT 'Y',
    rqrscn         CHAR(1) DEFAULT 'Y',
    rqrenc         CHAR(1) DEFAULT 'N',
    maxclmcnt      INT,
    maxrwcnt       BIGINT,
    vldcntnt       CHAR(1) DEFAULT 'Y',
    curflg         CHAR(1) DEFAULT 'Y',
    crtdby         VARCHAR(100),
    crtdt          DATETIME DEFAULT GETDATE(),
    uptdby         VARCHAR(100),
    uptdt          DATETIME NULL
);

CREATE INDEX idx_flupldvld_fltyp ON dms_flupldvld(fltyp);

-- Create Security Configuration table
CREATE TABLE dms_flupldsec (
    secid         INT IDENTITY PRIMARY KEY,
    scnngnbl      CHAR(1) DEFAULT 'Y',
    scnngprvd     VARCHAR(50),
    scnngcmd      VARCHAR(500),
    rqrvrfy       CHAR(1) DEFAULT 'Y',
    rqrenc        CHAR(1) DEFAULT 'N',
    encalg        VARCHAR(50),
    qrntnflg      CHAR(1) DEFAULT 'Y',
    qrntndir      VARCHAR(1000),
    rtrntm        INT DEFAULT 90,
    maxflsz       BIGINT DEFAULT 104857600,
    maxupldhr     INT DEFAULT 50,
    maxszhr       BIGINT DEFAULT 524288000,
    alwdflexts    TEXT,
    blckdflexts   TEXT,
    alwdiprngs    TEXT,
    blckdiprngs   TEXT,
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         DATETIME DEFAULT GETDATE(),
    uptdby        VARCHAR(100),
    uptdt         DATETIME NULL
);
*/

