# Table Restructure Analysis for File Upload Module

## Problem Statement

When loading files, users may:
1. Assign wrong data types to columns during initial setup
2. Want to change column names after the table is created
3. Need to add new columns to existing tables

**Current Issue:** The `create_table_if_not_exists()` function only creates tables if they don't exist. Once a table is created, any changes to column mappings in `DMS_FLUPLDDTL` are ignored during subsequent loads.

## Current Flow

1. User configures file upload with column mappings (`DMS_FLUPLDDTL`)
2. On first load, table is created based on mappings
3. On subsequent loads, if table exists, creation is skipped (line 37-40 in `table_creator.py`)
4. If user updates column mappings (e.g., changes data type), the existing table structure is not updated

## Proposed Solution

### Option 1: Automatic Table Sync (Recommended)

Enhance `create_table_if_not_exists()` to:
1. **Check if table exists** (current behavior)
2. **If table exists, compare existing structure with desired mappings**
3. **Generate ALTER TABLE statements** for:
   - ✅ Adding missing columns (SAFE)
   - ⚠️ Modifying column data types (WITH WARNINGS - may cause data loss)
   - ❌ Column renaming (COMPLEX - requires data migration)

**Implementation Strategy:**
- Add a new function `sync_table_structure()` that:
  - Queries existing table columns from `information_schema` (PostgreSQL) or `user_tab_columns` (Oracle)
  - Compares with desired column mappings
  - Generates ALTER TABLE statements
  - Returns summary of changes

### Option 2: Manual Restructure Option

Add a UI button/option to "Restructure Table" that:
1. Shows diff between current table structure and desired mappings
2. Asks user to confirm changes
3. Executes ALTER TABLE statements

### Option 3: Force Recreate (Not Recommended)

Add a "Drop and Recreate Table" option - **RISKY** as it deletes existing data.

---

## Recommended Implementation (Option 1 + Option 2 Hybrid)

### Phase 1: Backend - Table Structure Comparison

Create new functions in `table_creator.py`:

1. **`get_existing_table_structure()`**
   - Query existing columns and data types
   - Return: `Dict[str, Dict]` mapping column names to their properties

2. **`compare_table_structure()`**
   - Compare existing structure vs desired mappings
   - Return: `TableStructureDiff` object with:
     - `columns_to_add: List[ColumnDef]`
     - `columns_to_modify: List[ColumnModification]`
     - `columns_unchanged: List[str]`

3. **`generate_alter_table_statements()`**
   - Generate ALTER TABLE SQL for:
     - `ADD COLUMN` for missing columns
     - `ALTER COLUMN TYPE` for type changes (with compatibility checks)
   - Handle database-specific syntax (PostgreSQL vs Oracle)

4. **`sync_table_structure()`**
   - Main function that orchestrates the above
   - Executes ALTER TABLE statements
   - Returns summary of changes

### Phase 2: Modify `create_table_if_not_exists()`

Update to call `sync_table_structure()` when table exists:

```python
def create_table_if_not_exists(...):
    table_exists = _check_table_exists(...)
    if table_exists:
        # NEW: Sync table structure instead of just skipping
        sync_result = sync_table_structure(
            connection, schema, table, column_mappings, metadata_connection
        )
        return sync_result  # Returns dict with changes made
    else:
        # Create new table (existing logic)
        ...
```

### Phase 3: API Endpoint

Add endpoint to preview/execute table restructure:
- `GET /file-upload/preview-table-structure?flupldref=XXX`
  - Returns diff without executing
- `POST /file-upload/sync-table-structure`
  - Executes the sync

### Phase 4: Frontend UI

Add to UploadForm or new modal:
- Show table structure comparison
- Preview ALTER TABLE statements
- Confirmation dialog for type changes (warn about data loss)
- Execute sync button

---

## Detailed Implementation Plan

### 1. Backend Functions

#### `get_existing_table_structure()`

```python
def get_existing_table_structure(
    cursor, db_type: str, schema: str, table: str
) -> Dict[str, Dict[str, Any]]:
    """
    Get existing table column structure.
    
    Returns:
        {
            'COLUMN_NAME': {
                'data_type': 'VARCHAR2(100)',
                'nullable': True,
                'data_length': 100,
                'data_precision': None,
                'data_scale': None
            },
            ...
        }
    """
```

**PostgreSQL Query:**
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale,
    is_nullable
FROM information_schema.columns
WHERE table_schema = %s AND table_name = %s
ORDER BY ordinal_position
```

**Oracle Query:**
```sql
SELECT 
    column_name,
    data_type,
    data_length,
    data_precision,
    data_scale,
    nullable
FROM all_tab_columns
WHERE owner = :owner AND table_name = :table
ORDER BY column_id
```

#### `compare_table_structure()`

```python
def compare_table_structure(
    existing_columns: Dict[str, Dict],
    desired_mappings: List[Dict],
    db_type: str,
    metadata_connection
) -> TableStructureDiff:
    """
    Compare existing table structure with desired column mappings.
    
    Returns TableStructureDiff with:
    - columns_to_add: Columns in mappings but not in table
    - columns_to_modify: Columns with different data types
    - columns_unchanged: Columns that match
    """
```

#### `is_type_compatible()`

```python
def is_type_compatible(
    old_type: str, 
    new_type: str, 
    db_type: str
) -> Tuple[bool, str]:
    """
    Check if data type change is safe.
    
    Returns:
        (is_compatible, warning_message)
        
    Examples:
    - VARCHAR2(50) -> VARCHAR2(100): Compatible (size increase)
    - VARCHAR2(100) -> VARCHAR2(50): Warning (size decrease - may truncate)
    - VARCHAR2 -> NUMBER: Incompatible (requires data migration)
    - NUMBER(10) -> NUMBER(19): Compatible (precision increase)
    """
