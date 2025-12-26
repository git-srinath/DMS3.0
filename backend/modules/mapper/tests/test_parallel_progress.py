"""
Unit tests for ProgressTracker.
"""
import unittest
from unittest.mock import Mock, patch
import time
from backend.modules.mapper.parallel_progress import (
    ProgressTracker,
    ProgressSnapshot,
    create_progress_callback
)


class TestProgressSnapshot(unittest.TestCase):
    """Test cases for ProgressSnapshot"""
    
    def test_progress_percentage_empty(self):
        """Test progress percentage with no chunks"""
        snapshot = ProgressSnapshot(total_chunks=0)
        self.assertEqual(snapshot.progress_percentage, 0.0)
    
    def test_progress_percentage_partial(self):
        """Test progress percentage calculation"""
        snapshot = ProgressSnapshot(
            total_chunks=10,
            completed_chunks=3
        )
        self.assertEqual(snapshot.progress_percentage, 30.0)
    
    def test_progress_percentage_complete(self):
        """Test progress percentage at 100%"""
        snapshot = ProgressSnapshot(
            total_chunks=10,
            completed_chunks=10
        )
        self.assertEqual(snapshot.progress_percentage, 100.0)
    
    def test_chunks_in_progress(self):
        """Test chunks in progress calculation"""
        snapshot = ProgressSnapshot(
            total_chunks=10,
            completed_chunks=3,
            failed_chunks=2
        )
        self.assertEqual(snapshot.chunks_in_progress, 5)  # 10 - 3 - 2 = 5


class TestProgressTracker(unittest.TestCase):
    """Test cases for ProgressTracker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.total_chunks = 5
        self.tracker = ProgressTracker(total_chunks=self.total_chunks)
    
    def test_initial_state(self):
        """Test initial tracker state"""
        snapshot = self.tracker.get_snapshot()
        
        self.assertEqual(snapshot.total_chunks, self.total_chunks)
        self.assertEqual(snapshot.completed_chunks, 0)
        self.assertEqual(snapshot.failed_chunks, 0)
        self.assertEqual(snapshot.total_rows_processed, 0)
    
    def test_update_chunk_started(self):
        """Test updating chunk started"""
        self.tracker.update_chunk_started(0)
        
        snapshot = self.tracker.get_snapshot()
        self.assertIn(0, snapshot.chunks_detail)
        self.assertEqual(snapshot.chunks_detail[0]['status'], 'started')
    
    def test_update_chunk_completed(self):
        """Test updating chunk completed"""
        self.tracker.update_chunk_completed(
            chunk_id=0,
            rows_processed=100,
            rows_successful=95,
            rows_failed=5
        )
        
        snapshot = self.tracker.get_snapshot()
        self.assertEqual(snapshot.completed_chunks, 1)
        self.assertEqual(snapshot.total_rows_processed, 100)
        self.assertEqual(snapshot.total_rows_successful, 95)
        self.assertEqual(snapshot.total_rows_failed, 5)
        self.assertEqual(snapshot.chunks_detail[0]['status'], 'completed')
    
    def test_update_chunk_failed(self):
        """Test updating chunk failed"""
        self.tracker.update_chunk_failed(0, "Connection error")
        
        snapshot = self.tracker.get_snapshot()
        self.assertEqual(snapshot.failed_chunks, 1)
        self.assertEqual(snapshot.chunks_detail[0]['status'], 'failed')
        self.assertEqual(snapshot.chunks_detail[0]['error'], "Connection error")
    
    def test_multiple_chunks(self):
        """Test tracking multiple chunks"""
        # Start chunks
        for i in range(3):
            self.tracker.update_chunk_started(i)
        
        # Complete chunks
        self.tracker.update_chunk_completed(0, 100, 100, 0)
        self.tracker.update_chunk_completed(1, 100, 95, 5)
        self.tracker.update_chunk_failed(2, "Error")
        
        snapshot = self.tracker.get_snapshot()
        self.assertEqual(snapshot.completed_chunks, 2)
        self.assertEqual(snapshot.failed_chunks, 1)
        self.assertEqual(snapshot.total_rows_processed, 200)
        self.assertEqual(snapshot.progress_percentage, 60.0)  # 3/5 chunks done
    
    def test_estimated_remaining_time(self):
        """Test estimated remaining time calculation"""
        # Complete first chunk quickly
        time.sleep(0.01)  # Small delay to simulate processing
        self.tracker.update_chunk_completed(0, 100, 100, 0)
        
        snapshot = self.tracker.get_snapshot()
        # Should have estimated remaining time based on average
        self.assertIsNotNone(snapshot.estimated_remaining_time)
        self.assertGreater(snapshot.estimated_remaining_time, 0)
    
    def test_callback_invocation(self):
        """Test that callback is invoked"""
        callback = Mock()
        tracker = ProgressTracker(
            total_chunks=2,
            callback=callback,
            update_interval=0.1  # Very short interval for testing
        )
        
        tracker.update_chunk_completed(0, 100, 100, 0)
        
        # Give a moment for callback to be triggered
        time.sleep(0.15)
        
        # Callback should have been called at least once
        self.assertGreaterEqual(callback.call_count, 1)
        
        # Verify callback was called with ProgressSnapshot
        if callback.called:
            args = callback.call_args[0]
            self.assertEqual(len(args), 1)
            self.assertIsInstance(args[0], ProgressSnapshot)
    
    def test_callback_not_called_before_interval(self):
        """Test that callback respects update interval"""
        callback = Mock()
        tracker = ProgressTracker(
            total_chunks=2,
            callback=callback,
            update_interval=1.0  # 1 second interval
        )
        
        tracker.update_chunk_completed(0, 100, 100, 0)
        # Should not be called immediately
        self.assertEqual(callback.call_count, 0)
    
    def test_thread_safety(self):
        """Test that tracker is thread-safe"""
        import threading
        
        def update_chunk(chunk_id):
            self.tracker.update_chunk_started(chunk_id)
            time.sleep(0.01)  # Simulate processing
            self.tracker.update_chunk_completed(chunk_id, 100, 100, 0)
        
        # Create multiple threads
        threads = []
        for i in range(self.total_chunks):
            thread = threading.Thread(target=update_chunk, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all chunks were tracked correctly
        snapshot = self.tracker.get_snapshot()
        self.assertEqual(snapshot.completed_chunks, self.total_chunks)
        self.assertEqual(snapshot.total_rows_processed, self.total_chunks * 100)


class TestCreateProgressCallback(unittest.TestCase):
    """Test cases for create_progress_callback"""
    
    def test_create_default_callback(self):
        """Test creating default progress callback"""
        callback = create_progress_callback()
        
        self.assertIsNotNone(callback)
        self.assertTrue(callable(callback))
    
    def test_callback_with_snapshot(self):
        """Test callback with progress snapshot"""
        callback = create_progress_callback("Test Processing")
        snapshot = ProgressSnapshot(
            total_chunks=10,
            completed_chunks=5,
            total_rows_processed=50000,
            elapsed_time=10.5,
            estimated_remaining_time=10.5
        )
        
        # Should not raise exception
        callback(snapshot)


if __name__ == '__main__':
    unittest.main()

