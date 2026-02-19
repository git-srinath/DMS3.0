"""Test script to verify adapter format_table_ref behavior after MySQL fix."""
import sys
sys.path.insert(0, 'd:/DMS/DMSTOOL')

from backend.modules.common.db_adapter import get_db_adapter

print("Adapter Table Reference Formatting Test")
print("=" * 60)

test_cases = [
    ('MYSQL', 'CDR', 'DIM_ACNT_LN2'),
    ('POSTGRESQL', 'analytics', 'sales'),
    ('MSSQL', 'dbo', 'Customers'),
    ('ORACLE', 'HR', 'EMPLOYEES'),
    ('SYBASE', 'guest', 'orders'),
    ('DB2', 'MYSCHEMA', 'ORDERS'),
    ('REDSHIFT', 'public', 'events'),
    ('SNOWFLAKE', 'sales_schema', 'transactions'),
    ('HIVE', 'warehouse', 'fact_sales'),
]

for db_type, schema, table in test_cases:
    try:
        adapter = get_db_adapter(db_type)
        table_ref = adapter.format_table_ref(schema, table)
        print(f"{db_type:12} | {schema:15} . {table:20} => {table_ref}")
    except Exception as e:
        print(f"{db_type:12} | ERROR: {e}")

print("\nMySQL specific test (should ONLY return table name):")
mysql_adapter = get_db_adapter('MYSQL')
print(f"  With schema: {mysql_adapter.format_table_ref('CDR', 'DIM_ACNT_LN2')}")
print(f"  Without schema: {mysql_adapter.format_table_ref(None, 'DIM_ACNT_LN2')}")

print("\nPostgreSQL specific test (should include schema with quotes and lowercase):")
pg_adapter = get_db_adapter('POSTGRESQL')
print(f"  With schema: {pg_adapter.format_table_ref('Analytics', 'Sales')}")
print(f"  Without schema: {pg_adapter.format_table_ref(None, 'Sales')}")
