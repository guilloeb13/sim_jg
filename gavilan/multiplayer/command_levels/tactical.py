"""
Nivel Táctico (Pilot/Fighter Controller) para GAVILAN Multiplayer

Capacidades:
- Control directo de aeronaves asignadas
- Tomar decisiones de combate
- Reportar contactos
- Solicitar soporte
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from gavilan.core.entities import Side
from gavilan.multiplayer.auth import Permission
from .base import Command, CommandInterface, CommandLevel, CommandResult


class TacticalCommands:
    """Comandos tácticos"""
    SET_WAYPOINT = "set_waypoint"
    SET_ALTITUDE = "set_altitude"
    SET_SPEED = "set_speed"
    ENGAGE_TARGET = "engage_target"
    DISENGAGE = "disengage"
    LAUNCH_WEAPON = "launch_weapon"
    DEPLOY_COUNTERMEASURES = "deploy_countermeasures"
    REQUEST_TANKER = "request_tanker"
    REQUEST_SAR = "request_sar"
    REPORT_CONTACT = "report_contact"
    RTB = "rtb"  # Return to base


class TacticalLevel(CommandInterface):
    """Nivel de comando Táctico"""

    def __init__(self, side: Side, simulation_engine):
        super().__init__(side)
        self.simulation_engine = simulation_engine
        self.assigned_aircraft: List[UUID] = []  # Aeronaves asignadas a este controlador

    def get_level(self) -> CommandLevel:
        return CommandLevel.TACTICAL

    def get_available_commands(self) -> List[str]:
        return [
            TacticalCommands.SET_WAYPOINT,
            TacticalCommands.SET_ALTITUDE,
            TacticalCommands.SET_SPEED,
            TacticalCommands.ENGAGE_TARGET,
            TacticalCommands.DISENGAGE,
            TacticalCommands.LAUNCH_WEAPON,
            TacticalCommands.DEPLOY_COUNTERMEASURES,
            TacticalCommands.REQUEST_TANKER,
            TacticalCommands.REQUEST_SAR,
            TacticalCommands.REPORT_CONTACT,
            TacticalCommands.RTB,
        ]

    def _get_required_permission(self, command_type: str) -> Optional[Permission]:
        if command_type in [
            TacticalCommands.ENGAGE_TARGET,
            TacticalCommands.LAUNCH_WEAPON,
        ]:
            return Permission.ENGAGE_TARGETS
        elif command_type in [
            TacticalCommands.REQUEST_TANKER,
            TacticalCommands.REQUEST_SAR,
        ]:
            return Permission.REQUEST_SUPPORT
        else:
            return Permission.CONTROL_AIRCRAFT

    def execute_command(self, command: Command) -> CommandResult:
        command_type = command.command_type
        data = command.data

        try:
            aircraft_id = UUID(data.get("aircraft_id"))

            # Verificar que aeronave esté asignada
            if aircraft_id not in self.assigned_aircraft:
                return CommandResult(
                    success=False,
                    message="Aircraft not assigned to this controller",
                )

            # Obtener aeronave
            aircraft = self.simulation_engine.get_entity(aircraft_id)
            if not aircraft:
                return CommandResult(
                    success=False,
                    message="Aircraft not found",
                )

            # Ejecutar comando
            if command_type == TacticalCommands.SET_WAYPOINT:
                return self._set_waypoint(aircraft, data.get("waypoint"))

            elif command_type == TacticalCommands.SET_ALTITUDE:
                return self._set_altitude(aircraft, data.get("altitude_ft"))

            elif command_type == TacticalCommands.SET_SPEED:
                return self._set_speed(aircraft, data.get("speed_kts"))

            elif command_type == TacticalCommands.ENGAGE_TARGET:
                return self._engage_target(aircraft, UUID(data.get("target_id")))

            elif command_type == TacticalCommands.DISENGAGE:
                return self._disengage(aircraft)

            elif command_type == TacticalCommands.LAUNCH_WEAPON:
                return self._launch_weapon(
                    aircraft,
                    UUID(data.get("target_id")),
                    data.get("weapon_type"),
                )

            elif command_type == TacticalCommands.DEPLOY_COUNTERMEASURES:
                return self._deploy_countermeasures(aircraft)

            elif command_type == TacticalCommands.RTB:
                return self._rtb(aircraft)

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

    def assign_aircraft(self, aircraft_id: UUID):
        """Asigna aeronave a este controlador"""
        if aircraft_id not in self.assigned_aircraft:
            self.assigned_aircraft.append(aircraft_id)

    def _set_waypoint(self, aircraft, waypoint: Dict) -> CommandResult:
        """Establece waypoint"""
        # TODO: Implementar sistema de waypoints
        return CommandResult(
            success=True,
            message=f"Waypoint set for {aircraft.callsign}",
            data={"waypoint": waypoint},
        )

    def _set_altitude(self, aircraft, altitude_ft: float) -> CommandResult:
        """Cambia altitud"""
        # TODO: Implementar cambio gradual de altitud
        aircraft.target_altitude_ft = altitude_ft
        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} climbing/descending to {altitude_ft} ft",
            data={"altitude_ft": altitude_ft},
        )

    def _set_speed(self, aircraft, speed_kts: float) -> CommandResult:
        """Cambia velocidad"""
        if speed_kts > aircraft.max_speed_kts:
            return CommandResult(
                success=False,
                message=f"Speed exceeds max speed ({aircraft.max_speed_kts} kts)",
            )

        aircraft.target_speed_kts = speed_kts
        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} adjusting speed to {speed_kts} kts",
            data={"speed_kts": speed_kts},
        )

    def _engage_target(self, aircraft, target_id: UUID) -> CommandResult:
        """Ordena engagement contra objetivo"""
        air_module = self.simulation_engine.get_module("air_simulation")
        if not air_module:
            return CommandResult(
                success=False,
                message="Air simulation module not available",
            )

        # Solicitar engagement
        success = air_module.request_engagement(aircraft.id, target_id)

        if success:
            return CommandResult(
                success=True,
                message=f"{aircraft.callsign} engaging target {target_id}",
                data={"target_id": str(target_id)},
            )
        else:
            return CommandResult(
                success=False,
                message="Engagement request failed",
            )

    def _disengage(self, aircraft) -> CommandResult:
        """Ordena disengage"""
        # TODO: Implementar disengage
        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} disengaging",
        )

    def _launch_weapon(
        self,
        aircraft,
        target_id: UUID,
        weapon_type: str
    ) -> CommandResult:
        """Lanza arma contra objetivo"""
        air_module = self.simulation_engine.get_module("air_simulation")
        if not air_module:
            return CommandResult(
                success=False,
                message="Air simulation module not available",
            )

        # Verificar que tenga el arma
        # TODO: Verificar inventario de armas

        # Lanzar arma
        # TODO: Implementar lanzamiento de arma

        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} launched {weapon_type}",
            data={
                "weapon_type": weapon_type,
                "target_id": str(target_id),
            },
        )

    def _deploy_countermeasures(self, aircraft) -> CommandResult:
        """Despliega contramedidas"""
        if not hasattr(aircraft, 'countermeasures') or aircraft.countermeasures <= 0:
            return CommandResult(
                success=False,
                message="No countermeasures available",
            )

        aircraft.countermeasures -= 1

        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} deployed countermeasures",
            data={"countermeasures_remaining": aircraft.countermeasures},
        )

    def _rtb(self, aircraft) -> CommandResult:
        """Return to base"""
        # TODO: Implementar RTB automático
        return CommandResult(
            success=True,
            message=f"{aircraft.callsign} returning to base",
        )

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "assigned_aircraft": len(self.assigned_aircraft),
        })
        return status
