""" User Route"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status
from app.core.config import settings
from app.dependencies.auth import get_current_active_user
from app.dependencies.dependencies import UserControllerDep
from app.models.user import User
from app.schemas.response import PaginatedResponse, StandardResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate, user_create_form, user_update_form

router = APIRouter(prefix=settings.API_V1_STR + "/users", tags=["User"])


@router.get("/", response_model=PaginatedResponse[UserResponse],
            status_code=status.HTTP_200_OK)
async def get_user_list(
    controller: UserControllerDep,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(
        None, description="Search by user name (partial match)"),
    email: Optional[str] = Query(
        None, description="Search by email (partial match)"),
    role: Optional[int] = Query(
        None, description="Filter by role (0=User, 1=Admin)"),
    start_date: Optional[date] = Query(
        None, description="Created from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="Created to date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query(
        "created_at", description="Search by email (partial match)"),
    sort_order: Optional[str] = Query(
        "desc", description="Search by email (partial match)"),
    current_user: User = Depends(get_current_active_user)
):
    """ Get User List"""
    print("current user : ", current_user)
    return controller.get_user_list(
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


@router.get("/{user_id}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, controller: UserControllerDep, current_user: User =
                   Depends(get_current_active_user),) -> StandardResponse:
    """
    Docstring for get_user
    """
    print("current user : ", current_user)
    return await controller.get_user(user_id)


@router.post("/create", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create(
    controller: UserControllerDep,
    profile_image: UploadFile = File(...),
    user_data: UserCreate = Depends(user_create_form),
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse:
    """Create a new user"""
    return await controller.create_user(user_data, profile_image, current_user)


@router.put("/{user_id}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def update(
    user_id: int,
    controller: UserControllerDep,
    profile_image: UploadFile | None = File(None),
    user_data: UserUpdate = Depends(user_update_form),
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse:
    """Update existing user"""
    return await controller.update_user(user_id, user_data, profile_image, current_user)


@router.post("/delete", response_model=StandardResponse,
             status_code=status.HTTP_200_OK)
async def delete_users(
        controller: UserControllerDep,
        current_user: User = Depends(get_current_active_user),
        user_ids: List[int] = Body(
        ...,
        description="List of user IDs to unlock",
        examples=[[1, 2, 3]]
        ),
):
    """ Delete Users """
    if not user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User IDs list cannot be empty"
        )

    if len(user_ids) > 100:  # limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlock more than 100 users at once"
        )
    return controller.delete_users(user_ids, current_user)


@router.post("/unlock", response_model=StandardResponse,
             status_code=status.HTTP_200_OK)
async def unlock_users(
        controller: UserControllerDep,
        current_user: User = Depends(get_current_active_user),
        user_ids: List[int] = Body(
        ...,
        description="List of user IDs to unlock",
        examples=[[1, 2, 3]]
        ),
):
    """ Unlock Users """
    if not user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User IDs list cannot be empty"
        )

    if len(user_ids) > 100:  # limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlock more than 100 users at once"
        )
    return controller.unlock_users(user_ids, current_user)
