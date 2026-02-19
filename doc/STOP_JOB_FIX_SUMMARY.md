# Stop Job Functionality Fix

## Issue
The "stop job" button in the logs & status screen was not updating the job status in DMS_PRCLOG, preventing re-execution of stalled jobs.

## Root Cause
When a stop request was made:
1. A STOP request was queued in DMS_PRCREQ
2. The scheduler service processed it and called `_handle_stop_request` which only acknowledged the request
3. The job status in DMS_PRCLOG was not updated to 'STOPPED' for stalled jobs
4. This left the job with status 'IP' (In Progress) or 'CLAIMED', blocking re-execution

## Solution
Updated the stop job functionality to directly update DMS_PRCLOG status to 'FL' (failed) when a stop is requested. Note: DMS_PRCLOG.status column only accepts 2 characters, so 'FL' is used instead of 'STOPPED':

### 1. Enhanced `_handle_stop_request` in `execution_engine.py`
- Now directly updates DMS_PRCLOG status to 'FL' (failed) for matching jobs
- Matches jobs by mapref and start timestamp (within 1 hour window)
- Handles both PostgreSQL and Oracle databases
- Updates enddt, recupdt, and msg fields appropriately

### 2. Enhanced `stop_running_job` endpoint in `fastapi_jobs.py`
- Immediately updates DMS_PRCLOG status to 'FL' (failed) when stop is requested
- This ensures stalled jobs are marked as stopped even if they're not actively processing
- Still queues the stop request for active jobs to handle gracefully

## Changes Made

### `backend/modules/jobs/execution_engine.py`
- Lines 711-828: Enhanced `_handle_stop_request` method to:
  - Extract start_timestamp and force flag from payload
  - Update DMS_PRCLOG status to 'FL' (failed) for matching jobs
  - Handle both PostgreSQL and Oracle database syntax
  - Log the number of records updated

### `backend/modules/jobs/fastapi_jobs.py`
- Lines 1126-1175: Enhanced `stop_running_job` endpoint to:
  - Directly update DMS_PRCLOG status to 'FL' (failed) immediately
  - Match jobs by mapref and start timestamp
  - Handle both PostgreSQL and Oracle databases
  - Log updates for debugging

## Benefits
1. **Immediate Status Update**: Job status is updated immediately when stop is requested
2. **Stalled Job Handling**: Stalled jobs are properly marked as STOPPED
3. **Re-execution Enabled**: Jobs can be re-executed immediately after being stopped
4. **Dual Protection**: Both immediate update and queued request ensure job stops properly

## Testing
After this fix:
1. Stop button should immediately update job status to 'FL' (failed)
2. Stalled jobs should be properly marked as failed
3. Jobs should be re-executable immediately after being stopped
4. Both actively running and stalled jobs should be handled correctly

