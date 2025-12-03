## Scheduler Service Design (PKGDWPRC Python Replacement)

### 1. Purpose
- Replace Oracle `PKGDWPRC` package with a portable Python scheduler/executor.
- Support ETL job flows (generated Python code) and upcoming report-mapping workflows.
- Preserve existing logging/checkpoint semantics so UI dashboards continue to work.

### 2. Top-Level Requirements
- **Database agnostic**: no reliance on `DBMS_SCHEDULER` or other Oracle-only APIs.
- **Background service**: long-running Python process (outside Flask) that can continue running jobs even when the API layer restarts.
- **Shared metadata**: continue to use `DMS_JOBFLW`, `DMS_JOBSCH`, `DMS_PRCLOG`, `DMS_JOBLOG`, `DMS_JOBERR`, etc., so no UI or reporting rewrites are needed.
- **Extensibility**: design job descriptors so new “report mapping” jobs can plug in without touching the scheduler core.
- **Observability**: emit the same status codes (`IP`, `PC`, `FL`, `ST`) and log records used by checkpoint/resume logic today.

### 3. Architecture Overview
| Component | Responsibility |
|-----------|----------------|
| **Scheduler Service** (new) | Runs APScheduler + worker pool; wakes up on schedule metadata or queue entries, triggers executions. |
| **Execution Engine** | Reads `DMS_JOBFLW.DWLOGIC`, `exec()` the stored Python code, calls `execute_job()` with params, and persists log/status rows. |
| **Job Queue Table (`DMS_PRCREQ`)** *(new)* | Lightweight table for “immediate” or ad-hoc run requests (regular or history). Scheduler polls it to trigger work outside Flask. |
| **Flask API / UI** | Continues to handle user input (frequency, dates, dependencies, enable/disable) but now calls Python functions instead of PL/SQL blocks. |
| **Report Runner** *(future)* | Implements `execute_report_job(payload)` and reuses the same scheduler/executor pipeline. |

```
Frontend ➜ Flask API ➜ metadata tables / DMS_PRCREQ ➜ Scheduler Service ➜ Execution Engine ➜ DMS_JOBLOG / DMS_PRCLOG / DMS_JOBERR
```

### 4. Scheduler Service Details
1. **Runtime Container**
   - Standalone Python process (can be launched via `python -m modules.jobs.scheduler_service`).
   - Uses APScheduler with a persistent job store (SQLAlchemy + same database) so schedules survive restarts.
   - Exposes health metrics/logging via existing logger.

2. **Job Types**
   - `etl_flow`: executes generated code stored in `DMS_JOBFLW.DWLOGIC`.
   - `etl_history`: loops dates, optionally truncates target, invokes `etl_flow` per slice.
   - `report`: placeholder for upcoming report mappings (exec SQL/report generator).

3. **Triggers**
   - **Scheduled**: Derived from `DMS_JOBSCH` frequency columns. APScheduler trigger mapping mirrors `PKGDWPRC.GET_REPEAT_INTERVAL` logic:
     - `YR`: `CronTrigger(year='*', day=p_frqdd, hour=p_frqhh, minute=p_frqmi)`
     - `HY`: same Cron with `month='1,7'`
     - `MN`: Cron with `day=p_frqdd`
     - `FN`/`WK`: Cron with `day_of_week=p_frqdd`
     - `DL`: Cron daily
     - `ID`: Interval trigger (hours/minutes) depending on populated fields.
   - **Immediate / Queue**: Poll `DMS_PRCREQ` (status `NEW`). When found, enqueue a one-off job run with supplied parameters, mark request as `RUNNING/COMPLETE/FAILED`.

4. **Dependencies**
   - Store parent-child links in `DMS_JOBSCH.DPND_JOBSCHID`.
   - Scheduler listens for completion events: when parent job finishes (status `PC`), it enqueues dependent job(s).
   - For cascading chains, maintain an in-memory DAG/adjacency list refreshed periodically from the DB.

5. **Concurrency / Workers**
   - ThreadPoolExecutor (size configurable) for executing jobs concurrently.
   - Enforce per-mapref mutex if `DMS_PRCLOG` shows a job already `IP`, reproducing `check_job_already_running`.

6. **Checkpoint Compatibility**
   - `process_job_flow()`:
     1. Insert row into `DMS_PRCLOG` (status `IP`, params captured, session ID = new UUID).
     2. `exec()` job code to obtain callable(s); run inside `try/except`.
     3. On success, update `DMS_PRCLOG` (status `PC`, end timestamp), insert/refresh `DMS_JOBLOG` row using the row counts returned by the job code.
     4. On failure, update `DMS_PRCLOG` (status `FL`, error message) and insert `DMS_JOBERR`.
   - `create_job_log()` and `log_job_error()` Python equivalents will follow the PL/SQL package structure so checkpoint routines remain unchanged.

