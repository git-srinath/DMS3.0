from datetime import datetime, timedelta
import hashlib
import os
import re
import secrets
import smtplib

import jwt
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database.dbconnect import sqlite_engine


load_dotenv()

# Database setup: reuse the same SQLite engine as the rest of the backend
Session = sessionmaker(bind=sqlite_engine)

router = APIRouter(tags=["auth"])


# ----- Helper functions -----

def generate_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha512((password + salt).encode()).hexdigest()


def is_valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def send_reset_email_fastapi(email: str, reset_token: str, base_url: str) -> bool:
    """
    Send password reset email. This mirrors the Flask implementation but avoids
    relying on the global Flask `request` object by accepting base_url explicitly.
    """
    msg = MIMEMultipart()
    msg["From"] = os.getenv("MAIL_USERNAME")
    msg["To"] = email
    msg["Subject"] = "Password Reset Request"

    reset_link = f"{base_url}reset-password?token={reset_token}"
    body = f"""
    You have requested to reset your password.
    Please click on the following link to reset your password:
    {reset_link}

    This link will expire in 30 minutes.
    If you did not request this, please ignore this email.
    """

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT")))
        server.starttls()
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:  # pragma: no cover - logging side-effect
        # Support both FastAPI/package context and legacy Flask context
        try:
            from backend.modules.logger import error
        except ImportError:
            from modules.logger import error  # type: ignore

        error(f"Error sending email: {str(e)}")
        return False


