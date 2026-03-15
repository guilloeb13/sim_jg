# ARQUITECTURA MULTIPLAYER - SISTEMA GAVILAN

## 1. VISIÓN GENERAL

GAVILAN evoluciona de un simulador single-player a una **plataforma multinivel, multijugador y multiescenario** para entrenamiento de fuerzas aéreas.

### 1.1 Características Principales

- **Multinivel**: 4 niveles de comando (Director, Estratégico, Operacional, Táctico)
- **Multijugador**: 2 bandos humanos (BLUE vs RED) con equipos distribuidos
- **Multiescenario**: 3 tipos de juegos (Guerra Externa, Conflicto Interno, Gestión de Crisis)
- **Tiempo real**: Sincronización mediante WebSocket
- **Fog of War**: Visibilidad limitada por bando
- **Administración**: Consola para configurar escenarios y perfiles de IA

---

## 2. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────┐
│                         CAPA DE CLIENTES                        │
├─────────────┬─────────────┬─────────────┬──────────────────────┤
│   Director  │ Estratégico │ Operacional │      Táctico         │
│   Console   │   Console   │   Console   │     Console          │
│  (Web UI)   │  (Web UI)   │  (Web UI)   │    (Web UI)          │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬───────────────┘
       │             │             │             │
       └─────────────┴─────────────┴─────────────┘
                     │
              WebSocket / REST API
                     │
┌────────────────────┴──────────────────────────────────────────┐
│                    SERVIDOR MULTIPLAYER                        │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            Session Manager & Authentication              │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Game Instance Manager                       │ │
│  │  - Multiple concurrent games                            │ │
│  │  - Per-game simulation engine                           │ │
│  │  - Fog of War per side                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Command Level Router                        │ │
│  │  - Routes commands to appropriate level                 │ │
│  │  - Validates permissions                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              AI Director                                 │ │
│  │  - Enemy autonomous behavior                            │ │
│  │  - Disaster simulation                                  │ │
│  │  - Insurgent tactics                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                     │
┌────────────────────┴──────────────────────────────────────────┐
│                   MOTOR DE SIMULACIÓN GAVILAN                  │
│              (Extendido con capacidades multiplayer)           │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. NIVELES DE COMANDO

### 3.1 NIVEL DIRECTOR (Game Master)

**Rol**: Controla y supervisa todo el juego de guerra.

**Capacidades**:
- ✅ Visibilidad total (BLUE + RED + Ground Truth)
- ✅ Pausar/reanudar/terminar simulación
- ✅ Inyectar eventos (clima espacial, ataques cyber, desastres)
- ✅ Modificar condiciones en tiempo real
- ✅ Evaluar desempeño de equipos
- ✅ Chat con todos los niveles
- ✅ Ver métricas agregadas de ambos bandos

**Interfaz**:
- Mapa táctico completo
- Panel de control de simulación
- Timeline de eventos
- Consola de inyección de eventos
- Dashboard de métricas por bando

---

### 3.2 NIVEL ESTRATÉGICO (High Command)

**Rol**: Establece objetivos estratégicos y asigna recursos.

**Capacidades**:
- ✅ Ver situación general del teatro (fog of war aplicado)
- ✅ Definir ROE (Rules of Engagement)
- ✅ Asignar objetivos estratégicos
- ✅ Aprobar/rechazar ATOs (Air Tasking Orders)
- ✅ Asignar recursos entre sectores
- ✅ Coordinar con aliados (en juegos multi-coalición)
- ✅ Establecer prioridades (A2, A4, A6)
- ❌ NO control directo de unidades

**Interfaz**:
- Mapa estratégico (baja resolución, actualización cada 5-10 min)
- Panel de objetivos estratégicos
- Dashboard de recursos (fuel, munitions, personal)
- ROE configurator
- ATO approval queue
- Intel briefs de A2

---

### 3.3 NIVEL OPERACIONAL (Air Operations Center - AOC)

**Rol**: Planifica y coordina misiones tácticas.

