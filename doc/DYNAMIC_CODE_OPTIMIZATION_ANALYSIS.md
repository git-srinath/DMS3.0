# Dynamic Code Block Optimization Analysis

## Executive Summary

The current dynamic code block stored in `DMS_JOBFLW.DWLOGIC` contains **~1500-2000 lines** of code per job. This analysis identifies what can be extracted to external modules to reduce the database-stored code to **~100-200 lines** (90% reduction).

---

## Current Dynamic Code Structure

### What's Currently in the Dynamic Block

1. **Imports and Constants** (~50 lines)
   - Standard library imports
   - Database-specific constants
   - Job-specific constants (MAPREF, JOBID, TARGET_SCHEMA, etc.)

2. **Helper Functions** (~200 lines)
   - `map_row_to_target_columns()` - Column mapping logic
   - `generate_hash()` - Hash generation for change detection
   - `log_batch_progress()` - Progress logging
   - `check_stop_request()` - Stop request checking

3. **Main execute_job Function** (~1200 lines)
   - Connection validation
   - Cursor creation
   - Checkpoint handling logic
   - Source query execution with checkpoint
   - Batch processing loop
   - Row transformation
   - Primary key lookup
   - Hash comparison
   - SCD Type 1/2 handling
   - Bulk insert/update operations
   - Error handling
   - Progress tracking
   - Checkpoint updates

4. **Job-Specific Logic** (~100-500 lines per combination)
   - Source SQL queries (job-specific)
   - Column mappings (job-specific)
   - Transformation logic (job-specific)
   - Target table structure (job-specific)

---

## Extraction Strategy

### ✅ Can Be Extracted (Common Code)

#### 1. **Job Execution Framework** → `mapper_job_executor.py`
**Size Reduction: ~800 lines**

Extract to external module:
- Connection validation
- Cursor creation and management
- Checkpoint handling (all strategies)
- Stop request checking
- Progress logging
- Error handling framework
- Batch processing orchestration

**New Module:** `backend/modules/mapper/mapper_job_executor.py`

**Function Signature:**
```python
def execute_mapper_job(
    metadata_conn,
    source_conn,
    target_conn,
    job_config: Dict[str, Any],
    source_sql: str,
    transformation_func: Callable,
    checkpoint_config: Dict[str, Any],
    session_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute mapper job with all common logic handled internally.
    
    Args:
        job_config: Job-specific configuration (mapref, jobid, target schema/table, etc.)
        source_sql: Source SQL query
        transformation_func: Function to transform source rows to target format
        checkpoint_config: Checkpoint strategy and configuration
        session_params: Session parameters from DMS_PRCLOG
    
    Returns:
        Execution result dictionary
    """
```

#### 2. **Row Transformation Utilities** → `mapper_transformation_utils.py`
**Size Reduction: ~150 lines**

Extract to external module:
- `map_row_to_target_columns()` - Column name mapping
- `generate_hash()` - Hash generation
- Column normalization utilities

**New Module:** `backend/modules/mapper/mapper_transformation_utils.py`

**Functions:**
```python
def map_row_to_target_columns(
    row_dict: Dict[str, Any],
    column_mapping: Dict[str, str],
    all_target_columns: List[str]
) -> Dict[str, Any]:
    """Map source row to target column structure"""

def generate_hash(
    row_dict: Dict[str, Any],
    column_order: List[str],
    exclude_columns: Set[str] = None
) -> str:
    """Generate MD5 hash for change detection"""
```

#### 3. **Checkpoint Management** → `mapper_checkpoint_handler.py`
**Size Reduction: ~200 lines**

Extract to external module:
- Checkpoint value parsing
- Checkpoint query building (KEY strategy)
- Checkpoint updates
- Checkpoint completion

**New Module:** `backend/modules/mapper/mapper_checkpoint_handler.py`

**Functions:**
```python
def apply_checkpoint_to_query(
    base_query: str,
    checkpoint_config: Dict[str, Any],
    checkpoint_value: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """Apply checkpoint to source query, returns modified query and bind params"""

def update_checkpoint(
    metadata_conn,
    session_params: Dict[str, Any],
    checkpoint_value: str
) -> None:
    """Update checkpoint in DMS_PRCLOG"""

def complete_checkpoint(
    metadata_conn,
    session_params: Dict[str, Any]
) -> None:
    """Mark checkpoint as completed"""
```

#### 4. **SCD Handling** → `mapper_scd_handler.py`
**Size Reduction: ~300 lines**

Extract to external module:
- SCD Type 1 update logic
- SCD Type 2 insert/expire logic
- Hash comparison
- Primary key lookup

**New Module:** `backend/modules/mapper/mapper_scd_handler.py`

