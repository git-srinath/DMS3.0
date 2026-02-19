"""Oracle adapter implementation."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class OracleAdapter(BaseDbAdapter):
    db_type = "ORACLE"

    def ping_sql(self) -> str:
        return "SELECT 1 FROM DUAL"

    def normalize_identifier(self, name: str) -> str:
        return name.upper()

    def quote_identifier(self, name: str) -> str:
        import re

        name_upper = name.upper()
        is_simple_identifier = re.match(r"^[A-Z_][A-Z0-9_]*$", name_upper) is not None
        reserved_keywords = {
            "DATE",
            "NUMBER",
            "VARCHAR2",
            "TIMESTAMP",
            "USER",
            "SESSION",
            "LEVEL",
            "ROWID",
            "UID",
            "SYSDATE",
            "DOMAIN",
            "VALUE",
        }
        if (not is_simple_identifier) or (name_upper in reserved_keywords):
            return f'"{name_upper}"'
        return name_upper

    def format_table_ref(self, schema: Optional[str], table: str) -> str:
        if schema:
            return f"{schema.upper()}.{table.upper()}"
        return table.upper()

    def table_exists(self, cursor, schema: Optional[str], table: str) -> bool:
        if schema:
            cursor.execute(
                """
                SELECT COUNT(*) FROM all_tables
                WHERE owner = UPPER(:1) AND table_name = UPPER(:2)
                """,
                [schema, table],
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) FROM user_tables
                WHERE table_name = UPPER(:1)
                """,
                [table],
            )
        result = cursor.fetchone()
        return result[0] > 0 if result else False

    def column_exists(self, cursor, schema: Optional[str], table: str, column: str) -> bool:
        if schema:
            cursor.execute(
                """
                SELECT COUNT(*) FROM all_tab_columns
                WHERE owner = UPPER(:1) AND table_name = UPPER(:2) AND column_name = UPPER(:3)
                """,
                [schema, table, column],
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) FROM user_tab_columns
                WHERE table_name = UPPER(:1) AND column_name = UPPER(:2)
                """,
                [table, column],
            )
        result = cursor.fetchone()
        return result[0] > 0 if result else False

    def build_alter_table(self, schema: Optional[str], table: str, column_defs: List[str]) -> str:
        table_ref = self.format_table_ref(schema, table)
        cols = list(column_defs)
        if not cols:
            raise ValueError("No columns provided for ALTER TABLE")
        return f"ALTER TABLE {table_ref} ADD (\n  " + ",\n  ".join(cols) + "\n)"

    def supports_sequence(self) -> bool:
        return True

    def ensure_sequence(self, cursor, schema: Optional[str], table: str, use_owner_filter: bool) -> None:
        seq_name = f"{table}_SEQ".upper()
        if use_owner_filter and schema:
            cursor.execute(
                """
                SELECT sequence_name FROM all_sequences
                WHERE sequence_owner = :owner AND sequence_name = :seq
                """,
                {"owner": schema.upper(), "seq": seq_name},
            )
        else:
            cursor.execute(
                """
                SELECT sequence_name FROM user_sequences
                WHERE sequence_name = :seq
                """,
                {"seq": seq_name},
            )
        seq_exists = cursor.fetchone()
        if not seq_exists:
            schema_prefix = f"{schema.upper()}." if schema else ""
            cursor.execute(
                f"CREATE SEQUENCE {schema_prefix}{seq_name} START WITH 1 INCREMENT BY 1"
            )

    def get_skey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "SKEY NUMBER(20) PRIMARY KEY"
        return None

    def get_rwhkey_column(self, table_type: str) -> Optional[str]:
        if table_type in ("DIM", "FCT", "MRT"):
            return "RWHKEY VARCHAR2(32)"
        return None

    def get_dim_scd_columns(self) -> List[str]:
        return [
            "CURFLG VARCHAR2(1)",
            "FROMDT DATE",
            "TODT DATE",
        ]

    def get_audit_columns(self) -> List[str]:
        return [
            "RECCRDT DATE",
            "RECUPDT DATE",
        ]
