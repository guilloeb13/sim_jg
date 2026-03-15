"""
Nivel Operacional (Air Operations Center) para GAVILAN Multiplayer

Capacidades:
- Generar ATO
- Planificar misiones
- Asignar aeronaves a misiones
- Ordenar SCRAMBLE
- Coordinar con A1, A4
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from gavilan.core.entities import Side
from gavilan.multiplayer.auth import Permission
from .base import Command, CommandInterface, CommandLevel, CommandResult


class OperationalCommands:
    """Comandos operacionales"""
    CREATE_ATO = "create_ato"
    CREATE_MISSION = "create_mission"
    ASSIGN_AIRCRAFT = "assign_aircraft"
    LAUNCH_MISSION = "launch_mission"
    ABORT_MISSION = "abort_mission"
    SCRAMBLE = "scramble"
    REQUEST_TANKER = "request_tanker"
    REQUEST_AWACS = "request_awacs"


class OperationalLevel(CommandInterface):
    """Nivel de comando Operacional (AOC)"""

    def __init__(self, side: Side, simulation_engine):
        super().__init__(side)
        self.simulation_engine = simulation_engine

    def get_level(self) -> CommandLevel:
        return CommandLevel.OPERATIONAL

    def get_available_commands(self) -> List[str]:
        return [
            OperationalCommands.CREATE_ATO,
            OperationalCommands.CREATE_MISSION,
            OperationalCommands.ASSIGN_AIRCRAFT,
            OperationalCommands.LAUNCH_MISSION,
            OperationalCommands.ABORT_MISSION,
            OperationalCommands.SCRAMBLE,
            OperationalCommands.REQUEST_TANKER,
            OperationalCommands.REQUEST_AWACS,
        ]

    def _get_required_permission(self, command_type: str) -> Optional[Permission]:
        mapping = {
            OperationalCommands.CREATE_ATO: Permission.CREATE_ATO,
            OperationalCommands.CREATE_MISSION: Permission.ASSIGN_MISSIONS,
            OperationalCommands.ASSIGN_AIRCRAFT: Permission.ASSIGN_MISSIONS,
            OperationalCommands.LAUNCH_MISSION: Permission.ASSIGN_MISSIONS,
            OperationalCommands.ABORT_MISSION: Permission.ASSIGN_MISSIONS,
            OperationalCommands.SCRAMBLE: Permission.SCRAMBLE,
            OperationalCommands.REQUEST_TANKER: Permission.COORDINATE_LOGISTICS,
            OperationalCommands.REQUEST_AWACS: Permission.ASSIGN_MISSIONS,
        }
        return mapping.get(command_type)

    def execute_command(self, command: Command) -> CommandResult:
        command_type = command.command_type
        data = command.data

        try:
            if command_type == OperationalCommands.CREATE_MISSION:
                return self._create_mission(
                    mission_type=data.get("mission_type"),
                    target=data.get("target"),
                    priority=data.get("priority", "MEDIUM"),
                )

            elif command_type == OperationalCommands.ASSIGN_AIRCRAFT:
                return self._assign_aircraft(
                    mission_id=data.get("mission_id"),
                    aircraft_ids=data.get("aircraft_ids", []),
                )

            elif command_type == OperationalCommands.LAUNCH_MISSION:
                return self._launch_mission(data.get("mission_id"))

            elif command_type == OperationalCommands.ABORT_MISSION:
                return self._abort_mission(data.get("mission_id"))

            elif command_type == OperationalCommands.SCRAMBLE:
                return self._scramble(
                    threat_position=data.get("threat_position"),
                    num_aircraft=data.get("num_aircraft", 2),
                )

            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command_type}",
                )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Error: {str(e)}",
            )

    def _create_mission(
        self,
        mission_type: str,
        target: Dict,
        priority: str
    ) -> CommandResult:
        """Crea una nueva misión"""
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        # Crear misión a través de A3
        mission = staff_module.a3.create_mission(
            mission_type=mission_type,
            target_location=target,
            priority=priority,
        )

        return CommandResult(
            success=True,
            message=f"Mission created: {mission_type}",
            data={"mission_id": str(mission.id)},
        )

    def _assign_aircraft(
        self,
        mission_id: str,
        aircraft_ids: List[str]
    ) -> CommandResult:
        """Asigna aeronaves a una misión"""
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        # Asignar aeronaves
        for aircraft_id in aircraft_ids:
            aircraft_uuid = UUID(aircraft_id)
            mission_uuid = UUID(mission_id)
            staff_module.a3.assign_aircraft_to_mission(mission_uuid, aircraft_uuid)

        return CommandResult(
            success=True,
            message=f"Assigned {len(aircraft_ids)} aircraft to mission",
            data={"mission_id": mission_id, "aircraft_count": len(aircraft_ids)},
        )

    def _launch_mission(self, mission_id: str) -> CommandResult:
        """Lanza una misión"""
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        mission_uuid = UUID(mission_id)
        staff_module.a3.launch_mission(mission_uuid)

        return CommandResult(
            success=True,
            message=f"Mission {mission_id} launched",
            data={"mission_id": mission_id, "status": "LAUNCHED"},
        )

    def _abort_mission(self, mission_id: str) -> CommandResult:
        """Aborta una misión"""
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        mission_uuid = UUID(mission_id)
        staff_module.a3.abort_mission(mission_uuid)

        return CommandResult(
            success=True,
            message=f"Mission {mission_id} aborted",
            data={"mission_id": mission_id, "status": "ABORTED"},
        )

    def _scramble(
        self,
        threat_position: Dict[str, float],
        num_aircraft: int
    ) -> CommandResult:
        """Ordena scramble ante amenaza"""
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        # Crear misión de scramble
        mission = staff_module.a3.scramble(
            threat_location=threat_position,
            num_aircraft=num_aircraft,
        )

        return CommandResult(
            success=True,
            message=f"Scramble ordered: {num_aircraft} aircraft",
            data={"mission_id": str(mission.id) if mission else None},
        )

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        staff_module = self.simulation_engine.get_module("staff")
        if staff_module:
            status.update({
                "active_missions": len(staff_module.a3.active_missions),
                "aircraft_available": len([a for a in self.simulation_engine.get_aircraft(self.side) if not a.mission_id]),
            })
        return status
