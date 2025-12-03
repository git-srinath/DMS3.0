from flask import Blueprint, request, jsonify
from database.dbconnect import create_metadata_connection
from modules.common.db_table_utils import _detect_db_type, get_postgresql_table_name
import os
import dotenv
import json
from decimal import Decimal
from datetime import timedelta

dotenv.load_dotenv()

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)
SCHEMA=os.getenv("DMS_SCHEMA")

def convert_to_serializable(obj):
    """Convert Oracle objects to JSON serializable format"""
    if isinstance(obj, timedelta):
        # Convert timedelta to total seconds
        return obj.total_seconds()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    return obj

def process_rows(rows):
    """Process database rows to make them JSON serializable"""
    processed_rows = []
    for row in rows:
        processed_row = []
        for item in row:
            processed_row.append(convert_to_serializable(item))
        processed_rows.append(processed_row)
    return processed_rows

@dashboard_bp.route("/all_metrics", methods=["GET"])
def all_metrics():
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_mapr_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_MAPR')
        dms_job_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOB')
        dms_jobflw_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBFLW')
        dms_jobsch_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBSCH')
        
        # Quote table names if they contain uppercase letters
        dms_mapr_ref = f'"{dms_mapr_table}"' if dms_mapr_table != dms_mapr_table.lower() else dms_mapr_table
        dms_job_ref = f'"{dms_job_table}"' if dms_job_table != dms_job_table.lower() else dms_job_table
        dms_jobflw_ref = f'"{dms_jobflw_table}"' if dms_jobflw_table != dms_jobflw_table.lower() else dms_jobflw_table
        dms_jobsch_ref = f'"{dms_jobsch_table}"' if dms_jobsch_table != dms_jobsch_table.lower() else dms_jobsch_table
        
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_mapr_full = f'{schema_prefix}{dms_mapr_ref}'
        dms_job_full = f'{schema_prefix}{dms_job_ref}'
        dms_jobflw_full = f'{schema_prefix}{dms_jobflw_ref}'
        dms_jobsch_full = f'{schema_prefix}{dms_jobsch_ref}'
        
        # PostgreSQL: Use LEFT JOIN
        query = f""" 
            SELECT COUNT(m.mapref) AS total_mappings
                  ,SUM(CASE WHEN m.lgvrfyflg = 'Y' THEN 1 ELSE 0 END) AS logic_verified
                  ,SUM(CASE WHEN m.stflg = 'A' THEN 1 ELSE 0 END) AS active_mappings
                  ,SUM(CASE WHEN j.mapref IS NOT NULL THEN 1 ELSE 0 END) AS total_jobs
                  ,SUM(CASE WHEN j.stflg = 'A' THEN 1 ELSE 0 END) AS Active_jobs
                  ,SUM(CASE WHEN f.mapref IS NOT NULL THEN 1 ELSE 0 END) AS job_flow_created
                  ,SUM(CASE WHEN s.mapref IS NOT NULL THEN 1 ELSE 0 END) AS schedule_created
            FROM {dms_mapr_full} m
            LEFT JOIN {dms_job_full} j ON j.mapref = m.mapref AND j.curflg = m.curflg
            LEFT JOIN {dms_jobflw_full} f ON f.mapref = j.mapref AND f.jobid = j.jobid AND f.curflg = 'Y'
            LEFT JOIN {dms_jobsch_full} s ON s.jobflwid = f.jobflwid AND s.curflg = 'Y'
            WHERE m.curflg = 'Y'
        """
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_mapr_full = f"{schema_prefix}DMS_MAPR"
        dms_job_full = f"{schema_prefix}DMS_JOB"
        dms_jobflw_full = f"{schema_prefix}DMS_JOBFLW"
        dms_jobsch_full = f"{schema_prefix}DMS_JOBSCH"
        
        # Oracle: Use (+) outer join syntax
        query = f""" 
            SELECT COUNT(m.mapref) AS total_mappings
                  ,SUM(CASE WHEN m.lgvrfyflg = 'Y' THEN 1 ELSE 0 END) AS logic_verified
                  ,SUM(CASE WHEN m.stflg = 'A' THEN 1 ELSE 0 END) AS active_mappings
                  ,SUM(CASE WHEN j.mapref IS NOT NULL THEN 1 ELSE 0 END) AS total_jobs
                  ,SUM(CASE WHEN j.stflg = 'A' THEN 1 ELSE 0 END) AS Active_jobs
                  ,SUM(CASE WHEN f.mapref IS NOT NULL THEN 1 ELSE 0 END) AS job_flow_created
                  ,SUM(CASE WHEN s.mapref IS NOT NULL THEN 1 ELSE 0 END) AS schedule_created
            FROM {dms_mapr_full} m, {dms_job_full} j, {dms_jobflw_full} f, {dms_jobsch_full} s
            WHERE m.curflg = 'Y'
            AND   j.mapref (+) = m.mapref
            AND   j.curflg (+) = m.curflg
            AND   f.mapref (+) = j.mapref
            AND   f.jobid (+) = j.jobid
            AND   f.curflg (+) = 'Y'
            AND   s.jobflwid (+) = f.jobflwid
            AND   s.curflg (+) = 'Y'
        """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500  
    


