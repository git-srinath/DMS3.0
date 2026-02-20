"""PostgreSQL adapter implementation."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class PostgresAdapter(BaseDbAdapter):
    db_type = "POSTGRESQL"

    def ping_sql(self) -> str:
        return "SELECT 1"

    def normalize_identifier(self, name: str) -> str:
        return name.lower()

    def quote_identifier(self, name: str) -> str:
        return f'"{name.lower()}"'

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        if schema:
            return f'"{schema.lower()}"."{table.lower()}"'
        return f'"{table.lower()}"'

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        schema_name = schema.lower() if schema else "public"
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema_name, table.lower()),
        )
        return cursor.fetchone() is not None

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        schema_name = schema.lower() if schema else "public"
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """,
            (schema_name, table.lower(), column.lower()),
        )
        return cursor.fetchone() is not None

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: List[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD COLUMN " + ", ADD COLUMN ".join(cols)

        def supports_sequence(self) -> bool:
            return True

        def ensure_sequence(self, cursor, schema: Optional[str], table: str, use_owner_filter: bool) -> None:
            schema_name = (schema or "public").lower()
            seq_name = f"{table}_seq".lower()
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.sequences
                WHERE sequence_schema = %s
                  AND sequence_name = %s
                """,
                (schema_name, seq_name),
            )
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE SEQUENCE "{schema_name}"."{seq_name}" START WITH 1 INCREMENT BY 1')

    def get_skey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "SKEY BIGINT PRIMARY KEY"
        return None

    def get_rwhkey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "RWHKEY VARCHAR(32)"
        return None

    def get_dim_scd_columns(self) -> List[str]:
        return [
            "CURFLG VARCHAR(1)",
            "FROMDT TIMESTAMP",
            "TODT TIMESTAMP",
        ]

    def get_audit_columns(self) -> List[str]:
        return [
            "RECCRDT TIMESTAMP",
            "RECUPDT TIMESTAMP",
        ]
