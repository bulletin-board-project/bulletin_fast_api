"""" Dependency injection definitions """
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.auth_controller import AuthController
from app.controllers.post_controller import PostController
from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.post_service import PostService
from app.services.user_service import UserService


DatabaseDep = Annotated[Session, Depends(get_db)]


## Repository dependencies ##
def get_user_repository(db: DatabaseDep) -> UserRepository:
    """ Get UserRepository dependency """
    return UserRepository(db)


def get_post_repository(db: DatabaseDep) -> PostRepository:
    """ Get PostRepository dependency """
    return PostRepository(db)

## Service dependencies ##


def get_auth_service(
    db: DatabaseDep,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthService:
    """ Get AuthService dependency """
    return AuthService(user_repo, db)


def get_user_service(
        db: DatabaseDep,
        user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    """ Get UserService dependency"""
    return UserService(user_repo, db)


def get_post_service(
        db: DatabaseDep,
        user_repo: Annotated[PostRepository, Depends(get_post_repository)]
) -> PostService:
    """ Get PostService dependency"""
    return PostService(user_repo, db)


## Controller dependencies ##
def get_auth_controller(
    service: Annotated[AuthService, Depends(get_auth_service)]
):
    """ Get AuthController dependency """
    return AuthController(service)


def get_user_controller(
        service: Annotated[UserService, Depends(get_user_service)]
):
    """Get User Controller dependency"""
    return UserController(service)


def get_post_controller(
        service: Annotated[PostService, Depends(get_post_service)]
):
    """Get Post Controller dependency"""
    return PostController(service)


## Type aliases for dependency injection ##
AuthControllerDep = Annotated[AuthController, Depends(get_auth_controller)]
UserControllerDep = Annotated[UserController, Depends(get_user_controller)]
PostControllerDep = Annotated[PostController, Depends(get_post_controller)]
