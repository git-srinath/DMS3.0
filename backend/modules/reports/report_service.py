import ast
import csv
import hashlib
import json
import os
from contextlib import suppress
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.etree.ElementTree import Element, SubElement, ElementTree

try:
    from backend.database.dbconnect import (
        create_metadata_connection,
        create_target_connection,
    )
    from backend.modules.common.db_table_utils import (
        detect_db_type,
        get_metadata_table_refs,
    )
    from backend.modules.common.id_provider import IdProviderError, next_id
    from backend.modules.logger import debug, error, info
except ImportError:  # Fallback for Flask-style imports
    from database.dbconnect import (  # type: ignore
        create_metadata_connection,
        create_target_connection,
    )
    from modules.common.db_table_utils import (  # type: ignore
        detect_db_type,
        get_metadata_table_refs,
    )
    from modules.common.id_provider import IdProviderError, next_id  # type: ignore
    from modules.logger import debug, error, info  # type: ignore

MAX_PREVIEW_ROWS = 1000
REPORT_OUTPUT_BASE = Path(os.getenv("REPORT_OUTPUT_DIR", os.path.join("data", "reports_output")))
REPORT_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)


class ReportServiceError(Exception):
    """Domain-specific exception for report metadata failures."""

    def __init__(self, message: str, status_code: int = 400, code: str = "REPORT_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class _ParamBuilder:
    """Utility to build parameter collections for Oracle (dict) vs PostgreSQL (tuple)."""

    def __init__(self, db_type: str):
        self.db_type = db_type.upper()
        self._params: Dict[str, Any] | List[Any]
        if self.db_type == "ORACLE":
            self._params = {}
        else:
            self._params = []
        self._counter = 0

    def add(self, value: Any, hint: str = "p") -> str:
        if self.db_type == "ORACLE":
            key = f"{hint}{self._counter}"
            self._counter += 1
            self._params[key] = value
            return f":{key}"
        else:
            self._params.append(value)
            return "%s"

    @property
    def params(self) -> Dict[str, Any] | Sequence[Any] | None:
        if self.db_type == "ORACLE":
            return self._params if self._params else None
        return tuple(self._params) if self._params else None


class _MetadataRepository:
    """Shared helpers for metadata-backed services."""

    def __init__(self):
        self.schema = os.getenv("DMS_SCHEMA", "DMS")

    def _open_connection(self):
        conn = create_metadata_connection()
        cursor = conn.cursor()
        db_type = detect_db_type(conn)
        tables = get_metadata_table_refs(cursor, self.schema, db_type)
        return conn, cursor, db_type, tables

    def _close_connection(self, conn, cursor):
        with suppress(Exception):
            if cursor:
                cursor.close()
        with suppress(Exception):
            if conn:
                conn.close()

    def _commit(self, conn):
        with suppress(Exception):
            if hasattr(conn, "autocommit") and conn.autocommit:
                return
            conn.commit()

    def _rollback(self, conn):
        with suppress(Exception):
            if hasattr(conn, "autocommit") and conn.autocommit:
                return
            conn.rollback()

    def _execute(self, cursor, query: str, params: Optional[Sequence[Any] | Dict[str, Any]] = None):
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)

    def _execute_insert(self, cursor, table: str, columns: List[str], values: List[Any], db_type: str):
        placeholders = [f":{col.lower()}" if db_type == "ORACLE" else "%s" for col in columns]
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        if db_type == "ORACLE":
            params = {col.lower(): value for col, value in zip(columns, values)}
            cursor.execute(sql, params)
        else:
            cursor.execute(sql, tuple(values))

    def _fetch_all_dict(self, cursor) -> List[Dict[str, Any]]:
        rows = cursor.fetchall()
        if not rows:
            return []
        columns = [desc[0].lower() for desc in cursor.description]
        results = []
        for row in rows:
            row_dict = {columns[idx]: row[idx] for idx in range(len(columns))}
            results.append(row_dict)
        return results


