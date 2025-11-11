# Ahana DW Tool Deployment Guide

## Initial Deployment Steps

### 1. Connect to Server
Connect to your Windows or Linux server using your preferred method (SSH, RDP, etc.)

### 2. Clone Repository
```bash
git clone https://github.com/ahana-admteam/ahana-dw-tool.git
cd ahana-dw-tool
```

### 3. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Setup Python Environment
**Option A: Activate existing conda environment**
```bash
conda activate your-environment-name
```

**Option B: Create new environment with required packages**
```bash
conda create -n ahana-env python=3.x
conda activate ahana-env
pip install -r python_libs.txt
```

#### Generate License Key
```bash
python key_gen.py --days <number_of_days>
```

#### Start Gunicorn Server
**Method 1: Direct command**
```bash
gunicorn --bind 0.0.0.0:5001 -w 10 app:app
```

**Method 2: Using server script**
```bash
./server.sh start
```

#### Verify Backend Process
```bash
ps -ef | grep gunicorn
```

### 4. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd ../frontend
```

#### Install Dependencies
```bash
npm install
```

#### Build the Packages
```bash
npm run build
```

#### Start Frontend Application
```bash
pm2 start eco-config.js
```

```bash
npm run dev # To start server in dev mode # optional
```

#### Verify Frontend Status
```bash
pm2 status eco-config.js
```

## Service Management

### Starting Services

**Backend:**
```bash
cd backend
./server.sh start
# OR
gunicorn --bind 0.0.0.0:5001 -w 10 app:app
```

**Frontend:**
```bash
cd frontend
pm2 start eco-config.js
```

### Stopping Services

**Frontend:**
```bash
cd frontend
pm2 stop eco-config.js
```

**Backend:**
```bash
cd backend
# Find process ID
ps -ef | grep gunicorn
# Kill process using PID
kill <process_id>
# OR if using server script
./server.sh stop
```

### Restarting Services

**Backend:**
```bash
cd backend
./server.sh restart
```

**Frontend:**
```bash
cd frontend
pm2 restart eco-config.js
```

## Verification Commands

- **Check backend processes:** `ps -ef | grep gunicorn`
- **Check frontend status:** `pm2 status e
