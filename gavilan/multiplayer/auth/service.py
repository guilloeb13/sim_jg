"""
Servicio de autenticación para sistema multiplayer GAVILAN
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from .models import User, Session, UserRepository, SessionRepository


class AuthenticationError(Exception):
    """Error de autenticación"""
    pass


class AuthorizationError(Exception):
    """Error de autorización"""
    pass


class AuthService:
    """Servicio de autenticación y autorización"""

    def __init__(
        self,
        secret_key: str,
        token_expiry_hours: int = 24,
        user_repo: Optional[UserRepository] = None,
        session_repo: Optional[SessionRepository] = None,
    ):
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours
        self.user_repo = user_repo or UserRepository()
        self.session_repo = session_repo or SessionRepository()

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Registra un nuevo usuario"""
        # Validaciones básicas
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if "@" not in email:
            raise ValueError("Invalid email format")

        # Crear usuario
        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)

        # Guardar en repositorio
        return self.user_repo.create(user)

    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Autentica usuario y retorna (user, token)

        Raises:
            AuthenticationError: Si credenciales inválidas
        """
        # Buscar usuario
        user = self.user_repo.get_by_username(username)
        if not user:
            raise AuthenticationError("Invalid username or password")

        # Verificar password
        if not user.verify_password(password):
            raise AuthenticationError("Invalid username or password")

        # Verificar si está activo
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Generar JWT token
        token = self._generate_jwt_token(user)

        # Crear sesión
        session = Session(
            user_id=user.id,
            token=token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.token_expiry_hours),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session_repo.create(session)

        # Actualizar last_login
        user.last_login = datetime.now()
        self.user_repo.update(user)

        return user, token

    def logout(self, token: str) -> bool:
        """
        Cierra sesión invalidando el token

        Returns:
            True si se cerró sesión correctamente
        """
        session = self.session_repo.get_by_token(token)
        if session:
            return self.session_repo.invalidate(session.id)
        return False

    def verify_token(self, token: str) -> Optional[User]:
        """
        Verifica token JWT y retorna usuario si válido

        Returns:
            User si token válido, None si inválido
        """
        try:
            # Verificar JWT
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )

            # Verificar sesión
            session = self.session_repo.get_by_token(token)
            if not session or not session.is_valid():
                return None

            # Obtener usuario
            user_id = UUID(payload.get("user_id"))
            user = self.user_repo.get_by_id(user_id)

            if not user or not user.is_active:
                return None

            return user

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def _generate_jwt_token(self, user: User) -> str:
        """Genera JWT token para usuario"""
        payload = {
            "user_id": str(user.id),
            "username": user.username,
            "roles": [r.value for r in user.roles],
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(hours=self.token_expiry_hours),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        self.session_repo.cleanup_expired()


# Singleton global para el servicio de autenticación
_auth_service: Optional[AuthService] = None


def get_auth_service(secret_key: str = "CHANGE_ME_IN_PRODUCTION") -> AuthService:
    """Obtiene instancia singleton del servicio de autenticación"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(secret_key=secret_key)
    return _auth_service
