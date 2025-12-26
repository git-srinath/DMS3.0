# File Upload Execution Engine & Scheduling - Implementation Plan

## Overview
This document outlines the implementation plan for the File Upload execution engine and scheduling functionality, building on the existing file upload configuration module.

## Current State Analysis

### ✅ Completed
1. **Database Schema**: `DMS_FLUPLD` and `DMS_FLUPLDDTL` tables created
2. **Configuration UI**: File upload configuration screen with column mapping
3. **Column Mapping**: Source to target column mapping with data types
4. **Formula Support**: Derivation logic (`drvlgc`) and flag (`drvlgcflg`) fields
5. **Data Type Integration**: Uses `DMS_PARAMS` parameter system
6. **File Parsing**: File upload and preview functionality
7. **CRUD Operations**: Create, read, update, delete file upload configurations

### ❌ Missing (To Be Implemented)
1. **Execution Engine**: Actual data loading to target database
2. **Table Creation**: Auto-create target tables based on column mappings
3. **Formula Evaluation**: Execute Python formulas during data transformation
4. **Scheduling Integration**: Schedule file uploads similar to reports
5. **Job Tracking**: Track execution status, logs, and errors
6. **File Processing**: Process uploaded files and load data

---

## 1. Execution Engine Requirements

### 1.1 Core Functionality
The execution engine needs to:
1. **Read Configuration**: Load file upload configuration from `DMS_FLUPLD` and `DMS_FLUPLDDTL`
2. **Read File**: Parse the uploaded file (CSV, Excel, JSON, XML, Parquet, etc.)
3. **Transform Data**: 
   - Map source columns to target columns
   - Apply formulas (Python expressions) where `drvlgcflg = 'Y'`
   - Apply default values where specified
   - Handle audit columns (CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY)
4. **Create/Verify Table**: Ensure target table exists with correct schema
5. **Load Data**: Insert/upsert data into target database
6. **Track Execution**: Log execution status, errors, and statistics

### 1.2 Execution Flow

```
1. User triggers execution (manual or scheduled)
   ↓
2. Execution Engine loads configuration:
   - DMS_FLUPLD (main config: flupldref, trgconid, trgschm, trgtblnm, trnctflg, etc.)
   - DMS_FLUPLDDTL (column mappings: srcclnm, trgclnm, trgcldtyp, drvlgc, etc.)
   ↓
3. Get target database connection (using trgconid)
   ↓
4. Read and parse file (using flpth or file from request)
   ↓
5. Transform data:
   - Map columns (srcclnm → trgclnm)
   - Apply formulas (evaluate drvlgc using Python AST)
   - Apply defaults (dfltval)
   - Add audit columns
   ↓
6. Create/verify target table:
   - Check if table exists
   - If not, create table with schema from column mappings
   - Resolve data types from DMS_PARAMS (target database)
   ↓
7. Load data:
   - If trnctflg = 'Y': TRUNCATE TABLE
   - Insert/upsert data (batch processing)
   ↓
8. Update execution status:
   - Update DMS_FLUPLD.lstrundt
   - Log to DMS_JOBLOG (if job tracking enabled)
   - Update DMS_FLUPLD.nxtrundt (if scheduled)
```

### 1.3 Formula Evaluation
Similar to reports module's `FormulaEvaluator`:
- Use Python AST parsing for safe evaluation
- Support column references (e.g., `COL1`, `COL2`)
- Support Python functions (string, math, date operations)
- Handle errors gracefully (log and continue with default/null)

### 1.4 Table Creation Logic
1. Query `DMS_FLUPLDDTL` for column mappings (where `curflg = 'Y'`)
2. For each column:
   - Get generic data type (`trgcldtyp`) from `DMS_FLUPLDDTL`
   - Query target database's `DMS_PARAMS` to get database-specific type (`PRVAL`)
   - Build column definition: `COLUMN_NAME DATA_TYPE [NOT NULL]`
3. Build primary key constraint from columns where `trgkyflg = 'Y'`
4. Execute `CREATE TABLE` with database-specific syntax

### 1.5 Data Loading Strategies
- **Insert Only**: Simple INSERT statements
- **Truncate and Load**: TRUNCATE TABLE, then INSERT
- **Upsert** (Future): MERGE/ON CONFLICT based on primary key

