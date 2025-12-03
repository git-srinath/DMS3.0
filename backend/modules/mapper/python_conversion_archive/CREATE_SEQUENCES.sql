-- =============================================================================
-- Create Oracle Sequences for DWTOOL PKGDMS_MAPR Module
-- =============================================================================
-- These sequences are required for the Python PKGDMS_MAPR module to work
-- Run this script in your Oracle database before using the application
-- =============================================================================

-- Drop sequences if they exist (to start fresh)
-- Comment these out if you want to keep existing sequence values
BEGIN
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DMS_MAPRSQLSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DMS_MAPRSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DMS_MAPRDTLSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DMS_MAPERRSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
END;
/

-- =============================================================================
-- 1. DMS_MAPRSQLSEQ - Sequence for SQL Query Mappings (DMS_MAPRSQL table)
-- =============================================================================
CREATE SEQUENCE DMS_MAPRSQLSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DMS_MAPRSQLSEQ IS 'Sequence for generating SQL mapping IDs in DMS_MAPRSQL table';

-- =============================================================================
-- 2. DMS_MAPRSEQ - Sequence for Mappings (DMS_MAPR table)
-- =============================================================================
CREATE SEQUENCE DMS_MAPRSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DMS_MAPRSEQ IS 'Sequence for generating mapping IDs in DMS_MAPR table';

-- =============================================================================
-- 3. DMS_MAPRDTLSEQ - Sequence for Mapping Details (DMS_MAPRDTL table)
-- =============================================================================
CREATE SEQUENCE DMS_MAPRDTLSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DMS_MAPRDTLSEQ IS 'Sequence for generating mapping detail IDs in DMS_MAPRDTL table';

-- =============================================================================
-- 4. DMS_MAPERRSEQ - Sequence for Mapping Errors (DMS_MAPERR table)
-- =============================================================================
CREATE SEQUENCE DMS_MAPERRSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DMS_MAPERRSEQ IS 'Sequence for generating mapping error IDs in DMS_MAPERR table';

-- =============================================================================
-- Verification - Check if sequences were created successfully
-- =============================================================================
SELECT 
    sequence_name,
    min_value,
    max_value,
    increment_by,
    last_number
FROM user_sequences
WHERE sequence_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ')
ORDER BY sequence_name;

-- =============================================================================
-- Grant permissions (if needed for other users/schemas)
-- Uncomment and modify as needed
-- =============================================================================
-- GRANT SELECT ON DMS_MAPRSQLSEQ TO your_user_or_role;
-- GRANT SELECT ON DMS_MAPRSEQ TO your_user_or_role;
-- GRANT SELECT ON DMS_MAPRDTLSEQ TO your_user_or_role;
-- GRANT SELECT ON DMS_MAPERRSEQ TO your_user_or_role;

-- =============================================================================
-- Testing - Test the sequences
-- =============================================================================
-- SELECT DMS_MAPRSQLSEQ.NEXTVAL FROM DUAL;   -- Should return 1
-- SELECT DMS_MAPRSEQ.NEXTVAL FROM DUAL;       -- Should return 1
-- SELECT DMS_MAPRDTLSEQ.NEXTVAL FROM DUAL;    -- Should return 1
-- SELECT DMS_MAPERRSEQ.NEXTVAL FROM DUAL;     -- Should return 1

COMMIT;

PROMPT '============================================='
PROMPT 'Sequences created successfully!'
PROMPT 'Run the verification query above to confirm.'
PROMPT '============================================='

