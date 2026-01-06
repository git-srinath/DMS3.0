"""
Mapper checkpoint management.
Generic functions for handling checkpoints (resume from previous run).
No job-specific code - all job data passed as parameters.
"""
from typing import Dict, Any, List, Tuple, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.database_sql_adapter import create_adapter
    from backend.modules.logger import info, warning, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.database_sql_adapter import create_adapter  # type: ignore
    from modules.logger import info, warning, debug  # type: ignore


def parse_checkpoint_value(
    checkpoint_value: Optional[str],
    checkpoint_strategy: str,
    checkpoint_columns: List[str]
) -> Tuple[Optional[str], List[str], int]:
    """
    Parse checkpoint value based on strategy.
    
    Args:
        checkpoint_value: Checkpoint value from session params (param1)
        checkpoint_strategy: Checkpoint strategy ('KEY', 'PYTHON', 'AUTO', 'NONE')
        checkpoint_columns: List of checkpoint column names
        
    Returns:
        Tuple of (checkpoint_value, checkpoint_values_list, rows_to_skip)
        - checkpoint_value: Single checkpoint value (for KEY strategy, single column)
        - checkpoint_values: List of checkpoint values (for KEY strategy, composite key)
        - rows_to_skip: Number of rows to skip (for PYTHON strategy)
    """
    if not checkpoint_value or checkpoint_value == 'COMPLETED':
        return None, [], 0
    
    if checkpoint_strategy == 'PYTHON':
        try:
            rows_to_skip = int(checkpoint_value)
            return None, [], rows_to_skip
        except ValueError:
            warning(f"Invalid checkpoint value for PYTHON strategy: {checkpoint_value}. Starting fresh.")
            return None, [], 0
    
    elif checkpoint_strategy == 'KEY' and checkpoint_columns:
        if len(checkpoint_columns) > 1:
            # Composite key: pipe-separated values
            checkpoint_values = checkpoint_value.split('|')
            if len(checkpoint_values) != len(checkpoint_columns):
                warning(f"Invalid composite checkpoint value: {checkpoint_value}. "
                       f"Expected {len(checkpoint_columns)} values separated by '|'. Starting fresh.")
                return None, [], 0
            return None, checkpoint_values, 0
        else:
            # Single column key
            return checkpoint_value, [], 0
    
    return None, [], 0


def apply_checkpoint_to_query(
    base_query: str,
    checkpoint_config: Dict[str, Any],
    checkpoint_value: Optional[str],
    checkpoint_values: List[str],
    db_type: str = "ORACLE"
) -> Tuple[str, Any]:
    """
    Apply checkpoint to source query based on strategy.
    
    Args:
        base_query: Base source SQL query
        checkpoint_config: Checkpoint configuration dictionary with:
            - 'enabled': bool
            - 'strategy': str ('KEY', 'PYTHON', 'AUTO', 'NONE')
            - 'columns': List[str] (checkpoint column names)
            - 'column': Optional[str] (single checkpoint column name)
        checkpoint_value: Single checkpoint value (for single column KEY strategy)
        checkpoint_values: List of checkpoint values (for composite KEY strategy)
        db_type: Database type string (e.g., 'ORACLE', 'POSTGRESQL', 'MYSQL', etc.)
        
    Returns:
        Tuple of (modified_query, bind_parameters)
        - modified_query: SQL query with checkpoint WHERE clause applied
        - bind_parameters: Formatted parameters (dict or tuple) for the query
    """
    if not checkpoint_config.get('enabled', False):
        return base_query, {}
    
    strategy = checkpoint_config.get('strategy', 'AUTO')
    checkpoint_columns = checkpoint_config.get('columns', [])
    
    # Create adapter for database-specific syntax
    from backend.modules.mapper.database_sql_adapter import create_adapter_from_type
    adapter = create_adapter_from_type(db_type)
    
    if strategy == 'KEY' and checkpoint_columns:
        if len(checkpoint_columns) > 1:
            # Composite key: Use tuple comparison
            if checkpoint_values:
                columns_str = ', '.join(checkpoint_columns)
                order_by_str = ', '.join(checkpoint_columns)
                
                # Build placeholders
                if adapter.supports_named_parameters():
                    placeholders = ', '.join([f':checkpoint_val_{i}' for i in range(len(checkpoint_columns))])
                    bind_params_dict = {f'checkpoint_val_{i}': checkpoint_values[i] 
                                      for i in range(len(checkpoint_columns))}
                    bind_params = adapter.format_parameters(bind_params_dict, use_named=True)
                else:
                    ph = adapter.get_parameter_placeholder()
                    placeholders = ', '.join([ph for _ in checkpoint_columns])
                    bind_params_dict = {f'val_{i}': checkpoint_values[i] 
                                      for i in range(len(checkpoint_columns))}
                    bind_params = adapter.format_parameters(bind_params_dict, use_named=False)
                
                modified_query = f"""
SELECT * FROM (
{base_query}
) source_data
WHERE ({columns_str}) > ({placeholders})
ORDER BY {order_by_str}
"""
                
                debug(f"Applied KEY checkpoint (composite): ({columns_str}) > ({checkpoint_values})")
                return modified_query.strip(), bind_params
            else:
                # No checkpoint value yet, return base query
                return base_query, {}
        else:
            # Single column key
            if checkpoint_value:
                column = checkpoint_columns[0]
                placeholder = adapter.get_parameter_placeholder('checkpoint_value')
                
                params_dict = {'checkpoint_value': checkpoint_value}
                bind_params = adapter.format_parameters(params_dict, use_named=True)
                
                modified_query = f"""
SELECT * FROM (
{base_query}
) source_data
WHERE {column} > {placeholder}
ORDER BY {column}
"""
                
                debug(f"Applied KEY checkpoint: {column} > {checkpoint_value}")
                return modified_query.strip(), bind_params
            else:
                # No checkpoint value yet, return base query
                return base_query, {}
    
    # For PYTHON strategy or no checkpoint, return base query
    # (rows will be skipped after fetch)
    return base_query, {}


