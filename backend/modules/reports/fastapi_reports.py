from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

try:
    from backend.database.dbconnect import create_metadata_connection
    from backend.modules.jobs.pkgdwprc_python import (
        JobSchedulerService,
        SchedulerRepositoryError,
    )
    from backend.modules.logger import error, info
    from backend.modules.reports.report_service import (
        ReportMetadataService,
        ReportServiceError,
    )
except ImportError:  # Fallback for Flask-style imports
    from database.dbconnect import create_metadata_connection  # type: ignore
    from modules.jobs.pkgdwprc_python import (  # type: ignore
        JobSchedulerService,
        SchedulerRepositoryError,
    )
    from modules.logger import error, info  # type: ignore
    from modules.reports.report_service import (  # type: ignore
        ReportMetadataService,
        ReportServiceError,
    )


router = APIRouter(tags=["reports"])
report_service = ReportMetadataService()


def _current_username(request: Request) -> str:
    return (
        request.headers.get("X-User")
        or request.headers.get("X-USER-ID")
        or request.headers.get("X-USERNAME")
        or "system"
    )


def _handle_service_error(exc: ReportServiceError) -> JSONResponse:
    response = {
        "success": False,
        "message": exc.message,
        "code": exc.code,
        "details": exc.details,
    }
    return JSONResponse(status_code=exc.status_code, content=response)


@router.get("/reports")
async def list_reports(search: Optional[str] = None, includeInactive: str = "false"):
    include_inactive = includeInactive.lower() == "true"
    try:
        data = report_service.list_reports(
            search=search, include_inactive=include_inactive
        )
        return {"success": True, "count": len(data), "data": data}
    except ReportServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "success": False,
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive
        error(f"[reports.list_reports] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch reports"
        ) from exc


@router.get("/reports/sql-sources")
async def list_sql_sources():
    try:
        data = report_service.list_sql_sources()
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.list_sql_sources] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load SQL sources"
        ) from exc


@router.post("/reports/describe-sql")
async def describe_sql(payload: Dict[str, Any]):
    sql_text = payload.get("sqlText")
    db_connection_id = payload.get("dbConnectionId")
    try:
        data = report_service.describe_sql_columns(
            sql_text=sql_text, db_connection_id=db_connection_id
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.describe_sql] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to describe SQL"
        ) from exc


@router.get("/reports/{report_id}")
async def get_report(report_id: int):
    try:
        data = report_service.get_report(report_id)
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.get_report] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load report"
        ) from exc


@router.post("/reports", status_code=201)
async def create_report(request: Request, payload: Dict[str, Any]):
    username = _current_username(request)
    try:
        data = report_service.create_report(payload, username=username)
        info(
            f"[reports.create_report] Created report {data.get('reportId')} by {username}"
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.create_report] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to create report"
        ) from exc


@router.put("/reports/{report_id}")
async def update_report(request: Request, report_id: int, payload: Dict[str, Any]):
    username = _current_username(request)
    force_update = bool(payload.get("forceUpdate"))
    try:
        data = report_service.update_report(
            report_id, payload, username=username, force_update=force_update
        )
        info(f"[reports.update_report] Updated report {report_id} by {username}")
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.update_report] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to update report"
        ) from exc


@router.post("/reports/{report_id}/preview")
async def preview_report(request: Request, report_id: int, payload: Dict[str, Any]):
    row_limit = payload.get("rowLimit")
    parameters = payload.get("parameters") or {}
    username = _current_username(request)
    try:
        data = report_service.preview_report(
            report_id=report_id,
            row_limit=row_limit,
            parameters=parameters,
            username=username,
        )
        info(
            f"[reports.preview_report] Generated preview for report {report_id} by {username}"
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.preview_report] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate preview"
        ) from exc


