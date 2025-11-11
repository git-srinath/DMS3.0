import os
import oracledb
import dotenv
from modules.logger import logger, info, warning, error
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
            TRGTBNM, FRQCD, SRCSYSTM, STFLG, BLKPRCROWS, LGVRFYFLG
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
     
            ORDER BY MAPDTLID
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
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter for error message
        p_err = cursor.var(oracledb.STRING, 2000)  # Assuming error message can be up to 2000 chars
        
        # SQL to execute with named parameters
        sql = """
        BEGIN
            PKGDWMAPR.ACTIVATE_DEACTIVATE_MAPPING(
                p_mapref => :p_mapref,
                p_stflg => :p_stflg,
                p_err => :p_err
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            p_mapref=p_mapref,
            p_stflg=p_stflg,
            p_err=p_err
        )
        connection.commit()
        
        # Get the error message (if any)
        error_message = p_err.getvalue()
        
        if error_message:
            return False, f"Error: {error_message}"
        else:
            action = "activated" if p_stflg == "A" else "deactivated"
            return True, f"Mapping {p_mapref} successfully {action}"
    
    except Exception as e:
        error_message = f"Exception while activating/deactivating mapping: {str(e)}"
        return False, error_message
    
    finally:
        if cursor:
            cursor.close()

# mapping function

def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, 
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, p_stflg,p_blkprcrows,user_id):

    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter
        v_mapid = cursor.var(oracledb.NUMBER)
        
        # SQL to execute with named parameters
        sql = f"""
        BEGIN
            :result := {ORACLE_SCHEMA}.PKGDWMAPR.CREATE_UPDATE_MAPPING(
                p_mapref => :p_mapref,
                p_mapdesc => :p_mapdesc,
                p_trgschm => :p_trgschm,
                p_trgtbtyp => :p_trgtbtyp,
                p_trgtbnm => :p_trgtbnm,
                p_frqcd => :p_frqcd,
                p_srcsystm => :p_srcsystm,
                p_lgvrfyflg => :p_lgvrfyflg,
                p_lgvrfydt => :p_lgvrfydt,
                p_stflg => :p_stflg,
                p_blkprcrows=>:p_blkprcrows,
                p_user=>:p_user
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            result=v_mapid,
            p_mapref=p_mapref,
            p_mapdesc=p_mapdesc,
            p_trgschm=p_trgschm,
            p_trgtbtyp=p_trgtbtyp,
            p_trgtbnm=p_trgtbnm,
            p_frqcd=p_frqcd,
            p_srcsystm=p_srcsystm,
            p_lgvrfyflg=p_lgvrfyflg,
            p_lgvrfydt=p_lgvrfydt,
            p_stflg=p_stflg,
            p_blkprcrows=p_blkprcrows,
            p_user=user_id
        )
        
        # Get the result
        mapid = v_mapid.getvalue()

        return mapid
        
    except Exception as e:
        error(f"Error creating/updating mapping: {str(e)}")
        raise
        
    finally:
        if cursor:
            cursor.close()


def create_update_mapping_detail(connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, 
                               p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm, 
                               p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp, p_lgvrfyflg, p_lgvrfydt,user_id):
 
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter
        v_mapdtlid = cursor.var(oracledb.NUMBER)
        
        # SQL to execute with named parameters
        sql = f"""
        BEGIN
            :result := {ORACLE_SCHEMA}.PKGDWMAPR.CREATE_UPDATE_MAPPING_DETAIL(
                p_mapref => :p_mapref,
                p_trgclnm => :p_trgclnm,
                p_trgcldtyp => :p_trgcldtyp,
                p_trgkeyflg => :p_trgkeyflg,
                p_trgkeyseq => :p_trgkeyseq,
                p_trgcldesc => :p_trgcldesc,
                p_maplogic => :p_maplogic,
                p_keyclnm => :p_keyclnm,
                p_valclnm => :p_valclnm,
                p_mapcmbcd => :p_mapcmbcd,
                p_excseq => :p_excseq,
                p_scdtyp => :p_scdtyp,
                p_lgvrfyflg => :p_lgvrfyflg,
                p_lgvrfydt => :p_lgvrfydt,
                p_user=>:p_user
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            result=v_mapdtlid,
            p_mapref=p_mapref,
            p_trgclnm=p_trgclnm,
            p_trgcldtyp=p_trgcldtyp,
            p_trgkeyflg=p_trgkeyflg,
            p_trgkeyseq=p_trgkeyseq,
            p_trgcldesc=p_trgcldesc,
            p_maplogic=p_maplogic,
            p_keyclnm=p_keyclnm,
            p_valclnm=p_valclnm,
            p_mapcmbcd=p_mapcmbcd,
            p_excseq=p_excseq,
            p_scdtyp=p_scdtyp,
            p_lgvrfyflg=p_lgvrfyflg,
            p_lgvrfydt=p_lgvrfydt,
            p_user=user_id
        )
        
        # Get the result
        mapdtlid = v_mapdtlid.getvalue()
        return mapdtlid
        
    except Exception as e:
        error(f"Error creating/updating mapping detail: {str(e)}")
        raise
        
    finally:
        if cursor:
            cursor.close()

def validate_logic_in_db(connection, p_logic, p_keyclnm, p_valclnm):

    cursor = connection.cursor()
    v_is_valid = cursor.var(oracledb.STRING)
    
    sql = f"""
    BEGIN
        :result := {ORACLE_SCHEMA}.PKGDWMAPR.VALIDATE_LOGIC(
            p_logic => :p_logic,
            p_keyclnm => :p_keyclnm,
            p_valclnm => :p_valclnm
        );
    END;
    """
    
    cursor.execute(
        sql,
        result=v_is_valid,
        p_logic=p_logic,
        p_keyclnm=p_keyclnm,
        p_valclnm=p_valclnm
    )
    connection.commit()
    
    return v_is_valid.getvalue()



def validate_logic2(connection, p_logic, p_keyclnm, p_valclnm):

    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameters
        v_is_valid = cursor.var(oracledb.STRING)
        v_error = cursor.var(oracledb.STRING, 4000)  # Error output parameter
        
        # SQL to execute with named parameters
        sql = f"""
        BEGIN
            :result := {ORACLE_SCHEMA}.PKGDWMAPR.VALIDATE_LOGIC2(
                p_logic => :p_logic,
                p_keyclnm => :p_keyclnm,
                p_valclnm => :p_valclnm,
                p_err => :p_err
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            result=v_is_valid,
            p_logic=p_logic,
            p_keyclnm=p_keyclnm,
            p_valclnm=p_valclnm,
            p_err=v_error
        )
        connection.commit()
        
        # Get the results
        is_valid = v_is_valid.getvalue()
        error_message = v_error.getvalue()
        
        return is_valid, error_message
    
    except Exception as e:
        error(f"Error validating logic: {str(e)}")
        raise
    
    finally:
        if cursor:
            cursor.close()

