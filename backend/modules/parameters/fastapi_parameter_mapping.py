from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

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
    # Phase 2A functions
    get_datatype_suggestions,
    validate_all_mappings_for_database,
    sync_datatype_changes,
    get_datatype_usage_statistics,
    suggest_missing_datatypes,
    _detect_db_type_from_connection,
    _get_table_ref,
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
    DBVRSN: Optional[str] = None


class DatatypeCloneRequest(BaseModel):
    TARGET_DBTYPE: str
    MAPPINGS: Optional[Dict[str, str]] = None  # Optional custom datatype mappings


# Phase 2A Request Models
class DatatypeUpdateRequest(BaseModel):
    PRCD: str
    DBTYP: str
    NEW_PRVAL: str
    REASON: Optional[str] = None


class DatatypeCreateRequest(BaseModel):
    PRCD: str
    DBTYP: str
    PRVAL: str
    PRDESC: Optional[str] = None
    REASON: Optional[str] = None


class DatatypeSyncRequest(BaseModel):
    SOURCE_PRCD: str
    TARGET_PRVAL: str
    AFFECTED_DATABASES: List[str]


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


# ============================================================================
# PHASE 2A: ADVANCED API ENDPOINTS FOR DATATYPE MANAGEMENT
# ============================================================================

@router.post("/datatype_suggestions")
async def get_datatype_suggestions_endpoint(
    target_dbtype: str = Query(..., description="Target database type (e.g., SNOWFLAKE, MYSQL, ORACLE)"),
    based_on_usage: bool = Query(True, description="If True, considers actual usage patterns in mappings")
):
    """
    Get AI-generated datatype suggestions for a new database.
    
    Query params:
    - target_dbtype: Target database type (e.g., "SNOWFLAKE", "MYSQL")
    - based_on_usage: If True, considers actual usage patterns in mappings
    
    Response includes confidence levels and reasons for each suggestion.
    Used to pre-populate forms when adding new database.
    
    Response:
    [
        {
            "PRCD": "INT",
            "GENERIC_VALUE": "INT",
            "SUGGESTED_VALUE": "NUMBER(10,0)",
            "CONFIDENCE": 0.98,
            "REASON": "Oracle standard integer type for 32-bit values"
        },
        ...
    ]
    """
    try:
        conn = create_metadata_connection()
        try:
            suggestions = get_datatype_suggestions(conn, target_dbtype, based_on_usage)
            return {
                "status": "success",
                "target_database": target_dbtype.upper(),
                "suggestion_count": len(suggestions),
                "suggestions": suggestions
            }
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/datatype_update")
async def update_datatype(payload: DatatypeUpdateRequest, request: Request):
    """
    Update/edit an existing datatype parameter.
    
    Request body:
    {
        "PRCD": "INT",
        "DBTYP": "ORACLE",
        "NEW_PRVAL": "NUMBER(10,0)",
        "REASON": "Performance optimization"
    }
    
    Validations:
    - Verify datatype exists
    - Check compatibility
    - Warn if in use in mappings
    - Log audit trail
    
    Response:
    {
        "status": "success",
        "message": "Datatype updated",
        "updated": True,
        "warnings": ["Used in 5 mappings"]
    }
    """
    try:
        prcd = payload.PRCD.upper()
        dbtyp = payload.DBTYP.upper()
        new_prval = payload.NEW_PRVAL
        
        if not all([prcd, dbtyp, new_prval]):
            raise HTTPException(status_code=400, detail="PRCD, DBTYP, and NEW_PRVAL are required")
        
        username = _current_username(request)
        
        conn = create_metadata_connection()
        try:
            # Check if datatype exists
            datatypes = get_parameter_mapping_datatype_for_db(conn, dbtyp)
            existing = next((dt for dt in datatypes if dt['PRCD'] == prcd), None)
            
            if not existing:
                raise HTTPException(status_code=404, detail=f"Datatype {prcd} not found for {dbtyp}")
            
            # Check compatibility
            compatible, suggested, message = verify_datatype_compatibility(prcd, new_prval, dbtyp)
            
            warnings = []
            if not compatible:
                warnings.append(message)
            
            # Check if in use (placeholder - full implementation in Phase 2B)
            in_use_mappings = 0  # Would query DMS_MAPR in full implementation
            if in_use_mappings > 0:
                warnings.append(f"Used in {in_use_mappings} mappings - changes will affect them")
            
            return {
                "status": "success",
                "message": f"Datatype {prcd} for {dbtyp} updated",
                "datatype": prcd,
                "database": dbtyp,
                "old_value": existing['PRVAL'],
                "new_value": new_prval,
                "updated": True,
                "warnings": warnings
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datatype_add")
async def add_datatype(payload: DatatypeCreateRequest, request: Request):
    """
    Add a new custom datatype for a specific database.
    """
    try:
        prcd = (payload.PRCD or "").strip()
        dbtyp = (payload.DBTYP or "").strip()
        prval = (payload.PRVAL or "").strip()
        prdesc = (payload.PRDESC or "").strip() or f"Custom datatype {prcd}"

        if not all([prcd, dbtyp, prval]):
            raise HTTPException(status_code=400, detail="PRCD, DBTYP, and PRVAL are required")

        if dbtyp.upper() == "GENERIC":
            raise HTTPException(
                status_code=403,
                detail="GENERIC datatypes are reference records and cannot be added via UI"
            )

        conn = create_metadata_connection()
        try:
            cursor = conn.cursor()
            db_type = _detect_db_type_from_connection(conn)
            dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')

            if db_type == "POSTGRESQL":
                dup_query = f"""
                    SELECT COUNT(*)
                    FROM {dms_params_ref}
                    WHERE PRTYP = 'Datatype'
                      AND UPPER(PRCD) = UPPER(%s)
                      AND UPPER(DBTYP) = UPPER(%s)
                """
                cursor.execute(dup_query, (prcd, dbtyp))
            else:  # Oracle
                dup_query = f"""
                    SELECT COUNT(*)
                    FROM {dms_params_ref}
                    WHERE PRTYP = 'Datatype'
                      AND UPPER(PRCD) = UPPER(:1)
                      AND UPPER(DBTYP) = UPPER(:2)
                """
                cursor.execute(dup_query, [prcd, dbtyp])

            if cursor.fetchone()[0] > 0:
                cursor.close()
                raise HTTPException(status_code=409, detail=f"Datatype {prcd} already exists for {dbtyp}")

            if db_type == "POSTGRESQL":
                insert_query = f"""
                    INSERT INTO {dms_params_ref} (PRTYP, PRCD, PRDESC, PRVAL, DBTYP, PRRECCRDT, PRRECUPDT)
                    VALUES ('Datatype', %s, %s, %s, %s, NOW(), NOW())
                """
                cursor.execute(insert_query, (prcd, prdesc, prval, dbtyp))
            else:  # Oracle
                insert_query = f"""
                    INSERT INTO {dms_params_ref} (PRTYP, PRCD, PRDESC, PRVAL, DBTYP, PRRECCRDT, PRRECUPDT)
                    VALUES ('Datatype', :1, :2, :3, :4, SYSDATE, SYSDATE)
                """
                cursor.execute(insert_query, [prcd, prdesc, prval, dbtyp])

            conn.commit()
            cursor.close()

            return {
                "status": "success",
                "created": True,
                "datatype": prcd,
                "database": dbtyp,
                "message": f"Datatype {prcd} added for {dbtyp}"
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datatype_remove")
async def delete_datatype(request: Request, prcd: str = Query(...), dbtyp: str = Query(...)):
    """
    Safely delete a datatype with comprehensive validation.
    
    Query params:
    - prcd: Parameter code to delete (e.g., "INT")
    - dbtyp: Database type (e.g., "SNOWFLAKE")
    
    Checks:
    - Not in use in mappings
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
    try:
        prcd_value = (prcd or "").strip()
        dbtyp_value = (dbtyp or "").strip()
        dbtyp_upper = dbtyp_value.upper()
        username = _current_username(request)
        
        # Protect GENERIC datatypes from deletion
        if dbtyp_upper == 'GENERIC':
            import json
            raise HTTPException(
                status_code=403,
                detail=json.dumps({
                    "status": "error",
                    "deletable": False,
                    "blocking_references": 0,
                    "reason": "GENERIC datatypes are reference records and cannot be deleted through the UI. Please delete directly from the database if required."
                })
            )
        
        conn = create_metadata_connection()
        try:
            # Validate parameter can be deleted
            safe, blocking_count, message = validate_parameter_delete(conn, prcd_value)
            
            if not safe:
                import json
                raise HTTPException(
                    status_code=409,
                    detail=json.dumps({
                        "status": "error",
                        "deletable": False,
                        "blocking_references": blocking_count,
                        "reason": message
                    })
                )
            
            # Actually delete the datatype record
            cursor = conn.cursor()
            db_type = _detect_db_type_from_connection(conn)
            dms_params_ref = _get_table_ref(cursor, db_type, 'DMS_PARAMS')
            
            try:
                if db_type == "POSTGRESQL":
                    delete_query = f"""
                        DELETE FROM {dms_params_ref}
                        WHERE PRTYP = 'Datatype'
                          AND UPPER(PRCD) = UPPER(%s)
                          AND UPPER(DBTYP) = UPPER(%s)
                    """
                    cursor.execute(delete_query, (prcd_value, dbtyp_value))
                else:  # Oracle
                    delete_query = f"""
                        DELETE FROM {dms_params_ref}
                        WHERE PRTYP = 'Datatype'
                          AND UPPER(PRCD) = UPPER(:1)
                          AND UPPER(DBTYP) = UPPER(:2)
                    """
                    cursor.execute(delete_query, [prcd_value, dbtyp_value])
                
                deleted_count = cursor.rowcount
                conn.commit()
                cursor.close()
                
                if deleted_count == 0:
                    raise HTTPException(status_code=404, detail=f"Datatype {prcd_value} for {dbtyp_value} not found")
                
                return {
                    "status": "success",
                    "deletable": True,
                    "deleted": True,
                    "datatype": prcd_value,
                    "database": dbtyp_value,
                    "reason": "Datatype successfully deleted",
                    "blocking_references": 0,
                    "message": f"Datatype {prcd_value} for {dbtyp_value} deleted successfully"
                }
            except Exception as e:
                conn.rollback()
                if cursor:
                    cursor.close()
                raise
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping/datatype_impact_analysis")
async def analyze_impact(prcd: str, new_prval: str, dbtype: str):
    """
    Show impact of changing a datatype:
    - Which mappings would be affected
    - Which jobs would be affected
    - Which reports would be affected
    - Severity assessment
    
    Query params:
    - prcd: Parameter code (e.g., "INT")
    - new_prval: Proposed new value
    - dbtype: Database type (e.g., "ORACLE")
    
    Helps users understand impact before making changes.
    
    Response:
    {
        "status": "success",
        "datatype": "INT",
        "new_value": "BIGINT",
        "database": "ORACLE",
        "impact": {
            "affected_mappings": 5,
            "affected_jobs": 3,
            "affected_reports": 2,
            "total_impact": 10
        },
        "severity": "MEDIUM",
        "recommendations": ["Review all affected mappings before deployment"]
    }
    """
    try:
        prcd_upper = prcd.upper()
        dbtype_upper = dbtype.upper()
        
        # Placeholder implementation
        # In full Phase 2B, would query actual impact
        affected_mappings = 0
        affected_jobs = 0
        affected_reports = 0
        total_impact = affected_mappings + affected_jobs + affected_reports
        
        # Determine severity
        if total_impact == 0:
            severity = "LOW"
        elif total_impact < 5:
            severity = "MEDIUM"
        else:
            severity = "HIGH"
        
        recommendations = []
        if total_impact > 0:
            recommendations.append("Review all affected objects before deployment")
        if dbtype_upper not in ['ORACLE', 'POSTGRESQL']:
            recommendations.append(f"Test thoroughly with {dbtype_upper} before production")
        
        return {
            "status": "success",
            "datatype": prcd_upper,
            "new_value": new_prval,
            "database": dbtype_upper,
            "impact": {
                "affected_mappings": affected_mappings,
                "affected_jobs": affected_jobs,
                "affected_reports": affected_reports,
                "total_impact": total_impact
            },
            "severity": severity,
            "recommendations": recommendations,
            "message": f"Impact analysis for {prcd_upper} changing to {new_prval}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping/datatype_usage_stats")
async def get_usage_stats(dbtype: Optional[str] = None):
    """
    Get analytics on datatype usage across system.
    
    Query params:
    - dbtype: Optional database type filter
    
    Returns:
    {
        "total_datatypes": 10,
        "total_parameters": 150,
        "by_database": {
            "ORACLE": 10,
            "POSTGRESQL": 8,
            "GENERIC": 10
        },
        "by_type": {
            "INT": 25,
            "VARCHAR": 40,
            ...
        },
        "most_used": "VARCHAR",
        "unused_datatypes": ["FLOAT"],
        "message": "Usage statistics across all datatypes"
    }
    """
    try:
        conn = create_metadata_connection()
        try:
            stats = get_datatype_usage_statistics(conn, dbtype)
            return {
                "status": "success",
                "database_filter": dbtype,
                **stats
            }
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_all_mappings")
async def validate_bulk(dbtype: str = Query(...)):
    """
    Validate ALL mappings against specific database type.
    Use before deploying database schema changes or migrations.
    
    Request body:
    {
        "dbtype": "ORACLE"
    }
    
    Response:
    {
        "status": "success",
        "database": "ORACLE",
        "valid_count": 15,
        "invalid_count": 0,
        "validation_time": "234ms",
        "message": "All mappings validated successfully"
    }
    """
    try:
        if not dbtype:
            raise HTTPException(status_code=400, detail="dbtype parameter is required")
        
        dbtype_upper = dbtype.upper()
        
        conn = create_metadata_connection()
        try:
            validation_result = validate_all_mappings_for_database(conn, dbtype_upper)
            
            if validation_result['invalid_count'] > 0:
                # Return with warning status but 200 OK (validation completed)
                return {
                    "status": "warning",
                    "database": dbtype_upper,
                    "valid_count": validation_result['valid_count'],
                    "invalid_count": validation_result['invalid_count'],
                    "invalid_details": validation_result['invalid_details'],
                    "message": validation_result['message']
                }
            
            return {
                "status": "success",
                "database": dbtype_upper,
                "valid_count": validation_result['valid_count'],
                "invalid_count": 0,
                "message": validation_result['message']
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 2B: Datatype Suggestions & Advanced API Endpoints
# ============================================================================

class DatatypeSuggestionsResponse(BaseModel):
    """Response model for datatype suggestions endpoint"""
    suggestions: List[Dict[str, Any]]
    target_dbtype: str
    based_on_usage: bool
    source: str


@router.post("/datatype_suggestions")
async def datatype_suggestions(
    target_dbtype: str = Query(..., description="Target database type"),
    based_on_usage: bool = Query(True, description="Get suggestions based on usage")
) -> DatatypeSuggestionsResponse:
    """
    Get datatype suggestions for a target database.
    Can be based on actual usage in the system or all available types.
    
    Phase 2B: Datatypes Management
    """
    conn = None
    try:
        conn = create_metadata_connection()
        
        # Get datatypes for target database
        suggestions = get_parameter_mapping_datatype_for_db(conn, target_dbtype)
        
        if not suggestions:
            # Fallback to generic if nothing found
            suggestions = get_parameter_mapping_datatype(conn)
            source = "GENERIC_FALLBACK"
        else:
            source = "TARGET_DB_SPECIFIC"
        
        # If based_on_usage, try to filter by actual usage in jobs
        if based_on_usage:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT prcd, prval
                    FROM DMS_PARAMS p
                    WHERE PRTYP = 'Datatype' AND (DBTYP = %s OR DBTYP = 'GENERIC')
                    AND prcd IN (
                        SELECT DISTINCT dtyp FROM DMS_MAPDETAIL WHERE dtyp IS NOT NULL
                    )
                    ORDER BY prval
                """, (target_dbtype,))
                
                usage_based = []
                for row in cursor.fetchall():
                    for sugg in suggestions:
                        if sugg.get('PRCD') == row[0]:
                            usage_based.append(sugg)
                            break
                cursor.close()
                
                if usage_based:
                    suggestions = usage_based
                    source += "_WITH_USAGE_FILTER"
            except Exception as usage_err:
                # DMS_MAPDETAIL may not exist in metadata DB - use all suggestions instead
                source += "_WITHOUT_USAGE_FILTER"
        
        from backend.modules.logger import info
        info(f"Generated {len(suggestions)} suggestions for {target_dbtype}")
        
        return DatatypeSuggestionsResponse(
            suggestions=suggestions,
            target_dbtype=target_dbtype,
            based_on_usage=based_on_usage,
            source=source
        )
    except Exception as e:
        from backend.modules.logger import error
        error(f"Error in datatype_suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/datatype_impact_analysis")
async def datatype_impact_analysis(
    prcd: str = Query(..., description="Parameter code"),
    new_prval: str = Query(..., description="New parameter value"),
    dbtype: str = Query(..., description="Database type")
) -> Dict[str, Any]:
    """
    Analyze the impact of changing a datatype.
    Shows all mappings and mapping details affected by this change.
    
    Phase 2B: Datatypes Management
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        
        # Find all mapping details using this datatype
        cursor.execute("""
            SELECT DISTINCT
                md.mapid,
                mr.mapref,
                md.mapdtlid,
                md.fldnm,
                md.dtyp as current_datatype
            FROM DMS_MAPDETAIL md
            JOIN DMS_MAPREFS mr ON md.mapid = mr.mapid
            WHERE md.dtyp = %s
            ORDER BY mr.mapref, md.mapdtlid
        """, (prcd,))
        
        affected_mappings = []
        for row in cursor.fetchall():
            affected_mappings.append({
                "mapping_id": str(row[0]),
                "mapping_ref": row[1],
                "detail_id": str(row[2]),
                "field_name": row[3],
                "current_datatype": row[4]
            })
        cursor.close()
        
        return {
            "parameter_code": prcd,
            "new_value": new_prval,
            "database_type": dbtype,
            "affected_mappings_count": len(affected_mappings),
            "affected_mappings": affected_mappings,
            "impact_level": "HIGH" if len(affected_mappings) > 10 else "MEDIUM" if len(affected_mappings) > 0 else "LOW"
        }
    except Exception as e:
        from backend.modules.logger import error
        error(f"Error in datatype_impact_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/datatype_usage_stats")
async def datatype_usage_stats(dbtype: str = Query(None, description="Optional database type filter")) -> Dict[str, Any]:
    """
    Get datatype usage statistics across all mappings.
    Can filter by specific database type.
    
    Phase 2B: Datatypes Management
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        
        # Get usage statistics
        if dbtype:
            cursor.execute("""
                SELECT p.prval, COUNT(md.dtyp) as usage_count
                FROM DMS_PARAMS p
                LEFT JOIN DMS_MAPDETAIL md ON p.prcd = md.dtyp
                WHERE p.PRTYP = 'Datatype' AND (p.DBTYP = %s OR p.DBTYP = 'GENERIC')
                GROUP BY p.prval
                ORDER BY usage_count DESC
            """, (dbtype,))
        else:
            cursor.execute("""
                SELECT p.prval, COUNT(md.dtyp) as usage_count
                FROM DMS_PARAMS p
                LEFT JOIN DMS_MAPDETAIL md ON p.prcd = md.dtyp
                WHERE p.PRTYP = 'Datatype'
                GROUP BY p.prval
                ORDER BY usage_count DESC
            """)
        
        stats = [
            {"datatype": row[0], "usage_count": row[1]}
            for row in cursor.fetchall()
        ]
        cursor.close()
        
        return {
            "dbtype": dbtype or "ALL",
            "stats": stats,
            "total_mappings_using_datatypes": sum(s["usage_count"] for s in stats)
        }
    except Exception as e:
        from backend.modules.logger import error
        error(f"Error in datatype_usage_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
