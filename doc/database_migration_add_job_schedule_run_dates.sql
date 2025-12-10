-- ============================================================================
-- Database Migration: Add Last Run and Next Run Date Columns to DMS_JOBSCH
-- ============================================================================
-- Purpose: Add LST_RUN_DT and NXT_RUN_DT columns to track job execution history
--          and calculate next scheduled run times
-- 
-- Date: 2025-01-XX
-- Version: 1.0
-- ============================================================================

SET SERVEROUTPUT ON;

-- ============================================================================
-- ORACLE VERSION
-- ============================================================================

-- Check if running on Oracle
DECLARE
    v_db_version VARCHAR2(100);
    v_count      NUMBER;
BEGIN
    -- Detect database type
    SELECT BANNER INTO v_db_version FROM V$VERSION WHERE ROWNUM = 1;
    
    IF UPPER(v_db_version) LIKE '%ORACLE%' THEN
        DBMS_OUTPUT.PUT_LINE('=================================================================');
        DBMS_OUTPUT.PUT_LINE('Oracle Database Detected');
        DBMS_OUTPUT.PUT_LINE('Adding LST_RUN_DT and NXT_RUN_DT columns to DMS_JOBSCH');
        DBMS_OUTPUT.PUT_LINE('=================================================================');
        DBMS_OUTPUT.PUT_LINE('');
        
        -- Check if LST_RUN_DT column exists
        SELECT COUNT(*)
        INTO v_count
        FROM user_tab_columns
        WHERE table_name = 'DMS_JOBSCH'
          AND column_name = 'LST_RUN_DT';
        
        IF v_count = 0 THEN
            -- Add LST_RUN_DT column
            EXECUTE IMMEDIATE 'ALTER TABLE DMS_JOBSCH ADD (LST_RUN_DT TIMESTAMP(6))';
            DBMS_OUTPUT.PUT_LINE('[OK] Added LST_RUN_DT column to DMS_JOBSCH');
        ELSE
            DBMS_OUTPUT.PUT_LINE('[SKIP] LST_RUN_DT column already exists in DMS_JOBSCH');
        END IF;
        
        -- Check if NXT_RUN_DT column exists
        SELECT COUNT(*)
        INTO v_count
        FROM user_tab_columns
        WHERE table_name = 'DMS_JOBSCH'
          AND column_name = 'NXT_RUN_DT';
        
        IF v_count = 0 THEN
            -- Add NXT_RUN_DT column
            EXECUTE IMMEDIATE 'ALTER TABLE DMS_JOBSCH ADD (NXT_RUN_DT TIMESTAMP(6))';
            DBMS_OUTPUT.PUT_LINE('[OK] Added NXT_RUN_DT column to DMS_JOBSCH');
        ELSE
            DBMS_OUTPUT.PUT_LINE('[SKIP] NXT_RUN_DT column already exists in DMS_JOBSCH');
        END IF;
        
        -- Add comments
        BEGIN
            EXECUTE IMMEDIATE 'COMMENT ON COLUMN DMS_JOBSCH.LST_RUN_DT IS ''Last execution date and time for this scheduled job''';
            EXECUTE IMMEDIATE 'COMMENT ON COLUMN DMS_JOBSCH.NXT_RUN_DT IS ''Next scheduled execution date and time for this job''';
            DBMS_OUTPUT.PUT_LINE('[OK] Added column comments');
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('[WARN] Could not add comments: ' || SQLERRM);
        END;
        
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('=================================================================');
        DBMS_OUTPUT.PUT_LINE('Migration completed successfully!');
        DBMS_OUTPUT.PUT_LINE('=================================================================');
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('Next Steps:');
        DBMS_OUTPUT.PUT_LINE('  1. Restart the backend application');
        DBMS_OUTPUT.PUT_LINE('  2. The scheduler service will automatically calculate and');
        DBMS_OUTPUT.PUT_LINE('     update NXT_RUN_DT when schedules are created/updated');
        DBMS_OUTPUT.PUT_LINE('  3. LST_RUN_DT will be updated automatically when jobs execute');
        DBMS_OUTPUT.PUT_LINE('');
        
        COMMIT;
    ELSE
        DBMS_OUTPUT.PUT_LINE('[ERROR] This script is for Oracle databases only');
        DBMS_OUTPUT.PUT_LINE('        For PostgreSQL, use the PostgreSQL section below');
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('[ERROR] Migration failed: ' || SQLERRM);
        ROLLBACK;
        RAISE;
END;
/

-- ============================================================================
-- POSTGRESQL VERSION
-- ============================================================================
-- Run this section if you are using PostgreSQL
-- 
-- To use: Comment out the Oracle section above and uncomment this section,
-- or run these commands directly in a PostgreSQL client

/*
-- Check if columns exist and add them if they don't
DO $$
BEGIN
    -- Add LST_RUN_DT column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = current_schema() 
        AND table_name = 'dms_jobsch' 
        AND column_name = 'lst_run_dt'
    ) THEN
        ALTER TABLE dms_jobsch ADD COLUMN lst_run_dt TIMESTAMP(6);
        RAISE NOTICE 'Added LST_RUN_DT column to DMS_JOBSCH';
    ELSE
        RAISE NOTICE 'LST_RUN_DT column already exists in DMS_JOBSCH';
    END IF;
    
    -- Add NXT_RUN_DT column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = current_schema() 
        AND table_name = 'dms_jobsch' 
        AND column_name = 'nxt_run_dt'
    ) THEN
        ALTER TABLE dms_jobsch ADD COLUMN nxt_run_dt TIMESTAMP(6);
        RAISE NOTICE 'Added NXT_RUN_DT column to DMS_JOBSCH';
    ELSE
        RAISE NOTICE 'NXT_RUN_DT column already exists in DMS_JOBSCH';
    END IF;
    
    -- Add comments
    COMMENT ON COLUMN dms_jobsch.lst_run_dt IS 'Last execution date and time for this scheduled job';
    COMMENT ON COLUMN dms_jobsch.nxt_run_dt IS 'Next scheduled execution date and time for this job';
    
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Restart the backend application';
    RAISE NOTICE '  2. The scheduler service will automatically calculate and';
    RAISE NOTICE '     update NXT_RUN_DT when schedules are created/updated';
    RAISE NOTICE '  3. LST_RUN_DT will be updated automatically when jobs execute';
END $$;
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify the migration was successful

-- Oracle Verification
/*
SELECT 
    column_name,
    data_type,
    nullable,
    data_default
FROM user_tab_columns
WHERE table_name = 'DMS_JOBSCH'
  AND column_name IN ('LST_RUN_DT', 'NXT_RUN_DT')
ORDER BY column_name;
*/

-- PostgreSQL Verification
/*
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name = 'dms_jobsch'
  AND column_name IN ('lst_run_dt', 'nxt_run_dt')
ORDER BY column_name;
*/

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- Only run this if you need to rollback the migration

-- Oracle Rollback
/*
ALTER TABLE DMS_JOBSCH DROP COLUMN LST_RUN_DT;
ALTER TABLE DMS_JOBSCH DROP COLUMN NXT_RUN_DT;
COMMIT;
*/

-- PostgreSQL Rollback
/*
ALTER TABLE dms_jobsch DROP COLUMN lst_run_dt;
ALTER TABLE dms_jobsch DROP COLUMN nxt_run_dt;
*/

