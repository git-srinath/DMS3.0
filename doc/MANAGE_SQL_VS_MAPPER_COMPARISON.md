# Manage SQL vs Mapper Module - Connection Feature Comparison

## Visual Comparison

### Mapper Module (Target Connection) - EXISTING
```
┌─────────────────────────────────────────────────────────────┐
│                     MAPPER MODULE                           │
│                                                             │
│  Purpose: Define WHERE data should be WRITTEN              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DWMAPR Table                                         │  │
│  │                                                      │  │
│  │  MAPREF: "MAP_001"                                  │  │
│  │  MAPDESC: "Customer Mapping"                        │  │
│  │  TRGSCHM: "TARGET_SCHEMA"                           │  │
│  │  TRGTBNM: "CUSTOMERS"                               │  │
│  │  TRGCONID: 2  ────────────┐                         │  │
│  │                            │                         │  │
│  └────────────────────────────┼─────────────────────────┘  │
│                                │                            │
│                                ▼                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ DWDBCONDTLS Table                                  │    │
│  │                                                    │    │
│  │  CONID: 2                                         │    │
│  │  CONNM: "PROD_DATABASE"                           │    │
│  │  DBHOST: "prod-server"                            │    │
│  │  DBSRVNM: "PRODDB"                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Result: Data is WRITTEN to PROD_DATABASE                  │
└─────────────────────────────────────────────────────────────┘
```

### Manage SQL Module (Source Connection) - NEW
```
┌─────────────────────────────────────────────────────────────┐
│                   MANAGE SQL MODULE                         │
│                                                             │
│  Purpose: Define WHERE data should be READ FROM            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DWMAPRSQL Table                                      │  │
│  │                                                      │  │
│  │  DWMAPRSQLCD: "SQL_001"                             │  │
│  │  DWMAPRSQL: "SELECT * FROM source_table"            │  │
│  │  SQLCONID: 1  ────────────┐                         │  │
│  │                            │                         │  │
│  └────────────────────────────┼─────────────────────────┘  │
│                                │                            │
│                                ▼                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ DWDBCONDTLS Table (Same table, shared!)           │    │
│  │                                                    │    │
│  │  CONID: 1                                         │    │
│  │  CONNM: "SOURCE_DATABASE"                         │    │
│  │  DBHOST: "source-server"                          │    │
│  │  DBSRVNM: "SOURCEDB"                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Result: Data is READ FROM SOURCE_DATABASE                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Complete ETL Flow with Both Modules

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ETL PROCESS FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

Step 1: SOURCE DATA (Manage SQL)
────────────────────────────────
   ┌──────────────────┐
   │  SOURCE DB       │
   │  (Connection 1)  │ ◄────── SQLCONID in DWMAPRSQL
   │                  │         (Manage SQL Module)
   │  ┌────────────┐  │
   │  │ EMP Table  │  │
   │  │ Customer   │  │
   │  └────────────┘  │
   └──────────────────┘
           │
           │ SQL_001: SELECT * FROM emp
           │
           ▼
   ┌──────────────────┐
   │  EXTRACT DATA    │
   │  (via SQL)       │
   └──────────────────┘
           │
           ▼

Step 2: TRANSFORMATION (Mapper)
────────────────────────────────
   ┌──────────────────┐
   │  MAPPER LOGIC    │
   │  (MAP_001)       │
   │                  │
   │  Apply rules     │
   │  Transform data  │
   │  Map fields      │
   └──────────────────┘
           │
           ▼

Step 3: TARGET DATA (Mapper)
────────────────────────────────
   ┌──────────────────┐
   │  TARGET DB       │
   │  (Connection 2)  │ ◄────── TRGCONID in DWMAPR
   │                  │         (Mapper Module)
   │  ┌────────────┐  │
   │  │ CUSTOMERS  │  │
   │  │ (Target)   │  │
   │  └────────────┘  │
   └──────────────────┘
```

---

## Side-by-Side Comparison

