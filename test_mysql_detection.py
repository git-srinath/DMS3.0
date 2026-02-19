"""
Test script to verify MySQL connection detection
"""
import sys
sys.path.insert(0, 'd:/DMS/DMSTOOL')

print("Testing database type detection")
print("=" * 70)

# Test with mock connection objects
class MockMySQLConnection:
    """Mock MySQL connection"""
    pass

class MockPostgreSQLConnection:
    """Mock PostgreSQL connection"""
    pass

class MockOracleConnection:
    """Mock Oracle connection"""
    pass

# Set module names to simulate different connection types
import types

# Create mock MySQL connection
mysql_conn = MockMySQLConnection()
mysql_conn.__class__.__module__ = "mysql.connector.connection_cext"
mysql_conn.__class__.__name__ = "CMySQLConnection"

# Create mock PostgreSQL connection
pg_conn = MockPostgreSQLConnection()
pg_conn.__class__.__module__ = "psycopg2.extensions"
pg_conn.__class__.__name__ = "connection"

# Create mock Oracle connection
oracle_conn = MockOracleConnection()
oracle_conn.__class__.__module__ = "oracledb"
oracle_conn.__class__.__name__ = "Connection"

# Test detection
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.common.db_adapter import get_db_adapter

print("\nConnection Type Detection:")
print("-" * 70)

connections = [
    ("MySQL", mysql_conn),
    ("PostgreSQL", pg_conn),
    ("Oracle", oracle_conn),
]

for name, conn in connections:
    detected_type = _detect_db_type(conn)
    adapter = get_db_adapter(detected_type)
    adapter_name = type(adapter).__name__
    
    # Test table formatting
    table_ref = adapter.format_table_ref("CDR", "DIM_ACNT_LN2")
    
    print(f"{name:12} | Detected: {detected_type:12} | Adapter: {adapter_name:20} | Table: {table_ref}")

print("\n" + "=" * 70)
print("Expected:")
print("  MySQL:      Detected: MYSQL        | Adapter: MysqlAdapter        | Table: DIM_ACNT_LN2")
print("  PostgreSQL: Detected: POSTGRESQL   | Adapter: PostgresAdapter     | Table: \"cdr\".\"dim_acnt_ln2\"")
print("  Oracle:     Detected: ORACLE       | Adapter: OracleAdapter       | Table: CDR.DIM_ACNT_LN2")
print("=" * 70)
