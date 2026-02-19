# File Upload Strategy for Large Files

## Current Implementation Overview

### Architecture Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. User selects file
       │ 2. Entire file sent via FormData (axios.post)
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  upload_file endpoint        │  │
│  │  - await file.read()         │  │
│  │  - Loads ENTIRE file         │  │
│  │    into memory               │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │  FileParserManager           │  │
│  │  - parse_file()              │  │
│  │  - Reads ENTIRE file         │  │
│  │  - Creates pandas DataFrame  │  │
│  │    (entire file in memory)   │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │  Data Loader                 │  │
│  │  - load_data()              │  │
│  │  - Processes in BATCHES     │  │
│  │  - batch_size: 1000 rows    │  │
│  │  - Only DB insertion is      │  │
│  │    batched, not parsing      │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Current Strategy Details

### 1. Frontend Upload (UploadForm.js)

**Location**: `frontend/src/app/file_upload_module/UploadForm.js`

**Current Approach**:
```javascript
const formDataObj = new FormData()
formDataObj.append('file', selectedFile)
formDataObj.append('preview_rows', '10')

const response = await axios.post(
  `${API_BASE_URL}/file-upload/upload-file`, 
  formDataObj,
  {
    headers: {
      'Content-Type': 'multipart/form-data',
      Authorization: `Bearer ${token}`,
    },
  }
)
```

**Characteristics**:
- ✅ Simple and straightforward
- ❌ **Sends entire file in one request**
- ❌ **No chunking or streaming**
- ❌ **No progress tracking**
- ❌ **Memory intensive on client side**
- ❌ **Timeout risk for very large files**

**Limitations**:
- Maximum file size limited by:
  - Browser memory
  - HTTP request timeout
  - Network stability
- No resumable uploads
- No progress indication during upload

### 2. Backend File Reception (fastapi_file_upload.py)

**Location**: `backend/modules/file_upload/fastapi_file_upload.py`

**Current Approach**:
```python
@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    preview_rows: int = Query(10, ge=1, le=100)
):
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=UPLOAD_DIR) as temp_file:
        content = await file.read()  # ⚠️ Loads ENTIRE file into memory
        temp_file.write(content)
        temp_file_path = temp_file.name
```

**Characteristics**:
- ✅ Simple file handling
- ❌ **`await file.read()` loads entire file into RAM**
- ❌ **No streaming to disk**
- ❌ **Memory usage = file size**
- ❌ **Risk of OOM (Out of Memory) for large files**

**Memory Impact**:
- For a 1GB file: ~1GB RAM usage during upload
- For a 10GB file: ~10GB RAM usage (likely to fail)

### 3. File Parsing (file_parser.py)

**Location**: `backend/modules/file_upload/file_parser.py`

**Current Approach**:
```python
def parse_file(self, file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
    parser = self.get_parser(file_path)
    return parser.parse(file_path, options)  # Returns entire DataFrame
```

**Characteristics**:
- ✅ Uses pandas for robust parsing
- ❌ **Entire file parsed into single DataFrame**
- ❌ **Memory usage = 2-3x file size** (original file + DataFrame)
- ❌ **No chunked/streaming parsing**

**Memory Impact**:
- CSV: ~2x file size (file + DataFrame)
- Excel: ~3-4x file size (compressed file + uncompressed DataFrame)
- JSON: ~2-3x file size

### 4. Data Loading (data_loader.py)

**Location**: `backend/modules/file_upload/data_loader.py`

**Current Approach**:
```python
def load_data(
    connection,
    schema: str,
    table: str,
    dataframe: pd.DataFrame,  # ⚠️ Entire DataFrame in memory
    column_mappings: List[Dict[str, Any]],
    load_mode: str = LoadMode.INSERT,
    batch_size: int = 1000,  # ✅ Only DB insertion is batched
    username: Optional[str] = None
):
    # Process in batches
    total_rows = len(dataframe)
    num_batches = (total_rows + batch_size - 1) // batch_size
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_rows)
        batch_df = dataframe.iloc[start_idx:end_idx].copy()  # ✅ Slices DataFrame
        # Insert batch into database
```

