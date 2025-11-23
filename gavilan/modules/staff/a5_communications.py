"""
A5 - Sección de Comunicaciones
==============================

Gestiona:
- Estado de enlaces satelitales, radio VHF/UHF, microondas
- Interferencias y jamming
- Ciberataques a comunicaciones
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime

from gavilan.core.events import Event, EventType, event_bus


class CommType(Enum):
    """Tipos de comunicación"""
    VHF = "vhf"
    UHF = "uhf"
    HF = "hf"
    SATCOM = "satcom"
    DATA_LINK = "data_link"
    MICROWAVE = "microwave"
    FIBER = "fiber"


class CommStatus(Enum):
    """Estado de comunicaciones"""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    JAMMED = "jammed"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class CommLink:
    """Enlace de comunicaciones"""
    link_id: str
    comm_type: CommType
    name: str
    status: CommStatus = CommStatus.OPERATIONAL

    # Características
    frequency_mhz: float = 0
    bandwidth_kbps: float = 0
    range_km: float = 0
    encrypted: bool = True

    # Estado
    signal_strength: float = 100.0  # 0-100
    noise_level: float = 10.0  # 0-100
    jamming_level: float = 0.0  # 0-100
    latency_ms: float = 50.0

    # Conectividad
    source_id: str = ""
    destination_id: str = ""


@dataclass
class CommNetwork:
    """Red de comunicaciones"""
    network_id: str
    name: str
    links: dict[str, CommLink] = field(default_factory=dict)
    redundancy_level: int = 1  # Número de rutas alternativas


class CommunicationsSection:
    """Sección A5 - Gestión de Comunicaciones"""

    def __init__(self):
        self.event_bus = event_bus
        self._networks: dict[str, CommNetwork] = {}
        self._links: dict[str, CommLink] = {}

        # Estado general
        self._overall_status = CommStatus.OPERATIONAL
        self._jamming_sources: list = []

        # Métricas
        self._link_failures: int = 0
        self._jamming_events: int = 0

    def create_network(self, network_id: str, name: str) -> CommNetwork:
        """Crea una red de comunicaciones"""
        network = CommNetwork(network_id=network_id, name=name)
        self._networks[network_id] = network
        return network

    def add_link(
        self,
        network_id: str,
        link_id: str,
        comm_type: CommType,
        name: str,
        **kwargs
    ) -> CommLink:
        """Añade un enlace a una red"""
        link = CommLink(
            link_id=link_id,
            comm_type=comm_type,
            name=name
        )

        # Configurar características por tipo
        default_configs = {
            CommType.VHF: {"range_km": 50, "bandwidth_kbps": 16, "latency_ms": 10},
            CommType.UHF: {"range_km": 80, "bandwidth_kbps": 32, "latency_ms": 15},
            CommType.HF: {"range_km": 3000, "bandwidth_kbps": 8, "latency_ms": 100},
            CommType.SATCOM: {"range_km": 40000, "bandwidth_kbps": 512, "latency_ms": 600},
            CommType.DATA_LINK: {"range_km": 500, "bandwidth_kbps": 1024, "latency_ms": 50},
            CommType.MICROWAVE: {"range_km": 50, "bandwidth_kbps": 10000, "latency_ms": 5},
        }

        if comm_type in default_configs:
            for key, value in default_configs[comm_type].items():
                setattr(link, key, value)

        # Aplicar kwargs
        for key, value in kwargs.items():
            if hasattr(link, key):
                setattr(link, key, value)

        self._links[link_id] = link

        if network_id in self._networks:
            self._networks[network_id].links[link_id] = link

        return link

    def apply_jamming(self, link_id: str, jamming_level: float, source: str = ""):
        """Aplica interferencia a un enlace"""
        if link_id not in self._links:
            return

        link = self._links[link_id]
        link.jamming_level = min(100, link.jamming_level + jamming_level)

        self._jamming_events += 1

        if source:
            self._jamming_sources.append({
                "source": source,
                "target": link_id,
                "level": jamming_level,
                "time": datetime.now()
            })

        # Actualizar estado
        if link.jamming_level > 80:
            link.status = CommStatus.JAMMED
        elif link.jamming_level > 40:
            link.status = CommStatus.DEGRADED

        # Publicar evento
        self.event_bus.publish(Event(
            event_type=EventType.JAMMING_DETECTED,
            source="A5",
            data={
                "link_id": link_id,
                "jamming_level": link.jamming_level
            }
        ))

    def apply_space_weather_effect(self, effect: dict):
        """Aplica efectos del clima espacial"""
        # Degradar SATCOM y HF
        for link in self._links.values():
            if link.comm_type == CommType.SATCOM:
                degradation = effect.get("comm_degradation_factor", 1.0)
                link.signal_strength *= degradation
                link.noise_level += (1 - degradation) * 50

            elif link.comm_type == CommType.HF:
                # HF muy sensible a clima espacial
                kp = effect.get("kp_index", 0)
                if kp > 5:
                    link.status = CommStatus.DEGRADED
                    link.signal_strength *= 0.5

        self._update_overall_status()

    def fail_link(self, link_id: str, reason: str = ""):
        """Marca un enlace como fallido"""
        if link_id not in self._links:
            return

        link = self._links[link_id]
        link.status = CommStatus.FAILED
        link.signal_strength = 0

        self._link_failures += 1

        self.event_bus.publish(Event(
            event_type=EventType.COMM_FAILURE,
            source="A5",
            data={
                "link_id": link_id,
                "comm_type": link.comm_type.value,
                "reason": reason
            }
        ))

        self._update_overall_status()

    def restore_link(self, link_id: str):
        """Restaura un enlace"""
        if link_id not in self._links:
            return

        link = self._links[link_id]
        link.status = CommStatus.OPERATIONAL
        link.signal_strength = 100
        link.jamming_level = 0
        link.noise_level = 10

        self.event_bus.publish(Event(
            event_type=EventType.COMM_RESTORED,
            source="A5",
            data={"link_id": link_id}
        ))

        self._update_overall_status()

    def _update_overall_status(self):
        """Actualiza estado general de comunicaciones"""
        if not self._links:
            self._overall_status = CommStatus.OPERATIONAL
            return

        failed = sum(1 for l in self._links.values() if l.status == CommStatus.FAILED)
        jammed = sum(1 for l in self._links.values() if l.status == CommStatus.JAMMED)
        degraded = sum(1 for l in self._links.values() if l.status == CommStatus.DEGRADED)
        total = len(self._links)

        if failed > total * 0.5:
            self._overall_status = CommStatus.FAILED
        elif jammed > total * 0.3 or failed > total * 0.2:
            self._overall_status = CommStatus.JAMMED
        elif degraded > total * 0.3:
            self._overall_status = CommStatus.DEGRADED
        else:
            self._overall_status = CommStatus.OPERATIONAL

    def check_connectivity(self, source_id: str, dest_id: str) -> dict:
        """Verifica conectividad entre dos puntos"""
        available_links = []

        for link in self._links.values():
            if link.status == CommStatus.OPERATIONAL:
                available_links.append(link)

        if not available_links:
            return {
                "connected": False,
                "reason": "No links available"
            }

        # Seleccionar mejor enlace
        best_link = min(available_links, key=lambda l: l.latency_ms)

        return {
            "connected": True,
            "link_id": best_link.link_id,
            "comm_type": best_link.comm_type.value,
            "latency_ms": best_link.latency_ms,
            "bandwidth_kbps": best_link.bandwidth_kbps
        }

    def update(self, dt: float, engine):
        """Actualiza estado de comunicaciones"""
        for link in self._links.values():
            # Reducir jamming gradualmente (contra-medidas)
            if link.jamming_level > 0:
                link.jamming_level = max(0, link.jamming_level - 5 * dt)

                # Actualizar estado si jamming baja
                if link.jamming_level < 40 and link.status == CommStatus.JAMMED:
                    link.status = CommStatus.DEGRADED
                elif link.jamming_level < 10 and link.status == CommStatus.DEGRADED:
                    link.status = CommStatus.OPERATIONAL

            # Variación natural en señal
            import random
            link.noise_level += random.uniform(-1, 1)
            link.noise_level = max(0, min(50, link.noise_level))

        self._update_overall_status()

    def get_network_status(self, network_id: str = None) -> dict:
        """Obtiene estado de una red o todas"""
        if network_id and network_id in self._networks:
            network = self._networks[network_id]
            return {
                "network_id": network_id,
                "name": network.name,
                "links": {
                    lid: {
                        "type": l.comm_type.value,
                        "status": l.status.value,
                        "signal": l.signal_strength
                    }
                    for lid, l in network.links.items()
                }
            }

        return {
            nid: self.get_network_status(nid)
            for nid in self._networks.keys()
        }

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        by_status = {}
        by_type = {}

        for link in self._links.values():
            status = link.status.value
            ltype = link.comm_type.value

            by_status[status] = by_status.get(status, 0) + 1
            by_type[ltype] = by_type.get(ltype, 0) + 1

        return {
            "overall_status": self._overall_status.value,
            "total_links": len(self._links),
            "networks": len(self._networks),
            "by_status": by_status,
            "by_type": by_type,
            "link_failures": self._link_failures,
            "jamming_events": self._jamming_events
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación de comunicaciones"""
        if not self._links:
            return 0.5

        operational = sum(
            1 for l in self._links.values()
            if l.status == CommStatus.OPERATIONAL
        )
        degraded = sum(
            1 for l in self._links.values()
            if l.status == CommStatus.DEGRADED
        )

        score = (operational + degraded * 0.5) / len(self._links)
        return score
