# F-String Format Specifier Fix

## Issue
When adding the 3rd connection parameter (source_connection) to the `execute_job` function, dictionary literals containing `MAPREF` and `prcid` inside f-strings were causing Python to throw:
```
ValueError: Invalid format specifier ' MAPREF, 'prcid': prcid' for object of type 'str'
```

## Root Cause
Python's f-string parser was trying to evaluate `MAPREF` and `prcid` as format specifiers when they appeared in single-line dictionary literals like:
```python
{{'mapref': MAPREF, 'prcid': prcid}}
```

Even though `{{` and `}}` escape the braces, Python's f-string parser was still scanning the content and attempting to interpret `MAPREF` and `prcid` as format specifiers.

## Solution
Changed dictionary literals from single-line to multi-line format, matching the working pattern used elsewhere in the file (e.g., lines 270-276).

### Fixed Locations:

1. **Line 488-491** (in `check_stop_request` function):
   - **Before**: `{{'mapref': MAPREF, 'prcid': prcid}}`
   - **After**: 
     ```python
     {{
         'mapref': MAPREF,
         'prcid': prcid
     }}
     ```

2. **Line 889-891** (in stop request processing):
   - **Before**: `{'mapref': MAPREF}`
   - **After**:
     ```python
     {{
         'mapref': MAPREF
     }}
     ```

## Why This Works
The multi-line format with proper `{{` and `}}` escaping prevents Python's f-string parser from treating `MAPREF` and `prcid` as format specifiers. The parser correctly treats them as literal variable names that will appear in the generated code.

## Pattern to Follow
When using dictionary literals with variable names (like `MAPREF`, `prcid`, `JOBID`) inside f-strings in code generation:
- ✅ **Use multi-line format**: Split dictionary across multiple lines with `{{` and `}}`
- ❌ **Avoid single-line format**: Single-line dictionaries can cause f-string parser issues

## Example of Correct Pattern
```python
code_parts.append(f'''
    metadata_cursor.execute("""
        SELECT * FROM table
        WHERE col = :val
    """, {{
        'mapref': MAPREF,
        'prcid': prcid
    }})
''')
```

## Date Fixed
2025-11-19

## Files Modified
- `backend/modules/jobs/pkgdwjob_create_job_flow.py` (lines 488-491, 889-891)

