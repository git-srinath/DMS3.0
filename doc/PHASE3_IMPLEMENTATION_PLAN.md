# Phase 3 Implementation Plan
**Module Integration with Database-Specific Datatypes**

**Status:** ⏳ In Progress  
**Start Date:** February 16, 2026  
**Estimated Duration:** 4 days (32 hours)  
**Integration Scope:** 4 modules (Jobs, File Upload, Mapper, Reports)

---

## Overview

Phase 3 integrates the datatype management system (from Phase 1 & 2A) into the core modules. Currently, these modules fetch datatypes without considering the target database type, treating all datatypes as generic. Phase 3 updates each module to filter and use database-specific datatypes.

### Current Problem

All modules currently execute this query:
```sql
SELECT PRCD, PRVAL FROM DMS_PARAMS 
WHERE PRTYP = 'Datatype'
```

This returns all datatypes regardless of target database type. When executing jobs/uploads against Oracle, PostgreSQL, Snowflake, etc., the wrong datatype definitions get used.

### Phase 3 Solution

Update all modules to execute database-aware queries:
```sql
SELECT PRCD, PRVAL FROM DMS_PARAMS 
WHERE PRTYP = 'Datatype' AND DBTYP = :target_database_type
```

---

## Integration Points by Module

### 1. Jobs Module (1-2 days)

**Files to Update:**
- `backend/modules/jobs/pkgdwjob_python.py` - Main job creation logic
- `backend/modules/jobs/pkgdwjob_create_job_flow.py` - Job flow code generation
- `backend/modules/jobs/execution_engine.py` - Job execution context

**Current Issues:**
- Line 201-220: `create_target_table()` fetches datatypes without DBTYP filter
  ```python
  JOIN {metadata_schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' AND p.prcd = jd.trgcldtyp
  ```
- Line 437+: `build_job_flow_code()` has same issue

**Changes Required:**
1. Extract target database type from job configuration
2. Pass database type to datatype lookup functions
3. Update SQL queries to include DBTYP filter
4. Test with multiple target databases

**Sample Changes:**
```python
# Before
query = f"""
    SELECT p.prval FROM {metadata_schema}.DMS_PARAMS p 
    WHERE p.prtyp = 'Datatype' AND p.prcd = jd.trgcldtyp
"""

# After
query = f"""
    SELECT p.prval FROM {metadata_schema}.DMS_PARAMS p 
    WHERE p.prtyp = 'Datatype' 
      AND p.prcd = jd.trgcldtyp 
      AND p.dbtyp = %s
"""
# Execute with target database type parameter
```

### 2. File Upload Module (1 day)

**Files to Update:**
- `backend/modules/file_upload/table_creator.py` - Table creation logic
- `backend/modules/file_upload/file_upload_service.py` - Upload service context

**Current Issues:**
- Line 280+: `_resolve_data_types()` doesn't filter by DBTYP
  ```sql
  WHERE PRTYP = 'Datatype'
  ```

**Changes Required:**
1. Determine target database type from upload configuration
2. Update `_resolve_data_types()` to accept dbtype parameter
3. Add DBTYP filter to SQL query
4. Update all callers of `_resolve_data_types()`

**Sample Changes:**
```python
# Before
def _resolve_data_types(connection, db_type: str, metadata_connection=None) -> Dict[str, str]:
    query = "SELECT UPPER(TRIM(PRCD)), PRVAL FROM DMS_PARAMS WHERE PRTYP = 'Datatype'"

# After
def _resolve_data_types(connection, db_type: str, target_dbtype: str, metadata_connection=None) -> Dict[str, str]:
    query = """
        SELECT UPPER(TRIM(PRCD)), PRVAL FROM DMS_PARAMS 
        WHERE PRTYP = 'Datatype' AND DBTYP = %s
    """
    # Execute with target_dbtype parameter
```

### 3. Mapper Module (0.5 days)

**Files to Update:**
- `backend/modules/mapper/fastapi_mapper.py` - Mapper API endpoints
- `backend/modules/mapper/mapper_transformation_utils.py` - Transformation logic