---

## 2. Scheduling Integration

### 2.1 Database Schema Changes

#### Option A: Reuse DMS_JOBSCH (Recommended)
Reuse existing `DMS_JOBSCH` table with a new job type for file uploads.

**Required Changes:**
1. Add `JOB_TYPE` column to `DMS_JOBSCH` (or use existing `MAPREF` pattern)
2. Store `flupldref` in a reference field (could use `MAPREF` or add `FLUPLDREF`)
3. Add file upload-specific fields if needed

**Migration SQL:**
```sql
-- PostgreSQL
ALTER TABLE dms_jobsch ADD COLUMN IF NOT EXISTS flupldref VARCHAR(100);
ALTER TABLE dms_jobsch ADD COLUMN IF NOT EXISTS job_type VARCHAR(20) DEFAULT 'ETL';

-- Oracle
ALTER TABLE DMS_JOBSCH ADD (FLUPLDREF VARCHAR2(100));
ALTER TABLE DMS_JOBSCH ADD (JOB_TYPE VARCHAR2(20) DEFAULT 'ETL');
```

#### Option B: Create DMS_FLUPLD_SCHD Table (Alternative)
Create a dedicated scheduling table for file uploads.

**New Table:**
```sql
-- PostgreSQL
CREATE TABLE dms_flupld_schd (
    schdid SERIAL PRIMARY KEY,
    flupldref VARCHAR(100) NOT NULL,
    frqcd VARCHAR(10),  -- Frequency code (DL, WK, MN, etc.)
    frqdd VARCHAR(10),  -- Frequency day
    frqhh INTEGER,     -- Frequency hour
    frqmi INTEGER,     -- Frequency minute
    stflg CHAR(1) DEFAULT 'N',  -- Status flag (A=Active, N=Inactive)
    strtdt TIMESTAMP,  -- Start date
    enddt TIMESTAMP,   -- End date
    lstrundt TIMESTAMP,  -- Last run date
    nxtrundt TIMESTAMP,  -- Next run date
    curflg CHAR(1) DEFAULT 'Y',
    crtdby VARCHAR(100),
    crtdt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptdby VARCHAR(100),
    uptdt TIMESTAMP,
    FOREIGN KEY (flupldref) REFERENCES dms_flupld(flupldref)
);

-- Oracle
CREATE TABLE DMS_FLUPLD_SCHD (
    SCHDID NUMBER PRIMARY KEY,
    FLUPLDREF VARCHAR2(100) NOT NULL,
    FRQCD VARCHAR2(10),
    FRQDD VARCHAR2(10),
    FRQHH NUMBER,
    FRQMI NUMBER,
    STFLG CHAR(1) DEFAULT 'N',
    STRDT TIMESTAMP(6),
    ENDDT TIMESTAMP(6),
    LSTRUNDT TIMESTAMP(6),
    NXTRUNDT TIMESTAMP(6),
    CURFLG CHAR(1) DEFAULT 'Y',
    CRTDBY VARCHAR2(100),
    CRTDATE TIMESTAMP(6) DEFAULT SYSTIMESTAMP,
    UPTDBY VARCHAR2(100),
    UPTDATE TIMESTAMP(6),
    FOREIGN KEY (FLUPLDREF) REFERENCES DMS_FLUPLD(FLUPLDREF)
);

CREATE SEQUENCE DMS_FLUPLD_SCHD_SEQ;
```

**Recommendation**: Use **Option A** (reuse `DMS_JOBSCH`) for consistency with existing scheduling infrastructure.

### 2.2 Scheduler Service Integration

The scheduler service (`backend/modules/jobs/scheduler_service.py`) already supports:
- Multiple job types (ETL, REPORT, etc.)
- Frequency codes (DL, WK, MN, etc.)
- Next run calculation
- Schedule synchronization

**Required Changes:**
1. Add file upload job type to scheduler
2. Add file upload schedule sync method (similar to `_sync_report_schedules()`)
3. Queue file upload execution requests to `DMS_PRCREQ`

### 2.3 Execution Engine Integration