**Functions:**
```python
def process_scd_batch(
    target_conn,
    target_schema: str,
    target_table: str,
    rows_to_insert: List[Dict],
    rows_to_update_scd1: List[Dict],
    rows_to_update_scd2: List[Dict],
    scd_type: int,
    target_type: str
) -> Tuple[int, int, int]:
    """Process SCD batch operations, returns (inserted, updated, expired)"""
```

#### 5. **Progress and Logging** → `mapper_progress_tracker.py`
**Size Reduction: ~100 lines**

Extract to external module:
- Batch progress logging
- Stop request checking
- Progress updates

**New Module:** `backend/modules/mapper/mapper_progress_tracker.py`

**Functions:**
```python
def log_batch_progress(
    metadata_conn,
    mapref: str,
    jobid: int,
    batch_num: int,
    source_rows: int,
    target_rows: int,
    error_rows: int,
    session_params: Dict[str, Any]
) -> None:
    """Log batch progress to DMS_JOBLOG"""

def check_stop_request(
    metadata_conn,
    mapref: str
) -> bool:
    """Check if stop request exists for job"""
```

---

### ❌ Must Stay in Dynamic Block (Job-Specific)

#### 1. **Job Configuration Constants** (~30 lines)
- MAPREF, JOBID, TARGET_SCHEMA, TARGET_TABLE
- BLOCK_PROCESS_ROWS, BULK_LIMIT
- CHECKPOINT_ENABLED, CHECKPOINT_STRATEGY, CHECKPOINT_COLUMNS
- PK_COLUMNS, PK_SOURCE_MAPPING
- ALL_COLUMNS, COLUMN_SOURCE_MAPPING
- TARGET_TYPE, CURRENT_SCD_TYPE

**Reason:** Job-specific, varies per job

#### 2. **Source SQL Queries** (~10-50 lines per combination)
- Actual SQL queries from DMS_MAPRSQL or MAPLOGIC
- Job-specific query logic

**Reason:** Unique per job/mapping

#### 3. **Transformation Function** (~50-200 lines per combination)
- Row-by-row transformation logic
- Column mapping application
- Business logic specific to the mapping

**Reason:** Unique per mapping

#### 4. **Main Execution Call** (~20-50 lines)
- Call to `execute_mapper_job()` with job-specific parameters
- Result handling
- Return statement

**Reason:** Orchestrates job-specific components

---

## Proposed Dynamic Block Structure

### Minimal Dynamic Block (~100-200 lines)

```python
# ===== JOB CONFIGURATION =====
MAPREF = "{mapref}"
JOBID = {jobid}
TARGET_SCHEMA = "{trgschm}"
TARGET_TABLE = "{trgtbnm}"
TARGET_TYPE = "{trgtbtyp}"
FULL_TABLE_NAME = "{tbnam}"

# Checkpoint configuration
CHECKPOINT_ENABLED = {chkpntenbld == 'Y'}
CHECKPOINT_STRATEGY = "{chkpntstrtgy}"
CHECKPOINT_COLUMNS = {checkpoint_columns}
CHECKPOINT_COLUMN = "{chkpntclnm}"

# Processing configuration
BLOCK_PROCESS_ROWS = {blkprcrows}
BULK_LIMIT = {w_limit}

# Column mappings (job-specific)
PK_COLUMNS = {pk_columns}
PK_SOURCE_MAPPING = {pk_source_mapping}
ALL_COLUMNS = {all_columns}
COLUMN_SOURCE_MAPPING = {column_source_mapping}

# ===== IMPORTS =====
from backend.modules.mapper.mapper_job_executor import execute_mapper_job
from backend.modules.mapper.mapper_transformation_utils import (
    map_row_to_target_columns,
    generate_hash
)

# ===== TRANSFORMATION FUNCTION (Job-Specific) =====
def transform_row(source_row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform source row to target format.
    This is job-specific logic.
    """
    # Map columns
    normalized = map_row_to_target_columns(
        source_row_dict,
        COLUMN_SOURCE_MAPPING,
        ALL_COLUMNS
    )
    
    # Apply job-specific transformations
    # ... job-specific logic here ...
    
    return normalized

# ===== MAIN EXECUTION =====
def execute_job(metadata_connection, source_connection, target_connection, session_params):
    """
    Execute ETL job for {mapref}.
    """
    # Job configuration
    job_config = {{
        'mapref': MAPREF,
        'jobid': JOBID,
        'target_schema': TARGET_SCHEMA,
        'target_table': TARGET_TABLE,
        'target_type': TARGET_TYPE,
        'full_table_name': FULL_TABLE_NAME,
        'pk_columns': PK_COLUMNS,
        'pk_source_mapping': PK_SOURCE_MAPPING,
        'all_columns': ALL_COLUMNS,
        'column_source_mapping': COLUMN_SOURCE_MAPPING,
        'block_process_rows': BLOCK_PROCESS_ROWS,
        'bulk_limit': BULK_LIMIT
    }}
    
    # Checkpoint configuration
    checkpoint_config = {{
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN
    }}
    
    # Source SQL (job-specific)
    source_sql = """{source_sql}"""
    
    # Execute using framework
    result = execute_mapper_job(
        metadata_conn=metadata_connection,
        source_conn=source_connection,
        target_conn=target_connection,
        job_config=job_config,
        source_sql=source_sql,
        transformation_func=transform_row,
        checkpoint_config=checkpoint_config,
        session_params=session_params
    )
    
    return result
```

