from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict, Any
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.login.fastapi_login import get_user_from_token
    from backend.modules.login.login import hash_password, generate_salt, is_valid_password
    from backend.database.dbconnect import sqlite_engine
    from backend.modules.logger import info, error
except ImportError:  # When running Flask app.py directly inside backend
    from modules.login.login import hash_password, generate_salt, is_valid_password  # type: ignore
    from sqlalchemy import create_engine  # type: ignore
    engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))  # type: ignore
    Session = sessionmaker(bind=engine)  # type: ignore
    from modules.logger import info, error  # type: ignore

load_dotenv()

# Database setup
try:
    Session = sessionmaker(bind=sqlite_engine)
except NameError:
    # Fallback for Flask context
    from sqlalchemy import create_engine
    engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
    Session = sessionmaker(bind=engine)

router = APIRouter(tags=["admin"])

# Notification file path
NOTIFICATION_FILE_PATH = os.path.join('data', 'notifications.json')

# Ensure data directory exists
os.makedirs('data', exist_ok=True)


# ===== Dependencies =====

def get_current_user(request: Request):
    """Dependency to get current user from token"""
    return get_user_from_token(request)


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


def admin_required(user=Depends(get_current_user)):
    """Dependency to require admin privileges"""
    if not check_admin_permission(user.user_id):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


# ===== Pydantic Models =====

class UserCreateRequest(BaseModel):
    username: str
    email: str  # Changed from EmailStr to str for more lenient validation (matches Flask behavior)
    password: str
    first_name: str
    last_name: str
    role_id: int
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = True
    change_password: Optional[bool] = False


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    account_status: Optional[str] = None


class UserStatusRequest(BaseModel):
    is_active: bool


class UserDetailsUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone_number: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


class RoleCreateRequest(BaseModel):
    role_name: str
    description: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None


class ModuleCreateRequest(BaseModel):
    module_name: str
    display_name: str
    description: Optional[str] = None


class ModuleUpdateRequest(BaseModel):
    module_name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None


class NotificationCreateRequest(BaseModel):
    title: str
    message: str
    notification_type: Optional[str] = "info"
    target_user_id: Optional[int] = None


class NotificationDismissRequest(BaseModel):
    notification_id: int


# ===== User Management Endpoints =====

@router.get("/users")
async def get_users(admin_user=Depends(admin_required)):
    """Get all users with their roles and profiles"""
    session = Session()
    try:
        users = session.execute(
            text("""
                SELECT 
                    u.user_id, 
                    u.username, 
                    u.email, 
                    u.is_active, 
                    u.account_status,
                    u.created_at, 
                    u.created_by, 
                    u.approved_by,
                    r.role_id,
                    r.role_name,
                    up.first_name,
                    up.last_name,
                    up.department,
                    up.position
                FROM users u
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.role_id
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                ORDER BY u.user_id
            """)
        ).fetchall()
        
        # Process the results
        users_dict = {}
        for user in users:
            user_id = user.user_id
            if user_id not in users_dict:
                users_dict[user_id] = {
                    'user_id': str(user.user_id),
                    'username': str(user.username),
                    'email': str(user.email),
                    'is_active': bool(user.is_active),
                    'account_status': str(user.account_status),
                    'created_at': str(user.created_at),
                    'created_by': str(user.created_by),
                    'approved_by': str(user.approved_by) if user.approved_by else None,
                    'first_name': str(user.first_name) if user.first_name else None,
                    'last_name': str(user.last_name) if user.last_name else None,
                    'department': str(user.department) if user.department else None,
                    'position': str(user.position) if user.position else None,
                    'roles': []
                }
            if user.role_id:
                users_dict[user_id]['roles'].append({
                    'role_id': user.role_id,
                    'role_name': user.role_name
                })
        
        # For backward compatibility with the original Flask implementation
        # and existing frontend (which expects a plain list), return the list
        # of users directly rather than wrapping in an object.
        return list(users_dict.values())
    except Exception as e:
        error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")
    finally:
        session.close()