| Aspect                    | Mapper Module           | Manage SQL Module       |
|---------------------------|-------------------------|-------------------------|
| **Column Name**           | `TRGCONID`             | `SQLCONID`              |
| **Table**                 | `DWMAPR`               | `DWMAPRSQL`             |
| **Purpose**               | Target (WHERE to write)| Source (WHERE to read)  |
| **Direction**             | ➡️ Output              | ⬅️ Input                |
| **Connection Table**      | `DWDBCONDTLS`          | `DWDBCONDTLS` (shared!) |
| **Nullable**              | YES (default metadata) | YES (default metadata)  |
| **Foreign Key**           | ✅ FK_DWMAPR_TRGCONID  | ✅ FK_DWMAPRSQL_SQLCONID|
| **API Endpoint**          | `/mapper/get-connections` | `/manage-sql/get-connections` |
| **Save Endpoint**         | `/mapper/save-to-db`   | `/manage-sql/save-sql`  |
| **Fetch Endpoint**        | `/mapper/get-by-reference` | `/manage-sql/fetch-sql-logic` |
| **Function Parameter**    | `p_trgconid`           | `p_sqlconid`            |
| **Default Behavior**      | Use metadata connection| Use metadata connection |
| **Implementation Status** | ✅ Complete            | ✅ Complete             |

---

## Real-World Example

### Scenario: Copy data from Oracle to PostgreSQL

#### 1. Define Source Connection (Manage SQL)
```sql
-- In DWDBCONDTLS
INSERT INTO DWDBCONDTLS VALUES (
  1,                           -- CONID
  'ORACLE_SOURCE',             -- CONNM
  'oracle-server',             -- DBHOST
  1521,                        -- DBPORT
  'ORCL',                      -- DBSRVNM
  'source_user',               -- USRNM
  'source_pass',               -- PASSWD
  NULL,                        -- CONSTR
  SYSDATE, SYSDATE, 'Y'
);

-- Create SQL Query with source connection
-- DWMAPRSQL record:
DWMAPRSQLCD: "GET_ORACLE_CUSTOMERS"
DWMAPRSQL: "SELECT customer_id, customer_name, email FROM oracle_customers"
SQLCONID: 1  ◄── Points to ORACLE_SOURCE
```

#### 2. Define Target Connection (Mapper)
```sql
-- In DWDBCONDTLS (same table!)
INSERT INTO DWDBCONDTLS VALUES (
  2,                           -- CONID
  'POSTGRES_TARGET',           -- CONNM
  'postgres-server',           -- DBHOST
  5432,                        -- DBPORT
  'pgdb',                      -- DBSRVNM
  'target_user',               -- USRNM
  'target_pass',               -- PASSWD
  NULL,                        -- CONSTR
  SYSDATE, SYSDATE, 'Y'
);

-- Create Mapping with target connection
-- DWMAPR record:
MAPREF: "MAP_CUSTOMERS"
TRGSCHM: "public"
TRGTBNM: "customers"
TRGCONID: 2  ◄── Points to POSTGRES_TARGET
```

#### 3. ETL Process Flow
```
1. Execute SQL_001 on connection 1 (ORACLE_SOURCE)
   └─> Fetches data from Oracle database

2. Transform data using MAP_CUSTOMERS logic
   └─> Apply business rules and field mappings

3. Write to target using connection 2 (POSTGRES_TARGET)
   └─> Inserts data into PostgreSQL database
```

---

## Code Flow Comparison

### Mapper Module
```python
# 1. Get target connection ID from DWMAPR
cursor.execute("""
    SELECT trgconid FROM DWMAPR 
    WHERE mapref = :1 AND curflg = 'Y'
""", [mapref])

# 2. If connection ID exists, create target connection
if trgconid:
    target_conn = create_target_connection(trgconid)
else:
    target_conn = create_oracle_connection()  # Metadata

# 3. Write data to target
cursor = target_conn.cursor()
cursor.execute("INSERT INTO target_table VALUES (...)")
```

### Manage SQL Module
```python
# 1. Get source connection ID from DWMAPRSQL
cursor.execute("""
    SELECT dwmaprsql, sqlconid FROM DWMAPRSQL 
    WHERE dwmaprsqlcd = :1 AND curflg = 'Y'
""", [sql_code])

# 2. If connection ID exists, create source connection
if sqlconid:
    source_conn = create_target_connection(sqlconid)
else:
    source_conn = create_oracle_connection()  # Metadata

# 3. Read data from source
cursor = source_conn.cursor()
cursor.execute(sql_content)  # User's SQL query
data = cursor.fetchall()
```

---

## Connection Registry (DWDBCONDTLS)

This single table serves **BOTH** modules:

