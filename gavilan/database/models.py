"""
Modelos de base de datos SQLAlchemy
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Scenario(Base):
    """Modelo de escenario"""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    mode = Column(String(50))
    difficulty = Column(String(50))

    # Área geográfica
    center_lat = Column(Float)
    center_lon = Column(Float)
    radius_km = Column(Float)

    # Configuración
    config_json = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    missions = relationship("Mission", back_populates="scenario")
    entities = relationship("Entity", back_populates="scenario")


class Mission(Base):
    """Modelo de misión"""
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)
    mission_id = Column(String(50), unique=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))

    mission_type = Column(String(50))
    priority = Column(Integer)
    status = Column(String(50))
    callsign = Column(String(50))

    # Tiempos
    planned_takeoff = Column(DateTime)
    actual_takeoff = Column(DateTime)
    planned_rtb = Column(DateTime)
    actual_rtb = Column(DateTime)

    # Resultados
    objectives_achieved = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    damage_assessment = Column(Text)

    # Datos adicionales
    mission_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    scenario = relationship("Scenario", back_populates="missions")


class Entity(Base):
    """Modelo de entidad"""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    entity_id = Column(String(50), unique=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))

    name = Column(String(200))
    entity_type = Column(String(50))
    side = Column(String(20))

    # Posición inicial
    lat = Column(Float)
    lon = Column(Float)
    altitude_ft = Column(Float)

    # Estado
    active = Column(Boolean, default=True)
    destroyed = Column(Boolean, default=False)
    health = Column(Float, default=100)

    # Datos adicionales
    entity_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    scenario = relationship("Scenario", back_populates="entities")


class Event(Base):
    """Modelo de evento"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), unique=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))

    event_type = Column(String(100))
    source = Column(String(100))
    target = Column(String(100))
    priority = Column(Integer)

    # Datos
    event_data = Column(JSON)

    timestamp = Column(DateTime, default=datetime.utcnow)


class Score(Base):
    """Modelo de puntaje"""
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    team_id = Column(String(50))

    # Puntajes
    total_score = Column(Float, default=0)
    operations_score = Column(Float, default=0)
    logistics_score = Column(Float, default=0)
    intel_score = Column(Float, default=0)
    cyber_score = Column(Float, default=0)
    comm_score = Column(Float, default=0)
    personnel_score = Column(Float, default=0)

    # Métricas
    missions_completed = Column(Integer, default=0)
    aircraft_lost = Column(Integer, default=0)
    enemy_destroyed = Column(Integer, default=0)

    # CTF
    flags_captured = Column(Integer, default=0)
    challenges_completed = Column(Integer, default=0)

    grade = Column(String(5))

    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Log de auditoría"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String(100))
    user_id = Column(String(100))
    entity_type = Column(String(100))
    entity_id = Column(String(100))
    old_value = Column(JSON)
    new_value = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SpaceWeatherLog(Base):
    """Log de clima espacial"""
    __tablename__ = "space_weather_logs"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))

    kp_index = Column(Float)
    dst_index = Column(Float)
    solar_wind_speed = Column(Float)
    xray_flux = Column(Float)

    storm_level = Column(String(50))
    operational_impacts = Column(JSON)

    timestamp = Column(DateTime, default=datetime.utcnow)


class CyberIncident(Base):
    """Incidente de ciberseguridad"""
    __tablename__ = "cyber_incidents"

    id = Column(Integer, primary_key=True)
    incident_id = Column(String(50), unique=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))

    attack_type = Column(String(100))
    target_system = Column(String(100))
    severity = Column(Integer)

    detected = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
    mitigated = Column(Boolean, default=False)

    impact_score = Column(Float)
    incident_data = Column(JSON)

    timestamp = Column(DateTime, default=datetime.utcnow)
    resolution_time = Column(DateTime)
