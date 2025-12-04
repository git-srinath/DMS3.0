import os

from flask import Blueprint, jsonify, request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.login.login import token_required
    from backend.modules.admin.admin import admin_required
except ImportError:  # When running Flask app.py directly inside backend
    # Try relative import first (works in both contexts)
    try:
        from ..login.login import token_required  # type: ignore
        from ..admin.admin import admin_required  # type: ignore
    except ImportError:
        # Last resort: absolute import for Flask context
        from modules.login.login import token_required  # type: ignore
        from modules.admin.admin import admin_required  # type: ignore

from .utils import (
    AVAILABLE_MODULES,
    AVAILABLE_MODULE_KEYS,
    ensure_user_module_table,
    get_user_module_states,
)

load_dotenv()

# Lazy initialization: only create engine and session when actually needed
# This prevents SQLite connection errors when importing in FastAPI context
_engine = None
_Session = None


def _get_session():
    """Lazy initialization of SQLite engine and session"""
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
        _Session = sessionmaker(bind=_engine)
    return _Session()


def _initialize_table():
    """Initialize the user_module table - only called when Flask blueprint is actually used"""
    session = _get_session()
    try:
        ensure_user_module_table(session)
        session.commit()
    finally:
        session.close()


security_bp = Blueprint('security', __name__)

# Defer initialization - don't run at module import time
# This prevents SQLite connection errors when importing in FastAPI context
# The table will be initialized on first route access instead


@security_bp.route('/modules', methods=['GET'])
@token_required
@admin_required
def list_modules(current_user_id):
    """
    Returns the modules that can be assigned to users.
    """
    # Ensure table is initialized on first access
    _initialize_table()
    return jsonify({'modules': AVAILABLE_MODULES})


@security_bp.route('/user-access/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user_access(current_user_id, user_id):
    # Ensure table is initialized on first access
    _initialize_table()
    session = _get_session()
    try:
        # Validate user exists
        user_exists = session.execute(
            text("SELECT 1 FROM users WHERE user_id = :user_id"),
            {'user_id': user_id},
        ).fetchone()

        if not user_exists:
            return jsonify({'error': 'User not found'}), 404

        modules = get_user_module_states(session, user_id)
        return jsonify({'modules': modules})
    finally:
        session.close()


@security_bp.route('/user-access/<int:user_id>', methods=['POST'])
@token_required
@admin_required
def update_user_access(current_user_id, user_id):
    # Ensure table is initialized on first access
    _initialize_table()
    payload = request.get_json() or {}
    modules_payload = payload.get('modules')

    if not isinstance(modules_payload, list):
        return jsonify({'error': 'Modules payload must be a list'}), 400

    session = _get_session()
    try:
        ensure_user_module_table(session)

        user_exists = session.execute(
            text("SELECT 1 FROM users WHERE user_id = :user_id"),
            {'user_id': user_id},
        ).fetchone()
        if not user_exists:
            return jsonify({'error': 'User not found'}), 404

        # Validate module keys
        provided_keys = {module.get('key') for module in modules_payload if 'key' in module}
        invalid_keys = provided_keys - AVAILABLE_MODULE_KEYS
        if invalid_keys:
            return jsonify({'error': f'Invalid module keys: {", ".join(sorted(invalid_keys))}'}), 400

        # Normalize modules to ensure every module has a value
        normalized_states = {}
        for module in modules_payload:
            key = module.get('key')
            if key in AVAILABLE_MODULE_KEYS:
                normalized_states[key] = bool(module.get('enabled', True))

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
                    'assigned_by': current_user_id,
                },
            )

        session.commit()
        modules = get_user_module_states(session, user_id)
        return jsonify({'message': 'User access updated successfully', 'modules': modules})
    except Exception as exc:
        session.rollback()
        return jsonify({'error': f'Failed to update access: {str(exc)}'}), 500
    finally:
        session.close()


@security_bp.route('/my-modules', methods=['GET'])
@token_required
def get_current_user_modules(current_user_id):
    # Ensure table is initialized on first access
    _initialize_table()
    session = _get_session()
    try:
        modules = get_user_module_states(session, current_user_id)
        enabled_keys = [module['key'] for module in modules if module['enabled']]
        return jsonify({'modules': modules, 'enabled_keys': enabled_keys})
    finally:
        session.close()

