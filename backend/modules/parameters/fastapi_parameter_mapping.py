from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.dbconnect import create_metadata_connection
from backend.modules.helper_functions import (
    get_parameter_mapping,
    add_parameter_mapping,
)


router = APIRouter(tags=["parameter_mapping"])


class ParameterCreateRequest(BaseModel):
    PRTYP: str
    PRCD: str
    PRDESC: str
    PRVAL: str


@router.get("/parameter_mapping")
async def parameter_display():
    """
    Return the list of parameters.
    Mirrors the Flask endpoint:
    GET /mapping/parameter_mapping
    """
    try:
        conn = create_metadata_connection()
        try:
            parameter_data = get_parameter_mapping(conn)
            return parameter_data
        finally:
            conn.close()
    except Exception as e:
        # Same behavior as Flask: return error and 500 code
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parameter_add")
async def add_parameter(payload: ParameterCreateRequest):
    """
    Add a new parameter.
    Mirrors the Flask endpoint:
    POST /mapping/parameter_add
    """
    try:
        prtyp = payload.PRTYP
        prcd = payload.PRCD
        prdesc = payload.PRDESC
        prval = payload.PRVAL

        if not all([prtyp, prcd, prdesc, prval]):
            raise HTTPException(status_code=400, detail="All fields are required")

        conn = create_metadata_connection()
        try:
            add_parameter_mapping(conn, prtyp, prcd, prdesc, prval)
            return {"message": "Parameter added successfully"}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        # Log error similarly to Flask (if needed)
        raise HTTPException(status_code=500, detail=str(e))

