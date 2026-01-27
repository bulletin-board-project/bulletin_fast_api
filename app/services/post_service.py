""" Post Service """
from datetime import date, datetime
import math
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.post import Post
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostCreate, PostExportRequest, PostResponse, PostUpdate
from app.schemas.response import PaginatedResponse, StandardResponse
from app.utils.file_handler import FileHandler


class PostService:
    """ Post Service """

    def __init__(self, repo: PostRepository, db: Session):
        self.post_repo = repo
        self.db = db

    def get_post_list(
        self,
        page: int,
        per_page: int,
        title: Optional[str],
        description: Optional[str],
        post_status: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedResponse[PostResponse]:
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
            'title': title,
            'description': description,
            'status': post_status,
            'start_date': start_date,
            'end_date': end_date,
            'is_active': True,
        }

        # Get data from repository
        posts: List[Post]
        total_count: int
        posts, total_count = self.post_repo.find_posts(
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
        post_responses = [
            PostResponse.model_validate(post)
            for post in posts
        ]

        # Create response
        return PaginatedResponse[PostResponse](
            success=True,
            message=f"Found {len(post_responses)} post(s)",
            data=post_responses,
            current_page=page,
            per_page=per_page,
            total=total_count,
            total_pages=total_pages
        )

    async def get_post(self, post_id: int):
        """ Get Post """
        existing_post = self.post_repo.get_by_id(post_id)
        if not existing_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Post Not Found",
                    "error_code": "NOT_FOUND"
                }
            )

        # Convert to UserResponse
        post_response = PostResponse.model_validate(existing_post)

        return StandardResponse(
            success=True,
            message="Get Post Success",
            data=jsonable_encoder(post_response)
        )

    async def create_post(self, post_data: PostCreate, current_user: User):
        """ Create a new Post """

        print('user==>', current_user)
        # Check if post already exists
        existing_post = self.post_repo.get_by_title(post_data.title)

        if existing_post:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Title already registered",
                    "error_code": "TITLE_EXISTS"
                }
            )

        # Create new psot
        post_dict = post_data.model_dump(exclude_none=True)
        # Add additional fields
        post_dict.update({
            'create_user_id': current_user.id
        })

        db_post = Post(**post_dict)
        post = self.post_repo.save(
            db_post
        )

        self.db.commit()
        self.db.refresh(post)
        # Convert to UserResponse
        post_response = PostResponse.model_validate(post)

        return StandardResponse(
            success=True,
            message="Post created successfully",
            data=jsonable_encoder(post_response)
        )

    async def update_post(self, post_id: int, update_data: PostUpdate, current_user: User):
        """ Update Post """

        print('user==>', current_user)

        original_post = self.post_repo.get_by_id(post_id)
        if not original_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Post Not Found",
                    "error_code": "NOT_FOUND"
                }
            )

        if current_user.id != original_post.create_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "You haven't permission to edit this.",
                    "error_code": "UNAUTHORIZED_POST_EDIT"
                }
            )

        if update_data.title and update_data.title != original_post.title:
            exists = self.post_repo.get_by_title(update_data.title)
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Title already exists",
                        "error_code": "TITLE_EXISTS"
                    }
                )

        post_dict = update_data.model_dump(exclude_none=True)
        # Add additional fields
        post_dict["updated_user_id"] = current_user.id

        for k, v in post_dict.items():
            setattr(original_post, k, v)

        self.db.commit()
        self.db.refresh(original_post)

        # Convert to PostResponse
        post_response = PostResponse.model_validate(original_post)

        return StandardResponse(
            success=True,
            message="Post created successfully",
            data=jsonable_encoder(post_response)
        )

    def delete_posts(self, post_ids: List[int], current_user: User) -> StandardResponse:
        """Delete Post"""
        # Validation: Check if posts exist
        existing_post = self.post_repo.find_by_ids(post_ids)
        if len(existing_post) != len(post_ids):
            missing_ids = set(post_ids) - {u.id for u in existing_post}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=StandardResponse(
                    success=False,
                    message=f"Posts not found: {missing_ids}",
                    error_code="NOT_FOUND"
                ).model_dump()
            )

        existing_user_ids = [post.create_user_id for post in existing_post]

        if current_user.id not in existing_user_ids:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=StandardResponse(
                    success=False,
                    message="You haven't permission to delete this.",
                    error_code="UNAUTHORIZED_POST_DELETE"
                ).model_dump()
            )

        try:
            # Perform soft delete
            deleted_count = self.post_repo.bulk_delete_posts(
                post_ids=post_ids,
                deleted_at=datetime.now(),
                current_user=current_user
            )

            # Update other audit fields
            audit_fields = {
                'updated_at': datetime.now(),
                'updated_user_id': current_user.id
            }
            audit_update_count = self.post_repo.bulk_update_general(
                post_ids=post_ids,
                **audit_fields
            )

            self.db.commit()

            # Return Standard response
            return StandardResponse(
                success=True,
                message=f"Successfully soft deleted {deleted_count} post(s)",
                data={
                    "deleted_count": deleted_count,
                    "post_ids": post_ids,
                    "audit_updated": audit_update_count
                }
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=StandardResponse(
                    success=False,
                    message=f"Failed to delete posts: {str(e)}",
                    error_code="INTERNAL_SERVER_ERROR"
                ).model_dump()
            ) from e

    async def import_csv(self, file: UploadFile, current_user: User) -> StandardResponse:
        """import CSV Post"""

        results = {
            "total": 0,
            "success": 0,
            "errors": []
        }
        row_index = 0
        existing_titles = [title.lower()
                           for title in self.post_repo.get_all_titles()]
        seen_titles = set()

        async for rows in FileHandler.read_file(
            file,
            required_columns=["title", "description", "status"],
            chunk_size=100
        ):
            posts = []

            for row in rows:
                row_index += 1
                results["total"] += 1

                try:
                    # Row-level validation
                    title = str(row.get("title", "")).strip()
                    description = str(row.get("description", "")).strip()
                    status_str = str(row.get("status", "")).strip()

                    if not title:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Title is required"
                        )
                    if not description:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Description is required"
                        )
                    if not status_str:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Status is required"
                        )

                    post_status = int(status_str)
                    if post_status not in [0, 1]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Status must be 0 or 1"
                        )

                    # Check if title already exists
                    lower_title = title.lower()
                    if lower_title in existing_titles or lower_title in seen_titles:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Title already exists"
                        )

                    seen_titles.add(lower_title)

                    post = Post(
                        title=title,
                        description=description,
                        status=post_status,
                        create_user_id=current_user.id
                    )

                    posts.append(post)
                    results["success"] += 1

                except HTTPException as e:
                    results["errors"].append(
                        f"Row {row_index}: {e.detail}"
                    )
                except (ValueError, TypeError) as e:
                    results["errors"].append(
                        f"Row {row_index}: Data error - {str(e)}"
                    )
            # Commit per chunk
            if posts:
                try:
                    self.db.bulk_save_objects(posts)
                    self.db.commit()
                except SQLAlchemyError as e:
                    self.db.rollback()
                    results["errors"].append(
                        f"Chunk failed near row {row_index}: {str(e)}"
                    )

        message = f"Imported {results['success']} of {results['total']} posts successfully"
        if results["errors"]:
            message += f" ({len(results['errors'])} errors)"

        return StandardResponse(
            success=True,
            message=message,
            data=results
        )

    async def export_csv(self, export_request: PostExportRequest) -> StreamingResponse:
        """ Export posts to CSV file """

        posts = []
        if export_request.post_ids and len(export_request.post_ids) > 0:
            posts = self.post_repo.find_by_ids(export_request.post_ids)
            print(f"DEBUG: Found {len(posts)} posts by IDs")
        else:
            # Validation
            if export_request.page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=PaginatedResponse(
                        success=False,
                        message="Page must be positive",
                        error_code="INVALID_PAGE"
                    ).model_dump(),
                )

            if export_request.per_page < 1 or export_request.per_page > 100:
                export_request.per_page = min(
                    max(export_request.per_page, 1), 100)

            # Calculate offset
            offset = (export_request.page - 1) * export_request.per_page

            # Prepare filters
            filters = {
                'title': export_request.title,
                'description': export_request.description,
                'status': export_request.status,
                'start_date': export_request.start_date,
                'end_date': export_request.end_date,
                'is_active': True,
            }

            # Get data from repository
            posts,total_count  = self.post_repo.find_posts(
                offset=offset,
                limit=export_request.per_page,
                sort_by=export_request.sort_by,
                sort_order=export_request.sort_order,
                **filters
            )
            print(f"DEBUG: Found {total_count} total posts")
            print(f"DEBUG: Found {len(posts) if posts else 0} posts")

        if not posts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No posts found matching the criteria"
            )

        if not posts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No posts found to export"
            )

        if not isinstance(posts, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Posts is not a list"
            )

        # Convert to response models
        post_responses = [
            PostResponse.model_validate(post)
            for post in posts
        ]

        data = [p.model_dump() for p in post_responses]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"posts_export_{timestamp}.csv"
        # Create CSV file
        result = FileHandler.write_csv(data)

        return StreamingResponse(
            iter([result["content"]]),
            media_type=result["media_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"  # CORS
            }
        )
