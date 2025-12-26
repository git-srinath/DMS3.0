"""
Data models for parallel processing of mapper jobs.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Strategy for chunking source data"""
    OFFSET_LIMIT = "OFFSET_LIMIT"  # Use OFFSET/LIMIT for chunking
    KEY_BASED = "KEY_BASED"  # Use key column ranges for chunking
    ROWID_BASED = "ROWID_BASED"  # Use ROWID for Oracle


@dataclass
class ChunkResult:
    """Result of processing a single chunk"""
    chunk_id: int
    rows_processed: int = 0
    rows_successful: int = 0
    rows_failed: int = 0
    errors: List[Dict[str, Any]] = None
    error: Optional[str] = None  # Error message if entire chunk failed
    processing_time: float = 0.0  # Time taken to process chunk in seconds
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ParallelProcessingResult:
    """Aggregated result from parallel processing"""
    total_rows_processed: int = 0
    total_rows_successful: int = 0
    total_rows_failed: int = 0
    chunks_total: int = 0
    chunks_succeeded: int = 0
    chunks_failed: int = 0
    chunk_results: List[ChunkResult] = None
    chunk_errors: List[Dict[str, Any]] = None
    processing_time: float = 0.0  # Total processing time in seconds
    
    def __post_init__(self):
        if self.chunk_results is None:
            self.chunk_results = []
        if self.chunk_errors is None:
            self.chunk_errors = []


@dataclass
class ChunkConfig:
    """Configuration for chunking"""
    strategy: ChunkingStrategy = ChunkingStrategy.OFFSET_LIMIT
    chunk_size: int = 50000
    key_column: Optional[str] = None  # For KEY_BASED strategy
    total_rows: Optional[int] = None  # Estimated or actual total rows
    num_chunks: Optional[int] = None  # Calculated number of chunks

