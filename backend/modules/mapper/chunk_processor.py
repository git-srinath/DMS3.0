"""
Chunk Processor for parallel processing.
Handles processing of individual data chunks: extract, transform, load.
"""
import time
from typing import Dict, Any, List, Optional, Callable

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.common.db_table_utils import _detect_db_type  # type: ignore
    from modules.logger import info, warning, error, debug  # type: ignore

from .parallel_models import ChunkResult
from .chunk_manager import ChunkManager


class ChunkProcessor:
    """Processes a single chunk of data end-to-end"""
    
    def __init__(self, db_type: str):
        """
        Initialize chunk processor.
        
        Args:
            db_type: Database type ('POSTGRESQL' or 'ORACLE')
        """
        self.db_type = db_type.upper()
        self.chunk_manager = ChunkManager(db_type)
    
    def process_chunk(
        self,
        chunk_id: int,
        source_conn,
        original_sql: str,
        chunk_size: int,
        transformation_logic: Optional[Callable] = None,
        target_conn = None,
        target_schema: Optional[str] = None,
        target_table: Optional[str] = None,
        key_column: Optional[str] = None,
        retry_handler = None
    ) -> ChunkResult:
        """
        Process a single chunk end-to-end: extract, transform, load.
        
        Args:
            chunk_id: Zero-based chunk identifier
            source_conn: Source database connection
            original_sql: Original source SQL query
            chunk_size: Number of rows per chunk
            transformation_logic: Optional transformation function to apply
            target_conn: Optional target database connection (if None, uses source_conn)
            target_schema: Optional target schema name
            target_table: Optional target table name
            key_column: Optional key column for chunking
            retry_handler: Optional RetryHandler instance for retry logic
            
        Returns:
            ChunkResult with processing statistics
        """
        start_time = time.time()
        result = ChunkResult(chunk_id=chunk_id)
        
        try:
            # 1. Extract chunk data
            debug(f"[Chunk {chunk_id}] Starting extraction...")
            chunk_sql = self.chunk_manager.create_chunked_query(
                original_sql, chunk_id, chunk_size, key_column
            )
            
            source_cursor = source_conn.cursor()
            try:
                source_cursor.execute(chunk_sql)
                chunk_data = source_cursor.fetchall()
                columns = [desc[0].lower() if hasattr(desc, 'lower') else str(desc[0]).lower() 
                          for desc in source_cursor.description]
                # Handle different cursor description formats
                if not columns and source_cursor.description:
                    columns = [str(desc[0]).lower() for desc in source_cursor.description]
            finally:
                source_cursor.close()
            
            if not chunk_data:
                debug(f"[Chunk {chunk_id}] No data found, returning empty result")
                result.rows_processed = 0
                result.processing_time = time.time() - start_time
                return result
            
            result.rows_processed = len(chunk_data)
            debug(f"[Chunk {chunk_id}] Extracted {len(chunk_data)} rows")
            
            # 2. Transform data (if transformation logic provided)
            transformed_data = chunk_data
            if transformation_logic:
                debug(f"[Chunk {chunk_id}] Applying transformation...")
                try:
                    # Convert to list of dicts for transformation
                    rows_as_dicts = [
                        dict(zip(columns, row)) for row in chunk_data
                    ]
                    transformed_data = transformation_logic(rows_as_dicts)
                    debug(f"[Chunk {chunk_id}] Transformation complete: {len(transformed_data)} rows")
                except Exception as e:
                    error(f"[Chunk {chunk_id}] Transformation failed: {e}")
                    result.error = f"Transformation error: {str(e)}"
                    result.rows_failed = len(chunk_data)
                    result.processing_time = time.time() - start_time
                    return result
            
            # 3. Load to target (if target specified)
            if target_conn and target_schema and target_table:
                debug(f"[Chunk {chunk_id}] Loading to target table {target_schema}.{target_table}...")
                
                def load_chunk_data():
                    """Load data to target with retry support"""
                    return self._load_chunk(
                        target_conn,
                        target_schema,
                        target_table,
                        transformed_data,
                        columns
                    )
                
                # Use retry logic if configured
                if retry_handler:
                    load_result = retry_handler.execute_with_retry(
                        load_chunk_data,
                        f"[Chunk {chunk_id}] Load"
                    )
                else:
                    load_result = load_chunk_data()
                
                result.rows_successful = load_result.get('rows_successful', 0)
                result.rows_failed = load_result.get('rows_failed', 0)
                result.errors = load_result.get('errors', [])
                debug(f"[Chunk {chunk_id}] Load complete: {result.rows_successful} successful, {result.rows_failed} failed")
            else:
                # No target specified, just count rows
                result.rows_successful = len(transformed_data)
                debug(f"[Chunk {chunk_id}] No target table specified, skipping load")
            
        except Exception as e:
            error(f"[Chunk {chunk_id}] Processing failed: {e}", exc_info=True)
            result.error = str(e)
            result.rows_failed = result.rows_processed
            
        finally:
            result.processing_time = time.time() - start_time
            debug(f"[Chunk {chunk_id}] Processing complete in {result.processing_time:.2f}s")
        
        return result
    
    def _load_chunk(
        self,
        target_conn,
        target_schema: str,
        target_table: str,
        data: List[Any],
        columns: List[str]
    ) -> Dict[str, Any]:
        """
        Load chunk data into target table.
        
        Args:
            target_conn: Target database connection
            target_schema: Target schema name
            target_table: Target table name
            data: List of data rows (list of tuples or list of dicts)
            columns: Column names
            
        Returns:
            Dictionary with load statistics
        """
        target_db_type = _detect_db_type(target_conn)
        cursor = target_conn.cursor()
        
        rows_successful = 0
        rows_failed = 0
        errors = []
        
        try:
            # Build INSERT statement
            if target_db_type == "POSTGRESQL":
                table_ref = f'"{target_schema}"."{target_table}"' if target_schema else f'"{target_table}"'
                columns_str = ", ".join([f'"{col}"' for col in columns])
                placeholders = ", ".join(["%s"] * len(columns))
            else:  # Oracle
                table_ref = f"{target_schema}.{target_table}" if target_schema else target_table
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
            
            insert_sql = f"INSERT INTO {table_ref} ({columns_str}) VALUES ({placeholders})"
            
            # Convert data to tuples if needed
            if data and isinstance(data[0], dict):
                data_tuples = [tuple(row.get(col, None) for col in columns) for row in data]
            else:
                data_tuples = data
            
            # Insert rows
            for row_idx, row_data in enumerate(data_tuples):
                try:
                    if target_db_type == "ORACLE":
                        cursor.execute(insert_sql, list(row_data))
                    else:
                        cursor.execute(insert_sql, row_data)
                    rows_successful += 1
                except Exception as e:
                    rows_failed += 1
                    errors.append({
                        'row_index': row_idx,
                        'error_message': str(e)
                    })
                    if len(errors) <= 10:  # Limit error details
                        warning(f"Error inserting row {row_idx}: {str(e)}")
            
            target_conn.commit()
            
        except Exception as e:
            target_conn.rollback()
            error(f"Error loading chunk to target table: {e}")
            raise
        finally:
            cursor.close()
        
        return {
            'rows_successful': rows_successful,
            'rows_failed': rows_failed,
            'errors': errors
        }

