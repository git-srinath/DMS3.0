# Target Connection Implementation - COMPLETE ✅

**Date:** November 13, 2025  
**Feature:** Enable users to select target database connections for object creation and data loading

---

## 📋 Implementation Summary

The target connection feature has been successfully implemented, allowing users to specify a target database connection for each mapping. This separates metadata operations (which use the default connection) from data operations (which can use a user-selected connection).

---

## ✅ Changes Completed

### **Step 1: Database Schema Changes** ✅
*(Completed by user)*

- Added `TRGCONID` column to `DWMAPR` table
- Added `TRGCONID` column to `DWJOB` table  
- Added foreign key constraint to `DWDBCONDTLS`
- Existing records default to `NULL` for `TRGCONID`

---

### **Step 2: Backend Python Changes** ✅

#### **2.1: `backend/modules/mapper/pkgdwmapr_python.py`**

**Changes:**
- Modified `create_update_mapping()` function signature to accept `p_trgconid` parameter
- Added validation logic for `p_trgconid`:
  - Checks if value is numeric
  - Validates that `conid` exists in `DWDBCONDTLS` and is active (`curflg='Y'`)
  - Raises appropriate errors if validation fails
- Updated `SELECT` query to fetch `trgconid` from `DWMAPR`
- Updated change detection logic to compare `trgconid`
- Updated `INSERT` statement to include `trgconid` column and value

**Function Signature:**
```python
def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
                         p_stflg, p_blkprcrows, p_trgconid=None, p_user=None):
```

**Validation Logic:**
```python
# Validate p_trgconid if provided
trgconid_val = None
if p_trgconid is not None:
    # Check if numeric
    try:
        trgconid_val = int(p_trgconid)
    except (ValueError, TypeError):
        _raise_error(107, p_mapref, G_USER, 
                    "Invalid target connection ID: must be numeric")
    
    # Validate connection exists and is active
    cursor.execute("""
        SELECT COUNT(*)
        FROM DWDBCONDTLS
        WHERE conid = :1 AND curflg = 'Y'
    """, [trgconid_val])
    
    if cursor.fetchone()[0] == 0:
        _raise_error(107, p_mapref, G_USER,
                    f"Target connection ID {trgconid_val} not found or inactive")
```

---

#### **2.2: `backend/modules/helper_functions.py`**

**Changes:**
- Modified `get_mapping_ref()` query to include `TRGCONID` column
- Modified `create_update_mapping()` function signature to accept `p_trgconid` parameter
- Updated call to `pkgdwmapr.create_update_mapping()` to pass `p_trgconid`

**Updated Query:**
```python
query = """
    SELECT 
    MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
    TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID
    FROM DWMAPR WHERE MAPREF = :1  AND  CURFLG = 'Y'
"""
```

**Updated Function Signature:**
```python
def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, 
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, 
                         p_stflg, p_blkprcrows, p_trgconid, user_id):
```

---

#### **2.3: `backend/database/dbconnect.py`**

**Changes:**
- Added `create_target_connection(connection_id)` function
  - Fetches connection details from `DWDBCONDTLS` using metadata connection
  - Closes metadata connection
  - Establishes new connection to target database
  - Returns target connection object

- Added `get_connection_for_mapping(mapref)` function
  - Checks if mapping has a `trgconid` in `DWMAPR`
  - If yes: returns target connection via `create_target_connection()`
  - If no: returns metadata connection
  - Returns tuple: `(connection, is_target_connection, trgconid)`

**Function: `create_target_connection()`**
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
    # Implementation details...
```

**Function: `get_connection_for_mapping()`**
```python
def get_connection_for_mapping(mapref):
    """
    Get the appropriate database connection for a mapping
    If mapping has a target connection ID, use that; otherwise use metadata connection
    
    Args:
        mapref: Mapping reference code
    
    Returns:
        Tuple: (connection, is_target_connection, trgconid)
    """
    # Implementation details...
```

---

#### **2.4: `backend/modules/mapper/mapper.py`**

**Changes:**
- Added `/get-connections` API endpoint to fetch active connections from `DWDBCONDTLS`
- Updated `save_to_db()` to extract and pass `targetConnectionId` to `create_update_mapping()`
- Updated `get_by_reference()` to include `targetConnectionId` in the response

**New API Endpoint:**
```python
@mapper_bp.route('/get-connections', methods=['GET'])
def get_connections():
    """
    Get list of active database connections from DWDBCONDTLS
    """
    # Returns: [{'conid': '1', 'connm': 'DEV_DB', 'dbhost': 'localhost', 'dbsrvnm': 'ORCL'}, ...]
