"""
Chunk Manager for parallel processing.
Handles chunking strategies for different database types and data sources.
"""
from typing import Optional, Tuple
import re

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.common.db_table_utils import _detect_db_type  # type: ignore
    from modules.logger import info, warning, error, debug  # type: ignore

from .parallel_models import ChunkingStrategy, ChunkConfig


class ChunkManager:
    """Manages chunking strategies for different data sources"""
    
    def __init__(self, db_type: str):
        """
        Initialize chunk manager.
        
        Args:
            db_type: Database type ('POSTGRESQL' or 'ORACLE')
        """
        self.db_type = db_type.upper()
    
    def estimate_total_rows(
        self,
        connection,
        source_sql: str,
        source_schema: Optional[str] = None
    ) -> int:
        """
        Estimate total number of rows in source query.
        
        Args:
            connection: Database connection
            source_sql: Source SQL query
            source_schema: Optional source schema
            
        Returns:
            Estimated row count
        """
        cursor = connection.cursor()
        try:
            # Wrap source SQL in COUNT query
            count_sql = f"SELECT COUNT(*) FROM ({source_sql}) subq"
            
            if self.db_type == "POSTGRESQL":
                cursor.execute(count_sql)
            else:  # Oracle
                cursor.execute(count_sql)
            
            result = cursor.fetchone()
            return int(result[0]) if result else 0
        except Exception as e:
            warning(f"Failed to estimate total rows: {e}, assuming 0")
            return 0
        finally:
            cursor.close()
    
    def create_chunked_query(
        self,
        original_sql: str,
        chunk_id: int,
        chunk_size: int,
        key_column: Optional[str] = None
    ) -> str:
        """
        Create a chunked version of the source SQL.
        
        Args:
            original_sql: Original source SQL query
            chunk_id: Zero-based chunk identifier
            chunk_size: Number of rows per chunk
            key_column: Optional key column for KEY_BASED chunking
            
        Returns:
            Modified SQL query for this chunk
        """
        if key_column and self.db_type == "POSTGRESQL":
            # Key-based chunking (more efficient)
            return self._create_key_based_chunk_query(
                original_sql, chunk_id, chunk_size, key_column
            )
        else:
            # OFFSET/LIMIT chunking (works for all databases)
            return self._create_offset_limit_chunk_query(
                original_sql, chunk_id, chunk_size
            )
    
    def _create_offset_limit_chunk_query(
        self,
        sql: str,
        chunk_id: int,
        chunk_size: int
    ) -> str:
        """
        Create chunk query using OFFSET/LIMIT pattern.
        Works for PostgreSQL, MySQL, and most databases.
        """
        offset = chunk_id * chunk_size
        
        if self.db_type == "POSTGRESQL":
            return f"""
                SELECT * FROM (
                    {sql}
                ) subq
                LIMIT {chunk_size} OFFSET {offset}
            """
        elif self.db_type == "ORACLE":
            # Oracle uses ROWNUM or OFFSET/FETCH (Oracle 12c+)
            # Try OFFSET/FETCH first (Oracle 12c+), fallback to ROWNUM
            return f"""
                SELECT * FROM (
                    SELECT subq.*, ROWNUM as rn FROM (
                        {sql}
                    ) subq WHERE ROWNUM <= {offset + chunk_size}
                ) WHERE rn > {offset}
            """
        else:
            # Default to LIMIT/OFFSET (MySQL, etc.)
            return f"""
                SELECT * FROM (
                    {sql}
                ) subq
                LIMIT {chunk_size} OFFSET {offset}
            """
    
    def _create_key_based_chunk_query(
        self,
        sql: str,
        chunk_id: int,
        chunk_size: int,
        key_column: str
    ) -> str:
        """
        Create chunk query using key column ranges.
        More efficient than OFFSET/LIMIT for large datasets.
        Requires ordered key column.
        """
        # This requires pre-calculated key ranges
        # For now, we'll use a subquery approach with ROW_NUMBER
        # In production, key ranges should be pre-calculated
        
        offset = chunk_id * chunk_size
        end_offset = offset + chunk_size
        
        if self.db_type == "POSTGRESQL":
            return f"""
                SELECT * FROM (
                    SELECT *, ROW_NUMBER() OVER (ORDER BY {key_column}) as rn
                    FROM ({sql}) subq
                ) numbered
                WHERE rn > {offset} AND rn <= {end_offset}
                ORDER BY {key_column}
            """
        elif self.db_type == "ORACLE":
            return f"""
                SELECT * FROM (
                    SELECT subq.*, ROW_NUMBER() OVER (ORDER BY {key_column}) as rn
                    FROM ({sql}) subq
                ) numbered
                WHERE rn > {offset} AND rn <= {end_offset}
                ORDER BY {key_column}
            """
        else:
            # Fallback to OFFSET/LIMIT for other databases
            return self._create_offset_limit_chunk_query(sql, chunk_id, chunk_size)
    
    def detect_key_column(
        self,
        connection,
        source_sql: str
    ) -> Optional[str]:
        """
        Attempt to detect a suitable key column from the source SQL.
        Looks for primary key columns or ordered columns.
        
        Args:
            connection: Database connection
            source_sql: Source SQL query
            
        Returns:
            Key column name if found, None otherwise
        """
        # Try to extract ORDER BY clause
        order_by_match = re.search(r'ORDER\s+BY\s+([^\s,\(\)]+)', source_sql, re.IGNORECASE)
        if order_by_match:
            key_col = order_by_match.group(1).strip()
            # Remove table alias if present
            if '.' in key_col:
                key_col = key_col.split('.')[-1]
            return key_col
        
        # Could also query INFORMATION_SCHEMA for primary keys
        # For now, return None and use OFFSET/LIMIT
        return None
    
    def calculate_chunk_config(
        self,
        connection,
        source_sql: str,
        chunk_size: int,
        source_schema: Optional[str] = None
    ) -> ChunkConfig:
        """
        Calculate chunking configuration for a source query.
        
        Args:
            connection: Database connection
            source_sql: Source SQL query
            chunk_size: Desired chunk size
            source_schema: Optional source schema
            
        Returns:
            ChunkConfig with strategy and chunk count
        """
        # Estimate total rows
        total_rows = self.estimate_total_rows(connection, source_sql, source_schema)
        
        # Try to detect key column for key-based chunking
        key_column = self.detect_key_column(connection, source_sql)
        
        # Determine strategy
        if key_column:
            strategy = ChunkingStrategy.KEY_BASED
        else:
            strategy = ChunkingStrategy.OFFSET_LIMIT
        
        # Calculate number of chunks
        num_chunks = (total_rows + chunk_size - 1) // chunk_size if total_rows > 0 else 1
        
        return ChunkConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            key_column=key_column,
            total_rows=total_rows,
            num_chunks=num_chunks
        )

