# Target Connection Implementation Plan

## Overview
Separate metadata schema (where DWMAPR, DWMAPRDTL, etc. reside) from target data schema (where created tables and data will reside).

**Current Architecture:**
```
┌─────────────────────────────┐
│  Single Oracle Connection   │
│  (from .env file)           │
├─────────────────────────────┤
│  • Metadata Tables (DWMAPR) │
│  • Target Tables            │
│  • Data Loading             │
└─────────────────────────────┘
```

**Target Architecture:**
```
┌──────────────────────────────┐     ┌─────────────────────────────┐
│  Metadata Connection         │     │  Target Data Connection     │
│  (from .env - default)       │     │  (user selectable)          │
├──────────────────────────────┤     ├─────────────────────────────┤
│  • DWMAPR                    │     │  • Created Tables           │
│  • DWMAPRDTL                 │     │  • DIM_*, FCT_*, MRT_*      │
│  • DWJOB                     │     │  • Data Loading Operations  │
│  • DWDBCONDTLS (connections) │     │                             │
└──────────────────────────────┘     └─────────────────────────────┘
```

---

## Implementation Steps

### STEP 1: Database Schema Changes

#### 1.1 Add Target Connection Column to DWMAPR Table

**SQL Script:**
```sql
-- Add new column for target database connection ID
ALTER TABLE DWMAPR ADD (
    trgconid NUMBER(12)  -- Foreign key to DWDBCONDTLS.CONID
);

-- Add comment
COMMENT ON COLUMN DWMAPR.TRGCONID IS 'Target database connection ID for creating objects and loading data';

-- Optional: Add foreign key constraint
ALTER TABLE DWMAPR ADD CONSTRAINT DWMAPR_TRGCON_FK 
    FOREIGN KEY (TRGCONID) REFERENCES DWDBCONDTLS(CONID);

-- Optional: Add index for performance
CREATE INDEX DWMAPR_TRGCONID_IDX ON DWMAPR(TRGCONID);
```

#### 1.2 Update Existing Records (if needed)
```sql
-- Set default connection for existing mappings
-- Option 1: Set to NULL (metadata connection will be used as default)
UPDATE DWMAPR SET TRGCONID = NULL WHERE TRGCONID IS NULL;

-- Option 2: Set to a specific connection ID
-- UPDATE DWMAPR SET TRGCONID = <default_connection_id> WHERE TRGCONID IS NULL;

COMMIT;
```

#### 1.3 Update DWJOB Table (for consistency)
```sql
-- Add target connection to job table as well
ALTER TABLE DWJOB ADD (
    trgconid NUMBER(12)
);

COMMENT ON COLUMN DWJOB.TRGCONID IS 'Target database connection ID for job execution';
```

---

### STEP 2: Backend Python Changes

#### 2.1 Update `pkgdwmapr_python.py`

**Location:** `backend/modules/mapper/pkgdwmapr_python.py`

**Changes in `create_update_mapping()` function:**

```python
def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
                         p_stflg, p_blkprcrows, p_trgconid=None, p_user=None):  # ADD p_trgconid parameter
```

**Update validation:**
```python
# Add validation for target connection if provided
if p_trgconid is not None:
    try:
        # Validate connection exists
        cursor.execute("""
            SELECT conid FROM DWDBCONDTLS 
            WHERE conid = :1 AND curflg = 'Y'
        """, [p_trgconid])
        if not cursor.fetchone():
            w_msg = 'Invalid target connection ID. Connection not found or inactive.'
    except Exception as e:
        w_msg = f'Error validating target connection: {str(e)}'
```

**Update SELECT query:**
```python
query = """
    SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
           srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid  -- ADD trgconid
    FROM dwmapr
    WHERE mapref = :1
    AND curflg = 'Y'
"""
```

**Update change detection:**
```python
if (w_mapr_rec['mapdesc'] == p_mapdesc and
    # ... other comparisons ...
    _nvl(w_mapr_rec['trgconid'], -1) == _nvl(p_trgconid, -1)):  # ADD trgconid comparison
```

**Update INSERT statement:**
```python
cursor.execute("""
    INSERT INTO dwmapr 
    (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
     lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, 
     trgconid, crtdby, uptdby)  -- ADD trgconid
    VALUES 
    (dwmaprseq.nextval, :1, :2, :3, :4, :5, :6, :7,
     :8, :9, :10, sysdate, sysdate, 'Y', :11, 
     :12, :13, :14)  -- ADD parameter
    RETURNING mapid INTO :15
""", [p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
      _nvl(p_lgvrfyflg, 'N'), p_lgvrfydt, _nvl(p_stflg, 'N'), blkprcrows_val,
      p_trgconid, G_USER, G_USER, var_mapid])  -- ADD p_trgconid
```

#### 2.2 Update `helper_functions.py`

**Location:** `backend/modules/helper_functions.py`

