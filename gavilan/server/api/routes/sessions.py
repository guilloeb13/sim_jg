"""
API REST - Sesiones de Juego
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from gavilan.multiplayer.auth import User, Role, Permission
from gavilan.multiplayer.session import get_session_manager, GameType, SessionStatus
from gavilan.core.config import GavilanConfig, SimulationMode, DifficultyLevel
from .auth import get_current_user


router = APIRouter()


# Models

class CreateSessionRequest(BaseModel):
    name: str
    game_type: str  # "external_war", "internal_conflict", "disaster_management"


class SessionResponse(BaseModel):
    id: str
    name: str
    game_type: str
    status: str
    director: Optional[str]
    players: int
    slots_available: int


class StartSessionRequest(BaseModel):
    mode: str = "wargame"
    difficulty: str = "medium"
    max_duration_seconds: int = 3600


# Endpoints

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva sesión de juego"""
    # Verificar permisos (solo GAME_MASTER o ADMIN)
    if not (current_user.has_role(Role.GAME_MASTER) or current_user.has_role(Role.ADMIN)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Game Master or Admin can create sessions"
        )

    session_manager = get_session_manager()

    session = session_manager.create_session(
        name=request.name,
        game_type=GameType(request.game_type),
        director=current_user,
    )

    return SessionResponse(**session.get_status_dict())


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Lista sesiones disponibles"""
    session_manager = get_session_manager()

    filter_status = SessionStatus(status_filter) if status_filter else None
    sessions = session_manager.list_sessions(status=filter_status)

    return [SessionResponse(**s.get_status_dict()) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Obtiene información de una sesión"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return SessionResponse(**session.get_status_dict())


@router.post("/{session_id}/start")
async def start_session(
    session_id: UUID,
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Inicia una sesión"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verificar que sea el director
    if session.director.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only session director can start session"
        )

    # Crear configuración
    config = GavilanConfig(
        mode=SimulationMode(request.mode.upper()),
        difficulty=DifficultyLevel(request.difficulty.upper()),
        max_duration_seconds=request.max_duration_seconds,
    )

    try:
        session.start(config)
        return {"message": "Session started", "status": session.status.value}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{session_id}/pause")
async def pause_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Pausa una sesión"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session or session.director.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    session.pause()
    return {"message": "Session paused"}


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Reanuda una sesión"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session or session.director.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    session.resume()
    return {"message": "Session resumed"}


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Elimina una sesión"""
    if not current_user.has_permission(Permission.MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    session_manager = get_session_manager()
    success = session_manager.delete_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session deleted"}
