"""
File Upload Execution Service
Orchestrates the execution of file uploads: parsing, transformation, table creation, and data loading.
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from backend.database.dbconnect import create_metadata_connection, create_target_connection
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.logger import info, error, warning

from .file_upload_service import get_file_upload_details
from .file_parser import FileParserManager
from .formula_evaluator import FormulaEvaluator
from .table_creator import create_table_if_not_exists
from .data_loader import load_data, LoadMode


class FileUploadExecutor:
    """Executes file upload configurations."""
    
    def __init__(self):
        self.parser_manager = FileParserManager()
        self.formula_evaluator = FormulaEvaluator()
    
    def execute(
        self,
        flupldref: str,
        file_path: Optional[str] = None,
        load_mode: str = LoadMode.INSERT,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute file upload configuration.

        In addition to returning the execution summary, this method records
        execution history (DMS_FLUPLD_RUN) and row‑level error details
        (DMS_FLUPLD_ERR) in the metadata database.
        """
        execution_start_time = datetime.now()
        # Store username for use in transformation
        self._current_username = username or 'SYSTEM'
        
        metadata_conn = None
        target_conn = None
        
        try:
            # Step 1: Load configuration
            info(f"Loading configuration for {flupldref}")
            metadata_conn = create_metadata_connection()
            config = get_file_upload_config(metadata_conn, flupldref)
            
            if not config:
                raise ValueError(f"File upload configuration not found: {flupldref}")
            
            # Step 2: Get target connection
            trgconid = config.get('trgconid')
            if not trgconid:
                raise ValueError(f"Target connection ID not specified for {flupldref}")
            
            info(f"Connecting to target database (connection ID: {trgconid})")
            target_conn = create_target_connection(trgconid)
            if not target_conn:
                raise ValueError(f"Failed to connect to target database (connection ID: {trgconid})")
            
            # Step 3: Get file path
            if not file_path:
                file_path = config.get('flpth')
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            # Step 4: Get column mappings
            info(f"Loading column mappings for {flupldref}")
            column_mappings = get_file_upload_details(metadata_conn, flupldref)
            
            if not column_mappings:
                raise ValueError(f"No column mappings found for {flupldref}")
            
            # Step 5: Parse file
            info(f"Parsing file: {file_path}")
            file_type = config.get('fltyp', 'CSV')
            hdrrwcnt = config.get('hdrrwcnt', 0)
            ftrrwcnt = config.get('ftrrwcnt', 0)
            
            parse_options = {
                'header_rows': hdrrwcnt,
                'footer_rows': ftrrwcnt,
            }
            
            dataframe = self.parser_manager.parse_file(file_path, parse_options)
            info(f"Parsed {len(dataframe)} rows from file")
            
            # Step 6: Transform data (apply formulas, defaults, etc.)
            info("Transforming data (applying formulas and defaults)")
            dataframe = self._transform_data(dataframe, column_mappings)
            
            # Step 7: Create/verify target table
            trgschm = config.get('trgschm', '')
            trgtblnm = config.get('trgtblnm', '')
            
            if not trgtblnm:
                raise ValueError(f"Target table name not specified for {flupldref}")
            
            info(f"Creating/verifying target table: {trgschm}.{trgtblnm}")
            table_created = create_table_if_not_exists(
                target_conn, trgschm, trgtblnm, column_mappings, metadata_conn
            )
            
            # Step 8: Determine load mode
            # If config has trnctflg='Y', use TRUNCATE_LOAD unless explicitly overridden
            if config.get('trnctflg') == 'Y' and load_mode == LoadMode.INSERT:
                load_mode = LoadMode.TRUNCATE_LOAD
                info("trnctflg='Y' detected, using TRUNCATE_LOAD mode")
            
            # Step 9: Get batch size from config and validate
            batch_size = config.get('batch_size', 1000)
            if batch_size < 100:
                batch_size = 100
                warning(f"Batch size too small for {flupldref}, using minimum 100")
            elif batch_size > 100000:
                batch_size = 100000
                warning(f"Batch size too large for {flupldref}, capped at 100000")
            
            # Database-specific limits
            target_db_type = _detect_db_type(target_conn)
            if target_db_type == "ORACLE" and batch_size > 1000:
                batch_size = 1000
                warning(f"Batch size capped at 1000 for Oracle database")
            
            # Step 10: Load data
            info(f"Loading data using mode: {load_mode}, batch size: {batch_size}")
            load_result = load_data(
                target_conn,
                trgschm,
                trgtblnm,
                dataframe,
                column_mappings,
                load_mode=load_mode,
                batch_size=batch_size,
                username=username
            )

            # Step 11: Record execution history & error rows in metadata DB
            try:
                self._record_execution_history_and_errors(
                    metadata_conn=metadata_conn,
                    flupldref=flupldref,
                    file_path=file_path,
                    load_mode=load_mode,
                    username=username,
                    execution_start_time=execution_start_time,
                    execution_end_time=datetime.now(),
                    load_result=load_result,
                )
            except Exception as e:
                # Do not fail the main execution if history recording fails
                warning(f"Error recording execution history/error rows: {str(e)}")
            
            # Step 12: Update last run date
            self._update_last_run_date(metadata_conn, flupldref)
            
            # Step 13: Return results
            result = {
                'success': True,
                'message': f"File upload completed successfully. {load_result['rows_successful']} rows loaded, {load_result['rows_failed']} failed.",
                'rows_processed': load_result['rows_processed'],
                'rows_successful': load_result['rows_successful'],
                'rows_failed': load_result['rows_failed'],
                'errors': load_result['errors'],
                'table_created': table_created
            }
            
            info(f"Execution completed for {flupldref}: {result['rows_successful']} successful, {result['rows_failed']} failed")
            return result
            
        except Exception as e:
            error(f"Error executing file upload {flupldref}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Execution failed: {str(e)}",
                'rows_processed': 0,
                'rows_successful': 0,
                'rows_failed': 0,
                'errors': [{'error_message': str(e)}],
                'table_created': False
            }
        finally:
            if metadata_conn:
                try:
                    metadata_conn.close()
                except:
                    pass
            if target_conn:
                try:
                    target_conn.close()
                except:
                    pass
    
    def _transform_data(
        self,
        dataframe: pd.DataFrame,
        column_mappings: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform data by applying formulas, defaults, and column mappings.
        
        Args:
            dataframe: Source DataFrame
            column_mappings: List of column mapping dictionaries
            
        Returns:
            Transformed DataFrame
        """
        # Create a copy to avoid modifying original
        df = dataframe.copy()
        
        # Build mapping: source column -> target column
        src_to_trg = {}
        formulas = {}  # target column -> formula expression
        defaults = {}  # target column -> default value
        
        # Create a case-insensitive mapping of DataFrame column names
        df_cols_lower = {col.lower(): col for col in df.columns}
        
        # Get all target columns from mappings first (needed for later checks)
        all_target_columns = set()
        for col in column_mappings:
            trg_col = col.get('trgclnm', '').strip()
            if trg_col:
                all_target_columns.add(trg_col)
        
        for col in column_mappings:
            src_col = col.get('srcclnm', '').strip()
            trg_col = col.get('trgclnm', '').strip()
            drvlgc = col.get('drvlgc', '').strip()
            drvlgcflg = col.get('drvlgcflg', 'N')
            dfltval = col.get('dfltval', '').strip()
            
            if not trg_col:
                continue
            
            if src_col:
                # Try to find the actual column name in DataFrame (case-insensitive)
                actual_src_col = df_cols_lower.get(src_col.lower())
                if actual_src_col:
                    # Only add to mapping if source column actually exists in DataFrame
                    src_to_trg[actual_src_col] = trg_col
                    if actual_src_col != src_col:
                        info(f"Column name case mismatch: mapping '{src_col}' -> '{actual_src_col}' (from DataFrame) -> '{trg_col}'")
                # If source column doesn't exist, it will be handled by defaults or audit column logic
            
            # Track formulas
            if drvlgcflg == 'Y' and drvlgc:
                formulas[trg_col] = drvlgc
            
            # Track defaults
            if dfltval:
                defaults[trg_col] = dfltval
        
        # Log high-level mapping summary (avoid very verbose per-column logs)
        info(f"Source DataFrame columns: {list(df.columns)}")
        info(f"Total target columns: {len(all_target_columns)}, mapped from source: {len(src_to_trg)}")
        
        # Build list of row dictionaries for better performance
        # This is much faster than using pd.concat in a loop
        rows_data = []
        
        # Apply transformations row by row
        for idx, row in df.iterrows():
            # Build context for formula evaluation (uppercase column names)
            context = {}
            for src_col, trg_col in src_to_trg.items():
                if src_col in row:
                    context[src_col.upper()] = row[src_col] if pd.notna(row[src_col]) else None
                # Also add target column name for formulas that reference target columns
                context[trg_col.upper()] = row[src_col] if src_col in row and pd.notna(row[src_col]) else None
            
            # Build row data with target column names
            row_data = {}
            
            # Initialize all target columns
            for trg_col in all_target_columns:
                row_data[trg_col] = None
            
            # First, map source columns to target columns
            for src_col, trg_col in src_to_trg.items():
                if src_col in row.index:
                    value = row[src_col]
                    # Handle string values - strip whitespace, but preserve non-empty strings
                    if isinstance(value, str):
                        stripped = value.strip()
                        # Only convert to None if the stripped value is empty
                        value = stripped if stripped else None
                    elif pd.isna(value):
                        value = None
                    
                    row_data[trg_col] = value
                    
                    # Log first row mapping for debugging
                    if idx == 0 and trg_col == 'COD_ACCT_NO':
                        info(f"Row {idx}: Mapped '{src_col}' -> '{trg_col}' = '{row_data[trg_col]}' (original from row: '{row[src_col]}', type: {type(row[src_col]).__name__})")
                else:
                    # Log warning for first row only to avoid spam
                    if idx == 0:
                        warning(f"Source column '{src_col}' not found in DataFrame row. Available columns: {list(row.index)}")
                    row_data[trg_col] = None
                    if idx == 0 and trg_col == 'COD_ACCT_NO':
                        warning(f"Row {idx}: COD_ACCT_NO will be NULL because source column '{src_col}' not found in row.index")
            
            # Apply formulas (formulas override source column mappings)
            for trg_col, formula in formulas.items():
                try:
                    result = self.formula_evaluator.evaluate(formula, context)
                    row_data[trg_col] = result
                except Exception as e:
                    warning(f"Error evaluating formula for {trg_col} at row {idx}: {str(e)}")
                    # Use default if formula fails
                    if trg_col in defaults:
                        row_data[trg_col] = defaults[trg_col]
                    else:
                        row_data[trg_col] = None
            
            # Apply defaults for columns without values
            for trg_col, default_val in defaults.items():
                if trg_col not in row_data or row_data[trg_col] is None or (isinstance(row_data[trg_col], float) and pd.isna(row_data[trg_col])):
                    row_data[trg_col] = default_val
            
            # Add audit columns if they exist in target columns (only if not already set)
            current_time = datetime.now()
            username = getattr(self, '_current_username', 'SYSTEM')
            if 'CRTDBY' in all_target_columns and (row_data.get('CRTDBY') is None or (isinstance(row_data.get('CRTDBY'), float) and pd.isna(row_data.get('CRTDBY')))):
                row_data['CRTDBY'] = username
            if 'CRTDDT' in all_target_columns and (row_data.get('CRTDDT') is None or (isinstance(row_data.get('CRTDDT'), float) and pd.isna(row_data.get('CRTDDT')))):
                row_data['CRTDDT'] = current_time
            if 'UPDTBY' in all_target_columns and (row_data.get('UPDTBY') is None or (isinstance(row_data.get('UPDTBY'), float) and pd.isna(row_data.get('UPDTBY')))):
                row_data['UPDTBY'] = username
            if 'UPDTDT' in all_target_columns and (row_data.get('UPDTDT') is None or (isinstance(row_data.get('UPDTDT'), float) and pd.isna(row_data.get('UPDTDT')))):
                row_data['UPDTDT'] = current_time
            
            # Append row data to list
            rows_data.append(row_data)
        
        # Create DataFrame from list of dictionaries (much faster than pd.concat in loop)
        # Ensure all target columns are present by explicitly setting columns
        target_df = pd.DataFrame(rows_data)
        
        # Ensure all target columns are present (in case some rows didn't have all columns)
        for trg_col in all_target_columns:
            if trg_col not in target_df.columns:
                warning(f"Target column '{trg_col}' missing from DataFrame, adding as NULL column")
                target_df[trg_col] = None
        
        # Reorder columns to match target_columns order for consistency
        # Get columns in order: first all_target_columns, then any extras
        ordered_columns = [col for col in all_target_columns if col in target_df.columns]
        ordered_columns.extend([col for col in target_df.columns if col not in ordered_columns])
        target_df = target_df[ordered_columns]
        
        # Log concise summary of transformed data
        if len(target_df) > 0:
            info(f"Transformed DataFrame shape: {target_df.shape}")
            info(f"Transformed DataFrame columns: {list(target_df.columns)}")
        
        return target_df

    def _record_execution_history_and_errors(
        self,
        metadata_conn,
        flupldref: str,
        file_path: Optional[str],
        load_mode: str,
        username: Optional[str],
        execution_start_time: datetime,
        execution_end_time: datetime,
        load_result: Dict[str, Any],
    ) -> None:
        """
        Persist execution history (DMS_FLUPLD_RUN) and error rows (DMS_FLUPLD_ERR)
        into the metadata database.
        """
        from backend.modules.helper_functions import _get_table_ref

        if metadata_conn is None:
            warning("Metadata connection is None; cannot record execution history or errors")
            return

        cursor = metadata_conn.cursor()
        db_type = _detect_db_type(metadata_conn)

        rows_processed = int(load_result.get("rows_processed", 0))
        rows_successful = int(load_result.get("rows_successful", 0))
        rows_failed = int(load_result.get("rows_failed", 0))
        errors = load_result.get("errors", []) or []

        # Determine status
        if rows_failed == 0:
            status = "SUCCESS"
        elif rows_successful == 0:
            status = "FAILED"
        else:
            status = "PARTIAL"

        # Summary message: use first error message if any
        message = None
        if errors:
            first_err = errors[0]
            message = str(first_err.get("error_message") or "")[:1000]

        # Insert into DMS_FLUPLD_RUN and get runid
        runid = None
        try:
            if db_type == "POSTGRESQL":
                table_name = "dms_flupld_run"
                cursor.execute(
                    f"""
                    INSERT INTO {table_name}
                    (flupldref, strttm, ndtm, rwsprcssd, rwsstccssfl, rwsfld,
                     stts, mssg, ldmde, flpth, crtdby, crtdt, curflg)
                    VALUES (%s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'Y')
                    RETURNING runid
                    """,
                    (
                        flupldref,
                        execution_start_time,
                        execution_end_time,
                        rows_processed,
                        rows_successful,
                        rows_failed,
                        status,
                        message,
                        load_mode,
                        file_path,
                        username or "SYSTEM",
                    ),
                )
                runid = cursor.fetchone()[0]
            else:
                table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD_RUN")

                if db_type == "ORACLE":
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name}
                        (flupldref, strttm, ndtm, rwsprcssd, rwsstccssfl, rwsfld,
                         stts, mssg, ldmde, flpth, crtdby, crtdt, curflg)
                        VALUES (:1, :2, :3, :4, :5, :6,
                                :7, :8, :9, :10, :11, SYSTIMESTAMP, 'Y')
                        """,
                        [
                            flupldref,
                            execution_start_time,
                            execution_end_time,
                            rows_processed,
                            rows_successful,
                            rows_failed,
                            status,
                            message,
                            load_mode,
                            file_path,
                            username or "SYSTEM",
                        ],
                    )
                    cursor.execute(
                        f"""
                        SELECT runid
                        FROM {table_name}
                        WHERE flupldref = :1
                        ORDER BY strttm DESC FETCH FIRST 1 ROWS ONLY
                        """,
                        [flupldref],
                    )
                    row = cursor.fetchone()
                    if row:
                        runid = row[0]
                else:
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name}
                        (flupldref, strttm, ndtm, rwsprcssd, rwsstccssfl, rwsfld,
                         stts, mssg, ldmde, flpth, crtdby, crtdt, curflg)
                        VALUES (%s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'Y')
                        """,
                        (
                            flupldref,
                            execution_start_time,
                            execution_end_time,
                            rows_processed,
                            rows_successful,
                            rows_failed,
                            status,
                            message,
                            load_mode,
                            file_path,
                            username or "SYSTEM",
                        ),
                    )
        except Exception as e:
            error(f"Error inserting into DMS_FLUPLD_RUN: {str(e)}", exc_info=True)
            metadata_conn.rollback()
            cursor.close()
            return

        # Insert error rows into DMS_FLUPLD_ERR (if any)
        if errors:
            try:
                if db_type == "POSTGRESQL":
                    table_name_err = "dms_flupld_err"
                    insert_sql = f"""
                        INSERT INTO {table_name_err}
                        (flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """
                else:
                    table_name_err = _get_table_ref(cursor, db_type, "DMS_FLUPLD_ERR")
                    if db_type == "ORACLE":
                        insert_sql = f"""
                            INSERT INTO {table_name_err}
                            (flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt)
                            VALUES (:1, :2, :3, :4, :5, :6, :7, SYSTIMESTAMP)
                        """
                    else:
                        insert_sql = f"""
                            INSERT INTO {table_name_err}
                            (flupldref, runid, rwndx, rwdtjsn, rrcd, rrmssg, crtdby, crtdt)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """

                for err in errors:
                    row_index = int(err.get("row_index", -1))
                    row_data = err.get("row_data") or {}
                    row_json = json.dumps(row_data, default=str)
                    full_message = str(err.get("error_message") or "")
                    m = re.search(r"([A-Z]+-\d+)", full_message)
                    error_code = m.group(1) if m else None

                    if db_type == "ORACLE":
                        params = [
                            flupldref,
                            runid,
                            row_index,
                            row_json,
                            error_code,
                            full_message,
                            username or "SYSTEM",
                        ]
                    else:
                        params = (
                            flupldref,
                            runid,
                            row_index,
                            row_json,
                            error_code,
                            full_message,
                            username or "SYSTEM",
                        )

                    cursor.execute(insert_sql, params)

            except Exception as e:
                error(f"Error inserting into DMS_FLUPLD_ERR: {str(e)}", exc_info=True)
                metadata_conn.rollback()
                cursor.close()
                return

        try:
            metadata_conn.commit()
        except Exception as e:
            error(f"Error committing execution history/error rows: {str(e)}", exc_info=True)
            metadata_conn.rollback()
        finally:
            cursor.close()
    
    def _update_last_run_date(self, connection, flupldref: str):
        """Update last run date in DMS_FLUPLD."""
        from backend.modules.common.db_table_utils import _detect_db_type
        from backend.modules.helper_functions import _get_table_ref
        
        cursor = connection.cursor()
        db_type = _detect_db_type(connection)
        table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
        
        try:
            current_time = datetime.now()
            
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"UPDATE {table_name} SET lstrundt = %s WHERE flupldref = %s",
                    (current_time, flupldref)
                )
            else:  # Oracle
                cursor.execute(
                    f"UPDATE {table_name} SET lstrundt = :1 WHERE flupldref = :2",
                    [current_time, flupldref]
                )
            
            connection.commit()
            info(f"Updated last run date for {flupldref}")
        except Exception as e:
            warning(f"Error updating last run date: {str(e)}")
            connection.rollback()
        finally:
            cursor.close()


def get_file_upload_config(connection, flupldref: str) -> Optional[Dict[str, Any]]:
    """
    Get file upload configuration by reference.
    
    Args:
        connection: Database connection
        flupldref: File upload reference
        
    Returns:
        Configuration dictionary or None if not found
    """
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.helper_functions import _get_table_ref
    
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
    
    try:
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT flupldid, flupldref, fluplddesc, flnm, flpth, fltyp,
                       trgconid, trgschm, trgtblnm, trnctflg, hdrrwcnt, ftrrwcnt,
                       hdrrwpttrn, ftrrwpttrn, frqcd, stflg, lstrundt, nxtrundt
                FROM {table_name}
                WHERE flupldref = %s AND curflg = 'Y'
            """
            cursor.execute(query, (flupldref,))
        else:  # Oracle
            query = f"""
                SELECT flupldid, flupldref, fluplddesc, flnm, flpth, fltyp,
                       trgconid, trgschm, trgtblnm, trnctflg, hdrrwcnt, ftrrwcnt,
                       hdrrwpttrn, ftrrwpttrn, frqcd, stflg, lstrundt, nxtrundt
                FROM {table_name}
                WHERE flupldref = :1 AND curflg = 'Y'
            """
            cursor.execute(query, [flupldref])
        
        columns = [desc[0].lower() for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return None
        
    except Exception as e:
        error(f"Error getting file upload config: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()

