# PL/SQL to Python Function Mapping

## Quick Reference Guide

This document provides a side-by-side comparison of PL/SQL functions in `PKGDMS_MAPR_bdy.sql` and their Python equivalents in `pkgdms_mapr.py`.

---

## Package Version

### PL/SQL
```sql
function version return varchar is
begin
  return g_name||':'||g_ver;
end;
```

### Python
```python
@staticmethod
def version() -> str:
    return f"{PKGDMS_MAPR.G_NAME}:{PKGDMS_MAPR.G_VER}"
```

**Usage:**
```python
# PL/SQL: SELECT PKGDMS_MAPR.VERSION() FROM DUAL;
# Python:
version = PKGDMS_MAPR.version()
```

---

## CREATE_UPDATE_SQL

### PL/SQL
```sql
function CREATE_UPDATE_SQL(
    p_dms_maprsqlcd in DMS_MAPRSQL.dms_maprsqlcd%type,
    p_dms_maprsql   in DMS_MAPRSQL.DMS_MAPRSQL%type
) return DMS_MAPRSQL.dms_maprsqlid%type;
```

### Python
```python
def create_update_sql(
    self,
    p_dms_maprsqlcd: str,
    p_dms_maprsql: str
) -> int:
```

**Usage:**
```python
# PL/SQL:
# v_sql_id := PKGDMS_MAPR.CREATE_UPDATE_SQL('MY_SQL_CODE', 'SELECT * FROM ...');

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
sql_id = pkg.create_update_sql('MY_SQL_CODE', 'SELECT * FROM ...')
```

---

## CREATE_UPDATE_MAPPING (without user parameter)

### PL/SQL
```sql
function CREATE_UPDATE_MAPPING(
   p_mapref     in DMS_MAPR.mapref%type,
   p_mapdesc    in DMS_MAPR.mapdesc%type,
   p_trgschm    in DMS_MAPR.trgschm%type,
   p_trgtbtyp   in DMS_MAPR.trgtbtyp%type,
   p_trgtbnm    in DMS_MAPR.trgtbnm%type,
   p_frqcd      in DMS_MAPR.frqcd%type,
   p_srcsystm   in DMS_MAPR.srcsystm%type,
   p_lgvrfyflg  in DMS_MAPR.lgvrfyflg%type,
   p_lgvrfydt   in DMS_MAPR.lgvrfydt%type,
   p_stflg      in DMS_MAPR.stflg%type,
   p_blkprcrows in DMS_MAPR.blkprcrows%type
) return DMS_MAPR.mapid%type;
```

### Python
```python
def create_update_mapping(
    self,
    p_mapref: str,
    p_mapdesc: str,
    p_trgschm: str,
    p_trgtbtyp: str,
    p_trgtbnm: str,
    p_frqcd: str,
    p_srcsystm: str,
    p_lgvrfyflg: str = None,
    p_lgvrfydt: datetime = None,
    p_stflg: str = 'N',
    p_blkprcrows: int = None
) -> int:
```

**Usage:**
```python
# PL/SQL:
# v_mapid := PKGDMS_MAPR.CREATE_UPDATE_MAPPING(
#     p_mapref => 'MAP001',
#     p_mapdesc => 'Description',
#     ...
# );

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
mapid = pkg.create_update_mapping(
    p_mapref='MAP001',
    p_mapdesc='Description',
    ...
)
```

---

## CREATE_UPDATE_MAPPING (with user parameter)

### PL/SQL
```sql
function CREATE_UPDATE_MAPPING(
   p_mapref     in DMS_MAPR.mapref%type,
   p_mapdesc    in DMS_MAPR.mapdesc%type,
   ...
   p_user       in DMS_MAPR.crtdby%type
) return DMS_MAPR.mapid%type;
```

### Python
```python
# Method 1: Set user in constructor
pkg = PKGDMS_MAPR(connection, user='admin')
mapid = pkg.create_update_mapping(...)

# Method 2: Use convenience function
from modules.mapper.pkgdms_mapr import create_update_mapping_with_user

mapid = create_update_mapping_with_user(
    connection=connection,
    p_mapref='MAP001',
    ...
    p_user='admin'
)
```