@router.post("/users")
async def create_user(
    payload: UserCreateRequest,
    admin_user=Depends(admin_required)
):
    """Create a new user"""
    session = Session()
    try:
        # Validate password
        if not is_valid_password(payload.password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters"
            )

        # Check if username or email already exists
        existing_user = session.execute(
            text("""
                SELECT user_id, username, email 
                FROM users 
                WHERE username = :username OR email = :email
            """),
            {'username': payload.username, 'email': payload.email}
        ).fetchone()

        if existing_user:
            if existing_user.username == payload.username:
                raise HTTPException(status_code=400, detail="Username already exists")
            if existing_user.email == payload.email:
                raise HTTPException(status_code=400, detail="Email already exists")

        # Check if role exists
        role = session.execute(
            text("SELECT role_id FROM roles WHERE role_id = :role_id"),
            {'role_id': payload.role_id}
        ).fetchone()

        if not role:
            raise HTTPException(status_code=400, detail=f"Invalid role ID: {payload.role_id}")

        # Generate password hash and salt
        salt = generate_salt()
        password_hash = hash_password(payload.password, salt)

        # Create user with transaction
        try:
            # Insert user
            result = session.execute(
                text("""
                    INSERT INTO users (
                        username, email, password_hash, salt, 
                        created_by, account_status, is_active, change_password
                    )
                    VALUES (
                        :username, :email, :password_hash, :salt,
                        :created_by, 'PENDING', :is_active, :change_password
                    )
                    RETURNING user_id
                """),
                {
                    'username': payload.username,
                    'email': payload.email,
                    'password_hash': password_hash,
                    'salt': salt,
                    'created_by': admin_user.user_id,
                    'is_active': payload.is_active,
                    'change_password': payload.change_password
                }
            )
            user_id = result.fetchone()[0]

            # Create user profile
            session.execute(
                text("""
                    INSERT INTO user_profiles (
                        user_id, first_name, last_name, department, position
                    )
                    VALUES (
                        :user_id, :first_name, :last_name, :department, :position
                    )
                """),
                {
                    'user_id': user_id,
                    'first_name': payload.first_name,
                    'last_name': payload.last_name,
                    'department': payload.department,
                    'position': payload.position
                }
            )

            # Create user_roles entry
            session.execute(
                text("""
                    INSERT INTO user_roles (user_id, role_id, assigned_by)
                    VALUES (:user_id, :role_id, :assigned_by)
                """),
                {
                    'user_id': user_id,
                    'role_id': payload.role_id,
                    'assigned_by': admin_user.user_id
                }
            )

            session.commit()
            return {
                'message': 'User created successfully',
                'user_id': user_id
            }
        except Exception as e:
            session.rollback()
            error(f"Database error in create_user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error in create_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        session.close()


@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: int = Path(..., description="User ID to approve"),
    admin_user=Depends(admin_required)
):
    """Approve a pending user"""
    session = Session()
    try:
        # Check if user exists and is pending
        user = session.execute(
            text("SELECT user_id, account_status FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.account_status != 'PENDING':
            raise HTTPException(status_code=400, detail="User is not pending approval")

        # Update user status
        session.execute(
            text("""
                UPDATE users 
                SET account_status = 'APPROVED', approved_by = :approved_by
                WHERE user_id = :user_id
            """),
            {'user_id': user_id, 'approved_by': admin_user.user_id}
        )
        session.commit()

        return {'message': 'User approved successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error approving user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve user: {str(e)}")
    finally:
        session.close()


@router.post("/users/{user_id}/approve")
async def approve_user_alt(
    user_id: int = Path(..., description="User ID to approve"),
    admin_user=Depends(admin_required)
):
    """Approve a pending user (alternative endpoint)"""
    return await approve_user(user_id, admin_user)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(..., description="User ID"),
    payload: UserUpdateRequest = ...,
    admin_user=Depends(admin_required)
):
    """Update user information"""
    session = Session()
    try:
        # Check if user exists
        user = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build update query dynamically
        updates = []
        params = {'user_id': user_id}

        if payload.username is not None:
            # Check if username already exists
            existing = session.execute(
                text("SELECT user_id FROM users WHERE username = :username AND user_id != :user_id"),
                {'username': payload.username, 'user_id': user_id}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
            updates.append("username = :username")
            params['username'] = payload.username

        if payload.email is not None:
            # Check if email already exists
            existing = session.execute(
                text("SELECT user_id FROM users WHERE email = :email AND user_id != :user_id"),
                {'email': payload.email, 'user_id': user_id}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Email already exists")
            updates.append("email = :email")
            params['email'] = payload.email

        if payload.is_active is not None:
            updates.append("is_active = :is_active")
            params['is_active'] = payload.is_active

        if payload.account_status is not None:
            updates.append("account_status = :account_status")
            params['account_status'] = payload.account_status

        if updates:
            session.execute(
                text(f"UPDATE users SET {', '.join(updates)} WHERE user_id = :user_id"),
                params
            )

        # Update user profile
        profile_updates = []
        profile_params = {'user_id': user_id}

        if payload.first_name is not None:
            profile_updates.append("first_name = :first_name")
            profile_params['first_name'] = payload.first_name

        if payload.last_name is not None:
            profile_updates.append("last_name = :last_name")
            profile_params['last_name'] = payload.last_name

        if payload.department is not None:
            profile_updates.append("department = :department")
            profile_params['department'] = payload.department

        if payload.position is not None:
            profile_updates.append("position = :position")
            profile_params['position'] = payload.position

        if profile_updates:
            # Check if profile exists
            profile_exists = session.execute(
                text("SELECT user_id FROM user_profiles WHERE user_id = :user_id"),
                {'user_id': user_id}
            ).fetchone()

            if profile_exists:
                session.execute(
                    text(f"UPDATE user_profiles SET {', '.join(profile_updates)} WHERE user_id = :user_id"),
                    profile_params
                )
            else:
                # Create profile if it doesn't exist
                session.execute(
                    text("""
                        INSERT INTO user_profiles (user_id, first_name, last_name, department, position)
                        VALUES (:user_id, :first_name, :last_name, :department, :position)
                    """),
                    profile_params
                )

        # Update role if provided
        if payload.role_id is not None:
            # Check if role exists
            role = session.execute(
                text("SELECT role_id FROM roles WHERE role_id = :role_id"),
                {'role_id': payload.role_id}
            ).fetchone()

            if not role:
                raise HTTPException(status_code=400, detail=f"Invalid role ID: {payload.role_id}")

            # Update or create user_roles entry
            existing_role = session.execute(
                text("SELECT user_id FROM user_roles WHERE user_id = :user_id"),
                {'user_id': user_id}
            ).fetchone()

            if existing_role:
                session.execute(
                    text("""
                        UPDATE user_roles 
                        SET role_id = :role_id, assigned_by = :assigned_by
                        WHERE user_id = :user_id
                    """),
                    {
                        'user_id': user_id,
                        'role_id': payload.role_id,
                        'assigned_by': admin_user.user_id
                    }
                )
            else:
                session.execute(
                    text("""
                        INSERT INTO user_roles (user_id, role_id, assigned_by)
                        VALUES (:user_id, :role_id, :assigned_by)
                    """),
                    {
                        'user_id': user_id,
                        'role_id': payload.role_id,
                        'assigned_by': admin_user.user_id
                    }
                )

        session.commit()
        return {'message': 'User updated successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    finally:
        session.close()


@router.post("/users/{user_id}/status")
async def update_user_status(
    user_id: int = Path(..., description="User ID"),
    payload: UserStatusRequest = ...,
    admin_user=Depends(admin_required)
):
    """Update user active status"""
    session = Session()
    try:
        user = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session.execute(
            text("UPDATE users SET is_active = :is_active WHERE user_id = :user_id"),
            {'user_id': user_id, 'is_active': payload.is_active}
        )
        session.commit()

        return {'message': 'User status updated successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error updating user status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user status: {str(e)}")
    finally:
        session.close()


@router.get("/pending-approvals")
async def get_pending_approvals(admin_user=Depends(admin_required)):
    """Get all users pending approval"""
    session = Session()
    try:
        users = session.execute(
            text("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.email,
                    u.created_at,
                    u.created_by,
                    up.first_name,
                    up.last_name,
                    up.department,
                    up.position
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.account_status = 'PENDING'
                ORDER BY u.created_at DESC
            """)
        ).fetchall()

        result = []
        for user in users:
            result.append({
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'created_at': str(user.created_at),
                'created_by': str(user.created_by),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'department': user.department,
                'position': user.position
            })

        return {'pending_users': result}
    except Exception as e:
        error(f"Error getting pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending approvals: {str(e)}")
    finally:
        session.close()


@router.put("/users/{user_id}/details")
async def update_user_details(
    user_id: int = Path(..., description="User ID"),
    payload: UserDetailsUpdateRequest = ...,
    admin_user=Depends(admin_required)
):
    """Update user profile details"""
    session = Session()
    try:
        user = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if profile exists
        profile_exists = session.execute(
            text("SELECT user_id FROM user_profiles WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        updates = []
        params = {'user_id': user_id}

        if payload.first_name is not None:
            updates.append("first_name = :first_name")
            params['first_name'] = payload.first_name

        if payload.last_name is not None:
            updates.append("last_name = :last_name")
            params['last_name'] = payload.last_name

        if payload.department is not None:
            updates.append("department = :department")
            params['department'] = payload.department

        if payload.position is not None:
            updates.append("position = :position")
            params['position'] = payload.position

        if payload.phone_number is not None:
            updates.append("phone_number = :phone_number")
            params['phone_number'] = payload.phone_number

        if updates:
            if profile_exists:
                session.execute(
                    text(f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = :user_id"),
                    params
                )
            else:
                # Create profile if it doesn't exist
                session.execute(
                    text(f"""
                        INSERT INTO user_profiles (user_id, {', '.join([u.split(' = ')[0] for u in updates])})
                        VALUES (:user_id, {', '.join([':' + u.split(' = ')[0] for u in updates])})
                    """),
                    params
                )

        session.commit()
        return {'message': 'User details updated successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error updating user details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
    finally:
        session.close()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int = Path(..., description="User ID"),
    admin_user=Depends(admin_required)
):
    """Delete a user"""
    session = Session()
    try:
        user = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete user (cascade will handle related records if foreign keys are set up)
        session.execute(
            text("DELETE FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        session.commit()

        return {'message': 'User deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    finally:
        session.close()


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int = Path(..., description="User ID"),
    payload: ResetPasswordRequest = ...,
    admin_user=Depends(admin_required)
):
    """Reset a user's password"""
    session = Session()
    try:
        user = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate password
        if not is_valid_password(payload.new_password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters"
            )

        # Generate new password hash and salt
        salt = generate_salt()
        password_hash = hash_password(payload.new_password, salt)

        # Update password
        session.execute(
            text("UPDATE users SET password_hash = :password_hash, salt = :salt WHERE user_id = :user_id"),
            {
                'user_id': user_id,
                'password_hash': password_hash,
                'salt': salt
            }
        )
        session.commit()

        return {'message': 'Password reset successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error resetting password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")
    finally:
        session.close()


# ===== Role Management Endpoints =====

@router.get("/roles")
async def get_roles(admin_user=Depends(admin_required)):
    """Get all roles with their permissions (mirrors legacy Flask behavior)."""
    session = Session()
    try:
        # This query matches the original Flask implementation in admin.py,
        # joining roles with the permission_matrix to build a permissions map.
        roles = session.execute(
            text(
                """
                SELECT 
                    r.role_id,
                    r.role_name,
                    r.description,
                    r.is_system_role,
                    pm.module_name,
                    pm.can_view,
                    pm.can_create,
                    pm.can_edit,
                    pm.can_delete
                FROM roles r
                LEFT JOIN permission_matrix pm ON r.role_id = pm.role_id
                ORDER BY r.role_id
                """
            )
        ).fetchall()

        formatted_roles: dict[int, dict] = {}
        for row in roles:
            role_id = row.role_id
            if role_id not in formatted_roles:
                formatted_roles[role_id] = {
                    "role_id": role_id,
                    "role_name": row.role_name,
                    "description": row.description,
                    "is_system_role": bool(row.is_system_role),
                    "permissions": {},
                }

            # Add permission entry if a module_name is present
            if row.module_name:
                formatted_roles[role_id]["permissions"][row.module_name] = {
                    "can_view": bool(row.can_view),
                    "can_create": bool(row.can_create),
                    "can_edit": bool(row.can_edit),
                    "can_delete": bool(row.can_delete),
                }

        # Return a plain list so the frontend can do setRoles(response.data)
        return list(formatted_roles.values())
    except Exception as e:
        error(f"Error getting roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get roles: {str(e)}")
    finally:
        session.close()


@router.post("/roles")
async def create_role(
    payload: RoleCreateRequest,
    admin_user=Depends(admin_required)
):
    """Create a new role"""
    session = Session()
    try:
        # Check if role name already exists
        existing_role = session.execute(
            text("SELECT role_id FROM roles WHERE role_name = :role_name"),
            {'role_name': payload.role_name}
        ).fetchone()

        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")

        # Create role
        result = session.execute(
            text("""
                INSERT INTO roles (role_name, description)
                VALUES (:role_name, :description)
                RETURNING role_id
            """),
            {
                'role_name': payload.role_name,
                'description': payload.description
            }
        )
        role_id = result.fetchone()[0]
        session.commit()

        return {
            'message': 'Role created successfully',
            'role_id': role_id
        }
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error creating role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")
    finally:
        session.close()


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int = Path(..., description="Role ID"),
    payload: RoleUpdateRequest = ...,
    admin_user=Depends(admin_required)
):
    """Update a role"""
    session = Session()
    try:
        role = session.execute(
            text("SELECT role_id FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()

        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        updates = []
        params = {'role_id': role_id}

        if payload.role_name is not None:
            # Check if role name already exists
            existing = session.execute(
                text("SELECT role_id FROM roles WHERE role_name = :role_name AND role_id != :role_id"),
                {'role_name': payload.role_name, 'role_id': role_id}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Role name already exists")
            updates.append("role_name = :role_name")
            params['role_name'] = payload.role_name

        if payload.description is not None:
            updates.append("description = :description")
            params['description'] = payload.description

        if updates:
            session.execute(
                text(f"UPDATE roles SET {', '.join(updates)} WHERE role_id = :role_id"),
                params
            )
            session.commit()

        return {'message': 'Role updated successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error updating role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")
    finally:
        session.close()


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int = Path(..., description="Role ID"),
    admin_user=Depends(admin_required)
):
    """Delete a role"""
    session = Session()
    try:
        role = session.execute(
            text("SELECT role_id FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()

        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Check if role is assigned to any users
        users_with_role = session.execute(
            text("SELECT COUNT(*) as count FROM user_roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()

        if users_with_role and users_with_role.count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete role: {users_with_role.count} user(s) are assigned to this role"
            )

        session.execute(
            text("DELETE FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        )
        session.commit()

        return {'message': 'Role deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error deleting role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete role: {str(e)}")
    finally:
        session.close()


# ===== Audit Logs Endpoint =====

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, description="Number of logs to return"),
    offset: int = Query(0, description="Offset for pagination"),
    admin_user=Depends(admin_required)
):
    """Get audit logs"""
    session = Session()
    try:
        logs = session.execute(
            text("""
                SELECT 
                    log_id,
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    ip_address,
                    user_agent,
                    created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {'limit': limit, 'offset': offset}
        ).fetchall()

        result = []
        for log in logs:
            result.append({
                'log_id': log.log_id,
                'user_id': log.user_id,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'created_at': str(log.created_at) if log.created_at else None
            })

        # Return a plain list so the frontend can do response.data.map(...)
        return result
    except Exception as e:
        error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")
    finally:
        session.close()


# ===== Module Management Endpoints =====

@router.get("/modules")
async def get_modules(admin_user=Depends(admin_required)):
    """Get all modules"""
    session = Session()
    try:
        # Check if modules table exists
        table_exists = session.execute(
            text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='modules'
            """)
        ).fetchone()

        # Create modules table if it doesn't exist
        if not table_exists:
            session.execute(
                text("""
                    CREATE TABLE modules (
                        module_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        module_name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            )
            session.commit()

            # Add default modules
            default_modules = [
                ('dashboard', 'Dashboard', 'Main dashboard features'),
                ('users', 'Users Management', 'User management features'),
                ('reports', 'Reports', 'Reporting features'),
                ('analytics', 'Analytics', 'Analytics features'),
                ('settings', 'Settings', 'System settings')
            ]

            for module in default_modules:
                session.execute(
                    text("""
                        INSERT INTO modules (module_name, display_name, description)
                        VALUES (:module_name, :display_name, :description)
                    """),
                    {
                        'module_name': module[0],
                        'display_name': module[1],
                        'description': module[2]
                    }
                )
            session.commit()

        # Get all modules
        modules = session.execute(
            text("""
                SELECT module_id, module_name, display_name, description, 
                       created_at, updated_at
                FROM modules
                ORDER BY module_name
            """)
        ).fetchall()

        result = []
        for module in modules:
            result.append({
                'module_id': module.module_id,
                'module_name': module.module_name,
                'display_name': module.display_name,
                'description': module.description,
                'created_at': str(module.created_at) if module.created_at else None,
                'updated_at': str(module.updated_at) if module.updated_at else None
            })

        # Return a plain list so the frontend can do setModules(response.data)
        return result
    except Exception as e:
        error(f"Error getting modules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get modules: {str(e)}")
    finally:
        session.close()


@router.post("/modules")
async def create_module(
    payload: ModuleCreateRequest,
    admin_user=Depends(admin_required)
):
    """Create a new module"""
    session = Session()
    try:
        # Validate module_name format (lowercase, underscores, alphanumeric)
        if not re.match(r'^[a-z0-9_]+$', payload.module_name):
            raise HTTPException(
                status_code=400,
                detail="Module name must contain only lowercase letters, numbers, and underscores"
            )

        # Check if module name already exists
        existing_module = session.execute(
            text("SELECT module_id FROM modules WHERE module_name = :module_name"),
            {'module_name': payload.module_name}
        ).fetchone()

        if existing_module:
            raise HTTPException(status_code=400, detail="Module name already exists")

        # Create new module
        result = session.execute(
            text("""
                INSERT INTO modules (module_name, display_name, description)
                VALUES (:module_name, :display_name, :description)
                RETURNING module_id
            """),
            {
                'module_name': payload.module_name,
                'display_name': payload.display_name,
                'description': payload.description or ''
            }
        )

        module_id = result.fetchone()[0]
        session.commit()

        return {
            'message': 'Module created successfully',
            'module_id': module_id
        }
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error creating module: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create module: {str(e)}")
    finally:
        session.close()


@router.put("/modules/{module_id}")
async def update_module(
    module_id: int = Path(..., description="Module ID"),
    payload: ModuleUpdateRequest = ...,
    admin_user=Depends(admin_required)
):
    """Update a module"""
    session = Session()
    try:
        module = session.execute(
            text("SELECT module_id FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        ).fetchone()

        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        updates = []
        params = {'module_id': module_id}

        if payload.module_name is not None:
            # Validate module_name format
            if not re.match(r'^[a-z0-9_]+$', payload.module_name):
                raise HTTPException(
                    status_code=400,
                    detail="Module name must contain only lowercase letters, numbers, and underscores"
                )
            # Check if module name already exists
            existing = session.execute(
                text("SELECT module_id FROM modules WHERE module_name = :module_name AND module_id != :module_id"),
                {'module_name': payload.module_name, 'module_id': module_id}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Module name already exists")
            updates.append("module_name = :module_name")
            params['module_name'] = payload.module_name

        if payload.display_name is not None:
            updates.append("display_name = :display_name")
            params['display_name'] = payload.display_name

        if payload.description is not None:
            updates.append("description = :description")
            params['description'] = payload.description

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            session.execute(
                text(f"UPDATE modules SET {', '.join(updates)} WHERE module_id = :module_id"),
                params
            )
            session.commit()

        return {'message': 'Module updated successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error updating module: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update module: {str(e)}")
    finally:
        session.close()


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int = Path(..., description="Module ID"),
    admin_user=Depends(admin_required)
):
    """Delete a module"""
    session = Session()
    try:
        module = session.execute(
            text("SELECT module_id FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        ).fetchone()

        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        session.execute(
            text("DELETE FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        )
        session.commit()

        return {'message': 'Module deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error deleting module: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete module: {str(e)}")
    finally:
        session.close()


# ===== Notification Endpoints =====

@router.post("/notifications")
async def create_notification(
    payload: NotificationCreateRequest,
    admin_user=Depends(admin_required)
):
    """Create a notification"""
    try:
        # Load existing notifications
        notifications = []
        if os.path.exists(NOTIFICATION_FILE_PATH):
            with open(NOTIFICATION_FILE_PATH, 'r') as f:
                notifications = json.load(f)

        # Create new notification
        notification = {
            'id': len(notifications) + 1,
            'title': payload.title,
            'message': payload.message,
            'type': payload.notification_type,
            'target_user_id': payload.target_user_id,
            'created_by': admin_user.user_id,
            'created_at': datetime.now().isoformat(),
            'dismissed': False
        }

        notifications.append(notification)

        # Save notifications
        with open(NOTIFICATION_FILE_PATH, 'w') as f:
            json.dump(notifications, f, indent=2)

        return {
            'message': 'Notification created successfully',
            'notification_id': notification['id']
        }
    except Exception as e:
        error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@router.get("/notifications")
async def get_notifications(
    target_user_id: Optional[int] = Query(None, description="Filter by target user ID"),
    admin_user=Depends(admin_required)
):
    """Get all notifications"""
    try:
        if not os.path.exists(NOTIFICATION_FILE_PATH):
            return {'notifications': []}

        with open(NOTIFICATION_FILE_PATH, 'r') as f:
            notifications = json.load(f)

        # Filter by target_user_id if provided
        if target_user_id is not None:
            notifications = [n for n in notifications if n.get('target_user_id') == target_user_id]

        # Filter out dismissed notifications
        notifications = [n for n in notifications if not n.get('dismissed', False)]

        return {'notifications': notifications}
    except Exception as e:
        error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")


@router.post("/notifications/dismiss")
async def dismiss_notification(
    payload: NotificationDismissRequest,
    admin_user=Depends(admin_required)
):
    """Dismiss a notification"""
    try:
        if not os.path.exists(NOTIFICATION_FILE_PATH):
            raise HTTPException(status_code=404, detail="Notification not found")

        with open(NOTIFICATION_FILE_PATH, 'r') as f:
            notifications = json.load(f)

        # Find and dismiss notification
        found = False
        for notification in notifications:
            if notification['id'] == payload.notification_id:
                notification['dismissed'] = True
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Save notifications
        with open(NOTIFICATION_FILE_PATH, 'w') as f:
            json.dump(notifications, f, indent=2)

        return {'message': 'Notification dismissed successfully'}
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error dismissing notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to dismiss notification: {str(e)}")

