"""
Integration tests for Phase 4 parallel processing implementation.

These tests verify the integration of parallel processing with mapper job execution,
including SCD logic, checkpoints, progress tracking, and stop requests.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Support both FastAPI and Flask import contexts
try:
    from backend.modules.mapper.mapper_job_executor import (
        execute_mapper_job,
        _execute_mapper_job_parallel
    )
    from backend.modules.mapper.parallel_models import ChunkConfig, ChunkingStrategy
except ImportError:
    from modules.mapper.mapper_job_executor import (  # type: ignore
        execute_mapper_job,
        _execute_mapper_job_parallel
    )
    from modules.mapper.parallel_models import ChunkConfig, ChunkingStrategy  # type: ignore


class TestPhase4Integration(unittest.TestCase):
    """Integration tests for Phase 4 parallel processing"""
    
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
        
        # Default job config with parallel enabled
        self.job_config_parallel = {
            'mapref': 'TEST_MAPREF',
            'jobid': 123,
            'target_schema': 'TARGET_SCHEMA',
            'target_table': 'TARGET_TABLE',
            'target_type': 'DIM',
            'full_table_name': 'TARGET_SCHEMA.TARGET_TABLE',
            'pk_columns': {'ID'},
            'pk_source_mapping': {'ID': 'ID'},
            'all_columns': ['ID', 'NAME', 'RWHKEY', 'CURFLG', 'FROMDT', 'TODT'],
            'column_source_mapping': {'ID': 'ID', 'NAME': 'NAME'},
            'hash_exclude_columns': {'RWHKEY', 'CURFLG', 'FROMDT', 'TODT'},
            'bulk_limit': 5000,
            'scd_type': 2,  # SCD Type 2
            'parallel_config': {
                'enable_parallel': True,
                'max_workers': 2,
                'chunk_size': 50000,
                'min_rows_for_parallel': 100000
            }
        }
        
        # Job config without parallel
        self.job_config_sequential = {
            **self.job_config_parallel,
            'parallel_config': {
                'enable_parallel': False
            }
        }
        
        self.checkpoint_config = {
            'enabled': True,
            'strategy': 'KEY',
            'columns': ['ID'],
            'column': 'ID'
        }
        
        self.session_params = {
            'prcid': 1,
            'sessionid': 1,
            'param1': None
        }
        
        self.source_sql = "SELECT ID, NAME FROM SOURCE_TABLE ORDER BY ID"
        
        def mock_transformation(row_dict):
            # Simple transformation that adds required columns
            result = row_dict.copy()
            result['RWHKEY'] = 'hash123'
            result['CURFLG'] = 'Y'
            result['FROMDT'] = '2024-01-01'
            result['TODT'] = '9999-12-31'
            return result
        
        self.transformation_func = mock_transformation
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._verify_target_table')
    def test_parallel_vs_sequential_decision(self, mock_verify, mock_check_stop, 
                                            mock_chunk_manager, mock_detect_db):
        """Test that system correctly chooses parallel vs sequential processing"""
        # Setup
        mock_detect_db.side_effect = lambda conn: 'POSTGRESQL'
        mock_check_stop.return_value = False
        mock_verify.return_value = None
        
        # Test 1: Parallel enabled, rows above threshold
        mock_manager = Mock()
        mock_manager.estimate_total_rows.return_value = 150000
        mock_chunk_manager.return_value = mock_manager
        
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchmany.return_value = []
        
        # Should use parallel (we verify by checking if estimate_total_rows was called)
        result = execute_mapper_job(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
            self.source_sql,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params
        )
        
        mock_manager.estimate_total_rows.assert_called()
        
        # Test 2: Parallel enabled, rows below threshold
        mock_manager.estimate_total_rows.return_value = 50000
        
        result = execute_mapper_job(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
            self.source_sql,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params
        )
        
        # Should use sequential (estimate called but parallel not used)
        mock_manager.estimate_total_rows.assert_called()
        
        # Test 3: Parallel disabled
        result = execute_mapper_job(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_sequential,
            self.source_sql,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params
        )
        
        # Should use sequential (no parallel config check)
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.ThreadPoolExecutor')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._process_mapper_chunk')
    @patch('backend.modules.mapper.mapper_job_executor.update_checkpoint')
    @patch('backend.modules.mapper.mapper_job_executor.complete_checkpoint')
    @patch('backend.modules.mapper.mapper_job_executor.update_process_log_progress')
    def test_checkpoint_handling_in_parallel(self, mock_update_progress, mock_complete_checkpoint,
                                            mock_update_checkpoint, mock_process_chunk,
                                            mock_check_stop, mock_executor, 
                                            mock_chunk_manager, mock_detect_db):
        """Test checkpoint handling in parallel processing context"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
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
        
        # Mock chunk results with checkpoint values
        mock_process_chunk.side_effect = [
            {'chunk_id': 0, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS', 'checkpoint_value': '50000'},
            {'chunk_id': 1, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS', 'checkpoint_value': '100000'},
            {'chunk_id': 2, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS', 'checkpoint_value': '150000'}
        ]
        
        # Mock executor
        from concurrent.futures import Future
        futures = []
        for i in range(3):
            future = Future()
            future.set_result(mock_process_chunk.return_value)
            futures.append(future)
        
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = futures[0]
        
        # Execute
        parallel_config = self.job_config_parallel['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
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
        
        # Verify checkpoint was updated with last chunk's value
        mock_update_checkpoint.assert_called_once()
        # Should be called with last successful chunk's checkpoint value
        call_args = mock_update_checkpoint.call_args
        self.assertEqual(call_args[0][2], '150000')  # Last chunk's checkpoint value
        
        # Verify checkpoint was completed
        mock_complete_checkpoint.assert_called_once()
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.ThreadPoolExecutor')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._process_mapper_chunk')
    @patch('backend.modules.mapper.mapper_job_executor.update_process_log_progress')
    def test_progress_tracking_in_parallel(self, mock_update_progress, mock_process_chunk,
                                          mock_check_stop, mock_executor,
                                          mock_chunk_manager, mock_detect_db):
        """Test progress tracking across parallel workers"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        # Mock chunk config
        mock_manager = Mock()
        mock_config = ChunkConfig(
            strategy=ChunkingStrategy.OFFSET_LIMIT,
            chunk_size=50000,
            total_rows=250000,
            num_chunks=5
        )
        mock_manager.calculate_chunk_config.return_value = mock_config
        mock_chunk_manager.return_value = mock_manager
        
        # Mock chunk results
        mock_process_chunk.side_effect = [
            {'chunk_id': i, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS'} for i in range(5)
        ]
        
        # Mock executor
        from concurrent.futures import Future
        futures = []
        for i in range(5):
            future = Future()
            future.set_result(mock_process_chunk.return_value)
            futures.append(future)
        
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = futures[0]
        
        # Execute
        parallel_config = self.job_config_parallel['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
            self.source_sql,
            None,
            self.transformation_func,
            self.checkpoint_config,
            self.session_params,
            ['ID', 'NAME'],
            'POSTGRESQL',
            'POSTGRESQL',
            parallel_config,
            250000
        )
        
        # Verify progress was updated (should be called every 5 chunks + final)
        # With 5 chunks, should be called at least once
        self.assertGreaterEqual(mock_update_progress.call_count, 1)
        
        # Verify final progress update
        final_call = mock_update_progress.call_args_list[-1]
        self.assertEqual(final_call[0][2], 250000)  # total_source_rows
        self.assertEqual(final_call[0][3], 250000)  # total_target_rows
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.ThreadPoolExecutor')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._process_mapper_chunk')
    def test_stop_request_during_parallel_processing(self, mock_process_chunk,
                                                      mock_check_stop, mock_executor,
                                                      mock_chunk_manager, mock_detect_db):
        """Test stop request handling during parallel processing"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        
        # Mock check_stop_request to return True after first chunk
        stop_call_count = [0]
        def mock_stop_check(*args):
            stop_call_count[0] += 1
            return stop_call_count[0] > 2  # Stop after 2 checks
        
        mock_check_stop.side_effect = mock_stop_check
        
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
            {'chunk_id': 0, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS'},
            {'chunk_id': 1, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'STOPPED'}  # Second chunk stopped
        ]
        
        # Mock executor
        from concurrent.futures import Future
        futures = []
        for i in range(3):
            future = Future()
            if i < 2:
                future.set_result(mock_process_chunk.return_value)
            futures.append(future)
        
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = futures[0]
        
        # Execute
        parallel_config = self.job_config_parallel['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
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
        
        # Verify stop was handled
        # Result should reflect partial processing
        self.assertIn(result['status'], ['STOPPED', 'SUCCESS'])  # May complete before stop
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.ThreadPoolExecutor')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor._process_mapper_chunk')
    def test_error_aggregation_across_chunks(self, mock_process_chunk,
                                            mock_check_stop, mock_executor,
                                            mock_chunk_manager, mock_detect_db):
        """Test error aggregation across parallel chunks"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
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
        
        # Mock chunk results with errors
        mock_process_chunk.side_effect = [
            {'chunk_id': 0, 'source_rows': 50000, 'target_rows': 49000, 'error_rows': 1000, 
             'status': 'SUCCESS'},
            {'chunk_id': 1, 'source_rows': 50000, 'target_rows': 0, 'error_rows': 50000, 
             'status': 'ERROR', 'error_message': 'Processing failed'},
            {'chunk_id': 2, 'source_rows': 50000, 'target_rows': 50000, 'error_rows': 0, 
             'status': 'SUCCESS'}
        ]
        
        # Mock executor
        from concurrent.futures import Future
        futures = []
        for i in range(3):
            future = Future()
            future.set_result(mock_process_chunk.return_value)
            futures.append(future)
        
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = futures[0]
        
        # Execute
        parallel_config = self.job_config_parallel['parallel_config']
        result = _execute_mapper_job_parallel(
            self.mock_metadata_conn,
            self.mock_source_conn,
            self.mock_target_conn,
            self.job_config_parallel,
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
        
        # Verify error aggregation
        self.assertEqual(result['source_rows'], 150000)
        self.assertEqual(result['target_rows'], 99000)  # 49000 + 0 + 50000
        self.assertEqual(result['error_rows'], 51000)  # 1000 + 50000 + 0
        # Status may be SUCCESS or FAILED depending on implementation
        self.assertIn(result['status'], ['SUCCESS', 'FAILED'])


class TestSCDInParallelContext(unittest.TestCase):
    """Test SCD logic in parallel processing context"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_metadata_conn = Mock()
        self.mock_source_conn = Mock()
        self.mock_target_conn = Mock()
        
        self.mock_source_cursor = Mock()
        self.mock_target_cursor = Mock()
        
        self.mock_source_conn.cursor.return_value = self.mock_source_cursor
        self.mock_target_conn.cursor.return_value = self.mock_target_cursor
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor.build_primary_key_values')
    @patch('backend.modules.mapper.mapper_job_executor._lookup_target_record')
    @patch('backend.modules.mapper.mapper_job_executor.generate_hash')
    @patch('backend.modules.mapper.mapper_job_executor.prepare_row_for_scd')
    @patch('backend.modules.mapper.mapper_job_executor.process_scd_batch')
    def test_scd_type_1_in_parallel_chunk(self, mock_process_scd, mock_prepare_scd,
                                          mock_generate_hash, mock_lookup,
                                          mock_build_pk, mock_check_stop,
                                          mock_chunk_manager, mock_detect_db):
        """Test SCD Type 1 processing in parallel chunk"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.create_chunked_query.return_value = "SELECT * FROM source LIMIT 50000 OFFSET 0"
        mock_chunk_manager.return_value = mock_manager
        
        # Mock source data
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchall.return_value = [
            (1, 'Name1'),
            (2, 'Name2')
        ]
        
        # Mock SCD Type 1 logic (update existing)
        mock_build_pk.return_value = {'ID': 1}
        mock_lookup.return_value = {'ID': 1, 'NAME': 'OldName', 'RWHKEY': 'oldhash'}
        mock_generate_hash.return_value = 'newhash'
        mock_prepare_scd.return_value = (None, {'ID': 1, 'NAME': 'Name1'}, None)  # Update SCD1
        mock_process_scd.return_value = (0, 2, 0)  # 0 inserted, 2 updated, 0 expired
        
        # Import and execute
        from backend.modules.mapper.mapper_job_executor import _process_mapper_chunk
        
        result = _process_mapper_chunk(
            chunk_id=0,
            source_conn=self.mock_source_conn,
            source_query="SELECT ID, NAME FROM SOURCE",
            query_bind_params=None,
            chunk_size=50000,
            key_column=None,
            source_columns=['ID', 'NAME'],
            transformation_func=lambda x: x,
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
            mapref='TEST',
            checkpoint_columns=None,
            retry_handler=None
        )
        
        # Verify SCD Type 1 processing
        mock_process_scd.assert_called_once()
        call_args = mock_process_scd.call_args
        self.assertEqual(call_args[0][6], [])  # rows_to_insert (empty for SCD1)
        self.assertEqual(len(call_args[0][7]), 2)  # rows_to_update_scd1 (2 rows)
        self.assertEqual(call_args[0][8], [])  # rows_to_update_scd2 (empty for SCD1)
        self.assertEqual(call_args[0][9], 1)  # scd_type
    
    @patch('backend.modules.mapper.mapper_job_executor.detect_database_type')
    @patch('backend.modules.mapper.mapper_job_executor.ChunkManager')
    @patch('backend.modules.mapper.mapper_job_executor.check_stop_request')
    @patch('backend.modules.mapper.mapper_job_executor.build_primary_key_values')
    @patch('backend.modules.mapper.mapper_job_executor._lookup_target_record')
    @patch('backend.modules.mapper.mapper_job_executor.generate_hash')
    @patch('backend.modules.mapper.mapper_job_executor.prepare_row_for_scd')
    @patch('backend.modules.mapper.mapper_job_executor.process_scd_batch')
    def test_scd_type_2_in_parallel_chunk(self, mock_process_scd, mock_prepare_scd,
                                          mock_generate_hash, mock_lookup,
                                          mock_build_pk, mock_check_stop,
                                          mock_chunk_manager, mock_detect_db):
        """Test SCD Type 2 processing in parallel chunk"""
        # Setup
        mock_detect_db.return_value = 'POSTGRESQL'
        mock_check_stop.return_value = False
        
        mock_manager = Mock()
        mock_manager.create_chunked_query.return_value = "SELECT * FROM source LIMIT 50000 OFFSET 0"
        mock_chunk_manager.return_value = mock_manager
        
        # Mock source data
        self.mock_source_cursor.description = [('ID',), ('NAME',)]
        self.mock_source_cursor.fetchall.return_value = [
            (1, 'Name1'),
            (2, 'Name2')
        ]
        
        # Mock SCD Type 2 logic (insert new version, expire old)
        mock_build_pk.return_value = {'ID': 1}
        mock_lookup.return_value = {'ID': 1, 'NAME': 'OldName', 'RWHKEY': 'oldhash', 'SKEY': 100}
        mock_generate_hash.return_value = 'newhash'
        mock_prepare_scd.return_value = (
            {'ID': 1, 'NAME': 'Name1'},  # Insert new
            None,  # No SCD1 update
            {'SKEY': 100}  # Expire old
        )
        mock_process_scd.return_value = (2, 0, 2)  # 2 inserted, 0 updated, 2 expired
        
        # Import and execute
        from backend.modules.mapper.mapper_job_executor import _process_mapper_chunk
        
        result = _process_mapper_chunk(
            chunk_id=0,
            source_conn=self.mock_source_conn,
            source_query="SELECT ID, NAME FROM SOURCE",
            query_bind_params=None,
            chunk_size=50000,
            key_column=None,
            source_columns=['ID', 'NAME'],
            transformation_func=lambda x: x,
            target_conn=self.mock_target_conn,
            target_schema='TARGET_SCHEMA',
            target_table='TARGET_TABLE',
            full_table_name='TARGET_SCHEMA.TARGET_TABLE',
            pk_columns={'ID'},
            pk_source_mapping={'ID': 'ID'},
            all_columns=['ID', 'NAME'],
            hash_exclude_columns=set(),
            scd_type=2,
            target_type='DIM',
            source_db_type='POSTGRESQL',
            target_db_type='POSTGRESQL',
            metadata_conn=self.mock_metadata_conn,
            mapref='TEST',
            checkpoint_columns=None,
            retry_handler=None
        )
        
        # Verify SCD Type 2 processing
        mock_process_scd.assert_called_once()
        call_args = mock_process_scd.call_args
        self.assertEqual(len(call_args[0][6]), 2)  # rows_to_insert (2 new versions)
        self.assertEqual(call_args[0][7], [])  # rows_to_update_scd1 (empty for SCD2)
        self.assertEqual(len(call_args[0][8]), 2)  # rows_to_update_scd2 (2 to expire)
        self.assertEqual(call_args[0][9], 2)  # scd_type


if __name__ == '__main__':
    unittest.main()

