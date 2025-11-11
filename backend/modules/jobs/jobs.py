from flask import Blueprint, request, jsonify
from modules.helper_functions import get_job_list,call_create_update_job,get_mapping_ref,get_mapping_details
from database.dbconnect import create_oracle_connection
import os
import dotenv
import oracledb
import threading
import pandas as pd
import json
import traceback
from modules.logger import logger, info, warning, error, exception
from datetime import datetime
dotenv.load_dotenv()
ORACLE_SCHEMA = os.getenv("SCHEMA")
# Create blueprint
jobs_bp = Blueprint('jobs', __name__)



@jobs_bp.route("/jobs_list", methods=["GET"])
def jobs():
    try:
        conn = create_oracle_connection()
        try:
            job_list = get_job_list(conn)
           
            # Convert datetime objects to ISO format strings for JSON serialization
            for job in job_list:
                if 'RECCRDT' in job and job['RECCRDT']:
                    job['RECCRDT'] = job['RECCRDT'].isoformat()
                if 'RECUPDT' in job and job['RECUPDT']:
                    job['RECUPDT'] = job['RECUPDT'].isoformat()
           
            return jsonify(job_list)
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
@jobs_bp.route("/view_mapping/<mapping_reference>")
def job_mapping_view(mapping_reference):
    try:
        conn = create_oracle_connection()
        try:
            # Get mapping reference and details data
            mapping_ref_data = get_mapping_ref(conn, reference=mapping_reference)
            mapping_detail_data = get_mapping_details(conn, reference=mapping_reference)
           
            # Prepare the response
            response_data = {
                "mapping_reference": mapping_ref_data,
                "mapping_details": mapping_detail_data
            }
           
            return jsonify(response_data)
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/create-update', methods=['POST'])
def create_update_job():
    try:
        data = request.json
        p_mapref = data.get('mapref')
        
        if not p_mapref:
            return jsonify({
                'success': False,
                'message': 'Missing required parameter: mapref'
            }), 400
            
        conn = create_oracle_connection()
        try:
            job_id, error_message = call_create_update_job(conn, p_mapref)
            
            if error_message:
                return jsonify({
                    'success': False,
                    'message': error_message
                }), 500
                
            return jsonify({
                'success': True,
                'message': 'Job created/updated successfully',
                'job_id': job_id
            })
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in create_update_job: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred while processing the request: {str(e)}'
        }), 500 

