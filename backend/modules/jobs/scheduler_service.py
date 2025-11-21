"""
Background scheduler service that replaces Oracle DBMS_SCHEDULER.

The service is intentionally framework-agnostic so it can run as a separate
process (or container) alongside the web application.  It performs three key
tasks:

1. Synchronise recurring job schedules from DWJOBSCH into APScheduler.
2. Poll DWPRCREQ for immediate/history/stop/report requests.
3. Execute job flows (or reports) using the execution engine, logging results
   back to DWPRCLOG/DWJOBLOG/DWJOBERR just like the PL/SQL package did.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database.dbconnect import create_oracle_connection
from modules.logger import info, error, debug
from modules.jobs.pkgdwprc_python import (
    JobRequestType,
    JobSchedulerService,
    ImmediateJobRequest,
)
from modules.jobs.scheduler_models import SchedulerConfig, QueueRequest
from modules.jobs.execution_engine import JobExecutionEngine
from modules.jobs.scheduler_frequency import build_trigger


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
        Refresh APScheduler jobs from DWJOBSCH.  This is a placeholder that
        simply logs the desire to sync; the concrete implementation will map
        frequency codes to APScheduler triggers.
        """
        with self._db_cursor() as cursor:
            cursor.execute(
                """
                SELECT jobschid, mapref, frqcd, frqdd, frqhh, frqmi,
                       strtdt, enddt, schflg
                FROM DWJOBSCH
                WHERE curflg = 'Y'
                """
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

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

    def _poll_queue(self) -> None:
        """
        Poll DWPRCREQ for pending requests.
        """
        with self._db_cursor() as cursor:
            cursor.execute(
                """
                SELECT request_id, mapref, request_type, payload
                FROM DWPRCREQ
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

            cursor.executemany(
                """
                UPDATE DWPRCREQ
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

    def _mark_request_complete(self, request: QueueRequest, status: str, payload: Dict[str, Any]) -> None:
        with self._db_cursor() as cursor:
            cursor.execute(
                """
                UPDATE DWPRCREQ
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

        if status == "DONE" and payload.get("status") == "SUCCESS":
            self._enqueue_child_jobs(request.mapref)

    # ------------------------------------------------------------------ #
    # DB helpers
    # ------------------------------------------------------------------ #
    @contextmanager
    def _db_cursor(self):
        connection = create_oracle_connection()
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
            connection = create_oracle_connection()
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

    def _enqueue_child_jobs(self, parent_mapref: str) -> None:
        with self._db_cursor() as cursor:
            cursor.execute(
                """
                SELECT child.mapref, child.jobschid
                FROM DWJOBSCH child
                JOIN DWJOBSCH parent
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

