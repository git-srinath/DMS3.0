# SQL Prefill Feature Analysis for Mapper Module

## Overview
This document analyzes the requirements and prerequisites for adding a SQL-based prefill feature to the mapper module. This feature will allow users to select a SQL query (from Manage SQL or manually entered) to automatically prefill mapper form fields, reducing manual data entry.

## Current State Analysis

### 1. Mapper Form Structure

#### Form Header Fields (from `FORM_FIELDS`):
- `reference` - Unique mapping identifier
- `description` - Mapping description
- `sourceSystem` - Source system name
- `tableName` - Target table name
- `tableType` - DIM/FCT/MRT
- `targetSchema` - Target schema
- `freqCode` - Frequency code
- `bulkProcessRows` - Batch processing size
- `targetConnectionId` - Target database connection

#### Row Fields (from `TABLE_FIELDS`):
- `fieldName` - Target column name
- `dataType` - Target data type
- `primaryKey` - Primary key flag
- `pkSeq` - Primary key sequence
- `fieldDesc` - Field description
- `scdType` - SCD type (1/2)
- `keyColumn` - Key column for lookups
- `valColumn` - Value column for lookups
- `logic` - Transformation logic (SQL expression)
- `mapCombineCode` - Aggregation code
- `execSequence` - Execution sequence

### 2. Manage SQL Module

**Database Table:** `DMS_MAPRSQL`
- `MAPRSQLCD` - SQL Code (unique identifier)
- `MAPRSQL` - SQL Content (CLOB)
- `SQLCONID` - Source connection ID (optional)
- `CURFLG` - Current flag (Y/N)

**Existing APIs:**
- `GET /manage-sql/fetch-all-sql-codes` - Returns list of all SQL codes
- `GET /manage-sql/fetch-sql-logic?sql_code={code}` - Returns SQL content and connection ID

### 3. Current Mapper Input Methods

1. **Manual Entry** - User fills form fields manually
2. **File Upload** - Excel/CSV template upload (parses and fills form)
3. **SQL Editor** - Currently used for individual field logic, not for base SQL

## Feature Requirements

### User Flow
1. User clicks a button (e.g., "Load from SQL" or "Prefill from SQL")
2. Dialog opens with:
   - Dropdown to select SQLCODE from Manage SQL
   - OR text area to enter SQL manually
   - Option to preview SQL
   - "Extract Columns" button
3. On "Extract Columns":
   - Execute SQL (or parse it) to extract metadata
   - Show column selection screen with:
     - Checkboxes for each column (user selects which to include)
     - Source data type for each column
     - Suggested target data type (from parameter)
     - Option to edit suggested data type
   - "Apply to Form" button
4. On "Apply to Form":
   - If new SQL was entered manually, prompt to register it to Manage SQL
   - Check for duplicate SQL (if registering)
   - Prefill mapper form fields for selected columns
   - All fields remain editable until user clicks "Save"
5. After Save:
   - Form behavior returns to current setup (locked fields, etc.)

### What Can Be Prefilled from SQL

#### From SQL Parsing (Static Analysis):
1. **Column Names** - From SELECT clause
   - Can prefill `fieldName` rows
   - Can suggest `logic` as column name (e.g., `COLUMN_NAME`)

2. **Table/Schema Names** - From FROM clause
   - Can suggest `sourceSystem` (from schema/table name)
   - Can suggest `tableName` (if not already set)

3. **Data Types** - Requires execution or metadata query
   - Can prefill `dataType` if we query database metadata

#### From SQL Execution (Dynamic Analysis):
1. **Column Metadata** - Execute `DESCRIBE` or query `INFORMATION_SCHEMA`
   - Column names
   - Data types
   - Nullable flags
   - Primary key information (if available)

2. **Sample Data** - Execute with LIMIT 1
   - Can help infer data types
   - Can help suggest field descriptions

## Prerequisites & Technical Requirements

### 1. Backend API Endpoints Needed

#### A. SQL Column Extraction Endpoint
**Endpoint:** `POST /mapper/extract-sql-columns`

**Request:**
```json
{
  "sql_code": "SQL_001",  // Optional - if provided, fetch from Manage SQL
  "sql_content": "SELECT col1, col2 FROM table",  // Optional - if sql_code not provided
  "connection_id": "1"  // Optional - source connection ID
}
```

