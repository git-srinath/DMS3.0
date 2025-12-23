"""
Parquet Parser
Handles Apache Parquet files.
"""
import os
from typing import List, Dict, Optional

import pandas as pd

from .base_parser import BaseFileParser


class ParquetParser(BaseFileParser):
    """Parser for Parquet files (.parquet, .parq)."""

    def detect_format(self, file_path: str) -> bool:
        """Detect if file is Parquet format."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext in [".parquet", ".parq"]

    def _get_engine(self, options: Optional[Dict] = None) -> str:
        """
        Determine which Parquet engine to use.

        We default to 'pyarrow', which is listed in backend/requirements.txt.
        """
        if options is None:
            options = {}
        engine = options.get("engine") or "pyarrow"
        # Only allow supported values to avoid "engine must be one of" errors
        if engine not in ("pyarrow", "fastparquet"):
            engine = "pyarrow"
        return engine

    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse Parquet file.

        Options (all optional, passed through to pandas.read_parquet):
            - columns: List of column names to read
            - engine: Parquet engine ('pyarrow' or 'fastparquet')
        """
        if options is None:
            options = {}

        read_kwargs: Dict = {}
        if "columns" in options and options["columns"]:
            read_kwargs["columns"] = options["columns"]

        engine = self._get_engine(options)
        try:
            df = pd.read_parquet(file_path, engine=engine, **read_kwargs)
        except ImportError as exc:
            # Provide a clear, user-friendly error if the engine is not installed
            raise ValueError(
                "Parquet support requires the 'pyarrow' (recommended) or 'fastparquet' "
                "package to be installed on the server."
            ) from exc
        return df

    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from Parquet file."""
        if options is None:
            options = {}

        engine = self._get_engine(options)

        # Read no data, just schema/columns when possible
        try:
            df = pd.read_parquet(file_path, columns=None, engine=engine)
        except TypeError:
            # Older pandas may not accept columns=None; fall back to reading full file
            df = pd.read_parquet(file_path, engine=engine)
        return list(df.columns)

    def preview(
        self,
        file_path: str,
        rows: int = 10,
        options: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """Preview first N rows of Parquet file."""
        if options is None:
            options = {}

        engine = self._get_engine(options)

        # pandas.read_parquet does not support nrows directly in older versions.
        # Read full file, then slice first N rows. This is acceptable for moderate sizes.
        df = pd.read_parquet(file_path, engine=engine)
        return df.head(rows)


