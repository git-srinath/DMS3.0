# Two-Schema Architecture - DWT & CDR

## Overview
This document describes the two-schema architecture implemented for the DWTOOL application, separating metadata from actual data storage.

## Architecture Decision

### The Challenge
- Original implementation used a single `SCHEMA` variable
- Required creating synonyms from CDR schema to DWT objects
- Caused "table does not exist" errors when synonyms weren't created
- Mixed concerns: metadata and data in same context

### The Solution
**Two separate schemas with clear separation of concerns:**

1. **DWT Schema** - Metadata & Configuration
2. **CDR Schema** - Actual Business Data

## Schema Definitions

### DWT Schema (Data Warehouse Toolkit - Metadata)

**Purpose:** Stores all application metadata, configuration, and control information

**Tables:**
- `DMS_MAPR` - Mapping definitions
- `DMS_MAPRDTL` - Mapping detail definitions  
- `DMS_MAPRSQL` - SQL query definitions
- `DMS_MAPERR` - Validation error logs
- `DMS_PARAMS` - Application parameters
- `DMS_JOB` - Job definitions
- `DMS_JOBDTL` - Job detail definitions

**Sequences:**
- `DMS_MAPRSEQ` - Mapping IDs
- `DMS_MAPRDTLSEQ` - Mapping detail IDs
- `DMS_MAPRSQLSEQ` - SQL query IDs
- `DMS_MAPERRSEQ` - Error log IDs

**Used By:**
- Mapper module (`modules/mapper/`)
- Manage SQL module (`modules/manage_sql/`)
- Jobs module (`modules/jobs/`)
- Dashboard module (`modules/dashboard/`)
- Helper functions (`modules/helper_functions.py`)

### CDR Schema (Common Data Repository - Business Data)

**Purpose:** Stores actual business data tables created and populated by the mapper

**Tables:**
- Target tables defined in mappings (e.g., `DIM_CUSTOMER`, `FACT_SALES`)
- Created dynamically based on mapping configurations
- Populated by ETL/data loading processes

**Used By:**
- Data loading/ETL operations (future implementation)
- Query/reporting tools accessing business data

## Benefits of Two-Schema Architecture

### 1. **Clean Separation of Concerns**
```
DWT Schema (Metadata)          CDR Schema (Data)
├── Configuration              ├── Business tables
├── Mappings                   ├── Dimensions
├── Job definitions            ├── Facts
└── Application state          └── Staging tables
```

### 2. **No Synonym Management**
- **Before:** Required `CREATE SYNONYM` statements in CDR for all DWT objects
- **After:** Direct schema-qualified access (e.g., `DWT.DMS_MAPR`)
- **Result:** Eliminates "table does not exist" errors

### 3. **Easier Permission Management**
```sql
-- Clear, explicit grants
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPR TO app_user;
GRANT CREATE TABLE ON CDR TO app_user;
```

### 4. **Independent Evolution**
- Metadata schema changes don't affect data schema
- Data schema can be restructured without touching metadata
- Different backup/recovery strategies for each

### 5. **Multi-Tenant Possibilities**
- One DWT schema can manage multiple CDR schemas
- Useful for separating dev/test/prod data
- Or separating different business units

## Configuration

### Environment Variables

**In `.env` file (or environment):**
```bash
# DWT Schema - For metadata
DWT_SCHEMA=DWT

# CDR Schema - For data
CDR_SCHEMA=CDR
```

### Code Implementation

**All modules now support both schemas:**

```python
# modules/mapper/pkgdms_mapr.py (example)
DWT_SCHEMA = os.getenv("DWT_SCHEMA", "")
CDR_SCHEMA = os.getenv("CDR_SCHEMA", "")

DWT_SCHEMA_PREFIX = f"{DWT_SCHEMA}." if DWT_SCHEMA else ""
CDR_SCHEMA_PREFIX = f"{CDR_SCHEMA}." if CDR_SCHEMA else ""

# Usage in SQL:
cursor.execute(f"""
    SELECT * FROM {DWT_SCHEMA_PREFIX}DMS_MAPR 
    WHERE mapref = :mapref
""")
```

**Updated modules:**
- ✅ `modules/mapper/pkgdms_mapr.py`
- ✅ `modules/helper_functions.py`
- ✅ `modules/manage_sql/manage_sql.py`
- ✅ `modules/jobs/jobs.py`
- ✅ `modules/dashboard/dashboard.py`

### Backward Compatibility

The implementation maintains backward compatibility with the old `SCHEMA` variable:

```python
# If DWT_SCHEMA is not set, falls back to SCHEMA
if not DWT_SCHEMA and os.getenv("SCHEMA"):
    DWT_SCHEMA = os.getenv("SCHEMA")
```

