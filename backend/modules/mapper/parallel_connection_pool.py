"""
Connection Pool Manager for parallel processing.
Manages database connections for worker threads.
"""
from typing import Optional, Dict, Any
from contextlib import contextmanager
import threading

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import info, warning, error, debug  # type: ignore


class ConnectionPoolManager:
    """
    Manages connection pooling for parallel processing workers.
    Each worker thread gets its own database connection from the pool.
    """
    
    def __init__(self, source_conn_factory=None, target_conn_factory=None):
        """
        Initialize connection pool manager.
        
        Args:
            source_conn_factory: Factory function to create source connections
            target_conn_factory: Factory function to create target connections
        """
        self.source_conn_factory = source_conn_factory
        self.target_conn_factory = target_conn_factory
        self._source_connections = {}  # Thread ID -> connection
        self._target_connections = {}  # Thread ID -> connection
        self._lock = threading.Lock()
    
    @contextmanager
    def get_source_connection(self):
        """
        Get a source connection for the current thread.
        Creates a new connection if one doesn't exist for this thread.
        
        Usage:
            with pool.get_source_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        thread_id = threading.get_ident()
        
        # Get or create connection for this thread
        with self._lock:
            if thread_id not in self._source_connections:
                if self.source_conn_factory:
                    self._source_connections[thread_id] = self.source_conn_factory()
                    debug(f"Created source connection for thread {thread_id}")
                else:
                    raise ValueError("Source connection factory not provided")
        
        conn = self._source_connections[thread_id]
        
        try:
            yield conn
        except Exception as e:
            error(f"Error with source connection in thread {thread_id}: {e}")
            # Close and remove connection on error
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._source_connections.pop(thread_id, None)
            raise
    
    @contextmanager
    def get_target_connection(self):
        """
        Get a target connection for the current thread.
        Creates a new connection if one doesn't exist for this thread.
        
        Usage:
            with pool.get_target_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT ...")
                conn.commit()
        """
        thread_id = threading.get_ident()
        
        # Get or create connection for this thread
        with self._lock:
            if thread_id not in self._target_connections:
                if self.target_conn_factory:
                    self._target_connections[thread_id] = self.target_conn_factory()
                    debug(f"Created target connection for thread {thread_id}")
                else:
                    raise ValueError("Target connection factory not provided")
        
        conn = self._target_connections[thread_id]
        
        try:
            yield conn
        except Exception as e:
            error(f"Error with target connection in thread {thread_id}: {e}")
            # Close and remove connection on error
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._target_connections.pop(thread_id, None)
            raise
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        with self._lock:
            # Close source connections
            for thread_id, conn in list(self._source_connections.items()):
                try:
                    conn.close()
                    debug(f"Closed source connection for thread {thread_id}")
                except Exception:
                    pass
            self._source_connections.clear()
            
            # Close target connections
            for thread_id, conn in list(self._target_connections.items()):
                try:
                    conn.close()
                    debug(f"Closed target connection for thread {thread_id}")
                except Exception:
                    pass
            self._target_connections.clear()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close all connections"""
        self.close_all_connections()

