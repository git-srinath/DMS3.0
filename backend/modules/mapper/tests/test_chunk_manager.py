"""
Unit tests for ChunkManager.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from backend.modules.mapper.chunk_manager import ChunkManager
from backend.modules.mapper.parallel_models import ChunkingStrategy


class TestChunkManager(unittest.TestCase):
    """Test cases for ChunkManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.postgresql_manager = ChunkManager("POSTGRESQL")
        self.oracle_manager = ChunkManager("ORACLE")
    
    def test_create_offset_limit_query_postgresql(self):
        """Test OFFSET/LIMIT query generation for PostgreSQL"""
        sql = "SELECT * FROM test_table"
        chunk_sql = self.postgresql_manager._create_offset_limit_chunk_query(sql, 0, 100)
        
        self.assertIn("LIMIT 100", chunk_sql)
        self.assertIn("OFFSET 0", chunk_sql)
        self.assertIn("SELECT * FROM (", chunk_sql)
    
    def test_create_offset_limit_query_oracle(self):
        """Test OFFSET/LIMIT query generation for Oracle"""
        sql = "SELECT * FROM test_table"
        chunk_sql = self.oracle_manager._create_offset_limit_chunk_query(sql, 1, 100)
        
        self.assertIn("ROWNUM", chunk_sql)
        self.assertIn("> 100", chunk_sql)  # offset = 1 * 100 = 100
        self.assertIn("<= 200", chunk_sql)  # offset + chunk_size = 200
    
    def test_create_key_based_query_postgresql(self):
        """Test key-based query generation for PostgreSQL"""
        sql = "SELECT * FROM test_table"
        chunk_sql = self.postgresql_manager._create_key_based_chunk_query(
            sql, 0, 100, "id"
        )
        
        self.assertIn("ROW_NUMBER()", chunk_sql)
        self.assertIn("ORDER BY id", chunk_sql)
        self.assertIn("rn > 0", chunk_sql)
        self.assertIn("rn <= 100", chunk_sql)
    
    def test_detect_key_column_with_order_by(self):
        """Test key column detection from ORDER BY clause"""
        sql = "SELECT * FROM test_table ORDER BY id DESC"
        key_col = self.postgresql_manager.detect_key_column(None, sql)
        
        self.assertEqual(key_col, "id")
    
    def test_detect_key_column_with_table_alias(self):
        """Test key column detection with table alias"""
        sql = "SELECT * FROM test_table t ORDER BY t.id"
        key_col = self.postgresql_manager.detect_key_column(None, sql)
        
        self.assertEqual(key_col, "id")
    
    def test_detect_key_column_no_order_by(self):
        """Test key column detection when no ORDER BY exists"""
        sql = "SELECT * FROM test_table"
        key_col = self.postgresql_manager.detect_key_column(None, sql)
        
        self.assertIsNone(key_col)
    
    @patch('backend.modules.mapper.chunk_manager.ChunkManager.estimate_total_rows')
    def test_calculate_chunk_config(self, mock_estimate):
        """Test chunk configuration calculation"""
        mock_estimate.return_value = 250000
        
        mock_conn = Mock()
        sql = "SELECT * FROM test_table ORDER BY id"
        
        config = self.postgresql_manager.calculate_chunk_config(
            mock_conn, sql, 50000
        )
        
        self.assertEqual(config.total_rows, 250000)
        self.assertEqual(config.chunk_size, 50000)
        self.assertEqual(config.num_chunks, 5)  # 250000 / 50000 = 5
        self.assertIsNotNone(config.key_column)  # Should detect 'id' from ORDER BY
    
    def test_estimate_total_rows(self):
        """Test total row estimation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1000,)
        mock_cursor.description = None
        
        sql = "SELECT * FROM test_table"
        
        total = self.postgresql_manager.estimate_total_rows(mock_conn, sql)
        
        self.assertEqual(total, 1000)
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_estimate_total_rows_error_handling(self):
        """Test error handling in row estimation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query failed")
        
        sql = "SELECT * FROM test_table"
        
        total = self.postgresql_manager.estimate_total_rows(mock_conn, sql)
        
        self.assertEqual(total, 0)  # Should return 0 on error


if __name__ == '__main__':
    unittest.main()