This allows gradual migration without breaking existing deployments.

## Setup Instructions

### Step 1: Update Environment Configuration

**Copy the template:**
```bash
cp env.template .env
```

**Edit `.env` file:**
```bash
# Database connection
DB_HOST=your_host
DB_PORT=1521
DB_SERVICE=your_service
DB_USER=app_user
DB_PASSWORD=your_password

# Schema configuration
DWT_SCHEMA=DWT
CDR_SCHEMA=CDR
```

### Step 2: Grant Required Permissions

**As DBA or schema owner, run:**

```sql
-- ==================================================
-- DWT Schema Permissions (Metadata)
-- ==================================================

-- Table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPR TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPRDTL TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPRSQL TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.DMS_MAPERR TO app_user;
GRANT SELECT ON DWT.DMS_PARAMS TO app_user;
GRANT SELECT ON DWT.DMS_JOB TO app_user;
GRANT SELECT ON DWT.DMS_JOBDTL TO app_user;

-- Sequence permissions
GRANT SELECT ON DWT.DMS_MAPRSEQ TO app_user;
GRANT SELECT ON DWT.DMS_MAPRDTLSEQ TO app_user;
GRANT SELECT ON DWT.DMS_MAPRSQLSEQ TO app_user;
GRANT SELECT ON DWT.DMS_MAPERRSEQ TO app_user;

-- ==================================================
-- CDR Schema Permissions (Data)
-- ==================================================

-- For creating tables dynamically
GRANT CREATE TABLE TO app_user;
GRANT CREATE SEQUENCE TO app_user;

-- For data operations on CDR schema
GRANT SELECT, INSERT, UPDATE, DELETE ON CDR.* TO app_user;

-- Note: Specific table grants will depend on your data model
```

### Step 3: Verify Configuration

**Check that schemas are loaded:**

```python
import os
print(f"DWT_SCHEMA: {os.getenv('DWT_SCHEMA')}")
print(f"CDR_SCHEMA: {os.getenv('CDR_SCHEMA')}")
```

**Check application logs:**
```
PKGDMS_MAPR: DWT metadata schema prefix: 'DWT.'
PKGDMS_MAPR: CDR data schema prefix: 'CDR.' (for future data operations)
```

### Step 4: Test Operations

**Test metadata operations:**
```python
# Should work with DWT schema prefix
# Example: Creating a mapping
# SQL generated: INSERT INTO DWT.DMS_MAPR VALUES (DWT.DMS_MAPRSEQ.nextval, ...)
```

**Test data operations (future):**
```python
# Will use CDR schema prefix
# Example: Creating target table
# SQL generated: CREATE TABLE CDR.DIM_CUSTOMER (...)
```

## Migration Guide

### From Single Schema to Two-Schema

**Scenario: You're currently using `SCHEMA=DWT` and want to separate:**

#### Option 1: Keep Everything in DWT (Simple)
```bash
# .env file
DWT_SCHEMA=DWT
CDR_SCHEMA=DWT  # Same schema for both
```

No data migration needed. Both metadata and data stay in DWT schema.

#### Option 2: Separate to Two Schemas (Recommended)

**Step 1: Keep metadata in DWT, move data to CDR**

```bash
# .env file
DWT_SCHEMA=DWT  # Metadata stays here
CDR_SCHEMA=CDR  # Data will go here
```

**Step 2: Move existing data tables (if any)**

```sql
-- Export data tables from DWT
expdp user/pass DIRECTORY=dpdir DUMPFILE=data_tables.dmp SCHEMAS=DWT EXCLUDE=TABLE:"IN ('DMS_MAPR','DMS_MAPRDTL','DMS_MAPRSQL','DMS_MAPERR','DMS_PARAMS','DMS_JOB','DMS_JOBDTL')"

-- Import into CDR
impdp user/pass DIRECTORY=dpdir DUMPFILE=data_tables.dmp REMAP_SCHEMA=DWT:CDR
```

**Step 3: Update application references (future implementation)**

When implementing data loading, use `CDR_SCHEMA_PREFIX` for target tables.

### From Synonyms to Schema Prefixes

**If you were using synonyms:**

**Before:**
```sql
-- In CDR schema
CREATE SYNONYM DMS_MAPR FOR DWT.DMS_MAPR;
CREATE SYNONYM DMS_MAPRDTL FOR DWT.DMS_MAPRDTL;
-- etc...

-- Application used: SELECT * FROM DMS_MAPR
```

**After:**
```bash
# .env
DWT_SCHEMA=DWT
CDR_SCHEMA=CDR
```

