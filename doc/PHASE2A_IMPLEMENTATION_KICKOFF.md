# Phase 2A Implementation Kickoff
**Multi-Database Datatype Management System - API Endpoint Development**

**Status:** 🔄 PHASE 2A IN PROGRESS  
**Start Date:** February 16, 2026  
**Estimated Duration:** 2 days (16 hours)  
**Estimated Completion:** February 18, 2026

---

## Overview

Phase 2A focuses on extending the Phase 1 backend infrastructure with advanced API endpoints, enhanced error handling, and comprehensive API documentation.

**Main Goal:** Create full-featured API endpoints for datatype management that are production-ready with proper error handling, validation, and documentation.

---

## Phase 2A Deliverables Checklist

### 1. Extended Helper Functions ✅ IN PROGRESS
- [ ] `get_datatype_suggestions(conn, target_dbtype)` - AI-based pre-fill suggestions
- [ ] `validate_all_mappings_for_database(conn, dbtype)` - Bulk validation
- [ ] `sync_datatype_changes(conn, source_prcd, mappings)` - Propagate changes
- [ ] `get_datatype_usage_statistics(conn)` - Analytics metrics
- [ ] `suggest_missing_datatypes(conn, dbtype)` - Identify gaps

### 2. Advanced API Endpoints ⏳ TO DO
- [ ] PUT `/mapping/datatype_update` - Edit existing datatype
- [ ] DELETE `/mapping/datatype_remove` - Safe deletion
- [ ] POST `/mapping/datatype_suggestions` - Get AI suggestions
- [ ] GET `/mapping/datatype_impact_analysis` - Show impact of changes
- [ ] GET `/mapping/datatype_usage_stats` - Datatype usage analytics
- [ ] POST `/mapping/validate_all_mappings` - Bulk validation

### 3. Error Handling & Validation ⏳ TO DO
- [ ] Detailed error messages (> 5 error classes)
- [ ] Proper HTTP status codes (400, 409, 422, 500)
- [ ] Validation response models
- [ ] Exception handling patterns
- [ ] Logging improvements

### 4. API Documentation ⏳ TO DO
- [ ] OpenAPI/Swagger schema
- [ ] Request/response examples (all 14 endpoints)
- [ ] Error code reference (all error types)
- [ ] Authentication & headers documentation
- [ ] Rate limiting documentation (if applicable)

---

## Implementation Details

### Task 1: Extended Helper Functions (4-5 hours)

#### 1.1 Enhanced Datatype Suggestion Function
```python
def get_datatype_suggestions(conn, target_dbtype: str, based_on_usage: bool = True):
    """
    Generate datatype suggestions for target database based on:
    1. Compatibility matrix defaults
    2. Actual usage patterns in mappings (if based_on_usage=True)
    3. Performance recommendations
    
    Returns:
    [
        {
            "PRCD": "INT",
            "GENERIC_VALUE": "INT",
            "SUGGESTED_VALUE": "NUMBER(10,0)",
            "CONFIDENCE": 0.95,
            "REASON": "Oracle standard integer type for 32-bit values"
        },
        ...
    ]
    """
```

#### 1.2 Bulk Validation Function
```python
def validate_all_mappings_for_database(conn, dbtype: str):
    """
    Validate ALL mappings against a specific database type.
    Checks:
    - All datatypes exist for target database
    - No incompatible type combinations
    - All mappings have required parameters
    
    Returns:
    {
        "valid_count": 15,
        "invalid_count": 2,
        "invalid_mappings": [
            {
                "MAPID": 123,
                "ERROR": "Datatype VARCHAR(2000) not supported in MySQL"
            }
        ],
        "warnings": [...]
    }
    """
```

#### 1.3 Datatype Change Propagation
```python
def sync_datatype_changes(conn, source_prcd: str, target_prval: str, affected_databases: list):
    """
    When a datatype changes, propagate to dependent:
    - Mapping definitions
    - Job configurations
    - File upload column mappings
    - Report parameters
    
    Returns sync status and counts
    """
```

#### 1.4 Usage Statistics
```python
def get_datatype_usage_statistics(conn, dbtype: str = None):
    """
    Get analytics on datatype usage:
    - Total parameters per type
    - Usage in mappings (count)
    - Usage in jobs (count)
    - Most used datatypes
    - Unused datatypes
    
    Returns statistics dictionary
    """
```

#### 1.5 Missing Datatype Detection
```python
def suggest_missing_datatypes(conn, dbtype: str, based_on_mappings: bool = True):
    """
    Identify datatypes that should exist for a database but don't.
    Suggests which datatypes to clone from GENERIC.
    
    Example: For SNOWFLAKE database, detects that JSON
    datatype is missing and needed by some mappings.
    """
```