**Characteristics**:
- ✅ **Database insertion is batched** (1000 rows default)
- ✅ Reduces database load
- ✅ Better transaction management
- ❌ **Entire DataFrame must be in memory first**
- ❌ **Parsing is NOT batched**

**Batch Size Configuration**:
- Default: 1000 rows
- Minimum: 100 rows
- Maximum: 100,000 rows (or 1,000 for Oracle)
- Configurable per upload configuration

## Current Limitations for Large Files

### Memory Bottlenecks

1. **Client Side**:
   - Entire file loaded into browser memory
   - FormData serialization overhead
   - Network buffer overhead

2. **Server Side - Upload**:
   - Entire file read into RAM: `await file.read()`
   - Temporary file write (disk I/O)

3. **Server Side - Parsing**:
   - Entire file parsed into pandas DataFrame
   - Memory usage: 2-4x file size depending on format

4. **Server Side - Processing**:
   - Entire DataFrame kept in memory during batch processing
   - Only database insertion is batched

### Performance Bottlenecks

1. **Upload Time**:
   - Single HTTP request (no parallelization)
   - No resumability (must restart on failure)
   - Network timeout risk

2. **Processing Time**:
   - Sequential parsing (entire file before processing)
   - No parallel processing
   - Blocking operations

### Scalability Limits

**Estimated Maximum File Sizes** (with 8GB server RAM):

| File Type | Estimated Max Size | Reason |
|-----------|-------------------|--------|
| CSV | ~2-3 GB | Memory = 2x file size |
| Excel | ~1-2 GB | Memory = 3-4x file size |
| JSON | ~2-3 GB | Memory = 2-3x file size |
| Parquet | ~3-4 GB | More efficient, but still limited |

**Note**: These are rough estimates. Actual limits depend on:
- Available server RAM
- Concurrent uploads
- Other system processes
- Database connection limits

## How Current System Handles Large Files

### What Works Well

1. **Batch Database Insertion**:
   - Reduces database load
   - Better transaction management
   - Configurable batch size

2. **Temporary File Storage**:
   - Files saved to disk before processing
   - Allows retry without re-upload

3. **Error Handling**:
   - Per-row error tracking
   - Continues processing on individual row failures

### What Doesn't Scale

1. **Memory-Intensive Operations**:
   - Entire file in memory during upload
   - Entire file in memory during parsing
   - Entire DataFrame in memory during processing

2. **No Streaming**:
   - Upload: No chunked upload
   - Parsing: No chunked parsing
   - Processing: No streaming to database

3. **No Progress Tracking**:
   - No upload progress
   - No processing progress
   - No resumability

## Recommended Improvements for Large Files

### 1. Chunked File Upload

**Implementation**:
- Split file into chunks (e.g., 5-10MB chunks)
- Upload chunks sequentially or in parallel
- Reassemble on server
- Track upload progress

**Benefits**:
- Resumable uploads
- Progress tracking
- Better error recovery
- Reduced memory usage

**Technology Options**:
- Custom chunked upload endpoint
- Use libraries like `tus` (resumable upload protocol)
- Use cloud storage direct upload (S3, Azure Blob)

### 2. Streaming File Parsing

**Implementation**:
- Parse file in chunks (e.g., 10,000 rows at a time)
- Process each chunk immediately
- Don't keep entire DataFrame in memory

**Benefits**:
- Constant memory usage
- Can handle files larger than RAM
- Faster time-to-first-row

**Technology Options**:
- `pandas.read_csv(chunksize=10000)`
- `polars` (more memory-efficient)
- Custom streaming parsers

### 3. Streaming Database Loading

**Implementation**:
- Process chunks as they're parsed
- Stream directly to database
- No intermediate DataFrame storage

