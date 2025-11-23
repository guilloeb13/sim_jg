"""
Módulo del Estado Mayor (A1-A6)
================================

Gestiona todas las funciones del Estado Mayor:
- A1: Personal
- A2: Inteligencia
- A3: Operaciones
- A4: Logística
- A5: Comunicaciones
- A6: Ciberdefensa
"""

from gavilan.modules.staff.main import StaffModule
from gavilan.modules.staff.a1_personnel import PersonnelSection
from gavilan.modules.staff.a2_intelligence import IntelligenceSection
from gavilan.modules.staff.a3_operations import OperationsSection
from gavilan.modules.staff.a4_logistics import LogisticsSection
from gavilan.modules.staff.a5_communications import CommunicationsSection
from gavilan.modules.staff.a6_cyber import CyberSection

__all__ = [
    "StaffModule",
    "PersonnelSection",
    "IntelligenceSection",
    "OperationsSection",
    "LogisticsSection",
    "CommunicationsSection",
    "CyberSection",
]
