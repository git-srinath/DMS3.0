from fastapi import APIRouter, HTTPException, Query, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.login.fastapi_login import get_user_from_token
    from backend.database.dbconnect import sqlite_engine
except ImportError:  # When running Flask app.py directly inside backend
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

router = APIRouter(tags=["access_control"])


# FastAPI dependency to get current user
def get_current_user(request: Request):
    """Dependency to get current user from token"""
    return get_user_from_token(request)


@router.get("/get-permissions")
async def get_permissions(
    user_id: int = Query(..., description="User ID"),
    module_name: str = Query(..., description="Module name"),
    user=Depends(get_current_user)
):
    """Get permissions for a specific user and module"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Check if user id exists in the database
    session = Session()
    try:
        user_check = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user_check:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the user's permissions
        query = """
            SELECT 
                pm.module_name,
                r.role_name,
                CASE WHEN pm.can_view = 1 THEN 'Yes' ELSE 'No' END as can_view,
                CASE WHEN pm.can_create = 1 THEN 'Yes' ELSE 'No' END as can_create,
                CASE WHEN pm.can_edit = 1 THEN 'Yes' ELSE 'No' END as can_edit,
                CASE WHEN pm.can_delete = 1 THEN 'Yes' ELSE 'No' END as can_delete
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            JOIN permission_matrix pm ON r.role_id = pm.role_id
            WHERE u.user_id = :user_id
            AND pm.module_name = :module_name
            ORDER BY r.role_name, pm.module_name
        """
        permissions = session.execute(
            text(query),
            {'user_id': user_id, 'module_name': module_name}
        ).fetchall()
        
        # Convert Row objects to dictionaries for JSON serialization
        permissions_list = []
        for permission in permissions:
            permissions_list.append({
                'module_name': permission.module_name,
                'role_name': permission.role_name,
                'can_view': permission.can_view,
                'can_create': permission.can_create,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete
            })
        
        return {'permissions': permissions_list}
    finally:
        session.close()

