"""
Módulo de Clima Espacial
========================

Simula condiciones del clima espacial y su impacto operacional
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import math
import random

from gavilan.core.events import Event, EventType, event_bus


class SpaceWeatherLevel(Enum):
    """Niveles de actividad espacial"""
    QUIET = "quiet"
    UNSETTLED = "unsettled"
    ACTIVE = "active"
    MINOR_STORM = "minor_storm"
    MAJOR_STORM = "major_storm"
    SEVERE_STORM = "severe_storm"


class AlertType(Enum):
    """Tipos de alertas espaciales"""
    GEOMAGNETIC = "geomagnetic"
    SOLAR_RADIATION = "solar_radiation"
    RADIO_BLACKOUT = "radio_blackout"


@dataclass
class SpaceWeatherData:
    """Datos del clima espacial"""
    # Índices geomagnéticos
    kp_index: float = 2.0  # 0-9
    dst_index: float = -10.0  # nT
    ap_index: float = 10.0

    # Viento solar
    solar_wind_speed: float = 400.0  # km/s
    solar_wind_density: float = 5.0  # protons/cm³
    imf_bz: float = 0.0  # nT (componente norte-sur)

    # Radiación
    proton_flux_10mev: float = 1.0  # pfu
    proton_flux_100mev: float = 0.1  # pfu
    electron_flux: float = 100.0  # particles/cm²/s/sr

    # Rayos X solares
    xray_flux: float = 1e-6  # W/m²
    xray_class: str = "A"

    # Eyecciones de masa coronal
    cme_active: bool = False
    cme_arrival_hours: float = 0.0
    cme_speed: float = 0.0  # km/s

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


class SpaceWeatherModule:
    """Módulo de gestión del clima espacial"""

    def __init__(self):
        self.event_bus = event_bus
        self.current_data = SpaceWeatherData()
        self._storm_level = SpaceWeatherLevel.QUIET
        self._active_alerts: list[dict] = []
        self._effects_calculator = SpaceWeatherEffects()
        self._time_elapsed = 0.0

    def update(self, dt: float, engine):
        """Actualiza el clima espacial"""
        self._time_elapsed += dt

        # Simular variaciones naturales
        self._simulate_variations(dt)

        # Calcular nivel de tormenta
        self._calculate_storm_level()

        # Generar alertas si es necesario
        self._check_alerts()

        # Calcular y aplicar efectos
        effects = self._effects_calculator.calculate_effects(self.current_data)
        self._apply_effects_to_systems(effects, engine)

    def _simulate_variations(self, dt: float):
        """Simula variaciones naturales del clima espacial"""
        data = self.current_data

        # Variación del índice Kp (ciclo ~3 horas)
        kp_variation = math.sin(self._time_elapsed / 10800) * 0.5
        data.kp_index = max(0, min(9, data.kp_index + kp_variation * 0.01 * dt))

        # Viento solar
        wind_variation = random.uniform(-5, 5)
        data.solar_wind_speed = max(200, min(800, data.solar_wind_speed + wind_variation * 0.1 * dt))

        # IMF Bz
        bz_variation = random.uniform(-0.5, 0.5)
        data.imf_bz = max(-20, min(20, data.imf_bz + bz_variation * 0.1 * dt))

        # Actualizar Dst basado en Bz y viento solar
        if data.imf_bz < -5:
            data.dst_index -= 0.5 * dt
        else:
            data.dst_index = min(0, data.dst_index + 0.1 * dt)

        # Simular posible CME
        if data.cme_active:
            data.cme_arrival_hours -= dt / 3600
            if data.cme_arrival_hours <= 0:
                self._trigger_cme_impact()

        data.timestamp = datetime.now()

    def _calculate_storm_level(self):
        """Calcula nivel de tormenta geomagnética"""
        kp = self.current_data.kp_index

        if kp < 4:
            self._storm_level = SpaceWeatherLevel.QUIET
        elif kp < 5:
            self._storm_level = SpaceWeatherLevel.UNSETTLED
        elif kp < 6:
            self._storm_level = SpaceWeatherLevel.ACTIVE
        elif kp < 7:
            self._storm_level = SpaceWeatherLevel.MINOR_STORM
        elif kp < 8:
            self._storm_level = SpaceWeatherLevel.MAJOR_STORM
        else:
            self._storm_level = SpaceWeatherLevel.SEVERE_STORM

    def _check_alerts(self):
        """Verifica si se deben generar alertas"""
        data = self.current_data

        # Alerta geomagnética
        if data.kp_index >= 5:
            self._create_alert(
                AlertType.GEOMAGNETIC,
                f"Kp={data.kp_index:.1f}",
                data.kp_index >= 7
            )

        # Alerta de radiación solar
        if data.proton_flux_10mev >= 10:
            self._create_alert(
                AlertType.SOLAR_RADIATION,
                f"Flujo={data.proton_flux_10mev:.1f} pfu",
                data.proton_flux_10mev >= 100
            )

        # Alerta de blackout de radio
        if data.xray_flux >= 1e-4:
            self._create_alert(
                AlertType.RADIO_BLACKOUT,
                f"Rayos X clase {data.xray_class}",
                data.xray_flux >= 1e-3
            )

    def _create_alert(self, alert_type: AlertType, message: str, critical: bool):
        """Crea una alerta de clima espacial"""
        alert = {
            "type": alert_type.value,
            "message": message,
            "critical": critical,
            "timestamp": datetime.now()
        }

        self._active_alerts.append(alert)

        self.event_bus.publish(Event(
            event_type=EventType.SPACE_WEATHER_ALERT,
            source="space_weather",
            priority=1 if critical else 3,
            data=alert
        ))

    def _trigger_cme_impact(self):
        """Dispara el impacto de una CME"""
        data = self.current_data
        data.cme_active = False

        # Incrementos súbitos
        data.kp_index = min(9, data.kp_index + 3)
        data.dst_index -= 100
        data.solar_wind_speed += 200

        self._create_alert(
            AlertType.GEOMAGNETIC,
            "CME Impact - Tormenta geomagnética severa",
            True
        )

    def _apply_effects_to_systems(self, effects: dict, engine):
        """Aplica efectos del clima espacial a los sistemas"""
        # Degradar GPS en aeronaves
        if effects["gps_degradation"] > 0.2:
            self.event_bus.publish(Event(
                event_type=EventType.GPS_DEGRADATION,
                source="space_weather",
                data={"degradation": effects["gps_degradation"]}
            ))

        # Afectar comunicaciones satelitales
        if effects["satcom_degradation"] > 0.3:
            self.event_bus.publish(Event(
                event_type=EventType.SATCOM_FAILURE,
                source="space_weather",
                data={"degradation": effects["satcom_degradation"]}
            ))

    def inject_event(self, event_type: str, magnitude: float = 1.0):
        """Inyecta un evento espacial para simulación"""
        data = self.current_data

        if event_type == "cme":
            data.cme_active = True
            data.cme_arrival_hours = 24 + random.uniform(-12, 12)
            data.cme_speed = 800 + magnitude * 400
        elif event_type == "solar_flare":
            # Clase X
            data.xray_flux = 1e-4 * magnitude
            data.xray_class = f"X{magnitude:.1f}"
            data.proton_flux_10mev *= (1 + magnitude * 10)
        elif event_type == "geomagnetic_storm":
            data.kp_index = min(9, 5 + magnitude * 2)
            data.dst_index = -50 * magnitude

    def get_operational_impacts(self) -> dict:
        """Obtiene los impactos operacionales actuales"""
        effects = self._effects_calculator.calculate_effects(self.current_data)

        impacts = {
            "gps_accuracy": f"{(1 - effects['gps_degradation']) * 100:.0f}%",
            "satcom_availability": f"{(1 - effects['satcom_degradation']) * 100:.0f}%",
            "hf_propagation": f"{(1 - effects['hf_degradation']) * 100:.0f}%",
            "radar_noise": f"+{effects['radar_noise_increase']:.1f} dB",
            "navigation_errors": f"+{effects['navigation_error_m']:.0f} m",
            "recommendations": []
        }

        # Generar recomendaciones
        if effects['gps_degradation'] > 0.3:
            impacts['recommendations'].append("Usar navegación INS como respaldo")
        if effects['satcom_degradation'] > 0.4:
            impacts['recommendations'].append("Cambiar a comunicaciones HF/VHF")
        if effects['hf_degradation'] > 0.5:
            impacts['recommendations'].append("Evitar frecuencias HF altas")

        return impacts

    def get_status(self) -> dict:
        """Obtiene estado del clima espacial"""
        return {
            "storm_level": self._storm_level.value,
            "kp_index": self.current_data.kp_index,
            "dst_index": self.current_data.dst_index,
            "solar_wind_speed": self.current_data.solar_wind_speed,
            "xray_class": self.current_data.xray_class,
            "cme_active": self.current_data.cme_active,
            "active_alerts": len(self._active_alerts),
            "operational_impacts": self.get_operational_impacts()
        }

    def get_forecast(self, hours: int = 24) -> list[dict]:
        """Genera pronóstico del clima espacial"""
        forecast = []
        current_kp = self.current_data.kp_index

        for hour in range(0, hours, 3):
            # Simulación simplificada
            variation = random.uniform(-1, 1)
            predicted_kp = max(0, min(9, current_kp + variation))

            forecast.append({
                "hour": hour,
                "kp_predicted": round(predicted_kp, 1),
                "storm_level": self._kp_to_level(predicted_kp),
                "confidence": max(0.5, 1 - hour/hours * 0.5)
            })

        return forecast

    def _kp_to_level(self, kp: float) -> str:
        """Convierte Kp a nivel de tormenta"""
        if kp < 5:
            return "quiet"
        elif kp < 6:
            return "active"
        elif kp < 7:
            return "minor_storm"
        else:
            return "major_storm"


class SpaceWeatherEffects:
    """Calcula efectos del clima espacial en sistemas"""

    def calculate_effects(self, data: SpaceWeatherData) -> dict:
        """Calcula todos los efectos operacionales"""
        return {
            "gps_degradation": self._calc_gps_degradation(data),
            "satcom_degradation": self._calc_satcom_degradation(data),
            "hf_degradation": self._calc_hf_degradation(data),
            "radar_noise_increase": self._calc_radar_noise(data),
            "navigation_error_m": self._calc_nav_error(data),
        }

    def _calc_gps_degradation(self, data: SpaceWeatherData) -> float:
        """Calcula degradación GPS"""
        # Basado en Kp y centelleo ionosférico
        kp_factor = data.kp_index / 9
        proton_factor = min(1, math.log10(max(1, data.proton_flux_10mev)) / 3)

        return min(1, kp_factor * 0.5 + proton_factor * 0.5)

    def _calc_satcom_degradation(self, data: SpaceWeatherData) -> float:
        """Calcula degradación de comunicaciones satelitales"""
        # Afectado por radiación y centelleo
        radiation_factor = min(1, math.log10(max(1, data.proton_flux_10mev)) / 2)
        storm_factor = data.kp_index / 9

        return min(1, radiation_factor * 0.6 + storm_factor * 0.4)

    def _calc_hf_degradation(self, data: SpaceWeatherData) -> float:
        """Calcula degradación de comunicaciones HF"""
        # Muy sensible a rayos X
        xray_factor = min(1, math.log10(data.xray_flux * 1e6 + 1) / 3)
        dst_factor = abs(data.dst_index) / 200

        return min(1, xray_factor * 0.7 + dst_factor * 0.3)

    def _calc_radar_noise(self, data: SpaceWeatherData) -> float:
        """Calcula incremento de ruido en radares OTH"""
        # dB adicionales
        return data.kp_index * 0.5 + abs(data.dst_index) * 0.01

    def _calc_nav_error(self, data: SpaceWeatherData) -> float:
        """Calcula error adicional en navegación"""
        # Metros adicionales de error
        gps_deg = self._calc_gps_degradation(data)
        return gps_deg * 50  # Hasta 50m de error adicional
