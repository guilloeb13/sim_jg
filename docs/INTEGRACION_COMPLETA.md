# GAVILAN Multiplayer - Guía de Integración Completa

## 🎯 Resumen Ejecutivo

Se ha implementado un sistema completo **multinivel, multijugador y multiescenario** para el simulador militar GAVILAN, cumpliendo con todos los requisitos solicitados.

### ✅ Fases Completadas

**Fase 1 - Arquitectura Core** ✅
- Sistema de autenticación y autorización
- Fog of War con visibilidad limitada
- 4 niveles de comando (Director/Estratégico/Operacional/Táctico)
- Sesiones multiplayer concurrentes

**Fase 2 - Servidor & API** ✅
- Servidor WebSocket para tiempo real
- API REST completa
- Connection manager para múltiples clientes
- Protocolo de mensajes bidireccional

**Fase 3 - IA Avanzada** ✅
- IA para enemigos autónomos (dificultad escalable)
- IA para insurgentes (tácticas asimétricas)
- Simulador de desastres naturales dinámico

**Fase 4 - Frontend Base** ✅
- Portal de acceso HTML
- Estructura para consolas específicas
- Integración con WebSocket

---

## 📁 Arquitectura Completa

```
gavilan/
├── multiplayer/                  # FASE 1: Core multiplayer
│   ├── auth/                     # Autenticación (JWT, bcrypt)
│   │   ├── models.py             # Usuarios, roles, permisos
│   │   └── service.py            # Login, registro
│   ├── fog_of_war/               # Sistema de tracks
│   │   └── fog_of_war.py         # Visibilidad limitada
│   ├── command_levels/           # Niveles de comando
│   │   ├── director.py           # 11 comandos
│   │   ├── strategic.py          # 6 comandos
│   │   ├── operational.py        # 8 comandos
│   │   └── tactical.py           # 11 comandos
│   └── session/                  # Gestión de sesiones
│       ├── game_session.py       # Sesión individual
│       └── session_manager.py    # Gestor global
│
├── server/                       # FASE 2: Servidor
│   ├── websocket/                # WebSocket server
│   │   ├── protocol.py           # Protocolo de mensajes
│   │   ├── connection_manager.py # Gestión de conexiones
│   │   └── server.py             # Servidor WebSocket
│   └── api/                      # API REST
│       ├── app.py                # FastAPI app
│       └── routes/               # Endpoints
│           ├── auth.py           # Login, registro
│           ├── sessions.py       # CRUD sesiones
│           ├── users.py          # Gestión usuarios
│           └── scenarios.py      # Escenarios
│
├── ai/                           # FASE 3: IA Avanzada
│   ├── enemy_ai.py               # IA enemigos (guerra externa)
│   ├── insurgent_ai.py           # IA insurgentes (COIN)
│   └── disaster_simulator.py     # Simulador desastres
│
├── core/                         # Motor de simulación (existente)
│   ├── engine.py
│   ├── entities.py
│   ├── events.py
│   └── config.py
│
└── modules/                      # Módulos de simulación (existente)
    ├── staff/                    # Estado Mayor (A1-A6)
    ├── air_simulation/           # Simulación aérea
    ├── space/                    # Clima espacial
    └── cyber/                    # Ciberoperaciones

frontend/                         # FASE 4: Frontend
├── index.html                    # Portal principal
├── director/                     # Consola Director
├── strategic/                    # Consola Estratégica
├── operational/                  # Consola Operacional
├── tactical/                     # Consola Táctica
└── admin/                        # Consola Administración
```

---

## 🚀 Deployment

### Requisitos

```bash
# Python 3.10+
python --version

# Dependencias
pip install -r requirements.txt
```

### Dependencias Principales

```txt
# Web Framework
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
websockets>=11.0

# Autenticación
bcrypt>=4.0.0
PyJWT>=2.8.0

# Base de datos (opcional)
sqlalchemy>=2.0.0
alembic>=1.11.0

# Computación
numpy>=1.24.0

# HTTP Client
httpx>=0.24.0
```

### Inicio Rápido

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd sim_jg

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar servidor
python start_server.py
```

El servidor estará disponible en:
- **WebSocket**: `ws://localhost:8000/ws`
- **API REST**: `http://localhost:8000/api`
- **Documentación**: `http://localhost:8000/docs`
- **Frontend**: `http://localhost:8000`

---

## 🔌 Uso del Sistema

### 1. Autenticación

