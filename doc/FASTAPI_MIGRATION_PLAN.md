## FastAPI Migration Plan for DMS Backend

This document describes how to migrate the existing Flask backend in `backend/app.py` to FastAPI **incrementally**, while keeping the application usable and minimizing risk.

The main goals are:

- **Replace Flask with FastAPI** as the primary web framework.
- **Reuse existing business logic** (modules, DB access, security) as much as possible.
- **Avoid breaking the current frontend** during migration.
- **Build new Data Upload functionality directly on FastAPI** once the base is stable.

---

## 1. Branching & High-Level Strategy

- Create a long-lived migration branch:

```bash
git checkout main
git pull
git checkout -b feature/fastapi-migration
git push -u origin feature/fastapi-migration
```

- All migration work happens in `feature/fastapi-migration` until FastAPI is stable.
- The existing Flask app in `backend/app.py` remains **unchanged** until the final cut-over.
- FastAPI is introduced **side-by-side** with Flask, on a different port (e.g., FastAPI on 8000, Flask on 5000).

Once FastAPI fully replaces Flask routes and is tested:

- Merge `feature/fastapi-migration` into `main`.
- Remove Flask-specific code and stop running the Flask app.
- Begin/continue Data Upload development on FastAPI.

---

## 2. Phase 1 – FastAPI Skeleton and Shared Infrastructure

### 2.1 Create FastAPI entrypoint

- Add `backend/fastapi_app.py` (or `backend/main_fastapi.py`) that:
  - Creates a `FastAPI` instance.
  - Configures CORS to match current needs (allow frontend origin, credentials, headers, methods).
  - Registers a global exception handler that logs via `modules.logger` (similar to Flask `@app.errorhandler`).
  - Provides a `/health` endpoint for basic smoke tests.

**Acceptance criteria:**

- `uvicorn backend.fastapi_app:app --reload --host 0.0.0.0 --port 8000` starts successfully.
- `/health` returns `{"status": "ok"}`.

### 2.2 Extract shared configuration and DB access (if needed)

- Review `backend/database/dbconnect.py` and current configuration loading.
- Ensure that:
  - Environment variables are loaded via `dotenv` (already used in `backend/app.py`).
  - Database engine/session creation is exposed in a way usable by both Flask and FastAPI.
- If required, introduce helper functions/dependencies:
  - `get_db()` for creating/yielding DB sessions (can be wired into FastAPI with `Depends` later).

**Acceptance criteria:**

- FastAPI app can import and use the same DB connection utilities as Flask.

---

## 3. Phase 2 – Convert a First Blueprint to a FastAPI Router

Choose a relatively self-contained blueprint first (e.g. **auth/login**).

### 3.1 Create a FastAPI router for login/auth

- In `modules/login/`, add a new file, e.g. `fastapi_login.py`, which:
  - Defines `router = APIRouter(tags=["auth"])`.
  - Creates Pydantic models for request/response payloads (`LoginRequest`, `LoginResponse`, etc.).
  - Reuses existing business logic from `modules/login/login.py` where possible (token generation, validation).
  - Implements routes that mirror existing Flask endpoints (`POST /auth/login`, etc.).

### 3.2 Register router in `fastapi_app.py`

- Import and register the router:

```python
from modules.login.fastapi_login import router as auth_router
app.include_router(auth_router, prefix="/auth")
```

### 3.3 Frontend test (small and isolated)

- In a small test branch (or via config), point the frontend’s login API calls to the FastAPI base URL (`http://localhost:8000` instead of the Flask port) for `/auth/*` only.
- Verify login, token handling, and error responses work as expected.

**Acceptance criteria:**

- Login flow works end-to-end using FastAPI for `/auth/*` routes.
- No change in observable behavior for the user (same UI/UX, same status codes where practical).

---

## 4. Phase 3 – Port Security & Auth Dependencies

### 4.1 Convert auth decorators to FastAPI dependencies

- Existing decorators like `token_required`, `admin_required` should be adapted to FastAPI:
  - Implement `current_user` dependency that:
    - Reads the `Authorization` header.
    - Validates the token using existing helper logic.
    - Returns user info or raises an HTTP 401.
  - Implement `admin_user` dependency layered on `current_user`.

- Use these dependencies in FastAPI routes:

```python
from fastapi import Depends

@router.get("/secure-endpoint")
async def secure_endpoint(user=Depends(admin_user)):
    ...
```

**Acceptance criteria:**

- All new FastAPI routes that require auth use dependency-based enforcement.
- Behavior matches current security rules.

---

## 5. Phase 4 – Migrate Feature Modules Incrementally

For each major module currently registered in `backend/app.py`:

