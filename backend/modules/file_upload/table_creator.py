"""
Table Creator Service for File Upload Module
Creates target tables based on column mappings.
"""
import re
from typing import List, Dict, Any, Optional
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.helper_functions import _get_table_ref
from backend.modules.logger import info, error, warning


def create_table_if_not_exists(
    connection,
    schema: str,
    table: str,
    column_mappings: List[Dict[str, Any]],
    metadata_connection=None
) -> bool:
    """
    Create target table if it doesn't exist, based on column mappings.
    
    Args:
        connection: Target database connection
        schema: Target schema name
        table: Target table name
        column_mappings: List of column mapping dictionaries from DMS_FLUPLDDTL
        metadata_connection: Metadata connection for querying DMS_PARAMS (optional)
        
    Returns:
        True if table was created, False if it already existed
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    
    try:
        # Check if table exists
        table_exists = _check_table_exists(cursor, db_type, schema, table)
        if table_exists:
            info(f"Table {schema}.{table} already exists, skipping creation")
            return False
        
        # Resolve data types from target database's DMS_PARAMS
        dtype_map = _resolve_data_types(connection, db_type, metadata_connection)
        
        # Build column definitions
        col_defs = []
        primary_keys = []
        existing_column_names = set()  # Track all column names that already exist
        
        # Process user-defined column mappings
        for col in column_mappings:
            trgclnm = col.get('trgclnm', '').strip()
            if not trgclnm:
                continue
            
            # Track existing column names (case-insensitive for comparison)
            existing_column_names.add(trgclnm.upper())
                
            trgcldtyp = col.get('trgcldtyp', '').strip()
            trgkyflg = col.get('trgkyflg', 'N')
            trgkyseq = col.get('trgkyseq')
            isrqrd = col.get('isrqrd', 'N')
            isaudit = col.get('isaudit', 'N')
            audttyp = col.get('audttyp', '').strip().upper() if col.get('audttyp') else ''
            
            # Get database-specific data type directly from DMS_PARAMS (metadata database)
            # Query DMS_PARAMS for the exact PRCD value
            db_specific_type = _get_datatype_from_params(cursor, db_type, trgcldtyp, metadata_connection) if trgcldtyp else _get_default_type(db_type)
            
            # If not found in DMS_PARAMS, try the dtype_map (cached) and then parsing
            if not db_specific_type or db_specific_type == trgcldtyp:
                db_specific_type = _resolve_single_data_type(trgcldtyp, db_type, dtype_map) if trgcldtyp else _get_default_type(db_type)
            
            # Build column definition
            col_def = f"{_quote_identifier(trgclnm, db_type)} {db_specific_type}"
            if isrqrd == 'Y':
                col_def += " NOT NULL"
            col_defs.append(col_def)
            
            # Track primary keys
            if trgkyflg == 'Y':
                primary_keys.append((trgkyseq or 0, trgclnm))
        
        # Automatically add default audit columns if not already present
        default_audit_columns = [
            ('CRTDBY', 'String100'),
            ('CRTDDT', 'Timestamp'),
            ('UPDTBY', 'String100'),
            ('UPDTDT', 'Timestamp'),
        ]
        
        for audit_col_name, audit_col_type in default_audit_columns:
            # Check if column name already exists (case-insensitive)
            if audit_col_name.upper() not in existing_column_names:
                # Get data type for audit column
                db_specific_type = _get_datatype_from_params(cursor, db_type, audit_col_type, metadata_connection)
                if not db_specific_type or db_specific_type == audit_col_type:
                    db_specific_type = _resolve_single_data_type(audit_col_type, db_type, dtype_map)
                
                # Default types for audit columns if not found
                if not db_specific_type or db_specific_type == audit_col_type:
                    if audit_col_name.endswith('DT'):  # CRTDDT, UPDTDT
                        if db_type == "ORACLE":
                            db_specific_type = "TIMESTAMP(6)"
                        elif db_type == "POSTGRESQL":
                            db_specific_type = "TIMESTAMP"
                        else:
                            db_specific_type = "TIMESTAMP"
                    else:  # CRTDBY, UPDTBY
                        if db_type == "ORACLE":
                            db_specific_type = "VARCHAR2(100)"
                        elif db_type == "POSTGRESQL":
                            db_specific_type = "VARCHAR(100)"
                        else:
                            db_specific_type = "VARCHAR(100)"
                
                # Add audit column (NOT NULL for dates, nullable for BY columns)
                col_def = f"{_quote_identifier(audit_col_name, db_type)} {db_specific_type}"
                if audit_col_name.endswith('DT'):  # CRTDDT, UPDTDT
                    col_def += " NOT NULL"
                col_defs.append(col_def)
                info(f"Automatically added audit column: {audit_col_name} ({db_specific_type})")
        
        if not col_defs:
            raise ValueError("No valid column definitions found")
        
        # Build CREATE TABLE statement
        create_sql = _build_create_table_sql(db_type, schema, table, col_defs, primary_keys)
        
        # Execute CREATE TABLE
        info(f"Creating table {schema}.{table} with SQL: {create_sql}")
        cursor.execute(create_sql)
        connection.commit()
        
        info(f"Table {schema}.{table} created successfully")
        return True
        
    except Exception as e:
        error(f"Error creating table {schema}.{table}: {str(e)}", exc_info=True)
        connection.rollback()
        raise
    finally:
        cursor.close()


def _check_table_exists(cursor, db_type: str, schema: str, table: str) -> bool:
    """Check if table exists in database."""
    try:
        if db_type == "POSTGRESQL":
            if schema:
                query = """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    )
                """
                cursor.execute(query, (schema.lower(), table.lower()))
            else:
                query = """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                """
                cursor.execute(query, (table.lower(),))
        else:  # Oracle
            if schema:
                query = """
                    SELECT COUNT(*) FROM all_tables 
                    WHERE owner = UPPER(:1) AND table_name = UPPER(:2)
                """
                cursor.execute(query, [schema, table])
            else:
                query = """
                    SELECT COUNT(*) FROM user_tables 
                    WHERE table_name = UPPER(:1)
                """
                cursor.execute(query, [table])
        
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except Exception as e:
        warning(f"Error checking table existence: {str(e)}")
        return False


def _resolve_data_types(connection, db_type: str, metadata_connection=None) -> Dict[str, str]:
    """
    Resolve generic data types to database-specific types from DMS_PARAMS.
    Queries the METADATA database's DMS_PARAMS table (not target database).
    
    Args:
        connection: Target database connection (not used, but kept for compatibility)
        db_type: Metadata database type
        metadata_connection: Metadata connection (required - DMS_PARAMS is in metadata DB)
        
    Returns:
        Dictionary mapping generic type codes to database-specific types
    """
    dtype_map = {}
    
    # DMS_PARAMS is in the metadata database, not the target database
    if not metadata_connection:
        warning("Metadata connection not provided, cannot load DMS_PARAMS mappings")
        return dtype_map
    
    metadata_cursor = None
    try:
        metadata_cursor = metadata_connection.cursor()
        metadata_db_type = _detect_db_type(metadata_connection)
        
        # Query DMS_PARAMS from metadata database
        if metadata_db_type == "POSTGRESQL":
            try:
                dms_params_ref = _get_table_ref(metadata_cursor, metadata_db_type, 'DMS_PARAMS')
                query = f"""
                    SELECT UPPER(TRIM(PRCD)), PRVAL 
                    FROM {dms_params_ref} 
                    WHERE PRTYP = 'Datatype'
                """
                metadata_cursor.execute(query)
                dtype_map = {row[0]: row[1] for row in metadata_cursor.fetchall()}
                info(f"Loaded {len(dtype_map)} data type mappings from DMS_PARAMS (metadata DB - PostgreSQL)")
            except Exception as e:
                warning(f"DMS_PARAMS not found in metadata database: {str(e)}, using defaults")
        else:  # Oracle, MySQL, etc.
            try:
                query = """
                    SELECT UPPER(TRIM(PRCD)), PRVAL 
                    FROM DMS_PARAMS 
                    WHERE PRTYP = 'Datatype'
                """
                metadata_cursor.execute(query)
                dtype_map = {row[0]: row[1] for row in metadata_cursor.fetchall()}
                info(f"Loaded {len(dtype_map)} data type mappings from DMS_PARAMS (metadata DB - Oracle)")
            except Exception as e:
                warning(f"DMS_PARAMS not found in metadata database: {str(e)}, using defaults")
        
        # Add default mappings if not found
        default_mappings = {
            'VARCHAR': 'VARCHAR(255)' if metadata_db_type == 'POSTGRESQL' else 'VARCHAR2(255)',
            'INTEGER': 'INTEGER' if metadata_db_type == 'POSTGRESQL' else 'NUMBER(10)',
            'BIGINT': 'BIGINT' if metadata_db_type == 'POSTGRESQL' else 'NUMBER(19)',
            'DECIMAL': 'DECIMAL(18,2)' if metadata_db_type == 'POSTGRESQL' else 'NUMBER(18,2)',
            'TIMESTAMP': 'TIMESTAMP' if metadata_db_type == 'POSTGRESQL' else 'TIMESTAMP(6)',
            'DATE': 'DATE',
            'TEXT': 'TEXT' if metadata_db_type == 'POSTGRESQL' else 'CLOB',
        }
        
        for key, value in default_mappings.items():
            if key not in dtype_map:
                dtype_map[key] = value
                
    except Exception as e:
        warning(f"Error resolving data types: {str(e)}, using defaults")
    finally:
        if metadata_cursor:
            metadata_cursor.close()
    
    return dtype_map


def _build_create_table_sql(
    db_type: str,
    schema: str,
    table: str,
    col_defs: List[str],
    primary_keys: List[tuple]
) -> str:
    """Build CREATE TABLE SQL statement for specific database type."""
    # Format table name
    if schema:
        if db_type == "POSTGRESQL":
            table_ref = f'"{schema.lower()}"."{table.lower()}"'
        elif db_type == "ORACLE":
            table_ref = f"{schema.upper()}.{table.upper()}"
        else:
            table_ref = f"{schema}.{table}"
    else:
        table_ref = _quote_identifier(table, db_type)
    
    # Build column definitions
    columns_sql = ",\n    ".join(col_defs)
    
    # Add primary key constraint if any
    if primary_keys:
        primary_keys.sort()  # Sort by sequence
        pk_columns = [_quote_identifier(col, db_type) for _, col in primary_keys]
        columns_sql += f",\n    PRIMARY KEY ({', '.join(pk_columns)})"
    
    # Build final SQL
    create_sql = f"CREATE TABLE {table_ref} (\n    {columns_sql}\n)"
    
    return create_sql


def _quote_identifier(name: str, db_type: str) -> str:
    """Quote identifier based on database type."""
    if db_type == "POSTGRESQL":
        return f'"{name.lower()}"'
    elif db_type == "ORACLE":
        return name.upper()
    else:
        return name


def _resolve_single_data_type(generic_type: str, db_type: str, dtype_map: Dict[str, str]) -> str:
    """
    Resolve a single generic data type to database-specific type.
    
    Handles patterns like:
    - "String20" -> "VARCHAR2(20)" for Oracle
    - "String5" -> "VARCHAR2(5)" for Oracle
    - "VARCHAR" -> "VARCHAR2(255)" for Oracle (with default size)
    - "Integer" -> "NUMBER(10)" for Oracle
    
    Args:
        generic_type: Generic type code (e.g., "String20", "VARCHAR", "Integer")
        db_type: Target database type
        dtype_map: Dictionary mapping generic types to database-specific types from DMS_PARAMS
        
    Returns:
        Database-specific type string
    """
    if not generic_type:
        return _get_default_type(db_type)
    
    generic_type_upper = generic_type.upper().strip()
    
    # First, try exact match in dtype_map
    if generic_type_upper in dtype_map:
        return dtype_map[generic_type_upper]
    
    # Try to parse patterns like "String20", "String5", "Integer10", etc.
    
    # Pattern: String20, String5, String100, etc. (with size)
    string_match = re.match(r'^STRING(\d+)$', generic_type_upper)
    if string_match:
        size = string_match.group(1)
        # Look for base "STRING" or "VARCHAR" in dtype_map
        base_type = dtype_map.get('STRING') or dtype_map.get('VARCHAR')
        if base_type:
            # Replace size in the base type (e.g., "VARCHAR2(255)" -> "VARCHAR2(20)")
            if '(' in base_type:
                base_type = re.sub(r'\(\d+\)', f'({size})', base_type)
            else:
                base_type = f"{base_type}({size})"
            return base_type
        else:
            # Fallback: construct directly
            if db_type == "ORACLE":
                return f"VARCHAR2({size})"
            elif db_type == "POSTGRESQL":
                return f"VARCHAR({size})"
            else:
                return f"VARCHAR({size})"
    
    # Pattern: String (without size) - use default size
    if generic_type_upper == "STRING":
        base_type = dtype_map.get('STRING') or dtype_map.get('VARCHAR')
        if base_type:
            return base_type
        else:
            if db_type == "ORACLE":
                return "VARCHAR2(255)"
            elif db_type == "POSTGRESQL":
                return "VARCHAR(255)"
            else:
                return "VARCHAR(255)"
    
    # Pattern: Integer, Integer10, Integer20, etc.
    integer_match = re.match(r'^INTEGER(\d+)?$', generic_type_upper)
    if integer_match:
        size = integer_match.group(1) or "10"
        base_type = dtype_map.get('INTEGER') or dtype_map.get('INT')
        if base_type:
            # For Oracle NUMBER, preserve the format
            if db_type == "ORACLE" and 'NUMBER' in base_type.upper():
                return f"NUMBER({size})"
            return base_type
        else:
            if db_type == "ORACLE":
                return f"NUMBER({size})"
            elif db_type == "POSTGRESQL":
                return "INTEGER"
            else:
                return "INTEGER"
    
    # Pattern: Decimal, Decimal18, Decimal(18,2), etc.
    decimal_match = re.match(r'^DECIMAL(?:(\d+)(?:,(\d+))?)?$', generic_type_upper)
    if decimal_match:
        precision = decimal_match.group(1) or "18"
        scale = decimal_match.group(2) or "2"
        base_type = dtype_map.get('DECIMAL') or dtype_map.get('NUMERIC')
        if base_type:
            if db_type == "ORACLE" and 'NUMBER' in base_type.upper():
                return f"NUMBER({precision},{scale})"
            return base_type
        else:
            if db_type == "ORACLE":
                return f"NUMBER({precision},{scale})"
            elif db_type == "POSTGRESQL":
                return f"DECIMAL({precision},{scale})"
            else:
                return f"DECIMAL({precision},{scale})"
    
    # Pattern: Date, Timestamp, etc. (no size)
    date_types = ['DATE', 'TIMESTAMP', 'TIME']
    if generic_type_upper in date_types:
        base_type = dtype_map.get(generic_type_upper)
        if base_type:
            return base_type
        else:
            if db_type == "ORACLE" and generic_type_upper == "TIMESTAMP":
                return "TIMESTAMP(6)"
            return generic_type_upper
    
    # If no pattern matches, try to find base type without size
    # Remove trailing digits and try again
    base_type_code = re.sub(r'\d+$', '', generic_type_upper)
    if base_type_code and base_type_code != generic_type_upper:
        base_type = dtype_map.get(base_type_code)
        if base_type:
            # Try to extract size from original
            size_match = re.search(r'(\d+)$', generic_type_upper)
            if size_match and '(' in base_type:
                size = size_match.group(1)
                base_type = re.sub(r'\(\d+\)', f'({size})', base_type)
            return base_type
    
    # Final fallback: use generic type as-is (will likely fail, but better than nothing)
    warning(f"Could not resolve data type '{generic_type}' for {db_type}, using as-is")
    return generic_type


def _get_default_type(db_type: str) -> str:
    """Get default data type for database."""
    if db_type == "ORACLE":
        return "VARCHAR2(255)"
    elif db_type == "POSTGRESQL":
        return "VARCHAR(255)"
    else:
        return "VARCHAR(255)"


def _get_datatype_from_params(cursor, db_type: str, prcd: str, metadata_connection=None) -> Optional[str]:
    """
    Query DMS_PARAMS directly for a specific PRCD value.
    This queries the METADATA database's DMS_PARAMS table (not target database).
    
    Args:
        cursor: Target database cursor (not used, but kept for compatibility)
        db_type: Metadata database type
        prcd: Parameter code (e.g., "String20", "String5", "Integer") - the exact value from user selection
        metadata_connection: Metadata database connection (required)
        
    Returns:
        PRVAL from DMS_PARAMS, or None if not found
    """
    if not prcd:
        return None
    
    # Use metadata connection to query DMS_PARAMS
    # DMS_PARAMS is in the metadata database, not the target database
    if not metadata_connection:
        warning(f"Cannot query DMS_PARAMS for '{prcd}': metadata connection not provided")
        return None
    
    metadata_cursor = None
    try:
        metadata_cursor = metadata_connection.cursor()
        metadata_db_type = _detect_db_type(metadata_connection)
        
        if metadata_db_type == "POSTGRESQL":
            dms_params_ref = _get_table_ref(metadata_cursor, metadata_db_type, 'DMS_PARAMS')
            query = f"""
                SELECT PRVAL 
                FROM {dms_params_ref} 
                WHERE PRTYP = 'Datatype' AND UPPER(TRIM(PRCD)) = UPPER(TRIM(%s))
            """
            metadata_cursor.execute(query, (prcd,))
        else:  # Oracle, MySQL, etc.
            query = """
                SELECT PRVAL 
                FROM DMS_PARAMS 
                WHERE PRTYP = 'Datatype' AND UPPER(TRIM(PRCD)) = UPPER(TRIM(:1))
            """
            metadata_cursor.execute(query, [prcd])
        
        row = metadata_cursor.fetchone()
        if row and row[0]:
            prval = row[0]
            info(f"Found data type mapping from DMS_PARAMS (metadata DB): PRCD='{prcd}' -> PRVAL='{prval}'")
            return prval
        else:
            warning(f"Data type '{prcd}' not found in DMS_PARAMS (PRTYP='Datatype') in metadata database")
            return None
            
    except Exception as e:
        warning(f"Error querying DMS_PARAMS (metadata DB) for PRCD='{prcd}': {str(e)}")
        return None
    finally:
        if metadata_cursor:
            metadata_cursor.close()

