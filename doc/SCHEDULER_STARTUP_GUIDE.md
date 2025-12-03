# Scheduler Service Startup Guide

## Overview

The scheduler service is a standalone Python process that runs independently from your Flask web application. It performs three main functions:

1. **Schedule Synchronization**: Reads job schedules from `DMS_JOBSCH` and syncs them to APScheduler
2. **Queue Polling**: Polls `DMS_PRCREQ` for immediate/history/stop requests and executes them
3. **Job Execution**: Executes ETL job flows and logs results to `DMS_PRCLOG`/`DMS_JOBLOG`/`DMS_JOBERR`

---

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- All dependencies installed from `requirements.txt`:
  ```bash
  pip install -r backend/requirements.txt
  ```

### 2. Database Setup
- Oracle database connection configured
- `DMS_PRCREQ` table created (run `doc/database_migration_add_scheduler_queue.sql`)
- Environment variables configured (see below)

### 3. Environment Variables

Create a `.env` file in the project root (or use existing one) with:

```bash
# Oracle Database Connection
DB_HOST=your_database_host
DB_PORT=1521
DB_SID=your_service_name
DB_USER=your_username
DB_PASSWORD=your_password

# Schema Configuration
SCHEMA=your_schema_name  # Schema containing DMS_JOBSCH, DMS_PRCREQ, etc.

# Optional: Scheduler Configuration (defaults shown)
SCHEDULER_POLL_INTERVAL=15      # Seconds between queue polls
SCHEDULER_REFRESH_INTERVAL=60   # Seconds between schedule syncs
SCHEDULER_MAX_WORKERS=4         # Concurrent job executions
SCHEDULER_TIMEZONE=UTC          # Timezone for schedules
```

---

## Starting the Scheduler Service

### Method 1: Direct Python Execution (Development/Testing)

From the project root directory:

```bash
# Windows
cd backend
python -m modules.jobs.scheduler_service

# Linux/macOS
cd backend
python3 -m modules.jobs.scheduler_service
```

**Note**: The service will run in the foreground and log to console. Press `Ctrl+C` to stop.

### Method 2: Using the Startup Script (Recommended)

We provide convenience scripts for easier startup:

**Windows** (`start_scheduler.bat`):
```batch
@echo off
cd backend
python -m modules.jobs.scheduler_service
pause
```

**Linux/macOS** (`start_scheduler.sh`):
```bash
#!/bin/bash
cd backend
python3 -m modules.jobs.scheduler_service
```

Make the script executable:
```bash
chmod +x start_scheduler.sh
./start_scheduler.sh
```

### Method 3: Background Process (Linux/macOS)

Run in background with output redirected to log file:

```bash
cd backend
nohup python3 -m modules.jobs.scheduler_service > ../logs/scheduler.log 2>&1 &
echo $! > scheduler.pid  # Save process ID
```

To stop:
```bash
kill $(cat scheduler.pid)
```

### Method 4: Windows Service (Production)

For production Windows environments, you can run as a Windows Service using:

**Option A: NSSM (Non-Sucking Service Manager)**
1. Download NSSM from https://nssm.cc/download
2. Install the service:
   ```cmd
   nssm install DWTOOL_Scheduler "C:\Python\python.exe" "-m" "modules.jobs.scheduler_service"
   nssm set DWTOOL_Scheduler AppDirectory "D:\CursorTesting\DWTOOL\backend"
   nssm set DWTOOL_Scheduler AppEnvironmentExtra "DB_HOST=your_host;DB_PORT=1521;..."
   nssm start DWTOOL_Scheduler
   ```

**Option B: Python Windows Service Wrapper**
- Use `pywin32` library to create a Windows service
- See `scripts/scheduler_windows_service.py` (if created)

### Method 5: Linux Systemd Service (Production)

Create `/etc/systemd/system/dwtool-scheduler.service`:

```ini
[Unit]
Description=DWTOOL Scheduler Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/DWTOOL/backend
Environment="PATH=/usr/bin:/usr/local/bin"
EnvironmentFile=/path/to/DWTOOL/.env
ExecStart=/usr/bin/python3 -m modules.jobs.scheduler_service
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dwtool-scheduler
sudo systemctl start dwtool-scheduler
sudo systemctl status dwtool-scheduler
```

---

## Verifying the Service is Running

### Check Logs

The scheduler logs to your application's logger. Check log output for:

```
INFO: Starting scheduler service
INFO: Synchronising job schedules...
INFO: Polling queue for pending requests...
```

### Check Database

Query `DMS_PRCREQ` to see if requests are being processed:

```sql
SELECT request_id, mapref, request_type, status, 
       requested_at, claimed_at, completed_at
FROM DMS_PRCREQ
ORDER BY requested_at DESC
FETCH FIRST 10 ROWS ONLY;
```

