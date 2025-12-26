"""
Unit tests for ConnectionPoolManager.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import threading
from backend.modules.mapper.parallel_connection_pool import ConnectionPoolManager


class TestConnectionPoolManager(unittest.TestCase):
    """Test cases for ConnectionPoolManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.source_conn1 = Mock()
        self.source_conn2 = Mock()
        self.target_conn1 = Mock()
        self.target_conn2 = Mock()
        
        self.source_conn_count = 0
        self.target_conn_count = 0
    
    def source_factory(self):
        """Factory for creating source connections"""
        self.source_conn_count += 1
        if self.source_conn_count == 1:
            return self.source_conn1
        return self.source_conn2
    
    def target_factory(self):
        """Factory for creating target connections"""
        self.target_conn_count += 1
        if self.target_conn_count == 1:
            return self.target_conn1
        return self.target_conn2
    
    def test_source_connection_creation(self):
        """Test that source connections are created on demand"""
        pool = ConnectionPoolManager(
            source_conn_factory=self.source_factory,
            target_conn_factory=None
        )
        
        with pool.get_source_connection() as conn:
            self.assertEqual(conn, self.source_conn1)
            self.assertEqual(self.source_conn_count, 1)
    
    def test_target_connection_creation(self):
        """Test that target connections are created on demand"""
        pool = ConnectionPoolManager(
            source_conn_factory=None,
            target_conn_factory=self.target_factory
        )
        
        with pool.get_target_connection() as conn:
            self.assertEqual(conn, self.target_conn1)
            self.assertEqual(self.target_conn_count, 1)
    
    def test_connection_reuse_same_thread(self):
        """Test that connections are reused within the same thread"""
        pool = ConnectionPoolManager(
            source_conn_factory=self.source_factory,
            target_conn_factory=self.target_factory
        )
        
        # First use
        with pool.get_source_connection() as conn1:
            pass
        
        # Second use in same thread should reuse
        with pool.get_source_connection() as conn2:
            self.assertEqual(conn1, conn2)
            self.assertEqual(self.source_conn_count, 1)  # Should only create once
    
    def test_connection_close_on_error(self):
        """Test that connections are closed and removed on error"""
        pool = ConnectionPoolManager(
            source_conn_factory=self.source_factory,
            target_conn_factory=None
        )
        
        self.source_conn1.execute.side_effect = Exception("Connection error")
        
        try:
            with pool.get_source_connection() as conn:
                conn.execute("SELECT 1")
        except Exception:
            pass
        
        # Connection should be closed
        self.source_conn1.close.assert_called_once()
        
        # Next call should create a new connection
        with pool.get_source_connection() as conn:
            self.assertEqual(conn, self.source_conn2)
            self.assertEqual(self.source_conn_count, 2)
    
    def test_close_all_connections(self):
        """Test that close_all_connections closes all connections"""
        pool = ConnectionPoolManager(
            source_conn_factory=self.source_factory,
            target_conn_factory=self.target_factory
        )
        
        # Create connections
        with pool.get_source_connection():
            pass
        with pool.get_target_connection():
            pass
        
        # Close all
        pool.close_all_connections()
        
        self.source_conn1.close.assert_called_once()
        self.target_conn1.close.assert_called_once()
    
    def test_context_manager(self):
        """Test that ConnectionPoolManager works as context manager"""
        with ConnectionPoolManager(
            source_conn_factory=self.source_factory,
            target_conn_factory=self.target_factory
        ) as pool:
            with pool.get_source_connection() as conn:
                self.assertIsNotNone(conn)
        
        # Connections should be closed on exit
        self.source_conn1.close.assert_called_once()
        self.target_conn1.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()