**Current Status:**
- Already has endpoint `/get-parameter-mapping-datatype`
- Should integrate Phase 2A endpoints for validation

**Changes Recommended:**
1. Create wrapper function using new Phase 2A endpoints
2. Add impact analysis before allowing datatype changes
3. Update database mapping display to show database type
4. Add validation for datatype compatibility

**Sample Changes:**
```python
# Add new endpoint using Phase 2A function
@router.get("/get-parameter-mapping-datatype/{dbtype}")
async def get_parameter_mapping_datatype_for_db(dbtype: str):
    """Get database-specific datatypes using Phase 2A function"""
    conn = create_metadata_connection()
    return get_parameter_mapping_datatype_for_db(conn, dbtype)
```

### 4. Reports Module (0.5 days)

**Files to Update:**
- `backend/modules/reports/report_service.py` - Report generation
- `backend/modules/reports/report_executor.py` - Report execution

**Current Status:**
- Minimal datatype usage  
- Needs to respect database-specific datatypes in output formatting

**Changes Recommended:**
1. Check if reports use datatypes
2. Update to use database-specific definitions
3. Ensure output formatting respects database types

---

## Implementation Strategy

### Phase 3A: Helper Function Enhancement (High Priority)

Create a new helper function that returns database-specific datatypes:

```python
def get_parameter_mapping_datatype_for_db_with_fallback(conn, target_dbtype):
    """
    Get datatypes for specific database, with fallback to GENERIC.
    Returns datatypes specific to target_dbtype, falling back to GENERIC
    if specific types not found.
    """
    try:
        # Try to get database-specific datatypes
        specific = get_parameter_mapping_datatype_for_db(conn, target_dbtype)
        if specific:
            return specific
    except:
        pass
    
    # Fallback to GENERIC if target types not found
    return get_parameter_mapping_datatype_for_db(conn, 'GENERIC')
```

This function is already implemented in helper_functions.py (Phase 1).

### Phase 3B: Jobs Module Update (Priority 1)

1. **Identify Database Type Context**
   - From j.trgconid (target connection ID)
   - Join with DMS_DBCONNECTION to get database type
   - Or get from job header/mapping configuration

2. **Update SQL Queries**
   - Jobs module has hardcoded joins to DMS_PARAMS
   - Need to pass DBTYP parameter to these queries

3. **Test with Multiple Databases**
   - Oracle target
   - PostgreSQL target
   - Snowflake target (if supported)

### Phase 3C: File Upload Module Update (Priority 2)

1. **Determine Target Database Type**
   - From upload configuration
   - From target connection in DMS_FLUPLDSCH

2. **Update Type Resolution**
   - Add dbtype parameter to `_resolve_data_types()`
   - Update all callers

3. **Backward Compatibility**
   - Ensure GENERIC fallback works
   - Support both old and new behavior

### Phase 3D: Mapper & Reports Updates (Priority 3)

**Mapper:**
- Already relatively database-aware
- Focus on integrating Phase 2A endpoints

**Reports:**
- Check current usage
- Update if necessary

---

## Detailed Changes by File

### File 1: backend/modules/jobs/pkgdwjob_python.py

**Location:** Line 201-230 (create_target_table function)

**Current Code:**
```python
query = f"""
    SELECT jd.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
           jd.trgclnm, jd.trgcldtyp, jd.trgkeyflg, jd.trgkeyseq,
           p.prval
    FROM {metadata_schema}.DMS_JOB j
    JOIN {metadata_schema}.DMS_JOBDTL jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
    JOIN {metadata_schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' AND p.prcd = jd.trgcldtyp
    WHERE j.mapref = %s
      AND j.curflg = 'Y'
    ORDER BY jd.excseq
"""
```

