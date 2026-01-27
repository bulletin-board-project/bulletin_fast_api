
""" Password Reset repository Module """

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.password_reset import PasswordReset


class PasswordResetRepository:
    """ Password Reset repository implementation. """

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[PasswordReset]:
        """ Get all password resets """
        return self.db.query(PasswordReset).filter(PasswordReset.deleted_at.is_(None)).all()

    def get_by_email(self, email: str) -> Optional[PasswordReset]:
        """ Get password reset by email """
        return (
            self.db.query(PasswordReset)
            .filter(
                PasswordReset.email == email,
                PasswordReset.deleted_at.is_(None)
            )
            .first()
        )

    def get_by_token_hash(self, token_hash: str) -> Optional[PasswordReset]:
        """ get by token hash """
        return self.db.query(PasswordReset).filter(
            PasswordReset.token == token_hash,
            PasswordReset.deleted_at.is_(None)
        ).first()

    def create(self, email: str, token: str) -> PasswordReset:
        """ Create a new password reset """
        reset = PasswordReset(
            email=email,
            token=token
        )
        self.db.add(reset)
        self.db.commit()
        self.db.refresh(reset)
        return reset

    def soft_delete(self, reset: PasswordReset) -> None:
        """Soft delete user"""
        reset.deleted_at = datetime.now()
        self.db.add(reset)
        self.db.commit()

    def soft_delete_by_email(self, email: str) -> None:
        """Soft delete user by email"""
        resets = (
            self.db.query(PasswordReset)
            .filter(
                PasswordReset.email == email,
                PasswordReset.deleted_at.is_(None)
            )
            .all()
        )
        for r in resets:
            r.deleted_at = datetime.now()
            self.db.add(r)
        self.db.commit()
