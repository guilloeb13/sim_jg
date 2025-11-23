"""
Módulo principal de simulación aérea
"""

from dataclasses import dataclass
from typing import Optional
import math

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Aircraft, Radar, Side, Position, EntityType
from gavilan.modules.air_simulation.combat import CombatEngine
from gavilan.modules.air_simulation.radar import RadarSimulator
from gavilan.modules.air_simulation.weapons import WeaponSystem


class AirSimulationModule:
    """Módulo de simulación de operaciones aéreas"""

    def __init__(self):
        self.event_bus = event_bus
        self.combat_engine = CombatEngine()
        self.radar_simulator = RadarSimulator()
        self.weapon_system = WeaponSystem()

        self._engagements: list = []

    def update(self, dt: float, engine):
        """Actualiza la simulación aérea"""
        # Actualizar cinemática de todas las aeronaves
        aircraft_list = engine.get_entities_by_type(EntityType.AIRCRAFT)

        for aircraft in aircraft_list:
            if aircraft.active and not aircraft.destroyed:
                self._update_aircraft_state(aircraft, dt)

        # Actualizar detecciones de radar
        self.radar_simulator.update(dt, engine)

        # Procesar combates
        self.combat_engine.update(dt, engine)

        # Actualizar armas en vuelo
        self.weapon_system.update(dt, engine)

    def _update_aircraft_state(self, aircraft: Aircraft, dt: float):
        """Actualiza estado de una aeronave"""
        # Consumir combustible
        hours = dt / 3600
        aircraft.consume_fuel(hours)

        # Verificar combustible crítico
        if aircraft.fuel_current_lbs < aircraft.fuel_capacity_lbs * 0.15:
            self.event_bus.publish(Event(
                event_type=EventType.FUEL_LOW,
                source="air_simulation",
                data={
                    "aircraft_id": aircraft.entity_id,
                    "fuel_percent": (aircraft.fuel_current_lbs / aircraft.fuel_capacity_lbs) * 100
                }
            ))

        # Verificar altitud mínima/máxima
        if aircraft.position.altitude_ft > aircraft.max_altitude_ft:
            aircraft.velocity.climb_rate_fpm = -1000
        elif aircraft.position.altitude_ft < 500:
            aircraft.velocity.climb_rate_fpm = max(0, aircraft.velocity.climb_rate_fpm)

    def calculate_intercept(
        self,
        interceptor: Aircraft,
        target: Aircraft
    ) -> dict:
        """Calcula solución de interceptación"""
        # Posiciones actuales
        dist = interceptor.position.distance_to(target.position)
        bearing = interceptor.position.bearing_to(target.position)

        # Velocidades
        int_speed = interceptor.velocity.speed_kts
        tgt_speed = target.velocity.speed_kts
        tgt_heading = target.velocity.heading_deg

        # Calcular punto de intercepción (simplificado)
        closure_rate = int_speed + tgt_speed * math.cos(
            math.radians(tgt_heading - bearing)
        )

        if closure_rate <= 0:
            return {
                "feasible": False,
                "reason": "No closure"
            }

        time_to_intercept = dist / (closure_rate * 1.852 / 3600)  # km to hours

        # Calcular heading requerido
        lead_angle = math.degrees(math.asin(
            min(1, tgt_speed * math.sin(math.radians(tgt_heading - bearing)) / int_speed)
        ))
        required_heading = (bearing + lead_angle) % 360

        return {
            "feasible": True,
            "bearing": bearing,
            "distance_km": dist,
            "required_heading": required_heading,
            "time_to_intercept_min": time_to_intercept * 60,
            "closure_rate_kts": closure_rate
        }

    def evaluate_threat(
        self,
        aircraft: Aircraft,
        threat: Aircraft
    ) -> dict:
        """Evalúa nivel de amenaza de un contacto"""
        dist = aircraft.position.distance_to(threat.position)
        bearing = aircraft.position.bearing_to(threat.position)

        # Aspecto (si viene de frente o atrás)
        relative_bearing = (threat.velocity.heading_deg - bearing + 180) % 360
        is_hot = 150 <= relative_bearing <= 210  # Viene hacia nosotros

        # Altitud
        alt_diff = threat.position.altitude_ft - aircraft.position.altitude_ft
        has_altitude_advantage = alt_diff > 2000

        # Velocidad
        speed_advantage = threat.velocity.speed_kts > aircraft.velocity.speed_kts

        # Calcular nivel de amenaza
        threat_level = 0

        if dist < 20:
            threat_level += 40
        elif dist < 50:
            threat_level += 25
        elif dist < 100:
            threat_level += 10

        if is_hot:
            threat_level += 30

        if has_altitude_advantage:
            threat_level += 15

        if speed_advantage:
            threat_level += 15

        return {
            "threat_level": min(100, threat_level),
            "distance_km": dist,
            "bearing": bearing,
            "is_hot": is_hot,
            "altitude_diff_ft": alt_diff,
            "recommendation": self._get_defensive_recommendation(threat_level, is_hot)
        }

    def _get_defensive_recommendation(self, threat_level: int, is_hot: bool) -> str:
        """Genera recomendación defensiva"""
        if threat_level >= 70:
            if is_hot:
                return "Break turn + chaff/flare"
            return "Defensive maneuver, deploy countermeasures"
        elif threat_level >= 40:
            return "Maintain awareness, prepare defensive"
        else:
            return "Monitor contact"

    def request_engagement(
        self,
        shooter: Aircraft,
        target: Aircraft,
        weapon_type: str
    ) -> dict:
        """Solicita engagement con un objetivo"""
        return self.combat_engine.initiate_engagement(
            shooter,
            target,
            weapon_type
        )

    def get_air_picture(self, engine, for_side: Side = Side.BLUE) -> list[dict]:
        """Obtiene imagen aérea actual"""
        picture = []

        for entity in engine._entities.values():
            if entity.entity_type != EntityType.AIRCRAFT:
                continue

            if entity.side == for_side:
                status = "friendly"
            elif entity.side == Side.RED:
                status = "hostile"
            else:
                status = "unknown"

            picture.append({
                "entity_id": entity.entity_id,
                "callsign": entity.callsign if hasattr(entity, 'callsign') else entity.name,
                "status": status,
                "position": {
                    "lat": entity.position.latitude,
                    "lon": entity.position.longitude,
                    "alt_ft": entity.position.altitude_ft
                },
                "velocity": {
                    "speed_kts": entity.velocity.speed_kts,
                    "heading": entity.velocity.heading_deg
                },
                "active": entity.active
            })

        return picture

    def get_status(self) -> dict:
        """Obtiene estado del módulo"""
        return {
            "active_engagements": len(self.combat_engine.get_active_engagements()),
            "weapons_in_flight": self.weapon_system.get_weapons_in_flight(),
            "radar_tracks": self.radar_simulator.get_track_count()
        }
