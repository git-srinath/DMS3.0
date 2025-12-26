# File Upload Module - File-First Workflow with Auto-Fill Design

## Overview

Redesign the file upload form to start with file specification, with intelligent auto-fill capabilities to minimize manual data entry.

---

## Current Flow vs Proposed Flow

### **Current Flow** ❌
1. User fills form fields (Reference, Description, etc.)
2. User clicks "Upload File & Preview" button
3. Dialog opens for file selection
4. File is uploaded and parsed
5. Columns are auto-detected
6. User maps columns manually

### **Proposed Flow** ✅
1. **User specifies file first** (text box + browse button)
2. **User clicks "Prefill Details" button**
3. System uploads/parses file automatically
4. **System auto-fills:**
   - File Reference (from filename)
   - File Name
   - File Type
   - Target Table (suggested from filename)
   - Description (suggested)
   - Columns (auto-detected)
5. User reviews and adjusts auto-filled values
6. User completes remaining fields (Connection, Frequency, etc.)

---

## Design Specifications

### **1. File Specification Section (First Section)**

```
┌─────────────────────────────────────────────────────────────────┐
│ File Specification                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  File Path/Name: [________________________] [Browse] [Prefill]  │
│                                                                   │
│  ℹ️ Enter file path or select file to auto-fill form details    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Text Field**: For file path/name input
- **Browse Button**: Opens file picker
- **Prefill Button**: Uploads file and auto-fills all possible fields

**Behavior:**
- User can type file path OR click Browse to select
- After file selection, "Prefill" button becomes enabled
- Clicking "Prefill" triggers upload and auto-fill process

---

### **2. Auto-Fill Logic**

#### **A. File Reference Generation**
```javascript
// Algorithm
function generateFileReference(filename) {
  // Remove extension
  let ref = filename.replace(/\.[^/.]+$/, '');
  
  // Convert to uppercase
  ref = ref.toUpperCase();
  
  // Replace spaces and special chars with underscores
  ref = ref.replace(/[^A-Z0-9_]/g, '_');
  
  // Remove multiple consecutive underscores
  ref = ref.replace(/_+/g, '_');
  
  // Remove leading/trailing underscores
  ref = ref.replace(/^_+|_+$/g, '');
  
  // Limit length (e.g., 50 chars)
  ref = ref.substring(0, 50);
  
  return ref;
}

// Examples:
// "customer_data.csv" → "CUSTOMER_DATA"
// "Sales Report 2024.xlsx" → "SALES_REPORT_2024"
// "user-info.json" → "USER_INFO"
// "product.inventory.parquet" → "PRODUCT_INVENTORY"
```

#### **B. Target Table Name Suggestion**
```javascript
// Algorithm
function suggestTableName(filename) {
  // Use same logic as file reference, but can be customized
  let tableName = generateFileReference(filename);
  
  // Optional: Add prefix/suffix based on configuration
  // e.g., "STG_" + tableName for staging tables
  
  return tableName;
}

// Examples:
// "customer_data.csv" → "CUSTOMER_DATA"
// "monthly_sales.xlsx" → "MONTHLY_SALES"
```

#### **C. Description Suggestion**
```javascript
// Algorithm
function suggestDescription(filename, fileInfo) {
  // Start with filename (human-readable)
  let desc = filename.replace(/\.[^/.]+$/, '');
  
  // Add file type info
  desc += ` (${fileInfo.file_type} file)`;
  
  // Add row count if available
  if (fileInfo.row_count) {
    desc += ` - ${fileInfo.row_count.toLocaleString()} rows`;
  }
  
  // Add column count if available
  if (fileInfo.column_count) {
    desc += `, ${fileInfo.column_count} columns`;
  }
  
  return desc;
}

// Examples:
// "customer_data.csv" → "customer_data (CSV file) - 1,234 rows, 15 columns"
// "sales_report.xlsx" → "sales_report (XLSX file) - 5,678 rows, 20 columns"
```

#### **D. Schema Suggestion (Optional)**
```javascript
// Could suggest schema based on:
// 1. Connection default schema
// 2. File reference pattern (e.g., STG_* → staging schema)
// 3. User's recent selections
```

---

### **3. Form Layout (After Auto-Fill)**

```
┌─────────────────────────────────────────────────────────────────┐
│ File Specification                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ File: [customer_data.csv________________] [Browse] [Prefill]│ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ✅ File uploaded successfully. Details pre-filled below.         │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Configuration                                                    │
│                                                                   │
│  Reference:     [CUSTOMER_DATA________]  (auto-filled)          │
│  Description:   [customer_data (CSV file) - 1,234 rows...]      │
│  Target Conn:   [Select Connection ▼]                           │
│  Target Table:  [CUSTOMER_DATA________]  (auto-filled)           │
│  Frequency:     [Daily (DL) ▼]                                  │
│  Truncate:      [☑ Truncate before load]                        │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Column Mapping                                                   │
│                                                                   │
│  ✅ 15 columns detected from file                                │
│  [Column Mapping Table with auto-mapped columns]                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### **Frontend Changes**