**Capacidades**:
- ✅ Generar ATO (Air Tasking Order)
- ✅ Planificar paquetes de misiones (CAP, SEAD, STRIKE, etc.)
- ✅ Asignar aeronaves a misiones
- ✅ Coordinar con A1 (personal), A4 (logística)
- ✅ Recibir intel de A2
- ✅ Monitorear estado de misiones
- ✅ Ordenar SCRAMBLE ante amenazas
- ✅ Coordinar tiempo/espacio (deconfliction)
- ❌ NO control directo de aeronaves en vuelo

**Interfaz**:
- ATO planner (drag-and-drop de misiones)
- Mapa operacional (actualización cada 1-2 min)
- Mission status board
- Aircraft availability (integrado con A4)
- Pilot roster (integrado con A1)
- Intel feed de A2
- Communication con nivel táctico

---

### 3.4 NIVEL TÁCTICO (Fighter Controller / Pilot)

**Rol**: Ejecución táctica directa.

**Capacidades**:
- ✅ Control directo de unidades asignadas
- ✅ Ejecutar misiones del ATO
- ✅ Tomar decisiones de combate (engage/disengage)
- ✅ Reportar contactos a A2
- ✅ Solicitar soporte (AWACS, tanker, SAR)
- ✅ Ver radar/sensores en tiempo real
- ✅ Comunicación con otras unidades tácticas
- ❌ NO puede cambiar objetivos estratégicos

**Interfaz**:
- Mapa táctico (tiempo real, alta resolución)
- Radar display
- Weapon systems panel
- Communication panel
- Fuel/ammo status
- Threat warning
- Data link (Link-16 simulation)

---

## 4. SISTEMA DE AUTENTICACIÓN Y ROLES

### 4.1 Modelo de Usuarios

```python
class User:
    id: UUID
    username: str
    password_hash: str  # bcrypt
    email: str
    created_at: datetime
    roles: List[Role]

class Role:
    GAME_MASTER = "game_master"      # Nivel Director
    BLUE_STRATEGIC = "blue_strategic"
    BLUE_OPERATIONAL = "blue_operational"
    BLUE_TACTICAL = "blue_tactical"
    RED_STRATEGIC = "red_strategic"
    RED_OPERATIONAL = "red_operational"
    RED_TACTICAL = "red_tactical"
    OBSERVER = "observer"             # Solo lectura
    ADMIN = "admin"                   # Administración del sistema
```

### 4.2 Permisos por Rol

| Rol | Visibilidad | Comandos | Pausa | Inyectar Eventos |
|-----|-------------|----------|-------|------------------|
| game_master | Todo | Todos | ✅ | ✅ |
| X_strategic | Bando X (fog of war) | Estratégicos | ❌ | ❌ |
| X_operational | Bando X (fog of war) | Operacionales | ❌ | ❌ |
| X_tactical | Bando X (sensores) | Tácticos | ❌ | ❌ |
| observer | Todo (read-only) | Ninguno | ❌ | ❌ |
| admin | Sistema | Admin | ✅ | ✅ |

---

## 5. TIPOS DE JUEGOS

### 5.1 GUERRA EXTERNA (Air/Space/Cyber Warfare)

**Descripción**: Conflicto convencional entre dos naciones.

**Dominios humanos**:
- ✅ Aire (combate BVR/WVR, SEAD, STRIKE, CAP)
- ✅ Espacio (satélites, GPS, clima espacial)
- ✅ Ciberespacio (ataques, defensa)

**Dominios simulados por IA**:
- 🤖 Tierra (infantería, tanques, artillería)
- 🤖 Naval (portaaviones, destructores, submarinos)

**Configuración**:
```python
GameType.EXTERNAL_WAR
- Bandos: BLUE (defensor) vs RED (agresor)
- Objetivo BLUE: Defender territorio, mantener superiority
- Objetivo RED: Penetrar defensa, strikes en objetivos críticos
- Duración: 2-6 horas
- Métricas: Aeronaves destruidas, objetivos neutralizados, territorio controlado
```

