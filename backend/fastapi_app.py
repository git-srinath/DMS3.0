from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

from backend.modules.login.fastapi_login import router as auth_router
from backend.modules.type_mapping.fastapi_parameter_mapping import (
    router as parameter_mapping_router,
)
from backend.modules.db_connections.fastapi_crud_dbconnections import (
    router as dbconnections_router,
)
from backend.modules.manage_sql.fastapi_manage_sql import (
    router as manage_sql_router,
)
from backend.modules.mapper.fastapi_mapper import (
    router as mapper_router,
)
from backend.modules.jobs.fastapi_jobs import (
    router as jobs_router,
)
from backend.modules.reports.fastapi_reports import (
    router as reports_router,
)
from backend.modules.license.fastapi_license import (
    router as license_router,
)
from backend.modules.dashboard.fastapi_dashboard import (
    router as dashboard_router,
)
from backend.modules.admin.fastapi_access_control import (
    router as access_control_router,
)
from backend.modules.admin.fastapi_admin import (
    router as admin_router,
)
from backend.modules.security.fastapi_security import (
    router as security_router,
)

load_dotenv()

app = FastAPI(title="DMS Backend (FastAPI)", version="4.0.0")

# CORS configuration – must specify exact origins when using credentials
# Cannot use wildcard "*" when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        # Add production frontend URL here when deploying
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler mirroring Flask's @app.errorhandler(Exception).
    Logs the error and returns a generic response.
    """
    # Local import to avoid circular dependencies; support both package and Flask contexts
    try:
        from backend.modules.logger import error
    except ImportError:
        from modules.logger import error

    error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred"},
    )


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint used for smoke testing the FastAPI app.
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    Root endpoint that redirects to health check.
    """
    return {"status": "ok", "message": "DMS Backend (FastAPI) is running", "health": "/health"}


# Routers (Phase 2: start with auth/login)
app.include_router(auth_router, prefix="/auth")
app.include_router(parameter_mapping_router, prefix="/mapping")
app.include_router(dbconnections_router, prefix="/api")
app.include_router(manage_sql_router, prefix="/manage-sql")
app.include_router(mapper_router, prefix="/mapper")
app.include_router(jobs_router, prefix="/job")
app.include_router(reports_router, prefix="/api")
app.include_router(license_router, prefix="/api")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(access_control_router, prefix="/access-control")
app.include_router(admin_router, prefix="/admin")
app.include_router(security_router, prefix="/security")


# Ensure required directories exist (mirrors Flask app.py behavior)
os.makedirs("data/drafts", exist_ok=True)
os.makedirs("data/templates", exist_ok=True)


# Note:
# - During migration, run with:
#       uvicorn backend.fastapi_app:app --reload --host 0.0.0.0 --port 8000
# - Routers for each module (auth, admin, mapper, jobs, etc.) will be added and
#   included here in later phases of the migration plan.


