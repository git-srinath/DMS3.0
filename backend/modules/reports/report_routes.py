from flask import Blueprint, jsonify, request

try:
    from backend.database.dbconnect import create_metadata_connection
    from backend.modules.jobs.pkgdwprc_python import (
        JobSchedulerService,
        SchedulerRepositoryError,
    )
    from backend.modules.logger import error, info
except ImportError:  # Fallback for Flask-style imports
    from database.dbconnect import create_metadata_connection  # type: ignore
    from modules.jobs.pkgdwprc_python import (  # type: ignore
        JobSchedulerService,
        SchedulerRepositoryError,
    )
    from modules.logger import error, info  # type: ignore

from .report_service import ReportMetadataService, ReportServiceError

reports_bp = Blueprint("reports", __name__)
report_service = ReportMetadataService()


def _current_username() -> str:
    return (
        request.headers.get("X-User")
        or request.headers.get("X-USER-ID")
        or request.headers.get("X-USERNAME")
        or "system"
    )


def _handle_service_error(exc: ReportServiceError):
    response = {
        "success": False,
        "message": exc.message,
        "code": exc.code,
        "details": exc.details,
    }
    return jsonify(response), exc.status_code


@reports_bp.route("/reports", methods=["GET"])
def list_reports():
    search = request.args.get("search")
    include_inactive = request.args.get("includeInactive", "false").lower() == "true"
    try:
        data = report_service.list_reports(search=search, include_inactive=include_inactive)
        return jsonify({"success": True, "count": len(data), "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover - defensive
        error(f"[reports.list_reports] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch reports"}), 500


@reports_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    try:
        data = report_service.get_report(report_id)
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.get_report] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to load report"}), 500


@reports_bp.route("/reports", methods=["POST"])
def create_report():
    payload = request.get_json(silent=True) or {}
    username = _current_username()
    try:
        data = report_service.create_report(payload, username=username)
        info(f"[reports.create_report] Created report {data.get('reportId')} by {username}")
        return jsonify({"success": True, "data": data}), 201
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.create_report] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to create report"}), 500


@reports_bp.route("/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id: int):
    payload = request.get_json(silent=True) or {}
    username = _current_username()
    force_update = bool(payload.get("forceUpdate"))
    try:
        data = report_service.update_report(report_id, payload, username=username, force_update=force_update)
        info(f"[reports.update_report] Updated report {report_id} by {username}")
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.update_report] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to update report"}), 500


@reports_bp.route("/reports/<int:report_id>/preview", methods=["POST"])
def preview_report(report_id: int):
    payload = request.get_json(silent=True) or {}
    row_limit = payload.get("rowLimit")
    parameters = payload.get("parameters") or {}
    username = _current_username()
    try:
        data = report_service.preview_report(
            report_id=report_id,
            row_limit=row_limit,
            parameters=parameters,
            username=username,
        )
        info(f"[reports.preview_report] Generated preview for report {report_id} by {username}")
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.preview_report] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to generate preview"}), 500

@reports_bp.route("/reports/sql-sources", methods=["GET"])
def list_sql_sources():
    try:
        data = report_service.list_sql_sources()
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.list_sql_sources] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to load SQL sources"}), 500


@reports_bp.route("/reports/describe-sql", methods=["POST"])
def describe_sql():
    payload = request.get_json(silent=True) or {}
    sql_text = payload.get("sqlText")
    db_connection_id = payload.get("dbConnectionId")
    try:
        data = report_service.describe_sql_columns(sql_text=sql_text, db_connection_id=db_connection_id)
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.describe_sql] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to describe SQL"}), 500