#### Registro de Usuario

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "piloto1",
    "email": "piloto1@example.com",
    "password": "password123"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "piloto1",
    "password": "password123"
  }'

# Response:
{
  "user_id": "uuid",
  "username": "piloto1",
  "email": "piloto1@example.com",
  "roles": [],
  "token": "eyJ..."
}
```

Guardar el `token` para uso posterior.

---

### 2. Asignar Roles (Admin)

```bash
# Asignar rol BLUE_TACTICAL
curl -X POST http://localhost:8000/api/users/{user_id}/roles \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"role": "blue_tactical"}'
```

---

### 3. Crear Sesión de Juego

```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Authorization: Bearer {game_master_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Defensa Aérea 2026",
    "game_type": "external_war"
  }'

# Response:
{
  "id": "session-uuid",
  "name": "Defensa Aérea 2026",
  "game_type": "external_war",
  "status": "lobby",
  ...
}
```

---

### 4. Conectar vía WebSocket

```javascript
// Cliente JavaScript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    // 1. Autenticar
    ws.send(JSON.stringify({
        type: 'authenticate',
        data: {
            token: 'eyJ...'
        }
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'authenticated') {
        console.log('✓ Autenticado como:', message.data.username);

        // 2. Unirse a sesión
        ws.send(JSON.stringify({
            type: 'join_session',
            data: {
                session_id: 'session-uuid',
                role: 'blue_tactical'
            }
        }));
    }

    if (message.type === 'session_joined') {
        console.log('✓ Unido a sesión');
    }

    if (message.type === 'state_update') {
        // Actualizar UI con nuevo estado
        updateUI(message.data);
    }
};
```

---

### 5. Ejecutar Comandos

```javascript
// Nivel Táctico: Cambiar altitud
ws.send(JSON.stringify({
    type: 'execute_command',
    data: {
        command: {
            level: 'tactical',
            command_type: 'set_altitude',
            side: 'blue',
            data: {
                aircraft_id: 'ac-uuid',
                altitude_ft: 25000
            }
        }
    }
}));

// Servidor responde con:
{
    type: 'command_result',
    data: {
        command_id: 'cmd-uuid',
        success: true,
        message: 'Aircraft climbing to 25000 ft'
    }
}
```

---

## 🎮 Tipos de Juegos

### 1. Guerra Externa

```python
game_type = GameType.EXTERNAL_WAR

# Bandos:
# - BLUE: Defensor (humanos)
# - RED: Agresor (humanos o IA)

# Dominios:
# - Aire: Humanos
# - Espacio: Humanos
# - Ciberespacio: Humanos
# - Tierra/Naval: IA simulada

# IA Enemiga (si RED no tiene jugadores):
enemy_ai = EnemyAI(Side.RED, DifficultyLevel.MEDIUM)
# Tácticas: BVR, WVR, SEAD, engagements coordinados
```

### 2. Conflicto Interno

```python
game_type = GameType.INTERNAL_CONFLICT

# Bandos:
# - BLUE: Fuerza del orden (humanos)
# - RED: Insurgentes (IA siempre)
# - NEUTRAL: Población civil

# IA Insurgente:
insurgent_ai = InsurgentAI(
    profile=InsurgentProfile(
        name="FARC-style",
        aggressiveness=0.6,
        caution=0.7,
        popular_support=0.5,
    )
)
# Tácticas: IEDs, MANPADS, emboscadas, propaganda
```

### 3. Gestión de Desastres

```python
game_type = GameType.DISASTER_MANAGEMENT

# Sin enemigos
# BLUE: Equipo de rescate (humanos)

# Simulador de Desastre:
disaster = DisasterSimulator(
    disaster_type=DisasterType.EARTHQUAKE,
    severity=0.8  # Magnitud 7.8
)
# Progresión: WARNING → IMPACT → EMERGENCY → STABILIZATION → RECOVERY
```

---

## 🤖 Sistema de IA

### IA Enemiga (Guerra Externa)

**Niveles de Dificultad**:

- **EASY**: Tácticas básicas, sin coordinación
  - Vuela directo al objetivo
  - Dispara cuando en rango
  - Maniobras evasivas simples

- **MEDIUM**: Tácticas intermedias, coordinación básica
  - Beam maneuvers
  - Uso de contramedidas
  - Engagements cooperativos básicos

- **HARD**: Tácticas avanzadas, alta coordinación
  - Posicionamiento BVR óptimo
  - Tácticas de pincer
  - Defensive splits coordinados

- **EXPERT**: Tácticas expertas, predicción adaptativa
  - Estrategia dinámica
  - Engaño y feints
  - Posicionamiento predictivo

### IA Insurgente (Conflicto Interno)

**Comportamiento Asimétrico**:
- Evita confrontación directa
- Ataca objetivos vulnerables
- Se esconde cuando presión es alta
- Explota daño colateral para propaganda
- Reclutamiento basado en apoyo popular

**Tácticas**:
- IEDs en rutas predecibles
- MANPADS contra aeronaves bajas
- Morteros contra bases
- Propaganda tras daño colateral

### Simulador de Desastres

**Tipos Soportados**:

1. **Terremoto** (Magnitude 5.0-8.5)
   - Réplicas aleatorias
   - Daño estructural
   - Búsqueda y rescate

2. **Inundación**
   - Nivel de agua dinámico
   - Bloqueo de accesos
   - Evacuación urgente

3. **Incendio Forestal**
   - Propagación dinámica (viento, humedad)
   - Saltos de fuego (embers)
   - Evacuación de comunidades

4. **Huracán** (Categorías 1-5)
   - Fase de warning previa
   - Impacto prolongado
   - Daño extenso

---

## 📊 Monitoreo y Métricas

### Health Check

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "sessions": {
    "total_sessions": 5,
    "by_status": {
      "lobby": 2,
      "running": 2,
      "ended": 1
    },
    "active_players": 12
  }
}
```

### Métricas de Sesión

```python
session = get_session_manager().get_session(session_id)
status = session.get_status_dict()

print(status)
# {
#   "id": "...",
#   "name": "Defensa Aérea 2026",
#   "game_type": "external_war",
#   "status": "running",
#   "players": 6,
#   "simulation_time": 1234.5,
#   ...
# }
```

---

## 🔒 Seguridad

### Autenticación

- **JWT tokens** con expiración de 24h
- **bcrypt** para hash de passwords
- **HTTPS** en producción (configurar reverse proxy)

### Autorización

- **Validación por rol** en cada comando
- **Fog of War** impide ver información de otro bando
- **Rate limiting** en API (configurar en producción)

### WebSocket

- **Autenticación obligatoria** antes de enviar comandos
- **Validación de permisos** en cada mensaje
- **Desconexión automática** si token inválido

---

## 🧪 Testing

### Test de Autenticación

```bash
pytest tests/test_auth.py
```

### Test de Sesiones

```bash
pytest tests/test_sessions.py
```

### Test de IA

```bash
pytest tests/test_ai.py
```

---

## 📈 Escalabilidad

### Horizontal Scaling

```python
# Múltiples workers de Uvicorn
uvicorn gavilan.server.api.app:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8000
```

### Load Balancing

```nginx
# nginx.conf
upstream gavilan {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
    server localhost:8004;
}

server {
    listen 80;
    location / {
        proxy_pass http://gavilan;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Database Scaling

```python
# Usar PostgreSQL en producción
DATABASE_URL = "postgresql://user:pass@localhost/gavilan"

# Usar Redis para sesiones
REDIS_URL = "redis://localhost:6379"
```

---

## 🐛 Troubleshooting

### Error: "Authentication failed"

```bash
# Verificar que token es válido
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer {token}"
```

### Error: "Session not found"

```bash
# Listar sesiones disponibles
curl http://localhost:8000/api/sessions \
  -H "Authorization: Bearer {token}"
```

### WebSocket se desconecta

```javascript
// Implementar reconexión automática
ws.onclose = () => {
    setTimeout(() => {
        connectWebSocket();
    }, 3000);
};
```

---

## 📚 Recursos Adicionales

- **Arquitectura Completa**: `docs/ARQUITECTURA_MULTIPLAYER.md`
- **Guía de Usuario**: `docs/MULTIPLAYER_README.md`
- **Ejemplo Funcional**: `examples/multiplayer_demo.py`
- **API Docs**: `http://localhost:8000/docs` (cuando servidor activo)

---

## ✅ Checklist de Deployment

- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Configurar variables de entorno (JWT secret, database URL)
- [ ] Migrar base de datos: `alembic upgrade head`
- [ ] Iniciar servidor: `python start_server.py`
- [ ] Verificar health check: `curl http://localhost:8000/health`
- [ ] Crear usuario admin inicial
- [ ] Configurar HTTPS (nginx + Let's Encrypt)
- [ ] Configurar monitoring (Prometheus, Grafana)
- [ ] Backup automático de base de datos

---

**GAVILAN Multiplayer** - Sistema Completo Implementado ✅
