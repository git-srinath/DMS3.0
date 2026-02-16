from typing import List, Optional

import builtins
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.dbconnect import (
    create_metadata_connection,
    _load_db_driver,
    _parse_standard_connection_url,
)

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import info, error
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import info, error  # type: ignore


router = APIRouter(tags=["db_connections"])

TABLE_NAME = "DMS_DBCONDTLS"


def _detect_db_type(conn) -> str:
    """Detect database type from connection (PostgreSQL vs Oracle)."""
    module_name = builtins.type(conn).__module__
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    if "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    # Fallback with simple queries
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM dual")
        cursor.close()
        return "ORACLE"
    except Exception:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return "POSTGRESQL"
        except Exception:
            return "ORACLE"


def format_error_message(err: Exception) -> str:
    """Port of the Flask helper to keep user-facing messages consistent."""
    error_str = str(err)
    if "DPY-6005" in error_str or "timed out" in error_str.lower():
        return (
            "Unable to connect to the database. Please check if the database "
            "server is running and accessible."
        )
    if "ORA-" in error_str:
        return f"Database error: {error_str}"
    if "connection" in error_str.lower() and "refused" in error_str.lower():
        return (
            "Database connection refused. Please check database server status "
            "and network connectivity."
        )
    return f"An error occurred: {error_str}"


class DbConnectionBase(BaseModel):
    connm: str
    dbtyp: str
    dbhost: str
    # Allow numeric ports (e.g. INTEGER/DECIMAL from DB) as well as strings
    dbport: Optional[str | int] = None
    dbsrvnm: Optional[str] = None
    usrnm: Optional[str] = None
    passwd: Optional[str] = None
    constr: Optional[str] = None
    dbdescr: Optional[str] = None
    sslfg: Optional[str] = "N"


class DbConnectionCreate(DbConnectionBase):
    crtdby: Optional[str] = "system"


class DbConnectionUpdate(DbConnectionBase):
    uptdby: Optional[str] = "system"


class DbConnection(DbConnectionBase):
    conid: int
    curflg: Optional[str] = "Y"

    class Config:
        from_attributes = True


class DbConnectionsResponse(BaseModel):
    success: bool
    data: List[DbConnection]


class DbConnectionSingleResponse(BaseModel):
    success: bool
    data: Optional[DbConnection] = None
    message: Optional[str] = None


class SimpleResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class TestConnectionRequest(BaseModel):
    dbtyp: str
    dbhost: str
    dbport: Optional[str | int] = None
    dbsrvnm: Optional[str] = None
    usrnm: Optional[str] = None
    passwd: Optional[str] = None
    constr: Optional[str] = None


