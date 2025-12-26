# File Upload Module - Implementation Plan

## Overview
A new module to allow users to upload data from files (CSV, Excel, JSON, XML, Parquet, etc.) to database tables with column mapping, value derivation, and scheduling capabilities. The module is designed to be extensible, allowing easy addition of new file formats in the future.

## Module Name
**File Upload Module** (or **Data Import Module**)

## Architecture & Design

### 1. Database Schema

#### Multi-Database Support
The file upload module supports multiple RDBMS platforms for both metadata storage and target data loading:
- **Metadata Databases**: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, and other RDBMS
- **Target Databases**: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, Redshift, Snowflake, DB2, Hive, and other RDBMS

Database-specific SQL syntax differences are handled automatically through:
- Database type detection from connection objects
- SQL dialect abstraction layer
- Parameter placeholder conversion (`:1` → `%s` → `?` based on database)
- Data type mapping (VARCHAR2 → VARCHAR, NUMBER → INT/BIGINT, etc.)
- Sequence/identity column handling

#### Main Table: `DMS_FLUPLD` (File Upload Definition)
**Note:** Following DMS naming convention - vowels removed from table and column names

```sql
-- PostgreSQL Version
CREATE TABLE dms_flupld (
    flupldid      SERIAL PRIMARY KEY,
    flupldref     VARCHAR(100) UNIQUE NOT NULL,  -- Reference name (e.g., CUSTOMER_IMPORT)
    fluplddesc    VARCHAR(500),                   -- Description
    flnm          VARCHAR(500),                   -- Original filename
    fltyp         VARCHAR(50),                    -- CSV, XLSX, JSON, XML, PARQUET, TSV, etc.
    trgconid      INTEGER,                        -- Target DB connection ID
    trgschm       VARCHAR(100),                   -- Target schema
    trgtblnm      VARCHAR(100),                  -- Target table name
    trnctflg      CHAR(1) DEFAULT 'N',            -- Truncate before load (Y/N)
    frqcd         VARCHAR(10),                   -- Frequency code (DL, WK, etc.)
    stflg         CHAR(1) DEFAULT 'N',           -- Status flag (A=Active, N=Inactive)
    curflg        CHAR(1) DEFAULT 'Y',           -- Current flag
    crtdby        VARCHAR(100),                  -- Created by
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Created date
    uptdby        VARCHAR(100),                  -- Updated by
    uptdt         TIMESTAMP,                     -- Updated date
    lstrundt      TIMESTAMP,                     -- Last run date
    nxtrundt      TIMESTAMP                      -- Next run date
);

-- Oracle Version
CREATE TABLE DMS_FLUPLD (
    FLUPLDID      NUMBER PRIMARY KEY,
    FLUPLDREF     VARCHAR2(100) UNIQUE NOT NULL,
    FLUPLDDESC    VARCHAR2(500),
    FLNM          VARCHAR2(500),
    FLTYP         VARCHAR2(50),
    TRGCONID      NUMBER,
    TRGSCHM       VARCHAR2(100),
    TRGTBLNM      VARCHAR2(100),
    TRNCTFLG      CHAR(1) DEFAULT 'N',
    FRQCD         VARCHAR2(10),
    STFLG         CHAR(1) DEFAULT 'N',
    CURFLG        CHAR(1) DEFAULT 'Y',
    CRTDBY        VARCHAR2(100),
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    UPTDBY        VARCHAR2(100),
    UPTDATE       TIMESTAMP(6),
    LSTRUNDT      TIMESTAMP(6),
    NXTRUNDT      TIMESTAMP(6)
);

CREATE SEQUENCE DMS_FLUPLDSEQ;
```

**Note:** For other databases (MySQL, MS SQL Server, Sybase, etc.), use appropriate syntax:
- **MySQL**: Use `AUTO_INCREMENT` instead of sequences
- **MS SQL Server**: Use `IDENTITY(1,1)` or sequences (SQL Server 2012+)
- **Sybase**: Use `IDENTITY` or sequences depending on version

#### Detail Table: `DMS_FLUPLDDTL` (File Upload Column Mapping)
```sql
-- PostgreSQL Version
CREATE TABLE dms_fluplddtl (
    fluplddtlid   SERIAL PRIMARY KEY,
    flupldref     VARCHAR(100) NOT NULL,          -- Reference to DMS_FLUPLD
    srcclnm       VARCHAR(100),                   -- Source column name (from file)
    trgclnm       VARCHAR(100) NOT NULL,          -- Target column name (in DB)
    trgcldtyp     VARCHAR(50),                   -- Target column data type
    trgkyflg      CHAR(1) DEFAULT 'N',           -- Is primary key (Y/N)
    trgkyseq      INTEGER,                        -- Primary key sequence
    trgcldesc     VARCHAR(500),                  -- Column description
    drvlgc        TEXT,                          -- Value derivation logic (SQL/Python)
    drvlgcflg     CHAR(1) DEFAULT 'N',           -- Logic verified flag (Y/N)
    excseq        INTEGER,                       -- Execution sequence
    isaudit       CHAR(1) DEFAULT 'N',           -- Is audit column (Y/N)
    audttyp       VARCHAR(20),                   -- CREATED_DATE, UPDATED_DATE, CREATED_BY, etc.
    dfltval       VARCHAR(500),                  -- Default value
    isrqrd        CHAR(1) DEFAULT 'N',           -- Is required (Y/N)
    curflg        CHAR(1) DEFAULT 'Y',
    crtdby        VARCHAR(100),
    crtdt         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby        VARCHAR(100),
    uptdt         TIMESTAMP
);

-- Oracle Version
CREATE TABLE DMS_FLUPLDDTL (
    FLUPLDDTLID   NUMBER PRIMARY KEY,
    FLUPLDREF     VARCHAR2(100) NOT NULL,
    SRCCLNM       VARCHAR2(100),
    TRGCLNM       VARCHAR2(100) NOT NULL,
    TRGCLDTYP     VARCHAR2(50),
    TRGKYFLG      CHAR(1) DEFAULT 'N',
    TRGKYSEQ      NUMBER,
    TRGCLDESC     VARCHAR2(500),
    DRVLGC        CLOB,
    DRVLGCFLG     CHAR(1) DEFAULT 'N',
    EXCSEQ        NUMBER,
    ISAUDIT       CHAR(1) DEFAULT 'N',
    AUDTTYP       VARCHAR2(20),
    DFLTVAL       VARCHAR2(500),
    ISRQRD        CHAR(1) DEFAULT 'N',
    CURFLG        CHAR(1) DEFAULT 'Y',
    CRTDBY        VARCHAR2(100),
    CRTDATE       TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    UPTDBY        VARCHAR2(100),
    UPTDATE       TIMESTAMP(6)
);

CREATE SEQUENCE DMS_FLUPLDDTLSEQ;
```

