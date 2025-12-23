"""
XML Parser
Handles XML files with XPath support.
"""
import os
import pandas as pd
from typing import List, Dict, Optional, Any
from .base_parser import BaseFileParser

# Try to use lxml for better XPath support, fallback to standard library
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    import xml.etree.ElementTree as etree
    HAS_LXML = False


class XMLParser(BaseFileParser):
    """Parser for XML files with XPath support."""
    
    def detect_format(self, file_path: str) -> bool:
        """Detect if file is XML format."""
        ext = os.path.splitext(file_path.lower())[1]
        return ext in ['.xml']
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse XML file.
        
        Options:
            - row_xpath: XPath expression to select row elements (default: '//row' or '//*[not(*)]')
            - encoding: File encoding (default: 'utf-8')
            - attribute_mode: If True, extract attributes; if False, extract text content (default: False)
            - namespace: Dictionary mapping namespace prefixes to URIs
            - columns: Dictionary mapping column names to XPath expressions relative to row element
                       If not provided, will auto-detect from first row
        """
        if options is None:
            options = {}
        
        encoding = options.get('encoding', 'utf-8')
        row_xpath = options.get('row_xpath')
        attribute_mode = options.get('attribute_mode', False)
        namespace = options.get('namespace', {})
        columns = options.get('columns')
        
        # Parse XML file
        if HAS_LXML:
            parser = etree.XMLParser(resolve_entities=False)  # Security: disable entities
            tree = etree.parse(file_path, parser)
            root = tree.getroot()
        else:
            tree = etree.parse(file_path)
            root = tree.getroot()
        
        # Auto-detect row_xpath if not provided
        if not row_xpath:
            row_xpath = self._detect_row_xpath(root, namespace)
        
        # Get all row elements
        if HAS_LXML:
            row_elements = root.xpath(row_xpath, namespaces=namespace)
        else:
            # For standard library, convert XPath to ElementTree compatible
            # Simple conversion: //tag becomes .//tag, then use iterfind
            xpath_converted = row_xpath.replace('//', './/') if row_xpath.startswith('//') else row_xpath
            try:
                row_elements = list(root.iterfind(xpath_converted))
            except Exception:
                # Fallback: try without leading dot
                try:
                    row_elements = list(root.findall(xpath_converted.replace('.//', '//').replace('//', '.')))
                except Exception:
                    # Last resort: find all leaf elements (elements with no children)
                    row_elements = [elem for elem in root.iter() if not list(elem)]
        
        if not row_elements:
            return pd.DataFrame()
        
        # Auto-detect columns from first row if not provided
        if not columns:
            columns = self._detect_columns(row_elements[0], attribute_mode, namespace)
        
        # Extract data from each row
        rows_data = []
        for row_elem in row_elements:
            row_data = {}
            for col_name, xpath_expr in columns.items():
                try:
                    if HAS_LXML:
                        values = row_elem.xpath(xpath_expr, namespaces=namespace)
                        value = values[0] if values else None
                    else:
                        # Standard library fallback
                        xpath_clean = xpath_expr.replace('./', '').replace('@', '')
                        if '@' in xpath_expr:
                            # Attribute - extract from current element
                            attr_name = xpath_expr.split('@')[-1].split('/')[-1]
                            value = row_elem.attrib.get(attr_name) if hasattr(row_elem, 'attrib') else None
                        else:
                            # Text content from child element
                            found = row_elem.find(xpath_clean)
                            if found is not None:
                                value = found.text
                            else:
                                value = None
                    
                    row_data[col_name] = value
                except Exception:
                    row_data[col_name] = None
            
            rows_data.append(row_data)
        
        return pd.DataFrame(rows_data)
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from XML file."""
        if options is None:
            options = {}
        
        # Use preview to detect columns
        preview_df = self.preview(file_path, rows=1, options=options)
        return list(preview_df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of XML file."""
        if options is None:
            options = {}
        
        # Parse full file but limit rows in options
        encoding = options.get('encoding', 'utf-8')
        row_xpath = options.get('row_xpath')
        attribute_mode = options.get('attribute_mode', False)
        namespace = options.get('namespace', {})
        columns = options.get('columns')
        
        # Parse XML file
        if HAS_LXML:
            parser = etree.XMLParser(resolve_entities=False)
            tree = etree.parse(file_path, parser)
            root = tree.getroot()
        else:
            tree = etree.parse(file_path)
            root = tree.getroot()
        
        # Auto-detect row_xpath if not provided
        if not row_xpath:
            row_xpath = self._detect_row_xpath(root, namespace)
        
        # Get row elements
        if HAS_LXML:
            all_row_elements = root.xpath(row_xpath, namespaces=namespace)
        else:
            # For standard library, convert XPath to ElementTree compatible
            xpath_converted = row_xpath.replace('//', './/') if row_xpath.startswith('//') else row_xpath
            try:
                all_row_elements = list(root.iterfind(xpath_converted))
            except Exception:
                try:
                    all_row_elements = list(root.findall(xpath_converted.replace('.//', '//').replace('//', '.')))
                except Exception:
                    all_row_elements = [elem for elem in root.iter() if not list(elem)]
        
        # Limit to first N rows
        row_elements = all_row_elements[:rows]
        
        if not row_elements:
            return pd.DataFrame()
        
        # Auto-detect columns if not provided
        if not columns:
            columns = self._detect_columns(row_elements[0], attribute_mode, namespace)
        
        # Extract data
        rows_data = []
        for row_elem in row_elements:
            row_data = {}
            for col_name, xpath_expr in columns.items():
                try:
                    if HAS_LXML:
                        values = row_elem.xpath(xpath_expr, namespaces=namespace)
                        value = values[0] if values else None
                    else:
                        # Standard library fallback
                        xpath_clean = xpath_expr.replace('./', '').replace('@', '')
                        if '@' in xpath_expr:
                            # Attribute - extract from current element
                            attr_name = xpath_expr.split('@')[-1].split('/')[-1]
                            value = row_elem.attrib.get(attr_name) if hasattr(row_elem, 'attrib') else None
                        else:
                            # Text content from child element
                            found = row_elem.find(xpath_clean)
                            if found is not None:
                                value = found.text
                            else:
                                value = None
                    row_data[col_name] = value
                except Exception:
                    row_data[col_name] = None
            rows_data.append(row_data)
        
        return pd.DataFrame(rows_data)
    
    def _detect_row_xpath(self, root, namespace: Dict) -> str:
        """Auto-detect row XPath by finding repeating elements."""
        # Simple heuristic: find the most common element path
        element_counts = {}
        
        def count_elements(elem, path: str = '.'):
            if not list(elem):  # Leaf element
                element_counts[path] = element_counts.get(path, 0) + 1
            else:
                for child in elem:
                    child_path = f"{path}/{child.tag}"
                    if child_path in element_counts:
                        element_counts[child_path] += 1
                    else:
                        element_counts[child_path] = 1
                    count_elements(child, child_path)
        
        count_elements(root)
        
        # Return the path with most occurrences
        if element_counts:
            max_path = max(element_counts, key=element_counts.get)
            # Convert to XPath format
            return f"//{max_path.split('/')[-1]}"
        
        return '//row'  # Default fallback
    
    def _detect_columns(self, row_elem, attribute_mode: bool, namespace: Dict) -> Dict[str, str]:
        """Auto-detect column mappings from a row element."""
        columns = {}
        
        if attribute_mode:
            # Extract attributes
            if hasattr(row_elem, 'attrib'):
                for attr_name, attr_value in row_elem.attrib.items():
                    columns[attr_name] = f"./@{attr_name}"
        else:
            # Extract child elements
            for child in row_elem:
                if not list(child):  # Leaf element (has text content)
                    columns[child.tag] = f"./{child.tag}"
                else:
                    # Nested element - use tag name
                    columns[child.tag] = f"./{child.tag}"
        
        # If no children/attributes found, try text content
        if not columns and row_elem.text and row_elem.text.strip():
            columns['value'] = './text()' if HAS_LXML else '.'
        
        return columns

