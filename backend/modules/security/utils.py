from sqlalchemy import text

# Define the modules that can be toggled for end users.
# Other groups (Essentials, Admin) remain universally available.
AVAILABLE_MODULES = [
    {
        'key': 'manage_sql',
        'title': 'Manage SQL',
        'description': 'Create and Edit SQL queries.',
        'path': '/manage_sql',
        'group': 'data_management',
    },
    {
        'key': 'data_mapper',
        'title': 'Data Mapper',
        'description': 'Map and Transform Data Elements.',
        'path': '/mapper_module',
        'group': 'data_management',
    },
    {
        'key': 'jobs',
        'title': 'Jobs',
        'description': 'Schedule, Manage and Monitor Jobs.',
        'path': '/jobs',
        'group': 'data_management',
    },
    {
        'key': 'job_status_and_logs',
        'title': 'Jobs and Status',
        'description': 'Track and Manage Jobs.',
        'path': '/job_status_and_logs',
        'group': 'data_management',
    },
    {
        'key': 'dashboard',
        'title': 'Dashboard',
        'description': 'Job Summary and Performance.',
        'path': '/dashboard',
        'group': 'report_management',
    },
    {
        'key': 'reports',
        'title': 'Reports',
        'description': 'Define report mappings and preview outputs.',
        'path': '/reports',
        'group': 'report_management',
    },
]

AVAILABLE_MODULE_KEYS = {module['key'] for module in AVAILABLE_MODULES}


def ensure_user_module_table(session):
    """
    Creates the user_module_access table if it is not present.
    """
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS user_module_access (
                access_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_key TEXT NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1,
                assigned_by INTEGER,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, module_key),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )
    )


def get_user_module_states(session, user_id):
    """
    Returns a list of available modules with an enabled flag for the given user.
    Missing entries default to enabled (True) to avoid locking out existing users.
    """
    ensure_user_module_table(session)

    results = session.execute(
        text(
            """
            SELECT module_key, is_enabled
            FROM user_module_access
            WHERE user_id = :user_id
            """
        ),
        {'user_id': user_id},
    ).fetchall()

    state_map = {row.module_key: bool(row.is_enabled) for row in results}

    modules_with_state = []
    for module in AVAILABLE_MODULES:
        modules_with_state.append(
            {
                **module,
                'enabled': state_map.get(module['key'], True),
            }
        )

    return modules_with_state


def get_enabled_module_keys(session, user_id):
    """
    Returns the list of module keys that are enabled for the user.
    """
    modules = get_user_module_states(session, user_id)
    return [module['key'] for module in modules if module['enabled']]

