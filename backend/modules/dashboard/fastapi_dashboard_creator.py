from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import io

from backend.modules.dashboard.dashboard_creator_service import (
    DashboardCreatorError,
    DashboardCreatorService,
)


router = APIRouter(tags=["dashboard_creator"])
service = DashboardCreatorService()


def _current_username(request: Request) -> str:
    return (
        request.headers.get("X-User")
        or request.headers.get("X-USER-ID")
        or request.headers.get("X-USERNAME")
        or "system"
    )


def _current_user_id(request: Request) -> Optional[int]:
    candidate_values = [
        request.headers.get("X-USER-ID"),
        request.headers.get("X-User-ID"),
        request.headers.get("X-User"),
        request.headers.get("X-USERNAME"),
    ]

    for candidate in candidate_values:
        if candidate is None:
            continue
        value = str(candidate).strip()
        if value.isdigit():
            return int(value)
    return None


def _handle_service_error(exc: DashboardCreatorError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
    )


@router.get("/dashboards")
async def list_dashboards(
    search: Optional[str] = None,
    includeInactive: str = "false",
    ownerUserId: Optional[int] = None,
):
    include_inactive = includeInactive.lower() == "true"
    try:
        data = service.list_dashboards(
            search=search,
            include_inactive=include_inactive,
            owner_user_id=ownerUserId,
        )
        return {"success": True, "count": len(data), "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list dashboards: {exc}") from exc


@router.post("/dashboards", status_code=201)
async def create_dashboard(request: Request, payload: Dict[str, Any]):
    username = _current_username(request)
    owner_user_id = _current_user_id(request)
    try:
        data = service.create_dashboard(payload, username=username, owner_user_id=owner_user_id)
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {exc}") from exc


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(request: Request, dashboard_id: int, payload: Dict[str, Any]):
    username = _current_username(request)
    owner_user_id = _current_user_id(request)
    try:
        data = service.update_dashboard(
            dashboard_id,
            payload,
            username=username,
            owner_user_id=owner_user_id,
        )
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update dashboard: {exc}") from exc


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(request: Request, dashboard_id: int):
    username = _current_username(request)
    try:
        data = service.delete_dashboard(dashboard_id, username=username)
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete dashboard: {exc}") from exc


@router.get("/dashboards/sql-sources")
async def list_dashboard_sql_sources():
    try:
        data = service.list_sql_sources()
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load SQL sources: {exc}") from exc


@router.post("/dashboards/describe-sql")
async def describe_dashboard_sql(payload: Dict[str, Any]):
    try:
        data = service.describe_sql_columns(
            sql_text=payload.get("sqlText"),
            db_connection_id=payload.get("dbConnectionId"),
        )
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to describe SQL: {exc}") from exc


@router.post("/dashboards/preview-widget")
async def preview_dashboard_widget_sql(payload: Dict[str, Any]):
    try:
        data = service.preview_widget_sql(
            sql_text=payload.get("sqlText"),
            db_connection_id=payload.get("dbConnectionId"),
            row_limit=payload.get("rowLimit", 100),
        )
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to preview widget SQL: {exc}") from exc


@router.post("/dashboards/{dashboard_id}/export")
async def export_dashboard(request: Request, dashboard_id: int, payload: Dict[str, Any]):
    username = _current_username(request)
    try:
        export_format = payload.get("format") or "PDF"
        row_limit = payload.get("rowLimit", 500)
        result = service.export_dashboard(
            dashboard_id=dashboard_id,
            export_format=export_format,
            username=username,
            row_limit=row_limit,
        )
        return StreamingResponse(
            io.BytesIO(result["content"]),
            media_type=result["mediaType"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["fileName"]}"'
            },
        )
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to export dashboard: {exc}") from exc


@router.get("/dashboards/export-history")
async def get_all_dashboard_export_history(limit: int = 50):
    try:
        data = service.list_export_history(dashboard_id=None, limit=limit)
        return {"success": True, "count": len(data), "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load export history: {exc}") from exc


@router.get("/dashboards/{dashboard_id}/export-history")
async def get_dashboard_export_history(dashboard_id: int, limit: int = 50):
    try:
        data = service.list_export_history(dashboard_id=dashboard_id, limit=limit)
        return {"success": True, "count": len(data), "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard export history: {exc}") from exc


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: int):
    try:
        data = service.get_dashboard(dashboard_id)
        return {"success": True, "data": data}
    except DashboardCreatorError as exc:
        return _handle_service_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {exc}") from exc
