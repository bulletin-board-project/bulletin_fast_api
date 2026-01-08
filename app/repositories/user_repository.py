""" User repository module. """
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import User


class UserRepository:
    """ User repository implementation. """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone"""
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_name(self, name: str) -> Optional[User]:
        """Get user by name"""
        return self.db.query(User).filter(User.name == name).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool = True
    ) -> List[User]:
        """Get all users with pagination and optional active filter"""
        query = self.db.query(User)
        query = query.filter(User.deleted_at.is_(None))
        if is_active:
            query = query.filter(User.lock_flg.is_(False))
        return query.offset(skip).limit(limit).all()

    def create(self, user: User) -> User:
        """Create new user"""
        self.db.add(user)
        return user

    def update(self, user: User) -> User:
        """Update user"""
        self.db.add(user)
        return user

    def exists_by_email_or_phone(self, email: str, phone: Optional[str]):
        """Check if user exists by email or phone"""
        query = self.db.query(User).filter(User.email == email)
        if phone:
            query = query.filter(User.phone == phone)
        return query.first() is not None
