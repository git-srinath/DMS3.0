"""
FastAPI Router for File Upload Module
Provides endpoints for file upload, configuration, and data loading.
"""
import os
import tempfile
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Path as PathParam, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from datetime import date

from backend.database.dbconnect import create_metadata_connection, create_target_connection
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.helper_functions import _get_table_ref
from backend.modules.logger import info, error, warning
from backend.modules.jobs.pkgdwprc_python import _calculate_next_run_time

from .file_parser import FileParserManager
from .file_upload_service import (
    create_update_file_upload,
    create_update_file_upload_detail,
    delete_file_upload,
    activate_deactivate_file_upload,
    get_file_upload_details,
)
from .file_upload_executor import FileUploadExecutor, LoadMode, get_file_upload_config
from .table_creator import _check_table_exists

router = APIRouter(tags=["file_upload"])

# Initialize file parser manager
parser_manager = FileParserManager()

# File upload directory
UPLOAD_DIR = os.path.join("data", "file_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===== Pydantic Models =====

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    message: str
    file_info: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None
    preview: Optional[List[Dict[str, Any]]] = None


class FileUploadConfig(BaseModel):
    """File upload configuration model."""
    flupldref: str
    fluplddesc: Optional[str] = None
    flnm: Optional[str] = None
    flpth: Optional[str] = None
    fltyp: Optional[str] = None
    trgconid: Optional[int] = None
    trgschm: Optional[str] = None
    trgtblnm: Optional[str] = None
    trnctflg: Optional[str] = "N"
    hdrrwcnt: Optional[int] = 0
    ftrrwcnt: Optional[int] = 0
    hdrrwpttrn: Optional[str] = None
    ftrrwpttrn: Optional[str] = None
    frqcd: Optional[str] = None
    stflg: Optional[str] = "N"
    batch_size: Optional[int] = 1000  # Batch size for data loading
    crtdby: Optional[str] = None
    flupldid: Optional[int] = None  # ID for updates


class FileUploadScheduleRequest(BaseModel):
    """Request model for creating/updating a file upload schedule (DMS_FLUPLD_SCHD)."""
    flupldref: str
    frqncy: str                      # DL, WK, MN, HY, YR, ID
    tm_prm: Optional[str] = None     # e.g. DL_10:30, WK_MON_10:30, MN_15_10:30
    stts: Optional[str] = "ACTIVE"   # ACTIVE / PAUSED / etc.
    strtdt: Optional[date] = None    # Optional start date (YYYY-MM-DD)
    enddt: Optional[date] = None     # Optional end date (YYYY-MM-DD)


# ===== Helper Functions =====

def _get_table_name(cursor, db_type: str, table_name: str) -> str:
    """Get properly formatted table name based on database type."""
    return _get_table_ref(cursor, db_type, table_name)


# ===== API Endpoints =====

@router.post("/upload-file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    preview_rows: int = Query(10, ge=1, le=100, description="Number of preview rows")
):
    """
    Upload and parse a file (CSV, Excel, JSON, etc.).
    Returns file information, columns, and preview data.
    """
    temp_file_path = None
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Save uploaded file to temporary location
        file_ext = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=UPLOAD_DIR) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        info(f"File uploaded: {file.filename} -> {temp_file_path}")
        
        # Get file info
        file_info = parser_manager.get_file_info(temp_file_path)
        
        # Get columns
        columns = parser_manager.get_columns(temp_file_path)
        
        # Get preview
        preview_df = parser_manager.preview_file(temp_file_path, rows=preview_rows)
        preview = preview_df.to_dict('records')
        
        # Convert preview values to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                else:
                    row[key] = str(value)
        
        return FileUploadResponse(
            success=True,
            message=f"File uploaded and parsed successfully: {file.filename}",
            file_info={
                **file_info,
                "original_filename": file.filename,
                "saved_path": temp_file_path
            },
            columns=columns,
            preview=preview
        )
    
    except ValueError as e:
        error(f"File parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        # Note: We keep the file for now - it will be used when saving configuration
        # In production, you might want to clean up old files periodically
        pass


@router.get("/get-all-uploads")
async def get_all_uploads():
    """Get all file upload configurations with schedule information."""
    conn = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        
        table_name = _get_table_name(cursor, db_type, "DMS_FLUPLD")
        
        # Try to include schedule info, fallback if schedule table doesn't exist
        include_schedule = True
        try:
            schedule_table = _get_table_ref(cursor, db_type, "DMS_FLUPLD_SCHD")
        except Exception:
            include_schedule = False
            warning("DMS_FLUPLD_SCHD table not found, schedule information will not be included")
        
        if include_schedule:
            try:
                if db_type == "POSTGRESQL":
                    query = f"""
                        SELECT u.flupldid, u.flupldref, u.fluplddesc, u.flnm, u.fltyp, u.trgconid, 
                               u.trgschm, u.trgtblnm, u.trnctflg, u.stflg, u.crtdt, u.lstrundt, u.nxtrundt,
                               s.schdid, s.frqncy, s.stts as schd_stts, s.nxt_run_dt as schd_nxt_run_dt
                        FROM {table_name} u
                        LEFT JOIN {schedule_table} s ON u.flupldref = s.flupldref AND s.curflg = 'Y' AND s.stts = 'ACTIVE'
                        WHERE u.curflg = 'Y'
                        ORDER BY u.flupldref
                    """
                    cursor.execute(query)
                else:  # Oracle, etc.
                    query = f"""
                        SELECT u.FLUPLDID, u.FLUPLDREF, u.FLUPLDDESC, u.FLNM, u.FLTYP, u.TRGCONID, 
                               u.TRGSCHM, u.TRGTBLNM, u.TRNCTFLG, u.STFLG, u.CRTDT, u.LSTRUNDT, u.NXTRUNDT,
                               s.SCHDID, s.FRQNCY, s.STTS as SCHD_STTS, s.NXT_RUN_DT as SCHD_NXT_RUN_DT
                        FROM {table_name} u
                        LEFT JOIN {schedule_table} s ON u.FLUPLDREF = s.FLUPLDREF AND s.CURFLG = 'Y' AND s.STTS = 'ACTIVE'
                        WHERE u.CURFLG = 'Y'
                        ORDER BY u.FLUPLDREF
                    """
                    cursor.execute(query)
            except Exception as join_error:
                # If JOIN fails (e.g., table doesn't exist), fallback to query without schedule
                warning(f"Failed to join schedule table: {str(join_error)}, falling back to query without schedule")
                include_schedule = False
        
        if not include_schedule:
            # Fallback query without schedule join
            if db_type == "POSTGRESQL":
                query = f"""
                    SELECT flupldid, flupldref, fluplddesc, flnm, fltyp, trgconid, 
                           trgschm, trgtblnm, trnctflg, stflg, crtdt, lstrundt, nxtrundt
                    FROM {table_name}
                    WHERE curflg = 'Y'
                    ORDER BY flupldref
                """
                cursor.execute(query)
            else:  # Oracle, etc.
                query = f"""
                    SELECT FLUPLDID, FLUPLDREF, FLUPLDDESC, FLNM, FLTYP, TRGCONID, 
                           TRGSCHM, TRGTBLNM, TRNCTFLG, STFLG, CRTDT, LSTRUNDT, NXTRUNDT
                    FROM {table_name}
                    WHERE CURFLG = 'Y'
                    ORDER BY FLUPLDREF
                """
                cursor.execute(query)
        
        columns = [desc[0].lower() for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Add null schedule fields if schedule table wasn't included
        if not include_schedule:
            for row in rows:
                row['schdid'] = None
                row['frqncy'] = None
                row['schd_stts'] = None
                row['schd_nxt_run_dt'] = None
        
        cursor.close()
        return {"success": True, "data": rows}
    
    except Exception as e:
        error(f"Error fetching uploads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching uploads: {str(e)}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/get-by-reference/{flupldref}")
async def get_by_reference(flupldref: str = PathParam(..., description="File upload reference")):
    """Get file upload configuration by reference."""
    conn = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        
        table_name = _get_table_name(cursor, db_type, "DMS_FLUPLD")
        
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, 
                       trgschm, trgtblnm, trnctflg, hdrrwcnt, ftrrwcnt, 
                       hdrrwpttrn, ftrrwpttrn, frqcd, stflg, crtdt, lstrundt, nxtrundt
                FROM {table_name}
                WHERE flupldref = %s AND curflg = 'Y'
            """
            cursor.execute(query, (flupldref,))
        else:  # Oracle, etc.
            query = f"""
                SELECT flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, 
                       trgschm, trgtblnm, trnctflg, hdrrwcnt, ftrrwcnt, 
                       hdrrwpttrn, ftrrwpttrn, frqcd, stflg, crtdt, lstrundt, nxtrundt
                FROM {table_name}
                WHERE flupldref = :1 AND curflg = 'Y'
            """
            cursor.execute(query, [flupldref])
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Upload configuration not found: {flupldref}")
        
        columns = [desc[0].lower() for desc in cursor.description]
        data = dict(zip(columns, row))
        
        return {"success": True, "data": data}
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error fetching upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching upload: {str(e)}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/get-connections")
async def get_connections():
    """Get available database connections for target database selection."""
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        
        # Query DMS_DBCONDTLS table
        db_type = _detect_db_type(conn)
        table_name = _get_table_name(cursor, db_type, "DMS_DBCONDTLS")
        
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT conid, connm, dbhost, dbsrvnm, usrnm
                FROM {table_name}
                WHERE curflg = 'Y'
                ORDER BY connm
            """
            cursor.execute(query)
        else:  # Oracle, etc.
            query = f"""
                SELECT conid, connm, dbhost, dbsrvnm, usrnm
                FROM {table_name}
                WHERE curflg = 'Y'
                ORDER BY connm
            """
            cursor.execute(query)
        
        connections = []
        for row in cursor.fetchall():
            connections.append({
                "conid": str(row[0]),
                "connm": row[1],
                "dbhost": row[2],
                "dbsrvnm": row[3],
                "usrnm": row[4] if len(row) > 4 else None,
            })
        
        cursor.close()
        return {"success": True, "data": connections}
    
    except Exception as e:
        error(f"Error fetching connections: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching connections: {str(e)}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/preview-file")
async def preview_file(
    file_path: str = Query(..., description="Path to file to preview"),
    rows: int = Query(10, ge=1, le=100, description="Number of rows to preview")
):
    """Preview file contents (first N rows)."""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        preview_df = parser_manager.preview_file(file_path, rows=rows)
        preview = preview_df.to_dict('records')
        
        # Convert preview values to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                else:
                    row[key] = str(value)
        
        return {
            "success": True,
            "data": preview,
            "columns": list(preview_df.columns),
            "row_count": len(preview_df)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error previewing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")


# ===== CRUD Operations =====

class SaveFileUploadRequest(BaseModel):
    """Request model for saving file upload configuration."""
    formData: FileUploadConfig
    columns: Optional[List[Dict[str, Any]]] = None  # Column mappings


@router.post("/save")
async def save_file_upload(payload: SaveFileUploadRequest):
    """
    Save or update file upload configuration and column mappings.
    """
    conn = None
    try:
        form_data = payload.formData
        columns = payload.columns or []
        user_id = form_data.crtdby or "SYSTEM"
        
        conn = create_metadata_connection()
        
        try:
            # Save main configuration
            # Use flupldid from form_data if provided (for updates), otherwise let the function find it by flupldref
            flupldid = create_update_file_upload(
                conn,
                flupldref=form_data.flupldref,
                fluplddesc=form_data.fluplddesc,
                flnm=form_data.flnm,
                flpth=form_data.flpth,
                fltyp=form_data.fltyp,
                trgconid=form_data.trgconid,
                trgschm=form_data.trgschm,
                trgtblnm=form_data.trgtblnm,
                trnctflg=form_data.trnctflg or "N",
                hdrrwcnt=form_data.hdrrwcnt or 0,
                ftrrwcnt=form_data.ftrrwcnt or 0,
                hdrrwpttrn=form_data.hdrrwpttrn,
                ftrrwpttrn=form_data.ftrrwpttrn,
                frqcd=form_data.frqcd,
                stflg=form_data.stflg or "N",
                batch_size=form_data.batch_size or 1000,
                crtdby=user_id,
                flupldid=form_data.flupldid  # Pass flupldid for updates
            )
            
            # Before saving new column mappings, set all existing mappings for this flupldref to curflg='N'
            # This ensures we don't have duplicates with curflg='Y'
            try:
                cursor = conn.cursor()
                db_type = _detect_db_type(conn)
                detail_table_name = _get_table_name(cursor, db_type, "DMS_FLUPLDDTL")
                if db_type == "POSTGRESQL":
                    cursor.execute(
                        f"UPDATE {detail_table_name} SET curflg = 'N', uptdt = CURRENT_TIMESTAMP WHERE flupldref = %s AND curflg = 'Y'",
                        (form_data.flupldref,)
                    )
                else:  # Oracle
                    cursor.execute(
                        f"UPDATE {detail_table_name} SET curflg = 'N', uptdate = SYSTIMESTAMP WHERE flupldref = :1 AND curflg = 'Y'",
                        [form_data.flupldref]
                    )
                cursor.close()
            except Exception as e:
                warning(f"Error deactivating old column mappings: {str(e)}")
                # Continue anyway - we'll still save new mappings
            
            # Define default audit columns that must always exist
            default_audit_columns = [
                {"trgclnm": "CRTDBY", "audttyp": "CREATED_BY", "trgcldtyp": "String100", "isrqrd": "N"},
                {"trgclnm": "CRTDDT", "audttyp": "CREATED_DATE", "trgcldtyp": "Timestamp", "isrqrd": "Y"},
                {"trgclnm": "UPDTBY", "audttyp": "UPDATED_BY", "trgcldtyp": "String100", "isrqrd": "N"},
                {"trgclnm": "UPDTDT", "audttyp": "UPDATED_DATE", "trgcldtyp": "Timestamp", "isrqrd": "Y"},
            ]
            # Convenience maps for audit handling
            audit_name_to_type = {c["trgclnm"]: c["audttyp"] for c in default_audit_columns}
            audit_names = set(audit_name_to_type.keys())
            
            # Track which audit columns are already in the user's columns
            existing_audit_cols = set()
            user_columns = []
            max_excseq = 0
            
            for idx, col in enumerate(columns):
                if not col.get("trgclnm", "").strip():
                    continue
                
                trgclnm = col.get("trgclnm", "").strip().upper()
                isaudit_val = col.get("isaudit")
                isaudit = "Y" if (isaudit_val == "Y" or isaudit_val is True) else "N"
                audttyp = col.get("audttyp", "").strip().upper() if col.get("audttyp") else ""
                
                # Normalise audit flags: only standard audit columns should be treated as audit
                is_audit_col = False
                if trgclnm in audit_names:
                    is_audit_col = True
                    # Force correct audttyp for standard audit columns
                    audttyp = audit_name_to_type[trgclnm]
                elif isaudit == "Y" and audttyp:
                    # (Optional) custom audit columns – keep behaviour, but they won't
                    # be auto-managed like system audit columns.
                    is_audit_col = True
                
                # Track audit columns
                if is_audit_col and audttyp:
                    existing_audit_cols.add(audttyp)
                
                user_columns.append(col)
                excseq = col.get("excseq") or (idx + 1)
                if isinstance(excseq, (int, float)):
                    max_excseq = max(max_excseq, int(excseq))
            
            # Add missing audit columns
            for audit_col in default_audit_columns:
                if audit_col["audttyp"] not in existing_audit_cols:
                    # Add audit column to user columns
                    user_columns.append({
                        "trgclnm": audit_col["trgclnm"],
                        "srcclnm": "",  # No source column for audit columns
                        "trgcldtyp": audit_col["trgcldtyp"],
                        "trgkyflg": "N",
                        "trgkyseq": None,
                        "trgcldesc": f"System audit column: {audit_col['audttyp']}",
                        "drvlgc": "",
                        "drvlgcflg": "N",
                        "excseq": max_excseq + 1,
                        "isaudit": "Y",
                        "audttyp": audit_col["audttyp"],
                        "dfltval": "",
                        "isrqrd": audit_col["isrqrd"],
                    })
                    max_excseq += 1
            
            # Save column mappings (including auto-added audit columns)
            processed_columns = []
            for idx, col in enumerate(user_columns):
                if not col.get("trgclnm", "").strip():
                    continue
                
                fluplddtlid = col.get("fluplddtlid")
                
                # Get flag values - check explicitly for 'Y' string or True boolean, not just truthy
                trgkyflg_val = col.get("trgkyflg")
                trgkyflg = "Y" if (trgkyflg_val == "Y" or trgkyflg_val is True) else "N"
                
                isrqrd_val = col.get("isrqrd")
                isrqrd = "Y" if (isrqrd_val == "Y" or isrqrd_val is True) else "N"
                
                # Normalise audit flags when persisting:
                #  - Only the four standard audit columns are treated as audit
                #  - All other columns are forced to non-audit
                trgclnm_upper = col.get("trgclnm", "").strip().upper()
                if trgclnm_upper in audit_names:
                    isaudit = "Y"
                    audttyp = audit_name_to_type[trgclnm_upper]
                else:
                    isaudit = "N"
                    audttyp = None
                
                detail_id = create_update_file_upload_detail(
                    conn,
                    flupldref=form_data.flupldref,
                    srcclnm=col.get("srcclnm"),
                    trgclnm=col.get("trgclnm"),
                    trgcldtyp=col.get("trgcldtyp"),
                    trgkyflg=trgkyflg,
                    trgkyseq=col.get("trgkyseq"),
                    trgcldesc=col.get("trgcldesc"),
                    drvlgc=col.get("drvlgc"),
                    drvlgcflg=col.get("drvlgcflg") or "N",
                    excseq=col.get("excseq") or (idx + 1),
                    isaudit=isaudit,
                    audttyp=audttyp,
                    dfltval=col.get("dfltval"),
                    isrqrd=isrqrd,
                    crtdby=user_id,
                    fluplddtlid=fluplddtlid
                )
                
                processed_columns.append({
                    "index": idx,
                    "fluplddtlid": detail_id,
                    "trgclnm": col.get("trgclnm")
                })
            
            conn.commit()
            
            return {
                "success": True,
                "message": "File upload configuration saved successfully",
                "flupldid": str(flupldid),
                "processedColumns": processed_columns
            }
        
        except Exception as e:
            if conn:
                conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file upload configuration: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in save_file_upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file upload configuration: {str(e)}"
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/get-columns/{flupldref}")
async def get_columns(flupldref: str = PathParam(..., description="File upload reference")):
    """Get column mappings for a file upload configuration."""
    conn = None
    try:
        conn = create_metadata_connection()
        columns = get_file_upload_details(conn, flupldref)
        
        return {
            "success": True,
            "data": columns
        }
    
    except Exception as e:
        error(f"Error fetching columns: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching columns: {str(e)}"
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/check-table-exists/{flupldref}")
async def check_table_exists(flupldref: str = PathParam(..., description="File upload reference")):
    """
    Check if the target table already exists in the database.
    Returns true if table exists, false otherwise.
    """
    metadata_conn = None
    target_conn = None
    try:
        metadata_conn = create_metadata_connection()
        config = get_file_upload_config(metadata_conn, flupldref)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"File upload configuration not found: {flupldref}"
            )
        
        trgconid = config.get('trgconid')
        trgschm = config.get('trgschm', '')
        trgtblnm = config.get('trgtblnm', '')
        
        if not trgconid or not trgtblnm:
            # If no target connection or table name, table doesn't exist
            return {
                "success": True,
                "table_exists": False,
                "message": "Target connection or table name not configured"
            }
        
        # Connect to target database
        target_conn = create_target_connection(trgconid)
        if not target_conn:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to target database (connection ID: {trgconid})"
            )
        
        # Check if table exists
        cursor = target_conn.cursor()
        db_type = _detect_db_type(target_conn)
        table_exists = _check_table_exists(cursor, db_type, trgschm, trgtblnm)
        cursor.close()
        
        return {
            "success": True,
            "table_exists": table_exists,
            "schema": trgschm,
            "table": trgtblnm
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error checking table existence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking table existence: {str(e)}"
        )
    finally:
        if metadata_conn:
            try:
                metadata_conn.close()
            except Exception:
                pass
        if target_conn:
            try:
                target_conn.close()
            except Exception:
                pass


class DeleteFileUploadRequest(BaseModel):
    """Request model for deleting file upload."""
    flupldref: str


@router.post("/delete")
async def delete_file_upload_endpoint(payload: DeleteFileUploadRequest):
    """Delete file upload configuration (soft delete)."""
    conn = None
    try:
        conn = create_metadata_connection()
        
        try:
            delete_file_upload(conn, payload.flupldref)
            conn.commit()
            
            return {
                "success": True,
                "message": f"File upload configuration '{payload.flupldref}' deleted successfully"
            }
        
        except Exception as e:
            if conn:
                conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting file upload configuration: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in delete_file_upload_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file upload configuration: {str(e)}"
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


class ActivateDeactivateRequest(BaseModel):
    """Request model for activate/deactivate."""
    flupldref: str
    stflg: str  # 'A' for Active, 'N' for Inactive


@router.post("/activate-deactivate")
async def activate_deactivate_endpoint(payload: ActivateDeactivateRequest):
    """Activate or deactivate file upload configuration."""
    conn = None
    try:
        if payload.stflg not in ['A', 'N']:
            raise HTTPException(
                status_code=400,
                detail="stflg must be 'A' (Active) or 'N' (Inactive)"
            )
        
        conn = create_metadata_connection()
        
        try:
            activate_deactivate_file_upload(conn, payload.flupldref, payload.stflg)
            conn.commit()
            
            status_text = "activated" if payload.stflg == 'A' else "deactivated"
            return {
                "success": True,
                "message": f"File upload configuration '{payload.flupldref}' {status_text} successfully"
            }
        
        except Exception as e:
            if conn:
                conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error updating file upload status: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in activate_deactivate_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating file upload status: {str(e)}"
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ===== Execution Endpoints =====

class ExecuteRequest(BaseModel):
    """Request model for file upload execution."""
    flupldref: str
    file_path: Optional[str] = None  # Optional: if not provided, uses flpth from config
    load_mode: str = LoadMode.INSERT  # INSERT, TRUNCATE_LOAD, UPSERT


@router.post("/execute")
async def execute_file_upload(request: Request, payload: ExecuteRequest):
    """
    Execute file upload configuration.
    
    Args:
        request: FastAPI request object (for getting username)
        payload: ExecuteRequest with flupldref, optional file_path, and load_mode
        
    Returns:
        JSONResponse with execution results
    """
    try:
        # Get username from token
        username = None
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if token:
                # Decode token to get username (simplified - adjust based on your auth system)
                import jwt
                decoded = jwt.decode(token, options={"verify_signature": False})
                username = decoded.get("username") or decoded.get("sub")
        except Exception:
            pass
        
        # Validate load mode
        valid_modes = [LoadMode.INSERT, LoadMode.TRUNCATE_LOAD, LoadMode.UPSERT]
        if payload.load_mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid load_mode. Must be one of: {', '.join(valid_modes)}"
            )
        
        # Execute file upload
        executor = FileUploadExecutor()
        result = executor.execute(
            flupldref=payload.flupldref,
            file_path=payload.file_path,
            load_mode=payload.load_mode,
            username=username
        )
        
        if result['success']:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result['message'],
                    "data": {
                        "rows_processed": result['rows_processed'],
                        "rows_successful": result['rows_successful'],
                        "rows_failed": result['rows_failed'],
                        "table_created": result['table_created'],
                        "errors": result['errors'][:100]  # Limit to first 100 errors
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": result['message'],
                    "data": {
                        "rows_processed": result['rows_processed'],
                        "rows_successful": result['rows_successful'],
                        "rows_failed": result['rows_failed'],
                        "errors": result['errors']
                    }
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error executing file upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing file upload: {str(e)}"
        )


@router.get("/runs")
async def list_all_file_upload_runs(
    flupldref: Optional[str] = Query(None, description="Filter by file upload reference"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, FAILED, PARTIAL)"),
    target_connection_id: Optional[int] = Query(None, description="Filter by target database connection ID"),
    load_mode: Optional[str] = Query(None, description="Filter by load mode (INSERT, TRUNCATE_LOAD, UPSERT)"),
    file_type: Optional[str] = Query(None, description="Filter by file type (CSV, XLSX, etc.)"),
    file_name: Optional[str] = Query(None, description="Search in file name (partial match)"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get all file upload execution history (runs) with optional filtering.
    Reads from DMS_FLUPLD_RUN and joins with DMS_FLUPLD for file metadata.
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)
        run_table = _get_table_ref(cursor, db_type, "DMS_FLUPLD_RUN")
        upload_table = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
        
        # Build WHERE clause and parameters
        where_conditions = []
        params = []
        param_idx = 1
        
        if flupldref:
            # Exact match on flupldref (reference, not description)
            # Use exact match for better performance and accuracy
            if db_type == "POSTGRESQL":
                where_conditions.append("r.flupldref = %s")
            else:
                where_conditions.append(f"r.flupldref = :{param_idx}")
            params.append(flupldref)
            param_idx += 1
        
        if status:
            if db_type == "POSTGRESQL":
                where_conditions.append("r.stts = %s")
            else:
                where_conditions.append(f"r.stts = :{param_idx}")
            params.append(status.upper())
            param_idx += 1
        
        if target_connection_id:
            if db_type == "POSTGRESQL":
                where_conditions.append("u.trgconid = %s")
            else:
                where_conditions.append(f"u.trgconid = :{param_idx}")
            params.append(target_connection_id)
            param_idx += 1
        
        if load_mode:
            if db_type == "POSTGRESQL":
                where_conditions.append("r.ldmde = %s")
            else:
                where_conditions.append(f"r.ldmde = :{param_idx}")
            params.append(load_mode.upper())
            param_idx += 1
        
        if file_type:
            if db_type == "POSTGRESQL":
                where_conditions.append("u.fltyp = %s")
            else:
                where_conditions.append(f"u.fltyp = :{param_idx}")
            params.append(file_type.upper())
            param_idx += 1
        
        if file_name:
            search_pattern = f"%{file_name}%"
            if db_type == "POSTGRESQL":
                where_conditions.append("(LOWER(u.flnm) LIKE LOWER(%s) OR LOWER(r.flpth) LIKE LOWER(%s))")
                params.extend([search_pattern, search_pattern])
            else:
                where_conditions.append(f"(LOWER(u.flnm) LIKE LOWER(:{param_idx}) OR LOWER(r.flpth) LIKE LOWER(:{param_idx + 1}))")
                params.extend([search_pattern, search_pattern])
                param_idx += 2
        
        if start_date:
            if db_type == "POSTGRESQL":
                where_conditions.append("DATE(r.strttm) >= %s")
            else:
                where_conditions.append(f"TRUNC(r.strttm) >= :{param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            if db_type == "POSTGRESQL":
                where_conditions.append("DATE(r.strttm) <= %s")
            else:
                where_conditions.append(f"TRUNC(r.strttm) <= :{param_idx}")
            params.append(end_date)
            param_idx += 1
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        if db_type == "POSTGRESQL":
            sql = f"""
                SELECT r.runid, r.flupldref, r.strttm, r.ndtm,
                       r.rwsprcssd, r.rwsstccssfl, r.rwsfld,
                       r.stts, r.mssg, r.ldmde, r.flpth,
                       u.flnm, u.fltyp, u.fluplddesc
                FROM {run_table} r
                LEFT JOIN {upload_table} u ON r.flupldref = u.flupldref
                WHERE {where_clause}
                ORDER BY r.strttm DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
        else:  # Oracle
            sql = f"""
                SELECT r.runid, r.flupldref, r.strttm, r.ndtm,
                       r.rwsprcssd, r.rwsstccssfl, r.rwsfld,
                       r.stts, r.mssg, r.ldmde, r.flpth,
                       u.flnm, u.fltyp, u.fluplddesc
                FROM {run_table} r
                LEFT JOIN {upload_table} u ON r.flupldref = u.flupldref
                WHERE {where_clause}
                ORDER BY r.strttm DESC
            """
            cursor.execute(sql, params)
            all_rows = cursor.fetchall()
            # Apply limit/offset manually for Oracle
            if offset > 0 or limit < len(all_rows):
                rows = all_rows[offset:offset + limit]
            else:
                rows = all_rows

        columns = [desc[0].lower() for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        return {
            "success": True,
            "count": len(data),
            "data": data,
        }
    except Exception as e:
        error(f"Error fetching file upload runs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching file upload runs: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/errors/{flupldref}")
async def get_file_upload_errors(
    flupldref: str,
    runid: Optional[int] = Query(None, description="Execution run ID"),
    error_code: Optional[str] = Query(None, description="Filter by error code (RRCD)"),
    search: Optional[str] = Query(None, description="Search in error message"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Get error rows for a given file upload reference (and optional run).
    Reads from DMS_FLUPLD_ERR in the metadata database.
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)

        filters = ["flupldref = %s"]
        params: list = [flupldref]

        if runid is not None:
            filters.append("runid = %s")
            params.append(runid)

        if error_code:
            filters.append("rrcd = %s")
            params.append(error_code)

        if search:
            filters.append("LOWER(rrmssg) LIKE %s")
            params.append(f"%{search.lower()}%")

        where_clause = " AND ".join(filters)

        if db_type == "POSTGRESQL":
            table_name = "dms_flupld_err"
            sql = f"""
                SELECT errid, flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt
                FROM {table_name}
                WHERE {where_clause}
                ORDER BY rwndx
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cursor.execute(sql, tuple(params))
            rows_to_process = cursor.fetchall()
        else:
            table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD_ERR")
            if db_type == "ORACLE":
                sql_filters = []
                ora_params = []
                idx = 1
                for flt, val in zip(filters, params):
                    sql_filters.append(flt.replace("%s", f":{idx}"))
                    ora_params.append(val)
                    idx += 1
                where_clause_oracle = " AND ".join(sql_filters)
                # Oracle: fetch all and apply limit/offset in Python (same pattern as /runs endpoint)
                sql = f"""
                    SELECT errid, flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt
                    FROM {table_name}
                    WHERE {where_clause_oracle}
                    ORDER BY rwndx
                """
                cursor.execute(sql, ora_params)
                all_rows = cursor.fetchall()
                # Apply limit/offset manually for Oracle
                if offset > 0 or limit < len(all_rows):
                    rows_to_process = all_rows[offset:offset + limit]
                else:
                    rows_to_process = all_rows
            else:
                sql = f"""
                    SELECT errid, flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt
                    FROM {table_name}
                    WHERE {where_clause}
                    ORDER BY rwndx
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                cursor.execute(sql, tuple(params))
                rows_to_process = cursor.fetchall()

        columns = [desc[0].lower() for desc in cursor.description]
        rows = []
        for row in rows_to_process:
            row_dict = dict(zip(columns, row))
            # Ensure rwdtjsn is always a string (JSONB columns may return as dict/object)
            if 'rwdtjsn' in row_dict and row_dict['rwdtjsn'] is not None:
                if isinstance(row_dict['rwdtjsn'], (dict, list)):
                    import json
                    row_dict['rwdtjsn'] = json.dumps(row_dict['rwdtjsn'], default=str)
                elif not isinstance(row_dict['rwdtjsn'], str):
                    row_dict['rwdtjsn'] = str(row_dict['rwdtjsn'])
            rows.append(row_dict)

        return {
            "success": True,
            "data": rows,
        }
    except Exception as e:
        error(f"Error fetching file upload errors for {flupldref}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching file upload errors: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/schedules/{flupldref}")
async def get_file_upload_schedules(flupldref: str = PathParam(..., description="File upload reference")):
    """
    List schedules for a given file upload (DMS_FLUPLD_SCHD).
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)
        table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD_SCHD")

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"""
                SELECT schdid, flupldref, frqncy, tm_prm, nxt_run_dt, lst_run_dt,
                       stts, crtdby, crtdt, uptdby, uptdt, curflg
                FROM {table_name}
                WHERE flupldref = %s
                ORDER BY schdid DESC
                """,
                (flupldref,),
            )
        else:
            cursor.execute(
                f"""
                SELECT SCHDID, FLUPLDREF, FRQNCY, TM_PRM, NXT_RUN_DT, LST_RUN_DT,
                       STTS, CRTDBY, CRTDT, UPTDBY, UPTDT, CURFLG
                FROM {table_name}
                WHERE FLUPLDREF = :1
                ORDER BY SCHDID DESC
                """,
                [flupldref],
            )

        columns = [desc[0].lower() for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return {"success": True, "data": rows}
    except Exception as e:
        error(f"Error fetching file upload schedules: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching file upload schedules: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/schedules")
async def save_file_upload_schedule(payload: FileUploadScheduleRequest):
    """
    Create/update a schedule for a file upload in DMS_FLUPLD_SCHD.
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)
        table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD_SCHD")

        frq = (payload.frqncy or "").upper()
        if frq not in {"DL", "WK", "MN", "HY", "YR", "ID"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid frequency code '{payload.frqncy}'. Allowed: DL, WK, MN, HY, YR, ID.",
            )

        tm_prm = (payload.tm_prm or "").strip().upper() or None
        if frq != "ID" and not tm_prm:
            raise HTTPException(
                status_code=400,
                detail="Time parameter (tm_prm) is required for non-ID schedules",
            )

        freq_day: Optional[str] = None
        freq_hour: Optional[int] = None
        freq_minute: Optional[int] = None
        if tm_prm:
          parts = tm_prm.split("_")
          if frq in {"DL", "ID"}:
              if len(parts) >= 2:
                  try:
                      h_str, m_str = parts[1].split(":")
                      freq_hour = int(h_str)
                      freq_minute = int(m_str)
                  except Exception:
                      raise HTTPException(
                          status_code=400,
                          detail=f"Invalid time pattern in tm_prm: '{tm_prm}'. Expected format e.g. DL_10:30",
                      )
          elif frq in {"WK", "FN"}:
              if len(parts) >= 3:
                  freq_day = parts[1]
                  try:
                      h_str, m_str = parts[2].split(":")
                      freq_hour = int(h_str)
                      freq_minute = int(m_str)
                  except Exception:
                      raise HTTPException(
                          status_code=400,
                          detail=f"Invalid time pattern in tm_prm: '{tm_prm}'. Expected format e.g. WK_MON_10:30",
                      )
          elif frq in {"MN", "HY", "YR"}:
              if len(parts) >= 3:
                  freq_day = parts[1]
                  try:
                      h_str, m_str = parts[2].split(":")
                      freq_hour = int(h_str)
                      freq_minute = int(m_str)
                  except Exception:
                      raise HTTPException(
                          status_code=400,
                          detail=f"Invalid time pattern in tm_prm: '{tm_prm}'. Expected format e.g. MN_15_10:30",
                      )

        tz = os.getenv("DMS_TIMEZONE", "UTC")
        next_run = _calculate_next_run_time(
            frequency_code=frq,
            frequency_day=freq_day,
            frequency_hour=freq_hour,
            frequency_minute=freq_minute,
            start_date=payload.strtdt,
            end_date=payload.enddt,
            timezone=tz,
        )

        # Close existing active schedules for this upload (keep history)
        if db_type == "POSTGRESQL":
            cursor.execute(
                f"""
                UPDATE {table_name}
                SET curflg = 'N', uptdt = CURRENT_TIMESTAMP
                WHERE flupldref = %s AND curflg = 'Y'
                """,
                (payload.flupldref,),
            )
        else:
            cursor.execute(
                f"""
                UPDATE {table_name}
                SET CURFLG = 'N', UPTDT = SYSTIMESTAMP
                WHERE FLUPLDREF = :1 AND CURFLG = 'Y'
                """,
                [payload.flupldref],
            )

        stts = (payload.stts or "ACTIVE").upper()
        crtdby = "SYSTEM"

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"""
                INSERT INTO {table_name}
                (flupldref, frqncy, tm_prm, nxt_run_dt, lst_run_dt,
                 stts, crtdby, crtdt, uptdby, uptdt, curflg)
                VALUES
                (%s, %s, %s, %s, NULL,
                 %s, %s, CURRENT_TIMESTAMP, %s, NULL, 'Y')
                RETURNING schdid
                """,
                (
                    payload.flupldref,
                    frq,
                    tm_prm,
                    next_run,
                    stts,
                    crtdby,
                    crtdby,
                ),
            )
            schdid = cursor.fetchone()[0]
        else:
            cursor.execute(
                f"""
                INSERT INTO {table_name}
                (SCHDID, FLUPLDREF, FRQNCY, TM_PRM, NXT_RUN_DT, LST_RUN_DT,
                 STTS, CRTDBY, CRTDT, UPTDBY, UPTDT, CURFLG)
                VALUES
                (DMS_FLUPLD_SCHDSEQ.NEXTVAL, :1, :2, :3, :4, NULL,
                 :5, :6, SYSTIMESTAMP, :6, NULL, 'Y')
                """,
                [
                    payload.flupldref,
                    frq,
                    tm_prm,
                    next_run,
                    stts,
                    crtdby,
                ],
            )
            cursor.execute("SELECT DMS_FLUPLD_SCHDSEQ.CURRVAL FROM DUAL")
            row = cursor.fetchone()
            schdid = row[0] if row else None

        conn.commit()

        return {
            "success": True,
            "data": {
                "schdid": schdid,
                "flupldref": payload.flupldref,
                "frqncy": frq,
                "tm_prm": tm_prm,
                "nxt_run_dt": next_run,
                "lst_run_dt": None,
                "stts": stts,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        error(f"Error saving file upload schedule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file upload schedule: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

