"""
Retry handler for parallel processing chunks.
Handles retry logic with exponential backoff for failed chunks.
"""
import time
import random
from typing import Optional, Callable, Dict, Any

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import info, warning, error, debug
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import info, warning, error, debug  # type: ignore


class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            exponential_base: Base for exponential backoff (default: 2.0)
            jitter: Add random jitter to delays (default: True)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryHandler:
    """Handles retries for failed chunk processing with exponential backoff"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration (default: RetryConfig())
        """
        self.config = config or RetryConfig()
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            attempt: Current attempt number (0-based)
            error: The exception that occurred
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        if attempt >= self.config.max_retries:
            return False
        
        # Don't retry certain types of errors
        error_type = type(error).__name__
        error_msg = str(error).upper()
        
        # Don't retry syntax errors or configuration errors
        non_retryable_errors = [
            'SYNTAXERROR', 'VALUEERROR', 'ATTRIBUTEERROR',
            'KEYERROR', 'TYPERROR'
        ]
        
        if any(non_retryable in error_type.upper() or non_retryable in error_msg 
               for non_retryable in non_retryable_errors):
            debug(f"Error {error_type} is not retryable: {error}")
            return False
        
        return True
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if enabled (random value between 0 and delay * 0.1)
        if self.config.jitter:
            jitter_amount = delay * 0.1 * random.random()
            delay += jitter_amount
        
        return delay
    
    def execute_with_retry(
        self,
        func: Callable,
        func_name: str = "operation",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            func_name: Name of function for logging
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):  # +1 for initial attempt
            try:
                if attempt > 0:
                    delay = self.calculate_delay(attempt - 1)
                    debug(f"{func_name}: Retry attempt {attempt}/{self.config.max_retries} after {delay:.2f}s delay")
                    time.sleep(delay)
                
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                error(f"{func_name}: Attempt {attempt + 1} failed: {type(e).__name__}: {e}")
                
                if not self.should_retry(attempt, e):
                    debug(f"{func_name}: Error is not retryable or max retries reached")
                    raise
                
                if attempt < self.config.max_retries:
                    warning(f"{func_name}: Will retry ({attempt + 1}/{self.config.max_retries})")
        
        # All retries exhausted
        error(f"{func_name}: All {self.config.max_retries + 1} attempts failed")
        raise last_exception


def create_retry_handler(
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None
) -> RetryHandler:
    """
    Create a retry handler with optional configuration.
    
    Args:
        max_retries: Maximum retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        
    Returns:
        Configured RetryHandler instance
    """
    config = RetryConfig()
    
    if max_retries is not None:
        config.max_retries = max_retries
    if initial_delay is not None:
        config.initial_delay = initial_delay
    if max_delay is not None:
        config.max_delay = max_delay
    
    return RetryHandler(config)