#### **1. Reorder Form Sections**
```javascript
// UploadForm.js - New structure
<Box>
  {/* Section 1: File Specification (FIRST) */}
  <FileSpecificationSection
    filePath={filePath}
    onFileSelect={handleFileSelect}
    onPrefill={handlePrefill}
    fileInfo={fileInfo}
  />
  
  {/* Section 2: Configuration (auto-filled) */}
  <ConfigurationSection
    formData={formData}
    onInputChange={handleInputChange}
    connections={connections}
    autoFilledFields={autoFilledFields}
  />
  
  {/* Section 3: Column Mapping */}
  <ColumnMappingSection
    columns={columns}
    mappings={columnMappings}
    onMappingChange={handleMappingChange}
  />
</Box>
```

#### **2. File Specification Component**
```javascript
const FileSpecificationSection = ({ filePath, onFileSelect, onPrefill, fileInfo, loading }) => {
  const [localFilePath, setLocalFilePath] = useState(filePath || '');
  const fileInputRef = useRef(null);
  
  const handleBrowse = () => {
    fileInputRef.current?.click();
  };
  
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setLocalFilePath(file.name);
      onFileSelect(file);
    }
  };
  
  const handlePrefillClick = async () => {
    if (!localFilePath && !fileInputRef.current?.files?.[0]) {
      message.warning('Please select a file first');
      return;
    }
    await onPrefill();
  };
  
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        File Specification
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
        <TextField
          fullWidth
          label="File Path/Name"
          value={localFilePath}
          onChange={(e) => setLocalFilePath(e.target.value)}
          placeholder="Enter file path or click Browse to select"
          helperText="Specify the file to upload. Click 'Prefill Details' to auto-fill form."
        />
        
        <Button
          variant="outlined"
          onClick={handleBrowse}
          startIcon={<CloudUploadIcon />}
        >
          Browse
        </Button>
        
        <input
          ref={fileInputRef}
          type="file"
          hidden
          onChange={handleFileChange}
          accept=".csv,.xlsx,.xls,.json,.parquet,.parq"
        />
        
        <Button
          variant="contained"
          onClick={handlePrefillClick}
          disabled={loading || !localFilePath}
          startIcon={loading ? <CircularProgress size={16} /> : <AutoAwesomeIcon />}
        >
          {loading ? 'Prefilling...' : 'Prefill Details'}
        </Button>
      </Box>
      
      {fileInfo && (
        <Box sx={{ mt: 2, p: 1.5, bgcolor: 'success.light', borderRadius: 1 }}>
          <Typography variant="body2" color="success.dark">
            ✅ File uploaded: {fileInfo.original_filename} ({fileInfo.file_type})
            {fileInfo.row_count && ` - ${fileInfo.row_count.toLocaleString()} rows`}
            {fileInfo.column_count && `, ${fileInfo.column_count} columns`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};
```