7. **History Runs**
   - `process_historical_data(mapref, start_date, end_date, truncate_flag)`:
     - Optionally truncate target table (still done via connection + `TRUNCATE` statement).
     - Iterate date range, calling `process_job_flow` with date parameter for each day (commit between iterations).
     - Each iteration logs to `DMS_PRCLOG/DMS_JOBLOG`.

8. **Enable/Disable**
   - Instead of toggling DBMS scheduler jobs, mark `DMS_JOBSCH.SCHFLG` and add/remove APScheduler jobs.
   - When API requests enable/disable, scheduler module updates metadata and signals the service (via control table or direct RPC) to refresh schedules.

9. **Stop Running Job**
   - Mark request in `DMS_PRCREQ` with action `STOP`.
   - Scheduler checks running workers; if job is `IP`, signal cancellation (set threading Event) and update `DMS_PRCLOG` status to `ST`. For long-running ETL code, we wrap `execute_job` to periodically check for cancel signals.

### 5. Data Model Additions / Changes
| Table | Change | Notes |
|-------|--------|-------|
| `DMS_PRCREQ` *(new)* | `request_id`, `mapref`, `request_type` (`IMMEDIATE`, `HISTORY`, `REPORT`), payload JSON, `status`, timestamps | Acts as durable queue between API and scheduler service. |
| `DMS_PRCLOG` | Add columns for `service_node`, `cancel_flag` (optional) | Helps in multi-node deployments. |
| `DMS_JOBSCH` | No schema change required; Python validates same business rules already enforced in PL/SQL. |

If schema changes are undesirable, `DMS_PRCREQ` can be replaced with an existing table (e.g., extend `DMS_PRCLOG`) but dedicated queue table keeps semantics clean.

### 6. Module Layout
```
backend/modules/jobs/
├── scheduler_service.py      # entry point; starts scheduler loop
├── scheduler_store.py        # queries DMS_JOBSCH/DMS_PRCREQ, maps to APScheduler jobs
├── execution_engine.py       # process_job_flow, process_historical_data, logging helpers
├── job_types/
│   ├── etl_flow.py
│   ├── etl_history.py
│   └── report.py             # placeholder for upcoming report module
└── utils/
    ├── frequency.py          # translates FRQCD/DD/HH/MI to triggers
    └── concurrency.py        # job mutex, cancellation tracking
```

### 7. API Layer Updates (Flask)
- Replace PL/SQL anonymous-block calls with functions in `pkgdwprc_python`.
- Endpoints simply validate inputs and insert/modify records via SQLAlchemy/cursor helpers (same DB). No scheduler logic remains in Flask.
- For immediate runs: endpoint inserts a row in `DMS_PRCREQ` (type `IMMEDIATE`) and returns request ID; scheduler picks it up asynchronously.

### 8. Report Module Integration
- Report mappings will store SQL/query + output spec in their own tables.
- Scheduler treats them as `report` jobs: loads mapping metadata, executes query via configured connection, writes output (file/table), and logs status using the same `DMS_PRCLOG/DMS_JOBLOG` pipeline.
- Because the scheduler service is type-agnostic, introducing report jobs is mostly about implementing `job_types/report.py`.

### 9. Operational Notes
- **Deployment**: run scheduler service under supervisord/systemd/Windows service. Provide CLI args for DB connection profile, poll interval, worker count.
- **Monitoring**: integrate with existing `modules/logger`, provide heartbeat logs (“Scheduler alive”, “job queued/executing/completed”).
- **Scaling**: start with single instance; later we can allow multiple scheduler nodes by leasing queue rows (status `CLAIMED` with node identifier) to avoid double execution.

### 10. Next Steps
1. Implement `pkgdwprc_python` module (validations, metadata updates, queue inserts).
2. Build `execution_engine.py` with logging/error parity.
3. Create scheduler service skeleton + APScheduler wiring.
4. Update Flask endpoints to call the new module.
5. Write migration notes for DB additions (`DMS_PRCREQ`, optional columns).
6. Add tests / dry-run script to execute a sample job (unit test hooking into SQLite).

Once this foundation is in place, both ETL jobs and future report schedules will rely on the same background service, fulfilling the requirement for a comprehensive, database-independent scheduler.