```

**Updated `save_to_db()`:**
```python
# Extract target connection ID (can be null/None for metadata connection)
target_connection_id = form_data.get('targetConnectionId')

mapid = create_update_mapping(
    conn,
    form_data['reference'],
    # ... other parameters ...
    target_connection_id,  # Target connection ID
    user_id
)
```

**Updated `get_by_reference()` response:**
```python
form_data = {
    # ... existing fields ...
    'targetConnectionId': str(main_result['TRGCONID']) if main_result.get('TRGCONID') else None,
    # ... other fields ...
}
```

---

### **Step 3: Frontend Changes** ✅

#### **3.1: `frontend/src/app/mapper_module/ReferenceForm.js`**

**Changes:**
1. **Added state for target connection:**
   ```javascript
   const [connections, setConnections] = useState([])
   ```

2. **Added `targetConnectionId` to `formData`:**
   ```javascript
   const [formData, setFormData] = useState({
     // ... existing fields ...
     targetConnectionId: null,
   })
   ```

3. **Added `useEffect` to fetch connections:**
   ```javascript
   const fetchConnections = async () => {
     try {
       const response = await fetch(
         `${process.env.NEXT_PUBLIC_API_URL}/mapper/get-connections`
       )
       if (!response.ok) {
         throw new Error('Failed to fetch connections')
       }
       const data = await response.json()
       setConnections(data)
     } catch (error) {
       console.error('Failed to load connections:', error)
       message.error(getApiErrorMessage(error, 'Failed to load database connections'))
     }
   }
   ```

4. **Added connection dropdown selector in the form:**
   - Positioned after "Bulk Process Rows" field
   - Label: "Target Connection (Optional)"
   - Default option: "Use Metadata Connection"
   - Displays connection details: `{connm} ({dbhost}/{dbsrvnm})`

   ```javascript
   <FormControl size="small" variant="outlined" className="col-span-2">
     <InputLabel id="target-connection-label">
       Target Connection (Optional)
     </InputLabel>
     <Select
       labelId="target-connection-label"
       value={formData.targetConnectionId || ''}
       onChange={(e) =>
         handleFormChange('targetConnectionId', e.target.value || null)
       }
       label="Target Connection (Optional)"
     >
       <MenuItem value="">
         <em>Use Metadata Connection</em>
       </MenuItem>
       {connections.map((conn) => (
         <MenuItem key={conn.conid} value={conn.conid}>
           {conn.connm} ({conn.dbhost}/{conn.dbsrvnm})
         </MenuItem>
       ))}
     </Select>
   </FormControl>
   ```

5. **Save/Load Logic:**
   - Save: `targetConnectionId` is automatically included via `...formData` spread operator
   - Load: `targetConnectionId` is populated from API response in `get_by_reference()`

---

## 🎯 How It Works

### **User Workflow:**

1. **User opens Mapper Module**
   - Connection dropdown is displayed in the form
   - Dropdown loads active connections from `DWDBCONDTLS`

2. **User creates/edits a mapping**
   - User can select a target connection from the dropdown
   - Or leave it as "Use Metadata Connection" (default)

3. **User saves the mapping**
   - `targetConnectionId` is sent to backend
   - Backend validates the connection ID
   - Backend stores `trgconid` in `DWMAPR` table

4. **Data processing (future implementation)**
   - When processing the mapping, the system will:
     - Check if `trgconid` is set in `DWMAPR`
     - Use `get_connection_for_mapping(mapref)` to get the appropriate connection
     - Create objects and load data into the target database
     - Use metadata connection for metadata operations

---

## 🔄 Connection Logic Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User selects mapping                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
           ┌──────────────────────────────┐
           │  get_connection_for_mapping()│
           └──────────────┬───────────────┘
                          │
                          ▼
           ┌──────────────────────────────┐
           │  Check DWMAPR.TRGCONID       │
           └──────────────┬───────────────┘
                          │
         ┌────────────────┴─────────────────┐
         │                                  │
         ▼                                  ▼
   trgconid IS NULL               trgconid HAS VALUE
         │                                  │
         ▼                                  ▼
Return metadata connection    Call create_target_connection()
         │                                  │
         │                                  ▼
         │                    Fetch connection details from
         │                         DWDBCONDTLS
         │                                  │
         │                                  ▼
         │                    Return target connection
         │                                  │
         └────────────────┬─────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Use connection for   │
              │  object creation and  │
              │  data loading         │
              └───────────────────────┘
```

---

## 📝 Database Schema

