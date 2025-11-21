-- =============================================================================
-- Create Oracle Sequences for DWTOOL PKGDWMAPR Module
-- =============================================================================
-- These sequences are required for the Python PKGDWMAPR module to work
-- Run this script in your Oracle database before using the application
-- =============================================================================

-- Drop sequences if they exist (to start fresh)
-- Comment these out if you want to keep existing sequence values
BEGIN
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DWMAPRSQLSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DWMAPRSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DWMAPRDTLSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE DWMAPERRSEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
END;
/

-- =============================================================================
-- 1. DWMAPRSQLSEQ - Sequence for SQL Query Mappings (DWMAPRSQL table)
-- =============================================================================
CREATE SEQUENCE DWMAPRSQLSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DWMAPRSQLSEQ IS 'Sequence for generating SQL mapping IDs in DWMAPRSQL table';

-- =============================================================================
-- 2. DWMAPRSEQ - Sequence for Mappings (DWMAPR table)
-- =============================================================================
CREATE SEQUENCE DWMAPRSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DWMAPRSEQ IS 'Sequence for generating mapping IDs in DWMAPR table';

-- =============================================================================
-- 3. DWMAPRDTLSEQ - Sequence for Mapping Details (DWMAPRDTL table)
-- =============================================================================
CREATE SEQUENCE DWMAPRDTLSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DWMAPRDTLSEQ IS 'Sequence for generating mapping detail IDs in DWMAPRDTL table';

-- =============================================================================
-- 4. DWMAPERRSEQ - Sequence for Mapping Errors (DWMAPERR table)
-- =============================================================================
CREATE SEQUENCE DWMAPERRSEQ
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999999999999999999999
    NOCACHE
    NOCYCLE
    ORDER;

COMMENT ON SEQUENCE DWMAPERRSEQ IS 'Sequence for generating mapping error IDs in DWMAPERR table';

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
WHERE sequence_name IN ('DWMAPRSQLSEQ', 'DWMAPRSEQ', 'DWMAPRDTLSEQ', 'DWMAPERRSEQ')
ORDER BY sequence_name;

-- =============================================================================
-- Grant permissions (if needed for other users/schemas)
-- Uncomment and modify as needed
-- =============================================================================
-- GRANT SELECT ON DWMAPRSQLSEQ TO your_user_or_role;
-- GRANT SELECT ON DWMAPRSEQ TO your_user_or_role;
-- GRANT SELECT ON DWMAPRDTLSEQ TO your_user_or_role;
-- GRANT SELECT ON DWMAPERRSEQ TO your_user_or_role;

-- =============================================================================
-- Testing - Test the sequences
-- =============================================================================
-- SELECT DWMAPRSQLSEQ.NEXTVAL FROM DUAL;   -- Should return 1
-- SELECT DWMAPRSEQ.NEXTVAL FROM DUAL;       -- Should return 1
-- SELECT DWMAPRDTLSEQ.NEXTVAL FROM DUAL;    -- Should return 1
-- SELECT DWMAPERRSEQ.NEXTVAL FROM DUAL;     -- Should return 1

COMMIT;

PROMPT '============================================='
PROMPT 'Sequences created successfully!'
PROMPT 'Run the verification query above to confirm.'
PROMPT '============================================='