@router.post("/reports/{report_id}/execute")
async def execute_report_sync(request: Request, report_id: int, payload: Dict[str, Any]):
    """
    Execute report synchronously and return file for download.
    Mirrors Flask endpoint: POST /api/reports/{id}/execute
    """
    username = _current_username(request)
    output_format = (payload.get("outputFormat") or "CSV").upper()

    info(
        f"[reports.execute_report_sync] Executing report {report_id}, format: {output_format}"
    )

    try:
        # Get report data using preview (which runs the actual query)
        result = report_service.preview_report(
            report_id=report_id,
            row_limit=None,  # No limit for actual execution
            parameters=payload.get("parameters"),
            username=username,
            allow_unbounded=True,  # Allow full data export
        )

        columns = result.get("columns", [])
        rows = result.get("rows", [])
        report = report_service.get_report(report_id)
        report_name = report.get("reportName", f"report_{report_id}")
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in report_name
        )

        # CSV Format
        if output_format == "CSV":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row.get(col, "") for col in columns])
            output_bytes = output.getvalue().encode("utf-8")
            return StreamingResponse(
                io.BytesIO(output_bytes),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_name}.csv"'
                },
            )

        # JSON Format
        if output_format == "JSON":
            json_data = json.dumps(
                {"columns": columns, "rows": rows, "rowCount": len(rows)},
                indent=2,
                default=str,
            )
            return StreamingResponse(
                io.BytesIO(json_data.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_name}.json"'
                },
            )

        # Excel Format
        if output_format == "EXCEL":
            try:
                from openpyxl import Workbook

                wb = Workbook()
                ws = wb.active
                ws.title = "Report Data"
                ws.append(columns)
                for row in rows:
                    ws.append([row.get(col, "") for col in columns])

                output = io.BytesIO()
                wb.save(output)
                output.seek(0)

                return StreamingResponse(
                    output,
                    media_type=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                    headers={
                        "Content-Disposition": f'attachment; filename="{safe_name}.xlsx"'
                    },
                )
            except ImportError:
                error(
                    "[reports.execute_report_sync] openpyxl not installed for Excel export"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Excel export requires openpyxl package. Install with: pip install openpyxl",
                )

        # PDF Format
        if output_format == "PDF":
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.platypus import (
                    SimpleDocTemplate,
                    Table,
                    TableStyle,
                    Paragraph,
                )
                from reportlab.lib.styles import getSampleStyleSheet

                output = io.BytesIO()
                doc = SimpleDocTemplate(output, pagesize=landscape(letter))
                elements = []

                styles = getSampleStyleSheet()
                elements.append(Paragraph(report_name, styles["Title"]))

                # Prepare table data
                table_data = [columns]
                for row in rows:
                    table_data.append([str(row.get(col, "")) for col in columns])

                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                elements.append(table)

                doc.build(elements)
                output.seek(0)

                return StreamingResponse(
                    output,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="{safe_name}.pdf"'
                    },
                )
            except ImportError:
                error(
                    "[reports.execute_report_sync] reportlab not installed for PDF export"
                )
                raise HTTPException(
                    status_code=400,
                    detail="PDF export requires reportlab package. Install with: pip install reportlab",
                )

        # XML Format
        if output_format == "XML":
            import xml.etree.ElementTree as ET

            root = ET.Element("report")
            root.set("name", report_name)
            root.set("rowCount", str(len(rows)))

            for idx, row in enumerate(rows):
                row_elem = ET.SubElement(root, "row")
                row_elem.set("index", str(idx + 1))
                for col in columns:
                    col_elem = ET.SubElement(
                        row_elem, col.replace(" ", "_").replace("-", "_")
                    )
                    col_elem.text = str(row.get(col, ""))

            xml_str = ET.tostring(root, encoding="unicode", method="xml")
            xml_output = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

            return StreamingResponse(
                io.BytesIO(xml_output.encode("utf-8")),
                media_type="application/xml",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_name}.xml"'
                },
            )

        # Parquet Format
        if output_format == "PARQUET":
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq

                data = {col: [row.get(col) for row in rows] for col in columns}
                table = pa.table(data)

                output = io.BytesIO()
                pq.write_table(table, output)
                output.seek(0)

                return StreamingResponse(
                    output,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f'attachment; filename="{safe_name}.parquet"'
                    },
                )
            except ImportError:
                error(
                    "[reports.execute_report_sync] pyarrow not installed for Parquet export"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Parquet export requires pyarrow package. Install with: pip install pyarrow",
                )

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported output format: {output_format}",
        )
    except ReportServiceError as exc:
        error(f"[reports.execute_report_sync] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except HTTPException:
        raise
    except Exception as exc:
        error(f"[reports.execute_report_sync] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to execute report: {str(exc)}"
        ) from exc


@router.post("/reports/{report_id}/execute-async")
async def execute_report_async(request: Request, report_id: int, payload: Dict[str, Any]):
    """
    Queue report for async execution (Email/File destinations).
    Mirrors Flask endpoint: POST /api/reports/{id}/execute-async
    """
    username = _current_username(request)
    payload.setdefault("requestedBy", username)
    payload.setdefault("outputFormat", "CSV")

    destination = (payload.get("destination") or "FILE").upper()

    if destination == "EMAIL":
        email = (payload.get("email") or "").strip()
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email address is required for EMAIL destination",
            )

    info(
        f"[reports.execute_report_async] Queueing report {report_id} for async execution, destination: {destination}"
    )

    connection = None
    try:
        connection = create_metadata_connection()
        service = JobSchedulerService(connection)
        request_id = service.queue_report_request(
            report_id=report_id, payload=payload
        )
        info(
            f"[reports.execute_report_async] Queued report {report_id} by {username}, request_id: {request_id}"
        )
        return {
            "success": True,
            "requestId": request_id,
            "message": f"Report queued for {destination.lower()} delivery",
        }
    except SchedulerRepositoryError as exc:
        error(f"[reports.execute_report_async] Scheduler error: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        error(f"[reports.execute_report_async] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to queue report: {str(exc)}"
        ) from exc
    finally:
        if connection:
            connection.close()