**Updated Code:**
```python
# First, get target database type from connection
query_dbtype = f"""
    SELECT DBTYP FROM {metadata_schema}.DMS_DBCONNECTION 
    WHERE CONID = (SELECT TRGCONID FROM {metadata_schema}.DMS_JOB 
                   WHERE MAPREF = %s)
"""
cursor.execute(query_dbtype, (p_mapref,))
dbtype_row = cursor.fetchone()
target_dbtype = dbtype_row[0] if dbtype_row else 'GENERIC'

# Then use database-specific datatypes
query = f"""
    SELECT jd.mapref, j.trgschm, j.trgtbtyp, j.trgtbnm,
           jd.trgclnm, jd.trgcldtyp, jd.trgkeyflg, jd.trgkeyseq,
           p.prval
    FROM {metadata_schema}.DMS_JOB j
    JOIN {metadata_schema}.DMS_JOBDTL jd ON jd.mapref = j.mapref AND jd.curflg = 'Y'
    JOIN {metadata_schema}.DMS_PARAMS p ON p.prtyp = 'Datatype' 
                                          AND p.prcd = jd.trgcldtyp
                                          AND (p.dbtyp = %s OR p.dbtyp = 'GENERIC')
    WHERE j.mapref = %s
      AND j.curflg = 'Y'
    ORDER BY jd.excseq, p.dbtyp DESC
```

### File 2: backend/modules/jobs/pkgdwjob_create_job_flow.py

**Location:** Line 430-450 (build_job_flow_code function)

Similar changes required - add DBTYP filter and get database type from job config.

### File 3: backend/modules/file_upload/table_creator.py

**Location:** Line 280-310 (_resolve_data_types function)

**Current Code:**
```python
def _resolve_data_types(connection, db_type: str, metadata_connection=None) -> Dict[str, str]:
    query = f"""
        SELECT UPPER(TRIM(PRCD)), PRVAL 
        FROM {dms_params_ref} 
        WHERE PRTYP = 'Datatype'
    """
```

**Updated Code:**
```python
def _resolve_data_types(connection, db_type: str, target_dbtype: str = 'GENERIC', metadata_connection=None) -> Dict[str, str]:
    query = f"""
        SELECT UPPER(TRIM(PRCD)), PRVAL 
        FROM {dms_params_ref} 
        WHERE PRTYP = 'Datatype'
          AND (DBTYP = %s OR DBTYP = 'GENERIC')
        ORDER BY DBTYP DESC
    """
    cursor.execute(query, (target_dbtype,))
```

---

## Testing Strategy

### Unit Tests
- [ ] Test jobs with Oracle target
- [ ] Test jobs with PostgreSQL target
- [ ] Test file uploads with different targets
- [ ] Test fallback to GENERIC when specific types not found

### Integration Tests
- [ ] End-to-end job creation and execution
- [ ] File upload with table creation
- [ ] Mapper validation with datatype changes
- [ ] Report generation

### Manual Testing
- [ ] Create job targeting Oracle, verify datatypes used
- [ ] Create job targeting PostgreSQL, verify different datatypes
- [ ] Upload file with column type mapping to different databases

---

## Rollback Plan

Each change:
1. Add new parameter (with default value for backward compatibility)
2. Keep old query logic alive initially
3. Toggle between old/new via feature flag or condition
4. After testing, remove old logic

---

## Success Criteria

✅ Phase 3 is complete when:
- [ ] Jobs module uses database-specific datatypes
- [ ] File upload module uses database-specific datatypes  
- [ ] Mapper module has validation endpoints integrated
- [ ] Reports module respects database-specific datatypes
- [ ] All modules tested with multiple database targets
- [ ] Backward compatibility maintained (GENERIC fallback)
- [ ] No regression in existing functionality
- [ ] Code documented and committed

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Phase 3A: Helper enhancements | 2 hours | ⏳ |
| Phase 3B: Jobs module | 8 hours | ⏳ |
| Phase 3C: File upload module | 6 hours | ⏳ |
| Phase 3D: Mapper & Reports | 4 hours | ⏳ |
| Testing & verification | 6 hours | ⏳ |
| Documentation & cleanup | 4 hours | ⏳ |
| **TOTAL** | **30 hours** | |

---

*Phase 3 Implementation Plan*  
*Prepared: February 16, 2026*  
*Ready to Start Implementation*
