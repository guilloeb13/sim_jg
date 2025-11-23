"""
Conexión a base de datos
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from gavilan.database.models import Base

# URL por defecto (SQLite)
DATABASE_URL = "sqlite:///gavilan.db"

# Motor y sesión
engine = None
SessionLocal = None


def init_db(database_url: str = None):
    """Inicializa la base de datos"""
    global engine, SessionLocal

    url = database_url or DATABASE_URL

    # Crear motor
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(url)

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    # Crear session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine


def get_db() -> Generator[Session, None, None]:
    """Obtiene una sesión de base de datos"""
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager para sesiones de base de datos"""
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_db():
    """Reinicia la base de datos (elimina todas las tablas)"""
    global engine

    if engine:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