**Note:** For other databases, adapt sequence/identity column syntax as needed.

**Naming Convention:**
- `FLUPLD` = File Upload (vowels removed: FILEUPLD → FLUPLD)
- `FLUPLDDTL` = File Upload Detail
- `FLNM` = File Name
- `FLTYP` = File Type
- `TRNCTFLG` = Truncate Flag
- `DRVLGC` = Derivation Logic
- `AUDTTYP` = Audit Type
- `DFLTVAL` = Default Value
- `ISRQRD` = Is Required

#### Audit Columns (Default)
- `CREATED_DATE` - TIMESTAMP (auto-populated on insert)
- `UPDATED_DATE` - TIMESTAMP (auto-populated on insert/update)
- `CREATED_BY` - VARCHAR2(100) (from current user)
- `UPDATED_BY` - VARCHAR2(100) (from current user)

### 2. Frontend Structure

#### Directory: `frontend/src/app/file_upload_module/`

**Files:**
- `page.js` - Main page component (similar to mapper_module/page.js)
- `UploadTable.js` - List view of all file upload configurations
- `UploadForm.js` - Main form component (similar to ReferenceForm.js)
- `FileUploadDialog.js` - Dialog for file selection and preview
- `ColumnMappingTable.js` - Table for column mapping configuration
- `ScheduleDialog.js` - Dialog for scheduling configuration (reuse from jobs module)

#### UI Layout (Similar to Mapper Module)

**Header Section:**
```
┌─────────────────────────────────────────────────────────────┐
│ File Upload Configuration                                    │
├─────────────────────────────────────────────────────────────┤
│ Reference: [___________]  Description: [_________________]  │
│ File: [Browse...] [filename.xlsx]                          │
│ Target DB: [Dropdown]  Schema: [____]  Table: [___________]   │
│ Truncate Before Load: [☑]  Frequency: [Daily ▼]          │
│ Header Rows to Skip: [0]  Footer Rows to Skip: [0]        │
│ Header Pattern: [________]  Footer Pattern: [________]     │
└─────────────────────────────────────────────────────────────┘
```

