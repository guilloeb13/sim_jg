"""
Modelos de autenticación y usuarios para sistema multiplayer GAVILAN
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
import bcrypt


class Role(str, Enum):
    """Roles disponibles en el sistema"""
    # Administración
    ADMIN = "admin"                           # Administrador del sistema
    GAME_MASTER = "game_master"              # Director de juego de guerra

    # Bando BLUE
    BLUE_STRATEGIC = "blue_strategic"        # Comando estratégico BLUE
    BLUE_OPERATIONAL = "blue_operational"    # AOC - Air Operations Center BLUE
    BLUE_TACTICAL = "blue_tactical"          # Control táctico / Piloto BLUE

    # Bando RED
    RED_STRATEGIC = "red_strategic"          # Comando estratégico RED
    RED_OPERATIONAL = "red_operational"      # AOC RED
    RED_TACTICAL = "red_tactical"            # Control táctico / Piloto RED

    # Observador
    OBSERVER = "observer"                     # Solo lectura, ve todo


class Permission(str, Enum):
    """Permisos específicos del sistema"""
    # Simulación
    VIEW_ALL = "view_all"                     # Ver ambos bandos (Director/Observer)
    VIEW_OWN_SIDE = "view_own_side"          # Ver solo su bando
    PAUSE_SIMULATION = "pause_simulation"     # Pausar/reanudar simulación
    INJECT_EVENTS = "inject_events"           # Inyectar eventos (clima, cyber, etc)

    # Comandos estratégicos
    SET_ROE = "set_roe"                       # Establecer Rules of Engagement
    SET_STRATEGIC_OBJECTIVES = "set_strategic_objectives"
    ALLOCATE_RESOURCES = "allocate_resources"
    APPROVE_ATO = "approve_ato"

    # Comandos operacionales
    CREATE_ATO = "create_ato"                 # Crear Air Tasking Order
    ASSIGN_MISSIONS = "assign_missions"
    SCRAMBLE = "scramble"                     # Ordenar scramble
    COORDINATE_LOGISTICS = "coordinate_logistics"

    # Comandos tácticos
    CONTROL_AIRCRAFT = "control_aircraft"     # Control directo de aeronaves
    ENGAGE_TARGETS = "engage_targets"
    REQUEST_SUPPORT = "request_support"

    # Administración
    MANAGE_USERS = "manage_users"
    MANAGE_SCENARIOS = "manage_scenarios"
    MANAGE_AI_PROFILES = "manage_ai_profiles"


# Mapeo de roles a permisos
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.VIEW_ALL,
        Permission.PAUSE_SIMULATION,
        Permission.INJECT_EVENTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SCENARIOS,
        Permission.MANAGE_AI_PROFILES,
    ],
    Role.GAME_MASTER: [
        Permission.VIEW_ALL,
        Permission.PAUSE_SIMULATION,
        Permission.INJECT_EVENTS,
    ],
    Role.BLUE_STRATEGIC: [
        Permission.VIEW_OWN_SIDE,
        Permission.SET_ROE,
        Permission.SET_STRATEGIC_OBJECTIVES,
        Permission.ALLOCATE_RESOURCES,
        Permission.APPROVE_ATO,
    ],
    Role.BLUE_OPERATIONAL: [
        Permission.VIEW_OWN_SIDE,
        Permission.CREATE_ATO,
        Permission.ASSIGN_MISSIONS,
        Permission.SCRAMBLE,
        Permission.COORDINATE_LOGISTICS,
    ],
    Role.BLUE_TACTICAL: [
        Permission.VIEW_OWN_SIDE,
        Permission.CONTROL_AIRCRAFT,
        Permission.ENGAGE_TARGETS,
        Permission.REQUEST_SUPPORT,
    ],
    Role.RED_STRATEGIC: [
        Permission.VIEW_OWN_SIDE,
        Permission.SET_ROE,
        Permission.SET_STRATEGIC_OBJECTIVES,
        Permission.ALLOCATE_RESOURCES,
        Permission.APPROVE_ATO,
    ],
    Role.RED_OPERATIONAL: [
        Permission.VIEW_OWN_SIDE,
        Permission.CREATE_ATO,
        Permission.ASSIGN_MISSIONS,
        Permission.SCRAMBLE,
        Permission.COORDINATE_LOGISTICS,
    ],
    Role.RED_TACTICAL: [
        Permission.VIEW_OWN_SIDE,
        Permission.CONTROL_AIRCRAFT,
        Permission.ENGAGE_TARGETS,
        Permission.REQUEST_SUPPORT,
    ],
    Role.OBSERVER: [
        Permission.VIEW_ALL,
    ],
}


@dataclass
class User:
    """Usuario del sistema"""
    id: UUID = field(default_factory=uuid4)
    username: str = ""
    email: str = ""
    password_hash: str = ""  # bcrypt hash
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    roles: List[Role] = field(default_factory=list)

    def set_password(self, password: str):
        """Hash password con bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verifica password contra hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def has_permission(self, permission: Permission) -> bool:
        """Verifica si usuario tiene un permiso específico"""
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, []):
                return True
        return False

    def has_role(self, role: Role) -> bool:
        """Verifica si usuario tiene un rol específico"""
        return role in self.roles

    def add_role(self, role: Role):
        """Agrega un rol al usuario"""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: Role):
        """Remueve un rol del usuario"""
        if role in self.roles:
            self.roles.remove(role)

    def get_all_permissions(self) -> List[Permission]:
        """Retorna todos los permisos del usuario"""
        permissions = set()
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        return list(permissions)

    def to_dict(self) -> dict:
        """Serializa a diccionario (sin password)"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "roles": [r.value for r in self.roles],
            "permissions": [p.value for p in self.get_all_permissions()],
        }


@dataclass
class Session:
    """Sesión de autenticación"""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    token: str = ""  # JWT token
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def is_expired(self) -> bool:
        """Verifica si la sesión expiró"""
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """Verifica si la sesión es válida"""
        return self.is_active and not self.is_expired()


class UserRepository:
    """Repositorio de usuarios (en memoria para MVP, luego PostgreSQL)"""

    def __init__(self):
        self._users: dict[UUID, User] = {}
        self._username_index: dict[str, UUID] = {}
        self._email_index: dict[str, UUID] = {}

    def create(self, user: User) -> User:
        """Crea un nuevo usuario"""
        if user.username in self._username_index:
            raise ValueError(f"Username '{user.username}' already exists")
        if user.email in self._email_index:
            raise ValueError(f"Email '{user.email}' already exists")

        self._users[user.id] = user
        self._username_index[user.username] = user.id
        self._email_index[user.email] = user.id
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene usuario por ID"""
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene usuario por username"""
        user_id = self._username_index.get(username)
        if user_id:
            return self._users.get(user_id)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene usuario por email"""
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    def update(self, user: User) -> User:
        """Actualiza un usuario"""
        if user.id not in self._users:
            raise ValueError(f"User {user.id} not found")

        old_user = self._users[user.id]

        # Actualizar índices si cambió username o email
        if old_user.username != user.username:
            del self._username_index[old_user.username]
            self._username_index[user.username] = user.id

        if old_user.email != user.email:
            del self._email_index[old_user.email]
            self._email_index[user.email] = user.id

        self._users[user.id] = user
        return user

    def delete(self, user_id: UUID) -> bool:
        """Elimina un usuario"""
        user = self._users.get(user_id)
        if not user:
            return False

        del self._users[user_id]
        del self._username_index[user.username]
        del self._email_index[user.email]
        return True

    def list_all(self) -> List[User]:
        """Lista todos los usuarios"""
        return list(self._users.values())

    def find_by_role(self, role: Role) -> List[User]:
        """Encuentra usuarios por rol"""
        return [u for u in self._users.values() if u.has_role(role)]


class SessionRepository:
    """Repositorio de sesiones (en memoria, luego Redis)"""

    def __init__(self):
        self._sessions: dict[UUID, Session] = {}
        self._token_index: dict[str, UUID] = {}

    def create(self, session: Session) -> Session:
        """Crea una nueva sesión"""
        self._sessions[session.id] = session
        self._token_index[session.token] = session.id
        return session

    def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Obtiene sesión por ID"""
        return self._sessions.get(session_id)

    def get_by_token(self, token: str) -> Optional[Session]:
        """Obtiene sesión por token"""
        session_id = self._token_index.get(token)
        if session_id:
            return self._sessions.get(session_id)
        return None

    def invalidate(self, session_id: UUID) -> bool:
        """Invalida una sesión"""
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False

    def cleanup_expired(self):
        """Limpia sesiones expiradas"""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            session = self._sessions[sid]
            del self._token_index[session.token]
            del self._sessions[sid]
