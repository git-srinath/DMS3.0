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

from modules.logger import info, error

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


def _generate_numeric_id(cursor, sequence_name: str) -> int:
    """
    Generate surrogate numeric ID. Tries to use Oracle sequences first,
    otherwise falls back to a timestamp-based integer.
    """
    try:
        cursor.execute(f"SELECT {sequence_name}.NEXTVAL FROM dual")
        row = cursor.fetchone()
        if row:
            return int(row[0])
    except Exception:
        # Fallback for non-Oracle databases
        return int(datetime.utcnow().timestamp() * 1000)
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
                cursor.execute(
                    """
                    UPDATE DWJOBSCH
                    SET curflg = 'N', recupdt = SYSTIMESTAMP
                    WHERE jobschid = :jobschid
                    """,
                    {"jobschid": replaced_jobschid},
                )

            jobschid = _generate_numeric_id(cursor, "DWJOBSCHSEQ")
            cursor.execute(
                """
                INSERT INTO DWJOBSCH (
                    jobschid, jobflwid, mapref,
                    frqcd, frqdd, frqhh, frqmi,
                    strtdt, enddt, stflg,
                    reccrdt, recupdt, curflg, schflg
                ) VALUES (
                    :jobschid, :jobflwid, :mapref,
                    :frqcd, :frqdd, :frqhh, :frqmi,
                    :strtdt, :enddt, 'N',
                    SYSTIMESTAMP, SYSTIMESTAMP, 'Y', 'N'
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

            cursor.execute(
                """
                UPDATE DWJOBSCH
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
            cursor.execute(
                """
                UPDATE DWJOBSCH
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
        cursor.execute(
            """
            SELECT jobflwid, jobid
            FROM DWJOBFLW
            WHERE mapref = :mapref
              AND curflg = 'Y'
              AND stflg = 'A'
            """,
            {"mapref": mapref},
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {"JOBFLWID": row[0], "JOBID": row[1]}

    def _fetch_active_schedule(self, cursor, mapref: str) -> Optional[Dict[str, Any]]:
        cursor.execute(
            """
            SELECT jobschid, frqcd, frqdd, frqhh, frqmi, strtdt, enddt, schflg
            FROM DWJOBSCH
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
            cursor.execute(
                """
                INSERT INTO DWPRCREQ (
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

