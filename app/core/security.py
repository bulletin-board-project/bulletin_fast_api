"""
Security utilities: JWT tokens, password hashing
"""
from datetime import datetime, timedelta
import hashlib
import os
import secrets
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
        "type": "access"
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(
        hours=settings.REFRESH_TOKEN_EXPIRE_HOUR
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def check_account_lock(user) -> Tuple[bool, Optional[str]]:
    """
    Check if account is locked
    Returns: (is_locked, message_if_locked)
    """
    if user.lock_flg:
        lock_time = user.last_lock_at
        if lock_time:
            # Auto-unlock after 30 minutes
            unlock_time = lock_time + timedelta(minutes=30)
            if datetime.now() < unlock_time:
                remaining = unlock_time - datetime.now()
                minutes = int(remaining.total_seconds() // 60)
                return True, f"Account locked. Try again in {minutes} minutes."
            else:
                # Auto unlock
                user.reset_lock_count()
                return False, None
        return True, "Account is locked. Contact administrator."
    return False, None


def generate_otp(length: int = 8) -> str:
    """ Generate OTP """
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp_with_salt(otp: str) -> tuple[str, str]:
    """Salt and hash OTP"""
    salt = settings.OTP_SALT
    return hashlib.sha256(f"{salt}:{otp}".encode()).hexdigest()

# def hash_otp(otp: str) -> str:
#     """ Hash OTP """
#     return pwd_context.hash(otp)


# def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
#     """ verify OTP """
#     try:
#         return pwd_context.verify(plain_otp, hashed_otp)
#     except Exception as e:  # pylint: disable=broad-exception-caught
#         print(f"Reset Token verification error: {e}")
#         return False