**Update `get_mapping_ref()` function:**
```python
def get_mapping_ref(conn, reference):
    """Fetch reference data from DWMAPR table"""
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
            MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
            TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG,
            TRGCONID  -- ADD THIS
            FROM DWMAPR WHERE MAPREF = :1 AND CURFLG = 'Y'
        """
        # ... rest of function
```

**Update `create_update_mapping()` function:**
```python
def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, 
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, 
                         p_stflg, p_blkprcrows, p_trgconid, user_id):  # ADD p_trgconid
    try:
        mapid = pkgdwmapr.create_update_mapping(
            connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
            p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
            p_stflg, p_blkprcrows, p_trgconid, user_id)  # ADD p_trgconid
        return mapid
```

#### 2.3 Create Connection Helper Function

**Add to `database/dbconnect.py`:**
```python
def create_target_connection(connection_id):
    """
    Create a database connection for target data operations
    based on connection ID from DWDBCONDTLS
    
    Args:
        connection_id: CONID from DWDBCONDTLS table
    
    Returns:
        Oracle connection object
    """
    try:
        from modules.logger import info, error
        
        # Get metadata connection first
        metadata_conn = create_oracle_connection()
        cursor = metadata_conn.cursor()
        
        # Fetch connection details from DWDBCONDTLS
        cursor.execute("""
            SELECT connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr
            FROM DWDBCONDTLS
            WHERE conid = :1 AND curflg = 'Y'
        """, [connection_id])
        
        row = cursor.fetchone()
        if not row:
            raise Exception(f"Connection ID {connection_id} not found or inactive")
        
        connm, dbhost, dbport, dbsrvnm, usrnm, passwd, constr = row
        
        # Close metadata connection
        cursor.close()
        metadata_conn.close()
        
        # Create target connection
        if constr:  # Use connection string if provided
            target_conn = oracledb.connect(dsn=constr)
        else:  # Build from components
            target_conn = oracledb.connect(
                user=usrnm,
                password=passwd,
                dsn=f"{dbhost}:{dbport}/{dbsrvnm}"
            )
        
        info(f"Target connection '{connm}' (ID: {connection_id}) established successfully")
        return target_conn
        
    except Exception as e:
        from modules.logger import error
        error(f"Error establishing target connection (ID: {connection_id}): {str(e)}")
        raise

def get_connection_for_mapping(mapref):
    """
    Get the appropriate database connection for a mapping
    If mapping has a target connection ID, use that; otherwise use metadata connection
    
    Args:
        mapref: Mapping reference code
    
    Returns:
        Tuple: (connection, is_target_connection)
    """
    try:
        from modules.logger import info
        
        # Get metadata connection
        metadata_conn = create_oracle_connection()
        cursor = metadata_conn.cursor()
        
        # Check if mapping has a target connection
        cursor.execute("""
            SELECT trgconid
            FROM DWMAPR
            WHERE mapref = :1 AND curflg = 'Y'
        """, [mapref])
        
        row = cursor.fetchone()
        cursor.close()
        
        if row and row[0]:  # Has target connection
            trgconid = row[0]
            metadata_conn.close()
            target_conn = create_target_connection(trgconid)
            info(f"Using target connection (ID: {trgconid}) for mapping {mapref}")
            return target_conn, True
        else:  # Use metadata connection
            info(f"Using metadata connection for mapping {mapref}")
            return metadata_conn, False
            
    except Exception as e:
        from modules.logger import error
        error(f"Error getting connection for mapping {mapref}: {str(e)}")
        raise
```

#### 2.4 Update Mapper API Endpoint

**Location:** `backend/modules/mapper/mapper.py`

**Update the save mapping endpoint:**
```python
@mapper_bp.route('/save-mapping', methods=['POST'])
def save_mapping():
    try:
        data = request.json
        # ... existing validation code ...
        
        # Get target connection ID from request
        target_connection_id = data.get('target_connection_id')  # NEW
        
        # Call updated function
        mapid = helper_functions.create_update_mapping(
            conn, 
            mapref, mapdesc, trgschm, trgtbtyp,
            trgtbnm, frqcd, srcsystm, lgvrfyflg, lgvrfydt,
            stflg, blkprcrows, target_connection_id, user_id  # ADD target_connection_id
        )
        # ... rest of function
```

**Update the get mapping endpoint:**
```python
@mapper_bp.route('/get-mapping/<reference>', methods=['GET'])
def get_mapping(reference):
    try:
        conn = create_oracle_connection()
        mapping = helper_functions.get_mapping_ref(conn, reference)
        
        if mapping:
            # Include target connection info in response
            result = {
                'mapid': mapping['MAPID'],
                'mapref': mapping['MAPREF'],
                # ... other fields ...
                'target_connection_id': mapping.get('TRGCONID'),  # NEW
            }
            return jsonify({'success': True, 'data': result})
```

---

### STEP 3: Frontend Changes

#### 3.1 Add Connection Selector to Mapper SQL Module

**Location:** `frontend/src/components/ManageSQLModule/ManageSQLModule.jsx` (or similar)

