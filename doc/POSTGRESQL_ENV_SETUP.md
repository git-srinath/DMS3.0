# PostgreSQL Metadata Database - .env Configuration Guide

## Required .env Changes for PostgreSQL

Since you're using PostgreSQL for metadata, you need to update your `.env` file with PostgreSQL-specific settings. Here are the required changes:

### 1. Database Type Configuration

Add a new variable to specify the database type:

```env
# Database type: ORACLE or POSTGRESQL
DB_TYPE=POSTGRESQL
```

### 2. PostgreSQL Connection Settings

Replace the Oracle-specific settings with PostgreSQL equivalents:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: PostgreSQL connection string (alternative to above)
# If provided, this will be used instead of individual components
# Format: postgresql://user:password@host:port/database
# DB_CONNECTION_STRING=postgresql://user:password@localhost:5432/database_name
```

### 3. Schema Configuration (PostgreSQL)

For PostgreSQL, schemas work similarly to Oracle:

```env
# DMS_SCHEMA: Schema containing metadata tables (PostgreSQL schema)
# Example: DMS_SCHEMA=public (or your custom schema name)
DMS_SCHEMA=public

# CDR_SCHEMA: Schema containing actual data tables
# Example: CDR_SCHEMA=cdr
CDR_SCHEMA=cdr
```

**Note**: In PostgreSQL, if you don't specify a schema, it defaults to `public`. You can use `public` or create a custom schema like `dms_metadata`.

### 4. Complete .env Example for PostgreSQL

```env
# =============================================================================
# Database Type
# =============================================================================
DB_TYPE=POSTGRESQL

# =============================================================================
# PostgreSQL Database Configuration
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dms_metadata
DB_USER=dms_user
DB_PASSWORD=your_secure_password

# Optional: Use connection string instead
# DB_CONNECTION_STRING=postgresql://dms_user:password@localhost:5432/dms_metadata

# =============================================================================
# PostgreSQL Schema Configuration
# =============================================================================
DMS_SCHEMA=public
CDR_SCHEMA=cdr

# =============================================================================
# Application Configuration
# =============================================================================
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here_change_this_in_production

# =============================================================================
# Security Configuration
# =============================================================================
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## Important Notes

1. **DB_NAME vs DB_SID**: PostgreSQL uses `DB_NAME` (database name) instead of Oracle's `DB_SID` or `DB_SERVICE`.

2. **Default Port**: PostgreSQL default port is `5432` (Oracle uses `1521`).

3. **Schema Names**: 
   - PostgreSQL schemas are similar to Oracle schemas
   - Default schema is `public`
   - You can use `public` or create a custom schema

4. **Connection String**: You can use either:
   - Individual components (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
   - OR a connection string (DB_CONNECTION_STRING)

## Next Steps

After updating your `.env` file, you'll also need to:

1. **Install PostgreSQL driver**: Add `psycopg2` or `psycopg2-binary` to `requirements.txt`
2. **Update dbconnect.py**: The connection code needs to support PostgreSQL (I can help with this)
3. **Test the connection**: Verify the application can connect to your PostgreSQL database

## Verification

To verify your PostgreSQL connection works, you can test with:

```python
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="dms_metadata",
    user="dms_user",
    password="your_password"
)
print("Connection successful!")
conn.close()
```