```

#### `generate_alter_table_statements()`

```python
def generate_alter_table_statements(
    diff: TableStructureDiff,
    db_type: str,
    schema: str,
    table: str,
    metadata_connection
) -> List[str]:
    """
    Generate ALTER TABLE statements.
    
    Returns list of SQL statements:
    - ALTER TABLE ... ADD COLUMN ...
    - ALTER TABLE ... ALTER COLUMN ... TYPE ...
    """
```

### 2. Safe Operations

**Always Safe:**
- ✅ Adding new columns
- ✅ Adding columns with DEFAULT values

**Safe with Warnings:**
- ⚠️ Increasing VARCHAR size (VARCHAR(50) → VARCHAR(100))
- ⚠️ Increasing NUMBER precision
- ⚠️ Changing NULL to NOT NULL (if no NULL values exist)

**Risky (Requires Data Migration):**
- ❌ Decreasing VARCHAR size (may truncate)
- ❌ Changing VARCHAR to NUMBER (requires conversion)
- ❌ Changing NUMBER to VARCHAR
- ❌ Changing NULL to NOT NULL (if NULL values exist)
- ❌ Dropping columns (data loss)

**Not Supported (Too Complex):**
- ❌ Column renaming (requires data copy)
- ❌ Changing column order
- ❌ Dropping columns

### 3. Database-Specific Considerations

#### PostgreSQL
```sql
-- Add column
ALTER TABLE schema.table ADD COLUMN column_name data_type;

-- Modify column type
ALTER TABLE schema.table ALTER COLUMN column_name TYPE new_type;
-- Note: PostgreSQL may require USING clause for type conversions
```

#### Oracle
```sql
-- Add column
ALTER TABLE schema.table ADD (column_name data_type);

-- Modify column type (limited support)
ALTER TABLE schema.table MODIFY (column_name new_type);
-- Note: Oracle has restrictions on modifying columns with data
```

### 4. User Experience Flow

**Scenario 1: Adding New Columns**
1. User updates column mappings to add new column
2. On next load, system detects new column
3. System adds column automatically (safe operation)
4. Load continues normally

**Scenario 2: Changing Data Type**
1. User changes `VARCHAR(50)` to `VARCHAR(100)`
2. System detects change
3. System checks compatibility (increase = safe)
4. System applies change automatically
5. Load continues

**Scenario 3: Incompatible Type Change**
1. User changes `VARCHAR` to `NUMBER`
2. System detects incompatible change
3. System logs warning/error
4. User must manually migrate data or use different approach

---

## Implementation Steps

### Step 1: Add Helper Functions to `table_creator.py`

1. `get_existing_table_structure()` - Query existing columns
2. `compare_table_structure()` - Compare structures
3. `is_type_compatible()` - Check type compatibility
4. `generate_alter_table_statements()` - Generate ALTER SQL

### Step 2: Modify `create_table_if_not_exists()`

Add option to sync structure when table exists (with flag to enable/disable).

### Step 3: Add Configuration Option

Add to file upload configuration:
- `auto_sync_structure: bool` - Enable automatic structure sync
- `allow_type_changes: bool` - Allow data type modifications

### Step 4: Add Logging and Reporting

Return detailed report of:
- Columns added
- Columns modified
- Warnings generated
- Errors encountered

### Step 5: Add API Endpoints

- Preview structure changes
- Execute structure sync
- Get structure diff

### Step 6: Add UI Components

- Structure comparison view
- Preview changes dialog
- Confirmation for risky operations

---

## Risk Mitigation

1. **Backup Recommendations**: Warn users to backup data before structural changes
2. **Dry Run Mode**: Allow preview of changes before execution
3. **Transaction Safety**: Wrap ALTER statements in transactions where possible
4. **Error Handling**: Rollback on errors, provide detailed error messages
5. **Audit Trail**: Log all structure changes for audit purposes

---

## Testing Considerations

1. Test adding columns to existing tables
2. Test compatible type changes (size increases)
3. Test incompatible type changes (should fail gracefully)
4. Test with empty tables
5. Test with tables containing data
6. Test PostgreSQL and Oracle syntax differences
7. Test error scenarios (insufficient permissions, invalid types)

---

## Example Usage

```python
# In file_upload_executor.py
info(f"Creating/verifying target table: {trgschm}.{trgtblnm}")
table_created = create_table_if_not_exists(
    target_conn, trgschm, trgtblnm, column_mappings, metadata_conn
)

# If table existed, check if structure was synced
if not table_created:
    sync_result = sync_table_structure(
        target_conn, trgschm, trgtblnm, column_mappings, metadata_conn,
        allow_type_changes=True
    )
    if sync_result['columns_added']:
        info(f"Added {len(sync_result['columns_added'])} new columns")
    if sync_result['columns_modified']:
        info(f"Modified {len(sync_result['columns_modified'])} columns")
```

---

## Future Enhancements

1. **Column Renaming Support**: Add logic to rename columns (copy data)
2. **Column Dropping**: Add option to drop unused columns (with confirmation)
3. **Index Management**: Automatically create/drop indexes for added/removed columns
4. **Constraint Management**: Handle NOT NULL, UNIQUE, CHECK constraints
5. **Data Migration Wizard**: UI for complex type changes requiring data transformation

