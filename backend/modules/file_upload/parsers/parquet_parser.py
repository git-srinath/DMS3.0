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
        """Preview first N rows of Parquet file. Optimized to read only necessary rows."""
        if options is None:
            options = {}

        engine = self._get_engine(options)

        # Optimize: Use pyarrow directly to read only first N rows when possible
        # This avoids reading the entire file for large Parquet files
        try:
            if engine == 'pyarrow':
                try:
                    import pyarrow.parquet as pq
                    parquet_file = pq.ParquetFile(file_path)
                    # Read only first row group(s) that contain enough rows
                    total_rows = parquet_file.metadata.num_rows
                    
                    if total_rows <= rows:
                        # File has fewer rows than requested, read all
                        df = pd.read_parquet(file_path, engine=engine)
                    else:
                        # Read only first N rows using pyarrow's row group filtering
                        # Read first row group and slice if needed
                        first_row_group = parquet_file.read_row_group(0)
                        df = first_row_group.to_pandas()
                        
                        # If first row group has enough rows, slice it
                        if len(df) >= rows:
                            df = df.head(rows)
                        else:
                            # Need more rows, read additional row groups (limit to max 5 row groups for performance)
                            rows_read = len(df)
                            max_row_groups = min(5, parquet_file.num_row_groups)  # Limit to prevent hanging
                            for i in range(1, max_row_groups):
                                if rows_read >= rows:
                                    break
                                row_group = parquet_file.read_row_group(i)
                                df_additional = row_group.to_pandas()
                                df = pd.concat([df, df_additional], ignore_index=True)
                                rows_read = len(df)
                                if rows_read >= rows:
                                    df = df.head(rows)
                                    break
                except (ImportError, AttributeError, Exception) as e:
                    # If pyarrow optimization fails, fall back to standard approach
                    # Log the error but continue with fallback
                    import logging
                    logging.warning(f"PyArrow optimization failed, using standard read: {str(e)}")
                    df = pd.read_parquet(file_path, engine=engine)
                    df = df.head(rows)
            else:
                # For fastparquet or fallback, read full file then slice
                # This is acceptable for moderate sizes
                df = pd.read_parquet(file_path, engine=engine)
                df = df.head(rows)
        except Exception as e:
            # Final fallback: If all else fails, try standard read
            # This ensures we don't hang even if optimization fails
            import logging
            logging.warning(f"Parquet preview optimization failed, using standard read: {str(e)}")
            df = pd.read_parquet(file_path, engine=engine)
            df = df.head(rows)
        
        return df


