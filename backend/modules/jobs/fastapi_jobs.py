from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.database.dbconnect import create_metadata_connection

try:
    from backend.modules.helper_functions import (
        call_create_update_job,
        get_mapping_ref,
        get_mapping_details,
    )
except ImportError:  # Fallback for direct Flask-style imports if needed
    from modules.helper_functions import (  # type: ignore
        call_create_update_job,
        get_mapping_ref,
        get_mapping_details,
    )

try:
    from backend.modules.common.db_table_utils import (
        _detect_db_type,
        get_postgresql_table_name,
    )
except ImportError:  # Fallback
    from modules.common.db_table_utils import (  # type: ignore
        _detect_db_type,
        get_postgresql_table_name,
    )

try:
    from backend.modules.logger import info, error, debug
except ImportError:  # Fallback
    from modules.logger import info, error, debug  # type: ignore

from backend.modules.jobs.pkgdwprc_python import (
    JobSchedulerService,
    ScheduleRequest,
    ImmediateJobRequest,
    HistoryJobRequest,
    SchedulerValidationError,
    SchedulerRepositoryError,
    SchedulerError,
)


router = APIRouter(tags=["jobs"])


def _parse_date(value: Optional[str]):
    if value in (None, "", "null"):
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise SchedulerValidationError(f"Invalid date format: {value}") from exc


def _optional_int(value: Optional[str]):
    if value in (None, "", "null"):
        return None
    return int(value)


def _parse_datetime(value: Optional[str]):
    if value in (None, "", "null"):
        return None
    try:
        sanitized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(sanitized)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise SchedulerValidationError(
                f"Invalid datetime format: {value}"
            ) from exc


