""" Password Reset Model """
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class PasswordReset(BaseModel):
    """
    Password Reset Model
    """
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    token: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False, unique=True)
