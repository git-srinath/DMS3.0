from typing import Any, Dict, List, Optional
import datetime
import io

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.database.dbconnect import (
    create_metadata_connection,
    create_target_connection,
)
from backend.modules.helper_functions import (
    get_mapping_ref,
    get_mapping_details,
    get_parameter_mapping_datatype,
    get_parameter_mapping_scd_type,
    check_if_job_already_created,
    create_update_mapping,
    create_update_mapping_detail,
    validate_logic2,
    validate_all_mapping_details,
    get_error_messages_list,
    call_activate_deactivate_mapping,
    call_delete_mapping,
    call_delete_mapping_details,
)


router = APIRouter(tags=["mapper"])

# Constants for form and table fields (matching Flask mapper.py)
FORM_FIELDS = [
    "reference",
    "description",
    "sourceSystem",
    "tableName",
    "tableType",
    "targetSchema",
    "freqCode",
    "bulkProcessRows",
]
TABLE_FIELDS = [
    "primaryKey",
    "pkSeq",
    "fieldName",
    "dataType",
    "fieldDesc",
    "scdType",
    "keyColumn",
    "valColumn",
    "logic",
    "mapCombineCode",
    "execSequence",
]


@router.get("/get-parameter-mapping-datatype")
async def get_parameter_mapping_datatype_api() -> List[Dict[str, Any]]:
    """
    Return parameter mapping entries of type 'Datatype'.
    Mirrors Flask endpoint: GET /mapper/get-parameter-mapping-datatype
    """
    conn = None
    try:
        conn = create_metadata_connection()
        return get_parameter_mapping_datatype(conn)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in get_parameter_mapping_datatype: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/parameter_scd_type")
async def parameter_scd_type() -> List[Dict[str, Any]]:
    """
    Return parameter mapping entries of type 'SCD'.
    Mirrors Flask endpoint: GET /mapper/parameter_scd_type
    """
    conn = None
    try:
        conn = create_metadata_connection()
        try:
            parameter_data = get_parameter_mapping_scd_type(conn)
            return parameter_data
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in parameter_scd_type: {str(e)}"
        )