**Usage:**
```python
# PL/SQL:
# v_mapid := PKGDMS_MAPR.CREATE_UPDATE_MAPPING(
#     p_mapref => 'MAP001',
#     ...
#     p_user => 'ADMIN'
# );

# Python - Option 1:
pkg = PKGDMS_MAPR(connection, user='admin')
mapid = pkg.create_update_mapping(p_mapref='MAP001', ...)

# Python - Option 2:
mapid = create_update_mapping_with_user(
    connection=connection,
    p_mapref='MAP001',
    ...
    p_user='admin'
)
```

---

## CREATE_UPDATE_MAPPING_DETAIL

### PL/SQL
```sql
function CREATE_UPDATE_MAPPING_DETAIL(
   p_mapref     in DMS_MAPRDTL.mapref%type,
   p_trgclnm    in DMS_MAPRDTL.trgclnm%type,
   p_trgcldtyp  in DMS_MAPRDTL.trgcldtyp%type,
   p_trgkeyflg  in DMS_MAPRDTL.trgkeyflg%type,
   p_trgkeyseq  in DMS_MAPRDTL.trgkeyseq%type,
   p_trgcldesc  in DMS_MAPRDTL.trgcldesc%type,
   p_maplogic   in DMS_MAPRDTL.maplogic%type,
   p_keyclnm    in DMS_MAPRDTL.keyclnm%type,
   p_valclnm    in DMS_MAPRDTL.valclnm%type,
   p_mapcmbcd   in DMS_MAPRDTL.mapcmbcd%type,
   p_excseq     in DMS_MAPRDTL.excseq%type,
   p_scdtyp     in DMS_MAPRDTL.scdtyp%type,
   p_lgvrfyflg  in DMS_MAPRDTL.lgvrfyflg%type,
   p_lgvrfydt   in DMS_MAPRDTL.lgvrfydt%type
) return DMS_MAPRDTL.mapdtlid%type;
```

### Python
```python
def create_update_mapping_detail(
    self,
    p_mapref: str,
    p_trgclnm: str,
    p_trgcldtyp: str,
    p_trgkeyflg: str = None,
    p_trgkeyseq: int = None,
    p_trgcldesc: str = None,
    p_maplogic: str = None,
    p_keyclnm: str = None,
    p_valclnm: str = None,
    p_mapcmbcd: str = None,
    p_excseq: int = None,
    p_scdtyp: int = 1,
    p_lgvrfyflg: str = None,
    p_lgvrfydt: datetime = None
) -> int:
```

---

## VALIDATE_SQL

### PL/SQL
```sql
function VALIDATE_SQL(p_logic in DMS_MAPRSQL.DMS_MAPRSQL%type)
return varchar2;
```

### Python
```python
def validate_sql(self, p_logic: str) -> str:
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDMS_MAPR.VALIDATE_SQL('SELECT * FROM ...');
# IF v_result = 'Y' THEN ...

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
result = pkg.validate_sql('SELECT * FROM ...')
if result == 'Y':
    print("Valid")
```

---

## VALIDATE_LOGIC (for single logic)

### PL/SQL
```sql
Function VALIDATE_LOGIC(
    p_logic   in DMS_MAPRDTL.maplogic%type,
    p_keyclnm in DMS_MAPRDTL.keyclnm%type,
    p_valclnm in DMS_MAPRDTL.valclnm%type
) return DMS_MAPRDTL.lgvrfyflg%type;
```

### Python
```python
def validate_logic(
    self,
    p_logic: str,
    p_keyclnm: str,
    p_valclnm: str
) -> str:
```

---

## VALIDATE_LOGIC2 (with error output)

### PL/SQL
```sql
Function VALIDATE_LOGIC2(
    p_logic   in  DMS_MAPRDTL.maplogic%type,
    p_keyclnm in  DMS_MAPRDTL.keyclnm%type,
    p_valclnm in  DMS_MAPRDTL.valclnm%type,
    p_err     out varchar2
) return DMS_MAPRDTL.lgvrfyflg%type;
```

### Python
```python
def validate_logic2(
    self,
    p_logic: str,
    p_keyclnm: str,
    p_valclnm: str
) -> Tuple[str, str]:  # Returns (result, error_message)
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDMS_MAPR.VALIDATE_LOGIC2(
#     p_logic => 'SELECT ...',
#     p_keyclnm => 'id',
#     p_valclnm => 'name',
#     p_err => v_error
# );

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
result, error = pkg.validate_logic2(
    p_logic='SELECT ...',
    p_keyclnm='id',
    p_valclnm='name'
)
```

