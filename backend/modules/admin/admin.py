from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from modules.login.login import token_required, hash_password, generate_salt, is_valid_password
from datetime import datetime
import json
import re
from functools import wraps
from modules.license.license_manager import LicenseManager
import os.path

load_dotenv()

# Database setup
engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
Session = sessionmaker(bind=engine)

# Blueprint setup
admin_bp = Blueprint('admin', __name__)
license_manager = LicenseManager()

# Notification file path
NOTIFICATION_FILE_PATH = os.path.join('data', 'notifications.json')

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def check_admin_permission(user_id):
    session = Session()
    try:
        # Check if user has admin role
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

def admin_required(f):
    def decorated(current_user_id, *args, **kwargs):
        if not check_admin_permission(current_user_id):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(current_user_id, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user_id):
    session = Session()
    try:
        # Get all users with their roles and profiles in a single query using JOINs
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
                    'approved_by': str(user.approved_by),
                    'first_name': str(user.first_name) if user.first_name else None,
                    'last_name': str(user.last_name) if user.last_name else None,
                    'department': str(user.department) if user.department else None,
                    'position': str(user.position) if user.position else None,
                    'role_id': str(user.role_id) if user.role_id else None,
                    'role_name': str(user.role_name) if user.role_name else None
                }
            
        
        # Convert dictionary to list
        users_list = list(users_dict.values())
        return jsonify(users_list)
        
    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.args}")
        return jsonify({'error': f'Failed to retrieve users: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user_id):
    session = Session()
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate password
        if not is_valid_password(data['password']):
            return jsonify({
                'error': 'Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
            }), 400

        # Check if username or email already exists
        existing_user = session.execute(
            text("""
                SELECT user_id, username, email 
                FROM users 
                WHERE username = :username OR email = :email
            """),
            {'username': data['username'], 'email': data['email']}
        ).fetchone()

        if existing_user:
            if existing_user.username == data['username']:
                return jsonify({'error': 'Username already exists'}), 400
            if existing_user.email == data['email']:
                return jsonify({'error': 'Email already exists'}), 400

        # Check if role exists
        role = session.execute(
            text("SELECT role_id FROM roles WHERE role_id = :role_id"),
            {'role_id': data['role_id']}
        ).fetchone()

        if not role:
            return jsonify({'error': f'Invalid role ID: {data["role_id"]}'}), 400

        # Generate password hash and salt
        salt = generate_salt()
        password_hash = hash_password(data['password'], salt)

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
                    'username': data['username'],
                    'email': data['email'],
                    'password_hash': password_hash,
                    'salt': salt,
                    'created_by': current_user_id,
                    'is_active': data.get('is_active', True),
                    'change_password': data.get('change_password', False)
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
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'department': data.get('department'),
                    'position': data.get('position')
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
                    'role_id': data['role_id'],
                    'assigned_by': current_user_id
                }
            )

            session.commit()
            return jsonify({
                'message': 'User created successfully',
                'user_id': user_id
            }), 201

        except Exception as e:
            session.rollback()
            print(f"Database error in create_user: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        print(f"Error in create_user: {str(e)}")
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@token_required
@admin_required
def approve_user(current_user_id, user_id):
    try:
        data = request.get_json()
        action = data.get('action', 'approve').lower()
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Invalid action. Must be "approve" or "reject"'}), 400
            
        session = Session()
        
        # Check if user exists and is pending
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id AND account_status = 'PENDING'"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found or not in pending status'}), 404
            
        # Check if approver is different from creator
        if user.created_by == current_user_id:
            return jsonify({'error': 'Creator cannot approve or reject their own user creation'}), 403
        
        if action == 'approve':
            # Approve user
            session.execute(
                text("""
                    UPDATE users 
                    SET account_status = 'ACTIVE',
                        is_active = 1,
                        approved_by = :approved_by
                    WHERE user_id = :user_id
                """),
                {
                    'user_id': user_id,
                    'approved_by': current_user_id
                }
            )
            message = 'User approved successfully'
        else:
            # Reject user
            session.execute(
                text("""
                    UPDATE users 
                    SET account_status = 'REJECTED',
                        approved_by = :approved_by
                    WHERE user_id = :user_id
                """),
                {
                    'user_id': user_id,
                    'approved_by': current_user_id
                }
            )
            message = 'User rejected successfully'
        
        session.commit()
        return jsonify({'message': message})
        
    except Exception as e:
        print(f"Error approving user: {str(e)}")
        return jsonify({'error': 'Failed to approve user'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@token_required
@admin_required
def legacy_approve_user(current_user_id, user_id):
    # For backward compatibility
    try:
        session = Session()
        
        # Check if user exists and is pending
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id AND account_status = 'PENDING'"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found or not in pending status'}), 404
            
        # Check if approver is different from creator
        if user.created_by == current_user_id:
            return jsonify({'error': 'Creator cannot approve their own user creation'}), 403
            
        # Approve user
        session.execute(
            text("""
                UPDATE users 
                SET account_status = 'ACTIVE',
                    is_active = 1,
                    approved_by = :approved_by,
                    approved_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id
            """),
            {
                'user_id': user_id,
                'approved_by': current_user_id
            }
        )
        
        session.commit()
        return jsonify({'message': 'User approved successfully'})
        
    except Exception as e:
        print(f"Error approving user: {str(e)}")
        return jsonify({'error': 'Failed to approve user'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user_id, user_id):
    session = Session()
    try:
        data = request.get_json()

        # Check if user exists
        user = session.execute(
            text("""
                SELECT u.*, up.first_name, up.last_name, up.department, up.position
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.user_id = :user_id
            """),
            {'user_id': user_id}
        ).fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Start transaction
        try:
            # Update user fields
            user_updates = {}
            
            # Handle username update
            if 'username' in data and data['username'] != user.username:
                # Check username uniqueness
                existing_username = session.execute(
                    text("""
                        SELECT user_id FROM users 
                        WHERE username = :username AND user_id != :user_id
                    """),
                    {'username': data['username'], 'user_id': user_id}
                ).fetchone()
                if existing_username:
                    return jsonify({'error': 'Username already exists'}), 400
                user_updates['username'] = data['username']

            # Handle email update
            if 'email' in data and data['email'] != user.email:
                # Check email uniqueness
                existing_email = session.execute(
                    text("""
                        SELECT user_id FROM users 
                        WHERE email = :email AND user_id != :user_id
                    """),
                    {'email': data['email'], 'user_id': user_id}
                ).fetchone()
                if existing_email:
                    return jsonify({'error': 'Email already exists'}), 400
                user_updates['email'] = data['email']

            # Handle is_active update
            if 'is_active' in data:
                user_updates['is_active'] = 1 if data['is_active'] else 0
                
            # Handle change_password update
            if 'change_password' in data:
                user_updates['change_password'] = 1 if data['change_password'] else 0

            # Update user table if there are changes
            if user_updates:
                update_query = "UPDATE users SET " + \
                             ", ".join(f"{k} = :{k}" for k in user_updates.keys()) + \
                             " WHERE user_id = :user_id"
                user_updates['user_id'] = user_id
                session.execute(text(update_query), user_updates)

            # Update profile fields
            profile_updates = {}
            profile_fields = ['first_name', 'last_name', 'department', 'position']
            for field in profile_fields:
                if field in data:
                    profile_updates[field] = data[field]

            if profile_updates:
                if user.first_name is None:  # Profile doesn't exist
                    profile_updates['user_id'] = user_id
                    session.execute(
                        text("""
                            INSERT INTO user_profiles (
                                user_id, first_name, last_name, department, position
                            )
                            VALUES (
                                :user_id, :first_name, :last_name, :department, :position
                            )
                        """),
                        profile_updates
                    )
                else:  # Profile exists, update it
                    update_query = "UPDATE user_profiles SET " + \
                                 ", ".join(f"{k} = :{k}" for k in profile_updates.keys()) + \
                                 " WHERE user_id = :user_id"
                    profile_updates['user_id'] = user_id
                    session.execute(text(update_query), profile_updates)

            # Update role if provided
            if 'role_id' in data:
                # Check if role exists
                role = session.execute(
                    text("SELECT role_id FROM roles WHERE role_id = :role_id"),
                    {'role_id': data['role_id']}
                ).fetchone()

                if not role:
                    return jsonify({'error': f'Invalid role ID: {data["role_id"]}'}), 400

                # Remove existing roles
                session.execute(
                    text("DELETE FROM user_roles WHERE user_id = :user_id"),
                    {'user_id': user_id}
                )

                # Add new role
                session.execute(
                    text("""
                        INSERT INTO user_roles (user_id, role_id, assigned_by)
                        VALUES (:user_id, :role_id, :assigned_by)
                    """),
                    {
                        'user_id': user_id,
                        'role_id': data['role_id'],
                        'assigned_by': current_user_id
                    }
                )

            session.commit()
            return jsonify({'message': 'User updated successfully'})

        except Exception as e:
            session.rollback()
            print(f"Database error in update_user: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        print(f"Error in update_user: {str(e)}")
        return jsonify({'error': f'Failed to update user: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@token_required
@admin_required
def change_user_status(current_user_id, user_id):
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({'error': 'is_active status is required'}), 400
            
        session = Session()
        
        # Check if user exists
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Update user status
        session.execute(
            text("UPDATE users SET is_active = :is_active WHERE user_id = :user_id"),
            {'is_active': 1 if is_active else 0, 'user_id': user_id}
        )
        
        session.commit()
        return jsonify({'message': f"User {'activated' if is_active else 'deactivated'} successfully"})
        
    except Exception as e:
        print(f"Error changing user status: {str(e)}")
        return jsonify({'error': 'Failed to change user status'}), 500
    finally:
        session.close()

@admin_bp.route('/pending-approvals', methods=['GET'])
@token_required
@admin_required
def get_pending_approvals(current_user_id):
    try:
        session = Session()
        pending_users = session.execute(
            text("""
                SELECT u.*, up.first_name, up.last_name, 
                       creator.username as creator_username,
                       GROUP_CONCAT(r.role_name) as roles
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                LEFT JOIN users creator ON u.created_by = creator.user_id
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.role_id
                WHERE u.account_status = 'PENDING'
                GROUP BY u.user_id
            """)
        ).fetchall()
        
        result = []
        for user in pending_users:
            user_dict = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'account_status': user.account_status,
                'created_at': str(user.created_at) if user.created_at else None,
                'created_by': user.creator_username,
                'approved_by': user.approved_by,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'creator_username': user.creator_username,
                'roles': user.roles.split(',') if user.roles else []
            }
            result.append(user_dict)
            
        return jsonify(result)
    except Exception as e:
        print(f"Error getting pending approvals: {str(e)}")
        return jsonify({'error': 'Failed to retrieve pending approvals'}), 500
    finally:
        session.close()

@admin_bp.route('/roles', methods=['GET'])
@token_required
@admin_required
def get_roles(current_user_id):
    try:
        session = Session()
        # Get roles with permissions in a single query using LEFT JOIN
        roles = session.execute(
            text("""
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
            """)
        ).fetchall()
        
        # Process the results to format roles with their permissions
        formatted_roles = {}
        for row in roles:
            role_id = row.role_id
            if role_id not in formatted_roles:
                formatted_roles[role_id] = {
                    'role_id': role_id,
                    'role_name': row.role_name,
                    'description': row.description,
                    'is_system_role': bool(row.is_system_role),
                    'permissions': {}
                }
            
            # Add permission if module_name exists
            if row.module_name:
                formatted_roles[role_id]['permissions'][row.module_name] = {
                    'can_view': bool(row.can_view),
                    'can_create': bool(row.can_create),
                    'can_edit': bool(row.can_edit),
                    'can_delete': bool(row.can_delete)
                }
        
        # Convert dictionary to list
        result = list(formatted_roles.values())
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting roles: {str(e)}")
        return jsonify({'error': 'Failed to retrieve roles'}), 500
    finally:
        session.close()

@admin_bp.route('/roles', methods=['POST'])
@token_required
@admin_required
def create_role(current_user_id):
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('role_name'):
            return jsonify({'error': 'Role name is required'}), 400
            
        session = Session()
        
        # Check if role name already exists
        existing_role = session.execute(
            text("SELECT role_id FROM roles WHERE role_name = :role_name"),
            {'role_name': data['role_name']}
        ).fetchone()
        
        if existing_role:
            return jsonify({'error': 'Role name already exists'}), 400
            
        # Create new role
        result = session.execute(
            text("""
                INSERT INTO roles (role_name, description, is_system_role)
                VALUES (:role_name, :description, :is_system_role)
                RETURNING role_id
            """),
            {
                'role_name': data['role_name'],
                'description': data.get('description'),
                'is_system_role': data.get('is_system_role', 0)
            }
        )
        
        role_id = result.fetchone()[0]

        # Handle permissions if provided
        if 'permissions' in data:
            for module_name, permissions in data['permissions'].items():
                session.execute(
                    text("""
                        INSERT INTO permission_matrix 
                        (role_id, module_name, can_view, can_create, can_edit, can_delete)
                        VALUES 
                        (:role_id, :module_name, :can_view, :can_create, :can_edit, :can_delete)
                    """),
                    {
                        'role_id': role_id,
                        'module_name': module_name,
                        'can_view': 1 if permissions.get('can_view', False) else 0,
                        'can_create': 1 if permissions.get('can_create', False) else 0,
                        'can_edit': 1 if permissions.get('can_edit', False) else 0,
                        'can_delete': 1 if permissions.get('can_delete', False) else 0
                    }
                )
        
        session.commit()
        
        return jsonify({
            'message': 'Role created successfully',
            'role_id': role_id
        }), 201
        
    except Exception as e:
        print(f"Error creating role: {str(e)}")
        return jsonify({'error': 'Failed to create role'}), 500
    finally:
        session.close()

@admin_bp.route('/roles/<int:role_id>', methods=['PUT'])
@token_required
@admin_required
def update_role(current_user_id, role_id):
    try:
        data = request.get_json()
        session = Session()
        
        # Check if role exists
        role = session.execute(
            text("SELECT * FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()
        
        if not role:
            return jsonify({'error': 'Role not found'}), 404
            
        # Check if role is a system role
        if role.is_system_role:
            return jsonify({'error': 'Cannot modify system roles'}), 403
            
        # Validate role name uniqueness if being updated
        if 'role_name' in data and data['role_name'] != role.role_name:
            existing_role = session.execute(
                text("SELECT role_id FROM roles WHERE role_name = :role_name AND role_id != :role_id"),
                {'role_name': data['role_name'], 'role_id': role_id}
            ).fetchone()
            
            if existing_role:
                return jsonify({'error': 'Role name already exists'}), 400
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_params = {'role_id': role_id}
        
        allowed_fields = ['role_name', 'description']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = :{field}")
                update_params[field] = data[field]
        
        if update_fields:
            update_query = f"""
                UPDATE roles 
                SET {', '.join(update_fields)}
                WHERE role_id = :role_id
            """
            session.execute(text(update_query), update_params)

        # Handle permissions update if provided
        if 'permissions' in data:
            # First delete existing permissions for this role
            session.execute(
                text("DELETE FROM permission_matrix WHERE role_id = :role_id"),
                {'role_id': role_id}
            )
            
            # Insert new permissions
            for module_name, permissions in data['permissions'].items():
                session.execute(
                    text("""
                        INSERT INTO permission_matrix 
                        (role_id, module_name, can_view, can_create, can_edit, can_delete)
                        VALUES 
                        (:role_id, :module_name, :can_view, :can_create, :can_edit, :can_delete)
                    """),
                    {
                        'role_id': role_id,
                        'module_name': module_name,
                        'can_view': 1 if permissions.get('can_view', False) else 0,
                        'can_create': 1 if permissions.get('can_create', False) else 0,
                        'can_edit': 1 if permissions.get('can_edit', False) else 0,
                        'can_delete': 1 if permissions.get('can_delete', False) else 0
                    }
                )
        
        session.commit()
        
        return jsonify({'message': 'Role updated successfully'})
        
    except Exception as e:
        print(f"Error updating role: {str(e)}")
        return jsonify({'error': 'Failed to update role'}), 500
    finally:
        session.close()

@admin_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_role(current_user_id, role_id):
    try:
        session = Session()
        
        # Check if role exists
        role = session.execute(
            text("SELECT * FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()
        
        if not role:
            return jsonify({'error': 'Role not found'}), 404
            
        # Check if role is a system role
        if role.is_system_role:
            return jsonify({'error': 'Cannot delete system roles'}), 403
            
        # Check if role is assigned to any users
        users_with_role = session.execute(
            text("SELECT COUNT(*) as count FROM user_roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        ).fetchone()
        
        if users_with_role.count > 0:
            return jsonify({'error': 'Cannot delete role that is assigned to users'}), 400
            
        # Delete the role
        session.execute(
            text("DELETE FROM roles WHERE role_id = :role_id"),
            {'role_id': role_id}
        )
        
        session.commit()
        return jsonify({'message': 'Role deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting role: {str(e)}")
        return jsonify({'error': 'Failed to delete role'}), 500
    finally:
        session.close()

@admin_bp.route('/audit-logs', methods=['GET'])
@token_required
@admin_required
def get_audit_logs(current_user_id):
    try:
        session = Session()
        logs = session.execute(
            text("""
                SELECT l.*, u.username
                FROM login_audit_log l
                JOIN users u ON l.user_id = u.user_id
                ORDER BY login_timestamp DESC
                LIMIT 50
            """)
        ).fetchall()
        
        # Convert SQLAlchemy Row objects to dictionaries properly
        logs_dict = []
        for log in logs:
            log_dict = {
                'log_id': log.log_id,
                'user_id': log.user_id,
                'login_timestamp': str(log.login_timestamp) if log.login_timestamp else None,
                'ip_address': log.ip_address,
                'login_status': log.login_status,
                'login_type': log.login_type,
                'username': log.username
            }
            logs_dict.append(log_dict)
            
        return jsonify(logs_dict)
    except Exception as e:
        print(f"Error getting audit logs: {str(e)}")
        return jsonify({'error': 'Failed to retrieve audit logs'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/details', methods=['PUT'])
@token_required
@admin_required
def update_user_details(current_user_id, user_id):
    try:
        data = request.get_json()
        session = Session()
        
        # Check if user exists
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Validate email uniqueness if email is being updated
        if 'email' in data and data['email'] != user.email:
            existing_email = session.execute(
                text("SELECT user_id FROM users WHERE email = :email AND user_id != :user_id"),
                {'email': data['email'], 'user_id': user_id}
            ).fetchone()
            
            if existing_email:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Validate username uniqueness if username is being updated
        if 'username' in data and data['username'] != user.username:
            existing_username = session.execute(
                text("SELECT user_id FROM users WHERE username = :username AND user_id != :user_id"),
                {'username': data['username'], 'user_id': user_id}
            ).fetchone()
            
            if existing_username:
                return jsonify({'error': 'Username already exists'}), 400
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_params = {'user_id': user_id}
        
        allowed_fields = [
            'username', 'email', 'is_active'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = :{field}")
                update_params[field] = data[field]
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
            
        update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE user_id = :user_id
        """
        
        session.execute(text(update_query), update_params)
        session.commit()
        
        return jsonify({'message': 'User details updated successfully'})
        
    except Exception as e:
        print(f"Error updating user details: {str(e)}")
        return jsonify({'error': 'Failed to update user details'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def soft_delete_user(current_user_id, user_id):
    try:
        session = Session()
        
        # Check if user exists
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Prevent self-deletion
        if user_id == current_user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 403
            
        # Soft delete by setting is_active to false
        session.execute(
            text("""
                UPDATE users 
                SET is_active = 0,
                    account_status = 'INACTIVE'
                WHERE user_id = :user_id
            """),
            {'user_id': user_id}
        )
        
        session.commit()
        return jsonify({'message': 'User soft deleted successfully'})
        
    except Exception as e:
        print(f"Error soft deleting user: {str(e)}")
        return jsonify({'error': 'Failed to soft delete user'}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@token_required
@admin_required
def reset_user_password(current_user_id, user_id):
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('new_password'):
            return jsonify({'error': 'New password is required'}), 400
            
        # Validate password requirements
        if not is_valid_password(data['new_password']):
            return jsonify({
                'error': 'New password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
            }), 400
            
        session = Session()
        
        # Check if user exists and get their role
        user = session.execute(
            text("""
                SELECT u.*, r.role_name 
                FROM users u
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.role_id
                WHERE u.user_id = :user_id
            """),
            {'user_id': user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # If user is not admin, they can only change their own password
        if user_id != current_user_id:
            # Check if current user is admin
            admin_check = session.execute(
                text("""
                    SELECT r.role_name 
                    FROM user_roles ur 
                    JOIN roles r ON ur.role_id = r.role_id 
                    WHERE ur.user_id = :user_id 
                    AND r.role_name IN ('ADMIN', 'ADMIN')
                """),
                {'user_id': current_user_id}
            ).fetchone()
            
            if not admin_check:
                return jsonify({'error': 'Only administrators can reset other users\' passwords'}), 403
            
        # Generate new salt and hash for the new password
        new_salt = generate_salt()
        new_password_hash = hash_password(data['new_password'], new_salt)
        
        # Update password
        session.execute(
            text("""
                UPDATE users 
                SET password_hash = :password_hash,
                    salt = :salt
                WHERE user_id = :user_id
            """),
            {
                'user_id': user_id,
                'password_hash': new_password_hash,
                'salt': new_salt
            }
        )
        
        session.commit()
        return jsonify({'message': 'Password reset successfully'})
        
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        return jsonify({'error': 'Failed to reset password'}), 500
    finally:
        session.close()

@admin_bp.route('/license/activate', methods=['POST'])
def activate_license():
    data = request.get_json()
    license_key = data.get('license_key')
    
    if not license_key:
        return jsonify({
            'success': False,
            'message': 'License key is required'
        }), 400
        
    success, message = license_manager.activate_license(license_key)
    return jsonify({
        'success': success,
        'message': message
    })

@admin_bp.route('/license/deactivate', methods=['POST'])
def deactivate_license():
    success, message = license_manager.deactivate_license()
    return jsonify({
        'success': success,
        'message': message
    })

@admin_bp.route('/modules', methods=['GET'])
@token_required
@admin_required
def get_modules(current_user_id):
    """Get all modules for the system"""
    try:
        session = Session()
        
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
        
        # Format response
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
        
        return jsonify(result)
    except Exception as e:
        print(f"Error getting modules: {str(e)}")
        return jsonify({'error': 'Failed to retrieve modules'}), 500
    finally:
        session.close()

@admin_bp.route('/modules', methods=['POST'])
@token_required
@admin_required
def create_module(current_user_id):
    """Create a new module"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('module_name') or not data.get('display_name'):
            return jsonify({'error': 'Module name and display name are required'}), 400
        
        # Validate module_name format (lowercase, underscores, alphanumeric)
        if not re.match(r'^[a-z0-9_]+$', data['module_name']):
            return jsonify({'error': 'Module name must contain only lowercase letters, numbers, and underscores'}), 400
        
        session = Session()
        
        # Check if module name already exists
        existing_module = session.execute(
            text("SELECT module_id FROM modules WHERE module_name = :module_name"),
            {'module_name': data['module_name']}
        ).fetchone()
        
        if existing_module:
            return jsonify({'error': 'Module name already exists'}), 400
        
        # Create new module
        result = session.execute(
            text("""
                INSERT INTO modules (module_name, display_name, description)
                VALUES (:module_name, :display_name, :description)
                RETURNING module_id
            """),
            {
                'module_name': data['module_name'],
                'display_name': data['display_name'],
                'description': data.get('description', '')
            }
        )
        
        module_id = result.fetchone()[0]
        session.commit()
        
        return jsonify({
            'message': 'Module created successfully',
            'module_id': module_id
        }), 201
    except Exception as e:
        print(f"Error creating module: {str(e)}")
        return jsonify({'error': f'Failed to create module: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/modules/<int:module_id>', methods=['PUT'])
@token_required
@admin_required
def update_module(current_user_id, module_id):
    """Update an existing module"""
    try:
        data = request.get_json()
        session = Session()
        
        # Check if module exists
        existing_module = session.execute(
            text("SELECT * FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        ).fetchone()
        
        if not existing_module:
            return jsonify({'error': 'Module not found'}), 404
        
        # Validate required fields
        if not data.get('display_name'):
            return jsonify({'error': 'Display name is required'}), 400
        
        # Update module
        session.execute(
            text("""
                UPDATE modules 
                SET display_name = :display_name,
                    description = :description,
                    updated_at = CURRENT_TIMESTAMP
                WHERE module_id = :module_id
            """),
            {
                'module_id': module_id,
                'display_name': data['display_name'],
                'description': data.get('description', '')
            }
        )
        
        # If the module_name is being changed, need to update permission_matrix references
        if 'module_name' in data and data['module_name'] != existing_module.module_name:
            # Validate module_name format
            if not re.match(r'^[a-z0-9_]+$', data['module_name']):
                return jsonify({'error': 'Module name must contain only lowercase letters, numbers, and underscores'}), 400
                
            # Check if new module name already exists
            name_exists = session.execute(
                text("SELECT module_id FROM modules WHERE module_name = :module_name AND module_id != :module_id"),
                {'module_name': data['module_name'], 'module_id': module_id}
            ).fetchone()
            
            if name_exists:
                return jsonify({'error': 'Module name already exists'}), 400
                
            # Update module name
            session.execute(
                text("UPDATE modules SET module_name = :module_name WHERE module_id = :module_id"),
                {'module_name': data['module_name'], 'module_id': module_id}
            )
            
            # Update permission_matrix references
            session.execute(
                text("""
                    UPDATE permission_matrix
                    SET module_name = :new_module_name
                    WHERE module_name = :old_module_name
                """),
                {
                    'new_module_name': data['module_name'],
                    'old_module_name': existing_module.module_name
                }
            )
        
        session.commit()
        return jsonify({'message': 'Module updated successfully'})
    except Exception as e:
        print(f"Error updating module: {str(e)}")
        return jsonify({'error': f'Failed to update module: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/modules/<int:module_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_module(current_user_id, module_id):
    """Delete a module"""
    try:
        session = Session()
        
        # Check if module exists
        module = session.execute(
            text("SELECT * FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        ).fetchone()
        
        if not module:
            return jsonify({'error': 'Module not found'}), 404
        
        # Check if module is used in permission_matrix
        permissions_using_module = session.execute(
            text("""
                SELECT COUNT(*) as count 
                FROM permission_matrix 
                WHERE module_name = :module_name and can_view=1
            """),
            {'module_name': module.module_name}
        ).fetchone()
        
        if permissions_using_module.count > 0:
            return jsonify({
                'error': 'Cannot delete module that is being used in role permissions',
                'count': permissions_using_module.count
            }), 400
        
        # Delete module
        session.execute(
            text("DELETE FROM modules WHERE module_id = :module_id"),
            {'module_id': module_id}
        )
        
        session.commit()
        return jsonify({'message': 'Module deleted successfully'})
    except Exception as e:
        print(f"Error deleting module: {str(e)}")
        return jsonify({'error': f'Failed to delete module: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/notifications', methods=['POST'])
@token_required
@admin_required
def create_notification(current_user_id):
    session = Session()
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Create notification object
        notification = {
            'id': str(datetime.now().timestamp()),
            'title': data['title'],
            'description': data['description'],
            'created_at': str(datetime.now()),
            'created_by': current_user_id
        }
        
        # Load existing notifications or create new file
        try:
            if os.path.exists(NOTIFICATION_FILE_PATH):
                with open(NOTIFICATION_FILE_PATH, 'r') as f:
                    notifications = json.load(f)
            else:
                notifications = []
        except Exception as e:
            notifications = []
        
        # Add new notification
        notifications.append(notification)
        
        # Save to file
        with open(NOTIFICATION_FILE_PATH, 'w') as f:
            json.dump(notifications, f, indent=4)
        
        # Update all users to show notification
        session.execute(
            text("UPDATE users SET show_notification = 1")
        )
        session.commit()
        
        return jsonify({'success': True, 'notification': notification}), 201
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
        return jsonify({'error': f'Failed to create notification: {str(e)}'}), 500
    finally:
        session.close()

@admin_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user_id):
    try:
        # Load notifications from file
        if os.path.exists(NOTIFICATION_FILE_PATH):
            with open(NOTIFICATION_FILE_PATH, 'r') as f:
                notifications = json.load(f)
        else:
            notifications = []
        
        return jsonify(notifications)
    except Exception as e:
        print(f"Error retrieving notifications: {str(e)}")
        return jsonify({'error': f'Failed to retrieve notifications: {str(e)}'}), 500

@admin_bp.route('/notifications/dismiss', methods=['POST'])
@token_required
def dismiss_notification(current_user_id):
    session = Session()
    try:
        # Update user to not show notification
        session.execute(
            text("UPDATE users SET show_notification = 0 WHERE user_id = :user_id"),
            {'user_id': current_user_id}
        )
        session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Error dismissing notification: {str(e)}")
        return jsonify({'error': f'Failed to dismiss notification: {str(e)}'}), 500
    finally:
        session.close() 
