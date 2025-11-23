"""
Simulador de radar
"""

from dataclasses import dataclass, field
from typing import Optional
import math
import random

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Radar, Aircraft, Side, EntityType


@dataclass
class RadarTrack:
    """Track de radar"""
    track_id: str
    target_id: str
    radar_id: str
    quality: float  # 0-1
    age: float  # segundos desde última actualización

    # Datos medidos
    range_km: float
    azimuth_deg: float
    altitude_ft: float
    speed_kts: float
    heading_deg: float

    # Clasificación
    classification: str = "unknown"
    iff_response: str = "none"


class RadarSimulator:
    """Simula detección radar"""

    def __init__(self):
        self.event_bus = event_bus
        self._tracks: dict[str, RadarTrack] = {}
        self._noise_level: float = 0.1

    def update(self, dt: float, engine):
        """Actualiza detecciones de radar"""
        # Obtener radares propios
        radars = [
            e for e in engine.get_entities_by_type(EntityType.RADAR)
            if e.side == Side.BLUE and e.operational
        ]

        # Obtener todos los objetivos potenciales
        targets = [
            e for e in engine._entities.values()
            if e.entity_type == EntityType.AIRCRAFT and e.active
        ]

        # Procesar detecciones
        for radar in radars:
            for target in targets:
                self._process_detection(radar, target, dt)

        # Degradar tracks antiguos
        for track_id in list(self._tracks.keys()):
            track = self._tracks[track_id]
            track.age += dt
            track.quality = max(0, track.quality - 0.01 * dt)

            if track.quality < 0.1:
                del self._tracks[track_id]
                self.event_bus.publish(Event(
                    event_type=EventType.RADAR_LOST,
                    source="radar",
                    data={"track_id": track_id}
                ))

    def _process_detection(self, radar: Radar, target, dt: float):
        """Procesa posible detección de un objetivo"""
        can_detect, probability = radar.can_detect(target)

        if not can_detect:
            return

        # Tirar dados para detección
        if random.random() > probability:
            return

        # Calcular parámetros de detección
        range_km = radar.position.distance_to(target.position)
        azimuth = radar.position.bearing_to(target.position)

        # Añadir errores de medición
        range_error = random.gauss(0, radar.accuracy_range_m / 1000)
        azimuth_error = random.gauss(0, radar.accuracy_azimuth_deg)

        track_id = f"{radar.entity_id}_{target.entity_id}"

        if track_id in self._tracks:
            # Actualizar track existente
            track = self._tracks[track_id]
            track.range_km = range_km + range_error
            track.azimuth_deg = azimuth + azimuth_error
            track.altitude_ft = target.position.altitude_ft
            track.speed_kts = target.velocity.speed_kts
            track.heading_deg = target.velocity.heading_deg
            track.quality = min(1.0, track.quality + 0.1)
            track.age = 0

            self.event_bus.publish(Event(
                event_type=EventType.RADAR_TRACK,
                source="radar",
                data={"track_id": track_id, "quality": track.quality}
            ))
        else:
            # Nuevo contacto
            track = RadarTrack(
                track_id=track_id,
                target_id=target.entity_id,
                radar_id=radar.entity_id,
                quality=probability,
                age=0,
                range_km=range_km + range_error,
                azimuth_deg=azimuth + azimuth_error,
                altitude_ft=target.position.altitude_ft,
                speed_kts=target.velocity.speed_kts,
                heading_deg=target.velocity.heading_deg
            )

            # Determinar clasificación
            if target.side == Side.BLUE:
                track.classification = "friendly"
                track.iff_response = "valid"
            elif target.side == Side.RED:
                track.classification = "hostile"
                track.iff_response = "none"
            else:
                track.classification = "unknown"

            self._tracks[track_id] = track

            self.event_bus.publish(Event(
                event_type=EventType.RADAR_CONTACT,
                source="radar",
                data={
                    "track_id": track_id,
                    "range_km": track.range_km,
                    "azimuth": track.azimuth_deg,
                    "classification": track.classification
                }
            ))

    def apply_jamming(self, radar_id: str, effectiveness: float):
        """Aplica jamming a un radar"""
        # Degradar tracks de ese radar
        for track in self._tracks.values():
            if track.radar_id == radar_id:
                track.quality *= (1 - effectiveness)

        self.event_bus.publish(Event(
            event_type=EventType.RADAR_JAM,
            source="radar",
            data={"radar_id": radar_id, "effectiveness": effectiveness}
        ))

    def get_radar_picture(self) -> list[dict]:
        """Obtiene imagen radar actual"""
        return [
            {
                "track_id": t.track_id,
                "range_km": t.range_km,
                "azimuth_deg": t.azimuth_deg,
                "altitude_ft": t.altitude_ft,
                "speed_kts": t.speed_kts,
                "heading_deg": t.heading_deg,
                "classification": t.classification,
                "quality": t.quality,
                "iff": t.iff_response
            }
            for t in self._tracks.values()
        ]

    def get_track_count(self) -> int:
        """Obtiene número de tracks activos"""
        return len(self._tracks)