def validate_all_mapping_details(connection, p_mapref):

    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameters
        v_result = cursor.var(oracledb.STRING)
        v_err = cursor.var(oracledb.STRING, 400)  # VARCHAR2(400) in Oracle
        
        # SQL to execute with named parameters
        sql = f"""
        BEGIN
            :result := {ORACLE_SCHEMA}.PKGDWMAPR.VALIDATE_MAPPING_DETAILS(
                p_mapref => :p_mapref,
                p_err => :p_err
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            result=v_result,
            p_mapref=p_mapref,
            p_err=v_err
        )
        connection.commit()
        # Get the results
        result = v_result.getvalue()
        error_message = v_err.getvalue()
        
        return result, error_message
        
    except Exception as e:
        error(f"Error validating mapping details: {str(e)}")
        raise
        
    finally:
        if cursor:
            cursor.close()


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

    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter for job_id
        v_job_id = cursor.var(oracledb.NUMBER)  # Assuming jobid is a NUMBER in Oracle
        
        # SQL to execute with named parameters
        sql = f"""
        BEGIN
            :job_id := {ORACLE_SCHEMA}.PKGDWJOB.CREATE_UPDATE_JOB(
                p_mapref => :p_mapref
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            job_id=v_job_id,
            p_mapref=p_mapref
        )
        connection.commit()
        
        # Get the result
        job_id = v_job_id.getvalue()
        
        return job_id, None
    
    except Exception as e:
        error_message = f"Error creating/updating job: {str(e)}"
        error(error_message)
        return None, error_message
    
    finally:
        if cursor:
            cursor.close()

def call_delete_mapping(connection, p_mapref):
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter for error message
        p_err = cursor.var(oracledb.STRING, 2000)  # Assuming error message can be up to 2000 chars
        
        # SQL to execute with named parameters
        sql = """
        BEGIN
            PKGDWMAPR.DELETE_MAPPING(
                p_mapref => :p_mapref,
                p_err => :p_err
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            p_mapref=p_mapref,
            p_err=p_err
        )
        connection.commit()
        
        # Get the error message (if any)
        error_message = p_err.getvalue()
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping {p_mapref} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping: {str(e)}"
        return False, error_message
    finally:
        if cursor:
            cursor.close()

def call_delete_mapping_details(connection, p_mapref, p_trgclnm):
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Define the output parameter for error message
        p_err = cursor.var(oracledb.STRING, 2000)  # Assuming error message can be up to 2000 chars
        
        # SQL to execute with named parameters
        sql = """
        BEGIN
            PKGDWMAPR.DELETE_MAPPING_DETAILS(
                p_mapref => :p_mapref,
                p_trgclnm => :p_trgclnm,
                p_err => :p_err
            );
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            p_mapref=p_mapref,
            p_trgclnm=p_trgclnm,
            p_err=p_err
        )
        connection.commit()
        
        # Get the error message (if any)
        error_message = p_err.getvalue()
        
        if error_message:
            return False, error_message
        else:
            return True, f"Mapping detail {p_mapref}-{p_trgclnm} successfully deleted"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping detail: {str(e)}"
        return False, error_message
    finally:
        if cursor:
            cursor.close()






