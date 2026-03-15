"""
IA para Insurgentes (Conflicto Interno)

Controla comportamiento asimétrico de insurgentes/terroristas.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class InsurgentTactic(str, Enum):
    """Tácticas insurgentes"""
    IED_AMBUSH = "ied_ambush"
    MANPADS_ATTACK = "manpads_attack"
    SMALL_ARMS_FIRE = "small_arms_fire"
    MORTAR_ATTACK = "mortar_attack"
    KIDNAPPING = "kidnapping"
    PROPAGANDA = "propaganda"
    RECRUITMENT = "recruitment"
    SUPPLY_RUN = "supply_run"
    HIDE = "hide"


class CellStatus(str, Enum):
    """Estados de célula insurgente"""
    ACTIVE = "active"
    HIDING = "hiding"
    COMPROMISED = "compromised"
    DISBANDED = "disbanded"


@dataclass
class InsurgentCell:
    """Célula insurgente"""
    id: str
    location: Dict[str, float]
    members: int
    weapons: Dict[str, int] = field(default_factory=dict)
    morale: float = 0.8  # 0-1
    status: CellStatus = CellStatus.ACTIVE
    last_activity: Optional[datetime] = None
    heat_level: float = 0.0  # 0-1 (qué tan buscada está)

    def is_operational(self) -> bool:
        return self.status == CellStatus.ACTIVE and self.morale > 0.3 and self.members > 0


@dataclass
class InsurgentProfile:
    """Perfil de comportamiento insurgente"""
    name: str
    aggressiveness: float  # 0-1
    caution: float  # 0-1
    resources: float  # 0-1
    popular_support: float  # 0-1
    intelligence_capability: float  # 0-1


class InsurgentAI:
    """
    IA para insurgentes en conflicto interno

    Comportamiento asimétrico:
    - Evitan confrontación directa
    - Usan tácticas de guerrilla
    - Explotan debilidades
    - Propaganda y reclutamiento
    """

    def __init__(self, profile: InsurgentProfile):
        self.profile = profile
        self.cells: List[InsurgentCell] = []
        self.safe_houses: List[Dict] = []
        self.recent_attacks: List[Dict] = []
        self.propaganda_score: float = 0.0

    def initialize(self, num_cells: int = 5):
        """Inicializa células insurgentes"""
        for i in range(num_cells):
            cell = InsurgentCell(
                id=f"CELL-{i+1}",
                location=self._random_location(),
                members=random.randint(5, 15),
                weapons={
                    "small_arms": random.randint(3, 10),
                    "rpg": random.randint(0, 2),
                    "manpads": random.randint(0, 1) if self.profile.resources > 0.7 else 0,
                    "mortars": random.randint(0, 2),
                    "ied": random.randint(2, 8),
                },
                morale=self.profile.popular_support,
            )
            self.cells.append(cell)

    def _random_location(self) -> Dict[str, float]:
        """Genera ubicación aleatoria"""
        # TODO: Usar áreas reales del escenario
        return {
            "lat": random.uniform(4.0, 5.0),
            "lon": random.uniform(-75.0, -74.0),
        }

    def update(self, game_state: Dict):
        """
        Actualiza IA insurgente cada tick

        Args:
            game_state: Estado actual del juego
        """
        # 1. Evaluar situación
        blue_forces = self._detect_blue_forces(game_state)

        # 2. Actualizar heat level de células
        self._update_heat_levels(blue_forces)

        # 3. Tomar decisiones por célula
        for cell in self.cells:
            if not cell.is_operational():
                continue

            # Decidir acción
            action = self._decide_action(cell, blue_forces)

            # Ejecutar acción
            if action:
                self._execute_action(cell, action, game_state)

        # 4. Reclutamiento y propaganda
        if random.random() < 0.1:  # 10% chance cada tick
            self._conduct_recruitment()

        # 5. Explotación de daños colaterales
        if game_state.get("collateral_damage_occurred"):
            self._exploit_collateral_damage()

    def _detect_blue_forces(self, game_state: Dict) -> List[Dict]:
        """Detecta fuerzas BLUE mediante inteligencia"""
        blue_forces = []

        # Capacidad de inteligencia limitada
        detection_chance = self.profile.intelligence_capability

        for aircraft in game_state.get("aircraft", []):
            if aircraft["side"] == "blue":
                if random.random() < detection_chance:
                    blue_forces.append(aircraft)

        return blue_forces

    def _update_heat_levels(self, blue_forces: List[Dict]):
        """Actualiza nivel de presión sobre células"""
        for cell in self.cells:
            # Decaer heat con el tiempo
            cell.heat_level *= 0.95

            # Aumentar si fuerzas BLUE cerca
            for force in blue_forces:
                distance = self._calculate_distance(cell.location, force["position"])
                if distance < 50:  # 50km
                    cell.heat_level = min(cell.heat_level + 0.1, 1.0)

            # Si heat muy alto, esconderse
            if cell.heat_level > 0.7 and cell.status == CellStatus.ACTIVE:
                cell.status = CellStatus.HIDING

            # Si heat baja, reactivar
            if cell.heat_level < 0.3 and cell.status == CellStatus.HIDING:
                cell.status = CellStatus.ACTIVE

    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Calcula distancia (simplificado)"""
        import math
        dlat = loc2.get("lat", 0) - loc1["lat"]
        dlon = loc2.get("lon", 0) - loc1["lon"]
        return math.sqrt(dlat**2 + dlon**2) * 111

    def _decide_action(self, cell: InsurgentCell, blue_forces: List[Dict]) -> Optional[InsurgentTactic]:
        """Decide acción para una célula"""
        # Si está escondida, no actuar
        if cell.status == CellStatus.HIDING:
            return None

        # Si heat muy alto, esconderse
        if cell.heat_level > 0.8:
            return InsurgentTactic.HIDE

        # Buscar oportunidades
        opportunities = self._find_opportunities(cell, blue_forces)

        if not opportunities:
            # Sin oportunidades, actividades de soporte
            return random.choice([
                InsurgentTactic.PROPAGANDA,
                InsurgentTactic.RECRUITMENT,
                InsurgentTactic.SUPPLY_RUN,
            ])

        # Decidir basado en agresividad y cautela
        risk_level = opportunities[0]["risk"]

        if risk_level > self.profile.caution:
            # Muy riesgoso, evitar
            return None

        if random.random() < self.profile.aggressiveness:
            return opportunities[0]["tactic"]

        return None

    def _find_opportunities(self, cell: InsurgentCell, blue_forces: List[Dict]) -> List[Dict]:
        """Encuentra oportunidades de ataque"""
        opportunities = []

        for force in blue_forces:
            distance = self._calculate_distance(cell.location, force["position"])

            # MANPADS contra aeronaves bajas
            if (cell.weapons.get("manpads", 0) > 0 and
                distance < 10 and
                force["position"]["alt_ft"] < 5000):
                opportunities.append({
                    "tactic": InsurgentTactic.MANPADS_ATTACK,
                    "target": force,
                    "risk": 0.6,
                })

            # Morteros contra bases
            if (cell.weapons.get("mortars", 0) > 0 and
                10 < distance < 30):
                opportunities.append({
                    "tactic": InsurgentTactic.MORTAR_ATTACK,
                    "target": force,
                    "risk": 0.4,
                })

        # Ordenar por menor riesgo
        opportunities.sort(key=lambda o: o["risk"])
        return opportunities

    def _execute_action(self, cell: InsurgentCell, tactic: InsurgentTactic, game_state: Dict):
        """Ejecuta acción insurgente"""
        if tactic == InsurgentTactic.MANPADS_ATTACK:
            self._execute_manpads_attack(cell)

        elif tactic == InsurgentTactic.MORTAR_ATTACK:
            self._execute_mortar_attack(cell)

        elif tactic == InsurgentTactic.IED_AMBUSH:
            self._plant_ied(cell)

        elif tactic == InsurgentTactic.PROPAGANDA:
            self._conduct_propaganda()

        elif tactic == InsurgentTactic.HIDE:
            cell.status = CellStatus.HIDING

        # Registrar actividad
        cell.last_activity = datetime.now()

        # Aumentar heat después de acción ofensiva
        if tactic in [InsurgentTactic.MANPADS_ATTACK, InsurgentTactic.MORTAR_ATTACK, InsurgentTactic.IED_AMBUSH]:
            cell.heat_level = min(cell.heat_level + 0.3, 1.0)

    def _execute_manpads_attack(self, cell: InsurgentCell):
        """Ejecuta ataque con MANPADS"""
        if cell.weapons["manpads"] > 0:
            cell.weapons["manpads"] -= 1
            # TODO: Crear evento de ataque
            self.recent_attacks.append({
                "type": "manpads",
                "cell_id": cell.id,
                "timestamp": datetime.now(),
            })

    def _execute_mortar_attack(self, cell: InsurgentCell):
        """Ejecuta ataque con mortero"""
        if cell.weapons["mortars"] > 0:
            # TODO: Crear evento de ataque
            self.recent_attacks.append({
                "type": "mortar",
                "cell_id": cell.id,
                "timestamp": datetime.now(),
            })

    def _plant_ied(self, cell: InsurgentCell):
        """Planta IED en ruta"""
        if cell.weapons["ied"] > 0:
            cell.weapons["ied"] -= 1
            # TODO: Crear IED en mapa

    def _conduct_propaganda(self):
        """Realiza propaganda"""
        self.propaganda_score += 0.1 * self.profile.popular_support

    def _conduct_recruitment(self):
        """Recluta nuevos miembros"""
        if self.propaganda_score > 0.5:
            # Agregar miembros a células operacionales
            for cell in self.cells:
                if cell.is_operational():
                    new_recruits = random.randint(1, 3)
                    cell.members += new_recruits
                    break

            self.propaganda_score *= 0.8  # Consumir propaganda

    def _exploit_collateral_damage(self):
        """Explota daño colateral para propaganda"""
        self.propaganda_score += 0.3
        self.profile.popular_support = min(self.profile.popular_support + 0.1, 1.0)

        # Aumentar moral de células
        for cell in self.cells:
            cell.morale = min(cell.morale + 0.1, 1.0)

    def get_status(self) -> Dict:
        """Retorna estado de la insurgencia"""
        return {
            "profile": self.profile.name,
            "total_cells": len(self.cells),
            "active_cells": sum(1 for c in self.cells if c.is_operational()),
            "hiding_cells": sum(1 for c in self.cells if c.status == CellStatus.HIDING),
            "total_members": sum(c.members for c in self.cells),
            "propaganda_score": self.propaganda_score,
            "popular_support": self.profile.popular_support,
            "recent_attacks": len([a for a in self.recent_attacks if (datetime.now() - a["timestamp"]).seconds < 3600]),
        }
