# GAVILAN Multiplayer - Guía de Usuario

## Introducción

GAVILAN Multiplayer transforma el simulador en una plataforma **multinivel, multijugador y multiescenario** para entrenamiento de fuerzas aéreas.

### Características Principales

✅ **Multinivel**: 4 niveles de comando (Director, Estratégico, Operacional, Táctico)
✅ **Multijugador**: 2 bandos (BLUE vs RED) con equipos de hasta 6 jugadores
✅ **Multiescenario**: 3 tipos de juegos (Guerra Externa, Conflicto Interno, Gestión de Crisis)
✅ **Fog of War**: Visibilidad limitada por bando
✅ **Tiempo Real**: Sincronización mediante WebSocket

---

## Arquitectura del Sistema

```
Director (Game Master)
    ↓
├─ BLUE Team                    ├─ RED Team
│  ├─ Strategic Level           │  ├─ Strategic Level
│  ├─ Operational Level         │  ├─ Operational Level
│  └─ Tactical Level            │  └─ Tactical Level
└─────────────────────────────────────────────
          Simulation Engine
          Fog of War (BLUE & RED)
```

---

## Niveles de Comando

### 1. Director (Game Master)

**Rol**: Controla y supervisa todo el juego de guerra.

**Capacidades**:
- ✅ Visibilidad total (BLUE + RED + Ground Truth)
- ✅ Pausar/reanudar/terminar simulación
- ✅ Inyectar eventos (clima espacial, ataques cyber, desastres)
- ✅ Modificar condiciones en tiempo real
- ✅ Evaluar desempeño de equipos

**Comandos disponibles**:
```python
- pause_simulation
- resume_simulation
- end_simulation
- inject_space_weather
- inject_cyber_attack
- inject_disaster
- modify_weather
- spawn_entity
```

---

### 2. Nivel Estratégico (High Command)

**Rol**: Establece objetivos estratégicos y asigna recursos.

**Capacidades**:
- ✅ Ver situación general (fog of war aplicado)
- ✅ Definir ROE (Rules of Engagement)
- ✅ Asignar objetivos estratégicos
- ✅ Aprobar/rechazar ATOs
- ❌ NO control directo de unidades

**Comandos disponibles**:
```python
- set_roe
- set_strategic_objective
- allocate_resources
- approve_ato
- reject_ato
- set_priority
```

---

### 3. Nivel Operacional (Air Operations Center)

**Rol**: Planifica y coordina misiones tácticas.

**Capacidades**:
- ✅ Generar ATO (Air Tasking Order)
- ✅ Planificar misiones (CAP, SEAD, STRIKE, etc.)
- ✅ Asignar aeronaves a misiones
- ✅ Ordenar SCRAMBLE ante amenazas
- ✅ Coordinar con A1 (personal), A4 (logística)
- ❌ NO control directo de aeronaves en vuelo

**Comandos disponibles**:
```python
- create_ato
- create_mission
- assign_aircraft
- launch_mission
- abort_mission
- scramble
- request_tanker
- request_awacs
```

---

### 4. Nivel Táctico (Pilot / Fighter Controller)

**Rol**: Ejecución táctica directa.

**Capacidades**:
- ✅ Control directo de aeronaves asignadas
- ✅ Tomar decisiones de combate (engage/disengage)
- ✅ Reportar contactos a A2
- ✅ Solicitar soporte (AWACS, tanker, SAR)
- ✅ Ver radar/sensores en tiempo real

**Comandos disponibles**:
```python
- set_waypoint
- set_altitude
- set_speed
- engage_target
- launch_weapon
- deploy_countermeasures
- request_tanker
- rtb  # Return to base
```

---

## Tipos de Juegos

### 1. Guerra Externa

**Descripción**: Conflicto convencional entre dos naciones.

**Dominios**:
- ✅ Aire (combate BVR/WVR, SEAD, STRIKE, CAP)
- ✅ Espacio (satélites, GPS, clima espacial)
- ✅ Ciberespacio (ataques, defensa)

**Ejemplo de escenario**:
```python
GameType.EXTERNAL_WAR
Bandos: BLUE (defensor) vs RED (agresor)
Objetivo BLUE: Defender espacio aéreo, mantener superioridad
Objetivo RED: Penetrar defensa, strikes en objetivos críticos
Duración: 2-6 horas
```

