from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os


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
    from modules.logger import error  # local import to avoid circular dependencies

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


# Ensure required directories exist (mirrors Flask app.py behavior)
os.makedirs("data/drafts", exist_ok=True)
os.makedirs("data/templates", exist_ok=True)


# Note:
# - During migration, run with:
#       uvicorn backend.fastapi_app:app --reload --host 0.0.0.0 --port 8000
# - Routers for each module (auth, admin, mapper, jobs, etc.) will be added and
#   included here in later phases of the migration plan.