def _check_job_already_running(connection, p_mapref: str) -> bool:
    """
    Return True if a job is already running (status IP or CLAIMED in last 24h).
    Replaces the old Flask helper removed during migration.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        schema = (os.getenv("DMS_SCHEMA", "")).strip()

        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else "public"
            dms_prclog_ref = get_postgresql_table_name(cursor, schema_lower, "DMS_PRCLOG")
            # Quote if created with uppercase
            dms_prclog_ref = f'"{dms_prclog_ref}"' if dms_prclog_ref != dms_prclog_ref.lower() else dms_prclog_ref
            schema_prefix = f"{schema_lower}." if schema else ""
            dms_prclog_full = f"{schema_prefix}{dms_prclog_ref}"
            sql = f"""
            SELECT COUNT(*) FROM {dms_prclog_full}
            WHERE mapref = %s
              AND status IN ('IP', 'CLAIMED')
              AND strtdt > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """
            cursor.execute(sql, (p_mapref,))
        else:
            schema_prefix = f"{schema}." if schema else ""
            sql = f"""
            SELECT COUNT(*) FROM {schema_prefix}DMS_PRCLOG
            WHERE mapref = :p_mapref
              AND status IN ('IP', 'CLAIMED')
              AND strtdt > SYSTIMESTAMP - INTERVAL '24' HOUR
            """
            cursor.execute(sql, {"p_mapref": p_mapref})

        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        error(f"Error checking if job is running: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

# ----- Simple job endpoints used by frontend -----


@router.get("/get_all_jobs")
async def get_all_jobs():
    """
    Get all jobs and their schedule status.
    Mirrors Flask endpoint: GET /job/get_all_jobs
    """
    conn = None
    cursor = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)

        info(f"[get_all_jobs] Database type detected: {db_type}")

        # Get schema name from environment
        schema = os.getenv("DMS_SCHEMA", "TRG")
        info(f"[get_all_jobs] Using schema: {schema}")

        # Get table references for PostgreSQL (handles case sensitivity)
        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else "public"
            try:
                dms_job_table = get_postgresql_table_name(
                    cursor, schema_lower, "DMS_JOB"
                )
                dms_jobflw_table = get_postgresql_table_name(
                    cursor, schema_lower, "DMS_JOBFLW"
                )
                dms_jobsch_table = get_postgresql_table_name(
                    cursor, schema_lower, "DMS_JOBSCH"
                )
                info(
                    "[get_all_jobs] PostgreSQL table names - "
                    f"JOB: {dms_job_table}, JOBFLW: {dms_jobflw_table}, "
                    f"JOBSCH: {dms_jobsch_table}"
                )
            except Exception as table_err:
                error(f"[get_all_jobs] Error detecting table names: {str(table_err)}")
                # Fallback to lowercase
                dms_job_table = "dms_job"
                dms_jobflw_table = "dms_jobflw"
                dms_jobsch_table = "dms_jobsch"
                info("[get_all_jobs] Using fallback table names")

            # Quote table names if they contain uppercase letters (were created with quotes)
            dms_job_ref = (
                f'"{dms_job_table}"'
                if dms_job_table != dms_job_table.lower()
                else dms_job_table
            )
            dms_jobflw_ref = (
                f'"{dms_jobflw_table}"'
                if dms_jobflw_table != dms_jobflw_table.lower()
                else dms_jobflw_table
            )
            dms_jobsch_ref = (
                f'"{dms_jobsch_table}"'
                if dms_jobsch_table != dms_jobsch_table.lower()
                else dms_jobsch_table
            )

            schema_prefix = f"{schema_lower}." if schema else ""
            dms_job_full = f"{schema_prefix}{dms_job_ref}"
            dms_jobflw_full = f"{schema_prefix}{dms_jobflw_ref}"
            dms_jobsch_full = f"{schema_prefix}{dms_jobsch_ref}"

            info(
                "[get_all_jobs] Full table references - "
                f"JOB: {dms_job_full}, JOBFLW: {dms_jobflw_full}, "
                f"JOBSCH: {dms_jobsch_full}"
            )

            # Query from DMS_JOB and left join with DMS_JOBFLW and DMS_JOBSCH
            # This ensures we show all jobs even if flow creation failed
            query_job_flow = f"""
                SELECT 
                    COALESCE(f.JOBFLWID, j.JOBID) AS JOBFLWID,
                    j.MAPREF,
                    j.TRGSCHM,
                    j.TRGTBTYP,
                    j.TRGTBNM,
                    f.DWLOGIC,
                    COALESCE(f.STFLG, j.STFLG) AS STFLG,
                    CASE 
                        WHEN s.SCHFLG = 'Y' THEN 'Scheduled'
                        ELSE 'Not Scheduled'
                    END AS JOB_SCHEDULE_STATUS,
                    s.JOBSCHID,
                    s.DPND_JOBSCHID,
                    s.FRQCD AS "Frequency code",
                    s.FRQDD AS "Frequency day",
                    s.FRQHH AS "frequency hour",
                    s.FRQMI AS "frequency month",
                    s.STRTDT AS "start date",
                    s.ENDDT AS "end date",
                    s.LST_RUN_DT AS "last run",
                    s.NXT_RUN_DT AS "next run"
                FROM 
                    {dms_job_full} j
                LEFT JOIN 
                    {dms_jobflw_full} f ON f.MAPREF = j.MAPREF AND f.CURFLG = 'Y'
                LEFT JOIN 
                    (
                        SELECT 
                            f2.JOBFLWID,
                            MIN(s2.JOBSCHID) AS JOBSCHID, 
                            MIN(s2.DPND_JOBSCHID) AS DPND_JOBSCHID,
                            -- Prioritize schedule with SCHFLG = 'Y' for frequency fields
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.FRQCD END), MIN(s2.FRQCD)) AS FRQCD,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.FRQDD END), MIN(s2.FRQDD)) AS FRQDD,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.FRQHH END), MIN(s2.FRQHH)) AS FRQHH,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.FRQMI END), MIN(s2.FRQMI)) AS FRQMI,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.STRTDT END), MIN(s2.STRTDT)) AS STRTDT,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.ENDDT END), MIN(s2.ENDDT)) AS ENDDT,
                            MAX(s2.SCHFLG) AS SCHFLG,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.LST_RUN_DT END), MAX(s2.LST_RUN_DT)) AS LST_RUN_DT,
                            COALESCE(MAX(CASE WHEN s2.SCHFLG = 'Y' THEN s2.NXT_RUN_DT END), MAX(s2.NXT_RUN_DT)) AS NXT_RUN_DT
                        FROM 
                            {dms_jobsch_full} s2
                        INNER JOIN
                            {dms_jobflw_full} f2 ON f2.JOBFLWID = s2.JOBFLWID
                        WHERE 
                            s2.CURFLG = 'Y' AND f2.CURFLG = 'Y'
                        GROUP BY 
                            f2.JOBFLWID
                    ) s
                ON 
                    f.JOBFLWID = s.JOBFLWID
                WHERE 
                    j.CURFLG = 'Y'
                ORDER BY j.RECCRDT DESC
            """
        else:  # Oracle
            schema_prefix = f"{schema}." if schema else ""
            # Query from DMS_JOB and left join with DMS_JOBFLW and DMS_JOBSCH
            # This ensures we show all jobs even if flow creation failed
            query_job_flow = f"""
                SELECT 
                    NVL(f.JOBFLWID, j.JOBID) AS JOBFLWID,
                    j.MAPREF,
                    j.TRGSCHM,
                    j.TRGTBTYP,
                    j.TRGTBNM,
                    f.DWLOGIC,
                    NVL(f.STFLG, j.STFLG) AS STFLG,
                    CASE 
                        WHEN s.SCHFLG = 'Y' THEN 'Scheduled'
                        ELSE 'Not Scheduled'
                    END AS JOB_SCHEDULE_STATUS,
                    s.JOBSCHID,
                    s.DPND_JOBSCHID,
                    s.FRQCD AS "Frequency code",
                    s.FRQDD AS "Frequency day",
                    s.FRQHH AS "frequency hour",
                    s.FRQMI AS "frequency month",
                    s.STRTDT AS "start date",
                    s.ENDDT AS "end date",
                    s.LST_RUN_DT AS "last run",
                    s.NXT_RUN_DT AS "next run"
                FROM 
                    {schema_prefix}DMS_JOB j
                LEFT JOIN 
                    {schema_prefix}DMS_JOBFLW f ON f.MAPREF = j.MAPREF AND f.CURFLG = 'Y'
                LEFT JOIN 
                    (
                        SELECT 
                            f2.JOBFLWID,
                            MIN(s2.JOBSCHID) AS JOBSCHID, 
                            MIN(s2.DPND_JOBSCHID) AS DPND_JOBSCHID,
                            MIN(s2.FRQCD) AS FRQCD,
                            MIN(s2.FRQDD) AS FRQDD,
                            MIN(s2.FRQHH) AS FRQHH,
                            MIN(s2.FRQMI) AS FRQMI,
                            MIN(s2.STRTDT) AS STRTDT,
                            MIN(s2.ENDDT) AS ENDDT,
                            MAX(s2.SCHFLG) AS SCHFLG,
                            MAX(s2.LST_RUN_DT) AS LST_RUN_DT,
                            MAX(s2.NXT_RUN_DT) AS NXT_RUN_DT
                        FROM 
                            {schema_prefix}DMS_JOBSCH s2
                        INNER JOIN
                            {schema_prefix}DMS_JOBFLW f2 ON f2.JOBFLWID = s2.JOBFLWID
                        WHERE 
                            s2.CURFLG = 'Y' AND f2.CURFLG = 'Y'
                        GROUP BY 
                            f2.JOBFLWID
                    ) s
                ON 
                    f.JOBFLWID = s.JOBFLWID
                WHERE 
                    j.CURFLG = 'Y'
                ORDER BY j.RECCRDT DESC
            """

        info("[get_all_jobs] Executing query...")
        cursor.execute(query_job_flow)
        columns = [col[0] for col in cursor.description]
        raw_jobs = cursor.fetchall()

        info(f"[get_all_jobs] Query executed successfully. Found {len(raw_jobs)} rows.")
        info(f"[get_all_jobs] Column names from query: {columns}")

        # Normalize column names to uppercase for consistency (PostgreSQL returns lowercase)
        columns_upper = [col.upper() if col else col for col in columns]
        info(f"[get_all_jobs] Normalized column names: {columns_upper}")

        # Convert rows into list of dictionaries (JSON-serialisable)
        jobs: List[Dict[str, Any]] = []
        for row_idx, row in enumerate(raw_jobs):
            job_dict: Dict[str, Any] = {}
            for i, column in enumerate(columns_upper):
                value = row[i]
                # Handle LOB-like objects
                if hasattr(value, "read"):
                    try:
                        value = value.read()
                        if isinstance(value, bytes):
                            value = value.decode("utf-8")
                    except Exception as lob_err:
                        value = str(lob_err)
                # Convert dates/datetimes to ISO strings for JSON
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                job_dict[column] = value

            if row_idx == 0:
                info(f"[get_all_jobs] First job keys: {list(job_dict.keys())}")
                info(
                    "[get_all_jobs] First job JOBFLWID: "
                    f"{job_dict.get('JOBFLWID')}, MAPREF: {job_dict.get('MAPREF')}"
                )

            jobs.append(job_dict)

        info(f"[get_all_jobs] Returning {len(jobs)} jobs")
        return jobs
    except Exception as e:
        error(f"Error in get_all_jobs: {str(e)}")
        import traceback

        error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "details": traceback.format_exc()},
        )
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/create-update")
async def create_update_job(payload: Dict[str, Any]):
    """
    Create or update a job for a given mapping reference.
    Mirrors Flask endpoint: POST /job/create-update
    """
    try:
        p_mapref = payload.get("mapref")

        if not p_mapref:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Missing required parameter: mapref",
                },
            )

        conn = create_metadata_connection()
        try:
            job_id, error_message = call_create_update_job(conn, p_mapref)

            if error_message:
                raise HTTPException(
                    status_code=500,
                    detail={"success": False, "message": error_message},
                )

            return {
                "success": True,
                "message": "Job created/updated successfully",
                "job_id": job_id,
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in create_update_job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"An error occurred while processing the request: {str(e)}",
            },
        )


@router.get("/get_job_details/{mapref}")
async def get_job_details(mapref: str):
    """
    Get job detail columns (TRGCLNM, MAPLOGIC, etc.) for a mapping.
    Mirrors Flask endpoint: GET /job/get_job_details/<mapref>
    """
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)

        if db_type == "POSTGRESQL":
            schema = (os.getenv("DMS_SCHEMA", "") or "").strip()
            schema_lower = schema.lower() if schema else "public"
            dms_jobdtl_ref = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBDTL"
            )
            dms_jobdtl_ref = (
                f'"{dms_jobdtl_ref}"'
                if dms_jobdtl_ref != dms_jobdtl_ref.lower()
                else dms_jobdtl_ref
            )
            schema_prefix = f"{schema_lower}." if schema else ""
            dms_jobdtl_full = f"{schema_prefix}{dms_jobdtl_ref}"
            job_details_query = (
                f"SELECT TRGCLNM,TRGCLDTYP,TRGKEYFLG,TRGKEYSEQ,TRGCLDESC,"
                f"MAPLOGIC,KEYCLNM,VALCLNM,SCDTYP "
                f"FROM {dms_jobdtl_full} WHERE CURFLG = 'Y' AND MAPREF = %s"
            )
            cursor.execute(job_details_query, (mapref,))
        else:
            job_details_query = """
                SELECT TRGCLNM,TRGCLDTYP,TRGKEYFLG,TRGKEYSEQ,TRGCLDESC,
                       MAPLOGIC,KEYCLNM,VALCLNM,SCDTYP
                FROM DMS_JOBDTL
                WHERE CURFLG = 'Y' AND MAPREF = :mapref
            """
            cursor.execute(job_details_query, {"mapref": mapref})

        job_details = cursor.fetchall()
        return {"job_details": job_details}
    except Exception as e:
        error(f"Error in get_job_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


@router.get("/get_job_schedule_details/{job_flow_id}")
async def get_job_schedule_details(job_flow_id: str):
    """
    Get schedule details for a job flow id.
    Mirrors Flask endpoint: GET /job/get_job_schedule_details/<job_flow_id>
    """
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)

        if db_type == "POSTGRESQL":
            schema = (os.getenv("DMS_SCHEMA", "") or "").strip()
            schema_lower = schema.lower() if schema else "public"
            dms_jobsch_ref = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBSCH"
            )
            dms_jobsch_ref = (
                f'"{dms_jobsch_ref}"'
                if dms_jobsch_ref != dms_jobsch_ref.lower()
                else dms_jobsch_ref
            )
            schema_prefix = f"{schema_lower}." if schema else ""
            dms_jobsch_full = f"{schema_prefix}{dms_jobsch_ref}"
            query = f"""
                SELECT 
                    JOBFLWID,
                    MAPREF,
                    FRQCD,
                    FRQDD,
                    FRQHH,
                    FRQMI,
                    STRTDT,
                    ENDDT,
                    STFLG,
                    DPND_JOBSCHID,
                    RECCRDT,
                    RECUPDT,
                    LST_RUN_DT,
                    NXT_RUN_DT
                FROM {dms_jobsch_full} 
                WHERE CURFLG ='Y' AND JOBFLWID=%s
            """
            cursor.execute(query, (job_flow_id,))
        else:
            query = """
                SELECT 
                    JOBFLWID,
                    MAPREF,
                    FRQCD,
                    FRQDD,
                    FRQHH,
                    FRQMI,
                    STRTDT,
                    ENDDT,
                    STFLG,
                    DPND_JOBSCHID,
                    RECCRDT,
                    RECUPDT,
                    LST_RUN_DT,
                    NXT_RUN_DT
                FROM DMS_JOBSCH 
                WHERE CURFLG ='Y' AND JOBFLWID=:job_flow_id
            """
            cursor.execute(query, {"job_flow_id": job_flow_id})

        columns = [col[0] for col in cursor.description]
        job_schedule_details: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            job_dict: Dict[str, Any] = {}
            for i, column in enumerate(columns):
                value = row[i]
                if value is None:
                    job_dict[column] = None
                elif isinstance(value, (int, float)):
                    # For numeric fields like FRQHH, FRQMI, keep as number if it's a frequency component
                    if column in ["FRQHH", "FRQMI"]:
                        job_dict[column] = int(value) if isinstance(value, float) and value.is_integer() else value
                    else:
                        job_dict[column] = str(value)
                elif hasattr(value, "isoformat"):
                    # For date/datetime fields, convert to ISO format string
                    job_dict[column] = value.isoformat()
                else:
                    job_dict[column] = str(value)

            # If next run date is missing but we have frequency info, compute it on the fly
            if not job_dict.get("NXT_RUN_DT") and job_dict.get("FRQCD"):
                try:
                    computed_next = _calculate_next_run_time(
                        job_dict.get("FRQCD"),
                        job_dict.get("FRQDD"),
                        _optional_int(job_dict.get("FRQHH")),
                        _optional_int(job_dict.get("FRQMI")),
                        _parse_date(job_dict.get("STRTDT") or job_dict.get("STRT_DT")),
                        _parse_date(job_dict.get("ENDDT") or job_dict.get("END_DT")),
                        os.getenv("DMS_TIMEZONE", "UTC"),
                    )
                    if computed_next:
                        job_dict["NXT_RUN_DT"] = computed_next.isoformat()
                except Exception as _:
                    # Best-effort; leave as-is if calculation fails
                    pass
            job_schedule_details.append(job_dict)

        return job_schedule_details
    except Exception as e:
        error(f"Error in get_job_schedule_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


# ----- Scheduling and dependency endpoints -----


class SaveJobScheduleRequest(BaseModel):
    MAPREF: str
    FRQCD: str
    FRQDD: Optional[str] = None
    FRQHH: Optional[str] = None
    FRQMI: Optional[str] = None
    STRTDT: Optional[str] = None
    ENDDT: Optional[str] = None


@router.post("/save_job_schedule")
async def save_job_schedule(payload: SaveJobScheduleRequest):
    """
    Save or update a job schedule.
    Mirrors Flask endpoint: POST /job/save_job_schedule
    """
    conn = None
    try:
        data = payload.model_dump()
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        schedule_request = ScheduleRequest(
            mapref=data.get("MAPREF"),
            frequency_code=data.get("FRQCD"),
            frequency_day=data.get("FRQDD"),
            frequency_hour=_optional_int(data.get("FRQHH")),
            frequency_minute=_optional_int(data.get("FRQMI")),
            start_date=_parse_date(data.get("STRTDT")),
            end_date=_parse_date(data.get("ENDDT")),
        )
        result = service.create_job_schedule(schedule_request)
        return {
            "success": True,
            "message": result.message,
            "job_schedule_id": result.job_schedule_id,
            "status": result.status,
        }
    except SchedulerValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(exc)},
        )
    except SchedulerRepositoryError as exc:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Database error: {str(exc)}"},
        )
    except Exception as exc:
        error(f"Error in save_job_schedule: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Unexpected error: {str(exc)}"},
        )
    finally:
        if conn:
            conn.close()


class SaveParentChildJobRequest(BaseModel):
    PARENT_MAP_REFERENCE: str
    CHILD_MAP_REFERENCE: str


@router.post("/save_parent_child_job")
async def save_parent_child_job(payload: SaveParentChildJobRequest):
    """
    Save parent/child job relationship.
    Mirrors Flask endpoint: POST /job/save_parent_child_job
    """
    data = payload.model_dump()
    parent_map_reference = data.get("PARENT_MAP_REFERENCE")
    child_map_reference = data.get("CHILD_MAP_REFERENCE")

    if not parent_map_reference or not child_map_reference:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Missing required parameters: PARENT_MAP_REFERENCE or CHILD_MAP_REFERENCE",
            },
        )

    conn = None
    try:
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        service.create_job_dependency(parent_map_reference, child_map_reference)
        return {
            "success": True,
            "message": "Parent-child job relationship saved successfully",
        }
    except SchedulerValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(exc)},
        )
    except SchedulerRepositoryError as exc:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Database error: {str(exc)}"},
        )
    except Exception as exc:
        error(f"Error in save_parent_child_job: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(exc)},
        )
    finally:
        if conn:
            conn.close()


class EnableDisableJobRequest(BaseModel):
    MAPREF: str
    JOB_FLG: str


@router.post("/enable_disable_job")
async def enable_disable_job(payload: EnableDisableJobRequest):
    """
    Enable or disable a job schedule.
    Mirrors Flask endpoint: POST /job/enable_disable_job
    """
    data = payload.model_dump()
    map_ref = data.get("MAPREF")
    job_flag = data.get("JOB_FLG")

    if not map_ref or job_flag not in {"E", "D"}:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Invalid or missing parameters"},
        )

    conn = None
    try:
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        service.enable_disable_schedule(map_ref, job_flag)
        message = (
            "Job enabled successfully"
            if job_flag == "E"
            else "Job disabled successfully"
        )
        return {"success": True, "message": message}
    except SchedulerValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(exc)},
        )
    except SchedulerRepositoryError as exc:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Database error: {str(exc)}"},
        )
    except Exception as exc:
        error(f"Error in enable_disable_job: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(exc)},
        )
    finally:
        if conn:
            conn.close()


class ToggleJobStatusRequest(BaseModel):
    MAPREF: str
    STFLG: str  # 'A' for active, 'N' for inactive


@router.post("/toggle_job_status")
async def toggle_job_status(payload: ToggleJobStatusRequest):
    """
    Toggle job active/inactive status by updating STFLG in DMS_JOB, DMS_JOBFLW, and DMS_JOBSCH tables.
    Mirrors Flask endpoint: POST /job/toggle_job_status
    """
    data = payload.model_dump()
    mapref = data.get("MAPREF")
    stflg = data.get("STFLG")

    if not mapref or stflg not in ["A", "N"]:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Invalid or missing parameters. MAPREF and STFLG (A or N) are required.",
            },
        )

    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)
        schema = os.getenv("DMS_SCHEMA", "TRG")

        try:
            # Get table references
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else "public"
                dms_job_table = get_postgresql_table_name(cursor, schema_lower, "DMS_JOB")
                dms_jobflw_table = get_postgresql_table_name(
                    cursor, schema_lower, "DMS_JOBFLW"
                )
                dms_jobsch_table = get_postgresql_table_name(
                    cursor, schema_lower, "DMS_JOBSCH"
                )
                dms_job_ref = (
                    f'"{dms_job_table}"'
                    if dms_job_table != dms_job_table.lower()
                    else dms_job_table
                )
                dms_jobflw_ref = (
                    f'"{dms_jobflw_table}"'
                    if dms_jobflw_table != dms_jobflw_table.lower()
                    else dms_jobflw_table
                )
                dms_jobsch_ref = (
                    f'"{dms_jobsch_table}"'
                    if dms_jobsch_table != dms_jobsch_table.lower()
                    else dms_jobsch_table
                )
                schema_prefix = f"{schema_lower}." if schema else ""
                dms_job_full = f"{schema_prefix}{dms_job_ref}"
                dms_jobflw_full = f"{schema_prefix}{dms_jobflw_ref}"
                dms_jobsch_full = f"{schema_prefix}{dms_jobsch_ref}"

                # Update DMS_JOB
                cursor.execute(
                    f"""
                    UPDATE {dms_job_full}
                    SET stflg = %s, recupdt = CURRENT_TIMESTAMP
                    WHERE mapref = %s AND curflg = 'Y'
                    """,
                    (stflg, mapref),
                )

                # Update DMS_JOBFLW
                cursor.execute(
                    f"""
                    UPDATE {dms_jobflw_full}
                    SET stflg = %s, recupdt = CURRENT_TIMESTAMP
                    WHERE mapref = %s AND curflg = 'Y'
                    """,
                    (stflg, mapref),
                )

                # Update DMS_JOBSCH - update all active schedules for this mapref
                cursor.execute(
                    f"""
                    UPDATE {dms_jobsch_full}
                    SET stflg = %s, recupdt = CURRENT_TIMESTAMP
                    WHERE mapref = %s AND curflg = 'Y'
                    """,
                    (stflg, mapref),
                )
            else:  # Oracle
                schema_prefix = f"{schema}." if schema else ""
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_JOB
                    SET stflg = :stflg, recupdt = SYSTIMESTAMP
                    WHERE mapref = :mapref AND curflg = 'Y'
                    """,
                    {"stflg": stflg, "mapref": mapref},
                )
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_JOBFLW
                    SET stflg = :stflg, recupdt = SYSTIMESTAMP
                    WHERE mapref = :mapref AND curflg = 'Y'
                    """,
                    {"stflg": stflg, "mapref": mapref},
                )
                # Update DMS_JOBSCH - update all active schedules for this mapref
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_JOBSCH
                    SET stflg = :stflg, recupdt = SYSTIMESTAMP
                    WHERE mapref = :mapref AND curflg = 'Y'
                    """,
                    {"stflg": stflg, "mapref": mapref},
                )

            conn.commit()
            status_text = "activated" if stflg == "A" else "deactivated"
            return {"success": True, "message": f"Job {status_text} successfully"}
        except Exception as exc:
            conn.rollback()
            error(f"Error updating job status: {exc}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": f"Failed to update job status: {str(exc)}",
                },
            )
        finally:
            cursor.close()
    except HTTPException:
        raise
    except Exception as exc:
        error(f"Error in toggle_job_status: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"An error occurred: {str(exc)}"},
        )
    finally:
        if conn:
            conn.close()


