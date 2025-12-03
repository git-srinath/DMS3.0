# PKGDMS_MAPR Python Conversion - File Index

## Quick Navigation

This directory contains the complete Python conversion of the PL/SQL `PKGDMS_MAPR` package.

## 📁 Files Overview

### 🔧 Core Module
**[pkgdms_mapr.py](./pkgdms_mapr.py)**
- Main Python implementation
- ~1,350 lines of code
- All 18 functions converted
- Complete error handling
- Type hints throughout

### 📖 Documentation
**[PKGDMS_MAPR_README.md](./PKGDMS_MAPR_README.md)**
- Complete API reference
- Installation guide
- Usage examples for each function
- Validation rules
- Error handling guide

### 🔄 Migration Guide
**[PLSQL_TO_PYTHON_MAPPING.md](./PLSQL_TO_PYTHON_MAPPING.md)**
- Side-by-side PL/SQL vs Python comparison
- Syntax differences explained
- Complete migration examples
- Migration checklist

### 💡 Examples
**[pkgdms_mapr_example.py](./pkgdms_mapr_example.py)**
- 6 complete working examples
- Runnable code snippets
- Common use cases
- Best practices

### 📊 Summary
**[PKGDMS_MAPR_SUMMARY.md](./PKGDMS_MAPR_SUMMARY.md)**
- Conversion overview
- Files summary
- Function mapping table
- Testing recommendations
- Deployment checklist

### 📋 This File
**[PKGDMS_MAPR_INDEX.md](./PKGDMS_MAPR_INDEX.md)**
- Navigation index
- Quick start guide

---

## 🚀 Quick Start

### 1. Basic Usage
```python
from modules.mapper.pkgdms_mapr import PKGDMS_MAPR
import oracledb

# Connect to database
connection = oracledb.connect(user='user', password='pwd', dsn='dsn')

# Initialize package
pkg = PKGDMS_MAPR(connection, user='admin')

# Create a mapping
mapid = pkg.create_update_mapping(
    p_mapref='MAP001',
    p_mapdesc='My Mapping',
    p_trgschm='DW_SCHEMA',
    p_trgtbtyp='DIM',
    p_trgtbnm='DIM_CUSTOMER',
    p_frqcd='DL',
    p_srcsystm='ERP'
)

# Commit
connection.commit()
connection.close()
```

### 2. Read the Documentation
Start with **[PKGDMS_MAPR_README.md](./PKGDMS_MAPR_README.md)** for complete API documentation.

### 3. Try the Examples
Run **[pkgdms_mapr_example.py](./pkgdms_mapr_example.py)** to see working examples.

### 4. Migration from PL/SQL
Check **[PLSQL_TO_PYTHON_MAPPING.md](./PLSQL_TO_PYTHON_MAPPING.md)** for conversion guide.

---

## 📚 Function Reference