@reports_bp.route("/reports/<int:report_id>/execute", methods=["POST"])
def execute_report_sync(report_id: int):
    """Execute report synchronously and return file for download."""
    from flask import send_file
    import io
    import csv
    import json
    
    payload = request.get_json(silent=True) or {}
    username = _current_username()
    output_format = (payload.get("outputFormat") or "CSV").upper()
    
    info(f"[reports.execute_report_sync] Executing report {report_id}, format: {output_format}")
    
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
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in report_name)
        
        # CSV Format
        if output_format == "CSV":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row.get(col, "") for col in columns])
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"{safe_name}.csv"
            )
        
        # JSON Format
        elif output_format == "JSON":
            json_data = json.dumps({"columns": columns, "rows": rows, "rowCount": len(rows)}, indent=2, default=str)
            return send_file(
                io.BytesIO(json_data.encode("utf-8")),
                mimetype="application/json",
                as_attachment=True,
                download_name=f"{safe_name}.json"
            )
        
        # Excel Format
        elif output_format == "EXCEL":
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
                
                return send_file(
                    output,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    as_attachment=True,
                    download_name=f"{safe_name}.xlsx"
                )
            except ImportError:
                error("[reports.execute_report_sync] openpyxl not installed for Excel export")
                return jsonify({"success": False, "message": "Excel export requires openpyxl package. Install with: pip install openpyxl"}), 400
        
        # PDF Format
        elif output_format == "PDF":
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet
                
                output = io.BytesIO()
                doc = SimpleDocTemplate(output, pagesize=landscape(letter))
                elements = []
                
                styles = getSampleStyleSheet()
                elements.append(Paragraph(report_name, styles['Title']))
                
                # Prepare table data
                table_data = [columns]
                for row in rows:
                    table_data.append([str(row.get(col, "")) for col in columns])
                
                # Create table with styling
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
                
                doc.build(elements)
                output.seek(0)
                
                return send_file(
                    output,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"{safe_name}.pdf"
                )
            except ImportError:
                error("[reports.execute_report_sync] reportlab not installed for PDF export")
                return jsonify({"success": False, "message": "PDF export requires reportlab package. Install with: pip install reportlab"}), 400
        
        # XML Format
        elif output_format == "XML":
            import xml.etree.ElementTree as ET
            
            root = ET.Element("report")
            root.set("name", report_name)
            root.set("rowCount", str(len(rows)))
            
            for idx, row in enumerate(rows):
                row_elem = ET.SubElement(root, "row")
                row_elem.set("index", str(idx + 1))
                for col in columns:
                    col_elem = ET.SubElement(row_elem, col.replace(" ", "_").replace("-", "_"))
                    col_elem.text = str(row.get(col, ""))
            
            xml_str = ET.tostring(root, encoding="unicode", method="xml")
            xml_output = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
            
            return send_file(
                io.BytesIO(xml_output.encode("utf-8")),
                mimetype="application/xml",
                as_attachment=True,
                download_name=f"{safe_name}.xml"
            )
        
        # Parquet Format
        elif output_format == "PARQUET":
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
                
                # Convert rows to columnar format
                data = {col: [row.get(col) for row in rows] for col in columns}
                table = pa.table(data)
                
                output = io.BytesIO()
                pq.write_table(table, output)
                output.seek(0)
                
                return send_file(
                    output,
                    mimetype="application/octet-stream",
                    as_attachment=True,
                    download_name=f"{safe_name}.parquet"
                )
            except ImportError:
                error("[reports.execute_report_sync] pyarrow not installed for Parquet export")
                return jsonify({"success": False, "message": "Parquet export requires pyarrow package. Install with: pip install pyarrow"}), 400
        
        else:
            return jsonify({"success": False, "message": f"Unsupported output format: {output_format}"}), 400
            
    except ReportServiceError as exc:
        error(f"[reports.execute_report_sync] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.execute_report_sync] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": f"Failed to execute report: {str(exc)}"}), 500


