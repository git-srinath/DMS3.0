"""
Python replacement scaffolding for the PKGDWPRC scheduling/processing package.

This module provides validation, persistence helpers, and queue-enqueue logic
that will be used both by the Flask controllers and by the new scheduler
service.  The actual execution engine runs inside
`backend/modules/jobs/scheduler_service.py`.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional

try:
    from backend.modules.logger import info, error, warning, debug
    from backend.modules.common.id_provider import next_id as get_next_id
    from backend.modules.common.db_table_utils import (
        _detect_db_type,
        get_postgresql_table_name,
    )
    from backend.modules.jobs.scheduler_frequency import build_trigger
except ImportError:  # Fallback for Flask-style imports
    from modules.logger import info, error, warning, debug  # type: ignore
    from modules.common.id_provider import next_id as get_next_id  # type: ignore
    from modules.common.db_table_utils import (  # type: ignore
        _detect_db_type,
        get_postgresql_table_name,
    )
    from modules.jobs.scheduler_frequency import build_trigger  # type: ignore
import os

ALLOWED_FREQUENCY_CODES = {"ID", "DL", "WK", "FN", "MN", "HY", "YR"}
WEEKDAY_CODES = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}


class SchedulerError(Exception):
    """Base error for scheduler operations."""


class SchedulerValidationError(SchedulerError):
    """Raised when user input fails validation."""


class SchedulerRepositoryError(SchedulerError):
    """Raised when persistence layer operations fail."""


class JobRequestType(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    HISTORY = "HISTORY"
    REPORT = "REPORT"
    STOP = "STOP"
    REFRESH_SCHEDULE = "REFRESH_SCHEDULE"
    FILE_UPLOAD = "FILE_UPLOAD"


@dataclass(frozen=True)
class ScheduleRequest:
    mapref: str
    frequency_code: str
    frequency_day: Optional[str] = None
    frequency_hour: Optional[int] = None
    frequency_minute: Optional[int] = None
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None


@dataclass(frozen=True)
class ScheduleResult:
    job_schedule_id: int
    replaced_job_schedule_id: Optional[int]
    status: str
    message: str


@dataclass(frozen=True)
class ImmediateJobRequest:
    mapref: str
    request_type: JobRequestType = JobRequestType.IMMEDIATE
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HistoryJobRequest:
    mapref: str
    start_date: date
    end_date: date
    truncate_flag: str = "N"


def _validate_schedule_request(request: ScheduleRequest) -> None:
    if not request.mapref:
        raise SchedulerValidationError("Mapping reference is required.")

    frq = request.frequency_code
    if frq not in ALLOWED_FREQUENCY_CODES:
        raise SchedulerValidationError(
            f"Invalid frequency code '{frq}'. "
            "Valid values: ID, DL, WK, FN, MN, HY, YR."
        )

    if frq in {"WK", "FN"}:
        if request.frequency_day not in WEEKDAY_CODES:
            raise SchedulerValidationError(
                "Weekly/Fortnightly schedules must use weekday codes "
                "MON,TUE,WED,THU,FRI,SAT,SUN."
            )
    elif frq not in {"DL", "ID"}:
        if request.frequency_day is None:
            raise SchedulerValidationError("Frequency day is required for this frequency.")
        if isinstance(request.frequency_day, str):
            try:
                freq_day_int = int(request.frequency_day)
            except ValueError as exc:
                raise SchedulerValidationError("Frequency day must be a number.") from exc
        else:
            freq_day_int = request.frequency_day
        if not 1 <= int(freq_day_int) <= 31:
            raise SchedulerValidationError("Frequency day must be between 1 and 31.")

    if request.frequency_hour is not None and not 0 <= int(request.frequency_hour) <= 23:
        raise SchedulerValidationError("Frequency hour must be between 0 and 23.")

    if request.frequency_minute is not None and not 0 <= int(request.frequency_minute) <= 59:
        raise SchedulerValidationError("Frequency minute must be between 0 and 59.")

    if request.start_date is None:
        raise SchedulerValidationError("Start date must be provided.")

    if request.end_date and request.start_date >= request.end_date:
        raise SchedulerValidationError("End date must be after start date.")


def _serialize_payload(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


def _calculate_next_run_time(
    frequency_code: str,
    frequency_day: Optional[str],
    frequency_hour: Optional[int],
    frequency_minute: Optional[int],
    start_date: Optional[date],
    end_date: Optional[date],
    timezone: str = "UTC",
) -> Optional[datetime]:
    """
    Calculate the next run time for a schedule using APScheduler trigger.
    
    Args:
        frequency_code: Frequency code (DL, WK, FN, MN, HY, YR, ID)
        frequency_day: Day parameter (weekday for WK/FN, day of month for MN/HY/YR)
        frequency_hour: Hour (0-23)
        frequency_minute: Minute (0-59)
        start_date: Start date for the schedule
        end_date: End date for the schedule
        timezone: Timezone string (default: UTC)
    
    Returns:
        Next run datetime or None if cannot be calculated
    """
    try:
        from datetime import time as dt_time, timezone as dt_timezone

        # Prefer stdlib zoneinfo (Python 3.9+) to avoid external pytz dependency.
        try:
            from zoneinfo import ZoneInfo
            tz_obj = ZoneInfo(timezone) if timezone else dt_timezone.utc
        except Exception:
            warning(
                f"Invalid/unsupported timezone '{timezone}'. Falling back to UTC for next-run calculation."
            )
            tz_obj = dt_timezone.utc

        now = datetime.now(tz_obj)
        
        # Build schedule row dict for build_trigger
        start_dt = None
        if start_date:
            # Combine with hour and minute if provided
            hour = frequency_hour if frequency_hour is not None else 0
            minute = frequency_minute if frequency_minute is not None else 0
            start_dt = datetime.combine(start_date, dt_time(hour, minute))
            start_dt = start_dt.replace(tzinfo=tz_obj) if start_dt.tzinfo is None else start_dt
        
        end_dt = None
        if end_date:
            end_dt = datetime.combine(end_date, dt_time(23, 59, 59))
            end_dt = end_dt.replace(tzinfo=tz_obj) if end_dt.tzinfo is None else end_dt
        
        schedule_row = {
            "FRQCD": frequency_code,
            "FRQDD": frequency_day,
            "FRQHH": frequency_hour,
            "FRQMI": frequency_minute,
            "STRTDT": start_dt,
            "ENDDT": end_dt,
        }
        
        # Build trigger
        trigger = build_trigger(schedule_row, timezone)
        
        # Get next fire time from trigger
        # APScheduler triggers have get_next_fire_time method
        if hasattr(trigger, 'get_next_fire_time'):
            try:
                next_run = trigger.get_next_fire_time(None, now)
                # Convert to naive datetime if needed (remove timezone for database storage)
                if next_run and next_run.tzinfo:
                    next_run = next_run.replace(tzinfo=None)
                return next_run
            except Exception as trigger_err:
                debug(f"Trigger get_next_fire_time failed: {trigger_err}, trying alternative method")
        
        # Fallback: If start date is in the future, use it
        if start_dt and start_dt > now:
            return start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
        
        # If no start date or start date is in past, calculate based on frequency
        # Fallback calculation based on frequency code
        if start_dt:
            # Use start date as base even if in past
            base_dt = start_dt
        else:
            # Use current time as base
            base_dt = now
        
        # Calculate next run based on frequency
        from datetime import timedelta
        base_dt_naive = base_dt.replace(tzinfo=None) if base_dt.tzinfo else base_dt
        
        if frequency_code == 'DL':  # Daily
            next_run = base_dt_naive + timedelta(days=1)
        elif frequency_code == 'WK':  # Weekly
            next_run = base_dt_naive + timedelta(weeks=1)
        elif frequency_code == 'FN':  # Fortnightly
            next_run = base_dt_naive + timedelta(weeks=2)
        elif frequency_code == 'MN':  # Monthly (approx 30 days)
            next_run = base_dt_naive + timedelta(days=30)
        elif frequency_code == 'HY':  # Half-yearly
            next_run = base_dt_naive + timedelta(days=180)
        elif frequency_code == 'YR':  # Yearly
            next_run = base_dt_naive + timedelta(days=365)
        elif frequency_code == 'ID':  # Interval (default to daily)
            next_run = base_dt_naive + timedelta(days=1)
        else:
            # Default to daily if unknown
            next_run = base_dt_naive + timedelta(days=1)
        
        # Set the time component if provided
        if frequency_hour is not None and frequency_minute is not None:
            next_run = next_run.replace(hour=frequency_hour, minute=frequency_minute, second=0, microsecond=0)
        
        return next_run
    except Exception as e:
        error(f"Error calculating next run time: {e}")
        import traceback
        debug(f"Traceback: {traceback.format_exc()}")
        return None


def _generate_numeric_id(cursor, sequence_name: str) -> int:
    """
    Generate surrogate numeric ID using ID provider (supports Oracle/PostgreSQL).
    Falls back to timestamp-based integer on error.
    """
    try:
        return int(get_next_id(cursor, sequence_name))
    except Exception as exc:
        warning(f"ID provider failed for {sequence_name}: {exc}. Falling back to timestamp.")
        return int(datetime.utcnow().timestamp() * 1000)


class JobSchedulerService:
    """
    Thin service layer that mirrors the interface of PKGDWPRC.

    The Flask controllers (or any other API surface) should instantiate this
    service with an open DB connection and call the respective methods.  All
    write operations are committed by the service; callers are expected to
    manage connection lifecycle (open/close).
    """

    def __init__(self, connection):
        self.connection = connection
        self.db_type = _detect_db_type(connection)
        self.schema = os.getenv('DMS_SCHEMA', 'TRG')

    # ------------------------------------------------------------------ #
    # Schedule creation / maintenance
    # ------------------------------------------------------------------ #
    def create_job_schedule(self, request: ScheduleRequest) -> ScheduleResult:
        _validate_schedule_request(request)
        cursor = self.connection.cursor()
        try:
            job_flow = self._fetch_active_job_flow(cursor, request.mapref)
            if not job_flow:
                raise SchedulerValidationError(
                    f"No active job flow found for mapping {request.mapref}."
                )

            active_schedule = self._fetch_active_schedule(cursor, request.mapref)
            if active_schedule and self._schedule_matches(active_schedule, request):
                info(
                    f"Schedule unchanged for {request.mapref} (jobschid={active_schedule['JOBSCHID']})"
                )
                return ScheduleResult(
                    job_schedule_id=active_schedule["JOBSCHID"],
                    replaced_job_schedule_id=None,
                    status="UNCHANGED",
                    message="Existing schedule already matches request.",
                )

            replaced_jobschid = None
            if active_schedule:
                replaced_jobschid = active_schedule["JOBSCHID"]
                # Get table reference for PostgreSQL (handles case sensitivity)
                if self.db_type == "POSTGRESQL":
                    schema_lower = self.schema.lower() if self.schema else 'public'
                    dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                    dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                    schema_prefix = f'{schema_lower}.' if self.schema else ''
                    dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                    cursor.execute(
                        f"""
                        UPDATE {dms_jobsch_full}
                        SET curflg = 'N', recupdt = CURRENT_TIMESTAMP
                        WHERE jobschid = %s
                        """,
                        (replaced_jobschid,),
                    )
                else:  # Oracle
                    schema_prefix = f'{self.schema}.' if self.schema else ''
                    cursor.execute(
                        f"""
                        UPDATE {schema_prefix}DMS_JOBSCH
                        SET curflg = 'N', recupdt = SYSTIMESTAMP
                        WHERE jobschid = :jobschid
                        """,
                        {"jobschid": replaced_jobschid},
                    )

            jobschid = _generate_numeric_id(cursor, "DMS_JOBSCHSEQ")
            
            # Get the job's current stflg status to set it in the schedule
            # Use the job flow's stflg, defaulting to 'A' if not available
            schedule_stflg = job_flow.get("STFLG", "A")
            
            # Calculate next run time
            timezone = os.getenv('DMS_TIMEZONE', 'UTC')
            next_run_time = _calculate_next_run_time(
                request.frequency_code,
                request.frequency_day,
                request.frequency_hour,
                request.frequency_minute,
                request.start_date,
                request.end_date,
                timezone
            )
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if self.db_type == "POSTGRESQL":
                schema_lower = self.schema.lower() if self.schema else 'public'
                dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                schema_prefix = f'{schema_lower}.' if self.schema else ''
                dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                cursor.execute(
                    f"""
                    INSERT INTO {dms_jobsch_full} (
                        jobschid, jobflwid, mapref,
                        frqcd, frqdd, frqhh, frqmi,
                        strtdt, enddt, stflg,
                        reccrdt, recupdt, curflg, schflg,
                        nxt_run_dt
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', 'N',
                        %s
                    )
                    """,
                    (
                        jobschid,
                        job_flow["JOBFLWID"],
                        request.mapref,
                        request.frequency_code,
                        request.frequency_day,
                        request.frequency_hour,
                        request.frequency_minute,
                        request.start_date,
                        request.end_date,
                        schedule_stflg,
                        next_run_time,
                    ),
                )
            else:  # Oracle
                schema_prefix = f'{self.schema}.' if self.schema else ''
                cursor.execute(
                    f"""
                    INSERT INTO {schema_prefix}DMS_JOBSCH (
                        jobschid, jobflwid, mapref,
                        frqcd, frqdd, frqhh, frqmi,
                        strtdt, enddt, stflg,
                        reccrdt, recupdt, curflg, schflg,
                        nxt_run_dt
                    ) VALUES (
                        :jobschid, :jobflwid, :mapref,
                        :frqcd, :frqdd, :frqhh, :frqmi,
                        :strtdt, :enddt, :stflg,
                        SYSTIMESTAMP, SYSTIMESTAMP, 'Y', 'N',
                        :nxt_run_dt
                    )
                    """,
                    {
                        "jobschid": jobschid,
                        "jobflwid": job_flow["JOBFLWID"],
                        "mapref": request.mapref,
                        "frqcd": request.frequency_code,
                        "frqdd": request.frequency_day,
                        "frqhh": request.frequency_hour,
                        "frqmi": request.frequency_minute,
                        "strtdt": request.start_date,
                        "enddt": request.end_date,
                        "stflg": schedule_stflg,
                        "nxt_run_dt": next_run_time,
                    },
                )

            self.connection.commit()
            info(f"Job schedule created for {request.mapref} (jobschid={jobschid})")
            return ScheduleResult(
                job_schedule_id=jobschid,
                replaced_job_schedule_id=replaced_jobschid,
                status="CREATED" if replaced_jobschid is None else "UPDATED",
                message="Job schedule saved successfully.",
            )
        except SchedulerError:
            self.connection.rollback()
            raise
        except Exception as exc:
            self.connection.rollback()
            error(f"Error creating job schedule: {exc}")
            raise SchedulerRepositoryError(str(exc)) from exc
        finally:
            cursor.close()

    def create_job_dependency(self, parent_mapref: str, child_mapref: str) -> None:
        if not parent_mapref or not child_mapref:
            raise SchedulerValidationError("Parent and child map references are required.")
        cursor = self.connection.cursor()
        try:
            parent_schedule = self._fetch_active_schedule(cursor, parent_mapref)
            child_schedule = self._fetch_active_schedule(cursor, child_mapref)
            if not parent_schedule or not child_schedule:
                raise SchedulerValidationError("Both mappings must have active schedules.")

            # Get table reference for PostgreSQL (handles case sensitivity)
            if self.db_type == "POSTGRESQL":
                schema_lower = self.schema.lower() if self.schema else 'public'
                dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                schema_prefix = f'{schema_lower}.' if self.schema else ''
                dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                cursor.execute(
                    f"""
                    UPDATE {dms_jobsch_full}
                    SET dpnd_jobschid = %s, recupdt = CURRENT_TIMESTAMP
                    WHERE jobschid = %s AND curflg = 'Y'
                    """,
                    (parent_schedule["JOBSCHID"], child_schedule["JOBSCHID"]),
                )
            else:  # Oracle
                schema_prefix = f'{self.schema}.' if self.schema else ''
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_JOBSCH
                    SET dpnd_jobschid = :parent_jobschid, recupdt = SYSTIMESTAMP
                    WHERE jobschid = :child_jobschid AND curflg = 'Y'
                    """,
                    {
                        "parent_jobschid": parent_schedule["JOBSCHID"],
                        "child_jobschid": child_schedule["JOBSCHID"],
                    },
                )
            self.connection.commit()
            info(f"Dependency saved: {parent_mapref} -> {child_mapref}")
        except SchedulerError:
            self.connection.rollback()
            raise
        except Exception as exc:
            self.connection.rollback()
            raise SchedulerRepositoryError(str(exc)) from exc
        finally:
            cursor.close()

    def enable_disable_schedule(self, mapref: str, action: str) -> None:
        if action not in {"E", "D"}:
            raise SchedulerValidationError("Action must be 'E' (enable) or 'D' (disable).")
        cursor = self.connection.cursor()
        try:
            schedule = self._fetch_active_schedule(cursor, mapref)
            if not schedule:
                raise SchedulerValidationError(f"No active schedule found for {mapref}.")
            desired_flag = "Y" if action == "E" else "N"
            
            # If enabling and next run date is null, recalculate it
            next_run_dt = None
            if action == "E" and not schedule.get("NXT_RUN_DT"):
                timezone = os.getenv('DMS_TIMEZONE', 'UTC')
                next_run_dt = _calculate_next_run_time(
                    schedule.get("FRQCD"),
                    schedule.get("FRQDD"),
                    schedule.get("FRQHH"),
                    schedule.get("FRQMI"),
                    schedule.get("STRTDT").date() if schedule.get("STRTDT") else None,
                    schedule.get("ENDDT").date() if schedule.get("ENDDT") else None,
                    timezone
                )
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if self.db_type == "POSTGRESQL":
                schema_lower = self.schema.lower() if self.schema else 'public'
                dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                schema_prefix = f'{schema_lower}.' if self.schema else ''
                dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                if next_run_dt:
                    cursor.execute(
                        f"""
                        UPDATE {dms_jobsch_full}
                        SET schflg = %s, nxt_run_dt = %s, recupdt = CURRENT_TIMESTAMP
                        WHERE jobschid = %s
                        """,
                        (desired_flag, next_run_dt, schedule["JOBSCHID"]),
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE {dms_jobsch_full}
                        SET schflg = %s, recupdt = CURRENT_TIMESTAMP
                        WHERE jobschid = %s
                        """,
                        (desired_flag, schedule["JOBSCHID"]),
                    )
            else:  # Oracle
                schema_prefix = f'{self.schema}.' if self.schema else ''
                if next_run_dt:
                    cursor.execute(
                        f"""
                        UPDATE {schema_prefix}DMS_JOBSCH
                        SET schflg = :schflg, nxt_run_dt = :nxt_run_dt, recupdt = SYSTIMESTAMP
                        WHERE jobschid = :jobschid
                        """,
                        {"schflg": desired_flag, "nxt_run_dt": next_run_dt, "jobschid": schedule["JOBSCHID"]},
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE {schema_prefix}DMS_JOBSCH
                        SET schflg = :schflg, recupdt = SYSTIMESTAMP
                        WHERE jobschid = :jobschid
                        """,
                        {"schflg": desired_flag, "jobschid": schedule["JOBSCHID"]},
                    )
            self.connection.commit()
            action_text = "enabled" if action == "E" else "disabled"
            info(f"Schedule {action_text} for {mapref}")
        except SchedulerError:
            self.connection.rollback()
            raise
        except Exception as exc:
            self.connection.rollback()
            raise SchedulerRepositoryError(str(exc)) from exc
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    # Queue helpers for immediate / history / stop operations
    # ------------------------------------------------------------------ #
    def queue_immediate_job(self, request: ImmediateJobRequest) -> str:
        return self._insert_queue_request(
            mapref=request.mapref,
            request_type=request.request_type,
            payload=request.params,
        )

    def queue_history_job(self, request: HistoryJobRequest) -> str:
        payload = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "truncate_flag": request.truncate_flag,
        }
        return self._insert_queue_request(
            mapref=request.mapref,
            request_type=JobRequestType.HISTORY,
            payload=payload,
        )

    def queue_report_request(self, report_id: int, payload: Optional[Dict[str, Any]] = None) -> str:
        if not report_id:
            raise SchedulerValidationError("Report ID is required.")
        normalized_payload = payload.copy() if payload else {}
        normalized_payload["reportId"] = report_id
        mapref = f"REPORT:{report_id}"
        return self._insert_queue_request(
            mapref=mapref,
            request_type=JobRequestType.REPORT,
            payload=normalized_payload,
        )

    def queue_file_upload_request(self, flupldref: str, payload: Optional[Dict[str, Any]] = None) -> str:
        if not flupldref:
            raise SchedulerValidationError("File upload reference is required.")
        normalized_payload = payload.copy() if payload else {}
        normalized_payload["flupldref"] = flupldref
        mapref = f"FLUPLD:{flupldref}"
        return self._insert_queue_request(
            mapref=mapref,
            request_type=JobRequestType.FILE_UPLOAD,
            payload=normalized_payload,
        )

    def request_job_stop(self, mapref: str, start_timestamp: datetime, force: str = "N") -> str:
        payload = {
            "start_timestamp": start_timestamp.isoformat(),
            "force": force,
        }
        return self._insert_queue_request(
            mapref=mapref,
            request_type=JobRequestType.STOP,
            payload=payload,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _fetch_active_job_flow(self, cursor, mapref: str) -> Optional[Dict[str, Any]]:
        # Get table reference for PostgreSQL (handles case sensitivity)
        if self.db_type == "POSTGRESQL":
            schema_lower = self.schema.lower() if self.schema else 'public'
            dms_jobflw_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBFLW')
            dms_jobflw_ref = f'"{dms_jobflw_table}"' if dms_jobflw_table != dms_jobflw_table.lower() else dms_jobflw_table
            schema_prefix = f'{schema_lower}.' if self.schema else ''
            dms_jobflw_full = f'{schema_prefix}{dms_jobflw_ref}'
            cursor.execute(
                f"""
                SELECT jobflwid, jobid, stflg
                FROM {dms_jobflw_full}
                WHERE mapref = %s
                  AND curflg = 'Y'
                  AND stflg = 'A'
                """,
                (mapref,),
            )
        else:  # Oracle
            schema_prefix = f'{self.schema}.' if self.schema else ''
            cursor.execute(
                f"""
                SELECT jobflwid, jobid, stflg
                FROM {schema_prefix}DMS_JOBFLW
                WHERE mapref = :mapref
                  AND curflg = 'Y'
                  AND stflg = 'A'
                """,
                {"mapref": mapref},
            )
        row = cursor.fetchone()
        if not row:
            return None
        return {"JOBFLWID": row[0], "JOBID": row[1], "STFLG": row[2]}

    def _fetch_active_schedule(self, cursor, mapref: str) -> Optional[Dict[str, Any]]:
        # Get table reference for PostgreSQL (handles case sensitivity)
        if self.db_type == "POSTGRESQL":
            schema_lower = self.schema.lower() if self.schema else 'public'
            dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
            dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
            schema_prefix = f'{schema_lower}.' if self.schema else ''
            dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
            cursor.execute(
                f"""
                SELECT jobschid, frqcd, frqdd, frqhh, frqmi, strtdt, enddt, schflg, nxt_run_dt
                FROM {dms_jobsch_full}
                WHERE mapref = %s
                  AND curflg = 'Y'
                """,
                (mapref,),
            )
        else:  # Oracle
            schema_prefix = f'{self.schema}.' if self.schema else ''
            cursor.execute(
                f"""
                SELECT jobschid, frqcd, frqdd, frqhh, frqmi, strtdt, enddt, schflg, nxt_run_dt
                FROM {schema_prefix}DMS_JOBSCH
                WHERE mapref = :mapref
                  AND curflg = 'Y'
                """,
                {"mapref": mapref},
            )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "JOBSCHID": row[0],
            "FRQCD": row[1],
            "FRQDD": row[2],
            "FRQHH": row[3],
            "FRQMI": row[4],
            "STRTDT": row[5],
            "ENDDT": row[6],
            "SCHFLG": row[7],
            "NXT_RUN_DT": row[8] if len(row) > 8 else None,
        }

    @staticmethod
    def _schedule_matches(schedule_row: Dict[str, Any], request: ScheduleRequest) -> bool:
        return (
            schedule_row["FRQCD"] == request.frequency_code
            and (schedule_row["FRQDD"] or None) == request.frequency_day
            and (schedule_row["FRQHH"] or None) == request.frequency_hour
            and (schedule_row["FRQMI"] or None) == request.frequency_minute
            and schedule_row["STRTDT"].date() == request.start_date
            and (
                (schedule_row["ENDDT"].date() if schedule_row["ENDDT"] else None)
                == request.end_date
            )
        )

    def _insert_queue_request(
        self,
        mapref: str,
        request_type: JobRequestType,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not mapref:
            raise SchedulerValidationError("Mapping reference is required.")
        cursor = self.connection.cursor()
        try:
            request_id = str(uuid.uuid4())
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if self.db_type == "POSTGRESQL":
                schema_lower = self.schema.lower() if self.schema else 'public'
                dms_prcreq_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCREQ')
                # Quote table name if it contains uppercase letters (was created with quotes)
                dms_prcreq_ref = f'"{dms_prcreq_table}"' if dms_prcreq_table != dms_prcreq_table.lower() else dms_prcreq_table
                schema_prefix = f'{schema_lower}.' if self.schema else ''
                dms_prcreq_full = f'{schema_prefix}{dms_prcreq_ref}'
                
                # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
                cursor.execute(
                    f"""
                    INSERT INTO {dms_prcreq_full} (
                        request_id,
                        mapref,
                        request_type,
                        payload,
                        status,
                        requested_at
                    ) VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        'NEW',
                        CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        request_id,
                        mapref,
                        request_type.value,
                        _serialize_payload(payload or {}),
                    ),
                )
            else:  # Oracle
                schema_prefix = f'{self.schema}.' if self.schema else ''
                # Oracle: Use :param for bind variables and SYSTIMESTAMP
                cursor.execute(
                    f"""
                    INSERT INTO {schema_prefix}DMS_PRCREQ (
                        request_id,
                        mapref,
                        request_type,
                        payload,
                        status,
                        requested_at
                    ) VALUES (
                        :request_id,
                        :mapref,
                        :request_type,
                        :payload,
                        'NEW',
                        SYSTIMESTAMP
                    )
                    """,
                    {
                        "request_id": request_id,
                        "mapref": mapref,
                        "request_type": request_type.value,
                        "payload": _serialize_payload(payload or {}),
                    },
                )
            self.connection.commit()
            info(f"Queued {request_type.value} request {request_id} for mapref {mapref}")
            return request_id
        except Exception as exc:
            self.connection.rollback()
            raise SchedulerRepositoryError(str(exc)) from exc
        finally:
            cursor.close()


__all__ = [
    "JobSchedulerService",
    "ScheduleRequest",
    "ScheduleResult",
    "ImmediateJobRequest",
    "HistoryJobRequest",
    "SchedulerError",
    "SchedulerValidationError",
    "SchedulerRepositoryError",
    "JobRequestType",
]

