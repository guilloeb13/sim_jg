"""
Módulo de evaluación y puntaje
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from gavilan.core.events import EventType, event_bus
from gavilan.modules.evaluation.scoring import ScoringEngine


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento"""
    # Operaciones
    missions_planned: int = 0
    missions_executed: int = 0
    missions_successful: int = 0
    missions_failed: int = 0

    # Combate
    aircraft_lost: int = 0
    aircraft_damaged: int = 0
    enemy_destroyed: int = 0
    weapons_expended: int = 0

    # Logística
    sortie_rate: float = 0.0
    maintenance_efficiency: float = 0.0

    # Ciberdefensa
    attacks_blocked: int = 0
    attacks_successful: int = 0
    systems_compromised: int = 0
    recovery_time_avg: float = 0.0


class EvaluationModule:
    """Módulo de evaluación del ejercicio"""

    def __init__(self):
        self.event_bus = event_bus
        self.scoring_engine = ScoringEngine()
        self.metrics = PerformanceMetrics()

        self._section_scores: dict = {
            "A1": 0.0,
            "A2": 0.0,
            "A3": 0.0,
            "A4": 0.0,
            "A5": 0.0,
            "A6": 0.0
        }

        self._events_log: list = []
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Configura handlers de eventos para métricas"""
        self.event_bus.subscribe(
            EventType.MISSION_COMPLETE,
            self._on_mission_complete
        )
        self.event_bus.subscribe(
            EventType.MISSION_ABORT,
            self._on_mission_abort
        )
        self.event_bus.subscribe(
            EventType.AIRCRAFT_DESTROY,
            self._on_aircraft_destroyed
        )
        self.event_bus.subscribe(
            EventType.CYBER_ATTACK,
            self._on_cyber_attack
        )

    def _on_mission_complete(self, event):
        """Handler para misión completada"""
        self.metrics.missions_executed += 1
        self.metrics.missions_successful += 1
        self._log_event("mission_complete", event.data)

    def _on_mission_abort(self, event):
        """Handler para misión abortada"""
        self.metrics.missions_executed += 1
        self.metrics.missions_failed += 1
        self._log_event("mission_abort", event.data)

    def _on_aircraft_destroyed(self, event):
        """Handler para aeronave destruida"""
        data = event.data
        # Determinar si es propia o enemiga
        if "killer" in data:
            self.metrics.enemy_destroyed += 1
        else:
            self.metrics.aircraft_lost += 1
        self._log_event("aircraft_destroyed", data)

    def _on_cyber_attack(self, event):
        """Handler para ataque cibernético"""
        data = event.data
        if data.get("blocked", False):
            self.metrics.attacks_blocked += 1
        else:
            self.metrics.attacks_successful += 1
        self._log_event("cyber_attack", data)

    def _log_event(self, event_type: str, data: dict):
        """Registra evento para análisis"""
        self._events_log.append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })

    def update(self, dt: float, engine):
        """Actualiza evaluaciones"""
        # Calcular puntajes por sección
        staff = engine._modules.get("staff")
        if staff:
            self._section_scores["A1"] = staff.a1_personnel.get_readiness() * 100
            self._section_scores["A2"] = staff.a2_intelligence.get_readiness() * 100
            self._section_scores["A3"] = staff.a3_operations.get_readiness() * 100
            self._section_scores["A4"] = staff.a4_logistics.get_readiness() * 100
            self._section_scores["A5"] = staff.a5_communications.get_readiness() * 100
            self._section_scores["A6"] = staff.a6_cyber.get_readiness() * 100

    def calculate_final_score(self) -> dict:
        """Calcula puntaje final del ejercicio"""
        # Puntaje base por secciones
        section_avg = sum(self._section_scores.values()) / len(self._section_scores)

        # Puntaje por operaciones
        if self.metrics.missions_executed > 0:
            ops_score = (self.metrics.missions_successful / self.metrics.missions_executed) * 100
        else:
            ops_score = 0

        # Puntaje por bajas
        if self.metrics.aircraft_lost > 0:
            casualty_penalty = min(50, self.metrics.aircraft_lost * 10)
        else:
            casualty_penalty = 0

        # Puntaje por ciberdefensa
        total_cyber = self.metrics.attacks_blocked + self.metrics.attacks_successful
        if total_cyber > 0:
            cyber_score = (self.metrics.attacks_blocked / total_cyber) * 100
        else:
            cyber_score = 100

        # Puntaje final
        final_score = (
            section_avg * 0.3 +
            ops_score * 0.3 +
            cyber_score * 0.2 +
            (100 - casualty_penalty) * 0.2
        )

        return {
            "final_score": round(final_score, 1),
            "grade": self._score_to_grade(final_score),
            "breakdown": {
                "section_average": round(section_avg, 1),
                "operations": round(ops_score, 1),
                "cyber_defense": round(cyber_score, 1),
                "casualties_penalty": round(casualty_penalty, 1)
            },
            "section_scores": {k: round(v, 1) for k, v in self._section_scores.items()}
        }

    def _score_to_grade(self, score: float) -> str:
        """Convierte puntaje a calificación"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def get_performance_report(self) -> dict:
        """Genera reporte de rendimiento"""
        return {
            "metrics": {
                "missions": {
                    "planned": self.metrics.missions_planned,
                    "executed": self.metrics.missions_executed,
                    "successful": self.metrics.missions_successful,
                    "failed": self.metrics.missions_failed
                },
                "combat": {
                    "aircraft_lost": self.metrics.aircraft_lost,
                    "enemy_destroyed": self.metrics.enemy_destroyed,
                    "weapons_expended": self.metrics.weapons_expended
                },
                "cyber": {
                    "attacks_blocked": self.metrics.attacks_blocked,
                    "attacks_successful": self.metrics.attacks_successful
                }
            },
            "scores": self.calculate_final_score(),
            "events_count": len(self._events_log)
        }

    def get_status(self) -> dict:
        """Obtiene estado del módulo"""
        return {
            "events_logged": len(self._events_log),
            "current_scores": self._section_scores
        }