@reports_bp.route("/reports/<int:report_id>/execute-async", methods=["POST"])
def execute_report_async(report_id: int):
    """Queue report for async execution (Email/File destinations)."""
    payload = request.get_json(silent=True) or {}
    username = _current_username()
    payload.setdefault("requestedBy", username)
    payload.setdefault("outputFormat", "CSV")
    
    destination = (payload.get("destination") or "FILE").upper()
    
    # Validate destination-specific requirements
    if destination == "EMAIL":
        email = payload.get("email", "").strip()
        if not email:
            return jsonify({"success": False, "message": "Email address is required for EMAIL destination"}), 400
    
    info(f"[reports.execute_report_async] Queueing report {report_id} for async execution, destination: {destination}")
    
    connection = None
    try:
        connection = create_metadata_connection()
        service = JobSchedulerService(connection)
        request_id = service.queue_report_request(report_id=report_id, payload=payload)
        info(f"[reports.execute_report_async] Queued report {report_id} by {username}, request_id: {request_id}")
        return jsonify({
            "success": True, 
            "requestId": request_id,
            "message": f"Report queued for {destination.lower()} delivery"
        })
    except SchedulerRepositoryError as exc:
        error(f"[reports.execute_report_async] Scheduler error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        error(f"[reports.execute_report_async] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": f"Failed to queue report: {str(exc)}"}), 500
    finally:
        if connection:
            connection.close()


@reports_bp.route("/report-schedules", methods=["GET", "POST", "OPTIONS"])
def handle_report_schedules():
    if request.method == "OPTIONS":
        return "", 200
    if request.method == "GET":
        try:
            data = report_service.list_schedules()
            return jsonify({"success": True, "count": len(data), "data": data})
        except ReportServiceError as exc:
            return _handle_service_error(exc)
        except Exception as exc:
            error(f"[reports.list_report_schedules] Unexpected error: {exc}", exc_info=True)
            return jsonify({"success": False, "message": "Failed to load schedules"}), 500
    else:  # POST
        payload = request.get_json(silent=True) or {}
        username = _current_username()
        try:
            data = report_service.create_schedule(payload, username=username)
            return jsonify({"success": True, "data": data}), 201
        except ReportServiceError as exc:
            error(f"[reports.create_report_schedule] Service error: {exc}", exc_info=True)
            return _handle_service_error(exc)
        except Exception as exc:
            error(f"[reports.create_report_schedule] Unexpected error: {exc}", exc_info=True)
            return jsonify({"success": False, "message": f"Failed to create schedule: {str(exc)}"}), 500

@reports_bp.route("/report-schedules/<int:schedule_id>", methods=["PUT", "OPTIONS"])
def update_report_schedule(schedule_id: int):
    if request.method == "OPTIONS":
        return "", 200
    payload = request.get_json(silent=True) or {}
    username = _current_username()
    try:
        data = report_service.update_schedule(schedule_id, payload, username=username)
        return jsonify({"success": True, "data": data})
    except ReportServiceError as exc:
        error(f"[reports.update_report_schedule] Service error: {exc}", exc_info=True)
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.update_report_schedule] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": f"Failed to update schedule: {str(exc)}"}), 500

@reports_bp.route("/report-runs", methods=["GET"])
def list_all_report_runs():
    limit = int(request.args.get("limit", 50))
    report_id = request.args.get("reportId")
    try:
        data = report_service.list_runs(report_id=int(report_id) if report_id else None, limit=limit)
        return jsonify({"success": True, "count": len(data), "data": data})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        error(f"[reports.list_all_report_runs] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to load report runs"}), 500


@reports_bp.route("/reports/<int:report_id>/runs", methods=["GET"])
def list_report_runs(report_id: int):
    limit = int(request.args.get("limit", 50))
    try:
        runs = report_service.list_runs(report_id=report_id, limit=limit)
        return jsonify({"success": True, "count": len(runs), "data": runs})
    except ReportServiceError as exc:
        return _handle_service_error(exc)
    except Exception as exc:  # pragma: no cover
        error(f"[reports.list_report_runs] Unexpected error: {exc}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to load report runs"}), 500

