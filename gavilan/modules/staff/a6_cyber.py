"""
A6 - Sección de Ciberdefensa
============================

Gestiona:
- Ataques simulados a sistemas
- Defensa activa (firewalls, IPS)
- Forense post-ataque
- Simulación de Zero-Days
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import random
import uuid

from gavilan.core.events import Event, EventType, event_bus


class SystemType(Enum):
    """Tipos de sistemas"""
    RADAR = "radar"
    COMMAND_CONTROL = "c2"
    COMMUNICATIONS = "communications"
    DATABASE = "database"
    NETWORK = "network"
    ICS_SCADA = "ics_scada"
    WEAPONS = "weapons_system"


class AttackType(Enum):
    """Tipos de ataques cibernéticos"""
    DDOS = "ddos"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    APT = "apt"
    SQL_INJECTION = "sql_injection"
    PHISHING = "phishing"
    ZERO_DAY = "zero_day"
    MAN_IN_MIDDLE = "mitm"
    DATA_EXFILTRATION = "data_exfiltration"
    FALSE_DATA_INJECTION = "false_data_injection"


class ThreatLevel(Enum):
    """Nivel de amenaza"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CyberSystem:
    """Sistema monitoreado por ciberdefensa"""
    system_id: str
    system_type: SystemType
    name: str
    criticality: ThreatLevel = ThreatLevel.MEDIUM

    # Estado
    operational: bool = True
    compromised: bool = False
    integrity: float = 100.0  # 0-100

    # Defensa
    defense_level: float = 0.7  # 0-1
    has_ids: bool = True
    has_firewall: bool = True
    patched: bool = True

    # Métricas
    attacks_detected: int = 0
    attacks_blocked: int = 0


@dataclass
class CyberAttack:
    """Ataque cibernético"""
    attack_id: str
    attack_type: AttackType
    target_system: str
    severity: ThreatLevel
    timestamp: datetime = field(default_factory=datetime.now)

    # Estado
    detected: bool = False
    blocked: bool = False
    successful: bool = False

    # Detalles
    source_ip: str = ""
    vector: str = ""
    payload: str = ""

    # Impacto
    damage_percent: float = 0.0
    data_compromised: bool = False


@dataclass
class ForensicReport:
    """Reporte forense de un ataque"""
    report_id: str
    attack_id: str
    timestamp: datetime
    findings: dict = field(default_factory=dict)
    indicators_of_compromise: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


