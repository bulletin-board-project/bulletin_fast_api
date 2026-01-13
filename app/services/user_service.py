""" User Service """
from datetime import UTC, date, datetime
import math
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.response import PaginatedResponse, StandardResponse
from app.schemas.user import UserResponse


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

    def get_user(self):
        """ Get User """

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
