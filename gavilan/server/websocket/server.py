"""
Servidor WebSocket para GAVILAN Multiplayer

Maneja conexiones en tiempo real con los clientes.
"""

import asyncio
import json
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from gavilan.multiplayer.auth import get_auth_service
from gavilan.multiplayer.session import get_session_manager
from gavilan.multiplayer.command_levels import Command, CommandLevel
from gavilan.core.entities import Side

from .connection_manager import get_connection_manager
from .protocol import (
    WebSocketMessage,
    MessageType,
    AuthenticatedMessage,
    CommandResultMessage,
    ErrorMessage,
    StateUpdateMessage,
)


class WebSocketServer:
    """
    Servidor WebSocket para comunicación en tiempo real

    Maneja:
    - Autenticación de clientes
    - Ejecución de comandos
    - Broadcast de actualizaciones de estado
    - Chat entre jugadores
    """

    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.session_manager = get_session_manager()
        self.auth_service = get_auth_service()

    async def handle_client(self, websocket: WebSocket):
        """
        Maneja conexión de un cliente

        Args:
            websocket: WebSocket del cliente
        """
        user = None
        user_session_id = None

        try:
            # 1. Esperar autenticación
            user = await self._authenticate_client(websocket)
            if not user:
                await websocket.close(code=4001, reason="Authentication failed")
                return

            # 2. Conectar usuario
            await self.connection_manager.connect(websocket, user)

            # 3. Enviar confirmación de autenticación
            auth_msg = AuthenticatedMessage(
                user.id,
                user.username,
                [r.value for r in user.roles]
            )
            await self.connection_manager.send_to_user(user.id, auth_msg)

            # 4. Loop de mensajes
            while True:
                # Recibir mensaje
                data = await websocket.receive_text()
                message = WebSocketMessage.from_dict(json.loads(data))

                # Procesar mensaje
                if message.type == MessageType.JOIN_SESSION:
                    user_session_id = await self._handle_join_session(user, message)

                elif message.type == MessageType.LEAVE_SESSION:
                    await self._handle_leave_session(user, user_session_id)
                    user_session_id = None

                elif message.type == MessageType.EXECUTE_COMMAND:
                    await self._handle_execute_command(user, user_session_id, message)

                elif message.type == MessageType.CHAT_MESSAGE:
                    await self._handle_chat_message(user, user_session_id, message)

                elif message.type == MessageType.PING:
                    await self._handle_ping(user)

        except WebSocketDisconnect:
            print(f"Client disconnected: {user.username if user else 'unknown'}")

        except Exception as e:
            print(f"Error handling client: {e}")

        finally:
            # Cleanup
            if user:
                if user_session_id:
                    await self.connection_manager.leave_session(user.id, user_session_id)
                await self.connection_manager.disconnect(user.id)

    async def _authenticate_client(self, websocket: WebSocket) -> Optional[object]:
        """
        Autentica un cliente

        Returns:
            User si autenticación exitosa, None si falla
        """
        try:
            # Esperar mensaje de autenticación (timeout 10s)
            data = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=10.0
            )

            message = WebSocketMessage.from_dict(json.loads(data))

            if message.type != MessageType.AUTHENTICATE:
                await websocket.send_json(
                    ErrorMessage("AUTH_REQUIRED", "Authentication required").to_dict()
                )
                return None

            # Verificar token
            token = message.data.get("token")
            user = self.auth_service.verify_token(token)

            if not user:
                await websocket.send_json(
                    ErrorMessage("INVALID_TOKEN", "Invalid or expired token").to_dict()
                )
                return None

            return user

        except asyncio.TimeoutError:
            await websocket.send_json(
                ErrorMessage("AUTH_TIMEOUT", "Authentication timeout").to_dict()
            )
            return None

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    async def _handle_join_session(self, user, message: WebSocketMessage) -> Optional[UUID]:
        """Maneja JOIN_SESSION"""
        try:
            session_id = UUID(message.data["session_id"])
            role = message.data["role"]

            # Obtener sesión
            session = self.session_manager.get_session(session_id)
            if not session:
                await self.connection_manager.send_to_user(
                    user.id,
                    ErrorMessage("SESSION_NOT_FOUND", "Session not found")
                )
                return None

            # Unirse a sesión
            success = session.join_player(user, role)
            if not success:
                await self.connection_manager.send_to_user(
                    user.id,
                    ErrorMessage("JOIN_FAILED", "Failed to join session (slot unavailable)")
                )
                return None

            # Registrar en connection manager
            await self.connection_manager.join_session(user.id, session_id)

            # Enviar confirmación
            await self.connection_manager.send_to_user(
                user.id,
                WebSocketMessage(
                    type=MessageType.SESSION_JOINED,
                    data={
                        "session_id": str(session_id),
                        "role": role,
                    }
                )
            )

            # Enviar estado inicial
            state = session.get_state_for_user(user)
            await self.connection_manager.send_to_user(
                user.id,
                StateUpdateMessage(state)
            )

            return session_id

        except Exception as e:
            print(f"Error joining session: {e}")
            await self.connection_manager.send_to_user(
                user.id,
                ErrorMessage("JOIN_ERROR", str(e))
            )
            return None

    async def _handle_leave_session(self, user, session_id: Optional[UUID]):
        """Maneja LEAVE_SESSION"""
        if not session_id:
            return

        session = self.session_manager.get_session(session_id)
        if session:
            session.leave_player(user)

        await self.connection_manager.leave_session(user.id, session_id)

        await self.connection_manager.send_to_user(
            user.id,
            WebSocketMessage(
                type=MessageType.SESSION_LEFT,
                data={"session_id": str(session_id)}
            )
        )

    async def _handle_execute_command(
        self,
        user,
        session_id: Optional[UUID],
        message: WebSocketMessage
    ):
        """Maneja EXECUTE_COMMAND"""
        if not session_id:
            await self.connection_manager.send_to_user(
                user.id,
                ErrorMessage("NO_SESSION", "Not in a session")
            )
            return

        try:
            # Obtener sesión
            session = self.session_manager.get_session(session_id)
            if not session:
                await self.connection_manager.send_to_user(
                    user.id,
                    ErrorMessage("SESSION_NOT_FOUND", "Session not found")
                )
                return

            # Parsear comando
            cmd_data = message.data["command"]
            command = Command(
                level=CommandLevel(cmd_data["level"]),
                command_type=cmd_data["command_type"],
                user_id=user.id,
                side=Side(cmd_data.get("side", "blue")),
                data=cmd_data.get("data", {}),
            )

            # Ejecutar comando
            result = session.execute_command(command, user)

            # Enviar resultado
            await self.connection_manager.send_to_user(
                user.id,
                CommandResultMessage(
                    str(command.id),
                    result.success,
                    result.message,
                    result.data
                )
            )

            # Si comando exitoso, broadcast estado actualizado
            if result.success:
                await self._broadcast_state_update(session_id)

        except Exception as e:
            print(f"Error executing command: {e}")
            await self.connection_manager.send_to_user(
                user.id,
                ErrorMessage("COMMAND_ERROR", str(e))
            )

    async def _handle_chat_message(
        self,
        user,
        session_id: Optional[UUID],
        message: WebSocketMessage
    ):
        """Maneja CHAT_MESSAGE"""
        if not session_id:
            return

        chat_msg = WebSocketMessage(
            type=MessageType.CHAT_BROADCAST,
            data={
                "username": user.username,
                "message": message.data["message"],
                "channel": message.data.get("channel", "all"),
            }
        )

        await self.connection_manager.send_to_session(session_id, chat_msg)

    async def _handle_ping(self, user):
        """Maneja PING"""
        await self.connection_manager.send_to_user(
            user.id,
            WebSocketMessage(type=MessageType.PONG)
        )

    async def _broadcast_state_update(self, session_id: UUID):
        """Broadcast actualización de estado a todos en la sesión"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return

        # Obtener todos los usuarios de la sesión
        if session_id not in self.connection_manager.session_users:
            return

        for user_id in self.connection_manager.session_users[session_id]:
            user = self.connection_manager.get_user(user_id)
            if user:
                state = session.get_state_for_user(user)
                await self.connection_manager.send_to_user(
                    user_id,
                    StateUpdateMessage(state)
                )

    async def tick_all_sessions(self):
        """
        Loop que tickea todas las sesiones activas

        Debe ejecutarse en background task.
        """
        while True:
            try:
                # Tickear sesiones
                self.session_manager.tick_all()

                # Broadcast estado a cada sesión
                for session in self.session_manager.get_active_sessions():
                    await self._broadcast_state_update(session.id)

                # Esperar 1 segundo (1 Hz)
                await asyncio.sleep(1.0)

            except Exception as e:
                print(f"Error in tick loop: {e}")
                await asyncio.sleep(1.0)


# Singleton global
_websocket_server: Optional[WebSocketServer] = None


def get_websocket_server() -> WebSocketServer:
    """Obtiene instancia singleton del WebSocket server"""
    global _websocket_server
    if _websocket_server is None:
        _websocket_server = WebSocketServer()
    return _websocket_server
