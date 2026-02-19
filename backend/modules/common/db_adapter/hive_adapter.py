"""Hive adapter implementation."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class HiveAdapter(BaseDbAdapter):
    db_type = "HIVE"

    def ping_sql(self) -> str:
        return "SELECT 1"

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        if schema:
            return f"{schema}.{table}"
        return table

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        # Hive metadata checks vary by driver; use SHOW TABLES fallback.
        if schema:
            cursor.execute(f"SHOW TABLES IN {schema} LIKE '{table}'")
        else:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
        return cursor.fetchone() is not None

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        table_ref = self.format_table_ref(schema, table)
        cursor.execute(f"DESCRIBE {table_ref}")
        rows = cursor.fetchall() or []
        return any(str(row[0]).strip().lower() == column.lower() for row in rows)

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: List[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD COLUMNS (" + ", ".join(cols) + ")"

    def get_skey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "SKEY BIGINT"
        return None

    def get_rwhkey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "RWHKEY STRING"
        return None

    def get_dim_scd_columns(self) -> List[str]:
        return [
            "CURFLG STRING",
            "FROMDT TIMESTAMP",
            "TODT TIMESTAMP",
        ]

    def get_audit_columns(self) -> List[str]:
        return [
            "RECCRDT TIMESTAMP",
            "RECUPDT TIMESTAMP",
        ]
