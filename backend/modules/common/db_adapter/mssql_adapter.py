"""SQL Server adapter implementation (SQL Server / MSSQL / Sybase-style)."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class SqlServerAdapter(BaseDbAdapter):
    db_type = "SQL_SERVER"

    def ping_sql(self) -> str:
        return "SELECT 1"

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        """
        SQL Server supports schemas within databases. The connection already selects
        a database, and schema.table format is standard for SQL Server DDL.
        Schema here represents the actual schema (e.g., 'dbo', 'myschema').
        """
        # SQL Server supports schema.table format, keep as is
        if schema:
            return f"{schema}.{table}"
        return table

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        if schema:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = ? AND table_name = ?
                """,
                (schema, table),
            )
        else:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_name = ?
                """,
                (table,),
            )
        return cursor.fetchone() is not None

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        if schema:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = ? AND table_name = ? AND column_name = ?
                """,
                (schema, table, column),
            )
        else:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = ? AND column_name = ?
                """,
                (table, column),
            )
        return cursor.fetchone() is not None

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: List[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD " + ", ".join(cols)

    def get_skey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "SKEY BIGINT IDENTITY(1,1) PRIMARY KEY"
        return None

    def get_rwhkey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "RWHKEY VARCHAR(32)"
        return None

    def get_dim_scd_columns(self) -> List[str]:
        return [
            "CURFLG VARCHAR(1)",
            "FROMDT DATETIME",
            "TODT DATETIME",
        ]

    def get_audit_columns(self) -> List[str]:
        return [
            "RECCRDT DATETIME",
            "RECUPDT DATETIME",
        ]
