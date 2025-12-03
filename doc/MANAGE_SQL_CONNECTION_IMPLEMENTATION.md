# Manage SQL Connection Implementation

## Overview
This document describes the implementation of connection string support for the `manage_sql` module, similar to the target connection feature in the `mapper` module.

**Date:** November 13, 2025  
**Feature:** Source Database Connection for SQL Queries

---

## Summary of Changes

The `manage_sql` module now supports specifying a **source database connection** for SQL queries. This allows SQL queries to pull data from external databases or the same database using different connection credentials.

### Key Features:
1. ✅ Optional connection ID field in SQL management
2. ✅ Connection validation against `DMS_DBCONDTLS` table
3. ✅ Backward compatible (NULL connection = use metadata connection)
4. ✅ Connection dropdown API endpoint
5. ✅ Complete historization support

---

## Database Changes

### 1. New Column: `SQLCONID`

Added to the `DMS_MAPRSQL` table to store the source connection ID.

```sql
ALTER TABLE DMS_MAPRSQL ADD (SQLCONID NUMBER);
```

**Properties:**
- **Type:** NUMBER
- **Nullable:** YES
- **Default:** NULL (uses metadata connection)
- **Purpose:** References `DMS_DBCONDTLS.CONID` for source database connection

### 2. Foreign Key Constraint

```sql
ALTER TABLE DMS_MAPRSQL ADD CONSTRAINT FK_DMS_MAPRSQL_SQLCONID 
    FOREIGN KEY (SQLCONID) REFERENCES DMS_DBCONDTLS(CONID);
```

**Purpose:** Ensures connection ID references a valid connection in `DMS_DBCONDTLS`

---

## Backend Changes

### 1. Updated `pkgdms_mapr_python.py`

#### Function: `create_update_sql()`

**File:** `backend/modules/mapper/pkgdms_mapr_python.py`

**Changes:**
- Added `p_sqlconid` parameter (optional, defaults to `None`)
- Added connection ID validation
- Updated SELECT query to include `sqlconid` column
- Updated INSERT statement to include `sqlconid` column
- Connection ID comparison in change detection

**Signature:**
```python
def create_update_sql(connection, p_dms_maprsqlcd, p_dms_maprsql, p_sqlconid=None):
    """
    Function to record SQL query
    
    Args:
        connection: Database connection
        p_dms_maprsqlcd: SQL code identifier
        p_dms_maprsql: SQL query content
        p_sqlconid: Source database connection ID (from DMS_DBCONDTLS). 
                    If None, uses metadata connection.
    
    Returns:
        dms_maprsqlid
    """
```

**Validation Logic:**
```python
# Validate connection ID if provided
sqlconid_val = None
if p_sqlconid is not None and str(p_sqlconid).strip() != '':
    try:
        sqlconid_val = int(p_sqlconid)
        # Validate connection exists and is active
        cursor.execute("""
            SELECT conid FROM DMS_DBCONDTLS 
            WHERE conid = :1 AND curflg = 'Y'
        """, [sqlconid_val])
        if not cursor.fetchone():
            w_msg = f'Invalid or inactive source connection ID: {sqlconid_val}'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
    except ValueError:
        w_msg = f'Source connection ID must be numeric: {p_sqlconid}'
        _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
```

---

### 2. Updated `manage_sql.py`

**File:** `backend/modules/manage_sql/manage_sql.py`

#### A. Updated `/save-sql` Endpoint

**Changes:**
- Accepts `connection_id` parameter from request JSON
- Passes connection ID to `create_update_sql()` function

**Request Format:**
```json
{
  "sql_code": "SQL_001",
  "sql_content": "SELECT * FROM table",
  "connection_id": "1"  // Optional
}
```

**Code:**
```python
@manage_sql_bp.route('/save-sql', methods=['POST'])
def save_sql():
    data = request.json
    sql_code = data.get('sql_code')
    sql_content = data.get('sql_content')
    connection_id = data.get('connection_id')  # Optional
    
    # Call function with connection ID
    returned_sql_id = pkgdms_mapr.create_update_sql(
        conn, 
        sql_code, 
        sql_content,
        connection_id  # Pass the source connection ID
    )
```

#### B. Updated `/fetch-sql-logic` Endpoint

**Changes:**
- Now returns `connection_id` in response
- Updated SELECT query to include `SQLCONID` column

