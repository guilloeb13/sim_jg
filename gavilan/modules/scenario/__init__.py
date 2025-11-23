"""
Módulo de Configuración de Escenario
=====================================

Gestiona:
- Definición del área geográfica
- Orden de batalla propio y enemigo
- Cinemática inicial de entidades
- Clima meteorológico y espacial
- Reglas de enfrentamiento
"""

from gavilan.modules.scenario.manager import ScenarioManager
from gavilan.modules.scenario.orbat import OrderOfBattle, ForceComposition
from gavilan.modules.scenario.weather import WeatherSystem

__all__ = [
    "ScenarioManager",
    "OrderOfBattle",
    "ForceComposition",
    "WeatherSystem",
]
