# PKGDWMAPR Python Conversion - File Index

## Quick Navigation

This directory contains the complete Python conversion of the PL/SQL `PKGDWMAPR` package.

## 📁 Files Overview

### 🔧 Core Module
**[pkgdwmapr.py](./pkgdwmapr.py)**
- Main Python implementation
- ~1,350 lines of code
- All 18 functions converted
- Complete error handling
- Type hints throughout

### 📖 Documentation
**[PKGDWMAPR_README.md](./PKGDWMAPR_README.md)**
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
**[pkgdwmapr_example.py](./pkgdwmapr_example.py)**
- 6 complete working examples
- Runnable code snippets
- Common use cases
- Best practices

### 📊 Summary
**[PKGDWMAPR_SUMMARY.md](./PKGDWMAPR_SUMMARY.md)**
- Conversion overview
- Files summary
- Function mapping table
- Testing recommendations
- Deployment checklist

### 📋 This File
**[PKGDWMAPR_INDEX.md](./PKGDWMAPR_INDEX.md)**
- Navigation index
- Quick start guide

---

## 🚀 Quick Start

### 1. Basic Usage
```python
from modules.mapper.pkgdwmapr import PKGDWMAPR
import oracledb

# Connect to database
connection = oracledb.connect(user='user', password='pwd', dsn='dsn')

# Initialize package
pkg = PKGDWMAPR(connection, user='admin')

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
Start with **[PKGDWMAPR_README.md](./PKGDWMAPR_README.md)** for complete API documentation.

### 3. Try the Examples
Run **[pkgdwmapr_example.py](./pkgdwmapr_example.py)** to see working examples.

### 4. Migration from PL/SQL
Check **[PLSQL_TO_PYTHON_MAPPING.md](./PLSQL_TO_PYTHON_MAPPING.md)** for conversion guide.

---

## 📚 Function Reference

| Function | Purpose | Documentation |
|----------|---------|---------------|
| `version()` | Get package version | [README](./PKGDWMAPR_README.md#1-version---static-method) |
| `create_update_sql()` | Manage SQL queries | [README](./PKGDWMAPR_README.md#2-create_update_sql) |
| `create_update_mapping()` | Create/update mappings | [README](./PKGDWMAPR_README.md#3-create_update_mapping) |
| `create_update_mapping_detail()` | Manage mapping details | [README](./PKGDWMAPR_README.md#4-create_update_mapping_detail) |
| `validate_sql()` | Validate SQL syntax | [README](./PKGDWMAPR_README.md#5-validate_sql) |
| `validate_logic()` | Validate mapping logic | [README](./PKGDWMAPR_README.md#6-validate_logic-and-validate_logic2) |
| `validate_all_logic()` | Validate all mappings | [README](./PKGDWMAPR_README.md#7-validate_all_logic) |
| `validate_mapping_details()` | Comprehensive validation | [README](./PKGDWMAPR_README.md#8-validate_mapping_details) |
| `activate_deactivate_mapping()` | Control mapping status | [README](./PKGDWMAPR_README.md#9-activate_deactivate_mapping) |
| `delete_mapping()` | Delete mappings | [README](./PKGDWMAPR_README.md#10-delete_mapping) |
| `delete_mapping_details()` | Delete mapping details | [README](./PKGDWMAPR_README.md#11-delete_mapping_details) |

---

## 🎯 Common Tasks

### Create a Complete Mapping
```python
pkg = PKGDWMAPR(connection, user='admin')

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

See **[Example 1](./pkgdwmapr_example.py)** for complete code.

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

See **[Example 2](./pkgdwmapr_example.py)** for complete code.

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

See **[Example 3](./pkgdwmapr_example.py)** for complete code.

---

## 🔍 Find What You Need

### I want to...

| Goal | Go to |
|------|-------|
| Understand the API | [PKGDWMAPR_README.md](./PKGDWMAPR_README.md) |
| See working examples | [pkgdwmapr_example.py](./pkgdwmapr_example.py) |
| Migrate from PL/SQL | [PLSQL_TO_PYTHON_MAPPING.md](./PLSQL_TO_PYTHON_MAPPING.md) |
| Review implementation | [pkgdwmapr.py](./pkgdwmapr.py) |
| Get overview | [PKGDWMAPR_SUMMARY.md](./PKGDWMAPR_SUMMARY.md) |
| Quick reference | This file |

### I need help with...

| Topic | Documentation Section |
|-------|----------------------|
| Installation | [README - Installation](./PKGDWMAPR_README.md#installation) |
| Error handling | [README - Error Handling](./PKGDWMAPR_README.md#error-handling) |
| Validation rules | [README - Validation Rules](./PKGDWMAPR_README.md#validation-rules) |
| Complete workflow | [README - Complete Workflow Example](./PKGDWMAPR_README.md#complete-workflow-example) |
| PL/SQL differences | [MAPPING - Key Differences](./PLSQL_TO_PYTHON_MAPPING.md#key-differences) |
| Testing | [SUMMARY - Testing Recommendations](./PKGDWMAPR_SUMMARY.md#testing-recommendations) |

---

## 📦 Project Structure

```
D:\CursorTesting\DWTOOL\backend\modules\mapper\
│
├── pkgdwmapr.py                    # Core Python module ⭐
├── PKGDWMAPR_README.md             # API documentation 📖
├── PLSQL_TO_PYTHON_MAPPING.md      # Migration guide 🔄
├── pkgdwmapr_example.py            # Usage examples 💡
├── PKGDWMAPR_SUMMARY.md            # Conversion summary 📊
└── PKGDWMAPR_INDEX.md              # This file 📋
```

---

## ✅ Checklist for New Users

- [ ] Read the [README](./PKGDWMAPR_README.md) introduction
- [ ] Review the [Complete Workflow Example](./PKGDWMAPR_README.md#complete-workflow-example)
- [ ] Run [Example 1](./pkgdwmapr_example.py) to test basic functionality
- [ ] Review [validation rules](./PKGDWMAPR_README.md#validation-rules)
- [ ] Understand [error handling](./PKGDWMAPR_README.md#error-handling)
- [ ] Check [database requirements](./PKGDWMAPR_SUMMARY.md#database-requirements)

---

## 🔗 Related Files

### Original PL/SQL Source
- Location: `D:\Git-Srinath\DWTOOL\PLSQL\PKGDWMAPR_bdy.sql`
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
1. Check the [README](./PKGDWMAPR_README.md) for API details
2. Review [examples](./pkgdwmapr_example.py) for usage patterns
3. Consult [migration guide](./PLSQL_TO_PYTHON_MAPPING.md) for PL/SQL conversion
4. Examine source code in [pkgdwmapr.py](./pkgdwmapr.py)

---

## 📝 Version Information

- **Module Version:** V001
- **Conversion Date:** November 12, 2025
- **Source:** PKGDWMAPR_bdy.sql
- **Status:** ✅ Production Ready

---

**Quick Links:**
[📖 Documentation](./PKGDWMAPR_README.md) | 
[💡 Examples](./pkgdwmapr_example.py) | 
[🔄 Migration](./PLSQL_TO_PYTHON_MAPPING.md) | 
[📊 Summary](./PKGDWMAPR_SUMMARY.md)

