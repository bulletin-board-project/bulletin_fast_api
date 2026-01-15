""" User Service """
from datetime import UTC, date, datetime
import math
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.core.exceptions import AppException
from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.response import PaginatedResponse, StandardResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.utils.helper import delete_profile_image, upload_profile_image


class UserService:
    """ User Service """

    def __init__(self, repo: UserRepository, db: Session):
        self.user_repo = repo
        self.db = db

    def get_user_list(
        self,
        page: int,
        per_page: int,
        name: Optional[str],
        email: Optional[str],
        role: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedResponse[UserResponse]:
        """Get paginated user list"""

        # Validation
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=PaginatedResponse(
                    success=False,
                    message="Page must be positive",
                    error_code="INVALID_PAGE"
                ).model_dump(),
            )

        if per_page < 1 or per_page > 100:
            per_page = min(max(per_page, 1), 100)

        # Calculate offset
        offset = (page - 1) * per_page

        # Prepare filters
        filters = {
            'name': name,
            'email': email,
            'role': role,
            'start_date': start_date,
            'end_date': end_date,
            'is_active': True,
            'is_locked': None
        }

        # Get data from repository
        users: List[User]
        total_count: int
        users, total_count = self.user_repo.find_users(
            offset=offset,
            limit=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            **filters
        )

        # Calculate total pages
        total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0

        # Validate page exists
        if page > total_pages > 0:
            raise ValueError(f"Page {page} does not exist")

        # Convert to response models
        user_responses = [
            UserResponse.model_validate(user)
            for user in users
        ]

        # Create response
        return PaginatedResponse[UserResponse](
            success=True,
            message=f"Found {len(user_responses)} user(s)",
            data=user_responses,
            current_page=page,
            per_page=per_page,
            total=total_count,
            total_pages=total_pages
        )

    async def get_user(self, user_id: int):
        """ Get User """
        existing_user = self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "User Not Found",
                    "error_code": "USER_NOT_FOUND"
                }
            )

        # Convert to UserResponse
        user_response = UserResponse.model_validate(existing_user)

        return StandardResponse(
            success=True,
            message="Get User Success",
            data=jsonable_encoder(user_response)
        )

    async def create_user(self, user_data: UserCreate, profile_image: UploadFile, current_user: User):
        """ Register a new user """

        print('uploadFile ==>', profile_image)
        print('user==>', current_user)
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
        try:
            profile_url = None
            if profile_image is not None:
                print(f"🔼 Uploading image: {profile_image.filename}")
                profile_url = await upload_profile_image(profile_image)
                print(f"✅ Image uploaded to: {profile_url}")

            # Create new user
            hashed_password = get_password_hash(user_data.password)

            user_dict = user_data.model_dump(
                exclude={'confirm_password'}, exclude_none=True)
            # Add additional fields
            user_dict.update({
                'password': hashed_password,
                'profile_path': profile_url,
                'create_user_id': current_user.id
            })

            db_user = User(**user_dict)
            user = self.user_repo.save(
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
        except Exception as e:
            # remove uploaded file if DB fails
            if profile_url:
                await delete_profile_image(profile_url)
            raise e

    async def update_user(self, user_id: int, update_data: UserUpdate, profile_image: UploadFile, current_user: User):
        """ Register a new user """

        print('uploadFile ==>', profile_image)
        print('user==>', current_user)

        original_user = self.user_repo.get_by_id(user_id)
        if not original_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "User Not Found",
                    "error_code": "USER_NOT_FOUND"
                }
            )

        if update_data.email and update_data.email != original_user.email:
            exists = self.user_repo.get_by_email(update_data.email)
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Email already registered",
                        "error_code": "EMAIL_EXISTS"
                    }
                )
        if update_data.phone and update_data.phone != original_user.phone:
            exists = self.user_repo.get_by_phone(update_data.phone)
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "This Phone Number already registered",
                        "error_code": "PHONE_EXISTS"
                    }
                )

        try:
            ## Profile Path ##
            profile_url = original_user.profile_path
            new_profile_url = None
            if profile_image:
                # new image upload
                print(f"🔼 Uploading image: {profile_image.filename}")
                new_profile_url = await upload_profile_image(profile_image)
                print(f"✅ Image uploaded to: {profile_url}")
                profile_url = new_profile_url

            ## Password ##
            hashed_password = original_user.password
            if update_data.password:
                hashed_password = get_password_hash(update_data.password)

            user_dict = update_data.model_dump(exclude_none=True)
            # Add additional fields
            user_dict["password"] = hashed_password
            user_dict["profile_path"] = profile_url
            user_dict["updated_user_id"] = current_user.id

            for k, v in user_dict.items():
                setattr(original_user, k, v)

            self.db.commit()
            self.db.refresh(original_user)

            # commit success → delete old image
            if profile_image and original_user.profile_path:
                await delete_profile_image(original_user.profile_path)

            # Convert to UserResponse
            user_response = UserResponse.model_validate(original_user)

            return StandardResponse(
                success=True,
                message="User registered successfully",
                data=jsonable_encoder(user_response)
            )
        except Exception as e:
            # upload success but db fail → rollback image
            if new_profile_url:
                await delete_profile_image(new_profile_url)
            raise e

    def delete_users(self, user_ids: List[int], current_user: User) -> StandardResponse:
        """Delete User"""
        # Validation: Check if users exist
        existing_users = self.user_repo.find_by_ids(user_ids)
        if len(existing_users) != len(user_ids):
            missing_ids = set(user_ids) - {u.id for u in existing_users}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=StandardResponse(
                    success=False,
                    message=f"Users not found: {missing_ids}",
                    error_code="USER_NOT_FOUND"
                ).model_dump()
            )

        if current_user.id in user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=StandardResponse(
                    success=False,
                    message="Cannot delete your own account",
                    error_code="BAD_REQUEST"
                ).model_dump()
            )

        try:
            # Perform soft delete
            deleted_count = self.user_repo.bulk_delete_users(
                user_ids=user_ids,
                deleted_at=datetime.utcnow(),
                current_user=current_user
            )

            # Update other audit fields
            audit_fields = {
                'updated_at': datetime.now(UTC),
                'updated_user_id': current_user.id
            }
            audit_update_count = self.user_repo.bulk_update_general(
                user_ids=user_ids,
                **audit_fields
            )

            self.db.commit()

            # Return Standard response
            return StandardResponse(
                success=True,
                message=f"Successfully soft deleted {deleted_count} user(s)",
                data={
                    "deleted_count": deleted_count,
                    "user_ids": user_ids,
                    "audit_updated": audit_update_count
                }
            )

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=StandardResponse(
                    success=False,
                    message=f"Failed to delete users: {str(e)}",
                    error_code="INTERNAL_SERVER_ERROR"
                ).model_dump()
            ) from e

    def unlock_users(self, user_ids: List[int], current_user: User) -> StandardResponse:
        """Unlock User"""
        # Validation: Check if users exist
        existing_users = self.user_repo.find_by_ids(user_ids)
        if len(existing_users) != len(user_ids):
            missing_ids = set(user_ids) - {u.id for u in existing_users}
            raise AppException(
                message=f"Users not found: {missing_ids}",
                error_code="USER_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
            # raise HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     detail=StandardResponse(
            #         success=False,
            #         message=f"Users not found: {missing_ids}",
            #         error_code="USER_NOT_FOUND"
            #     ).model_dump()
            # )

        # Check if users are already unlocked
        locked_users = [u for u in existing_users if u.lock_flg]
        if not locked_users:
            raise AppException(
                message="Users are already unlocked",
                error_code="USER_ALREADY_UNLOCK",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            # raise HTTPException(
            #     status_code=status.HTTP_400_BAD_REQUEST,
            #     detail=StandardResponse(
            #         success=False,
            #         message=" users are already unlocked",
            #         error_code="USER_ALREADY_UNLOCK"
            #     ).model_dump()
            # )

        lock_count_reset_value = 0
        last_lock_at_value = None
        audit_fields = {
            'updated_at': datetime.now(UTC),
            'updated_user_id': current_user.id
        }

        try:
            # First update lock-specific fields
            lock_update_count = self.user_repo.bulk_update_lock_status(
                user_ids=user_ids,
                lock_status=False,  # Unlock
                last_lock_at=last_lock_at_value,
                lock_count=lock_count_reset_value
            )

            # Then update audit fields
            audit_update_count = self.user_repo.bulk_update_general(
                user_ids=user_ids,
                **audit_fields
            )

            # Commit transaction
            self.db.commit()

            # Return standard response
            return StandardResponse(
                success=True,
                message=f"Successfully unlocked {lock_update_count} user(s)",
                data={
                    "unlocked_count": lock_update_count,
                    "user_ids": user_ids,
                    "audit_updated": audit_update_count
                }
            )
        except Exception as e:
            self.db.rollback()
            raise AppException(
                message=f"Failed to unlock users: {str(e)}",
                error_code="INTERNAL_SERVER_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
            # raise HTTPException(
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     detail=StandardResponse(
            #         success=False,
            #         message=f"Failed to unlock users: {str(e)}",
            #         error_code="INTERNAL_SERVER_ERROR"
            #     ).model_dump()
            # ) from e
