"""
Configuración global del sistema GAVILAN
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import json
from pathlib import Path


class SimulationMode(Enum):
    """Modos de simulación disponibles"""
    TRAINING = "training"
    EXERCISE = "exercise"
    WARGAME = "wargame"
    CTF = "ctf"


class DifficultyLevel(Enum):
    """Niveles de dificultad"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class GeographicArea:
    """Definición del área geográfica de operaciones"""
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    min_altitude_ft: float = 0
    max_altitude_ft: float = 60000
    terrain_type: str = "mixed"


@dataclass
class WeatherConfig:
    """Configuración meteorológica"""
    visibility_km: float = 10.0
    cloud_ceiling_ft: float = 25000
    wind_speed_kts: float = 10.0
    wind_direction_deg: float = 270.0
    precipitation: str = "none"
    turbulence_level: str = "light"


@dataclass
class SpaceWeatherConfig:
    """Configuración del clima espacial"""
    kp_index: float = 2.0
    solar_wind_speed: float = 400.0
    dst_index: float = -10.0
    proton_flux: float = 1.0
    xray_flux: float = 1e-6
    gps_degradation_factor: float = 1.0
    comm_degradation_factor: float = 1.0


@dataclass
class RulesOfEngagement:
    """Reglas de enfrentamiento"""
    weapons_free: bool = False
    weapons_tight: bool = True
    weapons_hold: bool = False
    identification_required: bool = True
    minimum_range_nm: float = 10.0
    max_collateral_damage: str = "low"
    civilian_areas_restricted: bool = True


@dataclass
class GavilanConfig:
    """Configuración principal del sistema GAVILAN"""

    # Identificación
    scenario_name: str = "Default Scenario"
    scenario_id: str = "SCN-001"

    # Modo de simulación
    mode: SimulationMode = SimulationMode.TRAINING
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

    # Tiempo
    simulation_speed: float = 1.0
    max_duration_hours: float = 4.0
    time_step_seconds: float = 1.0

    # Área geográfica
    geographic_area: GeographicArea = field(
        default_factory=lambda: GeographicArea(
            name="Default AO",
            center_lat=4.6097,
            center_lon=-74.0817,
            radius_km=500
        )
    )

    # Clima
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    space_weather: SpaceWeatherConfig = field(default_factory=SpaceWeatherConfig)

    # Reglas de enfrentamiento
    roe: RulesOfEngagement = field(default_factory=RulesOfEngagement)

    # Configuración técnica
    database_url: str = "sqlite:///gavilan.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Flags de módulos
    enable_cyber_module: bool = True
    enable_space_module: bool = True
    enable_ctf_module: bool = False

    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario"""
        return {
            "scenario_name": self.scenario_name,
            "scenario_id": self.scenario_id,
            "mode": self.mode.value,
            "difficulty": self.difficulty.value,
            "simulation_speed": self.simulation_speed,
            "max_duration_hours": self.max_duration_hours,
            "time_step_seconds": self.time_step_seconds,
            "geographic_area": {
                "name": self.geographic_area.name,
                "center_lat": self.geographic_area.center_lat,
                "center_lon": self.geographic_area.center_lon,
                "radius_km": self.geographic_area.radius_km,
            },
            "weather": {
                "visibility_km": self.weather.visibility_km,
                "cloud_ceiling_ft": self.weather.cloud_ceiling_ft,
                "wind_speed_kts": self.weather.wind_speed_kts,
            },
            "space_weather": {
                "kp_index": self.space_weather.kp_index,
                "solar_wind_speed": self.space_weather.solar_wind_speed,
            },
            "roe": {
                "weapons_free": self.roe.weapons_free,
                "identification_required": self.roe.identification_required,
            },
        }

    def save(self, filepath: str):
        """Guarda la configuración en archivo JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'GavilanConfig':
        """Carga configuración desde archivo JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = cls()
        config.scenario_name = data.get("scenario_name", config.scenario_name)
        config.scenario_id = data.get("scenario_id", config.scenario_id)

        if "mode" in data:
            config.mode = SimulationMode(data["mode"])
        if "difficulty" in data:
            config.difficulty = DifficultyLevel(data["difficulty"])

        return config
