"""" Authentication controller """
from fastapi import Request
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin, UserChangePassword
from app.schemas.token import TokenRefresh
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest


class AuthController:
    """ Authentication controller """

    def __init__(self, service: AuthService):
        self.service = service

    def register(self, request: Request, user_data: UserCreate):
        """ register a new user """
        return self.service.register_user(request, user_data)

    def login(self, login_data: UserLogin):
        """ Login user """
        return self.service.login(login_data)

    def refresh(self, refresh_data: TokenRefresh):
        """ Refresh access token """
        return self.service.refresh_token(refresh_data)

    def change_password(self, current_user, password_data: UserChangePassword):
        """ Change user password """
        return self.service.change_password(current_user, password_data)

    def forget_password(self, data: ForgotPasswordRequest):
        """ Change user password """
        return self.service.forget_password(data)

    def reset_password(self, data: ResetPasswordRequest):
        """ Change user password """
        return self.service.reset_password(data)