### Check Active Schedules

Query `DMS_JOBSCH` to see active schedules:

```sql
SELECT mapref, frqcd, frqdd, frqhh, frqmi, 
       strtdt, enddt, schflg
FROM DMS_JOBSCH
WHERE curflg = 'Y' AND schflg = 'Y';
```

---

## Configuration Options

You can customize scheduler behavior by modifying `SchedulerConfig` in `scheduler_models.py` or passing a custom config:

```python
from modules.jobs.scheduler_models import SchedulerConfig
from modules.jobs.scheduler_service import SchedulerService

config = SchedulerConfig(
    poll_interval_seconds=10,      # Poll queue every 10 seconds
    schedule_refresh_seconds=30,   # Sync schedules every 30 seconds
    max_workers=8,                  # Allow 8 concurrent jobs
    timezone="America/New_York"     # Use Eastern timezone
)

service = SchedulerService(config=config)
service.start()
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'modules'"

**Solution**: Run from the `backend` directory or ensure Python path includes project root:
```bash
export PYTHONPATH=/path/to/DWTOOL:$PYTHONPATH
python -m modules.jobs.scheduler_service
```

### Issue: "Database connection failed"

**Solution**: 
1. Verify `.env` file exists and has correct database credentials
2. Test connection manually:
   ```python
   from database.dbconnect import create_oracle_connection
   conn = create_oracle_connection()
   print("Connected!")
   conn.close()
   ```

### Issue: "No pending requests being processed"

**Solution**:
1. Verify `DMS_PRCREQ` table exists and has `status='NEW'` rows
2. Check scheduler logs for errors
3. Verify database connection is working
4. Check that `DMS_JOBSCH` has active schedules (`curflg='Y'`)

### Issue: "Scheduler stops unexpectedly"

**Solution**:
1. Check logs for exceptions
2. Verify database connection stability
3. Check system resources (memory, CPU)
4. Consider running as a service with auto-restart (systemd/systemd)

### Issue: "Jobs not executing on schedule"

**Solution**:
1. Verify `DMS_JOBSCH.schflg = 'Y'` for the schedule
2. Check that `strtdt` is not in the future
3. Verify `enddt` is not in the past (if set)
4. Check scheduler logs for sync errors
5. Manually trigger sync by restarting scheduler

---

## Stopping the Service

### Graceful Shutdown

Press `Ctrl+C` in the terminal where it's running. The service will:
1. Stop accepting new jobs
2. Wait for current jobs to complete
3. Shutdown cleanly

### Force Stop

If graceful shutdown doesn't work:

**Linux/macOS**:
```bash
pkill -f "scheduler_service"
# Or if you saved PID:
kill $(cat scheduler.pid)
```

**Windows**:
```cmd
taskkill /F /IM python.exe /FI "WINDOWTITLE eq scheduler*"
```

---

## Monitoring

### Key Metrics to Monitor

1. **Queue Depth**: Number of `status='NEW'` requests in `DMS_PRCREQ`
2. **Processing Rate**: Requests completed per minute
3. **Error Rate**: Failed requests vs successful
4. **Active Jobs**: Jobs currently executing (check `DMS_PRCLOG` with `status='IP'`)
5. **Schedule Sync**: Frequency of schedule synchronization

### Sample Monitoring Queries

```sql
-- Queue depth
SELECT COUNT(*) as pending_requests
FROM DMS_PRCREQ
WHERE status = 'NEW';

-- Recent activity
SELECT request_type, status, COUNT(*) as count
FROM DMS_PRCREQ
WHERE requested_at > SYSDATE - 1/24  -- Last hour
GROUP BY request_type, status;

-- Active jobs
SELECT mapref, strtdt, status
FROM DMS_PRCLOG
WHERE status = 'IP'
ORDER BY strtdt;
```

---

## Best Practices

1. **Run as Service**: Use systemd (Linux) or Windows Service for production
2. **Monitor Logs**: Set up log rotation and monitoring
3. **Resource Limits**: Adjust `max_workers` based on system capacity
4. **Timezone**: Set timezone matching your business hours
5. **Backup**: Ensure database backups include `DMS_PRCREQ`, `DMS_PRCLOG`, etc.
6. **High Availability**: Consider running multiple scheduler instances with proper coordination (future enhancement)

---

## Next Steps

Once the scheduler is running:

1. **Test Immediate Execution**: Use Flask API to queue an immediate job
2. **Create Schedule**: Use Flask API to create a recurring schedule
3. **Monitor Execution**: Check `DMS_PRCLOG` and `DMS_JOBLOG` for results
4. **Set Up Monitoring**: Configure alerts for failed jobs

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0

