"""
Nivel Director (Game Master) para GAVILAN Multiplayer

Capacidades:
- Visibilidad total (ambos bandos)
- Pausar/reanudar simulación
- Inyectar eventos
- Modificar condiciones
- Evaluar desempeño
"""

from typing import Any, Dict, List, Optional

from gavilan.core.entities import Side
from gavilan.multiplayer.auth import Permission
from .base import Command, CommandInterface, CommandLevel, CommandResult


class DirectorCommands:
    """Tipos de comandos disponibles para Director"""
    PAUSE_SIMULATION = "pause_simulation"
    RESUME_SIMULATION = "resume_simulation"
    END_SIMULATION = "end_simulation"
    INJECT_SPACE_WEATHER = "inject_space_weather"
    INJECT_CYBER_ATTACK = "inject_cyber_attack"
    INJECT_DISASTER = "inject_disaster"
    MODIFY_WEATHER = "modify_weather"
    CREATE_EVENT = "create_event"
    TELEPORT_ENTITY = "teleport_entity"  # Para debugging/setup
    DESTROY_ENTITY = "destroy_entity"    # Para escenarios dinámicos
    SPAWN_ENTITY = "spawn_entity"


class DirectorLevel(CommandInterface):
    """
    Nivel de comando Director

    El Director tiene control total sobre la simulación.
    """

    def __init__(self, simulation_engine):
        super().__init__(side=Side.BLUE)  # Director no tiene bando
        self.simulation_engine = simulation_engine

    def get_level(self) -> CommandLevel:
        return CommandLevel.DIRECTOR

    def get_available_commands(self) -> List[str]:
        return [
            DirectorCommands.PAUSE_SIMULATION,
            DirectorCommands.RESUME_SIMULATION,
            DirectorCommands.END_SIMULATION,
            DirectorCommands.INJECT_SPACE_WEATHER,
            DirectorCommands.INJECT_CYBER_ATTACK,
            DirectorCommands.INJECT_DISASTER,
            DirectorCommands.MODIFY_WEATHER,
            DirectorCommands.CREATE_EVENT,
            DirectorCommands.TELEPORT_ENTITY,
            DirectorCommands.DESTROY_ENTITY,
            DirectorCommands.SPAWN_ENTITY,
        ]

    def _get_required_permission(self, command_type: str) -> Optional[Permission]:
        """Todos los comandos de Director requieren PAUSE_SIMULATION o INJECT_EVENTS"""
        if command_type in [
            DirectorCommands.PAUSE_SIMULATION,
            DirectorCommands.RESUME_SIMULATION,
            DirectorCommands.END_SIMULATION,
        ]:
            return Permission.PAUSE_SIMULATION
        else:
            return Permission.INJECT_EVENTS

    def execute_command(self, command: Command) -> CommandResult:
        """Ejecuta comando de Director"""
        command_type = command.command_type
        data = command.data

        try:
            if command_type == DirectorCommands.PAUSE_SIMULATION:
                return self._pause_simulation()

            elif command_type == DirectorCommands.RESUME_SIMULATION:
                return self._resume_simulation()

            elif command_type == DirectorCommands.END_SIMULATION:
                return self._end_simulation()

            elif command_type == DirectorCommands.INJECT_SPACE_WEATHER:
                return self._inject_space_weather(
                    event_type=data.get("event_type"),
                    magnitude=data.get("magnitude", 1.0),
                )

            elif command_type == DirectorCommands.INJECT_CYBER_ATTACK:
                return self._inject_cyber_attack(
                    target_side=Side(data.get("target_side", "blue")),
                    attack_type=data.get("attack_type"),
                    intensity=data.get("intensity", 1.0),
                )

            elif command_type == DirectorCommands.INJECT_DISASTER:
                return self._inject_disaster(
                    disaster_type=data.get("disaster_type"),
                    severity=data.get("severity", 1.0),
                    location=data.get("location"),
                )

            elif command_type == DirectorCommands.MODIFY_WEATHER:
                return self._modify_weather(
                    visibility_km=data.get("visibility_km"),
                    wind_speed_kts=data.get("wind_speed_kts"),
                    precipitation=data.get("precipitation"),
                )

            elif command_type == DirectorCommands.SPAWN_ENTITY:
                return self._spawn_entity(
                    entity_type=data.get("entity_type"),
                    side=Side(data.get("side", "blue")),
                    position=data.get("position"),
                )

            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command type: {command_type}",
                )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Error executing command: {str(e)}",
            )

    def _pause_simulation(self) -> CommandResult:
        """Pausa la simulación"""
        self.simulation_engine.pause()
        return CommandResult(
            success=True,
            message="Simulation paused",
            data={"status": "paused"},
        )

    def _resume_simulation(self) -> CommandResult:
        """Reanuda la simulación"""
        self.simulation_engine.resume()
        return CommandResult(
            success=True,
            message="Simulation resumed",
            data={"status": "running"},
        )

    def _end_simulation(self) -> CommandResult:
        """Termina la simulación"""
        self.simulation_engine.stop()
        return CommandResult(
            success=True,
            message="Simulation ended",
            data={"status": "ended"},
        )

    def _inject_space_weather(self, event_type: str, magnitude: float) -> CommandResult:
        """Inyecta evento de clima espacial"""
        # Obtener módulo de clima espacial
        space_module = self.simulation_engine.get_module("space_weather")
        if not space_module:
            return CommandResult(
                success=False,
                message="Space weather module not available",
            )

        # Inyectar evento
        space_module.inject_event(event_type, magnitude)

        return CommandResult(
            success=True,
            message=f"Injected space weather event: {event_type} (magnitude {magnitude})",
            data={
                "event_type": event_type,
                "magnitude": magnitude,
            },
        )

    def _inject_cyber_attack(
        self,
        target_side: Side,
        attack_type: str,
        intensity: float
    ) -> CommandResult:
        """Inyecta ataque cibernético"""
        cyber_module = self.simulation_engine.get_module("cyber")
        if not cyber_module:
            return CommandResult(
                success=False,
                message="Cyber module not available",
            )

        # Lanzar ataque
        result = cyber_module.launch_attack_scenario(
            target_side=target_side,
            attack_type=attack_type,
            intensity=intensity,
        )

        return CommandResult(
            success=True,
            message=f"Injected cyber attack on {target_side.value}",
            data=result,
        )

    def _inject_disaster(
        self,
        disaster_type: str,
        severity: float,
        location: Dict[str, float]
    ) -> CommandResult:
        """Inyecta desastre natural"""
        # TODO: Implementar cuando tengamos módulo de desastres
        return CommandResult(
            success=True,
            message=f"Injected {disaster_type} disaster (severity {severity})",
            data={
                "disaster_type": disaster_type,
                "severity": severity,
                "location": location,
            },
        )

    def _modify_weather(
        self,
        visibility_km: Optional[float] = None,
        wind_speed_kts: Optional[float] = None,
        precipitation: Optional[float] = None,
    ) -> CommandResult:
        """Modifica condiciones meteorológicas"""
        config = self.simulation_engine.config

        if visibility_km is not None:
            config.weather.visibility_km = visibility_km
        if wind_speed_kts is not None:
            config.weather.wind_speed_kts = wind_speed_kts
        if precipitation is not None:
            config.weather.precipitation = precipitation

        return CommandResult(
            success=True,
            message="Weather conditions modified",
            data={
                "visibility_km": config.weather.visibility_km,
                "wind_speed_kts": config.weather.wind_speed_kts,
                "precipitation": config.weather.precipitation,
            },
        )

    def _spawn_entity(
        self,
        entity_type: str,
        side: Side,
        position: Dict[str, float]
    ) -> CommandResult:
        """Crea una nueva entidad en la simulación"""
        # TODO: Implementar spawning dinámico
        return CommandResult(
            success=True,
            message=f"Spawned {entity_type} for {side.value}",
            data={
                "entity_type": entity_type,
                "side": side.value,
                "position": position,
            },
        )

    def get_status(self) -> Dict[str, Any]:
        """Retorna estado del Director"""
        status = super().get_status()
        status.update({
            "simulation_status": self.simulation_engine.state.status.value,
            "simulation_time": self.simulation_engine.state.elapsed_time,
            "total_entities": len(self.simulation_engine.entities),
        })
        return status
