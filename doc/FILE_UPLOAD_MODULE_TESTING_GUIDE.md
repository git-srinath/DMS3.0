# File Upload Module - Testing Guide

## Prerequisites

1. **Database Setup**: Ensure PostgreSQL metadata database is running and tables are created
   - Run the SQL script: `doc/database_migration_file_upload_module.sql` (PostgreSQL section)
   - Verify tables exist: `dms_flupld` and `dms_fluplddtl`
   - Verify sequences exist: `dms_flupldseq` and `dms_fluplddtlseq`

2. **Backend Dependencies**: Ensure required Python packages are installed
   - pandas
   - openpyxl (for Excel files)
   - fastapi
   - uvicorn

3. **Environment Variables**: Check `.env` file has correct database connection settings

## Starting the Servers

### 1. Start Backend (FastAPI)

**Option A: Using the batch file (Windows)**
```bash
start_fastapi.bat
```

**Option B: Manual command**
```bash
cd backend
uvicorn backend.fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

**Verify Backend is Running:**
- Open browser: http://localhost:8000/health
- Should return: `{"status":"ok"}`
- Check API docs: http://localhost:8000/docs

### 2. Start Frontend (Next.js)

```bash
cd frontend
npm run dev
```

**Verify Frontend is Running:**
- Open browser: http://localhost:3000
- Should see the login page or home page

## Testing Checklist

### ✅ Backend API Endpoints

#### 1. Health Check
- **URL**: `GET http://localhost:8000/health`
- **Expected**: `{"status":"ok"}`

#### 2. Get All Uploads (Empty initially)
- **URL**: `GET http://localhost:8000/file-upload/get-all-uploads`
- **Headers**: `Authorization: Bearer <your_token>`
- **Expected**: `{"success": true, "data": []}`

#### 3. Get Connections
- **URL**: `GET http://localhost:8000/file-upload/get-connections`
- **Headers**: `Authorization: Bearer <your_token>`
- **Expected**: List of database connections from `DMS_DBCONDTLS`

#### 4. Upload File (Test with sample CSV)
- **URL**: `POST http://localhost:8000/file-upload/upload-file`
- **Method**: POST (multipart/form-data)
- **Body**: 
  - `file`: Select a CSV file (e.g., `test.csv` with headers)
  - `preview_rows`: 10 (optional)
- **Expected**: 
  ```json
  {
    "success": true,
    "message": "File uploaded and parsed successfully",
    "file_info": {...},
    "columns": ["col1", "col2", ...],
    "preview": [...]
  }
  ```

#### 5. Save Configuration
- **URL**: `POST http://localhost:8000/file-upload/save`
- **Headers**: `Authorization: Bearer <your_token>`, `Content-Type: application/json`
- **Body**:
  ```json
  {
    "formData": {
      "flupldref": "TEST_UPLOAD_001",
      "fluplddesc": "Test upload configuration",
      "flnm": "test.csv",
      "flpth": "/path/to/test.csv",
      "fltyp": "CSV",
      "trgconid": 1,
      "trgschm": "public",
      "trgtblnm": "TEST_TABLE",
      "trnctflg": "N",
      "stflg": "N",
      "crtdby": "testuser"
    },
    "columns": []
  }
  ```
- **Expected**: `{"success": true, "message": "File upload configuration saved successfully", "flupldid": "1"}`

#### 6. Get by Reference
- **URL**: `GET http://localhost:8000/file-upload/get-by-reference/TEST_UPLOAD_001`
- **Headers**: `Authorization: Bearer <your_token>`
- **Expected**: Configuration details

#### 7. Activate/Deactivate
- **URL**: `POST http://localhost:8000/file-upload/activate-deactivate`
- **Body**: 
  ```json
  {
    "flupldref": "TEST_UPLOAD_001",
    "stflg": "A"
  }
  ```
- **Expected**: Success message

#### 8. Delete
- **URL**: `POST http://localhost:8000/file-upload/delete`
- **Body**: 
  ```json
  {
    "flupldref": "TEST_UPLOAD_001"
  }
  ```
- **Expected**: Success message

### ✅ Frontend UI Testing

#### 1. Access the Module
- Login to the application
- Navigate to **File Upload** from:
  - Sidebar menu (if you have `file_upload` access key enabled)
  - Home page cards
- **URL**: http://localhost:3000/file_upload_module

#### 2. Upload Table View
- ✅ Should display empty table with message "No upload configurations found"
- ✅ "New Upload" button should be visible
- ✅ Search bar should be visible
- ✅ Should show table headers: Reference, Description, File Name, File Type, Target Table, Status, Last Run, Actions

#### 3. Create New Upload
- Click "New Upload" button
- Should navigate to form view
- Should show "Back to List" button
- Form should have basic fields (Reference, Description)

#### 4. Navigation
- Check sidebar has "File Upload" menu item
- Check home page has "File Upload" card
- Verify navigation works correctly

## Sample Test Files

### Create a test CSV file (`test.csv`):
```csv
id,name,email,age
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,25
3,Bob Johnson,bob@example.com,35
```

### Create a test Excel file (`test.xlsx`):
- Create Excel file with same data as CSV above

## Common Issues & Troubleshooting

### Issue: "Module not found" error
**Solution**: 
- Check if `backend/modules/file_upload/` directory exists
- Verify `__init__.py` files are present
- Restart the backend server

### Issue: "Table does not exist" error
**Solution**:
- Run the database migration script
- Verify you're connected to the correct database
- Check table names are lowercase: `dms_flupld`, `dms_fluplddtl`

### Issue: "Sequence does not exist" error
**Solution**:
- Verify sequences are created: `dms_flupldseq`, `dms_fluplddtlseq`
- Check ID provider configuration in `DMS_PARAMS`

### Issue: Frontend shows "No upload configurations found"
**Expected**: This is normal if no configurations are saved yet

### Issue: CORS errors
**Solution**:
- Verify backend CORS is configured for `http://localhost:3000`
- Check `fastapi_app.py` CORS settings

### Issue: Authentication errors
**Solution**:
- Ensure you're logged in
- Check token is valid
- Verify token is sent in Authorization header

## Testing with API Documentation

FastAPI provides interactive API documentation:

1. **Swagger UI**: http://localhost:8000/docs
   - Browse all endpoints
   - Test endpoints directly from browser
   - See request/response schemas

2. **ReDoc**: http://localhost:8000/redoc
   - Alternative API documentation

## Next Steps After Testing

Once basic functionality is verified:
1. Test file upload with different file types (CSV, Excel, JSON)
2. Test column mapping (when implemented)
3. Test data loading (when implemented)
4. Test scheduling (when implemented)

## Notes

- The file upload form is currently a placeholder
- Column mapping UI will be implemented in Phase 2
- Data loading functionality will be implemented in Phase 3
- File uploads are saved to `data/file_uploads/` directory

