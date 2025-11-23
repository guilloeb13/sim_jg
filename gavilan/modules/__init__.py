"""
Módulos del sistema GAVILAN
"""

from gavilan.modules.scenario import ScenarioManager
from gavilan.modules.staff import StaffModule
from gavilan.modules.space import SpaceWeatherModule
from gavilan.modules.cyber import CyberModule
from gavilan.modules.air_simulation import AirSimulationModule
from gavilan.modules.intelligence import IntelligenceModule
from gavilan.modules.evaluation import EvaluationModule
from gavilan.modules.training import TrainingModule

__all__ = [
    "ScenarioManager",
    "StaffModule",
    "SpaceWeatherModule",
    "CyberModule",
    "AirSimulationModule",
    "IntelligenceModule",
    "EvaluationModule",
    "TrainingModule",
]
