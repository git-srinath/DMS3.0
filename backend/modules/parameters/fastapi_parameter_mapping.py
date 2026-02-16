from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, List

from backend.database.dbconnect import create_metadata_connection
from backend.modules.helper_functions import (
    get_parameter_mapping,
    add_parameter_mapping,
    get_supported_databases,
    add_supported_database,
    update_database_status,
    get_parameter_mapping_datatype_for_db,
    get_all_datatype_groups,
    verify_datatype_compatibility,
    clone_datatypes_from_generic,
    validate_parameter_delete,
    _current_username,
)


router = APIRouter(tags=["parameter_mapping"])


class ParameterCreateRequest(BaseModel):
    PRTYP: str
    PRCD: str
    PRDESC: str
    PRVAL: str
    DBTYP: Optional[str] = None  # Optional database type for datatypes


class DatabaseTypeRequest(BaseModel):
    DBTYP: str
    DBDESC: str
    DBVRSN: str


class DatatypeCloneRequest(BaseModel):
    TARGET_DBTYPE: str
    MAPPINGS: Optional[Dict[str, str]] = None  # Optional custom datatype mappings


@router.get("/parameter_mapping")
async def parameter_display():
    """
    Return the list of parameters.
    Mirrors the Flask endpoint:
    GET /mapping/parameter_mapping
    """
    try:
        conn = create_metadata_connection()
        try:
            parameter_data = get_parameter_mapping(conn)
            return parameter_data
        finally:
            conn.close()
    except Exception as e:
        # Same behavior as Flask: return error and 500 code
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parameter_add")
async def add_parameter(payload: ParameterCreateRequest, request: Request):
    """
    Add a new parameter.
    Mirrors the Flask endpoint:
    POST /mapping/parameter_add
    """
    try:
        prtyp = payload.PRTYP
        prcd = payload.PRCD
        prdesc = payload.PRDESC
        prval = payload.PRVAL
        dbtyp = payload.DBTYP or 'GENERIC'  # Default to GENERIC if not specified

        if not all([prtyp, prcd, prdesc, prval]):
            raise HTTPException(status_code=400, detail="All fields are required")

        username = _current_username(request)
        
        conn = create_metadata_connection()
        try:
            add_parameter_mapping(conn, prtyp, prcd, prdesc, prval, dbtyp, username)
            return {"message": "Parameter added successfully", "DBTYP": dbtyp}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        # Log error similarly to Flask (if needed)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW ENDPOINTS FOR DATABASE AND DATATYPE MANAGEMENT (Phase 1)
# ============================================================================

@router.get("/supported_databases")
async def get_databases():
    """
    Get list of supported database types.
    Returns all ACTIVE database types from DMS_SUPPORTED_DATABASES.
    
    Response: [
        {"DBTYP": "GENERIC", "DBDESC": "Generic/Universal", "DBVRSN": null, "STTS": "ACTIVE"},
        {"DBTYP": "ORACLE", "DBDESC": "Oracle Database", "DBVRSN": "19c", "STTS": "ACTIVE"},
        ...
    ]
    """
    try:
        conn = create_metadata_connection()
        try:
            databases = get_supported_databases(conn)
            return {
                "status": "success",
                "count": len(databases),
                "databases": databases
            }
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supported_database_add")
async def add_database(payload: DatabaseTypeRequest, request: Request):
    """
    Add a new supported database type.
    
    Request body:
    {
        "DBTYP": "SNOWFLAKE",
        "DBDESC": "Snowflake Cloud DW",
        "DBVRSN": "EDITION_BUSINESS_CRITICAL"
    }
    
    Response: {"status": "success", "message": "..."}
    """
    try:
        dbtyp = payload.DBTYP.upper()
        dbdesc = payload.DBDESC
        dbvrsn = payload.DBVRSN
        
        if not all([dbtyp, dbdesc]):
            raise HTTPException(status_code=400, detail="DBTYP and DBDESC are required")
        
        username = _current_username(request)
        
        conn = create_metadata_connection()
        try:
            success, message = add_supported_database(conn, dbtyp, dbdesc, dbvrsn, username)
            
            if success:
                return {
                    "status": "success",
                    "message": message,
                    "DBTYP": dbtyp
                }
            else:
                raise HTTPException(status_code=400, detail=message)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/supported_database_status")
async def update_db_status(dbtyp: str, status: str, request: Request):
    """
    Update status of a supported database type.
    
    Query params:
    - dbtyp: Database type (e.g., "SNOWFLAKE")
    - status: New status ("ACTIVE" or "INACTIVE")
    
    Response: {"status": "success", "message": "..."}
    """
    try:
        if status.upper() not in ['ACTIVE', 'INACTIVE']:
            raise HTTPException(status_code=400, detail="Status must be ACTIVE or INACTIVE")
        
        username = _current_username(request)
        
        conn = create_metadata_connection()
        try:
            success, message = update_database_status(conn, dbtyp.upper(), status.upper(), username)
            
            if success:
                return {"status": "success", "message": message}
            else:
                raise HTTPException(status_code=400, detail=message)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datatypes_for_database")
