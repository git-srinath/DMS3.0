"""
Unit tests for RetryHandler.
"""
import unittest
from unittest.mock import Mock, patch
import time
from backend.modules.mapper.parallel_retry_handler import (
    RetryHandler,
    RetryConfig,
    create_retry_handler
)


class TestRetryConfig(unittest.TestCase):
    """Test cases for RetryConfig"""
    
    def test_default_config(self):
        """Test default retry configuration"""
        config = RetryConfig()
        
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.initial_delay, 1.0)
        self.assertEqual(config.max_delay, 60.0)
        self.assertEqual(config.exponential_base, 2.0)
        self.assertTrue(config.jitter)
    
    def test_custom_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.initial_delay, 2.0)
        self.assertEqual(config.max_delay, 120.0)
        self.assertEqual(config.exponential_base, 3.0)
        self.assertFalse(config.jitter)


class TestRetryHandler(unittest.TestCase):
    """Test cases for RetryHandler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = RetryConfig(max_retries=2, initial_delay=0.1, max_delay=1.0)
        self.handler = RetryHandler(self.config)
    
    def test_should_retry_max_retries_exceeded(self):
        """Test that retry is not attempted when max retries exceeded"""
        error = Exception("Test error")
        self.assertFalse(self.handler.should_retry(3, error))  # Attempt 3 (0-based), max=2
    
    def test_should_retry_within_limits(self):
        """Test that retry is attempted within limits"""
        error = Exception("Test error")
        self.assertTrue(self.handler.should_retry(0, error))
        self.assertTrue(self.handler.should_retry(1, error))
    
    def test_should_retry_non_retryable_error(self):
        """Test that syntax errors are not retried"""
        error = SyntaxError("Invalid syntax")
        self.assertFalse(self.handler.should_retry(0, error))
    
    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff calculation"""
        delay1 = self.handler.calculate_delay(0)  # 0.1 * 2^0 = 0.1
        delay2 = self.handler.calculate_delay(1)  # 0.1 * 2^1 = 0.2
        delay3 = self.handler.calculate_delay(2)  # 0.1 * 2^2 = 0.4
        
        self.assertAlmostEqual(delay1, 0.1, places=2)
        self.assertAlmostEqual(delay2, 0.2, places=2)
        self.assertAlmostEqual(delay3, 0.4, places=2)
    
    def test_calculate_delay_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        config = RetryConfig(max_retries=5, initial_delay=10.0, max_delay=30.0)
        handler = RetryHandler(config)
        
        delay = handler.calculate_delay(10)  # Should be capped at 30.0
        self.assertLessEqual(delay, 30.0)
    
    def test_execute_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        func = Mock(return_value="success")
        
        result = self.handler.execute_with_retry(func, "test_operation")
        
        self.assertEqual(result, "success")
        func.assert_called_once()
    
    def test_execute_with_retry_success_after_retry(self):
        """Test successful execution after retry"""
        func = Mock(side_effect=[Exception("Error 1"), "success"])
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.handler.execute_with_retry(func, "test_operation")
        
        self.assertEqual(result, "success")
        self.assertEqual(func.call_count, 2)
    
    def test_execute_with_retry_all_attempts_fail(self):
        """Test that exception is raised after all retries fail"""
        func = Mock(side_effect=Exception("Persistent error"))
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with self.assertRaises(Exception) as context:
                self.handler.execute_with_retry(func, "test_operation")
        
        self.assertIn("Persistent error", str(context.exception))
        # Should try max_retries + 1 times (initial + retries)
        self.assertEqual(func.call_count, self.config.max_retries + 1)
    
    def test_execute_with_retry_non_retryable_error(self):
        """Test that non-retryable errors are not retried"""
        func = Mock(side_effect=SyntaxError("Syntax error"))
        
        with self.assertRaises(SyntaxError):
            self.handler.execute_with_retry(func, "test_operation")
        
        # Should only call once (no retries for syntax errors)
        func.assert_called_once()
    
    def test_create_retry_handler_default(self):
        """Test creating retry handler with defaults"""
        handler = create_retry_handler()
        
        self.assertIsInstance(handler, RetryHandler)
        self.assertEqual(handler.config.max_retries, 3)
    
    def test_create_retry_handler_custom(self):
        """Test creating retry handler with custom config"""
        handler = create_retry_handler(max_retries=5, initial_delay=2.0, max_delay=100.0)
        
        self.assertIsInstance(handler, RetryHandler)
        self.assertEqual(handler.config.max_retries, 5)
        self.assertEqual(handler.config.initial_delay, 2.0)
        self.assertEqual(handler.config.max_delay, 100.0)


if __name__ == '__main__':
    unittest.main()