- `modules.admin.admin` → `modules/admin/fastapi_admin.py`
- `modules.license.license` → `modules/license/fastapi_license.py`
- `modules.mapper.mapper` → `modules/mapper/fastapi_mapper.py`
- `modules.jobs.jobs` → `modules/jobs/fastapi_jobs.py`
- `modules.type_mapping.parameter_mapping` → `modules/type_mapping/fastapi_parameter_mapping.py`
- `modules.dashboard.dashboard` → `modules/dashboard/fastapi_dashboard.py`
- `modules.admin.access_control` → `modules/admin/fastapi_access_control.py`
- `modules.manage_sql.manage_sql` → `modules/manage_sql/fastapi_manage_sql.py`
- `modules.db_connections.crud_dbconnections` → `modules/db_connections/fastapi_crud_dbconnections.py`
- `modules.security` → `modules/fastapi_security.py` (or similar structure)
- `modules.reports` → `modules/fastapi_reports.py` or `modules/reports/fastapi_reports.py`

### 5.1 Pattern for each module

1. **Create a FastAPI router file** mirroring the existing blueprint routes.
2. **Copy or adapt** view logic to FastAPI route functions.
3. Introduce **Pydantic models** for request/response payloads where appropriate.
4. Register the router in `fastapi_app.py` with the same URL prefix currently used for that blueprint.
5. Update the frontend configuration so that module’s calls go to FastAPI (switch base URL).
6. Run targeted tests for that feature area.

### 5.2 Order of migration (suggested)

1. `auth` (already done in Phase 3).
2. `db_connections` (CRUD DB connections) – foundational for other features.
3. `mapper` and `manage_sql` – core to your data manipulation workflows.
4. `jobs` and `dashboard` – operational/monitoring views.
5. `reports` – reporting endpoints.
6. `admin`/`access_control`, `license`, and `security` refinements.

**Acceptance criteria (per module):**

- All endpoints in that module are available via FastAPI and behave as before (as much as possible).
- Frontend for that feature no longer depends on the Flask endpoint.

---

## 6. Phase 5 – Decommission Flask and Switch Fully to FastAPI

Once all major modules are migrated and the frontend uses FastAPI for all calls:

1. Stop starting `backend/app.py` in any scripts or deployment configurations.
2. Run a **full regression pass** of the application with only FastAPI running.
3. Remove or archive Flask-specific code:
   - `backend/app.py` (or reduce it to a thin compatibility layer if needed).
   - Flask-specific decorators or utility code that is no longer used.
4. Update documentation (e.g., `doc/backend_documentation.md`, `doc/how_to_deploy.md`) to reference FastAPI and `uvicorn` instead of Flask’s `app.run`.

**Acceptance criteria:**

- The system runs entirely off FastAPI in dev/test environments.
- All docs, scripts, and deployment steps reference FastAPI only.

---

## 7. Phase 6 – Data Upload Feature on FastAPI

Once FastAPI is the primary backend (or at least core modules are stable on it), start the **Data Upload** feature **on top of FastAPI**, not Flask.

### 7.1 Branching

- Create a new branch from the FastAPI migration branch (or from `main` after migration is merged):

```bash
git checkout feature/fastapi-migration   # or main, if merged
git checkout -b feature/data-upload
git push -u origin feature/data-upload
```

### 7.2 New FastAPI router for Data Upload

- Create `modules/data_upload/fastapi_data_upload.py` with:
  - `APIRouter` and endpoints for upload sessions, file upload, preview, mapping, transformations, and commit.
  - Pydantic models representing upload sessions, mapping configs, and transformation specs.
  - File handling and parsing logic for CSV/Excel/JSON plugged into the FastAPI dependency system.

### 7.3 Frontend integration

- Add new routes in the Next.js frontend (`/data-upload/...`) pointing to FastAPI endpoints.
- Implement the multi-step Data Upload UI (file upload, preview, mapping, transforms, commit) talking directly to FastAPI.

**Acceptance criteria:**

- Data Upload functionality works end-to-end using the FastAPI backend.
- Existing features remain stable.

---

## 8. Risk Management and Best Practices

- **Feature flags / toggles**: For significant changes, consider adding configuration flags so new routes/features can be turned on/off easily during rollout.
- **Logging and monitoring**: Ensure `modules.logger` is correctly used from FastAPI to capture errors and performance issues.
- **Testing strategy**:
  - Start with manual testing in each module after migration.
  - Gradually add automated tests (unit + integration) around critical paths, especially auth, DB connections, mapper, and jobs.
- **Performance considerations**:
  - Plan to use async endpoints in areas with heavy I/O (e.g., file uploads, DB queries for Data Upload).
  - Reuse DB connection pooling logic where possible.

---

## 9. Completion Criteria

The FastAPI migration is considered **complete** when:

1. All Flask blueprints have FastAPI router equivalents and are no longer used by the frontend.
2. The application can be fully started and operated using only:
   - `uvicorn backend.fastapi_app:app` (or your chosen ASGI server).
3. All deployment and local run instructions reference FastAPI instead of Flask.
4. New features (like Data Upload) are being built on FastAPI only.

At that point, `feature/fastapi-migration` can be merged to `main`, and the Flask code can be safely retired.