**Escenarios ejemplo**:
1. **Defensa de espacio aéreo**: RED intenta penetrar, BLUE intercepta
2. **SEAD campaign**: BLUE suprime SAMs RED para permitir strikes
3. **Counter-air**: Ambos bandos buscan superioridad aérea
4. **Ataque cibernético coordinado**: RED ataca C2 mientras penetra físicamente

---

### 5.2 CONFLICTO INTERNO (COIN - Counterinsurgency)

**Descripción**: Operaciones contra insurgencia/terrorismo.

**Bandos**:
- BLUE (humano): Fuerza del orden (Fuerza Aérea, Ejército)
- RED (IA): Insurgentes, terroristas, narcotraficantes
- NEUTRAL: Población civil (no combatientes)

**Dominios humanos**:
- ✅ Aire (CAS, ISR, transporte, MEDEVAC)
- ✅ Ciberespacio (contra propaganda, rastreo comunicaciones)
- ✅ Inteligencia (HUMINT, SIGINT)

**Dominios simulados por IA**:
- 🤖 Tierra (patrullas, checkpoints, raids)
- 🤖 Población civil (reacción a operaciones)

**Mecánicas especiales**:
- **Collateral damage**: Bajas civiles afectan apoyo de población
- **Intel gathering**: HUMINT crítico para localizar enemigo
- **Hearts & Minds**: Operaciones humanitarias mejoran control territorial
- **IEDs y emboscadas**: IA genera amenazas asimétricas

**Configuración**:
```python
GameType.INTERNAL_CONFLICT
- Bandos: BLUE (gobierno) vs RED (insurgentes) + NEUTRAL (civiles)
- Objetivo BLUE: Neutralizar insurgencia, minimizar bajas civiles
- Objetivo RED (IA): Sembrar caos, evitar detección
- Duración: 4-8 horas (ops prolongadas)
- Métricas: Insurgentes neutralizados, civiles protegidos, territorio pacificado
```

**Escenarios ejemplo**:
1. **Rescate de rehenes**: Operación precisa con mínimo collateral
2. **Interdicción de tráfico ilícito**: ISR + strikes en rutas
3. **Apoyo a tropas en contacto**: CAS en área urbana
4. **Evacuación de no combatientes**: Bajo fuego insurgente

---

### 5.3 GESTIÓN DE CRISIS / DESASTRE NATURAL (Humanitarian Ops)

**Descripción**: Operaciones de asistencia humanitaria y gestión de desastres.

**Bandos**:
- BLUE (humano): Fuerza Aérea en misión humanitaria
- No hay enemigo
- NEUTRAL: Población afectada

**Dominios humanos**:
- ✅ Aire (transporte, búsqueda y rescate, evacuación médica)
- ✅ Logística (distribución de suministros)
- ✅ Comunicaciones (restablecer redes en área afectada)

**Dominios simulados por IA**:
- 🤖 Desastre (terremoto, inundación, incendio, huracán)
- 🤖 Población (necesidades, evacuación, pánico)
- 🤖 Infraestructura (colapso, recuperación)

**Mecánicas especiales**:
- **Disaster progression**: El desastre evoluciona dinámicamente
- **Resource scarcity**: Fuel/supplies limitados, priorización crítica
- **Search & Rescue**: Localizar sobrevivientes (time-critical)
- **Medical triage**: Evacuación médica prioritaria
- **Infrastructure damage**: Aeropuertos/rutas dañados, requiere improvisación

**Configuración**:
```python
GameType.DISASTER_MANAGEMENT
- Bandos: BLUE (rescatistas)
- Objetivo: Maximizar vidas salvadas, minimizar sufrimiento
- Desastres disponibles:
  * Earthquake (magnitude 5.0-8.5)
  * Flood (rio overflow, coastal surge)
  * Wildfire (wind-driven spread)
  * Hurricane (categories 1-5)
  * Volcanic eruption
- Duración: 2-4 horas (primera respuesta)
- Métricas: Vidas salvadas, suministros entregados, áreas evacuadas
```

