"""
API principal FastAPI de GAVILAN
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from gavilan.core.engine import SimulationEngine
from gavilan.core.config import GavilanConfig, GeographicArea, SimulationMode, DifficultyLevel
from gavilan.core.entities import Side, Position, AircraftRole
from gavilan.modules.scenario import ScenarioManager
from gavilan.modules.staff import StaffModule
from gavilan.modules.space import SpaceWeatherModule
from gavilan.modules.cyber import CyberModule
from gavilan.modules.air_simulation import AirSimulationModule
from gavilan.modules.intelligence import IntelligenceModule
from gavilan.modules.evaluation import EvaluationModule
from gavilan.modules.training import TrainingModule


# Instancia global del motor
engine: Optional[SimulationEngine] = None
scenario_manager = ScenarioManager()


def create_app() -> FastAPI:
    """Crea la aplicación FastAPI"""
    app = FastAPI(
        title="GAVILAN API",
        description="Sistema de Simulación de Juegos de Guerra Aérea",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


# ============== Modelos Pydantic ==============

class ScenarioCreate(BaseModel):
    """Modelo para crear escenario"""
    name: str
    description: str = ""
    center_lat: float = 4.6097
    center_lon: float = -74.0817
    radius_km: float = 500
    mode: str = "training"
    difficulty: str = "medium"


class AircraftCreate(BaseModel):
    """Modelo para crear aeronave"""
    aircraft_type: str
    callsign: str
    side: str = "blue"
    lat: float
    lon: float
    altitude_ft: float
    speed_kts: float = 0
    heading_deg: float = 0
    role: str = "fighter"


class MissionCreate(BaseModel):
    """Modelo para crear misión"""
    mission_type: str
    priority: str = "medium"
    target: dict = {}
    callsign: str = ""


class CyberAttackRequest(BaseModel):
    """Modelo para solicitar ataque cibernético"""
    attack_type: str
    target_system: str
    intensity: float = 1.0


class FlagSubmission(BaseModel):
    """Modelo para enviar flag"""
    team_id: str
    challenge_id: str
    flag: str


# ============== Endpoints de Simulación ==============

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": "GAVILAN API",
        "version": "1.0.0",
        "status": "running",
        "simulation_active": engine is not None and engine.state.running
    }


@app.post("/simulation/create")
async def create_simulation(scenario: ScenarioCreate):
    """Crea una nueva simulación"""
    global engine

    # Crear configuración
    config = GavilanConfig()
    config.scenario_name = scenario.name

    if scenario.mode == "training":
        config.mode = SimulationMode.TRAINING
    elif scenario.mode == "exercise":
        config.mode = SimulationMode.EXERCISE
    elif scenario.mode == "wargame":
        config.mode = SimulationMode.WARGAME
    elif scenario.mode == "ctf":
        config.mode = SimulationMode.CTF

    if scenario.difficulty == "easy":
        config.difficulty = DifficultyLevel.EASY
    elif scenario.difficulty == "hard":
        config.difficulty = DifficultyLevel.HARD
    elif scenario.difficulty == "expert":
        config.difficulty = DifficultyLevel.EXPERT

    config.geographic_area = GeographicArea(
        name=scenario.name,
        center_lat=scenario.center_lat,
        center_lon=scenario.center_lon,
        radius_km=scenario.radius_km
    )

    # Crear motor
    engine = SimulationEngine(config)

    # Registrar módulos
    engine.register_module("staff", StaffModule())
    engine.register_module("space_weather", SpaceWeatherModule())
    engine.register_module("cyber", CyberModule())
    engine.register_module("air_simulation", AirSimulationModule())
    engine.register_module("intelligence", IntelligenceModule())
    engine.register_module("evaluation", EvaluationModule())
    engine.register_module("training", TrainingModule())

    return {
        "status": "created",
        "scenario_id": config.scenario_id,
        "scenario_name": scenario.name
    }


@app.post("/simulation/start")
async def start_simulation():
    """Inicia la simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    engine.start()

    return {
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/simulation/pause")
async def pause_simulation():
    """Pausa la simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    engine.pause()
    return {"status": "paused"}


@app.post("/simulation/resume")
async def resume_simulation():
    """Reanuda la simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    engine.resume()
    return {"status": "resumed"}


@app.post("/simulation/stop")
async def stop_simulation():
    """Detiene la simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    engine.stop()
    return {
        "status": "stopped",
        "elapsed_time": engine.state.elapsed_time
    }


@app.post("/simulation/tick")
async def tick_simulation(ticks: int = 1):
    """Ejecuta ticks de simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    for _ in range(ticks):
        engine.tick()

    return {
        "status": "ticked",
        "current_tick": engine.state.current_tick,
        "elapsed_time": engine.state.elapsed_time
    }


@app.get("/simulation/state")
async def get_simulation_state():
    """Obtiene estado de la simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    return engine.get_state_snapshot()


@app.get("/simulation/metrics")
async def get_metrics():
    """Obtiene métricas de simulación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    return engine.get_metrics()


# ============== Endpoints de Entidades ==============

@app.post("/entities/aircraft")
async def add_aircraft(aircraft: AircraftCreate):
    """Añade una aeronave"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    # Determinar lado
    side = Side.BLUE if aircraft.side == "blue" else Side.RED

    # Determinar rol
    role_map = {
        "fighter": AircraftRole.FIGHTER,
        "bomber": AircraftRole.BOMBER,
        "transport": AircraftRole.TRANSPORT,
        "tanker": AircraftRole.TANKER,
        "awacs": AircraftRole.AWACS,
        "recce": AircraftRole.RECCE,
    }
    role = role_map.get(aircraft.role, AircraftRole.FIGHTER)

    # Crear escenario temporal si no existe
    from gavilan.modules.scenario import ScenarioManager
    sm = ScenarioManager()
    scenario = sm.create_scenario(
        "Temp",
        "",
        engine.config.geographic_area
    )

    ac = sm.add_aircraft_to_scenario(
        scenario,
        side,
        aircraft.aircraft_type,
        aircraft.callsign,
        Position(aircraft.lat, aircraft.lon, aircraft.altitude_ft),
        role,
        speed_kts=aircraft.speed_kts,
        heading_deg=aircraft.heading_deg
    )

    engine.add_entity(ac)

    return {
        "status": "created",
        "entity_id": ac.entity_id,
        "callsign": ac.callsign
    }


@app.get("/entities")
async def get_entities():
    """Obtiene todas las entidades"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    return {
        "total": len(engine._entities),
        "entities": [
            {
                "id": e.entity_id,
                "name": e.name,
                "type": e.entity_type.value,
                "side": e.side.value,
                "active": e.active
            }
            for e in engine._entities.values()
        ]
    }