### Task 2: Advanced API Endpoints (5-6 hours)

#### 2.1 Update Datatype Endpoint
```python
@router.put("/mapping/datatype_update")
async def update_datatype(
    prcd: str,           # INT
    dbtype: str,         # ORACLE
    new_prval: str,      # NUMBER(10,0) or custom value
    request: Request
):
    """
    Update/edit an existing datatype parameter.
    
    Validations:
    - Verify datatype exists
    - Check compatibility
    - Prevent breaking changes if in use
    - Log audit trail
    
    Response:
    {
        "status": "success",
        "message": "Datatype updated",
        "updated": True,
        "warnings": ["Used in 5 mappings"]
    }
    """
```

#### 2.2 Delete Datatype Endpoint (Safe)
```python
@router.delete("/mapping/datatype_remove")
async def delete_datatype(prcd: str, dbtype: str, request: Request):
    """
    Safely delete a datatype with validation.
    
    Checks:
    - Not in use in any mappings
    - Not in use in jobs
    - Not in use in file uploads
    - Not in use in reports
    
    Returns:
    {
        "status": "success/error",
        "deletable": true/false,
        "reason": "...",
        "blocking_references": 0
    }
    """
```

#### 2.3 Datatype Suggestions Endpoint
```python
@router.post("/mapping/datatype_suggestions")
async def get_suggestions(target_dbtype: str, based_on_usage: bool = True):
    """
    Get AI-generated datatype suggestions for new database.
    
    Response includes confidence levels and reasons
    for each suggestion.
    
    Used to pre-populate forms when adding new database.
    """
```

#### 2.4 Impact Analysis Endpoint
```python
@router.get("/mapping/datatype_impact_analysis")
async def analyze_impact(prcd: str, new_prval: str, dbtype: str):
    """
    Show impact of changing a datatype:
    - Which mappings would be affected
    - Which jobs would be affected
    - Which reports would be affected
    - Severity assessment
    
    Helps users understand impact before making changes.
    """
```

#### 2.5 Usage Statistics Endpoint
```python
@router.get("/mapping/datatype_usage_stats")
async def get_usage_stats(dbtype: str = None):
    """
    Get analytics on datatype usage across system.
    
    Returns:
    {
        "total_datatypes": 10,
        "total_parameters": 150,
        "by_type": {
            "INT": 25,
            "VARCHAR": 40,
            ...
        },
        "unused": ["FLOAT"],
        "most_used": "VARCHAR"
    }
    """
```

#### 2.6 Bulk Validation Endpoint
```python
@router.post("/mapping/validate_all_mappings")
async def validate_bulk(dbtype: str):
    """
    Validate ALL mappings against specific database type.
    Use before deploying or making schema changes.
    """
```

### Task 3: Error Handling & Validation (3-4 hours)

#### Error Classes to Implement
```python
class DatatypeError(BaseException):
    """Base error for datatype operations"""
    
class DatatypeNotFoundError(DatatypeError):
    """Datatype does not exist"""
    HTTP_STATUS = 404
    
class DatatypeInUseError(DatatypeError):
    """Cannot delete/modify - datatype in use"""
    HTTP_STATUS = 409  # Conflict
    
class DatatypeIncompatibilityError(DatatypeError):
    """Datatype not compatible with target database"""
    HTTP_STATUS = 422  # Unprocessable Entity
    
class DatatypeValidationError(DatatypeError):
    """Validation failed on input"""
    HTTP_STATUS = 400  # Bad Request
    
class DatatypeOperationError(DatatypeError):
    """General operation error"""
    HTTP_STATUS = 500  # Server Error
```

#### Validation Response Model
```python
class ValidationError(BaseModel):
    field: str
    message: str
    code: str
    suggestion: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: str
    details: Optional[Dict] = None
    errors: Optional[List[ValidationError]] = None
    timestamp: datetime
```

