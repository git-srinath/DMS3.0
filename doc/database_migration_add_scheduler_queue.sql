-- ------------------------------------------------------------------
-- DMS_PRCREQ queue table for Python scheduler service
-- ------------------------------------------------------------------

CREATE TABLE DMS_PRCREQ (
    request_id      VARCHAR2(64)    NOT NULL,
    mapref          VARCHAR2(100)   NOT NULL,
    request_type    VARCHAR2(30)    NOT NULL,
    payload         CLOB,
    status          VARCHAR2(20)    DEFAULT 'NEW',
    requested_at    TIMESTAMP       DEFAULT SYSTIMESTAMP,
    claimed_at      TIMESTAMP,
    claimed_by      VARCHAR2(64),
    completed_at    TIMESTAMP,
    result_payload  CLOB,
    CONSTRAINT pk_dms_prcreq PRIMARY KEY (request_id)
);

CREATE INDEX dms_prcreq_status_idx
    ON DMS_PRCREQ (status, requested_at);

CREATE INDEX dms_prcreq_mapref_idx
    ON DMS_PRCREQ (mapref);

COMMENT ON TABLE DMS_PRCREQ IS 'Queue table for scheduler job requests (immediate, history, report, stop).';
COMMENT ON COLUMN DMS_PRCREQ.request_type IS 'IMMEDIATE, HISTORY, REPORT, STOP, REFRESH_SCHEDULE';
COMMENT ON COLUMN DMS_PRCREQ.status IS 'NEW, CLAIMED, DONE, FAILED';

