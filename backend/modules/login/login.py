from flask import Blueprint, request, jsonify, make_response, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import jwt
import hashlib
import os
import secrets
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import re

load_dotenv()

# Database setup
engine = create_engine(os.getenv('SQLITE_DATABASE_URL'))
Session = sessionmaker(bind=engine)

# Blueprint setup
auth_bp = Blueprint('auth', __name__)

# Helper functions
def generate_salt():
    return secrets.token_hex(16)

def hash_password(password, salt):
    return hashlib.sha512((password + salt).encode()).hexdigest()

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def send_reset_email(email, reset_token):
    msg = MIMEMultipart()
    msg['From'] = os.getenv('MAIL_USERNAME')
    msg['To'] = email
    msg['Subject'] = 'Password Reset Request'
    
    body = f"""
    You have requested to reset your password.
    Please click on the following link to reset your password:
    {request.host_url}reset-password?token={reset_token}
    
    This link will expire in 30 minutes.
    If you did not request this, please ignore this email.
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT')))
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        from modules.logger import error
        error(f"Error sending email: {str(e)}")
        return False
    
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        session = Session()
        
        # Get user from database
        user = session.execute(
            text("SELECT * FROM users WHERE username = :username AND is_active = 1"),
            {'username': username}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'Hmm, that didn’t work. Try again!'}), 401
            
        # Add check for PENDING status
        if user.account_status == 'PENDING':
            return jsonify({'error': 'Account is pending approval'}), 403
        
        # Check if account is locked
        login_attempts = session.execute(
            text("""
                SELECT COUNT(*) FROM login_audit_log 
                WHERE user_id = :user_id 
                AND login_status = 'FAILED' 
                AND login_timestamp > datetime('now', '-15 minutes')
            """),
            {'user_id': user.user_id}
        ).scalar()
        
        if login_attempts >= 5:
            return jsonify({'error': 'Account locked. Please try again after 15 minutes'}), 403
        
        # Verify password
        hashed_password = hash_password(password, user.salt)
        if hashed_password != user.password_hash:
            # Log failed attempt
            session.execute(
                text("""
                    INSERT INTO login_audit_log (user_id, ip_address, login_status, login_type)
                    VALUES (:user_id, :ip_address, 'FAILED', 'PASSWORD')
                """),
                {
                    'user_id': user.user_id,
                    'ip_address': request.remote_addr
                }
            )
            session.commit()
            return jsonify({'error': 'Hmm, that didn’t work. Try again!'}), 401
        
        # Generate JWT token with 1 day expiry
        token = jwt.encode(
            {
                'user_id': user.user_id,
                'exp': datetime.utcnow() + timedelta(days=1)
            },
            os.getenv('JWT_SECRET_KEY'),
            algorithm='HS256'
        )
        
        # Log successful login
        session.execute(
            text("""
                INSERT INTO login_audit_log (user_id, ip_address, login_status, login_type)
                VALUES (:user_id, :ip_address, 'SUCCESS', 'PASSWORD')
            """),
            {
                'user_id': user.user_id,
                'ip_address': request.remote_addr
            }
        )
        
        # Update last login
        session.execute(
            text("UPDATE users SET last_login = datetime('now') WHERE user_id = :user_id"),
            {'user_id': user.user_id}
        )
        
        session.commit()
        
        # Get user profile data
        user_profile = session.execute(
            text("""
                SELECT u.email, up.first_name, up.last_name, up.phone_number as phone, up.department, r.role_name
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON r.role_id = ur.role_id
                WHERE u.user_id = :user_id
            """),
            {'user_id': user.user_id}
        ).fetchone()
        
        # Create response with user data
        response_data = {
            'token': token,
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'first_name': user_profile.first_name if user_profile and user_profile.first_name else None,
            'last_name': user_profile.last_name if user_profile and user_profile.last_name else None,
            'phone': user_profile.phone if user_profile and user_profile.phone else None,
            'department': user_profile.department if user_profile and user_profile.department else None,
            'role': user_profile.role_name if user_profile and user_profile.role_name else 'User',
            'change_password': bool(user.change_password),
            'show_notification': bool(user.show_notification)
        }
        
        # Create response and set cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('token', token, max_age=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES')), secure=True, path='/', samesite='Lax')
        
        return response
        
    except Exception as e:
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error  # type: ignore
        error(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500
    finally:
        session.close()

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        session = Session()
        
        # Check if user exists
        user = session.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {'email': email}
        ).fetchone()
        
        if not user:
            return jsonify({'message': 'If an account exists with this email, a reset link will be sent'}), 200
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(minutes=30)
        
        # Save reset token
        session.execute(
            text("""
                UPDATE users 
                SET password_reset_token = :token,
                    password_reset_expires = :expires
                WHERE user_id = :user_id
            """),
            {
                'token': reset_token,
                'expires': expires,
                'user_id': user.user_id
            }
        )
        session.commit()
        
        # Send reset email
        if send_reset_email(email, reset_token):
            return jsonify({'message': 'Password reset instructions have been sent to your email'}), 200
        else:
            return jsonify({'error': 'Failed to send reset email'}), 500
            
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500
    finally:
        session.close()

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
            
        if not is_valid_password(new_password):
            return jsonify({
                'error': 'Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
            }), 400
        
        session = Session()
        
        # Find user with valid reset token
        user = session.execute(
            text("""
                SELECT * FROM users 
                WHERE password_reset_token = :token 
                AND password_reset_expires > datetime('now')
            """),
            {'token': token}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Check password history
        old_passwords = session.execute(
            text("SELECT password_hash FROM password_history WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 5"),
            {'user_id': user.user_id}
        ).fetchall()
        
        new_salt = generate_salt()
        new_hash = hash_password(new_password, new_salt)
        
        # Check if new password matches any of the last 5 passwords
        for old_pass in old_passwords:
            if old_pass.password_hash == new_hash:
                return jsonify({'error': 'Cannot reuse any of your last 5 passwords'}), 400
        
        # Update password
        session.execute(
            text("""
                UPDATE users 
                SET password_hash = :hash,
                    salt = :salt,
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE user_id = :user_id
            """),
            {
                'hash': new_hash,
                'salt': new_salt,
                'user_id': user.user_id
            }
        )
        
        # Add to password history
        session.execute(
            text("""
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (:user_id, :password_hash, datetime('now'))
            """),
            {
                'user_id': user.user_id,
                'password_hash': new_hash
            }
        )
        
        session.commit()
        return jsonify({'message': 'Password has been reset successfully'}), 200
        
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        return jsonify({'error': 'An error occurred resetting your password'}), 500
    finally:
        session.close()

# Middleware for protected routes
def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        
        # Import logger inside the function to avoid circular imports
        try:
            from backend.modules.logger import info, warning, error
        except ImportError:
            from modules.logger import info, warning, error  # type: ignore
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Check for token in cookies
        if not token and 'token' in request.cookies:
            token = request.cookies.get('token')
            
        if not token:
            error('Authentication failed: No token provided')
            return jsonify({'error': 'Authentication required'}), 401
            
        try:
            # Decode token
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            user_id = data['user_id']
            
            # Get user from database
            session = Session()
            user = session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {'user_id': user_id}
            ).fetchone()
            session.close()
            
            if not user:
                error(f'Authentication failed: User ID {user_id} not found')
                return jsonify({'error': 'User not found'}), 401
                
            # Store user information in Flask's g object for the logger
            g.user = {
                'user_id': user_id,
                'username': user.username,
                'email': user.email
            }
            
            info(f'User {user.username} authenticated successfully')
            
            return f(user_id, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            error('Authentication failed: Token has expired')
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            error('Authentication failed: Invalid token')
            return jsonify({'error': 'Invalid token'}), 401
            
    # Set the name of the decorated function to avoid endpoint conflicts
    decorated.__name__ = f.__name__
    return decorated

@auth_bp.route('/verify-token', methods=['GET'])
@token_required
def verify_token(current_user_id):
    return jsonify({'valid': True, 'user_id': current_user_id}) 

@auth_bp.route('/change-password-after-login', methods=['POST'])
@token_required
def change_password_after_login(current_user_id):
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
            
        if not is_valid_password(new_password):
            return jsonify({
                'error': 'Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
            }), 400
        
        session = Session()
        
        # Find user
        user = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {'user_id': current_user_id}
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if change_password is set (only allow if true or force_change parameter is provided)
        force_change = data.get('force_change', False)
        if not user.change_password and not force_change:
            return jsonify({'error': 'Password change not required for this user'}), 403
        
        # Check password history
        old_passwords = session.execute(
            text("SELECT password_hash FROM password_history WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 5"),
            {'user_id': current_user_id}
        ).fetchall()
        
        new_salt = generate_salt()
        new_hash = hash_password(new_password, new_salt)
        
        # Check if new password matches any of the last 5 passwords
        for old_pass in old_passwords:
            if old_pass.password_hash == new_hash:
                return jsonify({'error': 'Cannot reuse any of your last 5 passwords'}), 400
        
        # Update password and reset change_password flag
        session.execute(
            text("""
                UPDATE users 
                SET password_hash = :hash,
                    salt = :salt,
                    change_password = 0
                WHERE user_id = :user_id
            """),
            {
                'hash': new_hash,
                'salt': new_salt,
                'user_id': current_user_id
            }
        )
        
        # Add to password history
        session.execute(
            text("""
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (:user_id, :password_hash, datetime('now'))
            """),
            {
                'user_id': current_user_id,
                'password_hash': new_hash
            }
        )
        
        session.commit()
        return jsonify({'message': 'Password has been changed successfully'}), 200
        
    except Exception as e:
        print(f"Change password error: {str(e)}")
        return jsonify({'error': 'An error occurred changing your password'}), 500
    finally:
        session.close() 