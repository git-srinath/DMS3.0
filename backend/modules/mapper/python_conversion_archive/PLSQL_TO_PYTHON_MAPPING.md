# PL/SQL to Python Function Mapping

## Quick Reference Guide

This document provides a side-by-side comparison of PL/SQL functions in `PKGDWMAPR_bdy.sql` and their Python equivalents in `pkgdwmapr.py`.

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
    return f"{PKGDWMAPR.G_NAME}:{PKGDWMAPR.G_VER}"
```

**Usage:**
```python
# PL/SQL: SELECT PKGDWMAPR.VERSION() FROM DUAL;
# Python:
version = PKGDWMAPR.version()
```

---

## CREATE_UPDATE_SQL

### PL/SQL
```sql
function CREATE_UPDATE_SQL(
    p_dwmaprsqlcd in dwmaprsql.dwmaprsqlcd%type,
    p_dwmaprsql   in dwmaprsql.dwmaprsql%type
) return dwmaprsql.dwmaprsqlid%type;
```

### Python
```python
def create_update_sql(
    self,
    p_dwmaprsqlcd: str,
    p_dwmaprsql: str
) -> int:
```

**Usage:**
```python
# PL/SQL:
# v_sql_id := PKGDWMAPR.CREATE_UPDATE_SQL('MY_SQL_CODE', 'SELECT * FROM ...');

# Python:
pkg = PKGDWMAPR(connection, user='admin')
sql_id = pkg.create_update_sql('MY_SQL_CODE', 'SELECT * FROM ...')
```

---

## CREATE_UPDATE_MAPPING (without user parameter)

### PL/SQL
```sql
function CREATE_UPDATE_MAPPING(
   p_mapref     in dwmapr.mapref%type,
   p_mapdesc    in dwmapr.mapdesc%type,
   p_trgschm    in dwmapr.trgschm%type,
   p_trgtbtyp   in dwmapr.trgtbtyp%type,
   p_trgtbnm    in dwmapr.trgtbnm%type,
   p_frqcd      in dwmapr.frqcd%type,
   p_srcsystm   in dwmapr.srcsystm%type,
   p_lgvrfyflg  in dwmapr.lgvrfyflg%type,
   p_lgvrfydt   in dwmapr.lgvrfydt%type,
   p_stflg      in dwmapr.stflg%type,
   p_blkprcrows in dwmapr.blkprcrows%type
) return dwmapr.mapid%type;
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
# v_mapid := PKGDWMAPR.CREATE_UPDATE_MAPPING(
#     p_mapref => 'MAP001',
#     p_mapdesc => 'Description',
#     ...
# );

# Python:
pkg = PKGDWMAPR(connection, user='admin')
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
   p_mapref     in dwmapr.mapref%type,
   p_mapdesc    in dwmapr.mapdesc%type,
   ...
   p_user       in dwmapr.crtdby%type
) return dwmapr.mapid%type;
```

### Python
```python
# Method 1: Set user in constructor
pkg = PKGDWMAPR(connection, user='admin')
mapid = pkg.create_update_mapping(...)

# Method 2: Use convenience function
from modules.mapper.pkgdwmapr import create_update_mapping_with_user

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
# v_mapid := PKGDWMAPR.CREATE_UPDATE_MAPPING(
#     p_mapref => 'MAP001',
#     ...
#     p_user => 'ADMIN'
# );

# Python - Option 1:
pkg = PKGDWMAPR(connection, user='admin')
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
   p_mapref     in dwmaprdtl.mapref%type,
   p_trgclnm    in dwmaprdtl.trgclnm%type,
   p_trgcldtyp  in dwmaprdtl.trgcldtyp%type,
   p_trgkeyflg  in dwmaprdtl.trgkeyflg%type,
   p_trgkeyseq  in dwmaprdtl.trgkeyseq%type,
   p_trgcldesc  in dwmaprdtl.trgcldesc%type,
   p_maplogic   in dwmaprdtl.maplogic%type,
   p_keyclnm    in dwmaprdtl.keyclnm%type,
   p_valclnm    in dwmaprdtl.valclnm%type,
   p_mapcmbcd   in dwmaprdtl.mapcmbcd%type,
   p_excseq     in dwmaprdtl.excseq%type,
   p_scdtyp     in dwmaprdtl.scdtyp%type,
   p_lgvrfyflg  in dwmaprdtl.lgvrfyflg%type,
   p_lgvrfydt   in dwmaprdtl.lgvrfydt%type
) return dwmaprdtl.mapdtlid%type;
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
function VALIDATE_SQL(p_logic in dwmaprsql.dwmaprsql%type)
return varchar2;
```

### Python
```python
def validate_sql(self, p_logic: str) -> str:
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDWMAPR.VALIDATE_SQL('SELECT * FROM ...');
# IF v_result = 'Y' THEN ...

