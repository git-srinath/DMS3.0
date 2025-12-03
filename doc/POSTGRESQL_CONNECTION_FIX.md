# PostgreSQL Connection Fix Guide

## Issue
The error `role "DMS" does not exist` indicates that PostgreSQL is trying to connect with a user that doesn't exist in your PostgreSQL database.

## Solution

### 1. Check Your .env File

Make sure your `.env` file has the correct PostgreSQL user credentials:

```env
# Database Type
DB_TYPE=POSTGRESQL

# PostgreSQL Connection - USE YOUR ACTUAL POSTGRESQL USERNAME
DB_HOST=192.168.116.128
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_actual_postgresql_username    # <-- This should NOT be "DMS"
DB_PASSWORD=your_password

# Schema Configuration
DMS_SCHEMA=public
CDR_SCHEMA=cdr
```

### 2. Common PostgreSQL Usernames

- Default superuser: `postgres`
- Or your custom created user (e.g., `dms_user`, `dmsadmin`, etc.)

**Important**: The `DB_USER` should be a valid PostgreSQL user that:
- Exists in your PostgreSQL database
- Has permissions to access the `DMS_PARAMS` table and other metadata tables
- Has permissions on the schema specified in `DMS_SCHEMA`

### 3. Verify PostgreSQL User Exists

Connect to PostgreSQL and check:

```sql
-- Connect to PostgreSQL
psql -U postgres -h 192.168.116.128

-- List all users
\du

-- Or query
SELECT usename FROM pg_user;
```

### 4. Create User if Needed

If you need to create a new user:

```sql
-- Connect as postgres superuser
psql -U postgres -h 192.168.116.128

-- Create user
CREATE USER dms_user WITH PASSWORD 'your_password';

-- Grant permissions on database
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO dms_user;

-- Grant permissions on schema (if using public schema)
GRANT ALL PRIVILEGES ON SCHEMA public TO dms_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dms_user;

-- Or if using custom schema
GRANT ALL PRIVILEGES ON SCHEMA dms_metadata TO dms_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dms_metadata TO dms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dms_metadata TO dms_user;
```

### 5. Update .env File

After verifying/creating the user, update your `.env`:

```env
DB_USER=dms_user  # or postgres, or whatever user you created
DB_PASSWORD=your_password
```

### 6. Test Connection

You can test the connection manually:

```python
import psycopg2
conn = psycopg2.connect(
    host="192.168.116.128",
    port=5432,
    database="your_database_name",
    user="your_actual_username",  # Use the correct username here
    password="your_password"
)
print("Connection successful!")
conn.close()
```

## Additional Fixes Applied

I've also fixed SQL syntax issues in:
- `get_error_message()` - Now supports PostgreSQL `LIMIT` syntax
- `get_error_messages_list()` - Now supports PostgreSQL parameter binding (`%s`)

## Summary

The main issue is that `DB_USER` in your `.env` file is set to "DMS", but that user doesn't exist in PostgreSQL. Update it to a valid PostgreSQL username (like `postgres` or a user you created).

