#!/usr/bin/env python3
"""
Script de inicio para servidor GAVILAN Multiplayer

Inicia el servidor FastAPI con WebSocket y API REST.
"""

import uvicorn
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Inicia el servidor"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║            🛩️  GAVILAN MULTIPLAYER SERVER                   ║
    ║                                                              ║
    ║  Simulador de Guerra Aérea Multinivel y Multijugador        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

    📡 Starting server...

    WebSocket endpoint:  ws://localhost:8000/ws
    API REST:            http://localhost:8000/api
    Documentation:       http://localhost:8000/docs
    Health check:        http://localhost:8000/health
    Frontend portal:     http://localhost:8000

    Press CTRL+C to stop the server.
    """)

    # Configuración del servidor
    uvicorn.run(
        "gavilan.server.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
