"""
Fusión de sensores
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SensorType(Enum):
    """Tipos de sensores"""
    RADAR = "radar"
    EO_IR = "eo_ir"
    ADS_B = "ads_b"
    SIGINT = "sigint"
    ELINT = "elint"
    ACOUSTIC = "acoustic"


@dataclass
class SensorReport:
    """Reporte de un sensor"""
    sensor_id: str
    sensor_type: SensorType
    target_id: str
    confidence: float
    data: dict


class SensorFusion:
    """Sistema de fusión de sensores"""

    def __init__(self):
        self._sensor_reports: list[SensorReport] = []
        self._correlation_threshold: float = 0.7

    def process(self, dt: float, engine):
        """Procesa datos de sensores"""
        # En implementación completa: correlacionar reports
        pass

    def add_report(self, report: SensorReport):
        """Añade reporte de sensor"""
        self._sensor_reports.append(report)

    def correlate_reports(self) -> list[dict]:
        """Correlaciona reportes de múltiples sensores"""
        correlated = []

        # Agrupar por target_id
        by_target = {}
        for report in self._sensor_reports:
            if report.target_id not in by_target:
                by_target[report.target_id] = []
            by_target[report.target_id].append(report)

        # Fusionar
        for target_id, reports in by_target.items():
            if len(reports) >= 2:
                confidence = min(0.99, sum(r.confidence for r in reports) / len(reports) * 1.2)
            else:
                confidence = reports[0].confidence if reports else 0

            correlated.append({
                "target_id": target_id,
                "sources": [r.sensor_type.value for r in reports],
                "fused_confidence": confidence
            })

        return correlated
