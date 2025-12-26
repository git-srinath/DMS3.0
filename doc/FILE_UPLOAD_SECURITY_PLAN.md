# File Upload Module - Security & Controls Plan

## Overview
Comprehensive security controls and sophisticated validation mechanisms for file uploads to ensure data integrity, prevent malicious uploads, and maintain audit compliance. This plan supports multiple RDBMS platforms including PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, and other database systems.

## Security Architecture

### 1. File Validation Layers

#### Layer 1: Client-Side Validation (Frontend)
- **File Type Validation**: Whitelist-based file extension checking
- **File Size Validation**: Maximum size limit before upload
- **File Name Sanitization**: Remove special characters, path traversal attempts
- **Preview Before Upload**: Show file metadata before submission

#### Layer 2: Server-Side Validation (Backend)
- **Content-Type Verification**: Validate MIME type matches file extension
- **Magic Number Validation**: Check file headers (first bytes) to verify actual file type
- **File Size Limits**: Enforce server-side size restrictions
- **Filename Sanitization**: Remove dangerous characters, normalize paths
- **Content Scanning**: Scan for malicious patterns

#### Layer 3: Database Validation
- **Path Validation**: Ensure file paths are within allowed directories
- **Access Control**: Verify user permissions for file operations
- **Quarantine Flag**: Mark suspicious files for review

### 2. Enhanced Database Schema

#### Additional Security Columns for `DMS_FLUPLD`

**Multi-Database Support:** The following ALTER TABLE statements are provided for different database systems. Adapt syntax as needed for your specific database.

```sql
-- PostgreSQL
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
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flacclvl VARCHAR(20);          -- Access level (PUBLIC/PRIVATE/RESTRICTED)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flencflg CHAR(1) DEFAULT 'N';  -- Encrypted flag (Y/N)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flencalg VARCHAR(50);          -- Encryption algorithm
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flupldcnt INTEGER DEFAULT 0;   -- Upload attempt count
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS fllstacctm TIMESTAMP;          -- Last access time
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flacccnt INTEGER DEFAULT 0;    -- Access count
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flrtrntm TIMESTAMP;            -- Retention time (auto-delete after)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS flrtrnplcy VARCHAR(50);         -- Retention policy (DAYS_30/DAYS_90/YEARS_1/etc.)

-- Oracle
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
ALTER TABLE DMS_FLUPLD ADD (FLACCLVL VARCHAR2(20));          -- Access level (PUBLIC/PRIVATE/RESTRICTED)
ALTER TABLE DMS_FLUPLD ADD (FLENCFLG CHAR(1) DEFAULT 'N');  -- Encrypted flag (Y/N)
ALTER TABLE DMS_FLUPLD ADD (FLENCALG VARCHAR2(50));          -- Encryption algorithm
ALTER TABLE DMS_FLUPLD ADD (FLUPLDCNT NUMBER DEFAULT 0);     -- Upload attempt count
ALTER TABLE DMS_FLUPLD ADD (FLLSTACCTM TIMESTAMP(6));        -- Last access time
ALTER TABLE DMS_FLUPLD ADD (FLACCCNT NUMBER DEFAULT 0);      -- Access count
ALTER TABLE DMS_FLUPLD ADD (FLRTRNTM TIMESTAMP(6));          -- Retention time (auto-delete after)
ALTER TABLE DMS_FLUPLD ADD (FLRTRNPLCY VARCHAR2(50));       -- Retention policy

-- MySQL
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

-- MS SQL Server / SQL Server
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

-- Sybase
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
```

**Note:** For other RDBMS platforms (Redshift, Snowflake, DB2, Hive, etc.), adapt the data types and syntax accordingly. Use appropriate timestamp types (TIMESTAMP, DATETIME, DATETIME2) and integer types (INT, BIGINT, NUMBER) based on your database system.
```

#### File Access Audit Table: `DMS_FLUPLDACCLG`

**Multi-Database Support:** The following CREATE TABLE statements are provided for different database systems. Adapt syntax as needed for your specific database.

```sql
-- PostgreSQL
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

-- Oracle
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

-- MySQL
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

-- MS SQL Server / SQL Server
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

