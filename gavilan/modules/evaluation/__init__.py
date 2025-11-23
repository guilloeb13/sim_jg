"""
Módulo de Evaluación y Puntaje
==============================

Métricas y evaluación:
- Métricas por sección (A1-A6)
- Cumplimiento del ATO
- Resiliencia ante ataques
"""

from gavilan.modules.evaluation.eval_module import EvaluationModule
from gavilan.modules.evaluation.scoring import ScoringEngine

__all__ = [
    "EvaluationModule",
    "ScoringEngine",
]
