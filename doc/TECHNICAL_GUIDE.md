# DMS Tool - Technical Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Database Architecture](#database-architecture)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [API Documentation](#api-documentation)
8. [Module Details](#module-details)
9. [Data Flow & Processing](#data-flow--processing)
10. [Security Architecture](#security-architecture)
11. [Job Execution Engine](#job-execution-engine)
12. [Scheduler Service](#scheduler-service)
13. [Error Handling & Logging](#error-handling--logging)
14. [Performance Considerations](#performance-considerations)
15. [Configuration Reference](#configuration-reference)
16. [Development Guidelines](#development-guidelines)

---

## Introduction

The DMS (Data Management System) Tool is a comprehensive data warehouse management platform built with modern web technologies. This technical guide provides detailed information about the application's architecture, implementation details, APIs, and technical specifications.

### Application Version
- **Current Version**: 4.0.0
- **Backend Framework**: FastAPI (migrated from Flask)
- **Frontend Framework**: Next.js 14.x (React 18.x)
- **Python Version**: 3.8+ (3.9+ recommended)
- **Node.js Version**: 18.x+ (LTS recommended)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│                    (Web Browser - Next.js)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      API GATEWAY LAYER                       │
│                      (FastAPI Backend)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Module  │  │ Mapper Module│  │ Jobs Module  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Admin Module │  │ Reports Mod. │  │ Dashboard    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────┬────────────────────┬──────────────────┬─────────┘
            │                    │                  │
            │                    │                  │
┌───────────▼────────┐  ┌────────▼────────┐  ┌─────▼──────────┐
│  Metadata Database │  │ Scheduler Service│  │ SQLite (Users)│
│  (Oracle/PostgreSQL)│  │   (Background)   │  │               │
│  - DMS Schema      │  │                  │  │               │
│  - CDR Schema      │  │  Job Execution   │  │               │
│                    │  │     Engine       │  │               │
└────────────────────┘  └──────────────────┘  └───────────────┘
```

### Component Architecture

#### 1. Frontend (Next.js)
- **Framework**: Next.js 14.x with App Router
- **UI Libraries**: Material-UI (MUI), Tailwind CSS, Radix UI
- **State Management**: React Context API, React Hooks
- **HTTP Client**: Axios
- **Routing**: Next.js App Router

#### 2. Backend (FastAPI)
- **Framework**: FastAPI (async/await support)
- **API Style**: RESTful
- **Authentication**: JWT (JSON Web Tokens)
- **Database ORM**: SQLAlchemy (for SQLite), direct connection (for Oracle/PostgreSQL)
- **Validation**: Pydantic models

#### 3. Scheduler Service
- **Framework**: APScheduler (Advanced Python Scheduler)
- **Execution Engine**: ThreadPoolExecutor
- **Persistence**: SQLAlchemy job store

#### 4. Database Layer
- **Metadata**: Oracle or PostgreSQL
- **User Management**: SQLite
- **Schema Separation**: DMS Schema (metadata) and CDR Schema (data)

---

## Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | Latest | Web framework and API |
| **Language** | Python | 3.8+ | Backend programming |
| **Database Driver** | oracledb | Latest | Oracle connectivity |
| **Database Driver** | psycopg2-binary | Latest | PostgreSQL connectivity |
| **ORM** | SQLAlchemy | Latest | Database abstraction (SQLite) |
| **Scheduler** | APScheduler | Latest | Job scheduling |
| **Validation** | Pydantic | Latest | Data validation |
| **Environment** | python-dotenv | Latest | Configuration management |
| **Data Processing** | pandas | Latest | Data manipulation |
| **Excel Processing** | openpyxl | Latest | Excel file handling |

### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Next.js | 14.x | React framework |
| **Language** | JavaScript/TypeScript | ES6+ | Frontend programming |
| **UI Library** | Material-UI (MUI) | 5.x | Component library |
| **Styling** | Tailwind CSS | 3.x | Utility-first CSS |
| **State Management** | React Context API | Built-in | State management |
| **HTTP Client** | Axios | Latest | API communication |
| **Routing** | Next.js App Router | Built-in | Client-side routing |
| **Code Editor** | Monaco Editor | Latest | SQL/code editing |
| **Charts** | Chart.js | Latest | Data visualization |

---

## Database Architecture

### Schema Architecture

The application uses a **two-schema architecture**:

#### 1. DMS Schema (Metadata Schema)
- **Purpose**: Stores application metadata, configuration, and control information
- **Example Schema Names**: `DWT`, `dms_schema`
- **Location**: Configured via `DMS_SCHEMA` environment variable

**Tables**:
- `DMS_MAPR` - Mapping definitions
- `DMS_MAPRDTL` - Mapping detail definitions (field mappings)
- `DMS_MAPRSQL` - SQL query definitions
- `DMS_MAPERR` - Validation error logs
- `DMS_PARAMS` - Application parameters
- `DMS_JOB` - Job definitions
- `DMS_JOBDTL` - Job detail definitions
- `DMS_JOBSCH` - Job schedule definitions
- `DMS_JOBFLW` - Generated job flow code
- `DMS_JOBLOG` - Job execution logs
- `DMS_JOBERR` - Job execution errors
- `DMS_PRCLOG` - Process execution logs
- `DMS_PRCREQ` - Process request queue
- `DMS_DBCONDTLS` - Database connection definitions
- `DMS_FLUPLD` - File upload definitions
- `DMS_FLUPLDDTL` - File upload detail definitions

**Sequences**:
- `DWMAPRSEQ` - Mapping IDs
- `DWMAPRDTLSEQ` - Mapping detail IDs
- `DWMAPRSQLSEQ` - SQL query IDs
- `DWMAPERRSEQ` - Error log IDs

#### 2. CDR Schema (Data Schema)
- **Purpose**: Stores actual business data tables
- **Example Schema Names**: `CDR`, `cdr_schema`
- **Location**: Configured via `CDR_SCHEMA` environment variable

**Tables**:
- Created dynamically based on mapping configurations
- Examples: `DIM_CUSTOMER`, `FACT_SALES`, `STG_TRANSACTIONS`
- Include audit columns: `SKEY`, `RECCRDT`, `RECUPDT`, `RWHKEY` (hash column)

#### 3. SQLite Database (User Management)
- **Purpose**: User authentication and authorization
- **Location**: `backend/database/database_instance/sqlite_app.db`

**Tables**:
- `users` - User accounts
- `user_profiles` - User profile information
- `roles` - Role definitions
- `user_roles` - User-role assignments
- `permission_matrix` - Role-based permissions
- `password_history` - Password change history
- `login_audit_log` - Login audit trail

### Key Database Tables

#### DMS_MAPR (Mapping Definition)

```sql
CREATE TABLE DMS_MAPR (
    MAPID NUMBER PRIMARY KEY,
    MAPREF VARCHAR2(50) UNIQUE NOT NULL,
    MAPDESC VARCHAR2(500),
    SRCSYS VARCHAR2(100),
    TRGTBNM VARCHAR2(100),
    TRGTBTYP VARCHAR2(20),  -- DIMENSION, FACT, STAGING
    TRGSCHM VARCHAR2(100),
    FRQCD VARCHAR2(10),
    BLKPRCROWS NUMBER,
    TRGCONID NUMBER,  -- Target connection ID
    CURFLG VARCHAR2(1) DEFAULT 'Y',
    RECCRDT TIMESTAMP,
    RECUPDT TIMESTAMP,
    FOREIGN KEY (TRGCONID) REFERENCES DMS_DBCONDTLS(CONID)
);
```

#### DMS_MAPRDTL (Mapping Detail)

```sql
CREATE TABLE DMS_MAPRDTL (
    MAPDTLID NUMBER PRIMARY KEY,
    MAPREF VARCHAR2(50) NOT NULL,
    TRGCLNM VARCHAR2(100),  -- Target column name
    TRGCLDTYP VARCHAR2(50),  -- Data type
    TRGKEYFLG VARCHAR2(1),  -- Primary key flag
    TRGKEYSEQ NUMBER,  -- Primary key sequence
    TRGCLDESC VARCHAR2(500),
    MAPLOGIC CLOB,  -- Transformation logic
    KEYCLNM VARCHAR2(100),  -- Lookup key column
    VALCLNM VARCHAR2(100),  -- Lookup value column
    MAPCMBCD VARCHAR2(20),  -- Combine code (SUM, MAX, etc.)
    EXCSEQ NUMBER,  -- Execution sequence
    SCDTYP VARCHAR2(10),  -- SCD Type (1 or 2)
    LGVRFYFLG VARCHAR2(1),
    CURFLG VARCHAR2(1) DEFAULT 'Y',
    FOREIGN KEY (MAPREF) REFERENCES DMS_MAPR(MAPREF)
);
```

#### DMS_JOBSCH (Job Schedule)

```sql
CREATE TABLE DMS_JOBSCH (
    JOBSCHID NUMBER PRIMARY KEY,
    JOBID NUMBER NOT NULL,
    MAPREF VARCHAR2(50) NOT NULL,
    FRQCD VARCHAR2(10),  -- Frequency code (DL, WK, MN, etc.)
    FRQDD VARCHAR2(10),  -- Frequency day
    FRQHH NUMBER,  -- Frequency hour
    FRQMI NUMBER,  -- Frequency minute
    ENABLEFLG VARCHAR2(1) DEFAULT 'Y',
    DPND_JOBSCHID NUMBER,  -- Dependent job schedule ID
    STRDT TIMESTAMP,
    ENDDT TIMESTAMP,
    CURFLG VARCHAR2(1) DEFAULT 'Y',
    FOREIGN KEY (JOBID) REFERENCES DMS_JOB(JOBID),
    FOREIGN KEY (MAPREF) REFERENCES DMS_MAPR(MAPREF)
);
```

### Database Connection Management

#### Connection String Format

**Oracle**:
```
Connection String: host:port/service_name
Example: localhost:1521/XE
```

**PostgreSQL**:
```
Connection String: host:port/database
Example: localhost:5432/dms_tool
```

#### Environment Variables

```env
DB_TYPE=ORACLE  # or POSTGRESQL
DB_HOST=localhost
DB_PORT=1521
DB_SID=XE  # Oracle service name
DB_NAME=dms_tool  # PostgreSQL database name
DB_USER=username
DB_PASSWORD=password
DMS_SCHEMA=DWT
CDR_SCHEMA=CDR
```

---

## Backend Architecture

### Module Structure

```
backend/
├── fastapi_app.py              # Main FastAPI application
├── modules/
│   ├── login/                  # Authentication module
│   │   └── fastapi_login.py
│   ├── mapper/                 # Data mapping module
│   │   ├── fastapi_mapper.py
│   │   └── pkgdwmapr_python.py
│   ├── jobs/                   # Job management module
│   │   ├── fastapi_jobs.py
│   │   ├── scheduler_service.py
│   │   ├── execution_engine.py
│   │   └── pkgdwjob_python.py
│   ├── manage_sql/             # SQL management module
│   │   └── fastapi_manage_sql.py
│   ├── db_connections/         # Database connections module
│   │   └── fastapi_crud_dbconnections.py
│   ├── dashboard/              # Dashboard module
│   │   └── fastapi_dashboard.py
│   ├── reports/                # Reports module
│   │   └── fastapi_reports.py
│   ├── admin/                  # Admin module
│   │   ├── fastapi_admin.py
│   │   └── fastapi_access_control.py
│   ├── license/                # License management
│   │   └── fastapi_license.py
│   ├── file_upload/            # File upload module
│   │   └── fastapi_file_upload.py
│   ├── security/               # Security module
│   │   └── fastapi_security.py
│   └── logger.py               # Logging utility
├── database/
│   └── dbconnect.py            # Database connection utilities
└── helper_functions.py         # Common helper functions
```

### FastAPI Application Structure

```python
# fastapi_app.py
app = FastAPI(title="DMS Backend (FastAPI)", version="4.0.0")

# CORS Middleware
app.add_middleware(CORSMiddleware, ...)

# Global Exception Handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(...)

# Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(mapper_router, prefix="/mapper")
app.include_router(jobs_router, prefix="/job")
# ... other routers
```

### Authentication & Authorization

#### JWT Authentication

**Token Structure**:
```json
{
  "user_id": 1,
  "exp": 1234567890
}
```

**Token Generation**:
```python
token = jwt.encode(
    {"user_id": user.user_id, "exp": datetime.utcnow() + timedelta(days=1)},
    os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256"
)
```

**Token Validation**:
- Middleware validates JWT token on protected routes
- Token extracted from `Authorization` header or cookies
- User information loaded from database

#### Password Hashing

**Algorithm**: SHA-256 with salt
```python
salt = secrets.token_hex(16)
password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
```

### Database Connection Management

#### Connection Pooling

```python
# Oracle Connection
def create_oracle_connection():
    connection = oracledb.connect(
        user=db_user,
        password=db_password,
        dsn=f"{db_host}:{db_port}/{db_sid}"
    )
    return connection

# PostgreSQL Connection
def create_postgresql_connection():
    connection = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    connection.autocommit = True
    return connection
```

---

## Frontend Architecture

### Next.js App Router Structure

```
frontend/src/
├── app/                        # Next.js App Router pages
│   ├── auth/                   # Authentication pages
│   │   ├── login/
│   │   ├── forgot-password/
│   │   └── reset-password/
│   ├── home/                   # Home page
│   ├── mapper_module/          # Mapper module
│   ├── jobs/                   # Jobs module
│   ├── dashboard/              # Dashboard module
│   ├── admin/                  # Admin module
│   └── layout.js               # Root layout
├── components/                 # Shared components
│   ├── NavBar.js
│   ├── Sidebar.js
│   └── LayoutWrapper.js
├── context/                    # React contexts
│   ├── AuthContext.js
│   └── ThemeContext.js
└── config.js                   # Configuration
```

### State Management

#### AuthContext

```javascript
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  
  const login = async (username, password) => {
    // Login logic
  };
  
  const logout = () => {
    // Logout logic
  };
  
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### API Communication

#### Axios Configuration

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## API Documentation

### Authentication Endpoints

#### POST /auth/login
**Description**: User login
**Request Body**:
```json
{
  "username": "string",
  "password": "string",
  "recaptchaToken": "string (optional)"
}
```
**Response**:
```json
{
  "token": "jwt_token",
  "user_id": 1,
  "username": "string",
  "email": "string",
  "role": "string"
}
```

#### POST /auth/logout
**Description**: User logout
**Response**: `{"message": "Logged out successfully"}`

#### POST /auth/change-password
**Description**: Change user password
**Request Body**:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

### Mapper Endpoints

#### GET /mapper/get-mappings
**Description**: Get list of mappings
**Response**:
```json
[
  {
    "mapid": 1,
    "mapref": "MAP_001",
    "mapdesc": "Customer Dimension Mapping",
    "srcsys": "ERP",
    "trgtbnm": "DIM_CUSTOMER",
    "trgtbtyp": "DIMENSION",
    "curflg": "Y"
  }
]
```

#### POST /mapper/save-to-db
**Description**: Save mapping to database
**Request Body**:
```json
{
  "reference": "MAP_001",
  "description": "string",
  "sourceSystem": "string",
  "tableName": "string",
  "tableType": "DIMENSION",
  "targetSchema": "string",
  "freqCode": "DL",
  "bulkProcessRows": 1000,
  "sqlCode": "SQL_001",
  "rows": [
    {
      "fieldName": "CUSTOMER_ID",
      "dataType": "NUMBER",
      "primaryKey": true,
      "pkSeq": 1,
      "logic": ":1"
    }
  ]
}
```

### Jobs Endpoints

#### GET /job/get-jobs
**Description**: Get list of jobs
**Response**:
```json
[
  {
    "jobid": 1,
    "mapref": "MAP_001",
    "jobdesc": "Daily Customer Load",
    "status": "ACTIVE"
  }
]
```

#### POST /job/create-job
**Description**: Create a new job
**Request Body**:
```json
{
  "mapref": "MAP_001",
  "description": "string",
  "schedule": {
    "freqCode": "DL",
    "freqDD": "1",
    "freqHH": 2,
    "freqMI": 0
  }
}
```

#### POST /job/run-now
**Description**: Execute job immediately
**Request Body**:
```json
{
  "jobid": 1,
  "mapref": "MAP_001"
}
```

### Database Connections Endpoints

#### GET /api/db-connections
**Description**: Get list of database connections
**Response**:
```json
[
  {
    "conid": 1,
    "connm": "Production Oracle",
    "dbtyp": "ORACLE",
    "dbhost": "localhost",
    "dbport": 1521,
    "dbsid": "XE",
    "curflg": "Y"
  }
]
```

#### POST /api/db-connections
**Description**: Create database connection
**Request Body**:
```json
{
  "connm": "Production Oracle",
  "dbtyp": "ORACLE",
  "dbhost": "localhost",
  "dbport": 1521,
  "dbsid": "XE",
  "dbuser": "user",
  "dbpassword": "password"
}
```

### Full API Documentation

Access interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Module Details

### 1. Authentication Module

**Purpose**: User authentication and session management

**Key Features**:
- JWT-based authentication
- Password hashing with salt
- Login attempt tracking
- Account lockout after failed attempts
- Password reset functionality
- Session timeout management

**Files**:
- `backend/modules/login/fastapi_login.py`

### 2. Mapper Module

**Purpose**: Define data transformations from source to target

**Key Features**:
- Create and edit mappings
- Field-level transformation logic
- SCD Type 1 and Type 2 support
- Validation and error checking
- Preview functionality

**Files**:
- `backend/modules/mapper/fastapi_mapper.py`
- `backend/modules/mapper/pkgdwmapr_python.py`

### 3. Jobs Module

**Purpose**: Job creation, scheduling, and execution management

**Key Features**:
- Create jobs from mappings
- Schedule jobs (daily, weekly, monthly, etc.)
- Job dependencies
- Immediate execution
- Job status tracking

**Files**:
- `backend/modules/jobs/fastapi_jobs.py`
- `backend/modules/jobs/pkgdwjob_python.py`
- `backend/modules/jobs/scheduler_service.py`
- `backend/modules/jobs/execution_engine.py`

### 4. Manage SQL Module

**Purpose**: Create and manage SQL queries used as data sources

**Key Features**:
- SQL query editor
- Query validation
- Test execution
- Connection assignment
- Query versioning

**Files**:
- `backend/modules/manage_sql/fastapi_manage_sql.py`

### 5. Dashboard Module

**Purpose**: Analytics and performance monitoring

**Key Features**:
- Job execution metrics
- Success/failure rates
- Execution duration analysis
- Data volume tracking
- Performance trends

**Files**:
- `backend/modules/dashboard/fastapi_dashboard.py`

### 6. Reports Module

**Purpose**: Report generation and management

**Key Features**:
- Report definitions
- Report templates
- Multiple output formats (PDF, Excel, CSV)
- Scheduled report generation

**Files**:
- `backend/modules/reports/fastapi_reports.py`
- `backend/modules/reports/report_service.py`

### 7. File Upload Module

**Purpose**: Upload and process data files

**Key Features**:
- File upload (CSV, Excel, JSON)
- Column mapping
- Data validation
- Transformation rules
- Batch processing

**Files**:
- `backend/modules/file_upload/fastapi_file_upload.py`
- `backend/modules/file_upload/file_upload_service.py`

### 8. Admin Module

**Purpose**: System administration

**Key Features**:
- User management
- Role management
- Permission management
- License management
- System configuration

**Files**:
- `backend/modules/admin/fastapi_admin.py`
- `backend/modules/admin/fastapi_access_control.py`

---

## Data Flow & Processing

### ETL Process Flow

```
1. Source Data Extraction
   ├─ SQL Query (Manage SQL Module)
   ├─ Database Connection (Source)
   └─ Data Retrieval

2. Data Transformation
   ├─ Mapping Logic (Mapper Module)
   ├─ Field Transformations
   ├─ Lookups
   └─ Data Validation

3. Target Data Loading
   ├─ Target Table Creation (if needed)
   ├─ Data Insert/Update
   ├─ SCD Processing (Type 1/Type 2)
   └─ Audit Column Population
```

### Job Execution Flow

```
1. Job Creation
   ├─ Select Mapping
   ├─ Configure Schedule
   └─ Save Job

2. Schedule Activation
   ├─ Save to DMS_JOBSCH
   ├─ Scheduler Service Syncs
   └─ APScheduler Adds Job

3. Job Execution
   ├─ Trigger (Time-based or Manual)
   ├─ Queue Request (DMS_PRCREQ)
   ├─ Scheduler Picks Up Request
   ├─ Execution Engine Loads Job Flow
   ├─ Execute Python Code (DMS_JOBFLW.DWLOGIC)
   ├─ Log Execution (DMS_PRCLOG, DMS_JOBLOG)
   └─ Update Status

4. Post-Execution
   ├─ Update Job Status
   ├─ Trigger Dependent Jobs (if any)
   └─ Send Notifications (if configured)
```

### Hash-Based Change Detection

The system uses MD5 hash for efficient change detection:

```python
def generate_hash(row_data, columns):
    """
    Generate MD5 hash from row data.
    Excludes audit columns (SKEY, RECCRDT, RECUPDT, etc.)
    """
    hash_string = "|".join(str(row_data[col]) for col in columns)
    return hashlib.md5(hash_string.encode()).hexdigest()
```

**RWHKEY Column**:
- 32-character VARCHAR2 column
- Stores MD5 hash of row data
- Used for change detection (O(1) comparison)
- Automatically maintained

---

## Security Architecture

### Authentication

1. **Login Process**:
   - User submits credentials
   - Password verified (hashed comparison)
   - JWT token generated
   - Token stored in localStorage and cookies

2. **Token Validation**:
   - Middleware extracts token from request
   - Token validated (signature, expiration)
   - User loaded from database
   - Request proceeds if valid

3. **Session Management**:
   - Token expiration: 24 hours (configurable)
   - Refresh token support (optional)
   - Logout invalidates token

### Authorization

1. **Role-Based Access Control (RBAC)**:
   - Users assigned roles
   - Roles have permissions
   - Permissions map to modules/actions

2. **Module-Level Permissions**:
   - View, Create, Edit, Delete permissions
   - Module access control
   - Dynamic permission checking

3. **Row-Level Security**:
   - User context in queries
   - Data filtering based on user permissions

### Security Features

- Password hashing (SHA-256 with salt)
- Account lockout after failed attempts
- Password complexity requirements
- Session timeout
- CORS configuration
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF protection (token-based)

---

## Job Execution Engine

### Execution Flow

```python
class JobExecutionEngine:
    def execute(self, request: QueueRequest):
        # 1. Load job flow code
        job_flow_code = self._load_job_flow(request.mapref)
        
        # 2. Create execution context
        context = self._create_execution_context(request)
        
        # 3. Execute Python code
        exec(job_flow_code, context)
        
        # 4. Log results
        self._log_execution(request, result)
```

### Job Flow Code Structure

```python
# Generated Python code (stored in DMS_JOBFLW.DWLOGIC)
def execute_job():
    # Initialize connections
    source_conn = create_source_connection()
    target_conn = create_target_connection()
    
    # Execute source SQL
    source_data = execute_source_sql(source_conn)
    
    # Process each row
    for row in source_data:
        # Calculate hash
        hash_value = generate_hash(row, columns)
        
        # Check if exists in target
        existing = get_target_row(target_conn, row['PK'])
        
        if existing:
            if existing['RWHKEY'] != hash_value:
                # Update row
                update_target_row(target_conn, row)
        else:
            # Insert new row
            insert_target_row(target_conn, row)
    
    # Commit transaction
    target_conn.commit()
```

---

## Scheduler Service

### Architecture

```
Scheduler Service
├─ APScheduler (Background Scheduler)
│  ├─ Cron Triggers (Scheduled Jobs)
│  └─ Interval Triggers (Interval Jobs)
│
├─ Queue Poller
│  ├─ Polls DMS_PRCREQ table
│  ├─ Processes NEW requests
│  └─ Updates request status
│
└─ Execution Engine
   ├─ ThreadPoolExecutor
   ├─ Concurrent job execution
   └─ Job status tracking
```

### Frequency Codes

| Code | Description | Trigger Type |
|------|-------------|--------------|
| YR | Yearly | CronTrigger (year='*') |
| HY | Half-Yearly | CronTrigger (month='1,7') |
| QT | Quarterly | CronTrigger (month='1,4,7,10') |
| MN | Monthly | CronTrigger (day=DD) |
| FN | Fortnightly | CronTrigger (day_of_week=DD) |
| WK | Weekly | CronTrigger (day_of_week=DD) |
| DL | Daily | CronTrigger (hour=HH, minute=MI) |
| ID | Interval | IntervalTrigger |

### Dependency Handling

```python
# Job dependencies stored in DMS_JOBSCH.DPND_JOBSCHID
# When parent job completes:
1. Check for dependent jobs
2. Queue dependent jobs
3. Execute in order
```

---

## Error Handling & Logging

### Logging Architecture

```python
# Logger module (backend/modules/logger.py)
class Logger:
    def __init__(self):
        self.log_file = "backend/dwtool.log"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def info(self, message):
        # Log INFO level messages
    
    def error(self, message):
        # Log ERROR level messages
```

### Error Handling

1. **Global Exception Handler**:
```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred"}
    )
```

2. **Module-Level Error Handling**:
   - Try-catch blocks in all modules
   - Specific error messages
   - Error logging to DMS_MAPERR or DMS_JOBERR

3. **Validation Errors**:
   - Pydantic validation
   - Database constraint violations
   - Business rule violations

### Log Storage

- **Application Logs**: `backend/dwtool.log`
- **Database Error Logs**: `DMS_MAPERR`, `DMS_JOBERR`
- **Execution Logs**: `DMS_JOBLOG`, `DMS_PRCLOG`

---

## Performance Considerations

### Database Optimization

1. **Indexing**:
   - Primary keys automatically indexed
   - Foreign key indexes
   - Frequently queried columns

2. **Connection Pooling**:
   - Connection reuse
   - Connection timeout handling

3. **Query Optimization**:
   - Parameterized queries
   - Batch operations
   - Bulk insert/update

### Application Performance

1. **Caching**:
   - User session caching
   - Mapping metadata caching
   - Connection caching

2. **Async Operations**:
   - FastAPI async/await
   - Non-blocking I/O
   - Concurrent job execution

3. **Bulk Processing**:
   - Configurable batch sizes
   - Bulk insert operations
   - Chunked data processing

### Scheduler Performance

1. **Thread Pool**:
   - Configurable worker threads
   - Parallel job execution
   - Resource management

2. **Queue Processing**:
   - Efficient polling intervals
   - Batch queue processing
   - Priority handling

---

## Configuration Reference

### Environment Variables

```env
# Database Configuration
DB_TYPE=ORACLE
DB_HOST=localhost
DB_PORT=1521
DB_SID=XE
DB_USER=username
DB_PASSWORD=password
DMS_SCHEMA=DWT
CDR_SCHEMA=CDR

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# Scheduler Configuration
DMS_TIMEZONE=UTC
SCHEDULER_MAX_WORKERS=5

# CORS Configuration (in code)
ALLOWED_ORIGINS=http://localhost:3000
```

### Application Configuration

**Backend** (`backend/fastapi_app.py`):
- CORS origins
- Exception handlers
- Router registration

**Frontend** (`frontend/src/app/config.js`):
- API base URL
- reCAPTCHA configuration
- Feature flags

---

## Development Guidelines

### Code Style

- **Python**: PEP 8 compliant
- **JavaScript**: ESLint configured
- **Type Hints**: Python type hints recommended
- **Documentation**: Docstrings for all functions

### Git Workflow

1. Create feature branch
2. Make changes
3. Test locally
4. Commit with descriptive messages
5. Push and create pull request

### Testing

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test module interactions
3. **API Tests**: Test API endpoints
4. **E2E Tests**: Test complete workflows

### Deployment Checklist

- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Services started
- [ ] Health checks passing
- [ ] Initial admin user created
- [ ] License activated
- [ ] Backup configured

---

## Additional Resources

### Documentation
- User Guide: `doc/USER_GUIDE.md`
- Installation Guide: `doc/INSTALLATION_GUIDE.md`
- API Documentation: `http://localhost:8000/docs`

### Code Examples
- See `doc/` folder for implementation examples
- Check module-specific documentation

### Support
- Application logs: `backend/dwtool.log`
- Database logs: Check database server logs
- Error tracking: Review DMS_MAPERR, DMS_JOBERR tables

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Application Version**: 4.0.0