@jobs_bp.route('/get_all_jobs', methods=['GET'])
def get_all_jobs():
    try:
        conn = create_oracle_connection()
        query_job_flow = f"""

               SELECT 
            f.JOBFLWID,
            f.MAPREF,
            f.TRGSCHM,
            f.TRGTBTYP,
            f.TRGTBNM,
            f.DWLOGIC,
            f.STFLG,
            CASE 
                WHEN s.SCHFLG = 'Y' THEN 'Scheduled'
                ELSE 'Not Scheduled'
            END AS JOB_SCHEDULE_STATUS,
            s.JOBSCHID,
            s.DPND_JOBSCHID,
            s.FRQCD AS "Frequency code",
            s.FRQDD AS "Frequency day",
            s.FRQHH AS "frequency hour",
            s.FRQMI AS "frequency month",
            s.STRTDT AS "start date",
            s.ENDDT AS "end date"
        FROM 
            {ORACLE_SCHEMA}.DWJOBFLW f
        LEFT JOIN 
            (
                SELECT 
                    JOBFLWID, 
                    MIN(JOBSCHID) AS JOBSCHID, 
                    MIN(DPND_JOBSCHID) AS DPND_JOBSCHID,
                    MIN(FRQCD) AS FRQCD,
                    MIN(FRQDD) AS FRQDD,
                    MIN(FRQHH) AS FRQHH,
                    MIN(FRQMI) AS FRQMI,
                    MIN(STRTDT) AS STRTDT,
                    MIN(ENDDT) AS ENDDT,
                    MAX(SCHFLG) AS SCHFLG
                FROM 
                    {ORACLE_SCHEMA}.DWJOBSCH
                WHERE 
                    CURFLG = 'Y'
                GROUP BY 
                    JOBFLWID
            ) s
        ON 
            f.JOBFLWID = s.JOBFLWID
        WHERE 
            f.CURFLG = 'Y'


        """
        cursor = conn.cursor()
        cursor.execute(query_job_flow)
        columns = [col[0] for col in cursor.description]
        raw_jobs = cursor.fetchall()
    
        # Convert LOB objects to strings and create a list of dictionaries
        jobs = []
        for row in raw_jobs:
            job_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Handle LOB objects
                if hasattr(value, 'read'):
                    try:
                        value = value.read()
                        # If it's bytes, decode to string
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                    except Exception as e:
                        value = str(e)  # Fallback if reading fails
                job_dict[column] = value
            jobs.append(job_dict)
            
        return jsonify(jobs)
    except Exception as e:
        print(f"Error in get_all_jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500

# get job details
@jobs_bp.route('/get_job_details/<mapref>', methods=['GET'])
def get_job_details(mapref):
    try:
        conn = create_oracle_connection()

        job_details_query=""" 
        SELECT TRGCLNM,TRGCLDTYP,TRGKEYFLG,TRGKEYSEQ,TRGCLDESC,MAPLOGIC,KEYCLNM,VALCLNM,SCDTYP FROM DWJOBDTL WHERE CURFLG = 'Y' AND MAPREF = :mapref """
        cursor = conn.cursor()
        cursor.execute(job_details_query, {'mapref': mapref})
        job_details = cursor.fetchall()
        return jsonify({
            'job_details': job_details
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# get job schedule details
@jobs_bp.route('/get_job_schedule_details/<job_flow_id>', methods=['GET'])
def get_job_schedule_details(job_flow_id):
    try:
        conn = create_oracle_connection()
        query = """
        SELECT 
            JOBFLWID,
            MAPREF,
            FRQCD,
            FRQDD,
            FRQHH,
            FRQMI,
            STRTDT,
            ENDDT,
            STFLG,
            DPND_JOBSCHID,
            RECCRDT,
            RECUPDT 
        FROM DWJOBSCH 
        WHERE CURFLG ='Y' AND JOBFLWID=:job_flow_id
        """
        cursor = conn.cursor()
        cursor.execute(query, {'job_flow_id': job_flow_id})
        
        # Get column names
        columns = [col[0] for col in cursor.description]
        
        # Convert to list of dictionaries
        job_schedule_details = []
        for row in cursor.fetchall():
            job_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                
                # Convert Oracle NUMBER to string or int
                if isinstance(value, int) or isinstance(value, float):
                    job_dict[column] = str(value)  # Convert all numbers to strings for consistency
                # Handle date objects
                elif hasattr(value, 'strftime'):
                    job_dict[column] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                # Handle other types
                else:
                    job_dict[column] = str(value) if value is not None else ""
            
            # Debug information
            print(f"Job schedule details for {job_flow_id}: {job_dict}")
            job_schedule_details.append(job_dict)
        
        return jsonify(job_schedule_details)
    except Exception as e:
        print(f"Error in get_job_schedule_details: {str(e)}")
        return jsonify({"error": str(e)}), 500



####################### Scheduled Jobs and Logs #######################


# get list of scheduled jobs
@jobs_bp.route('/get_scheduled_jobs', methods=['GET'])
def get_scheduled_jobs():
    try:
        conn = create_oracle_connection()
        try:
            # Get period from query parameters, default to 7 days
            period = request.args.get('period', 7, type=int)
            query = """ 
                    select 
                    		jl.joblogid AS log_id,
                    		pl.reccrdt AS log_date,
                    		pl.mapref AS job_name,
                    		pl.status,
                    		pl.strtdt AS actual_start_date,
                    		err.errmsg||chr(10)||err.dberrmsg error_message,
                    		pl.sessionid AS session_id,
                            jl.srcrows AS source_rows,
                    		jl.trgrows AS target_rows,
                            pl.param1 AS param1,
                           case 
                           when pl.enddt IS NOT NULL THEN
                                EXTRACT(DAY FROM (pl.enddt - pl.strtdt)) * 86400 + 
                                EXTRACT(HOUR FROM (pl.enddt - pl.strtdt)) * 3600 + 
                                EXTRACT(MINUTE FROM (pl.enddt - pl.strtdt)) * 60 + 
                                EXTRACT(SECOND FROM (pl.enddt - pl.strtdt))
                           else null
                           end as run_duration_seconds
                    from dwprclog pl, dwjoblog jl, dwjoberr err
                    where jl.jobid(+)      = pl.jobid 
                    and   jl.sessionid(+)  = pl.sessionid
                    and   jl.prcid(+)      = pl.prcid
                    and   jl.mapref(+)     = pl.mapref
                    and   err.sessionid(+) = pl.sessionid
                    and   err.prcid(+)     = pl.prcid
                    and   err.mapref(+)    = pl.mapref
                    and   err.jobid(+)     = pl.jobid
                    and   pl.reccrdt >= SYSDATE - :period
                    order by pl.mapref, jl.reccrdt desc
 
            """
            cursor = conn.cursor()
            cursor.execute(query, {'period': period})
            column_names = [desc[0] for desc in cursor.description]
            raw_jobs = cursor.fetchall()
            
            # Convert data to JSON-serializable format and group by job
            jobs_dict = {}
            
            for row in raw_jobs:
                # Convert row data to proper format
                log_entry = {}
                for i, value in enumerate(row):
                    column_name = column_names[i]
                    
                    if value is None:
                        log_entry[column_name] = None
                    elif hasattr(value, 'total_seconds'):  # timedelta object
                        # Convert timedelta to total seconds as number
                        log_entry[column_name] = int(value.total_seconds())
                    elif hasattr(value, 'isoformat'):  # datetime object
                        log_entry[column_name] = value.isoformat()
                    elif hasattr(value, 'read'):  # LOB object
                        try:
                            lob_data = value.read()
                            if isinstance(lob_data, bytes):
                                log_entry[column_name] = lob_data.decode('utf-8')
                            else:
                                log_entry[column_name] = str(lob_data)
                        except Exception as e:
                            log_entry[column_name] = f"Error reading LOB: {str(e)}"
                    elif isinstance(value, (int, float)):  # Numeric values (including duration seconds)
                        log_entry[column_name] = value
                    else:
                        log_entry[column_name] = str(value) if value is not None else None
                
                # Group by job_name (which is the JOB_NAME column)
                job_name = log_entry.get('JOB_NAME')
                if job_name:
                    if job_name not in jobs_dict:
                        jobs_dict[job_name] = {
                            'job_name': job_name,
                            'logs': []
                        }
                    jobs_dict[job_name]['logs'].append(log_entry)
            
            # Convert dictionary to array for easier frontend consumption
            grouped_jobs = list(jobs_dict.values())
            
            # Sort jobs by job name and logs by log date (most recent first)
            grouped_jobs.sort(key=lambda x: x['job_name'])
            for job in grouped_jobs:
                job['logs'].sort(key=lambda x: x.get('LOG_DATE', ''), reverse=True)
            
            # Debug information
            print(f"Column names: {column_names}")
            print(f"Number of unique jobs found: {len(grouped_jobs)}")
            total_logs = sum(len(job['logs']) for job in grouped_jobs)
            print(f"Total log entries: {total_logs}")
            if len(grouped_jobs) > 0:
                print(f"Sample job: {grouped_jobs[0]['job_name']} with {len(grouped_jobs[0]['logs'])} logs")
                
            return jsonify({
                'jobs': grouped_jobs,
                'summary': {
                    'total_jobs': len(grouped_jobs),
                    'total_log_entries': total_logs,
                    'column_names': column_names
                }
            })
        finally:
            conn.close()
    except Exception as e:
        print(f"Error in get_scheduled_jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500







# get job and process log details for a scheduled job
@jobs_bp.route('/get_job_and_process_log_details/<mapref>', methods=['GET'])
def get_job_and_process_log_details(mapref):
    try:
        conn = create_oracle_connection()
        query = """ 
                select jbl.prcdt as PROCESS_DATE
                      ,jbl.mapref as MAP_REFERENCE
                	  ,jbl.jobid as JOB_ID
                	  ,jbl.srcrows as SOURCE_ROWS
                	  ,jbl.trgrows as target_rows
                	  ,jbl.errrows as ERROR_ROWS
                	  ,prc.strtdt as START_DATE
                	  ,prc.enddt as END_DATE
                	  ,prc.status as STATUS
                      ,err.errmsg||chr(10)||err.dberrmsg ERROR_MESSAGE
                from dwjoblog jbl
                    ,dwprclog prc
                	,dwjoberr err
                where jbl.mapref = :mapref
                and   jbl.jobid        = prc.jobid
                and   err.sessionid(+) = prc.sessionid
                and   err.prcid(+)     = prc.prcid
                and   err.mapref(+)    = prc.mapref
                and   err.jobid(+)     = prc.jobid
                order by start_date desc;
        """
        cursor = conn.cursor()
        cursor.execute(query, {'mapref': mapref})
        job_and_process_log_details = cursor.fetchall()
        return jsonify({
            'job_and_process_log_details': job_and_process_log_details
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get error details of a scheduled job
@jobs_bp.route('/get_error_details/<job_id>', methods=['GET'])
def get_error_details(job_id):
    try:
        conn = create_oracle_connection()
        query = """ 
        SELECT ERRID as ERROR_ID,
        PRCDT as PROCESS_DATE,
        ERRTYP as ERROR_TYPE,
        DBERRMSG as DATABASE_ERROR_MESSAGE,
        ERRMSG as ERROR_MESSAGE,
        KEYVALUE as KEY_VALUE 
        FROM DWJOBERR WHERE JOBID = :job_id 
        """
        cursor = conn.cursor()
        cursor.execute(query, {'job_id': job_id})
        error_details = cursor.fetchall()
        return jsonify({
            'error_details': error_details
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# save or update job schedule
@jobs_bp.route('/save_job_schedule', methods=['POST'])
def save_job_schedule():
    try:
        data = request.json
        
        # Required fields
        job_flow_id = data.get('JOBFLWID')
        map_ref = data.get('MAPREF')
        frequency_code = data.get('FRQCD')
        frequency_day = data.get('FRQDD')
        frequency_hour = data.get('FRQHH')
        frequency_minute = data.get('FRQMI')
        start_date = data.get('STRTDT')
        end_date = data.get('ENDDT')
        
        conn = create_oracle_connection()

        # Ensure job is disabled before saving the new schedule details



        try:
            cursor = conn.cursor()
            # Call the Oracle package function
            sql = f"""
            DECLARE
                v_jobschid NUMBER;
            BEGIN
                v_jobschid := {ORACLE_SCHEMA}.PKGDWPRC.CREATE_JOB_SCHEDULE(
                    p_mapref => :p_mapref,
                    p_frqcd => :p_frqcd,
                    p_frqdd => :p_frqdd,
                    p_frqhh => :p_frqhh,
                    p_frqmi => :p_frqmi,
                    p_strtdt => TO_DATE(:p_strtdt, 'YYYY-MM-DD'),
                    p_enddt => TO_DATE(:p_enddt, 'YYYY-MM-DD')
                );
                :job_schedule_id := v_jobschid;
            END;
            """
            
            # Prepare the parameters
            job_schedule_id = cursor.var(int)
            
            # Handle end_date, which can be null
            end_date_param = end_date if end_date else None
            
            # Execute the PL/SQL block
            cursor.execute(sql, {
                'p_mapref': map_ref,
                'p_frqcd': frequency_code,
                'p_frqdd': frequency_day,
                'p_frqhh': frequency_hour,
                'p_frqmi': frequency_minute,
                'p_strtdt': start_date,
                'p_enddt': end_date_param,
                'job_schedule_id': job_schedule_id
            })
            
            # Commit the transaction
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job schedule saved successfully',
                'job_schedule_id': job_schedule_id.getvalue()
            })
            
        except Exception as e:
            conn.rollback()
            error_message = str(e)
            print(f"Database error in save_job_schedule: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in save_job_schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred while saving the job schedule: {str(e)}'
        }), 500



# save save parent and child job.
@jobs_bp.route('/save_parent_child_job', methods=['POST'])
def save_parent_child_job():
    try:
        data = request.json
        
        # Required fields
        parent_map_reference = data.get('PARENT_MAP_REFERENCE')
        child_map_reference = data.get('CHILD_MAP_REFERENCE')
        
        # Validate required fields
        if not parent_map_reference or not child_map_reference:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: PARENT_MAP_REFERENCE or CHILD_MAP_REFERENCE'
            }), 400
            
        conn = create_oracle_connection()
        try:
            cursor = conn.cursor()
            
            # Call the Oracle package procedure
            sql = """
            BEGIN
                TRG.PKGDWPRC.CREATE_JOB_DEPENDENCY(
                    p_parent_mapref => :parent_map_reference,
                    p_child_mapref => :child_map_reference
                );
            END;
            """
            
            # Execute the PL/SQL block
            cursor.execute(sql, {
                'parent_map_reference': parent_map_reference,
                'child_map_reference': child_map_reference
            })
            
            # Commit the transaction
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Parent-child job relationship saved successfully'
            })
            
        except Exception as e:
            conn.rollback()
            error_message = str(e)
            print(f"Database error in save_parent_child_job: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in save_parent_child_job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while saving the parent-child job relationship: {str(e)}'
        }), 500



