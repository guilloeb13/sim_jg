"""
Módulo principal de ciberoperaciones
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid

from gavilan.core.events import Event, EventType, event_bus
from gavilan.modules.cyber.attacks import AttackSimulator, CyberThreat
from gavilan.modules.cyber.defense import DefenseSystem


class CyberModule:
    """Módulo de operaciones ciberespaciales"""

    def __init__(self):
        self.event_bus = event_bus
        self.attack_simulator = AttackSimulator()
        self.defense_system = DefenseSystem()

        self._incidents: list = []
        self._threat_intel: list = []

    def update(self, dt: float, engine):
        """Actualiza el módulo cibernético"""
        self.attack_simulator.update(dt)
        self.defense_system.update(dt)

    def launch_attack_scenario(
        self,
        scenario_type: str,
        targets: list,
        intensity: float = 1.0
    ) -> dict:
        """Lanza un escenario de ataque"""
        results = []

        for target in targets:
            threat = self.attack_simulator.generate_threat(
                scenario_type,
                target,
                intensity
            )

            # Evaluar contra defensas
            blocked = self.defense_system.evaluate_threat(threat)

            results.append({
                "target": target,
                "threat_id": threat.threat_id,
                "blocked": blocked,
                "impact": 0 if blocked else threat.impact_score
            })

            if not blocked:
                self._create_incident(threat)

        return {
            "scenario": scenario_type,
            "total_attacks": len(targets),
            "blocked": sum(1 for r in results if r["blocked"]),
            "successful": sum(1 for r in results if not r["blocked"]),
            "results": results
        }

    def _create_incident(self, threat: CyberThreat):
        """Crea un incidente de seguridad"""
        incident = {
            "incident_id": f"INC-{str(uuid.uuid4())[:8].upper()}",
            "threat_id": threat.threat_id,
            "target": threat.target,
            "type": threat.attack_type,
            "timestamp": datetime.now(),
            "status": "active",
            "impact": threat.impact_score
        }

        self._incidents.append(incident)

        self.event_bus.publish(Event(
            event_type=EventType.CYBER_ATTACK,
            source="cyber_module",
            priority=2,
            data=incident
        ))

    def get_threat_landscape(self) -> dict:
        """Obtiene panorama de amenazas"""
        return {
            "active_threats": self.attack_simulator.get_active_threats(),
            "incidents": len(self._incidents),
            "defense_status": self.defense_system.get_status()
        }

    def get_status(self) -> dict:
        """Obtiene estado del módulo"""
        active_incidents = sum(
            1 for i in self._incidents
            if i["status"] == "active"
        )

        return {
            "active_incidents": active_incidents,
            "total_incidents": len(self._incidents),
            "defense_readiness": self.defense_system.get_readiness()
        }
