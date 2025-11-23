"""
Módulo de Entrenamiento (CTF Militar)
=====================================

Retos y escenarios de entrenamiento:
- Capture The Flag militar
- Escenarios de ciberataque
- Pruebas Red/Blue
- Registro de desempeño
"""

from gavilan.modules.training.training_module import TrainingModule
from gavilan.modules.training.ctf import CTFEngine

__all__ = [
    "TrainingModule",
    "CTFEngine",
]
