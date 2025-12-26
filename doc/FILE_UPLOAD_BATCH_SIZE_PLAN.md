# File Upload Batch Size Configuration & Large File Handling Plan

## Overview
This document outlines the implementation plan for:
1. **Configurable Batch Size**: Allow users to set batch size per file upload configuration
2. **Large File Support**: Handle files with 100K, 1M, 10M, 100M+ records efficiently
3. **Memory Management**: Stream processing to avoid loading entire files into memory
4. **Database-Specific Optimization**: Optimal batch sizes per database type

---

## 1. Database Changes

### 1.1 Add `BATCH_SIZE` Column to `DMS_FLUPLD`

**Migration Script**: `doc/database_migration_file_upload_batch_size.sql`

```sql
-- PostgreSQL
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 1000;
COMMENT ON COLUMN dms_flupld.batch_size IS 'Number of rows to process per batch (default: 1000). Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';

-- Oracle
ALTER TABLE DMS_FLUPLD ADD (BATCH_SIZE NUMBER DEFAULT 1000);
COMMENT ON COLUMN DMS_FLUPLD.BATCH_SIZE IS 'Number of rows to process per batch (default: 1000). Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';
```

**Column Details:**
- **Name**: `batch_size` (or `btchsz` following DMS naming convention)
- **Type**: `INTEGER` (PostgreSQL) / `NUMBER` (Oracle)
- **Default**: `1000`
- **Range**: `100` to `100000` (validation in frontend/backend)
- **Purpose**: Number of rows to process in each batch during data loading

**Recommendations by Database:**
- **PostgreSQL**: 1000-5000 rows per batch
- **Oracle**: 100-1000 rows per batch (smaller due to array size limits)
- **MySQL**: 1000-5000 rows per batch
- **MS SQL Server**: 1000-5000 rows per batch
- **Sybase**: 500-2000 rows per batch

---

## 2. Backend Changes

### 2.1 Update `file_upload_service.py`

**Add `batch_size` parameter to `create_update_file_upload()`:**
```python
def create_update_file_upload(
    connection,
    flupldref: str,
    ...
    batch_size: Optional[int] = 1000,  # NEW
    ...
) -> int:
```

**Update INSERT/UPDATE statements** to include `batch_size` column.

### 2.2 Update `fastapi_file_upload.py`

**Add `batch_size` to `FileUploadConfig` model:**
```python
class FileUploadConfig(BaseModel):
    ...
    batch_size: Optional[int] = 1000  # NEW
```

**Update save endpoint** to accept and store `batch_size`.

### 2.3 Update `file_upload_executor.py`

**Modify `execute()` method:**
- Read `batch_size` from configuration
- Validate batch size (min: 100, max: 100000)
- Pass `batch_size` to `load_data()` instead of hardcoded 1000

**Add validation:**
```python
batch_size = config.get('batch_size', 1000)
if batch_size < 100:
    batch_size = 100
elif batch_size > 100000:
    batch_size = 100000
    warning(f"Batch size capped at 100000 for {flupldref}")
```

### 2.4 Update `data_loader.py`

**Modify `load_data()` to use provided batch_size:**
- Already accepts `batch_size` parameter, just ensure it's used correctly
- Consider database-specific limits (e.g., Oracle array size)

### 2.5 Large File Handling Strategy

**For files > 1M rows, implement streaming:**

1. **File Parsing**: Use chunked reading
   - CSV: `pd.read_csv(..., chunksize=batch_size)`
   - Excel: Read in chunks (pandas supports this)
   - JSON: Stream large JSON arrays
   - Parquet: Read row groups incrementally

2. **Memory Management**:
   - Process one batch at a time
   - Clear DataFrame after each batch
   - Use generators/iterators where possible

3. **Progress Tracking**:
   - Update progress after each batch
   - Log batch completion
   - Estimate remaining time

**Example Streaming Implementation:**
```python
def execute_with_streaming(self, flupldref, file_path, batch_size):
    # For large files, use chunked reading
    if file_size > 100MB or estimated_rows > 1000000:
        # Use chunked processing
        for chunk_df in pd.read_csv(file_path, chunksize=batch_size):
            # Transform chunk
            transformed_chunk = self._transform_data(chunk_df, column_mappings)
            # Load chunk
            load_data(..., dataframe=transformed_chunk, batch_size=batch_size)
            # Clear memory
            del transformed_chunk
    else:
        # Load entire file (existing logic)
        dataframe = self.parser_manager.parse_file(file_path)
        ...
```

