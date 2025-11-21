# Scheduler Service Troubleshooting Guide

## Issue: Job Queued But Not Executing / No Logs Appearing

### Symptoms
- ✅ Job queuing succeeds (you see success message)
- ❌ No entries in status/logs screen
- ❌ Job never executes

### Root Cause
**The scheduler service is not running.** The scheduler service is a separate background process that must be started independently from your Flask application.

---

## Quick Diagnosis

### Step 1: Check Queue Status

Call the diagnostic endpoint:
```
GET /api/jobs/check_scheduler_queue
```

This will show you:
- Queue status (NEW, CLAIMED, DONE, FAILED)
- How many jobs are waiting
- Recent process logs
- Whether jobs are stuck

**Expected Output:**
```json
{
  "queue_summary": {
    "total_requests": 1,
    "status_counts": {
      "NEW": 1  // ← This means scheduler hasn't picked it up yet
    },
    "stuck_jobs_count": 0,
    "recent_process_logs": 0
  }
}
```

**If you see `status: "NEW"`** → Scheduler service is NOT running or not processing

**If you see `status: "CLAIMED"`** → Scheduler picked it up but execution may be in progress or failed

**If you see `status: "DONE"`** → Job completed successfully

---

### Step 2: Verify Scheduler Service is Running

#### Windows
```cmd
tasklist | findstr python
```
Look for a Python process running `scheduler_service.py`

#### Linux/macOS
```bash
ps aux | grep scheduler_service
```

#### Check Logs
Look for scheduler service logs in `dwtool.log`:
```bash
# Should see messages like:
# "Starting scheduler service"
# "Synchronising job schedules..."
# "Polling queue for pending requests..."
```

---

## Solution: Start the Scheduler Service

### Method 1: Quick Start (Development/Testing)

**Windows:**
```cmd
start_scheduler.bat
```

**Linux/macOS:**
```bash
./start_scheduler.sh
```

**Or directly:**
```bash
cd backend
python -m modules.jobs.scheduler_service
```

### Method 2: Check if Already Running

The scheduler service runs continuously. If it's already running, you should see:
- Log messages every 15 seconds (queue polling)
- Log messages every 60 seconds (schedule sync)

---

## Understanding the Flow

```
1. User clicks "Run Job" in UI
   ↓
2. Flask API queues request → DWPRCREQ (status='NEW')
   ↓
3. Scheduler service polls DWPRCREQ every 15 seconds
   ↓
4. Scheduler claims request → Updates status to 'CLAIMED'
   ↓
5. Execution engine runs job → Creates DWPRCLOG entry
   ↓
6. Job completes → Updates DWPRCLOG status to 'PC' or 'FL'
   ↓
7. Status screen queries DWPRCLOG → Shows results
```

**If step 3 doesn't happen**, the scheduler service isn't running!

---

## Common Issues

### Issue 1: Scheduler Service Not Started

**Symptom:** Jobs stuck in `NEW` status

**Solution:** Start the scheduler service (see above)

---

### Issue 2: Scheduler Service Crashed

**Symptom:** Jobs were processing but stopped

**Check:**
```bash
# Check scheduler logs for errors
tail -f dwtool.log | grep -i error
```

**Solution:** Restart scheduler service

---

### Issue 3: Database Connection Issues

**Symptom:** Scheduler starts but can't connect to database

**Check:**
- `.env` file has correct database credentials
- Database is accessible
- Network connectivity

**Solution:** Fix database connection and restart scheduler

---

### Issue 4: Jobs Failing Silently

**Symptom:** Jobs show `CLAIMED` but never complete

**Check:**
```sql
-- Check for errors in DWPRCLOG
SELECT mapref, status, msg, strtdt, enddt
FROM DWPRCLOG
WHERE status = 'FL'
ORDER BY strtdt DESC;
```

**Solution:** Check error messages in `DWPRCLOG.msg` or `DWJOBERR` table

---

## Monitoring Commands

### Check Queue Status
```sql
SELECT 
    request_id,
    mapref,
    request_type,
    status,
    requested_at,
    claimed_at,
    completed_at
FROM DWPRCREQ
ORDER BY requested_at DESC
FETCH FIRST 10 ROWS ONLY;
```

### Check Recent Process Logs
```sql
SELECT 
    mapref,
    status,
    strtdt,
    enddt,
    msg
FROM DWPRCLOG
WHERE reccrdt >= SYSDATE - 1/24
ORDER BY reccrdt DESC;
```

### Check for Stuck Jobs
```sql
SELECT *
FROM DWPRCREQ
WHERE status = 'NEW'
AND requested_at < SYSTIMESTAMP - INTERVAL '5' MINUTE;
```

---

## Verification Checklist

- [ ] Scheduler service process is running
- [ ] Scheduler logs show "Starting scheduler service"
- [ ] Scheduler logs show periodic "Polling queue" messages
- [ ] Queue status shows jobs moving from NEW → CLAIMED → DONE
- [ ] DWPRCLOG table has entries for executed jobs
- [ ] Status screen shows job results

---

## Next Steps

1. **Start the scheduler service** using one of the methods above
2. **Wait 15-30 seconds** for it to poll the queue
3. **Check the diagnostic endpoint** again to see if status changed
4. **Check the status screen** - logs should appear

---

**Still having issues?** Check:
- Scheduler service logs (`dwtool.log`)
- Database connection
- Queue table (`DWPRCREQ`) for stuck jobs
- Process log table (`DWPRCLOG`) for error messages

