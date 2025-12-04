from fastapi import APIRouter, HTTPException, Depends, Request, Path
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import List

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.login.fastapi_login import get_user_from_token
    from backend.database.dbconnect import sqlite_engine
    from backend.modules.security.utils import (
        AVAILABLE_MODULES,
        AVAILABLE_MODULE_KEYS,
        ensure_user_module_table,
        get_user_module_states,
    )
except ImportError:  # When running Flask app.py directly inside backend
    from modules.login.login import token_required  # type: ignore
    from modules.security.utils import (  # type: ignore
        AVAILABLE_MODULES,
        AVAILABLE_MODULE_KEYS,
        ensure_user_module_table,
        get_user_module_states,
    )
    from sqlalchemy import create_engine  # type: ignore
    engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))  # type: ignore
    Session = sessionmaker(bind=engine)  # type: ignore

load_dotenv()

# Database setup
try:
    Session = sessionmaker(bind=sqlite_engine)
except NameError:
    # Fallback for Flask context
    from sqlalchemy import create_engine
    engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
    Session = sessionmaker(bind=engine)

router = APIRouter(tags=["security"])


# Initialize table on module load
def _initialize_table():
    session = Session()
    try:
        ensure_user_module_table(session)
        session.commit()
    finally:
        session.close()


_initialize_table()


# FastAPI dependency to get current user
def get_current_user(request: Request):
    """Dependency to get current user from token"""
    return get_user_from_token(request)


# Helper function to check admin permission
def check_admin_permission(user_id: int) -> bool:
    """Check if user has admin role"""
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT r.role_name 
                FROM user_roles ur 
                JOIN roles r ON ur.role_id = r.role_id 
                WHERE ur.user_id = :user_id 
                AND r.role_name IN ('ADMIN')
            """),
            {'user_id': user_id}
        ).fetchone()
        return bool(result)
    finally:
        session.close()


# FastAPI dependency for admin access
def admin_user(user=Depends(get_current_user)):
    """Dependency that ensures the user is an admin"""
    if not check_admin_permission(user.user_id):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


# Pydantic models
class ModuleUpdate(BaseModel):
    key: str
    enabled: bool = True


class UpdateUserAccessRequest(BaseModel):
    modules: List[ModuleUpdate]


@router.get("/modules")
async def list_modules(user=Depends(admin_user)):
    """
    Returns the modules that can be assigned to users.
    Admin only.
    """
    return {'modules': AVAILABLE_MODULES}


@router.get("/user-access/{user_id}")
async def get_user_access(
    user_id: int = Path(..., description="User ID"),
    admin_user_obj=Depends(admin_user)
):
    """Get user access modules (admin only)"""
    session = Session()
    try:
        # Validate user exists
        user_exists = session.execute(
            text("SELECT 1 FROM users WHERE user_id = :user_id"),
            {'user_id': user_id},
        ).fetchone()

        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        modules = get_user_module_states(session, user_id)
        return {'modules': modules}
    finally:
        session.close()


@router.post("/user-access/{user_id}")
async def update_user_access(
    user_id: int = Path(..., description="User ID"),
    payload: UpdateUserAccessRequest = ...,
    admin_user_obj=Depends(admin_user)
):
    """Update user access modules (admin only)"""
    if not isinstance(payload.modules, list):
        raise HTTPException(status_code=400, detail="Modules payload must be a list")

    session = Session()
    try:
        ensure_user_module_table(session)

        user_exists = session.execute(
            text("SELECT 1 FROM users WHERE user_id = :user_id"),
            {'user_id': user_id},
        ).fetchone()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate module keys
        provided_keys = {module.key for module in payload.modules}
        invalid_keys = provided_keys - AVAILABLE_MODULE_KEYS
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f'Invalid module keys: {", ".join(sorted(invalid_keys))}'
            )

        # Normalize modules to ensure every module has a value
        normalized_states = {}
        for module in payload.modules:
            if module.key in AVAILABLE_MODULE_KEYS:
                normalized_states[module.key] = bool(module.enabled)

        # For modules not included, treat as enabled by default
        for module in AVAILABLE_MODULES:
            normalized_states.setdefault(module['key'], True)

        for module_key, enabled in normalized_states.items():
            session.execute(
                text(
                    """
                    INSERT INTO user_module_access (user_id, module_key, is_enabled, assigned_by, assigned_at)
                    VALUES (:user_id, :module_key, :is_enabled, :assigned_by, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, module_key) DO UPDATE SET
                        is_enabled = excluded.is_enabled,
                        assigned_by = excluded.assigned_by,
                        assigned_at = excluded.assigned_at
                    """
                ),
                {
                    'user_id': user_id,
                    'module_key': module_key,
                    'is_enabled': 1 if enabled else 0,
                    'assigned_by': admin_user_obj.user_id,
                },
            )

        session.commit()
        modules = get_user_module_states(session, user_id)
        return {'message': 'User access updated successfully', 'modules': modules}
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f'Failed to update access: {str(exc)}')
    finally:
        session.close()


@router.get("/my-modules")
async def get_current_user_modules(user=Depends(get_current_user)):
    """Get current user's enabled modules"""
    session = Session()
    try:
        modules = get_user_module_states(session, user.user_id)
        enabled_keys = [module['key'] for module in modules if module['enabled']]
        return {'modules': modules, 'enabled_keys': enabled_keys}
    finally:
        session.close()

