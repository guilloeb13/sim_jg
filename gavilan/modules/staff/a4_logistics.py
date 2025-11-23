"""
A4 - Sección de Logística
=========================

Gestiona:
- Inventario de combustible, misiles, repuestos
- Tiempos de mantenimiento
- Impacto logístico en disponibilidad
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime, timedelta

from gavilan.core.events import Event, EventType, event_bus


class MaintenanceType(Enum):
    """Tipos de mantenimiento"""
    PREFLIGHT = "preflight"
    POSTFLIGHT = "postflight"
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    BATTLE_DAMAGE = "battle_damage"


class SupplyType(Enum):
    """Tipos de suministros"""
    FUEL = "fuel"
    AAM = "air_to_air_missiles"
    AGM = "air_to_ground_missiles"
    BOMBS = "bombs"
    AMMO = "ammunition"
    SPARE_PARTS = "spare_parts"
    COUNTERMEASURES = "countermeasures"


@dataclass
class SupplyItem:
    """Item de suministro"""
    supply_type: SupplyType
    quantity: float
    unit: str
    reorder_point: float
    max_capacity: float
    consumption_rate: float = 0  # Por hora


@dataclass
class MaintenanceTask:
    """Tarea de mantenimiento"""
    task_id: str
    aircraft_id: str
    maintenance_type: MaintenanceType
    description: str
    estimated_hours: float
    start_time: datetime = None
    end_time: datetime = None
    completed: bool = False
    technicians_required: int = 2


@dataclass
class AircraftLogistics:
    """Estado logístico de una aeronave"""
    aircraft_id: str
    fuel_percent: float = 100.0
    weapons_loaded: dict = field(default_factory=dict)
    maintenance_status: str = "operational"
    flight_hours: float = 0
    hours_until_inspection: float = 100
    last_maintenance: datetime = None
    scheduled_maintenance: datetime = None


class LogisticsSection:
    """Sección A4 - Gestión de Logística"""

    def __init__(self):
        self.event_bus = event_bus

        # Inventarios
        self._supplies: dict[str, dict[SupplyType, SupplyItem]] = {}  # Por base
        self._aircraft_logistics: dict[str, AircraftLogistics] = {}

        # Mantenimiento
        self._maintenance_queue: list[MaintenanceTask] = []
        self._active_maintenance: dict[str, MaintenanceTask] = {}
        self._maintenance_capacity: int = 5

        # Métricas
        self._total_fuel_dispensed: float = 0
        self._total_weapons_expended: int = 0

    def initialize_base_supplies(self, base_id: str, supply_levels: dict = None):
        """Inicializa suministros de una base"""
        default_supplies = {
            SupplyType.FUEL: SupplyItem(
                supply_type=SupplyType.FUEL,
                quantity=500000,
                unit="gallons",
                reorder_point=100000,
                max_capacity=1000000,
                consumption_rate=5000
            ),
            SupplyType.AAM: SupplyItem(
                supply_type=SupplyType.AAM,
                quantity=200,
                unit="missiles",
                reorder_point=50,
                max_capacity=500
            ),
            SupplyType.AGM: SupplyItem(
                supply_type=SupplyType.AGM,
                quantity=100,
                unit="missiles",
                reorder_point=25,
                max_capacity=300
            ),
            SupplyType.BOMBS: SupplyItem(
                supply_type=SupplyType.BOMBS,
                quantity=500,
                unit="units",
                reorder_point=100,
                max_capacity=1000
            ),
            SupplyType.SPARE_PARTS: SupplyItem(
                supply_type=SupplyType.SPARE_PARTS,
                quantity=1000,
                unit="sets",
                reorder_point=200,
                max_capacity=2000
            ),
        }

        if supply_levels:
            for stype, level in supply_levels.items():
                if stype in default_supplies:
                    default_supplies[stype].quantity = level

        self._supplies[base_id] = default_supplies

    def register_aircraft(self, aircraft_id: str):
        """Registra una aeronave en el sistema logístico"""
        self._aircraft_logistics[aircraft_id] = AircraftLogistics(
            aircraft_id=aircraft_id,
            last_maintenance=datetime.now()
        )

    def check_aircraft_ready(self, aircraft_id: str) -> bool:
        """Verifica si una aeronave está lista para misión"""
        if aircraft_id not in self._aircraft_logistics:
            return False

        logistics = self._aircraft_logistics[aircraft_id]

        # Verificar combustible
        if logistics.fuel_percent < 80:
            return False

        # Verificar mantenimiento
        if logistics.maintenance_status != "operational":
            return False

        # Verificar horas de vuelo
        if logistics.hours_until_inspection <= 0:
            return False

        return True

    def prepare_aircraft_for_mission(
        self,
        aircraft_id: str,
        base_id: str,
        loadout: dict
    ) -> bool:
        """Prepara una aeronave para misión"""
        if aircraft_id not in self._aircraft_logistics:
            return False

        if base_id not in self._supplies:
            return False

        logistics = self._aircraft_logistics[aircraft_id]
        base_supplies = self._supplies[base_id]

        # Repostar
        fuel_needed = (100 - logistics.fuel_percent) * 100  # Gallons aproximados
        if base_supplies[SupplyType.FUEL].quantity >= fuel_needed:
            base_supplies[SupplyType.FUEL].quantity -= fuel_needed
            logistics.fuel_percent = 100
            self._total_fuel_dispensed += fuel_needed
        else:
            return False

        # Cargar armamento
        for weapon_type, quantity in loadout.items():
            supply_type = self._map_weapon_to_supply(weapon_type)
            if supply_type and supply_type in base_supplies:
                if base_supplies[supply_type].quantity >= quantity:
                    base_supplies[supply_type].quantity -= quantity
                    logistics.weapons_loaded[weapon_type] = quantity
                else:
                    return False

        return True

    def _map_weapon_to_supply(self, weapon_type: str) -> Optional[SupplyType]:
        """Mapea tipo de arma a tipo de suministro"""
        mapping = {
            "AIM-120": SupplyType.AAM,
            "AIM-9": SupplyType.AAM,
            "AGM-88": SupplyType.AGM,
            "JDAM": SupplyType.BOMBS,
            "Mk82": SupplyType.BOMBS,
            "Mk84": SupplyType.BOMBS,
        }
        return mapping.get(weapon_type)

    def process_post_mission(self, aircraft_id: str, mission_result: dict):
        """Procesa logística post-misión"""
        if aircraft_id not in self._aircraft_logistics:
            return

        logistics = self._aircraft_logistics[aircraft_id]

        # Actualizar combustible usado
        fuel_used = mission_result.get("fuel_used_percent", 50)
        logistics.fuel_percent = max(0, logistics.fuel_percent - fuel_used)

        # Actualizar horas de vuelo
        flight_hours = mission_result.get("flight_hours", 2)
        logistics.flight_hours += flight_hours
        logistics.hours_until_inspection -= flight_hours

        # Verificar si necesita mantenimiento
        if logistics.hours_until_inspection <= 10:
            self.schedule_maintenance(
                aircraft_id,
                MaintenanceType.SCHEDULED,
                "Inspección programada",
                8
            )

        # Registrar armas expendidas
        weapons_used = mission_result.get("weapons_used", {})
        for weapon, count in weapons_used.items():
            if weapon in logistics.weapons_loaded:
                logistics.weapons_loaded[weapon] -= count
                self._total_weapons_expended += count

        # Verificar daño de batalla
        if mission_result.get("battle_damage", False):
            self.schedule_maintenance(
                aircraft_id,
                MaintenanceType.BATTLE_DAMAGE,
                "Reparación de daño de combate",
                24
            )
            logistics.maintenance_status = "damaged"

    def schedule_maintenance(
        self,
        aircraft_id: str,
        maint_type: MaintenanceType,
        description: str,
        estimated_hours: float
    ):
        """Programa mantenimiento para una aeronave"""
        import uuid

        task = MaintenanceTask(
            task_id=f"MX-{str(uuid.uuid4())[:8].upper()}",
            aircraft_id=aircraft_id,
            maintenance_type=maint_type,
            description=description,
            estimated_hours=estimated_hours
        )

        self._maintenance_queue.append(task)

        if aircraft_id in self._aircraft_logistics:
            self._aircraft_logistics[aircraft_id].maintenance_status = "awaiting_maintenance"

    def handle_mission_requirements(self, event: Event):
        """Maneja requisitos de misión desde A3"""
        mission_data = event.data
        # Verificar disponibilidad de recursos para la misión
        aircraft_count = mission_data.get("aircraft_count", 0)

        # Registrar en métricas
        pass

    def update(self, dt: float, engine):
        """Actualiza estado logístico"""
        hours = dt / 3600

        # Procesar cola de mantenimiento
        while (
            len(self._active_maintenance) < self._maintenance_capacity
            and self._maintenance_queue
        ):
            task = self._maintenance_queue.pop(0)
            task.start_time = datetime.now()
            self._active_maintenance[task.aircraft_id] = task

        # Actualizar mantenimientos activos
        completed = []
        for aid, task in self._active_maintenance.items():
            elapsed = (datetime.now() - task.start_time).total_seconds() / 3600

            if elapsed >= task.estimated_hours:
                task.completed = True
                task.end_time = datetime.now()
                completed.append(aid)

                # Restaurar aeronave
                if aid in self._aircraft_logistics:
                    logistics = self._aircraft_logistics[aid]
                    logistics.maintenance_status = "operational"

                    if task.maintenance_type == MaintenanceType.SCHEDULED:
                        logistics.hours_until_inspection = 100

        for aid in completed:
            del self._active_maintenance[aid]

        # Verificar niveles de suministros
        for base_id, supplies in self._supplies.items():
            for supply_type, item in supplies.items():
                if item.quantity <= item.reorder_point:
                    self.event_bus.publish(Event(
                        event_type=EventType.SUPPLY_DELIVERED if supply_type == SupplyType.FUEL else EventType.AMMO_LOW,
                        source="A4",
                        data={
                            "base_id": base_id,
                            "supply_type": supply_type.value,
                            "quantity": item.quantity,
                            "reorder_point": item.reorder_point
                        }
                    ))

    def get_supply_status(self, base_id: str = None) -> dict:
        """Obtiene estado de suministros"""
        if base_id and base_id in self._supplies:
            return {
                st.value: {
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "percent": (item.quantity / item.max_capacity) * 100
                }
                for st, item in self._supplies[base_id].items()
            }

        # Resumen de todas las bases
        return {
            bid: self.get_supply_status(bid)
            for bid in self._supplies.keys()
        }

    def get_fleet_readiness(self) -> dict:
        """Obtiene estado de preparación de la flota"""
        total = len(self._aircraft_logistics)
        operational = sum(
            1 for l in self._aircraft_logistics.values()
            if l.maintenance_status == "operational"
        )
        in_maintenance = len(self._active_maintenance)
        awaiting = sum(
            1 for l in self._aircraft_logistics.values()
            if l.maintenance_status == "awaiting_maintenance"
        )

        return {
            "total_aircraft": total,
            "operational": operational,
            "in_maintenance": in_maintenance,
            "awaiting_maintenance": awaiting,
            "readiness_rate": operational / max(1, total)
        }

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        fleet = self.get_fleet_readiness()

        return {
            "fleet_readiness": fleet,
            "maintenance_queue": len(self._maintenance_queue),
            "active_maintenance": len(self._active_maintenance),
            "total_fuel_dispensed": self._total_fuel_dispensed,
            "total_weapons_expended": self._total_weapons_expended,
            "bases_count": len(self._supplies)
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación logística"""
        fleet = self.get_fleet_readiness()
        fleet_score = fleet["readiness_rate"]

        # Verificar suministros críticos
        supply_score = 1.0
        for base_supplies in self._supplies.values():
            for item in base_supplies.values():
                if item.quantity < item.reorder_point:
                    supply_score -= 0.1

        return max(0, min(1, fleet_score * 0.6 + supply_score * 0.4))
