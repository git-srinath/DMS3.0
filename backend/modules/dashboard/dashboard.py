from flask import Blueprint, request, jsonify
from database.dbconnect import create_oracle_connection
import os
import dotenv
import json
from decimal import Decimal
from datetime import timedelta

dotenv.load_dotenv()

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)
SCHEMA=os.getenv("SCHEMA")

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
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=""" 
        select count(m.mapref) total_mappings
              ,sum(case when m.lgvrfyflg = 'Y' then 1 else 0 end) logic_verified
              ,sum(case when m.stflg = 'A' then 1 else 0 end) active_mappings
              ,sum(case when j.mapref is not null then 1 else 0 end) total_jobs
              ,sum(case when j.stflg = 'A' then 1 else 0 end) Active_jobs
              ,sum(case when f.mapref is not null then 1 else 0 end) job_flow_created
              ,sum(case when s.mapref is not null then 1 else 0 end) schedule_created
        from dwmapr m, dwjob j, dwjobflw f, dwjobsch s
        where m.curflg = 'Y'
        and   j.mapref (+) = m.mapref
        and   j.curflg (+) = m.curflg
        and   f.mapref (+) = j.mapref
        and   f.jobid (+) = j.jobid
        and   f.curflg (+) = 'Y'
        and   s.jobflwid (+) = f.jobflwid
        and   s.curflg (+) = 'Y'
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
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=""" 
            SELECT 
                l.mapref, 
                COUNT(l.mapref) AS times_processed,
                AVG(l.srcrows) AS average_src_rows_processed,
                CEIL(AVG(l.trgrows)) AS average_trg_rows_processed,
                MAX(enddt - strtdt) AS max_job_duration, 
                MIN(enddt - strtdt) AS min_job_duration
            FROM 
                dwjoblog l,
                dwprclog p
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
    
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=""" 
            SELECT 
                mapref,
                TO_CHAR(prcdt, 'yyyy-mm-dd') AS time_group,
                SUM(srcrows) AS total_srcrows,
                SUM(trgrows) AS total_trgrows
            FROM 
                dwjoblog
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
    try:
        cursor.execute(query, (mapref, period))
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
    
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=f""" 
            select x.prcdt, x.mapref,
                   extract(day    from x.run_duration) * 86400 +
                   extract(hour   from x.run_duration) * 3600 +
                   extract(minute from x.run_duration) * 60 +
                   extract(second from x.run_duration) run_durations
            from (
                select l.prcdt, l.mapref, enddt - strtdt run_duration
                from dwjoblog l, dwprclog p
                where p.sessionid = l.sessionid
                  and p.prcid = l.prcid
                  and p.mapref = :mapref
                  AND l.prcdt >= sysdate - :period 
            ) x
            order by 1
        """
    try:
        cursor.execute(query, (mapref, period))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# jobs and average run duration
@dashboard_bp.route("/jobs_average_run_duration", methods=["GET"])
def jobs_average_run_duration():
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=f""" 
        select x.mapref AS JOB_NAME
              ,avg(extract(day    from x.run_duration) * 86400 +
                   extract(hour   from x.run_duration) * 3600 +
                   extract(minute from x.run_duration) * 60 +
                   extract(second from x.run_duration)) avg_seconds
        from (
        select l.prcdt, l.mapref, enddt - strtdt run_duration
        from  dwjoblog l, dwprclog p
        where p.sessionid = l.sessionid
        and   p.prcid = l.prcid
         ) x
        group by x.mapref

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
    connection = create_oracle_connection()
    cursor = connection.cursor()
    query=f""" 
        select p.mapref AS job_name_prefix
            --,count(p.mapref) total_count
        	,sum(case when p.status = 'FL' then 1 else 0 end) failed_count
            ,sum(case when p.status = 'PC' then 1 else 0 end) succeeded_count
            
        from  dwprclog p
        where status in ('PC','FL')
        group by p.mapref
        """ 
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(process_rows(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

