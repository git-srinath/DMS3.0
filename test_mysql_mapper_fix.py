"""
Test script to verify MySQL table name formatting fix in mapper
"""
import sys
sys.path.insert(0, 'd:/DMS/DMSTOOL')

from backend.modules.mapper.database_sql_adapter import DatabaseSQLAdapter

print("Testing MySQL table name formatting in database_sql_adapter")
print("=" * 70)

# Test MySQL formatting
mysql_adapter = DatabaseSQLAdapter("MYSQL")
result = mysql_adapter.format_table_name("CDR", "DIM_ACNT_LN2")
print(f"MySQL format_table_name('CDR', 'DIM_ACNT_LN2') = '{result}'")
print(f"Expected: `DIM_ACNT_LN2` (no schema prefix)")
print(f"Match: {result == '`DIM_ACNT_LN2`'}")

print("\n" + "=" * 70)
print("Testing other databases (should include schema):")
print("=" * 70)

test_cases = [
    ("ORACLE", "HR", "EMPLOYEES", "HR.EMPLOYEES"),
    ("POSTGRESQL", "PUBLIC", "USERS", 'public.users'),
    ("MSSQL", "dbo", "Orders", '[dbo].[Orders]'),
]

for db_type, schema, table, expected in test_cases:
    adapter = DatabaseSQLAdapter(db_type)
    result = adapter.format_table_name(schema, table)
    match = "✓" if result == expected else "✗"
    print(f"{match} {db_type:12} | {schema}.{table:20} => {result:30} (expected: {expected})")

print("\n" + "=" * 70)
print("Summary: MySQL should only return table name, others include schema")
print("=" * 70)