The execution engine (`backend/modules/jobs/execution_engine.py`) needs:
1. New request type: `JobRequestType.FILE_UPLOAD`
2. Handler method: `_execute_file_upload_job(request)`
3. Integration with file upload service

---

## 3. Implementation Steps

### Phase 1: Execution Engine Core (Week 1)

#### Backend
1. **Create File Upload Execution Service**
   - File: `backend/modules/file_upload/file_upload_executor.py`
   - Methods:
     - `execute_file_upload(flupldref, file_path=None)`
     - `_load_configuration(flupldref)`
     - `_parse_file(file_path, file_type)`
     - `_transform_data(dataframe, column_mappings)`
     - `_evaluate_formulas(dataframe, formulas)`
     - `_create_target_table(connection, schema, table, column_mappings)`
     - `_load_data(connection, schema, table, dataframe, truncate_flag)`

2. **Formula Evaluator Integration**
   - Reuse or extend `FormulaEvaluator` from reports module
   - File: `backend/modules/file_upload/formula_evaluator.py`
   - Support column references and Python expressions

3. **Table Creation Service**
   - File: `backend/modules/file_upload/table_creator.py`
   - Methods:
     - `create_table_if_not_exists(connection, schema, table, column_mappings)`
     - `_resolve_data_types(connection, column_mappings)`
     - `_build_create_table_sql(db_type, schema, table, columns, primary_keys)`

4. **Data Loader Service**
   - File: `backend/modules/file_upload/data_loader.py`
   - Methods:
     - `load_data(connection, schema, table, dataframe, truncate_flag)`
     - `_batch_insert(connection, table, dataframe, batch_size)`
     - `_truncate_table(connection, schema, table)`

5. **API Endpoint**
   - File: `backend/modules/file_upload/fastapi_file_upload.py`
   - Endpoint: `POST /file-upload/execute`
   - Parameters: `flupldref`, optional `file_path` (for re-running with new file)

#### Frontend
1. **Execute Button**
   - Add "Execute" button to `UploadTable.js` actions
   - Add execution dialog with options (file selection, etc.)

2. **Execution Status**
   - Show execution status in table (last run date, next run date)
   - Add execution logs viewer

### Phase 2: Scheduling Integration (Week 2)

#### Database Changes
1. **Update DMS_JOBSCH Schema**
   - Add `flupldref` column (or use `MAPREF` pattern)
   - Add `job_type` column if not exists

2. **Migration Script**
   - File: `doc/database_migration_file_upload_scheduling.sql`

#### Backend
1. **Scheduler Service Updates**
   - File: `backend/modules/jobs/scheduler_service.py`
   - Add `_sync_file_upload_schedules()` method
   - Register file upload schedules in scheduler

2. **Execution Engine Updates**
   - File: `backend/modules/jobs/execution_engine.py`
   - Add `JobRequestType.FILE_UPLOAD`
   - Add `_execute_file_upload_job(request)` method

3. **Schedule Service**
   - File: `backend/modules/file_upload/file_upload_schedule_service.py`
   - Methods:
     - `create_schedule(flupldref, schedule_config)`
     - `update_schedule(schedule_id, schedule_config)`
     - `delete_schedule(schedule_id)`
     - `get_schedule(flupldref)`

4. **API Endpoints**
   - File: `backend/modules/file_upload/fastapi_file_upload.py`
   - Endpoints:
     - `POST /file-upload/schedules`
     - `GET /file-upload/schedules/{flupldref}`
     - `PUT /file-upload/schedules/{schedule_id}`
     - `DELETE /file-upload/schedules/{schedule_id}`

#### Frontend
1. **Schedule Dialog**
   - Reuse or adapt `ScheduleConfiguration.js` from jobs module
   - File: `frontend/src/app/file_upload_module/ScheduleDialog.js`
   - Options:
     - Frequency (Daily, Weekly, Monthly, etc.)
     - Day of week/day of month
     - Time (hour, minute)
     - Status (Active/Inactive)

2. **Schedule Actions**
   - Add "Schedule" button to `UploadTable.js` actions
   - Show schedule status in table (next run, last run)
   - Add schedule management UI

### Phase 3: Job Tracking & Logging (Week 3)

