-- ============================================================================
-- DASHBOARD CREATOR PHASE 1 MIGRATION (ORACLE)
-- ============================================================================
-- Date: 2026-02-20
-- Purpose:
--   Create metadata tables required for Dashboard Creator foundation.
--
-- Notes:
--   1) This script is for ORACLE metadata database.
--   2) PostgreSQL uses a separate script with lower-case identifiers.
--   3) Review in DEV/QA before production.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 0) Optional pre-checks
-- ---------------------------------------------------------------------------
-- SELECT table_name FROM user_tables WHERE table_name LIKE 'DMS_DASH_%';

-- ---------------------------------------------------------------------------
-- 1) Dashboard definition table
-- ---------------------------------------------------------------------------
CREATE TABLE DMS_DASH_DEF (
    DASHID           NUMBER PRIMARY KEY,
    DASHNM           VARCHAR2(200) NOT NULL,
    DSCRPTN          VARCHAR2(1000),
    OWNER_USRID      NUMBER,
    IS_ACTV          CHAR(1) DEFAULT 'Y' NOT NULL,
    CURFLG           CHAR(1) DEFAULT 'Y' NOT NULL,
    CRTDBY           VARCHAR2(100),
    CRTDDT           TIMESTAMP DEFAULT SYSTIMESTAMP,
    UPDTDBY          VARCHAR2(100),
    UPDTDT           TIMESTAMP
);

CREATE UNIQUE INDEX UK_DMS_DASH_DEF_NM_OWNER
    ON DMS_DASH_DEF (DASHNM, OWNER_USRID, CURFLG);

CREATE INDEX IDX_DMS_DASH_DEF_OWNER
    ON DMS_DASH_DEF (OWNER_USRID, IS_ACTV, CURFLG);

COMMENT ON TABLE DMS_DASH_DEF IS 'Dashboard Creator header metadata';
COMMENT ON COLUMN DMS_DASH_DEF.DASHID IS 'Primary key';
COMMENT ON COLUMN DMS_DASH_DEF.DASHNM IS 'Dashboard name';
COMMENT ON COLUMN DMS_DASH_DEF.DSCRPTN IS 'Dashboard description';
COMMENT ON COLUMN DMS_DASH_DEF.OWNER_USRID IS 'Owner user id from users table';
COMMENT ON COLUMN DMS_DASH_DEF.IS_ACTV IS 'Y/N active status';
COMMENT ON COLUMN DMS_DASH_DEF.CURFLG IS 'Current row flag';

-- ---------------------------------------------------------------------------
-- 2) Dashboard widget table
-- ---------------------------------------------------------------------------
CREATE TABLE DMS_DASH_WIDGET (
    WIDGTID          NUMBER PRIMARY KEY,
    DASHID           NUMBER NOT NULL,
    WIDGTNM          VARCHAR2(200) NOT NULL,
    WIDGTTYP         VARCHAR2(30) NOT NULL,
    SRCMODE          VARCHAR2(20) NOT NULL,
    SQLSRCID         NUMBER,
    ADHCSQL          CLOB,
    DBCNID           NUMBER,
    CFG_JSON         CLOB,
    LAYOUT_JSON      CLOB,
    ORDER_NO         NUMBER DEFAULT 1,
    IS_ACTV          CHAR(1) DEFAULT 'Y' NOT NULL,
    CURFLG           CHAR(1) DEFAULT 'Y' NOT NULL,
    CRTDBY           VARCHAR2(100),
    CRTDDT           TIMESTAMP DEFAULT SYSTIMESTAMP,
    UPDTDBY          VARCHAR2(100),
    UPDTDT           TIMESTAMP,
    CONSTRAINT FK_DASH_WIDGET_DEF FOREIGN KEY (DASHID) REFERENCES DMS_DASH_DEF(DASHID)
);

CREATE INDEX IDX_DMS_DASH_WIDGET_DASH
    ON DMS_DASH_WIDGET (DASHID, IS_ACTV, CURFLG, ORDER_NO);

COMMENT ON TABLE DMS_DASH_WIDGET IS 'Dashboard widgets and chart config metadata';
COMMENT ON COLUMN DMS_DASH_WIDGET.SRCMODE IS 'TABLE/SQL/REPORT_REF';
COMMENT ON COLUMN DMS_DASH_WIDGET.CFG_JSON IS 'Widget field mapping and chart config';
COMMENT ON COLUMN DMS_DASH_WIDGET.LAYOUT_JSON IS 'Canvas layout config (x,y,w,h)';

-- ---------------------------------------------------------------------------
-- 3) Dashboard filter table
-- ---------------------------------------------------------------------------
CREATE TABLE DMS_DASH_FILTER (
    FLTRID           NUMBER PRIMARY KEY,
    DASHID           NUMBER NOT NULL,
    SCOPE_TYP        VARCHAR2(20) NOT NULL,
    WIDGTID          NUMBER,
    FLTR_KEY         VARCHAR2(100) NOT NULL,
    FLTR_TYP         VARCHAR2(30) NOT NULL,
    FLTR_CFG_JSON    CLOB,
    IS_ACTV          CHAR(1) DEFAULT 'Y' NOT NULL,
    CURFLG           CHAR(1) DEFAULT 'Y' NOT NULL,
    CRTDBY           VARCHAR2(100),
    CRTDDT           TIMESTAMP DEFAULT SYSTIMESTAMP,
    UPDTDBY          VARCHAR2(100),
    UPDTDT           TIMESTAMP,
    CONSTRAINT FK_DASH_FILTER_DEF FOREIGN KEY (DASHID) REFERENCES DMS_DASH_DEF(DASHID),
    CONSTRAINT FK_DASH_FILTER_WIDGET FOREIGN KEY (WIDGTID) REFERENCES DMS_DASH_WIDGET(WIDGTID)
);

