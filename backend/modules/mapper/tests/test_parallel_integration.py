"""
Integration tests for parallel processing.
Tests the full end-to-end flow of parallel processing components.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from backend.modules.mapper import (
    ParallelProcessor,
    ChunkManager,
    ChunkProcessor,
    RetryHandler,
    RetryConfig,
    ProgressTracker,
    create_progress_callback,
    execute_query_parallel
)
from backend.modules.mapper.parallel_models import ParallelProcessingResult


class TestParallelProcessingIntegration(unittest.TestCase):
    """Integration tests for parallel processing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_source_conn = Mock()
        self.mock_target_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_source_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.description = [('id',), ('name',)]
        self.mock_cursor.fetchone.return_value = (1000,)  # Row count
    
    @patch('backend.modules.mapper.chunk_manager._detect_db_type')
    @patch('backend.modules.mapper.chunk_processor._detect_db_type')
    def test_full_parallel_processing_flow(self, mock_detect_target, mock_detect_source):
        """Test complete parallel processing flow"""
        mock_detect_source.return_value = "POSTGRESQL"
        mock_detect_target.return_value = "POSTGRESQL"
        
        # Mock chunk data
        chunk_data = [(i, f'row_{i}') for i in range(100)]
        self.mock_cursor.fetchall.return_value = chunk_data
        
        # Create processor
        processor = ParallelProcessor(
            max_workers=2,
            chunk_size=50,
            enable_parallel=True
        )
        
        # Execute
        result = processor.process_mapper_job(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table",
            target_conn=self.mock_target_conn,
            target_schema="target_schema",
            target_table="target_table",
            min_rows_for_parallel=10  # Low threshold for testing
        )
        
        # Verify result structure
        self.assertIsInstance(result, ParallelProcessingResult)
        self.assertGreater(result.chunks_total, 0)
    
    def test_parallel_processor_with_retry_handler(self):
        """Test parallel processor with retry handler"""
        retry_config = RetryConfig(max_retries=2, initial_delay=0.1)
        retry_handler = RetryHandler(retry_config)
        
        processor = ParallelProcessor(
            max_workers=2,
            chunk_size=50,
            retry_handler=retry_handler
        )
        
        # Verify retry handler is set
        self.assertEqual(processor.retry_handler, retry_handler)
    
    def test_parallel_processor_with_progress_tracker(self):
        """Test parallel processor with progress tracker"""
        progress_tracker = ProgressTracker(
            total_chunks=5,
            callback=create_progress_callback("Test")
        )
        
        processor = ParallelProcessor(
            max_workers=2,
            chunk_size=50,
            progress_tracker=progress_tracker
        )
        
        # Verify progress tracker is set
        self.assertEqual(processor.progress_tracker, progress_tracker)
    
    @patch('backend.modules.mapper.parallel_query_executor.ParallelProcessor')
    def test_execute_query_parallel_integration(self, mock_processor_class):
        """Test execute_query_parallel integration"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_result = Mock()
        mock_result.total_rows_processed = 1000
        mock_result.total_rows_successful = 1000
        mock_result.total_rows_failed = 0
        mock_processor.process_mapper_job.return_value = mock_result
        
        result = execute_query_parallel(
            source_conn=self.mock_source_conn,
            source_sql="SELECT * FROM test_table",
            target_conn=self.mock_target_conn,
            target_schema="schema",
            target_table="table",
            enable_retry=True,
            enable_progress=True
        )
        
        # Verify processor was created and called
        mock_processor_class.assert_called_once()
        mock_processor.process_mapper_job.assert_called_once()
        
        # Verify result
        self.assertEqual(result.total_rows_processed, 1000)
    
    def test_chunk_manager_and_processor_integration(self):
        """Test integration between chunk manager and processor"""
        from backend.modules.mapper.chunk_manager import ChunkManager
        from backend.modules.mapper.chunk_processor import ChunkProcessor
        
        # Mock database type detection
        with patch('backend.modules.mapper.chunk_manager._detect_db_type', return_value="POSTGRESQL"):
            chunk_manager = ChunkManager("POSTGRESQL")
            
            # Test chunk query generation
            original_sql = "SELECT * FROM test_table ORDER BY id"
            chunk_sql = chunk_manager.create_chunked_query(
                original_sql, chunk_id=0, chunk_size=100
            )
            
            # Verify chunk SQL is generated
            self.assertIn("LIMIT", chunk_sql)
            self.assertIn("OFFSET", chunk_sql)
        
        # Test processor with chunk manager
        with patch('backend.modules.mapper.chunk_processor._detect_db_type', return_value="POSTGRESQL"):
            processor = ChunkProcessor("POSTGRESQL")
            
            # Verify processor has chunk manager
            self.assertIsNotNone(processor.chunk_manager)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling"""
    
    def test_retry_on_transient_error(self):
        """Test that transient errors are retried"""
        retry_config = RetryConfig(max_retries=2, initial_delay=0.01)
        retry_handler = RetryHandler(retry_config)
        
        # Function that fails then succeeds
        call_count = [0]
        def failing_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Transient error")
            return "success"
        
        with patch('time.sleep'):  # Speed up test
            result = retry_handler.execute_with_retry(failing_function, "test")
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)  # 2 failures + 1 success
    
    def test_no_retry_on_syntax_error(self):
        """Test that syntax errors are not retried"""
        retry_config = RetryConfig(max_retries=3, initial_delay=0.01)
        retry_handler = RetryHandler(retry_config)
        
        def syntax_error_function():
            raise SyntaxError("Invalid syntax")
        
        with self.assertRaises(SyntaxError):
            retry_handler.execute_with_retry(syntax_error_function, "test")
        
        # Should only be called once (no retries)


class TestProgressTrackingIntegration(unittest.TestCase):
    """Integration tests for progress tracking"""
    
    def test_progress_tracking_multiple_chunks(self):
        """Test progress tracking across multiple chunks"""
        progress_tracker = ProgressTracker(total_chunks=5)
        
        # Simulate chunk processing
        for i in range(5):
            progress_tracker.update_chunk_started(i)
            progress_tracker.update_chunk_completed(i, 100, 95, 5)
        
        snapshot = progress_tracker.get_snapshot()
        
        self.assertEqual(snapshot.completed_chunks, 5)
        self.assertEqual(snapshot.total_rows_processed, 500)
        self.assertEqual(snapshot.progress_percentage, 100.0)
    
    def test_progress_with_failures(self):
        """Test progress tracking with failed chunks"""
        progress_tracker = ProgressTracker(total_chunks=5)
        
        # Complete some, fail others
        progress_tracker.update_chunk_completed(0, 100, 100, 0)
        progress_tracker.update_chunk_completed(1, 100, 95, 5)
        progress_tracker.update_chunk_failed(2, "Error")
        progress_tracker.update_chunk_completed(3, 100, 100, 0)
        progress_tracker.update_chunk_failed(4, "Error")
        
        snapshot = progress_tracker.get_snapshot()
        
        self.assertEqual(snapshot.completed_chunks, 3)
        self.assertEqual(snapshot.failed_chunks, 2)
        self.assertEqual(snapshot.progress_percentage, 100.0)  # All chunks processed


if __name__ == '__main__':
    unittest.main()

