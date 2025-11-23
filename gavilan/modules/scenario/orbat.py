"""
Orden de Batalla (ORBAT) - Organización de fuerzas
"""

from dataclasses import dataclass, field
from typing import Optional

from gavilan.core.entities import (
    Entity, Aircraft, Radar, CommandCenter, SAMSite, Airbase, Side
)


@dataclass
class ForceComposition:
    """Composición de una fuerza"""
    aircraft: list[Aircraft] = field(default_factory=list)
    radars: list[Radar] = field(default_factory=list)
    sam_sites: list[SAMSite] = field(default_factory=list)
    command_centers: list[CommandCenter] = field(default_factory=list)
    airbases: list[Airbase] = field(default_factory=list)

    def get_total_count(self) -> int:
        """Retorna el total de entidades"""
        return (
            len(self.aircraft) +
            len(self.radars) +
            len(self.sam_sites) +
            len(self.command_centers) +
            len(self.airbases)
        )


@dataclass
class OrderOfBattle:
    """Orden de Batalla completo para un bando"""
    side: Side
    name: str = ""
    composition: ForceComposition = field(default_factory=ForceComposition)

    # Organización por unidades
    squadrons: dict = field(default_factory=dict)
    wings: dict = field(default_factory=dict)

    def add_aircraft(self, aircraft: Aircraft):
        """Añade una aeronave al ORBAT"""
        aircraft.side = self.side
        self.composition.aircraft.append(aircraft)

    def add_radar(self, radar: Radar):
        """Añade un radar al ORBAT"""
        radar.side = self.side
        self.composition.radars.append(radar)

    def add_sam_site(self, sam: SAMSite):
        """Añade un sitio SAM al ORBAT"""
        sam.side = self.side
        self.composition.sam_sites.append(sam)

    def add_command_center(self, cc: CommandCenter):
        """Añade un centro de mando al ORBAT"""
        cc.side = self.side
        self.composition.command_centers.append(cc)

    def add_airbase(self, airbase: Airbase):
        """Añade una base aérea al ORBAT"""
        airbase.side = self.side
        self.composition.airbases.append(airbase)

    def get_all_entities(self) -> list[Entity]:
        """Retorna todas las entidades del ORBAT"""
        entities = []
        entities.extend(self.composition.aircraft)
        entities.extend(self.composition.radars)
        entities.extend(self.composition.sam_sites)
        entities.extend(self.composition.command_centers)
        entities.extend(self.composition.airbases)
        return entities

    def get_aircraft_by_role(self, role) -> list[Aircraft]:
        """Retorna aeronaves por rol"""
        return [a for a in self.composition.aircraft if a.role == role]

    def get_operational_aircraft(self) -> list[Aircraft]:
        """Retorna aeronaves operacionales"""
        return [
            a for a in self.composition.aircraft
            if a.active and not a.destroyed and a.maintenance_status == "operational"
        ]

    def get_summary(self) -> dict:
        """Retorna resumen del ORBAT"""
        return {
            "side": self.side.value,
            "total_aircraft": len(self.composition.aircraft),
            "operational_aircraft": len(self.get_operational_aircraft()),
            "radars": len(self.composition.radars),
            "sam_sites": len(self.composition.sam_sites),
            "command_centers": len(self.composition.command_centers),
            "airbases": len(self.composition.airbases),
            "total_entities": self.composition.get_total_count()
        }

    def to_dict(self) -> dict:
        """Convierte el ORBAT a diccionario"""
        return {
            "side": self.side.value,
            "name": self.name,
            "aircraft": [
                {
                    "id": a.entity_id,
                    "callsign": a.callsign,
                    "type": a.aircraft_type,
                    "role": a.role.value,
                    "position": {
                        "lat": a.position.latitude,
                        "lon": a.position.longitude,
                        "alt": a.position.altitude_ft
                    }
                }
                for a in self.composition.aircraft
            ],
            "radars": [
                {
                    "id": r.entity_id,
                    "name": r.name,
                    "type": r.radar_type,
                    "range_km": r.max_range_km
                }
                for r in self.composition.radars
            ],
            "sam_sites": [
                {
                    "id": s.entity_id,
                    "name": s.name,
                    "type": s.sam_type,
                    "range_km": s.max_range_km,
                    "missiles": s.missiles_available
                }
                for s in self.composition.sam_sites
            ],
            "summary": self.get_summary()
        }