```python
# Application now uses: SELECT * FROM DWT.DMS_MAPR
```

**Cleanup synonyms (optional):**
```sql
DROP SYNONYM DMS_MAPR;
DROP SYNONYM DMS_MAPRDTL;
-- etc...
```

## Usage Examples

### Example 1: Metadata Operations (Current)

**Creating a mapping:**
```python
# Uses DWT_SCHEMA_PREFIX
cursor.execute(f"""
    INSERT INTO {DWT_SCHEMA_PREFIX}DMS_MAPR 
    (mapid, mapref, mapdesc, ...)
    VALUES ({DWT_SCHEMA_PREFIX}DMS_MAPRSEQ.nextval, :mapref, :mapdesc, ...)
""")
# Generates: INSERT INTO DWT.DMS_MAPR VALUES (DWT.DMS_MAPRSEQ.nextval, ...)
```

### Example 2: Data Operations (Future Implementation)

**Creating a target table:**
```python
# Uses CDR_SCHEMA_PREFIX
cursor.execute(f"""
    CREATE TABLE {CDR_SCHEMA_PREFIX}DIM_CUSTOMER (
        customer_id NUMBER PRIMARY KEY,
        customer_name VARCHAR2(100),
        ...
    )
""")
# Generates: CREATE TABLE CDR.DIM_CUSTOMER (...)
```

**Loading data into target:**
```python
# Uses CDR_SCHEMA_PREFIX for target
cursor.execute(f"""
    INSERT INTO {CDR_SCHEMA_PREFIX}DIM_CUSTOMER
    SELECT customer_id, customer_name, ...
    FROM source_table
""")
# Generates: INSERT INTO CDR.DIM_CUSTOMER SELECT ...
```

## Deployment Scenarios

### Development Environment
```bash
# Single schema for simplicity
DWT_SCHEMA=DEV_SCHEMA
CDR_SCHEMA=DEV_SCHEMA
```

### Test Environment
```bash
# Separate schemas
DWT_SCHEMA=TEST_DWT
CDR_SCHEMA=TEST_CDR
```

### Production Environment
```bash
# Production schemas
DWT_SCHEMA=PROD_DWT
CDR_SCHEMA=PROD_CDR
```

### Multi-Tenant Production
```bash
# Shared metadata, separate data per client
DWT_SCHEMA=PROD_DWT
CDR_SCHEMA=CLIENT_A_CDR  # Or CLIENT_B_CDR, etc.
```

## Troubleshooting

### Error: ORA-00942 table or view does not exist

**Check:**
1. Environment variables are set correctly
2. Application has been restarted after .env changes
3. User has permissions on the schema
4. Schema prefix is being applied in logs

**Verify:**
```python
# Check what's being generated
print(f"DWT_SCHEMA_PREFIX: '{DWT_SCHEMA_PREFIX}'")
# Should see: DWT_SCHEMA_PREFIX: 'DWT.'
```

### Error: Still seeing old SCHEMA variable behavior

**Solution:** Restart the application to reload environment variables

### Error: Cannot access CDR schema

**Check CDR permissions:**
```sql
SELECT * FROM user_tab_privs WHERE table_schema = 'CDR';
SELECT * FROM user_sys_privs WHERE privilege LIKE '%CREATE%';
```

## Future Enhancements

### Data Loading Operations
When implementing ETL/data loading:

```python
from modules.mapper.pkgdms_mapr import CDR_SCHEMA_PREFIX

# Get mapping from DWT schema
mapping = get_mapping(mapping_ref)  # From DWT.DMS_MAPR

# Create/load target table in CDR schema
target_table = f"{CDR_SCHEMA_PREFIX}{mapping['target_table']}"
cursor.execute(f"""
    INSERT INTO {target_table}
    SELECT {mapping['column_list']}
    FROM {mapping['source']}
""")
```

### Schema-Specific Monitoring
```python
# Monitor DWT schema size (metadata)
# Monitor CDR schema size (data)
# Different alerting thresholds
```

### Backup Strategies
```bash
# More frequent backups of metadata (DWT)
expdp ... SCHEMAS=DWT

# Different backup schedule for data (CDR)
expdp ... SCHEMAS=CDR
```

## Related Documentation
- `env.template` - Environment configuration template
- `TABLE_SCHEMA_PREFIX_FIX.md` - Schema prefix implementation details
- `SESSION_FIXES_SUMMARY.md` - All bug fixes applied

## Credits
Architecture suggested by user based on operational requirements:
- Eliminate synonym management overhead
- Clear separation between metadata and data
- Reduce "table does not exist" errors

## Date
November 12, 2025

## Version
1.0 - Initial two-schema architecture implementation