**Details Panel:**
```
┌─────────────────────────────────────────────────────────────┐
│ Column Mapping                                               │
├──────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Seq  │ Source   │ Target   │ Data    │ Key?    │ Logic   │
│      │ Column   │ Column   │ Type    │         │         │
├──────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│  1   │ id       │ ID       │ NUMBER  │ ☑ (1)  │ [Edit]  │
│  2   │ name     │ NAME     │ VARCHAR │        │ [Edit]  │
│  3   │ email    │ EMAIL    │ VARCHAR │        │ [Edit]  │
│  4   │ [AUDIT]  │ CREATED_ │ TIMESTAM│        │ AUTO    │
│      │          │ DATE     │ P       │        │         │
│  5   │ [AUDIT]  │ CREATED_ │ VARCHAR │        │ AUTO    │
│      │          │ BY       │         │        │         │
└──────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3. Backend Structure

#### Directory: `backend/modules/file_upload/`

**Files:**
- `__init__.py` - Package initialization
- `fastapi_file_upload.py` - FastAPI router with endpoints
- `file_upload_service.py` - Business logic for file processing
- `file_parser.py` - File parsing utilities (CSV, Excel, JSON, XML, Parquet, TSV)
- `parsers/` - Directory for format-specific parsers
  - `csv_parser.py` - CSV/TSV parser
  - `excel_parser.py` - Excel (XLSX, XLS) parser
  - `json_parser.py` - JSON parser
  - `xml_parser.py` - XML parser
  - `parquet_parser.py` - Parquet parser
  - `base_parser.py` - Base parser interface for extensibility
- `column_mapper.py` - Column mapping and transformation logic
- `data_loader.py` - Database loading logic

### 4. API Endpoints

#### File Upload Endpoints
```
POST   /file-upload/upload-file          - Upload and parse file
GET    /file-upload/get-all-uploads       - Get all upload configurations
GET    /file-upload/get-by-reference/{ref} - Get upload config by reference
POST   /file-upload/save                  - Save upload configuration
POST   /file-upload/validate               - Validate configuration
POST   /file-upload/execute                - Execute file upload immediately
POST   /file-upload/activate-deactivate   - Activate/deactivate upload
POST   /file-upload/delete                 - Delete upload configuration
GET    /file-upload/get-connections        - Get available DB connections
GET    /file-upload/preview-file           - Preview file contents (first N rows)
```

#### Scheduling Endpoints (Reuse from jobs module)
```
POST   /file-upload/save-schedule          - Save schedule configuration
GET    /file-upload/get-schedule/{ref}      - Get schedule details
```

### 5. Implementation Phases

#### Phase 1: Core Infrastructure (Week 1)
1. **Database Schema**
   - Create `DMS_FILEUPLD` table
   - Create `DMS_FILEUPLDDTL` table
   - Create sequences
   - Add audit columns support

2. **Backend Foundation**
   - Create FastAPI router structure
   - File upload endpoint (multipart/form-data)
   - File parsing utilities (CSV, Excel, JSON)
   - Basic CRUD operations

3. **Frontend Foundation**
   - Create module directory structure
   - UploadTable component (list view)
   - Basic routing

#### Phase 2: File Upload & Parsing (Week 2)
1. **File Upload Dialog**
   - File selection component
   - File type detection
   - File preview (first 10-20 rows)
   - File metadata extraction

2. **File Parsers**
   - CSV parser (with delimiter detection)
   - Excel parser (XLSX, XLS)
   - JSON parser (flat and nested)
   - XML parser (with XPath support for nested structures)
   - Parquet parser (columnar format support)
   - TSV parser (tab-separated values)
   - Base parser interface for extensibility
   - Error handling for malformed files

3. **Column Auto-Detection**
   - Extract column names from file
   - Suggest data types based on sample data
   - Default column mapping

#### Phase 3: Column Mapping UI (Week 3)
1. **UploadForm Component**
   - Header section with file details
   - Target database/schema/table selection
   - Column mapping table
   - Add/remove columns
   - Edit column properties

2. **Column Mapping Features**
   - Source column → Target column mapping
   - Data type selection (from `DMS_PARAMS` parameter system)
     - Dropdown populated from `/mapper/get-parameter-mapping-datatype` API endpoint
     - Shows generic data types (PRCD) with descriptions (PRDESC)
     - Stores generic type code in `DMS_FLUPLDDTL.TRGCLDTYP`
     - Validates data type exists in `DMS_PARAMS` before saving
     - Same data type options as mapper module for consistency
   - Primary key configuration
   - Default values
   - Required field flags

3. **Parameter System Integration**
   - Fetch available data types on component mount
   - Cache data type list for performance
   - Handle data type validation errors
   - Show user-friendly error messages for invalid data types

3. **Audit Columns**
   - Auto-add audit columns
   - Show audit columns in UI
   - Configure audit column types
   - Auto-population logic

#### Phase 4: Value Derivation & Transformation (Week 4)
1. **Logic Editor**
   - SQL expression editor (similar to mapper module)
   - Python expression support
   - Syntax validation
   - Preview transformed values

2. **Transformation Types**
   - Direct mapping (source → target)
   - SQL expressions (e.g., `UPPER(source_column)`)
   - Python expressions (e.g., `source_column.strip()`)
   - Constant values
   - Date/time formatting

3. **Validation**
   - Logic syntax validation
   - Data type validation
     - Validates generic data type exists in `DMS_PARAMS` (PRTYP='Datatype')
     - Uses same validation logic as mapper module
     - Ensures data type is available for target database
   - Required field validation
   - Primary key uniqueness

#### Phase 5: Data Loading (Week 5)
1. **Data Loader Service**
   - Batch processing
   - Transaction management
   - Error handling and logging
   - Progress tracking
   - **Multi-database support**:
     - Database type detection from target connection
     - SQL dialect-specific query generation
     - Parameter placeholder conversion (`:1`, `%s`, `?`)
     - **Data type resolution from parameter system**:
       - Query target database's `DMS_PARAMS` table
       - Resolve generic type (PRCD) to database-specific type (PRVAL)
       - Use resolved type for table creation and data insertion
     - Database-specific bulk insert methods

2. **Load Strategies**
   - Insert only
   - Upsert (update if exists, insert if not)
     - Oracle: `MERGE` statement
     - PostgreSQL: `ON CONFLICT` clause
     - MySQL: `ON DUPLICATE KEY UPDATE`
     - MS SQL Server: `MERGE` statement
     - Sybase: `MERGE` or `IF EXISTS` logic
   - Truncate and load
   - Incremental load (based on date/key)

3. **Execution**
   - Immediate execution
   - Background job execution
   - Progress monitoring
   - Error reporting
   - **Database-specific optimizations**:
     - Bulk insert methods per database
     - Batch size optimization per database type
     - Connection pooling per database type

#### Phase 6: Scheduling Integration (Week 6)
1. **Schedule Configuration**
   - Reuse schedule dialog from jobs module
   - Frequency selection (Daily, Weekly, etc.)
   - Schedule time configuration
   - Save schedule to `DMS_JOBSCH` table

2. **Scheduler Integration**
   - Register file upload jobs with scheduler
   - Automatic file detection (if file path is scheduled)
   - Job execution via scheduler
   - Update last run / next run dates

#### Phase 7: Testing & Refinement (Week 7)
1. **Testing**
   - Unit tests for file parsers
   - Integration tests for data loading
   - UI/UX testing
   - Performance testing (large files)

2. **Documentation**
   - User guide
   - API documentation
   - Troubleshooting guide

### 6. Key Features & Functionality

#### File Upload
- **Supported Formats**: 
  - **CSV/TSV** - Comma/Tab-separated values
  - **Excel** - XLSX, XLS
  - **JSON** - Flat and nested JSON structures
  - **XML** - XML files with XPath support for element selection
  - **Parquet** - Columnar format (Apache Parquet)
  - **PDF** - PDF files with table extraction support
  - **Google Sheets** - Direct integration with Google Sheets API
  - **Extensible** - Plugin architecture for adding new formats
- **File Size Limit**: Configurable (default 100MB, higher for Parquet)
- **Encoding Detection**: Auto-detect UTF-8, Latin-1, Windows-1252, etc.
- **Delimiter Detection**: Auto-detect CSV/TSV delimiters (comma, tab, semicolon, pipe)
- **Format-Specific Features**:
  - **XML**: 
    - XPath configuration for selecting elements
    - Handling attributes and nested structures
    - Support for multiple root elements
    - Namespace handling
    - Configurable row element selector
   - **Parquet**: 
     - Schema inference from Parquet metadata
     - Column type detection (preserves Parquet types)
     - Efficient columnar reading
     - Support for complex types (arrays, maps, structs)
     - Partitioned file support
   - **PDF**: 
     - Table extraction from PDF documents
     - Text extraction for non-tabular data
     - Multi-page support
     - OCR support (optional, for scanned PDFs)
     - Page range selection
   - **Google Sheets**: 
     - Direct API integration (no file download needed)
     - OAuth2 authentication
     - Support for specific sheet/tab selection
     - Range selection (specific cell ranges)
     - Real-time data fetching
     - Support for both file upload (downloaded as Excel/CSV) and direct API access
  - **JSON**: 
    - Flatten nested objects
    - Array handling (one row per array element)
    - JSONPath support for nested data extraction
  - **CSV/TSV**: 
    - Header row detection
    - Multiple delimiter support
    - Quote character handling

#### Column Mapping
- **Auto-Mapping**: Pre-fill columns from file headers
- **Smart Suggestions**: Suggest data types based on sample data
- **Data Type Selection**: 
  - Users select from generic data types available in `DMS_PARAMS` (PRTYP='Datatype')
  - Generic types (PRCD) are stored in `DMS_FLUPLDDTL.TRGCLDTYP`
  - Database-specific types (PRVAL) are resolved at table creation time
  - Uses same parameter system as mapper module for consistency
- **Default Table Name**: Generate from filename (e.g., `customer_data.xlsx` → `CUSTOMER_DATA`)
- **Column Reordering**: Drag-and-drop column ordering
- **Column Filtering**: Show/hide columns

#### Value Derivation
- **SQL Expressions**: `UPPER(name)`, `TRIM(email)`, `TO_DATE(date_str, 'YYYY-MM-DD')`
- **Python Expressions**: `value.strip()`, `value.replace(' ', '_')`
- **Constants**: Fixed values for columns
- **Conditional Logic**: `CASE WHEN ... THEN ... ELSE ... END`

#### Audit Columns
- **Auto-Added**: `CREATED_DATE`, `UPDATED_DATE`, `CREATED_BY`, `UPDATED_BY`
- **Visible in UI**: Always shown in column mapping table
- **Auto-Populated**: System handles population, user cannot edit
- **Configurable**: User can choose which audit columns to include

#### Scheduling
- **Frequency Options**: Daily, Weekly, Monthly, etc.
- **Time Configuration**: Specific time of day
- **File Path Monitoring**: (Future) Monitor file system for new files
- **Job Integration**: Create job in `DMS_JOB` table for tracking

### 7. Technical Considerations

#### Multi-Database Considerations

**Database Type Detection:**
- Auto-detect database type from connection object (via `_detect_db_type()` helper)
- Support for: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, Redshift, Snowflake, DB2, Hive
- Fallback to environment variable `DB_TYPE` if connection detection fails

**SQL Syntax Abstraction:**
- Parameter placeholders:
  - Oracle: `:1`, `:2`, `:3` (named or positional)
  - PostgreSQL: `%s`, `%s`, `%s` (positional)
  - MySQL: `%s` (positional)
  - MS SQL Server: `?` (positional) or `@param1`, `@param2` (named)
  - Sybase: `?` (positional) or `@param1` (named)
- Date/time functions:
  - Oracle: `SYSDATE`, `SYSTIMESTAMP`, `TO_DATE()`, `TO_TIMESTAMP()`
  - PostgreSQL: `CURRENT_TIMESTAMP`, `NOW()`, `TO_TIMESTAMP()`
  - MySQL: `NOW()`, `CURRENT_TIMESTAMP()`, `STR_TO_DATE()`
  - MS SQL Server: `GETDATE()`, `GETUTCDATE()`, `CONVERT()`
  - Sybase: `GETDATE()`, `CONVERT()`
- String concatenation:
  - Oracle: `||` operator
  - PostgreSQL: `||` operator
  - MySQL: `CONCAT()` function or `||` (if enabled)
  - MS SQL Server: `+` operator or `CONCAT()`
  - Sybase: `+` operator

**Data Type Mapping:**
- Uses existing `DMS_PARAMS` parameter system (PRTYP='Datatype')
- Generic data types (PRCD) stored in `DMS_FLUPLDDTL.TRGCLDTYP`
- Database-specific types (PRVAL) resolved from target database's `DMS_PARAMS` table
- Same approach as mapper module for consistency
- Supports all database types through parameter configuration

**Identity Columns and Sequences:**
- Oracle: Use sequences with `SEQUENCE.NEXTVAL`
- PostgreSQL: Use `SERIAL` or sequences with `nextval()`
- MySQL: Use `AUTO_INCREMENT`
- MS SQL Server: Use `IDENTITY(1,1)` or sequences (SQL Server 2012+)
- Sybase: Use `IDENTITY` or sequences

**Bulk Insert Methods:**
- Oracle: `INSERT ALL` or batch inserts with `executemany()`
- PostgreSQL: `COPY` command or batch inserts
- MySQL: `LOAD DATA INFILE` or batch inserts
- MS SQL Server: `BULK INSERT` or batch inserts
- Sybase: `BULK INSERT` or batch inserts

#### File Storage
- **Option 1**: Store files in database as BLOB (in `DMS_FILEUPLD`)
- **Option 2**: Store files on filesystem, save path in database
- **Recommendation**: Option 2 (filesystem) for better performance

#### Performance
- **Batch Processing**: Process files in batches (e.g., 1000 rows at a time)
- **Database-Specific Batch Sizes**:
  - Oracle: 100-1000 rows per batch
  - PostgreSQL: 1000-5000 rows per batch
  - MySQL: 1000-5000 rows per batch
  - MS SQL Server: 1000-5000 rows per batch
  - Sybase: 500-2000 rows per batch
- **Streaming**: For large files, use streaming instead of loading entire file
  - **XML**: Use SAX parser for large XML files (streaming)
  - **Parquet**: Use chunked reading for large Parquet files
  - **CSV**: Use iterator-based reading for large CSV files
- **Progress Tracking**: Show progress bar during upload/processing
- **Memory Management**: 
  - Parquet: Read in chunks to avoid loading entire file
  - XML: Use streaming parser for files > 50MB
  - JSON: Stream large JSON arrays

#### Error Handling
- **File Parsing Errors**: Show line number and error message
- **Data Validation Errors**: Log invalid rows, continue processing valid rows
- **Database Errors**: Rollback transaction, show detailed error
- **Database-Specific Error Handling**:
  - Parse database-specific error codes and messages
  - Handle constraint violations per database type
  - Handle connection timeout errors

#### Security
- **File Type Validation**: Only allow approved file types
- **File Size Limits**: Prevent DoS attacks
- **SQL Injection Prevention**: Always use parameterized queries (database-agnostic)
- **Path Traversal Prevention**: Validate file paths
- **XML Security**: 
  - Disable external entity resolution (XXE attacks)
  - Validate XML against schema if provided
  - Limit XML depth to prevent billion laughs attack
- **Parquet Security**: 
  - Validate Parquet file structure
  - Limit column count to prevent memory exhaustion

### 8. Integration Points

#### With Existing Modules
- **DB Connections Module**: Reuse connection selection
- **Jobs Module**: Reuse scheduling functionality
- **Mapper Module**: 
  - Similar UI patterns and validation logic
  - **Shared Parameter System**: Uses same `DMS_PARAMS` table for data type management
  - **Consistent Data Types**: Same generic data types (PRCD) used across both modules
  - **Shared Functions**: Reuses `get_parameter_mapping_datatype()` from `helper_functions.py`
  - **Validation Logic**: Uses same data type validation as mapper module
- **Parameter Mapping Module**: 
  - Users configure data type mappings in parameter screen
  - File upload module reads these mappings for data type resolution
  - Supports multi-database through database-specific PRVAL values
- **Reports Module**: (Future) Generate reports on uploaded data

#### Database Integration
- **Metadata DB (Multi-Database Support)**: Store configuration in `DMS_FLUPLD` and `DMS_FLUPLDDTL`
  - Supported metadata databases: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, and other RDBMS
  - Database type detected from `DB_TYPE` environment variable or connection configuration
  - Table and column names follow DMS convention (vowels removed: FLUPLD, FLNM, FLTYP, etc.)
- **Target DB (Multi-Database Support)**: Load data to user-specified target database
  - Supported target databases: PostgreSQL, Oracle, MySQL, MS SQL Server, Sybase, Redshift, Snowflake, DB2, Hive, and other RDBMS
  - Target database selected via `trgconid` (connection ID from `DMS_DBCONDTLS`)
  - Database-specific SQL syntax and data types handled automatically
- **Job Tracking**: Use `DMS_JOB` and `DMS_JOBSCH` for scheduling
- **Multi-DB Support Architecture**: 
  - Database type auto-detection from connection objects
  - Database-specific SQL syntax handling (parameter placeholders, date functions, etc.)
  - Database-specific data type mappings (VARCHAR vs VARCHAR2, NUMBER vs INT, etc.)
  - Database-specific features (sequences, auto-increment, identity columns, etc.)
  - Connection pooling and driver management via `DRIVER_REGISTRY`

### 9. UI/UX Guidelines

#### Design Consistency
- Match mapper module's look and feel
- Use same color scheme and component styles
- Consistent button placement and actions
- Same validation error display patterns

#### User Experience
- **Wizard Flow**: (Optional) Step-by-step wizard for first-time users
- **Quick Actions**: One-click actions for common scenarios
- **Preview Before Save**: Show preview of mapped data before saving
- **Undo/Redo**: Allow users to undo changes
- **Keyboard Shortcuts**: Support common shortcuts (Ctrl+S to save, etc.)

### 10. Extensibility Architecture

#### Parser Plugin System
The module uses a plugin-based architecture for file parsers, making it easy to add new formats:

```python
# Base parser interface
from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict

