"""
SIMA Backend — Módulo de Autenticación y Seguridad JWT
Manejo de Hashing de Contraseñas, JWT y Sembrado de Usuarios Iniciales.

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

import os
import hashlib
import hmac
import time
import logging
from typing import Optional, Dict, Any, Tuple
import jwt

from .database import DatabaseManager

logger = logging.getLogger("sima.backend.auth")

SECRET_KEY = os.environ.get("SIMA_JWT_SECRET", "sima_super_secret_jwt_key_2026_x98f")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Horas de validez


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Genera un hash seguro utilizando PBKDF2-HMAC-SHA256 con salt.
    Devuelve (password_hash, salt_hex).
    """
    if not salt:
        salt_bytes = os.urandom(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_hex = salt
        salt_bytes = bytes.fromhex(salt)

    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100_000
    )
    return pwd_hash.hex(), salt_hex


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifica si la contraseña dada coincide con el hash almacenado."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def create_access_token(data: Dict[str, Any], expires_delta_seconds: int = 86400) -> str:
    """Crea un token JWT firmado con fecha de expiración."""
    to_encode = data.copy()
    expire = int(time.time()) + expires_delta_seconds
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Token JWT inválido: %s", e)
        return None


class AuthManager:
    """Servicio de Autenticación de Usuarios y Perfiles de SIMA."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Crea usuarios semilla si la base de datos está vacía."""
        users = self.db.list_all_users()
        if not users:
            logger.info("Base de datos sin usuarios. Creando cuentas por defecto...")
            
            # 1. Administrador (admin / admin123)
            p_hash, salt = hash_password("admin123")
            self.db.create_user(
                username="admin",
                email="admin@sima.local",
                password_hash=p_hash,
                salt=salt,
                full_name="Dicson (Administrador)",
                role="admin",
                bio="Administrador Principal del Sistema SIMA",
                avatar_color="#8B5CF6"
            )

            # 2. Operador de Sensores (operator / operator123)
            p_hash2, salt2 = hash_password("operator123")
            self.db.create_user(
                username="operador",
                email="operador@sima.local",
                password_hash=p_hash2,
                salt=salt2,
                full_name="Isabela (Operadora)",
                role="operator",
                bio="Especialista en Instrumentación y Telemetría",
                avatar_color="#10B981"
            )

            # 3. Analista Ambiental (analyst / analyst123)
            p_hash3, salt3 = hash_password("analyst123")
            self.db.create_user(
                username="analista",
                email="analista@sima.local",
                password_hash=p_hash3,
                salt=salt3,
                full_name="Pérez / Pilar (Analista)",
                role="analyst",
                bio="Analista de Datos y Reportes Ambientales",
                avatar_color="#F59E0B"
            )

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "operator",
        bio: str = "",
        avatar_color: str = "#3B82F6"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Registra un nuevo usuario en el sistema."""
        if len(username.strip()) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres.", None
        if len(password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres.", None

        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            return False, "El nombre de usuario ya se encuentra registrado.", None

        p_hash, salt = hash_password(password)
        user_data = self.db.create_user(
            username=username,
            email=email,
            password_hash=p_hash,
            salt=salt,
            full_name=full_name,
            role=role,
            bio=bio,
            avatar_color=avatar_color
        )

        if not user_data:
            return False, "Error de base de datos al registrar el usuario.", None

        return True, "Registro exitoso.", user_data

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[str]]:
        """Autentica a un usuario y devuelve su perfil + token JWT."""
        user = self.db.get_user_by_username(username)
        if not user:
            return False, "Usuario o contraseña incorrectos.", None, None

        if not verify_password(password, user["password_hash"], user["salt"]):
            return False, "Usuario o contraseña incorrectos.", None, None

        self.db.update_last_login(user["id"])
        
        token_payload = {
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"],
            "email": user["email"]
        }
        token = create_access_token(token_payload)

        # Sanitizar contraseña antes de devolver
        user_profile = {k: v for k, v in user.items() if k not in ("password_hash", "salt")}
        return True, "Autenticación exitosa.", user_profile, token

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información del usuario a partir de su token JWT."""
        payload = decode_access_token(token)
        if not payload or "user_id" not in payload:
            return None
        
        user = self.db.get_user_by_id(payload["user_id"])
        if not user:
            return None
        return {k: v for k, v in user.items() if k not in ("password_hash", "salt")}
