"""
File Upload Service
Business logic for file upload CRUD operations.
"""
import datetime
from typing import Optional, Dict, Any, List
from backend.database.dbconnect import create_metadata_connection
from backend.modules.common.db_table_utils import _detect_db_type
from backend.modules.helper_functions import _get_table_ref
from backend.modules.common.id_provider import next_id
from backend.modules.logger import info, error


def create_update_file_upload(
    connection,
    flupldref: str,
    fluplddesc: Optional[str] = None,
    flnm: Optional[str] = None,
    flpth: Optional[str] = None,
    fltyp: Optional[str] = None,
    trgconid: Optional[int] = None,
    trgschm: Optional[str] = None,
    trgtblnm: Optional[str] = None,
    trnctflg: str = "N",
    hdrrwcnt: int = 0,
    ftrrwcnt: int = 0,
    hdrrwpttrn: Optional[str] = None,
    ftrrwpttrn: Optional[str] = None,
    frqcd: Optional[str] = None,
    stflg: str = "N",
    crtdby: Optional[str] = None,
    flupldid: Optional[int] = None,
    batch_size: Optional[int] = 1000
) -> int:
    """
    Create or update file upload configuration.
    
    Args:
        connection: Database connection
        flupldref: File upload reference (unique identifier)
        fluplddesc: Description
        flnm: File name
        flpth: File path
        fltyp: File type (CSV, XLSX, JSON, etc.)
        trgconid: Target connection ID
        trgschm: Target schema
        trgtblnm: Target table name
        trnctflg: Truncate flag (Y/N)
        hdrrwcnt: Header rows count
        ftrrwcnt: Footer rows count
        hdrrwpttrn: Header row pattern
        ftrrwpttrn: Footer row pattern
        frqcd: Frequency code
        stflg: Status flag (A=Active, N=Inactive)
        crtdby: Created by user
        flupldid: File upload ID (if updating existing record)
        
    Returns:
        File upload ID
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
    
    try:
        # Check if record exists (any curflg)
        if flupldid is None:
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"SELECT flupldid FROM {table_name} WHERE flupldref = %s",
                    (flupldref,)
                )
            else:
                cursor.execute(
                    f"SELECT flupldid FROM {table_name} WHERE flupldref = :1",
                    [flupldref]
                )
            existing = cursor.fetchone()
            if existing:
                flupldid = existing[0]
        
        if flupldid:
            # Update existing record in place (avoid unique constraint issues)
            info(f"Updating file upload in place: flupldref={flupldref}, flupldid={flupldid}")
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"""
                    UPDATE {table_name}
                    SET fluplddesc = %s,
                        flnm = %s,
                        flpth = %s,
                        fltyp = %s,
                        trgconid = %s,
                        trgschm = %s,
                        trgtblnm = %s,
                        trnctflg = %s,
                        hdrrwcnt = %s,
                        ftrrwcnt = %s,
                        hdrrwpttrn = %s,
                        ftrrwpttrn = %s,
                        frqcd = %s,
                        stflg = %s,
                        batch_size = %s,
                        uptdby = %s,
                        uptdt = CURRENT_TIMESTAMP,
                        curflg = 'Y'
                    WHERE flupldid = %s
                    """,
                    (
                        fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                        trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd,
                        stflg, batch_size or 1000, crtdby, flupldid
                    )
                )
            else:  # Oracle
                cursor.execute(
                    f"""
                    UPDATE {table_name}
                    SET fluplddesc = :2,
                        flnm = :3,
                        flpth = :4,
                        fltyp = :5,
                        trgconid = :6,
                        trgschm = :7,
                        trgtblnm = :8,
                        trnctflg = :9,
                        hdrrwcnt = :10,
                        ftrrwcnt = :11,
                        hdrrwpttrn = :12,
                        ftrrwpttrn = :13,
                        frqcd = :14,
                        stflg = :15,
                        batch_size = :16,
                        uptdby = :17,
                        uptdate = SYSTIMESTAMP,
                        curflg = 'Y'
                    WHERE flupldid = :1
                    """,
                    [
                        flupldid, fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                        trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd, stflg, batch_size or 1000, crtdby
                    ]
                )
            return flupldid
        else:
            # Insert new record
            info(f"Creating new file upload: flupldref={flupldref}")
            flupldid = next_id(cursor, "DMS_FLUPLDSEQ")
            
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                     trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd, stflg, batch_size,
                     crtdby, crtdt, curflg)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'Y')
                    """,
                    (flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                     trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd, stflg, batch_size or 1000,
                     crtdby,)
                )
            else:  # Oracle
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                     trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd, stflg, batch_size,
                     crtdby, crtdate, curflg)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, :18, SYSTIMESTAMP, 'Y')
                    """,
                    [flupldid, flupldref, fluplddesc, flnm, flpth, fltyp, trgconid, trgschm, trgtblnm,
                     trnctflg, hdrrwcnt, ftrrwcnt, hdrrwpttrn, ftrrwpttrn, frqcd, stflg, batch_size or 1000,
                     crtdby]
                )
            
            return flupldid
    
    except Exception as e:
        error(f"Error in create_update_file_upload: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()


def create_update_file_upload_detail(
    connection,
    flupldref: str,
    trgclnm: str,
    srcclnm: Optional[str] = None,
    trgcldtyp: Optional[str] = None,
    trgkyflg: str = "N",
    trgkyseq: Optional[int] = None,
    trgcldesc: Optional[str] = None,
    drvlgc: Optional[str] = None,
    drvlgcflg: str = "N",
    excseq: Optional[int] = None,
    isaudit: str = "N",
    audttyp: Optional[str] = None,
    dfltval: Optional[str] = None,
    isrqrd: str = "N",
    crtdby: Optional[str] = None,
    fluplddtlid: Optional[int] = None
) -> int:
    """
    Create or update file upload detail (column mapping).
    
    Args:
        connection: Database connection
        flupldref: File upload reference
        trgclnm: Target column name
        srcclnm: Source column name
        trgcldtyp: Target column data type
        trgkyflg: Primary key flag (Y/N)
        trgkyseq: Primary key sequence
        trgcldesc: Column description
        drvlgc: Derivation logic
        drvlgcflg: Logic verified flag (Y/N)
        excseq: Execution sequence
        isaudit: Is audit column (Y/N)
        audttyp: Audit type
        dfltval: Default value
        isrqrd: Is required (Y/N)
        crtdby: Created by user
        fluplddtlid: Detail ID (if updating)
        
    Returns:
        File upload detail ID
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLDDTL")
    
    try:
        if fluplddtlid:
            # Update existing record
            info(f"Updating file upload detail: fluplddtlid={fluplddtlid}")
            
            # Set curflg to 'N' for old record
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"UPDATE {table_name} SET curflg = 'N', uptdt = CURRENT_TIMESTAMP WHERE fluplddtlid = %s",
                    (fluplddtlid,)
                )
            else:  # Oracle
                cursor.execute(
                    f"UPDATE {table_name} SET curflg = 'N', uptdate = SYSTIMESTAMP WHERE fluplddtlid = :1",
                    [fluplddtlid]
                )
            
            # Generate new ID
            new_fluplddtlid = next_id(cursor, "DMS_FLUPLDDTLSEQ")
            
            # Insert new record
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdt, uptdby, uptdt, curflg)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, CURRENT_TIMESTAMP, 'Y')
                    """,
                    (new_fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdby)
                )
            else:  # Oracle
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdate, uptdby, uptdate, curflg)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, SYSTIMESTAMP, :18, SYSTIMESTAMP, 'Y')
                    """,
                    [new_fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdby]
                )
            
            return new_fluplddtlid
        else:
            # Insert new record
            info(f"Creating new file upload detail: flupldref={flupldref}, trgclnm={trgclnm}")
            fluplddtlid = next_id(cursor, "DMS_FLUPLDDTLSEQ")
            
            if db_type == "POSTGRESQL":
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdt, curflg)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'Y')
                    """,
                    (fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby)
                )
            else:  # Oracle
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} 
                    (fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby, crtdate, curflg)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, SYSTIMESTAMP, 'Y')
                    """,
                    [fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                     trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd,
                     crtdby]
                )
            
            return fluplddtlid
    
    except Exception as e:
        error(f"Error in create_update_file_upload_detail: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()


def delete_file_upload(connection, flupldref: str) -> bool:
    """
    Delete file upload configuration (soft delete by setting curflg='N').
    
    Args:
        connection: Database connection
        flupldref: File upload reference
        
    Returns:
        True if deleted successfully
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
    detail_table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLDDTL")
    
    try:
        if db_type == "POSTGRESQL":
            # Soft delete main record
            cursor.execute(
                f"UPDATE {table_name} SET curflg = 'N', uptdt = CURRENT_TIMESTAMP WHERE flupldref = %s AND curflg = 'Y'",
                (flupldref,)
            )
            # Soft delete detail records
            cursor.execute(
                f"UPDATE {detail_table_name} SET curflg = 'N', uptdt = CURRENT_TIMESTAMP WHERE flupldref = %s AND curflg = 'Y'",
                (flupldref,)
            )
        else:  # Oracle
            cursor.execute(
                f"UPDATE {table_name} SET curflg = 'N', uptdate = SYSTIMESTAMP WHERE flupldref = :1 AND curflg = 'Y'",
                [flupldref]
            )
            cursor.execute(
                f"UPDATE {detail_table_name} SET curflg = 'N', uptdate = SYSTIMESTAMP WHERE flupldref = :1 AND curflg = 'Y'",
                [flupldref]
            )
        
        return True
    
    except Exception as e:
        error(f"Error in delete_file_upload: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()


def activate_deactivate_file_upload(connection, flupldref: str, stflg: str) -> bool:
    """
    Activate or deactivate file upload configuration.
    
    Args:
        connection: Database connection
        flupldref: File upload reference
        stflg: Status flag ('A' for Active, 'N' for Inactive)
        
    Returns:
        True if updated successfully
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLD")
    
    try:
        if db_type == "POSTGRESQL":
            cursor.execute(
                f"UPDATE {table_name} SET stflg = %s, uptdt = CURRENT_TIMESTAMP WHERE flupldref = %s AND curflg = 'Y'",
                (stflg, flupldref)
            )
        else:  # Oracle
            cursor.execute(
                f"UPDATE {table_name} SET stflg = :1, uptdate = SYSTIMESTAMP WHERE flupldref = :2 AND curflg = 'Y'",
                [stflg, flupldref]
            )
        
        return True
    
    except Exception as e:
        error(f"Error in activate_deactivate_file_upload: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()


def get_file_upload_details(connection, flupldref: str) -> List[Dict[str, Any]]:
    """
    Get all column mappings for a file upload configuration.
    
    Args:
        connection: Database connection
        flupldref: File upload reference
        
    Returns:
        List of column mapping dictionaries
    """
    cursor = connection.cursor()
    db_type = _detect_db_type(connection)
    table_name = _get_table_ref(cursor, db_type, "DMS_FLUPLDDTL")
    
    try:
        if db_type == "POSTGRESQL":
            query = f"""
                SELECT fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                       trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd
                FROM {table_name}
                WHERE flupldref = %s AND curflg = 'Y'
                ORDER BY excseq, trgclnm
            """
            cursor.execute(query, (flupldref,))
        else:  # Oracle
            query = f"""
                SELECT fluplddtlid, flupldref, srcclnm, trgclnm, trgcldtyp, trgkyflg, trgkyseq,
                       trgcldesc, drvlgc, drvlgcflg, excseq, isaudit, audttyp, dfltval, isrqrd
                FROM {table_name}
                WHERE flupldref = :1 AND curflg = 'Y'
                ORDER BY excseq, trgclnm
            """
            cursor.execute(query, [flupldref])
        
        columns = [desc[0].lower() for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return rows
    
    except Exception as e:
        error(f"Error in get_file_upload_details: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()

