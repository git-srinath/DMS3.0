"""
Mapper SCD (Slowly Changing Dimension) handling.
Generic functions for SCD Type 1 and Type 2 processing.
No job-specific code - all job data passed as parameters.
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.mapper.database_sql_adapter import create_adapter_from_type
    from backend.modules.mapper.mapper_transformation_utils import generate_hash
    from backend.modules.logger import warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.mapper.database_sql_adapter import create_adapter_from_type  # type: ignore
    from modules.mapper.mapper_transformation_utils import generate_hash  # type: ignore
    from modules.logger import warning, error, debug  # type: ignore


def process_scd_batch(
    target_conn,
    target_schema: str,
    target_table: str,
    full_table_name: str,
    rows_to_insert: List[Dict[str, Any]],
    rows_to_update_scd1: List[Dict[str, Any]],
    rows_to_update_scd2: List[Dict[str, Any]],
    all_columns: List[str],
    scd_type: int,
    target_type: str,
    db_type: str = "ORACLE"
) -> Tuple[int, int, int]:
    """
    Process SCD batch operations (insert, update SCD Type 1, expire SCD Type 2).
    
    Args:
        target_conn: Target database connection
        target_schema: Target schema name
        target_table: Target table name
        full_table_name: Full table name (schema.table) - legacy, not used for formatting
        rows_to_insert: List of new rows to insert
        rows_to_update_scd1: List of rows to update (SCD Type 1)
        rows_to_update_scd2: List of SKEY values to expire (SCD Type 2)
        all_columns: List of all target columns
        scd_type: SCD type (1 or 2)
        target_type: Target table type ('DIM', 'FCT', 'MRT')
        db_type: Database type ("ORACLE" or "POSTGRESQL")
        
    Returns:
        Tuple of (inserted_count, updated_count, expired_count)
    """
    cursor = target_conn.cursor()
    inserted_count = 0
    updated_count = 0
    expired_count = 0
    
    # Format table name correctly for this database type
    adapter = create_adapter_from_type(db_type)
    formatted_table_name = adapter.format_table_name(target_schema, target_table)
    
    try:
        # Process SCD Type 2 expiration first (before inserts)
        if rows_to_update_scd2:
            expired_count = _expire_scd2_records(
                cursor, formatted_table_name, rows_to_update_scd2, db_type
            )
        
        # Process SCD Type 1 updates
        if rows_to_update_scd1:
            updated_count = _update_scd1_records(
                cursor, formatted_table_name, rows_to_update_scd1, all_columns, db_type
            )
        
        # Process inserts
        if rows_to_insert:
            inserted_count = _insert_records(
                cursor, formatted_table_name, rows_to_insert, all_columns, 
                target_type, db_type, target_schema, target_table
            )
        
        cursor.close()
        return inserted_count, updated_count, expired_count
        
    except Exception as e:
        error(f"Error processing SCD batch: {e}")
        cursor.close()
        raise


def _expire_scd2_records(
    cursor,
    full_table_name: str,
    skey_list: List[Any],
    db_type: str
) -> int:
    """Expire SCD Type 2 records by setting CURFLG='N' and TODT=current date."""
    if not skey_list:
        return 0
    
    try:
        adapter = create_adapter_from_type(db_type)
        current_date = adapter.get_current_date()
        timestamp = adapter.get_current_timestamp()
        
        # Build parameters
        if adapter.supports_named_parameters():
            params = [{'skey': skey} for skey in skey_list]
            placeholder = adapter.get_parameter_placeholder('skey')
            query = f"""
                UPDATE {full_table_name}
                SET CURFLG = 'N', TODT = {current_date}, RECUPDT = {timestamp}
                WHERE SKEY = {placeholder}
            """
        else:
            # For positional parameters, convert to tuples
            params = [(skey,) for skey in skey_list]
            ph = adapter.get_parameter_placeholder()
            query = f"""
                UPDATE {full_table_name}
                SET CURFLG = 'N', TODT = {current_date}, RECUPDT = {timestamp}
                WHERE SKEY = {ph}
            """
        
        cursor.executemany(query, params)
        
        expired_count = cursor.rowcount if cursor.rowcount is not None else len(skey_list)
        debug(f"Expired {expired_count} SCD Type 2 records")
        return expired_count
    except Exception as e:
        error(f"Error expiring SCD Type 2 records: {e}")
        return 0


def _update_scd1_records(
    cursor,
    full_table_name: str,
    rows_to_update: List[Dict[str, Any]],
    all_columns: List[str],
    db_type: str
) -> int:
    """Update SCD Type 1 records."""
    if not rows_to_update:
        return 0
    
    try:
        adapter = create_adapter_from_type(db_type)
        timestamp = adapter.get_current_timestamp()
        
        # Exclude SKEY and RECCRDT from update (SKEY is in WHERE, RECCRDT never changes)
        update_cols = [col for col in all_columns if col not in {'SKEY', 'RECCRDT'}]
        
        if adapter.supports_named_parameters():
            set_clause = ", ".join([f"{col} = :{col}" for col in update_cols])
            params = []
            for row in rows_to_update:
                param_row = {col: row.get(col) for col in update_cols}
                param_row['SKEY'] = row.get('SKEY')
                params.append(param_row)
            
            where_clause = "SKEY = :SKEY"
            query = f"""
                UPDATE {full_table_name}
                SET {set_clause}, RECUPDT = {timestamp}
                WHERE {where_clause}
            """
        else:
            ph = adapter.get_parameter_placeholder()
            set_clause = ", ".join([f"{col} = {ph}" for col in update_cols])
            params = []
            for row in rows_to_update:
                param_row = [row.get(col) for col in update_cols]
                param_row.append(row.get('SKEY'))  # Add SKEY for WHERE clause
                params.append(tuple(param_row))
            
            where_clause = f"SKEY = {ph}"
            query = f"""
                UPDATE {full_table_name}
                SET {set_clause}, RECUPDT = {timestamp}
                WHERE {where_clause}
            """
        
        cursor.executemany(query, params)
        
        updated_count = cursor.rowcount if cursor.rowcount is not None else len(rows_to_update)
        debug(f"Updated {updated_count} SCD Type 1 records")
        return updated_count
    except Exception as e:
        error(f"Error updating SCD Type 1 records: {e}")
        return 0


def _insert_records(
    cursor,
    formatted_table_name: str,
    rows_to_insert: List[Dict[str, Any]],
    all_columns: List[str],
    target_type: str,
    db_type: str,
    target_schema: str = None,
    target_table: str = None
) -> int:
    """Insert new records."""
    if not rows_to_insert:
        return 0
    
    try:
        adapter = create_adapter_from_type(db_type)
        timestamp = adapter.get_current_timestamp()
        
        # Exclude SKEY, RECCRDT, RECUPDT from insert (handled separately)
        insert_cols = [col for col in all_columns 
                      if col not in {'SKEY', 'RECCRDT', 'RECUPDT'}]
        
        cols_str = ", ".join(insert_cols)
        
        # Get sequence nextval syntax - use schema.table for sequence name
        if target_schema and target_table:
            seq_name = f"{target_schema}.{target_table}_SEQ"
        else:
            seq_name = formatted_table_name + "_SEQ"
        seq_nextval = adapter.get_sequence_nextval(seq_name)
        
        if adapter.supports_named_parameters():
            vals_str = ", ".join([f":{col}" for col in insert_cols])
            params = []
            for row in rows_to_insert:
                param_row = {col: row.get(col) for col in insert_cols}
                params.append(param_row)
            
            query = f"""
                INSERT INTO {formatted_table_name} (SKEY, {cols_str}, RECCRDT, RECUPDT)
                VALUES ({seq_nextval}, {vals_str}, {timestamp}, {timestamp})
            """
        else:
            ph = adapter.get_parameter_placeholder()
            vals_str = ", ".join([ph for _ in insert_cols])
            params = []
            for row in rows_to_insert:
                param_row = [row.get(col) for col in insert_cols]
                params.append(tuple(param_row))
            
            query = f"""
                INSERT INTO {formatted_table_name} (SKEY, {cols_str}, RECCRDT, RECUPDT)
                VALUES ({seq_nextval}, {vals_str}, {timestamp}, {timestamp})
            """
        
        cursor.executemany(query, params)
        
        inserted_count = cursor.rowcount if cursor.rowcount is not None else len(rows_to_insert)
        debug(f"Inserted {inserted_count} records")
        return inserted_count
    except Exception as e:
        error(f"Error inserting records: {e}")
        return 0


def prepare_row_for_scd(
    source_row: Dict[str, Any],
    target_row: Optional[Dict[str, Any]],
    source_hash: str,
    scd_type: int,
    target_type: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Any]]:
    """
    Prepare row for SCD processing based on whether record exists and has changed.
    
    Args:
        source_row: Transformed source row (target column names)
        target_row: Existing target row (if found) or None
        source_hash: Hash of source row
        scd_type: SCD type (1 or 2)
        target_type: Target table type ('DIM', 'FCT', 'MRT')
        
    Returns:
        Tuple of (row_to_insert, row_to_update_scd1, skey_to_expire_scd2)
        - row_to_insert: New row to insert (if new or SCD Type 2 change)
        - row_to_update_scd1: Row to update (if SCD Type 1 change)
        - skey_to_expire_scd2: SKEY to expire (if SCD Type 2 change)
    """
    if target_row:
        # Record exists - check for changes
        target_hash = target_row.get('RWHKEY', '')
        
        if source_hash != target_hash:
            # Data changed
            if scd_type == 2:
                # SCD Type 2 - Insert new version, expire old
                new_version = dict(source_row)
                new_version['SKEY'] = None  # Will be generated
                new_version['RWHKEY'] = source_hash
                new_version['CURFLG'] = 'Y'
                new_version['FROMDT'] = datetime.now()
                new_version['TODT'] = datetime(9999, 12, 31)
                return new_version, None, target_row['SKEY']
            else:
                # SCD Type 1 - Update existing
                updated_row = dict(source_row)
                updated_row['SKEY'] = target_row['SKEY']
                updated_row['RWHKEY'] = source_hash
                return None, updated_row, None
        else:
            # No change - skip
            return None, None, None
    else:
        # New record
        new_row = dict(source_row)
        new_row['RWHKEY'] = source_hash
        if target_type == 'DIM':
            new_row['CURFLG'] = 'Y'
            new_row['FROMDT'] = datetime.now()
            new_row['TODT'] = datetime(9999, 12, 31)
        return new_row, None, None

