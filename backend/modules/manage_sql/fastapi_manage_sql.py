from typing import List, Optional

import builtins
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.database.dbconnect import create_metadata_connection, create_target_connection
from backend.modules.mapper.pkgdwmapr_python import create_update_sql, validate_sql as pkg_validate_sql


router = APIRouter(tags=["manage_sql"])


def _detect_db_type(conn) -> str:
    """Detect database type from connection."""
    module_name = builtins.type(conn).__module__
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    if "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    return "ORACLE"


class FetchAllSqlCodesResponse(BaseModel):
    success: bool
    message: str
    data: List[str]
    count: int


class SqlLogicData(BaseModel):
    sql_code: str
    sql_content: str
    connection_id: Optional[str] = None


class FetchSqlLogicResponse(BaseModel):
    success: bool
    message: str
    data: Optional[SqlLogicData] = None


class HistoryItem(BaseModel):
    date: str
    sql_content: str


class SqlHistoryData(BaseModel):
    sql_code: str
    history_items: List[HistoryItem]


class FetchSqlHistoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[SqlHistoryData] = None


class SaveSqlRequest(BaseModel):
    sql_code: str
    sql_content: str
    connection_id: Optional[int] = None


class SaveSqlResponse(BaseModel):
    success: bool
    message: str
    sql_id: Optional[int] = None
    sql_code: Optional[str] = None


class ValidateSqlRequest(BaseModel):
    sql_content: str
    connection_id: Optional[int] = None


class ValidateSqlResponse(BaseModel):
    success: bool
    message: str
    is_valid: bool
    validation_result: Optional[str] = None


class ConnectionItem(BaseModel):
    conid: str
    connm: str
    dbhost: str
    dbsrvnm: str


