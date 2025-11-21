from flask import Blueprint, request, jsonify, send_file
from database.dbconnect import create_oracle_connection
import os
from modules.logger import info, error
from modules.mapper import pkgdwmapr_python as pkgdwmapr


# Get Oracle schema from environment
ORACLE_SCHEMA = os.getenv("SCHEMA")

# Create blueprint
manage_sql_bp = Blueprint('manage-sql', __name__)


@manage_sql_bp.route('/fetch-all-sql-codes', methods=['GET'])
def fetch_all_sql_codes():
    try:
        conn = create_oracle_connection()
        
        try:
            cursor = conn.cursor()
            
            # Query to fetch all SQL codes
            query = "SELECT DWMAPRSQLCD FROM DWMAPRSQL WHERE CURFLG = 'Y'"
            cursor.execute(query)
            
            # Fetch all results
            results = cursor.fetchall()
            
            # Convert to list of SQL codes
            sql_codes = [row[0] for row in results]
            
            info(f"Fetched {len(sql_codes)} SQL codes")
            
            return jsonify({
                'success': True,
                'message': f'Successfully fetched {len(sql_codes)} SQL codes',
                'data': sql_codes,
                'count': len(sql_codes)
            })
            
        except Exception as e:
            error_message = str(e)
            error(f"Database error in fetch_all_sql_codes: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in fetch_all_sql_codes: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while fetching SQL codes: {str(e)}'
        }), 500


@manage_sql_bp.route('/fetch-sql-logic', methods=['GET'])
def fetch_sql_logic():
    try:
        # Get sql_code from query parameters
        sql_code = request.args.get('sql_code')
        
        if not sql_code:
            return jsonify({
                'success': False,
                'message': 'SQL code parameter is required'
            }), 400
        
        conn = create_oracle_connection()
        
        try:
            cursor = conn.cursor()
            
            # Query to fetch SQL logic and connection ID for specific code
            query = "SELECT DWMAPRSQL, SQLCONID FROM DWMAPRSQL WHERE DWMAPRSQLCD = :sql_code AND CURFLG = 'Y'"
            cursor.execute(query, {'sql_code': sql_code})
            
            # Fetch the result
            result = cursor.fetchone()
            
            if result:
                # Extract the SQL content (CLOB) and connection ID
                sql_content = result[0].read() if hasattr(result[0], 'read') else str(result[0])
                connection_id = str(result[1]) if result[1] is not None else None
                
                info(f"Fetched SQL logic for code: {sql_code}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully fetched SQL logic for code: {sql_code}',
                    'data': {
                        'sql_code': sql_code,
                        'sql_content': sql_content,
                        'connection_id': connection_id
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'No SQL logic found for code: {sql_code}'
                }), 404
                
        except Exception as e:
            error_message = str(e)
            error(f"Database error in fetch_sql_logic: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in fetch_sql_logic: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while fetching SQL logic: {str(e)}'
        }), 500



@manage_sql_bp.route('/fetch-sql-history', methods=['GET'])
def fetch_sql_history():
    try:
        # Get sql_code from query parameters
        sql_code = request.args.get('sql_code')
        
        if not sql_code:
            return jsonify({
                'success': False,
                'message': 'SQL code parameter is required'
            }), 400
        
        conn = create_oracle_connection()
        
        try:
            cursor = conn.cursor()
            
            # Query to fetch SQL logic for specific code
            query = "SELECT RECCRDT,DWMAPRSQL FROM DWMAPRSQL WHERE DWMAPRSQLCD = :sql_code AND CURFLG = 'N'"
            cursor.execute(query, {'sql_code': sql_code})
            
            # Fetch all results - we want to get all historical versions
            results = cursor.fetchall()
            
            if results:
                # Process all historical versions
                history_items = []
                for result in results:
                    # Extract the date (first column)
                    date_value = result[0]
                    # Extract the SQL content (second column - CLOB)
                    sql_content = result[1].read() if hasattr(result[1], 'read') else str(result[1])
                    
                    # Add to history items
                    history_items.append({
                        'date': date_value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(date_value, 'strftime') else str(date_value),
                        'sql_content': sql_content
                    })
                
                info(f"Fetched {len(history_items)} historical versions for SQL code: {sql_code}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully fetched SQL history for code: {sql_code}',
                    'data': {
                        'sql_code': sql_code,
                        'history_items': history_items
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'No SQL history found for code: {sql_code}'
                }), 404
                
        except Exception as e:
            error_message = str(e)
            error(f"Database error in fetch_sql_history: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in fetch_sql_history: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while fetching SQL history: {str(e)}'
        }), 500






