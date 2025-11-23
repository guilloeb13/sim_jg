"""
GAVILAN - Sistema de Simulación de Juegos de Guerra Aérea
=========================================================

Sistema modular para entrenamiento de Fuerza Aérea que simula:
- Operaciones aéreas y combate
- Estado Mayor (A1-A6)
- Operaciones espaciales y clima espacial
- Ciberdefensa y ataques cibernéticos
- Inteligencia operacional

Autor: Fuerza Aérea
Versión: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Fuerza Aérea"

from gavilan.core.engine import SimulationEngine
from gavilan.core.config import GavilanConfig

__all__ = [
    "SimulationEngine",
    "GavilanConfig",
    "__version__",
]
