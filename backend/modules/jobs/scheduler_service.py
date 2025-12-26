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
    from backend.modules.logger import info, error, debug, warning
    from backend.modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name
    from backend.modules.jobs.pkgdwprc_python import (
        JobRequestType,
        JobSchedulerService,
        ImmediateJobRequest,
        _calculate_next_run_time,
    )
    from backend.modules.jobs.scheduler_models import SchedulerConfig, QueueRequest
    from backend.modules.jobs.execution_engine import JobExecutionEngine
    from backend.modules.jobs.scheduler_frequency import build_trigger
except ImportError:  # When running Flask app.py directly inside backend
    # Fallback imports for legacy Flask-style context
    try:
        from database.dbconnect import create_metadata_connection  # type: ignore
        from modules.logger import info, error, debug, warning  # type: ignore
        from modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name  # type: ignore
        from modules.jobs.pkgdwprc_python import (  # type: ignore
            JobRequestType,
            JobSchedulerService,
            ImmediateJobRequest,
            _calculate_next_run_time,
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
        # Allow timezone to be overridden via env (e.g., DMS_TIMEZONE=Asia/Kolkata)
        env_tz = os.getenv("DMS_TIMEZONE")
        if config:
            self.config = config
            if env_tz:
                self.config.timezone = env_tz
        else:
            self.config = SchedulerConfig(timezone=env_tz or "UTC")
        
        # Validate and fix timezone
        timezone_str = self.config.timezone
        validated_timezone = self._validate_timezone(timezone_str)
        if validated_timezone != timezone_str:
            self.config.timezone = validated_timezone

        self.scheduler = BackgroundScheduler(timezone=self.config.timezone)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.engine = JobExecutionEngine()
        self._stop_event = threading.Event()
        self._scheduled_job_ids = set()

    def start(self) -> None:
        info("=" * 80)
        info("Starting scheduler service")
        info(f"Schedule refresh interval: {self.config.schedule_refresh_seconds} seconds")
        info(f"Queue poll interval: {self.config.poll_interval_seconds} seconds")
        info(f"Max workers: {self.config.max_workers}")
        info(f"Timezone: {self.config.timezone}")
        info("=" * 80)
        
        # Add sync_schedules job - this runs periodically to refresh schedules from DB
        sync_job = self.scheduler.add_job(
            self._sync_schedules,
            IntervalTrigger(seconds=self.config.schedule_refresh_seconds),
            name="sync_schedules",
            max_instances=1,
            coalesce=True,
        )
        info(f"Added sync_schedules job to scheduler (runs every {self.config.schedule_refresh_seconds} seconds)")
        info(f"Sync job ID: {sync_job.id}")
        
        # Add poll_queue job - this polls DMS_PRCREQ for pending requests
        poll_job = self.scheduler.add_job(
            self._poll_queue,
            IntervalTrigger(seconds=self.config.poll_interval_seconds),
            name="poll_queue",
            max_instances=1,
            coalesce=True,
        )
        info(f"Added poll_queue job to scheduler (runs every {self.config.poll_interval_seconds} seconds)")
        info(f"Poll job ID: {poll_job.id}")
        
        # Start the scheduler
        self.scheduler.start()
        info("=" * 80)
        info("Scheduler started successfully!")
        info("=" * 80)
        
        # Verify scheduler is running
        if self.scheduler.running:
            info("Scheduler state: RUNNING")
        else:
            error("WARNING: Scheduler state is NOT RUNNING!")
        
        # List all jobs in scheduler (after starting, next_run_time should be available)
        all_jobs = self.scheduler.get_jobs()
        info(f"Total jobs in scheduler: {len(all_jobs)}")
        for job in all_jobs:
            next_run = getattr(job, 'next_run_time', None)
            next_run_str = str(next_run) if next_run else "Not scheduled yet"
            info(f"  - Job: {job.name} (ID: {job.id}), Next run: {next_run_str}")
        
        # Perform an immediate sync on startup to load existing schedules
        info("=" * 80)
        info("Performing initial schedule sync...")
        info("=" * 80)
        try:
            self._sync_schedules()
            info("=" * 80)
            info("Initial schedule sync completed")
            info("=" * 80)
        except Exception as e:
            import traceback
            error("=" * 80)
            error(f"ERROR during initial schedule sync: {e}")
            error(f"Traceback: {traceback.format_exc()}")
            error("=" * 80)
        
        info("Scheduler service is now running. Waiting for jobs...")
        info("=" * 80)
        
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            info("Scheduler service received KeyboardInterrupt")
        finally:
            self.shutdown()

    def _validate_timezone(self, timezone_str: str) -> str:
        """Validate timezone string and fix common typos."""
        if not timezone_str:
            return "UTC"
        
        # Common timezone typos and fixes
        timezone_fixes = {
            'Aisa/Kolkata': 'Asia/Kolkata',
            'Asia/Calcutta': 'Asia/Kolkata',
            'IST': 'Asia/Kolkata',
            'UTC': 'UTC',
        }
        
        # Check if it's a known typo
        if timezone_str in timezone_fixes:
            fixed_tz = timezone_fixes[timezone_str]
            warning(f"Timezone '{timezone_str}' corrected to '{fixed_tz}'")
            timezone_str = fixed_tz
        
        # Try to validate the timezone
        try:
            from zoneinfo import ZoneInfo
            try:
                ZoneInfo(timezone_str)
                return timezone_str
            except Exception:
                # Try with pytz as fallback
                try:
                    from pytz import timezone as tz
                    tz(timezone_str)
                    return timezone_str
                except Exception:
                    warning(f"Invalid timezone '{timezone_str}' - using UTC instead. Please set DMS_TIMEZONE to a valid timezone (e.g., 'Asia/Kolkata', 'America/New_York', 'UTC')")
                    return "UTC"
        except ImportError:
            # zoneinfo not available (Python < 3.9), use pytz
            try:
                from pytz import timezone as tz
                tz(timezone_str)
                return timezone_str
            except Exception:
                warning(f"Invalid timezone '{timezone_str}' - using UTC instead")
                return "UTC"
    
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
        info("[_sync_schedules] Starting schedule synchronization...")
        try:
            with self._db_cursor() as cursor:
                connection = cursor.connection
                db_type = _detect_db_type(connection)
                schema = os.getenv('DMS_SCHEMA', 'TRG')
                
                info(f"[_sync_schedules] Database type: {db_type}, Schema: {schema}")
                
                # Get table reference for PostgreSQL (handles case sensitivity)
                if db_type == "POSTGRESQL":
                    schema_lower = schema.lower() if schema else 'public'
                    dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
                    # Quote table name if it contains uppercase letters (was created with quotes)
                    dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
                    schema_prefix = f'{schema_lower}.' if schema else ''
                    dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
                    
                    info(f"[_sync_schedules] PostgreSQL table: {dms_jobsch_full}")
                    
                    # PostgreSQL is case-sensitive for column names
                    # Try uppercase column names first (if created with quotes), fallback to lowercase
                    # Use a query that works for both cases by trying uppercase first
                    query_success = False
                    try:
                        cursor.execute(
                            f"""
                            SELECT "JOBSCHID", "MAPREF", "FRQCD", "FRQDD", "FRQHH", "FRQMI",
                                   "STRTDT", "ENDDT", "SCHFLG", "NXT_RUN_DT"
                            FROM {dms_jobsch_full}
                            WHERE "CURFLG" = 'Y'
                            """
                        )
                        query_success = True
                    except Exception as e:
                        # If uppercase fails, try lowercase (columns created without quotes)
                        try:
                            cursor.execute(
                                f"""
                                SELECT jobschid, mapref, frqcd, frqdd, frqhh, frqmi,
                                       strtdt, enddt, schflg, nxt_run_dt
                                FROM {dms_jobsch_full}
                                WHERE curflg = 'Y'
                                """
                            )
                            query_success = True
                        except Exception as e2:
                            error(f"[_sync_schedules] Both queries failed. Uppercase error: {e}, Lowercase error: {e2}")
                            return
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
                    query_success = True
                
                if not query_success:
                    error("[_sync_schedules] Failed to execute query")
                    return
                
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                # Normalize column names to uppercase for consistency
                columns = [col.upper() if col else col for col in columns]
                
                info(f"[_sync_schedules] Found {len(rows)} schedule records in DMS_JOBSCH")

            desired_jobs = {}
            for row in rows:
                record = {columns[i]: row[i] for i in range(len(columns))}
                job_id = f"schedule:{record['JOBSCHID']}"
                schflg = record.get("SCHFLG")
                nxt_run_dt = record.get("NXT_RUN_DT")
                info(f"[_sync_schedules] Processing record: JOBSCHID={record['JOBSCHID']}, MAPREF={record.get('MAPREF')}, SCHFLG={schflg}, FRQCD={record.get('FRQCD')}, NXT_RUN_DT={nxt_run_dt}")
                
                if schflg == "Y":
                    desired_jobs[job_id] = record
                    info(f"[_sync_schedules] Added to desired_jobs: {job_id} for {record.get('MAPREF')}")
                else:
                    debug(f"[_sync_schedules] Skipping {job_id} - SCHFLG is not 'Y' (value: {schflg})")

            info(f"[_sync_schedules] Total desired jobs: {len(desired_jobs)}")

            current_jobs = set(self._scheduled_job_ids)
            removed_count = 0
            for job_id in current_jobs - desired_jobs.keys():
                try:
                    self.scheduler.remove_job(job_id)
                    self._scheduled_job_ids.remove(job_id)
                    info(f"[_sync_schedules] Removed schedule job {job_id}")
                    removed_count += 1
                except Exception as e:
                    debug(f"[_sync_schedules] Error removing job {job_id}: {e}")
                    continue
            
            if removed_count > 0:
                info(f"[_sync_schedules] Removed {removed_count} jobs from scheduler")

            added_count = 0
            updated_count = 0
            rescheduled_count = 0
            from datetime import datetime
            scheduler_tz = self.scheduler.timezone
            now = datetime.now(scheduler_tz)
            
            for job_id, record in desired_jobs.items():
                if job_id in self._scheduled_job_ids:
                    # Check if we need to update the job (e.g., if schedule changed or time has passed)
                    try:
                        existing_job = self.scheduler.get_job(job_id)
                        if existing_job:
                            next_run = getattr(existing_job, 'next_run_time', None)
                            if next_run:
                                # Make timezone-aware for comparison
                                if isinstance(next_run, datetime):
                                    if next_run.tzinfo is None:
                                        next_run = next_run.replace(tzinfo=scheduler_tz)
                                    if now.tzinfo is None:
                                        now = now.replace(tzinfo=scheduler_tz)

                                    # Check if next run time is in the past
                                    if next_run < now:
                                        info(f"[_sync_schedules] Job {job_id} next_run ({next_run}) is in the past (now: {now}), rescheduling...")
                                        # Remove and re-add to trigger immediate recalculation
                                        try:
                                            self.scheduler.remove_job(job_id)
                                            self._scheduled_job_ids.remove(job_id)
                                            rescheduled_count += 1
                                            info(f"[_sync_schedules] Removed job {job_id} for rescheduling")
                                            # Continue to re-add it below
                                        except Exception as e:
                                            debug(f"[_sync_schedules] Error removing job {job_id}: {e}")
                                            # Continue to re-add it
                                            if job_id in self._scheduled_job_ids:
                                                self._scheduled_job_ids.remove(job_id)
                                    else:
                                        seconds_until_run = (next_run - now).total_seconds()
                                        info(f"[_sync_schedules] Job {job_id} already scheduled, next run: {next_run} (in {seconds_until_run:.0f} seconds)")
                                        updated_count += 1
                                        continue
                                else:
                                    info(f"[_sync_schedules] Job {job_id} already scheduled, next run: {next_run}")
                                    updated_count += 1
                                    continue
                            else:
                                info(f"[_sync_schedules] Job {job_id} has no next_run_time, rescheduling...")
                                try:
                                    self.scheduler.remove_job(job_id)
                                    self._scheduled_job_ids.remove(job_id)
                                except Exception:
                                    if job_id in self._scheduled_job_ids:
                                        self._scheduled_job_ids.remove(job_id)
                        else:
                            # Job ID in our set but not in scheduler - re-add it
                            info(f"[_sync_schedules] Job {job_id} missing from scheduler, re-adding...")
                            self._scheduled_job_ids.remove(job_id)
                    except Exception as e:
                        debug(f"[_sync_schedules] Error checking existing job {job_id}: {e}")
                        # If we can't check, try to add it anyway
                        if job_id in self._scheduled_job_ids:
                            self._scheduled_job_ids.remove(job_id)
                
                try:
                    info(f"[_sync_schedules] Building trigger for {job_id} (MAPREF={record.get('MAPREF')}, FRQCD={record.get('FRQCD')}, FRQDD={record.get('FRQDD')}, FRQHH={record.get('FRQHH')}, FRQMI={record.get('FRQMI')}, STRTDT={record.get('STRTDT')}, ENDDT={record.get('ENDDT')})")
                    
                    # Fix end_date if it's too restrictive (e.g., tomorrow at midnight when job should run daily)
                    # If end_date is set and it's preventing scheduling, remove it or set it far in the future
                    enddt = record.get('ENDDT')
                    if enddt:
                        from datetime import datetime, timedelta
                        scheduler_tz = self.scheduler.timezone
                        now = datetime.now(scheduler_tz)
                        # Make enddt timezone-aware for comparison
                        if isinstance(enddt, datetime):
                            if enddt.tzinfo is None:
                                enddt = enddt.replace(tzinfo=scheduler_tz)
                            # If end_date is too soon (e.g., within next 7 days), remove it for recurring schedules
                            # This allows the schedule to continue running
                            if enddt < now + timedelta(days=7):
                                info(f"[_sync_schedules] End date {enddt} is too restrictive for recurring schedule (DL={record.get('FRQCD')}), removing it to allow continuous scheduling")
                                record['ENDDT'] = None
                    
                    # Ensure start_date is set - if not provided, use a date in the past so APScheduler can calculate next occurrence
                    # This is critical for APScheduler to calculate next_run_time
                    if not record.get('STRTDT'):
                        from datetime import datetime, timedelta
                        # Use yesterday at the scheduled time so APScheduler will schedule for today (if time hasn't passed) or tomorrow
                        scheduler_tz = self.scheduler.timezone
                        now = datetime.now(scheduler_tz)
                        # Set start_date to yesterday at the scheduled hour/minute
                        hour = record.get('FRQHH') or 0
                        minute = record.get('FRQMI') or 0
                        # Create start_date in scheduler timezone
                        start_date = (now - timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                        # Ensure timezone is set
                        if start_date.tzinfo is None:
                            start_date = scheduler_tz.localize(start_date) if hasattr(scheduler_tz, 'localize') else start_date.replace(tzinfo=scheduler_tz)
                        record['STRTDT'] = start_date
                        info(f"[_sync_schedules] No start_date in schedule, using yesterday at scheduled time: {start_date}")
                    
                    trigger = build_trigger(record, self.config.timezone)
                    info(f"[_sync_schedules] Trigger built successfully: {trigger}, start_date={record.get('STRTDT')}, end_date={record.get('ENDDT')}")
                    
                    job = self.scheduler.add_job(
                        self._enqueue_scheduled_job,
                        trigger=trigger,
                        id=job_id,
                        args=[record["MAPREF"], record["JOBSCHID"]],
                        replace_existing=True,
                    )
                    self._scheduled_job_ids.add(job_id)
                    added_count += 1
                    
                    # Wait a moment for APScheduler to calculate next_run_time
                    import time
                    time.sleep(0.2)
                    
                    # Get the job again to check next_run_time
                    job = self.scheduler.get_job(job_id)
                    next_run = getattr(job, 'next_run_time', None) if job else None
                    next_run_str = str(next_run) if next_run else 'Not scheduled yet'
                    
                    if not next_run:
                        error(f"[_sync_schedules] ERROR: Job {job_id} has no next_run_time! Trigger may not be configured correctly.")
                        error(f"[_sync_schedules] Trigger details: {trigger}")
                        error(f"[_sync_schedules] Start date: {record.get('STRTDT')}, End date: {record.get('ENDDT')}")
                        error(f"[_sync_schedules] Frequency: {record.get('FRQCD')}, Hour: {record.get('FRQHH')}, Minute: {record.get('FRQMI')}")
                    else:
                        # Calculate seconds until next run
                        if isinstance(next_run, datetime):
                            if next_run.tzinfo is None:
                                next_run = next_run.replace(tzinfo=scheduler_tz)
                            if now.tzinfo is None:
                                now = now.replace(tzinfo=scheduler_tz)
                            seconds_until = (next_run - now).total_seconds()
                            info(f"[_sync_schedules] Job {job_id} will run in {seconds_until:.0f} seconds ({seconds_until/60:.1f} minutes)")
                    
                    info(
                        f"[_sync_schedules] Successfully scheduled job {job_id} for mapref {record['MAPREF']} "
                        f"(frequency={record['FRQCD']}, trigger={trigger}, next_run={next_run_str})"
                    )
                except Exception as exc:
                    import traceback
                    error(
                        f"[_sync_schedules] Failed to schedule job {job_id} ({record.get('MAPREF')}): {exc}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
            
            if added_count > 0:
                info(f"[_sync_schedules] Added {added_count} new jobs to scheduler")
            if updated_count > 0:
                info(f"[_sync_schedules] Checked {updated_count} existing jobs in scheduler")
            if rescheduled_count > 0:
                info(f"[_sync_schedules] Rescheduled {rescheduled_count} jobs that were in the past")
            
            # Log all scheduled jobs and their next run times
            if len(self._scheduled_job_ids) > 0:
                info(f"[_sync_schedules] Currently scheduled jobs ({len(self._scheduled_job_ids)}):")
                for job_id in self._scheduled_job_ids:
                    try:
                        job = self.scheduler.get_job(job_id)
                        if job:
                            next_run = getattr(job, 'next_run_time', None)
                            next_run_str = str(next_run) if next_run else "Not scheduled yet"
                            info(f"[_sync_schedules]   - {job_id}: next_run={next_run_str}")
                        else:
                            info(f"[_sync_schedules]   - {job_id}: NOT FOUND in scheduler (will be removed)")
                            self._scheduled_job_ids.remove(job_id)
                    except Exception as e:
                        debug(f"[_sync_schedules] Error getting job {job_id}: {e}")
            else:
                warning("[_sync_schedules] No jobs are currently scheduled in APScheduler!")
            
            info(f"[_sync_schedules] Schedule sync complete. Total scheduled jobs: {len(self._scheduled_job_ids)}")

        except Exception as e:
            import traceback
            error(f"[_sync_schedules] Unexpected error during schedule sync: {e}\nTraceback: {traceback.format_exc()}")

        self._sync_report_schedules()
        self._sync_flupld_schedules()

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

    def _sync_flupld_schedules(self) -> None:
        """Sync file upload schedules from DMS_FLUPLD_SCHD and queue executions when due."""
        with self._db_cursor() as cursor:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
            schema = os.getenv('DMS_SCHEMA', 'TRG')

            if db_type == "POSTGRESQL":
                schema_lower = schema.lower() if schema else 'public'
                dms_flupld_schd_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_FLUPLD_SCHD')
                dms_flupld_schd_ref = f'"{dms_flupld_schd_table}"' if dms_flupld_schd_table != dms_flupld_schd_table.lower() else dms_flupld_schd_table
                schema_prefix = f'{schema_lower}.' if schema else ''
                dms_flupld_schd_full = f'{schema_prefix}{dms_flupld_schd_ref}'
                cursor.execute(
                    f"""
                    SELECT schdid, flupldref, frqncy, tm_prm, nxt_run_dt, lst_run_dt, stts
                    FROM {dms_flupld_schd_full}
                    WHERE UPPER(COALESCE(stts, '')) = 'ACTIVE'
                    """
                )
            else:
                schema_prefix = f'{schema}.' if schema else ''
                cursor.execute(
                    f"""
                    SELECT schdid, flupldref, frqncy, tm_prm, nxt_run_dt, lst_run_dt, stts
                    FROM {schema_prefix}DMS_FLUPLD_SCHD
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
            flupldref = sched.get("FLUPLDREF")
            schedule_id = sched.get("SCHDID")
            frqncy = sched.get("FRQNCY", "DL")
            tm_prm = sched.get("TM_PRM") or ""
            
            info(f"[_sync_flupld_schedules] Processing schedule {schedule_id} for {flupldref}: frqncy={frqncy}, tm_prm={tm_prm}")
            
            # Parse tm_prm to extract frequency_day, hour, minute
            # Format: DL_10:30, WK_MON_10:30, MN_15_10:30, etc.
            freq_day = None
            hour = 0
            minute = 0
            if tm_prm:
                parts = tm_prm.split("_")
                info(f"[_sync_flupld_schedules] Parsed tm_prm parts: {parts}")
                if len(parts) >= 2:
                    # Last part is always HH:MM
                    time_part = parts[-1]
                    if ":" in time_part:
                        try:
                            hour_str, minute_str = time_part.split(":")
                            hour = int(hour_str)
                            minute = int(minute_str)
                            info(f"[_sync_flupld_schedules] Extracted time: hour={hour}, minute={minute}")
                        except (ValueError, IndexError) as e:
                            warning(f"[_sync_flupld_schedules] Failed to parse time part '{time_part}': {e}")
                    # For WK, FN: second part is day (MON, TUE, etc.)
                    # For MN, HY, YR: second part is day of month (1-31)
                    if len(parts) >= 3 and frqncy in ("WK", "FN"):
                        freq_day = parts[1]
                        info(f"[_sync_flupld_schedules] Extracted weekday: {freq_day}")
                    elif len(parts) >= 3 and frqncy in ("MN", "HY", "YR"):
                        try:
                            freq_day = str(int(parts[1]))  # Day of month as string
                            info(f"[_sync_flupld_schedules] Extracted day of month: {freq_day}")
                        except ValueError as e:
                            warning(f"[_sync_flupld_schedules] Failed to parse day of month '{parts[1]}': {e}")
            else:
                info(f"[_sync_flupld_schedules] No tm_prm provided, using defaults: hour=0, minute=0")
            
            # Get start/end dates from schedule (if stored, otherwise use defaults)
            # Note: DMS_FLUPLD_SCHD doesn't have strtdt/enddt columns in the current schema
            # We'll use None for now, which means no date restrictions
            strtdt = None
            enddt = None
            
            try:
                self._queue_file_upload_request(flupldref, payload={"load_mode": "INSERT"})
                info(f"[_sync_flupld_schedules] Queued file upload request for {flupldref} (schedule {schedule_id})")
                
                # Calculate next run time
                # Convert timezone object to string if needed
                tz = self.scheduler.timezone
                if hasattr(tz, 'zone'):
                    tz_str = tz.zone
                elif isinstance(tz, str):
                    tz_str = tz
                else:
                    tz_str = str(tz)
                
                info(f"[_sync_flupld_schedules] Calculating next run for schedule {schedule_id}: frqncy={frqncy}, freq_day={freq_day}, hour={hour}, minute={minute}, timezone={tz_str}")
                
                next_dt = _calculate_next_run_time(
                    frequency_code=frqncy,
                    frequency_day=freq_day,
                    frequency_hour=hour,
                    frequency_minute=minute,
                    start_date=strtdt,
                    end_date=enddt,
                    timezone=tz_str,
                )
                
                if next_dt is None:
                    warning(f"[_sync_flupld_schedules] Could not calculate next run time for schedule {schedule_id} ({flupldref})")
                    status = "PAUSED"
                else:
                    info(f"[_sync_flupld_schedules] Calculated next run time for schedule {schedule_id}: {next_dt}")
                    status = "ACTIVE"
                
                # Convert now to naive datetime for database storage
                last_run_naive = now.replace(tzinfo=None) if now.tzinfo else now
                next_run_naive = next_dt.replace(tzinfo=None) if next_dt and next_dt.tzinfo else next_dt
                
                info(f"[_sync_flupld_schedules] Updating schedule {schedule_id}: lst_run_dt={last_run_naive}, nxt_run_dt={next_run_naive}, stts={status}")
                self._update_file_upload_schedule(schedule_id, last_run=last_run_naive, next_run=next_run_naive, status=status)
                info(f"[_sync_flupld_schedules] Successfully updated schedule {schedule_id} for {flupldref}")
            except Exception as exc:
                import traceback
                error(f"[_sync_flupld_schedules] Failed to process file upload schedule {schedule_id} ({flupldref}): {exc}\nTraceback: {traceback.format_exc()}")

    def _poll_queue(self) -> None:
        """
        Poll DMS_PRCREQ for pending requests.
        """
        debug("[_poll_queue] Starting queue poll...")
        try:
            with self._db_cursor() as cursor:
                connection = cursor.connection
                db_type = _detect_db_type(connection)
                schema = os.getenv('DMS_SCHEMA', 'TRG')
                
                debug(f"[_poll_queue] Database type: {db_type}, Schema: {schema}")
                
                # Get table reference for PostgreSQL (handles case sensitivity)
                if db_type == "POSTGRESQL":
                    schema_lower = schema.lower() if schema else 'public'
                    dms_prcreq_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCREQ')
                    # Quote table name if it contains uppercase letters (was created with quotes)
                    dms_prcreq_ref = f'"{dms_prcreq_table}"' if dms_prcreq_table != dms_prcreq_table.lower() else dms_prcreq_table
                    schema_prefix = f'{schema_lower}.' if schema else ''
                    dms_prcreq_full = f'{schema_prefix}{dms_prcreq_ref}'
                    
                    # PostgreSQL: Use LIMIT instead of FETCH FIRST
                    # Try uppercase column names first, fallback to lowercase
                    try:
                        cursor.execute(
                            f"""
                            SELECT "REQUEST_ID", "MAPREF", "REQUEST_TYPE", "PAYLOAD"
                            FROM {dms_prcreq_full}
                            WHERE "STATUS" = 'NEW'
                            ORDER BY "REQUESTED_AT"
                            LIMIT 25
                            """
                        )
                    except Exception as e:
                        # Fallback to lowercase column names if uppercase fails
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
                    debug("[_poll_queue] No pending scheduler requests")
                    return
                
                info(f"[_poll_queue] Found {len(rows)} pending requests")

                claimed_ids: List[str] = []
                requests: List[QueueRequest] = []
                for row in rows:
                    req_id, mapref, req_type, payload = row
                    info(f"[_poll_queue] Processing request: request_id={req_id}, mapref={mapref}, type={req_type}")
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
                    # Try uppercase column names first
                    try:
                        cursor.executemany(
                            f"""
                            UPDATE {dms_prcreq_full}
                            SET "STATUS" = 'CLAIMED',
                                "CLAIMED_AT" = CURRENT_TIMESTAMP,
                                "CLAIMED_BY" = %s
                            WHERE "REQUEST_ID" = %s
                            """,
                            [
                                ("PY_SCHED", request_id)
                                for request_id in claimed_ids
                            ],
                        )
                    except Exception:
                        # Fallback to lowercase
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
                info(f"[_poll_queue] Claimed {len(claimed_ids)} requests")

            for request in requests:
                info(f"[_poll_queue] Submitting request {request.request_id} ({request.mapref}) to executor")
                self.executor.submit(self._execute_request, request)
        except Exception as e:
            import traceback
            error(f"[_poll_queue] Error during queue polling: {e}\nTraceback: {traceback.format_exc()}")

    def _execute_request(self, request: QueueRequest) -> None:
        info(f"[_execute_request] Starting execution of request {request.request_id} (mapref={request.mapref}, type={request.request_type.value})")
        try:
            # Handle REPORT type requests separately
            if request.request_type.value == "REPORT":
                info(f"[_execute_request] Executing REPORT request for {request.mapref}")
                result = self._execute_report_request(request)
            elif request.request_type.value == "FILE_UPLOAD":
                info(f"[_execute_request] Executing FILE_UPLOAD request for {request.mapref}")
                result = self._execute_file_upload_request(request)
            else:
                info(f"[_execute_request] Executing job flow for {request.mapref} using execution engine")
                result = self.engine.execute(request)
                info(f"[_execute_request] Execution completed for {request.mapref}, result: {result}")
            info(f"[_execute_request] Marking request {request.request_id} as DONE")
            self._mark_request_complete(request, "DONE", result)
            info(f"[_execute_request] Successfully completed request {request.request_id}")
        except Exception as exc:
            import traceback
            error_msg = str(exc)
            error_trace = traceback.format_exc()
            error(
                f"[_execute_request] Error executing request {request.request_id} ({request.request_type.value}): {error_msg}\n"
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
                error(f"[_execute_request] Failed to mark request as failed: {mark_exc}")

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

    def _execute_file_upload_request(self, request: QueueRequest) -> Dict[str, Any]:
        """Execute a FILE_UPLOAD type request using the FileUploadExecutor."""
        # Support both FastAPI (package import) and legacy Flask (relative import) contexts
        try:
            from backend.modules.file_upload.file_upload_executor import FileUploadExecutor
        except ImportError:  # When running Flask app.py directly inside backend
            from modules.file_upload.file_upload_executor import FileUploadExecutor  # type: ignore

        payload = request.payload or {}
        flupldref = payload.get("flupldref")
        
        if not flupldref:
            # Try to extract from mapref (format: "FLUPLD:ReportData")
            if request.mapref and request.mapref.startswith("FLUPLD:"):
                flupldref = request.mapref.split(":", 1)[1]
        
        if not flupldref:
            raise ValueError("File upload reference not found in request payload or mapref")
        
        load_mode = payload.get("load_mode", "INSERT")
        username = "system"  # Scheduled executions run as system
        
        executor = FileUploadExecutor()
        result = executor.execute(
            flupldref=flupldref,
            file_path=None,  # Use file path from configuration
            load_mode=load_mode,
            username=username
        )
        
        info(f"[SchedulerService] File upload {flupldref} executed successfully: {result}")
        return result

    def _mark_request_complete(self, request: QueueRequest, status: str, payload: Dict[str, Any]) -> None:
        info(f"[_mark_request_complete] Marking request {request.request_id} as {status}")
        try:
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
                    # Try uppercase column names first, fallback to lowercase
                    try:
                        cursor.execute(
                            f"""
                            UPDATE {dms_prcreq_full}
                            SET "STATUS" = %s,
                                "RESULT_PAYLOAD" = %s,
                                "COMPLETED_AT" = CURRENT_TIMESTAMP
                            WHERE "REQUEST_ID" = %s
                            """,
                            (
                                status,
                                json.dumps(payload, default=str),
                                request.request_id,
                            ),
                        )
                    except Exception:
                        # Fallback to lowercase
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
                info(f"[_mark_request_complete] Successfully updated request {request.request_id} to status {status}")
        except Exception as e:
            import traceback
            error(f"[_mark_request_complete] Failed to mark request {request.request_id} as {status}: {e}\nTraceback: {traceback.format_exc()}")
            raise

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
        info(f"[_enqueue_scheduled_job] Trigger fired! Enqueuing scheduled job for {mapref} (jobschid={jobschid})")
        try:
            payload = {"source": "schedule", "jobschid": jobschid}
            info(f"[_enqueue_scheduled_job] Calling _queue_immediate_job with mapref={mapref}, payload={payload}")
            self._queue_immediate_job(mapref, payload)
            info(f"[_enqueue_scheduled_job] Successfully enqueued job for {mapref}")
        except Exception as e:
            import traceback
            error(f"[_enqueue_scheduled_job] Failed to enqueue scheduled job {mapref}: {e}\nTraceback: {traceback.format_exc()}")
            raise

    def _queue_immediate_job(self, mapref: str, payload: Optional[Dict[str, Any]] = None) -> None:
        info(f"[_queue_immediate_job] Starting to queue immediate job for {mapref} with payload: {payload}")
        connection = None
        try:
            connection = create_metadata_connection()
            info(f"[_queue_immediate_job] Connection created, creating JobSchedulerService...")
            service = JobSchedulerService(connection)
            request = ImmediateJobRequest(
                mapref=mapref,
                params=payload or {},
            )
            info(f"[_queue_immediate_job] Calling service.queue_immediate_job with mapref={mapref}, params={payload}")
            request_id = service.queue_immediate_job(request)
            info(f"[_queue_immediate_job] Successfully queued job {mapref} with request_id={request_id}")
        except Exception as exc:
            import traceback
            error(f"[_queue_immediate_job] Failed to enqueue job {mapref}: {exc}\nTraceback: {traceback.format_exc()}")
            raise
        finally:
            if connection:
                connection.close()
                debug(f"[_queue_immediate_job] Connection closed for {mapref}")

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

    def _queue_file_upload_request(self, flupldref: str, payload: Optional[Dict[str, Any]] = None) -> None:
        connection = None
        try:
            connection = create_metadata_connection()
            service = JobSchedulerService(connection)
            service.queue_file_upload_request(flupldref=flupldref, payload=payload)
        except Exception as exc:
            error(f"Failed to enqueue file upload {flupldref}: {exc}")
            raise
        finally:
            if connection:
                connection.close()

    def _update_file_upload_schedule(self, schedule_id: int, last_run: datetime, next_run: Optional[datetime], status: Optional[str]):
        try:
            with self._db_cursor() as cursor:
                connection = cursor.connection
                db_type = _detect_db_type(connection)
                schema = os.getenv('DMS_SCHEMA', 'TRG')
                if db_type == "POSTGRESQL":
                    schema_lower = schema.lower() if schema else 'public'
                    dms_flupld_schd_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_FLUPLD_SCHD')
                    dms_flupld_schd_ref = f'"{dms_flupld_schd_table}"' if dms_flupld_schd_table != dms_flupld_schd_table.lower() else dms_flupld_schd_table
                    schema_prefix = f'{schema_lower}.' if schema else ''
                    dms_flupld_schd_full = f'{schema_prefix}{dms_flupld_schd_ref}'
                    info(f"[_update_file_upload_schedule] Updating PostgreSQL table {dms_flupld_schd_full} for schedule {schedule_id}")
                    cursor.execute(
                        f"""
                        UPDATE {dms_flupld_schd_full}
                        SET lst_run_dt = %s,
                            nxt_run_dt = %s,
                            stts = %s
                        WHERE schdid = %s
                        """,
                        (last_run, next_run, status or "ACTIVE", schedule_id),
                    )
                    rows_updated = cursor.rowcount
                    info(f"[_update_file_upload_schedule] PostgreSQL UPDATE affected {rows_updated} row(s)")
                else:
                    schema_prefix = f'{schema}.' if schema else ''
                    info(f"[_update_file_upload_schedule] Updating Oracle table {schema_prefix}DMS_FLUPLD_SCHD for schedule {schedule_id}")
                    cursor.execute(
                        f"""
                        UPDATE {schema_prefix}DMS_FLUPLD_SCHD
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
                    rows_updated = cursor.rowcount
                    info(f"[_update_file_upload_schedule] Oracle UPDATE affected {rows_updated} row(s)")
                
                cursor.connection.commit()
                info(f"[_update_file_upload_schedule] Successfully committed update for schedule {schedule_id}")
        except Exception as exc:
            import traceback
            error(f"[_update_file_upload_schedule] Failed to update schedule {schedule_id}: {exc}\nTraceback: {traceback.format_exc()}")
            raise

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
                
                # PostgreSQL: Use %s for bind variables, handle case-sensitive column names
                try:
                    cursor.execute(
                        f"""
                        SELECT child."MAPREF", child."JOBSCHID"
                        FROM {dms_jobsch_full} child
                        JOIN {dms_jobsch_full} parent
                          ON child."DPND_JOBSCHID" = parent."JOBSCHID"
                        WHERE parent."MAPREF" = %s
                          AND parent."CURFLG" = 'Y'
                          AND child."CURFLG" = 'Y'
                          AND child."SCHFLG" = 'Y'
                        """,
                        (parent_mapref,),
                    )
                except Exception:
                    # If uppercase fails, try lowercase (columns created without quotes)
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

