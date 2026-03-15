"""
API REST - Gestión de Escenarios
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional

from gavilan.multiplayer.auth import User, Permission
from .auth import get_current_user


router = APIRouter()


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    game_type: str
    difficulty: str


# TODO: Implementar repositorio de escenarios persistente
SCENARIOS = [
    {
        "id": "SCN-001",
        "name": "Defensa Aérea Básica",
        "description": "Defensa territorial contra incursión aérea",
        "game_type": "external_war",
        "difficulty": "easy"
    },
    {
        "id": "SCN-002",
        "name": "Operación SEAD",
        "description": "Supresión de defensas aéreas enemigas",
        "game_type": "external_war",
        "difficulty": "medium"
    },
    {
        "id": "SCN-003",
        "name": "Interceptación BVR",
        "description": "Combate más allá del rango visual",
        "game_type": "external_war",
        "difficulty": "medium"
    },
    {
        "id": "SCN-004",
        "name": "Operación Contrainsurgente",
        "description": "CAS y apoyo a tropas en contacto",
        "game_type": "internal_conflict",
        "difficulty": "hard"
    },
    {
        "id": "SCN-005",
        "name": "Terremoto 7.2",
        "description": "Respuesta a desastre natural mayor",
        "game_type": "disaster_management",
        "difficulty": "hard"
    },
]


@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(
    game_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Lista escenarios disponibles"""
    scenarios = SCENARIOS

    if game_type:
        scenarios = [s for s in scenarios if s["game_type"] == game_type]

    return [ScenarioResponse(**s) for s in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene detalles de un escenario"""
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    return ScenarioResponse(**scenario)
