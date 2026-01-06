# Sample: Final Dynamic Code Block (After All Phases)

## Overview

This document shows what the database-stored dynamic code will look like after implementing all 4 phases. The common modules will be **completely generic** with **zero job-specific code**.

---

## Key Principle

**Common Modules = Generic & Reusable**
- No job-specific constants
- No job-specific SQL
- No job-specific transformation logic
- All job-specific data passed as parameters

**Dynamic Block = Job-Specific Only**
- Job configuration constants
- Job-specific SQL queries
- Job-specific transformation logic
- Call to generic framework

---

## Sample: Complete Dynamic Block (Final Version)

### Scenario: Simple Dimension Table Load

**Job Details:**
- Mapref: `DIM_CUSTOMER`
- Target: `DW.CUSTOMER_DIM`
- Source: `SELECT customer_id, customer_name, city, country FROM source.customers`
- SCD Type: 1 (overwrite)
- Checkpoint: Disabled

---

### Final Dynamic Code (Stored in DMS_JOBFLW.DWLOGIC)

```python
"""
Auto-generated ETL job for DIM_CUSTOMER
Generated: 2025-01-15 10:30:00
Target: DW.CUSTOMER_DIM
"""

from typing import Dict, Any, List
from datetime import datetime
from backend.modules.mapper.mapper_job_executor import execute_mapper_job
from backend.modules.mapper.mapper_transformation_utils import map_row_to_target_columns

# ============================================================================
# JOB CONFIGURATION (Job-Specific Constants)
# ============================================================================

MAPREF = "DIM_CUSTOMER"
JOBID = 12345
TARGET_SCHEMA = "DW"
TARGET_TABLE = "CUSTOMER_DIM"
TARGET_TYPE = "DIM"
FULL_TABLE_NAME = "DW.CUSTOMER_DIM"

# Checkpoint configuration
CHECKPOINT_ENABLED = False
CHECKPOINT_STRATEGY = "AUTO"
CHECKPOINT_COLUMNS = []
CHECKPOINT_COLUMN = None

# Processing configuration
BLOCK_PROCESS_ROWS = 50000
BULK_LIMIT = 50000

# Primary key configuration
PK_COLUMNS = {'CUSTOMER_ID'}
PK_SOURCE_MAPPING = {'CUSTOMER_ID': 'customer_id'}

# All target columns (in execution order)
ALL_COLUMNS = ['CUSTOMER_ID', 'CUSTOMER_NAME', 'CITY', 'COUNTRY', 'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG']

# Column source mapping (target column -> source column)
COLUMN_SOURCE_MAPPING = {
    'CUSTOMER_ID': 'customer_id',
    'CUSTOMER_NAME': 'customer_name',
    'CITY': 'city',
    'COUNTRY': 'country'
}

# Columns to exclude from hash calculation
HASH_EXCLUDE_COLUMNS = {'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG', 'FROMDT', 'TODT', 'VALDFRM', 'VALDTO'}

# SCD Type for this combination
CURRENT_SCD_TYPE = 1

# ============================================================================
# JOB-SPECIFIC SOURCE SQL (Job-Specific)
# ============================================================================

SOURCE_SQL = """
SELECT 
    customer_id,
    customer_name,
    city,
    country
FROM source.customers
ORDER BY customer_id
"""

# ============================================================================
# TRANSFORMATION FUNCTION (Job-Specific Logic)
# ============================================================================

def transform_row(source_row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform source row to target format.
    This function contains job-specific transformation logic.
    
    Args:
        source_row_dict: Dictionary with source column names as keys
        
    Returns:
        Dictionary with target column names as keys
    """
    # Step 1: Map source columns to target columns
    normalized = map_row_to_target_columns(
        row_dict=source_row_dict,
        column_mapping=COLUMN_SOURCE_MAPPING,
        all_target_columns=ALL_COLUMNS
    )
    
    # Step 2: Apply job-specific transformations
    # Example: Uppercase customer name
    if 'CUSTOMER_NAME' in normalized and normalized['CUSTOMER_NAME']:
        normalized['CUSTOMER_NAME'] = str(normalized['CUSTOMER_NAME']).upper()
    
    # Example: Default values
    if 'COUNTRY' not in normalized or not normalized['COUNTRY']:
        normalized['COUNTRY'] = 'UNKNOWN'
    
    # Step 3: Ensure required columns are present
    # (Framework will add SKEY, RWHKEY, RECCRDT, etc. automatically)
    
    return normalized

# ============================================================================
# MAIN EXECUTION FUNCTION (Orchestration)
# ============================================================================

def execute_job(
    metadata_connection,
    source_connection,
    target_connection,
    session_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute ETL job for DIM_CUSTOMER.
    
    This is a thin orchestration layer that:
    1. Packages job-specific configuration
    2. Calls the generic execution framework
    3. Returns results
    
    Args:
        metadata_connection: Connection for metadata tables (DMS_JOBLOG, DMS_PRCLOG)
        source_connection: Connection for source data queries
        target_connection: Connection for target table operations
        session_params: Session parameters from DMS_PRCLOG
        
    Returns:
        Dictionary with execution results:
        {
            'status': 'SUCCESS' | 'FAILED' | 'STOPPED',
            'source_rows': int,
            'target_rows': int,
            'error_rows': int
        }
    """
    # Package job configuration
    job_config = {
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
        'hash_exclude_columns': HASH_EXCLUDE_COLUMNS,
        'block_process_rows': BLOCK_PROCESS_ROWS,
        'bulk_limit': BULK_LIMIT,
        'scd_type': CURRENT_SCD_TYPE
    }
    
    # Package checkpoint configuration
    checkpoint_config = {
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN
    }
    
    # Execute using generic framework
    result = execute_mapper_job(
        metadata_conn=metadata_connection,
        source_conn=source_connection,
        target_conn=target_connection,
        job_config=job_config,
        source_sql=SOURCE_SQL,
        transformation_func=transform_row,
        checkpoint_config=checkpoint_config,
        session_params=session_params
    )
    
    return result
```

