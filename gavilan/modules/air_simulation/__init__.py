"""
Motor de Simulación Aérea
=========================

Incluye:
- Cinemática 2D/3D de aeronaves y misiles
- Modelos de radar (RCS, detección)
- Combate aire-aire y aire-tierra
- ECM/ECCM
- Lógica de daños y pérdidas
"""

from gavilan.modules.air_simulation.air_module import AirSimulationModule
from gavilan.modules.air_simulation.combat import CombatEngine
from gavilan.modules.air_simulation.radar import RadarSimulator
from gavilan.modules.air_simulation.weapons import WeaponSystem

__all__ = [
    "AirSimulationModule",
    "CombatEngine",
    "RadarSimulator",
    "WeaponSystem",
]