def get_user_from_token(request: Request):
    """
    Decode JWT token from Authorization header or cookie and return user record.
    Mirrors the behavior of the Flask `token_required` decorator.
    """
    # Support both FastAPI/package context and legacy Flask context
    try:
        from backend.modules.logger import info, error
    except ImportError:
        from modules.logger import info, error  # type: ignore

    token = None

    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # Check cookies if no header token
    if not token:
        token = request.cookies.get("token")

    if not token:
        error("Authentication failed: No token provided")
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        user_id = data["user_id"]

        session = Session()
        try:
            user = session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
        finally:
            session.close()

        if not user:
            error(f"Authentication failed: User ID {user_id} not found")
            raise HTTPException(status_code=401, detail="User not found")

        info(f"User {user.username} authenticated successfully")
        return user

    except jwt.ExpiredSignatureError:
        error("Authentication failed: Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        error("Authentication failed: Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")


# ----- Pydantic models -----


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: int
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    department: str | None = None
    role: str
    change_password: bool
    show_notification: bool


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SimpleMessageResponse(BaseModel):
    message: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: int


# ----- Routes -----


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response):
    session = Session()
    try:
        username = payload.username
        password = payload.password

        if not username or not password:
            raise HTTPException(
                status_code=400, detail="Username and password are required"
            )

        user = session.execute(
            text("SELECT * FROM users WHERE username = :username AND is_active = 1"),
            {"username": username},
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=401, detail="Hmm, that didn’t work. Try again!"
            )

        if getattr(user, "account_status", None) == "PENDING":
            raise HTTPException(
                status_code=403, detail="Account is pending approval"
            )

        login_attempts = session.execute(
            text(
                """
                SELECT COUNT(*) FROM login_audit_log 
                WHERE user_id = :user_id 
                AND login_status = 'FAILED' 
                AND login_timestamp > datetime('now', '-15 minutes')
            """
            ),
            {"user_id": user.user_id},
        ).scalar()

        if login_attempts >= 5:
            raise HTTPException(
                status_code=403,
                detail="Account locked. Please try again after 15 minutes",
            )

        hashed_password = hash_password(password, user.salt)
        if hashed_password != user.password_hash:
            session.execute(
                text(
                    """
                    INSERT INTO login_audit_log (user_id, ip_address, login_status, login_type)
                    VALUES (:user_id, :ip_address, 'FAILED', 'PASSWORD')
                """
                ),
                {
                    "user_id": user.user_id,
                    "ip_address": "0.0.0.0",  # IP not easily available here; can be improved
                },
            )
            session.commit()
            raise HTTPException(
                status_code=401, detail="Hmm, that didn’t work. Try again!"
            )

        token = jwt.encode(
            {"user_id": user.user_id, "exp": datetime.utcnow() + timedelta(days=1)},
            os.getenv("JWT_SECRET_KEY"),
            algorithm="HS256",
        )

        session.execute(
            text(
                """
                INSERT INTO login_audit_log (user_id, ip_address, login_status, login_type)
                VALUES (:user_id, :ip_address, 'SUCCESS', 'PASSWORD')
            """
            ),
            {
                "user_id": user.user_id,
                "ip_address": "0.0.0.0",
            },
        )

        session.execute(
            text("UPDATE users SET last_login = datetime('now') WHERE user_id = :user_id"),
            {"user_id": user.user_id},
        )

        session.commit()

        user_profile = session.execute(
            text(
                """
                SELECT u.email, up.first_name, up.last_name, up.phone_number as phone, 
                       up.department, r.role_name
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON r.role_id = ur.role_id
                WHERE u.user_id = :user_id
            """
            ),
            {"user_id": user.user_id},
        ).fetchone()

        role_name = (
            user_profile.role_name if user_profile and user_profile.role_name else "User"
        )

        response_data = LoginResponse(
            token=token,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=(
                user_profile.first_name
                if user_profile and user_profile.first_name
                else None
            ),
            last_name=(
                user_profile.last_name
                if user_profile and user_profile.last_name
                else None
            ),
            phone=user_profile.phone if user_profile and user_profile.phone else None,
            department=(
                user_profile.department
                if user_profile and user_profile.department
                else None
            ),
            role=role_name,
            change_password=bool(getattr(user, "change_password", False)),
            show_notification=bool(getattr(user, "show_notification", False)),
        )

        # Set cookie similar to Flask implementation (values from env)
        max_age = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))
        response.set_cookie(
            key="token",
            value=token,
            max_age=max_age,
            secure=True,
            httponly=False,
            samesite="lax",
            path="/",
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        from backend.modules.logger import error

        error(f"Login error (FastAPI): {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred during login"
        )
    finally:
        session.close()


@router.post(
    "/forgot-password", response_model=ForgotPasswordResponse, status_code=200
)
async def forgot_password(payload: ForgotPasswordRequest, request: Request):
    session = Session()
    try:
        email = payload.email

        user = session.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if not user:
            # Same behavior: don't reveal whether the email exists
            return ForgotPasswordResponse(
                message="If an account exists with this email, a reset link will be sent"
            )

        reset_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(minutes=30)

        session.execute(
            text(
                """
                UPDATE users 
                SET password_reset_token = :token,
                    password_reset_expires = :expires
                WHERE user_id = :user_id
            """
            ),
            {
                "token": reset_token,
                "expires": expires,
                "user_id": user.user_id,
            },
        )
        session.commit()

        base_url = str(request.base_url)
        if not send_reset_email_fastapi(email, reset_token, base_url):
            raise HTTPException(status_code=500, detail="Failed to send reset email")

        return ForgotPasswordResponse(
            message="Password reset instructions have been sent to your email"
        )

    except HTTPException:
        raise
    except Exception as e:
        from backend.modules.logger import error

        error(f"Forgot password error (FastAPI): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request",
        )
    finally:
        session.close()


@router.post("/reset-password", response_model=SimpleMessageResponse)
async def reset_password(payload: ResetPasswordRequest):
    session = Session()
    try:
        token = payload.token
        new_password = payload.new_password

        if not token or not new_password:
            raise HTTPException(
                status_code=400, detail="Token and new password are required"
            )

        if not is_valid_password(new_password):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Password must be at least 8 characters long and contain "
                    "uppercase, lowercase, numbers, and special characters"
                ),
            )

        user = session.execute(
            text(
                """
                SELECT * FROM users 
                WHERE password_reset_token = :token 
                AND password_reset_expires > datetime('now')
            """
            ),
            {"token": token},
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token"
            )

        old_passwords = session.execute(
            text(
                "SELECT password_hash FROM password_history "
                "WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 5"
            ),
            {"user_id": user.user_id},
        ).fetchall()

        new_salt = generate_salt()
        new_hash = hash_password(new_password, new_salt)

        for old_pass in old_passwords:
            if old_pass.password_hash == new_hash:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot reuse any of your last 5 passwords",
                )

        session.execute(
            text(
                """
                UPDATE users 
                SET password_hash = :hash,
                    salt = :salt,
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE user_id = :user_id
            """
            ),
            {
                "hash": new_hash,
                "salt": new_salt,
                "user_id": user.user_id,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (:user_id, :password_hash, datetime('now'))
            """
            ),
            {
                "user_id": user.user_id,
                "password_hash": new_hash,
            },
        )

        session.commit()
        return SimpleMessageResponse(
            message="Password has been reset successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        from backend.modules.logger import error

        error(f"Reset password error (FastAPI): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred resetting your password",
        )
    finally:
        session.close()


@router.get("/verify-token", response_model=VerifyTokenResponse)
async def verify_token(request: Request):
    user = get_user_from_token(request)
    return VerifyTokenResponse(valid=True, user_id=user.user_id)


class ChangePasswordAfterLoginRequest(BaseModel):
    new_password: str
    force_change: bool | None = False


@router.post(
    "/change-password-after-login", response_model=SimpleMessageResponse
)
async def change_password_after_login(
    payload: ChangePasswordAfterLoginRequest, request: Request
):
    session = Session()
    try:
        user = get_user_from_token(request)
        current_user_id = user.user_id

        new_password = payload.new_password
        force_change = bool(payload.force_change)

        if not new_password:
            raise HTTPException(
                status_code=400, detail="New password is required"
            )

        if not is_valid_password(new_password):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Password must be at least 8 characters long and contain "
                    "uppercase, lowercase, numbers, and special characters"
                ),
            )

        user_record = session.execute(
            text("SELECT * FROM users WHERE user_id = :user_id"),
            {"user_id": current_user_id},
        ).fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        if not user_record.change_password and not force_change:
            raise HTTPException(
                status_code=403,
                detail="Password change not required for this user",
            )

        old_passwords = session.execute(
            text(
                "SELECT password_hash FROM password_history WHERE user_id = :user_id "
                "ORDER BY created_at DESC LIMIT 5"
            ),
            {"user_id": current_user_id},
        ).fetchall()

        new_salt = generate_salt()
        new_hash = hash_password(new_password, new_salt)

        for old_pass in old_passwords:
            if old_pass.password_hash == new_hash:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot reuse any of your last 5 passwords",
                )

        session.execute(
            text(
                """
                UPDATE users 
                SET password_hash = :hash,
                    salt = :salt,
                    change_password = 0
                WHERE user_id = :user_id
            """
            ),
            {
                "hash": new_hash,
                "salt": new_salt,
                "user_id": current_user_id,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (:user_id, :password_hash, datetime('now'))
            """
            ),
            {
                "user_id": current_user_id,
                "password_hash": new_hash,
            },
        )

        session.commit()
        return SimpleMessageResponse(
            message="Password has been changed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        from backend.modules.logger import error

        error(f"Change password error (FastAPI): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred changing your password",
        )
    finally:
        session.close()



