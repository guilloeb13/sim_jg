"""
Efectos del clima espacial en operaciones
"""

from dataclasses import dataclass


@dataclass
class OperationalEffect:
    """Efecto operacional del clima espacial"""
    system: str
    effect_type: str
    magnitude: float
    description: str
    mitigation: str


# Re-exportar SpaceWeatherEffects desde el módulo principal
from gavilan.modules.space.space_weather import SpaceWeatherEffects

__all__ = ["SpaceWeatherEffects", "OperationalEffect"]