@dashboard_bp.route("/jobs_overview", methods=["GET"])
def jobs_overview():
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_joblog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBLOG')
        dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
        
        # Quote table names if they contain uppercase letters
        dms_joblog_ref = f'"{dms_joblog_table}"' if dms_joblog_table != dms_joblog_table.lower() else dms_joblog_table
        dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
        
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_joblog_full = f'{schema_prefix}{dms_joblog_ref}'
        dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
        
        # PostgreSQL: Use EXTRACT(EPOCH FROM ...) for duration
        query = f""" 
            SELECT 
                l.mapref, 
                COUNT(l.mapref) AS times_processed,
                AVG(l.srcrows) AS average_src_rows_processed,
                CEIL(AVG(l.trgrows)) AS average_trg_rows_processed,
                MAX(EXTRACT(EPOCH FROM (p.enddt - p.strtdt))) AS max_job_duration, 
                MIN(EXTRACT(EPOCH FROM (p.enddt - p.strtdt))) AS min_job_duration
            FROM 
                {dms_joblog_full} l
            INNER JOIN {dms_prclog_full} p ON p.sessionid = l.sessionid AND p.prcid = l.prcid
            GROUP BY 
                l.mapref
        """
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
        dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
        
        # Oracle: Use direct subtraction for duration
        query = f""" 
            SELECT 
                l.mapref, 
                COUNT(l.mapref) AS times_processed,
                AVG(l.srcrows) AS average_src_rows_processed,
                CEIL(AVG(l.trgrows)) AS average_trg_rows_processed,
                MAX(p.enddt - p.strtdt) AS max_job_duration, 
                MIN(p.enddt - p.strtdt) AS min_job_duration
            FROM 
                {dms_joblog_full} l,
                {dms_prclog_full} p
            WHERE 
                p.sessionid = l.sessionid
                AND p.prcid = l.prcid
            GROUP BY 
                l.mapref
        """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))    
    except Exception as e:
        return jsonify({"error": str(e)}), 500  