def update_checkpoint(
    metadata_conn,
    session_params: Dict[str, Any],
    checkpoint_value: str
) -> None:
    """
    Update checkpoint value in DMS_PRCLOG.
    
    Args:
        metadata_conn: Metadata database connection
        session_params: Session parameters (must contain 'prcid' and 'sessionid')
        checkpoint_value: New checkpoint value to store
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        timestamp = adapter.get_current_timestamp()
        
        params_dict = {
            'checkpoint_value': checkpoint_value,
            'sessionid': sessionid,
            'prcid': prcid
        }
        params = adapter.format_parameters(params_dict, use_named=True)
        
        if adapter.supports_named_parameters():
            query = f"""
                UPDATE DMS_PRCLOG
                SET PARAM1 = :checkpoint_value,
                    recupdt = {timestamp}
                WHERE sessionid = :sessionid
                  AND prcid = :prcid
            """
        else:
            ph = adapter.get_parameter_placeholder()
            query = f"""
                UPDATE DMS_PRCLOG
                SET PARAM1 = {ph},
                    recupdt = {timestamp}
                WHERE sessionid = {ph}
                  AND prcid = {ph}
            """
        
        cursor.execute(query, params)
        cursor.close()
        debug(f"Updated checkpoint to: {checkpoint_value}")
    except Exception as e:
        warning(f"Could not update checkpoint: {e}")


def complete_checkpoint(
    metadata_conn,
    session_params: Dict[str, Any]
) -> None:
    """
    Mark checkpoint as completed in DMS_PRCLOG.
    
    Args:
        metadata_conn: Metadata database connection
        session_params: Session parameters (must contain 'prcid' and 'sessionid')
    """
    try:
        cursor = metadata_conn.cursor()
        adapter = create_adapter(metadata_conn)
        
        prcid = session_params.get('prcid')
        sessionid = session_params.get('sessionid')
        timestamp = adapter.get_current_timestamp()
        
        params_dict = {
            'sessionid': sessionid,
            'prcid': prcid
        }
        params = adapter.format_parameters(params_dict, use_named=True)
        
        if adapter.supports_named_parameters():
            query = f"""
                UPDATE DMS_PRCLOG
                SET PARAM1 = 'COMPLETED',
                    recupdt = {timestamp}
                WHERE sessionid = :sessionid
                  AND prcid = :prcid
            """
        else:
            ph = adapter.get_parameter_placeholder()
            query = f"""
                UPDATE DMS_PRCLOG
                SET PARAM1 = 'COMPLETED',
                    recupdt = {timestamp}
                WHERE sessionid = {ph}
                  AND prcid = {ph}
            """
        
        cursor.execute(query, params)
        cursor.close()
        info("Checkpoint marked as completed")
    except Exception as e:
        warning(f"Could not complete checkpoint: {e}")

