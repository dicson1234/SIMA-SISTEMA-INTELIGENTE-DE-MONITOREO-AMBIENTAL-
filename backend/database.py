"""
SIMA Backend — Gestión de Base de Datos SQLite
Módulo de Persistencia para Usuarios, Perfiles, Sesiones y Auditoría.

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("sima.backend.database")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
DB_PATH = os.path.join(DB_DIR, "sima_users.db")


class DatabaseManager:
    """Administrador de la base de datos SQLite para Usuarios y Perfiles de SIMA."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión configurada a SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Inicializa las tablas de la base de datos y crea el usuario por defecto."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla de Usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'operator',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # 2. Tabla de Perfiles de Usuario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    bio TEXT DEFAULT '',
                    avatar_color TEXT DEFAULT '#3B82F6',
                    temp_threshold REAL DEFAULT 30.0,
                    hum_threshold REAL DEFAULT 70.0,
                    light_threshold REAL DEFAULT 800.0,
                    notifications_enabled INTEGER DEFAULT 1,
                    preferred_theme TEXT DEFAULT 'Oscuro',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # 3. Tabla de Registros de Auditoría
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)

            # 4. Tabla de Histórico de Telemetría por Usuario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    temperature REAL,
                    humidity REAL,
                    luminosity REAL,
                    comfort_index REAL,
                    status_label TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)

            conn.commit()
            logger.info("Base de datos inicializada en: %s", self.db_path)

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        salt: str,
        full_name: str,
        role: str = "operator",
        bio: str = "",
        avatar_color: str = "#3B82F6"
    ) -> Optional[Dict[str, Any]]:
        """Crea un nuevo usuario y su perfil asociado."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, salt, role)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username.lower().strip(), email.lower().strip(), password_hash, salt, role)
                )
                user_id = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO profiles (user_id, full_name, bio, avatar_color)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, full_name.strip(), bio.strip(), avatar_color)
                )

                self.log_action(conn, user_id, "USER_REGISTERED", f"Usuario {username} registrado con rol {role}.")
                conn.commit()
                return self.get_user_by_id(user_id)
            except sqlite3.IntegrityError as e:
                logger.warning("Error de integridad al crear usuario %s: %s", username, e)
                return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Busca un usuario por su nombre de usuario."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.*, p.full_name, p.bio, p.avatar_color, p.temp_threshold, 
                       p.hum_threshold, p.light_threshold, p.notifications_enabled, p.preferred_theme
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                WHERE LOWER(u.username) = ?
                """,
                (username.lower().strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene usuario y perfil completo por ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.*, p.full_name, p.bio, p.avatar_color, p.temp_threshold, 
                       p.hum_threshold, p.light_threshold, p.notifications_enabled, p.preferred_theme
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                WHERE u.id = ?
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_profile(self, user_id: int, **kwargs) -> bool:
        """Actualiza los datos del perfil de usuario."""
        allowed_fields = {
            "full_name", "bio", "avatar_color", "temp_threshold",
            "hum_threshold", "light_threshold", "notifications_enabled", "preferred_theme"
        }
        updates = []
        params = []
        for key, val in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(val)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        sql = f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            self.log_action(conn, user_id, "PROFILE_UPDATED", f"Campos actualizados: {list(kwargs.keys())}")
            conn.commit()
            return cursor.rowcount > 0

    def update_last_login(self, user_id: int) -> None:
        """Actualiza la fecha de último inicio de sesión."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            self.log_action(conn, user_id, "USER_LOGIN", "Inicio de sesión exitoso.")
            conn.commit()

    def list_all_users(self) -> List[Dict[str, Any]]:
        """Obtiene el listado de todos los usuarios registrados."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login,
                       p.full_name, p.avatar_color, p.preferred_theme
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                ORDER BY u.id ASC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def log_action(self, conn: sqlite3.Connection, user_id: Optional[int], action: str, details: str) -> None:
        """Registra una acción en el historial de auditoría."""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene las últimas acciones registradas en el sistema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.action, a.details, a.timestamp, u.username
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.id DESC LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
