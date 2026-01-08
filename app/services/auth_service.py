""" Authentication service """

from datetime import timedelta
from fastapi import HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.models import User
from app.repositories.user_repository import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    check_account_lock
)
from app.core.config import settings
from app.models import UserRole
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserLogin, UserChangePassword, UserResponse


class AuthService:
    """ Authentication service """

    def __init__(self, repo: UserRepository, db: Session):
        self.user_repo = repo
        self.db = db

    def register_user(self, request: Request, user_data: UserCreate):
        """ Register a new user """
        # Check if user already exists
        existing_user = self.user_repo.exists_by_email_or_phone(
            user_data.email, user_data.phone)

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Email already registered",
                        "error_code": "EMAIL_EXISTS"
                    }
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Phone number already registered",
                    "error_code": "PHONE_EXISTS"
                }
            )

        # Get current user ID from request (if available)
        current_user_id = self._get_current_user_id(request)
        # Create new user
        hashed_password = get_password_hash(user_data.password)

        user_dict = user_data.model_dump(
            exclude={'confirm_password'}, exclude_none=True)
        # Add additional fields
        user_dict.update({
            'role': UserRole.USER.value,
            'password': hashed_password
        })
        if current_user_id is not None:
            user_dict['created_user_id'] = current_user_id

        db_user = User(**user_dict)
        user = self.user_repo.create(
            db_user
        )

        self.db.commit()
        self.db.refresh(user)
        # Convert to UserResponse
        user_response = UserResponse.model_validate(user)

        return StandardResponse(
            success=True,
            message="User registered successfully",
            data=jsonable_encoder(user_response)
        )

    def login(self, login_data: UserLogin):
        """ User login """
        user = self.user_repo.get_by_email(login_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Incorrect email or password",
                    "error_code": "INVALID_CREDENTIALS"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if account is locked
        is_locked, lock_message = check_account_lock(user)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "success": False,
                    "message": lock_message,
                    "error_code": "ACCOUNT_LOCKED"
                }
            )

        # Check if user is deleted (soft delete)
        if user.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "success": False,
                    "message": "Account has been deleted",
                    "error_code": "ACCOUNT_DELETED"
                }
            )

        if not verify_password(login_data.password, user.password):
            user.increment_lock_count()
            self.db.commit()
            attempts_left = 5 - user.lock_count

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": f"Incorrect email or password. Attempts left: {attempts_left}",
                    "error_code": "INVALID_CREDENTIALS",
                    "details": {"attempts_left": attempts_left}
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.record_login()
        self.db.commit()

        tokens = self._generate_tokens(user)
        return StandardResponse(
            success=True,
            message="Login successful",
            data=tokens
        )

    def refresh_token(self, refresh_data):
        """ Refresh access token """
        payload = verify_token(refresh_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid refresh token",
                    "error_code": "INVALID_REFRESH_TOKEN"
                },
            )

        user_id = payload.get("sub")
        user = self.user_repo.get_by_id(user_id)

        if not user or user.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "User not found",
                    "error_code": "USER_NOT_FOUND"
                }
            )

        # Check if account is locked
        is_locked, lock_message = check_account_lock(user)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "success": False,
                    "message": lock_message,
                    "error_code": "ACCOUNT_LOCKED"
                }
            )

        tokens = self._generate_tokens(user, refresh=False)

        return StandardResponse(
            success=True,
            message="Token refreshed successfully",
            data=tokens
        )

    def change_password(self, current_user: User, data: UserChangePassword):
        """ Change user password """
        if not verify_password(data.current_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Current password is incorrect",
                    "error_code": "INVALID_CURRENT_PASSWORD"
                }
            )

        # Update password
        current_user.password = get_password_hash(data.new_password)
        current_user.updated_user_id = current_user.id
        self.db.commit()

        return StandardResponse(
            success=True,
            message="Password changed successfully",
            data=None
        )

    def _generate_tokens(self, user: User, refresh=True):
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            expires_delta=access_token_expires
        )

        result = {"access_token": access_token, "token_type": "bearer"}

        if refresh:
            result["refresh_token"] = create_refresh_token(
                data={"sub": str(user.id), "email": user.email, }
            )

        return result

    def _get_current_user_id(self, request: Request):
        token = request.headers.get("Authorization")
        if not token:
            return None
        payload = verify_token(token.replace("Bearer ", ""))
        return payload.get("sub") if payload else None
