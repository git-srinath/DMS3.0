# Scheduler Status Queries

This document shows the exact SQL queries used by the `/job/scheduler-status` endpoint to retrieve file upload job counts.

## Main Status Query

The endpoint uses one of these queries depending on the database type and column naming:

### PostgreSQL (with uppercase quoted identifiers):
```sql
SELECT 
    UPPER("REQUEST_TYPE") as request_type,
    UPPER("STATUS") as status,
    COUNT(*) as count
FROM {table_name}
WHERE UPPER("STATUS") IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED')
GROUP BY UPPER("REQUEST_TYPE"), UPPER("STATUS")
ORDER BY UPPER("REQUEST_TYPE"), UPPER("STATUS")
```

### PostgreSQL (with lowercase identifiers - fallback):
```sql
SELECT 
    UPPER(request_type) as request_type,
    UPPER(status) as status,
    COUNT(*) as count
FROM {table_name}
WHERE UPPER(status) IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED')
GROUP BY UPPER(request_type), UPPER(status)
ORDER BY UPPER(request_type), UPPER(status)
```

### Oracle:
```sql
SELECT 
    UPPER(request_type) as request_type,
    UPPER(status) as status,
    COUNT(*) as count
FROM {table_name}
WHERE UPPER(status) IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED')
GROUP BY UPPER(request_type), UPPER(status)
ORDER BY UPPER(request_type), UPPER(status)
```

## Recent Activity Query

### PostgreSQL (with uppercase quoted identifiers):
```sql
SELECT 
    "REQUEST_ID" as request_id,
    "MAPREF" as mapref,
    "REQUEST_TYPE" as request_type,
    "STATUS" as status,
    "REQUESTED_AT" as requested_at
FROM {table_name}
WHERE UPPER("STATUS") IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED', 'DONE', 'FAILED')
ORDER BY "REQUESTED_AT" DESC
LIMIT 10
```

### PostgreSQL (with lowercase identifiers - fallback):
```sql
SELECT 
    request_id,
    mapref,
    request_type,
    status,
    requested_at
FROM {table_name}
WHERE UPPER(status) IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED', 'DONE', 'FAILED')
ORDER BY requested_at DESC
LIMIT 10
```

### Oracle:
```sql
SELECT 
    request_id,
    mapref,
    request_type,
    status,
    requested_at
FROM (
    SELECT 
        request_id,
        mapref,
        request_type,
        status,
        requested_at
    FROM {table_name}
    WHERE UPPER(status) IN ('NEW', 'QUEUED', 'PROCESSING', 'CLAIMED', 'DONE', 'FAILED')
    ORDER BY requested_at DESC
)
WHERE ROWNUM <= 10
```

## Diagnostic Queries (Added for Debugging)

### All Jobs by Type and Status:
```sql
SELECT request_type, status, COUNT(*) as count
FROM {table_name}
GROUP BY request_type, status
ORDER BY request_type, status
```

### Last 5 FILE_UPLOAD Jobs:
```sql
SELECT request_id, mapref, request_type, status, requested_at
FROM {table_name}
WHERE UPPER(request_type) = 'FILE_UPLOAD'
ORDER BY requested_at DESC
LIMIT 5
```

## How the Data is Processed

1. The query returns rows with: `request_type`, `status`, `count`
2. Each row is processed:
   - `request_type` is converted to uppercase and stripped
   - `status` is converted to uppercase and stripped
   - `count` is converted to integer
3. The counts are accumulated into a `job_counts` dictionary:
   ```python
   job_counts = {
       'FILE_UPLOAD': {'NEW': 0, 'QUEUED': 0, 'PROCESSING': 0, 'CLAIMED': 0, 'total': 0},
       'REPORT': {...},
       ...
   }
   ```
4. The final response includes:
   ```json
   {
       "job_counts": {
           "file_uploads": {
               "active": <total of NEW+QUEUED+PROCESSING+CLAIMED>,
               "new": <NEW count>,
               "queued": <QUEUED count>,
               "processing": <PROCESSING + CLAIMED count>
           }
       }
   }
   ```

## Debugging

Check the backend logs for:
- `[scheduler-status]` - All debug messages from this endpoint
- `DIAGNOSTIC: All jobs in DMS_PRCREQ` - Shows all jobs regardless of status
- `DIAGNOSTIC: Last 5 FILE_UPLOAD jobs` - Shows recent file upload jobs
- `Status query returned X rows` - Number of rows returned by the main query
- `All status rows (raw)` - Raw database results
- `Processing: req_type=..., status=..., count=...` - Each row being processed

## Common Issues

1. **No jobs found**: Check if jobs exist in DMS_PRCREQ table with `request_type = 'FILE_UPLOAD'`
2. **Wrong status**: Jobs might be in 'DONE' or 'FAILED' status, which are excluded from active counts
3. **Case sensitivity**: The query uses UPPER() to handle case, but verify the actual data in the table
4. **Table name**: Verify `{table_name}` resolves to the correct table (check logs for actual table name)