---

## 3. Frontend Changes

### 3.1 Update `UploadForm.js`

**Add Batch Size field:**
- Location: In the header section, after "Truncate Before Load"
- Type: Number input with validation
- Default: 1000
- Range: 100 - 100000
- Helper text: "Number of rows to process per batch. Recommended: 1000-5000 for most databases, 100-1000 for Oracle."

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ File Upload Configuration                                    │
├─────────────────────────────────────────────────────────────┤
│ Reference: [___________]  Description: [_________________]  │
│ File: [Browse...] [filename.xlsx]                          │
│ Target DB: [Dropdown]  Schema: [____]  Table: [___________]   │
│ Truncate Before Load: [☑]  Batch Size: [1000]            │
│ Frequency: [Daily ▼]                                        │
│ Header Rows to Skip: [0]  Footer Rows to Skip: [0]        │
└─────────────────────────────────────────────────────────────┘
```

**Validation:**
- Min: 100
- Max: 100000
- Show warning if batch size > 10000 (may cause memory issues)
- Show info if batch size < 500 (may be slow for large files)

### 3.2 Update `UploadTable.js`

**Display batch size in table (optional):**
- Add "Batch Size" column if needed
- Or show in tooltip/details view

---

## 4. Implementation Steps

### Phase 1: Database Migration (Step 1)
1. Create migration script
2. Test on PostgreSQL and Oracle
3. Apply to database

### Phase 2: Backend Updates (Steps 2-5)
1. Update `file_upload_service.py` to handle `batch_size`
2. Update `fastapi_file_upload.py` models and endpoints
3. Update `file_upload_executor.py` to use configured batch size
4. Add validation and database-specific limits

### Phase 3: Frontend Updates (Step 6)
1. Add batch size input field to `UploadForm.js`
2. Add validation and helper text
3. Update save/load logic

### Phase 4: Large File Support (Future)
1. Implement streaming for CSV files
2. Implement streaming for Excel files
3. Implement streaming for JSON files
4. Add progress tracking
5. Add memory monitoring

---

## 5. Database-Specific Batch Size Recommendations

### PostgreSQL
- **Default**: 1000
- **Optimal Range**: 1000-5000
- **Large Files (1M+ rows)**: 2000-5000
- **Very Large Files (10M+ rows)**: 5000-10000 (with streaming)

### Oracle
- **Default**: 500
- **Optimal Range**: 100-1000
- **Large Files (1M+ rows)**: 500-1000
- **Note**: Oracle has array size limits, smaller batches recommended

### MySQL
- **Default**: 1000
- **Optimal Range**: 1000-5000
- **Large Files (1M+ rows)**: 2000-5000

### MS SQL Server
- **Default**: 1000
- **Optimal Range**: 1000-5000
- **Large Files (1M+ rows)**: 2000-5000

### Sybase
- **Default**: 500
- **Optimal Range**: 500-2000
- **Large Files (1M+ rows)**: 1000-2000

---

## 6. Large File Handling Strategy

### 6.1 File Size Thresholds

| File Size | Estimated Rows | Strategy |
|-----------|---------------|----------|
| < 10 MB | < 100K | Load entire file |
| 10-100 MB | 100K-1M | Load entire file, batch processing |
| 100 MB - 1 GB | 1M-10M | Streaming with chunked reading |
| > 1 GB | > 10M | Streaming with chunked reading + progress tracking |

### 6.2 Streaming Implementation

**For CSV Files:**
```python
def parse_csv_streaming(file_path, batch_size):
    for chunk in pd.read_csv(file_path, chunksize=batch_size):
        yield chunk
```

**For Excel Files:**
```python
def parse_excel_streaming(file_path, batch_size):
    # Excel doesn't support true streaming, but we can read in chunks
    total_rows = get_excel_row_count(file_path)
    for start_row in range(0, total_rows, batch_size):
        chunk = pd.read_excel(file_path, skiprows=start_row, nrows=batch_size)
        yield chunk
```

**For JSON Files:**
```python
def parse_json_streaming(file_path, batch_size):
    # For large JSON arrays, use ijson or similar
    import ijson
    items = ijson.items(open(file_path), 'item')
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield pd.DataFrame(batch)
            batch = []
    if batch:
        yield pd.DataFrame(batch)
