-- login_audit_log definition

CREATE TABLE login_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    target_user_id INTEGER,
    login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT NOT NULL,
    login_status TEXT NOT NULL, -- Enforce ENUM in application logic
    login_type TEXT NOT NULL, -- Enforce ENUM in application logic
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (target_user_id) REFERENCES users(user_id)
);


-- password_history definition

CREATE TABLE password_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- permission_matrix definition

CREATE TABLE permission_matrix (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    can_view INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER
    can_create INTEGER DEFAULT 0,
    can_edit INTEGER DEFAULT 0,
    can_delete INTEGER DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    UNIQUE (role_id, module_name)
);

-- roles definition

CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_system_role INTEGER DEFAULT 0 -- BOOLEAN as INTEGER
);

-- user_profiles definition

CREATE TABLE user_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT,
    department TEXT,
    position TEXT,
    profile_image_path TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- user_roles definition

CREATE TABLE user_roles (
    user_role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_by INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (assigned_by) REFERENCES users(user_id),
    UNIQUE (user_id, role_id)
);

-- users definition

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_active INTEGER DEFAULT 0, -- BOOLEAN as INTEGER (0 = FALSE, 1 = TRUE)
    account_status TEXT DEFAULT 'PENDING',
    created_by INTEGER,
    approved_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP, failed_login_attempts INTEGER DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

CREATE INDEX idx_users_username ON users(username);


