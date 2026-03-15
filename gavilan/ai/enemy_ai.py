"""
IA para Enemigos Autónomos (Guerra Externa)

Controla comportamiento de bando RED cuando no hay jugadores humanos.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from gavilan.core.entities import Side, Aircraft
from gavilan.core.config import DifficultyLevel


class TacticalState(str, Enum):
    """Estados tácticos"""
    PATROL = "patrol"
    INTERCEPT = "intercept"
    ENGAGE = "engage"
    DEFENSIVE = "defensive"
    RTB = "rtb"
    EVADE = "evade"


@dataclass
class ThreatAssessment:
    """Evaluación de amenaza"""
    target_id: str
    distance_km: float
    threat_level: float  # 0-1
    aspect: str  # "hot", "cold", "beam"
    altitude_advantage: bool
    speed_advantage: bool


@dataclass
class Doctrine:
    """Doctrina militar del bando IA"""
    name: str
    aggressiveness: float  # 0-1 (0=defensive, 1=very aggressive)
    risk_tolerance: float  # 0-1
    coordination_level: float  # 0-1 (tactics cooperation)
    tactics: List[str] = field(default_factory=list)


class EnemyAI:
    """
    IA para bando enemigo en guerra externa

    Controla:
    - Tácticas de combate aéreo
    - Planificación de misiones
    - Coordinación entre unidades
    - Respuesta a amenazas
    """

    def __init__(self, side: Side, difficulty: DifficultyLevel):
        self.side = side
        self.difficulty = difficulty
        self.doctrine = self._load_doctrine(difficulty)

        # Estado interno
        self.aircraft_states: Dict[str, TacticalState] = {}
        self.threat_assessments: Dict[str, List[ThreatAssessment]] = {}
        self.mission_assignments: Dict[str, str] = {}

    def _load_doctrine(self, difficulty: DifficultyLevel) -> Doctrine:
        """Carga doctrina según dificultad"""
        if difficulty == DifficultyLevel.EASY:
            return Doctrine(
                name="Basic",
                aggressiveness=0.3,
                risk_tolerance=0.2,
                coordination_level=0.1,
                tactics=["basic_intercept", "simple_evasion"]
            )
        elif difficulty == DifficultyLevel.MEDIUM:
            return Doctrine(
                name="Intermediate",
                aggressiveness=0.6,
                risk_tolerance=0.5,
                coordination_level=0.5,
                tactics=["beam_maneuver", "defensive_split", "cooperative_engagement"]
            )
        elif difficulty == DifficultyLevel.HARD:
            return Doctrine(
                name="Advanced",
                aggressiveness=0.8,
                risk_tolerance=0.7,
                coordination_level=0.8,
                tactics=["offensive_pincer", "feint_and_strike", "bvr_ambush", "defensive_wall"]
            )
        else:  # EXPERT
            return Doctrine(
                name="Expert",
                aggressiveness=0.9,
                risk_tolerance=0.8,
                coordination_level=1.0,
                tactics=["all_tactics", "adaptive_strategy", "predictive_positioning"]
            )

    def update(self, game_state: Dict):
        """
        Actualiza IA cada tick

        Args:
            game_state: Estado actual del juego
        """
        # 1. Evaluar amenazas
        threats = self._assess_threats(game_state)

        # 2. Asignar estados tácticos
        self._update_tactical_states(game_state, threats)

        # 3. Ejecutar tácticas
        for aircraft in game_state.get("aircraft", []):
            if aircraft["side"] != self.side.value:
                continue

            aircraft_id = aircraft["id"]
            state = self.aircraft_states.get(aircraft_id, TacticalState.PATROL)

            if state == TacticalState.ENGAGE:
                self._execute_engagement(aircraft, threats.get(aircraft_id, []))
            elif state == TacticalState.DEFENSIVE:
                self._execute_defensive(aircraft, threats.get(aircraft_id, []))
            elif state == TacticalState.PATROL:
                self._execute_patrol(aircraft)
            elif state == TacticalState.EVADE:
                self._execute_evasion(aircraft, threats.get(aircraft_id, []))

    def _assess_threats(self, game_state: Dict) -> Dict[str, List[ThreatAssessment]]:
        """Evalúa amenazas para cada aeronave"""
        threats = {}

        own_aircraft = [a for a in game_state.get("aircraft", []) if a["side"] == self.side.value]
        enemy_aircraft = [a for a in game_state.get("aircraft", []) if a["side"] != self.side.value]

        for own in own_aircraft:
            aircraft_threats = []

            for enemy in enemy_aircraft:
                # Calcular distancia (simplificado)
                distance = self._calculate_distance(own["position"], enemy["position"])

                # Evaluar nivel de amenaza
                threat_level = self._calculate_threat_level(own, enemy, distance)

                # Aspecto
                aspect = self._calculate_aspect(own, enemy)

                # Ventajas tácticas
                alt_adv = own["position"]["alt_ft"] > enemy["position"]["alt_ft"]
                spd_adv = own.get("speed_kts", 0) > enemy.get("speed_kts", 0)

                aircraft_threats.append(ThreatAssessment(
                    target_id=enemy["id"],
                    distance_km=distance,
                    threat_level=threat_level,
                    aspect=aspect,
                    altitude_advantage=alt_adv,
                    speed_advantage=spd_adv,
                ))

            # Ordenar por nivel de amenaza
            aircraft_threats.sort(key=lambda t: t.threat_level, reverse=True)
            threats[own["id"]] = aircraft_threats

        return threats

    def _calculate_distance(self, pos1: Dict, pos2: Dict) -> float:
        """Calcula distancia entre posiciones (simplificado)"""
        import math
        dlat = pos2["lat"] - pos1["lat"]
        dlon = pos2["lon"] - pos1["lon"]
        return math.sqrt(dlat**2 + dlon**2) * 111  # Aprox km

    def _calculate_threat_level(self, own: Dict, enemy: Dict, distance: float) -> float:
        """Calcula nivel de amenaza 0-1"""
        threat = 0.0

        # Proximidad (más cerca = más amenaza)
        if distance < 20:
            threat += 0.5
        elif distance < 50:
            threat += 0.3
        elif distance < 100:
            threat += 0.1

        # Aspecto (hot = más amenaza)
        aspect = self._calculate_aspect(own, enemy)
        if aspect == "hot":
            threat += 0.3
        elif aspect == "beam":
            threat += 0.1

        # Ventaja de altitud (enemigo arriba = más amenaza)
        if enemy["position"]["alt_ft"] > own["position"]["alt_ft"]:
            threat += 0.2

        return min(threat, 1.0)

    def _calculate_aspect(self, own: Dict, enemy: Dict) -> str:
        """Calcula aspecto relativo"""
        # Simplificado: aleatorio para demo
        return random.choice(["hot", "cold", "beam"])

    def _update_tactical_states(self, game_state: Dict, threats: Dict):
        """Actualiza estados tácticos de aeronaves"""
        for aircraft in game_state.get("aircraft", []):
            if aircraft["side"] != self.side.value:
                continue

            aircraft_id = aircraft["id"]
            aircraft_threats = threats.get(aircraft_id, [])

            # Tomar decisión según doctrina y amenazas
            if not aircraft_threats:
                # Sin amenazas: patrulla
                self.aircraft_states[aircraft_id] = TacticalState.PATROL

            elif aircraft_threats[0].threat_level > 0.7:
                # Amenaza alta: decidir según doctrina
                if self.doctrine.aggressiveness > 0.6:
                    self.aircraft_states[aircraft_id] = TacticalState.ENGAGE
                else:
                    self.aircraft_states[aircraft_id] = TacticalState.DEFENSIVE

            elif aircraft_threats[0].threat_level > 0.4:
                # Amenaza media: engage
                self.aircraft_states[aircraft_id] = TacticalState.ENGAGE

            else:
                # Amenaza baja: interceptar
                self.aircraft_states[aircraft_id] = TacticalState.INTERCEPT

    def _execute_engagement(self, aircraft: Dict, threats: List[ThreatAssessment]):
        """Ejecuta táctica de engagement"""
        if not threats:
            return

        primary_threat = threats[0]

        # Seleccionar táctica según dificultad
        if self.difficulty == DifficultyLevel.EASY:
            self._basic_intercept(aircraft, primary_threat)
        elif self.difficulty == DifficultyLevel.MEDIUM:
            if primary_threat.aspect == "hot":
                self._beam_maneuver(aircraft, primary_threat)
            else:
                self._offensive_positioning(aircraft, primary_threat)
        else:  # HARD/EXPERT
            if len(threats) > 1:
                self._cooperative_engagement(aircraft, threats)
            else:
                self._advanced_bvr_tactics(aircraft, primary_threat)

    def _basic_intercept(self, aircraft: Dict, threat: ThreatAssessment):
        """Táctica básica: volar directo al objetivo"""
        # TODO: Implementar comandos de navegación
        command = {
            "type": "set_waypoint",
            "aircraft_id": aircraft["id"],
            "target_id": threat.target_id,
        }
        return command

    def _beam_maneuver(self, aircraft: Dict, threat: ThreatAssessment):
        """Maniobra beam para reducir Pk del misil enemigo"""
        command = {
            "type": "execute_maneuver",
            "aircraft_id": aircraft["id"],
            "maneuver": "beam",
            "relative_to": threat.target_id,
        }
        return command

    def _offensive_positioning(self, aircraft: Dict, threat: ThreatAssessment):
        """Posicionamiento ofensivo para disparo óptimo"""
        command = {
            "type": "position_for_shot",
            "aircraft_id": aircraft["id"],
            "target_id": threat.target_id,
            "preferred_range_km": 40 if self.difficulty >= DifficultyLevel.HARD else 30,
        }
        return command

    def _advanced_bvr_tactics(self, aircraft: Dict, threat: ThreatAssessment):
        """Tácticas BVR avanzadas"""
        # Disparar desde rango óptimo con geometry favorable
        if threat.distance_km < 60 and threat.aspect != "cold":
            command = {
                "type": "launch_weapon",
                "aircraft_id": aircraft["id"],
                "target_id": threat.target_id,
                "weapon_type": "AAM_BVR",
            }
            return command

    def _cooperative_engagement(self, aircraft: Dict, threats: List[ThreatAssessment]):
        """Engagement cooperativo con otras aeronaves"""
        # TODO: Coordinar con wingman
        pass

    def _execute_defensive(self, aircraft: Dict, threats: List[ThreatAssessment]):
        """Ejecuta táctica defensiva"""
        if threats and threats[0].distance_km < 10:
            # Desplegar contramedidas
            command = {
                "type": "deploy_countermeasures",
                "aircraft_id": aircraft["id"],
            }
            return command

    def _execute_patrol(self, aircraft: Dict):
        """Ejecuta patrulla"""
        # Mantener CAP sobre zona asignada
        pass

    def _execute_evasion(self, aircraft: Dict, threats: List[ThreatAssessment]):
        """Ejecuta maniobras evasivas"""
        if threats:
            command = {
                "type": "execute_maneuver",
                "aircraft_id": aircraft["id"],
                "maneuver": "defensive_break",
                "direction": random.choice(["left", "right"]),
            }
            return command

    def get_status(self) -> Dict:
        """Retorna estado de la IA"""
        return {
            "side": self.side.value,
            "difficulty": self.difficulty.value,
            "doctrine": {
                "name": self.doctrine.name,
                "aggressiveness": self.doctrine.aggressiveness,
                "coordination": self.doctrine.coordination_level,
            },
            "aircraft_count": len(self.aircraft_states),
            "states": {state.value: sum(1 for s in self.aircraft_states.values() if s == state) for state in TacticalState},
        }