**Response Format:**
```json
{
  "success": true,
  "message": "Successfully fetched SQL logic for code: SQL_001",
  "data": {
    "sql_code": "SQL_001",
    "sql_content": "SELECT * FROM table",
    "connection_id": "1"  // null if using metadata connection
  }
}
```

**Code:**
```python
# Query to fetch SQL logic and connection ID
query = "SELECT DMS_MAPRSQL, SQLCONID FROM DMS_MAPRSQL WHERE DMS_MAPRSQLCD = :sql_code AND CURFLG = 'Y'"
cursor.execute(query, {'sql_code': sql_code})

result = cursor.fetchone()
if result:
    sql_content = result[0].read() if hasattr(result[0], 'read') else str(result[0])
    connection_id = str(result[1]) if result[1] is not None else None
```

#### C. New `/get-connections` Endpoint

**Purpose:** Fetch list of active database connections for dropdown

**Endpoint:** `GET /manage-sql/get-connections`

**Response Format:**
```json
[
  {
    "conid": "1",
    "connm": "DEV_DATABASE",
    "dbhost": "localhost",
    "dbsrvnm": "ORCL"
  },
  {
    "conid": "2",
    "connm": "PROD_DATABASE",
    "dbhost": "prod-server",
    "dbsrvnm": "PRODDB"
  }
]
```

**Code:**
```python
@manage_sql_bp.route('/get-connections', methods=['GET'])
def get_connections():
    """
    Get list of active database connections from DMS_DBCONDTLS
    This allows manage_sql to query data from external/source databases
    """
    cursor.execute("""
        SELECT conid, connm, dbhost, dbsrvnm
        FROM DMS_DBCONDTLS
        WHERE curflg = 'Y'
        ORDER BY connm
    """)
```

---

## How It Works

### Workflow:

1. **User Opens Manage SQL Module**
   - Connection dropdown loads active connections from `DMS_DBCONDTLS`
   - Default option: "Use Metadata Connection" (NULL value)

2. **User Creates/Edits SQL Query**
   - User can optionally select a source connection
   - If selected, connection ID is passed to backend
   - If not selected, `connection_id` is NULL (uses metadata connection)

3. **Backend Saves SQL Query**
   - Validates connection ID exists in `DMS_DBCONDTLS` and is active (`CURFLG='Y'`)
   - Saves SQL query with connection ID in `DMS_MAPRSQL.SQLCONID`
   - Historization: Old version set to `CURFLG='N'`, new version inserted with `CURFLG='Y'`

4. **User Loads Existing SQL Query**
   - Backend fetches SQL content and connection ID
   - Frontend displays selected connection in dropdown

5. **SQL Execution** (Future Implementation)
   - When SQL is executed, system checks `SQLCONID`
   - If NULL: Uses metadata connection
   - If set: Creates connection using `create_target_connection(connection_id)` from `dbconnect.py`

---

## Database Schema

### DMS_MAPRSQL Table (Updated)

| Column         | Type          | Nullable | Description                                    |
|----------------|---------------|----------|------------------------------------------------|
| DMS_MAPRSQLID    | NUMBER        | NO       | Primary key (auto-generated)                   |
| DMS_MAPRSQLCD    | VARCHAR2(100) | NO       | SQL code identifier (unique per active record) |
| DMS_MAPRSQL      | CLOB          | NO       | SQL query content                              |
| **SQLCONID**   | **NUMBER**    | **YES**  | **Source connection ID (NEW)**                 |
| RECCRDT        | DATE          | NO       | Record creation date                           |
| RECUPDT        | DATE          | NO       | Record update date                             |
| CURFLG         | CHAR(1)       | NO       | Current flag ('Y' or 'N')                      |

### DMS_DBCONDTLS Table (Existing)

| Column    | Type          | Description                  |
|-----------|---------------|------------------------------|
| CONID     | NUMBER        | Connection ID (Primary key)  |
| CONNM     | VARCHAR2(100) | Connection name              |
| DBHOST    | VARCHAR2(100) | Database host                |
| DBPORT    | NUMBER        | Database port                |
| DBSRVNM   | VARCHAR2(100) | Database service name        |
| USRNM     | VARCHAR2(100) | Username                     |
| PASSWD    | VARCHAR2(100) | Password                     |
| CONSTR    | VARCHAR2(500) | Connection string (optional) |
| CURFLG    | CHAR(1)       | Current flag ('Y' or 'N')    |

---

## Migration Instructions

### Step 1: Run Database Migration Script

Execute the SQL script: `database_migration_manage_sql_connection.sql`

