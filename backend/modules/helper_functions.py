import os
import oracledb
import dotenv
from modules.logger import logger, info, warning, error
from modules.mapper import pkgdwmapr_python as pkgdwmapr
dotenv.load_dotenv()

ORACLE_SCHEMA = os.getenv("SCHEMA")

def get_parameter_mapping(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT FROM DWPARAMS"
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows and convert to dictionaries
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def add_parameter_mapping(conn, type, code, desc, value):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO DWPARAMS (PRTYP, PRCD, PRDESC, PRVAL, PRRECCRDT, PRRECUPDT)
            VALUES (:1, :2, :3, :4, sysdate, sysdate)
        """
        cursor.execute(query, [type, code, desc, value])
        conn.commit()
        cursor.close()
        return "Parameter mapping added successfully."
    except Exception as e:
        error(f"Error adding parameter mapping: {str(e)}")
        raise

def get_mapping_ref(conn, reference):
    """Fetch reference data from DWMAPR table"""
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
            MAPID, MAPREF, MAPDESC, TRGSCHM, TRGTBTYP, 
            TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG, TRGCONID,
            CHKPNTSTRTGY, CHKPNTCLNM, CHKPNTENBLD
            FROM DWMAPR WHERE MAPREF = :1  AND  CURFLG = 'Y'

        """
        cursor.execute(query, [reference])
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch one row and convert to dictionary
        row = cursor.fetchone()
        result = dict(zip(columns, row)) if row else None
        
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching mapping reference: {str(e)}")
        raise

def get_mapping_details(conn, reference):
    """Fetch mapping details from DWMAPRDTL table"""
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                MAPDTLID, MAPREF, TRGCLNM, TRGCLDTYP, TRGKEYFLG, 
                TRGKEYSEQ, TRGCLDESC, MAPLOGIC, KEYCLNM, 
                VALCLNM, MAPCMBCD, EXCSEQ, SCDTYP, LGVRFYFLG
            FROM DWMAPRDTL 
            WHERE MAPREF = :1
            and CURFLG='Y'
     
            ORDER BY EXCSEQ NULLS LAST, MAPDTLID
        """
        cursor.execute(query, [reference])
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows and convert to dictionaries
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching mapping details: {str(e)}")
        raise

def check_if_job_already_created(connection, p_mapref):
    cursor = None
    try:
        cursor = connection.cursor()
        sql = """
        SELECT COUNT(*) FROM DWJOB WHERE CURFLG ='Y' AND MAPREF = :p_mapref    
        """
        cursor.execute(sql, {'p_mapref': p_mapref})
        count = cursor.fetchone()[0]
        if count > 0:
            return 'Y'
        else:
            return 'N'
    except Exception as e:
        return 'N'
    finally:
        if cursor:
            cursor.close()  

def get_error_message(conn, map_detail_id):
    """ref: refernece of detail mapping table"""
    try:
        cursor = conn.cursor()
        query = """
            SELECT errmsg FROM DWMAPERR 
            WHERE DWMAPERR.MAPDTLID = :1 
            ORDER BY DWMAPERR.MAPERRID DESC 
            FETCH FIRST 1 ROWS ONLY 
        """
        cursor.execute(query, [map_detail_id])
        
        # Fetch one row
        row = cursor.fetchone()
        
        cursor.close()
        
        if not row:
            return "Logic is Verified"
        
        return row[0]  # Return the first column value
    except Exception as e:
        error(f"Error getting error message: {str(e)}")
        raise

def get_error_messages_list(conn, map_detail_ids):
    try:
        result_dict = {}
        cursor = conn.cursor()
        query = """
            SELECT errmsg FROM DWMAPERR
            WHERE DWMAPERR.MAPDTLID = :1
            ORDER BY DWMAPERR.MAPERRID DESC
            FETCH FIRST 1 ROWS ONLY
        """
       
        for map_detail_id in map_detail_ids:
            cursor.execute(query, [map_detail_id])
           
            # Fetch one row
            row = cursor.fetchone()
           
            if not row:
                result_dict[map_detail_id] = "Logic is Verified"
            else:
                result_dict[map_detail_id] = row[0]  # Return the first column value
       
        cursor.close()
        return result_dict
       
    except Exception as e:
        error(f"Error getting error messages: {str(e)}")
        raise
def get_parameter_mapping_datatype(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT PRCD, PRDESC ,PRVAL FROM DWPARAMS WHERE PRTYP = 'Datatype'"
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows and convert to dictionaries
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def get_parameter_mapping_scd_type(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT PRCD, PRDESC , PRVAL FROM DWPARAMS WHERE PRTYP = 'SCD'"
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows and convert to dictionaries
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching parameter mapping: {str(e)}")
        raise

def call_activate_deactivate_mapping(connection, p_mapref, p_stflg):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.activate_deactivate_mapping(connection, p_mapref, p_stflg)
        
        if error_message:
            return False, f"Error: {error_message}"
        else:
            action = "activated" if p_stflg == "A" else "deactivated"
            return True, f"Mapping {p_mapref} successfully {action}"
    
    except Exception as e:
        error_message = f"Exception while activating/deactivating mapping: {str(e)}"
        return False, error_message

# mapping function

def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, 
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, p_stflg, p_blkprcrows, 
                         p_trgconid=None, p_user=None, p_chkpntstrtgy='AUTO', p_chkpntclnm=None, p_chkpntenbld='Y'):

    try:
        # Call Python function instead of PL/SQL package
        mapid = pkgdwmapr.create_update_mapping(
            connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
            p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
            p_stflg, p_blkprcrows, p_trgconid=p_trgconid, p_user=p_user,
            p_chkpntstrtgy=p_chkpntstrtgy, p_chkpntclnm=p_chkpntclnm, p_chkpntenbld=p_chkpntenbld
        )
        
        return mapid
        
    except Exception as e:
        error(f"Error creating/updating mapping: {str(e)}")
        raise


def create_update_mapping_detail(connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, 
                               p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm, 
                               p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp, p_lgvrfyflg, p_lgvrfydt,user_id):
 
    try:
        # Call Python function instead of PL/SQL package
        mapdtlid = pkgdwmapr.create_update_mapping_detail(
            connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg,
            p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm,
            p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp,
            p_lgvrfyflg, p_lgvrfydt, user_id
        )
        
        return mapdtlid
        
    except Exception as e:
        error(f"Error creating/updating mapping detail: {str(e)}")
        raise

def validate_logic_in_db(connection, p_logic, p_keyclnm, p_valclnm):
    
    try:
        # Call Python function instead of PL/SQL package
        is_valid = pkgdwmapr.validate_logic(connection, p_logic, p_keyclnm, p_valclnm)
        return is_valid
        
    except Exception as e:
        error(f"Error validating logic: {str(e)}")
        raise



def validate_logic2(connection, p_logic, p_keyclnm, p_valclnm):

    try:
        # Call Python function instead of PL/SQL package
        is_valid, error_message = pkgdwmapr.validate_logic2(connection, p_logic, p_keyclnm, p_valclnm)
        
        return is_valid, error_message
    
    except Exception as e:
        error(f"Error validating logic: {str(e)}")
        raise

def validate_all_mapping_details(connection, p_mapref):

    try:
        # Call Python function instead of PL/SQL package
        result, error_message = pkgdwmapr.validate_mapping_details(connection, p_mapref)
        
        return result, error_message
        
    except Exception as e:
        error(f"Error validating mapping details: {str(e)}")
        raise


# job function

def get_job_list(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT JOBID, MAPID, MAPREF, FRQCD, TRGSCHM, TRGTBTYP, TRGTBNM, SRCSYSTM, STFLG, RECCRDT, RECUPDT, CURFLG, BLKPRCROWS FROM DWJOB"
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows and convert to dictionaries
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
            
        cursor.close()
        return result
    except Exception as e:
        error(f"Error fetching job list: {str(e)}")
        raise


def call_create_update_job(connection, p_mapref):
    """
    Create or update job using Python implementation with hash-based change detection.
    
    Args:
        connection: Oracle database connection
        p_mapref: Mapping reference
        
    Returns:
        Tuple of (job_id, error_message)
    """
    try:
        # Import Python implementation
        from modules.jobs import pkgdwjob_python as pkgdwjob
        
        # Call Python version
        job_id = pkgdwjob.create_update_job(connection, p_mapref)
        
        if job_id:
            info(f"Job created/updated successfully for {p_mapref}: JobID={job_id}")
            return job_id, None
        else:
            error_message = f"Failed to create/update job for {p_mapref}"
            error(error_message)
            return None, error_message
    
    except Exception as e:
        error_message = f"Error creating/updating job: {str(e)}"
        error(error_message)
        return None, error_message

def call_delete_mapping(connection, p_mapref):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.delete_mapping(connection, p_mapref)
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping {p_mapref} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping: {str(e)}"
        return False, error_message

def call_delete_mapping_details(connection, p_mapref, p_trgclnm):
    try:
        # Call Python function instead of PL/SQL package
        error_message = pkgdwmapr.delete_mapping_details(connection, p_mapref, p_trgclnm)
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping detail {p_mapref}-{p_trgclnm} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping detail: {str(e)}"
        return False, error_message






