"""
Enhanced authentication routes with account lock features
"""
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.dependencies.dependencies import AuthControllerDep
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserChangePassword
from app.schemas.token import Token, TokenRefresh
from app.dependencies.auth import get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    controller: AuthControllerDep
) -> UserResponse:
    """Register a new user with audit trail"""
    return controller.register(request, user_data)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    controller: AuthControllerDep
):
    """Login user with account lock protection"""
    return controller.login(login_data)


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_data: TokenRefresh,
    controller: AuthControllerDep
):
    """Refresh access token using refresh token"""
    return controller.refresh(refresh_data)


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    controller: AuthControllerDep,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""
    return controller.change_password(current_user, password_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)"""
    return {"message": "Successfully logged out"}