# ----- Immediate / history job execution -----


class ScheduleJobImmediatelyRequest(BaseModel):
    mapref: str
    loadType: Optional[str] = "regular"  # 'regular' or 'history'
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    truncateLoad: Optional[str] = "N"


def _call_schedule_regular_job_async(p_mapref: str, truncate_load: str = "N"):
    conn = None
    try:
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        # Pass truncate_flag in params for regular load
        params = {"truncate_flag": truncate_load} if truncate_load == "Y" else {}
        request_id = service.queue_immediate_job(
            ImmediateJobRequest(mapref=p_mapref, params=params)
        )
        truncate_msg = " (with truncate)" if truncate_load == "Y" else ""
        return True, f"Job {p_mapref} queued for immediate execution{truncate_msg} (request_id={request_id})"
    except SchedulerError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            conn.close()


def _call_schedule_history_job_async(
    p_mapref: str, p_strtdt: str, p_enddt: str, p_tlflg: str
):
    conn = None
    try:
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        request_id = service.queue_history_job(
            HistoryJobRequest(
                mapref=p_mapref,
                start_date=_parse_date(p_strtdt),
                end_date=_parse_date(p_enddt),
                truncate_flag=p_tlflg or "N",
            )
        )
        return (
            True,
            f"History job {p_mapref} queued "
            f"(request_id={request_id}, {p_strtdt} to {p_enddt})",
        )
    except SchedulerError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            conn.close()


