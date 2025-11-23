"""
Motor de combate aéreo
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import math
import random
import uuid

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Aircraft, Side


class EngagementType(Enum):
    """Tipos de engagement"""
    BVR = "beyond_visual_range"
    WVR = "within_visual_range"
    GUN = "guns"


class EngagementResult(Enum):
    """Resultados de engagement"""
    PENDING = "pending"
    HIT = "hit"
    MISS = "miss"
    DESTROYED = "destroyed"
    DAMAGED = "damaged"
    EVADED = "evaded"


@dataclass
class Engagement:
    """Registro de un engagement"""
    engagement_id: str
    shooter_id: str
    target_id: str
    engagement_type: EngagementType
    weapon_type: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    result: EngagementResult = EngagementResult.PENDING

    # Condiciones
    initial_range_km: float = 0
    aspect_angle: float = 0
    target_altitude_ft: float = 0

    # Resultado
    pk_calculated: float = 0
    damage_inflicted: float = 0


class CombatEngine:
    """Motor de simulación de combate"""

    def __init__(self):
        self.event_bus = event_bus
        self._engagements: dict[str, Engagement] = {}

        # Tablas de Pk (probabilidad de kill)
        self._pk_tables = self._load_pk_tables()

    def _load_pk_tables(self) -> dict:
        """Carga tablas de probabilidad de kill por arma"""
        return {
            "AIM-120": {
                "base_pk": 0.85,
                "max_range_km": 100,
                "min_range_km": 5,
                "aspect_factor": 0.8  # Menor desde atrás
            },
            "AIM-9X": {
                "base_pk": 0.90,
                "max_range_km": 20,
                "min_range_km": 1,
                "aspect_factor": 0.7
            },
            "R-77": {
                "base_pk": 0.80,
                "max_range_km": 80,
                "min_range_km": 5,
                "aspect_factor": 0.75
            },
            "R-73": {
                "base_pk": 0.85,
                "max_range_km": 30,
                "min_range_km": 0.5,
                "aspect_factor": 0.65
            },
            "GUN": {
                "base_pk": 0.30,
                "max_range_km": 2,
                "min_range_km": 0.1,
                "aspect_factor": 1.0
            }
        }

    def initiate_engagement(
        self,
        shooter: Aircraft,
        target: Aircraft,
        weapon_type: str
    ) -> dict:
        """Inicia un engagement"""
        # Calcular condiciones
        range_km = shooter.position.distance_to(target.position)
        bearing = shooter.position.bearing_to(target.position)

        # Calcular ángulo de aspecto
        relative_bearing = (target.velocity.heading_deg - bearing + 180) % 360
        is_front_aspect = 150 <= relative_bearing <= 210

        # Determinar tipo de engagement
        if range_km > 20:
            eng_type = EngagementType.BVR
        elif weapon_type == "GUN":
            eng_type = EngagementType.GUN
        else:
            eng_type = EngagementType.WVR

        # Verificar alcance del arma
        weapon_data = self._pk_tables.get(weapon_type, self._pk_tables["AIM-120"])

        if range_km > weapon_data["max_range_km"]:
            return {
                "success": False,
                "reason": f"Target out of range ({range_km:.1f} km > {weapon_data['max_range_km']} km)"
            }

        if range_km < weapon_data["min_range_km"]:
            return {
                "success": False,
                "reason": f"Target too close ({range_km:.1f} km < {weapon_data['min_range_km']} km)"
            }

        # Calcular Pk
        pk = self._calculate_pk(
            weapon_data,
            range_km,
            is_front_aspect,
            target
        )

        # Crear engagement
        engagement = Engagement(
            engagement_id=f"ENG-{str(uuid.uuid4())[:8].upper()}",
            shooter_id=shooter.entity_id,
            target_id=target.entity_id,
            engagement_type=eng_type,
            weapon_type=weapon_type,
            initial_range_km=range_km,
            aspect_angle=relative_bearing,
            target_altitude_ft=target.position.altitude_ft,
            pk_calculated=pk
        )

        self._engagements[engagement.engagement_id] = engagement

        # Publicar evento
        self.event_bus.publish(Event(
            event_type=EventType.WEAPON_LAUNCH,
            source="combat",
            data={
                "engagement_id": engagement.engagement_id,
                "shooter": shooter.entity_id,
                "target": target.entity_id,
                "weapon": weapon_type
            }
        ))

        return {
            "success": True,
            "engagement_id": engagement.engagement_id,
            "pk": pk,
            "range_km": range_km,
            "engagement_type": eng_type.value
        }

    def _calculate_pk(
        self,
        weapon_data: dict,
        range_km: float,
        is_front_aspect: bool,
        target: Aircraft
    ) -> float:
        """Calcula probabilidad de kill"""
        base_pk = weapon_data["base_pk"]

        # Factor de rango
        max_range = weapon_data["max_range_km"]
        range_factor = 1 - (range_km / max_range) ** 2

        # Factor de aspecto
        aspect_factor = 1.0 if is_front_aspect else weapon_data["aspect_factor"]

        # Factor de RCS del objetivo (menor RCS = menor Pk)
        rcs = target.rcs_m2
        if rcs < 1:
            rcs_factor = 0.5 + (rcs * 0.5)
        else:
            rcs_factor = min(1.2, 1 + math.log10(rcs) * 0.1)

        # Factor de maniobra (más G disponibles = puede evadir mejor)
        maneuver_factor = 1 - (target.max_g - 5) * 0.02

        # Factor de contramedidas
        cm_factor = 1 - (target.countermeasures / 100) * 0.15

        # Pk final
        pk = base_pk * range_factor * aspect_factor * rcs_factor * maneuver_factor * cm_factor

        return max(0.05, min(0.95, pk))

    def resolve_engagement(self, engagement_id: str, engine) -> dict:
        """Resuelve un engagement"""
        if engagement_id not in self._engagements:
            return {"error": "Engagement not found"}

        engagement = self._engagements[engagement_id]

        # Tirar dados
        roll = random.random()

        if roll < engagement.pk_calculated:
            # Hit
            damage = random.uniform(30, 100)
            engagement.damage_inflicted = damage

            # Aplicar daño al objetivo
            target = engine.get_entity(engagement.target_id)
            if target:
                target.health -= damage

                if target.health <= 0:
                    engagement.result = EngagementResult.DESTROYED
                    target.destroyed = True
                    target.active = False

                    self.event_bus.publish(Event(
                        event_type=EventType.AIRCRAFT_DESTROY,
                        source="combat",
                        data={
                            "aircraft_id": target.entity_id,
                            "killer": engagement.shooter_id
                        }
                    ))
                else:
                    engagement.result = EngagementResult.DAMAGED

                    self.event_bus.publish(Event(
                        event_type=EventType.AIRCRAFT_DAMAGE,
                        source="combat",
                        data={
                            "aircraft_id": target.entity_id,
                            "damage": damage
                        }
                    ))
        else:
            # Miss
            engagement.result = EngagementResult.MISS

        engagement.end_time = datetime.now()

        self.event_bus.publish(Event(
            event_type=EventType.WEAPON_IMPACT,
            source="combat",
            data={
                "engagement_id": engagement_id,
                "result": engagement.result.value
            }
        ))

        return {
            "engagement_id": engagement_id,
            "result": engagement.result.value,
            "damage": engagement.damage_inflicted,
            "pk_was": engagement.pk_calculated
        }

    def update(self, dt: float, engine):
        """Actualiza engagements pendientes"""
        # Resolver engagements que han tenido tiempo de vuelo
        for eng_id, eng in list(self._engagements.items()):
            if eng.result == EngagementResult.PENDING:
                elapsed = (datetime.now() - eng.start_time).total_seconds()

                # Tiempo de vuelo aproximado basado en rango
                flight_time = eng.initial_range_km / 3  # ~3 km/s para misil

                if elapsed >= flight_time:
                    self.resolve_engagement(eng_id, engine)

    def get_active_engagements(self) -> list[dict]:
        """Obtiene engagements activos"""
        return [
            {
                "engagement_id": e.engagement_id,
                "shooter": e.shooter_id,
                "target": e.target_id,
                "weapon": e.weapon_type,
                "pk": e.pk_calculated
            }
            for e in self._engagements.values()
            if e.result == EngagementResult.PENDING
        ]
