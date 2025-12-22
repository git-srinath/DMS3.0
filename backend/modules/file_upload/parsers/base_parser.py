"""
Base Parser Interface
Abstract base class for all file parsers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd


class BaseFileParser(ABC):
    """Base class for all file parsers. All parsers must implement these methods."""
    
    @abstractmethod
    def detect_format(self, file_path: str) -> bool:
        """
        Detect if file matches this parser's format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file matches this parser's format, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse file and return DataFrame.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options (e.g., delimiter, sheet_name, etc.)
            
        Returns:
            pandas DataFrame with parsed data
        """
        pass
    
    @abstractmethod
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """
        Get column names from file without parsing entire file.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options
            
        Returns:
            List of column names
        """
        pass
    
    @abstractmethod
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Preview first N rows of the file.
        
        Args:
            file_path: Path to the file
            rows: Number of rows to preview
            options: Parser-specific options
            
        Returns:
            pandas DataFrame with first N rows
        """
        pass
    
    def get_file_info(self, file_path: str, options: Optional[Dict] = None) -> Dict:
        """
        Get basic file information (row count, column count, etc.).
        Default implementation - can be overridden for better performance.
        
        Args:
            file_path: Path to the file
            options: Parser-specific options
            
        Returns:
            Dictionary with file information
        """
        try:
            df = self.parse(file_path, options)
            return {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "file_path": file_path
            }
        except Exception as e:
            return {
                "error": str(e),
                "file_path": file_path
            }