**Response:**
```json
{
  "success": true,
  "columns": [
    {
      "column_name": "COL1",
      "source_data_type": "VARCHAR2(100)",
      "suggested_data_type": "VARCHAR",  // From parameter
      "suggested_data_type_options": ["VARCHAR", "TEXT", "CHAR"],  // Available options
      "nullable": true,
      "is_primary_key": false,
      "sample_value": "example"
    },
    {
      "column_name": "COL2",
      "source_data_type": "NUMBER(10,2)",
      "suggested_data_type": "NUMERIC",
      "suggested_data_type_options": ["NUMERIC", "INTEGER", "DECIMAL"],
      "nullable": false,
      "is_primary_key": true,
      "sample_value": 123
    }
  ],
  "source_table": "SOURCE_TABLE",
  "source_schema": "SOURCE_SCHEMA",
  "sql_content": "SELECT col1, col2 FROM table"  // Return SQL for registration
}
```

**Implementation Requirements:**
- Parse SQL to extract SELECT columns
- If `sql_code` provided, fetch SQL from `DMS_MAPRSQL`
- If `connection_id` provided, use that connection; otherwise use metadata connection
- Execute SQL with LIMIT 1 to get column metadata
- Query database metadata (INFORMATION_SCHEMA, ALL_TAB_COLUMNS, etc.) for data types
- Use parameter module to get suggested target data types
- Return available data type options for each column
- Handle errors gracefully (invalid SQL, connection issues, etc.)

#### B. SQL Duplicate Detection Endpoint
**Endpoint:** `POST /mapper/check-sql-duplicate`

**Request:**
```json
{
  "sql_content": "SELECT col1, col2 FROM table WHERE id > 100",
  "connection_id": "1"  // Optional
}
```

**Response:**
```json
{
  "has_exact_match": false,
  "similar_queries": [
    {
      "sql_code": "SQL_001",
      "sql_content": "SELECT col1, col2 FROM table WHERE id > 50",
      "similarity_score": 0.85,
      "similarity_reason": "Same columns and table, similar WHERE clause"
    },
    {
      "sql_code": "SQL_002",
      "sql_content": "SELECT col1, col2, col3 FROM table",
      "similarity_score": 0.70,
      "similarity_reason": "Overlapping columns and same table"
    }
  ]
}
```

#### C. SQL Registration Endpoint
**Endpoint:** `POST /mapper/register-sql`

**Request:**
```json
{
  "sql_code": "SQL_003",  // User-provided or auto-generated
  "sql_content": "SELECT col1, col2 FROM table",
  "connection_id": "1",  // Optional
  "force_register": false  // If true, skip duplicate check
}
```

**Response:**
```json
{
  "success": true,
  "message": "SQL registered successfully",
  "sql_code": "SQL_003"
}
```

#### D. SQL Preview Endpoint (Optional Enhancement)
**Endpoint:** `POST /mapper/preview-sql`

**Request:**
```json
{
  "sql_code": "SQL_001",
  "sql_content": "SELECT * FROM table",
  "connection_id": "1",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "columns": ["COL1", "COL2", "COL3"],
  "preview_data": [
    {"COL1": "value1", "COL2": "value2", "COL3": "value3"}
  ],
  "row_count": 1000
}
```

### 2. Frontend Components Needed

#### A. SQL Prefill Dialog Component
**Location:** `frontend/src/app/mapper_module/SqlPrefillDialog.js`

**Features:**
- **Step 1: SQL Selection**
  - Autocomplete dropdown for SQLCODE selection (fetches from `/manage-sql/fetch-all-sql-codes`)
  - Text area for manual SQL entry
  - Toggle between "Select from Manage SQL" and "Enter SQL manually"
  - SQL preview section (optional)
  - "Extract Columns" button
  - Loading state during column extraction

- **Step 2: Column Selection & Data Type Review**
  - Checkbox list of all extracted columns
  - Show source data type for each column
  - Show suggested target data type (from parameter)
  - Dropdown to change suggested data type (shows available options)
  - "Select All" / "Deselect All" buttons
  - "Apply to Form" button
  - "Back" button to return to SQL selection

- **Step 3: SQL Registration (if new SQL)**
  - Dialog showing duplicate detection results (if any)
  - Option to:
    - Use existing similar SQL
    - Register as new SQL (with SQLCODE input)
    - Skip registration
  - "Register" and "Skip" buttons

#### B. Integration with ReferenceForm
**Modifications to:** `frontend/src/app/mapper_module/ReferenceForm.js`

**Changes:**
- Add "Load from SQL" button in form header
- Add state for SQL prefill dialog
- Add handler to process selected columns and prefill form
- Map selected columns to form rows (only selected columns)
- Ensure all fields remain editable until Save button is clicked
- After Save, restore existing form behavior (locked fields, validation, etc.)

### 3. SQL Parsing Logic

