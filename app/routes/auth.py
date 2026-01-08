"""
Enhanced authentication routes with account lock features
"""
from fastapi import APIRouter, Depends, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from app.dependencies.dependencies import AuthControllerDep
from app.models import User
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserChangePassword
from app.schemas.token import TokenRefresh
from app.dependencies.auth import get_current_active_user
from app.core.config import settings

router = APIRouter(prefix=settings.API_V1_STR +
                   "/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    controller: AuthControllerDep
) -> StandardResponse:
    """Register a new user with audit trail"""
    return controller.register(request, user_data)


@router.post("/login", response_model=StandardResponse)
async def login(
    login_data: UserLogin,
    controller: AuthControllerDep
):
    """Login user with account lock protection"""
    return controller.login(login_data)


@router.post("/refresh", response_model=StandardResponse)
async def refresh(
    refresh_data: TokenRefresh,
    controller: AuthControllerDep
):
    """Refresh access token using refresh token"""
    return controller.refresh(refresh_data)


@router.post("/change-password", response_model=StandardResponse)
async def change_password(
    password_data: UserChangePassword,
    controller: AuthControllerDep,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""
    return controller.change_password(current_user, password_data)


@router.get("/me", response_model=StandardResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    user_response = UserResponse.model_validate(current_user)
    return StandardResponse(
        success=True,
        message="User information retrieved successfully",
        data=jsonable_encoder(user_response)
    )


@router.post("/logout", response_model=StandardResponse)
async def logout():
    """Logout user (client should discard tokens)"""
    return StandardResponse(
        success=True,
        message="Successfully logged out",
        data=None
    )