@router.get(
    "/fetch-all-sql-codes", response_model=FetchAllSqlCodesResponse, name="fetch_all_sql_codes"
)
async def fetch_all_sql_codes():
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAPRSQLCD FROM DMS_MAPRSQL WHERE CURFLG = 'Y'")
        results = cursor.fetchall()
        cursor.close()

        sql_codes = [row[0] for row in results]
        return FetchAllSqlCodesResponse(
            success=True,
            message=f"Successfully fetched {len(sql_codes)} SQL codes",
            data=sql_codes,
            count=len(sql_codes),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching SQL codes: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/fetch-sql-logic", response_model=FetchSqlLogicResponse)
async def fetch_sql_logic(sql_code: str = Query(..., alias="sql_code")):
    conn = None
    try:
        if not sql_code:
            raise HTTPException(
                status_code=400, detail="SQL code parameter is required"
            )

        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            query = (
                "SELECT MAPRSQL, SQLCONID FROM DMS_MAPRSQL "
                "WHERE MAPRSQLCD = %s AND CURFLG = 'Y'"
            )
            cursor.execute(query, (sql_code,))
        else:
            query = (
                "SELECT MAPRSQL, SQLCONID FROM DMS_MAPRSQL "
                "WHERE MAPRSQLCD = :sql_code AND CURFLG = 'Y'"
            )
            cursor.execute(query, {"sql_code": sql_code})

        result = cursor.fetchone()
        cursor.close()

        if not result:
            return FetchSqlLogicResponse(
                success=False,
                message=f"No SQL logic found for code: {sql_code}",
                data=None,
            )

        sql_content = result[0].read() if hasattr(result[0], "read") else str(result[0])
        connection_id = str(result[1]) if result[1] is not None else None

        return FetchSqlLogicResponse(
            success=True,
            message=f"Successfully fetched SQL logic for code: {sql_code}",
            data=SqlLogicData(
                sql_code=sql_code,
                sql_content=sql_content,
                connection_id=connection_id,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching SQL logic: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/fetch-sql-history", response_model=FetchSqlHistoryResponse)
async def fetch_sql_history(sql_code: str = Query(..., alias="sql_code")):
    conn = None
    try:
        if not sql_code:
            raise HTTPException(
                status_code=400, detail="SQL code parameter is required"
            )

        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            query = (
                "SELECT RECCRDT, MAPRSQL FROM DMS_MAPRSQL "
                "WHERE MAPRSQLCD = %s AND CURFLG = 'N'"
            )
            cursor.execute(query, (sql_code,))
        else:
            query = (
                "SELECT RECCRDT, MAPRSQL FROM DMS_MAPRSQL "
                "WHERE MAPRSQLCD = :sql_code AND CURFLG = 'N'"
            )
            cursor.execute(query, {"sql_code": sql_code})

        results = cursor.fetchall()
        cursor.close()

        if not results:
            return FetchSqlHistoryResponse(
                success=False,
                message=f"No SQL history found for code: {sql_code}",
                data=None,
            )

        history_items: List[HistoryItem] = []
        for row in results:
            date_value = row[0]
            sql_content = row[1].read() if hasattr(row[1], "read") else str(row[1])
            history_items.append(
                HistoryItem(
                    date=date_value.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(date_value, "strftime")
                    else str(date_value),
                    sql_content=sql_content,
                )
            )

        return FetchSqlHistoryResponse(
            success=True,
            message=f"Successfully fetched SQL history for code: {sql_code}",
            data=SqlHistoryData(sql_code=sql_code, history_items=history_items),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching SQL history: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/save-sql", response_model=SaveSqlResponse)
async def save_sql(payload: SaveSqlRequest):
    conn = None
    try:
        sql_code = payload.sql_code
        sql_content = payload.sql_content
        connection_id = payload.connection_id

        if not sql_code:
            raise HTTPException(status_code=400, detail="SQL code is required")
        if not sql_content:
            raise HTTPException(status_code=400, detail="SQL content is required")
        if " " in sql_code:
            raise HTTPException(
                status_code=400, detail="Spaces are not allowed in SQL code"
            )

        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)

        returned_sql_id = create_update_sql(
            conn, sql_code, sql_content, connection_id
        )

        if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()

        return SaveSqlResponse(
            success=True,
            message="SQL saved/updated successfully",
            sql_id=returned_sql_id,
            sql_code=sql_code,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/validate-sql", response_model=ValidateSqlResponse)
async def validate_sql(payload: ValidateSqlRequest):
    conn = None
    try:
        sql_content = payload.sql_content
        connection_id = payload.connection_id

        if not sql_content:
            raise HTTPException(status_code=400, detail="SQL content is required")

        # Mirror Flask behavior:
        # - If connection_id is provided, validate against that target connection.
        # - Otherwise, use metadata connection.
        if connection_id is not None:
            try:
                conn = create_target_connection(connection_id)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Failed to connect to selected database for validation "
                        f"(connection_id={connection_id}): {str(e)}"
                    ),
                )
        else:
            conn = create_metadata_connection()

        result = pkg_validate_sql(conn, sql_content)

        if result == "Y":
            return ValidateSqlResponse(
                success=True,
                message="SQL validation passed successfully",
                is_valid=True,
                validation_result=result,
            )
        else:
            error_msg = result if result != "N" else "SQL validation failed"
            return ValidateSqlResponse(
                success=False,
                message=f"SQL validation failed: {error_msg}",
                is_valid=False,
                validation_result=result,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error during validation: {str(e)}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/get-connections", response_model=List[ConnectionItem])
async def get_connections():
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT conid, connm, dbhost, dbsrvnm
            FROM DMS_DBCONDTLS
            WHERE curflg = 'Y'
            ORDER BY connm
        """
        )

        connections: List[ConnectionItem] = []
        for row in cursor.fetchall():
            connections.append(
                ConnectionItem(
                    conid=str(row[0]),
                    connm=row[1],
                    dbhost=row[2],
                    dbsrvnm=row[3],
                )
            )

        cursor.close()
        return connections
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching connections: {str(e)}"
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


