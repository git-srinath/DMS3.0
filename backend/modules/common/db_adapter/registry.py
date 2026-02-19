"""Adapter registry for database-specific DDL operations."""
from __future__ import annotations
from typing import Dict

from .base_adapter import BaseDbAdapter
from .generic_adapter import GenericAdapter
from .oracle_adapter import OracleAdapter
from .postgres_adapter import PostgresAdapter
from .mysql_adapter import MysqlAdapter
from .mssql_adapter import SqlServerAdapter
from .sybase_adapter import SybaseAdapter
from .redshift_adapter import RedshiftAdapter
from .snowflake_adapter import SnowflakeAdapter
from .hive_adapter import HiveAdapter
from .db2_adapter import Db2Adapter


_ADAPTERS: Dict[str, BaseDbAdapter] = {
    "ORACLE": OracleAdapter(),
    "POSTGRESQL": PostgresAdapter(),
    "MYSQL": MysqlAdapter(),
    "MSSQL": SqlServerAdapter(),
    "SQL_SERVER": SqlServerAdapter(),
    "SYBASE": SybaseAdapter(),
    "REDSHIFT": RedshiftAdapter(),
    "SNOWFLAKE": SnowflakeAdapter(),
    "HIVE": HiveAdapter(),
    "DB2": Db2Adapter(),
    "GENERIC": GenericAdapter(),
}


def get_db_adapter(db_type: str) -> BaseDbAdapter:
    db_key = (db_type or "GENERIC").upper()
    return _ADAPTERS.get(db_key, GenericAdapter())