---

## Sample: Complex Job with Multiple Combinations

### Scenario: Fact Table with Multiple SCD Types

**Job Details:**
- Mapref: `FCT_SALES`
- Target: `DW.SALES_FACT`
- Multiple combinations (SCD Type 1 and 2)
- Checkpoint: Enabled (KEY strategy on ORDER_DATE)

---

### Final Dynamic Code (Multiple Combinations)

```python
"""
Auto-generated ETL job for FCT_SALES
Generated: 2025-01-15 10:30:00
Target: DW.SALES_FACT
Combinations: 2 (SCD Type 1 and 2)
"""

from typing import Dict, Any, List
from datetime import datetime
from backend.modules.mapper.mapper_job_executor import execute_mapper_job
from backend.modules.mapper.mapper_transformation_utils import map_row_to_target_columns

# ============================================================================
# COMMON JOB CONFIGURATION
# ============================================================================

MAPREF = "FCT_SALES"
JOBID = 12346
TARGET_SCHEMA = "DW"
TARGET_TABLE = "SALES_FACT"
TARGET_TYPE = "FCT"
FULL_TABLE_NAME = "DW.SALES_FACT"

BLOCK_PROCESS_ROWS = 50000
BULK_LIMIT = 50000

# Primary key
PK_COLUMNS = {'SALE_ID'}
PK_SOURCE_MAPPING = {'SALE_ID': 'sale_id'}

# All target columns
ALL_COLUMNS = [
    'SALE_ID', 'ORDER_DATE', 'CUSTOMER_ID', 'PRODUCT_ID',
    'QUANTITY', 'AMOUNT', 'DISCOUNT', 'SKEY', 'RWHKEY',
    'RECCRDT', 'RECUPDT', 'CURFLG', 'FROMDT', 'TODT'
]

# Column source mapping
COLUMN_SOURCE_MAPPING = {
    'SALE_ID': 'sale_id',
    'ORDER_DATE': 'order_date',
    'CUSTOMER_ID': 'customer_id',
    'PRODUCT_ID': 'product_id',
    'QUANTITY': 'quantity',
    'AMOUNT': 'amount',
    'DISCOUNT': 'discount'
}

HASH_EXCLUDE_COLUMNS = {'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG', 'FROMDT', 'TODT'}

# Checkpoint configuration
CHECKPOINT_ENABLED = True
CHECKPOINT_STRATEGY = "KEY"
CHECKPOINT_COLUMNS = ['ORDER_DATE']
CHECKPOINT_COLUMN = 'ORDER_DATE'

# ============================================================================
# COMBINATION 1: SCD Type 1 (Overwrite)
# ============================================================================

def transform_row_scd1(source_row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Transform for SCD Type 1"""
    normalized = map_row_to_target_columns(
        source_row_dict,
        COLUMN_SOURCE_MAPPING,
        ALL_COLUMNS
    )
    
    # SCD Type 1 specific transformations
    if 'AMOUNT' in normalized:
        normalized['AMOUNT'] = float(normalized['AMOUNT']) if normalized['AMOUNT'] else 0.0
    
    return normalized

SOURCE_SQL_SCD1 = """
SELECT 
    sale_id,
    order_date,
    customer_id,
    product_id,
    quantity,
    amount,
    discount
FROM source.sales
WHERE sale_type = 'REGULAR'
ORDER BY order_date, sale_id
"""

def execute_job_scd1(metadata_connection, source_connection, target_connection, session_params):
    """Execute SCD Type 1 combination"""
    job_config = {
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
        'hash_exclude_columns': HASH_EXCLUDE_COLUMNS,
        'block_process_rows': BLOCK_PROCESS_ROWS,
        'bulk_limit': BULK_LIMIT,
        'scd_type': 1  # SCD Type 1
    }
    
    checkpoint_config = {
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN
    }
    
    return execute_mapper_job(
        metadata_conn=metadata_connection,
        source_conn=source_connection,
        target_conn=target_connection,
        job_config=job_config,
        source_sql=SOURCE_SQL_SCD1,
        transformation_func=transform_row_scd1,
        checkpoint_config=checkpoint_config,
        session_params=session_params
    )

# ============================================================================
# COMBINATION 2: SCD Type 2 (Historical)
# ============================================================================

def transform_row_scd2(source_row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Transform for SCD Type 2"""
    normalized = map_row_to_target_columns(
        source_row_dict,
        COLUMN_SOURCE_MAPPING,
        ALL_COLUMNS
    )
    
    # SCD Type 2 specific transformations
    if 'AMOUNT' in normalized:
        normalized['AMOUNT'] = float(normalized['AMOUNT']) if normalized['AMOUNT'] else 0.0
    
    # Add effective date logic for SCD Type 2
    if 'ORDER_DATE' in normalized:
        normalized['FROMDT'] = normalized['ORDER_DATE']
    
    return normalized

SOURCE_SQL_SCD2 = """
SELECT 
    sale_id,
    order_date,
    customer_id,
    product_id,
    quantity,
    amount,
    discount
FROM source.sales
WHERE sale_type = 'HISTORICAL'
ORDER BY order_date, sale_id
"""

def execute_job_scd2(metadata_connection, source_connection, target_connection, session_params):
    """Execute SCD Type 2 combination"""
    job_config = {
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
        'hash_exclude_columns': HASH_EXCLUDE_COLUMNS,
        'block_process_rows': BLOCK_PROCESS_ROWS,
        'bulk_limit': BULK_LIMIT,
        'scd_type': 2  # SCD Type 2
    }
    
    checkpoint_config = {
        'enabled': CHECKPOINT_ENABLED,
        'strategy': CHECKPOINT_STRATEGY,
        'columns': CHECKPOINT_COLUMNS,
        'column': CHECKPOINT_COLUMN
    }
    
    return execute_mapper_job(
        metadata_conn=metadata_connection,
        source_conn=source_connection,
        target_conn=target_connection,
        job_config=job_config,
        source_sql=SOURCE_SQL_SCD2,
        transformation_func=transform_row_scd2,
        checkpoint_config=checkpoint_config,
        session_params=session_params
    )

# ============================================================================
# MAIN EXECUTION FUNCTION (Orchestrates All Combinations)
# ============================================================================

def execute_job(metadata_connection, source_connection, target_connection, session_params):
    """
    Execute ETL job for FCT_SALES.
    Processes all combinations sequentially.
    """
    results = []
    total_source_rows = 0
    total_target_rows = 0
    total_error_rows = 0
    
    # Execute Combination 1: SCD Type 1
    print("=" * 80)
    print("Processing Combination 1: SCD Type 1")
    print("=" * 80)
    result1 = execute_job_scd1(
        metadata_connection,
        source_connection,
        target_connection,
        session_params
    )
    results.append(result1)
    total_source_rows += result1.get('source_rows', 0)
    total_target_rows += result1.get('target_rows', 0)
    total_error_rows += result1.get('error_rows', 0)
    
    # Execute Combination 2: SCD Type 2
    print("=" * 80)
    print("Processing Combination 2: SCD Type 2")
    print("=" * 80)
    result2 = execute_job_scd2(
        metadata_connection,
        source_connection,
        target_connection,
        session_params
    )
    results.append(result2)
    total_source_rows += result2.get('source_rows', 0)
    total_target_rows += result2.get('target_rows', 0)
    total_error_rows += result2.get('error_rows', 0)
    
    # Return aggregated results
    return {
        'status': 'SUCCESS' if all(r.get('status') == 'SUCCESS' for r in results) else 'PARTIAL',
        'source_rows': total_source_rows,
        'target_rows': total_target_rows,
        'error_rows': total_error_rows,
        'combinations': len(results)
    }
```

