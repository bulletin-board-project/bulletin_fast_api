"""Post Model"""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from app.models.base import BaseModel

# Only for type checking (avoids circular import at runtime)
if TYPE_CHECKING:
    from app.models.user import User


class Status(enum.Enum):
    """Post Status Enum"""
    INACTIVE = 0
    ACTIVE = 1


class Post(BaseModel):
    """Post Model"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True,  index=True)
    description: Mapped[str] = mapped_column(
        String(5000), nullable=False)
    status: Mapped[int] = mapped_column(
        Integer,  default=Status.ACTIVE.value, nullable=False, index=True)

    # Foreign Keys with relationships
    create_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    updated_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    deleted_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[create_user_id],
        back_populates="created_posts"
    )
    updater: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_user_id],
        back_populates="updated_posts"
    )
    deleter: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[deleted_user_id],
        back_populates="deleted_posts"
    )

    __table_args__ = (
        # Composite indexes
        Index('idx_post_status', 'status', 'deleted_at'),
        Index('idx_post_title', 'title'),
        Index('idx_post_create_user', 'create_user_id', 'created_at'),
        Index('idx_post_updated_user', 'updated_user_id'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, title='{self.title}', description='{self.description}', status={self.status})>"  # pylint: disable=line-too-long

    @property
    def is_active(self) -> bool:
        """Check if post is active"""
        return self.status in [Status.ACTIVE.value]

    @property
    def is_deleted(self) -> bool:
        """Check if user is soft deleted"""
        return self.deleted_at is not None

    def soft_delete(self, deleted_by_user_id: int | None = None):
        """Soft delete the post"""
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_user_id = deleted_by_user_id
        self.status = Status.INACTIVE.value
    