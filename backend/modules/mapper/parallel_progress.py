"""
Progress tracking for parallel processing.
Provides real-time progress updates during chunk processing.
"""
import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import info, warning, error, debug  # type: ignore


@dataclass
class ProgressSnapshot:
    """Snapshot of current progress"""
    total_chunks: int = 0
    completed_chunks: int = 0
    failed_chunks: int = 0
    total_rows_processed: int = 0
    total_rows_successful: int = 0
    total_rows_failed: int = 0
    elapsed_time: float = 0.0
    estimated_remaining_time: Optional[float] = None
    chunks_detail: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage (0-100)"""
        if self.total_chunks == 0:
            return 0.0
        return (self.completed_chunks / self.total_chunks) * 100.0
    
    @property
    def chunks_in_progress(self) -> int:
        """Calculate chunks currently in progress"""
        return self.total_chunks - self.completed_chunks - self.failed_chunks


class ProgressTracker:
    """Tracks progress of parallel processing"""
    
    def __init__(
        self,
        total_chunks: int,
        callback: Optional[Callable[[ProgressSnapshot], None]] = None,
        update_interval: float = 1.0  # Update callback every N seconds
    ):
        """
        Initialize progress tracker.
        
        Args:
            total_chunks: Total number of chunks to process
            callback: Optional callback function called with progress updates
            update_interval: Minimum seconds between callback invocations
        """
        self.total_chunks = total_chunks
        self.callback = callback
        self.update_interval = update_interval
        
        # Use RLock (reentrant lock) to allow nested lock acquisition
        # This is needed because _maybe_trigger_callback() calls get_snapshot()
        # which also needs the lock, and it's called from within update_chunk_started()
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._last_callback_time = 0.0
        
        # Progress state
        self.completed_chunks = 0
        self.failed_chunks = 0
        self.total_rows_processed = 0
        self.total_rows_successful = 0
        self.total_rows_failed = 0
        self.chunks_detail = {}  # chunk_id -> {status, rows, etc}
    
    def update_chunk_started(self, chunk_id: int):
        """Mark chunk as started"""
        with self._lock:
            if chunk_id not in self.chunks_detail:
                self.chunks_detail[chunk_id] = {
                    'status': 'started',
                    'start_time': time.time(),
                    'rows_processed': 0,
                    'rows_successful': 0,
                    'rows_failed': 0
                }
            self._maybe_trigger_callback()
    
    def update_chunk_completed(
        self,
        chunk_id: int,
        rows_processed: int,
        rows_successful: int,
        rows_failed: int
    ):
        """Mark chunk as completed"""
        with self._lock:
            self.completed_chunks += 1
            self.total_rows_processed += rows_processed
            self.total_rows_successful += rows_successful
            self.total_rows_failed += rows_failed
            
            if chunk_id in self.chunks_detail:
                self.chunks_detail[chunk_id].update({
                    'status': 'completed',
                    'end_time': time.time(),
                    'rows_processed': rows_processed,
                    'rows_successful': rows_successful,
                    'rows_failed': rows_failed
                })
            else:
                self.chunks_detail[chunk_id] = {
                    'status': 'completed',
                    'end_time': time.time(),
                    'rows_processed': rows_processed,
                    'rows_successful': rows_successful,
                    'rows_failed': rows_failed
                }
            
            self._maybe_trigger_callback()
    
    def update_chunk_failed(self, chunk_id: int, error: str):
        """Mark chunk as failed"""
        with self._lock:
            self.failed_chunks += 1
            
            if chunk_id in self.chunks_detail:
                self.chunks_detail[chunk_id].update({
                    'status': 'failed',
                    'end_time': time.time(),
                    'error': error
                })
            else:
                self.chunks_detail[chunk_id] = {
                    'status': 'failed',
                    'end_time': time.time(),
                    'error': error
                }
            
            self._maybe_trigger_callback()
    
    def get_snapshot(self) -> ProgressSnapshot:
        """Get current progress snapshot"""
        with self._lock:
            elapsed_time = time.time() - self._start_time
            
            # Estimate remaining time based on average time per chunk
            estimated_remaining = None
            if self.completed_chunks > 0:
                avg_time_per_chunk = elapsed_time / self.completed_chunks
                remaining_chunks = self.total_chunks - self.completed_chunks - self.failed_chunks
                estimated_remaining = avg_time_per_chunk * remaining_chunks
            
            return ProgressSnapshot(
                total_chunks=self.total_chunks,
                completed_chunks=self.completed_chunks,
                failed_chunks=self.failed_chunks,
                total_rows_processed=self.total_rows_processed,
                total_rows_successful=self.total_rows_successful,
                total_rows_failed=self.total_rows_failed,
                elapsed_time=elapsed_time,
                estimated_remaining_time=estimated_remaining,
                chunks_detail=self.chunks_detail.copy()
            )
    
    def _maybe_trigger_callback(self):
        """Trigger callback if enough time has passed"""
        if not self.callback:
            return
        
        current_time = time.time()
        if current_time - self._last_callback_time >= self.update_interval:
            self._last_callback_time = current_time
            try:
                snapshot = self.get_snapshot()
                self.callback(snapshot)
            except Exception as e:
                warning(f"Progress callback failed: {e}")


def create_progress_callback(log_prefix: str = "Parallel Processing") -> Callable[[ProgressSnapshot], None]:
    """
    Create a progress callback that logs progress updates.
    
    Args:
        log_prefix: Prefix for log messages
        
    Returns:
        Callback function
    """
    def callback(snapshot: ProgressSnapshot):
        info(
            f"{log_prefix}: {snapshot.progress_percentage:.1f}% complete "
            f"({snapshot.completed_chunks}/{snapshot.total_chunks} chunks, "
            f"{snapshot.total_rows_processed:,} rows, "
            f"{snapshot.elapsed_time:.1f}s elapsed"
            + (f", ~{snapshot.estimated_remaining_time:.1f}s remaining" 
               if snapshot.estimated_remaining_time else "")
        )
    
    return callback
