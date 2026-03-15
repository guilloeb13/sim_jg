"""
Session Manager para GAVILAN Multiplayer

Gestiona múltiples sesiones de juego simultáneas.
"""

from typing import Dict, List, Optional
from uuid import UUID

from gavilan.multiplayer.auth import User
from .game_session import GameSession, GameType, SessionStatus


class SessionManager:
    """
    Gestor de sesiones de juego

    Responsabilidades:
    - Crear/eliminar sesiones
    - Asignar jugadores a sesiones
    - Tickear todas las sesiones activas
    """

    def __init__(self):
        self._sessions: Dict[UUID, GameSession] = {}

    def create_session(
        self,
        name: str,
        game_type: GameType,
        director: User,
    ) -> GameSession:
        """
        Crea una nueva sesión de juego

        Args:
            name: Nombre de la sesión
            game_type: Tipo de juego
            director: Director/Game Master

        Returns:
            Nueva sesión creada
        """
        session = GameSession(
            name=name,
            game_type=game_type,
        )
        session.assign_director(director)

        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[GameSession]:
        """Obtiene sesión por ID"""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: UUID) -> bool:
        """
        Elimina una sesión

        Returns:
            True si se eliminó
        """
        if session_id in self._sessions:
            # Detener si está corriendo
            session = self._sessions[session_id]
            if session.status == SessionStatus.RUNNING:
                session.stop()

            del self._sessions[session_id]
            return True
        return False

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
    ) -> List[GameSession]:
        """
        Lista sesiones

        Args:
            status: Filtrar por estado (opcional)

        Returns:
            Lista de sesiones
        """
        sessions = list(self._sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        return sessions

    def get_active_sessions(self) -> List[GameSession]:
        """Retorna sesiones activas (running o paused)"""
        return [
            s for s in self._sessions.values()
            if s.status in [SessionStatus.RUNNING, SessionStatus.PAUSED]
        ]

    def tick_all(self):
        """Tickea todas las sesiones activas"""
        for session in self.get_active_sessions():
            try:
                session.tick()
            except Exception as e:
                # Log error pero continuar con otras sesiones
                print(f"Error ticking session {session.id}: {e}")

    def get_user_sessions(self, user: User) -> List[GameSession]:
        """
        Obtiene sesiones donde el usuario participa

        Args:
            user: Usuario

        Returns:
            Lista de sesiones donde participa
        """
        user_sessions = []

        for session in self._sessions.values():
            # Director
            if session.director and session.director.id == user.id:
                user_sessions.append(session)
                continue

            # Jugador
            for slot in session.player_slots:
                if slot.user and slot.user.id == user.id:
                    user_sessions.append(session)
                    break

        return user_sessions

    def cleanup_ended_sessions(self, keep_hours: int = 24):
        """
        Limpia sesiones terminadas después de X horas

        Args:
            keep_hours: Horas a mantener sesiones terminadas
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(hours=keep_hours)
        to_delete = []

        for session_id, session in self._sessions.items():
            if session.status == SessionStatus.ENDED:
                if session.ended_at and session.ended_at < cutoff:
                    to_delete.append(session_id)

        for session_id in to_delete:
            del self._sessions[session_id]

    def get_stats(self) -> Dict:
        """Retorna estadísticas del sistema"""
        total = len(self._sessions)
        by_status = {}

        for status in SessionStatus:
            count = sum(1 for s in self._sessions.values() if s.status == status)
            by_status[status.value] = count

        total_players = sum(
            s.get_player_count()
            for s in self._sessions.values()
            if s.status in [SessionStatus.RUNNING, SessionStatus.PAUSED]
        )

        return {
            "total_sessions": total,
            "by_status": by_status,
            "active_players": total_players,
        }


# Singleton global
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Obtiene instancia singleton del session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
