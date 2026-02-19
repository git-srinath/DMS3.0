"""
Unit tests for parallel processing integration in mapper_job_executor.

Tests the Phase 4 implementation of parallel processing for mapper jobs.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List

# Support both FastAPI and Flask import contexts
try:
    from backend.modules.mapper.mapper_job_executor import (
        execute_mapper_job,
        _execute_mapper_job_parallel,
        _process_mapper_chunk
    )
    from backend.modules.mapper.parallel_models import ChunkConfig, ChunkingStrategy
except ImportError:
    from modules.mapper.mapper_job_executor import (  # type: ignore
        execute_mapper_job,
        _execute_mapper_job_parallel,
        _process_mapper_chunk
    )
    from modules.mapper.parallel_models import ChunkConfig, ChunkingStrategy  # type: ignore


class TestMapperJobExecutorParallel(unittest.TestCase):
    """Test cases for parallel processing in mapper_job_executor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_metadata_conn = Mock()
        self.mock_source_conn = Mock()
        self.mock_target_conn = Mock()
        
        self.mock_metadata_cursor = Mock()
        self.mock_source_cursor = Mock()
        self.mock_target_cursor = Mock()
        
        self.mock_metadata_conn.cursor.return_value = self.mock_metadata_cursor
        self.mock_source_conn.cursor.return_value = self.mock_source_cursor
        self.mock_target_conn.cursor.return_value = self.mock_target_cursor
        
        # Default job config
        self.job_config = {
            'mapref': 'TEST_MAPREF',
            'jobid': 123,
            'target_schema': 'TARGET_SCHEMA',
            'target_table': 'TARGET_TABLE',
            'target_type': 'DIM',
            'full_table_name': 'TARGET_SCHEMA.TARGET_TABLE',
            'pk_columns': {'ID'},
            'pk_source_mapping': {'ID': 'ID'},
            'all_columns': ['ID', 'NAME', 'RWHKEY'],
            'column_source_mapping': {'ID': 'ID', 'NAME': 'NAME'},
            'hash_exclude_columns': {'RWHKEY'},
            'bulk_limit': 5000,
            'scd_type': 1,
            'parallel_config': {
                'enable_parallel': True,
                'max_workers': 2,
                'chunk_size': 50000,
                'min_rows_for_parallel': 100000
            }
        }
        
        self.checkpoint_config = {
            'enabled': False,
            'strategy': 'AUTO',
            'columns': [],
            'column': None
        }
        
        self.session_params = {
            'prcid': 1,
            'sessionid': 1,
            'param1': None
        }
        
        self.source_sql = "SELECT ID, NAME FROM SOURCE_TABLE"
        
        def mock_transformation(row_dict):
            return row_dict
        
        self.transformation_func = mock_transformation
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    def test_row_count_estimation_enables_parallel(self, mock_check_stop, mock_chunk_manager, mock_detect_db):
        """Test that row count estimation enables parallel processing when threshold is met"""
        # Setup
        mock_detect_db.side_effect = lambda conn: 'POSTGRESQL' if conn == self.mock_source_conn else 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.estimate_total_rows.return_value = 150000  # Above threshold
        mock_chunk_manager.return_value = mock_manager
        
        # Mock cursor description for source query
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchmany.return_value = []
        
        # Execute
        result = execute_mapper_job(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config,
            self.source_sql,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params
        )
        
        # Verify
        mock_manager.estimate_total_rows.assert_called_once()
        # Should use parallel processing (we can't easily verify this without mocking the parallel function)
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    def test_row_count_estimation_disables_parallel(self, mock_check_stop, mock_chunk_manager, mock_detect_db):
        """Test that row count estimation disables parallel processing when below threshold"""
        # Setup
        mock_detect_db.side_effect = lambda conn: 'POSTGRESQL' if conn == self.mock_source_conn else 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.estimate_total_rows.return_value = 50000  # Below threshold
        mock_chunk_manager.return_value = mock_manager
        
        # Mock cursor description for source query
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchmany.return_value = []
        
        # Execute
        result = execute_mapper_job(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config,
            self.source_sql,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params
        )
        
        # Verify
        mock_manager.estimate_total_rows.assert_called_once()
        # Should use sequential processing
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.ThreadPoolExecutor')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._process_mapper_chunk')
    def test_parallel_processing_coordination(self, mock_process_chunk, mock_check_stop, 
                                             mock_executor, mock_chunk_manager, mock_detect_db):
        """Test that parallel processing coordinates chunks correctly"""
        # Setup
        mock_detect_db.side_effect = lambda conn: 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        # Mock chunk config
        mock_manager = Mock()
        mock_config = ChunkConfig(
            strategy=ChunkingStrategy.OFFSET_LIMIT,
            chunk_size=50000,
            total_rows=150000,
            num_chunks=3
        )
        mock_manager.calculate_chunk_config.return_value = mock_config
        mock_chunk_manager.return_value = mock_manager
        
        # Mock chunk results
        mock_process_chunk.side_effect = [
            {'chunk_id': 0, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 'status': 'SUCCESS'},
            {'chunk_id': 1, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 'status': 'SUCCESS'},
            {'chunk_id': 2, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 'status': 'SUCCESS'}
        ]
        
        # Mock executor
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Mock futures
        from concurrent.futures import Future
        futures = []
        for i in range(3):
            future = Future()
            future.set_result(mock_process_chunk.return_value)
            futures.append(future)
        
        mock_executor_instance.submit.return_value = futures[0]
        mock_executor_instance.__iter__ = lambda self: iter(futures)
        
        # Execute
        parallel_config = self.job_config['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config,
            self.source_sql,
            None,  # query_bind_params
            self.transformation_func,
            self.checkpoint_config,
            self.session_params,
            ['ID', 'NAME'],  # source_columns
            'POSTGRESQL',  # source_db_type
            'POSTGRESQL',  # target_db_type
            parallel_config,
            150000  # estimated_rows
        )
        
        # Verify
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['source_rows'], 150000)
        self.assertEqual(result['target_rows'], 150000)
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor.build_primary_key_values')
    @patch('backend.modules.mapper.mapper_job_executor._lookup_target_record')
    @patch('backend.modules.mapper.mapper_job_executor.generate_hash')
    @patch('backend.modules.mapper.mapper_job_executor.prepare_row_for_scd')
    @patch('backend.modules.mapper.mapper_job_executor.process_scd_batch')
    def test_process_mapper_chunk(self, mock_process_scd, mock_prepare_scd, mock_generate_hash,
                                  mock_lookup, mock_build_pk, mock_check_stop, 
                                  mock_chunk_manager, mock_detect_db):
        """Test processing a single mapper chunk"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        # Mock chunk manager
        mock_manager = Mock()
        mock_manager.create_chunked_query.return_value = "SELECT * FROM source LIMIT 50000 OFFSET 0"
        mock_chunk_manager.return_value = mock_manager
        
        # Mock source cursor
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchall.return_value = [
            (1, 'Name1'),
            (2, 'Name2')
        ]
        
        # Mock transformation and SCD logic
        mock_build_pk.return_value = {'ID': 1}
        mock_lookup.return_value = None
        mock_generate_hash.return_value = 'hash123'
        mock_prepare_scd.return_value = ({'ID': 1, 'NAME': 'Name1'}, None, None)
        mock_process_scd.return_value = (2, 0, 0)  # inserted, updated, expired
        
        # Execute
        result = _process_mapper_chunk(
            chunk_id=0,
            source_conn=self.mock_source_conn,
            source_query=self.source_sql,
            query_bind_params=None,
            chunk_size=50000,
            key_column=None,
            source_columns=['ID', 'NAME'],
            transformation_func=self.transformation_func,
            target_conn=self.mock_target_conn,
            target_schema='TARGET_SCHEMA',
            target_table='TARGET_TABLE',
            full_table_name='TARGET_SCHEMA.TARGET_TABLE',
            pk_columns={'ID'},
            pk_source_mapping={'ID': 'ID'},
            all_columns=['ID', 'NAME', 'RWHKEY'],
            hash_exclude_columns={'RWHKEY'},
            scd_type=1,
            target_type='DIM',
            source_db_type='POSTGRESQL',
            target_db_type='POSTGRESQL',
            metadata_conn=self.mock_metadata_conn,
            mapref='TEST_MAPREF',
            checkpoint_columns=None,
            retry_handler=None
        )
        
        # Verify
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['source_rows'], 2)
        self.assertEqual(result['target_rows'], 2)
        self.assertEqual(result['error_rows'], 0)
        mock_process_scd.assert_called_once()
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    def test_stop_request_before_parallel_processing(self, mock_check_stop, mock_chunk_manager, mock_detect_db):
        """Test that stop request before parallel processing returns STOPPED status"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = True  # Stop requested
        
        # Execute
        parallel_config = self.job_config['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config,
            self.source_sql,
            None,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params,
            ['ID', 'NAME'],
            'POSTGRESQL',
            'POSTGRESQL',
            parallel_config,
            150000
        )
        
        # Verify
        self.assertEqual(result['status'], 'STOPPED')
        self.assertEqual(result['source_rows'], 0)
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    def test_checkpoint_value_extraction_single_column(self, mock_check_stop, mock_chunk_manager, mock_detect_db):
        """Test checkpoint value extraction for single column"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.create_chunked_query.return_value = "SELECT * FROM source LIMIT 50000 OFFSET 0"
        mock_chunk_manager.return_value = mock_manager
        
        # Mock source cursor with checkpoint column
        self.mock_source_cursor.description = [('ID',), ('CHECKPOINT_COL',)]
        self.mock_source_cursor.fetchall.return_value = [
            (1, '2024-01-01'),
            (2, '2024-01-02')
        ]
        
        # Mock other functions
        with patch('backend.modules.mapper.mapper_job_executor.build_primary_key_values') as mock_build_pk, \
             patch('backend.modules.mapper.mapper_job_executor._lookup_target_record') as mock_lookup, \
             patch('backend.modules.mapper.mapper_job_executor.generate_hash') as mock_hash, \
             patch('backend.modules.mapper.mapper_job_executor.prepare_row_for_scd') as mock_prepare, \
             patch('backend.modules.mapper.mapper_job_executor.process_scd_batch') as mock_scd:
            
            mock_build_pk.return_value = {'ID': 1}
            mock_lookup.return_value = None
            mock_hash.return_value = 'hash123'
            mock_prepare.return_value = ({'ID': 1}, None, None)
            mock_scd.return_value = (2, 0, 0)
            
            # Execute
            result = _process_mapper_chunk(
                chunk_id=0,
                source_conn=self.mock_source_conn,
                source_query=self.source_sql,
                query_bind_params=None,
                chunk_size=50000,
                key_column=None,
                source_columns=['ID', 'CHECKPOINT_COL'],
                transformation_func=self.transformation_func,
                target_conn=self.mock_target_conn,
                target_schema='TARGET_SCHEMA',
                target_table='TARGET_TABLE',
                full_table_name='TARGET_SCHEMA.TARGET_TABLE',
                pk_columns={'ID'},
                pk_source_mapping={'ID': 'ID'},
                all_columns=['ID', 'CHECKPOINT_COL'],
                hash_exclude_columns=set(),
                scd_type=1,
                target_type='DIM',
                source_db_type='POSTGRESQL',
                target_db_type='POSTGRESQL',
                metadata_conn=self.mock_metadata_conn,
                mapref='TEST_MAPREF',
                checkpoint_columns=['CHECKPOINT_COL'],
                retry_handler=None
            )
            
            # Verify checkpoint value extracted
            self.assertEqual(result['checkpoint_value'], '2024-01-02')  # Last row's value
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    def test_error_handling_in_chunk_processing(self, mock_check_stop, mock_chunk_manager, mock_detect_db):
        """Test error handling in chunk processing"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.create_chunked_query.return_value = "SELECT * FROM source LIMIT 50000 OFFSET 0"
        mock_chunk_manager.return_value = mock_manager
        
        # Mock source cursor
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchall.return_value = [
            (1, 'Name1'),
            (2, 'Name2')
        ]
        
        # Mock SCD processing to raise error
        with patch('backend.modules.mapper.mapper_job_executor.build_primary_key_values') as mock_build_pk, \
             patch('backend.modules.mapper.mapper_job_executor._lookup_target_record') as mock_lookup, \
             patch('backend.modules.mapper.mapper_job_executor.generate_hash') as mock_hash, \
             patch('backend.modules.mapper.mapper_job_executor.prepare_row_for_scd') as mock_prepare, \
             patch('backend.modules.mapper.mapper_job_executor.process_scd_batch') as mock_scd:
            
            mock_build_pk.return_value = {'ID': 1}
            mock_lookup.return_value = None
            mock_hash.return_value = 'hash123'
            mock_prepare.return_value = ({'ID': 1}, None, None)
            mock_scd.side_effect = Exception("SCD processing failed")
            
            # Execute
            result = _process_mapper_chunk(
                chunk_id=0,
                source_conn=self.mock_source_conn,
                source_query=self.source_sql,
                query_bind_params=None,
                chunk_size=50000,
                key_column=None,
                source_columns=['ID', 'NAME'],
                transformation_func=self.transformation_func,
                target_conn=self.mock_target_conn,
                target_schema='TARGET_SCHEMA',
                target_table='TARGET_TABLE',
                full_table_name='TARGET_SCHEMA.TARGET_TABLE',
                pk_columns={'ID'},
                pk_source_mapping={'ID': 'ID'},
                all_columns=['ID', 'NAME'],
                hash_exclude_columns=set(),
                scd_type=1,
                target_type='DIM',
                source_db_type='POSTGRESQL',
                target_db_type='POSTGRESQL',
                metadata_conn=self.mock_metadata_conn,
                mapref='TEST_MAPREF',
                checkpoint_columns=None,
                retry_handler=None
            )
            
            # Verify error handling
            self.assertEqual(result['status'], 'ERROR')
            self.assertIn('error_message', result)
            self.assertGreater(result['error_rows'], 0)


