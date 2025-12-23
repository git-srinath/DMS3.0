"""
Google Sheets Parser
Handles Google Sheets files via Google Sheets API.
"""
import os
import pandas as pd
from typing import List, Dict, Optional
from .base_parser import BaseFileParser

# Google Sheets API
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False
    Request = None

# Google Drive API for file access
try:
    from googleapiclient.http import MediaIoBaseDownload
    import io
    HAS_DRIVE_API = True
except ImportError:
    HAS_DRIVE_API = False


class GoogleSheetsParser(BaseFileParser):
    """Parser for Google Sheets files."""
    
    # Google Sheets API scope
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 service_account_path: Optional[str] = None,
                 credentials: Optional[object] = None):
        """
        Initialize Google Sheets parser.
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            service_account_path: Path to service account credentials JSON file
            credentials: Pre-authenticated credentials object
        """
        super().__init__()
        self.credentials_path = credentials_path
        self.service_account_path = service_account_path
        self.credentials = credentials
        self._service = None
    
    def detect_format(self, file_path: str) -> bool:
        """
        Detect if file is Google Sheets.
        
        Google Sheets can be identified by:
        - URL pattern (docs.google.com/spreadsheets)
        - File ID format
        - Or .gsheet extension (if exported)
        """
        # Check if it's a Google Sheets URL
        if 'docs.google.com/spreadsheets' in file_path.lower():
            return True
        
        # Check for file ID pattern (long alphanumeric string)
        if len(file_path) > 20 and file_path.replace('-', '').replace('_', '').isalnum():
            return True
        
        # Check extension (unlikely but possible)
        ext = os.path.splitext(file_path.lower())[1]
        return ext == '.gsheet'
    
    def _get_service(self):
        """Get authenticated Google Sheets service."""
        if self._service:
            return self._service
        
        if not HAS_GOOGLE_API:
            raise ValueError(
                "Google API client not available. "
                "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        
        # Use provided credentials if available
        if self.credentials:
            creds = self.credentials
        # Use service account if provided
        elif self.service_account_path and os.path.exists(self.service_account_path):
            creds = ServiceAccountCredentials.from_service_account_file(
                self.service_account_path, scopes=self.SCOPES
            )
        # Use OAuth credentials if provided
        elif self.credentials_path and os.path.exists(self.credentials_path):
            creds = Credentials.from_authorized_user_file(self.credentials_path, self.SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise ValueError("Invalid or expired credentials. Please re-authenticate.")
        else:
            raise ValueError(
                "Google Sheets credentials not configured. "
                "Provide credentials_path, service_account_path, or credentials object."
            )
        
        self._service = build('sheets', 'v4', credentials=creds)
        return self._service
    
    def _extract_sheet_id(self, file_path: str) -> str:
        """Extract Google Sheets ID from URL or file path."""
        # If it's a URL, extract the ID
        if 'docs.google.com/spreadsheets/d/' in file_path:
            # Format: https://docs.google.com/spreadsheets/d/{ID}/edit...
            parts = file_path.split('/d/')
            if len(parts) > 1:
                sheet_id = parts[1].split('/')[0].split('?')[0]
                return sheet_id
        
        # If it's just an ID, return as is
        if len(file_path) > 20 and file_path.replace('-', '').replace('_', '').isalnum():
            return file_path
        
        raise ValueError(f"Could not extract Google Sheets ID from: {file_path}")
    
    def parse(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
        """
        Parse Google Sheets file.
        
        Options:
            - sheet_name: Sheet name or index (default: 0, first sheet)
            - range: A1 notation range (e.g., 'A1:Z100' or 'Sheet1!A1:Z100')
            - header: Row number to use as header (default: 0)
            - value_render_option: 'FORMATTED_VALUE', 'UNFORMATTED_VALUE', or 'FORMULA' (default: 'UNFORMATTED_VALUE')
            - date_time_render_option: 'SERIAL_NUMBER' or 'FORMATTED_STRING' (default: 'SERIAL_NUMBER')
        """
        if options is None:
            options = {}
        
        sheet_id = self._extract_sheet_id(file_path)
        sheet_name = options.get('sheet_name', 0)
        range_name = options.get('range')
        header = options.get('header', 0)
        value_render_option = options.get('value_render_option', 'UNFORMATTED_VALUE')
        date_time_render_option = options.get('date_time_render_option', 'SERIAL_NUMBER')
        
        service = self._get_service()
        
        # Get sheet name if index provided
        if isinstance(sheet_name, int):
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            if sheet_name >= len(sheets):
                sheet_name = 0
            sheet_name = sheets[sheet_name]['properties']['title']
        
        # Build range
        if range_name:
            if '!' in range_name:
                # Range already includes sheet name
                a1_range = range_name
            else:
                a1_range = f"{sheet_name}!{range_name}"
        else:
            # Use entire sheet
            a1_range = sheet_name
        
        # Read data from sheet
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=a1_range,
                valueRenderOption=value_render_option,
                dateTimeRenderOption=date_time_render_option
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(values)
            
            # Set header if specified
            if header is not None and len(df) > header:
                df.columns = df.iloc[header]
                df = df.iloc[header + 1:].reset_index(drop=True)
            else:
                # No header row
                df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
            
            # Clean up empty rows
            df = df.replace('', pd.NA)
            df = df.dropna(how='all')
            
            return df
            
        except HttpError as error:
            raise ValueError(f"Error reading Google Sheets: {error}")
    
    def get_columns(self, file_path: str, options: Optional[Dict] = None) -> List[str]:
        """Get column names from Google Sheets file."""
        if options is None:
            options = {}
        
        # Use preview to detect columns
        preview_df = self.preview(file_path, rows=1, options=options)
        return list(preview_df.columns)
    
    def preview(self, file_path: str, rows: int = 10, options: Optional[Dict] = None) -> pd.DataFrame:
        """Preview first N rows of Google Sheets file."""
        if options is None:
            options = {}
        
        sheet_id = self._extract_sheet_id(file_path)
        sheet_name = options.get('sheet_name', 0)
        header = options.get('header', 0)
        
        service = self._get_service()
        
        # Get sheet name if index provided
        if isinstance(sheet_name, int):
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            if sheet_name >= len(sheets):
                sheet_name = 0
            sheet_name = sheets[sheet_name]['properties']['title']
        
        # Limit range to first N rows (accounting for header)
        start_row = header + 1 if header is not None else 1
        end_row = start_row + rows
        
        a1_range = f"{sheet_name}!A{start_row}:ZZ{end_row}"
        
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=a1_range
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(values)
            
            # Set header if specified
            if header is not None and len(df) > header:
                # Get header row from full sheet (first row)
                header_result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"{sheet_name}!1:1"
                ).execute()
                header_values = header_result.get('values', [])
                if header_values:
                    # Pad header to match data columns
                    max_cols = max(len(row) for row in values)
                    header_row = header_values[0] + [''] * (max_cols - len(header_values[0]))
                    df.columns = header_row[:len(df.columns)]
                    df = df.iloc[max(0, header - start_row + 1):].reset_index(drop=True)
                else:
                    df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
            else:
                df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
            
            # Clean up
            df = df.replace('', pd.NA)
            df = df.dropna(how='all')
            
            return df
            
        except HttpError as error:
            raise ValueError(f"Error reading Google Sheets: {error}")
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """Get list of sheet names in Google Sheets file."""
        sheet_id = self._extract_sheet_id(file_path)
        service = self._get_service()
        
        try:
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            return [sheet['properties']['title'] for sheet in sheets]
        except HttpError as error:
            raise ValueError(f"Error getting sheet names: {error}")

