"""
FastAPI Application para GAVILAN Multiplayer

Expone:
- WebSocket endpoint para tiempo real
- API REST para administración
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from gavilan.server.websocket import get_websocket_server
from .routes import auth, sessions, users, scenarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager para la aplicación

    Inicia el tick loop en background.
    """
    # Startup
    ws_server = get_websocket_server()

    # Iniciar tick loop en background
    tick_task = asyncio.create_task(ws_server.tick_all_sessions())

    yield

    # Shutdown
    tick_task.cancel()
    try:
        await tick_task
    except asyncio.CancelledError:
        pass


# Crear aplicación FastAPI
app = FastAPI(
    title="GAVILAN Multiplayer Server",
    description="Servidor multiplayer para simulador militar GAVILAN",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (ajustar origins en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para comunicación en tiempo real

    Protocolo:
    1. Cliente conecta
    2. Cliente envía AUTHENTICATE con JWT token
    3. Servidor valida y confirma con AUTHENTICATED
    4. Cliente puede enviar JOIN_SESSION, EXECUTE_COMMAND, etc.
    5. Servidor envía STATE_UPDATE periódicamente
    """
    ws_server = get_websocket_server()
    await ws_server.handle_client(websocket)


# Incluir routers de API REST
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from gavilan.multiplayer.session import get_session_manager

    session_manager = get_session_manager()
    stats = session_manager.get_stats()

    return {
        "status": "healthy",
        "sessions": stats,
    }


# Root
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "GAVILAN Multiplayer Server",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws",
            "api": "/api",
            "docs": "/docs",
            "health": "/health",
        }
    }