---

## Size Reduction Estimates

### Current Size
- **Per Job:** ~1500-2000 lines
- **With 10 combinations:** ~2000-3000 lines
- **Database Storage:** ~50-100 KB per job

### After Optimization
- **Per Job:** ~100-200 lines
- **With 10 combinations:** ~200-400 lines
- **Database Storage:** ~5-10 KB per job

### Reduction
- **90% reduction** in database-stored code
- **Easier maintenance** - common code in one place
- **Better testability** - external modules can be unit tested
- **Version control** - external code in git, not database

---

## Implementation Plan

### Phase 1: Create External Modules (No Dynamic Block Changes)
1. Create `mapper_job_executor.py` with execution framework
2. Create `mapper_transformation_utils.py` with utilities
3. Create `mapper_checkpoint_handler.py` with checkpoint logic
4. Create `mapper_scd_handler.py` with SCD logic
5. Create `mapper_progress_tracker.py` with progress tracking
6. Unit test all modules

### Phase 2: Update Code Generation
1. Modify `pkgdwjob_create_job_flow.py` to generate minimal code
2. Generate imports to external modules
3. Generate job-specific configuration
4. Generate transformation function skeleton
5. Generate call to `execute_mapper_job()`

### Phase 3: Integration Testing
1. Test with existing jobs
2. Verify backward compatibility
3. Performance testing
4. Error handling validation

### Phase 4: Parallel Processing Integration
1. Add parallel processing support to `mapper_job_executor.py`
2. Update code generation to support parallel processing
3. Test parallel execution

---

## Benefits

### 1. **Reduced Database Storage**
- 90% reduction in CLOB size
- Faster code retrieval
- Lower database storage costs

### 2. **Improved Maintainability**
- Common code in one place
- Easier to fix bugs (fix once, affects all jobs)
- Version control for common code

### 3. **Better Testability**
- External modules can be unit tested
- Mock-friendly interfaces
- Integration tests for framework

### 4. **Easier Updates**
- Update framework without regenerating all jobs
- Add new features to framework
- Backward compatible changes

### 5. **Code Reusability**
- Framework can be used by other modules
- Consistent execution pattern
- Standardized error handling

### 6. **Parallel Processing Ready**
- Framework can easily support parallel processing
- Clean separation of concerns
- Easy to add new execution strategies

---

## Risk Mitigation

### Risk 1: Breaking Existing Jobs
**Mitigation:**
- Maintain backward compatibility
- Gradual migration path
- Comprehensive testing

### Risk 2: Performance Impact
**Mitigation:**
- Benchmark before/after
- Optimize external modules
- Cache frequently used data

### Risk 3: Complex Migration
**Mitigation:**
- Phased approach
- Keep old code generation as fallback
- Migration scripts if needed

---

## Next Steps

1. **Review this analysis** with team
2. **Create external modules** (Phase 1)
3. **Test modules independently**
4. **Update code generation** (Phase 2)
5. **Integration testing** (Phase 3)
6. **Add parallel processing** (Phase 4)

---

## File Structure After Implementation

```
backend/modules/mapper/
├── mapper_job_executor.py          # NEW: Main execution framework
├── mapper_transformation_utils.py   # NEW: Transformation utilities
├── mapper_checkpoint_handler.py     # NEW: Checkpoint management
├── mapper_scd_handler.py            # NEW: SCD Type 1/2 handling
├── mapper_progress_tracker.py       # NEW: Progress tracking
├── parallel_query_executor.py       # EXISTING: Parallel processing
├── parallel_processor.py            # EXISTING: Parallel coordinator
└── ... (other existing files)
```

---

## Conclusion

By extracting common code to external modules, we can:
- **Reduce dynamic block size by 90%**
- **Improve maintainability significantly**
- **Enable parallel processing integration**
- **Make code more testable and reusable**

The dynamic block will contain only:
- Job-specific configuration
- Job-specific SQL queries
- Job-specific transformation logic
- Simple call to execution framework

This approach aligns perfectly with the goal of keeping the dynamic block "simple and crisp" while moving major activity "behind the scenes."

