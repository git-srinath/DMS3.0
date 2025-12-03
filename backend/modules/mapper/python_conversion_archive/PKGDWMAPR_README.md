# PKGDMS_MAPR Python Module Documentation

## Overview

This module provides a Python equivalent of the `PKGDMS_MAPR` PL/SQL package body. It handles data warehouse mapping creation, validation, and management operations.

## Features

- **SQL Query Management**: Create and update SQL queries for mappings
- **Mapping Management**: Create, update, activate/deactivate, and delete mappings
- **Mapping Detail Management**: Manage individual mapping field details
- **Validation**: Comprehensive SQL and mapping logic validation
- **Error Handling**: Robust error handling with detailed logging
- **Historization**: Automatic version tracking of mapping changes

## Installation

The module requires the following dependencies:

```python
import oracledb
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from modules.logger import logger, info, warning, error
```

## Class: PKGDMS_MAPR

### Initialization

```python
from modules.mapper.pkgdms_mapr import PKGDMS_MAPR
import oracledb

# Create database connection
connection = oracledb.connect(user='username', password='password', dsn='dsn')

# Initialize the package
pkg = PKGDMS_MAPR(connection, user='current_user_id')
```

### Methods

#### 1. version() - Static Method

Returns the package version.

```python
version = PKGDMS_MAPR.version()
print(version)  # Output: PKGDMS_MAPR:V001
```

#### 2. create_update_sql()

Create or update SQL query mappings.

**Parameters:**
- `p_dms_maprsqlcd` (str): SQL code identifier (no spaces allowed)
- `p_dms_maprsql` (str): SQL query text (CLOB)

**Returns:** `int` - SQL mapping ID (dms_maprsqlid)

**Example:**

```python
sql_code = "CUSTOMER_QUERY"
sql_text = """
    SELECT 
        customer_id,
        customer_name,
        email
    FROM customers
    WHERE status = 'ACTIVE'
"""

sql_id = pkg.create_update_sql(sql_code, sql_text)
print(f"SQL mapping created with ID: {sql_id}")
```

#### 3. create_update_mapping()

Create or update a mapping record. Automatically historizes changes.