---

### 2. Conflicto Interno

**Descripción**: Operaciones contra insurgencia/terrorismo.

**Bandos**:
- BLUE (humano): Fuerza del orden
- RED (IA): Insurgentes, terroristas
- NEUTRAL: Población civil

**Mecánicas especiales**:
- Collateral damage afecta apoyo de población
- Intel HUMINT crítico
- Hearts & Minds

**Ejemplo de escenario**:
```python
GameType.INTERNAL_CONFLICT
Bandos: BLUE (gobierno) vs RED (insurgentes) + NEUTRAL (civiles)
Objetivo: Neutralizar insurgencia, minimizar bajas civiles
Operaciones: CAS, ISR, transporte, MEDEVAC
```

---

### 3. Gestión de Desastres

**Descripción**: Operaciones de asistencia humanitaria.

**Dominios**:
- ✅ Aire (transporte, SAR, evacuación médica)
- ✅ Logística (distribución de suministros)
- ✅ Comunicaciones (restablecer redes)

**Desastres disponibles**:
- Terremoto (magnitud 5.0-8.5)
- Inundación
- Incendio forestal
- Huracán (categorías 1-5)

**Ejemplo de escenario**:
```python
GameType.DISASTER_MANAGEMENT
Objetivo: Maximizar vidas salvadas, minimizar sufrimiento
Operaciones: Search & Rescue, evacuación, distribución de ayuda
Duración: 2-4 horas
```

---

## Fog of War

### Principio

Cada bando solo ve:
1. **Unidades propias**: Siempre visibles (posición exacta)
2. **Detecciones de sensores**: Radares, AWACS, SIGINT
3. **Inteligencia**: Con delay y calidad variable
4. **Estimaciones**: Cuando contacto se pierde (incertidumbre crece)

El Director ve **Ground Truth** (realidad completa).

### Ejemplo

```
Ground Truth (Director):
  - 5 aeronaves BLUE
  - 4 aeronaves RED
  - 2 radares BLUE
  - 2 SAM sites RED
  Total: 13 entidades

BLUE Player View:
  - 5 aeronaves propias (exactas)
  - 2 tracks RED (con incertidumbre ±3km)
  - 2 radares propios
  Total visible: 9 entidades

RED Player View:
  - 4 aeronaves propias (exactas)
  - 3 tracks BLUE (con incertidumbre ±2km)
  - 2 SAM sites propios
  Total visible: 9 entidades
```

---

## Roles y Permisos

### Mapeo de Roles

| Rol | Nivel | Permisos |
|-----|-------|----------|
| `GAME_MASTER` | Director | Todo |
| `BLUE_STRATEGIC` | Estratégico | ROE, objetivos, recursos |
| `BLUE_OPERATIONAL` | Operacional | ATO, misiones, scramble |
| `BLUE_TACTICAL` | Táctico | Control de aeronaves |
| `RED_STRATEGIC` | Estratégico | ROE, objetivos, recursos |
| `RED_OPERATIONAL` | Operacional | ATO, misiones, scramble |
| `RED_TACTICAL` | Táctico | Control de aeronaves |
| `OBSERVER` | Observador | Solo lectura (ve todo) |
| `ADMIN` | Administrador | Gestión del sistema |

---

## Uso del Sistema

### 1. Crear Usuarios

```python
from gavilan.multiplayer.auth import get_auth_service, Role

auth = get_auth_service()

# Crear Director
director = auth.register_user("director1", "dir@example.com", "pass123")
director.add_role(Role.GAME_MASTER)

# Crear jugadores BLUE
blue_strat = auth.register_user("blue_gen", "blue@example.com", "pass123")
blue_strat.add_role(Role.BLUE_STRATEGIC)

# ... más jugadores
```

### 2. Crear Sesión

```python
from gavilan.multiplayer.session import get_session_manager, GameType

session_mgr = get_session_manager()

session = session_mgr.create_session(
    name="Defensa Aérea 2026",
    game_type=GameType.EXTERNAL_WAR,
    director=director,
)
```

### 3. Jugadores se Unen

```python
session.join_player(blue_strat, Role.BLUE_STRATEGIC)
session.join_player(blue_ops, Role.BLUE_OPERATIONAL)
session.join_player(blue_tac, Role.BLUE_TACTICAL)

# Equipo RED
session.join_player(red_strat, Role.RED_STRATEGIC)
session.join_player(red_ops, Role.RED_OPERATIONAL)
```

