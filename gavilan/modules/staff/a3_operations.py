"""
A3 - Sección de Operaciones
===========================

Gestiona:
- Generación del ATO/ACO
- Control de misiones
- Gestión de SCRAMBLE, CAP, CAS, SEAD, escoltas
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime, timedelta
import uuid

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Aircraft, AircraftRole, Side


class MissionType(Enum):
    """Tipos de misión"""
    CAP = "combat_air_patrol"
    DCA = "defensive_counter_air"
    OCA = "offensive_counter_air"
    SEAD = "suppression_enemy_air_defense"
    DEAD = "destruction_enemy_air_defense"
    CAS = "close_air_support"
    AI = "air_interdiction"
    STRIKE = "strike"
    RECCE = "reconnaissance"
    ESCORT = "escort"
    TANKER = "air_refueling"
    AWACS = "awacs"
    TRANSPORT = "transport"
    SAR = "search_and_rescue"
    SCRAMBLE = "scramble"


class MissionStatus(Enum):
    """Estado de la misión"""
    PLANNED = "planned"
    BRIEFED = "briefed"
    LAUNCHED = "launched"
    EN_ROUTE = "en_route"
    ON_STATION = "on_station"
    ENGAGED = "engaged"
    RTB = "returning_to_base"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class MissionPriority(Enum):
    """Prioridad de misión"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Mission:
    """Definición de una misión"""
    mission_id: str
    mission_type: MissionType
    priority: MissionPriority
    status: MissionStatus = MissionStatus.PLANNED

    # Tiempos
    planned_takeoff: datetime = None
    actual_takeoff: datetime = None
    planned_rtb: datetime = None
    actual_rtb: datetime = None

    # Objetivos
    primary_target: dict = field(default_factory=dict)
    secondary_targets: list = field(default_factory=list)
    success_criteria: dict = field(default_factory=dict)

    # Recursos asignados
    aircraft_ids: list = field(default_factory=list)
    callsign: str = ""
    package_id: str = ""

    # Área de operaciones
    ingress_route: list = field(default_factory=list)
    egress_route: list = field(default_factory=list)
    station_point: dict = field(default_factory=dict)
    station_time_min: float = 60

    # Apoyo
    tanker_support: str = ""
    awacs_support: str = ""
    escort_package: str = ""

    # Resultados
    objectives_achieved: int = 0
    losses: int = 0
    damage_assessment: str = ""


@dataclass
class ATO:
    """Air Tasking Order"""
    ato_id: str
    period_start: datetime
    period_end: datetime
    missions: list[Mission] = field(default_factory=list)
    status: str = "draft"