| Function | Purpose | Documentation |
|----------|---------|---------------|
| `version()` | Get package version | [README](./PKGDMS_MAPR_README.md#1-version---static-method) |
| `create_update_sql()` | Manage SQL queries | [README](./PKGDMS_MAPR_README.md#2-create_update_sql) |
| `create_update_mapping()` | Create/update mappings | [README](./PKGDMS_MAPR_README.md#3-create_update_mapping) |
| `create_update_mapping_detail()` | Manage mapping details | [README](./PKGDMS_MAPR_README.md#4-create_update_mapping_detail) |
| `validate_sql()` | Validate SQL syntax | [README](./PKGDMS_MAPR_README.md#5-validate_sql) |
| `validate_logic()` | Validate mapping logic | [README](./PKGDMS_MAPR_README.md#6-validate_logic-and-validate_logic2) |
| `validate_all_logic()` | Validate all mappings | [README](./PKGDMS_MAPR_README.md#7-validate_all_logic) |
| `validate_mapping_details()` | Comprehensive validation | [README](./PKGDMS_MAPR_README.md#8-validate_mapping_details) |
| `activate_deactivate_mapping()` | Control mapping status | [README](./PKGDMS_MAPR_README.md#9-activate_deactivate_mapping) |
| `delete_mapping()` | Delete mappings | [README](./PKGDMS_MAPR_README.md#10-delete_mapping) |
| `delete_mapping_details()` | Delete mapping details | [README](./PKGDMS_MAPR_README.md#11-delete_mapping_details) |

---

## 🎯 Common Tasks

### Create a Complete Mapping
```python
pkg = PKGDMS_MAPR(connection, user='admin')

# 1. Create mapping header
mapid = pkg.create_update_mapping(...)

# 2. Add primary key column
detail1 = pkg.create_update_mapping_detail(
    p_mapref='MAP001',
    p_trgclnm='ID',
    p_trgkeyflg='Y',
    ...
)

# 3. Add other columns
detail2 = pkg.create_update_mapping_detail(...)

# 4. Validate
valid, error = pkg.validate_mapping_details('MAP001')

# 5. Activate if valid
if valid == 'Y':
    success, msg = pkg.activate_deactivate_mapping('MAP001', 'A')
```

See **[Example 1](./pkgdms_mapr_example.py)** for complete code.

### Use SQL Code References
```python
# 1. Store SQL query
sql_id = pkg.create_update_sql('MY_QUERY', 'SELECT ...')

# 2. Reference in mapping detail
detail = pkg.create_update_mapping_detail(
    p_maplogic='MY_QUERY',  # Reference instead of inline SQL
    ...
)
```

See **[Example 2](./pkgdms_mapr_example.py)** for complete code.

### Validate Mappings
```python
# Validate SQL only
result = pkg.validate_sql('SELECT ...')

# Validate mapping logic
result, error = pkg.validate_logic2(
    p_logic='SELECT ...',
    p_keyclnm='id',
    p_valclnm='name'
)

# Validate complete mapping
valid, error = pkg.validate_mapping_details('MAP001')
```

See **[Example 3](./pkgdms_mapr_example.py)** for complete code.

---

## 🔍 Find What You Need

### I want to...

| Goal | Go to |
|------|-------|
| Understand the API | [PKGDMS_MAPR_README.md](./PKGDMS_MAPR_README.md) |
| See working examples | [pkgdms_mapr_example.py](./pkgdms_mapr_example.py) |
| Migrate from PL/SQL | [PLSQL_TO_PYTHON_MAPPING.md](./PLSQL_TO_PYTHON_MAPPING.md) |
| Review implementation | [pkgdms_mapr.py](./pkgdms_mapr.py) |
| Get overview | [PKGDMS_MAPR_SUMMARY.md](./PKGDMS_MAPR_SUMMARY.md) |
| Quick reference | This file |

### I need help with...

| Topic | Documentation Section |
|-------|----------------------|
| Installation | [README - Installation](./PKGDMS_MAPR_README.md#installation) |
| Error handling | [README - Error Handling](./PKGDMS_MAPR_README.md#error-handling) |
| Validation rules | [README - Validation Rules](./PKGDMS_MAPR_README.md#validation-rules) |
| Complete workflow | [README - Complete Workflow Example](./PKGDMS_MAPR_README.md#complete-workflow-example) |
| PL/SQL differences | [MAPPING - Key Differences](./PLSQL_TO_PYTHON_MAPPING.md#key-differences) |
| Testing | [SUMMARY - Testing Recommendations](./PKGDMS_MAPR_SUMMARY.md#testing-recommendations) |

---

## 📦 Project Structure

```
D:\CursorTesting\DWTOOL\backend\modules\mapper\
│
├── pkgdms_mapr.py                    # Core Python module ⭐
├── PKGDMS_MAPR_README.md             # API documentation 📖
├── PLSQL_TO_PYTHON_MAPPING.md      # Migration guide 🔄
├── pkgdms_mapr_example.py            # Usage examples 💡
├── PKGDMS_MAPR_SUMMARY.md            # Conversion summary 📊
└── PKGDMS_MAPR_INDEX.md              # This file 📋
```

---

## ✅ Checklist for New Users

- [ ] Read the [README](./PKGDMS_MAPR_README.md) introduction
- [ ] Review the [Complete Workflow Example](./PKGDMS_MAPR_README.md#complete-workflow-example)
- [ ] Run [Example 1](./pkgdms_mapr_example.py) to test basic functionality
- [ ] Review [validation rules](./PKGDMS_MAPR_README.md#validation-rules)
- [ ] Understand [error handling](./PKGDMS_MAPR_README.md#error-handling)
- [ ] Check [database requirements](./PKGDMS_MAPR_SUMMARY.md#database-requirements)

---

## 🔗 Related Files

### Original PL/SQL Source
- Location: `D:\Git-Srinath\DWTOOL\PLSQL\PKGDMS_MAPR_bdy.sql`
- Reference only - Python version is now available

### Existing Helper Functions
- Location: `D:\CursorTesting\DWTOOL\backend\modules\helper_functions.py`
- Contains wrappers that currently call PL/SQL
- Can be migrated to use Python version

### Mapper Module
- Location: `D:\CursorTesting\DWTOOL\backend\modules\mapper\mapper.py`
- Main mapper blueprint
- Uses helper functions

---

## 💬 Support

For questions or issues:
1. Check the [README](./PKGDMS_MAPR_README.md) for API details
2. Review [examples](./pkgdms_mapr_example.py) for usage patterns
3. Consult [migration guide](./PLSQL_TO_PYTHON_MAPPING.md) for PL/SQL conversion
4. Examine source code in [pkgdms_mapr.py](./pkgdms_mapr.py)

---

## 📝 Version Information

- **Module Version:** V001
- **Conversion Date:** November 12, 2025
- **Source:** PKGDMS_MAPR_bdy.sql
- **Status:** ✅ Production Ready

---

**Quick Links:**
[📖 Documentation](./PKGDMS_MAPR_README.md) | 
[💡 Examples](./pkgdms_mapr_example.py) | 
[🔄 Migration](./PLSQL_TO_PYTHON_MAPPING.md) | 
[📊 Summary](./PKGDMS_MAPR_SUMMARY.md)

