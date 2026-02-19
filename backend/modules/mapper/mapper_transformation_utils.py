"""
Mapper transformation utilities.
Generic functions for row transformation and hash generation.
No job-specific code - all job data passed as parameters.
"""
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Set, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import debug, warning
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import debug, warning  # type: ignore


def map_row_to_target_columns(
    row_dict: Dict[str, Any],
    column_mapping: Dict[str, str],
    all_target_columns: List[str]
) -> Dict[str, Any]:
    """
    Normalize a source row dictionary so keys match target column names.
    Maps ALL target columns (from all_target_columns) to their source values.
    Uses column_mapping for preferred source column names and falls back
    to case-insensitive matches on both source and target column names.
    
    Args:
        row_dict: Source row dictionary with source column names as keys
        column_mapping: Mapping from target column names to source column names
                       Format: {'TARGET_COL': 'SOURCE_COL', ...}
        all_target_columns: List of all target column names (in execution order)
        
    Returns:
        Dictionary with target column names as keys, normalized values
    """
    normalized = {}
    upper_row = dict((k.upper(), v) for k, v in row_dict.items() if isinstance(k, str))
    
    # Process ALL target columns, not just those in column_mapping
    for target_col in all_target_columns:
        # First, try to get source column name from mapping
        source_col = column_mapping.get(target_col, target_col)
        
        # Try to get value using source column name
        value = row_dict.get(source_col)
        if value is None and isinstance(source_col, str):
            value = upper_row.get(source_col.upper())
        
        # If still None, try target column name directly (for columns with same name)
        if value is None:
            value = row_dict.get(target_col)
            if value is None and isinstance(target_col, str):
                value = upper_row.get(target_col.upper())
        
        # Store the value (even if None) - this ensures all target columns are present
        normalized[target_col] = value
    
    return normalized


def generate_hash(
    row_dict: Dict[str, Any],
    column_order: List[str],
    exclude_columns: Optional[Set[str]] = None
) -> str:
    """
    Generate MD5 hash from row data.
    
    Args:
        row_dict: Dictionary of column_name -> value
        column_order: Order of columns for hash (execution order)
        exclude_columns: Set of column names to exclude from hash calculation
                        (default: common audit columns)
        
    Returns:
        32-character MD5 hash
    """
    if exclude_columns is None:
        # Default exclude columns (audit columns)
        exclude_columns = {
            'SKEY', 'RWHKEY', 'RECCRDT', 'RECUPDT', 'CURFLG',
            'FROMDT', 'TODT', 'VALDFRM', 'VALDTO'
        }
    
    # Filter out audit columns and build concatenated string
    parts = []
    for col in column_order:
        if col.upper() not in exclude_columns:
            val = row_dict.get(col)
            if val is None:
                parts.append('<NULL>')
            elif isinstance(val, datetime):
                parts.append(val.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                parts.append(str(val))
    
    concat_str = '|'.join(parts)
    return hashlib.md5(concat_str.encode('utf-8')).hexdigest()


def build_primary_key_values(
    row_dict: Dict[str, Any],
    pk_columns: Set[str],
    pk_source_mapping: Dict[str, str]
) -> Dict[str, Any]:
    """
    Build primary key values dictionary from source row.
    
    Args:
        row_dict: Source row dictionary
        pk_columns: Set of target primary key column names
        pk_source_mapping: Mapping from target PK column names to source column names
        
    Returns:
        Dictionary with target PK column names as keys and values from source row
    """
    pk_values = {}
    upper_row = dict((k.upper(), v) for k, v in row_dict.items() if isinstance(k, str))
    
    for pk_col in pk_columns:
        # Get source column name from mapping (fallback to target name if not mapped)
        source_col = pk_source_mapping.get(pk_col, pk_col)
        
        # Try to get value from source data using source column name
        pk_value = row_dict.get(source_col)
        if pk_value is None and isinstance(source_col, str):
            pk_value = upper_row.get(source_col.upper())
        
        # If still None, try target column name as fallback
        if pk_value is None:
            pk_value = row_dict.get(pk_col)
            if pk_value is None and isinstance(pk_col, str):
                pk_value = upper_row.get(pk_col.upper())
        
        pk_values[pk_col] = pk_value
    
    return pk_values


def build_primary_key_where_clause(
    pk_columns: Set[str],
    db_type: str = "ORACLE"
) -> str:
    """
    Build WHERE clause for primary key lookup.
    
    Args:
        pk_columns: Set of primary key column names
        db_type: Database type string (e.g., 'ORACLE', 'POSTGRESQL', 'MYSQL', etc.)
        
    Returns:
        WHERE clause string (e.g., "COL1 = :col1 AND COL2 = :col2" or "COL1 = %s AND COL2 = %s")
    """
    # Support both FastAPI (package import) and legacy Flask (relative import) contexts
    try:
        from backend.modules.mapper.database_sql_adapter import create_adapter_from_type
    except ImportError:
        from modules.mapper.database_sql_adapter import create_adapter_from_type  # type: ignore
    
    adapter = create_adapter_from_type(db_type)
    
    # Build WHERE clause with database-agnostic placeholders
    if adapter.supports_named_parameters():
        return " AND ".join([f"{col} = :{col}" for col in pk_columns])
    else:
        placeholder = adapter.get_parameter_placeholder()
        return " AND ".join([f"{col} = {placeholder}" for col in pk_columns])