class BaseFileParser(ABC):
    @abstractmethod
    def detect_format(self, file_path: str) -> bool:
        """Detect if file matches this parser's format"""
        pass
    
    @abstractmethod
    def parse(self, file_path: str, options: dict) -> pd.DataFrame:
        """Parse file and return DataFrame"""
        pass
    
    @abstractmethod
    def get_columns(self, file_path: str) -> List[str]:
        """Get column names from file"""
        pass
    
    @abstractmethod
    def preview(self, file_path: str, rows: int = 10) -> pd.DataFrame:
        """Preview first N rows"""
        pass

# Example: Adding a new format
class AvroParser(BaseFileParser):
    def detect_format(self, file_path: str) -> bool:
        return file_path.endswith('.avro')
    
    def parse(self, file_path: str, options: dict) -> pd.DataFrame:
        # Implementation for Avro parsing
        pass
```

#### Adding New Formats
1. Create parser class inheriting from `BaseFileParser`
2. Implement required methods
3. Register parser in `file_parser.py`
4. Add file type to database enum/validation
5. Update frontend file type dropdown

#### Supported Extensions (Future)
- **Avro** - Apache Avro format
- **ORC** - Optimized Row Columnar format
- **Fixed Width** - Fixed-width text files
- **EDIFACT** - EDI format
- **HL7** - Healthcare data format
- **Custom Delimited** - User-defined delimiters
- **Microsoft OneDrive** - Direct integration with OneDrive
- **Dropbox** - Direct integration with Dropbox
- **Box** - Direct integration with Box

### 11. Multi-Database Implementation Details

#### Database Abstraction Layer

The file upload module uses a database abstraction layer to handle differences between database systems:

```python
# Example: Database-specific SQL generation
def generate_insert_sql(table_name: str, columns: list, db_type: str) -> str:
    """Generate INSERT SQL based on database type"""
    placeholders = {
        'ORACLE': ':1, :2, :3',
        'POSTGRESQL': '%s, %s, %s',
        'MYSQL': '%s, %s, %s',
        'MSSQL': '?, ?, ?',
        'SQL_SERVER': '?, ?, ?',
        'SYBASE': '?, ?, ?'
    }
    
    cols = ', '.join(columns)
    params = placeholders.get(db_type, '%s, %s, %s')
    
    if db_type in ['ORACLE', 'POSTGRESQL']:
        return f"INSERT INTO {table_name} ({cols}) VALUES ({params})"
    else:
        return f"INSERT INTO {table_name} ({cols}) VALUES ({params})"

