""" Auth Scheme """

from pydantic import BaseModel, EmailStr


class ForgotPasswordRequest(BaseModel):
    """
    Docstring for ForgotPasswordRequest
    """
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Docstring for ResetPasswordRequest
    """
    token: str
    password: str
    confirm_password: str
