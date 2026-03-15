"""
Nivel Estratégico (High Command) para GAVILAN Multiplayer

Capacidades:
- Ver situación general (fog of war aplicado)
- Definir ROE
- Asignar objetivos estratégicos
- Aprobar/rechazar ATOs
- Asignar recursos entre sectores
"""

from typing import Any, Dict, List, Optional

from gavilan.core.entities import Side
from gavilan.multiplayer.auth import Permission
from .base import Command, CommandInterface, CommandLevel, CommandResult


class StrategicCommands:
    """Comandos estratégicos"""
    SET_ROE = "set_roe"
    SET_STRATEGIC_OBJECTIVE = "set_strategic_objective"
    ALLOCATE_RESOURCES = "allocate_resources"
    APPROVE_ATO = "approve_ato"
    REJECT_ATO = "reject_ato"
    SET_PRIORITY = "set_priority"  # A2, A4, A6 priorities


class StrategicLevel(CommandInterface):
    """Nivel de comando Estratégico"""

    def __init__(self, side: Side, simulation_engine):
        super().__init__(side)
        self.simulation_engine = simulation_engine
        self.strategic_objectives: List[Dict] = []
        self.resource_allocations: Dict[str, float] = {}

    def get_level(self) -> CommandLevel:
        return CommandLevel.STRATEGIC

    def get_available_commands(self) -> List[str]:
        return [
            StrategicCommands.SET_ROE,
            StrategicCommands.SET_STRATEGIC_OBJECTIVE,
            StrategicCommands.ALLOCATE_RESOURCES,
            StrategicCommands.APPROVE_ATO,
            StrategicCommands.REJECT_ATO,
            StrategicCommands.SET_PRIORITY,
        ]

    def _get_required_permission(self, command_type: str) -> Optional[Permission]:
        mapping = {
            StrategicCommands.SET_ROE: Permission.SET_ROE,
            StrategicCommands.SET_STRATEGIC_OBJECTIVE: Permission.SET_STRATEGIC_OBJECTIVES,
            StrategicCommands.ALLOCATE_RESOURCES: Permission.ALLOCATE_RESOURCES,
            StrategicCommands.APPROVE_ATO: Permission.APPROVE_ATO,
            StrategicCommands.REJECT_ATO: Permission.APPROVE_ATO,
            StrategicCommands.SET_PRIORITY: Permission.ALLOCATE_RESOURCES,
        }
        return mapping.get(command_type)

    def execute_command(self, command: Command) -> CommandResult:
        command_type = command.command_type
        data = command.data

        try:
            if command_type == StrategicCommands.SET_ROE:
                return self._set_roe(data.get("roe"))

            elif command_type == StrategicCommands.SET_STRATEGIC_OBJECTIVE:
                return self._set_strategic_objective(
                    objective_type=data.get("objective_type"),
                    target=data.get("target"),
                    priority=data.get("priority", "MEDIUM"),
                )

            elif command_type == StrategicCommands.APPROVE_ATO:
                return self._approve_ato(data.get("ato_id"))

            elif command_type == StrategicCommands.REJECT_ATO:
                return self._reject_ato(data.get("ato_id"), data.get("reason"))

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

    def _set_roe(self, roe: str) -> CommandResult:
        """Establece Rules of Engagement"""
        self.simulation_engine.config.roe = roe
        return CommandResult(
            success=True,
            message=f"ROE set to {roe}",
            data={"roe": roe},
        )

    def _set_strategic_objective(
        self,
        objective_type: str,
        target: Dict,
        priority: str
    ) -> CommandResult:
        """Define objetivo estratégico"""
        objective = {
            "type": objective_type,
            "target": target,
            "priority": priority,
            "status": "ACTIVE",
        }
        self.strategic_objectives.append(objective)

        return CommandResult(
            success=True,
            message=f"Strategic objective set: {objective_type}",
            data=objective,
        )

    def _approve_ato(self, ato_id: str) -> CommandResult:
        """Aprueba Air Tasking Order"""
        # Obtener módulo A3
        staff_module = self.simulation_engine.get_module("staff")
        if not staff_module:
            return CommandResult(
                success=False,
                message="Staff module not available",
            )

        # Aprobar ATO
        # TODO: Implementar lógica de aprobación en A3

        return CommandResult(
            success=True,
            message=f"ATO {ato_id} approved",
            data={"ato_id": ato_id, "status": "APPROVED"},
        )

    def _reject_ato(self, ato_id: str, reason: str) -> CommandResult:
        """Rechaza Air Tasking Order"""
        return CommandResult(
            success=True,
            message=f"ATO {ato_id} rejected: {reason}",
            data={"ato_id": ato_id, "status": "REJECTED", "reason": reason},
        )

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "strategic_objectives": len(self.strategic_objectives),
            "roe": self.simulation_engine.config.roe,
        })
        return status