@manage_sql_bp.route('/save-sql', methods=['POST'])
def save_sql():
    try:
        data = request.json
        
        # Validate required parameters
        sql_code = data.get('sql_code')
        sql_content = data.get('sql_content')
        connection_id = data.get('connection_id')  # Optional - source database connection
        
        if not sql_code:
            return jsonify({
                'success': False,
                'message': 'SQL code is required'
            }), 400
            
        if not sql_content:
            return jsonify({
                'success': False,
                'message': 'SQL content is required'
            }), 400
        
        # Validate SQL code doesn't contain spaces (as per Oracle function logic)
        if ' ' in sql_code:
            return jsonify({
                'success': False,
                'message': 'Spaces are not allowed in SQL code'
            }), 400
        
        # Create Oracle connection
        conn = create_oracle_connection()
        
        try:
            # Call Python function with connection ID
            returned_sql_id = pkgdwmapr.create_update_sql(
                conn, 
                sql_code, 
                sql_content,
                connection_id  # Pass the source connection ID
            )
                        
            return jsonify({
                'success': True,
                'message': 'SQL saved/updated successfully',
                'sql_id': returned_sql_id,
                'sql_code': sql_code
            })
            
        except Exception as e:
            conn.rollback()
            error_message = str(e)
            error(f"Database error in save_sql: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error: {error_message}'
            }), 500         
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in save_sql: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while saving SQL: {str(e)}'
        }), 500


@manage_sql_bp.route('/validate-sql', methods=['POST'])
def validate_sql():
    try:
        data = request.json
        
        # Validate required parameters
        sql_content = data.get('sql_content')
        connection_id = data.get('connection_id')  # Optional connection ID
        
        if not sql_content:
            return jsonify({
                'success': False,
                'message': 'SQL content is required'
            }), 400
        
        # Create connection based on connection_id
        # If connection_id is provided, use that connection for validation
        # Otherwise, use metadata connection
        if connection_id:
            try:
                from database.dbconnect import create_target_connection
                conn = create_target_connection(connection_id)
                connection_name = f"connection ID {connection_id}"
            except Exception as e:
                error(f"Error creating target connection: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to connect to selected database: {str(e)}',
                    'is_valid': False
                }), 500
        else:
            conn = create_oracle_connection()
            connection_name = "metadata connection"
        
        try:
            # Validate SQL by executing EXPLAIN PLAN or trying to parse it
            result = pkgdwmapr.validate_sql(conn, sql_content)
            
            # Check if validation passed or failed
            if result == 'Y':
                info(f"SQL validation passed successfully on {connection_name}")
                return jsonify({
                    'success': True,
                    'message': f'SQL validation passed successfully on {connection_name}',
                    'is_valid': True,
                    'validation_result': result
                })
            else:
                info(f"SQL validation failed on {connection_name}")
                return jsonify({
                    'success': False,
                    'message': f'SQL validation failed on {connection_name}: {result}',
                    'is_valid': False,
                    'validation_result': result
                })
            
        except Exception as e:
            error_message = str(e)
            error(f"Database error in validate_sql on {connection_name}: {error_message}")
            return jsonify({
                'success': False,
                'message': f'Database error during validation: {error_message}',
                'is_valid': False
            }), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        error(f"Error in validate_sql: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'An error occurred while validating SQL: {str(e)}',
            'is_valid': False
        }), 500


@manage_sql_bp.route('/get-connections', methods=['GET'])
def get_connections():
    """
    Get list of active database connections from DWDBCONDTLS
    This allows manage_sql to query data from external/source databases
    """
    try:
        conn = create_oracle_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT conid, connm, dbhost, dbsrvnm
                FROM DWDBCONDTLS
                WHERE curflg = 'Y'
                ORDER BY connm
            """)
            
            connections = []
            for row in cursor.fetchall():
                connections.append({
                    'conid': str(row[0]),
                    'connm': row[1],
                    'dbhost': row[2],
                    'dbsrvnm': row[3]
                })
            
            cursor.close()
            return jsonify(connections)
        finally:
            conn.close()
    except Exception as e:
        error(f"Error fetching connections: {str(e)}")
        return jsonify({"error": str(e)}), 500