@router.get("/report-schedules")
async def list_report_schedules():
    try:
        data = report_service.list_schedules()
        return {"success": True, "count": len(data), "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.list_report_schedules] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load schedules"
        ) from exc


@router.post("/report-schedules")
async def create_report_schedule(request: Request, payload: Dict[str, Any]):
    username = _current_username(request)
    try:
        data = report_service.create_schedule(payload, username=username)
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        error(f"[reports.create_report_schedule] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(
            f"[reports.create_report_schedule] Unexpected error: {exc}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create schedule: {str(exc)}",
        ) from exc


@router.put("/report-schedules/{schedule_id}")
async def update_report_schedule(
    request: Request, schedule_id: int, payload: Dict[str, Any]
):
    username = _current_username(request)
    try:
        data = report_service.update_schedule(
            schedule_id, payload, username=username
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        error(f"[reports.update_report_schedule] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(
            f"[reports.update_report_schedule] Unexpected error: {exc}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update schedule: {str(exc)}",
        ) from exc


@router.delete("/report-schedules/{schedule_id}")
async def delete_report_schedule(request: Request, schedule_id: int):
    """Delete/stop a report schedule."""
    username = _current_username(request)
    try:
        data = report_service.delete_schedule(
            schedule_id, username=username
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        error(f"[reports.delete_report_schedule] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(
            f"[reports.delete_report_schedule] Unexpected error: {exc}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete schedule: {str(exc)}",
        ) from exc


@router.post("/report-schedules/{schedule_id}/stop")
async def stop_report_schedule(request: Request, schedule_id: int):
    """Stop/pause a report schedule (alias for DELETE)."""
    username = _current_username(request)
    try:
        data = report_service.delete_schedule(
            schedule_id, username=username
        )
        return {"success": True, "data": data}
    except ReportServiceError as exc:
        error(f"[reports.stop_report_schedule] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(
            f"[reports.stop_report_schedule] Unexpected error: {exc}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop schedule: {str(exc)}",
        ) from exc


@router.get("/report-runs")
async def list_all_report_runs(limit: int = 50, reportId: Optional[int] = None):
    try:
        data = report_service.list_runs(report_id=reportId, limit=limit)
        return {"success": True, "count": len(data), "data": data}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.list_all_report_runs] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load report runs"
        ) from exc


@router.get("/reports/{report_id}/runs")
async def list_report_runs(report_id: int, limit: int = 50):
    try:
        runs = report_service.list_runs(report_id=report_id, limit=limit)
        return {"success": True, "count": len(runs), "data": runs}
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.list_report_runs] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to load report runs"
        ) from exc



