"""
Módulo de inteligencia operacional
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum

from gavilan.core.events import Event, EventType, event_bus
from gavilan.core.entities import Position, Side
from gavilan.modules.intelligence.fusion import SensorFusion


class IntelConfidence(Enum):
    """Niveles de confianza"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


@dataclass
class FusedTrack:
    """Track fusionado de múltiples sensores"""
    track_id: str
    position: Position
    velocity: dict
    classification: str
    confidence: IntelConfidence
    sources: list
    last_update: datetime
    predicted_intent: str = ""


@dataclass
class CourseOfAction:
    """Curso de acción inferido"""
    coa_id: str
    entity_id: str
    description: str
    probability: float
    indicators: list
    timestamp: datetime


class IntelligenceModule:
    """Módulo de inteligencia operacional"""

    def __init__(self):
        self.event_bus = event_bus
        self.sensor_fusion = SensorFusion()
        self._fused_tracks: dict[str, FusedTrack] = {}
        self._inferred_coas: list[CourseOfAction] = []
        self._intel_products: list = []

    def update(self, dt: float, engine):
        """Actualiza inteligencia operacional"""
        # Fusionar datos de sensores
        self.sensor_fusion.process(dt, engine)

        # Actualizar tracks fusionados
        self._update_fused_tracks(engine)

        # Inferir cursos de acción
        self._infer_enemy_coas(engine)

    def _update_fused_tracks(self, engine):
        """Actualiza tracks fusionados"""
        # Obtener datos de múltiples fuentes
        radar_data = []
        sigint_data = []

        # Simulación: crear tracks fusionados de entidades enemigas
        red_entities = engine.get_entities_by_side(Side.RED)

        for entity in red_entities:
            if not entity.active:
                continue

            track_id = f"FT-{entity.entity_id[:8]}"

            confidence = IntelConfidence.MEDIUM
            sources = ["radar"]

            # Simular múltiples fuentes
            if hasattr(entity, 'rcs_m2') and entity.rcs_m2 > 5:
                sources.append("ir")
                confidence = IntelConfidence.HIGH

            fused = FusedTrack(
                track_id=track_id,
                position=entity.position,
                velocity={
                    "speed_kts": entity.velocity.speed_kts,
                    "heading": entity.velocity.heading_deg
                },
                classification=entity.entity_type.value,
                confidence=confidence,
                sources=sources,
                last_update=datetime.now()
            )

            self._fused_tracks[track_id] = fused

    def _infer_enemy_coas(self, engine):
        """Infiere cursos de acción del enemigo"""
        import uuid

        for track_id, track in self._fused_tracks.items():
            if track.confidence.value in ["low"]:
                continue

            # Análisis de comportamiento
            coa_type = "unknown"
            probability = 0.5

            # Inferir basado en velocidad y altitud
            if track.velocity["speed_kts"] > 500:
                if track.position.altitude_ft > 30000:
                    coa_type = "transit/penetration"
                    probability = 0.7
                else:
                    coa_type = "attack_run"
                    probability = 0.8
            elif track.velocity["speed_kts"] < 200:
                coa_type = "patrol/loiter"
                probability = 0.6

            coa = CourseOfAction(
                coa_id=f"COA-{str(uuid.uuid4())[:8]}",
                entity_id=track_id,
                description=coa_type,
                probability=probability,
                indicators=[f"speed={track.velocity['speed_kts']}", f"alt={track.position.altitude_ft}"],
                timestamp=datetime.now()
            )

            # Mantener solo COAs recientes
            self._inferred_coas = [
                c for c in self._inferred_coas
                if (datetime.now() - c.timestamp).total_seconds() < 300
            ]
            self._inferred_coas.append(coa)

    def get_common_operating_picture(self) -> dict:
        """Obtiene COP (Common Operating Picture)"""
        return {
            "timestamp": datetime.now().isoformat(),
            "tracks": [
                {
                    "track_id": t.track_id,
                    "position": {
                        "lat": t.position.latitude,
                        "lon": t.position.longitude,
                        "alt": t.position.altitude_ft
                    },
                    "velocity": t.velocity,
                    "classification": t.classification,
                    "confidence": t.confidence.value,
                    "sources": t.sources
                }
                for t in self._fused_tracks.values()
            ],
            "threat_assessment": self._get_threat_summary()
        }

    def _get_threat_summary(self) -> dict:
        """Obtiene resumen de amenazas"""
        total = len(self._fused_tracks)
        by_class = {}

        for track in self._fused_tracks.values():
            cls = track.classification
            by_class[cls] = by_class.get(cls, 0) + 1

        return {
            "total_tracks": total,
            "by_classification": by_class,
            "high_confidence": sum(
                1 for t in self._fused_tracks.values()
                if t.confidence in [IntelConfidence.HIGH, IntelConfidence.CONFIRMED]
            )
        }

    def get_enemy_coas(self) -> list[dict]:
        """Obtiene cursos de acción inferidos"""
        return [
            {
                "coa_id": c.coa_id,
                "entity": c.entity_id,
                "description": c.description,
                "probability": c.probability,
                "indicators": c.indicators
            }
            for c in self._inferred_coas
        ]

    def get_status(self) -> dict:
        """Obtiene estado del módulo"""
        return {
            "fused_tracks": len(self._fused_tracks),
            "inferred_coas": len(self._inferred_coas),
            "intel_products": len(self._intel_products)
        }
