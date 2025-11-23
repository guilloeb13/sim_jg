"""
A1 - Sección de Personal
========================

Gestiona:
- Disponibilidad del personal (pilotos, mecánicos, operadores)
- Fatiga y turnos
- Redistribución de recursos humanos
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random

from gavilan.core.events import Event, EventType, event_bus


class PersonnelStatus(Enum):
    """Estado del personal"""
    AVAILABLE = "available"
    ON_MISSION = "on_mission"
    RESTING = "resting"
    FATIGUED = "fatigued"
    INJURED = "injured"
    UNAVAILABLE = "unavailable"


class PersonnelRole(Enum):
    """Roles del personal"""
    PILOT = "pilot"
    COPILOT = "copilot"
    WSO = "weapon_systems_officer"
    CREW_CHIEF = "crew_chief"
    MECHANIC = "mechanic"
    RADAR_OPERATOR = "radar_operator"
    CONTROLLER = "air_controller"
    INTEL_ANALYST = "intel_analyst"
    COMM_SPECIALIST = "comm_specialist"


@dataclass
class Personnel:
    """Representa un miembro del personal"""
    personnel_id: str
    name: str
    rank: str
    role: PersonnelRole
    status: PersonnelStatus = PersonnelStatus.AVAILABLE

    # Fatiga y estado físico
    fatigue_level: float = 0.0  # 0-100
    max_fatigue: float = 80.0
    hours_on_duty: float = 0.0
    max_duty_hours: float = 12.0

    # Habilidades
    skill_level: float = 0.8  # 0-1
    experience_missions: int = 0

    # Asignación
    assigned_to: str = ""  # ID de aeronave o estación
    shift: int = 1  # Turno 1, 2 o 3


class PersonnelSection:
    """Sección A1 - Gestión de Personal"""

    def __init__(self):
        self.event_bus = event_bus
        self._personnel: dict[str, Personnel] = {}
        self._shifts = {1: [], 2: [], 3: []}
        self._current_shift = 1
        self._shift_duration_hours = 8.0
        self._time_in_shift = 0.0

    def add_personnel(self, person: Personnel):
        """Añade personal al sistema"""
        self._personnel[person.personnel_id] = person
        self._shifts[person.shift].append(person.personnel_id)

    def get_available_by_role(self, role: PersonnelRole) -> list[Personnel]:
        """Obtiene personal disponible por rol"""
        return [
            p for p in self._personnel.values()
            if p.role == role and p.status == PersonnelStatus.AVAILABLE
        ]

    def assign_to_mission(self, personnel_id: str, mission_id: str) -> bool:
        """Asigna personal a una misión"""
        if personnel_id not in self._personnel:
            return False

        person = self._personnel[personnel_id]

        if person.status != PersonnelStatus.AVAILABLE:
            return False

        if person.fatigue_level >= person.max_fatigue:
            self.event_bus.publish(Event(
                event_type=EventType.PERSONNEL_FATIGUE,
                source="A1",
                data={"personnel_id": personnel_id, "fatigue": person.fatigue_level}
            ))
            return False

        person.status = PersonnelStatus.ON_MISSION
        person.assigned_to = mission_id
        return True

    def release_from_mission(self, personnel_id: str):
        """Libera personal de una misión"""
        if personnel_id in self._personnel:
            person = self._personnel[personnel_id]
            person.status = PersonnelStatus.AVAILABLE
            person.assigned_to = ""
            person.experience_missions += 1

            # Aumentar fatiga
            person.fatigue_level = min(100, person.fatigue_level + 15)

    def update(self, dt: float, engine):
        """Actualiza estado del personal"""
        hours = dt / 3600

        for person in self._personnel.values():
            # Actualizar horas de servicio
            if person.status in [PersonnelStatus.AVAILABLE, PersonnelStatus.ON_MISSION]:
                person.hours_on_duty += hours

                # Aumentar fatiga gradualmente
                fatigue_rate = 2.0 if person.status == PersonnelStatus.ON_MISSION else 1.0
                person.fatigue_level = min(100, person.fatigue_level + fatigue_rate * hours)

                # Verificar límite de horas
                if person.hours_on_duty >= person.max_duty_hours:
                    if person.status == PersonnelStatus.AVAILABLE:
                        person.status = PersonnelStatus.RESTING

            # Recuperación durante descanso
            elif person.status == PersonnelStatus.RESTING:
                person.fatigue_level = max(0, person.fatigue_level - 5 * hours)
                if person.fatigue_level < 20:
                    person.status = PersonnelStatus.AVAILABLE
                    person.hours_on_duty = 0

        # Gestión de turnos
        self._time_in_shift += hours
        if self._time_in_shift >= self._shift_duration_hours:
            self._rotate_shifts()

    def _rotate_shifts(self):
        """Rota los turnos de trabajo"""
        self._current_shift = (self._current_shift % 3) + 1
        self._time_in_shift = 0

        # Enviar a descanso al turno saliente
        outgoing_shift = ((self._current_shift - 2) % 3) + 1
        for pid in self._shifts[outgoing_shift]:
            if self._personnel[pid].status == PersonnelStatus.AVAILABLE:
                self._personnel[pid].status = PersonnelStatus.RESTING

        # Activar turno entrante
        for pid in self._shifts[self._current_shift]:
            p = self._personnel[pid]
            if p.status == PersonnelStatus.RESTING and p.fatigue_level < 50:
                p.status = PersonnelStatus.AVAILABLE
                p.hours_on_duty = 0

        self.event_bus.publish(Event(
            event_type=EventType.SHIFT_CHANGE,
            source="A1",
            data={"new_shift": self._current_shift}
        ))

    def get_status(self) -> dict:
        """Obtiene estado de la sección"""
        by_status = {}
        by_role = {}

        for p in self._personnel.values():
            status = p.status.value
            role = p.role.value

            by_status[status] = by_status.get(status, 0) + 1
            by_role[role] = by_role.get(role, 0) + 1

        return {
            "total_personnel": len(self._personnel),
            "by_status": by_status,
            "by_role": by_role,
            "current_shift": self._current_shift,
            "average_fatigue": sum(p.fatigue_level for p in self._personnel.values()) / max(1, len(self._personnel))
        }

    def get_readiness(self) -> float:
        """Calcula nivel de preparación de personal"""
        if not self._personnel:
            return 0.0

        available = sum(1 for p in self._personnel.values() if p.status == PersonnelStatus.AVAILABLE)
        avg_fatigue = sum(p.fatigue_level for p in self._personnel.values()) / len(self._personnel)

        availability_score = available / len(self._personnel)
        fatigue_score = 1 - (avg_fatigue / 100)

        return (availability_score * 0.6 + fatigue_score * 0.4)

    def generate_personnel_roster(self, aircraft_count: int):
        """Genera roster de personal basado en necesidades"""
        roles_per_aircraft = [
            (PersonnelRole.PILOT, 2),
            (PersonnelRole.CREW_CHIEF, 1),
            (PersonnelRole.MECHANIC, 2),
        ]

        personnel_id = 1
        for _ in range(aircraft_count):
            for role, count in roles_per_aircraft:
                for _ in range(count):
                    for shift in [1, 2, 3]:
                        person = Personnel(
                            personnel_id=f"PER-{personnel_id:04d}",
                            name=f"Personal {personnel_id}",
                            rank="SGT" if role in [PersonnelRole.MECHANIC, PersonnelRole.CREW_CHIEF] else "LT",
                            role=role,
                            shift=shift,
                            skill_level=random.uniform(0.6, 0.95)
                        )
                        self.add_personnel(person)
                        personnel_id += 1