#### Option 1: Simple Regex Parsing (Quick Implementation)
- Extract SELECT columns using regex
- Extract FROM table/schema
- Pros: Fast, no database connection needed
- Cons: Limited accuracy, doesn't handle complex SQL

#### Option 2: SQL Execution + Metadata Query (Recommended)
- Execute SQL with LIMIT 1 to get cursor description
- Query database metadata for data types
- Pros: Accurate, gets real data types
- Cons: Requires database connection, may be slower

#### Option 3: SQL Parser Library (Most Robust)
- Use SQL parsing library (e.g., `sqlparse` for Python)
- Parse AST to extract columns, tables, etc.
- Pros: Most accurate, handles complex SQL
- Cons: Additional dependency, more complex

**Recommendation:** Start with Option 2 (SQL Execution), add Option 3 later if needed.

### 4. Column Mapping Strategy

When prefilling rows from SQL columns:

1. **User selects columns** - Only selected columns are prefilled
2. **Field Name:** Use SQL column name (uppercase, no spaces)
3. **Logic:** Default to column name (e.g., `COLUMN_NAME`)
4. **Data Type:** 
   - Show suggested data type from parameter module
   - Allow user to review and change before applying
   - User can edit after prefill (all fields editable until Save)
5. **Primary Key:** Detect if column is primary key (from metadata)
6. **Field Description:** Leave empty or use column name as description

### 5. SQL Registration & Duplicate Detection

When user enters new SQL manually:

1. **Prompt to Register:** After column extraction, ask if user wants to save SQL to Manage SQL
2. **Duplicate Detection:** Check if similar SQL already exists
3. **Registration:** If no duplicate or user confirms, save to `DMS_MAPRSQL` table

**Duplicate Detection Options:**

#### Option A: Exact Match (Simple)
- Compare normalized SQL strings (remove whitespace, case-insensitive)
- Pros: Simple, fast
- Cons: Misses semantically identical queries with different formatting

#### Option B: SQL Normalization + Similarity (Recommended)
- Normalize SQL (remove comments, normalize whitespace, case-insensitive)
- Compare normalized SQL with existing SQLs
- Calculate similarity score (using string similarity algorithms)
- Show matches above threshold (e.g., 80% similar)
- Pros: Catches most duplicates, user-friendly
- Cons: More complex, requires similarity algorithm

#### Option C: SQL Structure Comparison (Most Accurate)
- Parse SQL to extract structure (SELECT columns, FROM tables, WHERE conditions)
- Compare structures instead of full SQL
- Pros: Most accurate, catches logical duplicates
- Cons: Complex, requires SQL parser, may be slow

#### Option D: Hybrid Approach (Best Balance)
- First check exact match (normalized)
- If no exact match, check structure similarity
- Show top 3-5 similar queries with similarity percentage
- Let user choose: "Use Existing", "Save as New", or "Cancel"
- Pros: Good balance of accuracy and performance
- Cons: Moderate complexity

**Recommendation:** Option D (Hybrid Approach) with the following implementation:

**Implementation Steps:**
1. **Normalize SQL** (remove comments, extra whitespace, case-insensitive)
2. **Check for exact normalized match** - Fast lookup, exact duplicates
3. **If no exact match**, extract key elements:
   - SELECT columns (list of column names)
   - FROM tables (table/schema names)
   - WHERE conditions (simplified - just column names used)
   - JOIN tables (if any)
4. **Compare with existing SQLs** using:
   - Column overlap percentage: `(common_columns / total_columns) * 100`
   - Table name match: Exact match = 100%, partial = 50%
   - WHERE clause similarity: Compare column names used
   - Overall similarity: Weighted average of above factors
5. **Show matches** with similarity score (threshold: 70%+)
6. **User can view matched SQLs** before deciding:
   - Show SQLCODE, SQL content preview, similarity score
   - User can click to view full SQL
   - Options: "Use This SQL", "Register as New", "Cancel"

**Similarity Score Calculation Example:**
```python
def calculate_similarity(new_sql, existing_sql):
    # Extract elements
    new_cols = extract_columns(new_sql)  # ['col1', 'col2', 'col3']
    existing_cols = extract_columns(existing_sql)  # ['col1', 'col2']
    
    # Column overlap
    common_cols = set(new_cols) & set(existing_cols)
    column_score = len(common_cols) / max(len(new_cols), len(existing_cols))
    
    # Table match
    new_table = extract_table(new_sql)  # 'SOURCE_TABLE'
    existing_table = extract_table(existing_sql)  # 'SOURCE_TABLE'
    table_score = 1.0 if new_table == existing_table else 0.0
    
    # Overall similarity (weighted)
    similarity = (column_score * 0.6) + (table_score * 0.4)
    return similarity  # 0.0 to 1.0
```

