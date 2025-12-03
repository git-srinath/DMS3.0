# Scheduler Service - Quick Start

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Ensure `.env` file in project root has:
```bash
DB_HOST=your_host
DB_PORT=1521
DB_SID=your_service
DB_USER=your_user
DB_PASSWORD=your_password
SCHEMA=your_schema
```

### 3. Start Scheduler

**Windows:**
```cmd
start_scheduler.bat
```

**Linux/macOS:**
```bash
chmod +x start_scheduler.sh
./start_scheduler.sh
```

**Or directly:**
```bash
cd backend
python -m modules.jobs.scheduler_service
```

---

## ✅ Verify It's Running

Check logs for:
```
INFO: Starting scheduler service
INFO: Synchronising job schedules...
```

Query database:
```sql
SELECT COUNT(*) FROM DMS_PRCREQ WHERE status = 'NEW';
```

---

## 🛑 Stop the Service

Press `Ctrl+C` in the terminal

---

## 📚 Full Documentation

See `doc/SCHEDULER_STARTUP_GUIDE.md` for:
- Production deployment options
- Windows Service setup
- Linux systemd service
- Troubleshooting
- Configuration options

---

**That's it!** The scheduler is now running and will:
- ✅ Sync schedules from DMS_JOBSCH
- ✅ Execute recurring jobs automatically
- ✅ Process immediate job requests
- ✅ Handle parent→child job dependencies

