"""
API REST de GAVILAN
===================

Endpoints FastAPI para interactuar con el simulador
"""

from gavilan.api.main import create_app, app

__all__ = ["create_app", "app"]
