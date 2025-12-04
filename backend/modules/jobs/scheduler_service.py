"""
Background scheduler service that replaces Oracle DBMS_SCHEDULER.

The service is intentionally framework-agnostic so it can run as a separate
process (or container) alongside the web application.  It performs three key
tasks:

1. Synchronise recurring job schedules from DMS_JOBSCH into APScheduler.
2. Poll DMS_PRCREQ for immediate/history/stop/report requests.
3. Execute job flows (or reports) using the execution engine, logging results
   back to DMS_PRCLOG/DMS_JOBLOG/DMS_JOBERR just like the PL/SQL package did.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.database.dbconnect import create_metadata_connection
    from backend.modules.logger import info, error, debug
    from backend.modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name
    from backend.modules.jobs.pkgdwprc_python import (
        JobRequestType,
        JobSchedulerService,
        ImmediateJobRequest,
    )
    from backend.modules.jobs.scheduler_models import SchedulerConfig, QueueRequest
    from backend.modules.jobs.execution_engine import JobExecutionEngine
    from backend.modules.jobs.scheduler_frequency import build_trigger
except ImportError:  # When running Flask app.py directly inside backend
    # Fallback imports for legacy Flask-style context
    try:
        from database.dbconnect import create_metadata_connection  # type: ignore
        from modules.logger import info, error, debug  # type: ignore
        from modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name  # type: ignore
        from modules.jobs.pkgdwprc_python import (  # type: ignore
            JobRequestType,
            JobSchedulerService,
            ImmediateJobRequest,
        )
        from modules.jobs.scheduler_models import SchedulerConfig, QueueRequest  # type: ignore
        from modules.jobs.execution_engine import JobExecutionEngine  # type: ignore
        from modules.jobs.scheduler_frequency import build_trigger  # type: ignore
    except ImportError:
        # As a last resort, re-raise to surface the real import problem
        raise
import os


def _read_lob(value):
    """Helper function to read Oracle LOB objects."""
    if value is None:
        return None
    if hasattr(value, "read"):
        data = value.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data
    return value


class SchedulerService:
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.scheduler = BackgroundScheduler(timezone=self.config.timezone)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.engine = JobExecutionEngine()
        self._stop_event = threading.Event()
        self._scheduled_job_ids = set()

    def start(self) -> None:
        info("Starting scheduler service")
        self.scheduler.add_job(
            self._sync_schedules,
            IntervalTrigger(seconds=self.config.schedule_refresh_seconds),
            name="sync_schedules",
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.add_job(
            self._poll_queue,
            IntervalTrigger(seconds=self.config.poll_interval_seconds),
            name="poll_queue",
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            info("Scheduler service received KeyboardInterrupt")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self._stop_event.is_set():
            return
        info("Stopping scheduler service")
        self._stop_event.set()
        self.scheduler.shutdown(wait=False)
        self.executor.shutdown(wait=True)

    # ------------------------------------------------------------------ #
    # Schedule sync + queue polling
    # ------------------------------------------------------------------ #
    def _sync_schedules(self) -> None:
        """
        Refresh APScheduler jobs from DMS_JOBSCH.  This is a placeholder that
        simply logs the desire to sync; the concrete implementation will map
        frequency codes to APScheduler triggers.
        """
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                # Quote table name if it contains uppercase letters (was created with quotes)
                dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                
                cursor.execute(
                    f"""
                    SELECT jobschid, mapref, frqcd, frqdd, frqhh, frqmi,
                           strtdt, enddt, schflg
                    FROM {dms_jobsch_full}
                    WHERE curflg = 'Y'
                    """
                )
            else:  # Oracle
                schema_prefix = f'{schema}.' if schema else ''
                cursor.execute(
                    f"""
                    SELECT jobschid, mapref, frqcd, frqdd, frqhh, frqmi,
                           strtdt, enddt, schflg
                    FROM {schema_prefix}DMS_JOBSCH
                    WHERE curflg = 'Y'
                    """
                )
            
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            # Normalize column names to uppercase for consistency
            columns = [col.upper() if col else col for col in columns]

        desired_jobs = {}
        for row in rows:
            record = {columns[i]: row[i] for i in range(len(columns))}
            job_id = f"schedule:{record['JOBSCHID']}"
            if record.get("SCHFLG") == "Y":
                desired_jobs[job_id] = record

        current_jobs = set(self._scheduled_job_ids)
        for job_id in current_jobs - desired_jobs.keys():
            try:
                self.scheduler.remove_job(job_id)
                self._scheduled_job_ids.remove(job_id)
                info(f"Removed schedule job {job_id}")
            except Exception:
                continue

        for job_id, record in desired_jobs.items():
            if job_id in self._scheduled_job_ids:
                continue
            try:
                trigger = build_trigger(record, self.config.timezone)
                self.scheduler.add_job(
                    self._enqueue_scheduled_job,
                    trigger=trigger,
                    id=job_id,
                    args=[record["MAPREF"], record["JOBSCHID"]],
                    replace_existing=True,
                )
                self._scheduled_job_ids.add(job_id)
                info(
                    f"Scheduled job {job_id} for mapref {record['MAPREF']} (frequency={record['FRQCD']})"
                )
            except Exception as exc:
                error(
                    f"Failed to schedule job {job_id} ({record['MAPREF']}): {exc}"
                )

        self._sync_report_schedules()

    def _sync_report_schedules(self) -> None:
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')

            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_rprt_schd_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_RPRT_SCHD')
                dms_rprt_schd_ref = f'"{dms_rprt_schd_table}"' if dms_rprt_schd_table != dms_rprt_schd_table.lower() else dms_rprt_schd_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_rprt_schd_full = f'{schema_prefix}{dms_rprt_schd_ref}'
                cursor.execute(
                    f"""
                    SELECT schdid, rprtid, frqncy, tm_prm, otpt_fmt, dstn_typ, emal_to, fl_pth,
                           nxt_run_dt, lst_run_dt, stts
                    FROM {dms_rprt_schd_full}
                    WHERE UPPER(COALESCE(stts, '')) = 'ACTIVE'
                    """
                )
            else:
                schema_prefix = f'{schema}.' if schema else ''
                cursor.execute(
                    f"""
                    SELECT schdid, rprtid, frqncy, tm_prm, otpt_fmt, dstn_typ, emal_to, fl_pth,
                           nxt_run_dt, lst_run_dt, stts
                    FROM {schema_prefix}DMS_RPRT_SCHD
                    WHERE UPPER(COALESCE(stts, '')) = 'ACTIVE'
                    """
                )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        # Use scheduler timezone and make sure comparisons are tz-aware
        now = datetime.now(self.scheduler.timezone)
        schedules = [{columns[i].upper(): row[i] for i in range(len(columns))} for row in rows]
        for sched in schedules:
            next_run = sched.get("NXT_RUN_DT") or now
            if isinstance(next_run, datetime):
                # If DB datetime is naive, assume scheduler timezone
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=self.scheduler.timezone)
            else:
                next_run = now
            if next_run > now:
                continue
            report_id = sched.get("RPRTID")
            schedule_id = sched.get("SCHDID")
            # Build payload for ReportExecutor based on schedule delivery options
            raw_format = (sched.get("OTPT_FMT") or "").upper()
            raw_dest = (sched.get("DSTN_TYP") or "").upper()
            output_format = raw_format or "CSV"
            destination = raw_dest or "FILE"
            payload = {
                "outputFormat": output_format,
                "destination": destination,
                "requestedBy": "system",
            }
            email_to = sched.get("EMAL_TO")
            if email_to:
                payload["email"] = email_to
            file_path = sched.get("FL_PTH")
            if file_path:
                payload["filePath"] = file_path
            try:
                self._queue_report_request(report_id, payload)
                next_dt, status = self._calculate_next_report_run(sched.get("FRQNCY"), now)
                self._update_report_schedule(schedule_id, last_run=now, next_run=next_dt, status=status)
                info(f"Queued report schedule {schedule_id} for report {report_id}")
            except Exception as exc:
                error(f"Failed to process report schedule {schedule_id} (report {report_id}): {exc}")

    def _poll_queue(self) -> None:
        """
        Poll DMS_PRCREQ for pending requests.
        """
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_prcreq_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCREQ')
                # Quote table name if it contains uppercase letters (was created with quotes)
                dms_prcreq_ref = f'"{dms_prcreq_table}"' if dms_prcreq_table != dms_prcreq_table.lower() else dms_prcreq_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_prcreq_full = f'{schema_prefix}{dms_prcreq_ref}'
                
                # PostgreSQL: Use LIMIT instead of FETCH FIRST
                cursor.execute(
                    f"""
                    SELECT request_id, mapref, request_type, payload
                    FROM {dms_prcreq_full}
                    WHERE status = 'NEW'
                    ORDER BY requested_at
                    LIMIT 25
                    """
                )
            else:  # Oracle
                schema_prefix = f'{schema}.' if schema else ''
                cursor.execute(
                    f"""
                    SELECT request_id, mapref, request_type, payload
                    FROM {schema_prefix}DMS_PRCREQ
                    WHERE status = 'NEW'
                    ORDER BY requested_at
                    FETCH FIRST 25 ROWS ONLY
                    """
                )
            
            rows = cursor.fetchall()
            if not rows:
                debug("No pending scheduler requests")
                return

            claimed_ids: List[str] = []
            requests: List[QueueRequest] = []
            for row in rows:
                req_id, mapref, req_type, payload = row
                # Read LOB object if it's a LOB
                payload_str = _read_lob(payload)
                payload_dict = json.loads(payload_str) if payload_str else {}
                requests.append(
                    QueueRequest(
                        request_id=req_id,
                        mapref=mapref,
                        request_type=JobRequestType(req_type),
                        payload=payload_dict,
                    )
                )
                claimed_ids.append(req_id)

            # Update with database-specific syntax
            if db_type == "POSTGRESQL":
                cursor.executemany(
                    f"""
                    UPDATE {dms_prcreq_full}
                    SET status = 'CLAIMED',
                        claimed_at = CURRENT_TIMESTAMP,
                        claimed_by = %s
                    WHERE request_id = %s
                    """,
                    [
                        ("PY_SCHED", request_id)
                        for request_id in claimed_ids
                    ],
                )
            else:  # Oracle
                cursor.executemany(
                    f"""
                    UPDATE {schema_prefix}DMS_PRCREQ
                    SET status = 'CLAIMED',
                        claimed_at = SYSTIMESTAMP,
                        claimed_by = :claimed_by
                    WHERE request_id = :request_id
                    """,
                    [
                        {"claimed_by": "PY_SCHED", "request_id": request_id}
                        for request_id in claimed_ids
                    ],
                )
            cursor.connection.commit()

        for request in requests:
            self.executor.submit(self._execute_request, request)

    def _execute_request(self, request: QueueRequest) -> None:
        try:
            # Handle REPORT type requests separately
            if request.request_type.value == "REPORT":
                result = self._execute_report_request(request)
            else:
                result = self.engine.execute(request)
            self._mark_request_complete(request, "DONE", result)
        except Exception as exc:
            import traceback
            error_msg = str(exc)
            error_trace = traceback.format_exc()
            error(
                f"Error executing request {request.request_id} ({request.request_type.value}): {error_msg}\n"
                f"Request details: mapref={request.mapref}, payload={request.payload}\n"
                f"Traceback:\n{error_trace}"
            )
            try:
                self._mark_request_complete(
                    request,
                    "FAILED",
                    {"message": error_msg},
                )
            except Exception as mark_exc:
                error(f"Failed to mark request as failed: {mark_exc}")

    def _execute_report_request(self, request: QueueRequest) -> Dict[str, Any]:
        """Execute a REPORT type request using the ReportExecutor."""
        # Support both FastAPI (package import) and legacy Flask (relative import) contexts
        try:
            from backend.modules.reports.report_executor import get_report_executor
        except ImportError:  # When running Flask app.py directly inside backend
            from modules.reports.report_executor import get_report_executor  # type: ignore

        payload = request.payload or {}
        # Ensure the downstream executor knows the originating queue request ID
        # so it can be stored in DMS_RPRT_RUN.RQST_ID (NOT NULL column).
        if "requestId" not in payload:
            payload["requestId"] = request.request_id
        report_id = payload.get("reportId")
        
        if not report_id:
            # Try to extract from mapref (format: "REPORT:123")
            if request.mapref and request.mapref.startswith("REPORT:"):
                report_id = int(request.mapref.split(":")[1])
        
        if not report_id:
            raise ValueError("Report ID not found in request payload or mapref")
        
        executor = get_report_executor()
        result = executor.execute_report(report_id=report_id, payload=payload)
        
        info(f"[SchedulerService] Report {report_id} executed successfully: {result}")
        return result

    def _mark_request_complete(self, request: QueueRequest, status: str, payload: Dict[str, Any]) -> None:
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_prcreq_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCREQ')
                # Quote table name if it contains uppercase letters (was created with quotes)
                dms_prcreq_ref = f'"{dms_prcreq_table}"' if dms_prcreq_table != dms_prcreq_table.lower() else dms_prcreq_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_prcreq_full = f'{schema_prefix}{dms_prcreq_ref}'
                
                # PostgreSQL: Use %s for bind variables and CURRENT_TIMESTAMP
                cursor.execute(
                    f"""
                    UPDATE {dms_prcreq_full}
                    SET status = %s,
                        result_payload = %s,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE request_id = %s
                    """,
                    (
                        status,
                        json.dumps(payload, default=str),
                        request.request_id,
                    ),
                )
            else:  # Oracle
                schema_prefix = f'{schema}.' if schema else ''
                # Oracle: Use :param for bind variables and SYSTIMESTAMP
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_PRCREQ
                    SET status = :status,
                        result_payload = :result_payload,
                        completed_at = SYSTIMESTAMP
                    WHERE request_id = :request_id
                    """,
                    {
                        "status": status,
                        "result_payload": json.dumps(payload, default=str),
                        "request_id": request.request_id,
                    },
                )
            cursor.connection.commit()

        if (
            status == "DONE"
            and payload.get("status") == "SUCCESS"
            and request.request_type in {JobRequestType.IMMEDIATE, JobRequestType.HISTORY}
        ):
            self._enqueue_child_jobs(request.mapref)

    # ------------------------------------------------------------------ #
    # DB helpers
    # ------------------------------------------------------------------ #
    @contextmanager
    def _db_cursor(self):
        connection = create_metadata_connection()
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            finally:
                connection.close()

    def _enqueue_scheduled_job(self, mapref: str, jobschid: Optional[int] = None) -> None:
        info(f"Enqueuing scheduled job for {mapref} (jobschid={jobschid})")
        payload = {"source": "schedule", "jobschid": jobschid}
        self._queue_immediate_job(mapref, payload)

    def _queue_immediate_job(self, mapref: str, payload: Optional[Dict[str, Any]] = None) -> None:
        connection = None
        try:
            connection = create_metadata_connection()
            service = JobSchedulerService(connection)
            service.queue_immediate_job(
                ImmediateJobRequest(
                    mapref=mapref,
                    params=payload or {},
                )
            )
        except Exception as exc:
            error(f"Failed to enqueue job {mapref}: {exc}")
        finally:
            if connection:
                connection.close()

    def _queue_report_request(self, report_id: int, payload: Optional[Dict[str, Any]] = None) -> None:
        connection = None
        try:
            connection = create_metadata_connection()
            service = JobSchedulerService(connection)
            service.queue_report_request(report_id=report_id, payload=payload)
        except Exception as exc:
            error(f"Failed to enqueue report {report_id}: {exc}")
            raise
        finally:
            if connection:
                connection.close()

    def _update_report_schedule(self, schedule_id: int, last_run: datetime, next_run: Optional[datetime], status: Optional[str]):
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_rprt_schd_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_RPRT_SCHD')
                dms_rprt_schd_ref = f'"{dms_rprt_schd_table}"' if dms_rprt_schd_table != dms_rprt_schd_table.lower() else dms_rprt_schd_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_rprt_schd_full = f'{schema_prefix}{dms_rprt_schd_ref}'
                cursor.execute(
                    f"""
                    UPDATE {dms_rprt_schd_full}
                    SET lst_run_dt = %s,
                        nxt_run_dt = %s,
                        stts = %s
                    WHERE schdid = %s
                    """,
                    (last_run, next_run, status or "ACTIVE", schedule_id),
                )
            else:
                schema_prefix = f'{schema}.' if schema else ''
                cursor.execute(
                    f"""
                    UPDATE {schema_prefix}DMS_RPRT_SCHD
                    SET lst_run_dt = :last_run,
                        nxt_run_dt = :next_run,
                        stts = :status
                    WHERE schdid = :schdid
                    """,
                    {
                        "last_run": last_run,
                        "next_run": next_run,
                        "status": status or "ACTIVE",
                        "schdid": schedule_id,
                    },
                )
            cursor.connection.commit()

    def _calculate_next_report_run(self, frequency: Optional[str], reference: datetime) -> Tuple[Optional[datetime], str]:
        freq = (frequency or "DAILY").upper()
        if freq == "IMMEDIATE":
            return None, "PAUSED"
        if freq == "HOURLY":
            return reference + timedelta(hours=1), "ACTIVE"
        if freq == "DAILY":
            return reference + timedelta(days=1), "ACTIVE"
        if freq == "WEEKLY":
            return reference + timedelta(days=7), "ACTIVE"
        if freq == "MONTHLY":
            return reference + timedelta(days=30), "ACTIVE"
        if freq == "QUARTERLY":
            return reference + timedelta(days=90), "ACTIVE"
        if freq == "YEARLY":
            return reference + timedelta(days=365), "ACTIVE"
        return reference + timedelta(days=1), "ACTIVE"

    def _enqueue_child_jobs(self, parent_mapref: str) -> None:
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')
            
            # Get table reference for PostgreSQL (handles case sensitivity)
            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                # Quote table name if it contains uppercase letters (was created with quotes)
                dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                
                # PostgreSQL: Use %s for bind variables
                cursor.execute(
                    f"""
                    SELECT child.mapref, child.jobschid
                    FROM {dms_jobsch_full} child
                    JOIN {dms_jobsch_full} parent
                      ON child.dpnd_jobschid = parent.jobschid
                    WHERE parent.mapref = %s
                      AND parent.curflg = 'Y'
                      AND child.curflg = 'Y'
                      AND child.schflg = 'Y'
                    """,
                    (parent_mapref,),
                )
            else:  # Oracle
                schema_prefix = f'{schema}.' if schema else ''
                # Oracle: Use :param for bind variables
                cursor.execute(
                    f"""
                    SELECT child.mapref, child.jobschid
                    FROM {schema_prefix}DMS_JOBSCH child
                    JOIN {schema_prefix}DMS_JOBSCH parent
                      ON child.dpnd_jobschid = parent.jobschid
                    WHERE parent.mapref = :parent_mapref
                      AND parent.curflg = 'Y'
                      AND child.curflg = 'Y'
                      AND child.schflg = 'Y'
                    """,
                    {"parent_mapref": parent_mapref},
                )
            rows = cursor.fetchall()

        for child_mapref, child_jobschid in rows:
            info(f"Parent {parent_mapref} completed; enqueueing child {child_mapref}")
            self._enqueue_scheduled_job(child_mapref, child_jobschid)


def main() -> None:
    service = SchedulerService()
    service.start()


if __name__ == "__main__":
    main()