class ReportMetadataService(_MetadataRepository):
    """Handles CRUD operations for report metadata tables."""

    def __init__(self):
        super().__init__()
        self._grouping_columns_verified: Dict[Tuple[str, str], bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_reports(self, search: Optional[str] = None, include_inactive: bool = False) -> List[Dict[str, Any]]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            builder = _ParamBuilder(db_type)
            query = f"""
                SELECT
                    r.RPRTID AS report_id,
                    r.RPRTNM AS report_name,
                    r.DSCRPTN AS description,
                    r.SQLSRCID AS sql_source_id,
                    r.ADHCSQL AS adhoc_sql,
                    r.DBCNID AS db_connection_id,
                    r.DFLT_OTPT_FMT AS default_output_format,
                    r.SPPRTD_FMTS AS supported_formats,
                    r.PRVW_RW_LMT AS preview_row_limit,
                    r.IS_ACTV AS is_active,
                    r.CURFLG AS curflg,
                    r.CRTDDT AS created_at,
                    r.UPDTDT AS updated_at,
                    (
                        SELECT COUNT(1)
                        FROM {tables['DMS_RPRT_SCHD']} s
                        WHERE s.RPRTID = r.RPRTID
                          AND UPPER(COALESCE(s.STTS, '')) IN ('ACTIVE', 'QUEUED', 'SCHEDULED')
                    ) AS active_schedule_count
                FROM {tables['DMS_RPRT_DEF']} r
                WHERE r.CURFLG = 'Y'
            """

            if not include_inactive:
                query += " AND r.IS_ACTV = 'Y'"

            if search:
                like_value = f"%{search.upper()}%"
                placeholder_name = builder.add(like_value, "search")
                placeholder_desc = builder.add(like_value, "search")
                query += f" AND (UPPER(r.RPRTNM) LIKE {placeholder_name} OR UPPER(r.DSCRPTN) LIKE {placeholder_desc})"

            query += " ORDER BY r.RPRTNM"
            self._execute(cursor, query, builder.params)
            rows = self._fetch_all_dict(cursor)
            reports = [self._map_report_summary(row) for row in rows]

            # Fetch schedule info for all reports
            report_ids = [r["reportId"] for r in reports if r["reportId"]]
            if report_ids:
                schedule_map = self._fetch_latest_schedules_for_reports(cursor, tables, db_type, report_ids)
                for report in reports:
                    sched = schedule_map.get(report["reportId"])
                    if sched:
                        report["scheduleId"] = sched.get("scheduleId")
                        report["scheduleFrequency"] = sched.get("frequency")
                        report["scheduleTimeParam"] = sched.get("timeParam")
                        report["scheduleStatus"] = sched.get("status")
                        report["scheduleNextRun"] = sched.get("nextRunAt")
                        report["scheduleLastRun"] = sched.get("lastRunAt")
                        report["scheduleOutputFormat"] = sched.get("outputFormat")
                        report["scheduleDestination"] = sched.get("destination")

            return reports
        finally:
            self._close_connection(conn, cursor)

    def _fetch_latest_schedules_for_reports(self, cursor, tables, db_type: str, report_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not report_ids:
            return {}
        placeholders = ", ".join(str(rid) for rid in report_ids)
        query = f"""
            SELECT
                SCHDID AS schedule_id,
                RPRTID AS report_id,
                FRQNCY AS frequency,
                TM_PRM AS time_param,
                NXT_RUN_DT AS next_run_dt,
                LST_RUN_DT AS last_run_dt,
                STTS AS status,
                OTPT_FMT AS output_format,
                DSTN_TYP AS destination_type
            FROM {tables['DMS_RPRT_SCHD']}
            WHERE RPRTID IN ({placeholders})
            ORDER BY RPRTID, SCHDID DESC
        """
        self._execute(cursor, query, {})
        rows = self._fetch_all_dict(cursor)
        result: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            report_id = self._to_int(row.get("report_id"))
            if report_id and report_id not in result:
                result[report_id] = {
                    "scheduleId": self._to_int(row.get("schedule_id")),
                    "frequency": row.get("frequency"),
                    "timeParam": row.get("time_param") or "",
                    "status": (row.get("status") or "").upper() or None,
                    "nextRunAt": self._to_iso(row.get("next_run_dt")),
                    "lastRunAt": self._to_iso(row.get("last_run_dt")),
                    "outputFormat": (row.get("output_format") or "").upper() or None,
                    "destination": (row.get("destination_type") or "").upper() or None,
                }
        return result

    def get_report(self, report_id: int) -> Dict[str, Any]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            report = self._fetch_report_definition(cursor, tables, db_type, report_id)
            if not report:
                raise ReportServiceError("Report not found", status_code=404, code="REPORT_NOT_FOUND")

            fields = self._fetch_fields(cursor, tables, db_type, report_id)
            formulas = self._fetch_formulas(cursor, tables, db_type, report_id)
            layout = self._fetch_layout(cursor, tables, db_type, report_id)
            schedules = self._fetch_schedules(cursor, tables, db_type, report_id)

            report["fields"] = fields
            report["formulas"] = formulas
            report["layout"] = layout
            report["schedules"] = schedules
            report["hasActiveSchedule"] = any(s.get("status") in {"ACTIVE", "QUEUED", "SCHEDULED"} for s in schedules)

            return report
        finally:
            self._close_connection(conn, cursor)

    def create_report(self, payload: Dict[str, Any], username: str) -> Dict[str, Any]:
        normalized = self._normalize_payload(payload, is_update=False)

        conn, cursor, db_type, tables = self._open_connection()
        try:
            report_id = self._next_id(cursor, "DMS_RPRT_DEF_SEQ")
            checksum = self._compute_checksum(normalized)
            sql_details = self._resolve_sql_from_payload(cursor, tables, db_type, normalized)
            final_sql = self._build_final_sql_from_fields(
                sql_details.get("sqlText"),
                normalized.get("fields"),
            )
            self._insert_report_definition(
                cursor, tables, db_type, report_id, normalized, checksum, username, final_sql
            )

            formula_map = self._persist_formulas(cursor, tables, db_type, report_id, normalized.get("formulas", []), username)
            self._persist_fields(cursor, tables, db_type, report_id, normalized.get("fields", []), formula_map)
            self._persist_layout(cursor, tables, db_type, report_id, normalized.get("layout"))

            self._commit(conn)
            info(f"[ReportMetadataService] Created report {report_id}")
        except Exception as exc:
            self._rollback(conn)
            error(f"[ReportMetadataService] Failed to create report: {exc}", exc_info=True)
            if isinstance(exc, ReportServiceError):
                raise
            raise ReportServiceError("Failed to create report definition") from exc
        finally:
            self._close_connection(conn, cursor)

        return self.get_report(report_id)

    def update_report(self, report_id: int, payload: Dict[str, Any], username: str, force_update: bool = False) -> Dict[str, Any]:
        normalized = self._normalize_payload(payload, is_update=True)

        conn, cursor, db_type, tables = self._open_connection()
        try:
            if not self._report_exists(cursor, tables, db_type, report_id):
                raise ReportServiceError("Report not found", status_code=404, code="REPORT_NOT_FOUND")

            has_active_schedule = self._has_active_schedule(cursor, tables, db_type, report_id)
            if has_active_schedule and not force_update:
                raise ReportServiceError(
                    "Report has active schedules. Pass forceUpdate=true to proceed.",
                    status_code=409,
                    code="REPORT_HAS_ACTIVE_SCHEDULE",
                    details={"reportId": report_id},
                )

            checksum = self._compute_checksum(normalized)
            sql_details = self._resolve_sql_from_payload(cursor, tables, db_type, normalized)
            final_sql = self._build_final_sql_from_fields(
                sql_details.get("sqlText"),
                normalized.get("fields"),
            )
            self._update_report_definition(
                cursor, tables, db_type, report_id, normalized, checksum, username, final_sql
            )
            self._delete_children(cursor, tables, db_type, report_id)

            formula_map = self._persist_formulas(cursor, tables, db_type, report_id, normalized.get("formulas", []), username)
            self._persist_fields(cursor, tables, db_type, report_id, normalized.get("fields", []), formula_map)
            self._persist_layout(cursor, tables, db_type, report_id, normalized.get("layout"))

            self._commit(conn)
            info(f"[ReportMetadataService] Updated report {report_id}")
        except Exception as exc:
            self._rollback(conn)
            error(f"[ReportMetadataService] Failed to update report {report_id}: {exc}", exc_info=True)
            if isinstance(exc, ReportServiceError):
                raise
            raise ReportServiceError("Failed to update report definition") from exc
        finally:
            self._close_connection(conn, cursor)

        return self.get_report(report_id)

    def execute_report(
        self,
        report_id: int,
        payload: Optional[Dict[str, Any]] = None,
        username: str = "system",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        report = self.get_report(report_id)
        dataset = self._build_dataset(
            report=report,
            row_limit=payload.get("rowLimit"),
            parameters=payload.get("parameters"),
            allow_unbounded=True,
        )
        output_formats = self._normalize_output_formats(
            payload.get("outputFormats") or report.get("supportedFormats") or [report.get("defaultOutputFormat") or "CSV"]
        )

        conn, cursor, db_type, tables = self._open_connection()
        run_id = None
        try:
            run_id = self._insert_report_run(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                report_id=report_id,
                request_id=request_id,
                username=username,
                output_formats=output_formats,
                parameter_payload=payload.get("parameters"),
            )
            self._commit(conn)

            outputs = self._generate_outputs(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                report=report,
                run_id=run_id,
                dataset=dataset,
                output_formats=output_formats,
            )

            self._update_report_run_status(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                run_id=run_id,
                status="SUCCESS",
                row_count=dataset["rowCount"],
                message=None,
            )
            self._commit(conn)
            return {
                "runId": run_id,
                "reportId": report_id,
                "rowCount": dataset["rowCount"],
                "outputs": outputs,
            }
        except ReportServiceError:
            self._rollback(conn)
            raise
        except Exception as exc:
            self._rollback(conn)
            error(f"[ReportMetadataService] Report execution failed for {report_id}: {exc}", exc_info=True)
            if run_id:
                with suppress(Exception):
                    self._fail_report_run(run_id=run_id, message=str(exc))
            raise ReportServiceError("Failed to execute report", code="REPORT_EXECUTION_FAILED") from exc
        finally:
            self._close_connection(conn, cursor)

    def preview_report(
        self,
        report_id: int,
        row_limit: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None,
        username: str = "system",
        allow_unbounded: bool = False,
    ) -> Dict[str, Any]:
        report = self.get_report(report_id)
        if allow_unbounded and row_limit is None:
            effective_limit = None
        else:
            effective_limit = self._clamp_preview_limit(
                row_limit or report.get("previewRowLimit") or MAX_PREVIEW_ROWS
            )
        dataset = self._build_dataset(
            report=report,
            row_limit=effective_limit,
            parameters=parameters,
            allow_unbounded=allow_unbounded,
        )

        self._persist_preview_cache(
            report_id=report_id,
            username=username,
            row_limit=effective_limit,
            source_db_type=dataset["dbType"],
            rows=dataset["rows"],
        )

        return {
            "reportId": report_id,
            "rowLimit": effective_limit,
            "rowCount": dataset["rowCount"],
            "columns": dataset["columns"],
            "rows": dataset["rows"],
            "sourceDbType": dataset["dbType"],
            "finalSql": dataset.get("finalSql"),
        }

    # ------------------------------------------------------------------
    # Data Fetch helpers
    # ------------------------------------------------------------------
    def _fetch_report_definition(self, cursor, tables, db_type: str, report_id: int) -> Optional[Dict[str, Any]]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "rprtid")
        query = f"""
            SELECT
                r.RPRTID AS report_id,
                r.RPRTNM AS report_name,
                r.DSCRPTN AS description,
                r.SQLSRCID AS sql_source_id,
                r.ADHCSQL AS adhoc_sql,
                r.DBCNID AS db_connection_id,
                r.DFLT_OTPT_FMT AS default_output_format,
                r.SPPRTD_FMTS AS supported_formats,
                r.PRVW_RW_LMT AS preview_row_limit,
                r.IS_ACTV AS is_active,
                r.CURFLG AS curflg,
                r.FINAL_SQL AS final_sql,
                r.CHCKSM AS checksum,
                r.CRTDBY AS created_by,
                r.CRTDDT AS created_at,
                r.UPDTDBY AS updated_by,
                r.UPDTDT AS updated_at
            FROM {tables['DMS_RPRT_DEF']} r
            WHERE r.RPRTID = {placeholder}
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        if not rows:
            return None
        row = rows[0]
        summary = self._map_report_summary(row)
        summary["adhocSql"] = self._read_lob(row.get("adhoc_sql"))
        summary["finalSql"] = self._read_lob(row.get("final_sql"))
        summary["metadata"] = {
            "checksum": row.get("checksum"),
            "createdBy": row.get("created_by"),
            "createdAt": self._to_iso(row.get("created_at")),
            "updatedBy": row.get("updated_by"),
            "updatedAt": self._to_iso(row.get("updated_at")),
        }
        return summary

    def _fetch_fields(self, cursor, tables, db_type: str, report_id: int) -> List[Dict[str, Any]]:
        self._ensure_grouping_columns(cursor, tables, db_type)
        grp_col, seq_col, dir_col = self._grouping_column_names(db_type)
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "fields")
        query = f"""
            SELECT
                FLDID AS field_id,
                RPRTID AS report_id,
                PNL_TYP AS panel_type,
                ROW_ORDR AS row_order,
                FLD_NM AS field_name,
                FLD_ALS AS field_alias,
                SRC_CLMN AS source_column,
                FRMLA_ID AS formula_id,
                FRMLA_INLN AS inline_formula,
                DT_TYP AS data_type,
                FMT_MASK AS format_mask,
                IS_VSBL AS is_visible,
                {grp_col} AS is_group_by,
                {seq_col} AS order_by_seq,
                {dir_col} AS order_by_dir,
                NOTES AS notes
            FROM {tables['DMS_RPRT_FLD']}
            WHERE RPRTID = {placeholder}
            ORDER BY PNL_TYP, ROW_ORDR, FLDID
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        results = []
        for row in rows:
            results.append({
                "fieldId": self._to_int(row.get("field_id")),
                "panelType": row.get("panel_type"),
                "rowOrder": self._to_int(row.get("row_order")),
                "fieldName": row.get("field_name"),
                "fieldAlias": row.get("field_alias"),
                "sourceColumn": row.get("source_column"),
                "formulaId": self._to_int(row.get("formula_id")),
                "inlineFormula": self._read_lob(row.get("inline_formula")),
                "dataType": row.get("data_type"),
                "formatMask": row.get("format_mask"),
                "isVisible": self._from_flag(row.get("is_visible")),
                "isGroupBy": self._from_flag(row.get("is_group_by")),
                "orderBySeq": self._to_int(row.get("order_by_seq")),
                "orderByDir": (row.get("order_by_dir") or "ASC").upper() if row.get("order_by_dir") else None,
                "notes": row.get("notes"),
            })
        return results

    def _fetch_formulas(self, cursor, tables, db_type: str, report_id: int) -> List[Dict[str, Any]]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "formula")
        query = f"""
            SELECT
                FRMLA_ID AS formula_id,
                RPRTID AS report_id,
                NM AS name,
                XPRSN AS expression,
                SPPRTD_DB_TYP AS supported_db_types,
                HLP_TXT AS help_text
            FROM {tables['DMS_RPRT_FRML']}
            WHERE RPRTID = {placeholder}
            ORDER BY FRMLA_ID
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        results = []
        for row in rows:
            results.append({
                "formulaId": self._to_int(row.get("formula_id")),
                "name": row.get("name"),
                "expression": self._read_lob(row.get("expression")),
                "supportedDbTypes": self._deserialize_csv(row.get("supported_db_types")),
                "helpText": row.get("help_text"),
            })
        return results

    def _fetch_layout(self, cursor, tables, db_type: str, report_id: int) -> Dict[str, Any]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "layout")
        query = f"""
            SELECT
                LYOTID AS layout_id,
                HDR_TMPLT AS header_template,
                DTL_TMPLT AS detail_template,
                PRVW_STTNGS AS preview_settings
            FROM {tables['DMS_RPRT_LYOT']}
            WHERE RPRTID = {placeholder}
            ORDER BY LYOTID DESC
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        if not rows:
            return {"headerTemplate": None, "detailTemplate": None, "previewSettings": None}
        row = rows[0]
        return {
            "layoutId": self._to_int(row.get("layout_id")),
            "headerTemplate": self._load_json(self._read_lob(row.get("header_template"))),
            "detailTemplate": self._load_json(self._read_lob(row.get("detail_template"))),
            "previewSettings": self._load_json(self._read_lob(row.get("preview_settings"))),
        }

    def _fetch_schedules(self, cursor, tables, db_type: str, report_id: int) -> List[Dict[str, Any]]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "schedule")
        query = f"""
            SELECT
                SCHDID AS schedule_id,
                FRQNCY AS frequency,
                NXT_RUN_DT AS next_run_dt,
                LST_RUN_DT AS last_run_dt,
                STTS AS status,
                QUE_REQ_ID AS queue_request_id
            FROM {tables['DMS_RPRT_SCHD']}
            WHERE RPRTID = {placeholder}
            ORDER BY SCHDID DESC
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        results = []
        for row in rows:
            results.append({
                "scheduleId": self._to_int(row.get("schedule_id")),
                "frequency": row.get("frequency"),
                "nextRunAt": self._to_iso(row.get("next_run_dt")),
                "lastRunAt": self._to_iso(row.get("last_run_dt")),
                "status": (row.get("status") or "").upper(),
                "queueRequestId": row.get("queue_request_id"),
            })
        return results

    # ------------------------------------------------------------------
    # Preview helpers
    # ------------------------------------------------------------------
    def _build_dataset(
        self,
        report: Dict[str, Any],
        row_limit: Optional[int],
        parameters: Optional[Dict[str, Any]],
        allow_unbounded: bool,
    ) -> Dict[str, Any]:
        if row_limit is None:
            effective_limit = None if allow_unbounded else self._clamp_preview_limit(report.get("previewRowLimit") or MAX_PREVIEW_ROWS)
        else:
            effective_limit = self._clamp_preview_limit(row_limit) if not allow_unbounded else max(1, int(row_limit))

        sql_text, connection_id, final_sql = self._build_sql_for_execution(report)
        query_result = self._run_preview_query(
            connection_id=connection_id,
            sql_text=sql_text,
            row_limit=effective_limit,
            parameters=parameters or {},
        )
        rows = query_result["rows"]
        columns = query_result["columns"]
        return {
            "rows": rows,
            "columns": columns,
            "rowCount": len(rows),
            "dbType": query_result["dbType"],
            "finalSql": final_sql or sql_text,
        }

    def _resolve_sql_source(self, report: Dict[str, Any]) -> Dict[str, Any]:
        sql_source_id = report.get("sqlSourceId")
        report_connection_id = report.get("dbConnectionId")
        if sql_source_id:
            conn, cursor, db_type, tables = self._open_connection()
            try:
                record = self._load_sql_source_record(
                    cursor=cursor,
                    tables=tables,
                    db_type=db_type,
                    sql_source_id=sql_source_id,
                    fallback_connection_id=report_connection_id,
                )
            finally:
                self._close_connection(conn, cursor)
            sql_text = record["sqlText"]
            # Prefer report's dbConnectionId over SQL source's connection
            connection_id = report_connection_id or record.get("connectionId")
        else:
            sql_text = report.get("adhocSql")
            connection_id = report_connection_id

        if not sql_text:
            raise ReportServiceError("Report SQL is required before preview", code="SQL_SOURCE_REQUIRED")

        return {"sqlText": sql_text, "connectionId": connection_id}

    def _load_sql_source_record(
        self,
        cursor,
        tables,
        db_type: str,
        sql_source_id: int,
        fallback_connection_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(sql_source_id, "sqlsrc")
        query = f"""
            SELECT
                MAPRSQL AS sql_text,
                SQLCONID AS connection_id
            FROM {tables['DMS_MAPRSQL']}
            WHERE MAPRSQLID = {placeholder}
              AND CURFLG = 'Y'
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        if not rows:
            raise ReportServiceError("SQL source not found for report", code="SQL_SOURCE_NOT_FOUND", status_code=404)
        sql_text = self._read_lob(rows[0].get("sql_text"))
        connection_id = self._to_int(rows[0].get("connection_id")) or fallback_connection_id
        return {"sqlText": sql_text, "connectionId": connection_id}

    def _resolve_sql_from_payload(self, cursor, tables, db_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        sql_source_id = payload.get("sqlSourceId")
        if sql_source_id:
            return self._load_sql_source_record(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                sql_source_id=sql_source_id,
                fallback_connection_id=payload.get("dbConnectionId"),
            )
        return {
            "sqlText": payload.get("adhocSql"),
            "connectionId": payload.get("dbConnectionId"),
        }

    def _build_sql_for_execution(self, report: Dict[str, Any]) -> Tuple[str, Optional[int], Optional[str]]:
        sql_details = self._resolve_sql_source(report)
        final_sql = self._build_final_sql_from_fields(sql_details["sqlText"], report.get("fields"))
        sql_text = final_sql or sql_details["sqlText"]
        return sql_text, sql_details.get("connectionId"), final_sql

    def _build_final_sql_from_fields(self, base_sql: Optional[str], fields: Optional[List[Dict[str, Any]]]) -> Optional[str]:
        if not base_sql or not fields:
            return None
        # Remove trailing semicolons to allow wrapping in subquery
        base_sql = base_sql.strip().rstrip(';').strip()
        detail_fields = [
            field for field in fields
            if (field.get("panelType") or "DETAIL").upper() == "DETAIL"
        ]
        select_items: List[str] = []
        group_items: List[str] = []
        order_items: List[Tuple[int, str]] = []
        for index, field in enumerate(detail_fields):
            source_expr = field.get("inlineFormula") or field.get("sourceColumn")
            if not source_expr:
                continue
            alias = field.get("fieldAlias") or field.get("fieldName") or f"COLUMN_{index + 1}"
            select_items.append(f"{source_expr} AS \"{alias}\"")
            if field.get("isGroupBy"):
                group_items.append(source_expr)
            order_seq = field.get("orderBySeq")
            if order_seq is not None:
                try:
                    seq_value = int(order_seq)
                except (TypeError, ValueError):
                    seq_value = None
                if seq_value and seq_value > 0:
                    direction = (field.get("orderByDir") or "ASC").upper()
                    if direction not in ("ASC", "DESC"):
                        direction = "ASC"
                    order_items.append((seq_value, f"\"{alias}\" {direction}"))
        if not select_items:
            return None
        sql_lines = [
            "SELECT",
            "    " + ",\n    ".join(select_items),
            "FROM (",
            base_sql.strip(),
            ") base_query",
        ]
        if group_items:
            sql_lines.append("GROUP BY " + ", ".join(group_items))
        if order_items:
            order_items.sort(key=lambda item: item[0])
            sql_lines.append("ORDER BY " + ", ".join(item[1] for item in order_items))
        return "\n".join(sql_lines)

    def _run_preview_query(
        self,
        connection_id: Optional[int],
        sql_text: str,
        row_limit: Optional[int],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        sql_clean = sql_text.strip().rstrip(";")
        if not sql_clean.lower().startswith("select"):
            raise ReportServiceError("Preview only supports SELECT statements", code="SQL_NOT_SELECT")

        connection = None
        cursor = None
        try:
            if connection_id:
                connection = create_target_connection(connection_id)
            else:
                connection = create_metadata_connection()
            cursor = connection.cursor()
            target_db_type = detect_db_type(connection)

            limited_sql, limit_params = self._apply_row_limit(sql_clean, target_db_type, row_limit)
            if limit_params is None:
                cursor.execute(limited_sql)
            else:
                cursor.execute(limited_sql, limit_params)

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            dataset_rows = self._rows_to_dicts(columns, rows)
            if row_limit is not None and len(dataset_rows) > row_limit:
                dataset_rows = dataset_rows[:row_limit]

            return {"rows": dataset_rows, "dbType": target_db_type, "columns": columns}
        except ReportServiceError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            error(f"[ReportMetadataService] Preview query failed: {exc}", exc_info=True)
            raise ReportServiceError("Failed to execute preview query", code="PREVIEW_QUERY_FAILED") from exc
        finally:
            if cursor:
                with suppress(Exception):
                    cursor.close()
            if connection:
                with suppress(Exception):
                    connection.close()

    def _introspect_query_columns(self, sql_text: str, connection_id: Optional[int]) -> List[Dict[str, Any]]:
        sql_clean = (sql_text or "").strip().rstrip(";")
        if not sql_clean.lower().startswith("select"):
            raise ReportServiceError("Preview only supports SELECT statements", code="SQL_NOT_SELECT")
        connection = None
        cursor = None
        try:
            if connection_id:
                connection = create_target_connection(connection_id)
            else:
                connection = create_metadata_connection()
            cursor = connection.cursor()
            wrapper = f"SELECT * FROM ({sql_clean}) src WHERE 1=0"
            cursor.execute(wrapper)
            description = cursor.description or []
            columns: List[Dict[str, Any]] = []
            for desc in description:
                column_name = desc[0]
                data_type = None
                if len(desc) > 1:
                    type_token = desc[1]
                    data_type = getattr(type_token, "__name__", None) or str(type_token)
                columns.append({"name": column_name, "dataType": data_type})
            return columns
        except ReportServiceError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            error(f"[ReportMetadataService] SQL description failed: {exc}", exc_info=True)
            raise ReportServiceError("Failed to describe SQL", code="SQL_INTROSPECT_FAILED") from exc
        finally:
            if cursor:
                with suppress(Exception):
                    cursor.close()
            if connection:
                with suppress(Exception):
                    connection.close()

    def _apply_row_limit(self, base_sql: str, db_type: str, row_limit: Optional[int]):
        if row_limit is None:
            return base_sql, None
        db_type = (db_type or "").upper()
        if db_type == "ORACLE":
            return (
                f"SELECT * FROM ({base_sql}) src WHERE ROWNUM <= :preview_limit",
                {"preview_limit": row_limit},
            )
        if db_type in {"POSTGRESQL", "POSTGRES", "MYSQL"}:
            return (
                f"SELECT * FROM ({base_sql}) src LIMIT %s",
                (row_limit,),
            )
        if db_type in {"MSSQL", "SQL_SERVER", "SYBASE"}:
            return (
                f"SELECT * FROM (SELECT TOP {row_limit} * FROM ({base_sql}) src) limited_src",
                None,
            )
        return base_sql, None

    def _rows_to_dicts(self, columns: List[str], rows: Sequence[Sequence[Any]]) -> List[Dict[str, Any]]:
        dataset = []
        for row in rows:
            entry = {}
            for idx, column in enumerate(columns):
                entry[column] = row[idx]
            dataset.append(entry)
        return dataset

    def _project_fields(self, report: Dict[str, Any], dataset_rows: List[Dict[str, Any]]):
        fields = report.get("fields", [])
        visible_fields = [
            field for field in fields if field.get("isVisible", True)
        ]
        detail_fields = [
            field for field in visible_fields
            if (field.get("panelType") or "DETAIL").upper() == "DETAIL"
        ]
        if not detail_fields:
            detail_fields = visible_fields

        if not detail_fields:
            return dataset_rows, []

        formula_lookup = {}
        for formula in report.get("formulas", []):
            if formula.get("formulaId"):
                formula_lookup[int(formula["formulaId"])] = formula.get("expression")

        evaluator = FormulaEvaluator()
        projected_rows: List[Dict[str, Any]] = []
        column_order: List[str] = []
        prepared_fields = []

        for field in detail_fields:
            alias = field.get("fieldAlias") or field.get("fieldName") or f"FIELD_{field.get('fieldId')}"
            column_order.append(alias)
            prepared_fields.append(
                {
                    "alias": alias,
                    "sourceColumn": field.get("sourceColumn"),
                    "inlineFormula": field.get("inlineFormula"),
                    "formulaExpression": formula_lookup.get(field.get("formulaId")),
                }
            )

        for raw_row in dataset_rows:
            row_result: Dict[str, Any] = {}
            env = {str(key).upper(): value for key, value in raw_row.items()}
            for field in prepared_fields:
                alias = field["alias"]
                value = None

                source_column = field["sourceColumn"]
                if source_column:
                    value = self._lookup_case_insensitive(raw_row, source_column)
                elif field["inlineFormula"]:
                    value = evaluator.evaluate(field["inlineFormula"], env)
                elif field["formulaExpression"]:
                    value = evaluator.evaluate(field["formulaExpression"], env)

                row_result[alias] = value
                env[alias.upper()] = value

            projected_rows.append(row_result)

        return projected_rows, column_order

    def _lookup_case_insensitive(self, row: Dict[str, Any], column: str):
        if column in row:
            return row[column]
        upper_map = {str(key).upper(): key for key in row.keys()}
        lookup_key = column.upper()
        actual_key = upper_map.get(lookup_key)
        if actual_key:
            return row[actual_key]
        return None

    def _persist_preview_cache(self, report_id: int, username: str, row_limit: int, source_db_type: str, rows: List[Dict[str, Any]]):
        conn, cursor, db_type, tables = self._open_connection()
        try:
            cache_id = self._next_id(cursor, "DMS_RPRT_PRVW_CCH_SEQ")
            dataset_blob = self._serialize_dataset(rows)
            columns = ["CCHID", "RPRTID", "USRID", "ROW_LMT", "DTST", "DBTYP"]
            values = [cache_id, report_id, username, row_limit, dataset_blob, source_db_type]
            self._execute_insert(cursor, tables["DMS_RPRT_PRVW_CCH"], columns, values, db_type)
            self._commit(conn)
        except Exception as exc:
            self._rollback(conn)
            error(f"[ReportMetadataService] Failed to persist preview cache: {exc}", exc_info=True)
        finally:
            self._close_connection(conn, cursor)

    def _serialize_dataset(self, rows: List[Dict[str, Any]]) -> bytes:
        payload = json.dumps(rows, default=self._json_serializer)
        return payload.encode("utf-8")

    def _json_serializer(self, value: Any):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return str(value)

    def _clamp_preview_limit(self, limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError):
            value = MAX_PREVIEW_ROWS
        return max(1, min(value, MAX_PREVIEW_ROWS))

    # ------------------------------------------------------------------
    # Schedule & execution helpers
    # ------------------------------------------------------------------
    def list_sql_sources(self) -> List[Dict[str, Any]]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            query = f"""
                SELECT MAPRSQLID AS sql_id, MAPRSQLCD AS sql_code, SQLCONID AS connection_id
                FROM {tables['DMS_MAPRSQL']}
                WHERE CURFLG = 'Y'
                ORDER BY MAPRSQLCD
            """
            self._execute(cursor, query)
            rows = self._fetch_all_dict(cursor)
            return [
                {
                    "id": self._to_int(row.get("sql_id")),
                    "code": row.get("sql_code"),
                    "connectionId": self._to_int(row.get("connection_id")),
                }
                for row in rows
            ]
        finally:
            self._close_connection(conn, cursor)

    def describe_sql_columns(self, sql_text: Optional[str], db_connection_id: Optional[int]) -> Dict[str, Any]:
        if not sql_text or not str(sql_text).strip():
            raise ReportServiceError("sqlText is required", code="SQL_TEXT_REQUIRED")
        connection_id = self._to_int(db_connection_id)
        columns = self._introspect_query_columns(sql_text, connection_id)
        return {"columns": columns}

    def list_schedules(self) -> List[Dict[str, Any]]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            query = f"""
                SELECT
                    s.SCHDID AS schedule_id,
                    s.RPRTID AS report_id,
                    r.RPRTNM AS report_name,
                    s.FRQNCY AS frequency,
                    s.TM_PRM AS time_param,
                    s.NXT_RUN_DT AS next_run_dt,
                    s.LST_RUN_DT AS last_run_dt,
                    s.STTS AS status,
                    s.OTPT_FMT AS output_format,
                    s.DSTN_TYP AS destination_type,
                    s.EMAL_TO AS email_to,
                    s.FL_PTH AS file_path,
                    s.QUE_REQ_ID AS queue_request_id
                FROM {tables['DMS_RPRT_SCHD']} s
                JOIN {tables['DMS_RPRT_DEF']} r ON r.RPRTID = s.RPRTID
                WHERE r.CURFLG = 'Y'
                ORDER BY s.SCHDID DESC
            """
            self._execute(cursor, query)
            rows = self._fetch_all_dict(cursor)
            return [self._serialize_schedule_row(row) for row in rows]
        finally:
            self._close_connection(conn, cursor)

    def create_schedule(self, payload: Dict[str, Any], username: str) -> Dict[str, Any]:
        report_id = self._to_int(payload.get("reportId"))
        if not report_id:
            raise ReportServiceError("reportId is required", code="REPORT_ID_REQUIRED")
        frequency = (payload.get("frequency") or "DAILY").upper()
        time_param = payload.get("timeParam") or ""
        status = (payload.get("status") or "ACTIVE").upper()
        output_format = (payload.get("outputFormat") or "").upper() or None
        destination = (payload.get("destination") or "").upper() or None
        email_to = payload.get("email") or None
        file_path = payload.get("filePath") or None
        
        # Calculate next run based on time_param
        next_run_dt = self._calculate_next_run(frequency, time_param)

        conn, cursor, db_type, tables = self._open_connection()
        try:
            schedule_id = self._next_id(cursor, "DMS_RPRT_SCHD_SEQ")
            now = datetime.utcnow()
            columns = [
                "SCHDID",
                "RPRTID",
                "FRQNCY",
                "TM_PRM",
                "NXT_RUN_DT",
                "LST_RUN_DT",
                "STTS",
                "OTPT_FMT",
                "DSTN_TYP",
                "EMAL_TO",
                "FL_PTH",
                "QUE_REQ_ID",
                "CRTDDT",
                "UPDTDT",
            ]
            values = [
                schedule_id,
                report_id,
                frequency,
                time_param if time_param else None,
                next_run_dt,
                None,
                status,
                output_format,
                destination,
                email_to,
                file_path,
                None,
                now,
                now,
            ]
            self._execute_insert(cursor, tables["DMS_RPRT_SCHD"], columns, values, db_type)
            self._commit(conn)
            return self._serialize_schedule_row(
                {
                    "schedule_id": schedule_id,
                    "report_id": report_id,
                    "report_name": payload.get("reportName"),
                    "frequency": frequency,
                    "time_param": time_param,
                    "next_run_dt": next_run_dt,
                    "last_run_dt": None,
                    "status": status,
                    "output_format": output_format,
                    "destination_type": destination,
                    "email_to": email_to,
                    "file_path": file_path,
                    "queue_request_id": None,
                }
            )
        except Exception as exc:
            self._rollback(conn)
            if isinstance(exc, ReportServiceError):
                raise
            raise ReportServiceError("Failed to create report schedule") from exc
        finally:
            self._close_connection(conn, cursor)

    def update_schedule(self, schedule_id: int, payload: Dict[str, Any], username: str) -> Dict[str, Any]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            if not self._schedule_exists(cursor, tables, db_type, schedule_id):
                raise ReportServiceError("Schedule not found", status_code=404, code="SCHEDULE_NOT_FOUND")

            builder = _ParamBuilder(db_type)
            set_clauses = []
            freq = None
            time_param = None
            
            if "frequency" in payload:
                freq = (payload.get("frequency") or "DAILY").upper()
                set_clauses.append(f"FRQNCY = {builder.add(freq, 'freq')}")
            if "timeParam" in payload:
                time_param = payload.get("timeParam") or ""
                set_clauses.append(f"TM_PRM = {builder.add(time_param if time_param else None, 'tmprm')}")
            if "status" in payload:
                status = (payload.get("status") or "ACTIVE").upper()
                set_clauses.append(f"STTS = {builder.add(status, 'status')}")
            if "outputFormat" in payload:
                output_format = (payload.get("outputFormat") or "").upper() or None
                set_clauses.append(f"OTPT_FMT = {builder.add(output_format, 'otpt')}")
            if "destination" in payload:
                destination = (payload.get("destination") or "").upper() or None
                set_clauses.append(f"DSTN_TYP = {builder.add(destination, 'dstn')}")
            if "email" in payload:
                email_to = payload.get("email") or None
                set_clauses.append(f"EMAL_TO = {builder.add(email_to, 'email')}")
            if "filePath" in payload:
                file_path = payload.get("filePath") or None
                set_clauses.append(f"FL_PTH = {builder.add(file_path, 'flpth')}")
            
            # Recalculate next run if frequency or timeParam changed
            if freq or time_param is not None:
                # Get current schedule to fill in missing values
                current = self._get_schedule(cursor, tables, db_type, schedule_id)
                actual_freq = freq or current.get("frequency", "DAILY")
                actual_time_param = time_param if time_param is not None else current.get("timeParam", "")
                next_run = self._calculate_next_run(actual_freq, actual_time_param)
                set_clauses.append(f"NXT_RUN_DT = {builder.add(next_run, 'nextrun')}")
            elif "nextRunAt" in payload:
                next_run = self._parse_datetime(payload.get("nextRunAt"))
                set_clauses.append(f"NXT_RUN_DT = {builder.add(next_run, 'nextrun')}")

            if not set_clauses:
                raise ReportServiceError("No fields provided to update schedule", code="NO_FIELDS_TO_UPDATE")

            timestamp_placeholder = builder.add(datetime.utcnow(), "updt")
            set_clauses.append(f"UPDTDT = {timestamp_placeholder}")
            where_placeholder = builder.add(schedule_id, "schdid")
            query = f"""
                UPDATE {tables['DMS_RPRT_SCHD']}
                SET {', '.join(set_clauses)}
                WHERE SCHDID = {where_placeholder}
            """
            self._execute(cursor, query, builder.params)
            self._commit(conn)
            return self._get_schedule(cursor, tables, db_type, schedule_id)
        except Exception as exc:
            self._rollback(conn)
            if isinstance(exc, ReportServiceError):
                raise
            raise ReportServiceError("Failed to update schedule") from exc
        finally:
            self._close_connection(conn, cursor)

    def _normalize_output_formats(self, formats: Optional[List[str]]) -> List[str]:
        normalized: List[str] = []
        for fmt in formats or []:
            token = (fmt or "").strip().upper()
            if token:
                normalized.append(token)
        if not normalized:
            normalized = ["CSV"]
        # Preserve order but drop duplicates
        deduped = []
        for fmt in normalized:
            if fmt not in deduped:
                deduped.append(fmt)
        return deduped

    def _insert_report_run(
        self,
        cursor,
        tables,
        db_type: str,
        report_id: int,
        request_id: Optional[str],
        username: str,
        output_formats: List[str],
        parameter_payload: Optional[Dict[str, Any]],
    ) -> int:
        run_id = self._next_id(cursor, "DMS_RPRT_RUN_SEQ")
        payload_wrapper = {
            "params": parameter_payload or {},
            "message": None,
        }
        columns = [
            "RUNID",
            "RPRTID",
            "RQST_ID",
            "STRT_DT",
            "STTS",
            "TRGGRD_BY",
            "OTPT_FMT",
            "PRM_OVRRDS",
        ]
        # Use local server time for STRT_DT so it aligns with CRTDDT / schedule timestamps
        now = datetime.now()
        values = [
            run_id,
            report_id,
            request_id,
            now,
            "RUNNING",
            username,
            self._serialize_formats(output_formats),
            json.dumps(payload_wrapper, default=str),
        ]
        self._execute_insert(cursor, tables["DMS_RPRT_RUN"], columns, values, db_type)
        return run_id

    def _update_report_run_status(
        self,
        cursor,
        tables,
        db_type: str,
        run_id: int,
        status: str,
        row_count: Optional[int],
        message: Optional[str],
    ):
        builder = _ParamBuilder(db_type)
        # Use local server time for END_DT/UPDTDT so they align with STRT_DT/CRTDDT
        now = datetime.now()
        set_clauses = [
            f"STTS = {builder.add(status, 'status')}",
            f"END_DT = {builder.add(now, 'enddt')}",
            f"UPDTDT = {builder.add(now, 'updt')}",
        ]
        if row_count is not None:
            set_clauses.append(f"ROW_CNT = {builder.add(row_count, 'rowcnt')}")
        if message is not None:
            payload_wrapper = self._merge_run_payload(cursor, tables, db_type, run_id, message)
            set_clauses.append(f"PRM_OVRRDS = {builder.add(json.dumps(payload_wrapper, default=str), 'msg')}")
        run_placeholder = builder.add(run_id, "runid")
        query = f"""
            UPDATE {tables['DMS_RPRT_RUN']}
            SET {', '.join(set_clauses)}
            WHERE RUNID = {run_placeholder}
        """
        self._execute(cursor, query, builder.params)

    def _generate_outputs(
        self,
        cursor,
        tables,
        db_type: str,
        report: Dict[str, Any],
        run_id: int,
        dataset: Dict[str, Any],
        output_formats: List[str],
    ) -> List[Dict[str, Any]]:
        output_dir = REPORT_OUTPUT_BASE / f"report_{report['reportId']}" / f"run_{run_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: List[Dict[str, Any]] = []
        for fmt in output_formats:
            writer = self._get_output_writer(fmt)
            file_path = writer(output_dir, dataset["columns"], dataset["rows"])
            metadata = self._insert_report_output_record(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                run_id=run_id,
                fmt=fmt,
                file_path=file_path,
            )
            outputs.append(metadata)
        return outputs

    def _get_output_writer(self, fmt: str):
        mapping = {
            "CSV": self._write_csv,
            "TXT": self._write_txt,
            "JSON": self._write_json,
            "XML": self._write_xml,
            "EXCEL": self._write_excel,
            "XLSX": self._write_excel,
            "PDF": self._write_pdf,
            "PARQUET": self._write_parquet,
        }
        writer = mapping.get(fmt.upper())
        if not writer:
            raise ReportServiceError(f"Unsupported output format '{fmt}'", code="UNSUPPORTED_FORMAT")
        return writer

    def _write_csv(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col) for col in columns})
        return file_path

    def _write_txt(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.txt"
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write("|".join(columns) + "\n")
            for row in rows:
                values = ["" if row.get(col) is None else str(row.get(col)) for col in columns]
                handle.write("|".join(values) + "\n")
        return file_path

    def _write_json(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.json"
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, default=self._json_serializer, ensure_ascii=False, indent=2)
        return file_path

    def _write_xml(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.xml"
        root = Element("Report")
        for row in rows:
            row_element = SubElement(root, "Row")
            for col in columns:
                col_element = SubElement(row_element, col.replace(" ", "_"))
                value = row.get(col)
                col_element.text = "" if value is None else str(value)
        ElementTree(root).write(file_path, encoding="utf-8", xml_declaration=True)
        return file_path

    def _write_excel(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.xlsx"
        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise ReportServiceError("Excel output requires openpyxl to be installed", code="MISSING_DEPENDENCY") from exc
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(columns)
        for row in rows:
            sheet.append([row.get(col) for col in columns])
        workbook.save(file_path)
        return file_path

    def _write_pdf(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.pdf"
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise ReportServiceError("PDF output requires reportlab to be installed", code="MISSING_DEPENDENCY") from exc
        c = canvas.Canvas(str(file_path), pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, " | ".join(columns))
        y -= 20
        c.setFont("Helvetica", 9)
        for row in rows:
            line = " | ".join("" if row.get(col) is None else str(row.get(col)) for col in columns)
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line[:180])
            y -= 18
        c.save()
        return file_path

    def _write_parquet(self, output_dir: Path, columns: List[str], rows: List[Dict[str, Any]]) -> Path:
        file_path = output_dir / "report.parquet"
        try:
            import pandas as pd
        except ImportError as exc:
            raise ReportServiceError(
                "Parquet output requires pandas and pyarrow to be installed",
                code="MISSING_DEPENDENCY",
            ) from exc
        df = pd.DataFrame(rows, columns=columns)
        try:
            df.to_parquet(file_path, index=False)
        except Exception as exc:
            raise ReportServiceError("Failed to write Parquet file", code="OUTPUT_WRITE_FAILED") from exc
        return file_path

    def _insert_report_output_record(
        self,
        cursor,
        tables,
        db_type: str,
        run_id: int,
        fmt: str,
        file_path: Path,
    ) -> Dict[str, Any]:
        output_id = self._next_id(cursor, "DMS_RPRT_OTPT_SEQ")
        rel_path = os.path.relpath(file_path, REPORT_OUTPUT_BASE)
        file_size = file_path.stat().st_size
        checksum = self._hash_file(file_path)
        columns = ["OTPTID", "RUNID", "FMT", "STRG_TYP", "STRG_REF", "FLSZ", "CHCKSM"]
        values = [
            output_id,
            run_id,
            fmt.upper(),
            "FILESYSTEM",
            rel_path.replace("\\", "/"),
            file_size,
            checksum,
        ]
        self._execute_insert(cursor, tables["DMS_RPRT_OTPT"], columns, values, db_type)
        return {
            "outputId": output_id,
            "format": fmt.upper(),
            "path": str(file_path),
            "size": file_size,
            "checksum": checksum,
        }

    def _hash_file(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _fail_report_run(self, run_id: int, message: str):
        conn, cursor, db_type, tables = self._open_connection()
        try:
            self._update_report_run_status(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                run_id=run_id,
                status="FAILED",
                row_count=None,
                message=message,
            )
            self._commit(conn)
        finally:
            self._close_connection(conn, cursor)

    def _merge_run_payload(self, cursor, tables, db_type: str, run_id: int, message: Optional[str]):
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(run_id, "rid")
        query = f"""
            SELECT PRM_OVRRDS
            FROM {tables['DMS_RPRT_RUN']}
            WHERE RUNID = {placeholder}
        """
        self._execute(cursor, query, builder.params)
        row = cursor.fetchone()
        existing = {}
        if row and row[0] is not None:
            existing = self._load_json(self._read_lob(row[0])) or {}
        params = {}
        if isinstance(existing, dict):
            params = existing.get("params") or existing.get("parameters") or {}
        return {"params": params, "message": message}

    # ------------------------------------------------------------------
    # Run listing helpers
    # ------------------------------------------------------------------
    def list_runs(self, report_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn, cursor, db_type, tables = self._open_connection()
        try:
            builder = _ParamBuilder(db_type)
            query = f"""
                SELECT
                    RUNID AS run_id,
                    RPRTID AS report_id,
                    RQST_ID AS request_id,
                    STRT_DT AS start_dt,
                    END_DT AS end_dt,
                    STTS AS status,
                    TRGGRD_BY AS triggered_by,
                    ROW_CNT AS row_cnt,
                    OTPT_FMT AS output_formats,
                    PRM_OVRRDS AS param_overrides
                FROM {tables['DMS_RPRT_RUN']}
            """
            conditions = []
            if report_id is not None:
                conditions.append(f"RPRTID = {builder.add(report_id, 'rpt')}")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY RUNID DESC"
            if db_type == "POSTGRESQL":
                query += f" LIMIT {limit}"
            else:
                query = f"SELECT * FROM ({query}) WHERE ROWNUM <= {limit}"
            self._execute(cursor, query, builder.params)
            rows = self._fetch_all_dict(cursor)
            results = []
            for row in rows:
                payload = self._load_json(self._read_lob(row.get("param_overrides")))
                params = payload.get("params") if isinstance(payload, dict) else payload
                message = payload.get("message") if isinstance(payload, dict) else None
                results.append({
                    "runId": self._to_int(row.get("run_id")),
                    "reportId": self._to_int(row.get("report_id")),
                    "requestId": row.get("request_id"),
                    "startAt": self._to_iso(row.get("start_dt")),
                    "endAt": self._to_iso(row.get("end_dt")),
                    "status": (row.get("status") or "").upper(),
                    "triggeredBy": row.get("triggered_by"),
                    "rowCount": self._to_int(row.get("row_cnt")),
                    "outputFormats": self._deserialize_csv(row.get("output_formats")),
                    "parameters": params,
                    "message": message,
                })
            return results
        finally:
            self._close_connection(conn, cursor)

    def record_external_run(
        self,
        report_id: int,
        output_formats: List[str],
        row_count: int,
        username: str = "system",
        request_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> int:
        """
        Record a report run that was executed by an external component (e.g. scheduler).

        This creates a row in DMS_RPRT_RUN so that the run appears in the report runs UI.
        """
        conn, cursor, db_type, tables = self._open_connection()
        try:
            # Normalise formats using the same rules as execute_report
            normalized_formats = self._normalize_output_formats(output_formats)
            run_id = self._insert_report_run(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                report_id=report_id,
                request_id=request_id,
                username=username,
                output_formats=normalized_formats,
                parameter_payload=parameters,
            )

            # Immediately mark as completed with the provided row count/message
            self._update_report_run_status(
                cursor=cursor,
                tables=tables,
                db_type=db_type,
                run_id=run_id,
                status="SUCCESS",
                row_count=row_count,
                message=message,
            )
            self._commit(conn)
            return run_id
        finally:
            self._close_connection(conn, cursor)

    def _serialize_schedule_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "scheduleId": self._to_int(row.get("schedule_id")),
            "reportId": self._to_int(row.get("report_id")),
            "reportName": row.get("report_name"),
            "frequency": (row.get("frequency") or "").upper(),
            "timeParam": row.get("time_param") or "",
            "nextRunAt": self._to_iso(row.get("next_run_dt")),
            "lastRunAt": self._to_iso(row.get("last_run_dt")),
            "status": (row.get("status") or "").upper(),
            "outputFormat": (row.get("output_format") or "").upper() or None,
            "destination": (row.get("destination_type") or "").upper() or None,
            "email": row.get("email_to"),
            "filePath": row.get("file_path"),
            "queueRequestId": row.get("queue_request_id"),
        }

    def _schedule_exists(self, cursor, tables, db_type: str, schedule_id: int) -> bool:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(schedule_id, "schdid")
        query = f"SELECT 1 FROM {tables['DMS_RPRT_SCHD']} WHERE SCHDID = {placeholder}"
        self._execute(cursor, query, builder.params)
        return bool(cursor.fetchone())

    def _get_schedule(self, cursor, tables, db_type: str, schedule_id: int) -> Dict[str, Any]:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(schedule_id, "schdid")
        query = f"""
            SELECT
                s.SCHDID AS schedule_id,
                s.RPRTID AS report_id,
                r.RPRTNM AS report_name,
                s.FRQNCY AS frequency,
                s.TM_PRM AS time_param,
                s.NXT_RUN_DT AS next_run_dt,
                s.LST_RUN_DT AS last_run_dt,
                s.STTS AS status,
                s.QUE_REQ_ID AS queue_request_id
            FROM {tables['DMS_RPRT_SCHD']} s
            JOIN {tables['DMS_RPRT_DEF']} r ON r.RPRTID = s.RPRTID
            WHERE s.SCHDID = {placeholder}
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        if not rows:
            raise ReportServiceError("Schedule not found", status_code=404, code="SCHEDULE_NOT_FOUND")
        return self._serialize_schedule_row(rows[0])

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        try:
            text = str(value).strip()
            if text.endswith("Z"):
                text = text[:-1]
            return datetime.fromisoformat(text)
        except Exception:
            return None

    def _calculate_next_run(self, frequency: str, time_param: str) -> datetime:
        """
        Calculate next run datetime based on frequency and time_param.
        time_param format: "DL_09:00", "WK_MON_14:30", "MN_15_10:00"
        """
        now = datetime.utcnow()
        hour, minute = 0, 0
        day_of_week = None  # 0=Monday, 6=Sunday
        day_of_month = None
        
        # Parse time_param if provided
        if time_param:
            parts = time_param.split("_")
            # Find time part (HH:MM format)
            for part in parts:
                if ":" in part:
                    try:
                        time_parts = part.split(":")
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                    except (ValueError, IndexError):
                        pass
                elif part in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                    day_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
                    day_of_week = day_map.get(part)
                elif part.isdigit():
                    day_of_month = int(part)
        
        freq = frequency.upper()
        
        if freq == "DAILY" or freq == "DL":
            # Next occurrence at specified time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
            
        elif freq == "WEEKLY" or freq == "WK":
            # Next occurrence on specified day at specified time
            if day_of_week is None:
                day_of_week = 0  # Default to Monday
            days_ahead = day_of_week - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
            if next_run <= now:
                next_run += timedelta(days=7)
            return next_run
            
        elif freq == "MONTHLY" or freq == "MN":
            # Next occurrence on specified day of month at specified time
            if day_of_month is None:
                day_of_month = 1  # Default to 1st
            # Try current month first
            try:
                next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                # Day doesn't exist in current month, use last day
                import calendar
                last_day = calendar.monthrange(now.year, now.month)[1]
                next_run = now.replace(day=min(day_of_month, last_day), hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                try:
                    next_run = next_run.replace(year=next_year, month=next_month, day=day_of_month)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    next_run = next_run.replace(year=next_year, month=next_month, day=min(day_of_month, last_day))
            return next_run
        
        # Default: run immediately
        return now


    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _insert_report_definition(self, cursor, tables, db_type, report_id, data, checksum, username, final_sql):
        columns = [
            "RPRTID", "RPRTNM", "DSCRPTN", "SQLSRCID", "ADHCSQL", "FINAL_SQL", "DBCNID",
            "DFLT_OTPT_FMT", "SPPRTD_FMTS", "PRVW_RW_LMT", "IS_ACTV",
            "CURFLG", "CHCKSM", "CRTDBY", "UPDTDBY"
        ]
        values = [
            report_id,
            data["reportName"],
            data.get("description"),
            data.get("sqlSourceId"),
            data.get("adhocSql"),
            final_sql,
            data.get("dbConnectionId"),
            data["defaultOutputFormat"],
            self._serialize_formats(data.get("supportedFormats", [])),
            data["previewRowLimit"],
            self._to_flag(data.get("isActive", True)),
            "Y",
            checksum,
            username,
            username,
        ]
        self._execute_insert(cursor, tables["DMS_RPRT_DEF"], columns, values, db_type)

    def _update_report_definition(self, cursor, tables, db_type, report_id, data, checksum, username, final_sql):
        builder = _ParamBuilder(db_type)
        set_clauses = []
        for column, value in [
            ("RPRTNM", data["reportName"]),
            ("DSCRPTN", data.get("description")),
            ("SQLSRCID", data.get("sqlSourceId")),
            ("ADHCSQL", data.get("adhocSql")),
            ("FINAL_SQL", final_sql),
            ("DBCNID", data.get("dbConnectionId")),
            ("DFLT_OTPT_FMT", data["defaultOutputFormat"]),
            ("SPPRTD_FMTS", self._serialize_formats(data.get("supportedFormats", []))),
            ("PRVW_RW_LMT", data["previewRowLimit"]),
            ("IS_ACTV", self._to_flag(data.get("isActive", True))),
            ("CHCKSM", checksum),
            ("UPDTDBY", username),
        ]:
            placeholder = builder.add(value, column.lower())
            set_clauses.append(f"{column} = {placeholder}")

        timestamp_expr = "SYSTIMESTAMP" if db_type == "ORACLE" else "CURRENT_TIMESTAMP"
        set_clauses.append(f"UPDTDT = {timestamp_expr}")

        id_placeholder = builder.add(report_id, "report_id")
        query = f"""
            UPDATE {tables['DMS_RPRT_DEF']}
            SET {', '.join(set_clauses)}
            WHERE RPRTID = {id_placeholder}
        """
        self._execute(cursor, query, builder.params)

    def _persist_formulas(self, cursor, tables, db_type, report_id, formulas, username) -> Dict[str, int]:
        id_map: Dict[str, int] = {}
        for formula in formulas:
            formula_id = self._next_id(cursor, "DMS_RPRT_FRML_SEQ")
            columns = ["FRMLA_ID", "RPRTID", "NM", "XPRSN", "SPPRTD_DB_TYP", "HLP_TXT"]
            values = [
                formula_id,
                report_id,
                formula.get("name"),
                formula.get("expression"),
                self._serialize_formats(self._normalize_list(formula.get("supportedDbTypes"))),
                formula.get("helpText"),
            ]
            self._execute_insert(cursor, tables["DMS_RPRT_FRML"], columns, values, db_type)
            reference_key = formula.get("name") or formula.get("tempId")
            if reference_key:
                id_map[str(reference_key)] = formula_id
        return id_map

    def _persist_fields(self, cursor, tables, db_type, report_id, fields, formula_map):
        self._ensure_grouping_columns(cursor, tables, db_type)
        grp_col, seq_col, dir_col = self._grouping_column_names(db_type)
        for index, field in enumerate(fields):
            field_id = self._next_id(cursor, "DMS_RPRT_FLD_SEQ")
            panel_type = (field.get("panelType") or "DETAIL").upper()
            row_order = field.get("rowOrder", index + 1)
            formula_id = self._resolve_formula_id(field, formula_map)
            columns = [
                "FLDID", "RPRTID", "PNL_TYP", "ROW_ORDR", "FLD_NM", "FLD_ALS",
                "SRC_CLMN", "FRMLA_ID", "FRMLA_INLN", "DT_TYP", "FMT_MASK",
                "IS_VSBL", grp_col, seq_col, dir_col, "NOTES"
            ]
            values = [
                field_id,
                report_id,
                panel_type,
                row_order,
                field.get("fieldName"),
                field.get("fieldAlias"),
                field.get("sourceColumn"),
                formula_id,
                field.get("inlineFormula"),
                field.get("dataType"),
                field.get("formatMask"),
                self._to_flag(field.get("isVisible", True)),
                self._to_flag(field.get("isGroupBy", False)),
                field.get("orderBySeq"),
                field.get("orderByDir"),
                field.get("notes"),
            ]
            self._execute_insert(cursor, tables["DMS_RPRT_FLD"], columns, values, db_type)

    def _persist_layout(self, cursor, tables, db_type, report_id, layout):
        if not layout:
            return
        self._delete_layout(cursor, tables, db_type, report_id)
        layout_id = self._next_id(cursor, "DMS_RPRT_LYOT_SEQ")
        columns = ["LYOTID", "RPRTID", "HDR_TMPLT", "DTL_TMPLT", "PRVW_STTNGS"]
        values = [
            layout_id,
            report_id,
            self._dump_json(layout.get("headerTemplate")),
            self._dump_json(layout.get("detailTemplate")),
            self._dump_json(layout.get("previewSettings")),
        ]
        self._execute_insert(cursor, tables["DMS_RPRT_LYOT"], columns, values, db_type)

    def _delete_children(self, cursor, tables, db_type, report_id):
        for table in ("DMS_RPRT_FLD", "DMS_RPRT_FRML", "DMS_RPRT_LYOT"):
            builder = _ParamBuilder(db_type)
            placeholder = builder.add(report_id, "rid")
            query = f"DELETE FROM {tables[table]} WHERE RPRTID = {placeholder}"
            self._execute(cursor, query, builder.params)

    def _delete_layout(self, cursor, tables, db_type, report_id):
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "rid")
        query = f"DELETE FROM {tables['DMS_RPRT_LYOT']} WHERE RPRTID = {placeholder}"
        self._execute(cursor, query, builder.params)

    # ------------------------------------------------------------------
    # Validation & normalization
    # ------------------------------------------------------------------
    def _normalize_payload(self, payload: Dict[str, Any], is_update: bool) -> Dict[str, Any]:
        if not payload:
            raise ReportServiceError("Request body is required")

        report_name = (payload.get("reportName") or "").strip()
        if not report_name:
            raise ReportServiceError("Report name is required", code="REPORT_NAME_REQUIRED")

        sql_source_id = payload.get("sqlSourceId")
        adhoc_sql = payload.get("adhocSql")
        db_connection_id = payload.get("dbConnectionId")

        if not sql_source_id and not adhoc_sql:
            raise ReportServiceError("Either sqlSourceId or adhocSql must be provided", code="SQL_SOURCE_REQUIRED")
        if adhoc_sql and not db_connection_id:
            raise ReportServiceError("dbConnectionId is required when adhocSql is provided", code="DB_CONNECTION_REQUIRED")

        default_format = (payload.get("defaultOutputFormat") or "CSV").upper()
        supported_formats = self._normalize_list(payload.get("supportedFormats")) or [default_format]
        preview_limit = payload.get("previewRowLimit") or 100
        preview_limit = max(1, min(int(preview_limit), MAX_PREVIEW_ROWS))

        normalized = {
            "reportName": report_name,
            "description": payload.get("description"),
            "sqlSourceId": self._to_int(sql_source_id),
            "adhocSql": adhoc_sql,
            "dbConnectionId": self._to_int(db_connection_id),
            "defaultOutputFormat": default_format,
            "supportedFormats": [fmt.upper() for fmt in supported_formats],
            "previewRowLimit": preview_limit,
            "isActive": bool(payload.get("isActive", True)),
            "fields": self._normalize_fields_payload(payload.get("fields", [])),
            "formulas": payload.get("formulas", []),
            "layout": payload.get("layout"),
        }

        self._validate_fields_for_grouping(normalized["fields"])

        return normalized

    def _normalize_fields_payload(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized_fields: List[Dict[str, Any]] = []
        for field in fields or []:
            normalized_field = dict(field)
            normalized_field["isGroupBy"] = bool(field.get("isGroupBy"))
            order_seq = self._to_int(field.get("orderBySeq"))
            normalized_field["orderBySeq"] = order_seq
            order_dir = (field.get("orderByDir") or "ASC").upper()
            if order_dir not in ("ASC", "DESC"):
                order_dir = "ASC"
            normalized_field["orderByDir"] = order_dir if order_seq is not None else None
            normalized_fields.append(normalized_field)
        return normalized_fields

    def _ensure_grouping_columns(self, cursor, tables, db_type: str):
        table_ref = tables["DMS_RPRT_FLD"]
        cache_key = (db_type, table_ref)
        if self._grouping_columns_verified.get(cache_key):
            return
        grp_col, seq_col, dir_col = self._grouping_column_names(db_type)
        if db_type == "ORACLE":
            test_query = f"SELECT {grp_col}, {seq_col}, {dir_col} FROM {table_ref} WHERE ROWNUM = 0"
        else:
            test_query = f"SELECT {grp_col}, {seq_col}, {dir_col} FROM {table_ref} WHERE 1=0"
        try:
            self._execute(cursor, test_query)
        except Exception as exc:  # pragma: no cover
            message = (
                "Report metadata table DMS_RPRT_FLD is missing the grouping columns "
                "(IS_GRP_BY, ORDER_BY_SEQ, ORDER_BY_DIR). "
                "Apply doc/database_migration_add_report_field_grouping.sql and retry."
            )
            raise ReportServiceError(message, code="MISSING_GROUPING_COLUMNS") from exc
        self._grouping_columns_verified[cache_key] = True

    def _grouping_column_names(self, db_type: str) -> Tuple[str, str, str]:
        if (db_type or "").upper() == "POSTGRESQL":
            return "is_group_by", "order_by_seq", "order_by_dir"
        return "IS_GRP_BY", "ORDER_BY_SEQ", "ORDER_BY_DIR"

    def _validate_fields_for_grouping(self, fields: List[Dict[str, Any]]):
        detail_fields = [
            field for field in fields
            if (field.get("panelType") or "DETAIL").upper() == "DETAIL"
        ]
        if not detail_fields:
            return
        has_group_by = any(field.get("isGroupBy") for field in detail_fields)
        if not has_group_by:
            return
        violations = []
        for field in detail_fields:
            if field.get("isGroupBy"):
                continue
            inline_formula = (field.get("inlineFormula") or "").strip()
            has_formula = bool(inline_formula) or bool(field.get("formulaId"))
            if not has_formula:
                violations.append(field.get("fieldName") or field.get("fieldAlias") or "Unnamed field")
        if violations:
            raise ReportServiceError(
                "When using Group By, each non-grouped field must specify an aggregate formula.",
                code="GROUP_BY_REQUIRES_FORMULA",
                details={"fields": violations},
            )

    def _map_report_summary(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "reportId": self._to_int(row.get("report_id")),
            "reportName": row.get("report_name"),
            "description": row.get("description"),
            "sqlSourceId": self._to_int(row.get("sql_source_id")),
            "adhocSql": self._read_lob(row.get("adhoc_sql")),
            "dbConnectionId": self._to_int(row.get("db_connection_id")),
            "defaultOutputFormat": (row.get("default_output_format") or "").upper(),
            "supportedFormats": self._deserialize_csv(row.get("supported_formats")),
            "previewRowLimit": self._to_int(row.get("preview_row_limit")),
            "isActive": self._from_flag(row.get("is_active")),
            "hasActiveSchedule": (self._to_int(row.get("active_schedule_count")) or 0) > 0,
            "createdAt": self._to_iso(row.get("created_at")),
            "updatedAt": self._to_iso(row.get("updated_at")),
            "finalSql": self._read_lob(row.get("final_sql")),
            "scheduleId": None,
            "scheduleFrequency": None,
            "scheduleStatus": None,
            "scheduleNextRun": None,
        }

    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        payload = {
            "definition": {
                "reportName": data["reportName"],
                "description": data.get("description"),
                "sqlSourceId": data.get("sqlSourceId"),
                "adhocSql": data.get("adhocSql"),
                "dbConnectionId": data.get("dbConnectionId"),
                "defaultOutputFormat": data["defaultOutputFormat"],
                "supportedFormats": sorted(data.get("supportedFormats", [])),
                "previewRowLimit": data["previewRowLimit"],
                "isActive": data.get("isActive", True),
            },
            "fields": data.get("fields", []),
            "formulas": data.get("formulas", []),
            "layout": data.get("layout"),
        }
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _deserialize_csv(self, value: Optional[str]) -> List[str]:
        if not value:
            return []
        items = [token.strip() for token in value.replace("|", ",").split(",")]
        return [item.upper() for item in items if item]

    def _serialize_formats(self, formats: Optional[List[str]]) -> Optional[str]:
        if not formats:
            return None
        unique = sorted({fmt.upper() for fmt in formats if fmt})
        return ",".join(unique)

    def _normalize_list(self, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [token.strip() for token in value.split(",") if token.strip()]
        return [str(value).strip()]

    def _read_lob(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "read"):
            return value.read()
        return str(value)

    def _load_json(self, value: Optional[str]) -> Any:
        if not value:
            return None
        with suppress(json.JSONDecodeError, TypeError):
            return json.loads(value)
        return None

    def _dump_json(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    def _to_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return int(value)
        with suppress(ValueError, TypeError):
            return int(value)
        return None

    def _to_iso(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _to_flag(self, value: Any) -> str:
        return "Y" if str(value).lower() in ("true", "1", "y", "yes") else "N"

    def _from_flag(self, value: Any) -> bool:
        if value is None:
            return False
        return str(value).upper() == "Y"

    def _has_active_schedule(self, cursor, tables, db_type, report_id: int) -> bool:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "sched")
        query = f"""
            SELECT COUNT(1) AS active_count
            FROM {tables['DMS_RPRT_SCHD']}
            WHERE RPRTID = {placeholder}
              AND UPPER(COALESCE(STTS, '')) IN ('ACTIVE', 'QUEUED', 'SCHEDULED')
        """
        self._execute(cursor, query, builder.params)
        rows = self._fetch_all_dict(cursor)
        if not rows:
            return False
        return (self._to_int(rows[0].get("active_count")) or 0) > 0

    def _report_exists(self, cursor, tables, db_type, report_id: int) -> bool:
        builder = _ParamBuilder(db_type)
        placeholder = builder.add(report_id, "exists")
        query = f"SELECT 1 FROM {tables['DMS_RPRT_DEF']} WHERE RPRTID = {placeholder}"
        self._execute(cursor, query, builder.params)
        return bool(cursor.fetchone())

    def _next_id(self, cursor, sequence_name: str) -> int:
        try:
            return next_id(cursor, sequence_name)
        except IdProviderError as exc:
            error(f"[ReportMetadataService] Failed to fetch ID for {sequence_name}: {exc}")
            raise ReportServiceError(f"Unable to generate ID for {sequence_name}", code="ID_PROVIDER_ERROR") from exc

    def _resolve_formula_id(self, field: Dict[str, Any], formula_map: Dict[str, int]) -> Optional[int]:
        if field.get("formulaId"):
            return self._to_int(field.get("formulaId"))
        ref = field.get("formulaRef")
        if ref and ref in formula_map:
            return formula_map[ref]
        return None


class FormulaEvaluator:
    """Evaluates simple arithmetic/string expressions safely."""

    SAFE_FUNCTIONS = {
        "CONCAT": lambda *args: "".join("" if arg is None else str(arg) for arg in args),
        "COALESCE": lambda *args: next((arg for arg in args if arg not in (None, "")), None),
        "SPLIT": lambda value, delimiter, index=0: (
            str(value).split(delimiter)[int(index)] if value is not None else None
        ),
        "UPPER": lambda value: value.upper() if isinstance(value, str) else (str(value).upper() if value is not None else None),
        "LOWER": lambda value: value.lower() if isinstance(value, str) else (str(value).lower() if value is not None else None),
        "ABS": lambda value: abs(float(value)) if value is not None else None,
        "ROUND": lambda value, digits=0: round(float(value), int(digits)) if value is not None else None,
        "LEN": lambda value: len(value) if value is not None else 0,
    }

    ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)
    ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)

    def evaluate(self, expression: Optional[str], context: Dict[str, Any]) -> Any:
        if expression is None:
            return None
        expr = expression.strip()
        if not expr:
            return None
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise ReportServiceError(f"Invalid formula syntax: {exc.msg}", code="FORMULA_SYNTAX_ERROR") from exc
        return self._eval_node(tree.body, context)

    def _eval_node(self, node, context):
        if isinstance(node, ast.BinOp) and isinstance(node.op, self.ALLOWED_BINOPS):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            return self._apply_binop(node.op, left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, self.ALLOWED_UNARYOPS):
            operand = self._eval_node(node.operand, context)
            return -operand if isinstance(node.op, ast.USub) else operand
        if isinstance(node, ast.Name):
            key = node.id.upper()
            return context.get(key)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):  # pragma: no cover (Python <3.8 compatibility)
            return node.n
        if isinstance(node, ast.Call):
            func_name = self._get_func_name(node.func)
            if func_name not in self.SAFE_FUNCTIONS:
                raise ReportServiceError(f"Function '{func_name}' is not allowed in formulas", code="FORMULA_FUNC_NOT_ALLOWED")
            args = [self._eval_node(arg, context) for arg in node.args]
            return self.SAFE_FUNCTIONS[func_name](*args)
        raise ReportServiceError("Unsupported expression component in formula", code="FORMULA_UNSUPPORTED_NODE")

    def _apply_binop(self, op, left, right):
        if isinstance(op, ast.Add):
            if isinstance(left, str) or isinstance(right, str):
                return ("" if left is None else str(left)) + ("" if right is None else str(right))
            return (left or 0) + (right or 0)
        if isinstance(op, ast.Sub):
            return (left or 0) - (right or 0)
        if isinstance(op, ast.Mult):
            return (left or 0) * (right or 0)
        if isinstance(op, ast.Div):
            if right in (0, None):
                return None
            return (left or 0) / right
        if isinstance(op, ast.Mod):
            if right in (0, None):
                return None
            return (left or 0) % right
        raise ReportServiceError("Unsupported arithmetic operator in formula", code="FORMULA_OPERATOR_NOT_ALLOWED")

    def _get_func_name(self, func_node):
        if isinstance(func_node, ast.Name):
            return func_node.id.upper()
        raise ReportServiceError("Only simple function names are allowed in formulas", code="FORMULA_FUNC_NOT_ALLOWED")