class CyberSection:
    """Sección A6 - Gestión de Ciberdefensa"""

    def __init__(self):
        self.event_bus = event_bus
        self._systems: dict[str, CyberSystem] = {}
        self._attacks: list[CyberAttack] = []
        self._active_threats: list[CyberAttack] = []
        self._forensic_reports: list[ForensicReport] = []

        # Estado general
        self._threat_level = ThreatLevel.LOW
        self._alerts: list = []

    def register_system(
        self,
        system_id: str,
        system_type: SystemType,
        name: str,
        **kwargs
    ) -> CyberSystem:
        """Registra un sistema para monitoreo"""
        system = CyberSystem(
            system_id=system_id,
            system_type=system_type,
            name=name
        )

        for key, value in kwargs.items():
            if hasattr(system, key):
                setattr(system, key, value)

        self._systems[system_id] = system
        return system

    def simulate_attack(
        self,
        target_system_id: str,
        attack_type: AttackType,
        severity: ThreatLevel = ThreatLevel.MEDIUM
    ) -> CyberAttack:
        """Simula un ataque cibernético"""
        attack = CyberAttack(
            attack_id=f"ATK-{str(uuid.uuid4())[:8].upper()}",
            attack_type=attack_type,
            target_system=target_system_id,
            severity=severity,
            source_ip=f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
        )

        # Evaluar si el ataque es detectado y bloqueado
        if target_system_id in self._systems:
            system = self._systems[target_system_id]
            system.attacks_detected += 1

            # Probabilidad de detección
            detection_prob = system.defense_level
            if system.has_ids:
                detection_prob += 0.2
            if attack_type == AttackType.ZERO_DAY:
                detection_prob -= 0.4

            attack.detected = random.random() < detection_prob

            # Probabilidad de bloqueo
            if attack.detected:
                block_prob = system.defense_level
                if system.has_firewall:
                    block_prob += 0.3
                if system.patched:
                    block_prob += 0.2

                attack.blocked = random.random() < block_prob

            if attack.blocked:
                system.attacks_blocked += 1
            else:
                attack.successful = True
                attack.damage_percent = severity.value * 20

                # Aplicar daño
                system.integrity -= attack.damage_percent
                if system.integrity <= 0:
                    system.operational = False
                    system.compromised = True

        self._attacks.append(attack)

        if attack.successful:
            self._active_threats.append(attack)
            self.event_bus.publish(Event(
                event_type=EventType.SYSTEM_COMPROMISED,
                source="A6",
                priority=1,
                data={
                    "attack_id": attack.attack_id,
                    "system_id": target_system_id,
                    "attack_type": attack_type.value
                }
            ))

        self._update_threat_level()
        return attack

    def handle_compromise(self, event: Event):
        """Maneja evento de sistema comprometido"""
        system_id = event.data.get("system_id")
        if system_id in self._systems:
            # Iniciar respuesta a incidente
            self._initiate_incident_response(system_id)

    def _initiate_incident_response(self, system_id: str):
        """Inicia respuesta a incidente"""
        # En implementación real: aislar sistema, analizar, restaurar
        self._alerts.append({
            "type": "incident_response",
            "system_id": system_id,
            "timestamp": datetime.now(),
            "status": "initiated"
        })

    def restore_system(self, system_id: str) -> bool:
        """Restaura un sistema comprometido"""
        if system_id not in self._systems:
            return False

        system = self._systems[system_id]
        system.operational = True
        system.compromised = False
        system.integrity = 100.0

        # Generar reporte forense
        related_attacks = [
            a for a in self._active_threats
            if a.target_system == system_id
        ]

        if related_attacks:
            self._generate_forensic_report(related_attacks[-1])

        # Limpiar amenazas activas
        self._active_threats = [
            a for a in self._active_threats
            if a.target_system != system_id
        ]

        self.event_bus.publish(Event(
            event_type=EventType.SYSTEM_RESTORED,
            source="A6",
            data={"system_id": system_id}
        ))

        self._update_threat_level()
        return True

    def _generate_forensic_report(self, attack: CyberAttack) -> ForensicReport:
        """Genera reporte forense de un ataque"""
        report = ForensicReport(
            report_id=f"FOR-{str(uuid.uuid4())[:8].upper()}",
            attack_id=attack.attack_id,
            timestamp=datetime.now(),
            findings={
                "attack_type": attack.attack_type.value,
                "source_ip": attack.source_ip,
                "damage": attack.damage_percent,
                "timeline": attack.timestamp.isoformat()
            },
            indicators_of_compromise=[
                attack.source_ip,
                f"signature_{attack.attack_type.value}"
            ],
            recommendations=[
                "Update signatures",
                "Patch vulnerable systems",
                "Review access controls"
            ]
        )

        self._forensic_reports.append(report)
        return report

    def _update_threat_level(self):
        """Actualiza nivel de amenaza general"""
        if not self._active_threats:
            self._threat_level = ThreatLevel.LOW
        elif len(self._active_threats) >= 3:
            self._threat_level = ThreatLevel.CRITICAL
        elif any(a.severity == ThreatLevel.CRITICAL for a in self._active_threats):
            self._threat_level = ThreatLevel.HIGH
        else:
            self._threat_level = ThreatLevel.MEDIUM

    def inject_false_radar_data(self, radar_id: str, false_tracks: list):
        """Simula inyección de datos falsos a radar"""
        attack = self.simulate_attack(
            radar_id,
            AttackType.FALSE_DATA_INJECTION,
            ThreatLevel.HIGH
        )

        if attack.successful:
            return {
                "success": True,
                "false_tracks_injected": len(false_tracks),
                "attack_id": attack.attack_id
            }

        return {"success": False, "reason": "Attack blocked"}

    def update(self, dt: float, engine):
        """Actualiza estado de ciberdefensa"""
        # Recuperación gradual de sistemas
        for system in self._systems.values():
            if system.integrity < 100 and not system.compromised:
                system.integrity = min(100, system.integrity + 2 * dt)

        # Degradación de amenazas activas no mitigadas
        for attack in self._active_threats:
            if attack.successful:
                system = self._systems.get(attack.target_system)
                if system:
                    system.integrity = max(0, system.integrity - 0.5 * dt)

    def get_security_posture(self) -> dict:
        """Obtiene postura de seguridad actual"""
        compromised = sum(1 for s in self._systems.values() if s.compromised)
        operational = sum(1 for s in self._systems.values() if s.operational)

        return {
            "threat_level": self._threat_level.name,
            "systems_total": len(self._systems),
            "systems_operational": operational,
            "systems_compromised": compromised,
            "active_threats": len(self._active_threats),
            "total_attacks": len(self._attacks),
            "attacks_blocked": sum(1 for a in self._attacks if a.blocked)
        }

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        posture = self.get_security_posture()

        by_type = {}
        for system in self._systems.values():
            stype = system.system_type.value
            by_type[stype] = by_type.get(stype, 0) + 1

        return {
            **posture,
            "systems_by_type": by_type,
            "alerts": len(self._alerts),
            "forensic_reports": len(self._forensic_reports)
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación de ciberdefensa"""
        if not self._systems:
            return 0.5

        # Factor de integridad promedio
        avg_integrity = sum(
            s.integrity for s in self._systems.values()
        ) / len(self._systems) / 100

        # Factor de sistemas operacionales
        operational_ratio = sum(
            1 for s in self._systems.values() if s.operational
        ) / len(self._systems)

        # Penalización por amenazas activas
        threat_penalty = min(0.5, len(self._active_threats) * 0.1)

        return max(0, (avg_integrity * 0.4 + operational_ratio * 0.6) - threat_penalty)
