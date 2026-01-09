"""
Streaming File Upload Executor
Processes files in chunks without loading entire file into memory.
Designed for large files that would cause memory issues with full DataFrame approach.
"""
import os
import json
import re
from typing import Dict, Any, Optional, List, Iterator
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


class StreamingFileExecutor:
    """
    Executes file uploads using streaming/chunked processing.
    Processes files in chunks (e.g., 10,000 rows) instead of loading entire file.
    """
    
    def __init__(self, chunk_size: int = 10000):
        """
        Initialize streaming executor.
        
        Args:
            chunk_size: Number of rows to process per chunk (default: 10,000)
        """
        self.parser_manager = FileParserManager()
        self.formula_evaluator = FormulaEvaluator()
        self.chunk_size = chunk_size
    
    def execute(
        self,
        flupldref: str,
        file_path: Optional[str] = None,
        load_mode: str = LoadMode.INSERT,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute file upload using streaming processing.
        
        This method processes the file in chunks, avoiding memory issues
        with large files. Each chunk is:
        1. Parsed from file
        2. Transformed (formulas, defaults, mappings)
        3. Loaded into database
        4. Memory released before next chunk
        
        Args:
            flupldref: File upload reference
            file_path: Optional file path (uses config path if not provided)
            load_mode: Load mode (INSERT, TRUNCATE_LOAD, UPSERT)
            username: Username for audit columns
            
        Returns:
            Dictionary with execution results
        """
        execution_start_time = datetime.now()
        self._current_username = username or 'SYSTEM'
        
        metadata_conn = None
        target_conn = None
        
        try:
            # Step 1: Load configuration
            info(f"[Streaming] Loading configuration for {flupldref}")
            metadata_conn = create_metadata_connection()
            config = get_file_upload_config(metadata_conn, flupldref)
            
            if not config:
                raise ValueError(f"File upload configuration not found: {flupldref}")
            
            # Step 2: Get target connection
            trgconid = config.get('trgconid')
            if not trgconid:
                raise ValueError(f"Target connection ID not specified for {flupldref}")
            
            info(f"[Streaming] Connecting to target database (connection ID: {trgconid})")
            target_conn = create_target_connection(trgconid)
            if not target_conn:
                raise ValueError(f"Failed to connect to target database (connection ID: {trgconid})")
            
            # Step 3: Get file path
            if not file_path:
                file_path = config.get('flpth')
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            # Step 4: Get column mappings
            info(f"[Streaming] Loading column mappings for {flupldref}")
            column_mappings = get_file_upload_details(metadata_conn, flupldref)
            
            if not column_mappings:
                raise ValueError(f"No column mappings found for {flupldref}")
            
            # Step 5: Create/verify target table (before processing)
            trgschm = config.get('trgschm', '')
            trgtblnm = config.get('trgtblnm', '')
            
            if not trgtblnm:
                raise ValueError(f"Target table name not specified for {flupldref}")
            
            info(f"[Streaming] Creating/verifying target table: {trgschm}.{trgtblnm}")
            table_created = create_table_if_not_exists(
                target_conn, trgschm, trgtblnm, column_mappings, metadata_conn
            )
            
            # Step 6: Determine load mode
            if config.get('trnctflg') == 'Y' and load_mode == LoadMode.INSERT:
                load_mode = LoadMode.TRUNCATE_LOAD
                info("[Streaming] trnctflg='Y' detected, using TRUNCATE_LOAD mode")
            
            # Step 7: Get batch size from config
            batch_size = config.get('batch_size', 1000)
            if batch_size < 100:
                batch_size = 100
            elif batch_size > 100000:
                batch_size = 100000
            
            target_db_type = _detect_db_type(target_conn)
            if target_db_type == "ORACLE" and batch_size > 1000:
                batch_size = 1000
            
            # Step 8: Truncate if needed (only once, before processing chunks)
            if load_mode == LoadMode.TRUNCATE_LOAD:
                from .data_loader import _truncate_table, _format_table_ref
                table_ref = _format_table_ref(target_db_type, trgschm, trgtblnm)
                cursor = target_conn.cursor()
                if target_db_type == "POSTGRESQL":
                    cursor.execute(f"TRUNCATE TABLE {table_ref}")
                else:  # Oracle
                    cursor.execute(f"TRUNCATE TABLE {table_ref}")
                target_conn.commit()
                cursor.close()
                info(f"[Streaming] Truncated table {trgschm}.{trgtblnm}")
            
            # Step 9: Process file in chunks
            info(f"[Streaming] Starting streaming processing: chunk_size={self.chunk_size}, batch_size={batch_size}")
            
            file_type = config.get('fltyp', 'CSV')
            hdrrwcnt = config.get('hdrrwcnt', 0)
            ftrrwcnt = config.get('ftrrwcnt', 0)
            
            parse_options = {
                'header_rows': hdrrwcnt,
                'footer_rows': ftrrwcnt,
            }
            
            # Get file parser
            parser = self.parser_manager.get_parser(file_path)
            if not parser:
                raise ValueError(f"No parser available for file: {file_path}")
            
            # Process file in chunks
            total_rows_processed = 0
            total_rows_successful = 0
            total_rows_failed = 0
            all_errors = []
            chunk_number = 0
            is_first_chunk = True
            
            # Use chunked reading if parser supports it (CSV)
            if file_type.upper() == 'CSV' and hasattr(parser, 'parse_chunked'):
                # Stream CSV in chunks
                for chunk_df in parser.parse_chunked(file_path, parse_options, chunk_size=self.chunk_size):
                    chunk_number += 1
                    info(f"[Streaming] Processing chunk {chunk_number} ({len(chunk_df)} rows)")
                    
                    # Transform chunk
                    transformed_chunk = self._transform_data(chunk_df, column_mappings)
                    
                    # Load chunk to database
                    chunk_result = load_data(
                        target_conn,
                        trgschm,
                        trgtblnm,
                        transformed_chunk,
                        column_mappings,
                        load_mode=LoadMode.INSERT if not is_first_chunk else load_mode,  # Only truncate on first chunk
                        batch_size=batch_size,
                        username=username
                    )
                    
                    total_rows_processed += chunk_result['rows_processed']
                    total_rows_successful += chunk_result['rows_successful']
                    total_rows_failed += chunk_result['rows_failed']
                    all_errors.extend(chunk_result['errors'])
                    
                    is_first_chunk = False
                    
                    # Log progress
                    info(f"[Streaming] Chunk {chunk_number} complete: {chunk_result['rows_successful']} successful, {chunk_result['rows_failed']} failed")
                    
                    # Release memory
                    del chunk_df
                    del transformed_chunk
            else:
                # For non-CSV or parsers without chunked support, use iterator approach
                # Parse file and process in chunks using pandas chunking
                if file_type.upper() == 'CSV':
                    # Use pandas read_csv with chunksize
                    chunk_iterator = pd.read_csv(
                        file_path,
                        chunksize=self.chunk_size,
                        skiprows=hdrrwcnt,
                        engine='python'  # More compatible engine
                    )
                    
                    for chunk_df in chunk_iterator:
                        chunk_number += 1
                        info(f"[Streaming] Processing chunk {chunk_number} ({len(chunk_df)} rows)")
                        
                        # Transform chunk
                        transformed_chunk = self._transform_data(chunk_df, column_mappings)
                        
                        # Load chunk to database
                        chunk_result = load_data(
                            target_conn,
                            trgschm,
                            trgtblnm,
                            transformed_chunk,
                            column_mappings,
                            load_mode=LoadMode.INSERT if not is_first_chunk else load_mode,
                            batch_size=batch_size,
                            username=username
                        )
                        
                        total_rows_processed += chunk_result['rows_processed']
                        total_rows_successful += chunk_result['rows_successful']
                        total_rows_failed += chunk_result['rows_failed']
                        all_errors.extend(chunk_result['errors'])
                        
                        is_first_chunk = False
                        
                        info(f"[Streaming] Chunk {chunk_number} complete: {chunk_result['rows_successful']} successful, {chunk_result['rows_failed']} failed")
                        
                        # Release memory
                        del chunk_df
                        del transformed_chunk
                else:
                    # For Excel, JSON, etc., fall back to full parse but warn
                    warning(f"[Streaming] File type {file_type} doesn't support chunked parsing, using full parse (may use more memory)")
                    dataframe = self.parser_manager.parse_file(file_path, parse_options)
                    info(f"[Streaming] Parsed {len(dataframe)} rows from file")
                    
                    # Process in chunks from full DataFrame
                    total_rows = len(dataframe)
                    num_chunks = (total_rows + self.chunk_size - 1) // self.chunk_size
                    
                    for chunk_num in range(num_chunks):
                        chunk_number += 1
                        start_idx = chunk_num * self.chunk_size
                        end_idx = min(start_idx + self.chunk_size, total_rows)
                        chunk_df = dataframe.iloc[start_idx:end_idx].copy()
                        
                        info(f"[Streaming] Processing chunk {chunk_number}/{num_chunks} (rows {start_idx + 1}-{end_idx})")
                        
                        # Transform chunk
                        transformed_chunk = self._transform_data(chunk_df, column_mappings)
                        
                        # Load chunk to database
                        chunk_result = load_data(
                            target_conn,
                            trgschm,
                            trgtblnm,
                            transformed_chunk,
                            column_mappings,
                            load_mode=LoadMode.INSERT if not is_first_chunk else load_mode,
                            batch_size=batch_size,
                            username=username
                        )
                        
                        total_rows_processed += chunk_result['rows_processed']
                        total_rows_successful += chunk_result['rows_successful']
                        total_rows_failed += chunk_result['rows_failed']
                        all_errors.extend(chunk_result['errors'])
                        
                        is_first_chunk = False
                        
                        info(f"[Streaming] Chunk {chunk_number} complete: {chunk_result['rows_successful']} successful, {chunk_result['rows_failed']} failed")
                        
                        # Release memory
                        del chunk_df
                        del transformed_chunk
            
            # Step 10: Record execution history & errors
            try:
                self._record_execution_history_and_errors(
                    metadata_conn=metadata_conn,
                    flupldref=flupldref,
                    file_path=file_path,
                    load_mode=load_mode,
                    username=username,
                    execution_start_time=execution_start_time,
                    execution_end_time=datetime.now(),
                    load_result={
                        'rows_processed': total_rows_processed,
                        'rows_successful': total_rows_successful,
                        'rows_failed': total_rows_failed,
                        'errors': all_errors
                    },
                )
            except Exception as e:
                warning(f"[Streaming] Error recording execution history/error rows: {str(e)}")
            
            # Step 11: Update last run date
            self._update_last_run_date(metadata_conn, flupldref)
            
            # Step 12: Return results
            result = {
                'success': True,
                'message': f"File upload completed successfully. {total_rows_successful} rows loaded, {total_rows_failed} failed.",
                'rows_processed': total_rows_processed,
                'rows_successful': total_rows_successful,
                'rows_failed': total_rows_failed,
                'errors': all_errors,
                'table_created': table_created
            }
            
            info(f"[Streaming] Execution completed for {flupldref}: {total_rows_successful} successful, {total_rows_failed} failed")
            return result
            
        except Exception as e:
            error(f"[Streaming] Error executing file upload {flupldref}: {str(e)}", exc_info=True)
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
        Transform data chunk by applying formulas, defaults, and column mappings.
        Same logic as FileUploadExecutor but optimized for chunks.
        """
        # Reuse the same transformation logic from FileUploadExecutor
        from .file_upload_executor import FileUploadExecutor
        executor = FileUploadExecutor()
        executor._current_username = self._current_username
        return executor._transform_data(dataframe, column_mappings)
    
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
        """Record execution history and errors (same as FileUploadExecutor)."""
        from .file_upload_executor import FileUploadExecutor
        executor = FileUploadExecutor()
        executor._record_execution_history_and_errors(
            metadata_conn, flupldref, file_path, load_mode, username,
            execution_start_time, execution_end_time, load_result
        )
    
    def _update_last_run_date(self, connection, flupldref: str):
        """Update last run date (same as FileUploadExecutor)."""
        from .file_upload_executor import FileUploadExecutor
        executor = FileUploadExecutor()
        executor._update_last_run_date(connection, flupldref)


def get_file_upload_config(connection, flupldref: str) -> Optional[Dict[str, Any]]:
    """Get file upload configuration (reuse from file_upload_executor)."""
    from .file_upload_executor import get_file_upload_config as _get_config
    return _get_config(connection, flupldref)

