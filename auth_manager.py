"""
SIMA Client — Administrador de Sesión y Autenticación del Cliente (auth_manager.py)
Orquesta el inicio de sesión, almacenamiento de token de usuario y sincronización con el backend.

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal

from backend.auth import AuthManager as LocalAuthManager
from backend.database import DatabaseManager

logger = logging.getLogger("sima.auth_manager")


class AuthSessionManager(QObject):
    """
    Gestor de Sesión del Cliente SIMA.
    Mantiene el estado del usuario activo en la aplicación de escritorio y emite señales Qt.
    """

    user_logged_in = Signal(dict)
    user_logged_out = Signal()
    profile_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.local_auth = LocalAuthManager(self.db)
        self.current_user: Optional[Dict[str, Any]] = None
        self.auth_token: Optional[str] = None
        
        # Iniciar sesión automáticamente con la cuenta por defecto en modo local si existe
        self._auto_login_default()

    def _auto_login_default(self) -> None:
        """Inicia sesión por defecto con la cuenta de administrador inicial."""
        success, msg, user, token = self.local_auth.login("admin", "admin123")
        if success and user:
            self.current_user = user
            self.auth_token = token
            logger.info("Sesión inicial iniciada automáticamente para: %s (%s)", user["full_name"], user["role"])

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Realiza el inicio de sesión del usuario."""
        success, msg, user, token = self.local_auth.login(username, password)
        if success and user:
            self.current_user = user
            self.auth_token = token
            logger.info("Inicio de sesión exitoso para: %s", username)
            self.user_logged_in.emit(user)
            return True, msg
        return False, msg

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "operator",
        bio: str = "",
        avatar_color: str = "#3B82F6"
    ) -> Tuple[bool, str]:
        """Registra un nuevo usuario en la base de datos del backend."""
        success, msg, user = self.local_auth.register(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            bio=bio,
            avatar_color=avatar_color
        )
        if success and user:
            # Autologin tras registro
            self.login(username, password)
            return True, msg
        return False, msg

    def update_profile(self, **kwargs) -> Tuple[bool, str]:
        """Actualiza los datos del perfil activo."""
        if not self.current_user:
            return False, "No hay ningún usuario autenticado."

        user_id = self.current_user["id"]
        ok = self.db.update_profile(user_id, **kwargs)
        if ok:
            updated_user = self.db.get_user_by_id(user_id)
            if updated_user:
                self.current_user = {k: v for k, v in updated_user.items() if k not in ("password_hash", "salt")}
                self.profile_updated.emit(self.current_user)
                return True, "Perfil actualizado correctamente."
        return False, "Error al guardar cambios en el perfil."

    def logout(self) -> None:
        """Cierra la sesión del usuario activo."""
        username = self.current_user.get("username") if self.current_user else "desconocido"
        self.current_user = None
        self.auth_token = None
        logger.info("Sesión cerrada para el usuario: %s", username)
        self.user_logged_out.emit()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Devuelve los datos del usuario actualmente autenticado."""
        return self.current_user

    def is_admin(self) -> bool:
        """Verifica si el usuario activo tiene rol Administrador."""
        return self.current_user is not None and self.current_user.get("role") == "admin"


# Instancia Global Singleton del Gestor de Sesión
_session_instance: Optional[AuthSessionManager] = None

def get_auth_manager() -> AuthSessionManager:
    """Devuelve la instancia global del gestor de sesiones de usuario."""
    global _session_instance
    if _session_instance is None:
        _session_instance = AuthSessionManager()
    return _session_instance
