"""
Test script to verify TRUNCATE TABLE fix for MySQL
"""
import sys
sys.path.insert(0, 'd:/DMS/DMSTOOL')

from backend.modules.common.db_adapter import get_db_adapter

print("Testing TRUNCATE TABLE statement formatting for all databases")
print("=" * 70)

test_cases = [
    ("MYSQL", "CDR", "DIM_ACNT_LN2"),
    ("ORACLE", "DW", "FACT_SALES"),
    ("POSTGRESQL", "public", "dim_customer"),
    ("MSSQL", "dbo", "Orders"),
]

for db_type, schema, table in test_cases:
    adapter = get_db_adapter(db_type)
    table_ref = adapter.format_table_ref(schema, table)
    truncate_sql = f"TRUNCATE TABLE {table_ref}"
    print(f"{db_type:12} | {truncate_sql}")

print("\n" + "=" * 70)
print("Expected results:")
print("  - MYSQL:      TRUNCATE TABLE DIM_ACNT_LN2 (no schema prefix)")
print("  - ORACLE:     TRUNCATE TABLE DW.FACT_SALES")
print("  - POSTGRESQL: TRUNCATE TABLE \"public\".\"dim_customer\"")
print("  - MSSQL:      TRUNCATE TABLE dbo.Orders")
print("=" * 70)
