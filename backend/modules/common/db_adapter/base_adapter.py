"""
Base database adapter contract for DDL and metadata checks.
"""
from __future__ import annotations
from typing import Iterable, List, Optional


class BaseDbAdapter:
    db_type: str = "GENERIC"

    def ping_sql(self) -> str:
        return "SELECT 1"

    def normalize_identifier(self, name: str) -> str:
        return name

    def quote_identifier(self, name: str) -> str:
        return name

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        if schema:
            return f"{schema}.{table}"
        return table

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        raise NotImplementedError

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        raise NotImplementedError

    def build_create_table(
        self,
        schema: Optional[str],
        table: str,
        column_defs: Iterable[str],
        primary_keys: Optional[List[str]] = None,
    ) -> str:
        table_ref = self.format_table_ref(schema, table)
        columns_sql = ",\n    ".join(column_defs)
        if primary_keys:
            pk_cols = ", ".join(self.quote_identifier(col) for col in primary_keys)
            columns_sql += f",\n    PRIMARY KEY ({pk_cols})"
        return f"CREATE TABLE {table_ref} (\n    {columns_sql}\n)"

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: Iterable[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD (\n  " + ",\n  ".join(cols) + "\n)"

    def supports_sequence(self) -> bool:
        return False

    def ensure_sequence(self, cursor, schema: Optional[str], table: str, use_owner_filter: bool) -> None:
        return None

    def get_skey_column(self, table_type: str) -> Optional[str]:
        return None

    def get_rwhkey_column(self, table_type: str) -> Optional[str]:
        return None

    def get_dim_scd_columns(self) -> List[str]:
        return []

    def get_audit_columns(self) -> List[str]:
        return []
