"""MySQL adapter implementation."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class MysqlAdapter(BaseDbAdapter):
    db_type = "MYSQL"

    def ping_sql(self) -> str:
        return "SELECT 1"

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        """
        MySQL uses database-level connections, so schema is the database name.
        Since the connection already selects the database, we only use table name
        in DDL statements (CREATE/ALTER TABLE).
        """
        return table

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        if not schema:
            raise ValueError("MySQL requires schema/database name for table checks")
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        return cursor.fetchone() is not None

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        if not schema:
            raise ValueError("MySQL requires schema/database name for column checks")
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """,
            (schema, table, column),
        )
        return cursor.fetchone() is not None

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: List[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD COLUMN " + ", ADD COLUMN ".join(cols)

    def get_skey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "SKEY BIGINT PRIMARY KEY AUTO_INCREMENT"
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
