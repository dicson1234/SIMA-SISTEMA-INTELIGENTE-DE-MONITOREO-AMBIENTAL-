"""
SIMA Backend — API REST en FastAPI
Endpoints para Autenticación, Perfiles de Usuario y Telemetría.

Ejecución directa:
    uvicorn backend.server:app --reload --port 8000

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from .database import DatabaseManager
from .auth import AuthManager, create_access_token, decode_access_token

app = FastAPI(
    title="SIMA REST API — Backend Service",
    description="API de Backend para Autenticación de Usuarios, Gestión de Perfiles y Telemetría Ambiental SIMA.",
    version="2.0.0"
)

# Configurar CORS para soportar clientes frontend o clientes remotos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
auth_service = AuthManager(db)


# ==========================================
# Modelos Pydantic para Validaciones
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "operator"
    bio: Optional[str] = ""
    avatar_color: Optional[str] = "#3B82F6"


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_color: Optional[str] = None
    temp_threshold: Optional[float] = None
    hum_threshold: Optional[float] = None
    light_threshold: Optional[float] = None
    notifications_enabled: Optional[int] = None
    preferred_theme: Optional[str] = None


class TelemetryItem(BaseModel):
    temperature: float
    humidity: float
    luminosity: float
    comfort_index: float
    status_label: str


# ==========================================
# Depedencias de Seguridad
# ==========================================

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Valida el token Bearer JWT enviado en el header Authorization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization no proporcionado o inválido."
        )

    token = authorization.split(" ")[1]
    user = auth_service.get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado."
        )
    return user


# ==========================================
# Endpoints de la API
# ==========================================

@app.get("/api/health", tags=["Salud"])
def health_check():
    """Comprueba que el backend esté operando adecuadamente."""
    return {"status": "ok", "service": "SIMA Backend API", "version": "2.0.0"}


@app.post("/api/auth/login", tags=["Autenticación"])
def login(req: LoginRequest):
    """Inicia sesión y genera un token JWT con los datos del perfil."""
    success, msg, user, token = auth_service.login(req.username, req.password)
    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)
    return {
        "status": "success",
        "message": msg,
        "token": token,
        "user": user
    }


@app.post("/api/auth/register", tags=["Autenticación"])
def register(req: RegisterRequest):
    """Registra una nueva cuenta de usuario y su perfil."""
    success, msg, user = auth_service.register(
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
        bio=req.bio,
        avatar_color=req.avatar_color
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {
        "status": "success",
        "message": msg,
        "user": user
    }


@app.get("/api/users/me", tags=["Perfiles"])
def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtiene la información del perfil del usuario autenticado."""
    return {"status": "success", "user": current_user}


@app.put("/api/users/profile", tags=["Perfiles"])
def update_profile(
    req: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Actualiza las preferencias o datos del perfil del usuario."""
    update_data = {k: v for k, v in req.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    ok = db.update_profile(current_user["id"], **update_data)
    if not ok:
        raise HTTPException(status_code=500, detail="Error al actualizar el perfil en la base de datos.")

    updated_user = db.get_user_by_id(current_user["id"])
    sanitized = {k: v for k, v in updated_user.items() if k not in ("password_hash", "salt")}
    return {"status": "success", "message": "Perfil actualizado correctamente.", "user": sanitized}


@app.get("/api/users/list", tags=["Administración"])
def list_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lista todos los usuarios del sistema (Requiere rol Administrador)."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de Administrador."
        )
    users = db.list_all_users()
    return {"status": "success", "count": len(users), "users": users}


@app.get("/api/audit/logs", tags=["Auditoría"])
def get_audit_logs(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Obtiene los registros de auditoría recientes del sistema."""
    logs = db.get_audit_logs(limit=50)
    return {"status": "success", "logs": logs}