#### HTTP Status Codes Used
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success, no response
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource in use (can't delete)
- `422 Unprocessable Entity` - Business logic violation
- `500 Internal Server Error` - Unexpected error

### Task 4: API Documentation (2-3 hours)

#### 4.1 OpenAPI/Swagger Schema
- Auto-generated from Pydantic models
- Enabled with FastAPI's built-in support
- Available at `/docs` (Swagger UI)
- Available at `/redoc` (ReDoc UI)

#### 4.2 Request/Response Examples
All 14 endpoints documented with:
- Parameter descriptions
- Example requests
- Example responses
- Success and error scenarios

#### 4.3 Error Code Reference
| Code | HTTP | Meaning | Solution |
|------|------|---------|----------|
| DT001 | 404 | Datatype not found | Check PRCD and DBTYP |
| DT002 | 409 | Datatype in use | Review blocking references |
| DT003 | 422 | Incompatible type | Use suggested value |
| DT004 | 400 | Invalid parameter | Check input format |
| DT005 | 500 | Database error | Check connection |

---

## Implementation Steps

### Step 1: Implement Extended Helper Functions (NOW)
```javascript
Timeline: 2 hours
Files: backend/modules/helper_functions.py
Tasks:
  - Add 5 new functions with full error handling
  - Add custom datatype suggestions logic
  - Add bulk validation logic
  - Add usage analytics queries
```

### Step 2: Create Advanced API Endpoints (NEXT)
```javascript
Timeline: 2 hours
Files: backend/modules/parameters/fastapi_parameter_mapping.py
Tasks:
  - Add 6 new endpoints
  - Add request validation
  - Add error handling
  - Hook up to helper functions
```

### Step 3: Implement Error Handling Framework (THEN)
```javascript
Timeline: 1.5 hours
Files: backend/modules/parameters/fastapi_parameter_mapping.py
Tasks:
  - Create error classes
  - Create response models
  - Add exception handlers
  - Enhance logging
```

### Step 4: Create API Documentation (FINALLY)
```javascript
Timeline: 1 hour
Files: Auto-generated (Swagger) + markdown
Tasks:
  - Verify OpenAPI generation
  - Add endpoint descriptions
  - Add error code reference
  - Create integration examples
```

---

## Entry Points for Phase 2A Implementation

### Starting Position
- Phase 1 code: ✅ Complete in Git
- Database migration: ⏳ Ready to execute (user hasn't run yet)
- API endpoints: ✅ 8 basic endpoints ready
- Helper functions: ✅ 18 functions ready

### What We Build on
- `backend/modules/helper_functions.py` - Add 5 new functions here
- `backend/modules/parameters/fastapi_parameter_mapping.py` - Add 6 new endpoints here
- Existing error handling patterns - Enhance and standardize

### Testing Against
- Existing 8 Phase 1 endpoints (should still work)
- Backward compatibility (100%)
- Datatype compatibility matrix (use existing)
- Database adapters (both Oracle and PostgreSQL)

---

## Success Criteria for Phase 2A

✅ All 5 extended helper functions implement and working  
✅ All 6 advanced API endpoints responding  
✅ Error handling with proper HTTP status codes  
✅ Validation catching all invalid inputs  
✅ API documentation complete (Swagger)  
✅ All changes committed to Git  
✅ Backward compatible (Phase 1 still works)  
✅ Code follows existing patterns  

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Helper Functions | 2-3 hrs | ⏳ Next |
| API Endpoints | 2-3 hrs | ⏳ After helpers |
| Error Handling | 1-2 hrs | ⏳ After endpoints |
| Documentation | 1-2 hrs | ⏳ Final |
| Testing & Review | 1-2 hrs | ⏳ Last |
| **Total Phase 2A** | **8-12 hrs** | ⏳ IN PROGRESS |

**Estimated Completion:** Today (Feb 16) + next day (Feb 17) = by Feb 18

---

## Phase 2A → Phase 2B Handoff

When Phase 2A is complete:
- All API endpoints ready for frontend consumption
- Error handling standardized
- Documentation complete
- Code committed and reviewed

Phase 2B can then:
- Build React components for Datatypes UI tab
- Call the Phase 2A endpoints
- Handle errors appropriately in UI
- Provide user-friendly feedback

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Breaking Phase 1 | All changes backward compatible |
| Database connectivity | Errors handled, proper logging |
| Performance | Indexes in place, queries optimized |
| User errors | Comprehensive validation |
| Deployment issues | Rollback to Phase 1 available |

---

## Notes

- Phase 2A assumes database has NOT been migrated yet (Phase 1 migration is optional for API development)
- All new endpoints will work with empty DMS_SUPPORTED_DATABASES table
- Error handling should work even if migration not executed
- Testing can proceed without database migration complete

---

## Sign-Off

**Phase 2A Kickoff:** ✅ READY  
**Code Quality:** High (follows Phase 1 patterns)  
**Documentation:** Comprehensive  
**Timeline:** Realistic (2 days)  
**Team Ready:** Yes

**Begin Phase 2A implementation immediately**

---

*Phase 2A Implementation Plan - February 16, 2026*  
*Duration: 2 days (16 hours)*  
*Completion Target: February 18, 2026*