**Add state for connections:**
```javascript
const [connections, setConnections] = useState([]);
const [selectedConnection, setSelectedConnection] = useState(null);

// Fetch connections on component mount
useEffect(() => {
    fetchConnections();
}, []);

const fetchConnections = async () => {
    try {
        const response = await fetch('/api/crud-dbconnections/dbconnections');
        const data = await response.json();
        if (data.success) {
            setConnections(data.data);
        }
    } catch (error) {
        console.error('Error fetching connections:', error);
    }
};
```

**Add connection dropdown:**
```jsx
<div className="form-group">
    <label>Target Database Connection:</label>
    <select 
        value={selectedConnection || ''} 
        onChange={(e) => setSelectedConnection(e.target.value)}
        className="form-control"
    >
        <option value="">-- Use Metadata Connection (Default) --</option>
        {connections.map(conn => (
            <option key={conn.conid} value={conn.conid}>
                {conn.connm} ({conn.dbhost})
            </option>
        ))}
    </select>
    <small className="form-text text-muted">
        Select where target tables will be created and data will be loaded
    </small>
</div>
```

#### 3.2 Add Connection Selector to Mapping Module

**Location:** `frontend/src/components/MapperModule/MapperModule.jsx` (or similar)

**Similar changes as above - add connection selector dropdown**

**Update save function:**
```javascript
const saveMapping = async () => {
    const mappingData = {
        mapref: mapRef,
        mapdesc: mapDesc,
        // ... other fields ...
        target_connection_id: selectedConnection,  // NEW
    };
    
    const response = await fetch('/api/mapper/save-mapping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mappingData)
    });
    // ... handle response
};
```

**When loading existing mapping:**
```javascript
const loadMapping = async (mapref) => {
    const response = await fetch(`/api/mapper/get-mapping/${mapref}`);
    const data = await response.json();
    if (data.success) {
        setMapRef(data.data.mapref);
        setMapDesc(data.data.mapdesc);
        // ... other fields ...
        setSelectedConnection(data.data.target_connection_id);  // NEW
    }
};
```

---

### STEP 4: Update Data Processing Logic

#### 4.1 Update Job Execution to Use Target Connection

**When creating tables:**
```python
def create_target_table(mapref):
    """Create target table using appropriate connection"""
    from database.dbconnect import get_connection_for_mapping
    
    # Get the right connection
    conn, is_target = get_connection_for_mapping(mapref)
    
    try:
        # Create table DDL and execute
        cursor = conn.cursor()
        cursor.execute(create_table_ddl)
        conn.commit()
    finally:
        conn.close()
```

**When loading data:**
```python
def load_data_to_target(mapref):
    """Load data using appropriate connection"""
    from database.dbconnect import get_connection_for_mapping
    
    # Get the right connection
    conn, is_target = get_connection_for_mapping(mapref)
    
    try:
        # Execute data loading logic
        cursor = conn.cursor()
        cursor.execute(insert_statement)
        conn.commit()
    finally:
        conn.close()
```

---

## Summary of Changes

### Files to Modify:

1. **Database:**
   - Add `TRGCONID` column to `DWMAPR` table
   - Add `TRGCONID` column to `DWJOB` table (optional but recommended)

2. **Backend Python:**
   - `backend/modules/mapper/pkgdwmapr_python.py` - Add trgconid parameter to create_update_mapping
   - `backend/modules/helper_functions.py` - Update function signatures and queries
   - `backend/database/dbconnect.py` - Add target connection functions
   - `backend/modules/mapper/mapper.py` - Update API endpoints

3. **Frontend:**
   - Add connection selector dropdown to Mapper SQL module
   - Add connection selector dropdown to Mapping module
   - Update save/load functions to handle target_connection_id

4. **Job Processing:**
   - Update table creation logic to use target connection
   - Update data loading logic to use target connection

---

## Benefits

✅ **Separation of Concerns** - Metadata and data are in different schemas  
✅ **Flexibility** - Users can create objects in any registered database  
✅ **Security** - Different permissions for metadata vs data operations  
✅ **Multi-tenant Support** - Each tenant can have their own data schema  
✅ **Better Organization** - Clear separation between configuration and data  

---

## Testing Checklist

- [ ] Can create mapping without target connection (uses default)
- [ ] Can create mapping with specific target connection
- [ ] Can update mapping to change target connection
- [ ] Connection dropdown shows all active connections
- [ ] Invalid connection ID is rejected with clear error
- [ ] Job creation picks up target connection from mapping
- [ ] Tables are created in target schema (not metadata schema)
- [ ] Data loads into target schema tables correctly
- [ ] Existing mappings still work (backward compatibility)

---

## Migration Strategy

1. **Phase 1:** Add database column (can be NULL initially)
2. **Phase 2:** Update backend code
3. **Phase 3:** Update frontend UI
4. **Phase 4:** Test with new mappings
5. **Phase 5:** Optionally migrate existing mappings

---

Let me know which step you'd like to start with!

