# DMS Tool - Installation Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Pre-Installation Checklist](#pre-installation-checklist)
4. [Database Setup](#database-setup)
5. [Backend Installation](#backend-installation)
6. [Frontend Installation](#frontend-installation)
7. [Configuration](#configuration)
8. [Service Setup](#service-setup)
9. [License Configuration](#license-configuration)
10. [Verification & Testing](#verification--testing)
11. [Troubleshooting](#troubleshooting)
12. [Upgrading](#upgrading)

---

## Introduction

This guide provides detailed step-by-step instructions for installing and configuring the DMS Tool application. The application consists of:

- **Backend**: FastAPI-based Python application (runs on port 8000)
- **Frontend**: Next.js React application (runs on port 3000)
- **Scheduler Service**: Background job scheduler (runs as separate process)
- **Database**: Oracle or PostgreSQL database for metadata and data storage

---

## System Requirements

### Server Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk Space**: 10 GB free space
- **OS**: Windows Server 2016+, Linux (Ubuntu 18.04+, RHEL 7+, CentOS 7+)

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk Space**: 50+ GB free space
- **OS**: Windows Server 2019+, Linux (Ubuntu 20.04+, RHEL 8+)

### Software Requirements

#### Required Software
- **Python**: 3.8 or higher (3.9+ recommended)
- **Node.js**: 18.x or higher (LTS version recommended)
- **npm**: 9.x or higher (comes with Node.js)
- **Database Client**: Oracle Instant Client or PostgreSQL client libraries
- **Git**: For cloning the repository

#### Optional Software
- **Conda/Anaconda**: For Python environment management
- **PM2**: For process management (frontend)
- **Gunicorn**: For production backend deployment
- **Nginx**: Reverse proxy (optional)

### Database Requirements

#### Oracle Database
- **Version**: Oracle 11g R2 or higher (12c+ recommended)
- **Required Schemas**: 
  - DMS Schema (metadata) - e.g., DWT
  - CDR Schema (data) - e.g., CDR
- **Required Permissions**: See Database Setup section

#### PostgreSQL Database
- **Version**: PostgreSQL 11 or higher (13+ recommended)
- **Required Schemas**: 
  - DMS Schema (metadata) - typically 'public'
  - CDR Schema (data) - e.g., 'cdr'
- **Required Extensions**: Standard extensions

### Network Requirements
- **Ports to Open**:
  - 3000: Frontend web application
  - 8000: Backend API (or 5000 for legacy Flask)
  - Database ports (1521 for Oracle, 5432 for PostgreSQL)
- **Firewall**: Configure to allow connections between components

---

## Pre-Installation Checklist

Before starting installation, ensure you have:

- [ ] Server access (SSH for Linux, RDP for Windows)
- [ ] Database server access and credentials
- [ ] Required database schemas created (or permissions to create)
- [ ] Python 3.8+ installed and accessible
- [ ] Node.js 18+ installed and accessible
- [ ] Git installed for cloning repository
- [ ] License key (if required)
- [ ] Application repository access (Git URL or archive)
- [ ] Network connectivity verified between components

---

## Database Setup

### Oracle Database Setup

#### Step 1: Create Schemas

Connect to Oracle database as SYSDBA or user with CREATE USER privileges:

```sql
-- Create DMS schema user (metadata)
CREATE USER DWT IDENTIFIED BY "your_password_here"
DEFAULT TABLESPACE USERS
TEMPORARY TABLESPACE TEMP;

-- Grant privileges
GRANT CONNECT, RESOURCE TO DWT;
GRANT UNLIMITED TABLESPACE TO DWT;
GRANT CREATE SESSION TO DWT;
GRANT CREATE TABLE TO DWT;
GRANT CREATE SEQUENCE TO DWT;
GRANT CREATE VIEW TO DWT;

-- Create CDR schema user (data)
CREATE USER CDR IDENTIFIED BY "your_password_here"
DEFAULT TABLESPACE USERS
TEMPORARY TABLESPACE TEMP;

GRANT CONNECT, RESOURCE TO CDR;
GRANT UNLIMITED TABLESPACE TO CDR;
GRANT CREATE SESSION TO CDR;
GRANT CREATE TABLE TO CDR;
GRANT CREATE SEQUENCE TO CDR;

-- Grant cross-schema permissions (if needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON DWT.dwmapr TO CDR;
-- (Add other grants as needed)
```

#### Step 2: Run Database Migration Scripts

Run all migration scripts in order:

```bash
cd /path/to/application/doc
sqlplus DWT/password@database < database_migration_add_rwhkey.sql
sqlplus DWT/password@database < database_migration_manage_sql_connection.sql
sqlplus DWT/password@database < database_migration_add_scheduler_queue.sql
sqlplus DWT/password@database < database_migration_file_upload_module.sql
# Add other migration scripts as needed
```

#### Step 3: Create Required Tables

If tables don't exist, create them using DDL scripts:
- `tables_ddl_oracle.md` contains table creation scripts
- Run scripts in DWT schema

#### Step 4: Create Sequences

```sql
-- Connect as DWT user
CONNECT DWT/password@database

-- Create sequences (if not auto-created)
CREATE SEQUENCE DWMAPRSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPRDTLSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPRSQLSEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DWMAPERRSEQ START WITH 1 INCREMENT BY 1;
-- Add other sequences as needed
```

#### Step 5: Verify Setup

```sql
-- Verify tables exist
SELECT table_name FROM user_tables WHERE table_name LIKE 'DMS_%';

-- Verify sequences exist
SELECT sequence_name FROM user_sequences WHERE sequence_name LIKE 'DWMAPR%';

-- Verify schema access
SELECT USER FROM dual;
```

### PostgreSQL Database Setup

#### Step 1: Create Database and Schemas

```sql
-- Connect as postgres user
psql -U postgres

-- Create database
CREATE DATABASE dms_tool;

-- Connect to database
\c dms_tool

-- Create schemas
CREATE SCHEMA IF NOT EXISTS dms_schema;
CREATE SCHEMA IF NOT EXISTS cdr_schema;

-- Create user
CREATE USER dms_user WITH PASSWORD 'your_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dms_tool TO dms_user;
GRANT ALL ON SCHEMA dms_schema TO dms_user;
GRANT ALL ON SCHEMA cdr_schema TO dms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA dms_schema GRANT ALL ON TABLES TO dms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA cdr_schema GRANT ALL ON TABLES TO dms_user;
```

#### Step 2: Run Database Migration Scripts

```bash
cd /path/to/application/doc
psql -U dms_user -d dms_tool -f database_migration_add_rwhkey.sql
psql -U dms_user -d dms_tool -f database_migration_manage_sql_connection.sql
# Add other migration scripts (convert Oracle syntax if needed)
```

#### Step 3: Create Required Tables

- Review `tables_ddl_sqlite.md` for table structure reference
- Adapt for PostgreSQL syntax
- Create tables in dms_schema

---

## Backend Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd DMSTOOL

# Or extract from archive
unzip dms-tool-v4.0.0.zip
cd DMSTOOL
```

### Step 2: Setup Python Environment

#### Option A: Using Conda (Recommended)

```bash
# Create conda environment
conda create -n dms python=3.9
conda activate dms

# Install packages
cd backend
pip install -r requirements.txt
```

#### Option B: Using Virtualenv

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install packages
cd backend
pip install -r requirements.txt
```

### Step 3: Install Database Drivers

#### Oracle Database

```bash
# Install Oracle client driver
pip install oracledb

# Ensure Oracle Instant Client is installed on system
# Download from Oracle website and set PATH/LD_LIBRARY_PATH
```

#### PostgreSQL Database

```bash
# Install PostgreSQL driver
pip install psycopg2-binary
```

### Step 4: Configure Environment Variables

```bash
# Copy template file
cp env.template .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

Configure the following in `.env`:

```env
# Database Type (ORACLE or POSTGRESQL)
DB_TYPE=ORACLE

# Database Connection (Oracle)
DB_HOST=your_database_host
DB_PORT=1521
DB_SID=your_service_name
DB_USER=DWT
DB_PASSWORD=your_password

# Database Connection (PostgreSQL - use if DB_TYPE=POSTGRESQL)
# DB_NAME=dms_tool
# DB_USER=dms_user
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432

# Schema Configuration
DMS_SCHEMA=DWT
CDR_SCHEMA=CDR

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here_change_in_production

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here

# CORS Configuration (adjust for your frontend URL)
# Add frontend URL to backend/fastapi_app.py CORS origins
```

**Important**: Generate strong secret keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Initialize SQLite Database (User Management)

The application uses SQLite for user management. The database is auto-created on first run, but you can initialize it manually:

```bash
cd backend
python -c "from database.dbconnect import sqlite_engine; from sqlalchemy import text; engine = sqlite_engine; conn = engine.connect(); conn.execute(text('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, salt TEXT, email TEXT, is_active INTEGER DEFAULT 1)')); conn.commit(); conn.close()"
```

Or let it be created automatically on first backend start.

### Step 6: Test Backend Installation

```bash
cd backend

# Test database connection
python -c "from database.dbconnect import create_metadata_connection; conn = create_metadata_connection(); print('Connection successful!'); conn.close()"

# Test FastAPI application
python -c "from fastapi_app import app; print('FastAPI app loaded successfully!')"
```

### Step 7: Start Backend (Development)

```bash
cd backend

# Using uvicorn directly
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload

# Or using the batch/shell script
# Windows:
start_fastapi.bat
# Linux:
./start_fastapi.sh
```

Verify backend is running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Step 8: Create Initial Admin User

```bash
cd backend
python -c "
from database.dbconnect import sqlite_engine
from sqlalchemy import text
import hashlib
import secrets

engine = sqlite_engine
conn = engine.connect()

# Create admin user
username = 'admin'
password = 'Admin@123'  # Change this immediately after first login
salt = secrets.token_hex(16)
password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

conn.execute(text('''
    INSERT INTO users (username, password_hash, salt, email, is_active, role)
    VALUES (:username, :password_hash, :salt, :email, 1, 'admin')
'''), {
    'username': username,
    'password_hash': password_hash,
    'salt': salt,
    'email': 'admin@example.com'
})

conn.commit()
conn.close()
print('Admin user created successfully!')
"
```

---

## Frontend Installation

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
# Install Node.js dependencies
npm install

# If you encounter issues, try:
npm install --legacy-peer-deps
```

### Step 3: Configure Frontend

Edit `frontend/src/app/config.js` or create `.env.local`:

```javascript
// config.js or .env.local
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const AUTH_API_BASE_URL = process.env.NEXT_PUBLIC_AUTH_API_BASE_URL || 'http://localhost:8000';

// reCAPTCHA (if enabled)
const ENABLE_RECAPTCHA = false; // Set to true in production
const RECAPTCHA_SITE_KEY = 'your_recaptcha_site_key';
```

Or create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_RECAPTCHA=false
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=your_key_here
```

### Step 4: Build Frontend

```bash
# Build for production
npm run build

# Verify build succeeded
# Should see "✓ Compiled successfully" message
```

### Step 5: Start Frontend (Development)

```bash
# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### Step 6: Start Frontend (Production)

```bash
# Using PM2 (recommended)
npm install -g pm2
pm2 start npm --name "dms-frontend" -- start

# Or using Node.js directly
npm start
```

---

## Configuration

### Backend Configuration

#### FastAPI CORS Configuration

Edit `backend/fastapi_app.py` to configure CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "http://your-production-domain.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Logging Configuration

Edit `backend/modules/logger.py` or set environment variables:

```python
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=backend/dwtool.log
```

### Frontend Configuration

#### API Endpoints

Ensure frontend points to correct backend URL:
- Development: `http://localhost:8000`
- Production: `http://your-backend-server:8000`

#### Session Configuration

Configure session timeout in `frontend/src/app/context/AuthContext.js`:

```javascript
const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes
```

---

## Service Setup

### Backend Service Setup

#### Windows Service (Using NSSM)

1. Download NSSM (Non-Sucking Service Manager)
2. Install service:

```cmd
nssm install DMSBackend
```

Configure:
- **Path**: `C:\Python39\python.exe` (or your Python path)
- **Arguments**: `-m uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000`
- **Working Directory**: `D:\DMS\DMSTOOL\backend`
- **Service Name**: DMSBackend

#### Linux Service (Using systemd)

Create `/etc/systemd/system/dms-backend.service`:

```ini
[Unit]
Description=DMS Tool Backend Service
After=network.target

[Service]
Type=simple
User=dmsuser
WorkingDirectory=/opt/dms-tool/backend
Environment="PATH=/opt/dms-tool/venv/bin"
ExecStart=/opt/dms-tool/venv/bin/uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dms-backend
sudo systemctl start dms-backend
sudo systemctl status dms-backend
```

### Scheduler Service Setup

#### Windows Service

Create `backend/start_scheduler.bat`:

```batch
@echo off
cd /d %~dp0
python -m backend.modules.jobs.scheduler_service
pause
```

Use NSSM to install as service (similar to backend).

#### Linux Service

Create `/etc/systemd/system/dms-scheduler.service`:

```ini
[Unit]
Description=DMS Tool Scheduler Service
After=network.target dms-backend.service

[Service]
Type=simple
User=dmsuser
WorkingDirectory=/opt/dms-tool/backend
Environment="PATH=/opt/dms-tool/venv/bin"
ExecStart=/opt/dms-tool/venv/bin/python -m backend.modules.jobs.scheduler_service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dms-scheduler
sudo systemctl start dms-scheduler
sudo systemctl status dms-scheduler
```

### Frontend Service Setup

#### Using PM2 (Recommended)

```bash
cd frontend
npm install -g pm2

# Start frontend
pm2 start npm --name "dms-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup
# Follow the instructions provided
```

#### Using systemd (Linux)

Create `/etc/systemd/system/dms-frontend.service`:

```ini
[Unit]
Description=DMS Tool Frontend Service
After=network.target

[Service]
Type=simple
User=dmsuser
WorkingDirectory=/opt/dms-tool/frontend
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## License Configuration

### Generate License Key

```bash
cd backend
python key_gen.py --days 365
```

This generates a license key valid for 365 days.

### Activate License

1. Start the application
2. Login as admin user
3. Navigate to **Admin** → **License Manager**
4. Enter the license key
5. Click **"Activate"**

Or activate via API:

```bash
curl -X POST http://localhost:8000/admin/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "your_license_key_here"}'
```

---

## Verification & Testing

### Backend Verification

1. **Health Check**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

2. **API Documentation**:
```bash
# Open in browser
http://localhost:8000/docs
```

3. **Database Connection Test**:
```bash
curl http://localhost:8000/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}'
# Should return JWT token
```

### Frontend Verification

1. **Access Application**:
   - Open browser: `http://localhost:3000`
   - Should see login page

2. **Login Test**:
   - Login with admin credentials
   - Should redirect to home page

3. **Module Access**:
   - Verify all modules are accessible
   - Check navigation works

### Scheduler Verification

1. **Check Scheduler Status**:
```bash
# Check if scheduler process is running
ps aux | grep scheduler_service

# Check scheduler logs
tail -f backend/dwtool.log | grep scheduler
```

2. **Test Job Execution**:
   - Create a test mapping
   - Create a job from mapping
   - Run job manually
   - Verify execution in Job Status & Logs

### Integration Testing

1. **End-to-End Test**:
   - Create database connection
   - Create SQL query
   - Create mapping using SQL
   - Create job from mapping
   - Execute job
   - Verify data in target table

2. **Schedule Test**:
   - Create scheduled job
   - Verify job appears in scheduler
   - Wait for scheduled time
   - Verify job executes

---

## Troubleshooting

### Common Installation Issues

#### Backend Issues

**Problem**: Cannot import modules
- **Solution**: Ensure virtual environment is activated and packages are installed

**Problem**: Database connection fails
- **Solution**: 
  - Verify database credentials in .env
  - Test connection with database client
  - Check network connectivity
  - Verify Oracle Instant Client is installed (for Oracle)

**Problem**: Port 8000 already in use
- **Solution**: 
  - Change port in uvicorn command
  - Or kill process using port: `netstat -ano | findstr :8000` (Windows) / `lsof -i :8000` (Linux)

#### Frontend Issues

**Problem**: npm install fails
- **Solution**:
  - Clear npm cache: `npm cache clean --force`
  - Delete node_modules and package-lock.json
  - Try: `npm install --legacy-peer-deps`

**Problem**: Build fails
- **Solution**:
  - Check Node.js version (should be 18+)
  - Review build error messages
  - Clear .next directory and rebuild

**Problem**: Cannot connect to backend
- **Solution**:
  - Verify backend is running
  - Check API_BASE_URL configuration
  - Check CORS settings in backend
  - Verify firewall rules

#### Database Issues

**Problem**: Tables don't exist
- **Solution**: Run database migration scripts

**Problem**: Permission errors
- **Solution**: Verify user has required permissions (GRANT statements)

**Problem**: Sequence errors
- **Solution**: Create required sequences manually

### Service Issues

**Problem**: Service won't start
- **Solution**:
  - Check service logs
  - Verify paths in service configuration
  - Check user permissions
  - Verify dependencies are installed

**Problem**: Service crashes repeatedly
- **Solution**:
  - Check application logs
  - Verify database connectivity
  - Check disk space
  - Review configuration files

### Performance Issues

**Problem**: Application is slow
- **Solution**:
  - Check database performance
  - Review log levels (set to INFO or WARNING)
  - Check server resources (CPU, RAM)
  - Optimize database queries

---

## Upgrading

### Backup Before Upgrade

```bash
# Backup database
# Oracle:
expdp DWT/password@database schemas=DWT directory=BACKUP_DIR dumpfile=dms_backup.dmp

# PostgreSQL:
pg_dump -U dms_user dms_tool > dms_backup.sql

# Backup application files
tar -czf dms-backup-$(date +%Y%m%d).tar.gz /path/to/application

# Backup configuration
cp backend/.env backend/.env.backup
cp frontend/.env.local frontend/.env.local.backup
```

### Upgrade Steps

1. **Stop Services**:
```bash
# Stop all services
systemctl stop dms-backend
systemctl stop dms-scheduler
systemctl stop dms-frontend
# Or
pm2 stop all
```

2. **Update Code**:
```bash
# Pull latest code
git pull origin main
# Or extract new version archive
```

3. **Update Backend**:
```bash
cd backend
source venv/bin/activate  # or activate conda environment
pip install -r requirements.txt --upgrade
```

4. **Run Database Migrations**:
```bash
# Run any new migration scripts
sqlplus DWT/password@database < doc/new_migration.sql
```

5. **Update Frontend**:
```bash
cd frontend
npm install
npm run build
```

6. **Update Configuration**:
   - Review new configuration options
   - Update .env files if needed
   - Update service configurations

7. **Start Services**:
```bash
systemctl start dms-backend
systemctl start dms-scheduler
systemctl start dms-frontend
```

8. **Verify**:
   - Test login
   - Verify modules work
   - Check logs for errors

### Rollback Procedure

If upgrade fails:

1. **Stop Services**
2. **Restore Database**:
```bash
# Oracle:
impdp DWT/password@database schemas=DWT directory=BACKUP_DIR dumpfile=dms_backup.dmp

# PostgreSQL:
psql -U dms_user dms_tool < dms_backup.sql
```

3. **Restore Application**:
```bash
tar -xzf dms-backup-YYYYMMDD.tar.gz -C /
```

4. **Restore Configuration**:
```bash
cp backend/.env.backup backend/.env
cp frontend/.env.local.backup frontend/.env.local
```

5. **Start Services**
6. **Verify**

---

## Additional Resources

### Documentation
- Technical Guide: `doc/TECHNICAL_GUIDE.md`
- User Guide: `doc/USER_GUIDE.md`
- API Documentation: `http://localhost:8000/docs` (when backend is running)

### Support
- Check application logs: `backend/dwtool.log`
- Review error messages in application
- Contact system administrator
- Check issue tracker (if available)

### Maintenance Tasks

#### Regular Maintenance

1. **Log Rotation**:
   - Rotate application logs regularly
   - Archive old logs
   - Monitor log sizes

2. **Database Maintenance**:
   - Regular backups
   - Analyze/rebuild indexes
   - Clean up old execution logs

3. **Application Updates**:
   - Keep dependencies updated
   - Apply security patches
   - Monitor for new versions

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Application Version**: 4.0.0

