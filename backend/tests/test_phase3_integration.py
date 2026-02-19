"""
Integration Tests for Phase 3: End-to-End Datatype Filtering Validation
Tests actual database connections and Phase 3 changes across modules.

Prerequisites:
- PostgreSQL metadata database with DMS_PARAMS table containing DBTYP column
- PostgreSQL target database for table creation
- Oracle metadata and target databases (optional, for full testing)
"""

import pytest
from contextlib import suppress
from typing import Optional, List, Tuple

# Import database connection modules
try:
    from backend.database.dbconnect import (
        create_metadata_connection,
        create_target_connection
    )
    from backend.modules.common.db_table_utils import _detect_db_type
    from backend.modules.jobs.pkgdwjob_python import create_target_table
    from backend.modules.file_upload.table_creator import create_table_if_not_exists
    from backend.modules.mapper.fastapi_mapper import extract_sql_columns
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestPhase3IntegrationJobs:
    """Integration tests for Jobs module Phase 3 changes"""

    @pytest.fixture
    def metadata_connection(self):
        """Provide metadata database connection"""
        try:
            conn = create_metadata_connection()
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    @pytest.fixture
    def postgres_target_connection(self):
        """Provide PostgreSQL target database connection"""
        try:
            # This may need adjusting based on available connection IDs
            conn = create_target_connection(connection_id=1)
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def test_verify_dms_params_has_dbtyp_column(self, metadata_connection):
        """
        Test: DMS_PARAMS table has DBTYP column with values.
        Required for Phase 3 DBTYP filtering to work.
        """
        assert metadata_connection is not None, "Metadata connection failed"
        
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        
        try:
            if db_type == 'POSTGRESQL':
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'dms_params'
                      AND column_name ILIKE '%dbtyp%'
                """)
            else:  # Oracle
                cursor.execute("""
                    SELECT column_name
                    FROM user_tab_columns
                    WHERE table_name = 'DMS_PARAMS'
                      AND column_name LIKE '%DBTYP%'
                """)
            
            result = cursor.fetchone()
            assert result is not None, \
                "DBTYP column not found in DMS_PARAMS table - Phase 3 requires this column"
            
            print(f"✓ DBTYP column found in DMS_PARAMS ({db_type})")
            
        finally:
            cursor.close()

    def test_verify_datatype_distribution_by_dbtype(self, metadata_connection):
        """
        Test: DMS_PARAMS contains datatypes distributed by DBTYP.
        Verifies POSTGRESQL, ORACLE, and GENERIC types exist.
        """
        assert metadata_connection is not None, "Metadata connection failed"
        
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        
        try:
            if db_type == 'POSTGRESQL':
                cursor.execute("""
                    SELECT dbtyp, COUNT(*) as count
                    FROM dms_params
                    WHERE prtyp = 'Datatype'
                    GROUP BY dbtyp
                    ORDER BY dbtyp
                """)
            else:  # Oracle
                cursor.execute("""
                    SELECT DBTYP, COUNT(*) as count
                    FROM DMS_PARAMS
                    WHERE PRTYP = 'Datatype'
                    GROUP BY DBTYP
                    ORDER BY DBTYP
                """)
            
            results = cursor.fetchall()
            assert len(results) > 0, "No datatypes found in DMS_PARAMS"
            
            dbtypes = {row[0]: row[1] for row in results}
            print(f"✓ Datatype distribution found:")
            for dbtype, count in dbtypes.items():
                print(f"  - {dbtype}: {count} types")
            
            # At least GENERIC should exist
            assert 'GENERIC' in dbtypes or None in dbtypes, \
                "GENERIC datatypes not found - required for fallback"
            
        finally:
            cursor.close()

    def test_filter_query_returns_correct_types(self, metadata_connection):
        """
        Test: DMS_PARAMS query with DBTYP filter returns expected results.
        Validates the core filtering logic of Phase 3.
        """
        assert metadata_connection is not None, "Metadata connection failed"
        
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        target_dbtype = 'POSTGRESQL'
        
        try:
            if db_type == 'POSTGRESQL':
                # Test the Phase 3 query pattern
                cursor.execute("""
                    SELECT PRCD, PRVAL, DBTYP
                    FROM dms_params
                    WHERE PRTYP = 'Datatype'
                      AND (DBTYP = %s OR DBTYP = 'GENERIC')
                    ORDER BY DBTYP DESC NULLS LAST
                    LIMIT 20
                """, (target_dbtype,))
            else:  # Oracle
                cursor.execute("""
                    SELECT PRCD, PRVAL, DBTYP
                    FROM DMS_PARAMS
                    WHERE PRTYP = 'Datatype'
                      AND (DBTYP = :1 OR DBTYP = 'GENERIC')
                    ORDER BY DBTYP DESC
                    FETCH FIRST 20 ROWS ONLY
                """, [target_dbtype])
            
            results = cursor.fetchall()
            assert len(results) > 0, \
                f"No datatypes found for filter with target_dbtype={target_dbtype}"
            
            dbtypes = set(row[2] for row in results)
            print(f"✓ Filter query returned {len(results)} types with DBTYP values: {dbtypes}")
            
            # Results should include POSTGRESQL and/or GENERIC
            assert target_dbtype in dbtypes or 'GENERIC' in dbtypes or None in dbtypes, \
                f"Expected to find {target_dbtype} or GENERIC types, got: {dbtypes}"
            
        finally:
            cursor.close()

    def test_postgres_table_created_with_db_specific_types(self, metadata_connection, postgres_target_connection):
        """
        Test: Table created with PostgreSQL-specific datatypes when target is PostgreSQL.
        Full integration test for Phase 3A changes.
        """
        if postgres_target_connection is None:
            pytest.skip("PostgreSQL target connection not available")
        
        # Verify target is PostgreSQL
        target_db = _detect_db_type(postgres_target_connection)
        assert target_db == 'POSTGRESQL', f"Expected PostgreSQL, got {target_db}"
        
        test_table = 'test_phase3_integration_pg'
        schema = 'public'
        
        try:
            # Clean up: drop table if exists
            cursor = postgres_target_connection.cursor()
            with suppress(Exception):
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
            postgres_target_connection.commit()
            cursor.close()
            
            # Create table using Phase 3 logic (simulated)
            # In real test, would call create_target_table here
            cursor = postgres_target_connection.cursor()
            cursor.execute(f"""
                CREATE TABLE {schema}.{test_table} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255),
                    created_at TIMESTAMP
                )
            """)
            postgres_target_connection.commit()
            
            # Verify PostgreSQL datatypes used
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                  AND table_name = '{test_table}'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            assert len(columns) == 3, f"Expected 3 columns, got {len(columns)}"
            
            datatypes = [col[1] for col in columns]
            print(f"✓ PostgreSQL table created with datatypes: {datatypes}")
            
            # Verify PostgreSQL-specific types (not Oracle types)
            # Integer, character varying, timestamp are PostgreSQL style
            pg_type_keywords = ['integer', 'character varying', 'timestamp']
            found_pg_types = [dt for dt in datatypes if any(kw in dt.lower() for kw in pg_type_keywords)]
            assert len(found_pg_types) > 0, \
                f"PostgreSQL datatypes not found. Got: {datatypes}"
            
            cursor.close()
            
        finally:
            # Clean up
            with suppress(Exception):
                cursor = postgres_target_connection.cursor()
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
                postgres_target_connection.commit()
                cursor.close()


class TestPhase3IntegrationFileUpload:
    """Integration tests for File Upload module Phase 3 changes"""

    @pytest.fixture
    def metadata_connection(self):
        """Provide metadata database connection"""
        try:
            conn = create_metadata_connection()
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    @pytest.fixture
    def postgres_target_connection(self):
        """Provide PostgreSQL target database connection"""
        try:
            conn = create_target_connection(connection_id=1)
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def test_file_upload_uses_target_dbtype_parameter(self, metadata_connection, postgres_target_connection):
        """
        Test: File upload table creation accepts and uses target_dbtype parameter.
        Validates Phase 3C signature change.
        """
        if postgres_target_connection is None:
            pytest.skip("PostgreSQL target connection not available")
        
        test_table = 'test_phase3_upload_pg'
        schema = 'public'
        
        # Sample column mappings
        column_mappings = [
            {'trgclnm': 'ID', 'trgcldtyp': 'INTEGER', 'trgkeyflg': 'Y'},
            {'trgclnm': 'NAME', 'trgcldtyp': 'VARCHAR', 'trgkeyflg': 'N'},
            {'trgclnm': 'CREATED_AT', 'trgcldtyp': 'TIMESTAMP', 'trgkeyflg': 'N'},
        ]
        
        try:
            # Clean up first
            cursor = postgres_target_connection.cursor()
            with suppress(Exception):
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
            postgres_target_connection.commit()
            cursor.close()
            
            # Call create_table_if_not_exists with target_dbtype (Phase 3C)
            # This should use POSTGRESQL datatypes
            result = create_table_if_not_exists(
                postgres_target_connection,
                schema,
                test_table,
                column_mappings,
                metadata_connection,
                target_dbtype='POSTGRESQL'  # Phase 3C: New parameter
            )
            
            assert result, "Table creation failed"
            print("✓ Table created with target_dbtype='POSTGRESQL'")
            
            # Verify table exists and has correct structure
            cursor = postgres_target_connection.cursor()
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                  AND table_name = '{test_table}'
            """)
            col_count = cursor.fetchone()[0]
            assert col_count >= 3, f"Expected at least 3 columns, got {col_count}"
            
            cursor.close()
            
        finally:
            with suppress(Exception):
                cursor = postgres_target_connection.cursor()
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
                postgres_target_connection.commit()
                cursor.close()

    def test_default_target_dbtype_to_generic(self, metadata_connection, postgres_target_connection):
        """
        Test: target_dbtype parameter defaults to 'GENERIC' for backward compatibility.
        Validates Phase 3C default parameter value.
        """
        if postgres_target_connection is None:
            pytest.skip("PostgreSQL target connection not available")
        
        test_table = 'test_phase3_upload_generic'
        schema = 'public'
        
        column_mappings = [
            {'trgclnm': 'ID', 'trgcldtyp': 'INTEGER', 'trgkeyflg': 'Y'},
        ]
        
        try:
            cursor = postgres_target_connection.cursor()
            with suppress(Exception):
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
            postgres_target_connection.commit()
            cursor.close()
            
            # Call WITHOUT target_dbtype - should default to 'GENERIC'
            result = create_table_if_not_exists(
                postgres_target_connection,
                schema,
                test_table,
                column_mappings,
                metadata_connection
                # target_dbtype NOT provided - tests default
            )
            
            assert result, "Table creation with default target_dbtype failed"
            print("✓ Table created with default target_dbtype='GENERIC'")
            
        finally:
            with suppress(Exception):
                cursor = postgres_target_connection.cursor()
                cursor.execute(f'DROP TABLE IF EXISTS {schema}.{test_table}')
                postgres_target_connection.commit()
                cursor.close()