#### **3. Auto-Fill Handler**
```javascript
const handlePrefill = async () => {
  const file = fileInputRef.current?.files?.[0];
  if (!file) {
    message.error('Please select a file first');
    return;
  }
  
  setPrefilling(true);
  try {
    // Upload and parse file
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('preview_rows', '10');
    
    const response = await axios.post(
      `${API_BASE_URL}/file-upload/upload-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
      }
    );
    
    if (response.data?.success) {
      const data = response.data;
      const fileInfo = data.file_info;
      const filename = fileInfo.original_filename || file.name;
      
      // Auto-fill logic
      const autoFilled = {
        // File Reference: from filename (uppercase, no extension)
        flupldref: generateFileReference(filename),
        
        // File Name
        flnm: filename,
        
        // File Type
        fltyp: fileInfo.file_type || detectFileType(filename),
        
        // File Path
        flpth: fileInfo.saved_path,
        
        // Target Table: suggested from filename
        trgtblnm: suggestTableName(filename),
        
        // Description: suggested with file info
        fluplddesc: suggestDescription(filename, fileInfo),
        
        // Columns: auto-detected
        columns: data.columns || [],
        
        // Preview: for display
        preview: data.preview || [],
      };
      
      // Update form data
      setFormData(prev => ({
        ...prev,
        ...autoFilled,
      }));
      
      // Set columns and preview
      setColumns(autoFilled.columns);
      setPreview(autoFilled.preview);
      setFileInfo(fileInfo);
      
      // Auto-create column mappings
      const detectedColumns = (autoFilled.columns || []).map((c, idx) => ({
        id: createRowId(),
        srcclnm: c,
        trgclnm: c.toUpperCase().replace(/[^A-Z0-9_]/g, '_'), // Clean column name
        excseq: idx + 1,
        trgkyflg: 'N',
        isrqrd: 'N',
      }));
      setColumnMappings(detectedColumns);
      
      // Mark which fields were auto-filled
      setAutoFilledFields({
        flupldref: true,
        flnm: true,
        fltyp: true,
        flpth: true,
        trgtblnm: true,
        fluplddesc: true,
      });
      
      message.success('Form details pre-filled successfully. Please review and adjust as needed.');
    }
  } catch (error) {
    console.error('Prefill error:', error);
    const serverMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      'Failed to prefill details';
    message.error(serverMessage);
  } finally {
    setPrefilling(false);
  }
};
```

#### **4. Helper Functions**
```javascript
// Generate file reference from filename
const generateFileReference = (filename) => {
  if (!filename) return '';
  
  // Remove extension
  let ref = filename.replace(/\.[^/.]+$/, '');
  
  // Convert to uppercase
  ref = ref.toUpperCase();
  
  // Replace spaces and special chars with underscores
  ref = ref.replace(/[^A-Z0-9_]/g, '_');
  
  // Remove multiple consecutive underscores
  ref = ref.replace(/_+/g, '_');
  
  // Remove leading/trailing underscores
  ref = ref.replace(/^_+|_+$/g, '');
  
  // Limit length
  ref = ref.substring(0, 50);
  
  return ref || 'FILE_UPLOAD';
};

// Suggest table name
const suggestTableName = (filename) => {
  return generateFileReference(filename);
};

// Suggest description
const suggestDescription = (filename, fileInfo) => {
  let desc = filename.replace(/\.[^/.]+$/, '');
  
  if (fileInfo?.file_type) {
    desc += ` (${fileInfo.file_type} file)`;
  }
  
  if (fileInfo?.row_count) {
    desc += ` - ${fileInfo.row_count.toLocaleString()} rows`;
  }
  
  if (fileInfo?.column_count) {
    desc += `, ${fileInfo.column_count} columns`;
  }
  
  return desc;
};

// Detect file type from extension
const detectFileType = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const typeMap = {
    'csv': 'CSV',
    'tsv': 'TSV',
    'txt': 'CSV',
    'xlsx': 'XLSX',
    'xls': 'XLS',
    'json': 'JSON',
    'xml': 'XML',
    'parquet': 'PARQUET',
    'parq': 'PARQUET',
  };
  return typeMap[ext] || 'UNKNOWN';
};
```

#### **5. Visual Indicators for Auto-Filled Fields**
```javascript
// Show indicator for auto-filled fields
<TextField
  fullWidth
  label="Reference"
  value={formData.flupldref}
  onChange={(e) => handleInputChange('flupldref', e.target.value)}
  InputProps={{
    endAdornment: autoFilledFields.flupldref && (
      <InputAdornment position="end">
        <Tooltip title="Auto-filled from filename">
          <CheckCircleIcon color="success" fontSize="small" />
        </Tooltip>
      </InputAdornment>
    ),
  }}
  helperText={autoFilledFields.flupldref ? 'Auto-filled from filename' : ''}
