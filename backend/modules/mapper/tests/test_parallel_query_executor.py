"""
Unit tests for parallel_query_executor.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import os
from backend.modules.mapper.parallel_query_executor import (
    execute_query_parallel,
    get_parallel_config
)


class TestParallelQueryExecutor(unittest.TestCase):
    """Test cases for parallel_query_executor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_source_conn = Mock()
        self.mock_target_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_source_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.description = [('col1',), ('col2',)]
        self.mock_cursor.fetchone.return_value = (1000,)  # Row count
    
    @patch('backend.modules.mapper.parallel_query_executor.ParallelProcessor')
    def test_execute_query_parallel_basic(self, mock_processor_class):
        """Test basic parallel query execution"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_result = Mock()
        mock_result.total_rows_processed = 1000
        mock_processor.process_mapper_job.return_value = mock_result
        
        result = execute_query_parallel(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table",
            target_conn=self.mock_target_conn,
            target_schema="target_schema",
            target_table="target_table"
        )
        
        self.assertEqual(result.total_rows_processed, 1000)
        mock_processor.process_mapper_job.assert_called_once()
    
    @patch('backend.modules.mapper.parallel_query_executor.ParallelProcessor')
    @patch.dict(os.environ, {'MAPPER_PARALLEL_ENABLED': 'false'})
    def test_execute_query_parallel_env_disabled(self, mock_processor_class):
        """Test that environment variable can disable parallel processing"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        execute_query_parallel(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table"
        )
        
        # Verify processor was created with enable_parallel=False
        call_args = mock_processor_class.call_args
        self.assertFalse(call_args.kwargs['enable_parallel'])
    
    @patch('backend.modules.mapper.parallel_query_executor.ParallelProcessor')
    @patch.dict(os.environ, {'MAPPER_MAX_WORKERS': '8', 'MAPPER_CHUNK_SIZE': '100000'})
    def test_execute_query_parallel_env_config(self, mock_processor_class):
        """Test that environment variables configure the processor"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        execute_query_parallel(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table"
        )
        
        # Verify processor was created with env config
        call_args = mock_processor_class.call_args
        self.assertEqual(call_args.kwargs['max_workers'], 8)
        self.assertEqual(call_args.kwargs['chunk_size'], 100000)
    
    @patch('backend.modules.mapper.parallel_query_executor.ParallelProcessor')
    def test_execute_query_parallel_with_params(self, mock_processor_class):
        """Test that parameters override environment variables"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        execute_query_parallel(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table",
            enable_parallel=False,
            max_workers=4,
            chunk_size=25000
        )
        
        # Verify processor was created with param values
        call_args = mock_processor_class.call_args
        self.assertFalse(call_args.kwargs['enable_parallel'])
        self.assertEqual(call_args.kwargs['max_workers'], 4)
        self.assertEqual(call_args.kwargs['chunk_size'], 25000)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_parallel_config_defaults(self):
        """Test getting default configuration"""
        config = get_parallel_config()
        
        self.assertTrue(config['enabled'])  # Default is True
        self.assertIsNone(config['max_workers'])  # Default is None (auto-detect)
        self.assertEqual(config['chunk_size'], 50000)
        self.assertEqual(config['min_rows_for_parallel'], 100000)
    
    @patch.dict(os.environ, {
        'MAPPER_PARALLEL_ENABLED': 'false',
        'MAPPER_MAX_WORKERS': '6',
        'MAPPER_CHUNK_SIZE': '75000',
        'MAPPER_MIN_ROWS_FOR_PARALLEL': '50000'
    })
    def test_get_parallel_config_from_env(self):
        """Test getting configuration from environment variables"""
        config = get_parallel_config()
        
        self.assertFalse(config['enabled'])
        self.assertEqual(config['max_workers'], '6')
        self.assertEqual(config['chunk_size'], 75000)
        self.assertEqual(config['min_rows_for_parallel'], 50000)


if __name__ == '__main__':
    unittest.main()