---

## VALIDATE_LOGIC (for mapping reference)

### PL/SQL
```sql
Function VALIDATE_LOGIC(p_mapref in DMS_MAPR.mapref%type)
return DMS_MAPRDTL.lgvrfyflg%type;
```

### Python
```python
def validate_all_logic(self, p_mapref: str) -> str:
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDMS_MAPR.VALIDATE_LOGIC('MAP001');

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
result = pkg.validate_all_logic('MAP001')
```

---

## VALIDATE_MAPPING_DETAILS

### PL/SQL
```sql
function VALIDATE_MAPPING_DETAILS(
    p_mapref in  DMS_MAPR.mapref%type,
    p_err    out varchar2
) return varchar2;
```

### Python
```python
def validate_mapping_details(
    self,
    p_mapref: str
) -> Tuple[str, str]:  # Returns (result, error_message)
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDMS_MAPR.VALIDATE_MAPPING_DETAILS(
#     p_mapref => 'MAP001',
#     p_err => v_error
# );

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
result, error = pkg.validate_mapping_details('MAP001')
```

---

## ACTIVATE_DEACTIVATE_MAPPING

### PL/SQL
```sql
Procedure ACTIVATE_DEACTIVATE_MAPPING(
    p_mapref in  DMS_MAPR.mapref%type,
    p_stflg  in  DMS_MAPR.stflg%type,
    p_err    out varchar2
);
```

### Python
```python
def activate_deactivate_mapping(
    self,
    p_mapref: str,
    p_stflg: str
) -> Tuple[bool, str]:  # Returns (success, message)
```

**Usage:**
```python
# PL/SQL:
# PKGDMS_MAPR.ACTIVATE_DEACTIVATE_MAPPING(
#     p_mapref => 'MAP001',
#     p_stflg => 'A',
#     p_err => v_error
# );

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
success, message = pkg.activate_deactivate_mapping('MAP001', 'A')
if success:
    print(message)
else:
    print(f"Error: {message}")
```

---

## DELETE_MAPPING

### PL/SQL
```sql
procedure DELETE_MAPPING(
    p_mapref in  DMS_MAPR.mapref%type,
    p_err    out varchar2
);
```

### Python
```python
def delete_mapping(
    self,
    p_mapref: str
) -> Tuple[bool, str]:  # Returns (success, message)
```

**Usage:**
```python
# PL/SQL:
# PKGDMS_MAPR.DELETE_MAPPING(
#     p_mapref => 'MAP001',
#     p_err => v_error
# );

# Python:
pkg = PKGDMS_MAPR(connection, user='admin')
success, message = pkg.delete_mapping('MAP001')
```

---

## DELETE_MAPPING_DETAILS

### PL/SQL
```sql
procedure DELETE_MAPPING_DETAILS(
    p_mapref  in  DMS_MAPRDTL.mapref%type,
    p_trgclnm in  DMS_MAPRDTL.trgclnm%type,
    p_err     out varchar2
);
```

### Python
```python
def delete_mapping_details(
    self,
    p_mapref: str,
    p_trgclnm: str
) -> Tuple[bool, str]:  # Returns (success, message)
```

---

## Key Differences

### 1. OUT Parameters
**PL/SQL:**
```sql
PROCEDURE my_proc(
    p_input  IN  VARCHAR2,
    p_output OUT VARCHAR2
);
```

**Python:**
```python
# Returns tuple instead of OUT parameter
def my_proc(self, p_input: str) -> Tuple[bool, str]:
    return (success, output_value)
```

### 2. Error Handling
**PL/SQL:**
```sql
BEGIN
  -- code
EXCEPTION
  WHEN OTHERS THEN
    PKGERR.RAISE_ERROR(...);
END;
```

**Python:**
```python
try:
    # code
except Exception as e:
    raise PKGDMS_MAPRError(...)
```

### 3. NULL Handling
**PL/SQL:**
```sql
IF nvl(p_value, 'default') = 'something' THEN
```

**Python:**
```python
if (p_value or 'default') == 'something':
```

