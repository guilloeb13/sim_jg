"""
Módulo de autenticación y autorización para GAVILAN Multiplayer
"""

from .models import (
    User,
    Session,
    Role,
    Permission,
    ROLE_PERMISSIONS,
    UserRepository,
    SessionRepository,
)
from .service import (
    AuthService,
    AuthenticationError,
    AuthorizationError,
    get_auth_service,
)

__all__ = [
    "User",
    "Session",
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "UserRepository",
    "SessionRepository",
    "AuthService",
    "AuthenticationError",
    "AuthorizationError",
    "get_auth_service",
]
