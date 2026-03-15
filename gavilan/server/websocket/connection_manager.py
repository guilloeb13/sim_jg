"""
Connection Manager para WebSocket

Gestiona las conexiones activas de jugadores.
"""

import asyncio
import json
from typing import Dict, List, Optional, Set
from uuid import UUID
from fastapi import WebSocket

from gavilan.multiplayer.auth import User
from .protocol import WebSocketMessage, StateUpdateMessage, EventNotificationMessage


class ConnectionManager:
    """
    Gestor de conexiones WebSocket

    Mantiene track de todas las conexiones activas y permite
    enviar mensajes a usuarios específicos o broadcast.
    """

    def __init__(self):
        # Conexiones activas: user_id -> WebSocket
        self.active_connections: Dict[UUID, WebSocket] = {}

        # Mapeo de sesiones: session_id -> set(user_ids)
        self.session_users: Dict[UUID, Set[UUID]] = {}

        # Mapeo de usuarios: user_id -> User
        self.users: Dict[UUID, User] = {}

        # Lock para operaciones concurrentes
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user: User):
        """
        Conecta un usuario

        Args:
            websocket: WebSocket del cliente
            user: Usuario autenticado
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections[user.id] = websocket
            self.users[user.id] = user

    async def disconnect(self, user_id: UUID):
        """
        Desconecta un usuario

        Args:
            user_id: ID del usuario
        """
        async with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]

            if user_id in self.users:
                del self.users[user_id]

            # Remover de sesiones
            for session_id, users in list(self.session_users.items()):
                if user_id in users:
                    users.remove(user_id)
                    if not users:
                        del self.session_users[session_id]

    async def join_session(self, user_id: UUID, session_id: UUID):
        """
        Usuario se une a una sesión

        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
        """
        async with self._lock:
            if session_id not in self.session_users:
                self.session_users[session_id] = set()

            self.session_users[session_id].add(user_id)

    async def leave_session(self, user_id: UUID, session_id: UUID):
        """
        Usuario abandona una sesión

        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
        """
        async with self._lock:
            if session_id in self.session_users:
                self.session_users[session_id].discard(user_id)

                if not self.session_users[session_id]:
                    del self.session_users[session_id]

    async def send_to_user(self, user_id: UUID, message: WebSocketMessage):
        """
        Envía mensaje a un usuario específico

        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message.to_dict())
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                await self.disconnect(user_id)

    async def send_to_session(
        self,
        session_id: UUID,
        message: WebSocketMessage,
        exclude_user: Optional[UUID] = None
    ):
        """
        Envía mensaje a todos los usuarios de una sesión

        Args:
            session_id: ID de la sesión
            message: Mensaje a enviar
            exclude_user: Usuario a excluir (opcional)
        """
        if session_id not in self.session_users:
            return

        users = self.session_users[session_id].copy()

        if exclude_user:
            users.discard(exclude_user)

        # Enviar en paralelo
        tasks = [
            self.send_to_user(user_id, message)
            for user_id in users
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast(self, message: WebSocketMessage):
        """
        Broadcast a todos los usuarios conectados

        Args:
            message: Mensaje a enviar
        """
        tasks = [
            self.send_to_user(user_id, message)
            for user_id in list(self.active_connections.keys())
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_state_update(
        self,
        session_id: UUID,
        state: Dict
    ):
        """
        Broadcast actualización de estado a sesión

        Args:
            session_id: ID de la sesión
            state: Estado de simulación
        """
        message = StateUpdateMessage(state)
        await self.send_to_session(session_id, message)

    async def broadcast_event(
        self,
        session_id: UUID,
        event_type: str,
        event_data: Dict
    ):
        """
        Broadcast evento a sesión

        Args:
            session_id: ID de la sesión
            event_type: Tipo de evento
            event_data: Datos del evento
        """
        message = EventNotificationMessage(event_type, event_data)
        await self.send_to_session(session_id, message)

    def get_session_user_count(self, session_id: UUID) -> int:
        """Retorna número de usuarios en sesión"""
        return len(self.session_users.get(session_id, set()))

    def get_active_user_count(self) -> int:
        """Retorna número total de usuarios conectados"""
        return len(self.active_connections)

    def get_user(self, user_id: UUID) -> Optional[User]:
        """Obtiene usuario por ID"""
        return self.users.get(user_id)

    def is_user_connected(self, user_id: UUID) -> bool:
        """Verifica si usuario está conectado"""
        return user_id in self.active_connections


# Singleton global
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Obtiene instancia singleton del connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
