"""
Niveles de comando base para GAVILAN Multiplayer

Jerarquía:
- Director (Game Master): Control total
- Estratégico: Objetivos, ROE, recursos
- Operacional: ATO, planificación de misiones
- Táctico: Control directo de unidades
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from gavilan.core.entities import Side
from gavilan.multiplayer.auth import Permission, User


class CommandLevel(str, Enum):
    """Niveles de comando"""
    DIRECTOR = "director"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    TACTICAL = "tactical"


@dataclass
class Command:
    """
    Comando emitido por un jugador

    Representa una acción tomada por un jugador en cualquier nivel.
    """
    id: UUID = field(default_factory=uuid4)
    level: CommandLevel = CommandLevel.TACTICAL
    command_type: str = ""  # "launch_mission", "set_roe", "engage_target", etc.
    user_id: UUID = field(default_factory=uuid4)
    side: Side = Side.BLUE
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    # Resultado
    executed: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class CommandResult:
    """Resultado de ejecutar un comando"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class CommandInterface(ABC):
    """
    Interfaz base para niveles de comando

    Cada nivel implementa esta interfaz con comandos específicos.
    """

    def __init__(self, side: Side):
        self.side = side
        self.command_history: List[Command] = []

    @abstractmethod
    def get_available_commands(self) -> List[str]:
        """Retorna lista de comandos disponibles en este nivel"""
        pass

    @abstractmethod
    def execute_command(self, command: Command) -> CommandResult:
        """Ejecuta un comando"""
        pass

    def validate_command(self, command: Command, user: User) -> bool:
        """
        Valida que comando sea válido para este nivel y usuario

        Args:
            command: Comando a validar
            user: Usuario que emite el comando

        Returns:
            True si válido
        """
        # Verificar que comando sea del nivel correcto
        if command.level != self.get_level():
            return False

        # Verificar que usuario tenga permiso
        required_permission = self._get_required_permission(command.command_type)
        if required_permission and not user.has_permission(required_permission):
            return False

        # Verificar que sea del bando correcto
        if command.side != self.side:
            return False

        return True

    @abstractmethod
    def get_level(self) -> CommandLevel:
        """Retorna el nivel de comando"""
        pass

    @abstractmethod
    def _get_required_permission(self, command_type: str) -> Optional[Permission]:
        """Retorna permiso requerido para un tipo de comando"""
        pass

    def log_command(self, command: Command):
        """Registra comando en historial"""
        self.command_history.append(command)

    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual de este nivel"""
        return {
            "level": self.get_level().value,
            "side": self.side.value,
            "commands_executed": len(self.command_history),
        }
