"""
Sistema de armas
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid

from gavilan.core.entities import Position, Velocity


class WeaponType(Enum):
    """Tipos de armas"""
    AAM_ACTIVE = "aam_active"  # Misil A-A radar activo
    AAM_IR = "aam_ir"  # Misil A-A infrarrojo
    AGM = "agm"  # Misil aire-tierra
    BOMB_GUIDED = "bomb_guided"
    BOMB_UNGUIDED = "bomb_unguided"
    GUN = "gun"


class GuidanceType(Enum):
    """Tipos de guiado"""
    ACTIVE_RADAR = "active_radar"
    SEMI_ACTIVE_RADAR = "semi_active_radar"
    INFRARED = "infrared"
    GPS = "gps"
    LASER = "laser"
    INERTIAL = "inertial"
    WIRE = "wire"


@dataclass
class Weapon:
    """Arma en vuelo"""
    weapon_id: str
    weapon_name: str
    weapon_type: WeaponType
    guidance: GuidanceType

    # Estado
    position: Position
    velocity: Velocity
    active: bool = True
    fuel_remaining: float = 1.0  # 0-1

    # Características
    max_speed_kts: float = 2500
    max_range_km: float = 100
    warhead_kg: float = 25
    pk_max: float = 0.9

    # Target
    target_id: str = ""
    time_of_flight: float = 0


class WeaponSystem:
    """Gestiona armas en vuelo"""

    def __init__(self):
        self._weapons_in_flight: dict[str, Weapon] = {}
        self._weapon_catalog = self._load_catalog()

    def _load_catalog(self) -> dict:
        """Carga catálogo de armas"""
        return {
            "AIM-120": {
                "type": WeaponType.AAM_ACTIVE,
                "guidance": GuidanceType.ACTIVE_RADAR,
                "max_speed_kts": 2650,
                "max_range_km": 100,
                "warhead_kg": 23,
                "pk_max": 0.85
            },
            "AIM-9X": {
                "type": WeaponType.AAM_IR,
                "guidance": GuidanceType.INFRARED,
                "max_speed_kts": 2200,
                "max_range_km": 20,
                "warhead_kg": 9,
                "pk_max": 0.90
            },
            "AGM-88": {
                "type": WeaponType.AGM,
                "guidance": GuidanceType.SEMI_ACTIVE_RADAR,
                "max_speed_kts": 1400,
                "max_range_km": 150,
                "warhead_kg": 66,
                "pk_max": 0.75
            },
            "JDAM": {
                "type": WeaponType.BOMB_GUIDED,
                "guidance": GuidanceType.GPS,
                "max_speed_kts": 600,
                "max_range_km": 28,
                "warhead_kg": 430,
                "pk_max": 0.95
            },
            "R-77": {
                "type": WeaponType.AAM_ACTIVE,
                "guidance": GuidanceType.ACTIVE_RADAR,
                "max_speed_kts": 2600,
                "max_range_km": 80,
                "warhead_kg": 22,
                "pk_max": 0.80
            },
            "R-73": {
                "type": WeaponType.AAM_IR,
                "guidance": GuidanceType.INFRARED,
                "max_speed_kts": 1800,
                "max_range_km": 30,
                "warhead_kg": 7.4,
                "pk_max": 0.85
            }
        }

    def launch_weapon(
        self,
        weapon_name: str,
        launch_position: Position,
        target_id: str,
        initial_velocity: Velocity
    ) -> Optional[Weapon]:
        """Lanza un arma"""
        if weapon_name not in self._weapon_catalog:
            return None

        catalog_entry = self._weapon_catalog[weapon_name]

        weapon = Weapon(
            weapon_id=f"WPN-{str(uuid.uuid4())[:8].upper()}",
            weapon_name=weapon_name,
            weapon_type=catalog_entry["type"],
            guidance=catalog_entry["guidance"],
            position=launch_position,
            velocity=initial_velocity,
            max_speed_kts=catalog_entry["max_speed_kts"],
            max_range_km=catalog_entry["max_range_km"],
            warhead_kg=catalog_entry["warhead_kg"],
            pk_max=catalog_entry["pk_max"],
            target_id=target_id
        )

        self._weapons_in_flight[weapon.weapon_id] = weapon
        return weapon

    def update(self, dt: float, engine):
        """Actualiza armas en vuelo"""
        for weapon_id in list(self._weapons_in_flight.keys()):
            weapon = self._weapons_in_flight[weapon_id]

            if not weapon.active:
                continue

            # Actualizar tiempo de vuelo
            weapon.time_of_flight += dt

            # Consumir combustible
            weapon.fuel_remaining -= dt / 30  # ~30 segundos de combustible

            if weapon.fuel_remaining <= 0:
                weapon.active = False
                del self._weapons_in_flight[weapon_id]
                continue

            # Actualizar posición hacia objetivo
            target = engine.get_entity(weapon.target_id)
            if target and target.active:
                # Guiado proporcional simplificado
                bearing = weapon.position.bearing_to(target.position)
                weapon.velocity.heading_deg = bearing
                weapon.position.update_position = None  # Usar cinemática simplificada

    def get_weapons_in_flight(self) -> int:
        """Obtiene número de armas en vuelo"""
        return len(self._weapons_in_flight)

    def get_weapon_info(self, weapon_name: str) -> Optional[dict]:
        """Obtiene información de un arma"""
        return self._weapon_catalog.get(weapon_name)
