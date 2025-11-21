-- ------------------------------------------------------------------
-- DWPRCREQ queue table for Python scheduler service
-- ------------------------------------------------------------------

CREATE TABLE DWPRCREQ (
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
    CONSTRAINT pk_dwprcreq PRIMARY KEY (request_id)
);

CREATE INDEX dwprcreq_status_idx
    ON DWPRCREQ (status, requested_at);

CREATE INDEX dwprcreq_mapref_idx
    ON DWPRCREQ (mapref);

COMMENT ON TABLE DWPRCREQ IS 'Queue table for scheduler job requests (immediate, history, report, stop).';
COMMENT ON COLUMN DWPRCREQ.request_type IS 'IMMEDIATE, HISTORY, REPORT, STOP, REFRESH_SCHEDULE';
COMMENT ON COLUMN DWPRCREQ.status IS 'NEW, CLAIMED, DONE, FAILED';