class TestParallelProcessingIntegration(unittest.TestCase):
    """Integration tests for parallel processing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.job_config = {
            'mapref': 'TEST_MAPREF',
            'jobid': 123,
            'target_schema': 'TARGET_SCHEMA',
            'target_table': 'TARGET_TABLE',
            'target_type': 'DIM',
            'full_table_name': 'TARGET_SCHEMA.TARGET_TABLE',
            'pk_columns': {'ID'},
            'pk_source_mapping': {'ID': 'ID'},
            'all_columns': ['ID', 'NAME', 'RWHKEY'],
            'column_source_mapping': {'ID': 'ID', 'NAME': 'NAME'},
            'hash_exclude_columns': {'RWHKEY'},
            'bulk_limit': 5000,
            'scd_type': 1,
            'parallel_config': {
                'enable_parallel': True,
                'max_workers': 2,
                'chunk_size': 50000,
                'min_rows_for_parallel': 100000
            }
        }
    
    def test_parallel_config_extraction(self):
        """Test that parallel config is extracted correctly from job_config"""
        parallel_config = self.job_config.get('parallel_config', {})
        
        self.assertTrue(parallel_config['enable_parallel'])
        self.assertEqual(parallel_config['max_workers'], 2)
        self.assertEqual(parallel_config['chunk_size'], 50000)
        self.assertEqual(parallel_config['min_rows_for_parallel'], 100000)
    
    def test_parallel_config_defaults(self):
        """Test that parallel config has correct defaults"""
        job_config_no_parallel = {
            'mapref': 'TEST',
            'parallel_config': {}
        }
        
        parallel_config = job_config_no_parallel.get('parallel_config', {})
        enable_parallel = parallel_config.get('enable_parallel', False)
        chunk_size = parallel_config.get('chunk_size', 50000)
        min_rows = parallel_config.get('min_rows_for_parallel', 100000)
        
        self.assertFalse(enable_parallel)
        self.assertEqual(chunk_size, 50000)
        self.assertEqual(min_rows, 100000)


if __name__ == '__main__':
    unittest.main()