**Escenarios ejemplo**:
1. **Terremoto 7.2**: Edificios colapsados, rescate urbano
2. **Inundación masiva**: Evacuación de miles, puentes destruidos
3. **Incendio forestal**: Evacuación de comunidades, combate aéreo de incendio
4. **Huracán categoría 4**: Pre-posicionamiento, evacuación, respuesta post-impacto

---

## 6. FOG OF WAR

### 6.1 Principios

Cada bando solo ve:
1. **Unidades propias**: Siempre visibles (posición exacta)
2. **Detecciones de sensores**: Radares, AWACS, SIGINT, IMINT
3. **Reportes de inteligencia**: De A2, con delay y calidad variable
4. **Estimaciones**: Cuando contacto se pierde, posición estimada (uncertainty grows)

El Director ve **Ground Truth** (realidad completa).

### 6.2 Implementación

```python
class FogOfWar:
    def __init__(self, side: Side, game: Game):
        self.side = side
        self.game = game
        self.tracks: Dict[UUID, Track] = {}

    def get_visible_entities(self) -> List[Entity]:
        """Retorna solo entidades visibles para este bando"""
        visible = []

        # 1. Unidades propias (siempre visibles)
        visible.extend(self.game.get_entities(side=self.side))

        # 2. Detecciones de radar
        for radar in self.game.get_radars(side=self.side):
            if radar.is_operational():
                detections = radar.scan()
                for entity in detections:
                    if entity.side != self.side:
                        track = self._create_or_update_track(entity, radar)
                        visible.append(track.to_entity())

        # 3. Degradar tracks antiguos
        self._degrade_old_tracks()

        return visible

    def _create_or_update_track(self, entity, sensor):
        """Crea o actualiza track con incertidumbre"""
        if entity.id in self.tracks:
            track = self.tracks[entity.id]
            track.update(entity.position, sensor.accuracy)
        else:
            track = Track(
                entity_id=entity.id,
                position=entity.position,
                uncertainty=sensor.accuracy,
                last_seen=self.game.time,
                classification=sensor.classify(entity)
            )
            self.tracks[entity.id] = track
        return track

    def _degrade_old_tracks(self):
        """Aumenta incertidumbre de tracks no actualizados"""
        for track in self.tracks.values():
            age = self.game.time - track.last_seen
            track.uncertainty += age.seconds * 0.1  # 0.1 km por segundo
            if track.uncertainty > 50:  # Más de 50km incertidumbre
                del self.tracks[track.entity_id]  # Eliminar track
```

---

## 7. SERVIDOR MULTIPLAYER

### 7.1 Arquitectura

**Stack tecnológico**:
- **Backend**: Python + FastAPI + WebSocket
- **Frontend**: React + TypeScript + Leaflet (mapas)
- **Base de datos**: PostgreSQL (usuarios, escenarios) + Redis (sesiones, cache)
- **Comunicación**: WebSocket (tiempo real) + REST API (admin)

### 7.2 Componentes

#### 7.2.1 Session Manager

```python
class GameSession:
    id: UUID
    name: str
    game_type: GameType  # EXTERNAL_WAR, INTERNAL_CONFLICT, DISASTER
    created_at: datetime
    status: SessionStatus  # LOBBY, RUNNING, PAUSED, ENDED
    director: User
    players: Dict[Role, User]
    simulation_engine: SimulationEngine
    fog_of_war_blue: FogOfWar
    fog_of_war_red: FogOfWar
```

#### 7.2.2 WebSocket Protocol

```json
// Cliente → Servidor
{
  "type": "command",
  "command_type": "launch_mission",
  "level": "operational",
  "side": "blue",
  "data": {
    "mission_id": "MSN-001",
    "aircraft_ids": ["AC-1", "AC-2"]
  }
}

// Servidor → Cliente
{
  "type": "state_update",
  "timestamp": "2026-03-15T10:30:00Z",
  "data": {
    "entities": [...],  // Filtrado por fog of war
    "missions": [...],
    "events": [...]
  }
}
```

#### 7.2.3 Command Router