-- Sybase
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
```

#### File Validation Rules Table: `DMS_FLUPLDVLD`

**Multi-Database Support:** Adapt data types (TEXT vs CLOB vs VARCHAR(MAX)) based on your database system.

```sql
-- PostgreSQL
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

-- Oracle
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

-- MySQL (uses AUTO_INCREMENT instead of sequences)
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

-- MS SQL Server / SQL Server (uses IDENTITY instead of sequences)
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

-- Sybase (uses IDENTITY instead of sequences)
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
```

### 3. Security Controls Implementation

#### A. File Type Validation

**Magic Number Detection:**
```python
# File signature mapping
FILE_SIGNATURES = {
    'CSV': [b'\xEF\xBB\xBF', b'\xFF\xFE'],  # UTF-8 BOM, UTF-16 BOM
    'XLSX': [b'PK\x03\x04'],  # ZIP signature (XLSX is ZIP)
    'XLS': [b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'],  # OLE2 signature
    'JSON': [b'{', b'['],
    'XML': [b'<?xml', b'<'],
    'PARQUET': [b'PAR1'],
    'PDF': [b'%PDF-'],
    'GOOGLESHEETS': [],  # No file signature (API-based, not file-based)
    # Add more as needed
}

def validate_file_signature(file_path: str, expected_type: str) -> bool:
    """Validate file by checking magic numbers"""
    with open(file_path, 'rb') as f:
        header = f.read(20)  # Read first 20 bytes
        signatures = FILE_SIGNATURES.get(expected_type.upper(), [])
        return any(header.startswith(sig) for sig in signatures)
```

**MIME Type Validation:**
```python
import magic  # python-magic library

def validate_mime_type(file_path: str, expected_type: str) -> bool:
    """Validate MIME type matches file extension"""
    mime = magic.Magic(mime=True)
    detected_mime = mime.from_file(file_path)
    
    MIME_TYPE_MAP = {
        'CSV': ['text/csv', 'text/plain', 'application/csv'],
        'XLSX': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'XLS': ['application/vnd.ms-excel'],
        'JSON': ['application/json', 'text/json'],
        'XML': ['application/xml', 'text/xml'],
        'PARQUET': ['application/octet-stream'],  # Parquet doesn't have standard MIME
        'PDF': ['application/pdf'],
        'GOOGLESHEETS': [],  # No MIME type (API-based)
    }
    
    allowed_mimes = MIME_TYPE_MAP.get(expected_type.upper(), [])
    return detected_mime in allowed_mimes
```

#### B. File Size & Content Limits

```python
# Configuration
MAX_FILE_SIZE = {
    'CSV': 100 * 1024 * 1024,      # 100 MB
    'XLSX': 50 * 1024 * 1024,      # 50 MB
    'XLS': 50 * 1024 * 1024,       # 50 MB
    'JSON': 100 * 1024 * 1024,     # 100 MB
    'XML': 100 * 1024 * 1024,      # 100 MB
    'PARQUET': 500 * 1024 * 1024,  # 500 MB
    'PDF': 50 * 1024 * 1024,       # 50 MB
    'GOOGLESHEETS': None,          # No file size limit (API-based, limited by Google API quotas)
}

MAX_COLUMNS = 1000
MAX_ROWS = 10_000_000  # 10 million rows

def validate_file_size(file_path: str, file_type: str) -> tuple[bool, str]:
    """Validate file size against limits"""
    file_size = os.path.getsize(file_path)
    max_size = MAX_FILE_SIZE.get(file_type.upper(), 100 * 1024 * 1024)
    
    if file_size > max_size:
        return False, f"File size {file_size} exceeds maximum {max_size} bytes"
    return True, "OK"
```

#### C. Filename Sanitization

```python
import re
import os

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and injection"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Ensure not empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename

def validate_filename(filename: str) -> tuple[bool, str]:
    """Validate filename for security"""
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Filename contains path traversal characters"
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + \
                     [f'COM{i}' for i in range(1, 10)] + \
                     [f'LPT{i}' for i in range(1, 10)]
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False, "Filename uses reserved system name"
    
    return True, "OK"
```

#### D. Virus Scanning Integration

```python
import subprocess
import os

def scan_file_for_viruses(file_path: str) -> dict:
    """Scan file using ClamAV or Windows Defender"""
    result = {
        'scanned': False,
        'clean': False,
        'threats': [],
        'error': None
    }
    
    try:
        # Option 1: ClamAV (cross-platform)
        if os.name != 'nt':  # Linux/Mac
            cmd = ['clamscan', '--no-summary', file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                result['scanned'] = True
                result['clean'] = True
            elif process.returncode == 1:
                result['scanned'] = True
                result['clean'] = False
                result['threats'] = [process.stdout.strip()]
        
        # Option 2: Windows Defender (Windows only)
        elif os.name == 'nt':
            cmd = [
                'powershell',
                '-Command',
                f'Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring'
            ]
            # Use Windows Defender via PowerShell
            cmd = [
                'powershell',
                '-Command',
                f'$result = Start-MpScan -ScanType QuickScan -ScanPath "{file_path}"; $result.Threats'
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)
            # Parse result
            if 'No threats detected' in process.stdout:
                result['scanned'] = True
                result['clean'] = True
            else:
                result['scanned'] = True
                result['clean'] = False
                result['threats'] = [process.stdout.strip()]
        
    except FileNotFoundError:
        result['error'] = "Antivirus scanner not found"
    except Exception as e:
        result['error'] = str(e)
    
    return result
```

#### E. File Hash Calculation (Integrity)

```python
import hashlib

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate file hash for integrity verification"""
    hash_obj = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
    """Verify file hasn't been tampered with"""
    actual_hash = calculate_file_hash(file_path)
    return actual_hash == expected_hash
```

#### F. Quarantine System

```python
import shutil
from pathlib import Path

QUARANTINE_DIR = Path('data/quarantine')

def quarantine_file(file_path: str, reason: str) -> str:
    """Move file to quarantine directory"""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    quarantined_name = f"{timestamp}_{filename}"
    quarantine_path = QUARANTINE_DIR / quarantined_name
    
    shutil.move(file_path, quarantine_path)
    
    # Log quarantine action
    log_quarantine_action(quarantined_name, reason)
    
    return str(quarantine_path)
```

#### G. Access Control

```python
from enum import Enum

class AccessLevel(Enum):
    PUBLIC = 'PUBLIC'           # Anyone can access
    PRIVATE = 'PRIVATE'         # Only owner
    RESTRICTED = 'RESTRICTED'  # Specific users/groups
    CONFIDENTIAL = 'CONFIDENTIAL'  # Highest security

def check_file_access(user_id: int, file_ref: str, access_type: str) -> bool:
    """Check if user has permission to access file"""
    # Get file metadata
    file_meta = get_file_metadata(file_ref)
    
    if not file_meta:
        return False
    
    # Check access level
    access_level = AccessLevel(file_meta['flacclvl'])
    
    if access_level == AccessLevel.PUBLIC:
        return True
    
    if access_level == AccessLevel.PRIVATE:
        return file_meta['crtdby'] == get_username(user_id)
    
    if access_level == AccessLevel.RESTRICTED:
        # Check user permissions table
        return check_user_file_permission(user_id, file_ref)
    
    if access_level == AccessLevel.CONFIDENTIAL:
        # Require admin or explicit permission
        return is_admin(user_id) or check_user_file_permission(user_id, file_ref)
    
    return False
```

#### H. Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Rate limit tracking
upload_counts = defaultdict(list)

def check_rate_limit(user_id: int, file_size: int) -> tuple[bool, str]:
    """Check if user has exceeded rate limits"""
    now = datetime.now()
    user_uploads = upload_counts[user_id]
    
    # Remove old entries (older than 1 hour)
    user_uploads[:] = [dt for dt in user_uploads if now - dt < timedelta(hours=1)]
    
    # Limits
    MAX_UPLOADS_PER_HOUR = 50
    MAX_SIZE_PER_HOUR = 500 * 1024 * 1024  # 500 MB
    
    # Check upload count
    if len(user_uploads) >= MAX_UPLOADS_PER_HOUR:
        return False, f"Rate limit exceeded: {MAX_UPLOADS_PER_HOUR} uploads per hour"
    
    # Check total size (would need to track sizes)
    # This is simplified - in production, track sizes per upload
    
    # Add current upload
    user_uploads.append(now)
    
    return True, "OK"
```

#### I. Content Validation

```python
def validate_file_content(file_path: str, file_type: str) -> dict:
    """Validate file content structure"""
    result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'row_count': 0,
        'column_count': 0
    }
    
    try:
        if file_type.upper() == 'CSV':
            df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows
            result['column_count'] = len(df.columns)
            result['row_count'] = len(df)
            
            # Check for suspicious patterns
            for col in df.columns:
                # Check for SQL injection patterns
                if df[col].astype(str).str.contains(r"('|;|--|/\*|\*/|xp_|sp_)", case=False, na=False).any():
                    result['warnings'].append(f"Column {col} contains potential SQL injection patterns")
        
        elif file_type.upper() == 'XLSX':
            df = pd.read_excel(file_path, nrows=1000)
            result['column_count'] = len(df.columns)
            result['row_count'] = len(df)
        
        elif file_type.upper() == 'JSON':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    result['row_count'] = len(data)
                    if data:
                        result['column_count'] = len(data[0].keys()) if isinstance(data[0], dict) else 0
        
        elif file_type.upper() == 'PDF':
            # PDF validation - check if file is readable and has extractable content
            import pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    result['row_count'] = len(pdf.pages)  # Page count
                    # Try to extract first table to get column count
                    if pdf.pages:
                        tables = pdf.pages[0].extract_tables()
                        if tables and len(tables) > 0:
                            result['column_count'] = len(tables[0][0]) if tables[0] else 0
            except Exception as e:
                result['errors'].append(f"PDF validation error: {str(e)}")
        
        elif file_type.upper() == 'GOOGLESHEETS':
            # Google Sheets validation - check API access and sheet structure
            # This would require authentication, so validation might be deferred
            result['warnings'].append("Google Sheets validation requires API authentication")
        
        # Check limits
        if result['column_count'] > MAX_COLUMNS:
            result['errors'].append(f"Column count {result['column_count']} exceeds maximum {MAX_COLUMNS}")
        
        if result['row_count'] > MAX_ROWS:
            result['warnings'].append(f"Row count {result['row_count']} exceeds recommended {MAX_ROWS}")
        
        result['valid'] = len(result['errors']) == 0
        
    except Exception as e:
        result['errors'].append(f"Content validation error: {str(e)}")
    
    return result
```

### 4. Security Configuration

#### Security Settings Table: `DMS_FLUPLDSEC`

```sql
-- PostgreSQL
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

-- Oracle
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

-- MySQL (uses AUTO_INCREMENT instead of sequences)
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

-- MS SQL Server / SQL Server (uses IDENTITY instead of sequences)
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

-- Sybase (uses IDENTITY instead of sequences)
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
```

### 5. Security Workflow

#### Upload Process Flow

```
1. User selects file
   ↓
2. Client-side validation
   - File type check
   - File size check
   - Filename sanitization
   ↓
3. Upload to temporary location
   ↓
4. Server-side validation
   - Magic number check
   - MIME type verification
   - Filename validation
   - Path validation
   ↓
5. Rate limiting check
   ↓
6. Virus scanning (if enabled)
   ↓
7. Content validation
   - Structure validation
   - Pattern detection
   ↓
8. File hash calculation
   ↓
9. Access control check
   ↓
10. Encryption (if required)
    ↓
11. Move to final location
    ↓
12. Update database
    - Store metadata
    - Log access
    ↓
13. Notify user
```

### 6. Security Best Practices

#### A. File Storage Security
- **Isolated Storage**: Store files outside web root
- **Directory Permissions**: Restrict file system permissions (600 for files, 700 for directories)
- **Encryption at Rest**: Encrypt sensitive files
- **Backup Security**: Encrypt backups

#### B. Network Security
- **HTTPS Only**: Enforce HTTPS for all file transfers
- **IP Whitelisting**: Restrict uploads from specific IP ranges
- **VPN Requirement**: Require VPN for sensitive uploads

#### C. Authentication & Authorization
- **Multi-Factor Authentication**: Require MFA for file uploads
- **Role-Based Access**: Different permissions for different roles
- **Time-Based Access**: Restrict uploads to business hours

#### D. Monitoring & Alerting
- **Anomaly Detection**: Alert on unusual upload patterns
- **Failed Upload Tracking**: Monitor and alert on repeated failures
- **Access Logging**: Log all file access attempts

### 7. Implementation Priority

#### Phase 1: Critical Security (Week 1)
- [ ] Filename sanitization
- [ ] File type validation (extension + magic number)
- [ ] File size limits
- [ ] Path traversal prevention
- [ ] Basic access control
- [ ] File hash calculation

#### Phase 2: Enhanced Security (Week 2)
- [ ] Virus scanning integration
- [ ] Content validation
- [ ] Quarantine system
- [ ] Rate limiting
- [ ] Access audit logging

#### Phase 3: Advanced Security (Week 3)
- [ ] File encryption
- [ ] IP whitelisting/blacklisting
- [ ] Retention policies
- [ ] Advanced anomaly detection
- [ ] Security configuration UI

### 8. Security Testing

#### Test Cases
1. **Path Traversal**: Attempt `../../../etc/passwd`
2. **File Type Spoofing**: Upload `.exe` renamed as `.csv`
3. **Oversized Files**: Upload files exceeding limits
4. **Malicious Content**: Upload files with SQL injection patterns
5. **Rate Limiting**: Attempt rapid successive uploads
6. **Access Control**: Attempt to access files without permission
7. **Virus Files**: Upload known malware (in isolated environment)

### 9. Compliance Considerations

#### GDPR Compliance
- **Data Minimization**: Only collect necessary file metadata
- **Right to Erasure**: Implement file deletion on request
- **Data Retention**: Automatic deletion after retention period
- **Audit Trail**: Maintain logs of all file operations

#### SOX Compliance
- **Access Controls**: Strict access controls on financial data files
- **Audit Logging**: Comprehensive audit logs
- **Change Management**: Track all file modifications

#### HIPAA Compliance (if applicable)
- **Encryption**: Encrypt all PHI files
- **Access Logging**: Detailed access logs
- **Data Integrity**: File hash verification

### 10. Recommended Tools & Libraries

#### Python Libraries
- **python-magic**: MIME type detection
- **clamd**: ClamAV integration
- **cryptography**: File encryption
- **hashlib**: File hashing (built-in)
- **pandas**: Content validation

#### External Tools
- **ClamAV**: Open-source antivirus
- **Windows Defender**: Built-in Windows antivirus
- **VirusTotal API**: Cloud-based virus scanning (optional)

### 11. Configuration Examples

#### Default Security Settings
```python
DEFAULT_SECURITY_CONFIG = {
    'virus_scanning_enabled': True,
    'virus_scanner': 'CLAMAV',  # or 'DEFENDER' for Windows
    'require_verification': True,
    'require_encryption': False,
    'quarantine_enabled': True,
    'retention_days': 90,
    'max_file_size_mb': 100,
    'max_uploads_per_hour': 50,
    'max_size_per_hour_mb': 500,
    'allowed_extensions': ['csv', 'xlsx', 'xls', 'json', 'xml', 'parquet', 'pdf'],
    'blocked_extensions': ['exe', 'bat', 'cmd', 'sh', 'ps1', 'vbs', 'js'],
    'google_sheets_enabled': True,  # Enable Google Sheets integration
    'google_sheets_auth_method': 'SERVICE_ACCOUNT',  # SERVICE_ACCOUNT or OAUTH2
    'allowed_ip_ranges': [],  # Empty = allow all
    'blocked_ip_ranges': [],
}
```

## Summary

This security plan provides:
1. **Multi-layer validation** (client, server, database)
2. **File integrity** (hashing, verification)
3. **Threat detection** (virus scanning, pattern detection)
4. **Access control** (role-based, IP-based)
5. **Audit trail** (comprehensive logging)
6. **Compliance support** (GDPR, SOX, HIPAA)
7. **Quarantine system** (isolate suspicious files)
8. **Rate limiting** (prevent abuse)
9. **Encryption** (optional, for sensitive data)
10. **Retention policies** (automatic cleanup)

The implementation can be done in phases, starting with critical security controls and gradually adding more sophisticated features.

