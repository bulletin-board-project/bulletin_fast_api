""" Post Routes """

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status as http_status # pylint: disable=line-too-long
from fastapi.responses import StreamingResponse
from app.core.config import settings
from app.dependencies.auth import get_current_active_user
from app.dependencies.dependencies import PostControllerDep
from app.models.user import User
from app.schemas.post import PostCreate, PostExportRequest, PostResponse, PostUpdate
from app.schemas.response import PaginatedResponse, StandardResponse


router = APIRouter(prefix=settings.API_V1_STR + "/posts", tags=["Post"])


@router.get("/", response_model=PaginatedResponse[PostResponse],
            status_code=http_status.HTTP_200_OK)
async def get_post_list(
    controller: PostControllerDep,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    title: Optional[str] = Query(
        None, description="Search by title"),
    description: Optional[str] = Query(
        None, description="Search by description"),
    status: Optional[int] = Query(
        None, description="Filter by status (0=inactive, 1=active)"),
    start_date: Optional[date] = Query(
        None, description="Created from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="Created to date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query(
        "created_at", description="Search by email (partial match)"),
    sort_order: Optional[str] = Query(
        "desc", description="Search by email (partial match)"),
):
    """ Get Post List"""
    return controller.get_post_list(
        page=page,
        per_page=per_page,
        title=title,
        description=description,
        post_status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/{post_id}", response_model=StandardResponse, status_code=http_status.HTTP_200_OK)
async def get_post(post_id: int, controller: PostControllerDep, current_user: User =
                   Depends(get_current_active_user),) -> StandardResponse:
    """
    Docstring for get_post
    """
    print("current user : ", current_user)
    return await controller.get_post(post_id)


@router.post("/create", response_model=StandardResponse, status_code=http_status.HTTP_201_CREATED)
async def create(
    controller: PostControllerDep,
    user_data: PostCreate,
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse:
    """Create a new post"""
    return await controller.create_post(user_data, current_user)


@router.put("/{post_id}", response_model=StandardResponse, status_code=http_status.HTTP_200_OK)
async def update(
    post_id: int,
    controller: PostControllerDep,
    user_data: PostUpdate,
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse:
    """Update existing post"""
    return await controller.update_post(post_id, user_data, current_user)


@router.post("/delete", response_model=StandardResponse,
             status_code=http_status.HTTP_200_OK)
async def delete_users(
        controller: PostControllerDep,
        current_user: User = Depends(get_current_active_user),
        post_ids: List[int] = Body(
        ...,
        description="List of post IDs to delete",
        examples=[[1, 2, 3]]
        ),
):
    """ Delete Posts """
    if not post_ids:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="User IDs list cannot be empty"
        )

    if len(post_ids) > 100:  # limit
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlock more than 100 posts at once"
        )
    return controller.delete_posts(post_ids, current_user)


@router.post("/import/csv", response_model=StandardResponse, status_code=http_status.HTTP_200_OK)
async def import_csv(
    controller: PostControllerDep,
    file: UploadFile = File(..., description="CSV file to upload"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Import posts from CSV file
    """
    return await controller.import_csv(file, current_user)


@router.post("/export/csv", response_class=StreamingResponse, status_code=http_status.HTTP_200_OK)
async def export_csv(
    controller: PostControllerDep,
    export_request: PostExportRequest,
):
    """
    Export posts from CSV file
    """
    return await controller.export_csv(export_request)