# schedule job
@jobs_bp.route('/enable_disable_job', methods=['POST'])
def enable_disable_job():
 
    data = request.json
    map_ref = data.get('MAPREF')
    job_flag = data.get('JOB_FLG')
    conn = create_oracle_connection()
    try:
        cursor = conn.cursor()
        query = f""" 
        BEGIN
          {ORACLE_SCHEMA}.PKGDWPRC.ENABLE_DISABLE_SCHEDULE(:map_ref, :job_flag);
        END;
        """
        cursor.execute(query, {'map_ref': map_ref, 'job_flag': job_flag})
        conn.commit()
        if job_flag == 'E':
            return jsonify({
                'success': True,
                'message': 'Job enabled successfully'
            })
        elif job_flag == 'D':
            return jsonify({
                'success': True,
                'message': 'Job disabled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid job flag'
            }), 400 
    except Exception as e:
        conn.rollback()
        error_message = str(e)
        print(f"Database error in enable_disable_job: {error_message}")
        return jsonify({
            'success': False,
            'message': f'Database error: {error_message}'
        }), 500
    finally:
        conn.close()
        




def call_schedule_regular_job_async(p_mapref):
    def background_job():
        connection = None
        cursor = None
        try:
            print(f"Starting background job scheduling for {p_mapref}")
            connection = create_oracle_connection()
            cursor = connection.cursor()
            
            sql = """
            DECLARE
              v_mapref VARCHAR2(100) := :p_mapref;
            BEGIN
              PKGDWPRC.SCHEDULE_JOB_IMMEDIATE(p_mapref => v_mapref);
            END;
            """
            
            # Execute with named parameters
            cursor.execute(sql, p_mapref=p_mapref)
            connection.commit()
            
            print(f"Job {p_mapref} scheduled for immediate execution successfully")
            
        except Exception as e:
            error_message = f"Exception while scheduling job {p_mapref}: {str(e)}"
            print(f"Error: {error_message}")
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                try:
                    connection.close()
                except:
                    pass
    
    # Start the background thread
    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()
    return True, f"Job {p_mapref} execution started in background"


