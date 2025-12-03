--
-- Database Migration Script: Add Checkpoint/Restart Capability
-- 
-- Purpose: Add checkpoint configuration columns to DMS_MAPR table
--          for resumable ETL jobs
--
-- Date: 2025-11-14
-- Author: AI Assistant
--
-- Instructions:
-- 1. Review the changes
-- 2. Execute this script in the metadata schema
-- 3. Update mappings with checkpoint configuration
-- 4. Regenerate job flows
--

SET SERVEROUTPUT ON;

PROMPT ================================================================
PROMPT Adding Checkpoint Configuration to DMS_MAPR
PROMPT ================================================================
PROMPT

-- Add checkpoint columns to DMS_MAPR table
ALTER TABLE DMS_MAPR ADD (
    CHKPNTSTRTGY VARCHAR2(20) DEFAULT 'AUTO',
    -- Checkpoint strategy:
    -- 'AUTO'   - System determines best strategy
    -- 'KEY'    - Use source key column (recommended)
    -- 'PYTHON' - Python-side cursor skip (fallback)
    -- 'NONE'   - Disable checkpoint, always full reload
    
    CHKPNTCLNM VARCHAR2(100),
    -- Source column name for KEY strategy
    -- Should be sequential (ID, timestamp, etc.)
    -- Example: 'ORDER_ID', 'TRANSACTION_TIMESTAMP', 'CREATED_DATE'
    
    CHKPNTENBLD VARCHAR2(1) DEFAULT 'Y'
    -- Enable/disable checkpoint feature
    -- 'Y' = Enabled (resume on failure)
    -- 'N' = Disabled (always start fresh)
);

PROMPT Checkpoint columns added to DMS_MAPR successfully.
PROMPT

-- Add comments to document the columns
COMMENT ON COLUMN DMS_MAPR.CHKPNTSTRTGY IS 
'Checkpoint strategy: AUTO (auto-detect), KEY (use column), PYTHON (cursor skip), NONE (disabled)';

COMMENT ON COLUMN DMS_MAPR.CHKPNTCLNM IS 
'Source column for KEY strategy. Must be sequential/monotonic (e.g., ORDER_ID, TIMESTAMP)';

COMMENT ON COLUMN DMS_MAPR.CHKPNTENBLD IS 
'Enable checkpoint: Y (resume on failure), N (always full reload)';

PROMPT Column comments added.
PROMPT

-- Also add to DMS_JOB table for runtime use
ALTER TABLE DMS_JOB ADD (
    CHKPNTSTRTGY VARCHAR2(20),
    CHKPNTCLNM VARCHAR2(100),
    CHKPNTENBLD VARCHAR2(1)
);

PROMPT Checkpoint columns added to DMS_JOB successfully.
PROMPT

-- Verification
PROMPT ================================================================
PROMPT Verification Queries
PROMPT ================================================================
PROMPT

SELECT column_name, data_type, data_length, nullable, data_default
FROM user_tab_columns
WHERE table_name = 'DMS_MAPR' 
  AND column_name IN ('CHKPNTSTRTGY', 'CHKPNTCLNM', 'CHKPNTENBLD')
ORDER BY column_name;

PROMPT
PROMPT ================================================================
PROMPT Migration Complete!
PROMPT ================================================================
PROMPT
PROMPT Next Steps:
PROMPT 1. Configure checkpoint for your mappings:
PROMPT    UPDATE DMS_MAPR 
PROMPT    SET CHKPNTSTRTGY = 'KEY',
PROMPT        CHKPNTCLNM = 'YOUR_KEY_COLUMN'
PROMPT    WHERE MAPREF = 'YOUR_MAPPING';
PROMPT
PROMPT 2. Regenerate job flows:
PROMPT    - Call pkgdms_job.create_update_job for each mapping
PROMPT    - Or call pkgdms_job.create_all_jobs for all mappings
PROMPT
PROMPT 3. Test restart capability:
PROMPT    - Run a job
PROMPT    - Intentionally stop it mid-execution
PROMPT    - Restart - it should resume from checkpoint
PROMPT
PROMPT ================================================================
PROMPT

-- Example configuration for different scenarios
PROMPT Example Configurations:
PROMPT
PROMPT -- Fact table with transaction ID
PROMPT UPDATE DMS_MAPR 
PROMPT SET CHKPNTSTRTGY = 'KEY',
PROMPT     CHKPNTCLNM = 'TRANSACTION_ID',
PROMPT     CHKPNTENBLD = 'Y'
PROMPT WHERE MAPREF = 'SALES_FACT_LOAD';
PROMPT
PROMPT -- Dimension with timestamp
PROMPT UPDATE DMS_MAPR 
PROMPT SET CHKPNTSTRTGY = 'KEY',
PROMPT     CHKPNTCLNM = 'LAST_MODIFIED_DATE',
PROMPT     CHKPNTENBLD = 'Y'
PROMPT WHERE MAPREF = 'CUSTOMER_DIM_LOAD';
PROMPT
PROMPT -- Query without unique key (uses Python skip)
PROMPT UPDATE DMS_MAPR 
PROMPT SET CHKPNTSTRTGY = 'PYTHON',
PROMPT     CHKPNTCLNM = NULL,
PROMPT     CHKPNTENBLD = 'Y'
PROMPT WHERE MAPREF = 'COMPLEX_QUERY_LOAD';
PROMPT
PROMPT -- Disable checkpoint for small tables
PROMPT UPDATE DMS_MAPR 
PROMPT SET CHKPNTSTRTGY = 'NONE',
PROMPT     CHKPNTENBLD = 'N'
PROMPT WHERE MAPREF = 'LOOKUP_TABLE_LOAD';
PROMPT

COMMIT;

