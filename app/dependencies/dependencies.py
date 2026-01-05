"""" Dependency injection definitions """
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.auth_controller import AuthController
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


DatabaseDep = Annotated[Session, Depends(get_db)]


# Repository dependencies
def get_user_repository(db: DatabaseDep) -> UserRepository:
    """ Get UserRepository dependency """
    return UserRepository(db)


# Service dependencies
def get_auth_service(
    db: DatabaseDep,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthService:
    """ Get AuthService dependency """
    return AuthService(user_repo, db)


# Controller dependencies
def get_auth_controller(
    service: Annotated[AuthService, Depends(get_auth_service)]
):
    """ Get AuthController dependency """
    return AuthController(service)


# Type aliases for dependency injection
AuthControllerDep = Annotated[AuthController, Depends(get_auth_controller)]