def call_schedule_history_job_async(p_mapref, p_strtdt, p_enddt, p_tlflg):
    def background_job():
        connection = None
        cursor = None
        try:
            info(f"Starting background history job scheduling for {p_mapref} from {p_strtdt} to {p_enddt}")
            connection = create_oracle_connection()
            cursor = connection.cursor()
            
            sql = f"""
            DECLARE
              v_mapref VARCHAR2(100) := :p_mapref;
              v_strtdt DATE := TO_DATE(:p_strtdt, 'YYYY-MM-DD');
              v_enddt DATE := TO_DATE(:p_enddt, 'YYYY-MM-DD');
              v_tlflg VARCHAR2(1) := :p_tlflg;
            BEGIN
              {ORACLE_SCHEMA}.PKGDWPRC.SCHEDULE_HISTORY_JOB_IMMEDIATE(
                p_mapref => v_mapref,
                p_strtdt => v_strtdt,
                p_enddt => v_enddt,
                p_tlflg => v_tlflg
              );
            END;
            """
            
            # Execute with named parameters
            cursor.execute(sql, {
                'p_mapref': p_mapref,
                'p_strtdt': p_strtdt,
                'p_enddt': p_enddt,
                'p_tlflg': p_tlflg
            })
            connection.commit()
            
            info(f"History job {p_mapref} scheduled for immediate execution successfully")
            
        except Exception as e:
            error_message = f"Exception while scheduling history job {p_mapref}: {str(e)}"
            error(f"Error: {error_message}")
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                try:
                    connection.close()
                except:
                    pass
    
    # Start the background thread
    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()
    return True, f"History job {p_mapref} execution started in background (from {p_strtdt} to {p_enddt})"