class OperationsSection:
    """Sección A3 - Gestión de Operaciones"""

    def __init__(self):
        self.event_bus = event_bus
        self._current_ato: Optional[ATO] = None
        self._missions: dict[str, Mission] = {}
        self._active_missions: list[str] = []

        # Referencias a otras secciones
        self._logistics = None
        self._personnel = None
        self._intel = None

    def set_logistics_reference(self, logistics):
        """Establece referencia a A4"""
        self._logistics = logistics

    def set_personnel_reference(self, personnel):
        """Establece referencia a A1"""
        self._personnel = personnel

    def set_intel_reference(self, intel):
        """Establece referencia a A2"""
        self._intel = intel

    def generate_ato(self, objectives: list, duration_hours: float = 24) -> ATO:
        """Genera un ATO basado en objetivos"""
        now = datetime.now()

        ato = ATO(
            ato_id=f"ATO-{now.strftime('%Y%m%d-%H%M')}",
            period_start=now,
            period_end=now + timedelta(hours=duration_hours)
        )

        # Generar misiones para cada objetivo
        for obj in objectives:
            mission = self._plan_mission_for_objective(obj)
            if mission:
                ato.missions.append(mission)
                self._missions[mission.mission_id] = mission

        self._current_ato = ato

        self.event_bus.publish(Event(
            event_type=EventType.ATO_GENERATED,
            source="A3",
            data={
                "ato_id": ato.ato_id,
                "missions_count": len(ato.missions)
            }
        ))

        return ato

    def _plan_mission_for_objective(self, objective: dict) -> Optional[Mission]:
        """Planifica una misión para un objetivo específico"""
        obj_type = objective.get("type", "strike")
        priority = objective.get("priority", "medium")

        # Determinar tipo de misión
        mission_type_map = {
            "air_superiority": MissionType.CAP,
            "defense": MissionType.DCA,
            "strike": MissionType.STRIKE,
            "sead": MissionType.SEAD,
            "cas": MissionType.CAS,
            "reconnaissance": MissionType.RECCE,
        }

        mission_type = mission_type_map.get(obj_type, MissionType.STRIKE)

        priority_map = {
            "critical": MissionPriority.CRITICAL,
            "high": MissionPriority.HIGH,
            "medium": MissionPriority.MEDIUM,
            "low": MissionPriority.LOW,
        }

        mission = Mission(
            mission_id=f"MSN-{str(uuid.uuid4())[:8].upper()}",
            mission_type=mission_type,
            priority=priority_map.get(priority, MissionPriority.MEDIUM),
            primary_target=objective.get("target", {}),
            callsign=objective.get("callsign", f"EAGLE-{len(self._missions)+1}")
        )

        # Calcular tiempos
        mission.planned_takeoff = datetime.now() + timedelta(
            minutes=30 * (mission.priority.value)
        )

        return mission

    def assign_aircraft_to_mission(
        self,
        mission_id: str,
        aircraft_ids: list
    ) -> bool:
        """Asigna aeronaves a una misión"""
        if mission_id not in self._missions:
            return False

        mission = self._missions[mission_id]
        mission.aircraft_ids = aircraft_ids

        # Verificar con logística
        if self._logistics:
            for aid in aircraft_ids:
                if not self._logistics.check_aircraft_ready(aid):
                    return False

        self.event_bus.publish(Event(
            event_type=EventType.MISSION_ASSIGNED,
            source="A3",
            data={
                "mission_id": mission_id,
                "aircraft_count": len(aircraft_ids)
            }
        ))

        return True

    def launch_mission(self, mission_id: str) -> bool:
        """Lanza una misión"""
        if mission_id not in self._missions:
            return False

        mission = self._missions[mission_id]

        if not mission.aircraft_ids:
            return False

        mission.status = MissionStatus.LAUNCHED
        mission.actual_takeoff = datetime.now()
        self._active_missions.append(mission_id)

        return True

    def scramble(self, aircraft_ids: list, target_info: dict) -> Mission:
        """Ordena un scramble inmediato"""
        mission = Mission(
            mission_id=f"SCR-{str(uuid.uuid4())[:8].upper()}",
            mission_type=MissionType.SCRAMBLE,
            priority=MissionPriority.CRITICAL,
            primary_target=target_info,
            aircraft_ids=aircraft_ids,
            callsign=f"SCRAMBLE-{len(self._active_missions)+1}"
        )

        mission.status = MissionStatus.LAUNCHED
        mission.actual_takeoff = datetime.now()

        self._missions[mission.mission_id] = mission
        self._active_missions.append(mission.mission_id)

        self.event_bus.publish(Event(
            event_type=EventType.SCRAMBLE_ORDER,
            source="A3",
            priority=1,
            data={
                "mission_id": mission.mission_id,
                "aircraft": aircraft_ids,
                "target": target_info
            }
        ))

        return mission

    def update_mission_status(self, mission_id: str, new_status: MissionStatus):
        """Actualiza estado de una misión"""
        if mission_id in self._missions:
            mission = self._missions[mission_id]
            old_status = mission.status
            mission.status = new_status

            if new_status in [MissionStatus.COMPLETED, MissionStatus.ABORTED, MissionStatus.FAILED]:
                if mission_id in self._active_missions:
                    self._active_missions.remove(mission_id)
                mission.actual_rtb = datetime.now()

                event_type = (
                    EventType.MISSION_COMPLETE if new_status == MissionStatus.COMPLETED
                    else EventType.MISSION_ABORT
                )

                self.event_bus.publish(Event(
                    event_type=event_type,
                    source="A3",
                    data={
                        "mission_id": mission_id,
                        "status": new_status.value
                    }
                ))

    def handle_intel_update(self, event: Event):
        """Maneja actualizaciones de inteligencia"""
        # Evaluar si requiere cambios en misiones activas
        intel_data = event.data

        if intel_data.get("type") == "new_track":
            # Posible amenaza, evaluar scramble
            pass

    def update(self, dt: float, engine):
        """Actualiza operaciones"""
        # Actualizar estado de misiones activas
        for mid in list(self._active_missions):
            mission = self._missions.get(mid)
            if not mission:
                continue

            # Verificar aeronaves de la misión
            all_rtb = True
            for aid in mission.aircraft_ids:
                aircraft = engine.get_entity(aid)
                if aircraft and aircraft.active:
                    all_rtb = False

            if all_rtb and mission.status not in [
                MissionStatus.COMPLETED, MissionStatus.ABORTED
            ]:
                self.update_mission_status(mid, MissionStatus.COMPLETED)

    def get_mission_board(self) -> list[dict]:
        """Obtiene tablero de misiones"""
        return [
            {
                "mission_id": m.mission_id,
                "type": m.mission_type.value,
                "status": m.status.value,
                "priority": m.priority.value,
                "callsign": m.callsign,
                "aircraft_count": len(m.aircraft_ids),
                "planned_takeoff": m.planned_takeoff.isoformat() if m.planned_takeoff else None
            }
            for m in self._missions.values()
        ]

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        by_status = {}
        by_type = {}

        for m in self._missions.values():
            status = m.status.value
            mtype = m.mission_type.value

            by_status[status] = by_status.get(status, 0) + 1
            by_type[mtype] = by_type.get(mtype, 0) + 1

        return {
            "total_missions": len(self._missions),
            "active_missions": len(self._active_missions),
            "current_ato": self._current_ato.ato_id if self._current_ato else None,
            "by_status": by_status,
            "by_type": by_type
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación operacional"""
        if not self._missions:
            return 0.8  # Sin misiones, listo para planificar

        completed = sum(
            1 for m in self._missions.values()
            if m.status == MissionStatus.COMPLETED
        )
        failed = sum(
            1 for m in self._missions.values()
            if m.status in [MissionStatus.ABORTED, MissionStatus.FAILED]
        )
        total = len(self._missions)

        if total == 0:
            return 0.8

        success_rate = completed / total
        failure_penalty = failed / total * 0.3

        return max(0, min(1, success_rate - failure_penalty + 0.5))