```python
class CommandRouter:
    def route(self, command: Command, user: User) -> CommandResult:
        # 1. Validar permiso
        if not self._has_permission(user, command):
            raise PermissionDenied()

        # 2. Rutear a handler apropiado
        if command.level == Level.STRATEGIC:
            return self._handle_strategic(command)
        elif command.level == Level.OPERATIONAL:
            return self._handle_operational(command)
        elif command.level == Level.TACTICAL:
            return self._handle_tactical(command)
        elif command.level == Level.DIRECTOR:
            return self._handle_director(command)
```

---

## 8. MÓDULO DE IA

### 8.1 AI Director

Controla comportamiento autónomo de:
1. **Enemigos en guerra externa** (RED side cuando no hay jugadores)
2. **Insurgentes en conflicto interno** (siempre IA)
3. **Simulación de desastres** (progression dinámica)

### 8.2 Enemy AI (Guerra Externa)

```python
class EnemyAI:
    """IA para bando RED en guerra externa"""

    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.doctrine = self._load_doctrine(difficulty)

    def update(self, game_state: GameState):
        # 1. Analizar situación
        threats = self._assess_threats(game_state)
        opportunities = self._identify_opportunities(game_state)

        # 2. Tomar decisiones estratégicas
        if self.difficulty >= Difficulty.HARD:
            self._plan_coordinated_strike(game_state)

        # 3. Ejecutar tácticas
        for aircraft in game_state.get_aircraft(Side.RED):
            if not aircraft.has_mission():
                mission = self._assign_mission(aircraft, threats, opportunities)
                aircraft.assign_mission(mission)

            # Control táctico
            if aircraft.in_combat():
                self._execute_combat_tactics(aircraft, threats)

    def _execute_combat_tactics(self, aircraft, threats):
        """Tácticas de combate según dificultad"""
        if self.difficulty == Difficulty.EASY:
            # Básico: Volar directo, disparar cuando en rango
            self._basic_intercept(aircraft)

        elif self.difficulty == Difficulty.MEDIUM:
            # Intermedio: Maniobras básicas, uso de contramedidas
            if aircraft.is_defensive():
                aircraft.deploy_chaff()
            self._beam_maneuver(aircraft)

        elif self.difficulty >= Difficulty.HARD:
            # Avanzado: Tácticas cooperativas, engaño
            if threats.high_pk_threat_exists():
                self._defensive_split(aircraft)
            else:
                self._offensive_pincer(aircraft)
```

### 8.3 Insurgent AI (Conflicto Interno)

```python
class InsurgentAI:
    """IA para insurgentes en conflicto interno"""

    def __init__(self, profile: InsurgentProfile):
        self.profile = profile  # Agresividad, cautela, recursos
        self.cells: List[InsurgentCell] = []
        self.safe_houses: List[Location] = []

    def update(self, game_state: GameState):
        # 1. Intel gathering (intentar descubrir planes BLUE)
        self._conduct_surveillance(game_state)

        # 2. Planear ataques asimétricos
        if self._opportunity_exists(game_state):
            self._plan_ambush(game_state)

        # 3. Evitar detección
        for cell in self.cells:
            if cell.is_compromised():
                cell.disperse()
                cell.relocate_to_safe_house()

        # 4. Propaganda y reclutamiento
        if game_state.collateral_damage_occurred():
            self._exploit_for_recruitment()

    def _plan_ambush(self, game_state):
        """Emboscadas contra patrullas BLUE"""
        # IEDs, MANPADS, small arms
        vulnerable_targets = self._find_vulnerable_convoys(game_state)
        if vulnerable_targets:
            self._plant_ied(vulnerable_targets[0].route)
```

### 8.4 Disaster AI (Gestión de Crisis)

