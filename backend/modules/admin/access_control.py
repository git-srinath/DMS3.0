from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import re
import os.path
from modules.login.login import token_required

load_dotenv()

# Database setup
engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
Session = sessionmaker(bind=engine)

# Blueprint setup
access_control_bp = Blueprint('access_control', __name__)



@access_control_bp.route('/get-permissions', methods=['GET'])
@token_required
def get_permissions(current_user_id):
    user_id = request.args.get('user_id')
    module_name = request.args.get('module_name')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    #check if user id exist in the database
    session = Session()
    user = session.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id}).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    #get the user's permissions
    query="""
            SELECT 
                pm.module_name,
                r.role_name,
                CASE WHEN pm.can_view = 1 THEN 'Yes' ELSE 'No' END as can_view,
                CASE WHEN pm.can_create = 1 THEN 'Yes' ELSE 'No' END as can_create,
                CASE WHEN pm.can_edit = 1 THEN 'Yes' ELSE 'No' END as can_edit,
                CASE WHEN pm.can_delete = 1 THEN 'Yes' ELSE 'No' END as can_delete
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            JOIN permission_matrix pm ON r.role_id = pm.role_id
            WHERE u.user_id = :user_id
            AND pm.module_name = :module_name
            ORDER BY r.role_name, pm.module_name;

"""
    permissions = session.execute(text(query), {'user_id': user_id, 'module_name': module_name}).fetchall()
    
    # Convert Row objects to dictionaries for JSON serialization
    permissions_list = []
    for permission in permissions:
        permissions_list.append({
            'module_name': permission.module_name,
            'role_name': permission.role_name,
            'can_view': permission.can_view,
            'can_create': permission.can_create,
            'can_edit': permission.can_edit,
            'can_delete': permission.can_delete
        })
    
    session.close()
    
    #return the permissions
    return jsonify({'permissions': permissions_list})





