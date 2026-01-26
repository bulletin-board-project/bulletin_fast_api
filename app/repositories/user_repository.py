""" User repository module. """
from datetime import UTC, datetime
from typing import List, Optional, Tuple, cast
from sqlalchemy import asc, desc, or_, update
from sqlalchemy.orm import Session, Query
from app.models import User


class UserRepository:
    """ User repository implementation. """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    def find_by_ids(self, user_ids: List[int]) -> List[User]:
        """Find User by Ids"""
        if not user_ids:
            return []

        return (
            self.db.query(User)
            .filter(User.id.in_(user_ids),
                    User.deleted_at.is_(None))
            .order_by(User.id.asc())
            .all()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone"""
        return self.db.query(User).filter(User.phone == phone, User.deleted_at.is_(None)).first()

    def get_by_name(self, name: str) -> Optional[User]:
        """Get user by name"""
        return self.db.query(User).filter(User.name == name, User.deleted_at.is_(None)).first()

    def save(self, user: User) -> User:
        """Create new user"""
        self.db.add(user)
        return user

    def update(self, user: User) -> User:
        """Update user"""
        self.save(user)
        return user

    def delete(self, user: User) -> None:
        """Soft delete user"""
        user.deleted_at = datetime.now(UTC)
        self.db.add(user)

    def exists_by_email_or_phone(self, email: str, phone: Optional[str]) -> User | None:
        """Check if user exists by email or phone"""
        query = self.db.query(User).filter(User.email == email)
        if phone:
            query = self.db.query(User).filter(
                or_(User.email == email, User.phone == phone))
        return query.first()

     # === Query Operations ===

    def find_users(
        self,
        offset: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        **filters
    ) -> Tuple[List[User], int]:
        """
        Find users with filters and pagination
        Returns: (list_of_users, total_count_with_same_filters)
        """
        # Build query with filters
        query = self.db.query(User)
        query = self._apply_filters(query, **filters)

        # Get total count (with same filters)
        total_count = cast(int, query.count())

        # Apply sorting
        sort_column = self._get_sort_column(sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        query = query.order_by(User.created_at.desc())

        # Apply pagination (offset/limit)
        users = cast(List[User], query.offset(offset).limit(limit).all())

        return users, total_count

    def get_user_count(self, is_active: bool = True, is_locked: bool = None) -> int:
        """ Get User Count with filters """
        query = self.db.query(User)

        if is_active:
            query = query.filter(User.deleted_at.is_(None))

        if is_locked is not None:
            query = query.filter(User.lock_flg == is_locked)

        return query.count()

    # === Batch Operations ===

    def bulk_delete_users(
        self, user_ids: List[int], deleted_at: datetime, current_user: User,
    ) -> int:
        """Delete multiple users"""
        update_data = {
            "deleted_at": deleted_at,
            "deleted_user_id": current_user.id
        }

        # Only delete users who are not already deleted
        result = self.db.execute(
            update(User)
            .where(
                User.id.in_(user_ids),
                User.deleted_at.is_(None)  # Not already deleted
            )
            .values(**update_data)
        )

        return result.rowcount

    def bulk_update_lock_status(
        self,
        user_ids: List[int],
        lock_status: bool,
        last_lock_at: Optional[datetime] = None,
        lock_count: Optional[int] = None
    ) -> int:
        """
        updates lock-related fields only
        Returns: Number of rows updated
        """

        if not user_ids:
            return 0

        update_data = {
            "lock_flg": lock_status,
        }

        # Optional fields - only if provided
        if last_lock_at is not None:
            update_data["last_lock_at"] = last_lock_at

        if lock_count is not None:
            update_data["lock_count"] = lock_count

        # Execute update
        result = self.db.execute(
            update(User)
            .where(User.id.in_(user_ids))
            .values(**update_data)
        )

        return result.rowcount

    def bulk_update_general(
        self,
        user_ids: List[int],
        **update_fields
    ) -> int:
        """
        Generic bulk update for any fields
        """
        result = self.db.execute(
            update(User)
            .where(User.id.in_(user_ids))
            .values(**update_fields)
        )
        return result.rowcount

    # === Helper ====

    def _apply_filters(self, query: Query, **filters) -> Query:
        """
        Apply WHERE clauses to query
        Returns: Modified query object
        """
        # Name filter (partial match)
        if filters.get('name'):
            query = query.filter(User.name.ilike(f"%{filters['name']}%"))

        # Email filter (partial match)
        if filters.get('email'):
            query = query.filter(User.email.ilike(f"%{filters['email']}%"))

        # Role filter
        if filters.get('role') is not None:
            query = query.filter(User.role == filters['role'])

        # Date range filter
        if filters.get('start_date'):
            query = query.filter(User.created_at >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(User.created_at <= filters['end_date'])

        # Active users only (not deleted)
        if filters.get('is_active', True):
            query = query.filter(User.deleted_at.is_(None))

        # Lock status filter
        if filters.get('is_locked') is not None:
            query = query.filter(User.lock_flg == filters['is_locked'])

        return query

    def _get_sort_column(self, sort_by: str):
        """Get SQLAlchemy column from sort_by string"""
        sort_mapping = {
            'id': User.id,
            'name': User.name,
            'email': User.email,
            'role': User.role,
            'lock_flg': User.lock_flg,
            'created_at': User.created_at,
            'updated_at': User.updated_at,
            'last_login_at': User.last_login_at,
        }
        return sort_mapping.get(sort_by, User.created_at)
