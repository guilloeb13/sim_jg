"""
Módulo Ciberespacial
====================

Simulaciones de amenazas y defensa digital:
- Ataques DDoS a centros de comando
- Intrusión a sistemas SCADA
- Compromiso de redes radar
- Evaluación de daño y restauración
"""

from gavilan.modules.cyber.cyber_module import CyberModule
from gavilan.modules.cyber.attacks import AttackSimulator
from gavilan.modules.cyber.defense import DefenseSystem

__all__ = [
    "CyberModule",
    "AttackSimulator",
    "DefenseSystem",
]