**Parameters:**
- `p_mapref` (str): Mapping reference (unique identifier)
- `p_mapdesc` (str): Mapping description
- `p_trgschm` (str): Target schema name (no spaces, no special chars, can't start with number)
- `p_trgtbtyp` (str): Target table type (`NRM`, `DIM`, `FCT`, `MRT`)
- `p_trgtbnm` (str): Target table name (no spaces, no special chars, can't start with number)
- `p_frqcd` (str): Frequency code (`NA`, `ID`, `DL`, `WK`, `FN`, `MN`, `HY`, `YR`)
- `p_srcsystm` (str): Source system
- `p_lgvrfyflg` (str, optional): Logic verification flag (`Y`/`N`)
- `p_lgvrfydt` (datetime, optional): Logic verification date
- `p_stflg` (str, optional): Status flag (`A`=Active, `N`=Not Active), default='N'
- `p_blkprcrows` (int, optional): Bulk processing rows

**Returns:** `int` - Mapping ID (mapid)

**Example:**

```python
from datetime import datetime

mapid = pkg.create_update_mapping(
    p_mapref='CUST_DIM_001',
    p_mapdesc='Customer Dimension Mapping',
    p_trgschm='DW_SCHEMA',
    p_trgtbtyp='DIM',
    p_trgtbnm='DIM_CUSTOMER',
    p_frqcd='DL',
    p_srcsystm='ERP_SYSTEM',
    p_stflg='N',
    p_blkprcrows=1000
)
print(f"Mapping created with ID: {mapid}")
```

#### 4. create_update_mapping_detail()

Create or update individual mapping field details.

**Parameters:**
- `p_mapref` (str): Mapping reference
- `p_trgclnm` (str): Target column name (no spaces, no special chars, can't start with number)
- `p_trgcldtyp` (str): Target column data type (must exist in DMS_PARAMS)
- `p_trgkeyflg` (str, optional): Primary key flag (`Y`/`N`)
- `p_trgkeyseq` (int, optional): Primary key sequence (required if trgkeyflg='Y')
- `p_trgcldesc` (str, optional): Target column description
- `p_maplogic` (str): Mapping logic (SQL or SQL code reference)
- `p_keyclnm` (str): Key column name(s) in the SQL
- `p_valclnm` (str): Value column name(s) in the SQL
- `p_mapcmbcd` (str, optional): Mapping combination code
- `p_excseq` (int, optional): Execution sequence
- `p_scdtyp` (int, optional): SCD type (1, 2, 3), default=1
- `p_lgvrfyflg` (str, optional): Logic verification flag
- `p_lgvrfydt` (datetime, optional): Logic verification date

**Returns:** `int` - Mapping detail ID (mapdtlid)

**Example:**

```python
detail_id = pkg.create_update_mapping_detail(
    p_mapref='CUST_DIM_001',
    p_trgclnm='CUSTOMER_ID',
    p_trgcldtyp='NUMBER',
    p_trgkeyflg='Y',
    p_trgkeyseq=1,
    p_trgcldesc='Customer unique identifier',
    p_maplogic='SELECT cust_id, cust_name FROM source_customers',
    p_keyclnm='cust_id',
    p_valclnm='cust_id',
    p_mapcmbcd='MAIN',
    p_excseq=1,
    p_scdtyp=1
)
print(f"Mapping detail created with ID: {detail_id}")
```

#### 5. validate_sql()

Validate SQL query syntax.

**Parameters:**
- `p_logic` (str): SQL query to validate

**Returns:** `str` - 'Y' if valid, 'N' if invalid

**Example:**

```python
sql = "SELECT * FROM customers WHERE status = 'ACTIVE'"
result = pkg.validate_sql(sql)

if result == 'Y':
    print("SQL is valid")
else:
    print("SQL is invalid")
```

#### 6. validate_logic() and validate_logic2()

Validate mapping logic (SQL with key and value columns).

**Parameters:**
- `p_logic` (str): Mapping logic (SQL or SQL code)
- `p_keyclnm` (str): Key column name
- `p_valclnm` (str): Value column name

**Returns:** 
- `validate_logic()`: `str` - 'Y' if valid, 'N' if invalid
- `validate_logic2()`: `Tuple[str, str]` - (validation_flag, error_message)

**Example:**

```python
# Using validate_logic
result = pkg.validate_logic(
    p_logic='SELECT cust_id, cust_name FROM customers',
    p_keyclnm='cust_id',
    p_valclnm='cust_name'
)
print(f"Validation result: {result}")

# Using validate_logic2 (returns error message)
result, error_msg = pkg.validate_logic2(
    p_logic='SELECT cust_id, cust_name FROM customers',
    p_keyclnm='cust_id',
    p_valclnm='cust_name'
)

if result == 'N':
    print(f"Validation failed: {error_msg}")
else:
    print("Validation passed")
```

#### 7. validate_all_logic()

Validate all mapping details for a given mapping reference. Updates validation flags in the database.

**Parameters:**
- `p_mapref` (str): Mapping reference

**Returns:** `str` - 'Y' if all valid, 'N' if any invalid

**Example:**

```python
result = pkg.validate_all_logic('CUST_DIM_001')

if result == 'Y':
    print("All mapping details are valid")
else:
    print("Some mapping details have validation errors")
```

#### 8. validate_mapping_details()

Comprehensive validation of all mapping details including:
- Logic validation
- Primary key specifications
- Duplicate column name checks
- Duplicate value column checks within mapping codes

**Parameters:**
- `p_mapref` (str): Mapping reference

**Returns:** `Tuple[str, str]` - (validation_flag, error_message)

**Example:**

```python
valid, error_msg = pkg.validate_mapping_details('CUST_DIM_001')

if valid == 'Y':
    print("Mapping is valid and ready for activation")
else:
    print(f"Validation errors: {error_msg}")
```

#### 9. activate_deactivate_mapping()

Activate or deactivate a mapping. Automatically validates before activation.

**Parameters:**
- `p_mapref` (str): Mapping reference
- `p_stflg` (str): Status flag ('A'=Active, 'N'=Not Active)

**Returns:** `Tuple[bool, str]` - (success, message)

**Example:**

```python
# Activate mapping
success, message = pkg.activate_deactivate_mapping('CUST_DIM_001', 'A')

if success:
    print(f"Success: {message}")
else:
    print(f"Error: {message}")

# Deactivate mapping
success, message = pkg.activate_deactivate_mapping('CUST_DIM_001', 'N')
```

#### 10. delete_mapping()

Delete a mapping and all its details. Prevents deletion if related jobs exist.

**Parameters:**
- `p_mapref` (str): Mapping reference

**Returns:** `Tuple[bool, str]` - (success, message)

**Example:**

```python
success, message = pkg.delete_mapping('CUST_DIM_001')

if success:
    print(f"Success: {message}")
else:
    print(f"Error: {message}")
```

#### 11. delete_mapping_details()

Delete a specific mapping detail. Prevents deletion if related job details exist.

**Parameters:**
- `p_mapref` (str): Mapping reference
- `p_trgclnm` (str): Target column name

**Returns:** `Tuple[bool, str]` - (success, message)

**Example:**

```python
success, message = pkg.delete_mapping_details('CUST_DIM_001', 'CUSTOMER_NAME')

if success:
    print(f"Success: {message}")
else:
    print(f"Error: {message}")
```

## Convenience Functions

The module also provides convenience functions that automatically set the user:

### create_update_mapping_with_user()
### create_update_mapping_detail_with_user()
### validate_logic_with_user()
### validate_mapping_details_with_user()
### activate_deactivate_mapping_with_user()

**Example:**

```python
from modules.mapper.pkgdms_mapr import create_update_mapping_with_user

mapid = create_update_mapping_with_user(
    connection=connection,
    p_mapref='CUST_DIM_001',
    p_mapdesc='Customer Dimension',
    p_trgschm='DW_SCHEMA',
    p_trgtbtyp='DIM',
    p_trgtbnm='DIM_CUSTOMER',
    p_frqcd='DL',
    p_srcsystm='ERP',
    p_lgvrfyflg=None,
    p_lgvrfydt=None,
    p_stflg='N',
    p_blkprcrows=1000,
    p_user='admin_user'  # User parameter
)
```

## Error Handling

The module uses a custom exception class `PKGDMS_MAPRError` for all errors:

```python
from modules.mapper.pkgdms_mapr import PKGDMS_MAPRError

try:
    mapid = pkg.create_update_mapping(
        p_mapref='TEST_MAP',
        p_mapdesc='Test Mapping',
        # ... other parameters
    )
except PKGDMS_MAPRError as e:
    print(f"Error in procedure: {e.proc_name}")
    print(f"Error code: {e.error_code}")
    print(f"Parameters: {e.params}")
    print(f"Message: {e.message}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Complete Workflow Example

```python
from modules.mapper.pkgdms_mapr import PKGDMS_MAPR
import oracledb
from datetime import datetime

# 1. Create connection
connection = oracledb.connect(
    user='dw_user',
    password='password',
    dsn='localhost:1521/XEPDB1'
)

# 2. Initialize package
pkg = PKGDMS_MAPR(connection, user='admin')

try:
    # 3. Create a mapping
    mapid = pkg.create_update_mapping(
        p_mapref='PROD_DIM_001',
        p_mapdesc='Product Dimension Mapping',
        p_trgschm='DW_PROD',
        p_trgtbtyp='DIM',
        p_trgtbnm='DIM_PRODUCT',
        p_frqcd='DL',
        p_srcsystm='ERP_PRODUCTS',
        p_stflg='N',
        p_blkprcrows=5000
    )
    print(f"Created mapping with ID: {mapid}")
    
    # 4. Add mapping details (primary key)
    detail1_id = pkg.create_update_mapping_detail(
        p_mapref='PROD_DIM_001',
        p_trgclnm='PRODUCT_ID',
        p_trgcldtyp='NUMBER',
        p_trgkeyflg='Y',
        p_trgkeyseq=1,
        p_trgcldesc='Product ID',
        p_maplogic='SELECT prod_id, prod_id FROM erp_products',
        p_keyclnm='prod_id',
        p_valclnm='prod_id',
        p_mapcmbcd='MAIN',
        p_excseq=1,
        p_scdtyp=1
    )
    
    # 5. Add more mapping details
    detail2_id = pkg.create_update_mapping_detail(
        p_mapref='PROD_DIM_001',
        p_trgclnm='PRODUCT_NAME',
        p_trgcldtyp='VARCHAR2',
        p_trgkeyflg='N',
        p_trgkeyseq=None,
        p_trgcldesc='Product Name',
        p_maplogic='SELECT prod_id, prod_name FROM erp_products',
        p_keyclnm='prod_id',
        p_valclnm='prod_name',
        p_mapcmbcd='MAIN',
        p_excseq=1,
        p_scdtyp=2
    )
    
    # 6. Validate all mappings
    valid, error_msg = pkg.validate_mapping_details('PROD_DIM_001')
    
    if valid == 'Y':
        print("All validations passed!")
        
        # 7. Activate the mapping
        success, message = pkg.activate_deactivate_mapping('PROD_DIM_001', 'A')
        
        if success:
            print(f"Mapping activated: {message}")
        else:
            print(f"Activation failed: {message}")
    else:
        print(f"Validation errors: {error_msg}")
    
    # 8. Commit changes
    connection.commit()
    
except PKGDMS_MAPRError as e:
    print(f"PKGDMS_MAPR Error: {e.message}")
    connection.rollback()
except Exception as e:
    print(f"Error: {str(e)}")
    connection.rollback()
finally:
    connection.close()
```

## Validation Rules

### Mapping Reference Validation
- Cannot be empty
- Must be unique

### Target Schema/Table/Column Names
- No blank spaces allowed
- No special characters (only alphanumeric and underscore)
- Cannot start with a number

### Target Table Type
- Must be one of: `NRM`, `DIM`, `FCT`, `MRT`

### Frequency Code
- Must be one of: `NA`, `ID`, `DL`, `WK`, `FN`, `MN`, `HY`, `YR`

### Status Flag
- Must be: `A` (Active) or `N` (Not Active)

### Logic Verification
- Both flag and date must be provided together or both must be blank

### Primary Keys
- At least one column must be marked as primary key
- Primary key sequence cannot repeat
- Key sequence is mandatory if key flag is 'Y'

### Column Names
- Target column names cannot repeat within a mapping
- Value column names cannot repeat within the same mapping combination code

### Data Types
- Must exist in DMS_PARAMS table with PRTYP = 'Datatype'

### SCD Type
- Must be: 1, 2, or 3

### Bulk Processing Rows
- Cannot be negative

## Database Tables

The module interacts with the following tables:

- `DMS_MAPR` - Main mapping table
- `DMS_MAPRDTL` - Mapping details table
- `DMS_MAPRSQL` - SQL query storage table
- `DMS_MAPERR` - Mapping error table
- `DMS_PARAMS` - Parameter configuration table
- `DMS_JOB` - Job definitions table
- `DMS_JOBDTL` - Job details table

## Logging

All operations are logged using the application's logging system:

```python
from modules.logger import logger, info, warning, error
```

Errors are automatically logged when `PKGDMS_MAPRError` exceptions are raised.

## Migration from PL/SQL

If you're migrating from the PL/SQL package, here are the key differences:

1. **Function Return Values**: Some procedures in PL/SQL that used OUT parameters now return tuples in Python
2. **Error Handling**: Use Python's try-except instead of PL/SQL exception blocks
3. **CLOB Handling**: Python strings can handle large text directly
4. **Sequences**: Sequences are still handled by the database
5. **Commit**: You must explicitly call `connection.commit()`

## Version History

- **V001** (12-Nov-2025): Initial Python port from PL/SQL
  - Complete conversion of all PKGDMS_MAPR functions
  - Added comprehensive error handling
  - Added Python-style convenience functions
  - Enhanced documentation

## License

This module is part of the DWTOOL project and follows the same license terms.

## Support

For issues or questions, please refer to the main DWTOOL documentation or contact the development team.