def call_schedule_immediate_job(connection, p_mapref):
    cursor = None
    try:
        cursor = connection.cursor()
        p_err = cursor.var(oracledb.STRING, 2000)  
        sql = """

        DECLARE
          v_mapref VARCHAR2(100) := :p_mapref;
        BEGIN
          PKGDWPRC.SCHEDULE_JOB_IMMEDIATE(p_mapref => v_mapref);
        END;
        """
        
        # Execute with named parameters
        cursor.execute(
            sql,
            p_mapref=p_mapref,
        )
        connection.commit()
        
        # Get the error message (if any)
        error_message = p_err.getvalue()
        
        if error_message:
            return False, error_message
        else:
            return True, f"Job {p_mapref} scheduled for immediate execution"
    
    except Exception as e:
        error_message = f"Exception while deleting mapping detail: {str(e)}"
        return False, error_message
    finally:
        if cursor:
            cursor.close()


def check_job_already_running(connection, p_mapref):
    cursor = None
    try:
        cursor = connection.cursor()
        sql = """
        SELECT COUNT(*) FROM DWPRCLOG  WHERE MAPREF=:p_mapref AND status='IP'
        """
        cursor.execute(sql, {'p_mapref': p_mapref})
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        return False
    finally:
        if cursor:
            cursor.close()  