#### Backend
1. **Job Logging**
   - Integrate with `DMS_JOBLOG` for execution logs
   - Track: start time, end time, rows processed, errors

2. **Error Handling**
   - Log errors to `DMS_JOBERR` (if exists) or `DMS_JOBLOG`
   - Continue processing on non-fatal errors
   - Rollback on fatal errors

3. **Status Updates**
   - Update `DMS_FLUPLD.lstrundt` after execution
   - Update `DMS_FLUPLD.nxtrundt` for scheduled uploads

#### Frontend
1. **Execution History**
   - Show execution history in detail view
   - Display logs and errors

2. **Status Indicators**
   - Show execution status (Success, Failed, Running)
   - Show last run and next run dates

---

## 4. Database Changes Summary

### Required Changes

#### Option A: Reuse DMS_JOBSCH (Recommended)
```sql
-- PostgreSQL
ALTER TABLE dms_jobsch ADD COLUMN IF NOT EXISTS flupldref VARCHAR(100);
ALTER TABLE dms_jobsch ADD COLUMN IF NOT EXISTS job_type VARCHAR(20) DEFAULT 'ETL';

-- Oracle
ALTER TABLE DMS_JOBSCH ADD (FLUPLDREF VARCHAR2(100));
ALTER TABLE DMS_JOBSCH ADD (JOB_TYPE VARCHAR2(20) DEFAULT 'ETL');
```

#### Option B: New Table (Alternative)
See section 2.1 for `DMS_FLUPLD_SCHD` table definition.

### No Changes Needed (Already Exist)
- `DMS_FLUPLD` table (has `lstrundt`, `nxtrundt` columns)
- `DMS_FLUPLDDTL` table
- `DMS_JOBSCH` table (if reusing)
- `DMS_JOBLOG` table (for execution logs)
- `DMS_PRCREQ` table (for queuing requests)

---

## 5. API Endpoints Summary

### Execution
- `POST /file-upload/execute` - Execute file upload immediately
- `GET /file-upload/execution-status/{flupldref}` - Get execution status

### Scheduling
- `POST /file-upload/schedules` - Create schedule
- `GET /file-upload/schedules/{flupldref}` - Get schedule for upload
- `PUT /file-upload/schedules/{schedule_id}` - Update schedule
- `DELETE /file-upload/schedules/{schedule_id}` - Delete schedule
- `GET /file-upload/schedules` - List all schedules

---

## 6. Integration Points

### With Existing Modules
1. **Jobs Module**: Reuse scheduler service and execution engine
2. **Reports Module**: Reuse formula evaluator pattern
3. **DB Connections Module**: Use existing connection management
4. **Parameter System**: Use `DMS_PARAMS` for data type resolution

### Dependencies
- Python libraries: pandas, openpyxl, lxml, pyarrow (already in use)
- Database drivers: oracledb, psycopg2, pyodbc (already in use)
- Scheduler: APScheduler (already in use)

---

## 7. Testing Plan

### Unit Tests
- Formula evaluation
- Table creation SQL generation
- Data transformation logic
- File parsing

### Integration Tests
- End-to-end execution flow
- Scheduling integration
- Multi-database support (PostgreSQL, Oracle)

### User Acceptance Tests
- Manual execution
- Scheduled execution
- Error handling
- Large file processing

---

## 8. Next Steps

1. **Review and Approve Plan**: Confirm database changes approach (Option A vs B)
2. **Create Database Migration**: Prepare migration script
3. **Implement Execution Engine**: Start with Phase 1
4. **Add Scheduling**: Implement Phase 2
5. **Add Logging**: Implement Phase 3
6. **Testing**: Comprehensive testing across all phases
7. **Documentation**: Update user guide and API documentation

---

## Questions for User

1. **Database Changes**: Do you prefer Option A (reuse `DMS_JOBSCH`) or Option B (new table)?
2. **File Storage**: Should we store files in database (BLOB) or filesystem (path only)?
3. **Upsert Support**: Do you need upsert functionality (update if exists, insert if not)?
4. **Error Handling**: Should execution continue on non-fatal errors or stop immediately?
5. **Batch Size**: What batch size should we use for data loading? (default: 1000 rows)

