"""
Simulador de Desastres Naturales (Gestión de Crisis)

Simula evolución dinámica de desastres para operaciones humanitarias.
"""

import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class DisasterType(str, Enum):
    """Tipos de desastres"""
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    HURRICANE = "hurricane"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    LANDSLIDE = "landslide"


class DisasterPhase(str, Enum):
    """Fases del desastre"""
    WARNING = "warning"          # Pre-impacto
    IMPACT = "impact"            # Impacto inicial
    EMERGENCY = "emergency"      # Respuesta inmediata
    STABILIZATION = "stabilization"  # Estabilización
    RECOVERY = "recovery"        # Recuperación


@dataclass
class AffectedArea:
    """Área afectada por desastre"""
    id: str
    center: Dict[str, float]
    radius_km: float
    population_at_risk: int
    casualties: int = 0
    displaced: int = 0
    infrastructure_damage: float = 0.0  # 0-1
    access_blocked: bool = False


@dataclass
class Resource Need:
    """Necesidad de recursos"""
    type: str  # "medical", "food", "water", "shelter", "rescue"
    urgency: str  # "critical", "high", "medium", "low"
    quantity: int
    location: Dict[str, float]


class DisasterSimulator:
    """
    Simula evolución de desastres naturales

    Genera:
    - Progresión dinámica del desastre
    - Áreas afectadas
    - Necesidades de recursos
    - Población en riesgo
    """

    def __init__(self, disaster_type: DisasterType, severity: float):
        self.disaster_type = disaster_type
        self.severity = severity  # 0-1
        self.phase = DisasterPhase.WARNING
        self.start_time = datetime.now()
        self.elapsed_time = 0.0  # segundos

        # Áreas afectadas
        self.affected_areas: List[AffectedArea] = []

        # Necesidades de recursos
        self.resource_needs: List[ResourceNeed] = []

        # Estadísticas
        self.total_casualties = 0
        self.total_displaced = 0
        self.total_rescued = 0

        # Estado específico por tipo
        if disaster_type == DisasterType.WILDFIRE:
            self.fire_zones: List[Dict] = []
        elif disaster_type == DisasterType.FLOOD:
            self.water_level_cm = 0

        self._initialize_disaster()

    def _initialize_disaster(self):
        """Inicializa el desastre"""
        # Crear área inicial
        epicenter = {"lat": 4.5, "lon": -74.0}  # Bogotá ejemplo

        if self.disaster_type == DisasterType.EARTHQUAKE:
            self._initialize_earthquake(epicenter)
        elif self.disaster_type == DisasterType.FLOOD:
            self._initialize_flood(epicenter)
        elif self.disaster_type == DisasterType.WILDFIRE:
            self._initialize_wildfire(epicenter)
        elif self.disaster_type == DisasterType.HURRICANE:
            self._initialize_hurricane(epicenter)

    def _initialize_earthquake(self, epicenter: Dict):
        """Inicializa terremoto"""
        # Magnitud basada en severity
        magnitude = 5.0 + (self.severity * 3.5)  # 5.0 - 8.5

        # Radio de afectación
        radius_km = 50 * (magnitude / 7.0)

        area = AffectedArea(
            id="QUAKE-ZONE-1",
            center=epicenter,
            radius_km=radius_km,
            population_at_risk=int(100000 * self.severity),
            casualties=int(1000 * self.severity),
            displaced=int(5000 * self.severity),
            infrastructure_damage=self.severity * 0.8,
        )

        self.affected_areas.append(area)

        # Transición inmediata a IMPACT
        self.phase = DisasterPhase.IMPACT

    def _initialize_flood(self, location: Dict):
        """Inicializa inundación"""
        # Inundación de río
        self.water_level_cm = int(100 + self.severity * 400)  # 100-500 cm

        area = AffectedArea(
            id="FLOOD-ZONE-1",
            center=location,
            radius_km=20 + self.severity * 30,
            population_at_risk=int(50000 * self.severity),
            access_blocked=True,
        )

        self.affected_areas.append(area)
        self.phase = DisasterPhase.IMPACT

    def _initialize_wildfire(self, location: Dict):
        """Inicializa incendio forestal"""
        # Zona inicial de incendio
        fire_zone = {
            "id": "FIRE-1",
            "center": location,
            "perimeter_km": 2 + self.severity * 8,
            "intensity": self.severity,
            "spread_rate_kmh": 1 + self.severity * 5,
        }

        self.fire_zones.append(fire_zone)

        area = AffectedArea(
            id="FIRE-ZONE-1",
            center=location,
            radius_km=fire_zone["perimeter_km"],
            population_at_risk=int(20000 * self.severity),
        )

        self.affected_areas.append(area)
        self.phase = DisasterPhase.IMPACT

    def _initialize_hurricane(self, location: Dict):
        """Inicializa huracán"""
        # Categoría basada en severity
        category = int(1 + self.severity * 4)  # Cat 1-5

        area = AffectedArea(
            id="HURRICANE-ZONE-1",
            center=location,
            radius_km=100 + category * 50,
            population_at_risk=int(200000 * self.severity),
        )

        self.affected_areas.append(area)
        self.phase = DisasterPhase.WARNING  # Huracán tiene warning previo

    def update(self, dt: float):
        """
        Actualiza simulación del desastre

        Args:
            dt: Delta time en segundos
        """
        self.elapsed_time += dt

        # Actualizar fase
        self._update_phase()

        # Actualizar según tipo
        if self.disaster_type == DisasterType.WILDFIRE:
            self._update_wildfire(dt)
        elif self.disaster_type == DisasterType.FLOOD:
            self._update_flood(dt)
        elif self.disaster_type == DisasterType.HURRICANE:
            self._update_hurricane(dt)
        elif self.disaster_type == DisasterType.EARTHQUAKE:
            self._update_earthquake(dt)

        # Actualizar necesidades de recursos
        self._update_resource_needs()

    def _update_phase(self):
        """Actualiza fase del desastre"""
        hours_elapsed = self.elapsed_time / 3600

        if self.phase == DisasterPhase.WARNING and hours_elapsed > 2:
            self.phase = DisasterPhase.IMPACT

        elif self.phase == DisasterPhase.IMPACT and hours_elapsed > 6:
            self.phase = DisasterPhase.EMERGENCY

        elif self.phase == DisasterPhase.EMERGENCY and hours_elapsed > 24:
            self.phase = DisasterPhase.STABILIZATION

        elif self.phase == DisasterPhase.STABILIZATION and hours_elapsed > 72:
            self.phase = DisasterPhase.RECOVERY

    def _update_wildfire(self, dt: float):
        """Actualiza incendio forestal"""
        # Factores ambientales (simplificados)
        wind_speed_kmh = 10 + random.random() * 20
        humidity = 0.3 + random.random() * 0.4

        for fire_zone in self.fire_zones:
            # Calcular tasa de spread
            spread_rate = fire_zone["spread_rate_kmh"]
            spread_rate *= (wind_speed_kmh / 15)  # Factor viento
            spread_rate *= (1 - humidity)  # Factor humedad

            # Expandir perímetro
            growth = spread_rate * (dt / 3600)  # km
            fire_zone["perimeter_km"] += growth

            # Actualizar área afectada
            for area in self.affected_areas:
                if area.id.startswith("FIRE"):
                    area.radius_km = fire_zone["perimeter_km"]

            # Saltos de fuego (ember jumps) aleatorios
            if random.random() < 0.05:  # 5% chance
                self._create_spot_fire(fire_zone)

        # Calcular bajas
        self._calculate_casualties()

    def _create_spot_fire(self, origin_fire: Dict):
        """Crea fuego secundario por brasas voladoras"""
        # Nuevo foco a distancia aleatoria
        distance_km = random.uniform(1, 5)
        angle_rad = random.uniform(0, 2 * math.pi)

        new_lat = origin_fire["center"]["lat"] + (distance_km / 111) * math.cos(angle_rad)
        new_lon = origin_fire["center"]["lon"] + (distance_km / 111) * math.sin(angle_rad)

        new_fire = {
            "id": f"FIRE-{len(self.fire_zones) + 1}",
            "center": {"lat": new_lat, "lon": new_lon},
            "perimeter_km": 0.5,
            "intensity": origin_fire["intensity"] * 0.7,
            "spread_rate_kmh": origin_fire["spread_rate_kmh"] * 0.8,
        }

        self.fire_zones.append(new_fire)

    def _update_flood(self, dt: float):
        """Actualiza inundación"""
        hours = self.elapsed_time / 3600

        # Nivel de agua aumenta durante primeras 12h, luego decrece
        if hours < 12:
            self.water_level_cm += int((dt / 3600) * 10)  # +10cm/hora
        else:
            self.water_level_cm -= int((dt / 3600) * 5)   # -5cm/hora

        self.water_level_cm = max(0, self.water_level_cm)

        # Actualizar afectación
        for area in self.affected_areas:
            if self.water_level_cm > 200:  # >2m
                area.access_blocked = True
            else:
                area.access_blocked = False

        self._calculate_casualties()

    def _update_hurricane(self, dt: float):
        """Actualiza huracán"""
        hours = self.elapsed_time / 3600

        if self.phase == DisasterPhase.IMPACT:
            # Impacto durante 6-12 horas
            if hours > 12:
                self.phase = DisasterPhase.EMERGENCY

        self._calculate_casualties()

    def _update_earthquake(self, dt: float):
        """Actualiza terremoto"""
        # Terremotos tienen réplicas
        if random.random() < 0.01:  # 1% chance cada tick
            self._generate_aftershock()

    def _generate_aftershock(self):
        """Genera réplica"""
        # Réplica con menor magnitud
        aftershock_severity = self.severity * random.uniform(0.3, 0.7)

        # TODO: Agregar daño adicional

    def _calculate_casualties(self):
        """Calcula bajas basado en progresión"""
        for area in self.affected_areas:
            # Bajas aumentan con el tiempo si no hay rescate
            if self.phase in [DisasterPhase.IMPACT, DisasterPhase.EMERGENCY]:
                # Sin rescate, bajas aumentan
                new_casualties = int(area.population_at_risk * 0.001 * self.severity)
                area.casualties += new_casualties
                self.total_casualties += new_casualties

    def _update_resource_needs(self):
        """Actualiza necesidades de recursos"""
        self.resource_needs.clear()

        for area in self.affected_areas:
            # Necesidades según fase
            if self.phase == DisasterPhase.IMPACT:
                self.resource_needs.append(ResourceNeed(
                    type="rescue",
                    urgency="critical",
                    quantity=area.population_at_risk // 10,
                    location=area.center,
                ))

            if self.phase in [DisasterPhase.EMERGENCY, DisasterPhase.STABILIZATION]:
                self.resource_needs.extend([
                    ResourceNeed(
                        type="medical",
                        urgency="critical" if self.phase == DisasterPhase.EMERGENCY else "high",
                        quantity=area.casualties * 2,
                        location=area.center,
                    ),
                    ResourceNeed(
                        type="water",
                        urgency="high",
                        quantity=area.displaced * 5,  # 5L por persona
                        location=area.center,
                    ),
                    ResourceNeed(
                        type="food",
                        urgency="high",
                        quantity=area.displaced * 3,  # 3 raciones
                        location=area.center,
                    ),
                ])

    def get_priority_areas(self) -> List[AffectedArea]:
        """Retorna áreas prioritarias para respuesta"""
        # Ordenar por población en riesgo
        return sorted(
            self.affected_areas,
            key=lambda a: a.population_at_risk - a.displaced,
            reverse=True
        )

    def record_rescue(self, area_id: str, people_rescued: int):
        """Registra personas rescatadas"""
        for area in self.affected_areas:
            if area.id == area_id:
                area.displaced += people_rescued
                area.population_at_risk -= people_rescued
                self.total_rescued += people_rescued
                break

    def get_status(self) -> Dict:
        """Retorna estado del desastre"""
        return {
            "type": self.disaster_type.value,
            "severity": self.severity,
            "phase": self.phase.value,
            "elapsed_hours": self.elapsed_time / 3600,
            "affected_areas": len(self.affected_areas),
            "total_at_risk": sum(a.population_at_risk for a in self.affected_areas),
            "total_casualties": self.total_casualties,
            "total_displaced": self.total_displaced,
            "total_rescued": self.total_rescued,
            "critical_needs": len([n for n in self.resource_needs if n.urgency == "critical"]),
        }
