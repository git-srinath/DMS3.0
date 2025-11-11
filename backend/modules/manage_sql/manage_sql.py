from flask import Blueprint, request, jsonify, send_file
from database.dbconnect import create_oracle_connection
import os
from modules.logger import info, error


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
            
            # Query to fetch SQL logic for specific code
            query = "SELECT DWMAPRSQL FROM DWMAPRSQL WHERE DWMAPRSQLCD = :sql_code AND CURFLG = 'Y'"
            cursor.execute(query, {'sql_code': sql_code})
            
            # Fetch the result
            result = cursor.fetchone()
            
            if result:
                # Extract the SQL content (CLOB)
                sql_content = result[0].read() if hasattr(result[0], 'read') else str(result[0])
                
                info(f"Fetched SQL logic for code: {sql_code}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully fetched SQL logic for code: {sql_code}',
                    'data': {
                        'sql_code': sql_code,
                        'sql_content': sql_content
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
            cursor = conn.cursor()
            
            # Create a variable to capture the return value
            sql_id = cursor.var(int)
            
            # Call the Oracle package function
            sql = f"""
            BEGIN
                :sql_id := {ORACLE_SCHEMA}.PKGDWMAPR.CREATE_UPDATE_SQL(
                    p_dwmaprsqlcd => :sql_code,
                    p_dwmaprsql => :sql_content
                );
            END;
            """
            
            # Execute the PL/SQL block
            cursor.execute(sql, {
                'sql_code': sql_code,
                'sql_content': sql_content,
                'sql_id': sql_id
            })
            
            # Commit the transaction
            conn.commit()
            
            # Get the returned SQL ID
            returned_sql_id = sql_id.getvalue()
                        
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
        
        if not sql_content:
            return jsonify({
                'success': False,
                'message': 'SQL content is required'
            }), 400
        
        # Create Oracle connection
        conn = create_oracle_connection()
        
        try:
            cursor = conn.cursor()
            
            # Create a variable to capture the return value
            validation_result = cursor.var(str)
            
            # Call the Oracle package function
            sql = f"""
            BEGIN
                :validation_result := {ORACLE_SCHEMA}.PKGDWMAPR.VALIDATE_SQL(
                    p_logic => :sql_content
                );
            END;
            """
            
            # Execute the PL/SQL block
            cursor.execute(sql, {
                'sql_content': sql_content,
                'validation_result': validation_result
            })
            
            # Get the validation result ('Y' for valid, 'N' for invalid)
            result = validation_result.getvalue()
            
            # Check if validation passed or failed
            if result == 'Y':
                info("SQL validation passed successfully")
                return jsonify({
                    'success': True,
                    'message': 'SQL validation passed successfully',
                    'is_valid': True,
                    'validation_result': result
                })
            else:
                info("SQL validation failed")
                return jsonify({
                    'success': False,
                    'message': 'SQL validation failed',
                    'is_valid': False,
                    'validation_result': result
                })
            
        except Exception as e:
            error_message = str(e)
            error(f"Database error in validate_sql: {error_message}")
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

