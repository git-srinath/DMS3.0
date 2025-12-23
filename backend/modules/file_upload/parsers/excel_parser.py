"""
Excel Parser
Handles XLSX and XLS files.
"""
import pandas as pd
import os
from typing import List, Dict, Optional
from .base_parser import BaseFileParser


class ExcelParser(BaseFileParser):
    """Parser for Excel files (XLSX, XLS)."""
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if file is Excel format."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext in ['.xlsx', '.xls']
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse Excel file.
        
        Options:
            - sheet_name: Sheet name or index (default: 0, first sheet)
            - header: Row number to use as header (default: 0)
            - skiprows: Number of rows to skip from start
            - skipfooter: Number of rows to skip from end
            - engine: 'openpyxl' for .xlsx, 'xlrd' for .xls (default: auto-detect)
        """
        if options is None:
            options = {}
        
        sheet_name = options.get('sheet_name', 0)
        header = options.get('header', 0)
        skiprows = options.get('skiprows', 0)
        skipfooter = options.get('skipfooter', 0)
        
        # Determine engine based on file extension
        ext = os.path.splitext(file_path.lower())[1]
        engine = options.get('engine')
        if engine is None:
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        
        # Read Excel file
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header,
            skiprows=skiprows,
            engine=engine
        )
        
        # Skip footer rows if specified
        if skipfooter > 0:
            df = df.iloc[:-skipfooter]
        
        return df
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from Excel file."""
        if options is None:
            options = {}
        
        sheet_name = options.get('sheet_name', 0)
        header = options.get('header', 0)
        
        ext = os.path.splitext(file_path.lower())[1]
        engine = options.get('engine')
        if engine is None:
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        
        # Read only header row
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header,
            nrows=0,  # Read only header
            engine=engine
        )
        
        return list(df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of Excel file."""
        if options is None:
            options = {}
        
        sheet_name = options.get('sheet_name', 0)
        header = options.get('header', 0)
        skiprows = options.get('skiprows', 0)
        
        ext = os.path.splitext(file_path.lower())[1]
        engine = options.get('engine')
        if engine is None:
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header,
            skiprows=skiprows,
            nrows=rows,
            engine=engine
        )
        
        return df
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """Get list of sheet names in Excel file."""
        try:
            ext = os.path.splitext(file_path.lower())[1]
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            
            xl_file = pd.ExcelFile(file_path, engine=engine)
            return xl_file.sheet_names
        except Exception:
            return []

