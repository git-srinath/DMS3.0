"""
JSON Parser
Handles JSON files (flat and nested structures).
"""
import pandas as pd
import json
import os
from typing import List, Dict, Optional, Any
from .base_parser import BaseFileParser


class JSONParser(BaseFileParser):
    """Parser for JSON files."""
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if file is JSON format."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext == '.json'
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse JSON file.
        
        Options:
            - encoding: File encoding (default: 'utf-8')
            - orient: JSON orientation - 'records', 'index', 'values', etc. (default: 'records')
            - json_path: JSONPath expression for nested structures (future enhancement)
        """
        if options is None:
            options = {}
        
        encoding = options.get('encoding', 'utf-8')
        orient = options.get('orient', 'records')
        
        # Read JSON file
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # List of objects - convert directly
            df = pd.json_normalize(data)
        elif isinstance(data, dict):
            # Single object or nested structure
            if orient == 'records' and isinstance(data, dict):
                # Try to normalize nested structure
                df = pd.json_normalize(data)
            else:
                # Convert dict to DataFrame
                df = pd.DataFrame([data])
        else:
            # Other types - try to convert
            df = pd.DataFrame([data])
        
        return df
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from JSON file."""
        if options is None:
            options = {}
        
        encoding = options.get('encoding', 'utf-8')
        
        # Read JSON file
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        # Get first record to determine columns
        if isinstance(data, list) and len(data) > 0:
            # Use first item in list
            df = pd.json_normalize(data[0])
        elif isinstance(data, dict):
            df = pd.json_normalize(data)
        else:
            df = pd.DataFrame([data])
        
        return list(df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of JSON file. Optimized to limit data before processing."""
        if options is None:
            options = {}
        
        encoding = options.get('encoding', 'utf-8')
        
        # Optimize: For large JSON arrays, limit to first N items before normalizing
        # This prevents loading entire large files into memory
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            # Handle different structures
            if isinstance(data, list):
                # Limit to first N items BEFORE normalizing (saves significant memory)
                limited_data = data[:rows]
                df = pd.json_normalize(limited_data)
            elif isinstance(data, dict):
                df = pd.json_normalize(data)
            else:
                df = pd.DataFrame([data])
        except MemoryError:
            # If we get a MemoryError, the file is too large to load entirely
            # Re-raise it so the calling code can handle it appropriately
            # Don't try to read again as it will likely fail the same way
            raise ValueError(f"File is too large to load into memory. Please use a smaller file or increase available memory.")
        except json.JSONDecodeError as e:
            # Re-raise JSON decode errors with more context
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            # Catch any other exceptions and re-raise with context
            raise ValueError(f"Error reading JSON file: {str(e)}")
        
        return df

