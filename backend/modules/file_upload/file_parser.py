"""
File Parser Manager
Selects and uses the appropriate parser based on file type.
"""
import os
from typing import Optional, Dict, List
import pandas as pd

from .parsers.base_parser import BaseFileParser
from .parsers.csv_parser import CSVParser
from .parsers.excel_parser import ExcelParser
from .parsers.json_parser import JSONParser
from .parsers.parquet_parser import ParquetParser
from .parsers.xml_parser import XMLParser
from .parsers.pdf_parser import PDFParser
from .parsers.google_sheets_parser import GoogleSheetsParser


class FileParserManager:
    """Manages file parsers and selects appropriate parser for each file."""
    
    def __init__(self):
        """Initialize parser manager with available parsers."""
        self.parsers: List[BaseFileParser] = [
            CSVParser(),
            ExcelParser(),
            JSONParser(),
            ParquetParser(),
            XMLParser(),
            PDFParser(),
        ]
        # Google Sheets parser requires credentials, so it's added conditionally
        # Users can add it manually if needed via add_parser() method
    
    def get_parser(self, file_path: str) -> Optional[BaseFileParser]:
        """
        Get appropriate parser for file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance or None if no parser found
        """
        for parser in self.parsers:
            if parser.detect_format(file_path):
                return parser
        return None
    
    def detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type string (CSV, XLSX, JSON, etc.)
        """
        ext = os.path.splitext(file_path.lower())[1]
        ext_map = {
            '.csv': 'CSV',
            '.tsv': 'TSV',
            '.txt': 'CSV',  # Assume CSV for .txt
            '.xlsx': 'XLSX',
            '.xls': 'XLS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.parquet': 'PARQUET',
            '.parq': 'PARQUET',
            '.pdf': 'PDF',
            '.gsheet': 'GOOGLE_SHEETS',
        }
        return ext_map.get(ext, 'UNKNOWN')
    
    def parse_file(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse file using appropriate parser.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options
            
        Returns:
            pandas DataFrame with parsed data
            
        Raises:
            ValueError: If no parser found for file type
        """
        parser = self.get_parser(file_path)
        if parser is None:
            raise ValueError(f"No parser available for file: {file_path}")
        
        return parser.parse(file_path, options)
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """
        Get column names from file.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options
            
        Returns:
            List of column names
            
        Raises:
            ValueError: If no parser found for file type
        """
        parser = self.get_parser(file_path)
        if parser is None:
            raise ValueError(f"No parser available for file: {file_path}")
        
        return parser.get_columns(file_path, options)
    
    def preview_file(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Preview first N rows of file.
        
        Args:
            file_path: Path to the file
            rows: Number of rows to preview
            options: Parser-specific options
            
        Returns:
            pandas DataFrame with first N rows
            
        Raises:
            ValueError: If no parser found for file type
        """
        parser = self.get_parser(file_path)
        if parser is None:
            raise ValueError(f"No parser available for file: {file_path}")
        
        return parser.preview(file_path, rows, options)
    
    def get_file_info(self, file_path: str, options: Optional[Dict] = None) -> Dict:
        """
        Get file information.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options
            
        Returns:
            Dictionary with file information
        """
        parser = self.get_parser(file_path)
        if parser is None:
            return {
                "error": f"No parser available for file: {file_path}",
                "file_path": file_path
            }
        
        info = parser.get_file_info(file_path, options)
        info["file_type"] = self.detect_file_type(file_path)
        return info
    
    def add_parser(self, parser: BaseFileParser):
        """
        Add a custom parser to the manager.
        
        Args:
            parser: Parser instance to add
        """
        self.parsers.append(parser)
    
    def remove_parser(self, parser_type: type):
        """
        Remove a parser by type.
        
        Args:
            parser_type: Parser class type to remove
        """
        self.parsers = [p for p in self.parsers if not isinstance(p, parser_type)]