def get_current_timestamp_sql(db_type: str) -> str:
    """Get current timestamp SQL function based on database type"""
    timestamp_funcs = {
        'ORACLE': 'SYSTIMESTAMP',
        'POSTGRESQL': 'CURRENT_TIMESTAMP',
        'MYSQL': 'NOW()',
        'MSSQL': 'GETDATE()',
        'SQL_SERVER': 'GETDATE()',
        'SYBASE': 'GETDATE()'
    }
    return timestamp_funcs.get(db_type, 'CURRENT_TIMESTAMP')
```

#### Data Type Mapping Using Parameter System

The file upload module uses the existing **DMS_PARAMS** parameter mapping system for data type management, consistent with the mapper module:

```python
from backend.modules.helper_functions import get_parameter_mapping_datatype

def get_database_specific_datatype(target_connection, generic_datatype: str) -> str:
    """
    Get database-specific data type from DMS_PARAMS based on target database.
    
    Args:
        target_connection: Connection to target database
        generic_datatype: Generic data type code (e.g., 'VARCHAR', 'INTEGER', 'TIMESTAMP')
    
    Returns:
        Database-specific data type value (PRVAL from DMS_PARAMS)
    """
    cursor = target_connection.cursor()
    db_type = _detect_db_type(target_connection)
    
    # Query DMS_PARAMS from target database connection
    if db_type == "POSTGRESQL":
        dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
        query = f"""
            SELECT PRVAL 
            FROM {dms_params_ref} 
            WHERE PRTYP = 'Datatype' AND PRCD = %s
        """
        cursor.execute(query, (generic_datatype,))
    else:  # Oracle, MySQL, MS SQL Server, Sybase, etc.
        query = """
            SELECT PRVAL 
            FROM DMS_PARAMS 
            WHERE PRTYP = 'Datatype' AND PRCD = :1
        """
        cursor.execute(query, [generic_datatype])
    
    row = cursor.fetchone()
    cursor.close()
    
    if row:
        return row[0]  # Return PRVAL (database-specific data type)
    else:
        # Fallback to generic type if not found in parameters
        return generic_datatype

def get_available_datatypes(metadata_connection):
    """
    Get list of available generic data types from DMS_PARAMS.
    Used in UI for data type selection dropdown.
    
    Returns:
        List of dictionaries with PRCD (code), PRDESC (description), PRVAL (value)
    """
    return get_parameter_mapping_datatype(metadata_connection)
