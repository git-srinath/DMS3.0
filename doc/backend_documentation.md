# Ahana DW Tool Backend Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [File Structure](#file-structure)
3. [Core Components](#core-components)
4. [Database Connectivity](#database-connectivity)
5. [Authentication & Authorization](#authentication--authorization)
6. [License Management](#license-management)
7. [Mapper Module](#mapper-module)
8. [Jobs Module](#jobs-module)
9. [Dashboard Module](#dashboard-module)
10. [Error Handling & Logging](#error-handling--logging)
11. [Configuration & Dependencies](#configuration--dependencies)
12. [API Endpoints](#api-endpoints)

## Introduction

The Ahana DW Tool backend is a Flask-based application designed to manage data warehouse mappings, jobs, and their execution. It provides a comprehensive set of APIs for user authentication, license management, data mapping, job scheduling, and dashboard analytics.

The application connects to an Oracle database for storing and retrieving data warehouse mapping configurations, job details, and execution logs. It also uses SQLite for local user management and authentication.

## File Structure

```
backend/
├── app.py                  # Main application entry point
├── key_gen.py              # License key generation utilities
├── dwtool.log              # Application log file
├── config/                 # Configuration files
├── data/                   # Data files and templates
│   ├── drafts/             # Draft mapping files
│   └── templates/          # Template files
├── database/               # Database connection modules
│   ├── dbconnect.py        # Database connection utilities
│   └── database_instance/  # SQLite database files
├── modules/                # Application modules
│   ├── admin/              # Admin module for user management
│   ├── dashboard/          # Dashboard analytics module
│   ├── helper_functions.py # Common helper functions
│   ├── jobs/               # Job scheduling and execution module
│   ├── license/            # License management module
│   ├── logger.py           # Logging utilities
│   ├── login/              # Authentication module
│   ├── manage_sql/         # SQL management module
│   ├── mapper/             # Data mapping module
│   └── type_mapping/       # Data type mapping module
```

## Core Components

### app.py

The main application file that initializes the Flask application, registers blueprints, and sets up error handling. It serves as the entry point for the application.

Key features:
- Flask application initialization
- CORS configuration
- Blueprint registration for modular API endpoints
- Global error handling
- Directory structure setup

### modules/logger.py

A custom logger implementation for the application that provides consistent logging across all modules.

Key features:
- Singleton pattern implementation
- Custom formatting for logs
- Log filtering capabilities
- User context integration with Flask's g object

## Database Connectivity

### database/dbconnect.py

Handles database connections to both Oracle and SQLite databases.

Key features:
- Oracle connection management
- SQLite connection setup
- Environment variable loading for database credentials
- Error handling for connection failures

Connection types:
- Oracle: Primary database for storing mapping configurations, job details, and execution logs
- SQLite: Local database for user management and authentication

## Authentication & Authorization

### modules/login/login.py

Handles user authentication, password management, and session control.

Key features:
- JWT-based authentication
- Password hashing and salting
- Password reset functionality
- Login attempt tracking
- Token validation middleware

### modules/admin/admin.py

Manages user administration, roles, and permissions.

Key features:
- User creation and management
- Role-based access control
- User approval workflow
- Audit logging
- Notification management

### modules/admin/access_control.py

Implements access control mechanisms for different modules and functionalities.

## License Management

### modules/license/license.py

API endpoints for license management.

Key features:
- License status checking
- License activation
- License deactivation
- License changing

### modules/license/license_manager.py

Core license management functionality.

Key features:
- License validation
- System identification
- License file handling

### key_gen.py

Utility for generating and validating license keys.

Key features:
- Secret key generation
- System identifier extraction
- License key encryption/decryption
- License validation

## Mapper Module

### modules/mapper/mapper.py

Manages data mapping configurations for the data warehouse.

Key features:
- Template download/upload
- Mapping configuration management
- Logic validation
- Mapping activation/deactivation

Core functionality:
- Creating and updating mapping configurations
- Validating mapping logic
- Managing mapping details
- Exporting/importing mapping configurations

## Jobs Module

### modules/jobs/jobs.py

Handles job creation, scheduling, and execution.

Key features:
- Job creation from mappings
- Job scheduling (immediate, regular, historical)
- Job execution monitoring
- Job logs and error handling

Core functionality:
- Creating jobs from mapping configurations
- Scheduling jobs for execution
- Monitoring job execution
- Managing job dependencies
- Stopping running jobs

## Dashboard Module

### modules/dashboard/dashboard.py

Provides analytics and metrics for the application.

Key features:
- Overall system metrics
- Job execution statistics
- Performance metrics
- Success/failure tracking

Key metrics:
- Mapping and job counts
- Average job duration
- Rows processed statistics
- Success/failure rates

## Error Handling & Logging

### modules/logger.py

Custom logger implementation for consistent logging across the application.

Key features:
- User context integration
- Log filtering
- Formatted output
- Error tracking

### Global Error Handler

Implemented in app.py to catch and log all unhandled exceptions.

## Configuration & Dependencies

### Environment Variables

The application relies on the following environment variables:
- `DB_USER`: Oracle database username
- `DB_PASSWORD`: Oracle database password
- `DB_HOST`: Oracle database host
- `DB_PORT`: Oracle database port
- `DB_SID`: Oracle database SID
- `SQLITE_DATABASE_URL`: SQLite database URL
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `JWT_ACCESS_TOKEN_EXPIRES`: JWT token expiry time
- `SCHEMA`: Oracle schema name
- `MAIL_SERVER`: SMTP server for email notifications
- `MAIL_PORT`: SMTP port
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password

### External Dependencies

- Flask: Web framework
- Flask-CORS: Cross-origin resource sharing
- SQLAlchemy: SQL toolkit and ORM
- oracledb: Oracle database driver
- JWT: JSON Web Token for authentication
- pandas: Data manipulation library
- openpyxl: Excel file handling
- cryptography: Encryption utilities
- getmac: MAC address retrieval

## API Endpoints

### Authentication

- `POST /auth/login`: User login
- `POST /auth/forgot-password`: Request password reset
- `POST /auth/reset-password`: Reset password
- `GET /auth/verify-token`: Verify JWT token
- `POST /auth/change-password-after-login`: Change password after login

### Admin

- `GET /admin/users`: Get all users
- `POST /admin/users`: Create a new user
- `PUT /admin/users/<user_id>`: Update user details
- `DELETE /admin/users/<user_id>`: Delete (deactivate) a user
- `POST /admin/approve-user/<user_id>`: Approve a pending user
- `GET /admin/roles`: Get all roles
- `POST /admin/roles`: Create a new role
- `PUT /admin/roles/<role_id>`: Update a role
- `DELETE /admin/roles/<role_id>`: Delete a role
- `GET /admin/audit-logs`: Get audit logs
- `GET /admin/pending-approvals`: Get pending user approvals
- `POST /admin/users/<user_id>/reset-password`: Reset a user's password
- `POST /admin/notifications`: Create a notification
- `GET /admin/notifications`: Get all notifications
- `POST /admin/notifications/dismiss`: Dismiss notifications

### License

- `GET /api/license/status`: Get license status
- `POST /admin/license/activate`: Activate a license
- `POST /admin/license/deactivate`: Deactivate a license
- `POST /admin/license/change`: Change a license

### Mapper

- `GET /mapper/download-template`: Download mapping template
- `POST /mapper/download-current`: Download current mapping
- `POST /mapper/upload`: Upload mapping template
- `GET /mapper/get-by-reference/<reference>`: Get mapping by reference
- `POST /mapper/save-to-db`: Save mapping to database
- `POST /mapper/validate-logic`: Validate mapping logic
- `POST /mapper/validate-batch`: Validate batch logic
- `GET /mapper/get-parameter-mapping-datatype`: Get parameter mapping data types
- `GET /mapper/parameter_scd_type`: Get parameter SCD types
- `POST /mapper/activate-deactivate`: Activate/deactivate mapping
- `GET /mapper/get-all-mapper-reference`: Get all mapper references
- `POST /mapper/delete-mapper-reference`: Delete mapper reference
- `POST /mapper/delete-mapping-detail`: Delete mapping detail

### Jobs

- `GET /job/jobs_list`: Get all jobs
- `GET /job/view_mapping/<mapping_reference>`: View mapping details
- `POST /job/create-update`: Create or update a job
- `GET /job/get_all_jobs`: Get all job flows
- `GET /job/get_job_details/<mapref>`: Get job details
- `GET /job/get_job_schedule_details/<job_flow_id>`: Get job schedule details
- `GET /job/get_scheduled_jobs`: Get scheduled jobs
- `GET /job/get_job_and_process_log_details/<mapref>`: Get job and process log details
- `GET /job/get_error_details/<job_id>`: Get job error details
- `POST /job/save_job_schedule`: Save job schedule
- `POST /job/save_parent_child_job`: Save parent-child job relationship
- `POST /job/enable_disable_job`: Enable/disable job
- `POST /job/schedule-job-immediately`: Schedule job for immediate execution
- `POST /job/stop-running-job`: Stop a running job

### Dashboard

- `GET /dashboard/all_metrics`: Get all dashboard metrics
- `GET /dashboard/jobs_overview`: Get jobs overview
- `GET /dashboard/jobs_processed_rows`: Get processed rows by job
- `GET /dashboard/jobs_executed_duration`: Get job execution duration
- `GET /dashboard/jobs_average_run_duration`: Get average job run duration
- `GET /dashboard/jobs_successful_failed`: Get job success/failure counts


graph TD
    A[app.py] --> B[Blueprints]
    A --> C[Error Handling]
    A --> D[CORS Setup]
    
    B --> E[auth_bp]
    B --> F[admin_bp]
    B --> G[license_bp]
    B --> H[mapper_bp]
    B --> I[jobs_bp]
    B --> J[dashboard_bp]
    B --> K[access_control_bp]
    B --> L[manage_sql_bp]
    B --> M[parameter_mapping_bp]
    
    N[Database] --> O[Oracle DB]
    N --> P[SQLite]
    
    E --> Q[login.py]
    F --> R[admin.py]
    G --> S[license.py]
    H --> T[mapper.py]
    I --> U[jobs.py]
    J --> V[dashboard.py]
    
    Q --> W[Authentication]
    R --> X[User Management]
    S --> Y[License Management]
    T --> Z[Mapping Configuration]
    U --> AA[Job Scheduling]
    V --> AB[Analytics]
    
    AC[logger.py] --> AD[Logging System]
    
    AE[helper_functions.py] --> AF[Utility Functions]
    
    AG[key_gen.py] --> AH[License Generation]
    
    O --> AI[Mapping Data]
    O --> AJ[Job Data]
    O --> AK[Execution Logs]
    
    P --> AL[User Data]
    P --> AM[Authentication Data]
    
    S --> AG
    Y --> AG