/>
```

---

## Backend Changes (Minimal)

### **No Backend Changes Required** ✅

The existing `/file-upload/upload-file` endpoint already returns:
- `file_info` with all necessary metadata
- `columns` list
- `preview` data

All auto-fill logic can be handled on the frontend using the existing API response.

---

## User Experience Flow

### **Step-by-Step**

1. **User opens "New Upload" form**
   - Form shows empty state
   - File Specification section is at the top

2. **User selects file**
   - Option A: Types file path in text box
   - Option B: Clicks "Browse" and selects file
   - File name appears in text box

3. **User clicks "Prefill Details"**
   - Button shows loading state
   - File is uploaded to server
   - Server parses file and returns metadata

4. **System auto-fills form**
   - ✅ Reference: `CUSTOMER_DATA` (from "customer_data.csv")
   - ✅ File Name: `customer_data.csv`
   - ✅ File Type: `CSV`
   - ✅ Target Table: `CUSTOMER_DATA`
   - ✅ Description: `customer_data (CSV file) - 1,234 rows, 15 columns`
   - ✅ Columns: Auto-detected and mapped

5. **User reviews and adjusts**
   - User can modify any auto-filled value
   - Visual indicators show which fields were auto-filled
   - User completes remaining fields (Connection, Frequency, etc.)

6. **User saves configuration**
   - Standard save process continues

---

## Benefits

### ✅ **Reduced Data Entry**
- **Before**: User manually enters 5-7 fields
- **After**: User only needs to adjust 1-2 fields typically

### ✅ **Fewer Errors**
- Auto-generated references follow consistent naming
- File type detection is automatic
- Column detection is automatic

### ✅ **Better UX**
- File-first approach is more intuitive
- Users see immediate feedback
- Clear visual indicators for auto-filled fields

### ✅ **Faster Workflow**
- One-click prefill vs multiple manual entries
- Less time spent on repetitive data entry

---

## Edge Cases & Considerations

### **1. Duplicate References**
```javascript
// Check if reference already exists
const checkReferenceExists = async (reference) => {
  // Call API to check
  // If exists, suggest alternative: CUSTOMER_DATA_001
};
```

### **2. Invalid File Names**
```javascript
// Handle special characters, very long names, etc.
// Fallback to generic reference if needed
```

### **3. File Already Uploaded**
```javascript
// If editing existing upload, prefill from saved data
// Don't re-upload file unnecessarily
```

### **4. Column Name Cleaning**
```javascript
// Clean column names for database compatibility
// e.g., "Customer Name" → "CUSTOMER_NAME"
// e.g., "Email Address" → "EMAIL_ADDRESS"
```

### **5. Target Table Validation**
```javascript
// Check if table already exists
// Suggest alternative if needed
// Validate table name format
```

---

## Implementation Checklist

### **Frontend**
- [ ] Create `FileSpecificationSection` component
- [ ] Add auto-fill helper functions
- [ ] Implement `handlePrefill` function
- [ ] Add visual indicators for auto-filled fields
- [ ] Update form layout (file section first)
- [ ] Add loading states for prefill operation
- [ ] Handle error cases gracefully
- [ ] Add validation for file selection

### **Testing**
- [ ] Test with various file types (CSV, Excel, JSON, Parquet)
- [ ] Test with different filename formats
- [ ] Test with special characters in filenames
- [ ] Test with very long filenames
- [ ] Test duplicate reference handling
- [ ] Test error scenarios (invalid file, network errors)

---

## Estimated Implementation Time

| Task | Time |
|------|------|
| File Specification Component | 2-3 hours |
| Auto-Fill Logic Functions | 2-3 hours |
| Form Reordering & Integration | 2-3 hours |
| Visual Indicators | 1-2 hours |
| Testing & Refinement | 2-3 hours |
| **TOTAL** | **9-14 hours** |

---

## Alternative: Enhanced Backend Support

### **Optional: New Endpoint for Auto-Fill**

If we want more sophisticated auto-fill logic on the backend:

```python
@router.post("/upload-file-and-suggest")
async def upload_file_and_suggest(
    file: UploadFile = File(...),
    preview_rows: int = Query(10, ge=1, le=100)
):
    """
    Upload file and return suggestions for form fields.
    """
    # Upload and parse file (existing logic)
    # ...
    
    # Generate suggestions
    filename = file.filename
    suggestions = {
        "file_reference": generate_file_reference(filename),
        "target_table": suggest_table_name(filename),
        "description": suggest_description(filename, file_info),
        "suggested_schema": get_default_schema(connection_id),
    }
    
    return {
        "success": True,
        "file_info": file_info,
        "columns": columns,
        "preview": preview,
        "suggestions": suggestions  # NEW
    }
```

**Benefits:**
- Centralized logic
- Can use database context for better suggestions
- Can check for duplicates server-side

**Trade-off:**
- Requires backend changes
- More complex implementation

---

## Recommendation

**Start with Frontend-Only Implementation** ✅

- Faster to implement
- No backend changes needed
- Can enhance later with backend support if needed
- Meets all requirements

**Future Enhancement:**
- Add backend endpoint for more sophisticated suggestions
- Use database context for better table name suggestions
- Check for duplicate references server-side

---

## Conclusion

This design provides:
1. ✅ File-first workflow (more intuitive)
2. ✅ Intelligent auto-fill (reduces data entry)
3. ✅ Clear visual feedback (user knows what was auto-filled)
4. ✅ Flexible (user can override any auto-filled value)
5. ✅ Minimal implementation effort (frontend-only initially)

**Ready for implementation when approved!** 🚀

