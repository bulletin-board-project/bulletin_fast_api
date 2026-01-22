"""Post Repository Module"""


from datetime import UTC, datetime
from typing import List, Optional, Tuple, cast
from sqlalchemy import asc, desc, select, update
from sqlalchemy.orm import Session, Query
from app.models.post import Post
from app.models.user import User


class PostRepository:
    """ Psot repository implementation. """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by Id"""
        return self.db.query(Post).filter(Post.id == post_id, Post.deleted_at.is_(None)).first()

    def find_by_ids(self, post_ids: List[int]) -> List[Post]:
        """Find Post by Ids"""
        if not post_ids:
            return []

        return (
            self.db.query(Post)
            .filter(Post.id.in_(post_ids),
                    Post.deleted_at.is_(None))
            .order_by(Post.id.asc())
            .all()
        )

    def get_by_title(self, title: str) -> Optional[Post]:
        """Get user by title"""
        return self.db.query(Post).filter(Post.title == title, Post.deleted_at.is_(None)).first()

    def save(self, post: Post) -> Post:
        """Create new user"""
        self.db.add(post)
        return post

    def delete(self, post: Post) -> None:
        """Soft delete post"""
        post.deleted_at = datetime.now(UTC)
        self.db.add(post)

    def get_all_titles(self):
        """ Ge All Title """
        stmt = select(Post.title).filter(Post.deleted_at.is_(None))
        titles = self.db.execute(stmt).scalars().all()
        return titles

    # === Query Operations ===

    def find_posts(
        self,
        offset: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        **filters
    ) -> Tuple[List[Post], int]:
        """
        Find posts with filters and pagination
        Returns: (list_of_users, total_count_with_same_filters)
        """
        # Build query with filters
        query = self.db.query(Post)
        query = self._apply_filters(query, **filters)

        # Get total count (with same filters)
        total_count = cast(int, query.count())

        # Apply sorting
        sort_column = self._get_sort_column(sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        query = query.order_by(Post.created_at.desc())

        # Apply pagination (offset/limit)
        posts = cast(List[Post], query.offset(offset).limit(limit).all())

        return posts, total_count

    def get_psot_count(self, is_active: bool = True, is_locked: bool = None) -> int:
        """ Get User Count with filters """
        query = self.db.query(Post)

        if is_active:
            query = query.filter(Post.deleted_at.is_(None))

        if is_locked is not None:
            query = query.filter(Post.status == is_locked)

        return query.count()

      # === Batch Operations ===

    def bulk_delete_posts(self, post_ids: List[int], deleted_at: datetime, current_user: User) -> int:
        """Delete multiple users"""
        update_data = {
            "deleted_at": deleted_at,
            "deleted_user_id": current_user.id
        }

        # Only delete posts who are not already deleted
        result = self.db.execute(
            update(Post)
            .where(
                Post.id.in_(post_ids),
                Post.deleted_at.is_(None)  # Not already deleted
            )
            .values(**update_data)
        )

        return result.rowcount

    def bulk_update_general(
        self,
        post_ids: List[int],
        **update_fields
    ) -> int:
        """
        Generic bulk update for any fields
        """
        result = self.db.execute(
            update(Post)
            .where(Post.id.in_(post_ids))
            .values(**update_fields)
        )
        return result.rowcount

     # === Helper ====

    def _apply_filters(self, query: Query, **filters) -> Query:
        """
        Apply WHERE clauses to query
        Returns: Modified query object
        """
        # Title filter (partial match)
        if filters.get('title'):
            query = query.filter(Post.title.ilike(
                f"%{filters['title']}%"))

        # Description filter (partial match)
        if filters.get('description'):
            query = query.filter(Post.description.ilike(
                f"%{filters['description']}%"))

        # Status filter
        if filters.get('status') is not None:
            query = query.filter(Post.status == filters['status'])

        # Date range filter
        if filters.get('start_date'):
            query = query.filter(Post.created_at >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(Post.created_at <= filters['end_date'])

        # Active Post only (not deleted)
        if filters.get('is_active', True):
            query = query.filter(Post.deleted_at.is_(None))

        return query

    def _get_sort_column(self, sort_by: str):
        """Get SQLAlchemy column from sort_by string"""
        sort_mapping = {
            'id': Post.id,
            'title': Post.title,
            'description': Post.description,
            'status': Post.status,
            'created_at': Post.created_at,
            'updated_at': Post.updated_at,
        }
        return sort_mapping.get(sort_by, Post.created_at)