```python
class DisasterSimulator:
    """Simula evolución de desastres naturales"""

    def __init__(self, disaster_type: DisasterType, severity: float):
        self.type = disaster_type
        self.severity = severity
        self.affected_areas: List[Area] = []
        self.casualties: int = 0
        self.infrastructure_damage: Dict[str, float] = {}

    def update(self, dt: float):
        if self.type == DisasterType.EARTHQUAKE:
            self._simulate_earthquake(dt)
        elif self.type == DisasterType.FLOOD:
            self._simulate_flood(dt)
        elif self.type == DisasterType.WILDFIRE:
            self._simulate_wildfire(dt)
        elif self.type == DisasterType.HURRICANE:
            self._simulate_hurricane(dt)

    def _simulate_wildfire(self, dt):
        """Propagación de incendio forestal"""
        # Factores: viento, humedad, combustible disponible
        wind = self.game.weather.wind_speed
        humidity = self.game.weather.humidity

        for fire_zone in self.fire_zones:
            # Spread rate basado en condiciones
            spread_rate = (wind / 10) * (1 - humidity / 100) * self.severity

            # Expandir perímetro
            fire_zone.expand(spread_rate * dt)

            # Generar nuevas áreas afectadas
            if random.random() < 0.1:  # Ember jumps
                new_zone = self._create_spot_fire(fire_zone)
                self.fire_zones.append(new_zone)

            # Actualizar casualties
            self._calculate_casualties(fire_zone)

    def get_priority_areas(self) -> List[Area]:
        """Áreas que requieren atención inmediata"""
        priority = []
        for area in self.affected_areas:
            if area.population_at_risk > 100:
                priority.append(area)
        return sorted(priority, key=lambda a: a.population_at_risk, reverse=True)
```

---

## 9. CONSOLA DE ADMINISTRACIÓN

### 9.1 Funcionalidades

**Gestión de usuarios**:
- CRUD de usuarios
- Asignación de roles
- Historial de sesiones

**Gestión de escenarios**:
- Crear/editar/eliminar escenarios
- Templates predefinidos
- Configuración de IA

**Configuración de perfiles de IA**:
- Perfiles de enemigo (doctrina, agresividad, recursos)
- Perfiles de insurgentes (tácticas, objetivos)
- Perfiles de desastres (severity, progression)

**Monitoreo**:
- Sesiones activas
- Métricas de uso
- Logs de eventos

### 9.2 API REST

```python
# Usuarios
POST /api/users                    # Crear usuario
GET  /api/users/:id                # Obtener usuario
PUT  /api/users/:id                # Actualizar usuario
DELETE /api/users/:id              # Eliminar usuario

# Escenarios
POST /api/scenarios                # Crear escenario
GET  /api/scenarios                # Listar escenarios
GET  /api/scenarios/:id            # Obtener escenario
PUT  /api/scenarios/:id            # Actualizar escenario
DELETE /api/scenarios/:id          # Eliminar escenario

# Perfiles de IA
POST /api/ai-profiles              # Crear perfil
GET  /api/ai-profiles              # Listar perfiles
PUT  /api/ai-profiles/:id          # Actualizar perfil

# Sesiones de juego
POST /api/sessions                 # Crear sesión
GET  /api/sessions                 # Listar sesiones activas
GET  /api/sessions/:id             # Estado de sesión
POST /api/sessions/:id/start       # Iniciar sesión
POST /api/sessions/:id/pause       # Pausar sesión
POST /api/sessions/:id/stop        # Terminar sesión
```

---

## 10. FLUJOS DE JUEGO

### 10.1 Inicio de Sesión

```
1. Admin crea sesión desde consola
   ↓
2. Asigna Director (Game Master)
   ↓
3. Director configura:
   - Tipo de juego (EXTERNAL_WAR/INTERNAL/DISASTER)
   - Escenario
   - Duración
   - Perfiles de IA
   ↓
4. Director invita jugadores
   ↓
5. Jugadores se unen y seleccionan rol:
   - Bando (BLUE/RED)
   - Nivel (STRATEGIC/OPERATIONAL/TACTICAL)
   ↓
6. Director inicia simulación
   ↓
7. WebSocket envía actualizaciones cada tick
   ↓
8. Jugadores envían comandos según nivel
   ↓
9. IA controla enemigos/desastres
   ↓
10. Director puede inyectar eventos
   ↓
11. Simulación termina (tiempo o condiciones de victoria)
   ↓
12. After Action Review (AAR) disponible
```

### 10.2 Ejemplo: Misión en Guerra Externa

