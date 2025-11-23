"""
Motor de puntaje
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreCategory:
    """Categoría de puntaje"""
    name: str
    weight: float
    max_score: float
    current_score: float = 0


class ScoringEngine:
    """Motor de cálculo de puntajes"""

    def __init__(self):
        self.categories: dict[str, ScoreCategory] = {
            "operations": ScoreCategory("Operaciones", 0.30, 100),
            "logistics": ScoreCategory("Logística", 0.15, 100),
            "intelligence": ScoreCategory("Inteligencia", 0.15, 100),
            "cyber": ScoreCategory("Ciberdefensa", 0.15, 100),
            "communications": ScoreCategory("Comunicaciones", 0.10, 100),
            "personnel": ScoreCategory("Personal", 0.10, 100),
            "objectives": ScoreCategory("Objetivos", 0.05, 100)
        }

    def update_score(self, category: str, score: float):
        """Actualiza puntaje de una categoría"""
        if category in self.categories:
            self.categories[category].current_score = min(
                self.categories[category].max_score,
                max(0, score)
            )

    def calculate_weighted_total(self) -> float:
        """Calcula puntaje total ponderado"""
        total = 0
        for cat in self.categories.values():
            total += cat.current_score * cat.weight
        return total

    def get_breakdown(self) -> dict:
        """Obtiene desglose de puntajes"""
        return {
            name: {
                "score": cat.current_score,
                "max": cat.max_score,
                "weight": cat.weight,
                "weighted": cat.current_score * cat.weight
            }
            for name, cat in self.categories.items()
        }
