"""
Módulo Espacial
===============

Gestiona:
- Clima espacial (Kp, viento solar, eyecciones coronales)
- Impacto en GPS/INS
- Fallas en comunicaciones satelitales
- Alertas para A2 y A5
"""

from gavilan.modules.space.space_weather import SpaceWeatherModule, SpaceWeatherData
from gavilan.modules.space.effects import SpaceWeatherEffects

__all__ = [
    "SpaceWeatherModule",
    "SpaceWeatherData",
    "SpaceWeatherEffects",
]
