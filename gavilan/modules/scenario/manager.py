"""
Gestor principal de escenarios
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from gavilan.core.config import GavilanConfig, GeographicArea, RulesOfEngagement
from gavilan.core.entities import (
    Entity, Aircraft, Radar, CommandCenter, SAMSite, Airbase,
    Side, AircraftRole, Position, Velocity
)
from gavilan.modules.scenario.orbat import OrderOfBattle
from gavilan.modules.scenario.weather import WeatherSystem


@dataclass
class Scenario:
    """Definición completa de un escenario"""
    name: str
    description: str
    scenario_id: str

    # Configuración
    config: GavilanConfig

    # Fuerzas
    blue_orbat: OrderOfBattle
    red_orbat: OrderOfBattle

    # Sistemas
    weather: WeatherSystem

    # Objetivos
    blue_objectives: list = field(default_factory=list)
    red_objectives: list = field(default_factory=list)

    # Eventos programados
    scheduled_events: list = field(default_factory=list)


class ScenarioManager:
    """Gestiona la creación y carga de escenarios"""

    def __init__(self):
        self._current_scenario: Optional[Scenario] = None
        self._scenarios_library: dict[str, Scenario] = {}

    def create_scenario(
        self,
        name: str,
        description: str,
        geographic_area: GeographicArea,
        roe: RulesOfEngagement = None
    ) -> Scenario:
        """Crea un nuevo escenario"""

        config = GavilanConfig()
        config.scenario_name = name
        config.geographic_area = geographic_area

        if roe:
            config.roe = roe

        scenario = Scenario(
            name=name,
            description=description,
            scenario_id=config.scenario_id,
            config=config,
            blue_orbat=OrderOfBattle(side=Side.BLUE),
            red_orbat=OrderOfBattle(side=Side.RED),
            weather=WeatherSystem(geographic_area)
        )

        self._current_scenario = scenario
        return scenario

    def add_aircraft_to_scenario(
        self,
        scenario: Scenario,
        side: Side,
        aircraft_type: str,
        callsign: str,
        position: Position,
        role: AircraftRole = AircraftRole.FIGHTER,
        **kwargs
    ) -> Aircraft:
        """Añade una aeronave al escenario"""

        aircraft = Aircraft(
            name=callsign,
            aircraft_type=aircraft_type,
            callsign=callsign,
            role=role,
            side=side,
            position=position,
            velocity=Velocity(
                speed_kts=kwargs.get('speed_kts', 0),
                heading_deg=kwargs.get('heading_deg', 0)
            )
        )

        # Configurar según tipo
        aircraft_configs = {
            "F-16": {"max_speed_kts": 1320, "rcs_m2": 1.2, "max_g": 9.0},
            "F-18": {"max_speed_kts": 1190, "rcs_m2": 1.0, "max_g": 7.5},
            "Su-27": {"max_speed_kts": 1340, "rcs_m2": 15.0, "max_g": 9.0},
            "MiG-29": {"max_speed_kts": 1320, "rcs_m2": 5.0, "max_g": 9.0},
            "F-22": {"max_speed_kts": 1500, "rcs_m2": 0.0001, "max_g": 9.0},
            "A-10": {"max_speed_kts": 380, "rcs_m2": 10.0, "max_g": 6.0},
            "KC-135": {"max_speed_kts": 530, "rcs_m2": 100.0, "max_g": 2.5},
            "E-3": {"max_speed_kts": 480, "rcs_m2": 150.0, "max_g": 2.0},
        }

        if aircraft_type in aircraft_configs:
            for key, value in aircraft_configs[aircraft_type].items():
                setattr(aircraft, key, value)

        # Añadir al ORBAT
        orbat = scenario.blue_orbat if side == Side.BLUE else scenario.red_orbat
        orbat.add_aircraft(aircraft)

        return aircraft

    def add_radar_to_scenario(
        self,
        scenario: Scenario,
        side: Side,
        radar_type: str,
        name: str,
        position: Position,
        **kwargs
    ) -> Radar:
        """Añade un radar al escenario"""

        radar = Radar(
            name=name,
            radar_type=radar_type,
            side=side,
            position=position,
        )

        # Configurar según tipo
        radar_configs = {
            "AN/TPS-77": {"max_range_km": 450, "min_detectable_rcs_m2": 0.5},
            "S-300_SR": {"max_range_km": 300, "min_detectable_rcs_m2": 0.1},
            "ELM-2084": {"max_range_km": 470, "min_detectable_rcs_m2": 0.3},
            "96L6E": {"max_range_km": 300, "min_detectable_rcs_m2": 0.2},
            "AN/SPY-1": {"max_range_km": 450, "min_detectable_rcs_m2": 0.1},
        }

        if radar_type in radar_configs:
            for key, value in radar_configs[radar_type].items():
                setattr(radar, key, value)

        # Aplicar kwargs adicionales
        for key, value in kwargs.items():
            if hasattr(radar, key):
                setattr(radar, key, value)

        orbat = scenario.blue_orbat if side == Side.BLUE else scenario.red_orbat
        orbat.add_radar(radar)

        return radar

    def add_sam_site(
        self,
        scenario: Scenario,
        side: Side,
        sam_type: str,
        name: str,
        position: Position,
        **kwargs
    ) -> SAMSite:
        """Añade un sitio SAM al escenario"""

        sam = SAMSite(
            name=name,
            sam_type=sam_type,
            side=side,
            position=position
        )

        # Configurar según tipo
        sam_configs = {
            "S-300": {"max_range_km": 150, "missiles_max": 48},
            "S-400": {"max_range_km": 400, "missiles_max": 72},
            "Patriot": {"max_range_km": 70, "missiles_max": 16},
            "NASAMS": {"max_range_km": 25, "missiles_max": 12},
            "SA-6": {"max_range_km": 24, "missiles_max": 6},
        }

        if sam_type in sam_configs:
            for key, value in sam_configs[sam_type].items():
                setattr(sam, key, value)
            sam.missiles_available = sam.missiles_max

        orbat = scenario.blue_orbat if side == Side.BLUE else scenario.red_orbat
        orbat.add_sam_site(sam)

        return sam

    def add_command_center(
        self,
        scenario: Scenario,
        side: Side,
        name: str,
        position: Position,
        center_type: str = "Tactical Operations Center"
    ) -> CommandCenter:
        """Añade un centro de mando al escenario"""

        cc = CommandCenter(
            name=name,
            center_type=center_type,
            side=side,
            position=position
        )

        orbat = scenario.blue_orbat if side == Side.BLUE else scenario.red_orbat
        orbat.add_command_center(cc)

        return cc

    def add_airbase(
        self,
        scenario: Scenario,
        side: Side,
        name: str,
        position: Position,
        icao_code: str = "",
        **kwargs
    ) -> Airbase:
        """Añade una base aérea al escenario"""

        airbase = Airbase(
            name=name,
            icao_code=icao_code,
            side=side,
            position=position
        )

        for key, value in kwargs.items():
            if hasattr(airbase, key):
                setattr(airbase, key, value)

        orbat = scenario.blue_orbat if side == Side.BLUE else scenario.red_orbat
        orbat.add_airbase(airbase)

        return airbase

    def load_entities_to_engine(self, scenario: Scenario, engine):
        """Carga todas las entidades del escenario al motor"""

        # Cargar fuerzas azules
        for entity in scenario.blue_orbat.get_all_entities():
            engine.add_entity(entity)

        # Cargar fuerzas rojas
        for entity in scenario.red_orbat.get_all_entities():
            engine.add_entity(entity)

        print(f"Cargadas {len(scenario.blue_orbat.get_all_entities())} entidades BLUE")
        print(f"Cargadas {len(scenario.red_orbat.get_all_entities())} entidades RED")

    def save_scenario(self, scenario: Scenario, filepath: str):
        """Guarda un escenario en archivo JSON"""
        data = {
            "name": scenario.name,
            "description": scenario.description,
            "scenario_id": scenario.scenario_id,
            "config": scenario.config.to_dict(),
            "blue_orbat": scenario.blue_orbat.to_dict(),
            "red_orbat": scenario.red_orbat.to_dict(),
            "objectives": {
                "blue": scenario.blue_objectives,
                "red": scenario.red_objectives
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def get_predefined_scenarios(self) -> list[dict]:
        """Retorna lista de escenarios predefinidos"""
        return [
            {
                "id": "SCN-001",
                "name": "Defensa Aérea Básica",
                "description": "Escenario de entrenamiento para defensa de espacio aéreo",
                "difficulty": "easy"
            },
            {
                "id": "SCN-002",
                "name": "Operación SEAD",
                "description": "Supresión de defensas aéreas enemigas",
                "difficulty": "medium"
            },
            {
                "id": "SCN-003",
                "name": "Interceptación BVR",
                "description": "Combate aire-aire más allá del alcance visual",
                "difficulty": "medium"
            },
            {
                "id": "SCN-004",
                "name": "Ataque Cibernético a C2",
                "description": "Defensa contra ataques cibernéticos a centros de mando",
                "difficulty": "hard"
            },
            {
                "id": "SCN-005",
                "name": "Tormenta Geomagnética",
                "description": "Operaciones durante evento de clima espacial severo",
                "difficulty": "hard"
            }
        ]