### 4. Iniciar Simulación

```python
from gavilan.core.config import GavilanConfig, GameMode, Difficulty

config = GavilanConfig(
    mode=GameMode.WARGAME,
    difficulty=Difficulty.MEDIUM,
    max_duration_seconds=3600,
)

session.start(config)
```

### 5. Ejecutar Comandos

```python
from gavilan.multiplayer.command_levels import Command, CommandLevel

# Nivel Estratégico: Establecer ROE
cmd = Command(
    level=CommandLevel.STRATEGIC,
    command_type="set_roe",
    user_id=blue_strat.id,
    side=Side.BLUE,
    data={"roe": "WEAPONS_FREE"},
)

result = session.execute_command(cmd, blue_strat)
print(result.message)  # "ROE set to WEAPONS_FREE"

# Nivel Operacional: Crear misión
cmd = Command(
    level=CommandLevel.OPERATIONAL,
    command_type="create_mission",
    user_id=blue_ops.id,
    side=Side.BLUE,
    data={
        "mission_type": "CAP",
        "target": {"lat": 4.5, "lon": -74.0},
        "priority": "HIGH",
    },
)

result = session.execute_command(cmd, blue_ops)

# Nivel Táctico: Control de aeronave
cmd = Command(
    level=CommandLevel.TACTICAL,
    command_type="set_altitude",
    user_id=blue_tac.id,
    side=Side.BLUE,
    data={
        "aircraft_id": "ac-uuid-123",
        "altitude_ft": 25000,
    },
)

result = session.execute_command(cmd, blue_tac)
```

### 6. Obtener Estado (con Fog of War)

```python
# Director ve todo
state = session.get_state_for_user(director)
# state contiene todas las entidades (ground truth)

# Jugador BLUE ve solo lo detectado
state = session.get_state_for_user(blue_strat)
# state contiene solo entidades propias + tracks enemigos

# Jugador RED ve solo lo detectado
state = session.get_state_for_user(red_strat)
# state contiene solo entidades propias + tracks enemigos
```

---

## Ejemplo Completo

Ver `/examples/multiplayer_demo.py` para una demostración completa del sistema.

```bash
cd /home/user/sim_jg
python examples/multiplayer_demo.py
```

---

## Próximos Pasos

### Fase Actual (Completada)
- ✅ Autenticación y usuarios
- ✅ Niveles de comando
- ✅ Fog of War
- ✅ Sesiones multiplayer
- ✅ Sistema de permisos

### Fase 2 (En desarrollo)
- 🔨 Servidor WebSocket para tiempo real
- 🔨 Frontend web para consolas
- 🔨 API REST para administración

### Fase 3 (Planeada)
- 📋 IA para enemigos autónomos
- 📋 Simulación de desastres naturales
- 📋 Consola de administración
- 📋 Escenarios predefinidos expandidos

---

## Arquitectura de Archivos

```
gavilan/
├─ multiplayer/
│  ├─ auth/
│  │  ├─ models.py          # Usuarios, roles, permisos
│  │  └─ service.py         # Autenticación, JWT
│  ├─ fog_of_war/
│  │  └─ fog_of_war.py      # Sistema de tracks
│  ├─ command_levels/
│  │  ├─ base.py            # Interfaz base
│  │  ├─ director.py        # Nivel Director
│  │  ├─ strategic.py       # Nivel Estratégico
│  │  ├─ operational.py     # Nivel Operacional
│  │  └─ tactical.py        # Nivel Táctico
│  └─ session/
│     ├─ game_session.py    # Sesión de juego
│     └─ session_manager.py # Gestor de sesiones
├─ server/                   # (Próxima fase)
│  ├─ api/
│  └─ websocket/
└─ frontend/                 # (Próxima fase)
   ├─ director/
   ├─ strategic/
   ├─ operational/
   └─ tactical/
```

---

## Soporte

Para más información, ver:
- `docs/ARQUITECTURA_MULTIPLAYER.md` - Diseño arquitectónico completo
- `examples/multiplayer_demo.py` - Demostración funcional
- `gavilan/multiplayer/` - Código fuente

---

**GAVILAN Multiplayer** - Sistema de entrenamiento multinivel para Fuerzas Aéreas