@router.get("/dbconnections", response_model=DbConnectionsResponse)
async def get_all_db_connections():
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, "
            f"dbdescr, sslfg, curflg FROM {TABLE_NAME} WHERE curflg = 'Y'"
        )
        columns = [desc[0].lower() for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return DbConnectionsResponse(
            success=True, data=[DbConnection(**row) for row in rows]
        )
    except Exception as e:  # pragma: no cover - mirrors Flask behavior
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": user_message, "error": str(e)},
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/dbconnections/{conid}", response_model=DbConnectionSingleResponse)
async def get_db_connection(conid: int):
    conn = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, "
                f"dbdescr, sslfg, curflg FROM {TABLE_NAME} "
                "WHERE conid = %s AND curflg = 'Y'",
                (conid,),
            )
        else:
            cursor.execute(
                f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, "
                f"dbdescr, sslfg, curflg FROM {TABLE_NAME} "
                "WHERE conid = :conid AND curflg = 'Y'",
                {"conid": conid},
            )

        row = cursor.fetchone()
        columns = [desc[0].lower() for desc in cursor.description]
        data = dict(zip(columns, row)) if row else None
        cursor.close()

        if not data:
            return DbConnectionSingleResponse(
                success=False, data=None, message="Record not found"
            )

        return DbConnectionSingleResponse(success=True, data=DbConnection(**data))

    except Exception as e:
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": user_message, "error": str(e)},
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/dbconnections", response_model=SimpleResponse)
async def create_db_connection(payload: DbConnectionCreate):
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()

        # Get new conid from sequence
        if db_type == "POSTGRESQL":
            cursor.execute("SELECT nextval('DMS_DBCONDTLSSEQ')")
        else:
            cursor.execute("SELECT DMS_DBCONDTLSSEQ.NEXTVAL FROM dual")
        (conid,) = cursor.fetchone()

        data = payload.dict()

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"""
                INSERT INTO {TABLE_NAME} 
                (conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, 
                 dbdescr, sslfg, reccrdt, recupdt, curflg, crtdby) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s)
            """,
                (
                    conid,
                    data.get("connm"),
                    data.get("dbtyp"),
                    data.get("dbhost"),
                    data.get("dbport"),
                    data.get("dbsrvnm"),
                    data.get("usrnm"),
                    data.get("passwd"),
                    data.get("constr"),
                    data.get("dbdescr"),
                    data.get("sslfg", "N"),
                    data.get("crtdby", "system"),
                ),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {TABLE_NAME} 
                (conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, 
                 dbdescr, sslfg, reccrdt, recupdt, curflg, crtdby) 
                VALUES (:conid, :connm, :dbtyp, :dbhost, :dbport, :dbsrvnm, :usrnm, 
                        :passwd, :constr, :dbdescr, :sslfg, SYSDATE, SYSDATE, 'Y', :crtdby)
            """,
                {
                    "conid": conid,
                    "connm": data.get("connm"),
                    "dbtyp": data.get("dbtyp"),
                    "dbhost": data.get("dbhost"),
                    "dbport": data.get("dbport"),
                    "dbsrvnm": data.get("dbsrvnm"),
                    "usrnm": data.get("usrnm"),
                    "passwd": data.get("passwd"),
                    "constr": data.get("constr"),
                    "dbdescr": data.get("dbdescr"),
                    "sslfg": data.get("sslfg", "N"),
                    "crtdby": data.get("crtdby", "system"),
                },
            )

        if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()

        cursor.close()
        # Return conid in response to match Flask behavior (frontend expects it)
        return {
            "success": True,
            "conid": conid,
            "message": "Connection created successfully"
        }
    except Exception as e:
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except Exception:
                pass
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": user_message, "error": str(e)},
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.put("/dbconnections/{conid}", response_model=SimpleResponse)
async def update_db_connection(conid: int, payload: DbConnectionUpdate):
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        data = payload.dict()

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"""
                UPDATE {TABLE_NAME} SET
                    connm = %s,
                    dbtyp = %s,
                    dbhost = %s,
                    dbport = %s,
                    dbsrvnm = %s,
                    usrnm = %s,
                    passwd = %s,
                    constr = %s,
                    dbdescr = %s,
                    sslfg = %s,
                    recupdt = CURRENT_TIMESTAMP,
                    uptdby = %s
                WHERE conid = %s
            """,
                (
                    data.get("connm"),
                    data.get("dbtyp"),
                    data.get("dbhost"),
                    data.get("dbport"),
                    data.get("dbsrvnm"),
                    data.get("usrnm"),
                    data.get("passwd"),
                    data.get("constr"),
                    data.get("dbdescr"),
                    data.get("sslfg", "N"),
                    data.get("uptdby", "system"),
                    conid,
                ),
            )
        else:
            cursor.execute(
                f"""
                UPDATE {TABLE_NAME} SET
                    connm = :connm,
                    dbtyp = :dbtyp,
                    dbhost = :dbhost,
                    dbport = :dbport,
                    dbsrvnm = :dbsrvnm,
                    usrnm = :usrnm,
                    passwd = :passwd,
                    constr = :constr,
                    dbdescr = :dbdescr,
                    sslfg = :sslfg,
                    recupdt = SYSDATE,
                    uptdby = :uptdby
                WHERE conid = :conid
            """,
                {
                    "conid": conid,
                    "connm": data.get("connm"),
                    "dbtyp": data.get("dbtyp"),
                    "dbhost": data.get("dbhost"),
                    "dbport": data.get("dbport"),
                    "dbsrvnm": data.get("dbsrvnm"),
                    "usrnm": data.get("usrnm"),
                    "passwd": data.get("passwd"),
                    "constr": data.get("constr"),
                    "dbdescr": data.get("dbdescr"),
                    "sslfg": data.get("sslfg", "N"),
                    "uptdby": data.get("uptdby", "system"),
                },
            )

        if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()

        cursor.close()
        return SimpleResponse(success=True, message="Connection updated", error=None)
    except Exception as e:
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except Exception:
                pass
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": user_message, "error": str(e)},
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.delete("/dbconnections/{conid}", response_model=SimpleResponse)
async def delete_db_connection(conid: int):
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()

        if db_type == "POSTGRESQL":
            cursor.execute(
                f"UPDATE {TABLE_NAME} "
                "SET curflg = 'N', actby = %s, actdt = CURRENT_TIMESTAMP "
                "WHERE conid = %s",
                ("system", conid),
            )
        else:
            cursor.execute(
                f"UPDATE {TABLE_NAME} "
                "SET curflg = 'N', actby = :actby, actdt = SYSDATE "
                "WHERE conid = :conid",
                {"conid": conid, "actby": "system"},
            )

        if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()

        cursor.close()
        return SimpleResponse(success=True, message="Connection deleted", error=None)
    except Exception as e:
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, "autocommit", False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except Exception:
                pass
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": user_message, "error": str(e)},
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/dbconnections/test", response_model=SimpleResponse)
async def test_db_connection(payload: TestConnectionRequest):
    """Test a database connection with provided credentials"""
    test_conn = None
    try:
        # Validate required fields
        # If a full connection string is provided, only dbtyp is required.
        # If no connection string is provided, require individual connection pieces.
        base_required = ["dbtyp"]
        if not payload.constr:
            base_required.extend(["dbhost", "dbport", "dbsrvnm", "usrnm", "passwd"])

        missing_fields: list[str] = []
        for field in base_required:
            value = getattr(payload, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                },
            )

        db_type = payload.dbtyp.upper()
        host = payload.dbhost
        port = payload.dbport
        database = payload.dbsrvnm
        username = payload.usrnm
        password = payload.passwd
        connection_string = payload.constr
        
        # Test connection based on database type
        if db_type in ['ORACLE', 'ORACLEDB']:
            import oracledb
            if connection_string:
                # Use custom connection string if provided
                test_conn = oracledb.connect(connection_string)
            else:
                # Build DSN for Oracle
                dsn = f"{host}:{port}/{database}"
                test_conn = oracledb.connect(
                    user=username,
                    password=password,
                    dsn=dsn
                )
            # Test with a simple query
            cursor = test_conn.cursor()
            cursor.execute("SELECT 1 FROM dual")
            cursor.fetchone()
            cursor.close()
            
        elif db_type == 'POSTGRESQL':
            import psycopg2
            if connection_string:
                test_conn = psycopg2.connect(connection_string)
            else:
                test_conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password
                )
            cursor = test_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
        elif db_type == 'MYSQL':
            # Use shared driver loader/parsing logic for MySQL
            mysql_connector = _load_db_driver("MYSQL")
            if connection_string:
                # Expect a standard mysql://user:pass@host:port/dbname style URL
                parsed = _parse_standard_connection_url(connection_string, expected_scheme="mysql")
                test_conn = mysql_connector.connect(
                    host=parsed["host"],
                    port=parsed["port"] or 3306,
                    database=parsed["database"],
                    user=parsed["username"],
                    password=parsed["password"],
                )
            else:
                test_conn = mysql_connector.connect(
                    host=host,
                    port=int(port) if port else 3306,
                    database=database,
                    user=username,
                    password=password,
                )
            cursor = test_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
        elif db_type in ['SQLSERVER', 'MSSQL', 'SQL SERVER']:
            import pyodbc
            if connection_string:
                test_conn = pyodbc.connect(connection_string)
            else:
                # Build connection string for SQL Server
                driver = '{ODBC Driver 17 for SQL Server}'  # Common driver
                conn_str = f"DRIVER={driver};SERVER={host},{port};DATABASE={database};UID={username};PWD={password}"
                test_conn = pyodbc.connect(conn_str)
            cursor = test_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Unsupported database type: {db_type}. Supported types: Oracle, PostgreSQL, MySQL, SQL Server"
                }
            )
        
        info(f"Test connection successful for {db_type} database: {host}:{port}/{database}")
        return SimpleResponse(
            success=True,
            message=f"Connection test successful! Successfully connected to {db_type} database."
        )
        
    except ImportError as e:
        error(f"Database driver not installed: {str(e)}")
        missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Database driver not installed. Please install: {missing_module}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Test connection failed: {str(e)}")
        user_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": user_message,
                "error": str(e)
            }
        )
    finally:
        if test_conn:
            try:
                test_conn.close()
            except Exception:
                pass


