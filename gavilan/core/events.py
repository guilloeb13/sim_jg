"""
Sistema de eventos para comunicación entre módulos
"""

from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
from datetime import datetime
import uuid
import asyncio
from collections import defaultdict


class EventType(Enum):
    """Tipos de eventos del sistema"""
    # Eventos de simulación
    SIMULATION_START = "simulation_start"
    SIMULATION_PAUSE = "simulation_pause"
    SIMULATION_END = "simulation_end"
    TIME_TICK = "time_tick"

    # Eventos de aeronaves
    AIRCRAFT_SPAWN = "aircraft_spawn"
    AIRCRAFT_DESTROY = "aircraft_destroy"
    AIRCRAFT_DAMAGE = "aircraft_damage"
    AIRCRAFT_DETECT = "aircraft_detect"
    AIRCRAFT_LOST_CONTACT = "aircraft_lost_contact"

    # Eventos de combate
    WEAPON_LAUNCH = "weapon_launch"
    WEAPON_IMPACT = "weapon_impact"
    ENGAGEMENT_START = "engagement_start"
    ENGAGEMENT_END = "engagement_end"

    # Eventos de radar
    RADAR_CONTACT = "radar_contact"
    RADAR_TRACK = "radar_track"
    RADAR_LOST = "radar_lost"
    RADAR_JAM = "radar_jam"

    # Eventos de Estado Mayor
    MISSION_ASSIGNED = "mission_assigned"
    MISSION_COMPLETE = "mission_complete"
    MISSION_ABORT = "mission_abort"
    ATO_GENERATED = "ato_generated"
    SCRAMBLE_ORDER = "scramble_order"

    # Eventos A1 - Personal
    PERSONNEL_FATIGUE = "personnel_fatigue"
    PERSONNEL_UNAVAILABLE = "personnel_unavailable"
    SHIFT_CHANGE = "shift_change"

    # Eventos A2 - Inteligencia
    INTEL_UPDATE = "intel_update"
    THREAT_DETECTED = "threat_detected"
    SIGINT_INTERCEPT = "sigint_intercept"

    # Eventos A4 - Logística
    FUEL_LOW = "fuel_low"
    AMMO_LOW = "ammo_low"
    MAINTENANCE_REQUIRED = "maintenance_required"
    SUPPLY_DELIVERED = "supply_delivered"

    # Eventos A5 - Comunicaciones
    COMM_FAILURE = "comm_failure"
    COMM_RESTORED = "comm_restored"
    JAMMING_DETECTED = "jamming_detected"

    # Eventos A6 - Ciberdefensa
    CYBER_ATTACK = "cyber_attack"
    CYBER_DEFENSE = "cyber_defense"
    SYSTEM_COMPROMISED = "system_compromised"
    SYSTEM_RESTORED = "system_restored"

    # Eventos espaciales
    SPACE_WEATHER_ALERT = "space_weather_alert"
    GPS_DEGRADATION = "gps_degradation"
    SATCOM_FAILURE = "satcom_failure"

    # Eventos CTF
    FLAG_CAPTURED = "flag_captured"
    CHALLENGE_COMPLETE = "challenge_complete"


@dataclass
class Event:
    """Clase base para eventos del sistema"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "system"
    target: str = ""
    data: dict = field(default_factory=dict)
    priority: int = 5  # 1-10, 1 es más prioritario

    def to_dict(self) -> dict:
        """Convierte el evento a diccionario"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "priority": self.priority,
        }


class EventBus:
    """Bus de eventos para comunicación asíncrona entre módulos"""

    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self._event_history: list[Event] = []
        self._max_history: int = 10000
        self._async_queue: asyncio.Queue = None

    def subscribe(self, event_type: EventType, callback: Callable):
        """Suscribe una función a un tipo de evento"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Cancela la suscripción de una función"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event):
        """Publica un evento de forma síncrona"""
        self._event_history.append(event)

        # Limitar historial
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Notificar suscriptores
        for callback in self._subscribers[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error en callback para {event.event_type}: {e}")

    async def publish_async(self, event: Event):
        """Publica un evento de forma asíncrona"""
        self._event_history.append(event)

        for callback in self._subscribers[event.event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error en callback async para {event.event_type}: {e}")

    def get_history(
        self,
        event_type: EventType = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> list[Event]:
        """Obtiene historial de eventos filtrado"""
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events[-limit:]

    def clear_history(self):
        """Limpia el historial de eventos"""
        self._event_history.clear()


# Instancia global del bus de eventos
event_bus = EventBus()