### 4. Date Handling
**PL/SQL:**
```sql
SYSDATE
TO_DATE('2025-01-01', 'YYYY-MM-DD')
```

**Python:**
```python
from datetime import datetime

# Use Python datetime objects
datetime.now()
datetime(2025, 1, 1)
```

### 5. COMMIT/ROLLBACK
**PL/SQL:**
```sql
COMMIT;
ROLLBACK;
```

**Python:**
```python
connection.commit()
connection.rollback()
```

### 6. Cursor Management
**PL/SQL:**
```sql
CURSOR my_cur IS SELECT ...;
OPEN my_cur;
FETCH my_cur INTO ...;
CLOSE my_cur;
```

**Python:**
```python
cursor = connection.cursor()
cursor.execute("SELECT ...")
row = cursor.fetchone()
cursor.close()
```

---

## Complete Example Comparison

### PL/SQL
```sql
DECLARE
  v_mapid NUMBER;
  v_error VARCHAR2(400);
BEGIN
  -- Create mapping
  v_mapid := PKGDMS_MAPR.CREATE_UPDATE_MAPPING(
    p_mapref => 'MAP001',
    p_mapdesc => 'Test Mapping',
    p_trgschm => 'DW',
    p_trgtbtyp => 'DIM',
    p_trgtbnm => 'DIM_CUST',
    p_frqcd => 'DL',
    p_srcsystm => 'ERP',
    p_lgvrfyflg => NULL,
    p_lgvrfydt => NULL,
    p_stflg => 'N',
    p_blkprcrows => 1000,
    p_user => 'ADMIN'
  );
  
  -- Validate
  IF PKGDMS_MAPR.VALIDATE_MAPPING_DETAILS(
    p_mapref => 'MAP001',
    p_err => v_error
  ) = 'Y' THEN
    -- Activate
    PKGDMS_MAPR.ACTIVATE_DEACTIVATE_MAPPING(
      p_mapref => 'MAP001',
      p_stflg => 'A',
      p_err => v_error
    );
  END IF;
  
  COMMIT;
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    RAISE;
END;
```

### Python
```python
from modules.mapper.pkgdms_mapr import (
    PKGDMS_MAPR,
    PKGDMS_MAPRError
)
import oracledb

connection = oracledb.connect(...)

try:
    pkg = PKGDMS_MAPR(connection, user='ADMIN')
    
    # Create mapping
    mapid = pkg.create_update_mapping(
        p_mapref='MAP001',
        p_mapdesc='Test Mapping',
        p_trgschm='DW',
        p_trgtbtyp='DIM',
        p_trgtbnm='DIM_CUST',
        p_frqcd='DL',
        p_srcsystm='ERP',
        p_lgvrfyflg=None,
        p_lgvrfydt=None,
        p_stflg='N',
        p_blkprcrows=1000
    )
    
    # Validate
    valid, error = pkg.validate_mapping_details('MAP001')
    
    if valid == 'Y':
        # Activate
        success, message = pkg.activate_deactivate_mapping('MAP001', 'A')
        
        if success:
            print(message)
    
    connection.commit()
    
except PKGDMS_MAPRError as e:
    connection.rollback()
    print(f"Error: {e.message}")
except Exception as e:
    connection.rollback()
    print(f"Error: {str(e)}")
finally:
    connection.close()
```

---

## Migration Checklist

When migrating from PL/SQL to Python:

- [ ] Replace `FUNCTION` with `def` method
- [ ] Replace `PROCEDURE` with `def` method returning tuple for OUT parameters
- [ ] Replace `OUT` parameters with return tuples
- [ ] Replace `VARCHAR2`, `NUMBER`, `DATE` with Python types
- [ ] Replace `NVL()` with `or` operator or `if not value`
- [ ] Replace `SYSDATE` with `datetime.now()`
- [ ] Replace `COMMIT` with `connection.commit()`
- [ ] Replace `ROLLBACK` with `connection.rollback()`
- [ ] Replace PL/SQL exception blocks with Python try-except
- [ ] Use `PKGDMS_MAPRError` for custom errors
- [ ] Test all validations and edge cases

---

## Additional Resources

- See `PKGDMS_MAPR_README.md` for detailed Python documentation
- See `pkgdms_mapr_example.py` for working code examples
- See `pkgdms_mapr.py` for complete implementation

