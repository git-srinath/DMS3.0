"""Sanity tests for DB adapters without live databases."""
import os
import sys
import pytest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.modules.common.db_adapter.registry import get_db_adapter


class DummyCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


@pytest.mark.parametrize(
    "db_type",
    [
        "ORACLE",
        "POSTGRESQL",
        "MYSQL",
        "MSSQL",
        "SQL_SERVER",
        "SYBASE",
        "REDSHIFT",
        "SNOWFLAKE",
        "HIVE",
        "DB2",
        "GENERIC",
    ],
)
def test_adapter_registry_returns_adapter(db_type):
    adapter = get_db_adapter(db_type)
    assert adapter is not None
    assert adapter.db_type


@pytest.mark.parametrize("db_type", ["ORACLE", "POSTGRESQL", "MYSQL", "MSSQL", "SYBASE", "REDSHIFT", "SNOWFLAKE", "DB2"])
def test_build_create_and_alter_sql(db_type):
    adapter = get_db_adapter(db_type)
    create_sql = adapter.build_create_table("TRG", "TEST_TABLE", ["COL1 VARCHAR(10)"])
    assert "CREATE TABLE" in create_sql
    alter_sql = adapter.build_alter_table("TRG", "TEST_TABLE", ["COL2 VARCHAR(10)"])
    assert "ALTER TABLE" in alter_sql


def test_mysql_schema_required_for_checks():
    adapter = get_db_adapter("MYSQL")
    cursor = DummyCursor(fetchone_result=None)
    with pytest.raises(ValueError):
        adapter.table_exists(cursor, None, "T1")
    with pytest.raises(ValueError):
        adapter.column_exists(cursor, None, "T1", "C1")


def test_snowflake_schema_required_for_checks():
    adapter = get_db_adapter("SNOWFLAKE")
    cursor = DummyCursor(fetchone_result=None)
    with pytest.raises(ValueError):
        adapter.table_exists(cursor, None, "T1")
    with pytest.raises(ValueError):
        adapter.column_exists(cursor, None, "T1", "C1")


def test_table_exists_positive_and_negative():
    adapter = get_db_adapter("POSTGRESQL")
    cursor = DummyCursor(fetchone_result=(1,))
    assert adapter.table_exists(cursor, "public", "t1") is True

    cursor = DummyCursor(fetchone_result=None)
    assert adapter.table_exists(cursor, "public", "t1") is False


def test_hive_column_exists_uses_describe():
    adapter = get_db_adapter("HIVE")
    cursor = DummyCursor(fetchone_result=("t1",), fetchall_result=[("col1", "string"), ("col2", "int")])
    assert adapter.column_exists(cursor, "default", "t1", "col2") is True
    assert adapter.column_exists(cursor, "default", "t1", "missing") is False
