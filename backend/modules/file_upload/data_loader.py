""" 
Data Loader Service for File Upload Module
Handles data loading with different strategies: INSERT, TRUNCATE_LOAD, UPSERT.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.file_upload.table_creator import _quote_identifier
from backend.modules.logger import info, error, warning


# Toggle for very detailed debug logging in this module.
# Set to True temporarily when diagnosing issues; keep False for normal use.
DETAILED_FILE_UPLOAD_LOGS = False


class LoadMode:
    """Load mode constants."""
    INSERT = "INSERT"  # Insert only (no truncate, no upsert)
    TRUNCATE_LOAD = "TRUNCATE_LOAD"  # Truncate table, then insert
    UPSERT = "UPSERT"  # Update if exists, insert if not (based on primary key)


def load_data(
    connection,
    schema: str,
    table: str,
    dataframe: pd.DataFrame,
    column_mappings: List[Dict[str, Any]],
    load_mode: str = LoadMode.INSERT,
    batch_size: int = 1000,
    username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load data into target table with specified load mode.
    
    Args:
        connection: Target database connection
        schema: Target schema name
        table: Target table name
        dataframe: DataFrame with source data (should have target column names after transformation)
        column_mappings: List of column mapping dictionaries
        load_mode: Load mode (INSERT, TRUNCATE_LOAD, UPSERT)
        batch_size: Number of rows per batch
        username: Username for audit columns
        
    Returns:
        Dictionary with execution results:
        {
            'rows_processed': int,
            'rows_successful': int,
            'rows_failed': int,
            'errors': List[Dict]  # List of error records
        }
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    
    # Build target columns list, audit column mapping, and column type mapping
    target_columns = []
    primary_key_columns = []
    audit_columns = {}  # Map audit column names to their types
    column_types = {}  # Map column names to their data types
    
    for col in column_mappings:
        trg_col = col.get('trgclnm', '').strip()
        if not trg_col:
            continue
            
        target_columns.append(trg_col)
        
        # Track column data type
        trgcldtyp = col.get('trgcldtyp', '').strip().upper() if col.get('trgcldtyp') else ''
        if trgcldtyp:
            column_types[trg_col] = trgcldtyp
        
        # Track primary keys for UPSERT
        if col.get('trgkyflg') == 'Y':
            primary_key_columns.append(trg_col)
        
        # Track audit columns - only if isaudit is 'Y' AND has a valid audttyp
        # Also check if column name is one of the standard audit column names
        is_audit_col = False
        audttyp = ''
        
        if col.get('isaudit') == 'Y':
            audttyp = col.get('audttyp', '').strip().upper()
            # Only treat as audit column if audttyp is provided and valid
            if audttyp:
                is_audit_col = True
        
        # Also check if column name matches standard audit column names
        if trg_col in ('CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT'):
            is_audit_col = True
            # Set audttyp if not already set
            if not audttyp:
                if trg_col == 'CRTDBY':
                    audttyp = 'CREATED_BY'
                elif trg_col == 'CRTDDT':
                    audttyp = 'CREATED_DATE'
                elif trg_col == 'UPDTBY':
                    audttyp = 'UPDATED_BY'
                elif trg_col == 'UPDTDT':
                    audttyp = 'UPDATED_DATE'
        
        if is_audit_col and audttyp:
            audit_columns[trg_col] = audttyp
    
    if not target_columns:
        raise ValueError("No target columns found in column mappings")
    
    # Log audit columns for debugging
    info(f"[load_data] Identified {len(audit_columns)} audit columns: {list(audit_columns.keys())}")
    info(f"[load_data] Audit column mapping: {audit_columns}")
    
    try:
        # Truncate if needed
        if load_mode == LoadMode.TRUNCATE_LOAD:
            _truncate_table(cursor, db_type, schema, table)
            info(f"Truncated table {schema}.{table}")
        
        # Process in batches
        total_rows = len(dataframe)
        num_batches = (total_rows + batch_size - 1) // batch_size
        
        all_rows_successful = 0
        all_rows_failed = 0
        all_errors = []
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_rows)
            batch_df = dataframe.iloc[start_idx:end_idx].copy()
            
            info(f"Processing batch {batch_num + 1}/{num_batches} (rows {start_idx + 1}-{end_idx})")
            info(f"[load_data] Batch DataFrame shape: {batch_df.shape}")
            info(f"[load_data] Batch DataFrame columns: {list(batch_df.columns)}")
            if len(batch_df) > 0 and 'COD_ACCT_NO' in batch_df.columns:
                info(f"[load_data] Batch COD_ACCT_NO first value: '{batch_df.iloc[0]['COD_ACCT_NO']}'")
            
            if load_mode == LoadMode.UPSERT:
                result = _upsert_batch(
                    cursor, db_type, schema, table, batch_df, target_columns,
                    primary_key_columns, audit_columns, username, column_types
                )
            else:
                result = _insert_batch(
                    cursor, db_type, schema, table, batch_df, target_columns,
                    audit_columns, username, column_types
                )
            
            all_rows_successful += result['rows_successful']
            all_rows_failed += result['rows_failed']
            all_errors.extend(result['errors'])
        
        connection.commit()
        
        return {
            'rows_processed': total_rows,
            'rows_successful': all_rows_successful,
            'rows_failed': all_rows_failed,
            'errors': all_errors
        }
        
    except Exception as e:
        connection.rollback()
        error(f"Error loading data: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()


def _format_table_ref(db_type: str, schema: str, table: str) -> str:
    """Format table reference as schema.table based on database type."""
    if db_type == "POSTGRESQL":
        return f'"{schema.lower()}"."{table.lower()}"'
    elif db_type == "ORACLE":
        return f"{schema.upper()}.{table.upper()}"
    else:
        return f"{schema}.{table}"


def _truncate_table(cursor, db_type: str, schema: str, table: str):
    """Truncate table."""
    table_ref = _format_table_ref(db_type, schema, table)
    
    if db_type == "POSTGRESQL":
        sql = f"TRUNCATE TABLE {table_ref}"
    elif db_type == "ORACLE":
        sql = f"TRUNCATE TABLE {table_ref}"
    else:  # MySQL, MS SQL Server, etc.
        sql = f"TRUNCATE TABLE {table_ref}"
    
    cursor.execute(sql)


def _normalize_db_value(value: Any, column_type: Optional[str] = None, db_type: str = "ORACLE") -> Any:
    """
    Normalize Python / pandas / numpy values to types supported by DB drivers.

    In particular, Oracle (python-oracledb) does not accept numpy scalar types
    like np.int64 directly; they must be converted to built‑in Python types.
    
    Also handles string dates/timestamps conversion for Oracle DATE/TIMESTAMP columns.
    
    Args:
        value: Value to normalize
        column_type: Optional column data type (e.g., 'DATE', 'TIMESTAMP') to help with conversion
        db_type: Database type ('ORACLE', 'POSTGRESQL', etc.)
    """
    # Treat pandas NA/NaT as None
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    # pandas Timestamp -> builtin datetime
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # Handle string dates/timestamps for Oracle DATE/TIMESTAMP columns
    if isinstance(value, str) and value.strip() and column_type:
        col_type_upper = column_type.upper()
        # Check if this column should be a date or timestamp
        is_date_type = any(term in col_type_upper for term in ['DATE', 'TIMESTAMP'])
        
        if is_date_type:
            try:
                # Try to parse the string as a date/timestamp using pandas
                # pandas.to_datetime handles many formats automatically
                parsed = pd.to_datetime(value, errors='raise', infer_datetime_format=True)
                if isinstance(parsed, pd.Timestamp):
                    dt = parsed.to_pydatetime()
                    # For DATE columns (without time), return only the date part
                    if 'DATE' in col_type_upper and 'TIMESTAMP' not in col_type_upper:
                        # Check if the original value looks like date-only (no time component)
                        if ':' not in value and 'T' not in value:
                            return dt.date()
                    return dt
            except (ValueError, TypeError) as e:
                # If parsing fails, log warning but return original value
                # This will cause an error that will be caught and logged properly
                warning(f"Could not parse date string '{value}' for column type '{column_type}': {str(e)}")
                return value

    # numpy scalar types -> builtin Python types
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)

    return value


def _insert_batch(
    cursor,
    db_type: str,
    schema: str,
    table: str,
    batch_df: pd.DataFrame,
    target_columns: List[str],
    audit_columns: Dict[str, str],
    username: Optional[str],
    column_types: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Insert a batch of rows using a clean, direct approach.
    
    The DataFrame should already have target column names after transformation.
    We simply extract values in the order specified by target_columns.
    """
    table_ref = _format_table_ref(db_type, schema, table)
    columns_str = ", ".join([_quote_identifier(col, db_type) for col in target_columns])
    
    # Build placeholders based on database type
    if db_type == "POSTGRESQL":
        placeholders = ", ".join(["%s"] * len(target_columns))
    elif db_type == "ORACLE":
        placeholders = ", ".join([f":{i+1}" for i in range(len(target_columns))])
    else:
        placeholders = ", ".join(["?"] * len(target_columns))
    
    insert_sql = f"INSERT INTO {table_ref} ({columns_str}) VALUES ({placeholders})"
    info(f"[_insert_batch] INSERT SQL: {insert_sql}")
    
    rows_successful = 0
    rows_failed = 0
    errors = []
    current_time = datetime.now()
    
    # Ensure DataFrame has integer index for reliable access
    batch_df = batch_df.reset_index(drop=True)
    
    if DETAILED_FILE_UPLOAD_LOGS:
        # Log BEFORE reordering to verify data exists
        info(f"[_insert_batch] BEFORE reorder - Batch DataFrame shape: {batch_df.shape}")
        info(f"[_insert_batch] BEFORE reorder - Batch DataFrame columns: {list(batch_df.columns)}")
        if len(batch_df) > 0:
            first_row_before = dict(batch_df.iloc[0])
            info(f"[_insert_batch] BEFORE reorder - First row data: {first_row_before}")
            if 'COD_ACCT_NO' in batch_df.columns:
                info(f"[_insert_batch] BEFORE reorder - COD_ACCT_NO value: '{batch_df.iloc[0]['COD_ACCT_NO']}'")
    
    # CRITICAL FIX: Reorder DataFrame columns to match target_columns order
    # This ensures that when we iterate through target_columns, the DataFrame
    # columns are in the same order, making value extraction reliable
    
    # Check for case-insensitive column name matching
    batch_df_cols_lower = {col.lower(): col for col in batch_df.columns}
    target_cols_lower = {col.lower(): col for col in target_columns}
    
    # Find columns that exist (case-insensitive)
    available_cols = []
    missing_cols = []
    case_mismatches = []
    
    for trg_col in target_columns:
        trg_lower = trg_col.lower()
        if trg_col in batch_df.columns:
            # Exact match
            available_cols.append(trg_col)
        elif trg_lower in batch_df_cols_lower:
            # Case mismatch - rename the DataFrame column to match target
            actual_col = batch_df_cols_lower[trg_lower]
            batch_df = batch_df.rename(columns={actual_col: trg_col})
            available_cols.append(trg_col)
            case_mismatches.append(f"{actual_col} -> {trg_col}")
        else:
            missing_cols.append(trg_col)
    
    if DETAILED_FILE_UPLOAD_LOGS:
        info(f"[_insert_batch] Available columns in DataFrame: {available_cols}")
        if case_mismatches:
            info(f"[_insert_batch] Case mismatches fixed: {case_mismatches}")
        info(f"[_insert_batch] Missing columns: {missing_cols}")
    
    if missing_cols:
        warning(f"[_insert_batch] Missing columns in DataFrame (will be filled as NULL): {missing_cols}")
        # Add missing columns as None
        for col in missing_cols:
            batch_df[col] = None
    
    # Reorder DataFrame columns to match target_columns exactly
    # Only reorder columns that exist (or we've added)
    try:
        # Verify all target columns exist before reordering
        missing_in_reorder = [col for col in target_columns if col not in batch_df.columns]
        if missing_in_reorder:
            error(f"[_insert_batch] Cannot reorder - columns still missing: {missing_in_reorder}")
            error(f"[_insert_batch] Available columns: {list(batch_df.columns)}")
            error(f"[_insert_batch] Target columns: {target_columns}")
            raise ValueError(f"Missing columns for reordering: {missing_in_reorder}")
        
        batch_df = batch_df[target_columns]
        if DETAILED_FILE_UPLOAD_LOGS:
            info(f"[_insert_batch] Successfully reordered DataFrame")
    except KeyError as e:
        error(f"[_insert_batch] Failed to reorder DataFrame: {str(e)}")
        error(f"[_insert_batch] Available columns: {list(batch_df.columns)}")
        error(f"[_insert_batch] Target columns: {target_columns}")
        raise
    
    if DETAILED_FILE_UPLOAD_LOGS and len(batch_df) > 0:
        # Log AFTER reordering to verify data is still there
        info(f"[_insert_batch] AFTER reorder - Batch DataFrame shape: {batch_df.shape}")
        info(f"[_insert_batch] AFTER reorder - Batch DataFrame columns: {list(batch_df.columns)}")
        first_row_after = dict(batch_df.iloc[0])
        info(f"[_insert_batch] AFTER reorder - First row data: {first_row_after}")
    
    # Pre-compute audit column values (same for all rows in batch)
    audit_values = {}
    for trg_col in target_columns:
        if trg_col in audit_columns:
            audttyp = audit_columns[trg_col]
            if audttyp == "CREATED_DATE" or audttyp == "UPDATED_DATE":
                audit_values[trg_col] = current_time
            elif audttyp == "CREATED_BY" or audttyp == "UPDATED_BY":
                audit_values[trg_col] = username or "SYSTEM"
            else:
                audit_values[trg_col] = None
    
    # Process each row - use simple, direct DataFrame access
    # Final verification: Check if DataFrame actually has data
    if len(batch_df) == 0:
        warning(f"[_insert_batch] DataFrame is empty! Cannot process rows.")
        return {'rows_successful': 0, 'rows_failed': 0, 'errors': []}
    
    if DETAILED_FILE_UPLOAD_LOGS:
        # Verify at least one non-audit column has data
        non_audit_cols = [col for col in target_columns if col not in audit_values]
        if non_audit_cols:
            sample_col = non_audit_cols[0]
            if sample_col in batch_df.columns:
                sample_value = batch_df.iloc[0][sample_col]
                info(f"[_insert_batch] Sample non-audit column '{sample_col}' first value: '{sample_value}'")
                if sample_value is None or pd.isna(sample_value):
                    warning(f"[_insert_batch] WARNING: Sample column '{sample_col}' has None/NaN value! This may indicate data loss during reordering.")
    
    for row_idx in range(len(batch_df)):
        try:
            # Build values list in the exact order of target_columns
            values = []
            
            if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                info(f"[_insert_batch] Building values for row {row_idx}")
                info(f"[_insert_batch] Target columns count: {len(target_columns)}")
                info(f"[_insert_batch] Batch DataFrame shape: {batch_df.shape}")
                info(f"[_insert_batch] Batch DataFrame columns: {list(batch_df.columns)}")
                # Log first row as dict for debugging
                first_row_dict = dict(batch_df.iloc[0])
                info(f"[_insert_batch] First row data (as dict): {first_row_dict}")
            
            for col_idx, trg_col in enumerate(target_columns):
                # Check if audit column first
                if trg_col in audit_values:
                    val = audit_values[trg_col]
                    values.append(val)
                    if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                        info(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): audit value='{val}'")
                else:
                    # Direct access: DataFrame columns are now in the same order as target_columns
                    # Use column name access first (most reliable), then positional as fallback
                    try:
                        val = None
                        
                        # Method 1: Direct column name access (most reliable)
                        try:
                            if trg_col in batch_df.columns:
                                val = batch_df.iloc[row_idx][trg_col]
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    info(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 1 (iloc[{row_idx}]['{trg_col}']) = '{val}'")
                            else:
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Column '{trg_col}' not in DataFrame columns: {list(batch_df.columns)}")
                        except Exception as e:
                            if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 1 failed: {str(e)}")
                        
                        # Method 2: Positional access (fallback after reordering)
                        if val is None or (pd.notna(val) and isinstance(val, float) and pd.isna(val)):
                            try:
                                val = batch_df.iloc[row_idx, col_idx]
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    info(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 2 (iloc[{row_idx}, {col_idx}]) = '{val}'")
                            except Exception as e:
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 2 failed: {str(e)}")
                        
                        # Method 3: .at access (fallback)
                        if val is None or (pd.notna(val) and isinstance(val, float) and pd.isna(val)):
                            try:
                                val = batch_df.at[row_idx, trg_col]
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    info(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 3 (.at[{row_idx}, '{trg_col}']) = '{val}'")
                            except Exception as e:
                                if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                    warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Method 3 failed: {str(e)}")
                        
                        # Convert NaN/NaT to None
                        if val is None or pd.isna(val):
                            values.append(None)
                            if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Final value is None/NaN after all methods")
                        else:
                            values.append(val)
                            if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                                info(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Final value='{val}', type={type(val).__name__}")
                    except Exception as e:
                        if DETAILED_FILE_UPLOAD_LOGS:
                            warning(f"[_insert_batch] Row {row_idx}, Col {col_idx} ({trg_col}): Error accessing value: {str(e)}")
                        values.append(None)
            
            # Basic validation before insertion
            if len(values) != len(target_columns):
                warning(f"[_insert_batch] Row {row_idx}: Values count {len(values)} != target columns {len(target_columns)}, skipping insert")
                rows_failed += 1
                continue
            
            if row_idx == 0 and DETAILED_FILE_UPLOAD_LOGS:
                cod_pos = target_columns.index('COD_ACCT_NO') if 'COD_ACCT_NO' in target_columns else -1
                if cod_pos >= 0:
                    info(f"[_insert_batch] Row {row_idx}: COD_ACCT_NO at position {cod_pos}, value='{values[cod_pos]}'")
                info(f"[_insert_batch] Row {row_idx}: Values array length: {len(values)}, Expected: {len(target_columns)}")
                info(f"[_insert_batch] Row {row_idx}: First 5 values: {values[:5]}")
                info(f"[_insert_batch] Row {row_idx}: All values: {values}")
            
            # Execute insert
            # Normalize values to DB‑friendly Python types (e.g. np.int64 -> int)
            # Also convert string dates to datetime objects based on column types
            normalized_values = []
            for idx, v in enumerate(values):
                col_name = target_columns[idx] if idx < len(target_columns) else None
                col_type = column_types.get(col_name) if column_types and col_name else None
                normalized_values.append(_normalize_db_value(v, col_type, db_type))

            if db_type == "ORACLE":
                cursor.execute(insert_sql, normalized_values)
            else:
                cursor.execute(insert_sql, tuple(normalized_values))
            
            rows_successful += 1
            
        except Exception as e:
            rows_failed += 1
            # Serialize row data for error record
            row_dict = batch_df.iloc[row_idx].to_dict()
            serialized_row = {}
            for key, value in row_dict.items():
                if pd.isna(value):
                    serialized_row[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    serialized_row[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                else:
                    serialized_row[key] = value
            
            error_record = {
                'row_index': int(row_idx),
                'row_data': serialized_row,
                'error_message': str(e)
            }
            errors.append(error_record)
            warning(f"Error inserting row {row_idx}: {str(e)}")
    
    return {
        'rows_successful': rows_successful,
        'rows_failed': rows_failed,
        'errors': errors
    }


def _upsert_batch(
    cursor,
    db_type: str,
    schema: str,
    table: str,
    batch_df: pd.DataFrame,
    target_columns: List[str],
    primary_key_columns: List[str],
    audit_columns: Dict[str, str],
    username: Optional[str],
    column_types: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Upsert a batch of rows (update if exists, insert if not)."""
    if not primary_key_columns:
        # Fall back to insert if no primary key
        warning("No primary key columns found for UPSERT, falling back to INSERT")
        return _insert_batch(cursor, db_type, schema, table, batch_df, target_columns, audit_columns, username)
    
    table_ref = _format_table_ref(db_type, schema, table)
    
    # Build UPSERT SQL based on database type
    if db_type == "POSTGRESQL":
        # PostgreSQL: ON CONFLICT
        pk_str = ", ".join([_quote_identifier(col, db_type) for col in primary_key_columns])
        columns_str = ", ".join([_quote_identifier(col, db_type) for col in target_columns])
        placeholders = ", ".join(["%s"] * len(target_columns))
        
        # Build UPDATE clause (exclude primary keys and audit columns that shouldn't be updated)
        update_cols = []
        for col in target_columns:
            if col not in primary_key_columns:
                # Don't update CREATED_DATE or CREATED_BY
                if col in audit_columns:
                    audttyp = audit_columns[col]
                    if audttyp not in ("CREATED_DATE", "CREATED_BY"):
                        update_cols.append(f"{_quote_identifier(col, db_type)} = EXCLUDED.{_quote_identifier(col, db_type)}")
                else:
                    update_cols.append(f"{_quote_identifier(col, db_type)} = EXCLUDED.{_quote_identifier(col, db_type)}")
        
        upsert_sql = f"""
            INSERT INTO {table_ref} ({columns_str}) 
            VALUES ({placeholders})
            ON CONFLICT ({pk_str}) 
            DO UPDATE SET {', '.join(update_cols)}
        """
        
    elif db_type == "ORACLE":
        # Oracle: MERGE statement
        pk_conditions = " AND ".join([f"T.{_quote_identifier(col, db_type)} = S.{_quote_identifier(col, db_type)}" for col in primary_key_columns])
        columns_str = ", ".join([_quote_identifier(col, db_type) for col in target_columns])
        values_str = ", ".join([f"S.{_quote_identifier(col, db_type)}" for col in target_columns])
        
        # Build UPDATE clause
        update_cols = []
        for col in target_columns:
            if col not in primary_key_columns:
                if col in audit_columns:
                    audttyp = audit_columns[col]
                    if audttyp not in ("CREATED_DATE", "CREATED_BY"):
                        update_cols.append(f"T.{_quote_identifier(col, db_type)} = S.{_quote_identifier(col, db_type)}")
                else:
                    update_cols.append(f"T.{_quote_identifier(col, db_type)} = S.{_quote_identifier(col, db_type)}")
        
        upsert_sql = f"""
            MERGE INTO {table_ref} T
            USING (
                SELECT * FROM (
                    VALUES ({', '.join([f':{i+1}' for i in range(len(target_columns))])})
                ) AS S ({columns_str})
            ) S ON ({pk_conditions})
            WHEN MATCHED THEN UPDATE SET {', '.join(update_cols)}
            WHEN NOT MATCHED THEN INSERT ({columns_str}) VALUES ({values_str})
        """
        
    else:
        # MySQL, MS SQL Server: ON DUPLICATE KEY UPDATE or MERGE
        # For now, fall back to insert (can be enhanced later)
        warning(f"UPSERT not fully supported for {db_type}, falling back to INSERT")
        return _insert_batch(cursor, db_type, schema, table, batch_df, target_columns, audit_columns, username, column_types)
    
    rows_successful = 0
    rows_failed = 0
    errors = []
    
    current_time = datetime.now()
    batch_df = batch_df.reset_index(drop=True)
    
    # CRITICAL FIX: Reorder DataFrame columns to match target_columns order
    available_cols = [col for col in target_columns if col in batch_df.columns]
    missing_cols = [col for col in target_columns if col not in batch_df.columns]
    
    if missing_cols:
        warning(f"[_upsert_batch] Missing columns in DataFrame: {missing_cols}")
        for col in missing_cols:
            batch_df[col] = None
    
    # Reorder DataFrame columns to match target_columns exactly
    batch_df = batch_df[target_columns]
    
    # Pre-compute audit column values
    audit_values = {}
    for trg_col in target_columns:
        if trg_col in audit_columns:
            audttyp = audit_columns[trg_col]
            if audttyp == "CREATED_DATE" or audttyp == "UPDATED_DATE":
                audit_values[trg_col] = current_time
            elif audttyp == "CREATED_BY" or audttyp == "UPDATED_BY":
                audit_values[trg_col] = username or "SYSTEM"
            else:
                audit_values[trg_col] = None
    
    for row_idx in range(len(batch_df)):
        try:
            values = []
            for trg_col in target_columns:
                if trg_col in audit_values:
                    values.append(audit_values[trg_col])
                else:
                    # Use positional access (columns are now in same order as target_columns)
                    col_idx = target_columns.index(trg_col)
                    val = batch_df.iloc[row_idx, col_idx]
                    if pd.isna(val):
                        values.append(None)
                    else:
                        # Normalize value (convert string dates, etc.)
                        col_type = column_types.get(trg_col) if column_types else None
                        values.append(_normalize_db_value(val, col_type, db_type))
            
            # Execute upsert
            if db_type == "ORACLE":
                cursor.execute(upsert_sql, values)
            else:
                cursor.execute(upsert_sql, tuple(values))
            
            rows_successful += 1
            
        except Exception as e:
            rows_failed += 1
            row_dict = batch_df.iloc[row_idx].to_dict()
            serialized_row = {}
            for key, value in row_dict.items():
                if pd.isna(value):
                    serialized_row[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    serialized_row[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                else:
                    serialized_row[key] = value
            
            error_record = {
                'row_index': int(row_idx),
                'row_data': serialized_row,
                'error_message': str(e)
            }
            errors.append(error_record)
            warning(f"Error upserting row {row_idx}: {str(e)}")
    
    return {
        'rows_successful': rows_successful,
        'rows_failed': rows_failed,
        'errors': errors
    }