CREATE INDEX IDX_DMS_DASH_FILTER_DASH
    ON DMS_DASH_FILTER (DASHID, IS_ACTV, CURFLG);

COMMENT ON TABLE DMS_DASH_FILTER IS 'Global and widget-level filters for dashboards';

-- ---------------------------------------------------------------------------
-- 4) Dashboard sharing table
-- ---------------------------------------------------------------------------
CREATE TABLE DMS_DASH_SHARE (
    SHAREID          NUMBER PRIMARY KEY,
    DASHID           NUMBER NOT NULL,
    SHARE_TYP        VARCHAR2(20) NOT NULL,
    SHARE_REF_ID     NUMBER NOT NULL,
    CAN_VIEW         CHAR(1) DEFAULT 'Y' NOT NULL,
    CAN_EDIT         CHAR(1) DEFAULT 'N' NOT NULL,
    CAN_EXPORT       CHAR(1) DEFAULT 'Y' NOT NULL,
    IS_ACTV          CHAR(1) DEFAULT 'Y' NOT NULL,
    CURFLG           CHAR(1) DEFAULT 'Y' NOT NULL,
    CRTDBY           VARCHAR2(100),
    CRTDDT           TIMESTAMP DEFAULT SYSTIMESTAMP,
    UPDTDBY          VARCHAR2(100),
    UPDTDT           TIMESTAMP,
    CONSTRAINT FK_DASH_SHARE_DEF FOREIGN KEY (DASHID) REFERENCES DMS_DASH_DEF(DASHID)
);

CREATE UNIQUE INDEX UK_DMS_DASH_SHARE_UK
    ON DMS_DASH_SHARE (DASHID, SHARE_TYP, SHARE_REF_ID, CURFLG);

COMMENT ON TABLE DMS_DASH_SHARE IS 'Share settings by user or role for dashboards';
COMMENT ON COLUMN DMS_DASH_SHARE.SHARE_TYP IS 'USER/ROLE';

-- ---------------------------------------------------------------------------
-- 5) Dashboard export log table
-- ---------------------------------------------------------------------------
CREATE TABLE DMS_DASH_EXPORT_LOG (
    EXPID            NUMBER PRIMARY KEY,
    DASHID           NUMBER NOT NULL,
    EXPRT_FMT        VARCHAR2(10) NOT NULL,
    EXPRT_BY         VARCHAR2(100),
    EXPRT_AT         TIMESTAMP DEFAULT SYSTIMESTAMP,
    STTS             VARCHAR2(20) DEFAULT 'SUCCESS',
    MSG              VARCHAR2(2000),
    FILE_NM          VARCHAR2(500),
    FILE_SZ_BYTES    NUMBER,
    CONSTRAINT FK_DASH_EXPORT_DEF FOREIGN KEY (DASHID) REFERENCES DMS_DASH_DEF(DASHID)
);

CREATE INDEX IDX_DMS_DASH_EXPORT_DASH
    ON DMS_DASH_EXPORT_LOG (DASHID, EXPRT_AT);

COMMENT ON TABLE DMS_DASH_EXPORT_LOG IS 'Audit trail for dashboard PDF/PPT exports';

-- ---------------------------------------------------------------------------
-- 6) Sequences
-- ---------------------------------------------------------------------------
CREATE SEQUENCE DMS_DASH_DEF_SEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DMS_DASH_WIDGET_SEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DMS_DASH_FILTER_SEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DMS_DASH_SHARE_SEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE DMS_DASH_EXPORT_LOG_SEQ START WITH 1 INCREMENT BY 1;

-- ---------------------------------------------------------------------------
-- 7) Verification queries
-- ---------------------------------------------------------------------------
-- SELECT table_name FROM user_tables WHERE table_name IN (
--   'DMS_DASH_DEF','DMS_DASH_WIDGET','DMS_DASH_FILTER','DMS_DASH_SHARE','DMS_DASH_EXPORT_LOG'
-- );
--
-- SELECT sequence_name FROM user_sequences WHERE sequence_name LIKE 'DMS_DASH%_SEQ';

-- ---------------------------------------------------------------------------
-- 8) Rollback (manual)
-- ---------------------------------------------------------------------------
-- DROP TABLE DMS_DASH_EXPORT_LOG;
-- DROP TABLE DMS_DASH_SHARE;
-- DROP TABLE DMS_DASH_FILTER;
-- DROP TABLE DMS_DASH_WIDGET;
-- DROP TABLE DMS_DASH_DEF;
--
-- DROP SEQUENCE DMS_DASH_EXPORT_LOG_SEQ;
-- DROP SEQUENCE DMS_DASH_SHARE_SEQ;
-- DROP SEQUENCE DMS_DASH_FILTER_SEQ;
-- DROP SEQUENCE DMS_DASH_WIDGET_SEQ;
-- DROP SEQUENCE DMS_DASH_DEF_SEQ;

-- ============================================================================
-- End of ORACLE migration
-- ============================================================================
