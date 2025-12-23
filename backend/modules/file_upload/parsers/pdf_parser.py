"""
PDF Parser
Handles PDF files with table extraction support.
"""
import os
import pandas as pd
from typing import List, Dict, Optional
from .base_parser import BaseFileParser

# Try multiple PDF libraries for table extraction
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


class PDFParser(BaseFileParser):
    """Parser for PDF files with table extraction."""
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if file is PDF format."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext == '.pdf'
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse PDF file and extract tables.
        
        Options:
            - pages: Page numbers to extract (default: 'all' or [1, 2, 3])
            - table_index: Index of table to extract (default: 0, first table)
            - extraction_method: 'pdfplumber', 'tabula', or 'auto' (default: 'auto')
            - area: Bounding box area [top, left, bottom, right] for tabula (optional)
            - columns: Column boundaries for pdfplumber (optional)
            - header: Row number to use as header (default: 0)
            - encoding: Text encoding for extraction (default: 'utf-8')
        """
        if options is None:
            options = {}
        
        pages = options.get('pages', 'all')
        table_index = options.get('table_index', 0)
        extraction_method = options.get('extraction_method', 'auto')
        area = options.get('area')
        columns = options.get('columns')
        header = options.get('header', 0)
        
        # Choose extraction method
        if extraction_method == 'auto':
            if HAS_PDFPLUMBER:
                extraction_method = 'pdfplumber'
            elif HAS_TABULA:
                extraction_method = 'tabula'
            else:
                raise ValueError(
                    "No PDF extraction library available. "
                    "Please install pdfplumber (pip install pdfplumber) or tabula-py (pip install tabula-py)"
                )
        
        # Extract tables based on method
        if extraction_method == 'pdfplumber':
            if not HAS_PDFPLUMBER:
                raise ValueError("pdfplumber is required but not installed. Install with: pip install pdfplumber")
            return self._parse_with_pdfplumber(file_path, pages, table_index, columns, header)
        elif extraction_method == 'tabula':
            if not HAS_TABULA:
                raise ValueError("tabula-py is required but not installed. Install with: pip install tabula-py")
            return self._parse_with_tabula(file_path, pages, table_index, area, header)
        else:
            raise ValueError(f"Unknown extraction method: {extraction_method}")
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from PDF file."""
        if options is None:
            options = {}
        
        # Use preview to detect columns
        preview_df = self.preview(file_path, rows=1, options=options)
        return list(preview_df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of PDF file."""
        if options is None:
            options = {}
        
        # Parse full file first
        df = self.parse(file_path, options)
        
        # Limit to first N rows
        return df.head(rows)
    
    def _parse_with_pdfplumber(self, file_path: str, pages: str, table_index: int, 
                               columns: Optional[List], header: int) -> pd.DataFrame:
        """Extract tables using pdfplumber."""
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            # Determine pages to process
            if pages == 'all':
                page_nums = list(range(len(pdf.pages)))
            elif isinstance(pages, list):
                page_nums = [p - 1 for p in pages if 1 <= p <= len(pdf.pages)]  # Convert to 0-based
            else:
                page_nums = [int(pages) - 1] if 1 <= int(pages) <= len(pdf.pages) else []
            
            # Extract tables from each page
            for page_num in page_nums:
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
        
        # Select the requested table
        if not all_tables:
            return pd.DataFrame()
        
        if table_index >= len(all_tables):
            table_index = 0
        
        table_data = all_tables[table_index]
        
        # Convert to DataFrame
        if not table_data:
            return pd.DataFrame()
        
        # Use first row as header if specified
        if header is not None and len(table_data) > header:
            df = pd.DataFrame(table_data[header + 1:], columns=table_data[header])
        else:
            # No header row
            df = pd.DataFrame(table_data)
            df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
        
        # Clean up data - remove None values and empty strings
        df = df.replace('', pd.NA)
        df = df.dropna(how='all')  # Remove completely empty rows
        
        return df
    
    def _parse_with_tabula(self, file_path: str, pages: str, table_index: int,
                          area: Optional[List], header: int) -> pd.DataFrame:
        """Extract tables using tabula-py."""
        # Convert pages format for tabula
        if pages == 'all':
            pages_param = 'all'
        elif isinstance(pages, list):
            pages_param = pages
        else:
            pages_param = int(pages)
        
        # Extract tables
        tables = tabula.read_pdf(
            file_path,
            pages=pages_param,
            area=area,
            multiple_tables=True,
            pandas_options={'header': header if header is not None else 0}
        )
        
        if not tables:
            return pd.DataFrame()
        
        # Select the requested table
        if table_index >= len(tables):
            table_index = 0
        
        df = tables[table_index]
        
        # Clean up data
        df = df.replace('', pd.NA)
        df = df.dropna(how='all')
        
        return df
    
    def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF file."""
        if HAS_PDFPLUMBER:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        elif HAS_PYPDF2:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                return len(pdf.pages)
        else:
            raise ValueError("No PDF library available to count pages")
    
    def detect_tables(self, file_path: str, pages: Optional[str] = None) -> List[Dict]:
        """
        Detect all tables in PDF and return their locations.
        
        Returns list of dictionaries with table information:
        - page: Page number (1-based)
        - index: Table index on page
        - bbox: Bounding box coordinates (if available)
        """
        tables_info = []
        
        if HAS_PDFPLUMBER:
            with pdfplumber.open(file_path) as pdf:
                page_nums = list(range(len(pdf.pages))) if pages == 'all' or pages is None else [int(pages) - 1]
                
                for page_num in page_nums:
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    
                    for idx, table in enumerate(tables):
                        tables_info.append({
                            'page': page_num + 1,
                            'index': idx,
                            'rows': len(table) if table else 0,
                            'columns': len(table[0]) if table and table[0] else 0
                        })
        
        return tables_info

