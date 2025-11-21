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
from modules.jobs.pkgdwprc_python import (
    JobSchedulerService,
    ScheduleRequest,
    ImmediateJobRequest,
    HistoryJobRequest,
    SchedulerValidationError,
    SchedulerRepositoryError,
    SchedulerError,
)
dotenv.load_dotenv()
ORACLE_SCHEMA = os.getenv("SCHEMA")
# Create blueprint
jobs_bp = Blueprint('jobs', __name__)


def _parse_date(value):
    if value in (None, "", "null"):
        return None
    try:
        return datetime.strptime(value[:10], '%Y-%m-%d').date()
    except ValueError as exc:
        raise SchedulerValidationError(f"Invalid date format: {value}") from exc


def _optional_int(value):
    if value in (None, "", "null"):
        return None
    return int(value)


def _parse_datetime(value):
    if value in (None, "", "null"):
        return None
    try:
        # Handle ISO strings with timezone or milliseconds
        sanitized = value.replace('Z', '+00:00')
        return datetime.fromisoformat(sanitized)
    except ValueError:
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError as exc:
            raise SchedulerValidationError(f"Invalid datetime format: {value}") from exc



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
    data = request.json or {}
    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        schedule_request = ScheduleRequest(
            mapref=data.get('MAPREF'),
            frequency_code=data.get('FRQCD'),
            frequency_day=data.get('FRQDD'),
            frequency_hour=_optional_int(data.get('FRQHH')),
            frequency_minute=_optional_int(data.get('FRQMI')),
            start_date=_parse_date(data.get('STRTDT')),
            end_date=_parse_date(data.get('ENDDT')),
        )
        result = service.create_job_schedule(schedule_request)
        return jsonify({
            'success': True,
            'message': result.message,
            'job_schedule_id': result.job_schedule_id,
            'status': result.status
        })
    except SchedulerValidationError as exc:
        return jsonify({
            'success': False,
            'message': str(exc)
        }), 400
    except SchedulerRepositoryError as exc:
        return jsonify({
            'success': False,
            'message': f'Database error: {str(exc)}'
        }), 500
    except Exception as exc:
        error(f"Error in save_job_schedule: {exc}")
        return jsonify({
            'success': False,
            'message': f'Unexpected error: {str(exc)}'
        }), 500
    finally:
        if conn:
            conn.close()



# save save parent and child job.
@jobs_bp.route('/save_parent_child_job', methods=['POST'])
def save_parent_child_job():
    data = request.json or {}
    parent_map_reference = data.get('PARENT_MAP_REFERENCE')
    child_map_reference = data.get('CHILD_MAP_REFERENCE')

    if not parent_map_reference or not child_map_reference:
        return jsonify({
            'success': False,
            'message': 'Missing required parameters: PARENT_MAP_REFERENCE or CHILD_MAP_REFERENCE'
        }), 400

    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        service.create_job_dependency(parent_map_reference, child_map_reference)
        return jsonify({
            'success': True,
            'message': 'Parent-child job relationship saved successfully'
        })
    except SchedulerValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except SchedulerRepositoryError as exc:
        return jsonify({'success': False, 'message': f'Database error: {str(exc)}'}), 500
    except Exception as exc:
        error(f"Error in save_parent_child_job: {exc}", exc_info=True)
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        if conn:
            conn.close()



# schedule job
@jobs_bp.route('/enable_disable_job', methods=['POST'])
def enable_disable_job():
    data = request.json or {}
    map_ref = data.get('MAPREF')
    job_flag = data.get('JOB_FLG')
    if not map_ref or job_flag not in {'E', 'D'}:
        return jsonify({
            'success': False,
            'message': 'Invalid or missing parameters'
        }), 400
    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        service.enable_disable_schedule(map_ref, job_flag)
        message = 'Job enabled successfully' if job_flag == 'E' else 'Job disabled successfully'
        return jsonify({'success': True, 'message': message})
    except SchedulerValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except SchedulerRepositoryError as exc:
        return jsonify({'success': False, 'message': f'Database error: {str(exc)}'}), 500
    except Exception as exc:
        error(f"Error in enable_disable_job: {exc}")
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        if conn:
            conn.close()
        




def call_schedule_regular_job_async(p_mapref):
    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        request_id = service.queue_immediate_job(
            ImmediateJobRequest(mapref=p_mapref)
        )
        return True, f"Job {p_mapref} queued for immediate execution (request_id={request_id})"
    except SchedulerError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            conn.close()


