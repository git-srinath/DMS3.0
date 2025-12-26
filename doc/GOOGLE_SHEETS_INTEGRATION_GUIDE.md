# Google Sheets Integration Guide

## Overview
This guide explains how to integrate Google Sheets as a data source for the File Upload Module, allowing users to directly fetch data from Google Sheets without downloading files.

## Authentication Methods

### Option 1: Service Account (Recommended for Server-to-Server)

**Best for:** Automated, server-side access to Google Sheets

**Steps:**
1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download JSON credentials file
5. Share Google Sheets with service account email

**Advantages:**
- No user interaction required
- Works for scheduled/automated uploads
- Secure server-to-server communication
- No token expiration issues

**Disadvantages:**
- Requires sharing each sheet with service account
- Cannot access user's personal sheets without sharing

### Option 2: OAuth2 (User Authentication)

**Best for:** Accessing user's personal Google Sheets

**Steps:**
1. Create OAuth2 credentials in Google Cloud Console
2. Implement OAuth2 flow in application
3. Store refresh tokens securely
4. Use access tokens for API calls

**Advantages:**
- Can access user's personal sheets
- User controls access permissions
- More flexible for end users

**Disadvantages:**
- Requires user authentication flow
- Token management complexity
- Tokens can expire

## Implementation

### Service Account Setup

1. **Create Service Account:**
   - Go to Google Cloud Console
   - Navigate to IAM & Admin > Service Accounts
   - Create new service account
   - Download JSON key file

2. **Enable APIs:**
   - Enable "Google Sheets API"
   - Enable "Google Drive API" (if needed)

3. **Share Sheets:**
   - Share Google Sheet with service account email (e.g., `your-service-account@project.iam.gserviceaccount.com`)
   - Grant "Viewer" or "Editor" permission as needed

### Configuration

```python
# Environment variables
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'credentials/service_account.json')
GOOGLE_SHEETS_AUTH_METHOD = os.getenv('GOOGLE_SHEETS_AUTH_METHOD', 'SERVICE_ACCOUNT')  # or 'OAUTH2'
```

### Database Schema Addition

For Google Sheets, we need to store additional metadata:

```sql
-- Add columns to DMS_FLUPLD for Google Sheets
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshtid VARCHAR(500);      -- Google Sheets spreadsheet ID
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshtnm VARCHAR(200);     -- Sheet/tab name
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshtrng VARCHAR(100);    -- Range (A1 notation)
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshturl VARCHAR(1000);   -- Full Google Sheets URL
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshtacct VARCHAR(200);   -- Service account email or OAuth user
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS gglshtrtm CHAR(1) DEFAULT 'N';  -- Real-time sync (Y/N)
```

## Usage Examples

### Example 1: Upload from Google Sheets URL

```
User provides: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
System extracts: Spreadsheet ID = 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
System fetches: All data from first sheet
```

### Example 2: Upload from Specific Sheet and Range

```
User provides:
- Spreadsheet ID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
- Sheet Name: "Sales Data"
- Range: A1:Z1000
System fetches: Only specified range from specified sheet
```

### Example 3: Real-time Sync

```
User configures:
- Google Sheets URL
- Real-time sync: Enabled
- Schedule: Daily at 9 AM
System: Fetches latest data from Google Sheets on each scheduled run
```

## Security Considerations

1. **Credentials Storage:**
   - Store service account JSON in secure location
   - Use environment variables or secret management
   - Never commit credentials to version control

2. **Access Control:**
   - Only share sheets with service account that need access
   - Use "Viewer" permission when possible (read-only)
   - Regularly audit shared sheets

3. **API Quotas:**
   - Google Sheets API has quotas (requests per minute)
   - Implement rate limiting
   - Cache data when possible

4. **Data Privacy:**
   - Ensure compliance with data privacy regulations
   - Log access to Google Sheets data
   - Implement data retention policies

## Error Handling

Common errors and solutions:

1. **403 Forbidden:**
   - Sheet not shared with service account
   - Solution: Share sheet with service account email

2. **404 Not Found:**
   - Invalid spreadsheet ID
   - Solution: Verify spreadsheet ID or URL

3. **429 Too Many Requests:**
   - API quota exceeded
   - Solution: Implement rate limiting, retry with backoff

4. **401 Unauthorized:**
   - Invalid credentials
   - Solution: Verify service account JSON file

## UI Considerations

### File Upload Dialog Enhancement

For Google Sheets, the upload dialog should have:

1. **Input Method Selection:**
   - Radio buttons: "Upload File" vs "Connect to Google Sheets"

2. **Google Sheets Input:**
   - Text field for Google Sheets URL
   - Or separate fields for Spreadsheet ID
   - Button to "Test Connection"

3. **Sheet Selection:**
   - Dropdown populated with available sheets
   - Refresh button to reload sheet list

4. **Range Selection (Optional):**
   - Text field for A1 notation range
   - Or visual range picker

5. **Authentication Status:**
   - Show current authentication method
   - Button to re-authenticate (for OAuth2)

## API Rate Limits

Google Sheets API quotas (typical):
- **Read requests:** 300 requests per minute per project
- **Write requests:** 60 requests per minute per project
- **Queries per day:** 1,000,000 queries per day

**Recommendations:**
- Cache sheet metadata (sheet names, structure)
- Batch data fetching when possible
- Implement exponential backoff for retries
- Monitor API usage

## Testing

### Test Cases

1. **Valid Google Sheets URL:**
   - Input: Valid Google Sheets URL
   - Expected: Successfully extracts spreadsheet ID and fetches data

2. **Invalid URL:**
   - Input: Invalid or non-existent URL
   - Expected: Clear error message

3. **Unshared Sheet:**
   - Input: Valid URL but sheet not shared with service account
   - Expected: Permission error with instructions

4. **Specific Sheet Selection:**
   - Input: Spreadsheet with multiple sheets, select specific sheet
   - Expected: Fetches data only from selected sheet

5. **Range Selection:**
   - Input: Valid range (e.g., A1:Z100)
   - Expected: Fetches only specified range

6. **Large Sheets:**
   - Input: Sheet with 100,000+ rows
   - Expected: Handles efficiently, shows progress

## Migration from File Upload

For users who currently download Google Sheets as Excel/CSV:

1. **Backward Compatibility:**
   - Still support file upload (downloaded Google Sheets)
   - Add option to switch to direct API access

2. **Migration Path:**
   - Detect if uploaded file is from Google Sheets (check metadata)
   - Suggest switching to direct API access
   - Provide one-click migration

## Future Enhancements

1. **Google Drive Integration:**
   - Browse and select files from Google Drive
   - Support for other Google Workspace files

2. **Real-time Updates:**
   - Webhook integration for real-time data changes
   - Push notifications when sheet is updated

3. **Multi-account Support:**
   - Support multiple Google accounts
   - Switch between accounts

4. **Sheet Templates:**
   - Pre-configured templates for common use cases
   - Auto-detect sheet structure

