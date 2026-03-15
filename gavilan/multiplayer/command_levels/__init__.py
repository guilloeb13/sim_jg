"""
Niveles de comando para GAVILAN Multiplayer
"""

from .base import Command, CommandInterface, CommandLevel, CommandResult
from .director import DirectorLevel, DirectorCommands
from .strategic import StrategicLevel, StrategicCommands
from .operational import OperationalLevel, OperationalCommands
from .tactical import TacticalLevel, TacticalCommands

__all__ = [
    "Command",
    "CommandInterface",
    "CommandLevel",
    "CommandResult",
    "DirectorLevel",
    "DirectorCommands",
    "StrategicLevel",
    "StrategicCommands",
    "OperationalLevel",
    "OperationalCommands",
    "TacticalLevel",
    "TacticalCommands",
]
