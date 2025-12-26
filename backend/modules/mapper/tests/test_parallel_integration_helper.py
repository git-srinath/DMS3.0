"""
Unit tests for parallel_integration_helper.
"""
import unittest
from unittest.mock import Mock, patch
import os
from backend.modules.mapper.parallel_integration_helper import (
    get_parallel_config_from_params,
    should_use_parallel_processing,
    create_parallel_processor
)


class TestParallelIntegrationHelper(unittest.TestCase):
    """Test cases for parallel_integration_helper"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_parallel_config_from_params_all_provided(self):
        """Test extracting config when all params are provided"""
        params = {
            'enable_parallel': True,
            'max_workers': 4,
            'chunk_size': 50000,
            'min_rows_for_parallel': 100000
        }
        
        config = get_parallel_config_from_params(params)
        
        self.assertTrue(config['enable_parallel'])
        self.assertEqual(config['max_workers'], 4)
        self.assertEqual(config['chunk_size'], 50000)
        self.assertEqual(config['min_rows_for_parallel'], 100000)
    
    @patch.dict(os.environ, {
        'MAPPER_PARALLEL_ENABLED': 'false',
        'MAPPER_MAX_WORKERS': '8',
        'MAPPER_CHUNK_SIZE': '75000',
        'MAPPER_MIN_ROWS_FOR_PARALLEL': '50000'
    })
    def test_get_parallel_config_from_params_with_env_fallback(self):
        """Test that env vars are used when params not provided"""
        params = {}
        
        config = get_parallel_config_from_params(params)
        
        self.assertFalse(config['enable_parallel'])
        self.assertEqual(config['max_workers'], 8)
        self.assertEqual(config['chunk_size'], 75000)
        self.assertEqual(config['min_rows_for_parallel'], 50000)
    
    def test_get_parallel_config_enable_parallel_string_y(self):
        """Test that enable_parallel accepts string 'Y'"""
        params = {'enable_parallel': 'Y'}
        config = get_parallel_config_from_params(params)
        self.assertTrue(config['enable_parallel'])
    
    def test_get_parallel_config_enable_parallel_string_n(self):
        """Test that enable_parallel accepts string 'N'"""
        params = {'enable_parallel': 'N'}
        config = get_parallel_config_from_params(params)
        self.assertFalse(config['enable_parallel'])
    
    def test_should_use_parallel_processing_enabled_above_threshold(self):
        """Test that parallel is used when enabled and above threshold"""
        config = {
            'enable_parallel': True,
            'min_rows_for_parallel': 100000
        }
        
        self.assertTrue(should_use_parallel_processing(200000, config))
    
    def test_should_use_parallel_processing_enabled_below_threshold(self):
        """Test that parallel is NOT used when below threshold"""
        config = {
            'enable_parallel': True,
            'min_rows_for_parallel': 100000
        }
        
        self.assertFalse(should_use_parallel_processing(50000, config))
    
    def test_should_use_parallel_processing_disabled(self):
        """Test that parallel is NOT used when disabled"""
        config = {
            'enable_parallel': False,
            'min_rows_for_parallel': 100000
        }
        
        self.assertFalse(should_use_parallel_processing(200000, config))
    
    @patch('backend.modules.mapper.parallel_integration_helper.ParallelProcessor')
    def test_create_parallel_processor(self, mock_processor_class):
        """Test creating a parallel processor from config"""
        config = {
            'enable_parallel': True,
            'max_workers': 4,
            'chunk_size': 50000,
            'min_rows_for_parallel': 100000
        }
        
        processor = create_parallel_processor(config)
        
        mock_processor_class.assert_called_once_with(
            max_workers=4,
            chunk_size=50000,
            enable_parallel=True
        )
        self.assertEqual(processor, mock_processor_class.return_value)


if __name__ == '__main__':
    unittest.main()