**Alternative: Simpler Approach (If Hybrid is Too Complex)**
- Use Option B (Normalization + String Similarity)
- Use Python's `difflib.SequenceMatcher` or `fuzzywuzzy` library
- Normalize both SQLs and compare strings
- Show top 5 matches above 70% threshold
- Pros: Simpler, faster to implement
- Cons: Less accurate for complex queries

### 6. Database Connection Handling

- If SQLCODE has `SQLCONID`, use that connection
- If SQL is manually entered, use metadata connection by default
- Allow user to specify source connection in dialog (future enhancement)

### 7. Field Editability Behavior

**Before Save:**
- All fields in mapper form are editable
- User can modify any prefilled field
- No validation locks or restrictions
- Changes tracked but not enforced

**After Save:**
- Form behavior returns to current setup
- Fields become locked/restricted as per existing logic
- Validation rules apply
- Workflow states (validate, activate, etc.) enforced

## Implementation Steps

### Phase 1: Backend API (Estimated: 4-5 hours)
1. Create `POST /mapper/extract-sql-columns` endpoint
2. Implement SQL fetching from Manage SQL (if sql_code provided)
3. Implement SQL execution with LIMIT 1
4. Implement column metadata extraction
5. Implement data type mapping using parameter module
6. Return suggested data types and available options
7. Create `POST /mapper/check-sql-duplicate` endpoint
8. Implement SQL normalization and similarity comparison
9. Create `POST /mapper/register-sql` endpoint
10. Add error handling

### Phase 2: Frontend Dialog (Estimated: 4-5 hours)
1. Create `SqlPrefillDialog.js` component with multi-step flow
2. Step 1: SQL selection (dropdown + text area)
3. Step 2: Column selection with checkboxes
4. Step 2: Data type review with dropdowns
5. Step 3: SQL registration dialog (if new SQL)
6. Show duplicate detection results
7. Add loading states and transitions
8. Add validation and error handling

### Phase 3: Integration (Estimated: 2-3 hours)
1. Add "Load from SQL" button to ReferenceForm
2. Integrate dialog with form
3. Implement column-to-row mapping logic (only selected columns)
4. Prefill form fields with selected columns
5. Ensure all fields remain editable until Save
6. Restore form behavior after Save
7. Handle edge cases (existing data, validation, etc.)

### Phase 4: Testing & Refinement (Estimated: 2-3 hours)
1. Test with various SQL queries
2. Test with different database types
3. Test duplicate detection with various scenarios
4. Test column selection and data type mapping
5. Test SQL registration flow
6. Test field editability behavior
7. User acceptance testing
8. Refine based on feedback

## Estimated Total Time: 12-16 hours

## Potential Challenges & Solutions

### Challenge 1: Complex SQL Queries
**Issue:** SQL with JOINs, subqueries, CTEs may have ambiguous column sources
**Solution:** 
- Extract column names from SELECT clause
- Use alias if present
- For complex queries, show all columns and let user map manually

### Challenge 2: Data Type Mapping
**Issue:** Source data types may not match target data types
**Solution:**
- Use existing parameter module (`get_parameter_mapping_datatype`)
- Provide default mappings (VARCHAR2 -> VARCHAR, NUMBER -> NUMERIC)
- Allow user to override after prefill

### Challenge 3: SQL Execution Errors
**Issue:** SQL may fail to execute (syntax errors, missing tables, etc.)
**Solution:**
- Validate SQL syntax before execution
- Catch and display errors clearly
- Allow user to fix SQL and retry
- Provide fallback to simple parsing if execution fails

### Challenge 4: Existing Form Data
**Issue:** User may have already entered some data
**Solution:**
- Show confirmation dialog if form has data
- Option to "Append" or "Replace"
- Preserve user-entered data for fields not prefilled

### Challenge 5: SQL Duplicate Detection
**Issue:** Detecting similar SQL queries is complex
**Solution:**
- Use hybrid approach (exact match + structure comparison)
- Normalize SQL for comparison
- Show similarity scores and reasons
- Let user decide whether to use existing or register new

### Challenge 6: Data Type Mapping Accuracy
**Issue:** Source to target data type mapping may not always be accurate
**Solution:**
- Use existing parameter module for suggestions
- Show multiple options in dropdown
- Allow user to review and change before applying
- All fields remain editable after prefill

