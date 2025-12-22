"""
Database table name utilities for handling PostgreSQL case sensitivity.

PostgreSQL is case-sensitive for quoted identifiers:
- Unquoted identifiers are lowercased: CREATE TABLE DMS_MAPR → stored as 'dms_mapr'
- Quoted identifiers preserve case: CREATE TABLE "DMS_MAPR" → stored as 'DMS_MAPR'

This module provides utilities to detect and format table names correctly
for both PostgreSQL and Oracle.
"""

import builtins
import os


def _detect_db_type(connection):
    """Detect database type from connection"""
    if connection is None:
        # Fallback to environment variable
        db_type_env = os.getenv("DB_TYPE", "ORACLE").upper()
        return "POSTGRESQL" if db_type_env == "POSTGRESQL" else "ORACLE"
    
    connection_type = builtins.type(connection)
    module_name = connection_type.__module__
    class_name = connection_type.__name__
    
    # Check module name first (most reliable)
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    elif "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    
    # Check class name as fallback
    if "psycopg" in class_name.lower() or "postgres" in class_name.lower():
        return "POSTGRESQL"
    elif "oracle" in class_name.lower():
        return "ORACLE"
    
    # Last resort: check environment variable
    db_type_env = os.getenv("DB_TYPE", "ORACLE").upper()
    if db_type_env == "POSTGRESQL":
        return "POSTGRESQL"
    
    # Default fallback to Oracle
    return "ORACLE"


def get_postgresql_table_name(cursor, schema_name: str, table_name: str) -> str:
    """
    Get the actual table name as stored in PostgreSQL.
    PostgreSQL is case-sensitive for quoted identifiers, so we need to check
    how the table was actually created (with or without quotes).
    
    This function handles both cases:
    - Tables created without quotes: stored as lowercase (e.g., 'dms_mapr')
    - Tables created with quotes: stored with preserved case (e.g., 'DMS_MAPR')
    
    Args:
        cursor: Database cursor
        schema_name: Schema name (lowercase for PostgreSQL)
        table_name: Base table name (e.g., 'DMS_MAPR')
        
    Returns:
        Actual table name as stored in PostgreSQL (could be 'dms_mapr' or 'DMS_MAPR')
    """
    try:
        # Try to find the table in information_schema
        # Check both lowercase (unquoted) and uppercase (quoted) versions
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_name IN (%s, %s)
            LIMIT 1
        """, (schema_name, table_name.lower(), table_name.upper()))
        
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the actual table name as stored
        
        # Fallback: try case-insensitive search with schema match
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE LOWER(table_schema) = LOWER(%s)
              AND LOWER(table_name) = LOWER(%s)
            LIMIT 1
        """, (schema_name, table_name))
        
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the actual table name as stored
    except Exception:
        # If detection fails, fall back to lowercase (most common case)
        pass
    
    # Default to lowercase (most common case for unquoted identifiers)
    # This handles cases where:
    # 1. Table doesn't exist yet (shouldn't happen in normal flow, but safe fallback)
    # 2. Schema/table detection fails for any reason
    return table_name.lower()


def format_table_name(cursor, schema_name: str, table_name: str, db_type: str = None) -> str:
    """
    Format table name with schema prefix, handling PostgreSQL case sensitivity.
    
    Args:
        cursor: Database cursor
        schema_name: Schema name
        table_name: Base table name (e.g., 'DMS_MAPR')
        db_type: Database type ('POSTGRESQL' or 'ORACLE'). If None, auto-detects.
        
    Returns:
        Formatted table name with schema prefix (e.g., 'trg.dms_mapr' or 'TRG.DMS_MAPR')
    """
    if db_type is None:
        # Try to detect from cursor connection
        try:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
        except Exception:
            db_type = "ORACLE"  # Default fallback
    
    if db_type == "POSTGRESQL":
        schema_lower = schema_name.lower()
        # Detect actual table name format
        actual_table_name = get_postgresql_table_name(cursor, schema_lower, table_name)
        # Quote if uppercase (was created with quotes)
        if actual_table_name != actual_table_name.lower():
            return f'{schema_lower}."{actual_table_name}"'
        else:
            return f'{schema_lower}.{actual_table_name}'
    else:
        # Oracle: case-insensitive, use uppercase convention
        return f'{schema_name}.{table_name}'


def detect_db_type(connection):
    """Public wrapper around internal DB type detection."""
    return _detect_db_type(connection)


def get_metadata_table_refs(cursor, schema_name: str, db_type: str = None):
    """
    Get formatted table references for common metadata tables.
    Returns a dictionary with table references for: DMS_MAPR, DMS_MAPRDTL, DMS_JOB,
    DMS_JOBDTL, DMS_PARAMS, DMS_MAPRSQL, DMS_JOBFLW, etc.
    
    Args:
        cursor: Database cursor
        schema_name: Schema name
        db_type: Database type ('POSTGRESQL' or 'ORACLE'). If None, auto-detects.
        
    Returns:
        Dictionary with table name keys and formatted references as values
    """
    if db_type is None:
        try:
            connection = cursor.connection
            db_type = _detect_db_type(connection)
        except Exception:
            db_type = "ORACLE"
    
    common_tables = [
        'DMS_MAPR', 'DMS_MAPRDTL', 'DMS_JOB', 'DMS_JOBDTL',
        'DMS_PARAMS', 'DMS_MAPRSQL', 'DMS_JOBFLW', 'DMS_JOBLOG',
        'DMS_JOBERR', 'DMS_PRCLOG', 'DMS_PRCREQ', 'DMS_JOBSCH',
        'DMS_MAPERR', 'DMS_DBCONDTLS',
        # Report module metadata tables
        'DMS_RPRT_DEF', 'DMS_RPRT_FLD', 'DMS_RPRT_FRML', 'DMS_RPRT_LYOT',
        'DMS_RPRT_SCHD', 'DMS_RPRT_RUN', 'DMS_RPRT_OTPT', 'DMS_RPRT_PRVW_CCH',
        # File upload execution / schedule metadata tables
        'DMS_FLUPLD_RUN', 'DMS_FLUPLD_ERR', 'DMS_FLUPLD_SCHD',
    ]
    
    refs = {}
    for table_name in common_tables:
        refs[table_name] = format_table_name(cursor, schema_name, table_name, db_type)
    
    return refs