def call_schedule_history_job_async(p_mapref, p_strtdt, p_enddt, p_tlflg):
    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        request_id = service.queue_history_job(
            HistoryJobRequest(
                mapref=p_mapref,
                start_date=_parse_date(p_strtdt),
                end_date=_parse_date(p_enddt),
                truncate_flag=p_tlflg or 'N'
            )
        )
        return True, (
            f"History job {p_mapref} queued "
            f"(request_id={request_id}, {p_strtdt} to {p_enddt})"
        )
    except SchedulerError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            conn.close()


def check_job_already_running(connection, p_mapref):
    """
    Check if a job is already running.
    A job is considered running if it has status 'IP' (In Progress) or 'CLAIMED' 
    and was started recently (within the last 24 hours).
    This prevents false positives from old stuck records.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        sql = """
        SELECT COUNT(*) FROM DWPRCLOG  
        WHERE MAPREF=:p_mapref 
        AND status IN ('IP', 'CLAIMED')
        AND strtdt > SYSTIMESTAMP - INTERVAL '24' HOUR
        """
        cursor.execute(sql, {'p_mapref': p_mapref})
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        # On error, return False to allow job execution
        error(f"Error checking if job is running: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()


def reset_stuck_jobs(connection, p_mapref=None):
    """
    Reset stuck jobs (jobs with status 'IP' that have been running for more than 24 hours).
    This allows jobs that are truly stuck to be reset so they can be re-executed.
    
    Args:
        connection: Database connection
        p_mapref: Optional mapref to reset only specific job. If None, resets all stuck jobs.
    
    Returns:
        Tuple of (count_reset, list of reset prcids)
    """
    cursor = None
    try:
        cursor = connection.cursor()
        
        if p_mapref:
            # First, get the PRCIDs that will be reset
            cursor.execute("""
                SELECT PRCID FROM DWPRCLOG 
                WHERE MAPREF = :p_mapref 
                AND status = 'IP'
                AND strtdt < SYSTIMESTAMP - INTERVAL '24' HOUR
            """, {'p_mapref': p_mapref})
            reset_prcids = [row[0] for row in cursor.fetchall()]
            
            # Reset specific job
            sql = """
            UPDATE DWPRCLOG 
            SET status = 'FAILED',
                endtime = SYSTIMESTAMP,
                errmsg = 'Job reset: Was stuck in IP status for more than 24 hours'
            WHERE MAPREF = :p_mapref 
            AND status = 'IP'
            AND strtdt < SYSTIMESTAMP - INTERVAL '24' HOUR
            """
            cursor.execute(sql, {'p_mapref': p_mapref})
            connection.commit()
            count = cursor.rowcount
        else:
            # First, get the PRCIDs and MAPREFs that will be reset
            cursor.execute("""
                SELECT PRCID, MAPREF FROM DWPRCLOG 
                WHERE status = 'IP'
                AND strtdt < SYSTIMESTAMP - INTERVAL '24' HOUR
            """)
            reset_prcids = [(row[0], row[1]) for row in cursor.fetchall()]
            
            # Reset all stuck jobs
            sql = """
            UPDATE DWPRCLOG 
            SET status = 'FAILED',
                endtime = SYSTIMESTAMP,
                errmsg = 'Job reset: Was stuck in IP status for more than 24 hours'
            WHERE status = 'IP'
            AND strtdt < SYSTIMESTAMP - INTERVAL '24' HOUR
            """
            cursor.execute(sql)
            connection.commit()
            count = cursor.rowcount
        
        return count, reset_prcids
    except Exception as e:
        error(f"Error resetting stuck jobs: {str(e)}")
        connection.rollback()
        raise
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
    data = request.json or {}
    p_mapref = data.get('mapref')
    p_strtdt = data.get('startDate')
    p_force = data.get('force', 'N')

    if not p_mapref or not p_strtdt:
        return jsonify({
            'success': False,
            'message': 'Missing required parameters: mapref or startDate'
        }), 400

    try:
        start_dt = _parse_datetime(p_strtdt)
    except SchedulerValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400

    conn = None
    try:
        conn = create_oracle_connection()
        service = JobSchedulerService(conn)
        request_id = service.request_job_stop(p_mapref, start_dt, p_force)
        info(f"Stop requested for job {p_mapref} (request_id={request_id})")
        return jsonify({
            'success': True,
            'message': f'Stop request queued (request_id={request_id})'
        })
    except SchedulerRepositoryError as exc:
        return jsonify({'success': False, 'message': f'Database error: {str(exc)}'}), 500
    except Exception as exc:
        error(f"Error in stop_running_job: {exc}", exc_info=True)
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        if conn:
            conn.close()


# Reset stuck jobs endpoint
@jobs_bp.route('/reset-stuck-jobs', methods=['POST'])
def reset_stuck_jobs_endpoint():
    """
    Reset stuck jobs (jobs with status 'IP' that have been running for more than 24 hours).
    This allows jobs that are truly stuck to be reset so they can be re-executed.
    """
    try:
        data = request.json or {}
        p_mapref = data.get('mapref')  # Optional: if provided, only reset this specific job
        
        conn = create_oracle_connection()
        try:
            count, reset_prcids = reset_stuck_jobs(conn, p_mapref)
            
            if count > 0:
                if p_mapref:
                    message = f"Reset {count} stuck job(s) for {p_mapref}. PRCIDs: {reset_prcids}"
                else:
                    message = f"Reset {count} stuck job(s). Affected jobs: {reset_prcids}"
                info(message)
                return jsonify({
                    'success': True,
                    'message': message,
                    'count': count,
                    'reset_prcids': reset_prcids
                })
            else:
                message = f"No stuck jobs found to reset" + (f" for {p_mapref}" if p_mapref else "")
                return jsonify({
                    'success': True,
                    'message': message,
                    'count': 0
                })
        finally:
            conn.close()
    except Exception as e:
        error(f"Error in reset_stuck_jobs_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error resetting stuck jobs: {str(e)}'
        }), 500


# Diagnostic endpoint to check scheduler queue status
@jobs_bp.route('/check_scheduler_queue', methods=['GET'])
def check_scheduler_queue():
    """
    Diagnostic endpoint to check the status of queued jobs.
    Helps verify if scheduler service is processing requests.
    """
    try:
        conn = create_oracle_connection()
        try:
            # Check queue status
            queue_query = """
                SELECT 
                    request_id,
                    mapref,
                    request_type,
                    status,
                    requested_at,
                    claimed_at,
                    claimed_by,
                    completed_at,
                    CASE 
                        WHEN status = 'NEW' AND requested_at < SYSTIMESTAMP - INTERVAL '5' MINUTE 
                        THEN 'STUCK'
                        ELSE 'OK'
                    END as queue_health
                FROM DWPRCREQ
                ORDER BY requested_at DESC
                FETCH FIRST 20 ROWS ONLY
            """
            cursor = conn.cursor()
            cursor.execute(queue_query)
            columns = [col[0] for col in cursor.description]
            queue_rows = cursor.fetchall()
            
            queue_data = []
            for row in queue_rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if hasattr(value, 'isoformat'):
                        row_dict[col] = value.isoformat()
                    else:
                        row_dict[col] = str(value) if value is not None else None
                queue_data.append(row_dict)
            
            # Count by status
            status_counts = {}
            for row in queue_data:
                status = row.get('STATUS', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Check for stuck jobs
            stuck_jobs = [r for r in queue_data if r.get('QUEUE_HEALTH') == 'STUCK']
            
            # Check recent process logs
            process_log_query = """
                SELECT 
                    mapref,
                    status,
                    strtdt,
                    enddt,
                    reccrdt
                FROM DWPRCLOG
                WHERE reccrdt >= SYSDATE - 1/24
                ORDER BY reccrdt DESC
                FETCH FIRST 10 ROWS ONLY
            """
            cursor.execute(process_log_query)
            process_logs = []
            for row in cursor.fetchall():
                process_logs.append({
                    'mapref': row[0],
                    'status': row[1],
                    'strtdt': row[2].isoformat() if row[2] else None,
                    'enddt': row[3].isoformat() if row[3] else None,
                    'reccrdt': row[4].isoformat() if row[4] else None,
                })
            
            return jsonify({
                'success': True,
                'queue_summary': {
                    'total_requests': len(queue_data),
                    'status_counts': status_counts,
                    'stuck_jobs_count': len(stuck_jobs),
                    'recent_process_logs': len(process_logs)
                },
                'queue_details': queue_data,
                'recent_process_logs': process_logs,
                'diagnostics': {
                    'scheduler_running': 'UNKNOWN - Check scheduler service logs',
                    'recommendation': 'If status=NEW jobs exist, ensure scheduler service is running'
                }
            })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
