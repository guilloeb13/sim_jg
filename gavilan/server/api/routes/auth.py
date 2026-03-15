"""
API REST - Autenticación

Endpoints para login, logout, registro.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

from gavilan.multiplayer.auth import (
    get_auth_service,
    AuthenticationError,
    User,
    Role,
)


router = APIRouter()
security = HTTPBearer()


# Request/Response Models

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]
    token: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]
    permissions: list[str]


# Dependency para obtener usuario autenticado
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency que valida token y retorna usuario"""
    auth_service = get_auth_service()
    token = credentials.credentials

    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


# Endpoints

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Registra un nuevo usuario

    Crea un usuario sin roles asignados (admin debe asignarlos después).
    """
    auth_service = get_auth_service()

    try:
        user = auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
        )

        return UserResponse(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            roles=[r.value for r in user.roles],
            permissions=[p.value for p in user.get_all_permissions()],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Autentica usuario y retorna JWT token

    El token debe usarse en:
    - Header Authorization: Bearer <token> para API REST
    - Mensaje AUTHENTICATE para WebSocket
    """
    auth_service = get_auth_service()

    try:
        user, token = auth_service.login(
            username=request.username,
            password=request.password,
        )

        return LoginResponse(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            roles=[r.value for r in user.roles],
            token=token,
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Cierra sesión (invalida token)

    Nota: Requiere implementación de blacklist de tokens en producción.
    """
    # TODO: Implementar blacklist de tokens
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado
    """
    return UserResponse(
        user_id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        roles=[r.value for r in current_user.roles],
        permissions=[p.value for p in current_user.get_all_permissions()],
    )


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresca el token JWT

    Genera un nuevo token con tiempo de expiración extendido.
    """
    auth_service = get_auth_service()
    token = auth_service._generate_jwt_token(current_user)

    return {
        "token": token,
        "expires_in": auth_service.token_expiry_hours * 3600,
    }
