"""
Sesión de juego multiplayer para GAVILAN

Coordina:
- Simulación
- Jugadores
- Niveles de comando
- Fog of War
- Eventos
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from gavilan.core.engine import SimulationEngine
from gavilan.core.entities import Side
from gavilan.core.config import GavilanConfig
from gavilan.multiplayer.auth import User, Role
from gavilan.multiplayer.fog_of_war import FogOfWar
from gavilan.multiplayer.command_levels import (
    Command,
    CommandResult,
    DirectorLevel,
    StrategicLevel,
    OperationalLevel,
    TacticalLevel,
)


class GameType(str, Enum):
    """Tipos de juego disponibles"""
    EXTERNAL_WAR = "external_war"          # Guerra convencional
    INTERNAL_CONFLICT = "internal_conflict"  # Contrainsurgencia
    DISASTER_MANAGEMENT = "disaster_management"  # Gestión de crisis


class SessionStatus(str, Enum):
    """Estados de una sesión"""
    LOBBY = "lobby"          # Esperando jugadores
    BRIEFING = "briefing"    # Briefing pre-juego
    RUNNING = "running"      # Simulación activa
    PAUSED = "paused"        # Pausada
    ENDED = "ended"          # Terminada
    CANCELLED = "cancelled"  # Cancelada


@dataclass
class PlayerSlot:
    """Slot de jugador en una sesión"""
    role: Role
    side: Side
    user: Optional[User] = None
    joined_at: Optional[datetime] = None

    def is_filled(self) -> bool:
        return self.user is not None


@dataclass
class GameSession:
    """
    Sesión de juego multiplayer

    Representa una partida completa con jugadores, simulación y fog of war.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    game_type: GameType = GameType.EXTERNAL_WAR

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.LOBBY

    # Director/Admin
    director: Optional[User] = None

    # Jugadores
    player_slots: List[PlayerSlot] = field(default_factory=list)

    # Motor de simulación
    simulation_engine: Optional[SimulationEngine] = None
    config: Optional[GavilanConfig] = None

    # Fog of War por bando
    fog_of_war_blue: Optional[FogOfWar] = None
    fog_of_war_red: Optional[FogOfWar] = None

    # Niveles de comando
    director_level: Optional[DirectorLevel] = None
    blue_strategic: Optional[StrategicLevel] = None
    blue_operational: Optional[OperationalLevel] = None
    blue_tactical: Optional[TacticalLevel] = None
    red_strategic: Optional[StrategicLevel] = None
    red_operational: Optional[OperationalLevel] = None
    red_tactical: Optional[TacticalLevel] = None

    def __post_init__(self):
        """Inicializa slots de jugadores"""
        if not self.player_slots:
            self._initialize_player_slots()

    def _initialize_player_slots(self):
        """Crea slots para jugadores"""
        # Slots BLUE
        self.player_slots.extend([
            PlayerSlot(role=Role.BLUE_STRATEGIC, side=Side.BLUE),
            PlayerSlot(role=Role.BLUE_OPERATIONAL, side=Side.BLUE),
            PlayerSlot(role=Role.BLUE_TACTICAL, side=Side.BLUE),
        ])

        # Slots RED
        self.player_slots.extend([
            PlayerSlot(role=Role.RED_STRATEGIC, side=Side.RED),
            PlayerSlot(role=Role.RED_OPERATIONAL, side=Side.RED),
            PlayerSlot(role=Role.RED_TACTICAL, side=Side.RED),
        ])

    def assign_director(self, user: User):
        """Asigna Director"""
        if not user.has_role(Role.GAME_MASTER) and not user.has_role(Role.ADMIN):
            raise ValueError("User must have GAME_MASTER or ADMIN role")
        self.director = user

    def join_player(self, user: User, role: Role) -> bool:
        """
        Jugador se une a la sesión

        Returns:
            True si se unió exitosamente
        """
        # Buscar slot disponible con ese rol
        for slot in self.player_slots:
            if slot.role == role and not slot.is_filled():
                slot.user = user
                slot.joined_at = datetime.now()
                return True

        return False  # Slot no disponible

    def leave_player(self, user: User) -> bool:
        """
        Jugador abandona la sesión

        Returns:
            True si abandonó exitosamente
        """
        for slot in self.player_slots:
            if slot.user and slot.user.id == user.id:
                slot.user = None
                slot.joined_at = None
                return True

        return False

    def get_player_count(self) -> int:
        """Retorna número de jugadores activos"""
        return sum(1 for slot in self.player_slots if slot.is_filled())

    def get_available_slots(self) -> List[PlayerSlot]:
        """Retorna slots disponibles"""
        return [slot for slot in self.player_slots if not slot.is_filled()]

    def is_ready_to_start(self) -> bool:
        """Verifica si puede iniciar (al menos 1 jugador por bando + director)"""
        if not self.director:
            return False

        blue_count = sum(1 for s in self.player_slots if s.is_filled() and s.side == Side.BLUE)
        red_count = sum(1 for s in self.player_slots if s.is_filled() and s.side == Side.RED)

        # Mínimo 1 jugador por bando (excepto en disaster management)
        if self.game_type == GameType.DISASTER_MANAGEMENT:
            return blue_count >= 1
        else:
            return blue_count >= 1 and red_count >= 1

    def start(self, config: GavilanConfig):
        """Inicia la sesión de juego"""
        if self.status != SessionStatus.LOBBY:
            raise ValueError(f"Cannot start session in status {self.status}")

        if not self.is_ready_to_start():
            raise ValueError("Session not ready to start")

        # Crear motor de simulación
        self.simulation_engine = SimulationEngine(config)
        self.config = config

        # Crear Fog of War
        self.fog_of_war_blue = FogOfWar(Side.BLUE)
        self.fog_of_war_red = FogOfWar(Side.RED)

        # Crear niveles de comando
        self.director_level = DirectorLevel(self.simulation_engine)
        self.blue_strategic = StrategicLevel(Side.BLUE, self.simulation_engine)
        self.blue_operational = OperationalLevel(Side.BLUE, self.simulation_engine)
        self.blue_tactical = TacticalLevel(Side.BLUE, self.simulation_engine)
        self.red_strategic = StrategicLevel(Side.RED, self.simulation_engine)
        self.red_operational = OperationalLevel(Side.RED, self.simulation_engine)
        self.red_tactical = TacticalLevel(Side.RED, self.simulation_engine)

        # Iniciar simulación
        self.simulation_engine.start()

        # Actualizar estado
        self.status = SessionStatus.RUNNING
        self.started_at = datetime.now()

    def pause(self):
        """Pausa la sesión"""
        if self.simulation_engine:
            self.simulation_engine.pause()
        self.status = SessionStatus.PAUSED

    def resume(self):
        """Reanuda la sesión"""
        if self.simulation_engine:
            self.simulation_engine.resume()
        self.status = SessionStatus.RUNNING

    def stop(self):
        """Termina la sesión"""
        if self.simulation_engine:
            self.simulation_engine.stop()
        self.status = SessionStatus.ENDED
        self.ended_at = datetime.now()

    def tick(self):
        """
        Ejecuta un tick de simulación

        Actualiza:
        1. Simulación
        2. Fog of War
        3. Niveles de comando
        """
        if self.status != SessionStatus.RUNNING:
            return

        if not self.simulation_engine:
            return

        # 1. Tick de simulación
        self.simulation_engine.tick()

        # 2. Actualizar Fog of War
        all_entities = self.simulation_engine.entities

        # Obtener sensores de cada bando
        blue_sensors = [e for e in all_entities if e.side == Side.BLUE and hasattr(e, 'max_range_km')]
        red_sensors = [e for e in all_entities if e.side == Side.RED and hasattr(e, 'max_range_km')]

        self.fog_of_war_blue.update(all_entities, blue_sensors)
        self.fog_of_war_red.update(all_entities, red_sensors)

    def execute_command(self, command: Command, user: User) -> CommandResult:
        """
        Ejecuta un comando de jugador

        Args:
            command: Comando a ejecutar
            user: Usuario que emite el comando

        Returns:
            Resultado de la ejecución
        """
        # Seleccionar nivel apropiado
        level_interface = self._get_level_interface(command.level, command.side)

        if not level_interface:
            return CommandResult(
                success=False,
                message=f"Command level {command.level} not available",
            )

        # Validar comando
        if not level_interface.validate_command(command, user):
            return CommandResult(
                success=False,
                message="Command validation failed (permission denied or invalid)",
            )

        # Ejecutar
        result = level_interface.execute_command(command)

        # Registrar
        level_interface.log_command(command)

        return result

    def _get_level_interface(self, level, side):
        """Obtiene interfaz de nivel de comando"""
        if level == "director":
            return self.director_level
        elif level == "strategic":
            return self.blue_strategic if side == Side.BLUE else self.red_strategic
        elif level == "operational":
            return self.blue_operational if side == Side.BLUE else self.red_operational
        elif level == "tactical":
            return self.blue_tactical if side == Side.BLUE else self.red_tactical
        return None

    def get_state_for_user(self, user: User) -> Dict:
        """
        Retorna estado de simulación filtrado para un usuario

        Aplica Fog of War según rol del usuario.
        """
        if not self.simulation_engine:
            return {"status": "not_started"}

        # Determinar bando del usuario
        user_side = None
        for slot in self.player_slots:
            if slot.user and slot.user.id == user.id:
                user_side = slot.side
                break

        # Director/Admin ve todo (ground truth)
        if user.has_role(Role.GAME_MASTER) or user.has_role(Role.ADMIN):
            entities = self.simulation_engine.entities
        else:
            # Aplicar Fog of War
            if user_side == Side.BLUE:
                entities = self.fog_of_war_blue.get_visible_entities(
                    self.simulation_engine.entities
                )
            elif user_side == Side.RED:
                entities = self.fog_of_war_red.get_visible_entities(
                    self.simulation_engine.entities
                )
            else:
                entities = []

        return {
            "status": self.status.value,
            "simulation_time": self.simulation_engine.state.elapsed_time,
            "tick": self.simulation_engine.state.tick,
            "entities": [self._entity_to_dict(e) for e in entities],
        }

    def _entity_to_dict(self, entity) -> Dict:
        """Serializa entidad a diccionario"""
        return {
            "id": str(entity.id),
            "type": entity.type,
            "side": entity.side.value,
            "position": {
                "lat": entity.position.latitude,
                "lon": entity.position.longitude,
                "alt_ft": entity.altitude_ft,
            },
            "is_track": getattr(entity, '_is_track', False),
            "uncertainty_km": getattr(entity, '_track_uncertainty_km', 0),
        }

    def get_status_dict(self) -> Dict:
        """Retorna estado de la sesión"""
        return {
            "id": str(self.id),
            "name": self.name,
            "game_type": self.game_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "director": self.director.username if self.director else None,
            "players": self.get_player_count(),
            "slots_available": len(self.get_available_slots()),
        }
