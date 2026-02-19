"""Generic adapter implementation for unknown database types."""
from __future__ import annotations
from typing import List, Optional

from .base_adapter import BaseDbAdapter


class GenericAdapter(BaseDbAdapter):
    db_type = "GENERIC"

    def ping_sql(self) -> str:
        return "SELECT 1"

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
