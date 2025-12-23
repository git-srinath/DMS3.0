# File Format Parsers Implementation

## Overview

This document describes the implementation of additional file format parsers for the File Upload module: XML, PDF, and Google Sheets.

## Implemented Parsers

### 1. XML Parser (`xml_parser.py`)

**Features:**
- Supports XPath expressions for flexible data extraction
- Auto-detection of row elements and column structure
- Support for both element content and attributes
- XML namespace support (requires lxml)
- Graceful fallback to standard library if lxml is not available

**Usage Options:**
- `row_xpath`: XPath expression to select row elements (e.g., `//item`, `/root/customers/customer`)
- `columns`: Dictionary mapping column names to XPath expressions (e.g., `{'name': './name', 'id': './@id'}`)
- `attribute_mode`: If True, extracts attributes; if False, extracts text content
- `namespace`: Dictionary mapping namespace prefixes to URIs
- `encoding`: File encoding (default: 'utf-8')

**Example:**
```python
options = {
    'row_xpath': '//customer',
    'columns': {
        'customer_id': './@id',
        'name': './name',
        'email': './email',
        'city': './address/city'
    }
}
df = xml_parser.parse('customers.xml', options)
```

**Dependencies:**
- `lxml` (recommended for full XPath support)
- Standard library `xml.etree.ElementTree` (fallback, limited XPath support)

### 2. PDF Parser (`pdf_parser.py`)

**Features:**
- Table extraction from PDF files
- Support for multiple extraction libraries (pdfplumber, tabula-py)
- Page selection and table indexing
- Automatic table detection
- Header row configuration

**Usage Options:**
- `pages`: Page numbers to extract ('all' or list like [1, 2, 3])
- `table_index`: Index of table to extract (default: 0)
- `extraction_method`: 'pdfplumber', 'tabula', or 'auto' (default: 'auto')
- `area`: Bounding box area [top, left, bottom, right] for tabula (optional)
- `columns`: Column boundaries for pdfplumber (optional)
- `header`: Row number to use as header (default: 0)

**Example:**
```python
options = {
    'pages': [1, 2],  # Extract from pages 1 and 2
    'table_index': 0,  # First table on each page
    'extraction_method': 'pdfplumber',
    'header': 0
}
df = pdf_parser.parse('report.pdf', options)
```

**Dependencies:**
- `pdfplumber` (recommended for most use cases)
- `tabula-py` (alternative, good for structured tables)
- `PyPDF2` (optional, for page counting)

### 3. Google Sheets Parser (`google_sheets_parser.py`)

**Features:**
- Reads Google Sheets via Google Sheets API
- Support for OAuth2 and Service Account authentication
- Sheet selection by name or index
- Range selection using A1 notation
- Multiple value render options (formatted, unformatted, formula)

**Usage Options:**
- `sheet_name`: Sheet name or index (default: 0)
- `range`: A1 notation range (e.g., 'A1:Z100' or 'Sheet1!A1:Z100')
- `header`: Row number to use as header (default: 0)
- `value_render_option`: 'FORMATTED_VALUE', 'UNFORMATTED_VALUE', or 'FORMULA'
- `date_time_render_option`: 'SERIAL_NUMBER' or 'FORMATTED_STRING'

**Initialization:**
The Google Sheets parser requires authentication credentials. It can be initialized in several ways:

```python
# Option 1: Service Account (recommended for server applications)
parser = GoogleSheetsParser(service_account_path='path/to/service-account.json')

# Option 2: OAuth2 Credentials
parser = GoogleSheetsParser(credentials_path='path/to/credentials.json')

# Option 3: Pre-authenticated credentials object
parser = GoogleSheetsParser(credentials=credentials_object)
```

**File Path Format:**
Google Sheets can be identified by:
- Full URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
- Sheet ID only: `{SHEET_ID}` (long alphanumeric string)

**Example:**
```python
sheet_id = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
options = {
    'sheet_name': 'Sheet1',
    'range': 'A1:Z1000',
    'header': 0
}
df = parser.parse(sheet_id, options)
```

**Dependencies:**
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

## Integration

### FileParserManager Updates

The `FileParserManager` class in `file_parser.py` has been updated to include:

1. **XML Parser**: Automatically included in the default parser list
2. **PDF Parser**: Automatically included in the default parser list
3. **Google Sheets Parser**: Not included by default (requires credentials setup)
   - Can be added manually using `parser_manager.add_parser(GoogleSheetsParser(...))`

### File Type Detection

The `detect_file_type` method has been updated to recognize:
- `.xml` → `XML`
- `.pdf` → `PDF`
- `.gsheet` → `GOOGLE_SHEETS` (rare, usually uses URL or ID)

### Usage in File Upload Module

The parsers are automatically available through the existing `FileParserManager` instance used in:
- `file_upload_executor.py`: For parsing files during execution
- `fastapi_file_upload.py`: For file upload and preview endpoints

No changes are required to existing code - the parsers work with the existing API.

## Dependencies

### Required (for full functionality)
All dependencies have been added to `backend/requirements.txt`:

```txt
# XML parsing
lxml

# PDF parsing (at least one required)
pdfplumber
tabula-py

# Google Sheets (optional, requires credentials setup)
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

### Installation

```bash
pip install lxml pdfplumber tabula-py
# For Google Sheets:
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Implementation Details

### Parser Interface

All parsers implement the `BaseFileParser` abstract class, which requires:
- `detect_format(file_path) -> bool`: Detect if file matches format
- `parse(file_path, options) -> pd.DataFrame`: Parse full file
- `get_columns(file_path, options) -> List[str]`: Get column names
- `preview(file_path, rows, options) -> pd.DataFrame`: Preview first N rows

### Error Handling

All parsers include:
- Graceful degradation when optional libraries are not installed
- Clear error messages indicating required dependencies
- Fallback mechanisms where possible (e.g., XML parser with/without lxml)

### Security Considerations

- XML parser disables entity resolution to prevent XXE attacks
- Google Sheets parser requires explicit authentication setup
- PDF parsers use established libraries with security best practices

## Testing Recommendations

1. **XML Parser:**
   - Test with various XML structures (flat, nested, with/without attributes)
   - Test with and without lxml library
   - Test namespace handling
   - Test XPath expressions

2. **PDF Parser:**
   - Test with different PDF table structures
   - Test with both pdfplumber and tabula-py
   - Test page selection and table indexing
   - Test header detection

3. **Google Sheets Parser:**
   - Test with service account authentication
   - Test with OAuth2 authentication
   - Test sheet selection and range specification
   - Test various data types and formats

## Future Enhancements

Potential improvements:
1. **XML Parser:**
   - Support for XML Schema validation
   - Support for JSONPath-like syntax for simpler queries
   - Better auto-detection of complex nested structures

2. **PDF Parser:**
   - OCR support for scanned PDFs (requires tesseract)
   - Text extraction from non-table content
   - Support for form data extraction

3. **Google Sheets Parser:**
   - Support for Google Drive file access
   - Batch processing of multiple sheets
   - Incremental loading based on modification date

## Notes

- The Google Sheets parser is not included in the default parser list because it requires authentication setup. Users should add it manually when needed.
- PDF parsing quality depends heavily on the PDF structure. Well-formatted tables work best.
- XML parsing with lxml provides full XPath support, while the standard library fallback has limited XPath capabilities.