```

**How It Works:**
1. **User Selection**: Users select generic data types (PRCD values like 'VARCHAR', 'INTEGER', 'TIMESTAMP') from the parameter system
2. **Storage**: The generic data type code is stored in `DMS_FLUPLDDTL.TRGCLDTYP`
3. **Table Creation**: When creating target tables, the system:
   - Queries `DMS_PARAMS` from the **target database connection**
   - Looks up `PRVAL` where `PRTYP='Datatype'` and `PRCD` matches the generic type
   - Uses the `PRVAL` (database-specific type) for actual table creation
4. **Multi-Database Support**: Each target database has its own `DMS_PARAMS` table with database-specific `PRVAL` values

**Example:**
- Generic type: `VARCHAR` (stored in `DMS_FLUPLDDTL.TRGCLDTYP`)
- Oracle target: Queries Oracle's `DMS_PARAMS`, gets `PRVAL='VARCHAR2(255)'`
- PostgreSQL target: Queries PostgreSQL's `DMS_PARAMS`, gets `PRVAL='VARCHAR(255)'`
- MySQL target: Queries MySQL's `DMS_PARAMS`, gets `PRVAL='VARCHAR(255)'`

**Integration with Existing System:**
- Reuses `get_parameter_mapping_datatype()` from `helper_functions.py`
- Uses same parameter validation as mapper module
- Consistent with existing data type management approach

#### Bulk Insert Strategies

Different databases have different optimal bulk insert methods:

```python
def bulk_insert_data(connection, table_name: str, data: list, db_type: str):
    """Perform bulk insert optimized for each database type"""
    
    if db_type == 'POSTGRESQL':
        # Use COPY command for PostgreSQL (fastest)
        cursor = connection.cursor()
        cursor.copy_from(data, table_name)
        connection.commit()
    
    elif db_type == 'MYSQL':
        # Use executemany with batch size
        cursor = connection.cursor()
        cursor.executemany(insert_sql, data)
        connection.commit()
    
    elif db_type == 'MSSQL' or db_type == 'SQL_SERVER':
        # Use BULK INSERT or executemany
        cursor = connection.cursor()
        cursor.executemany(insert_sql, data)
        connection.commit()
    
    elif db_type == 'ORACLE':
        # Use executemany with array size optimization
        cursor = connection.cursor()
        cursor.arraysize = 1000
        cursor.executemany(insert_sql, data)
        connection.commit()
    
    elif db_type == 'SYBASE':
        # Use executemany
        cursor = connection.cursor()
        cursor.executemany(insert_sql, data)
        connection.commit()
```

#### Connection Management

```python
from backend.database.dbconnect import create_target_connection, DRIVER_REGISTRY

def get_target_connection(connection_id: int):
    """Get target database connection using existing infrastructure"""
    # Uses create_target_connection() which handles all database types
    return create_target_connection(connection_id)

def detect_database_type(connection):
    """Detect database type from connection object"""
    from backend.modules.common.db_table_utils import _detect_db_type
    return _detect_db_type(connection)
```

#### Schema and Table Name Handling

```python
def format_table_name(schema: str, table: str, db_type: str) -> str:
    """Format table name based on database type"""
    if not schema:
        return table
    
    if db_type == 'POSTGRESQL':
        # PostgreSQL: schema.table (lowercase if unquoted)
        return f"{schema.lower()}.{table.lower()}"
    elif db_type == 'ORACLE':
        # Oracle: SCHEMA.TABLE (uppercase)
        return f"{schema.upper()}.{table.upper()}"
    elif db_type in ['MSSQL', 'SQL_SERVER', 'SYBASE']:
        # SQL Server/Sybase: [schema].[table] or schema.table
        return f"{schema}.{table}"
    elif db_type == 'MYSQL':
        # MySQL: schema.table (case-sensitive on Linux, case-insensitive on Windows)
        return f"{schema}.{table}"
    else:
        return f"{schema}.{table}"
```

#### Table Creation with Parameter System

```python
def create_target_table_from_file_upload(target_connection, flupldref: str, 
                                         target_schema: str, target_table: str):
    """
    Create target table for file upload using parameter system for data types.
    
    Args:
        target_connection: Connection to target database
        flupldref: File upload reference
        target_schema: Target schema name
        target_table: Target table name
    """
    from backend.modules.helper_functions import get_parameter_mapping_datatype
    from backend.database.dbconnect import create_metadata_connection
    
    # Get metadata connection to read column mappings
    metadata_conn = create_metadata_connection()
    metadata_cursor = metadata_conn.cursor()
    
    # Get column mappings from DMS_FLUPLDDTL
    db_type = _detect_db_type(metadata_conn)
    if db_type == "POSTGRESQL":
        query = """
            SELECT trgclnm, trgcldtyp, trgkyflg, trgkyseq, isrqrd
            FROM dms_fluplddtl
            WHERE flupldref = %s AND curflg = 'Y'
            ORDER BY excseq
        """
        metadata_cursor.execute(query, (flupldref,))
    else:  # Oracle
        query = """
            SELECT trgclnm, trgcldtyp, trgkyflg, trgkyseq, isrqrd
            FROM DMS_FLUPLDDTL
            WHERE flupldref = :1 AND curflg = 'Y'
            ORDER BY excseq
        """
        metadata_cursor.execute(query, [flupldref])
    
    columns = metadata_cursor.fetchall()
    metadata_cursor.close()
    
    # Build CREATE TABLE statement
    target_cursor = target_connection.cursor()
    target_db_type = _detect_db_type(target_connection)
    
    # Get data type mappings from target database's DMS_PARAMS
    if target_db_type == "POSTGRESQL":
        dms_params_ref = _get_table_ref(target_cursor, target_db_type, 'DMS_PARAMS')
        dtype_query = f"""
            SELECT PRCD, PRVAL 
            FROM {dms_params_ref} 
            WHERE PRTYP = 'Datatype'
        """
        target_cursor.execute(dtype_query)
    else:  # Oracle, MySQL, MS SQL Server, Sybase, etc.
        dtype_query = """
            SELECT PRCD, PRVAL 
            FROM DMS_PARAMS 
            WHERE PRTYP = 'Datatype'
        """
        target_cursor.execute(dtype_query)
    
    # Build dictionary of data type mappings
    dtype_map = {row[0]: row[1] for row in target_cursor.fetchall()}
    
    # Build column definitions
    col_defs = []
    primary_keys = []
    
    for col in columns:
        trgclnm, trgcldtyp, trgkyflg, trgkyseq, isrqrd = col
        
        # Get database-specific data type from parameter system
        db_specific_type = dtype_map.get(trgcldtyp, trgcldtyp)  # Fallback to generic if not found
        
        # Build column definition
        col_def = f"{trgclnm} {db_specific_type}"
        if isrqrd == 'Y':
            col_def += " NOT NULL"
        col_defs.append(col_def)
        
        # Track primary keys
        if trgkyflg == 'Y':
            primary_keys.append((trgkyseq or 0, trgclnm))
    
    # Build CREATE TABLE statement
    table_name = format_table_name(target_schema, target_table, target_db_type)
    create_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(col_defs)
    
    # Add primary key constraint if any
    if primary_keys:
        primary_keys.sort()  # Sort by sequence
        pk_columns = [col for _, col in primary_keys]
        create_sql += f",\n    PRIMARY KEY ({', '.join(pk_columns)})"
    
    create_sql += "\n)"
    
    # Execute CREATE TABLE
    target_cursor.execute(create_sql)
    target_connection.commit()
    target_cursor.close()
    
    return f"Table {table_name} created successfully"