# jobs and procssed source and target rows
@dashboard_bp.route("/jobs_processed_rows", methods=["GET"])
def jobs_processed_rows():
    mapref = request.args.get('mapref')
    period = request.args.get('period', 'DAY')
    
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_joblog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBLOG')
        dms_joblog_ref = f'"{dms_joblog_table}"' if dms_joblog_table != dms_joblog_table.lower() else dms_joblog_table
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_joblog_full = f'{schema_prefix}{dms_joblog_ref}'
        
        # PostgreSQL: Use TO_CHAR equivalent and CURRENT_DATE
        if period.upper() == 'ALL':
            # No date filter for 'ALL' option
            query = f""" 
                SELECT 
                    mapref,
                    TO_CHAR(prcdt, 'YYYY-MM-DD') AS time_group,
                    SUM(srcrows) AS total_srcrows,
                    SUM(trgrows) AS total_trgrows
                FROM 
                    {dms_joblog_full}
                WHERE 
                    mapref = %s
                GROUP BY 
                    mapref, TO_CHAR(prcdt, 'YYYY-MM-DD')
                ORDER BY 
                    time_group
            """
            cursor.execute(query, (mapref,))
        else:
            period_conditions = {
                'DAY': "CURRENT_DATE",
                'WEEK': "CURRENT_DATE - INTERVAL '6 days'",
                'MONTH': "CURRENT_DATE - INTERVAL '29 days'"
            }
            period_condition = period_conditions.get(period.upper(), period_conditions['DAY'])
            
            query = f""" 
                SELECT 
                    mapref,
                    TO_CHAR(prcdt, 'YYYY-MM-DD') AS time_group,
                    SUM(srcrows) AS total_srcrows,
                    SUM(trgrows) AS total_trgrows
                FROM 
                    {dms_joblog_full}
                WHERE 
                    mapref = %s
                    AND prcdt >= {period_condition}
                GROUP BY 
                    mapref, TO_CHAR(prcdt, 'YYYY-MM-DD')
                ORDER BY 
                    time_group
            """
            cursor.execute(query, (mapref,))
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
        
        if period.upper() == 'ALL':
            # No date filter for 'ALL' option
            query = f""" 
                SELECT 
                    mapref,
                    TO_CHAR(prcdt, 'yyyy-mm-dd') AS time_group,
                    SUM(srcrows) AS total_srcrows,
                    SUM(trgrows) AS total_trgrows
                FROM 
                    {dms_joblog_full}
                WHERE 
                    mapref = :mapref
                GROUP BY 
                    mapref, TO_CHAR(prcdt, 'yyyy-mm-dd')
                ORDER BY 
                    time_group
            """
            cursor.execute(query, {'mapref': mapref})
        else:
            query = f""" 
                SELECT 
                    mapref,
                    TO_CHAR(prcdt, 'yyyy-mm-dd') AS time_group,
                    SUM(srcrows) AS total_srcrows,
                    SUM(trgrows) AS total_trgrows
                FROM 
                    {dms_joblog_full}
                WHERE 
                    mapref = :mapref
                    AND prcdt >= CASE :period
                        WHEN 'DAY'   THEN TRUNC(SYSDATE)
                        WHEN 'WEEK'  THEN TRUNC(SYSDATE) - 6
                        WHEN 'MONTH' THEN TRUNC(SYSDATE) - 29
                    END
                GROUP BY 
                    mapref, TO_CHAR(prcdt, 'yyyy-mm-dd')
                ORDER BY 
                    time_group
            """
            cursor.execute(query, {'mapref': mapref, 'period': period})
    
    try:
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# jobs and executed duration - day/week/month
@dashboard_bp.route("/jobs_executed_duration", methods=["GET"])
def jobs_executed_duration():
    mapref = request.args.get('mapref')
    period = request.args.get('period', '7')
    
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_joblog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBLOG')
        dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
        
        # Quote table names if they contain uppercase letters
        dms_joblog_ref = f'"{dms_joblog_table}"' if dms_joblog_table != dms_joblog_table.lower() else dms_joblog_table
        dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
        
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_joblog_full = f'{schema_prefix}{dms_joblog_ref}'
        dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
        
        # PostgreSQL: Use EXTRACT(EPOCH FROM ...) for duration
        if period.upper() == 'ALL':
            # No date filter for 'ALL' option
            query = f""" 
                SELECT x.prcdt, x.mapref,
                       EXTRACT(EPOCH FROM x.run_duration) AS run_durations
                FROM (
                    SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                    FROM {dms_joblog_full} l
                    INNER JOIN {dms_prclog_full} p ON p.sessionid = l.sessionid AND p.prcid = l.prcid
                    WHERE p.mapref = %s
                ) x
                ORDER BY 1
            """
            cursor.execute(query, (mapref,))
        else:
            # Note: INTERVAL cannot be parameterized, so we use string formatting
            query = f""" 
                SELECT x.prcdt, x.mapref,
                       EXTRACT(EPOCH FROM x.run_duration) AS run_durations
                FROM (
                    SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                    FROM {dms_joblog_full} l
                    INNER JOIN {dms_prclog_full} p ON p.sessionid = l.sessionid AND p.prcid = l.prcid
                    WHERE p.mapref = %s
                      AND l.prcdt >= CURRENT_TIMESTAMP - INTERVAL '{period} days'
                ) x
                ORDER BY 1
            """
            cursor.execute(query, (mapref,))
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
        dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
        
        if period.upper() == 'ALL':
            # No date filter for 'ALL' option
            query = f""" 
                SELECT x.prcdt, x.mapref,
                       EXTRACT(DAY    FROM x.run_duration) * 86400 +
                       EXTRACT(HOUR   FROM x.run_duration) * 3600 +
                       EXTRACT(MINUTE FROM x.run_duration) * 60 +
                       EXTRACT(SECOND FROM x.run_duration) AS run_durations
                FROM (
                    SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                    FROM {dms_joblog_full} l, {dms_prclog_full} p
                    WHERE p.sessionid = l.sessionid
                      AND p.prcid = l.prcid
                      AND p.mapref = :mapref
                ) x
                ORDER BY 1
            """
            cursor.execute(query, {'mapref': mapref})
        else:
            query = f""" 
                SELECT x.prcdt, x.mapref,
                       EXTRACT(DAY    FROM x.run_duration) * 86400 +
                       EXTRACT(HOUR   FROM x.run_duration) * 3600 +
                       EXTRACT(MINUTE FROM x.run_duration) * 60 +
                       EXTRACT(SECOND FROM x.run_duration) AS run_durations
                FROM (
                    SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                    FROM {dms_joblog_full} l, {dms_prclog_full} p
                    WHERE p.sessionid = l.sessionid
                      AND p.prcid = l.prcid
                      AND p.mapref = :mapref
                      AND l.prcdt >= SYSDATE - :period 
                ) x
                ORDER BY 1
            """
            cursor.execute(query, {'mapref': mapref, 'period': period})
    
    try:
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# jobs and average run duration
@dashboard_bp.route("/jobs_average_run_duration", methods=["GET"])
def jobs_average_run_duration():
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_joblog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_JOBLOG')
        dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
        
        # Quote table names if they contain uppercase letters
        dms_joblog_ref = f'"{dms_joblog_table}"' if dms_joblog_table != dms_joblog_table.lower() else dms_joblog_table
        dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
        
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_joblog_full = f'{schema_prefix}{dms_joblog_ref}'
        dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
        
        # PostgreSQL: Use EXTRACT(EPOCH FROM ...) for duration
        query = f""" 
            SELECT x.mapref AS JOB_NAME
                  ,AVG(EXTRACT(EPOCH FROM x.run_duration)) AS avg_seconds
            FROM (
                SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                FROM {dms_joblog_full} l
                INNER JOIN {dms_prclog_full} p ON p.sessionid = l.sessionid AND p.prcid = l.prcid
            ) x
            GROUP BY x.mapref
        """
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_joblog_full = f"{schema_prefix}DMS_JOBLOG"
        dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
        
        query = f""" 
            SELECT x.mapref AS JOB_NAME
                  ,AVG(EXTRACT(DAY    FROM x.run_duration) * 86400 +
                       EXTRACT(HOUR   FROM x.run_duration) * 3600 +
                       EXTRACT(MINUTE FROM x.run_duration) * 60 +
                       EXTRACT(SECOND FROM x.run_duration)) AS avg_seconds
            FROM (
                SELECT l.prcdt, l.mapref, p.enddt - p.strtdt AS run_duration
                FROM {dms_joblog_full} l, {dms_prclog_full} p
                WHERE p.sessionid = l.sessionid
                AND   p.prcid = l.prcid
            ) x
            GROUP BY x.mapref
        """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# jobs and number of times successful and failed