### **DWMAPR Table** (Updated)
```sql
ALTER TABLE DWMAPR ADD (
    TRGCONID NUMBER,
    CONSTRAINT FK_DWMAPR_TRGCONID FOREIGN KEY (TRGCONID)
        REFERENCES DWDBCONDTLS(CONID)
);
```

### **DWDBCONDTLS Table** (Existing)
```sql
CREATE TABLE DWDBCONDTLS (
    CONID NUMBER PRIMARY KEY,
    CONNM VARCHAR2(100),
    DBHOST VARCHAR2(100),
    DBPORT NUMBER,
    DBSRVNM VARCHAR2(100),
    USRNM VARCHAR2(100),
    PASSWD VARCHAR2(100),
    CONSTR VARCHAR2(500),
    CURFLG CHAR(1)
);
```

---

## 🧪 Testing Checklist

### **Step 4: Testing** (Ready to test)

- [ ] **Test 1: View connection dropdown**
  - Open Mapper Module
  - Verify connection dropdown appears
  - Verify it shows "Use Metadata Connection" as default
  - Verify active connections are listed

- [ ] **Test 2: Create new mapping with target connection**
  - Create a new mapping
  - Select a target connection from dropdown
  - Save the mapping
  - Verify `TRGCONID` is stored in `DWMAPR` table

- [ ] **Test 3: Create new mapping without target connection**
  - Create a new mapping
  - Leave connection as "Use Metadata Connection"
  - Save the mapping
  - Verify `TRGCONID` is NULL in `DWMAPR` table

- [ ] **Test 4: Load existing mapping with target connection**
  - Open an existing mapping that has `TRGCONID` set
  - Verify the correct connection is selected in dropdown

- [ ] **Test 5: Load existing mapping without target connection**
  - Open an existing mapping that has `TRGCONID` as NULL
  - Verify dropdown shows "Use Metadata Connection"

- [ ] **Test 6: Update mapping - change target connection**
  - Open existing mapping
  - Change target connection to a different value
  - Save
  - Verify `TRGCONID` is updated in database

- [ ] **Test 7: Update mapping - remove target connection**
  - Open mapping with target connection
  - Change to "Use Metadata Connection"
  - Save
  - Verify `TRGCONID` is set to NULL

- [ ] **Test 8: Validation - Invalid connection ID**
  - Manually set `TRGCONID` to an invalid value in database
  - Try to save mapping
  - Verify appropriate error message is shown

- [ ] **Test 9: Validation - Inactive connection**
  - Set a connection's `CURFLG` to 'N' in `DWDBCONDTLS`
  - Try to use that connection in mapping
  - Verify appropriate error message is shown

---

## 📚 API Endpoints

### **New Endpoint:**
```
GET /mapper/get-connections
```
**Response:**
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
    "dbsrvnm": "PROD"
  }
]
```

### **Modified Endpoint:**
```
GET /mapper/get-by-reference/<reference>
```
**Response (includes `targetConnectionId`):**
```json
{
  "exists": true,
  "formData": {
    "reference": "TEST_MAPPING",
    "description": "Test mapping",
    "targetConnectionId": "1",  // <-- NEW FIELD
    // ... other fields
  },
  "rows": [...]
}
```

---

## 🎉 Implementation Status

| Step | Component | Status |
|------|-----------|--------|
| 1    | Database Schema | ✅ Complete |
| 2.1  | pkgdwmapr_python.py | ✅ Complete |
| 2.2  | helper_functions.py | ✅ Complete |
| 2.3  | dbconnect.py | ✅ Complete |
| 2.4  | mapper.py | ✅ Complete |
| 3.1  | ReferenceForm.js | ✅ Complete |
| 4    | Testing | ⏳ Ready to test |

---

## 🚀 Ready for Testing!

All implementation changes are complete. The feature is now ready for end-to-end testing.

**Next Steps:**
1. Start the backend server
2. Start the frontend application
3. Test the connection selector in the Mapper Module
4. Verify database updates
5. Test all scenarios from the testing checklist above

---

## 📖 Related Documentation

- `TARGET_CONNECTION_IMPLEMENTATION_PLAN.md` - Original implementation plan
- `TARGET_CONNECTION_PROGRESS.md` - Progress tracking document
- `backend/database/dbconnect.py` - Connection management functions
- `backend/modules/mapper/pkgdwmapr_python.py` - Mapping functions
- `frontend/src/app/mapper_module/ReferenceForm.js` - Mapper UI component

---

**Implementation Date:** November 13, 2025  
**Status:** ✅ COMPLETE - Ready for Testing

