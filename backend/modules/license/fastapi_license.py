from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# FastAPI imports
from backend.modules.license.license_manager import LicenseManager
from backend.modules.login.fastapi_login import get_user_from_token
from backend.database.dbconnect import sqlite_engine
from backend.modules.logger import info, warning, error

load_dotenv()

# Database setup
Session = sessionmaker(bind=sqlite_engine)

# Initialize license manager
license_manager = LicenseManager()

router = APIRouter(tags=["license"])


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


# Helper function to verify admin password
def verify_admin_password(user_id: int, password: str) -> bool:
    """Verify user password"""
    try:
        from backend.modules.login.fastapi_login import hash_password
        
        session = Session()
        try:
            user = session.execute(
                text("SELECT password_hash, salt FROM users WHERE user_id = :user_id"),
                {'user_id': user_id}
            ).fetchone()
            
            if not user:
                warning(f"Password verification failed: user {user_id} not found")
                return False
                
            # Verify password
            hashed_password = hash_password(password, user.salt)
            return hashed_password == user.password_hash
        finally:
            session.close()
    except Exception as e:
        error(f"Error verifying password: {str(e)}")
        return False


# FastAPI dependency to get current user
def get_current_user(request: Request):
    """Dependency to get current user from token"""
    return get_user_from_token(request)


# FastAPI dependency for admin access
def admin_user(user=Depends(get_current_user)):
    """Dependency that ensures the user is an admin"""
    if not check_admin_permission(user.user_id):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


# Pydantic models
class LicenseActivateRequest(BaseModel):
    license_key: str


class LicenseDeactivateRequest(BaseModel):
    password: str


class LicenseChangeRequest(BaseModel):
    license_key: str
    password: str


class LicenseStatusResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
    message: str | None = None


class LicenseResponse(BaseModel):
    success: bool
    message: str


@router.get("/license/status", response_model=LicenseStatusResponse)
async def get_license_status():
    """Get license status without requiring authentication"""
    try:
        status = license_manager.get_license_status()
        info("License status checked successfully")
        return LicenseStatusResponse(
            success=True,
            data=status
        )
    except Exception as e:
        error(f"Error getting license status: {str(e)}")
        return LicenseStatusResponse(
            success=False,
            error='Failed to get license status',
            message=str(e)
        )


@router.post("/admin/license/activate", response_model=LicenseResponse)
async def activate_license(
    payload: LicenseActivateRequest,
    user=Depends(admin_user)
):
    """Activate license (admin only)"""
    try:
        if not payload.license_key:
            warning("License activation attempted without license key")
            raise HTTPException(
                status_code=400,
                detail="License key is required"
            )
            
        success, message = license_manager.activate_license(payload.license_key)
        if success:
            info("License activated successfully")
        else:
            warning(f"License activation failed: {message}")
        return LicenseResponse(
            success=success,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error activating license: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"License activation failed: {str(e)}"
        )


@router.post("/admin/license/deactivate", response_model=LicenseResponse)
async def deactivate_license(
    payload: LicenseDeactivateRequest,
    user=Depends(admin_user)
):
    """Deactivate license (admin only, requires password)"""
    try:
        if not payload.password:
            warning("License deactivation attempted without password")
            raise HTTPException(
                status_code=400,
                detail="Password is required for deactivation"
            )
            
        # Verify password
        if not verify_admin_password(user.user_id, payload.password):
            warning(f"License deactivation failed: incorrect password for user {user.user_id}")
            raise HTTPException(
                status_code=401,
                detail="Incorrect password"
            )
            
        success, message = license_manager.deactivate_license()
        if success:
            info("License deactivated successfully")
        else:
            warning(f"License deactivation failed: {message}")
        return LicenseResponse(
            success=success,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error deactivating license: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"License deactivation failed: {str(e)}"
        )


@router.post("/admin/license/change", response_model=LicenseResponse)
async def change_license(
    payload: LicenseChangeRequest,
    user=Depends(admin_user)
):
    """Change license (admin only, requires password)"""
    try:
        if not payload.license_key:
            warning("License change attempted without license key")
            raise HTTPException(
                status_code=400,
                detail="License key is required"
            )
            
        if not payload.password:
            warning("License change attempted without password")
            raise HTTPException(
                status_code=400,
                detail="Password is required for license change"
            )
            
        # Verify password
        if not verify_admin_password(user.user_id, payload.password):
            warning(f"License change failed: incorrect password for user {user.user_id}")
            raise HTTPException(
                status_code=401,
                detail="Incorrect password"
            )
            
        # First deactivate current license
        license_manager.deactivate_license()
        
        # Then activate new license
        success, message = license_manager.activate_license(payload.license_key)
        if success:
            info("License changed successfully")
        else:
            warning(f"License change failed: {message}")
        return LicenseResponse(
            success=success,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error changing license: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"License change failed: {str(e)}"
        )

