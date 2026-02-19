# PostgreSQL Connection Support - Update Summary

## Changes Made

### 1. Updated `backend/database/dbconnect.py`
- Added `DB_TYPE` environment variable support (ORACLE or POSTGRESQL)
- Added `DB_NAME` for PostgreSQL (replaces DB_SID)
- Added `DB_CONNECTION_STRING` optional support
- Created `create_metadata_connection()` function that auto-detects database type
- Created `create_postgresql_connection()` function
- Updated `create_oracle_connection()` to support connection strings
- Updated internal functions to use `create_metadata_connection()`

### 2. Updated All Metadata Connection Calls
Changed all `create_oracle_connection()` calls to `create_metadata_connection()` in:
- `backend/modules/parameters/fastapi_parameter_mapping.py`
- `backend/modules/dashboard/dashboard.py`
- `backend/modules/jobs/jobs.py`
- `backend/modules/jobs/scheduler_service.py`
- `backend/modules/mapper/mapper.py`
- `backend/modules/manage_sql/manage_sql.py`
- `backend/modules/db_connections/crud_dbconnections.py`

### 3. Updated SQL Syntax for PostgreSQL
- `backend/modules/helper_functions.py`:
  - Updated `add_parameter_mapping()` to handle both Oracle (`:1, :2, sysdate`) and PostgreSQL (`%s, %s, CURRENT_TIMESTAMP`)
  - Added `_detect_db_type_from_connection()` helper function

### 4. Updated Requirements
- Added `psycopg2-binary` to `requirements.txt`

## Required .env Configuration

For PostgreSQL metadata database, add these to your `.env`:

```env
# Database Type
DB_TYPE=POSTGRESQL

# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: Use connection string instead
# DB_CONNECTION_STRING=postgresql://user:password@host:port/database

# Schema Configuration
DMS_SCHEMA=public
CDR_SCHEMA=cdr
```

## Installation

Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

## Known Issues / TODO

Some SQL queries may still use Oracle-specific syntax:
- Parameter binding: `:1, :2` (Oracle) vs `%s, %s` (PostgreSQL)
- Date functions: `sysdate` (Oracle) vs `CURRENT_TIMESTAMP` (PostgreSQL)
- Dual table: `SELECT 1 FROM dual` (Oracle) vs `SELECT 1` (PostgreSQL)

These will need to be updated as they are encountered. The `add_parameter_mapping()` function has been updated as an example.

## Testing

After updating your `.env` file with PostgreSQL settings, test the parameters screen to verify the connection works.

