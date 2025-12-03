"""
Report Executor Service

Processes queued report requests from DMS_PRCREQ and generates output files.
Handles Email and File destinations for async report execution.
"""

import io
import os
import csv
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from typing import Dict, Any, Optional, List

from modules.logger import info, error, debug
from modules.reports.report_service import ReportMetadataService, ReportServiceError


class ReportExecutorConfig:
    """Configuration for report executor."""
    
    def __init__(self):
        # File output settings
        # Resolve a stable absolute directory so paths are predictable on Windows and Linux.
        # Default: <backend_root>/report_output unless REPORT_OUTPUT_DIR is explicitly set.
        default_base = os.path.abspath(
            os.environ.get(
                "REPORT_OUTPUT_DIR",
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "report_output"),
            )
        )
        self.output_directory = default_base
        
        # Email settings
        self.smtp_host = os.environ.get("SMTP_HOST", "localhost")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
        self.smtp_from_email = os.environ.get("SMTP_FROM_EMAIL", "reports@example.com")
        self.smtp_from_name = os.environ.get("SMTP_FROM_NAME", "Report System")
        
        # Ensure output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory, exist_ok=True)


class ReportExecutor:
    """Executes reports and handles output delivery."""
    
    def __init__(self, config: Optional[ReportExecutorConfig] = None):
        self.config = config or ReportExecutorConfig()
        self.report_service = ReportMetadataService()
    
    def execute_report(self, report_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a report and deliver output based on destination.
        
        Args:
            report_id: The report ID to execute
            payload: Contains outputFormat, destination, email, filePath, etc.
            
        Returns:
            Dict with execution results
        """
        output_format = (payload.get("outputFormat") or "CSV").upper()
        destination = (payload.get("destination") or "FILE").upper()
        
        info(f"[ReportExecutor] Executing report {report_id}, format: {output_format}, destination: {destination}")
        
        try:
            # Get report data
            result = self.report_service.preview_report(
                report_id=report_id,
                row_limit=None,
                parameters=payload.get("parameters"),
                username=payload.get("requestedBy", "system"),
                allow_unbounded=True,
            )
            
            columns = result.get("columns", [])
            rows = result.get("rows", [])
            report = self.report_service.get_report(report_id)
            report_name = report.get("reportName", f"report_{report_id}")
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in report_name)
            
            # Generate file content
            file_content, file_ext, mime_type = self._generate_file(
                columns=columns,
                rows=rows,
                output_format=output_format,
                report_name=report_name,
            )
            
            filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            
            # Deliver based on destination
            if destination == "EMAIL":
                email_addresses = payload.get("email", "")
                if not email_addresses:
                    raise ReportServiceError("Email address is required for EMAIL destination")
                
                self._send_email(
                    to_addresses=email_addresses,
                    subject=f"Report: {report_name}",
                    body=f"Please find attached the report '{report_name}' generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\nRows: {len(rows)}",
                    attachment_content=file_content,
                    attachment_filename=filename,
                    mime_type=mime_type,
                )
                # Record run in history so it appears in report runs UI
                run_id = self.report_service.record_external_run(
                    report_id=report_id,
                    output_formats=[output_format],
                    row_count=len(rows),
                    username=payload.get("requestedBy", "system"),
                    request_id=payload.get("requestId"),
                    parameters=payload.get("parameters"),
                    message=None,
                )
                info(f"[ReportExecutor] Report {report_id} sent via email to {email_addresses}")
                return {
                    "success": True,
                    "runId": run_id,
                    "destination": "EMAIL",
                    "recipients": email_addresses,
                    "filename": filename,
                    "rowCount": len(rows),
                }
            
            elif destination == "FILE":
                user_path = payload.get("filePath", "").strip()
                
                if user_path:
                    # Check if user provided a full file path (with extension) or just a directory
                    _, ext = os.path.splitext(user_path)
                    if ext:
                        # User provided a full file path with extension - use it directly
                        full_path = user_path
                    else:
                        # User provided a directory - append the generated filename
                        full_path = os.path.join(user_path, filename)
                else:
                    # No path provided - use default output directory
                    full_path = os.path.join(self.config.output_directory, filename)
                
                # Resolve to absolute path and ensure directory exists
                full_path = os.path.abspath(full_path)
                dir_path = os.path.dirname(full_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                
                with open(full_path, "wb") as f:
                    f.write(file_content)
                
                # Record run in history so it appears in report runs UI
                run_id = self.report_service.record_external_run(
                    report_id=report_id,
                    output_formats=[output_format],
                    row_count=len(rows),
                    username=payload.get("requestedBy", "system"),
                    request_id=payload.get("requestId"),
                    parameters=payload.get("parameters"),
                    message=None,
                )
                info(f"[ReportExecutor] Report {report_id} saved to {full_path}")
                return {
                    "success": True,
                    "runId": run_id,
                    "destination": "FILE",
                    "filePath": full_path,
                    "filename": os.path.basename(full_path),
                    "rowCount": len(rows),
                }
            
            else:
                raise ReportServiceError(f"Unsupported destination: {destination}")
                
        except Exception as exc:
            error(f"[ReportExecutor] Failed to execute report {report_id}: {exc}", exc_info=True)
            raise
    
    def _generate_file(
        self,
        columns: List[str],
        rows: List[Dict[str, Any]],
        output_format: str,
        report_name: str,
    ) -> tuple:
        """Generate file content in the specified format. Returns (content_bytes, extension, mime_type)."""
        
        if output_format == "CSV":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row.get(col, "") for col in columns])
            return output.getvalue().encode("utf-8"), "csv", "text/csv"
        
        elif output_format == "JSON":
            json_data = json.dumps({"columns": columns, "rows": rows, "rowCount": len(rows)}, indent=2, default=str)
            return json_data.encode("utf-8"), "json", "application/json"
        
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
                return output.getvalue(), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            except ImportError:
                raise ReportServiceError("Excel export requires openpyxl package")
        
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
                
                table_data = [columns]
                for row in rows:
                    table_data.append([str(row.get(col, "")) for col in columns])
                
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
                return output.getvalue(), "pdf", "application/pdf"
            except ImportError:
                raise ReportServiceError("PDF export requires reportlab package")
        
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
            return xml_output.encode("utf-8"), "xml", "application/xml"
        
        elif output_format == "PARQUET":
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
                
                data = {col: [row.get(col) for row in rows] for col in columns}
                table = pa.table(data)
                
                output = io.BytesIO()
                pq.write_table(table, output)
                return output.getvalue(), "parquet", "application/octet-stream"
            except ImportError:
                raise ReportServiceError("Parquet export requires pyarrow package")
        
        else:
            raise ReportServiceError(f"Unsupported output format: {output_format}")
    
    def _send_email(
        self,
        to_addresses: str,
        subject: str,
        body: str,
        attachment_content: bytes,
        attachment_filename: str,
        mime_type: str,
    ) -> None:
        """Send email with attachment."""
        
        msg = MIMEMultipart()
        msg["From"] = f"{self.config.smtp_from_name} <{self.config.smtp_from_email}>"
        msg["To"] = to_addresses
        msg["Subject"] = subject
        
        # Add body
        msg.attach(MIMEText(body, "plain"))
        
        # Add attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_content)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={attachment_filename}")
        msg.attach(part)
        
        # Send email
        try:
            if self.config.smtp_use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            
            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)
            
            recipients = [addr.strip() for addr in to_addresses.split(",")]
            server.sendmail(self.config.smtp_from_email, recipients, msg.as_string())
            server.quit()
            
            info(f"[ReportExecutor] Email sent successfully to {to_addresses}")
        except Exception as exc:
            error(f"[ReportExecutor] Failed to send email: {exc}", exc_info=True)
            raise ReportServiceError(f"Failed to send email: {str(exc)}")


# Singleton instance
_executor_instance: Optional[ReportExecutor] = None


def get_report_executor() -> ReportExecutor:
    """Get or create the report executor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ReportExecutor()
    return _executor_instance

