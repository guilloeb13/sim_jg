"""
Sistema de defensa cibernética
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random

from gavilan.modules.cyber.attacks import CyberThreat


class DefenseLayer(Enum):
    """Capas de defensa"""
    PERIMETER = "perimeter"
    NETWORK = "network"
    ENDPOINT = "endpoint"
    APPLICATION = "application"
    DATA = "data"


@dataclass
class SecurityControl:
    """Control de seguridad"""
    control_id: str
    name: str
    layer: DefenseLayer
    effectiveness: float  # 0-1
    active: bool = True
    last_updated: str = ""


class DefenseSystem:
    """Sistema de defensa en profundidad"""

    def __init__(self):
        self._controls: dict[str, SecurityControl] = {}
        self._detection_rate: float = 0.7
        self._block_rate: float = 0.6
        self._initialize_controls()

    def _initialize_controls(self):
        """Inicializa controles de seguridad por defecto"""
        default_controls = [
            ("firewall", "Next-Gen Firewall", DefenseLayer.PERIMETER, 0.85),
            ("ids", "Intrusion Detection System", DefenseLayer.NETWORK, 0.75),
            ("ips", "Intrusion Prevention System", DefenseLayer.NETWORK, 0.70),
            ("waf", "Web Application Firewall", DefenseLayer.APPLICATION, 0.65),
            ("edr", "Endpoint Detection Response", DefenseLayer.ENDPOINT, 0.80),
            ("dlp", "Data Loss Prevention", DefenseLayer.DATA, 0.60),
            ("siem", "Security Information Event Management", DefenseLayer.NETWORK, 0.70),
            ("av", "Antivirus/Antimalware", DefenseLayer.ENDPOINT, 0.55),
        ]

        for cid, name, layer, eff in default_controls:
            self._controls[cid] = SecurityControl(
                control_id=cid,
                name=name,
                layer=layer,
                effectiveness=eff
            )

    def evaluate_threat(self, threat: CyberThreat) -> bool:
        """Evalúa si una amenaza es bloqueada"""
        # Calcular probabilidad de detección
        detection_prob = self._detection_rate

        # Ajustar por características de la amenaza
        detection_prob *= (1 - threat.stealth * 0.5)

        # Evaluar controles relevantes
        for control in self._controls.values():
            if control.active:
                detection_prob = min(0.99, detection_prob + control.effectiveness * 0.1)

        # Penalización por zero-day
        if threat.attack_type == "zero_day":
            detection_prob *= 0.3

        # Determinar detección
        detected = random.random() < detection_prob
        threat.detected = detected

        if not detected:
            return False

        # Calcular probabilidad de bloqueo
        block_prob = self._block_rate

        for control in self._controls.values():
            if control.active:
                block_prob = min(0.95, block_prob + control.effectiveness * 0.05)

        # Ajustar por complejidad del ataque
        block_prob *= (1 - threat.complexity * 0.3)

        blocked = random.random() < block_prob
        threat.mitigated = blocked

        return blocked

    def add_control(self, control: SecurityControl):
        """Añade un control de seguridad"""
        self._controls[control.control_id] = control

    def disable_control(self, control_id: str):
        """Desactiva un control"""
        if control_id in self._controls:
            self._controls[control_id].active = False

    def enable_control(self, control_id: str):
        """Activa un control"""
        if control_id in self._controls:
            self._controls[control_id].active = True

    def update(self, dt: float):
        """Actualiza el sistema de defensa"""
        # Aquí se podrían actualizar firmas, reglas, etc.
        pass

    def get_status(self) -> dict:
        """Obtiene estado del sistema de defensa"""
        active = sum(1 for c in self._controls.values() if c.active)
        total = len(self._controls)

        by_layer = {}
        for c in self._controls.values():
            layer = c.layer.value
            if layer not in by_layer:
                by_layer[layer] = {"active": 0, "total": 0}
            by_layer[layer]["total"] += 1
            if c.active:
                by_layer[layer]["active"] += 1

        return {
            "active_controls": active,
            "total_controls": total,
            "by_layer": by_layer,
            "detection_rate": self._detection_rate,
            "block_rate": self._block_rate
        }

    def get_readiness(self) -> float:
        """Calcula preparación del sistema"""
        if not self._controls:
            return 0.0

        active = sum(1 for c in self._controls.values() if c.active)
        avg_effectiveness = sum(
            c.effectiveness for c in self._controls.values() if c.active
        ) / max(1, active)

        return (active / len(self._controls)) * avg_effectiveness
