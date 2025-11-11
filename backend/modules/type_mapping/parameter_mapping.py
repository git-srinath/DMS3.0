from flask import Blueprint, jsonify, request
from database.dbconnect  import create_oracle_connection

from modules.helper_functions import get_parameter_mapping, add_parameter_mapping 

parameter_mapping_bp = Blueprint('parameter_mapping', __name__)


@parameter_mapping_bp.route("/parameter_mapping", methods=["GET"])
def parameter_display():
    try:
        conn = create_oracle_connection()
        try:
            parameter_data = get_parameter_mapping(conn)
            return jsonify(parameter_data)
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@parameter_mapping_bp.route("/parameter_add", methods=["POST"])
def add_parameter():
    try:
        data = request.json
        prtyp = data.get('PRTYP')
        prcd = data.get('PRCD')
        prdesc = data.get('PRDESC')
        prval = data.get('PRVAL')

        if not all([prtyp, prcd, prdesc, prval]):
            return jsonify({"error": "All fields are required"}), 400

        conn = create_oracle_connection()
        try:
            add_parameter_mapping(conn, prtyp, prcd, prdesc, prval)
            return jsonify({"message": "Parameter mapping added successfully"}), 200
        finally:
            conn.close()
    except Exception as e:
        print(f"Error in add_parameter: {str(e)}")
        return jsonify({"error": str(e)}), 500 