```

**For Parquet Files:**
```python
def parse_parquet_streaming(file_path, batch_size):
    # Parquet supports row group reading
    parquet_file = pq.ParquetFile(file_path)
    for row_group in parquet_file.iter_row_groups():
        yield row_group.to_pandas()
```

### 6.3 Memory Management

1. **Process one batch at a time**
2. **Clear DataFrames after processing**
3. **Use generators to avoid loading entire file**
4. **Monitor memory usage** (optional, for very large files)

### 6.4 Progress Tracking

For large files, provide progress updates:
- Current batch number
- Total batches
- Rows processed
- Estimated time remaining
- Memory usage (optional)

---

## 7. Validation Rules

### Batch Size Validation

**Frontend:**
- Min: 100
- Max: 100000
- Default: 1000
- Warning if > 10000: "Large batch sizes may cause memory issues"
- Info if < 500: "Small batch sizes may be slow for large files"

**Backend:**
- Enforce min: 100
- Enforce max: 100000
- Database-specific limits:
  - Oracle: Cap at 1000 if > 1000
  - Others: Cap at 100000

---

## 8. Testing Plan

### Unit Tests
- Batch size validation
- Database-specific batch size limits
- Streaming file parsing

### Integration Tests
- Small files (< 100K rows) with various batch sizes
- Medium files (100K-1M rows) with various batch sizes
- Large files (1M-10M rows) with streaming
- Very large files (10M+ rows) with streaming

### Performance Tests
- Compare batch sizes: 100, 500, 1000, 5000, 10000
- Memory usage monitoring
- Execution time comparison

---

## 9. Migration Script

**File**: `doc/database_migration_file_upload_batch_size.sql`

```sql
-- ============================================================================
-- Migration: Add BATCH_SIZE column to DMS_FLUPLD table
-- Purpose: Allow users to configure batch size for file upload processing
-- Date: [Current Date]
-- ============================================================================

-- PostgreSQL
ALTER TABLE dms_flupld ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 1000;
COMMENT ON COLUMN dms_flupld.batch_size IS 'Number of rows to process per batch during data loading. Default: 1000. Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';

-- Oracle
ALTER TABLE DMS_FLUPLD ADD (BATCH_SIZE NUMBER DEFAULT 1000);
COMMENT ON COLUMN DMS_FLUPLD.BATCH_SIZE IS 'Number of rows to process per batch during data loading. Default: 1000. Recommended: 1000-5000 for most databases, 100-1000 for Oracle.';

-- Update existing records to have default batch size
-- PostgreSQL
UPDATE dms_flupld SET batch_size = 1000 WHERE batch_size IS NULL;

-- Oracle
UPDATE DMS_FLUPLD SET BATCH_SIZE = 1000 WHERE BATCH_SIZE IS NULL;
```

---

## 10. Future Enhancements (Parallel Processing)

### 10.1 Parallel Batch Processing

For very large files (10M+ rows), consider:
- **Multi-threaded batch processing**: Process multiple batches in parallel
- **Worker pool**: Use ThreadPoolExecutor or ProcessPoolExecutor
- **Database connection pooling**: Multiple connections for parallel inserts

### 10.2 Considerations

**Challenges:**
- Database connection limits
- Transaction management (parallel commits)
- Error handling across threads
- Progress tracking synchronization

**Benefits:**
- Faster processing for very large files
- Better resource utilization

**Implementation (Future):**
- Add `parallel_workers` configuration option
- Use ThreadPoolExecutor for parallel batch processing
- Implement connection pooling
- Add progress tracking with thread-safe counters

---

## Summary

1. **Add `batch_size` column** to `DMS_FLUPLD` table (default: 1000)
2. **Update backend** to read and use configured batch size
3. **Update frontend** to allow users to set batch size (100-100000)
4. **Implement streaming** for large files (> 1M rows)
5. **Add validation** and database-specific recommendations
6. **Future**: Parallel processing for very large files

This plan ensures:
- ✅ Users can configure batch size per upload
- ✅ Efficient processing of large files
- ✅ Memory-efficient streaming for very large files
- ✅ Database-specific optimizations
- ✅ Foundation for future parallel processing