@router.get("/get-connections")
async def get_connections() -> List[Dict[str, Any]]:
    """
    Get list of active database connections from DMS_DBCONDTLS.
    Mirrors Flask endpoint: GET /mapper/get-connections
    """
    conn = None
    try:
        conn = create_metadata_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT conid, connm, dbhost, dbsrvnm
                FROM DMS_DBCONDTLS
                WHERE curflg = 'Y'
                ORDER BY connm
            """
            )

            connections: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                connections.append(
                    {
                        "conid": str(row[0]),
                        "connm": row[1],
                        "dbhost": row[2],
                        "dbsrvnm": row[3],
                    }
                )

            cursor.close()
            return connections
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching connections: {str(e)}"
        )


@router.get("/get-by-reference/{reference}")
async def get_by_reference(reference: str):
    """
    Fetch mapping header + detail rows by reference.
    Mirrors Flask endpoint: GET /mapper/get-by-reference/<reference>
    """
    conn = None
    try:
        conn = create_metadata_connection()
        try:
            # Get reference data
            main_result: Optional[Dict[str, Any]] = get_mapping_ref(conn, reference)

            if not main_result:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "exists": False,
                        "message": (
                            "Reference not found or inactive. You can create a new "
                            "mapping with this reference."
                        ),
                    },
                )

            # Get mapping details
            details_result: List[Dict[str, Any]] = get_mapping_details(conn, reference)

            # Get job created status
            job_status = check_if_job_already_created(conn, reference)

            # Format response
            form_data = {
                "reference": main_result.get("MAPREF"),
                "description": main_result.get("MAPDESC") or "",
                "mapperId": str(main_result.get("MAPID")),
                "targetSchema": main_result.get("TRGSCHM") or "",
                "tableName": main_result.get("TRGTBNM") or "",
                "tableType": main_result.get("TRGTBTYP") or "",
                "freqCode": main_result.get("FRQCD") or "",
                "sourceSystem": main_result.get("SRCSYSTM") or "",
                "bulkProcessRows": main_result.get("BLKPRCROWS"),
                "targetConnectionId": (
                    str(main_result.get("TRGCONID"))
                    if main_result.get("TRGCONID")
                    else None
                ),
                "isReferenceDisabled": True,
                "logic_verification_status": main_result.get("LGVRFYFLG"),
                "activate_status": main_result.get("STFLG"),
                "job_creation_status": job_status,
                # Checkpoint configuration (handle NULL values for older mappings)
                "checkpointStrategy": (
                    main_result.get("CHKPNTSTRTGY")
                    if main_result.get("CHKPNTSTRTGY")
                    else "AUTO"
                ),
                "checkpointColumn": (
                    main_result.get("CHKPNTCLNM")
                    if main_result.get("CHKPNTCLNM")
                    else ""
                ),
                "checkpointEnabled": (
                    main_result.get("CHKPNTENBLD") == "Y"
                    if main_result.get("CHKPNTENBLD")
                    else True
                ),
            }

            # Transform the details result into rows
            rows: List[Dict[str, Any]] = []
            for row in details_result:
                rows.append(
                    {
                        "mapdtlid": str(row.get("MAPDTLID")),
                        "mapref": row.get("MAPREF") or "",
                        "fieldName": row.get("TRGCLNM") or "",
                        "dataType": row.get("TRGCLDTYP") or "",
                        "primaryKey": row.get("TRGKEYFLG") == "Y",
                        "pkSeq": (
                            str(row.get("TRGKEYSEQ"))
                            if row.get("TRGKEYSEQ") is not None
                            else ""
                        ),
                        "fieldDesc": row.get("TRGCLDESC") or "",
                        "logic": row.get("MAPLOGIC") or "",
                        "keyColumn": row.get("KEYCLNM") or "",
                        "valColumn": row.get("VALCLNM") or "",
                        "mapCombineCode": row.get("MAPCMBCD") or "",
                        "execSequence": (
                            str(row.get("EXCSEQ"))
                            if row.get("EXCSEQ") is not None
                            else ""
                        ),
                        "scdType": (
                            str(row.get("SCDTYP"))
                            if row.get("SCDTYP") is not None
                            else ""
                        ),
                        "LogicVerFlag": row.get("LGVRFYFLG"),
                    }
                )

            # If no detail rows exist, provide empty template rows
            if not rows:
                rows = [
                    {
                        "mapdtlid": "",
                        "mapref": reference,
                        "fieldName": "",
                        "dataType": "",
                        "primaryKey": False,
                        "pkSeq": "",
                        "fieldDesc": "",
                        "logic": "",
                        "keyColumn": "",
                        "valColumn": "",
                        "mapCombineCode": "",
                        "execSequence": "",
                        "scdType": "",
                        "LogicVerFlag": "",
                    }
                    for _ in range(6)
                ]

            response_data = {
                "exists": True,
                "formData": form_data,
                "rows": rows,
                "message": "Mapping data retrieved successfully",
            }

            return response_data
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "An error occurred while retrieving the mapping data",
                "details": str(e),
            },
        )


# ----- Write / validation / activation endpoints -----


class SaveToDbRequest(BaseModel):
    formData: Dict[str, Any]
    rows: List[Dict[str, Any]]
    modifiedRows: Optional[List[int]] = None


@router.post("/save-to-db")
async def save_to_db(payload: SaveToDbRequest):
    """
    Save mapping header and detail rows.
    Mirrors Flask endpoint: POST /mapper/save-to-db
    """
    conn = None
    try:
        data = payload.model_dump()
        form_data = data["formData"]
        rows = data["rows"]
        modified_rows = data.get("modifiedRows") or []
        user_id = form_data.get("username")

        conn = create_metadata_connection()
        try:
            target_connection_id = form_data.get("targetConnectionId")

            checkpoint_strategy = form_data.get("checkpointStrategy", "AUTO")
            checkpoint_column = form_data.get("checkpointColumn", None)
            checkpoint_enabled = (
                "Y" if form_data.get("checkpointEnabled", True) else "N"
            )

            mapid = create_update_mapping(
                conn,
                form_data["reference"],
                form_data["description"],
                form_data["targetSchema"],
                form_data["tableType"],
                form_data["tableName"],
                form_data["freqCode"],
                form_data["sourceSystem"],
                "N",  # lgvrfyflg
                datetime.datetime.now(),
                "N",  # stflg
                form_data["bulkProcessRows"],
                p_trgconid=target_connection_id,
                p_user=user_id,
                p_chkpntstrtgy=checkpoint_strategy,
                p_chkpntclnm=checkpoint_column,
                p_chkpntenbld=checkpoint_enabled,
            )

            processed_rows: List[Dict[str, Any]] = []
            for idx, row in enumerate(rows):
                if not row.get("fieldName", "").strip():
                    continue

                # Respect modifiedRows: skip unmodified rows with existing mapdtlid
                if not (idx in modified_rows or not row.get("mapdtlid")):
                    continue

                logic_ver_flag = row.get("LogicVerFlag", "")

                mapdtlid = create_update_mapping_detail(
                    conn,
                    form_data["reference"],
                    row["fieldName"],
                    row["dataType"],
                    "Y" if row.get("primaryKey") else "N",
                    row.get("pkSeq") if row.get("pkSeq") and row.get("primaryKey") else None,
                    row.get("fieldDesc"),
                    row["logic"] if row.get("logic", "").strip() else None,
                    row.get("keyColumn"),
                    row.get("valColumn"),
                    row.get("mapCombineCode"),
                    row.get("execSequence"),
                    row.get("scdType"),
                    logic_ver_flag,
                    "" if logic_ver_flag == "" else datetime.datetime.now(),
                    form_data.get("username"),
                )

                processed_rows.append(
                    {"index": idx, "mapdtlid": mapdtlid, "fieldName": row["fieldName"]}
                )

            conn.commit()

            return {
                "success": True,
                "message": "Mapping saved successfully",
                "mapperId": str(mapid),
                "processedRows": processed_rows,
            }
        except Exception as e:
            if conn:
                conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while saving the mapping data: {str(e)}",
            )
        finally:
            if conn:
                conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving the mapping data: {str(e)}",
        )


class ValidateLogicRequest(BaseModel):
    p_logic: str
    p_keyclnm: str
    p_valclnm: str
    # Optional: validate against a specific target connection instead of metadata DB
    connection_id: Optional[int] = None


@router.post("/validate-logic")
async def validate_logic(payload: ValidateLogicRequest):
    """
    Validate a single piece of mapping logic.
    Mirrors Flask endpoint: POST /mapper/validate-logic
    """
    data = payload.model_dump()
    p_logic = data.get("p_logic")
    p_keyclnm = data.get("p_keyclnm")
    p_valclnm = data.get("p_valclnm")
    connection_id = data.get("connection_id")

    if not all([p_logic, p_keyclnm, p_valclnm]):
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required parameters. Please provide p_logic, "
                "p_keyclnm, and p_valclnm."
            ),
        )

    connection = None
    try:
        # If a connection_id is provided, use that target DB for validation;
        # otherwise, fall back to metadata connection (mirrors extended behavior of validate-sql).
        if connection_id is not None:
            try:
                connection = create_target_connection(connection_id)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Failed to connect to selected database for validation "
                        f"(connection_id={connection_id}): {str(e)}"
                    ),
                )
        else:
            connection = create_metadata_connection()
        is_valid, err = validate_logic2(connection, p_logic, p_keyclnm, p_valclnm)
        return {
            "status": "success",
            "is_valid": is_valid,
            "message": "Logic is valid" if is_valid == "Y" else err,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error validating logic: {str(e)}"
        )
    finally:
        if connection:
            connection.close()


class ValidateBatchRequest(BaseModel):
    mapref: str
    rows: List[Dict[str, Any]] = []


@router.post("/validate-batch")
async def validate_batch_logic(payload: ValidateBatchRequest):
    """
    Validate all mapping details for a given mapref in bulk.
    Mirrors Flask endpoint: POST /mapper/validate-batch
    """
    data = payload.model_dump()
    p_mapref = data.get("mapref")
    rows = data.get("rows", [])

    metadata_connection = None
    target_connection = None
    try:
        metadata_connection = create_metadata_connection()

        # Determine target connection from mapping
        mapping_data = get_mapping_ref(metadata_connection, p_mapref)
        if mapping_data:
            trgconid = mapping_data.get("TRGCONID") or mapping_data.get("trgconid")
        else:
            trgconid = None

        if trgconid:
            try:
                target_connection = create_target_connection(trgconid)
            except Exception:
                # Fallback to metadata connection if target fails
                target_connection = metadata_connection
        else:
            target_connection = metadata_connection

        results: List[Dict[str, Any]] = []

        # Bulk validation using helper function
        bulk_result, bulk_error = validate_all_mapping_details(
            metadata_connection, p_mapref, target_connection
        )

        if bulk_error is None:
            for row in rows:
                if row.get("logic"):
                    results.append(
                        {
                            "rowId": row.get("mapdtlid"),
                            "fieldName": row.get("fieldName"),
                            "isValid": True,
                            "error": None,
                            "detailedError": "Logic is Verified",
                        }
                    )
            return {
                "status": "success",
                "bulkValidation": {"success": True, "error": None},
                "rowResults": results,
            }

        # Collect all mapdtlids that have logic
        map_detail_ids = [
            row.get("mapdtlid")
            for row in rows
            if row.get("mapdtlid") and row.get("logic")
        ]

        error_messages = get_error_messages_list(metadata_connection, map_detail_ids)

        for row in rows:
            if not row.get("logic"):
                continue

            err_msg = None
            if row.get("mapdtlid") and row.get("mapdtlid") in error_messages:
                err_msg = error_messages[row.get("mapdtlid")]

            results.append(
                {
                    "rowId": row.get("mapdtlid"),
                    "fieldName": row.get("fieldName"),
                    "isValid": err_msg == "Logic is Verified",
                    "error": None if err_msg == "Logic is Verified" else err_msg,
                    "detailedError": err_msg,
                }
            )

        return {
            "status": "success",
            "bulkValidation": {"success": bulk_result, "error": bulk_error},
            "rowResults": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in validate_batch: {str(e)}"
        )
    finally:
        if metadata_connection:
            metadata_connection.close()
        if target_connection and target_connection is not metadata_connection:
            try:
                target_connection.close()
            except Exception:
                pass


class ActivateDeactivateRequest(BaseModel):
    mapref: str
    statusFlag: str


@router.post("/activate-deactivate")
async def activate_deactivate_mapping(payload: ActivateDeactivateRequest):
    """
    Activate or deactivate a mapping.
    Mirrors Flask endpoint: POST /mapper/activate-deactivate
    """
    data = payload.model_dump()
    p_mapref = data.get("mapref")
    p_stflg = data.get("statusFlag")

    if not p_mapref or not p_stflg:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required parameters. Please provide mapref and statusFlag."
            ),
        )

    if p_stflg not in ["A", "N"]:
        raise HTTPException(
            status_code=400,
            detail='Invalid status flag. Must be either "A" (activate) or "N" (deactivate).',
        )

    conn = None
    try:
        conn = create_metadata_connection()
        success, message = call_activate_deactivate_mapping(conn, p_mapref, p_stflg)
        return {"success": success, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
    finally:
        if conn:
            conn.close()


# ----- Reference management & delete endpoints -----


@router.get("/get-all-mapper-reference")
async def get_all_mapper_reference() -> List[List[Any]]:
    """
    Get all mapper reference details.
    Mirrors Flask endpoint: GET /mapper/get-all-mapper-reference
    """
    conn = None
    try:
        conn = create_metadata_connection()
        query = """
        SELECT MAPREF, MAPDESC,TRGSCHM,TRGTBTYP,FRQCD,SRCSYSTM,LGVRFYFLG,STFLG,CRTDBY,UPTDBY
        FROM DMS_MAPR
        WHERE CURFLG = 'Y'
        """
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        # Convert tuples to lists for JSON serialization
        return [list(row) for row in result]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in get_all_mapper_reference: {str(e)}",
        )
    finally:
        if conn:
            conn.close()


class DeleteMapperReferenceRequest(BaseModel):
    mapref: str


@router.post("/delete-mapper-reference")
async def delete_mapper_reference(payload: DeleteMapperReferenceRequest):
    """
    Delete a mapper reference.
    Mirrors Flask endpoint: POST /mapper/delete-mapper-reference
    """
    conn = None
    try:
        p_mapref = payload.mapref
        conn = create_metadata_connection()

        try:
            success, message = call_delete_mapping(conn, p_mapref)

            if success:
                return {"success": True, "message": message}
            else:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "message": message},
                )
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in delete_mapper_reference: {str(e)}",
        )


class DeleteMappingDetailRequest(BaseModel):
    mapref: str
    trgclnm: str


@router.post("/delete-mapping-detail")
async def delete_mapping_detail(payload: DeleteMappingDetailRequest):
    """
    Delete a mapping detail row.
    Mirrors Flask endpoint: POST /mapper/delete-mapping-detail
    """
    conn = None
    try:
        p_mapref = payload.mapref
        p_trgclnm = payload.trgclnm

        if not p_mapref or not p_trgclnm:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Missing required parameters. Please provide mapref and trgclnm."
                ),
            )

        conn = create_metadata_connection()
        try:
            success, message = call_delete_mapping_details(conn, p_mapref, p_trgclnm)

            return {"success": success, "message": message}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the mapping detail: {str(e)}",
        )


# ----- Template/Excel endpoints -----


@router.get("/download-template")
async def download_template(format: str = Query("xlsx", regex="^(xlsx|csv)$")):
    """
    Download an empty mapper template (Excel or CSV).
    Mirrors Flask endpoint: GET /mapper/download-template?format=xlsx|csv
    """
    try:
        export_format = format.lower()
        if export_format not in ["xlsx", "csv"]:
            export_format = "xlsx"

        # Create a new workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Mapping Template"

        # Define styles
        header_fill = PatternFill(
            start_color="00B050", end_color="00B050", fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Write Form Fields section
        ws["A1"] = "Form Fields"
        ws.merge_cells("A1:H1")
        ws["A1"].fill = header_fill
        ws["A1"].font = header_font
        ws["A1"].alignment = header_alignment

        # Write Form Fields headers
        for col, field in enumerate(FORM_FIELDS, 1):
            cell = ws.cell(row=2, column=col)
            cell.value = field
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Add empty row for form data
        for col in range(1, len(FORM_FIELDS) + 1):
            cell = ws.cell(row=3, column=col)
            cell.border = border

        # Add space between sections
        ws.append([])

        # Write Table Fields section
        current_row = 5
        ws.cell(row=current_row, column=1, value="Table Fields")
        ws.merge_cells(f"A{current_row}:K{current_row}")
        ws.cell(row=current_row, column=1).fill = header_fill
        ws.cell(row=current_row, column=1).font = header_font
        ws.cell(row=current_row, column=1).alignment = header_alignment

        # Write Table Fields headers
        current_row += 1
        for col, field in enumerate(TABLE_FIELDS, 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = field
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Add empty rows for table data
        for row in range(current_row + 1, current_row + 11):  # 10 empty rows
            for col in range(1, len(TABLE_FIELDS) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = border

        # Adjust column widths
        for col_idx in range(1, max(len(FORM_FIELDS), len(TABLE_FIELDS)) + 1):
            max_length = 0
            column_letter = get_column_letter(col_idx)

            # Check form headers (row 2)
            if col_idx <= len(FORM_FIELDS):
                header_value = ws.cell(row=2, column=col_idx).value
                if header_value:
                    max_length = max(max_length, len(str(header_value)))

            # Check table headers (row 6)
            if col_idx <= len(TABLE_FIELDS):
                header_value = ws.cell(row=current_row, column=col_idx).value
                if header_value:
                    max_length = max(max_length, len(str(header_value)))

            # Set the column width
            adjusted_width = max_length + 2
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save to BytesIO buffer
        excel_buffer = io.BytesIO()

        if export_format == "csv":
            # Create DataFrame from workbook data to save as CSV
            form_headers = [
                ws.cell(row=2, column=i).value
                for i in range(1, len(FORM_FIELDS) + 1)
            ]
            form_data = [
                ws.cell(row=3, column=i).value or ""
                for i in range(1, len(FORM_FIELDS) + 1)
            ]

            table_headers = [
                ws.cell(row=current_row, column=i).value
                for i in range(1, len(TABLE_FIELDS) + 1)
            ]
            table_data = []
            for row in range(current_row + 1, current_row + 11):
                row_data = []
                for col in range(1, len(TABLE_FIELDS) + 1):
                    row_data.append(ws.cell(row=row, column=col).value or "")
                table_data.append(row_data)

            # First save form data
            form_df = pd.DataFrame([form_data], columns=form_headers)

            # Then save table data
            table_df = pd.DataFrame(table_data, columns=table_headers)

            # Combine them with a separator row
            combined_csv = form_df.to_csv(index=False) + "\n\n" + table_df.to_csv(
                index=False
            )

            # Convert to bytes and prepare response
            excel_buffer = io.BytesIO(combined_csv.encode())
            mimetype = "text/csv"
            download_name = "mapper_template.csv"
        else:  # xlsx format
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            download_name = "mapper_template.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type=mimetype,
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in download_template: {str(e)}"
        )


class DownloadCurrentRequest(BaseModel):
    formData: Dict[str, Any]
    rows: List[Dict[str, Any]]
    format: Optional[str] = "xlsx"


@router.post("/download-current")
async def download_current(payload: DownloadCurrentRequest):
    """
    Download current mapping data as Excel or CSV.
    Mirrors Flask endpoint: POST /mapper/download-current
    """
    try:
        data = payload.model_dump()
        form_data = data.get("formData", {})
        rows_data = data.get("rows", [])

        # Check if format parameter is provided, default to xlsx
        export_format = data.get("format", "xlsx").lower()
        if export_format not in ["xlsx", "csv"]:
            export_format = "xlsx"

        # Filter out rows without field names
        rows_data = [row for row in rows_data if row.get("fieldName")]

        # Create a new workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Mapping Template"

        # Define styles
        header_fill = PatternFill(
            start_color="00B050", end_color="00B050", fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Write Form Fields section
        ws["A1"] = "Form Fields"
        ws.merge_cells("A1:H1")
        ws["A1"].fill = header_fill
        ws["A1"].font = header_font
        ws["A1"].alignment = header_alignment

        # Write Form Fields headers
        for col, field in enumerate(FORM_FIELDS, 1):
            cell = ws.cell(row=2, column=col)
            cell.value = field
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Write Form Fields values
        for col, field in enumerate(FORM_FIELDS, 1):
            cell = ws.cell(row=3, column=col)
            cell.value = form_data.get(field, "")
            cell.border = border

        # Add space between sections
        ws.append([])

        # Write Table Fields section
        current_row = 5
        ws.cell(row=current_row, column=1, value="Table Fields")
        ws.merge_cells(f"A{current_row}:K{current_row}")
        ws.cell(row=current_row, column=1).fill = header_fill
        ws.cell(row=current_row, column=1).font = header_font
        ws.cell(row=current_row, column=1).alignment = header_alignment

        # Write Table Fields headers
        current_row += 1
        for col, field in enumerate(TABLE_FIELDS, 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = field
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Add rows with data
        for row_idx, row_data in enumerate(rows_data, current_row + 1):
            # Map the field names to match TABLE_FIELDS
            field_mapping = {
                "primaryKey": "primaryKey",
                "pkSeq": "pkSeq",
                "fieldName": "fieldName",
                "dataType": "dataType",
                "fieldDesc": "fieldDesc",
                "scdType": "scdType",
                "keyColumn": "keyColumn",
                "valColumn": "valColumn",
                "logic": "logic",
                "mapCombineCode": "mapCombineCode",
                "execSequence": "execSequence",
            }

            for col_idx, field in enumerate(TABLE_FIELDS, 1):
                cell = ws.cell(row=row_idx, column=col_idx)

                # Get the mapped field name
                mapped_field = field_mapping.get(field, field)

                # Handle boolean fields like primaryKey separately
                if field == "primaryKey":
                    cell.value = "Yes" if row_data.get(mapped_field, False) else "No"
                else:
                    cell.value = row_data.get(mapped_field, "")

                cell.border = border

        # Adjust column widths
        for col_idx in range(1, max(len(FORM_FIELDS), len(TABLE_FIELDS)) + 1):
            max_length = 0
            column_letter = get_column_letter(col_idx)

            # Check all rows for maximum value length
            for row in range(2, ws.max_row + 1):
                cell_value = ws.cell(row=row, column=col_idx).value
                if cell_value:
                    cell_value_str = str(cell_value)
                    # Limit preview length for very long values
                    max_length = max(max_length, min(len(cell_value_str), 50))

            # Set the column width
            adjusted_width = max(max_length + 2, 12)  # Minimum width of 12
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save to BytesIO buffer
        excel_buffer = io.BytesIO()

        if export_format == "csv":
            # Create DataFrame from workbook data to save as CSV
            form_headers = [
                ws.cell(row=2, column=i).value
                for i in range(1, len(FORM_FIELDS) + 1)
            ]
            form_data_values = [
                ws.cell(row=3, column=i).value or ""
                for i in range(1, len(FORM_FIELDS) + 1)
            ]

            table_headers = [
                ws.cell(row=current_row, column=i).value
                for i in range(1, len(TABLE_FIELDS) + 1)
            ]
            table_data = []
            for row in range(current_row + 1, current_row + 1 + len(rows_data)):
                row_data = []
                for col in range(1, len(TABLE_FIELDS) + 1):
                    row_data.append(ws.cell(row=row, column=col).value or "")
                table_data.append(row_data)

            # First save form data
            form_df = pd.DataFrame([form_data_values], columns=form_headers)

            # Then save table data
            table_df = pd.DataFrame(table_data, columns=table_headers)

            # Combine them with a separator row
            combined_csv = form_df.to_csv(index=False) + "\n\n" + table_df.to_csv(
                index=False
            )

            # Convert to bytes and prepare response
            excel_buffer = io.BytesIO(combined_csv.encode())
            mimetype = "text/csv"
            download_name = f"{form_data.get('reference', 'mapper')}_data.csv"
        else:  # xlsx format
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            download_name = f"{form_data.get('reference', 'mapper')}_data.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type=mimetype,
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in download_current: {str(e)}"
        )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and parse a mapper template Excel/CSV file.
    Mirrors Flask endpoint: POST /mapper/upload
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        # Read the file content
        file_content = await file.read()

        # Read the Excel file
        wb = load_workbook(io.BytesIO(file_content))
        ws = wb.active

        # Process form fields
        form_data = {}
        form_headers = [cell.value for cell in ws[2] if cell.value]
        form_values = [
            cell.value for cell in ws[3] if cell.column <= len(form_headers)
        ]

        for header, value in zip(form_headers, form_values):
            form_data[header] = str(value) if value is not None else ""

        # Process table fields
        table_start_row = 6  # Table headers start at row 6
        table_headers = [cell.value for cell in ws[table_start_row] if cell.value]
        rows = []

        for row in ws.iter_rows(min_row=table_start_row + 1, max_col=len(table_headers)):
            row_data = {}
            has_data = False

            for header, cell in zip(table_headers, row):
                value = cell.value

                # Handle boolean fields
                if header == "primaryKey":
                    if isinstance(value, bool):
                        value = value
                    elif isinstance(value, (int, float)):
                        value = bool(value)
                    else:
                        value = (
                            str(value).lower().strip() in ["true", "1", "yes", "y"]
                            if value
                            else False
                        )
                elif value is None:
                    value = ""
                else:
                    value = str(value).strip()
                    if value:
                        has_data = True

                row_data[header] = value

            if has_data:
                rows.append(row_data)

        # Map the data to the required format
        mapped_rows = []
        for row in rows:
            mapped_row = {
                "mapdtlid": "",  # This will be empty for new rows
                "fieldName": row.get("fieldName", ""),
                "dataType": row.get("dataType", ""),
                "primaryKey": row.get("primaryKey", False),
                "pkSeq": row.get("pkSeq", ""),
                "nulls": False,  # Default value
                "logic": row.get("logic", ""),
                "validator": "N",  # Default value
                "keyColumn": row.get("keyColumn", ""),
                "valColumn": row.get("valColumn", ""),
                "mapCombineCode": row.get("mapCombineCode", ""),
                "LogicVerFlag": "N",  # Default value
                "scdType": row.get("scdType", ""),
                "fieldDesc": row.get("fieldDesc", ""),
                "execSequence": row.get("execSequence", ""),
            }
            mapped_rows.append(mapped_row)

        # Prepare response data
        response_data = {
            "formData": {
                "reference": str(form_data.get("reference", "")).strip(),
                "description": str(form_data.get("description", "")).strip(),
                "mapperId": "",  # This might need to be generated or extracted
                "targetSchema": str(form_data.get("targetSchema", "")).strip(),
                "tableName": str(form_data.get("tableName", "")).strip(),
                "tableType": str(form_data.get("tableType", "")).strip(),
                "freqCode": str(form_data.get("freqCode", "")).strip(),
                "sourceSystem": str(form_data.get("sourceSystem", "")).strip(),
                "bulkProcessRows": form_data.get("bulkProcessRows", ""),
            },
            "rows": mapped_rows,
        }

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in upload_file: {str(e)}")



