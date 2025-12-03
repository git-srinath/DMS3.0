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

load_dotenv()

app = FastAPI(title="DMS Backend (FastAPI)", version="4.0.0")

# CORS configuration – start permissive, can be tightened later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to specific frontend origins if needed
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


# Routers (Phase 2: start with auth/login)
app.include_router(auth_router, prefix="/auth")
app.include_router(parameter_mapping_router, prefix="/mapping")
app.include_router(dbconnections_router, prefix="/api")
app.include_router(manage_sql_router, prefix="/manage-sql")
app.include_router(mapper_router, prefix="/mapper")
app.include_router(jobs_router, prefix="/job")
app.include_router(reports_router, prefix="/api")


# Ensure required directories exist (mirrors Flask app.py behavior)
os.makedirs("data/drafts", exist_ok=True)
os.makedirs("data/templates", exist_ok=True)


# Note:
# - During migration, run with:
#       uvicorn backend.fastapi_app:app --reload --host 0.0.0.0 --port 8000
# - Routers for each module (auth, admin, mapper, jobs, etc.) will be added and
#   included here in later phases of the migration plan.