---

## What Goes in Common Modules (Generic, No Job-Specific Code)

### Example: `mapper_job_executor.py` (Framework)

```python
"""
Generic mapper job execution framework.
NO job-specific code - all job data passed as parameters.
"""

def execute_mapper_job(
    metadata_conn,
    source_conn,
    target_conn,
    job_config: Dict[str, Any],  # All job-specific config passed here
    source_sql: str,              # Job-specific SQL passed here
    transformation_func: Callable, # Job-specific function passed here
    checkpoint_config: Dict[str, Any],  # Checkpoint config passed here
    session_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generic execution framework.
    
    This function:
    - Validates connections (generic)
    - Handles checkpoints (generic, uses config)
    - Executes source query (uses passed SQL)
    - Processes batches (generic)
    - Calls transformation function (job-specific, passed as parameter)
    - Handles SCD logic (generic, uses config)
    - Logs progress (generic)
    - Returns results (generic format)
    
    NO job-specific constants or logic here!
    """
    # All logic is generic, uses parameters from job_config
    # ...
```

---

## Key Points

### ✅ What's Generic (Common Modules)
- Connection validation
- Cursor management
- Checkpoint handling (uses config, not hardcoded)
- Batch processing loop
- SCD Type 1/2 logic (uses scd_type from config)
- Progress logging
- Error handling
- Stop request checking