@router.post("/schedule-job-immediately")
async def schedule_job_immediately(payload: ScheduleJobImmediatelyRequest):
    """
    Schedule a regular or history job for immediate execution.
    Mirrors Flask endpoint: POST /job/schedule-job-immediately
    """
    data = payload.model_dump()
    p_mapref = data.get("mapref")
    load_type = data.get("loadType", "regular")
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    truncate_load = data.get("truncateLoad", "N")

    if not p_mapref:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Missing required parameter: mapref"},
        )

    # Validate history params
    if load_type == "history" and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Missing required parameters for history load: startDate and endDate",
            },
        )

    conn = None
    try:
        conn = create_metadata_connection()
        if _check_job_already_running(conn, p_mapref):
            raise HTTPException(
                status_code=400,
                detail={"success": False, "message": f"{p_mapref} : Job is already running"},
            )

        if load_type == "history":
            success, message = _call_schedule_history_job_async(
                p_mapref, start_date, end_date, truncate_load
            )
        else:
            success, message = _call_schedule_regular_job_async(p_mapref, truncate_load)

        return {"success": success, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in schedule_job_immediately: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
    finally:
        if conn:
            conn.close()


# ----- Stop running job -----


class StopRunningJobRequest(BaseModel):
    mapref: str
    startDate: str
    force: Optional[str] = "N"


@router.post("/stop-running-job")
async def stop_running_job(payload: StopRunningJobRequest):
    """
    Request stop of a running job.
    Mirrors Flask endpoint: POST /job/stop-running-job
    """
    data = payload.model_dump()
    p_mapref = data.get("mapref")
    p_strtdt = data.get("startDate")
    p_force = data.get("force", "N")

    if not p_mapref or not p_strtdt:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Missing required parameters: mapref or startDate",
            },
        )

    try:
        start_dt = _parse_datetime(p_strtdt)
    except SchedulerValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(exc)},
        )

    conn = None
    try:
        conn = create_metadata_connection()
        service = JobSchedulerService(conn)
        request_id = service.request_job_stop(p_mapref, start_dt, p_force)
        info(f"Stop requested for job {p_mapref} (request_id={request_id})")
        return {
            "success": True,
            "message": f"Stop request queued (request_id={request_id})",
        }
    except SchedulerRepositoryError as exc:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Database error: {str(exc)}"},
        )
    except Exception as exc:
        error(f"Error in stop_running_job: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(exc)},
        )
    finally:
        if conn:
            conn.close()