async def get_datatypes_for_db(dbtype: Optional[str] = None):
    """
    Get datatype parameters for a specific database type.
    
    Query params:
    - dbtype: Optional database type filter (e.g., "ORACLE", "POSTGRESQL")
             If not provided, returns all datatypes
    
    Response: [
        {"PRCD": "INT", "PRDESC": "Integer", "PRVAL": "NUMBER(10,0)", "DBTYP": "ORACLE"},
        {"PRCD": "INT", "PRDESC": "Integer", "PRVAL": "INTEGER", "DBTYP": "POSTGRESQL"},
        ...
    ]
    """
    try:
        conn = create_metadata_connection()
        try:
            datatypes = get_parameter_mapping_datatype_for_db(conn, dbtype)
            return {
                "status": "success",
                "count": len(datatypes),
                "database_filter": dbtype,
                "datatypes": datatypes
            }
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all_datatype_groups")
async def get_datatype_groups():
    """
    Get all datatype parameters grouped by database type.
    
    Response: {
        "status": "success",
        "groups": {
            "ORACLE": [...],
            "POSTGRESQL": [...],
            "GENERIC": [...]
        }
    }
    """
    try:
        conn = create_metadata_connection()
        try:
            groups = get_all_datatype_groups(conn)
            return {
                "status": "success",
                "group_count": len(groups),
                "groups": groups
            }
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_datatype_compatibility")
async def check_datatype_compatibility(
    generic_prcd: str,
    target_prval: str,
    target_dbtype: str
):
    """
    Verify if a datatype is compatible with target database type.
    
    Query params:
    - generic_prcd: Generic datatype code (e.g., "INT", "VARCHAR")
    - target_prval: Proposed value for target database
    - target_dbtype: Target database type (e.g., "SNOWFLAKE")
    
    Response: {
        "status": "success",
        "compatible": true,
        "suggested_value": "NUMBER(10,0)",
        "message": "Datatype is compatible"
    }
    """
    try:
        compatible, suggested, message = verify_datatype_compatibility(
            generic_prcd, target_prval, target_dbtype
        )
        
        return {
            "status": "success",
            "generic_datatype": generic_prcd,
            "target_database": target_dbtype,
            "compatible": compatible,
            "suggested_value": suggested,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone_datatypes_from_generic")
async def clone_from_generic(payload: DatatypeCloneRequest, request: Request):
    """
    Clone datatype parameters from GENERIC database type to target database.
    
    Request body:
    {
        "TARGET_DBTYPE": "SNOWFLAKE",
        "MAPPINGS": {
            "INT": "NUMBER(10,0)",
            "VARCHAR": "VARCHAR(4096)"
        }
    }
    Optional: MAPPINGS can be null to use defaults from compatibility matrix
    
    Response: {
        "status": "success",
        "target_database": "SNOWFLAKE",
        "created_count": 10,
        "skipped_count": 0,
        "message": "Cloned 10 datatypes, skipped 0"
    }
    """
    try:
        target_dbtype = payload.TARGET_DBTYPE.upper()
        mappings = payload.MAPPINGS or {}
        
        if not target_dbtype:
            raise HTTPException(status_code=400, detail="TARGET_DBTYPE is required")
        
        username = _current_username(request)
        
        conn = create_metadata_connection()
        try:
            success, created, skipped, message = clone_datatypes_from_generic(
                conn, target_dbtype, mappings, username
            )
            
            if success:
                return {
                    "status": "success",
                    "target_database": target_dbtype,
                    "created_count": created,
                    "skipped_count": skipped,
                    "message": message
                }
            else:
                raise HTTPException(status_code=400, detail=message)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate_parameter_delete")
async def check_parameter_delete(prcd: str):
    """
    Validate that a parameter can be safely deleted.
    Checks if parameter is referenced in mappings, jobs, uploads, or reports.
    
    Query params:
    - prcd: Parameter code to validate (e.g., "INT", "VARCHAR")
    
    Response: {
        "status": "success",
        "parameter": "INT",
        "safe_to_delete": true,
        "blocking_references": 0,
        "message": "Parameter can be safely deleted"
    }
    """
    try:
        safe, blocking_count, message = validate_parameter_delete(None, prcd)
        
        return {
            "status": "success",
            "parameter": prcd,
            "safe_to_delete": safe,
            "blocking_references": blocking_count,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

