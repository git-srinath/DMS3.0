--
-- Database Migration Script: Add RWHKEY Column for Hash-Based Change Detection
-- 
-- Purpose: Add RWHKEY (Row Hash Key) column to existing dimension and fact tables
--          for efficient change detection using MD5 hash algorithm
--
-- Date: 2025-11-14
-- Author: AI Assistant
--
-- Instructions:
-- 1. Review the list of tables that need RWHKEY column
-- 2. Execute this script in the target schema
-- 3. Verify that all tables have the RWHKEY column added
-- 4. Re-run CREATE_UPDATE_JOB for all mappings to regenerate job flows
--

SET SERVEROUTPUT ON;

DECLARE
    v_count NUMBER;
    v_sql VARCHAR2(4000);
    v_tables_modified NUMBER := 0;
    v_tables_skipped NUMBER := 0;
BEGIN
    DBMS_OUTPUT.PUT_LINE('=================================================================');
    DBMS_OUTPUT.PUT_LINE('Adding RWHKEY Column to Dimension and Fact Tables');
    DBMS_OUTPUT.PUT_LINE('=================================================================');
    DBMS_OUTPUT.PUT_LINE('');
    
    -- Loop through all tables that have SKEY column (DIM, FCT, MRT tables)
    FOR tab_rec IN (
        SELECT DISTINCT table_name
        FROM user_tab_columns
        WHERE column_name = 'SKEY'
        ORDER BY table_name
    ) LOOP
        -- Check if RWHKEY column already exists
        SELECT COUNT(*)
        INTO v_count
        FROM user_tab_columns
        WHERE table_name = tab_rec.table_name
          AND column_name = 'RWHKEY';
        
        IF v_count = 0 THEN
            -- Add RWHKEY column
            v_sql := 'ALTER TABLE ' || tab_rec.table_name || ' ADD (RWHKEY VARCHAR2(32))';
            
            BEGIN
                EXECUTE IMMEDIATE v_sql;
                v_tables_modified := v_tables_modified + 1;
                DBMS_OUTPUT.PUT_LINE('[OK] Added RWHKEY to ' || tab_rec.table_name);
            EXCEPTION
                WHEN OTHERS THEN
                    DBMS_OUTPUT.PUT_LINE('[ERROR] Failed to add RWHKEY to ' || tab_rec.table_name);
                    DBMS_OUTPUT.PUT_LINE('        Error: ' || SQLERRM);
            END;
        ELSE
            v_tables_skipped := v_tables_skipped + 1;
            DBMS_OUTPUT.PUT_LINE('[SKIP] ' || tab_rec.table_name || ' already has RWHKEY column');
        END IF;
    END LOOP;
    
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('=================================================================');
    DBMS_OUTPUT.PUT_LINE('Migration Summary:');
    DBMS_OUTPUT.PUT_LINE('  Tables Modified: ' || v_tables_modified);
    DBMS_OUTPUT.PUT_LINE('  Tables Skipped:  ' || v_tables_skipped);
    DBMS_OUTPUT.PUT_LINE('  Total Tables:    ' || (v_tables_modified + v_tables_skipped));
    DBMS_OUTPUT.PUT_LINE('=================================================================');
    DBMS_OUTPUT.PUT_LINE('');
    
    IF v_tables_modified > 0 THEN
        DBMS_OUTPUT.PUT_LINE('IMPORTANT: Please regenerate job flows for all mappings:');
        DBMS_OUTPUT.PUT_LINE('  - Call PKGDWJOB.CREATE_ALL_JOBS or');
        DBMS_OUTPUT.PUT_LINE('  - Call PKGDWJOB.CREATE_UPDATE_JOB for each mapping');
        DBMS_OUTPUT.PUT_LINE('');
    END IF;
    
    COMMIT;
END;
/

-- Verification Query
-- Run this to verify RWHKEY column was added successfully
SELECT table_name, column_name, data_type, data_length, nullable
FROM user_tab_columns
WHERE column_name = 'RWHKEY'
ORDER BY table_name;

-- Optional: Create comment on RWHKEY columns
DECLARE
    v_sql VARCHAR2(1000);
BEGIN
    FOR tab_rec IN (
        SELECT DISTINCT table_name
        FROM user_tab_columns
        WHERE column_name = 'RWHKEY'
    ) LOOP
        v_sql := 'COMMENT ON COLUMN ' || tab_rec.table_name || '.RWHKEY IS ' ||
                 '''MD5 hash of source columns for change detection (excludes SKEY, audit columns)''';
        EXECUTE IMMEDIATE v_sql;
    END LOOP;
    DBMS_OUTPUT.PUT_LINE('Comments added to RWHKEY columns');
    COMMIT;
END;
/

-- Sample query to test hash-based change detection
/*
-- After migration, you can test with a sample dimension table:

SELECT 
    SKEY,
    RWHKEY,
    -- Your business columns here
    CURFLG,
    FROMDT,
    TODT,
    RECCRDT,
    RECUPDT
FROM YOUR_DIM_TABLE
WHERE CURFLG = 'Y'
  AND ROWNUM <= 10;
*/

PROMPT
PROMPT Migration completed! Please review the output above.
PROMPT