# ----- Scheduled jobs and logs (status + history) -----


@router.get("/get_scheduled_jobs")
async def get_scheduled_jobs(period: str = Query("7")):
    """
    Get list of scheduled jobs and their logs.
    Mirrors Flask endpoint: GET /job/get_scheduled_jobs?period=...
    """
    conn = None
    try:
        conn = create_metadata_connection()
        # Parse period
        period_param = period or "7"
        if period_param.upper() == "ALL":
            period_value: Any = "ALL"
        else:
            try:
                period_value = int(period_param)
            except (ValueError, TypeError):
                period_value = 7

        db_type = _detect_db_type(conn)
        schema = (os.getenv("DMS_SCHEMA", "") or "").strip()
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else "public"
            dms_prclog_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_PRCLOG"
            )
            dms_joblog_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBLOG"
            )
            dms_joberr_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBERR"
            )

            dms_prclog_ref = (
                f'"{dms_prclog_table}"'
                if dms_prclog_table != dms_prclog_table.lower()
                else dms_prclog_table
            )
            dms_joblog_ref = (
                f'"{dms_joblog_table}"'
                if dms_joblog_table != dms_joblog_table.lower()
                else dms_joblog_table
            )
            dms_joberr_ref = (
                f'"{dms_joberr_table}"'
                if dms_joberr_table != dms_joberr_table.lower()
                else dms_joberr_table
            )

            schema_prefix = f"{schema_lower}." if schema else ""
            dms_prclog_full = f"{schema_prefix}{dms_prclog_ref}"
            dms_joblog_full = f"{schema_prefix}{dms_joblog_ref}"
            dms_joberr_full = f"{schema_prefix}{dms_joberr_ref}"

            if period_value == "ALL":
                query = f"""
                    SELECT 
                        jl.joblogid AS log_id,
                        pl.reccrdt AS log_date,
                        pl.mapref AS job_name,
                        pl.status,
                        pl.strtdt AS actual_start_date,
                        err.errmsg || E'\\n' || err.dberrmsg AS error_message,
                        pl.sessionid AS session_id,
                        jl.srcrows AS source_rows,
                        jl.trgrows AS target_rows,
                        pl.param1 AS param1,
                        CASE 
                            WHEN pl.enddt IS NOT NULL THEN
                                EXTRACT(EPOCH FROM (pl.enddt - pl.strtdt))
                            ELSE NULL
                        END AS run_duration_seconds
                    FROM {dms_prclog_full} pl
                    LEFT JOIN {dms_joblog_full} jl ON jl.jobid = pl.jobid 
                        AND jl.sessionid = pl.sessionid
                        AND jl.prcid = pl.prcid
                        AND jl.mapref = pl.mapref
                    LEFT JOIN {dms_joberr_full} err ON err.sessionid = pl.sessionid
                        AND err.prcid = pl.prcid
                        AND err.mapref = pl.mapref
                        AND err.jobid = pl.jobid
                    ORDER BY pl.mapref, pl.reccrdt DESC
                """
            else:
                query = f"""
                    SELECT 
                        jl.joblogid AS log_id,
                        pl.reccrdt AS log_date,
                        pl.mapref AS job_name,
                        pl.status,
                        pl.strtdt AS actual_start_date,
                        err.errmsg || E'\\n' || err.dberrmsg AS error_message,
                        pl.sessionid AS session_id,
                        jl.srcrows AS source_rows,
                        jl.trgrows AS target_rows,
                        pl.param1 AS param1,
                        CASE 
                            WHEN pl.enddt IS NOT NULL THEN
                                EXTRACT(EPOCH FROM (pl.enddt - pl.strtdt))
                            ELSE NULL
                        END AS run_duration_seconds
                    FROM {dms_prclog_full} pl
                    LEFT JOIN {dms_joblog_full} jl ON jl.jobid = pl.jobid 
                        AND jl.sessionid = pl.sessionid
                        AND jl.prcid = pl.prcid
                        AND jl.mapref = pl.mapref
                    LEFT JOIN {dms_joberr_full} err ON err.sessionid = pl.sessionid
                        AND err.prcid = pl.prcid
                        AND err.mapref = pl.mapref
                        AND err.jobid = pl.jobid
                    WHERE pl.reccrdt >= CURRENT_TIMESTAMP - INTERVAL '{period_value} days'
                    ORDER BY pl.mapref, pl.reccrdt DESC
                """
            cursor.execute(query)
        else:
            schema_prefix = f"{schema}." if schema else ""
            dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
            dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
            dms_joberr_full = f"{schema_prefix}DMS_JOBERR"

            if period_value == "ALL":
                query = f"""
                    SELECT 
                        jl.joblogid AS log_id,
                        pl.reccrdt AS log_date,
                        pl.mapref AS job_name,
                        pl.status,
                        pl.strtdt AS actual_start_date,
                        err.errmsg || CHR(10) || err.dberrmsg AS error_message,
                        pl.sessionid AS session_id,
                        jl.srcrows AS source_rows,
                        jl.trgrows AS target_rows,
                        pl.param1 AS param1,
                        CASE 
                            WHEN pl.enddt IS NOT NULL THEN
                                EXTRACT(DAY FROM (pl.enddt - pl.strtdt)) * 86400 + 
                                EXTRACT(HOUR FROM (pl.enddt - pl.strtdt)) * 3600 + 
                                EXTRACT(MINUTE FROM (pl.enddt - pl.strtdt)) * 60 + 
                                EXTRACT(SECOND FROM (pl.enddt - pl.strtdt))
                            ELSE NULL
                        END AS run_duration_seconds
                    FROM {dms_prclog_full} pl, {dms_joblog_full} jl, {dms_joberr_full} err
                    WHERE jl.jobid(+) = pl.jobid 
                        AND jl.sessionid(+) = pl.sessionid
                        AND jl.prcid(+) = pl.prcid
                        AND jl.mapref(+) = pl.mapref
                        AND err.sessionid(+) = pl.sessionid
                        AND err.prcid(+) = pl.prcid
                        AND err.mapref(+) = pl.mapref
                        AND err.jobid(+) = pl.jobid
                    ORDER BY pl.mapref, pl.reccrdt DESC
                """
                cursor.execute(query)
            else:
                query = f"""
                    SELECT 
                        jl.joblogid AS log_id,
                        pl.reccrdt AS log_date,
                        pl.mapref AS job_name,
                        pl.status,
                        pl.strtdt AS actual_start_date,
                        err.errmsg || CHR(10) || err.dberrmsg AS error_message,
                        pl.sessionid AS session_id,
                        jl.srcrows AS source_rows,
                        jl.trgrows AS target_rows,
                        pl.param1 AS param1,
                        CASE 
                            WHEN pl.enddt IS NOT NULL THEN
                                EXTRACT(DAY FROM (pl.enddt - pl.strtdt)) * 86400 + 
                                EXTRACT(HOUR FROM (pl.enddt - pl.strtdt)) * 3600 + 
                                EXTRACT(MINUTE FROM (pl.enddt - pl.strtdt)) * 60 + 
                                EXTRACT(SECOND FROM (pl.enddt - pl.strtdt))
                            ELSE NULL
                        END AS run_duration_seconds
                    FROM {dms_prclog_full} pl, {dms_joblog_full} jl, {dms_joberr_full} err
                    WHERE jl.jobid(+) = pl.jobid 
                        AND jl.sessionid(+) = pl.sessionid
                        AND jl.prcid(+) = pl.prcid
                        AND jl.mapref(+) = pl.mapref
                        AND err.sessionid(+) = pl.sessionid
                        AND err.prcid(+) = pl.prcid
                        AND err.mapref(+) = pl.mapref
                        AND err.jobid(+) = pl.jobid
                        AND pl.reccrdt >= SYSDATE - :period
                    ORDER BY pl.mapref, pl.reccrdt DESC
                """
                cursor.execute(query, {"period": period_value})

        column_names = [desc[0] for desc in cursor.description]
        raw_jobs = cursor.fetchall()

        jobs_dict: Dict[str, Dict[str, Any]] = {}

        for row in raw_jobs:
            log_entry: Dict[str, Any] = {}
            for i, value in enumerate(row):
                column_name = column_names[i]
                column_name_upper = column_name.upper() if column_name else column_name

                if value is None:
                    log_entry[column_name_upper] = None
                elif hasattr(value, "total_seconds"):
                    log_entry[column_name_upper] = int(value.total_seconds())
                elif hasattr(value, "isoformat"):
                    log_entry[column_name_upper] = value.isoformat()
                elif hasattr(value, "read"):
                    try:
                        lob_data = value.read()
                        if isinstance(lob_data, bytes):
                            log_entry[column_name_upper] = lob_data.decode("utf-8")
                        else:
                            log_entry[column_name_upper] = str(lob_data)
                    except Exception as e:
                        log_entry[column_name_upper] = f"Error reading LOB: {str(e)}"
                elif isinstance(value, (int, float)):
                    log_entry[column_name_upper] = value
                else:
                    log_entry[column_name_upper] = (
                        str(value) if value is not None else None
                    )

            job_name = log_entry.get("JOB_NAME") or log_entry.get("job_name")
            if job_name:
                if job_name not in jobs_dict:
                    jobs_dict[job_name] = {"job_name": job_name, "logs": []}
                jobs_dict[job_name]["logs"].append(log_entry)

        grouped_jobs = list(jobs_dict.values())
        grouped_jobs.sort(key=lambda x: x["job_name"])
        for job in grouped_jobs:
            job["logs"].sort(
                key=lambda x: x.get("LOG_DATE") or x.get("log_date") or "",
                reverse=True,
            )

        total_logs = sum(len(job["logs"]) for job in grouped_jobs)

        return {
            "jobs": grouped_jobs,
            "summary": {
                "total_jobs": len(grouped_jobs),
                "total_log_entries": total_logs,
                "column_names": column_names,
            },
        }
    except Exception as e:
        error(f"Error in get_scheduled_jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@router.get("/get_job_and_process_log_details/{mapref}")
async def get_job_and_process_log_details(mapref: str):
    """
    Get job and process log details for a scheduled job.
    Mirrors Flask endpoint: GET /job/get_job_and_process_log_details/<mapref>
    """
    conn = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        schema = (os.getenv("DMS_SCHEMA", "") or "").strip()
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            schema_lower = schema.lower() if schema else "public"
            dms_joblog_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBLOG"
            )
            dms_prclog_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_PRCLOG"
            )
            dms_joberr_table = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBERR"
            )

            dms_joblog_ref = (
                f'"{dms_joblog_table}"'
                if dms_joblog_table != dms_joblog_table.lower()
                else dms_joblog_table
            )
            dms_prclog_ref = (
                f'"{dms_prclog_table}"'
                if dms_prclog_table != dms_prclog_table.lower()
                else dms_prclog_table
            )
            dms_joberr_ref = (
                f'"{dms_joberr_table}"'
                if dms_joberr_table != dms_joberr_table.lower()
                else dms_joberr_table
            )

            schema_prefix = f"{schema_lower}." if schema else ""
            dms_joblog_full = f"{schema_prefix}{dms_joblog_ref}"
            dms_prclog_full = f"{schema_prefix}{dms_prclog_ref}"
            dms_joberr_full = f"{schema_prefix}{dms_joberr_ref}"

            query = f"""
                SELECT jbl.prcdt AS PROCESS_DATE
                      ,jbl.mapref AS MAP_REFERENCE
                      ,jbl.jobid AS JOB_ID
                      ,jbl.srcrows AS SOURCE_ROWS
                      ,jbl.trgrows AS target_rows
                      ,jbl.errrows AS ERROR_ROWS
                      ,prc.strtdt AS START_DATE
                      ,prc.enddt AS END_DATE
                      ,prc.status AS STATUS
                      ,err.errmsg || E'\\n' || err.dberrmsg AS ERROR_MESSAGE
                FROM {dms_joblog_full} jbl
                INNER JOIN {dms_prclog_full} prc ON jbl.jobid = prc.jobid
                LEFT JOIN {dms_joberr_full} err ON err.sessionid = prc.sessionid
                    AND err.prcid = prc.prcid
                    AND err.mapref = prc.mapref
                    AND err.jobid = prc.jobid
                WHERE jbl.mapref = %s
                ORDER BY prc.strtdt DESC
            """
            cursor.execute(query, (mapref,))
        else:
            schema_prefix = f"{schema}." if schema else ""
            dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
            dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
            dms_joberr_full = f"{schema_prefix}DMS_JOBERR"

            query = f"""
                SELECT jbl.prcdt AS PROCESS_DATE
                      ,jbl.mapref AS MAP_REFERENCE
                      ,jbl.jobid AS JOB_ID
                      ,jbl.srcrows AS SOURCE_ROWS
                      ,jbl.trgrows AS target_rows
                      ,jbl.errrows AS ERROR_ROWS
                      ,prc.strtdt AS START_DATE
                      ,prc.enddt AS END_DATE
                      ,prc.status AS STATUS
                      ,err.errmsg || CHR(10) || err.dberrmsg AS ERROR_MESSAGE
                FROM {dms_joblog_full} jbl
                    ,{dms_prclog_full} prc
                    ,{dms_joberr_full} err
                WHERE jbl.mapref = :mapref
                    AND jbl.jobid = prc.jobid
                    AND err.sessionid(+) = prc.sessionid
                    AND err.prcid(+) = prc.prcid
                    AND err.mapref(+) = prc.mapref
                    AND err.jobid(+) = prc.jobid
                ORDER BY prc.strtdt DESC
            """
            cursor.execute(query, {"mapref": mapref})

        job_and_process_log_details = cursor.fetchall()
        return {"job_and_process_log_details": job_and_process_log_details}
    except Exception as e:
        error(f"Error in get_job_and_process_log_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@router.get("/get_error_details/{job_id}")
async def get_error_details(job_id: str):
    """
    Get error details for a scheduled job.
    Mirrors Flask endpoint: GET /job/get_error_details/<job_id>
    """
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = _detect_db_type(conn)

        query = """
        SELECT ERRID as ERROR_ID,
               PRCDT as PROCESS_DATE,
               ERRTYP as ERROR_TYPE,
               DBERRMSG as DATABASE_ERROR_MESSAGE,
               ERRMSG as ERROR_MESSAGE,
               KEYVALUE as KEY_VALUE 
        FROM {dms_joberr_full} WHERE JOBID = {bind_param}
        """

        if db_type == "POSTGRESQL":
            schema = (os.getenv("DMS_SCHEMA", "") or "").strip()
            schema_lower = schema.lower() if schema else "public"
            dms_joberr_ref = get_postgresql_table_name(
                cursor, schema_lower, "DMS_JOBERR"
            )
            dms_joberr_ref = (
                f'"{dms_joberr_ref}"'
                if dms_joberr_ref != dms_joberr_ref.lower()
                else dms_joberr_ref
            )
            schema_prefix = f"{schema_lower}." if schema else ""
            dms_joberr_full = f"{schema_prefix}{dms_joberr_ref}"
            bind_param = "%s"
            cursor.execute(
                query.format(dms_joberr_full=dms_joberr_full, bind_param=bind_param),
                (job_id,),
            )
        else:
            oracle_schema = os.getenv("DMS_SCHEMA", "") or ""
            schema_prefix = f"{oracle_schema}." if oracle_schema else ""
            dms_joberr_full = f"{schema_prefix}DMS_JOBERR"
            bind_param = ":job_id"
            cursor.execute(
                query.format(dms_joberr_full=dms_joberr_full, bind_param=bind_param),
                {"job_id": job_id},
            )

        error_details = cursor.fetchall()
        return {"error_details": error_details}
    except Exception as e:
        error(f"Error in get_error_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()