@app.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Obtiene una entidad específica"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    entity = engine.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return {
        "entity_id": entity.entity_id,
        "name": entity.name,
        "type": entity.entity_type.value,
        "side": entity.side.value,
        "position": {
            "lat": entity.position.latitude,
            "lon": entity.position.longitude,
            "alt": entity.position.altitude_ft
        },
        "velocity": {
            "speed_kts": entity.velocity.speed_kts,
            "heading": entity.velocity.heading_deg
        },
        "health": entity.health,
        "active": entity.active
    }


# ============== Endpoints de Estado Mayor ==============

@app.get("/staff/status")
async def get_staff_status():
    """Obtiene estado del Estado Mayor"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    staff = engine._modules.get("staff")
    if not staff:
        raise HTTPException(status_code=404, detail="Staff module not loaded")

    return staff.get_status_report()


@app.post("/staff/ato/generate")
async def generate_ato(objectives: list[dict]):
    """Genera un ATO"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    staff = engine._modules.get("staff")
    if not staff:
        raise HTTPException(status_code=404, detail="Staff module not loaded")

    ato = staff.request_ato_generation(objectives)

    return {
        "ato_id": ato.ato_id,
        "missions_count": len(ato.missions),
        "period_start": ato.period_start.isoformat(),
        "period_end": ato.period_end.isoformat()
    }


