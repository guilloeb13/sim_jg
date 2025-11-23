"""
Módulo principal del Estado Mayor
"""

from dataclasses import dataclass
from typing import Optional

from gavilan.core.events import EventBus, Event, EventType, event_bus
from gavilan.modules.staff.a1_personnel import PersonnelSection
from gavilan.modules.staff.a2_intelligence import IntelligenceSection
from gavilan.modules.staff.a3_operations import OperationsSection
from gavilan.modules.staff.a4_logistics import LogisticsSection
from gavilan.modules.staff.a5_communications import CommunicationsSection
from gavilan.modules.staff.a6_cyber import CyberSection


class StaffModule:
    """Módulo que integra todas las secciones del Estado Mayor"""

    def __init__(self):
        self.event_bus = event_bus

        # Inicializar secciones
        self.a1_personnel = PersonnelSection()
        self.a2_intelligence = IntelligenceSection()
        self.a3_operations = OperationsSection()
        self.a4_logistics = LogisticsSection()
        self.a5_communications = CommunicationsSection()
        self.a6_cyber = CyberSection()

        # Referencias cruzadas para coordinación
        self.a3_operations.set_logistics_reference(self.a4_logistics)
        self.a3_operations.set_personnel_reference(self.a1_personnel)
        self.a3_operations.set_intel_reference(self.a2_intelligence)

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Configura manejadores de eventos entre secciones"""
        # A2 recibe alertas de A5 sobre comunicaciones
        self.event_bus.subscribe(
            EventType.COMM_FAILURE,
            self.a2_intelligence.handle_comm_event
        )

        # A3 recibe actualizaciones de inteligencia
        self.event_bus.subscribe(
            EventType.INTEL_UPDATE,
            self.a3_operations.handle_intel_update
        )

        # A4 responde a necesidades de misiones
        self.event_bus.subscribe(
            EventType.MISSION_ASSIGNED,
            self.a4_logistics.handle_mission_requirements
        )

        # A6 monitorea sistemas de todas las secciones
        self.event_bus.subscribe(
            EventType.SYSTEM_COMPROMISED,
            self.a6_cyber.handle_compromise
        )

    def update(self, dt: float, engine):
        """Actualiza todas las secciones del Estado Mayor"""
        # Actualizar en orden de prioridad
        self.a2_intelligence.update(dt, engine)
        self.a1_personnel.update(dt, engine)
        self.a4_logistics.update(dt, engine)
        self.a5_communications.update(dt, engine)
        self.a6_cyber.update(dt, engine)
        self.a3_operations.update(dt, engine)  # Operaciones al final, usa datos de otros

    def get_status_report(self) -> dict:
        """Genera reporte de estado de todas las secciones"""
        return {
            "A1_Personnel": self.a1_personnel.get_status(),
            "A2_Intelligence": self.a2_intelligence.get_status(),
            "A3_Operations": self.a3_operations.get_status(),
            "A4_Logistics": self.a4_logistics.get_status(),
            "A5_Communications": self.a5_communications.get_status(),
            "A6_Cyber": self.a6_cyber.get_status(),
            "overall_readiness": self._calculate_overall_readiness()
        }

    def _calculate_overall_readiness(self) -> float:
        """Calcula la preparación general del Estado Mayor"""
        readiness_scores = [
            self.a1_personnel.get_readiness(),
            self.a2_intelligence.get_readiness(),
            self.a3_operations.get_readiness(),
            self.a4_logistics.get_readiness(),
            self.a5_communications.get_readiness(),
            self.a6_cyber.get_readiness(),
        ]
        return sum(readiness_scores) / len(readiness_scores)

    def request_ato_generation(self, objectives: list) -> dict:
        """Solicita generación de ATO a A3"""
        return self.a3_operations.generate_ato(objectives)

    def request_intel_assessment(self, area: dict) -> dict:
        """Solicita evaluación de inteligencia a A2"""
        return self.a2_intelligence.assess_area(area)

    def request_logistics_support(self, requirements: dict) -> dict:
        """Solicita apoyo logístico a A4"""
        return self.a4_logistics.process_request(requirements)