**Benefits**:
- Lower memory footprint
- Faster overall processing
- Better resource utilization

### 4. Progress Tracking & Resumability

**Implementation**:
- Track upload progress (chunks uploaded)
- Track processing progress (rows processed)
- Store checkpoint state
- Allow resume from checkpoint

**Benefits**:
- Better user experience
- Recovery from failures
- Visibility into long-running operations

### 5. Asynchronous Processing

**Implementation**:
- Upload file → return immediately
- Process file in background job
- Notify user when complete

**Benefits**:
- No request timeout issues
- Better user experience
- Can handle very long processing times

## Recommended Architecture for Large Files

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ Chunked Upload (5-10MB chunks)
       │ Progress: 45% uploaded
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Chunked Upload Endpoint     │  │
│  │  - Receive chunks            │  │
│  │  - Write to disk (streaming) │  │
│  │  - Track progress            │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │  Background Job Queue         │  │
│  │  - Celery / RQ / etc.         │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │  Streaming Parser           │  │
│  │  - Read chunks (10K rows)  │  │
│  │  - Parse incrementally      │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │  Streaming Loader            │  │
│  │  - Process chunk             │  │
│  │  - Insert to DB (batched)   │  │
│  │  - Release memory           │  │
│  │  - Repeat for next chunk    │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Updated Implementation (Streaming + Background Processing)

### New Architecture

The system has been updated to use:
1. **Streaming File Processing**: Files are processed in chunks (10,000 rows) instead of loading entire file
2. **Background Job Execution**: Jobs are queued and executed by scheduler service, users don't wait
3. **Status Polling**: Frontend can poll for job status without blocking

### How It Works Now

```
User clicks "Execute"
    ↓
Request queued in DMS_PRCREQ
    ↓
Returns immediately with request_id
    ↓
User can continue working
    ↓
Scheduler picks up job
    ↓
StreamingFileExecutor processes file in chunks:
  - Read chunk (10K rows)
  - Transform chunk
  - Load chunk to DB
  - Release memory
  - Repeat until done
    ↓
Status updated in DMS_PRCREQ
    ↓
Frontend polls for status updates
```

### Benefits

- ✅ **No Memory Issues**: Only 10K rows in memory at a time
- ✅ **Non-Blocking**: Users don't wait on screen
- ✅ **Scalable**: Can handle files larger than RAM
- ✅ **Progress Tracking**: Status can be polled
- ✅ **Better UX**: Users can continue working

## Summary

### Current State (After Update)
- ✅ Streaming chunked processing (10K rows per chunk)
- ✅ Background job execution via scheduler
- ✅ Status polling endpoint
- ✅ Works for files of any size (limited by disk, not RAM)
- ✅ Non-blocking user experience

### Recommended Next Steps

1. **Short-term** (Quick wins):
   - Add file size validation/warning
   - Increase batch size for large files
   - Add progress indicators (even if approximate)

2. **Medium-term** (Significant improvement):
   - Implement chunked file upload
   - Implement streaming file parsing
   - Add background job processing

3. **Long-term** (Enterprise-grade):
   - Full resumable uploads
   - Distributed processing
   - Cloud storage integration
   - Real-time progress tracking

## Configuration Recommendations

For current system with large files:

1. **Increase Batch Size**:
   ```python
   # In file_upload_executor.py
   batch_size = min(config.get('batch_size', 1000), 10000)  # Up to 10K
   ```

2. **Add Memory Monitoring**:
   - Monitor server memory during uploads
   - Set file size limits based on available RAM
   - Warn users about large files

3. **Optimize Parsing**:
   - Use `pandas.read_csv(chunksize=10000)` for CSV
   - Consider `polars` for better memory efficiency
   - Use appropriate data types to reduce memory

4. **Database Optimization**:
   - Use bulk insert operations
   - Consider COPY/LOAD commands for very large files
   - Optimize connection pooling