### ✅ What's Job-Specific (Dynamic Block)
- Job constants (MAPREF, JOBID, TARGET_SCHEMA, etc.)
- Source SQL queries
- Column mappings
- Transformation logic
- Configuration values

### ❌ What's NOT in Common Modules
- No hardcoded table names
- No hardcoded column names
- No hardcoded SQL queries
- No job-specific business logic
- No job-specific constants

---

## Size Comparison

### Before Optimization
- **Lines:** ~1500-2000
- **Size:** ~50-100 KB
- **Contains:** Everything (common + job-specific)

### After Optimization
- **Lines:** ~100-200 (simple job) or ~300-500 (complex job)
- **Size:** ~5-15 KB
- **Contains:** Only job-specific code
- **Common code:** In external modules (version controlled)

---

## Benefits

1. **Database Code is Minimal**
   - Only job-specific configuration and logic
   - Easy to read and understand
   - Quick to generate

2. **Common Code is Reusable**
   - No job-specific dependencies
   - Can be used by any job
   - Version controlled in git

3. **Easy to Maintain**
   - Fix bugs in common code once
   - Update framework without regenerating jobs
   - Add features to framework easily

4. **Parallel Processing Ready**
   - Framework can call parallel executor
   - Job code doesn't need to know about parallel processing
   - Clean separation of concerns

---

## Summary

**Common Modules = 100% Generic**
- Zero job-specific code
- All job data passed as parameters
- Reusable across all jobs

**Dynamic Block = 100% Job-Specific**
- Job configuration
- Job SQL queries
- Job transformation logic
- Simple orchestration

This ensures clean separation and maximum reusability!