# Schedule the job immediately
@jobs_bp.route('/schedule-job-immediately', methods=['POST'])
def schedule_job_immediately():
    try:
        data = request.json
        p_mapref = data.get('mapref')
        load_type = data.get('loadType', 'regular')  # 'regular' or 'history'
        
        # For history load, get additional parameters
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        truncate_load = data.get('truncateLoad', 'N')  # 'Y' or 'N'

        if not p_mapref:
            return jsonify({
                'success': False,
                'message': 'Missing required parameter: mapref'
            }), 400

        # Validate history load parameters
        if load_type == 'history':
            if not start_date or not end_date:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameters for history load: startDate and endDate'
                }), 400

        conn = create_oracle_connection()
        try:
            # Check if job is already running
            if check_job_already_running(conn, p_mapref):
                return jsonify({
                    'success': False,
                    'message': f'{p_mapref} : Job is already running'
                }), 400
                
            if load_type == 'history':
                # Schedule the history job immediately in background
                success, message = call_schedule_history_job_async(p_mapref, start_date, end_date, truncate_load)
            else:
                # Schedule the regular job immediately in background
                success, message = call_schedule_regular_job_async(p_mapref)
                
            return jsonify({
                'success': success,
                'message': message  
            })
        finally:
            conn.close()
    except Exception as e:
        error(f"Error in schedule_job_immediately: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

# stop a running job
@jobs_bp.route('/stop-running-job', methods=['POST'])
def stop_running_job():
    try:
        data = request.json
        p_mapref = data.get('mapref')
        p_strtdt = data.get('startDate')
        p_force = data.get('force', 'N')  # Default to graceful stop if not provided
        
        info(f"Stopping job: {p_mapref}, Start Date: {p_strtdt}, Force: {p_force}")
        
        if not p_mapref or not p_strtdt:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: mapref or startDate'
            }), 400
        
        # Format already provided as YYYY-MM-DD HH:MM:SS from frontend
        oracle_date = p_strtdt
        
        # If it's not in the expected format, try to parse it
        if not (len(p_strtdt) >= 10 and p_strtdt[4] == '-' and p_strtdt[7] == '-'):
            try:
                from datetime import datetime
                # Try to parse the ISO format date
                if 'T' in p_strtdt:
                    # Handle ISO format with timezone info
                    date_obj = datetime.fromisoformat(p_strtdt.replace('Z', '+00:00'))
                else:
                    # Handle simple date format
                    date_obj = datetime.strptime(p_strtdt, '%Y-%m-%d')
                    
                # Format date in a way Oracle will definitely understand
                oracle_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                info(f"Parsed date: {oracle_date}")
            except Exception as e:
                warning(f"Error parsing date: {str(e)}. Using original date string.")
                oracle_date = p_strtdt
            
        conn = create_oracle_connection()
        try:
            cursor = conn.cursor()
            
            # Call the Oracle package procedure with a simpler date format
            sql = f"""
            DECLARE
                v_err VARCHAR2(4000);
            BEGIN
                {ORACLE_SCHEMA}.PKGDWPRC.STOP_RUNNING_JOB(
                    p_mapref => :p_mapref,
                    p_strtdt => TO_DATE(:p_strtdt, 'YYYY-MM-DD HH24:MI:SS'),
                    p_force => :p_force,
                    p_err => v_err
                );
                :error_message := v_err;
            END;
            """
            
            # Prepare the parameters
            error_message = cursor.var(oracledb.STRING, 4000)
            
            # Execute the PL/SQL block
            cursor.execute(sql, {
                'p_mapref': p_mapref,
                'p_strtdt': oracle_date,
                'p_force': p_force,
                'error_message': error_message
            })
            
            # Commit the transaction
            conn.commit()
            
            # Check if there was an error
            if error_message.getvalue():
                warning(f"Error stopping job: {error_message.getvalue()}")
                return jsonify({
                    'success': False,
                    'message': f'Error stopping job: {error_message.getvalue()}'
                }), 500
            
            info(f"Job {p_mapref} stopped successfully")
            print({error_message.getvalue()})
            return jsonify({
                'success': True,
                'message': f'Job {p_mapref} has been stopped successfully : {error_message.getvalue()}'
            })
            
        except Exception as e:
            conn.rollback()
            error_message = str(e)
            exception(f"Database error in stop_running_job: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in stop_running_job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while stopping the job: {str(e)}'
        }), 500
    