```bash
sqlplus username/password@database
SQL> @database_migration_manage_sql_connection.sql
```

**Script performs:**
1. Adds `SQLCONID` column to `DMS_MAPRSQL`
2. Creates foreign key constraint to `DMS_DBCONDTLS`
3. Adds column comment
4. Runs verification queries

### Step 2: Verify Database Changes

```sql
-- Check column was added
SELECT column_name, data_type, nullable 
FROM user_tab_columns 
WHERE table_name = 'DMS_MAPRSQL' 
AND column_name = 'SQLCONID';

-- Check foreign key constraint
SELECT constraint_name, constraint_type 
FROM user_constraints
WHERE table_name = 'DMS_MAPRSQL'
AND constraint_name = 'FK_DMS_MAPRSQL_SQLCONID';

-- Verify existing records (should have NULL SQLCONID)
SELECT DMS_MAPRSQLCD, SQLCONID, CURFLG
FROM DMS_MAPRSQL
WHERE CURFLG = 'Y';
```

### Step 3: Backend Code Already Updated

✅ All backend code changes are already implemented in:
- `backend/modules/mapper/pkgdms_mapr_python.py`
- `backend/modules/manage_sql/manage_sql.py`

### Step 4: Frontend Integration (To Be Done)

**Frontend needs to:**
1. Add connection dropdown to Manage SQL UI
2. Load connections from `/manage-sql/get-connections`
3. Pass `connection_id` in save-sql request
4. Display `connection_id` when loading existing SQL

**Example Frontend API Calls:**

```javascript
// Get connections for dropdown
const connections = await fetch('/manage-sql/get-connections')
  .then(res => res.json());

// Save SQL with connection
await fetch('/manage-sql/save-sql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sql_code: 'SQL_001',
    sql_content: 'SELECT * FROM table',
    connection_id: selectedConnectionId || null
  })
});

// Fetch SQL (returns connection_id)
const sqlData = await fetch('/manage-sql/fetch-sql-logic?sql_code=SQL_001')
  .then(res => res.json());
console.log(sqlData.data.connection_id);
```

---

## Testing

### Test Case 1: Save SQL Without Connection
```bash
curl -X POST http://localhost:5000/manage-sql/save-sql \
  -H "Content-Type: application/json" \
  -d '{
    "sql_code": "TEST_SQL_001",
    "sql_content": "SELECT * FROM dual"
  }'
```

**Expected:** SQL saved with `SQLCONID = NULL`

### Test Case 2: Save SQL With Connection
```bash
curl -X POST http://localhost:5000/manage-sql/save-sql \
  -H "Content-Type: application/json" \
  -d '{
    "sql_code": "TEST_SQL_002",
    "sql_content": "SELECT * FROM employees",
    "connection_id": "1"
  }'
```

**Expected:** SQL saved with `SQLCONID = 1`

### Test Case 3: Invalid Connection ID
```bash
curl -X POST http://localhost:5000/manage-sql/save-sql \
  -H "Content-Type: application/json" \
  -d '{
    "sql_code": "TEST_SQL_003",
    "sql_content": "SELECT * FROM test",
    "connection_id": "9999"
  }'
```

**Expected:** Error message: "Invalid or inactive source connection ID: 9999"

### Test Case 4: Fetch Connections
```bash
curl http://localhost:5000/manage-sql/get-connections
```

**Expected:** JSON array of active connections

### Test Case 5: Fetch SQL With Connection
```bash
curl http://localhost:5000/manage-sql/fetch-sql-logic?sql_code=TEST_SQL_002
```

**Expected:** Response includes `connection_id: "1"`

---

## Verification Queries

### Check SQL Records with Connections
```sql
SELECT 
    s.DMS_MAPRSQLCD as SQL_CODE,
    s.SQLCONID as CONNECTION_ID,
    c.CONNM as CONNECTION_NAME,
    c.DBHOST as HOST,
    s.CURFLG as CURRENT_FLAG
FROM DMS_MAPRSQL s
LEFT JOIN DMS_DBCONDTLS c ON s.SQLCONID = c.CONID AND c.CURFLG = 'Y'
WHERE s.CURFLG = 'Y'
ORDER BY s.DMS_MAPRSQLCD;
```