```

### 12. Format-Specific Implementation Details

#### XML Parser Implementation
```python
# XML parsing with XPath support
import xml.etree.ElementTree as ET
from lxml import etree
import pandas as pd

class XMLParser(BaseFileParser):
    def detect_format(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.xml', '.xml.gz'))
    
    def parse(self, file_path: str, options: dict) -> pd.DataFrame:
        """
        Parse XML file with configurable XPath
        
        Options:
        - row_xpath: XPath to select row elements (e.g., '/root/item')
        - column_xpaths: Dict mapping column names to XPath expressions
        - attribute_mode: Extract from attributes vs elements
        - namespace: XML namespace mapping
        """
        # Use lxml for XPath support
        parser = etree.XMLParser(resolve_entities=False)  # Security: disable entities
        tree = etree.parse(file_path, parser)
        
        rows = []
        row_xpath = options.get('row_xpath', '//row')
        column_xpaths = options.get('column_xpaths', {})
        
        # Select row elements
        row_elements = tree.xpath(row_xpath, namespaces=options.get('namespace', {}))
        
        for row_elem in row_elements:
            row_data = {}
            for col_name, xpath_expr in column_xpaths.items():
                try:
                    value = row_elem.xpath(xpath_expr, namespaces=options.get('namespace', {}))
                    row_data[col_name] = value[0] if value else None
                except Exception as e:
                    row_data[col_name] = None
            rows.append(row_data)
        
        return pd.DataFrame(rows)
    
    def get_columns(self, file_path: str) -> List[str]:
        """Infer columns from XML structure"""
        # Sample first few rows to infer structure
        preview_df = self.preview(file_path, rows=5)
        return list(preview_df.columns)
```

#### Parquet Parser Implementation
```python
# Parquet parsing with schema inference
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd

class ParquetParser(BaseFileParser):
    def detect_format(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.parquet', '.parq'))
    
    def parse(self, file_path: str, options: dict) -> pd.DataFrame:
        """
        Parse Parquet file
        
        Options:
        - columns: List of columns to read (None = all)
        - use_pandas_metadata: Use pandas metadata if available
        - row_groups: Specific row groups to read
        """
        table = pq.read_table(
            file_path,
            columns=options.get('columns'),
            use_pandas_metadata=options.get('use_pandas_metadata', True),
            row_groups=options.get('row_groups')
        )
        return table.to_pandas()
    
    def get_schema(self, file_path: str) -> dict:
        """Get Parquet schema information"""
        parquet_file = pq.ParquetFile(file_path)
        schema = parquet_file.schema_arrow
        return {
            'columns': [field.name for field in schema],
            'types': {field.name: str(field.type) for field in schema},
            'num_rows': parquet_file.metadata.num_rows,
            'num_row_groups': parquet_file.num_row_groups
        }
    
    def get_columns(self, file_path: str) -> List[str]:
        """Get column names from Parquet metadata"""
        schema_info = self.get_schema(file_path)
        return schema_info['columns']
```

#### XML Configuration UI
For XML files, users need to configure:
- **Row XPath**: XPath expression to select row elements (e.g., `/root/customers/customer`)
- **Column Mappings**: XPath expressions for each column
  - Element: `./name` (text content of `<name>` element)
  - Attribute: `./@id` (value of `id` attribute)
  - Nested: `./address/city` (nested element)
- **Namespace Handling**: XML namespace declarations if needed

#### Parquet Configuration UI
For Parquet files:
- **Column Selection**: Show all available columns from Parquet schema
- **Type Preservation**: Display Parquet types (can be converted to DB types)
- **Row Group Selection**: (Advanced) Select specific row groups for large files
- **Schema Preview**: Show Parquet schema metadata

#### PDF Configuration UI
For PDF files:
- **Page Selection**: Select specific pages or page ranges (e.g., 1-5, 10, 15-20)
- **Table Extraction Mode**: 
  - Auto-detect tables (default)
  - Extract all text
  - Custom table settings
- **Table Settings**: Adjust table detection parameters (edge detection, etc.)
- **OCR Options**: Enable OCR for scanned PDFs (requires Tesseract)
- **Preview**: Show extracted tables/text before processing

#### Google Sheets Configuration UI
For Google Sheets:
- **Authentication**: 
  - Service Account (server-to-server, recommended)
  - OAuth2 (user authentication, for personal sheets)
- **Spreadsheet Selection**: 
  - Enter Google Sheets URL
  - Or enter Spreadsheet ID directly
- **Sheet/Tab Selection**: Dropdown to select specific sheet within spreadsheet
- **Range Selection**: 
  - Entire sheet (default)
  - Specific range (A1 notation, e.g., A1:Z100)
- **Header Row**: Toggle if first row contains headers
- **Real-time Sync**: Option to fetch latest data on each run

### 13. Future Enhancements

#### Phase 2 Features (Post-MVP)
- **File Monitoring**: Watch folder for new files
- **Data Validation Rules**: Custom validation rules per column
- **Data Transformation Pipeline**: Multi-step transformations
- **Incremental Load**: Only load new/changed records
- **Data Quality Checks**: Duplicate detection, data profiling
- **Notification**: Email/SMS on completion/failure
- **File History**: Track all uploaded files and versions
- **Rollback**: Ability to rollback a data load
- **Additional Formats**: Avro, ORC, Fixed Width, EDI formats
- **Compression Support**: Gzip, Bzip2, LZ4 for CSV/JSON
- **Multi-file Upload**: Upload and merge multiple files
- **XML Schema Validation**: Validate XML against XSD schema
- **Parquet Partitioning**: Support for partitioned Parquet files

## Implementation Checklist

### Backend
- [ ] Create database tables and sequences
- [ ] Create FastAPI router
- [ ] Implement file upload endpoint
- [ ] Implement file parsers (CSV, Excel, JSON, XML, Parquet, TSV)
- [ ] Implement base parser interface for extensibility
- [ ] Add XML XPath configuration UI
- [ ] Add Parquet schema detection
- [ ] Implement column auto-detection
- [ ] Implement CRUD operations
- [ ] **Integrate with parameter mapping system**:
  - [ ] Use `get_parameter_mapping_datatype()` for data type dropdown
  - [ ] Validate data types against `DMS_PARAMS` table
  - [ ] Resolve database-specific types from target database's `DMS_PARAMS`
  - [ ] Reuse data type validation logic from mapper module
- [ ] Implement data loading service
- [ ] Implement value derivation logic
- [ ] Implement scheduling integration
- [ ] Add error handling and logging
- [ ] Add unit tests

### Frontend
- [ ] Create module directory structure
- [ ] Create UploadTable component
- [ ] Create UploadForm component
- [ ] Create FileUploadDialog component
- [ ] Create ColumnMappingTable component
- [ ] Implement file upload UI
- [ ] Implement column mapping UI
- [ ] **Integrate with parameter mapping system**:
  - [ ] Fetch data types from `/mapper/get-parameter-mapping-datatype` endpoint
  - [ ] Populate data type dropdown with generic types (PRCD) and descriptions (PRDESC)
  - [ ] Store generic type code (PRCD) in column mapping
  - [ ] Show data type descriptions to users
- [ ] Implement value derivation editor
- [ ] Implement schedule dialog integration
- [ ] Add validation and error handling
- [ ] Add loading states and progress indicators
- [ ] Add unit tests

### Integration
- [ ] Integrate with DB connections module
- [ ] Integrate with jobs/scheduler module
- [ ] Add navigation menu item
- [ ] Add permissions/access control
- [ ] End-to-end testing

## Estimated Timeline
**Total: 7 weeks** (assuming 1 developer, full-time)

## Dependencies

### Backend Dependencies
- FastAPI backend (already in place)
- Database connection module (already in place)
- Jobs/scheduler module (already in place)
- Mapper module (for UI patterns reference)
- **Parameter mapping system** (already in place):
  - `DMS_PARAMS` table must exist in metadata database
  - `DMS_PARAMS` table should exist in target databases (for data type resolution)
  - Parameter entries with `PRTYP='Datatype'` must be configured
  - Each target database should have its own `DMS_PARAMS` with database-specific `PRVAL` values

### Python Libraries (to be added)
- **pandas** - Data manipulation (already in use)
- **openpyxl** - Excel file handling (already in use)
- **lxml** - XML parsing with XPath support (NEW)
- **pyarrow** - Parquet file reading/writing (NEW)
- **fastparquet** - Alternative Parquet library (optional, for compatibility)

### Database Drivers (as needed)
- **oracledb** - Oracle database (already in use)
- **psycopg2-binary** - PostgreSQL database (already in use)
- **pyodbc** - MS SQL Server and Sybase (already in use)
- **mysql-connector-python** - MySQL database (already in use)
- **snowflake-connector-python** - Snowflake (already in use)
- **ibm_db** - DB2 (already in use)
- **pyhive** - Hive (already in use)

**Note:** Database drivers are loaded dynamically based on target database type from `DMS_DBCONDTLS` connection configuration.

### Parameter System Requirements

#### DMS_PARAMS Configuration

The file upload module requires the `DMS_PARAMS` parameter system to be properly configured:

1. **Metadata Database**: 
   - `DMS_PARAMS` table must exist
   - Parameter entries with `PRTYP='Datatype'` must be configured
   - Used for UI dropdown population and validation

2. **Target Databases**:
   - `DMS_PARAMS` table should exist in each target database
   - Contains database-specific `PRVAL` values for each generic type (PRCD)
   - Used for resolving generic types to database-specific types during table creation

3. **Parameter Structure**:
   - `PRTYP`: 'Datatype' (for data type mappings)
   - `PRCD`: Generic data type code (e.g., 'VARCHAR', 'INTEGER', 'TIMESTAMP')
   - `PRDESC`: Human-readable description (e.g., 'Variable Character', 'Integer', 'Timestamp')
   - `PRVAL`: Database-specific data type value (e.g., 'VARCHAR2(255)' for Oracle, 'VARCHAR(255)' for PostgreSQL)

4. **Example Parameter Entries**:
   ```sql
   -- Oracle DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR2(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'NUMBER(10)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP(6)');
   
   -- PostgreSQL DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'INTEGER');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP');
   
   -- MySQL DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'INT');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP');
   ```

5. **Fallback Behavior**:
   - If `DMS_PARAMS` doesn't exist in target database, falls back to using generic type directly
   - If parameter entry not found, uses generic type code as-is
   - Logs warning when parameter resolution fails

### Parameter System Requirements

#### DMS_PARAMS Configuration

The file upload module requires the `DMS_PARAMS` parameter system to be properly configured:

1. **Metadata Database**: 
   - `DMS_PARAMS` table must exist
   - Parameter entries with `PRTYP='Datatype'` must be configured
   - Used for UI dropdown population and validation

2. **Target Databases**:
   - `DMS_PARAMS` table should exist in each target database
   - Contains database-specific `PRVAL` values for each generic type (PRCD)
   - Used for resolving generic types to database-specific types during table creation

3. **Parameter Structure**:
   - `PRTYP`: 'Datatype' (for data type mappings)
   - `PRCD`: Generic data type code (e.g., 'VARCHAR', 'INTEGER', 'TIMESTAMP')
   - `PRDESC`: Human-readable description (e.g., 'Variable Character', 'Integer', 'Timestamp')
   - `PRVAL`: Database-specific data type value (e.g., 'VARCHAR2(255)' for Oracle, 'VARCHAR(255)' for PostgreSQL)

4. **Example Parameter Entries**:
   ```sql
   -- Oracle DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR2(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'NUMBER(10)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP(6)');
   
   -- PostgreSQL DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'INTEGER');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP');
   
   -- MySQL DMS_PARAMS
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'VARCHAR', 'Variable Character', 'VARCHAR(255)');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'INTEGER', 'Integer', 'INT');
   INSERT INTO DMS_PARAMS (PRTYP, PRCD, PRDESC, PRVAL) VALUES ('Datatype', 'TIMESTAMP', 'Timestamp', 'TIMESTAMP');
   ```

5. **Fallback Behavior**:
   - If `DMS_PARAMS` doesn't exist in target database, falls back to using generic type directly
   - If parameter entry not found, uses generic type code as-is
   - Logs warning when parameter resolution fails

### Frontend Dependencies
- React/Next.js frontend (already in place)
- Material-UI components (already in use)
- Monaco Editor (for logic editing, already in use)

