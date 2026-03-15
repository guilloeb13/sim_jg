"""
Protocolo WebSocket para GAVILAN Multiplayer

Define los mensajes que se intercambian entre cliente y servidor.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class MessageType(str, Enum):
    """Tipos de mensajes WebSocket"""
    # Cliente → Servidor
    AUTHENTICATE = "authenticate"
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"
    EXECUTE_COMMAND = "execute_command"
    CHAT_MESSAGE = "chat_message"

    # Servidor → Cliente
    AUTHENTICATED = "authenticated"
    SESSION_JOINED = "session_joined"
    SESSION_LEFT = "session_left"
    STATE_UPDATE = "state_update"
    COMMAND_RESULT = "command_result"
    CHAT_BROADCAST = "chat_broadcast"
    EVENT_NOTIFICATION = "event_notification"
    ERROR = "error"

    # Bidireccional
    PING = "ping"
    PONG = "pong"


@dataclass
class WebSocketMessage:
    """Mensaje WebSocket base"""
    type: MessageType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serializa a diccionario"""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'WebSocketMessage':
        """Deserializa desde diccionario"""
        return cls(
            type=MessageType(data["type"]),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            data=data.get("data", {}),
        )


# Mensajes Cliente → Servidor

@dataclass
class AuthenticateMessage(WebSocketMessage):
    """Mensaje de autenticación"""
    def __init__(self, token: str):
        super().__init__(
            type=MessageType.AUTHENTICATE,
            data={"token": token}
        )


@dataclass
class JoinSessionMessage(WebSocketMessage):
    """Mensaje para unirse a sesión"""
    def __init__(self, session_id: UUID, role: str):
        super().__init__(
            type=MessageType.JOIN_SESSION,
            data={
                "session_id": str(session_id),
                "role": role,
            }
        )


@dataclass
class ExecuteCommandMessage(WebSocketMessage):
    """Mensaje para ejecutar comando"""
    def __init__(self, command: Dict):
        super().__init__(
            type=MessageType.EXECUTE_COMMAND,
            data={"command": command}
        )


@dataclass
class ChatMessage(WebSocketMessage):
    """Mensaje de chat"""
    def __init__(self, message: str, channel: str = "all"):
        super().__init__(
            type=MessageType.CHAT_MESSAGE,
            data={
                "message": message,
                "channel": channel,
            }
        )


# Mensajes Servidor → Cliente

@dataclass
class AuthenticatedMessage(WebSocketMessage):
    """Confirmación de autenticación"""
    def __init__(self, user_id: UUID, username: str, roles: list):
        super().__init__(
            type=MessageType.AUTHENTICATED,
            data={
                "user_id": str(user_id),
                "username": username,
                "roles": roles,
            }
        )


@dataclass
class StateUpdateMessage(WebSocketMessage):
    """Actualización de estado de simulación"""
    def __init__(self, state: Dict):
        super().__init__(
            type=MessageType.STATE_UPDATE,
            data=state
        )


@dataclass
class CommandResultMessage(WebSocketMessage):
    """Resultado de comando ejecutado"""
    def __init__(self, command_id: str, success: bool, message: str, data: Optional[Dict] = None):
        super().__init__(
            type=MessageType.COMMAND_RESULT,
            data={
                "command_id": command_id,
                "success": success,
                "message": message,
                "data": data or {},
            }
        )


@dataclass
class EventNotificationMessage(WebSocketMessage):
    """Notificación de evento de simulación"""
    def __init__(self, event_type: str, event_data: Dict):
        super().__init__(
            type=MessageType.EVENT_NOTIFICATION,
            data={
                "event_type": event_type,
                "event_data": event_data,
            }
        )


@dataclass
class ErrorMessage(WebSocketMessage):
    """Mensaje de error"""
    def __init__(self, error_code: str, error_message: str):
        super().__init__(
            type=MessageType.ERROR,
            data={
                "error_code": error_code,
                "error_message": error_message,
            }
        )