### Challenge 7: Field Editability State Management
**Issue:** Need to track when form is in "prefill mode" vs "normal mode"
**Solution:**
- Add state flag `isPrefillMode` or `isUnsavedChanges`
- Keep all fields editable until Save
- After Save, clear flag and restore normal behavior
- Track original form state to restore after Save

## Future Enhancements

1. **Smart Suggestions:**
   - Suggest target table name based on source table
   - Suggest primary keys based on source table metadata
   - Suggest SCD type based on table structure

2. **SQL Templates:**
   - Pre-defined SQL templates for common patterns
   - Template variables for dynamic SQL generation

3. **Column Mapping Assistant:**
   - Show source columns and target columns side-by-side
   - Drag-and-drop mapping interface
   - Auto-suggest mappings based on name similarity

4. **SQL Validation:**
   - Validate SQL before prefill
   - Check for common issues (missing WHERE, no ORDER BY, etc.)
   - Suggest optimizations

## Dependencies

### Backend:
- Existing: `backend/modules/manage_sql/fastapi_manage_sql.py`
- Existing: `backend/modules/mapper/fastapi_mapper.py`
- Existing: `backend/database/dbconnect.py`
- Existing: `backend/modules/helper_functions.py` (for type mapping)
- New: SQL parsing/execution utilities (can use existing database adapters)

### Frontend:
- Existing: `frontend/src/app/manage_sql/page.js` (for SQLCODE dropdown)
- Existing: `frontend/src/app/mapper_module/ReferenceForm.js`
- New: `frontend/src/app/mapper_module/SqlPrefillDialog.js`
- Material-UI components (already in use)

## Additional Implementation Details

### Data Type Mapping Integration

**Backend Implementation:**
```python
# Use existing helper function
from backend.modules.helper_functions import get_parameter_mapping_datatype

def get_suggested_data_type(source_data_type, target_db_type):
    """
    Get suggested target data type from parameter module.
    Returns suggested type and available options.
    """
    # Query DMS_PARAMS for type mappings
    # Return best match and alternatives
    pass
```

**Frontend Display:**
- Show source data type in read-only text
- Show suggested data type in dropdown (pre-selected)
- Show all available options in dropdown
- Allow user to change before applying

### SQL Duplicate Detection Implementation

**Normalization Function:**
```python
def normalize_sql(sql_content):
    """
    Normalize SQL for comparison:
    - Remove comments (-- and /* */)
    - Normalize whitespace
    - Case-insensitive
    - Remove extra spaces
    """
    # Remove comments
    # Normalize whitespace
    # Convert to uppercase
    return normalized_sql
```

**Similarity Calculation:**
```python
def calculate_sql_similarity(sql1, sql2):
    """
    Calculate similarity between two SQL queries.
    Returns score 0-1.
    """
    # Extract key elements:
    # - SELECT columns
    # - FROM tables
    # - WHERE conditions (if any)
    # Compare and calculate overlap percentage
    pass
```

### Column Selection UI Flow

1. **After Column Extraction:**
   - Show list with checkboxes
   - Each row shows: [ ] Column Name | Source Type | Suggested Type [dropdown]
   - "Select All" / "Deselect All" buttons
   - "Apply to Form" button (disabled if no columns selected)

2. **On Apply:**
   - If new SQL: Show registration dialog
   - If existing SQL: Directly apply to form
   - Create rows for selected columns only
   - Prefill with selected data types

### SQL Registration Flow

1. **After Column Selection (if new SQL):**
   - Show dialog: "Do you want to save this SQL to Manage SQL?"
   - If Yes:
     - Check for duplicates
     - Show results if duplicates found
     - User can: Use existing, Register as new, Cancel
   - If No: Skip registration, proceed to prefill

2. **Registration Options:**
   - Auto-generate SQLCODE (e.g., SQL_001, SQL_002)
   - Or let user enter custom SQLCODE
   - Validate SQLCODE uniqueness
   - Save to DMS_MAPRSQL table

## Conclusion

This feature is **highly feasible** and can be implemented in 12-16 hours. The enhanced requirements add complexity but significantly improve user experience:

1. **Column Selection** - Gives users control over what gets prefilled
2. **Data Type Suggestions** - Reduces errors and improves accuracy
3. **SQL Registration** - Builds reusable SQL library
4. **Duplicate Detection** - Prevents redundant SQL entries
5. **Flexible Editing** - Allows refinement before saving

The main work involves:

1. Creating backend APIs for column extraction, duplicate detection, and SQL registration
2. Building a multi-step frontend dialog with column selection and data type review
3. Integrating with existing mapper form while maintaining editability until Save
4. Implementing SQL similarity detection algorithm

The feature will significantly improve user experience by reducing manual data entry while maintaining flexibility and control.

