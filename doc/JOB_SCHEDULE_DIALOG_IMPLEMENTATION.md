# Job Schedule Dialog Implementation

## Overview
This document describes the implementation of a schedule dialog for jobs, similar to the reports page, that allows users to configure job schedules and view last run and next run information.

## Database Changes

### Migration Script
**File**: `doc/database_migration_add_job_schedule_run_dates.sql`

**Changes**:
- Adds `LST_RUN_DT TIMESTAMP(6)` column to `DMS_JOBSCH` table
- Adds `NXT_RUN_DT TIMESTAMP(6)` column to `DMS_JOBSCH` table
- Supports both Oracle and PostgreSQL databases

**To Apply**:
```bash
# Oracle
sqlplus username/password@database
SQL> @doc/database_migration_add_job_schedule_run_dates.sql

# PostgreSQL
psql -U username -d database -f doc/database_migration_add_job_schedule_run_dates.sql
```

## Backend Changes

### 1. Next Run Time Calculation
**File**: `backend/modules/jobs/pkgdwprc_python.py`

- Added `_calculate_next_run_time()` function that uses APScheduler triggers to calculate the next execution time
- Function is called when schedules are created/updated to populate `NXT_RUN_DT`

### 2. Schedule Creation/Update
**File**: `backend/modules/jobs/pkgdwprc_python.py`

- Updated `create_job_schedule()` to:
  - Calculate next run time using `_calculate_next_run_time()`
  - Store `NXT_RUN_DT` in the database when creating/updating schedules
  - Updated INSERT statements to include `nxt_run_dt` column

### 3. Last Run Time Update
**File**: `backend/modules/jobs/execution_engine.py`

- Updated `_finalize_success()` to:
  - Update `LST_RUN_DT` with current timestamp when job completes successfully
  - Recalculate and update `NXT_RUN_DT` for the next scheduled run
  - Handles both PostgreSQL and Oracle databases

### 4. API Endpoints Updated
**Files**: 
- `backend/modules/jobs/jobs.py`
- `backend/modules/jobs/fastapi_jobs.py`

**Endpoints Updated**:
- `GET /job/get_all_jobs` - Now returns `last run` and `next run` fields
- `GET /job/get_job_schedule_details/<job_flow_id>` - Now returns `LST_RUN_DT` and `NXT_RUN_DT`

### 5. Schedule Fetching
**File**: `backend/modules/jobs/pkgdwprc_python.py`

- Updated `_fetch_active_schedule()` to include `LST_RUN_DT` and `NXT_RUN_DT` in the returned dictionary

## Frontend Changes (To Be Implemented)

### 1. Schedule Dialog Component
**File**: `frontend/src/app/jobs/components/ScheduleDialog.js` (to be created)

- Similar to reports page schedule dialog
- Fields:
  - Frequency selector (DL, WK, FN, MN, HY, YR, ID)
  - Day selector (for WK, FN, MN, HY, YR)
  - Time selector (Hour:Minute)
  - Start Date picker
  - End Date picker (optional)
  - Read-only fields:
    - Last Run At
    - Next Run At

### 2. Schedule Button
**File**: `frontend/src/app/jobs/page.js`

- Add "Schedule" button that opens the schedule dialog
- Button should be visible in the jobs table row

### 3. Display Last/Next Run
**File**: `frontend/src/app/jobs/page.js`

- Update jobs table to display last run and next run columns
- Format dates using `formatDateTime()` helper (similar to reports page)

## Implementation Status

✅ **Completed**:
1. Database migration script created
2. Backend next run time calculation
3. Backend schedule creation/update with next run time
4. Backend last run time update on job completion
5. API endpoints updated to return last/next run information

⏳ **Pending**:
1. Frontend schedule dialog component
2. Frontend schedule button
3. Frontend display of last/next run information

## Testing Checklist

- [ ] Run database migration script
- [ ] Verify columns were added to DMS_JOBSCH
- [ ] Create a new schedule and verify NXT_RUN_DT is populated
- [ ] Execute a scheduled job and verify LST_RUN_DT is updated
- [ ] Verify NXT_RUN_DT is recalculated after job execution
- [ ] Test with different frequency codes (DL, WK, FN, MN, HY, YR, ID)
- [ ] Verify API endpoints return last/next run information
- [ ] Test schedule dialog opens and saves correctly
- [ ] Verify last/next run display in jobs table

## Notes

- The next run time calculation uses APScheduler's trigger system, which ensures accuracy
- Last run time is updated automatically when jobs complete successfully
- Next run time is recalculated after each job execution to account for schedule changes
- Both PostgreSQL and Oracle databases are supported

