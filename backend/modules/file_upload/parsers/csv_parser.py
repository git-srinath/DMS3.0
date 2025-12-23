"""
CSV/TSV Parser
Handles comma-separated and tab-separated value files.
"""
import pandas as pd
import os
from typing import List, Dict, Optional
from .base_parser import BaseFileParser


class CSVParser(BaseFileParser):
    """Parser for CSV and TSV files."""
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if file is CSV or TSV."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext in ['.csv', '.tsv', '.txt']
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse CSV/TSV file.
        
        Options:
            - delimiter: Delimiter character (default: auto-detect)
            - encoding: File encoding (default: 'utf-8')
            - header: Row number to use as header (default: 0)
            - skiprows: Number of rows to skip from start
            - skipfooter: Number of rows to skip from end
            - quotechar: Quote character (default: '"')
        """
        if options is None:
            options = {}
        
        # Auto-detect delimiter if not specified
        delimiter = options.get('delimiter')
        if delimiter is None:
            # Try common delimiters
            with open(file_path, 'r', encoding=options.get('encoding', 'utf-8'), errors='ignore') as f:
                first_line = f.readline()
                if '\t' in first_line:
                    delimiter = '\t'
                elif ',' in first_line:
                    delimiter = ','
                elif ';' in first_line:
                    delimiter = ';'
                elif '|' in first_line:
                    delimiter = '|'
                else:
                    delimiter = ','  # Default
        
        # Parse with pandas
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=options.get('encoding', 'utf-8'),
            header=options.get('header', 0),
            skiprows=options.get('skiprows', 0),
            skipfooter=options.get('skipfooter', 0),
            engine='python' if options.get('skipfooter', 0) > 0 else 'c',
            quotechar=options.get('quotechar', '"'),
            on_bad_lines='skip'  # Skip bad lines instead of raising error
        )
        
        return df
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from CSV file."""
        if options is None:
            options = {}
        
        # Read just the header row
        delimiter = options.get('delimiter', ',')
        encoding = options.get('encoding', 'utf-8')
        header_row = options.get('header', 0)
        
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            nrows=0,  # Read only header
            header=header_row
        )
        
        return list(df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of CSV file."""
        if options is None:
            options = {}
        
        delimiter = options.get('delimiter')
        if delimiter is None:
            # Auto-detect delimiter
            with open(file_path, 'r', encoding=options.get('encoding', 'utf-8'), errors='ignore') as f:
                first_line = f.readline()
                if '\t' in first_line:
                    delimiter = '\t'
                elif ',' in first_line:
                    delimiter = ','
                elif ';' in first_line:
                    delimiter = ';'
                elif '|' in first_line:
                    delimiter = '|'
                else:
                    delimiter = ','
        
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=options.get('encoding', 'utf-8'),
            header=options.get('header', 0),
            skiprows=options.get('skiprows', 0),
            nrows=rows,
            quotechar=options.get('quotechar', '"'),
            on_bad_lines='skip'
        )
        
        return df

