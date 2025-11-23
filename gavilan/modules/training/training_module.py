"""
Módulo de entrenamiento
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

from gavilan.core.events import Event, EventType, event_bus
from gavilan.modules.training.ctf import CTFEngine


class ChallengeType(Enum):
    """Tipos de desafíos"""
    CYBER_DEFENSE = "cyber_defense"
    CYBER_OFFENSE = "cyber_offense"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"


class TeamType(Enum):
    """Tipos de equipo"""
    RED = "red"
    BLUE = "blue"
    PURPLE = "purple"


@dataclass
class Challenge:
    """Desafío de entrenamiento"""
    challenge_id: str
    name: str
    description: str
    challenge_type: ChallengeType
    difficulty: int  # 1-5
    points: int
    flags: list = field(default_factory=list)
    hints: list = field(default_factory=list)
    time_limit_min: int = 60


@dataclass
class TeamScore:
    """Puntaje de equipo"""
    team_id: str
    team_type: TeamType
    score: int = 0
    flags_captured: int = 0
    challenges_completed: int = 0


class TrainingModule:
    """Módulo de entrenamiento y CTF"""

    def __init__(self):
        self.event_bus = event_bus
        self.ctf_engine = CTFEngine()
        self._challenges: dict[str, Challenge] = {}
        self._teams: dict[str, TeamScore] = {}
        self._active_session: Optional[dict] = None
        self._completed_challenges: list = []

        self._initialize_challenges()

    def _initialize_challenges(self):
        """Inicializa desafíos predefinidos"""
        challenges = [
            Challenge(
                challenge_id="CTF-001",
                name="Radar Network Intrusion",
                description="Penetrar la red de radares enemigos y obtener la configuración",
                challenge_type=ChallengeType.CYBER_OFFENSE,
                difficulty=3,
                points=100,
                flags=["FLAG{radar_config_extracted}"],
                hints=["Buscar puertos abiertos", "Credenciales por defecto"]
            ),
            Challenge(
                challenge_id="CTF-002",
                name="Defend the C2",
                description="Proteger el centro de comando de un ataque DDoS",
                challenge_type=ChallengeType.CYBER_DEFENSE,
                difficulty=2,
                points=75,
                flags=["FLAG{ddos_mitigated}"],
                hints=["Analizar patrones de tráfico", "Implementar rate limiting"]
            ),
            Challenge(
                challenge_id="CTF-003",
                name="SCADA Infiltration",
                description="Comprometer el sistema SCADA de defensa aérea",
                challenge_type=ChallengeType.CYBER_OFFENSE,
                difficulty=4,
                points=150,
                flags=["FLAG{scada_control_achieved}"],
                hints=["Protocolo Modbus", "PLC vulnerabilities"]
            ),
            Challenge(
                challenge_id="CTF-004",
                name="Intercept Communications",
                description="Interceptar y decodificar comunicaciones enemigas",
                challenge_type=ChallengeType.CYBER_OFFENSE,
                difficulty=3,
                points=100,
                flags=["FLAG{comms_decoded}"],
                hints=["Analizar frecuencias", "Buscar patrones"]
            ),
            Challenge(
                challenge_id="CTF-005",
                name="Air Defense Bypass",
                description="Planificar ruta evadiendo sistemas SAM",
                challenge_type=ChallengeType.TACTICAL,
                difficulty=3,
                points=100,
                flags=["FLAG{safe_route_planned}"],
                hints=["Analizar cobertura radar", "Terreno masking"]
            ),
            Challenge(
                challenge_id="CTF-006",
                name="Data Exfiltration Detection",
                description="Detectar y bloquear exfiltración de datos clasificados",
                challenge_type=ChallengeType.CYBER_DEFENSE,
                difficulty=4,
                points=125,
                flags=["FLAG{exfil_blocked}"],
                hints=["Monitor DNS queries", "Analizar tráfico saliente"]
            ),
            Challenge(
                challenge_id="CTF-007",
                name="GPS Spoofing Attack",
                description="Detectar y mitigar ataque de GPS spoofing",
                challenge_type=ChallengeType.CYBER_DEFENSE,
                difficulty=5,
                points=200,
                flags=["FLAG{gps_spoofing_detected}"],
                hints=["Comparar con INS", "Analizar anomalías de señal"]
            ),
            Challenge(
                challenge_id="CTF-008",
                name="False Flag Injection",
                description="Inyectar datos falsos en el sistema radar enemigo",
                challenge_type=ChallengeType.CYBER_OFFENSE,
                difficulty=5,
                points=200,
                flags=["FLAG{false_tracks_injected}"],
                hints=["Explotar protocolo de datos", "Timing crítico"]
            )
        ]

        for challenge in challenges:
            self._challenges[challenge.challenge_id] = challenge

    def start_training_session(
        self,
        session_name: str,
        team_type: TeamType,
        challenge_ids: list = None
    ) -> dict:
        """Inicia una sesión de entrenamiento"""
        session_id = f"SES-{str(uuid.uuid4())[:8].upper()}"

        self._active_session = {
            "session_id": session_id,
            "name": session_name,
            "team_type": team_type.value,
            "start_time": datetime.now(),
            "challenges": challenge_ids or list(self._challenges.keys()),
            "status": "active"
        }

        # Crear equipo
        team_id = f"TEAM-{team_type.value.upper()}"
        self._teams[team_id] = TeamScore(
            team_id=team_id,
            team_type=team_type
        )

        return self._active_session

    def submit_flag(self, team_id: str, challenge_id: str, flag: str) -> dict:
        """Envía una flag para validación"""
        if challenge_id not in self._challenges:
            return {"success": False, "message": "Challenge not found"}

        challenge = self._challenges[challenge_id]

        if flag in challenge.flags:
            # Flag correcta
            if team_id in self._teams:
                team = self._teams[team_id]
                team.score += challenge.points
                team.flags_captured += 1
                team.challenges_completed += 1

            self._completed_challenges.append({
                "team_id": team_id,
                "challenge_id": challenge_id,
                "timestamp": datetime.now(),
                "points": challenge.points
            })

            self.event_bus.publish(Event(
                event_type=EventType.FLAG_CAPTURED,
                source="training",
                data={
                    "team_id": team_id,
                    "challenge_id": challenge_id,
                    "points": challenge.points
                }
            ))

            return {
                "success": True,
                "message": "Flag captured!",
                "points": challenge.points
            }

        return {"success": False, "message": "Incorrect flag"}

    def get_hint(self, challenge_id: str, hint_index: int) -> Optional[str]:
        """Obtiene una pista para un desafío"""
        if challenge_id not in self._challenges:
            return None

        challenge = self._challenges[challenge_id]
        if hint_index < len(challenge.hints):
            return challenge.hints[hint_index]

        return None

    def get_leaderboard(self) -> list[dict]:
        """Obtiene tabla de posiciones"""
        sorted_teams = sorted(
            self._teams.values(),
            key=lambda t: t.score,
            reverse=True
        )

        return [
            {
                "rank": i + 1,
                "team_id": team.team_id,
                "team_type": team.team_type.value,
                "score": team.score,
                "flags_captured": team.flags_captured,
                "challenges_completed": team.challenges_completed
            }
            for i, team in enumerate(sorted_teams)
        ]

    def get_challenge_list(self) -> list[dict]:
        """Obtiene lista de desafíos"""
        return [
            {
                "challenge_id": c.challenge_id,
                "name": c.name,
                "type": c.challenge_type.value,
                "difficulty": c.difficulty,
                "points": c.points,
                "completed": c.challenge_id in [
                    cc["challenge_id"] for cc in self._completed_challenges
                ]
            }
            for c in self._challenges.values()
        ]

    def get_session_status(self) -> dict:
        """Obtiene estado de la sesión"""
        if not self._active_session:
            return {"active": False}

        elapsed = (datetime.now() - self._active_session["start_time"]).total_seconds()

        return {
            "active": True,
            "session_id": self._active_session["session_id"],
            "name": self._active_session["name"],
            "elapsed_minutes": elapsed / 60,
            "challenges_available": len(self._active_session["challenges"]),
            "challenges_completed": len(self._completed_challenges),
            "leaderboard": self.get_leaderboard()
        }

    def get_status(self) -> dict:
        """Obtiene estado del módulo"""
        return {
            "total_challenges": len(self._challenges),
            "active_session": self._active_session is not None,
            "teams": len(self._teams),
            "completed_challenges": len(self._completed_challenges)
        }
