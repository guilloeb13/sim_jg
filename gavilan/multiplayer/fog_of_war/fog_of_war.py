"""
Sistema de Fog of War para GAVILAN Multiplayer

Cada bando solo ve:
1. Unidades propias (siempre)
2. Detecciones de sensores (radares, AWACS, SIGINT, etc.)
3. Inteligencia con delay y calidad variable
4. Estimaciones cuando se pierde contacto
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID
import math

from gavilan.core.entities import Entity, Side


@dataclass
class Track:
    """
    Track de una entidad enemiga detectada

    Representa información imperfecta sobre una entidad enemiga.
    """
    entity_id: UUID
    classification: str  # "AIRCRAFT", "MISSILE", "UNKNOWN", etc.
    position_lat: float
    position_lon: float
    altitude_ft: float

    # Incertidumbre (en km para posición, pies para altitud)
    uncertainty_km: float = 1.0
    altitude_uncertainty_ft: float = 1000.0

    # Metadata
    last_seen: datetime = field(default_factory=datetime.now)
    first_detected: datetime = field(default_factory=datetime.now)
    detection_source: str = "RADAR"  # RADAR, AWACS, SIGINT, VISUAL, etc.
    confidence: float = 0.8  # 0-1, qué tan confiable es este track

    # Velocidad estimada (puede ser inexacta)
    speed_kts: Optional[float] = None
    heading_deg: Optional[float] = None

    # Identificación (puede ser incorrecta)
    iff_code: Optional[str] = None  # IFF response si existe
    threat_level: str = "UNKNOWN"  # LOW, MEDIUM, HIGH, CRITICAL

    def age_seconds(self) -> float:
        """Edad del track en segundos"""
        return (datetime.now() - self.last_seen).total_seconds()

    def update_position(
        self,
        lat: float,
        lon: float,
        alt: float,
        uncertainty_km: float,
        source: str,
    ):
        """Actualiza posición del track con nueva detección"""
        # Promediar con posición anterior para suavizar
        alpha = 0.7  # Weight para nueva detección
        self.position_lat = alpha * lat + (1 - alpha) * self.position_lat
        self.position_lon = alpha * lon + (1 - alpha) * self.position_lon
        self.altitude_ft = alpha * alt + (1 - alpha) * self.altitude_ft

        # Reducir incertidumbre con nueva detección
        self.uncertainty_km = min(self.uncertainty_km, uncertainty_km)
        self.last_seen = datetime.now()
        self.detection_source = source

    def extrapolate_position(self) -> tuple[float, float, float]:
        """
        Extrapola posición actual basado en última velocidad conocida

        Returns:
            (lat, lon, alt) estimados
        """
        if not self.speed_kts or not self.heading_deg:
            return self.position_lat, self.position_lon, self.altitude_ft

        # Tiempo desde última detección
        dt_seconds = self.age_seconds()

        # Distancia recorrida (aproximación simple)
        dist_nm = (self.speed_kts / 3600) * dt_seconds
        dist_km = dist_nm * 1.852

        # Convertir heading a componentes
        heading_rad = math.radians(self.heading_deg)

        # Aproximación simple (flat earth, suficiente para distancias cortas)
        # 1 grado lat ≈ 111 km
        # 1 grado lon ≈ 111 km * cos(lat)
        delta_lat = (dist_km / 111.0) * math.cos(heading_rad)
        delta_lon = (dist_km / (111.0 * math.cos(math.radians(self.position_lat)))) * math.sin(heading_rad)

        est_lat = self.position_lat + delta_lat
        est_lon = self.position_lon + delta_lon

        # Aumentar incertidumbre con el tiempo
        self.uncertainty_km += dt_seconds * 0.05  # 0.05 km/s = 3 km/min

        return est_lat, est_lon, self.altitude_ft


class FogOfWar:
    """
    Gestiona visibilidad y fog of war para un bando específico
    """

    def __init__(self, side: Side):
        self.side = side
        self.tracks: Dict[UUID, Track] = {}  # entity_id -> Track

        # Configuración
        self.max_track_age_seconds = 300  # 5 minutos, luego se descarta
        self.uncertainty_growth_rate = 0.05  # km/s

    def update(self, all_entities: List[Entity], sensors: List[Entity]):
        """
        Actualiza fog of war basado en entidades y sensores disponibles

        Args:
            all_entities: Todas las entidades en el juego (ground truth)
            sensors: Sensores propios (radares, AWACS, etc.)
        """
        detected_ids = set()

        # 1. Procesar detecciones de cada sensor
        for sensor in sensors:
            if not self._is_sensor_operational(sensor):
                continue

            # Obtener detecciones de este sensor
            detections = self._get_sensor_detections(sensor, all_entities)

            for entity in detections:
                detected_ids.add(entity.id)
                self._update_or_create_track(entity, sensor)

        # 2. Degradar tracks no actualizados
        self._degrade_old_tracks(detected_ids)

        # 3. Eliminar tracks muy antiguos
        self._cleanup_stale_tracks()

    def get_visible_entities(self, all_entities: List[Entity]) -> List[Entity]:
        """
        Retorna entidades visibles para este bando (con fog of war aplicado)

        Args:
            all_entities: Todas las entidades (ground truth)

        Returns:
            Lista de entidades visibles (propias + tracks de enemigos)
        """
        visible = []

        # 1. Todas las entidades propias (siempre visibles, exactas)
        for entity in all_entities:
            if entity.side == self.side:
                visible.append(entity)

        # 2. Tracks de entidades enemigas (con incertidumbre)
        for track in self.tracks.values():
            # Crear entidad "fantasma" basada en el track
            entity = self._track_to_entity(track)
            visible.append(entity)

        return visible

    def get_track(self, entity_id: UUID) -> Optional[Track]:
        """Obtiene track de una entidad específica"""
        return self.tracks.get(entity_id)

    def get_all_tracks(self) -> List[Track]:
        """Retorna todos los tracks activos"""
        return list(self.tracks.values())

    def _is_sensor_operational(self, sensor: Entity) -> bool:
        """Verifica si sensor está operacional"""
        # TODO: Integrar con estado de sensor (jammingm, daño, etc.)
        return hasattr(sensor, 'operational') and sensor.operational

    def _get_sensor_detections(
        self,
        sensor: Entity,
        all_entities: List[Entity]
    ) -> List[Entity]:
        """
        Simula detecciones de un sensor

        Args:
            sensor: Sensor (radar, AWACS, etc.)
            all_entities: Todas las entidades

        Returns:
            Entidades detectadas por este sensor
        """
        detections = []

        for entity in all_entities:
            # No detectar entidades propias
            if entity.side == self.side:
                continue

            # Verificar si está en rango
            distance_km = self._calculate_distance(sensor, entity)

            # Para radares, usar can_detect si disponible
            if hasattr(sensor, 'can_detect'):
                if sensor.can_detect(entity):
                    detections.append(entity)
            else:
                # Modelo simple: detección basada en rango
                # TODO: Mejorar con RCS, jamming, etc.
                max_range_km = getattr(sensor, 'max_range_km', 200)
                if distance_km <= max_range_km:
                    detections.append(entity)

        return detections

    def _update_or_create_track(self, entity: Entity, sensor: Entity):
        """Crea o actualiza track para una entidad detectada"""
        sensor_type = type(sensor).__name__

        # Calcular incertidumbre basada en sensor
        uncertainty_km = self._calculate_uncertainty(sensor, entity)

        if entity.id in self.tracks:
            # Actualizar track existente
            track = self.tracks[entity.id]
            track.update_position(
                entity.position.latitude,
                entity.position.longitude,
                entity.altitude_ft,
                uncertainty_km,
                sensor_type,
            )

            # Actualizar velocidad si disponible
            if hasattr(entity, 'speed_kts') and hasattr(entity, 'heading_deg'):
                track.speed_kts = entity.speed_kts
                track.heading_deg = entity.heading_deg

        else:
            # Crear nuevo track
            track = Track(
                entity_id=entity.id,
                classification=type(entity).__name__,
                position_lat=entity.position.latitude,
                position_lon=entity.position.longitude,
                altitude_ft=entity.altitude_ft,
                uncertainty_km=uncertainty_km,
                detection_source=sensor_type,
                confidence=0.8,
                speed_kts=getattr(entity, 'speed_kts', None),
                heading_deg=getattr(entity, 'heading_deg', None),
            )
            self.tracks[entity.id] = track

    def _calculate_uncertainty(self, sensor: Entity, target: Entity) -> float:
        """
        Calcula incertidumbre de detección en km

        Factores:
        - Distancia al sensor
        - Tipo de sensor
        - RCS del objetivo
        - Jamming
        """
        distance_km = self._calculate_distance(sensor, target)

        # Base uncertainty: crece con distancia
        base_uncertainty = 0.5 + (distance_km / 100.0)  # 0.5km a 0km, 2.5km a 200km

        # TODO: Ajustar por RCS, jamming, etc.

        return base_uncertainty

    def _calculate_distance(self, entity1: Entity, entity2: Entity) -> float:
        """Calcula distancia entre dos entidades en km"""
        # Haversine formula (aproximación esférica)
        lat1 = math.radians(entity1.position.latitude)
        lon1 = math.radians(entity1.position.longitude)
        lat2 = math.radians(entity2.position.latitude)
        lon2 = math.radians(entity2.position.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radio de la Tierra en km
        R = 6371.0

        return R * c

    def _degrade_old_tracks(self, detected_ids: Set[UUID]):
        """Degrada tracks que no fueron actualizados"""
        for track_id, track in self.tracks.items():
            if track_id not in detected_ids:
                # No fue detectado este tick, aumentar incertidumbre
                age = track.age_seconds()
                track.uncertainty_km += age * self.uncertainty_growth_rate
                track.confidence *= 0.95  # Reducir confianza

    def _cleanup_stale_tracks(self):
        """Elimina tracks muy antiguos"""
        stale = []
        for track_id, track in self.tracks.items():
            if track.age_seconds() > self.max_track_age_seconds:
                stale.append(track_id)

        for track_id in stale:
            del self.tracks[track_id]

    def _track_to_entity(self, track: Track) -> Entity:
        """
        Convierte Track a Entity (con información imperfecta)

        IMPORTANTE: Esta entidad NO es ground truth, es una estimación
        """
        # Extrapolar posición
        lat, lon, alt = track.extrapolate_position()

        # Crear entidad "fantasma"
        # TODO: Usar clase apropiada según classification
        from gavilan.core.entities import Entity as BaseEntity

        # Crear entity básica con información del track
        entity = BaseEntity(
            id=track.entity_id,
            type=track.classification,
            side=Side.RED if self.side == Side.BLUE else Side.BLUE,
        )

        # Posición extrapolada (NO exacta)
        entity.position.latitude = lat
        entity.position.longitude = lon
        entity.altitude_ft = alt

        # Metadata de track
        entity._is_track = True
        entity._track_uncertainty_km = track.uncertainty_km
        entity._track_confidence = track.confidence
        entity._track_age_seconds = track.age_seconds()

        return entity