@app.get("/staff/missions")
async def get_missions():
    """Obtiene tablero de misiones"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    staff = engine._modules.get("staff")
    if not staff:
        raise HTTPException(status_code=404, detail="Staff module not loaded")

    return staff.a3_operations.get_mission_board()


# ============== Endpoints de Clima Espacial ==============

@app.get("/space-weather/status")
async def get_space_weather():
    """Obtiene estado del clima espacial"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    sw = engine._modules.get("space_weather")
    if not sw:
        raise HTTPException(status_code=404, detail="Space weather module not loaded")

    return sw.get_status()


@app.post("/space-weather/event")
async def inject_space_event(event_type: str, magnitude: float = 1.0):
    """Inyecta un evento espacial"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    sw = engine._modules.get("space_weather")
    if not sw:
        raise HTTPException(status_code=404, detail="Space weather module not loaded")

    sw.inject_event(event_type, magnitude)

    return {
        "status": "injected",
        "event_type": event_type,
        "magnitude": magnitude
    }


# ============== Endpoints de Ciberdefensa ==============

@app.get("/cyber/status")
async def get_cyber_status():
    """Obtiene estado de ciberdefensa"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    cyber = engine._modules.get("cyber")
    if not cyber:
        raise HTTPException(status_code=404, detail="Cyber module not loaded")

    return cyber.get_threat_landscape()


@app.post("/cyber/attack")
async def launch_cyber_attack(attack: CyberAttackRequest):
    """Lanza un ataque cibernético simulado"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    cyber = engine._modules.get("cyber")
    if not cyber:
        raise HTTPException(status_code=404, detail="Cyber module not loaded")

    result = cyber.launch_attack_scenario(
        attack.attack_type,
        [attack.target_system],
        attack.intensity
    )

    return result


# ============== Endpoints de Inteligencia ==============

@app.get("/intelligence/cop")
async def get_cop():
    """Obtiene Common Operating Picture"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    intel = engine._modules.get("intelligence")
    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence module not loaded")

    return intel.get_common_operating_picture()


@app.get("/intelligence/coas")
async def get_enemy_coas():
    """Obtiene cursos de acción inferidos"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    intel = engine._modules.get("intelligence")
    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence module not loaded")

    return intel.get_enemy_coas()


# ============== Endpoints de Evaluación ==============

@app.get("/evaluation/report")
async def get_evaluation_report():
    """Obtiene reporte de evaluación"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    evaluation = engine._modules.get("evaluation")
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation module not loaded")

    return evaluation.get_performance_report()


@app.get("/evaluation/score")
async def get_final_score():
    """Obtiene puntaje final"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    evaluation = engine._modules.get("evaluation")
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation module not loaded")

    return evaluation.calculate_final_score()


# ============== Endpoints de Entrenamiento/CTF ==============

@app.get("/training/challenges")
async def get_challenges():
    """Obtiene lista de desafíos"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    training = engine._modules.get("training")
    if not training:
        raise HTTPException(status_code=404, detail="Training module not loaded")

    return training.get_challenge_list()


@app.post("/training/flag")
async def submit_flag(submission: FlagSubmission):
    """Envía una flag"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    training = engine._modules.get("training")
    if not training:
        raise HTTPException(status_code=404, detail="Training module not loaded")

    return training.submit_flag(
        submission.team_id,
        submission.challenge_id,
        submission.flag
    )


@app.get("/training/leaderboard")
async def get_leaderboard():
    """Obtiene tabla de posiciones"""
    global engine

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation created")

    training = engine._modules.get("training")
    if not training:
        raise HTTPException(status_code=404, detail="Training module not loaded")

    return training.get_leaderboard()


# ============== Health Check ==============

@app.get("/health")
async def health_check():
    """Verifica salud del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "simulation_loaded": engine is not None
    }