# Python:
pkg = PKGDWMAPR(connection, user='admin')
result = pkg.validate_sql('SELECT * FROM ...')
if result == 'Y':
    print("Valid")
```

---

## VALIDATE_LOGIC (for single logic)

### PL/SQL
```sql
Function VALIDATE_LOGIC(
    p_logic   in dwmaprdtl.maplogic%type,
    p_keyclnm in dwmaprdtl.keyclnm%type,
    p_valclnm in dwmaprdtl.valclnm%type
) return dwmaprdtl.lgvrfyflg%type;
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
    p_logic   in  dwmaprdtl.maplogic%type,
    p_keyclnm in  dwmaprdtl.keyclnm%type,
    p_valclnm in  dwmaprdtl.valclnm%type,
    p_err     out varchar2
) return dwmaprdtl.lgvrfyflg%type;
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
# v_result := PKGDWMAPR.VALIDATE_LOGIC2(
#     p_logic => 'SELECT ...',
#     p_keyclnm => 'id',
#     p_valclnm => 'name',
#     p_err => v_error
# );

# Python:
pkg = PKGDWMAPR(connection, user='admin')
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
Function VALIDATE_LOGIC(p_mapref in dwmapr.mapref%type)
return dwmaprdtl.lgvrfyflg%type;
```

### Python
```python
def validate_all_logic(self, p_mapref: str) -> str:
```

**Usage:**
```python
# PL/SQL:
# v_result := PKGDWMAPR.VALIDATE_LOGIC('MAP001');

# Python:
pkg = PKGDWMAPR(connection, user='admin')
result = pkg.validate_all_logic('MAP001')
```

---

## VALIDATE_MAPPING_DETAILS

### PL/SQL
```sql
function VALIDATE_MAPPING_DETAILS(
    p_mapref in  dwmapr.mapref%type,
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
# v_result := PKGDWMAPR.VALIDATE_MAPPING_DETAILS(
#     p_mapref => 'MAP001',
#     p_err => v_error
# );

# Python:
pkg = PKGDWMAPR(connection, user='admin')
result, error = pkg.validate_mapping_details('MAP001')
```

---

## ACTIVATE_DEACTIVATE_MAPPING

### PL/SQL
```sql
Procedure ACTIVATE_DEACTIVATE_MAPPING(
    p_mapref in  dwmapr.mapref%type,
    p_stflg  in  dwmapr.stflg%type,
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
# PKGDWMAPR.ACTIVATE_DEACTIVATE_MAPPING(
#     p_mapref => 'MAP001',
#     p_stflg => 'A',
#     p_err => v_error
# );

# Python:
pkg = PKGDWMAPR(connection, user='admin')
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
    p_mapref in  dwmapr.mapref%type,
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
# PKGDWMAPR.DELETE_MAPPING(
#     p_mapref => 'MAP001',
#     p_err => v_error
# );

# Python:
pkg = PKGDWMAPR(connection, user='admin')
success, message = pkg.delete_mapping('MAP001')
```

---

## DELETE_MAPPING_DETAILS

### PL/SQL
```sql
procedure DELETE_MAPPING_DETAILS(
    p_mapref  in  dwmaprdtl.mapref%type,
    p_trgclnm in  dwmaprdtl.trgclnm%type,
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
    raise PKGDWMAPRError(...)
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
  v_mapid := PKGDWMAPR.CREATE_UPDATE_MAPPING(
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
  IF PKGDWMAPR.VALIDATE_MAPPING_DETAILS(
    p_mapref => 'MAP001',
    p_err => v_error
  ) = 'Y' THEN
    -- Activate
    PKGDWMAPR.ACTIVATE_DEACTIVATE_MAPPING(
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
from modules.mapper.pkgdwmapr import (
    PKGDWMAPR,
    PKGDWMAPRError
)
import oracledb

connection = oracledb.connect(...)

try:
    pkg = PKGDWMAPR(connection, user='ADMIN')
    
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
    
except PKGDWMAPRError as e:
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
- [ ] Use `PKGDWMAPRError` for custom errors
- [ ] Test all validations and edge cases

---

## Additional Resources

- See `PKGDWMAPR_README.md` for detailed Python documentation
- See `pkgdwmapr_example.py` for working code examples
- See `pkgdwmapr.py` for complete implementation