```sql
SELECT 
    CONID,
    CONNM,
    DBHOST || ':' || DBPORT || '/' || DBSRVNM as DSN,
    CURFLG,
    -- Used by which modules?
    (SELECT COUNT(*) FROM DWMAPR WHERE TRGCONID = CONID AND CURFLG='Y') as MAPPER_USAGE,
    (SELECT COUNT(*) FROM DWMAPRSQL WHERE SQLCONID = CONID AND CURFLG='Y') as SQL_USAGE
FROM DWDBCONDTLS
WHERE CURFLG = 'Y'
ORDER BY CONNM;
```

**Example Output:**
```
CONID  CONNM              DSN                    CURFLG  MAPPER_USAGE  SQL_USAGE
────────────────────────────────────────────────────────────────────────────────
1      DEV_DATABASE       localhost:1521/ORCL    Y       5             12
2      PROD_DATABASE      prod:1521/PROD         Y       3             8
3      EXTERNAL_DB        ext:1521/EXT           Y       0             5
```

---

## Benefits of This Design

### 1. **Separation of Concerns**
- **Manage SQL**: Deals with SOURCE databases (input)
- **Mapper**: Deals with TARGET databases (output)

### 2. **Shared Infrastructure**
- Both use same `DWDBCONDTLS` table
- Both use same `create_target_connection()` function
- Consistent API patterns

### 3. **Flexibility**
```
Scenario A: Same database for source and target
  SQL_001: SQLCONID = 1 (read from DB1)
  MAP_001: TRGCONID = 1 (write to DB1)

Scenario B: Different databases
  SQL_001: SQLCONID = 1 (read from DB1)
  MAP_001: TRGCONID = 2 (write to DB2)

Scenario C: Multiple sources, one target
  SQL_001: SQLCONID = 1 (read from DB1)
  SQL_002: SQLCONID = 2 (read from DB2)
  MAP_001: TRGCONID = 3 (write to DB3)
```

### 4. **Backward Compatibility**
- NULL connection ID = use metadata connection
- Existing records work without changes
- No breaking changes

---

## Migration Path

### Phase 1: Database (REQUIRED)
```sql
-- Mapper already has this:
ALTER TABLE DWMAPR ADD (TRGCONID NUMBER);
ALTER TABLE DWMAPR ADD CONSTRAINT FK_DWMAPR_TRGCONID 
    FOREIGN KEY (TRGCONID) REFERENCES DWDBCONDTLS(CONID);

-- Manage SQL needs this (NEW):
ALTER TABLE DWMAPRSQL ADD (SQLCONID NUMBER);
ALTER TABLE DWMAPRSQL ADD CONSTRAINT FK_DWMAPRSQL_SQLCONID 
    FOREIGN KEY (SQLCONID) REFERENCES DWDBCONDTLS(CONID);
```

### Phase 2: Backend (COMPLETE) ✅
- ✅ Mapper: Already implemented
- ✅ Manage SQL: Just implemented

### Phase 3: Frontend (TO DO)
- ⚠️ Mapper: Add connection dropdown (if not already done)
- ⚠️ Manage SQL: Add connection dropdown (needs to be done)

---

## Summary

| Feature                  | Status          |
|--------------------------|-----------------|
| **Mapper Connection**    | ✅ Complete     |
| **Manage SQL Connection**| ✅ Complete     |
| **Database Schema**      | ⚠️ Script Ready |
| **Backend Code**         | ✅ Complete     |
| **API Endpoints**        | ✅ Complete     |
| **Documentation**        | ✅ Complete     |
| **Frontend Integration** | 🔄 Pending      |

---

## Quick Reference

### API Endpoints
```
Mapper Module:
  GET  /mapper/get-connections          - Get connection list
  POST /mapper/save-to-db               - Save mapping (with TRGCONID)
  GET  /mapper/get-by-reference/:ref    - Get mapping (returns TRGCONID)

Manage SQL Module:
  GET  /manage-sql/get-connections      - Get connection list
  POST /manage-sql/save-sql             - Save SQL (with SQLCONID)
  GET  /manage-sql/fetch-sql-logic      - Get SQL (returns SQLCONID)
```

### Database Columns
```
DWMAPR.TRGCONID      ───┐
                        ├──► DWDBCONDTLS.CONID
DWMAPRSQL.SQLCONID   ───┘
```

---

**Both modules now have symmetric connection support!** 🎉

