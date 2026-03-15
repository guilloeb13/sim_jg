"""
API REST - Gestión de Usuarios (Admin)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List
from uuid import UUID

from gavilan.multiplayer.auth import (
    User, Role, Permission,
    get_auth_service
)
from .auth import get_current_user


router = APIRouter()


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str]
    is_active: bool


class AddRoleRequest(BaseModel):
    role: str


# Dependency para verificar admin
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.has_permission(Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(admin: User = Depends(require_admin)):
    """Lista todos los usuarios (admin only)"""
    auth_service = get_auth_service()
    users = auth_service.user_repo.list_all()

    return [
        UserResponse(
            user_id=str(u.id),
            username=u.username,
            email=u.email,
            roles=[r.value for r in u.roles],
            is_active=u.is_active
        )
        for u in users
    ]


@router.post("/{user_id}/roles", response_model=UserResponse)
async def add_role(
    user_id: UUID,
    request: AddRoleRequest,
    admin: User = Depends(require_admin)
):
    """Agrega rol a usuario"""
    auth_service = get_auth_service()
    user = auth_service.user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    role = Role(request.role)
    user.add_role(role)
    auth_service.user_repo.update(user)

    return UserResponse(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        roles=[r.value for r in user.roles],
        is_active=user.is_active
    )


@router.delete("/{user_id}/roles/{role}")
async def remove_role(
    user_id: UUID,
    role: str,
    admin: User = Depends(require_admin)
):
    """Remueve rol de usuario"""
    auth_service = get_auth_service()
    user = auth_service.user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    user.remove_role(Role(role))
    auth_service.user_repo.update(user)

    return {"message": f"Role {role} removed"}