**BLUE Team**:
- Estratégico: Define objetivo "Destruir radar S-400 en (lat, lon)"
- Operacional: Crea ATO con paquete SEAD (2x F-16 + 1x EA-18G jammer)
- Táctico: Pilota F-16, ejecuta ingreso, dispara HARM, evade SAMs

**RED Team (IA o humano)**:
- Estratégico: Prioriza defensa de S-400
- Operacional: Ordena CAP con 2x Su-27 para proteger S-400
- Táctico: Pilota Su-27, intercepta F-16s

**Director**:
- Observa ambos bandos
- Inyecta tormenta geomagnética para degradar GPS (dificulta HARM targeting)
- Evalúa desempeño

---

## 11. MÉTRICAS Y EVALUACIÓN

### 11.1 Métricas por Nivel

**Estratégico**:
- Objetivos estratégicos completados (%)
- Recursos utilizados eficientemente (%)
- Tiempo de respuesta a crisis

**Operacional**:
- Misiones completadas exitosamente (%)
- Pérdidas vs bajas infligidas (K/D ratio)
- Coordinación entre secciones (A1-A6)

**Táctico**:
- Objetivos tácticos logrados (%)
- Supervivencia de unidades (%)
- Uso eficiente de armamento

### 11.2 After Action Review (AAR)

Al final de cada sesión, se genera reporte con:
- Timeline de eventos clave
- Decisiones tomadas por nivel
- Resultado de combates
- Análisis de errores/aciertos
- Recomendaciones

---

## 12. SEGURIDAD

### 12.1 Autenticación

- JWT tokens para sesiones
- bcrypt para passwords
- 2FA opcional para roles críticos (Director, Admin)

### 12.2 Autorización

- Validación de permisos en cada comando
- Rate limiting en API
- Audit log de todas las acciones

### 12.3 Protección contra Cheating

- Servidor authoritative (cliente solo muestra, no decide)
- Validación de comandos (física, recursos, fog of war)
- Detección de anomalías

---

## 13. ROADMAP DE IMPLEMENTACIÓN

### Fase 1: Core Multiplayer (4 semanas)
- [ ] Sistema de autenticación y usuarios
- [ ] Session manager
- [ ] WebSocket server
- [ ] Fog of War implementation
- [ ] Command router

### Fase 2: Niveles de Comando (3 semanas)
- [ ] Director console (web UI)
- [ ] Strategic console
- [ ] Operational console
- [ ] Tactical console

### Fase 3: Tipos de Juego (4 semanas)
- [ ] Guerra Externa (refactor existente)
- [ ] Conflicto Interno (insurgent AI)
- [ ] Gestión de Crisis (disaster simulation)

### Fase 4: IA Avanzada (3 semanas)
- [ ] Enemy AI con múltiples dificultades
- [ ] Insurgent AI
- [ ] Disaster simulator

### Fase 5: Consola de Administración (2 semanas)
- [ ] API REST completa
- [ ] Admin UI
- [ ] Scenario builder
- [ ] AI profile editor

### Fase 6: Testing y Refinamiento (2 semanas)
- [ ] Testing integración
- [ ] Balanceo de juego
- [ ] Optimización performance
- [ ] Documentación

**Total: ~18 semanas (4.5 meses)**

---

## 14. CONSIDERACIONES TÉCNICAS

### 14.1 Performance

- **Tick rate**: 1 Hz (1 update/sec) para Strategic/Operational, 10 Hz para Tactical
- **Concurrent games**: Hasta 10 sesiones simultáneas por servidor
- **Players per game**: Hasta 20 jugadores
- **Entities per game**: Hasta 500 entidades simultáneas

### 14.2 Escalabilidad

- **Horizontal scaling**: Múltiples workers de simulación
- **Load balancing**: Sesiones distribuidas entre workers
- **Database sharding**: Por región/organización

### 14.3 Monitoreo

- Prometheus + Grafana para métricas
- ELK stack para logs
- Healthchecks automáticos

---

Este documento define la arquitectura completa del sistema GAVILAN multiplayer. La implementación seguirá este diseño.
