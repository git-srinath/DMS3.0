from flask import Blueprint, request, jsonify
from database.dbconnect import create_metadata_connection
import os
from modules.logger import info, error
import builtins

crud_dbconnections_bp = Blueprint('crud-dbconnections', __name__)

table_name = 'DMS_DBCONDTLS'

def _detect_db_type(conn):
    """Detect database type from connection"""
    module_name = builtins.type(conn).__module__
    if "psycopg" in module_name or "pg8000" in module_name:
        return "POSTGRESQL"
    elif "oracledb" in module_name or "cx_Oracle" in module_name:
        return "ORACLE"
    else:
        # Fallback: try a simple query
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
                return "ORACLE"  # Default fallback

def format_error_message(err):
    """Format error messages to be more user-friendly"""
    error_str = str(err)
    if "DPY-6005" in error_str or "timed out" in error_str.lower():
        return "Unable to connect to the database. Please check if the database server is running and accessible."
    elif "ORA-" in error_str:
        return f"Database error: {error_str}"
    elif "connection" in error_str.lower() and "refused" in error_str.lower():
        return "Database connection refused. Please check database server status and network connectivity."
    else:
        return f"An error occurred: {error_str}"

# Fetch all DB connections (list view)
@crud_dbconnections_bp.route('/dbconnections', methods=['GET'])
def get_all_db_connections():
    conn = None
    try:
        conn = create_metadata_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, dbdescr, sslfg, curflg FROM {table_name} WHERE curflg = 'Y'")
        columns = [desc[0].lower() for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        error(f"Error fetching connections: {str(e)}")
        user_message = format_error_message(e)
        return jsonify({"success": False, "message": user_message, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Get a single DB connection by conid
@crud_dbconnections_bp.route('/dbconnections/<int:conid>', methods=['GET'])
def get_db_connection(conid):
    conn = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        
        if db_type == "POSTGRESQL":
            cursor.execute(f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, dbdescr, sslfg, curflg FROM {table_name} WHERE conid = %s AND curflg = 'Y'", (conid,))
        else:  # Oracle
            cursor.execute(f"SELECT conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, constr, dbdescr, sslfg, curflg FROM {table_name} WHERE conid = :conid AND curflg = 'Y'", {"conid": conid})
        
        row = cursor.fetchone()
        columns = [desc[0].lower() for desc in cursor.description]
        data = dict(zip(columns, row)) if row else None
        cursor.close()
        if data:
            return jsonify({"success": True, "data": data})
        else:
            return jsonify({"success": False, "message": "Record not found"}), 404
    except Exception as e:
        error(f"Error fetching connection: {str(e)}")
        user_message = format_error_message(e)
        return jsonify({"success": False, "message": user_message, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Create a new DB connection
@crud_dbconnections_bp.route('/dbconnections', methods=['POST'])
def create_db_connection():
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        data = request.json
        conid = None
        
        # Get new conid from sequence
        if db_type == "POSTGRESQL":
            cursor.execute("SELECT nextval('DMS_DBCONDTLSSEQ')")
        else:  # Oracle
            cursor.execute("SELECT DMS_DBCONDTLSSEQ.NEXTVAL FROM dual")
        (conid,) = cursor.fetchone()
        
        # Insert with database-specific syntax
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                INSERT INTO {table_name} 
                (conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, dbdescr, sslfg, reccrdt, recupdt, curflg, crtdby) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Y', %s)
            """, (
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
                data.get("sslfg", 'N'),
                data.get("crtdby", 'system')
            ))
        else:  # Oracle
            cursor.execute(f"""
                INSERT INTO {table_name} 
                (conid, connm, dbtyp, dbhost, dbport, dbsrvnm, usrnm, passwd, constr, dbdescr, sslfg, reccrdt, recupdt, curflg, crtdby) 
                VALUES (:conid, :connm, :dbtyp, :dbhost, :dbport, :dbsrvnm, :usrnm, :passwd, :constr, :dbdescr, :sslfg, SYSDATE, SYSDATE, 'Y', :crtdby)
            """, {
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
                "sslfg": data.get("sslfg", 'N'),
                "crtdby": data.get("crtdby", 'system')
            })
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()
        
        cursor.close()
        return jsonify({"success": True, "conid": conid})
    except Exception as e:
        error(f"Create error: {str(e)}")
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except:
                pass
        user_message = format_error_message(e)
        return jsonify({"success": False, "message": user_message, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Update a DB connection (by conid)
@crud_dbconnections_bp.route('/dbconnections/<int:conid>', methods=['PUT'])
def update_db_connection(conid):
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        data = request.json
        
        if db_type == "POSTGRESQL":
            cursor.execute(f"""
                UPDATE {table_name} SET
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
            """, (
                data.get("connm"),
                data.get("dbtyp"),
                data.get("dbhost"),
                data.get("dbport"),
                data.get("dbsrvnm"),
                data.get("usrnm"),
                data.get("passwd"),
                data.get("constr"),
                data.get("dbdescr"),
                data.get("sslfg", 'N'),
                data.get("uptdby", 'system'),
                conid
            ))
        else:  # Oracle
            cursor.execute(f"""
                UPDATE {table_name} SET
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
            """, {
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
                "sslfg": data.get("sslfg", 'N'),
                "uptdby": data.get("uptdby", 'system')
            })
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()
        
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        error(f"Update error: {str(e)}")
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except:
                pass
        user_message = format_error_message(e)
        return jsonify({"success": False, "message": user_message, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Delete (soft-delete) a DB connection
@crud_dbconnections_bp.route('/dbconnections/<int:conid>', methods=['DELETE'])
def delete_db_connection(conid):
    conn = None
    db_type = None
    try:
        conn = create_metadata_connection()
        db_type = _detect_db_type(conn)
        cursor = conn.cursor()
        
        # Soft-delete (set curflg = 'N')
        if db_type == "POSTGRESQL":
            cursor.execute(f"UPDATE {table_name} SET curflg = 'N', actby = %s, actdt = CURRENT_TIMESTAMP WHERE conid = %s", ('system', conid))
        else:  # Oracle
            cursor.execute(f"UPDATE {table_name} SET curflg = 'N', actby = :actby, actdt = SYSDATE WHERE conid = :conid", {"conid": conid, "actby": 'system'})
        
        # Commit only if autocommit is disabled (PostgreSQL with autocommit=False)
        if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
            conn.commit()
        elif db_type == "ORACLE":
            conn.commit()
        
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        error(f"Delete error: {str(e)}")
        if conn and db_type:
            try:
                if db_type == "POSTGRESQL" and not getattr(conn, 'autocommit', False):
                    conn.rollback()
                elif db_type == "ORACLE":
                    conn.rollback()
            except:
                pass
        user_message = format_error_message(e)
        return jsonify({"success": False, "message": user_message, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Test database connection
@crud_dbconnections_bp.route('/dbconnections/test', methods=['POST'])
def test_db_connection():
    """Test a database connection with provided credentials"""
    test_conn = None
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['dbtyp', 'dbhost', 'dbport', 'dbsrvnm', 'usrnm', 'passwd']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        db_type = data.get('dbtyp', '').upper()
        host = data.get('dbhost')
        port = data.get('dbport')
        database = data.get('dbsrvnm')
        username = data.get('usrnm')
        password = data.get('passwd')
        connection_string = data.get('constr')
        
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
            import mysql.connector
            if connection_string:
                # Parse connection string if provided (basic implementation)
                test_conn = mysql.connector.connect(connection_string)
            else:
                test_conn = mysql.connector.connect(
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
            return jsonify({
                "success": False,
                "message": f"Unsupported database type: {db_type}. Supported types: Oracle, PostgreSQL, MySQL, SQL Server"
            }), 400
        
        info(f"Test connection successful for {db_type} database: {host}:{port}/{database}")
        return jsonify({
            "success": True,
            "message": f"Connection test successful! Successfully connected to {db_type} database."
        })
        
    except ImportError as e:
        error(f"Database driver not installed: {str(e)}")
        missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
        return jsonify({
            "success": False,
            "message": f"Database driver not installed. Please install: {missing_module}"
        }), 500
    except Exception as e:
        error(f"Test connection failed: {str(e)}")
        user_message = format_error_message(e)
        return jsonify({
            "success": False,
            "message": user_message,
            "error": str(e)
        }), 500
    finally:
        if test_conn:
            try:
                test_conn.close()
            except:
                pass