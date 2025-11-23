#!/usr/bin/env python3
"""
GAVILAN - Sistema de Simulación de Juegos de Guerra Aérea
=========================================================

Script principal para ejecutar el simulador

Uso:
    python main.py                    # Ejecutar simulación de ejemplo
    python main.py --api              # Iniciar servidor API
    python main.py --scenario basic   # Ejecutar escenario básico
"""

import argparse
import asyncio
from datetime import datetime

from gavilan.core.engine import SimulationEngine
from gavilan.core.config import GavilanConfig, GeographicArea, SimulationMode
from gavilan.core.entities import Side, Position, AircraftRole
from gavilan.modules.scenario import ScenarioManager
from gavilan.modules.staff import StaffModule
from gavilan.modules.space import SpaceWeatherModule
from gavilan.modules.cyber import CyberModule
from gavilan.modules.air_simulation import AirSimulationModule
from gavilan.modules.intelligence import IntelligenceModule
from gavilan.modules.evaluation import EvaluationModule
from gavilan.modules.training import TrainingModule


def create_basic_scenario():
    """Crea un escenario básico de demostración"""
    print("=" * 60)
    print("GAVILAN - Sistema de Simulación de Juegos de Guerra Aérea")
    print("=" * 60)
    print()

    # Configuración
    config = GavilanConfig()
    config.scenario_name = "Defensa Aérea Básica"
    config.mode = SimulationMode.TRAINING
    config.geographic_area = GeographicArea(
        name="Zona de Operaciones Alpha",
        center_lat=4.6097,
        center_lon=-74.0817,
        radius_km=300
    )
    config.simulation_speed = 10.0
    config.max_duration_hours = 1.0

    # Crear motor
    engine = SimulationEngine(config)

    # Registrar módulos
    print("Registrando módulos...")
    engine.register_module("staff", StaffModule())
    engine.register_module("space_weather", SpaceWeatherModule())
    engine.register_module("cyber", CyberModule())
    engine.register_module("air_simulation", AirSimulationModule())
    engine.register_module("intelligence", IntelligenceModule())
    engine.register_module("evaluation", EvaluationModule())
    engine.register_module("training", TrainingModule())

    # Crear escenario
    print("Creando escenario...")
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.create_scenario(
        "Defensa Aérea Básica",
        "Escenario de entrenamiento para interceptación aérea",
        config.geographic_area
    )

    # Añadir fuerzas propias (BLUE)
    print("Desplegando fuerzas propias...")

    # Base aérea
    scenario_mgr.add_airbase(
        scenario, Side.BLUE, "Base Aérea Principal",
        Position(4.70, -74.15, 2500),
        icao_code="SKBO"
    )

    # Centro de mando
    scenario_mgr.add_command_center(
        scenario, Side.BLUE, "COC Principal",
        Position(4.65, -74.10, 2600)
    )

    # Radares
    scenario_mgr.add_radar_to_scenario(
        scenario, Side.BLUE, "AN/TPS-77", "Radar Norte",
        Position(5.0, -74.0, 3000)
    )
    scenario_mgr.add_radar_to_scenario(
        scenario, Side.BLUE, "ELM-2084", "Radar Sur",
        Position(4.3, -74.2, 2800)
    )

    # Aeronaves CAP
    scenario_mgr.add_aircraft_to_scenario(
        scenario, Side.BLUE, "F-16", "EAGLE-1",
        Position(4.8, -74.0, 25000),
        AircraftRole.FIGHTER,
        speed_kts=450, heading_deg=180
    )
    scenario_mgr.add_aircraft_to_scenario(
        scenario, Side.BLUE, "F-16", "EAGLE-2",
        Position(4.8, -74.1, 25000),
        AircraftRole.FIGHTER,
        speed_kts=450, heading_deg=180
    )

    # SAM
    scenario_mgr.add_sam_site(
        scenario, Side.BLUE, "NASAMS", "SAM-1",
        Position(4.6, -74.08, 2500)
    )

    # Añadir fuerzas enemigas (RED)
    print("Desplegando fuerzas enemigas...")

    # Aeronaves de ataque
    scenario_mgr.add_aircraft_to_scenario(
        scenario, Side.RED, "Su-27", "BANDIT-1",
        Position(3.5, -73.5, 30000),
        AircraftRole.FIGHTER,
        speed_kts=600, heading_deg=315
    )
    scenario_mgr.add_aircraft_to_scenario(
        scenario, Side.RED, "MiG-29", "BANDIT-2",
        Position(3.6, -73.6, 28000),
        AircraftRole.FIGHTER,
        speed_kts=580, heading_deg=320
    )

    # SAM enemigo
    scenario_mgr.add_sam_site(
        scenario, Side.RED, "S-300", "RED-SAM-1",
        Position(3.2, -73.3, 1500)
    )

    # Cargar entidades al motor
    scenario_mgr.load_entities_to_engine(scenario, engine)

    return engine, scenario


def run_simulation_demo():
    """Ejecuta una demostración de la simulación"""
    engine, scenario = create_basic_scenario()

    print()
    print("Iniciando simulación...")
    print("-" * 60)

    # Ejecutar simulación
    engine.start()

    # Simular varios ticks
    for i in range(100):
        engine.tick()

        # Mostrar estado cada 10 ticks
        if (i + 1) % 20 == 0:
            metrics = engine.get_metrics()
            print(f"Tick {engine.state.current_tick}: "
                  f"Tiempo={engine.state.elapsed_time:.1f}s, "
                  f"Entidades={metrics['total_entities']}")

    engine.stop()

    # Obtener resultados
    print()
    print("-" * 60)
    print("Simulación completada")
    print()

    # Mostrar evaluación
    evaluation = engine._modules.get("evaluation")
    if evaluation:
        report = evaluation.get_performance_report()
        scores = report.get("scores", {})

        print("RESULTADOS DE LA SIMULACIÓN")
        print("-" * 40)
        print(f"Puntaje Final: {scores.get('final_score', 0)}")
        print(f"Calificación: {scores.get('grade', 'N/A')}")
        print()

        section_scores = scores.get("section_scores", {})
        print("Puntajes por Sección:")
        for section, score in section_scores.items():
            print(f"  {section}: {score}")

    # Mostrar estado del Estado Mayor
    staff = engine._modules.get("staff")
    if staff:
        status = staff.get_status_report()
        print()
        print(f"Preparación General: {status.get('overall_readiness', 0)*100:.1f}%")

    print()
    print("=" * 60)


def run_api_server():
    """Inicia el servidor API"""
    import uvicorn
    from gavilan.api.main import app

    print("Iniciando servidor GAVILAN API...")
    print("Documentación disponible en: http://localhost:8000/docs")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="GAVILAN - Sistema de Simulación de Juegos de Guerra Aérea"
    )

    parser.add_argument(
        "--api",
        action="store_true",
        help="Iniciar servidor API"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="basic",
        help="Escenario a ejecutar (basic, advanced)"
    )

    args = parser.parse_args()

    if args.api:
        run_api_server()
    else:
        run_simulation_demo()


if __name__ == "__main__":
    main()