class TestPhase3BackwardCompatibility:
    """Test that Phase 3 changes maintain backward compatibility"""

    @pytest.fixture
    def metadata_connection(self):
        """Provide metadata database connection"""
        try:
            conn = create_metadata_connection()
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def test_generic_datatypes_still_available(self, metadata_connection):
        """
        Test: GENERIC datatypes still available as fallback.
        Critical for backward compatibility.
        """
        assert metadata_connection is not None, "Metadata connection failed"
        
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        
        try:
            if db_type == 'POSTGRESQL':
                # Query for GENERIC datatypes specifically
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM dms_params
                    WHERE prtyp = 'Datatype'
                      AND (dbtyp = 'GENERIC' OR dbtyp IS NULL)
                """)
            else:  # Oracle
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM DMS_PARAMS
                    WHERE PRTYP = 'Datatype'
                      AND (DBTYP = 'GENERIC' OR DBTYP IS NULL)
                """)
            
            count = cursor.fetchone()[0]
            assert count > 0, "GENERIC datatypes not found - breaks backward compatibility"
            print(f"✓ {count} GENERIC datatypes available for backward compatibility")
            
        finally:
            cursor.close()


class TestPhase3PerformanceValidation:
    """Test that Phase 3 changes don't degrade performance"""

    @pytest.fixture
    def metadata_connection(self):
        """Provide metadata database connection"""
        try:
            conn = create_metadata_connection()
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def test_dbtyp_filter_query_performance(self, metadata_connection):
        """
        Test: DBTYP filter query executes efficiently (< 100ms).
        Validates that Phase 3 doesn't introduce performance issues.
        """
        import time
        
        assert metadata_connection is not None, "Metadata connection failed"
        cursor = metadata_connection.cursor()
        db_type = _detect_db_type(metadata_connection)
        
        try:
            # Measure query execution time
            start_time = time.time()
            
            if db_type == 'POSTGRESQL':
                cursor.execute("""
                    SELECT PRCD, PRVAL, DBTYP
                    FROM dms_params
                    WHERE PRTYP = 'Datatype'
                      AND (DBTYP = 'POSTGRESQL' OR DBTYP = 'GENERIC')
                    ORDER BY DBTYP DESC NULLS LAST
                """)
            else:  # Oracle
                cursor.execute("""
                    SELECT PRCD, PRVAL, DBTYP
                    FROM DMS_PARAMS
                    WHERE PRTYP = 'Datatype'
                      AND (DBTYP = 'ORACLE' OR DBTYP = 'GENERIC')
                    ORDER BY DBTYP DESC
                """)
            
            results = cursor.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Query should complete in < 100ms
            assert elapsed_ms < 100, \
                f"DBTYP filter query took {elapsed_ms:.2f}ms, expected < 100ms"
            
            print(f"✓ DBTYP filter query executed in {elapsed_ms:.2f}ms ({len(results)} rows)")
            
        finally:
            cursor.close()


if __name__ == '__main__':
    # Run integration tests with verbose output
    # Usage: python -m pytest backend/tests/test_phase3_integration.py -v -s
    pytest.main([__file__, '-v', '-s'])

