""" Post Controller """

from datetime import date
from typing import List, Optional

from fastapi import UploadFile

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostExportRequest, PostUpdate
from app.services.post_service import PostService


class PostController:
    """ Post Controller """

    def __init__(self, service: PostService):
        self.service = service

    def get_post_list(
        self, page: int, per_page: int, title: Optional[str],
        description: Optional[str], post_status: Optional[int],  start_date: Optional[date],
        end_date: Optional[date], sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """ Get Post List"""
        return self.service.get_post_list(
            page=page,
            per_page=per_page,
            title=title,
            description=description,
            post_status=post_status,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )

    async def get_post(self, post_id: int):
        """ Get Post """
        return await self.service.get_post(post_id)

    async def create_post(self, post_data: PostCreate, post: Post):
        """ create a new post """
        return await self.service.create_post(post_data, post)

    async def update_post(self, user_id: int, user_data: PostUpdate, post: Post):
        """ create a new post """
        return await self.service.update_post(user_id, user_data, post)

    def delete_posts(self, post_ids: List[int], current_user: User):
        """ Delete Posts """
        return self.service.delete_posts(post_ids, current_user)

    async def import_csv(self, file: UploadFile, current_user: User):
        """ CSV Import Posts """
        return await self.service.import_csv(file, current_user)

    async def export_csv(self, export_request: PostExportRequest):
        """ CSV Export Posts """
        return await self.service.export_csv(export_request)
