""" User Controller """

from datetime import date
from typing import List, Optional

from fastapi import UploadFile
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class UserController:
    """ User Controller """

    def __init__(self, service: UserService):
        self.service = service

    def get_user_list(
        self, page: int, per_page: int, name: Optional[str],
        email: Optional[str], role: Optional[int],  start_date: Optional[date],
        end_date: Optional[date], sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """ Get User List"""
        return self.service.get_user_list(
            page=page,
            per_page=per_page,
            name=name,
            email=email,
            role=role,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )

    async def get_user(self, user_id: int):
        """ Get User """
        return await self.service.get_user(user_id)

    async def create_user(self, user_data: UserCreate, profile_image: UploadFile, user: User):
        """ create a new user """
        return await self.service.create_user(user_data, profile_image, user)

    async def update_user(self, user_id: int, user_data: UserUpdate, profile_image: UploadFile, user: User):
        """ create a new user """
        return await self.service.update_user(user_id, user_data, profile_image, user)

    def delete_users(self, user_ids: List[int], current_user: User):
        """ Delete User """
        return self.service.delete_users(user_ids, current_user)

    def unlock_users(self, user_ids: List[int], current_user: User):
        """ Unlock User """
        return self.service.unlock_users(user_ids, current_user)
