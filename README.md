# GAVILAN - Sistema de Simulación de Juegos de Guerra Aérea

Sistema modular para entrenamiento de Fuerza Aérea que simula operaciones aéreas, ciberdefensa, clima espacial y roles del Estado Mayor (A1-A6).

## Características

- **Simulación de Operaciones Aéreas**: Cinemática de aeronaves, combate BVR/WVR, detección radar
- **Estado Mayor Completo (A1-A6)**: Personal, Inteligencia, Operaciones, Logística, Comunicaciones, Ciberdefensa
- **Clima Espacial**: Simulación de tormentas geomagnéticas, degradación GPS, impacto en comunicaciones
- **Ciberdefensa**: Ataques DDoS, intrusión SCADA, defensa en profundidad
- **Entrenamiento CTF**: Desafíos de ciberseguridad militar
- **API REST**: Endpoints completos con FastAPI

## Instalación

```bash
# Clonar repositorio
git clone [url-del-repositorio]
cd sim_jg

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso Rápido

### Ejecutar simulación de demostración:
```bash
python main.py
```

### Iniciar servidor API:
```bash
python main.py --api
```

La documentación de la API estará disponible en `http://localhost:8000/docs`

## Estructura del Proyecto

```
gavilan/
├── core/                    # Motor principal
│   ├── engine.py           # Motor de simulación
│   ├── config.py           # Configuración
│   ├── events.py           # Sistema de eventos
│   └── entities.py         # Entidades base
├── modules/
│   ├── scenario/           # Configuración de escenarios
│   ├── staff/              # Estado Mayor (A1-A6)
│   ├── space/              # Clima espacial
│   ├── cyber/              # Ciberdefensa
│   ├── air_simulation/     # Simulación aérea
│   ├── intelligence/       # Inteligencia operacional
│   ├── evaluation/         # Evaluación y puntaje
│   └── training/           # Entrenamiento CTF
├── api/                    # Endpoints FastAPI
├── database/               # Modelos y conexión BD
└── utils/                  # Utilidades
```

## Módulos del Estado Mayor

### A1 - Personal
- Gestión de disponibilidad de pilotos y personal
- Control de fatiga y turnos
- Redistribución de recursos humanos

### A2 - Inteligencia
- Fusión de sensores (radar, SIGINT, IMINT)
- Estimación de amenazas
- Inferencia de cursos de acción enemigos

### A3 - Operaciones
- Generación de ATO (Air Tasking Order)
- Control de misiones CAP, SEAD, CAS
- Gestión de SCRAMBLE

### A4 - Logística
- Inventario de combustible y armamento
- Programación de mantenimiento
- Disponibilidad de aeronaves

### A5 - Comunicaciones
- Estado de enlaces satelitales y radio
- Detección de jamming
- Gestión de redes

### A6 - Ciberdefensa
- Monitoreo de amenazas
- Defensa activa (firewall, IDS/IPS)
- Respuesta a incidentes

## API Endpoints Principales

```
POST /simulation/create     # Crear simulación
POST /simulation/start      # Iniciar simulación
GET  /simulation/state      # Estado actual
GET  /staff/status          # Estado del Estado Mayor
POST /staff/ato/generate    # Generar ATO
GET  /space-weather/status  # Clima espacial
POST /cyber/attack          # Simular ataque
GET  /intelligence/cop      # Common Operating Picture
GET  /evaluation/score      # Puntaje final
GET  /training/challenges   # Desafíos CTF
```

## Ejemplo de Uso con API

```python
import requests

# Crear simulación
response = requests.post("http://localhost:8000/simulation/create", json={
    "name": "Ejercicio Alpha",
    "center_lat": 4.6097,
    "center_lon": -74.0817,
    "mode": "training"
})

# Iniciar
requests.post("http://localhost:8000/simulation/start")

# Obtener estado
state = requests.get("http://localhost:8000/simulation/state").json()
```

## Escenarios Disponibles

1. **Defensa Aérea Básica** - Interceptación de amenazas
2. **Operación SEAD** - Supresión de defensas aéreas
3. **Ataque Cibernético a C2** - Defensa de centros de mando
4. **Tormenta Geomagnética** - Operaciones durante clima espacial severo

## Tecnologías

- Python 3.11+
- FastAPI
- SQLAlchemy
- NumPy
- Pydantic

## Licencia

Propiedad de la Fuerza Aérea - Uso exclusivo para entrenamiento militar

## Contacto

Para soporte técnico contactar al equipo de desarrollo.
