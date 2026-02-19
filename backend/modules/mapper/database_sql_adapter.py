"""
Database SQL adapter for multi-database support.
Provides database-specific SQL syntax abstraction.

This module handles SQL syntax differences across multiple database types:
- Oracle, PostgreSQL, MySQL, SQL Server, Sybase, Redshift, Snowflake, DB2, Hive

All SQL generation is database-agnostic - the adapter handles the differences.
"""
from typing import Dict, Any, Optional, List, Tuple
import builtins

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import warning
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import warning  # type: ignore


class DatabaseSQLAdapter:
    """
    Adapter for database-specific SQL syntax.
    Provides unified interface for generating SQL that works across all database types.
    """
    
    def __init__(self, db_type: str):
        """
        Initialize adapter for specific database type.
        
        Args:
            db_type: Database type string (e.g., 'ORACLE', 'POSTGRESQL', 'MYSQL', etc.)
        """
        self.db_type = db_type.upper() if db_type else "ORACLE"
        # Removed debug log to reduce log noise - adapter is created frequently during processing
    
    def get_parameter_placeholder(self, param_name: Optional[str] = None, position: Optional[int] = None) -> str:
        """
        Get parameter placeholder for current database.
        
        Args:
            param_name: Optional parameter name (for named parameters)
            position: Optional position (for positional parameters)
            
        Returns:
            Parameter placeholder string (e.g., '%s', ':param', '?')
        """
        if self.db_type in ["POSTGRESQL", "POSTGRES", "MYSQL", "REDSHIFT"]:
            return "%s"
        elif self.db_type == "ORACLE":
            if param_name:
                return f":{param_name}"
            return ":param"
        elif self.db_type in ["MSSQL", "SQL_SERVER", "SYBASE", "DB2"]:
            return "?"
        elif self.db_type == "SNOWFLAKE":
            if param_name:
                return f":{param_name}"
            return "?"
        elif self.db_type == "HIVE":
            return "?"
        else:
            # Default to PostgreSQL-style
            warning(f"Unknown database type {self.db_type}, using PostgreSQL-style placeholders")
            return "%s"
    
    def format_parameters(self, params: Dict[str, Any], use_named: bool = True) -> Any:
        """
        Format parameters for database-specific execution.
        
        Args:
            params: Dictionary of parameter names to values
            use_named: Whether to use named parameters (if supported)
            
        Returns:
            Formatted parameters (dict for named, tuple for positional)
        """
        if self.db_type == "ORACLE":
            # Oracle supports named parameters
            return params
        elif self.db_type in ["POSTGRESQL", "POSTGRES", "MYSQL", "REDSHIFT"]:
            # PostgreSQL/MySQL use positional parameters
            return tuple(params.values())
        elif self.db_type in ["MSSQL", "SQL_SERVER", "SYBASE", "DB2", "SNOWFLAKE", "HIVE"]:
            # These use positional parameters
            return tuple(params.values())
        else:
            # Default to tuple
            return tuple(params.values())
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp function for current database.
        
        Returns:
            SQL function name (e.g., 'SYSTIMESTAMP', 'CURRENT_TIMESTAMP', 'GETDATE()')
        """
        timestamp_map = {
            "ORACLE": "SYSTIMESTAMP",
            "POSTGRESQL": "CURRENT_TIMESTAMP",
            "POSTGRES": "CURRENT_TIMESTAMP",
            "MYSQL": "NOW()",
            "MSSQL": "GETDATE()",
            "SQL_SERVER": "GETDATE()",
            "SYBASE": "GETDATE()",
            "REDSHIFT": "CURRENT_TIMESTAMP",
            "SNOWFLAKE": "CURRENT_TIMESTAMP()",
            "DB2": "CURRENT_TIMESTAMP",
            "HIVE": "CURRENT_TIMESTAMP()"
        }
        return timestamp_map.get(self.db_type, "CURRENT_TIMESTAMP")
    
    def get_current_date(self) -> str:
        """
        Get current date function for current database.
        
        Returns:
            SQL function name (e.g., 'SYSDATE', 'CURRENT_DATE', 'GETDATE()')
        """
        date_map = {
            "ORACLE": "SYSDATE",
            "POSTGRESQL": "CURRENT_DATE",
            "POSTGRES": "CURRENT_DATE",
            "MYSQL": "CURDATE()",
            "MSSQL": "GETDATE()",
            "SQL_SERVER": "GETDATE()",
            "SYBASE": "GETDATE()",
            "REDSHIFT": "CURRENT_DATE",
            "SNOWFLAKE": "CURRENT_DATE()",
            "DB2": "CURRENT_DATE",
            "HIVE": "CURRENT_DATE()"
        }
        return date_map.get(self.db_type, "CURRENT_DATE")
    
    def get_sequence_nextval(self, sequence_name: str) -> str:
        """
        Get sequence nextval syntax for current database.
        
        Args:
            sequence_name: Sequence name (e.g., 'DW.TABLE_SEQ')
            
        Returns:
            SQL expression for next sequence value
            Note: For MySQL, returns 'DEFAULT' (uses AUTO_INCREMENT)
        """
        if self.db_type == "ORACLE":
            return f"{sequence_name}.nextval"
        elif self.db_type in ["POSTGRESQL", "POSTGRES", "REDSHIFT"]:
            return f"nextval('{sequence_name}')"
        elif self.db_type == "SNOWFLAKE":
            return f"{sequence_name}.nextval"
        elif self.db_type in ["MSSQL", "SQL_SERVER"]:
            return f"NEXT VALUE FOR {sequence_name}"
        elif self.db_type == "DB2":
            return f"NEXT VALUE FOR {sequence_name}"
        elif self.db_type == "MYSQL":
            # MySQL uses AUTO_INCREMENT, not sequences
            # Return DEFAULT to use AUTO_INCREMENT
            return "DEFAULT"
        elif self.db_type in ["SYBASE", "HIVE"]:
            # These may not support sequences - use DEFAULT or handle differently
            warning(f"Sequence support may be limited for {self.db_type}, using DEFAULT")
            return "DEFAULT"
        else:
            # Default to PostgreSQL-style
            return f"nextval('{sequence_name}')"
    
    def get_limit_clause(self, limit: int, offset: Optional[int] = None) -> str:
        """
        Get LIMIT/TOP/ROWNUM clause for current database.
        
        Args:
            limit: Number of rows to limit
            offset: Optional offset (for OFFSET/LIMIT)
            
        Returns:
            SQL clause string
        """
        if self.db_type in ["POSTGRESQL", "POSTGRES", "MYSQL", "REDSHIFT", "SNOWFLAKE"]:
            if offset is not None:
                return f"LIMIT {limit} OFFSET {offset}"
            return f"LIMIT {limit}"
        elif self.db_type == "ORACLE":
            if offset is not None:
                # Oracle 12c+ supports OFFSET/FETCH
                return f"OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
            return f"WHERE ROWNUM <= {limit}"
        elif self.db_type in ["MSSQL", "SQL_SERVER"]:
            if offset is not None:
                return f"OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
            return f"TOP {limit}"
        elif self.db_type == "SYBASE":
            if offset is not None:
                return f"LIMIT {limit} OFFSET {offset}"
            return f"TOP {limit}"
        elif self.db_type == "DB2":
            if offset is not None:
                return f"OFFSET {offset} ROWS FETCH FIRST {limit} ROWS ONLY"
            return f"FETCH FIRST {limit} ROWS ONLY"
        elif self.db_type == "HIVE":
            if offset is not None:
                return f"LIMIT {limit} OFFSET {offset}"
            return f"LIMIT {limit}"
        else:
            # Default to LIMIT
            return f"LIMIT {limit}"
    
    def format_table_name(self, schema: str, table: str, quote_if_uppercase: bool = True) -> str:
        """
        Format table name with proper quoting for current database.
        
        Args:
            schema: Schema name
            table: Table name
            quote_if_uppercase: Whether to quote if table name is uppercase (PostgreSQL)
            
        Returns:
            Formatted table name (e.g., 'schema.table', '"schema"."table"', '[schema].[table]')
            
        Note:
            For MySQL, schema represents the database name which is already selected in the connection,
            so only the table name is returned (no schema prefix).
        """
        if self.db_type == "POSTGRESQL" or self.db_type == "POSTGRES":
            schema_lower = schema.lower() if schema else 'public'
            # Check if table is uppercase (was created with quotes)
            if quote_if_uppercase and table != table.lower():
                return f'{schema_lower}."{table}"'
            return f'{schema_lower}.{table.lower()}'
        elif self.db_type == "MYSQL":
            # MySQL: database is selected in connection, so only use table name
            # Use backticks for identifier quoting (MySQL standard)
            return f'`{table}`'
        elif self.db_type in ["MSSQL", "SQL_SERVER", "SYBASE"]:
            return f'[{schema}].[{table}]'
        elif self.db_type in ["SNOWFLAKE", "DB2"]:
            return f'"{schema}"."{table}"'
        elif self.db_type == "ORACLE":
            # Oracle is case-insensitive (unless quoted)
            return f'{schema}.{table}'
        elif self.db_type in ["REDSHIFT", "HIVE"]:
            # Similar to PostgreSQL
            schema_lower = schema.lower() if schema else 'public'
            if quote_if_uppercase and table != table.lower():
                return f'{schema_lower}."{table}"'
            return f'{schema_lower}.{table.lower()}'
        else:
            # Default to unquoted
            return f'{schema}.{table}'
    
    def build_where_clause(self, conditions: Dict[str, Any]) -> Tuple[str, Any]:
        """
        Build WHERE clause with proper parameter placeholders.
        
        Args:
            conditions: Dictionary of column names to values
            
        Returns:
            Tuple of (WHERE clause string, parameters)
        """
        if not conditions:
            return "", {}
        
        where_parts = []
        params = {}
        
        for col, val in conditions.items():
            placeholder = self.get_parameter_placeholder(col)
            where_parts.append(f"{col} = {placeholder}")
            params[col] = val
        
        where_clause = " AND ".join(where_parts)
        
        # Format parameters for database
        formatted_params = self.format_parameters(params, use_named=True)
        
        return where_clause, formatted_params
    
    def build_set_clause(self, updates: Dict[str, Any]) -> Tuple[str, Any]:
        """
        Build SET clause for UPDATE statements.
        
        Args:
            updates: Dictionary of column names to values
            
        Returns:
            Tuple of (SET clause string, parameters)
        """
        if not updates:
            return "", {}
        
        set_parts = []
        params = {}
        
        for col, val in updates.items():
            placeholder = self.get_parameter_placeholder(col)
            set_parts.append(f"{col} = {placeholder}")
            params[col] = val
        
        set_clause = ", ".join(set_parts)
        
        # Format parameters for database
        formatted_params = self.format_parameters(params, use_named=True)
        
        return set_clause, formatted_params
    
    def build_values_clause(self, columns: List[str]) -> str:
        """
        Build VALUES clause for INSERT statements.
        
        Args:
            columns: List of column names
            
        Returns:
            VALUES clause string with placeholders
        """
        placeholders = []
        for col in columns:
            placeholder = self.get_parameter_placeholder(col)
            placeholders.append(placeholder)
        
        return ", ".join(placeholders)
    
    def supports_named_parameters(self) -> bool:
        """
        Check if database supports named parameters.
        
        Returns:
            True if named parameters are supported
        """
        return self.db_type in ["ORACLE", "SNOWFLAKE"]
    
    def supports_sequences(self) -> bool:
        """
        Check if database supports sequences.
        
        Returns:
            True if sequences are supported
        """
        return self.db_type not in ["MYSQL"]  # MySQL uses AUTO_INCREMENT


def detect_database_type(connection) -> str:
    """
    Enhanced database type detection supporting all database types.
    
    Args:
        connection: Database connection object
        
    Returns:
        Database type string (e.g., 'ORACLE', 'POSTGRESQL', 'MYSQL', etc.)
    """
    if connection is None:
        import os
        db_type_env = os.getenv("DB_TYPE", "ORACLE").upper()
        return db_type_env
    
    connection_type = builtins.type(connection)
    module_name = connection_type.__module__
    class_name = connection_type.__name__
    
    # Check module name first (most reliable)
    module_lower = module_name.lower()
    class_lower = class_name.lower()
    
    # PostgreSQL
    if "psycopg" in module_lower or "pg8000" in module_lower:
        return "POSTGRESQL"
    
    # Oracle
    if "oracledb" in module_lower or "cx_oracle" in module_lower:
        return "ORACLE"
    
    # MySQL
    if "mysql" in module_lower or "mysql.connector" in module_lower:
        return "MYSQL"
    
    # SQL Server / MSSQL
    if "pyodbc" in module_lower:
        # Try to detect SQL Server vs Sybase by connection string or query
        try:
            cursor = connection.cursor()
            # SQL Server specific query
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()
            cursor.close()
            if version and "SQL Server" in str(version[0]):
                return "SQL_SERVER"
            elif version and "Sybase" in str(version[0]):
                return "SYBASE"
            # Default to SQL_SERVER for pyodbc if can't determine
            return "SQL_SERVER"
        except Exception:
            # If query fails, default to SQL_SERVER
            return "SQL_SERVER"
    
    # Snowflake
    if "snowflake" in module_lower or "snowflake.connector" in module_lower:
        return "SNOWFLAKE"
    
    # DB2
    if "ibm_db" in module_lower:
        return "DB2"
    
    # Hive
    if "pyhive" in module_lower or "hive" in module_lower:
        return "HIVE"
    
    # Redshift (uses psycopg2, so check connection string or query)
    if "psycopg" in module_lower:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            cursor.close()
            if version and "Redshift" in str(version[0]):
                return "REDSHIFT"
        except Exception:
            pass
    
    # Fallback: Try database-specific queries
    try:
        cursor = connection.cursor()
        
        # Try Oracle
        try:
            cursor.execute("SELECT 1 FROM dual")
            cursor.fetchone()
            cursor.close()
            return "ORACLE"
        except Exception:
            pass
        
        # Try PostgreSQL/MySQL
        try:
            cursor.execute("SELECT version()")
            cursor.fetchone()
            cursor.close()
            # Could be PostgreSQL or MySQL - check version string
            # For now, default to PostgreSQL
            return "POSTGRESQL"
        except Exception:
            pass
        
        # Try SQL Server
        try:
            cursor.execute("SELECT @@VERSION")
            cursor.fetchone()
            cursor.close()
            return "SQL_SERVER"
        except Exception:
            pass
        
        cursor.close()
    except Exception:
        pass
    
    # Last resort: check environment variable
    import os
    db_type_env = os.getenv("DB_TYPE", "ORACLE").upper()
    
    # Map common aliases
    if db_type_env in ["POSTGRES", "POSTGRESQL"]:
        return "POSTGRESQL"
    elif db_type_env in ["MSSQL", "SQL_SERVER", "SQLSERVER"]:
        return "SQL_SERVER"
    
    return db_type_env if db_type_env else "ORACLE"


def create_adapter(connection) -> DatabaseSQLAdapter:
    """
    Create database adapter from connection object.
    
    Args:
        connection: Database connection object
        
    Returns:
        DatabaseSQLAdapter instance configured for the connection's database type
    """
    db_type = detect_database_type(connection)
    return DatabaseSQLAdapter(db_type)


def create_adapter_from_type(db_type: str) -> DatabaseSQLAdapter:
    """
    Create database adapter from database type string.
    
    Args:
        db_type: Database type string (e.g., 'ORACLE', 'POSTGRESQL')
        
    Returns:
        DatabaseSQLAdapter instance
    """
    return DatabaseSQLAdapter(db_type)