### Check Connection Usage
```sql
-- Count SQL queries using each connection
SELECT 
    c.CONID,
    c.CONNM,
    COUNT(s.DMS_MAPRSQLID) as SQL_COUNT
FROM DMS_DBCONDTLS c
LEFT JOIN DMS_MAPRSQL s ON c.CONID = s.SQLCONID AND s.CURFLG = 'Y'
WHERE c.CURFLG = 'Y'
GROUP BY c.CONID, c.CONNM
ORDER BY c.CONNM;
```

---

## Backward Compatibility

✅ **100% Backward Compatible**

- Existing SQL records automatically have `SQLCONID = NULL`
- NULL value means "use metadata connection" (default behavior)
- No changes required to existing SQL queries
- Frontend can work without connection dropdown initially

---

## Comparison with Mapper Module

| Feature                    | Mapper Module       | Manage SQL Module    |
|----------------------------|---------------------|----------------------|
| **Column Name**            | `TRGCONID`          | `SQLCONID`           |
| **Purpose**                | Target connection   | Source connection    |
| **Table**                  | `DMS_MAPR`            | `DMS_MAPRSQL`          |
| **Connection Type**        | Where data goes     | Where data comes from|
| **API Endpoint**           | `/mapper/get-connections` | `/manage-sql/get-connections` |
| **Default**                | NULL (metadata)     | NULL (metadata)      |
| **Validation**             | ✅ Active connection check | ✅ Active connection check |
| **Foreign Key**            | ✅ FK to DMS_DBCONDTLS | ✅ FK to DMS_DBCONDTLS |

---

## Future Enhancements

### 1. Execute SQL on Source Connection
When implementing SQL execution:

```python
from database.dbconnect import create_target_connection

def execute_sql_query(sql_code):
    """Execute SQL query on appropriate connection"""
    # Fetch SQL and connection ID
    conn = create_oracle_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DMS_MAPRSQL, sqlconid 
        FROM DMS_MAPRSQL 
        WHERE dms_maprsqlcd = :1 AND curflg = 'Y'
    """, [sql_code])
    
    result = cursor.fetchone()
    sql_content, connection_id = result
    
    # Create appropriate connection
    if connection_id:
        exec_conn = create_target_connection(connection_id)
    else:
        exec_conn = create_oracle_connection()
    
    # Execute SQL
    exec_cursor = exec_conn.cursor()
    exec_cursor.execute(sql_content)
    data = exec_cursor.fetchall()
    
    exec_conn.close()
    return data
```

### 2. Connection Test Feature
Add endpoint to test connection before saving:

```python
@manage_sql_bp.route('/test-connection/<int:connection_id>', methods=['GET'])
def test_connection(connection_id):
    """Test if connection can be established"""
    try:
        conn = create_target_connection(connection_id)
        conn.close()
        return jsonify({'success': True, 'message': 'Connection successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

---

## Troubleshooting

### Error: "Invalid or inactive source connection ID"
**Cause:** Connection doesn't exist or `CURFLG='N'`

**Solution:**
```sql
-- Check connection status
SELECT CONID, CONNM, CURFLG FROM DMS_DBCONDTLS WHERE CONID = <id>;

-- Activate connection if needed
UPDATE DMS_DBCONDTLS SET CURFLG = 'Y' WHERE CONID = <id>;
COMMIT;
```

### Error: "ORA-02291: integrity constraint violated"
**Cause:** Trying to use non-existent connection ID

**Solution:**
- Use valid connection ID from `DMS_DBCONDTLS`
- Or use NULL for metadata connection

### Connection Dropdown Empty
**Cause:** No active connections in `DMS_DBCONDTLS`

**Solution:**
```sql
-- Check for active connections
SELECT COUNT(*) FROM DMS_DBCONDTLS WHERE CURFLG = 'Y';

-- If 0, register connections using DB Connections module
```

---

## Files Modified

1. ✅ `backend/modules/mapper/pkgdms_mapr_python.py` - Updated `create_update_sql()`
2. ✅ `backend/modules/manage_sql/manage_sql.py` - Updated endpoints
3. ✅ `database_migration_manage_sql_connection.sql` - Database migration script
4. ✅ `MANAGE_SQL_CONNECTION_IMPLEMENTATION.md` - This documentation

---

## Summary

The manage_sql module now supports:
- ✅ Optional source connection selection
- ✅ Connection validation
- ✅ Backward compatibility
- ✅ Complete historization
- ✅ Same pattern as mapper module

**Next Steps:**
1. Run database migration script
2. Verify backend changes (already complete)
3. Update frontend to include connection dropdown
4. Test all scenarios

---

**Questions or Issues?**
Contact: Development Team  
Date: November 13, 2025

