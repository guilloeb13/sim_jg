"""
Sistema de clima meteorológico
"""

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from gavilan.core.config import GeographicArea


@dataclass
class WeatherConditions:
    """Condiciones meteorológicas actuales"""
    temperature_c: float = 15.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
    visibility_km: float = 10.0
    cloud_coverage_percent: float = 30.0
    cloud_base_ft: float = 5000
    cloud_top_ft: float = 15000
    wind_speed_kts: float = 10.0
    wind_direction_deg: float = 270.0
    wind_gusts_kts: float = 15.0
    precipitation_type: str = "none"  # none, rain, snow, hail
    precipitation_intensity: float = 0.0  # 0-1
    turbulence_intensity: float = 0.1  # 0-1
    icing_conditions: bool = False
    thunderstorm: bool = False


class WeatherSystem:
    """Sistema de gestión del clima"""

    def __init__(self, geographic_area: GeographicArea):
        self.area = geographic_area
        self.current_conditions = WeatherConditions()
        self._time_elapsed = 0.0

    def update(self, dt: float):
        """Actualiza las condiciones meteorológicas"""
        self._time_elapsed += dt

        # Variaciones graduales del viento
        wind_variation = math.sin(self._time_elapsed / 3600) * 2
        self.current_conditions.wind_speed_kts = max(
            0,
            self.current_conditions.wind_speed_kts + wind_variation * 0.01
        )

        # Pequeña variación en dirección
        dir_variation = random.uniform(-0.5, 0.5)
        self.current_conditions.wind_direction_deg = (
            self.current_conditions.wind_direction_deg + dir_variation
        ) % 360

    def get_conditions_at_altitude(self, altitude_ft: float) -> dict:
        """Obtiene condiciones a una altitud específica"""
        base = self.current_conditions

        # Temperatura disminuye con altitud (aprox 2°C por 1000ft)
        temp = base.temperature_c - (altitude_ft / 1000) * 2

        # Viento aumenta con altitud
        wind_factor = 1 + (altitude_ft / 30000) * 0.5
        wind = base.wind_speed_kts * wind_factor

        # Determinar si está en nubes
        in_clouds = (
            base.cloud_base_ft <= altitude_ft <= base.cloud_top_ft
            and base.cloud_coverage_percent > 50
        )

        return {
            "temperature_c": temp,
            "wind_speed_kts": wind,
            "wind_direction_deg": base.wind_direction_deg,
            "in_clouds": in_clouds,
            "visibility_km": 0.5 if in_clouds else base.visibility_km,
            "icing_risk": temp < 0 and in_clouds
        }

    def get_impact_on_operations(self) -> dict:
        """Evalúa el impacto del clima en operaciones"""
        cond = self.current_conditions

        impacts = {
            "flight_operations": "normal",
            "visual_operations": "normal",
            "radar_performance": "normal",
            "communications": "normal",
            "landing_conditions": "normal"
        }

        # Evaluar visibilidad
        if cond.visibility_km < 3:
            impacts["visual_operations"] = "degraded"
            impacts["landing_conditions"] = "marginal"
        if cond.visibility_km < 1:
            impacts["visual_operations"] = "severely_degraded"
            impacts["landing_conditions"] = "below_minimums"

        # Evaluar viento
        if cond.wind_speed_kts > 25:
            impacts["landing_conditions"] = "marginal"
        if cond.wind_speed_kts > 40:
            impacts["flight_operations"] = "restricted"
            impacts["landing_conditions"] = "hazardous"

        # Evaluar precipitación
        if cond.precipitation_intensity > 0.5:
            impacts["radar_performance"] = "degraded"
        if cond.thunderstorm:
            impacts["flight_operations"] = "restricted"
            impacts["radar_performance"] = "severely_degraded"
            impacts["communications"] = "degraded"

        # Evaluar turbulencia
        if cond.turbulence_intensity > 0.5:
            impacts["flight_operations"] = "degraded"
        if cond.turbulence_intensity > 0.8:
            impacts["flight_operations"] = "restricted"

        return impacts

    def set_conditions(self, **kwargs):
        """Establece condiciones meteorológicas específicas"""
        for key, value in kwargs.items():
            if hasattr(self.current_conditions, key):
                setattr(self.current_conditions, key, value)

    def generate_forecast(self, hours_ahead: int = 6) -> list[dict]:
        """Genera pronóstico de las próximas horas"""
        forecast = []

        for hour in range(hours_ahead):
            # Simular cambios graduales
            conditions = {
                "hour": hour,
                "visibility_km": self.current_conditions.visibility_km + random.uniform(-1, 1),
                "wind_speed_kts": max(0, self.current_conditions.wind_speed_kts + random.uniform(-3, 3)),
                "cloud_coverage_percent": max(0, min(100,
                    self.current_conditions.cloud_coverage_percent + random.uniform(-10, 10)
                )),
                "precipitation_probability": min(100,
                    self.current_conditions.precipitation_intensity * 100 + random.uniform(-5, 10)
                )
            }
            forecast.append(conditions)

        return forecast

    def to_dict(self) -> dict:
        """Convierte el estado del clima a diccionario"""
        return {
            "current": {
                "temperature_c": self.current_conditions.temperature_c,
                "visibility_km": self.current_conditions.visibility_km,
                "wind_speed_kts": self.current_conditions.wind_speed_kts,
                "wind_direction_deg": self.current_conditions.wind_direction_deg,
                "cloud_coverage_percent": self.current_conditions.cloud_coverage_percent,
                "precipitation": self.current_conditions.precipitation_type,
            },
            "impacts": self.get_impact_on_operations()
        }
