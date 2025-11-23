"""
Simulador de ataques cibernéticos
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid
import random


class ThreatCategory(Enum):
    """Categorías de amenazas"""
    RECONNAISSANCE = "reconnaissance"
    WEAPONIZATION = "weaponization"
    DELIVERY = "delivery"
    EXPLOITATION = "exploitation"
    INSTALLATION = "installation"
    COMMAND_CONTROL = "c2"
    ACTIONS = "actions_on_objectives"


@dataclass
class CyberThreat:
    """Amenaza cibernética"""
    threat_id: str
    attack_type: str
    target: str
    category: ThreatCategory
    severity: int  # 1-10
    impact_score: float  # 0-100

    # Características
    complexity: float = 0.5  # 0-1
    stealth: float = 0.5  # 0-1
    persistence: bool = False

    # TTPs (Tactics, Techniques, Procedures)
    mitre_techniques: list = field(default_factory=list)

    # Estado
    detected: bool = False
    mitigated: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


class AttackSimulator:
    """Simula ataques cibernéticos"""

    def __init__(self):
        self._active_threats: dict[str, CyberThreat] = {}
        self._attack_templates = self._load_templates()

    def _load_templates(self) -> dict:
        """Carga plantillas de ataques"""
        return {
            "ddos": {
                "category": ThreatCategory.ACTIONS,
                "base_severity": 6,
                "mitre": ["T1498", "T1499"],
                "targets": ["c2", "network", "web_server"]
            },
            "apt": {
                "category": ThreatCategory.EXPLOITATION,
                "base_severity": 9,
                "mitre": ["T1190", "T1133", "T1078"],
                "targets": ["database", "c2", "classified"]
            },
            "ransomware": {
                "category": ThreatCategory.ACTIONS,
                "base_severity": 8,
                "mitre": ["T1486", "T1490"],
                "targets": ["database", "file_server", "workstation"]
            },
            "false_data_injection": {
                "category": ThreatCategory.ACTIONS,
                "base_severity": 9,
                "mitre": ["T1565"],
                "targets": ["radar", "sensor", "database"]
            },
            "scada_intrusion": {
                "category": ThreatCategory.EXPLOITATION,
                "base_severity": 10,
                "mitre": ["T0831", "T0855"],
                "targets": ["ics", "plc", "rtu"]
            },
            "phishing": {
                "category": ThreatCategory.DELIVERY,
                "base_severity": 5,
                "mitre": ["T1566"],
                "targets": ["user", "workstation"]
            },
            "zero_day": {
                "category": ThreatCategory.EXPLOITATION,
                "base_severity": 10,
                "mitre": ["T1203"],
                "targets": ["any"]
            },
            "supply_chain": {
                "category": ThreatCategory.WEAPONIZATION,
                "base_severity": 9,
                "mitre": ["T1195"],
                "targets": ["software", "hardware"]
            }
        }

    def generate_threat(
        self,
        attack_type: str,
        target: str,
        intensity: float = 1.0
    ) -> CyberThreat:
        """Genera una amenaza"""
        template = self._attack_templates.get(attack_type, {
            "category": ThreatCategory.ACTIONS,
            "base_severity": 5,
            "mitre": []
        })

        severity = min(10, int(template["base_severity"] * intensity))
        impact = severity * 10 * intensity

        threat = CyberThreat(
            threat_id=f"THR-{str(uuid.uuid4())[:8].upper()}",
            attack_type=attack_type,
            target=target,
            category=template["category"],
            severity=severity,
            impact_score=impact,
            complexity=random.uniform(0.3, 0.9),
            stealth=random.uniform(0.2, 0.8),
            mitre_techniques=template.get("mitre", [])
        )

        self._active_threats[threat.threat_id] = threat
        return threat

    def get_active_threats(self) -> list[dict]:
        """Obtiene amenazas activas"""
        return [
            {
                "threat_id": t.threat_id,
                "type": t.attack_type,
                "target": t.target,
                "severity": t.severity,
                "detected": t.detected,
                "mitigated": t.mitigated
            }
            for t in self._active_threats.values()
            if not t.mitigated
        ]

    def update(self, dt: float):
        """Actualiza el simulador"""
        # Eliminar amenazas mitigadas antiguas
        to_remove = []
        for tid, threat in self._active_threats.items():
            if threat.mitigated:
                elapsed = (datetime.now() - threat.timestamp).total_seconds()
                if elapsed > 3600:  # 1 hora
                    to_remove.append(tid)

        for tid in to_remove:
            del self._active_threats[tid]

    def mark_detected(self, threat_id: str):
        """Marca una amenaza como detectada"""
        if threat_id in self._active_threats:
            self._active_threats[threat_id].detected = True

    def mark_mitigated(self, threat_id: str):
        """Marca una amenaza como mitigada"""
        if threat_id in self._active_threats:
            self._active_threats[threat_id].mitigated = True