@dashboard_bp.route("/jobs_successful_failed", methods=["GET"])
def jobs_successful_failed():
    connection = create_metadata_connection()
    cursor = connection.cursor()
    
    # Detect database type
    db_type = _detect_db_type(connection)
    schema = (os.getenv("DMS_SCHEMA", "")).strip()
    
    # Get table references for PostgreSQL (handles case sensitivity)
    if db_type == "POSTGRESQL":
        schema_lower = schema.lower() if schema else 'public'
        dms_prclog_table = get_postgresql_table_name(cursor, schema_lower, 'DMS_PRCLOG')
        dms_prclog_ref = f'"{dms_prclog_table}"' if dms_prclog_table != dms_prclog_table.lower() else dms_prclog_table
        schema_prefix = f'{schema_lower}.' if schema else ''
        dms_prclog_full = f'{schema_prefix}{dms_prclog_ref}'
        
        query = f""" 
            SELECT p.mapref AS job_name_prefix
                  ,SUM(CASE WHEN p.status = 'FL' THEN 1 ELSE 0 END) AS failed_count
                  ,SUM(CASE WHEN p.status = 'PC' THEN 1 ELSE 0 END) AS succeeded_count
            FROM {dms_prclog_full} p
            WHERE p.status IN ('PC','FL')
            GROUP BY p.mapref
        """
    else:  # Oracle
        schema_prefix = f"{schema}." if schema else ""
        dms_prclog_full = f"{schema_prefix}DMS_PRCLOG"
        
        query = f""" 
            SELECT p.mapref AS job_name_prefix
                  ,SUM(CASE WHEN p.status = 'FL' THEN 1 ELSE 0 END) AS failed_count
                  ,SUM(CASE WHEN p.status = 'PC' THEN 1 ELSE 0 END) AS succeeded_count
            FROM {dms_prclog_full} p
            WHERE p.status IN ('PC','FL')
            GROUP BY p.mapref
        """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

