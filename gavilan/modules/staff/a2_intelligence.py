"""
A2 - Sección de Inteligencia
============================

Gestiona:
- Reconocimiento y sensores
- SIGINT, IMINT
- Estimación de amenazas
- Detección de rutas enemigas
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import math

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Entity, Side, Position


class IntelSource(Enum):
    """Fuentes de inteligencia"""
    RADAR = "radar"
    SIGINT = "sigint"
    IMINT = "imint"
    HUMINT = "humint"
    OSINT = "osint"
    ELINT = "elint"
    ADS_B = "ads_b"
    EO_IR = "eo_ir"


class ThreatLevel(Enum):
    """Niveles de amenaza"""
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IntelReport:
    """Reporte de inteligencia"""
    report_id: str
    timestamp: datetime
    source: IntelSource
    reliability: float  # 0-1
    content: dict
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    expires_at: datetime = None


@dataclass
class TrackedEntity:
    """Entidad rastreada por inteligencia"""
    entity_id: str
    first_detected: datetime
    last_updated: datetime
    position: Position
    velocity_estimate: dict
    classification: str
    confidence: float  # 0-1
    threat_level: ThreatLevel
    sources: list[IntelSource] = field(default_factory=list)
    track_quality: float = 1.0


class IntelligenceSection:
    """Sección A2 - Gestión de Inteligencia"""

    def __init__(self):
        self.event_bus = event_bus
        self._reports: list[IntelReport] = []
        self._tracked_entities: dict[str, TrackedEntity] = {}
        self._threat_assessment: dict = {}
        self._sensor_coverage: dict = {}

    def update(self, dt: float, engine):
        """Actualiza la sección de inteligencia"""
        # Procesar detecciones de radares
        self._process_radar_detections(engine)

        # Actualizar calidad de tracks
        self._update_track_quality(dt)

        # Evaluar amenazas
        self._assess_threats(engine)

        # Limpiar reportes expirados
        self._cleanup_expired_reports()

    def _process_radar_detections(self, engine):
        """Procesa detecciones de radares propios"""
        from gavilan.core.entities import Radar, EntityType

        radars = engine.get_entities_by_type(EntityType.RADAR)
        blue_radars = [r for r in radars if r.side == Side.BLUE and r.operational]

        red_entities = engine.get_entities_by_side(Side.RED)

        for radar in blue_radars:
            for target in red_entities:
                can_detect, probability = radar.can_detect(target)

                if can_detect:
                    self._update_track(
                        target,
                        IntelSource.RADAR,
                        probability,
                        radar.entity_id
                    )

    def _update_track(
        self,
        entity: Entity,
        source: IntelSource,
        confidence: float,
        sensor_id: str
    ):
        """Actualiza o crea track de una entidad"""
        now = datetime.now()

        if entity.entity_id in self._tracked_entities:
            track = self._tracked_entities[entity.entity_id]
            track.last_updated = now
            track.position = entity.position
            track.confidence = min(1.0, track.confidence + confidence * 0.1)

            if source not in track.sources:
                track.sources.append(source)

            track.track_quality = 1.0

        else:
            track = TrackedEntity(
                entity_id=entity.entity_id,
                first_detected=now,
                last_updated=now,
                position=entity.position,
                velocity_estimate={
                    "speed_kts": entity.velocity.speed_kts,
                    "heading_deg": entity.velocity.heading_deg
                },
                classification=entity.entity_type.value,
                confidence=confidence,
                threat_level=ThreatLevel.UNKNOWN,
                sources=[source]
            )

            self._tracked_entities[entity.entity_id] = track

            # Publicar evento de nuevo contacto
            self.event_bus.publish(Event(
                event_type=EventType.INTEL_UPDATE,
                source="A2",
                data={
                    "type": "new_track",
                    "entity_id": entity.entity_id,
                    "classification": entity.entity_type.value
                }
            ))

    def _update_track_quality(self, dt: float):
        """Degrada calidad de tracks sin actualización"""
        decay_rate = 0.1  # Por segundo

        for track in self._tracked_entities.values():
            track.track_quality = max(0, track.track_quality - decay_rate * dt)

            if track.track_quality < 0.3:
                track.confidence *= 0.95

    def _assess_threats(self, engine):
        """Evalúa nivel de amenaza de entidades rastreadas"""
        blue_assets = engine.get_entities_by_side(Side.BLUE)

        for track in self._tracked_entities.values():
            # Calcular distancia mínima a activos propios
            min_distance = float('inf')
            for asset in blue_assets:
                dist = asset.position.distance_to(track.position)
                min_distance = min(min_distance, dist)

            # Determinar nivel de amenaza
            if track.classification in ["aircraft", "missile"]:
                if min_distance < 50:
                    track.threat_level = ThreatLevel.CRITICAL
                elif min_distance < 150:
                    track.threat_level = ThreatLevel.HIGH
                elif min_distance < 300:
                    track.threat_level = ThreatLevel.MEDIUM
                else:
                    track.threat_level = ThreatLevel.LOW
            elif track.classification == "sam":
                if min_distance < 100:
                    track.threat_level = ThreatLevel.HIGH
                else:
                    track.threat_level = ThreatLevel.MEDIUM

    def _cleanup_expired_reports(self):
        """Limpia reportes expirados"""
        now = datetime.now()
        self._reports = [
            r for r in self._reports
            if r.expires_at is None or r.expires_at > now
        ]

        # Eliminar tracks muy degradados
        to_remove = [
            tid for tid, track in self._tracked_entities.items()
            if track.track_quality < 0.1
        ]
        for tid in to_remove:
            del self._tracked_entities[tid]

    def add_intel_report(
        self,
        source: IntelSource,
        content: dict,
        reliability: float = 0.8,
        threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    ):
        """Añade un reporte de inteligencia"""
        import uuid

        report = IntelReport(
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            source=source,
            reliability=reliability,
            content=content,
            threat_level=threat_level
        )

        self._reports.append(report)

        self.event_bus.publish(Event(
            event_type=EventType.INTEL_UPDATE,
            source="A2",
            data={"report_id": report.report_id, "source": source.value}
        ))

    def handle_comm_event(self, event: Event):
        """Maneja eventos de comunicaciones"""
        # Registrar posible SIGINT
        if event.event_type == EventType.COMM_FAILURE:
            self.add_intel_report(
                source=IntelSource.SIGINT,
                content={
                    "type": "communication_anomaly",
                    "details": event.data
                },
                reliability=0.6,
                threat_level=ThreatLevel.MEDIUM
            )

    def assess_area(self, area: dict) -> dict:
        """Evalúa un área específica"""
        center = Position(
            latitude=area.get("lat", 0),
            longitude=area.get("lon", 0),
            altitude_ft=0
        )
        radius = area.get("radius_km", 100)

        threats_in_area = []
        for track in self._tracked_entities.values():
            dist = center.distance_to(track.position)
            if dist <= radius:
                threats_in_area.append({
                    "entity_id": track.entity_id,
                    "classification": track.classification,
                    "threat_level": track.threat_level.value,
                    "distance_km": dist
                })

        # Calcular nivel de amenaza del área
        if not threats_in_area:
            area_threat = ThreatLevel.LOW
        elif any(t["threat_level"] == "critical" for t in threats_in_area):
            area_threat = ThreatLevel.CRITICAL
        elif any(t["threat_level"] == "high" for t in threats_in_area):
            area_threat = ThreatLevel.HIGH
        else:
            area_threat = ThreatLevel.MEDIUM

        return {
            "area": area,
            "threats": threats_in_area,
            "threat_level": area_threat.value,
            "recommendation": self._get_recommendation(area_threat)
        }

    def _get_recommendation(self, threat_level: ThreatLevel) -> str:
        """Genera recomendación basada en amenaza"""
        recommendations = {
            ThreatLevel.UNKNOWN: "Aumentar reconocimiento del área",
            ThreatLevel.LOW: "Operaciones normales permitidas",
            ThreatLevel.MEDIUM: "Precaución, escoltas recomendadas",
            ThreatLevel.HIGH: "Evitar área o preparar SEAD",
            ThreatLevel.CRITICAL: "Área restringida, amenaza inmediata"
        }
        return recommendations.get(threat_level, "Sin recomendación")

    def get_threat_picture(self) -> list[dict]:
        """Obtiene imagen de amenazas actual"""
        return [
            {
                "entity_id": t.entity_id,
                "position": {
                    "lat": t.position.latitude,
                    "lon": t.position.longitude,
                    "alt": t.position.altitude_ft
                },
                "classification": t.classification,
                "threat_level": t.threat_level.value,
                "confidence": t.confidence,
                "sources": [s.value for s in t.sources]
            }
            for t in self._tracked_entities.values()
        ]

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        by_threat = {}
        for t in self._tracked_entities.values():
            level = t.threat_level.value
            by_threat[level] = by_threat.get(level, 0) + 1

        return {
            "tracked_entities": len(self._tracked_entities),
            "active_reports": len(self._reports),
            "by_threat_level": by_threat,
            "avg_track_quality": sum(
                t.track_quality for t in self._tracked_entities.values()
            ) / max(1, len(self._tracked_entities))
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación de inteligencia"""
        if not self._tracked_entities:
            return 0.5  # Sin tracks, estado intermedio

        avg_quality = sum(
            t.track_quality for t in self._tracked_entities.values()
        ) / len(self._tracked_entities)

        avg_confidence = sum(
            t.confidence for t in self._tracked_entities.values()
        ) / len(self._tracked_entities)

        return (avg_quality * 0.5 + avg_confidence * 0.5)
