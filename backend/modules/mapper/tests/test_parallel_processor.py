"""
Unit tests for ParallelProcessor.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from backend.modules.mapper.parallel_processor import ParallelProcessor
from backend.modules.mapper.parallel_models import ParallelProcessingResult, ChunkResult


class TestParallelProcessor(unittest.TestCase):
    """Test cases for ParallelProcessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = ParallelProcessor(
            max_workers=2,
            chunk_size=100,
            enable_parallel=True
        )
    
    def test_init_default_workers(self):
        """Test initialization with default worker count"""
        import os
        processor = ParallelProcessor()
        
        expected_workers = max(1, (os.cpu_count() or 1) - 1)
        self.assertEqual(processor.max_workers, expected_workers)
    
    def test_init_custom_workers(self):
        """Test initialization with custom worker count"""
        processor = ParallelProcessor(max_workers=4)
        self.assertEqual(processor.max_workers, 4)
    
    def test_aggregate_results_success(self):
        """Test result aggregation with successful chunks"""
        chunk_results = [
            ChunkResult(chunk_id=0, rows_processed=100, rows_successful=100, rows_failed=0),
            ChunkResult(chunk_id=1, rows_processed=100, rows_successful=95, rows_failed=5),
            ChunkResult(chunk_id=2, rows_processed=50, rows_successful=50, rows_failed=0),
        ]
        
        result = self.processor._aggregate_results(chunk_results)
        
        self.assertEqual(result.chunks_total, 3)
        self.assertEqual(result.chunks_succeeded, 3)
        self.assertEqual(result.chunks_failed, 0)
        self.assertEqual(result.total_rows_processed, 250)
        self.assertEqual(result.total_rows_successful, 245)
        self.assertEqual(result.total_rows_failed, 5)
    
    def test_aggregate_results_with_errors(self):
        """Test result aggregation with failed chunks"""
        chunk_results = [
            ChunkResult(chunk_id=0, rows_processed=100, rows_successful=100, rows_failed=0),
            ChunkResult(chunk_id=1, rows_processed=0, error="Connection timeout"),
            ChunkResult(chunk_id=2, rows_processed=50, rows_successful=50, rows_failed=0),
        ]
        
        result = self.processor._aggregate_results(chunk_results)
        
        self.assertEqual(result.chunks_total, 3)
        self.assertEqual(result.chunks_succeeded, 2)
        self.assertEqual(result.chunks_failed, 1)
        self.assertEqual(len(result.chunk_errors), 1)
        self.assertEqual(result.chunk_errors[0]['chunk_id'], 1)
    
    def test_process_sequential_placeholder(self):
        """Test sequential processing placeholder"""
        mock_conn = Mock()
        
        result = self.processor._process_sequential(
            mock_conn, "SELECT * FROM test", None, None, None, None, "ORACLE"
        )
        
        self.assertEqual(result.chunks_failed, 1)
        self.assertIsNotNone(result.error)


if __name__ == '__main__':
    unittest.main()

