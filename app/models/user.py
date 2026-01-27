""" User Model """
from __future__ import annotations  # Forward references
import enum
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, date, timezone
from sqlalchemy import Index, String, Boolean, Integer, BigInteger, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


if TYPE_CHECKING:
    from app.models.post import Post  # only for type checking

class UserRole(enum.Enum):
    """User roles enum"""
    USER = 0
    ADMIN = 1


class User(BaseModel):
    """ User Model """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    profile_path: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, unique=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role: Mapped[int] = mapped_column(
        Integer, default=UserRole.USER.value, nullable=False)
    lock_flg: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    lock_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_lock_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    create_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True)
    updated_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True)
    deleted_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True)

    # Relationships
    created_posts: Mapped[List["Post"]] = relationship(
        "Post",
        foreign_keys="Post.create_user_id",
        back_populates="creator",
        lazy="dynamic"
    )
    updated_posts: Mapped[List["Post"]] = relationship(
        "Post",
        foreign_keys="Post.updated_user_id",
        back_populates="updater",
        lazy="dynamic"
    )
    deleted_posts: Mapped[List["Post"]] = relationship(
        "Post",
        foreign_keys="Post.deleted_user_id",
        back_populates="deleter",
        lazy="dynamic"
    )

    __table_args__ = (
        # Composite indexes
        Index('idx_user_status', 'lock_flg', 'role', 'deleted_at'),
        Index('idx_user_search', 'name', 'email'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role={self.role})>"

    @property
    def is_locked(self) -> bool:
        """Check if account is locked"""
        return self.lock_flg

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role in [UserRole.ADMIN.value]

    def increment_lock_count(self):
        """Increment failed login attempts"""
        self.lock_count += 1
        if self.lock_count >= 5:  # Lock after 5 failed attempts
            self.lock_flg = True
            self.last_lock_at = datetime.now()

    def reset_lock_count(self):
        """Reset failed login attempts"""
        self.lock_count = 0
        self.lock_flg = False

    def record_login(self):
        """Record successful login"""
        self.last_login_at = datetime.now()
        self.reset_lock_count()
