"""
Entidades base del sistema de simulación
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
import math
import numpy as np


class EntityType(Enum):
    """Tipos de entidades"""
    AIRCRAFT = "aircraft"
    HELICOPTER = "helicopter"
    UAV = "uav"
    MISSILE = "missile"
    RADAR = "radar"
    SAM = "sam"
    COMMAND_CENTER = "command_center"
    AIRBASE = "airbase"
    SHIP = "ship"
    GROUND_UNIT = "ground_unit"


class AircraftRole(Enum):
    """Roles de aeronaves"""
    FIGHTER = "fighter"
    BOMBER = "bomber"
    TRANSPORT = "transport"
    TANKER = "tanker"
    AWACS = "awacs"
    RECCE = "recce"
    EW = "electronic_warfare"
    CAS = "close_air_support"


class Side(Enum):
    """Bandos en el conflicto"""
    BLUE = "blue"  # Fuerzas propias
    RED = "red"    # Fuerzas enemigas
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class Position:
    """Posición 3D en coordenadas geográficas"""
    latitude: float
    longitude: float
    altitude_ft: float

    def distance_to(self, other: 'Position') -> float:
        """Calcula distancia en km usando fórmula de Haversine"""
        R = 6371  # Radio de la Tierra en km

        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        horizontal_dist = R * c
        vertical_dist = abs(other.altitude_ft - self.altitude_ft) * 0.0003048  # ft a km

        return math.sqrt(horizontal_dist**2 + vertical_dist**2)

    def bearing_to(self, other: 'Position') -> float:
        """Calcula azimut hacia otra posición en grados"""
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360


@dataclass
class Velocity:
    """Velocidad 3D"""
    speed_kts: float  # Velocidad en nudos
    heading_deg: float  # Rumbo en grados
    climb_rate_fpm: float = 0  # Razón de ascenso/descenso ft/min

    def to_vector(self) -> np.ndarray:
        """Convierte a vector de velocidad"""
        speed_ms = self.speed_kts * 0.514444
        heading_rad = math.radians(self.heading_deg)

        vx = speed_ms * math.sin(heading_rad)
        vy = speed_ms * math.cos(heading_rad)
        vz = self.climb_rate_fpm * 0.00508  # fpm a m/s

        return np.array([vx, vy, vz])


@dataclass
class Entity:
    """Clase base para todas las entidades"""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entity_type: EntityType = EntityType.GROUND_UNIT
    side: Side = Side.UNKNOWN
    position: Position = field(default_factory=lambda: Position(0, 0, 0))
    velocity: Velocity = field(default_factory=lambda: Velocity(0, 0, 0))

    # Estado
    active: bool = True
    destroyed: bool = False
    health: float = 100.0

    # Timestamps
    created_at: float = 0
    updated_at: float = 0

    def update_position(self, dt: float):
        """Actualiza posición basado en velocidad y tiempo"""
        if not self.active or self.destroyed:
            return

        # Conversión de velocidad
        speed_ms = self.velocity.speed_kts * 0.514444
        heading_rad = math.radians(self.velocity.heading_deg)

        # Desplazamiento en metros
        dx = speed_ms * math.sin(heading_rad) * dt
        dy = speed_ms * math.cos(heading_rad) * dt
        dz = self.velocity.climb_rate_fpm * 0.00508 * dt  # fpm a m/s

        # Actualizar coordenadas
        meters_per_deg_lat = 111320
        meters_per_deg_lon = meters_per_deg_lat * math.cos(math.radians(self.position.latitude))

        self.position.latitude += dy / meters_per_deg_lat
        self.position.longitude += dx / meters_per_deg_lon
        self.position.altitude_ft += dz * 3.28084  # m a ft

        self.updated_at += dt


@dataclass
class Aircraft(Entity):
    """Entidad de aeronave"""
    entity_type: EntityType = EntityType.AIRCRAFT

    # Características
    aircraft_type: str = "Generic Fighter"
    role: AircraftRole = AircraftRole.FIGHTER
    callsign: str = ""

    # Performance
    max_speed_kts: float = 1200
    max_altitude_ft: float = 50000
    max_g: float = 9.0
    turn_rate_deg_s: float = 15.0

    # Radar Cross Section
    rcs_m2: float = 5.0

    # Combustible
    fuel_capacity_lbs: float = 10000
    fuel_current_lbs: float = 8000
    fuel_consumption_lbs_h: float = 3000

    # Armamento
    weapons: list = field(default_factory=list)
    countermeasures: int = 60

    # Estado operacional
    mission_id: str = ""
    pilot_id: str = ""
    maintenance_status: str = "operational"

    def get_fuel_remaining_hours(self) -> float:
        """Calcula tiempo de vuelo restante"""
        if self.fuel_consumption_lbs_h <= 0:
            return float('inf')
        return self.fuel_current_lbs / self.fuel_consumption_lbs_h

    def consume_fuel(self, dt_hours: float):
        """Consume combustible"""
        consumption = self.fuel_consumption_lbs_h * dt_hours
        self.fuel_current_lbs = max(0, self.fuel_current_lbs - consumption)


@dataclass
class Radar(Entity):
    """Entidad de radar"""
    entity_type: EntityType = EntityType.RADAR

    # Características
    radar_type: str = "Search Radar"

    # Cobertura
    max_range_km: float = 400
    min_range_km: float = 5
    azimuth_coverage_deg: float = 360
    elevation_min_deg: float = -5
    elevation_max_deg: float = 45

    # Rendimiento
    update_rate_hz: float = 0.1
    min_detectable_rcs_m2: float = 1.0
    accuracy_range_m: float = 100
    accuracy_azimuth_deg: float = 1.0

    # Estado
    operational: bool = True
    jammed: bool = False
    jamming_effectiveness: float = 0.0

    def can_detect(self, target: Entity) -> tuple[bool, float]:
        """Determina si puede detectar un objetivo y con qué probabilidad"""
        if not self.operational or self.jammed:
            return False, 0.0

        distance = self.position.distance_to(target.position)

        if distance < self.min_range_km or distance > self.max_range_km:
            return False, 0.0

        # Calcular probabilidad basada en RCS y distancia
        if hasattr(target, 'rcs_m2'):
            rcs = target.rcs_m2
        else:
            rcs = 10.0  # RCS por defecto

        # Modelo simplificado: Pd = (RCS/min_RCS) * (1 - distance/max_range)^2
        rcs_factor = min(1.0, rcs / self.min_detectable_rcs_m2)
        range_factor = (1 - distance / self.max_range_km) ** 2

        probability = rcs_factor * range_factor * (1 - self.jamming_effectiveness)

        return probability > 0.3, probability


@dataclass
class CommandCenter(Entity):
    """Centro de comando y control"""
    entity_type: EntityType = EntityType.COMMAND_CENTER

    # Características
    center_type: str = "Tactical Operations Center"

    # Capacidades
    max_tracks: int = 200
    comm_range_km: float = 500

    # Estado sistemas
    systems_operational: dict = field(default_factory=lambda: {
        "radar_feed": True,
        "communications": True,
        "data_link": True,
        "command_system": True,
        "database": True,
    })

    # Ciberdefensa
    cyber_defense_level: float = 0.8
    compromised: bool = False

    def get_operational_status(self) -> float:
        """Calcula porcentaje de sistemas operacionales"""
        if not self.systems_operational:
            return 0.0
        operational = sum(1 for v in self.systems_operational.values() if v)
        return operational / len(self.systems_operational)


@dataclass
class SAMSite(Entity):
    """Sitio de misiles superficie-aire"""
    entity_type: EntityType = EntityType.SAM

    # Características
    sam_type: str = "Medium Range SAM"

    # Cobertura
    max_range_km: float = 80
    min_range_km: float = 3
    max_altitude_ft: float = 60000
    min_altitude_ft: float = 100

    # Armamento
    missiles_available: int = 8
    missiles_max: int = 8
    reload_time_min: float = 30

    # Radar asociado
    search_radar_id: str = ""
    track_radar_id: str = ""

    # Estado
    tracking_target: str = ""
    ready_to_fire: bool = True


@dataclass
class Airbase(Entity):
    """Base aérea"""
    entity_type: EntityType = EntityType.AIRBASE

    # Características
    name: str = "Air Base"
    icao_code: str = ""

    # Capacidades
    runway_length_ft: float = 10000
    parking_spots: int = 50
    fuel_capacity_gal: float = 1000000
    fuel_current_gal: float = 800000

    # Estado infraestructura
    runway_operational: bool = True
    runway_damage: float = 0.0

    # Aeronaves estacionadas
    aircraft_ids: list = field(default_factory=list)

    # Logística
    maintenance_capacity: int = 10  # Aeronaves simultáneas
    weapons_stockpile: dict = field(default_factory=dict)
