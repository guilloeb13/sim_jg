"""
Motor principal de simulación GAVILAN
"""

import asyncio
import time
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from gavilan.core.config import GavilanConfig
from gavilan.core.events import EventBus, Event, EventType, event_bus
from gavilan.core.entities import Entity, Aircraft, Radar, CommandCenter, Side


@dataclass
class SimulationState:
    """Estado actual de la simulación"""
    running: bool = False
    paused: bool = False
    elapsed_time: float = 0.0
    current_tick: int = 0
    start_time: datetime = None
    end_time: datetime = None


class SimulationEngine:
    """Motor principal que coordina todos los módulos de simulación"""

    def __init__(self, config: GavilanConfig = None):
        self.config = config or GavilanConfig()
        self.state = SimulationState()
        self.event_bus = event_bus

        # Entidades
        self._entities: dict[str, Entity] = {}
        self._blue_forces: dict[str, Entity] = {}
        self._red_forces: dict[str, Entity] = {}

        # Módulos (se cargan dinámicamente)
        self._modules: dict[str, object] = {}

        # Métricas
        self._metrics: dict = {
            "total_ticks": 0,
            "events_processed": 0,
            "aircraft_destroyed": 0,
            "missiles_fired": 0,
        }

    def register_module(self, name: str, module):
        """Registra un módulo en el motor"""
        self._modules[name] = module
        print(f"Módulo '{name}' registrado")

    def add_entity(self, entity: Entity):
        """Añade una entidad a la simulación"""
        self._entities[entity.entity_id] = entity

        if entity.side == Side.BLUE:
            self._blue_forces[entity.entity_id] = entity
        elif entity.side == Side.RED:
            self._red_forces[entity.entity_id] = entity

        # Publicar evento
        self.event_bus.publish(Event(
            event_type=EventType.AIRCRAFT_SPAWN,
            source="engine",
            data={"entity_id": entity.entity_id, "entity_type": entity.entity_type.value}
        ))

    def remove_entity(self, entity_id: str):
        """Elimina una entidad de la simulación"""
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            del self._entities[entity_id]

            if entity_id in self._blue_forces:
                del self._blue_forces[entity_id]
            if entity_id in self._red_forces:
                del self._red_forces[entity_id]

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Obtiene una entidad por ID"""
        return self._entities.get(entity_id)

    def get_entities_by_type(self, entity_type) -> list[Entity]:
        """Obtiene todas las entidades de un tipo"""
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def get_entities_by_side(self, side: Side) -> list[Entity]:
        """Obtiene todas las entidades de un bando"""
        if side == Side.BLUE:
            return list(self._blue_forces.values())
        elif side == Side.RED:
            return list(self._red_forces.values())
        return [e for e in self._entities.values() if e.side == side]

    def start(self):
        """Inicia la simulación"""
        self.state.running = True
        self.state.paused = False
        self.state.start_time = datetime.now()
        self.state.elapsed_time = 0

        self.event_bus.publish(Event(
            event_type=EventType.SIMULATION_START,
            source="engine",
            data={"config": self.config.to_dict()}
        ))

        print(f"Simulación '{self.config.scenario_name}' iniciada")

    def pause(self):
        """Pausa la simulación"""
        self.state.paused = True
        self.event_bus.publish(Event(
            event_type=EventType.SIMULATION_PAUSE,
            source="engine"
        ))

    def resume(self):
        """Reanuda la simulación"""
        self.state.paused = False

    def stop(self):
        """Detiene la simulación"""
        self.state.running = False
        self.state.end_time = datetime.now()

        self.event_bus.publish(Event(
            event_type=EventType.SIMULATION_END,
            source="engine",
            data={"elapsed_time": self.state.elapsed_time}
        ))

        print(f"Simulación terminada. Tiempo: {self.state.elapsed_time:.2f}s")

    def tick(self):
        """Ejecuta un paso de simulación"""
        if not self.state.running or self.state.paused:
            return

        dt = self.config.time_step_seconds * self.config.simulation_speed
        self.state.elapsed_time += dt
        self.state.current_tick += 1

        # Actualizar todas las entidades
        for entity in self._entities.values():
            entity.update_position(dt)

        # Actualizar módulos
        for name, module in self._modules.items():
            if hasattr(module, 'update'):
                try:
                    module.update(dt, self)
                except Exception as e:
                    print(f"Error actualizando módulo {name}: {e}")

        # Publicar evento de tick
        self.event_bus.publish(Event(
            event_type=EventType.TIME_TICK,
            source="engine",
            data={
                "tick": self.state.current_tick,
                "elapsed": self.state.elapsed_time
            }
        ))

        self._metrics["total_ticks"] += 1

        # Verificar fin de simulación
        max_seconds = self.config.max_duration_hours * 3600
        if self.state.elapsed_time >= max_seconds:
            self.stop()

    async def run_async(self):
        """Ejecuta la simulación de forma asíncrona"""
        self.start()

        while self.state.running:
            if not self.state.paused:
                self.tick()

            # Esperar según velocidad de simulación
            await asyncio.sleep(self.config.time_step_seconds / self.config.simulation_speed)

    def run(self, ticks: int = None):
        """Ejecuta la simulación de forma síncrona"""
        self.start()

        tick_count = 0
        while self.state.running:
            if ticks and tick_count >= ticks:
                break

            self.tick()
            tick_count += 1

            time.sleep(self.config.time_step_seconds / self.config.simulation_speed)

    def get_metrics(self) -> dict:
        """Obtiene métricas de la simulación"""
        return {
            **self._metrics,
            "elapsed_time": self.state.elapsed_time,
            "total_entities": len(self._entities),
            "blue_forces": len(self._blue_forces),
            "red_forces": len(self._red_forces),
        }

    def get_state_snapshot(self) -> dict:
        """Obtiene una instantánea del estado actual"""
        return {
            "state": {
                "running": self.state.running,
                "paused": self.state.paused,
                "elapsed_time": self.state.elapsed_time,
                "current_tick": self.state.current_tick,
            },
            "entities": {
                eid: {
                    "name": e.name,
                    "type": e.entity_type.value,
                    "side": e.side.value,
                    "position": {
                        "lat": e.position.latitude,
                        "lon": e.position.longitude,
                        "alt": e.position.altitude_ft
                    },
                    "active": e.active,
                    "health": e.health
                }
                for eid, e in self._entities.items()
            },
            "metrics": self.get_metrics()
        }
