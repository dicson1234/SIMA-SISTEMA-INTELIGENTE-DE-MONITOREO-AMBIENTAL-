"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Gestión de Configuración Persistente

Administra las preferencias del usuario almacenándolas en un
archivo JSON. Las configuraciones sobreviven entre sesiones
de la aplicación.

Responsabilidades:
    - Cargar configuración desde archivo JSON al iniciar.
    - Guardar configuración al modificar cualquier preferencia.
    - Proveer valores por defecto si el archivo no existe o
      está corrupto.
    - Validar que los valores sean coherentes antes de guardar.

El archivo de configuración se almacena en:
    config/settings.json

Autor:  Equipo SIMA — Ingeniero de Software
Fecha:  2026-07-14
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from config import (
    DEFAULT_PORT,
    DEFAULT_BAUDRATE,
    DEFAULT_THEME,
    UI_UPDATE_INTERVAL,
    EXCEL_AUTOSAVE_INTERVAL,
    EXCEL_DIR,
    GRAPHS_DIR,
    REPORTS_DIR,
    SETTINGS_FILE,
    AVAILABLE_THEMES,
    MAX_SAMPLES,
)
from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


# =====================================================================
#  VALORES POR DEFECTO
# =====================================================================

# Diccionario maestro de valores por defecto.
# Si el archivo JSON no existe, está incompleto o contiene valores
# inválidos, se usan estos valores como respaldo.
#
# Para agregar una nueva preferencia:
#   1. Agregar el key con su valor por defecto aquí.
#   2. Usar get()/set() en el módulo que la necesite.
#   No se requiere ningún otro cambio.

DEFAULT_SETTINGS: Dict[str, Any] = {
    # --- Comunicación serial ---
    "serial_port": DEFAULT_PORT,
    "serial_baudrate": DEFAULT_BAUDRATE,

    # --- Interfaz ---
    "theme": DEFAULT_THEME,
    "ui_update_interval": UI_UPDATE_INTERVAL,
    "max_samples": MAX_SAMPLES,

    # --- Exportación ---
    "excel_autosave_interval": EXCEL_AUTOSAVE_INTERVAL,
    "excel_directory": str(EXCEL_DIR),
    "graphs_directory": str(GRAPHS_DIR),
    "reports_directory": str(REPORTS_DIR),

    # --- Ventana ---
    "window_maximized": False,
    "window_width": 1280,
    "window_height": 800,

    # --- Monitoreo ---
    "auto_start": False,
    "auto_save_excel": True,
}


# =====================================================================
#  CLASE PRINCIPAL
# =====================================================================

class SettingsManager:
    """Gestor de configuración persistente del sistema SIMA.

    Carga, valida y almacena las preferencias del usuario en un
    archivo JSON. Implementa el patrón Singleton para garantizar
    una única instancia en toda la aplicación.

    Attributes:
        _instance: Referencia a la instancia única (Singleton).
        _settings: Diccionario con la configuración actual.
        _file_path: Ruta al archivo JSON de configuración.

    Example:
        >>> settings = SettingsManager()
        >>> port = settings.get("serial_port")
        >>> settings.set("theme", "light")
        >>> settings.save()
    """

    _instance: Optional["SettingsManager"] = None

    def __new__(cls) -> "SettingsManager":
        """Implementación del patrón Singleton.

        Garantiza que solo exista una instancia del gestor de
        configuración en toda la aplicación, evitando conflictos
        de lectura/escritura sobre el archivo JSON.

        Returns:
            La instancia única de SettingsManager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Inicializa el gestor de configuración.

        Carga la configuración desde el archivo JSON si existe.
        Si no existe o está corrupto, usa los valores por defecto
        y crea el archivo.
        """
        # Evitar reinicialización en llamadas posteriores (Singleton)
        if self._initialized:
            return

        self._file_path: Path = SETTINGS_FILE
        self._settings: Dict[str, Any] = {}

        # Cargar configuración existente o crear con defaults
        self._load()
        self._initialized = True

        logger.info(
            "SettingsManager inicializado — Archivo: %s",
            self._file_path,
        )

    # =================================================================
    #  ACCESO A CONFIGURACIÓN
    # =================================================================

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene el valor de una preferencia.

        Busca primero en la configuración del usuario. Si la clave
        no existe, busca en los valores por defecto. Si tampoco
        existe allí, retorna el default proporcionado.

        Args:
            key: Clave de la preferencia (ej: "serial_port").
            default: Valor de respaldo si la clave no existe en
                ningún diccionario.

        Returns:
            El valor de la preferencia solicitada.

        Example:
            >>> settings = SettingsManager()
            >>> settings.get("serial_port")
            '/dev/ttyUSB0'
            >>> settings.get("nonexistent", "fallback")
            'fallback'
        """
        return self._settings.get(
            key,
            DEFAULT_SETTINGS.get(key, default),
        )

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """Establece el valor de una preferencia.

        Actualiza la configuración en memoria y opcionalmente
        la guarda en disco de forma inmediata.

        Args:
            key: Clave de la preferencia a modificar.
            value: Nuevo valor de la preferencia.
            auto_save: Si True, guarda automáticamente en disco
                tras la modificación. Default: True.

        Example:
            >>> settings = SettingsManager()
            >>> settings.set("theme", "light")
        """
        old_value = self._settings.get(key)
        self._settings[key] = value

        if old_value != value:
            logger.debug(
                "Configuración cambiada: %s = %r (anterior: %r)",
                key, value, old_value,
            )

        if auto_save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        """Retorna una copia completa de la configuración actual.

        Combina los valores por defecto con las preferencias del
        usuario, donde las del usuario tienen prioridad.

        Returns:
            Diccionario con toda la configuración vigente.
        """
        merged = DEFAULT_SETTINGS.copy()
        merged.update(self._settings)
        return merged

    def reset(self) -> None:
        """Restaura toda la configuración a los valores por defecto.

        Reemplaza la configuración actual con los defaults y
        guarda el archivo JSON actualizado.
        """
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()
        logger.info("Configuración restaurada a valores por defecto")

    def reset_key(self, key: str) -> None:
        """Restaura una preferencia individual a su valor por defecto.

        Args:
            key: Clave de la preferencia a restaurar.
        """
        if key in DEFAULT_SETTINGS:
            self.set(key, DEFAULT_SETTINGS[key])
            logger.debug(
                "Preferencia restaurada: %s = %r",
                key, DEFAULT_SETTINGS[key],
            )

    # =================================================================
    #  PERSISTENCIA
    # =================================================================

    def save(self) -> bool:
        """Guarda la configuración actual en el archivo JSON.

        Escribe el archivo de forma atómica para evitar corrupción:
        primero escribe un archivo temporal, luego lo renombra.

        Returns:
            True si se guardó exitosamente, False en caso de error.
        """
        try:
            # Asegurar que el directorio existe
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            # Escribir con indentación para legibilidad humana
            temp_file = self._file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    self._settings,
                    f,
                    indent=4,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                f.write("\n")  # Newline final (buena práctica)

            # Renombrar atómicamente (previene corrupción)
            temp_file.replace(self._file_path)

            logger.debug("Configuración guardada en %s", self._file_path)
            return True

        except (OSError, PermissionError, TypeError) as e:
            logger.error(
                "Error al guardar configuración: %s — %s",
                type(e).__name__, str(e),
            )
            # Limpiar archivo temporal si quedó
            temp_file = self._file_path.with_suffix(".tmp")
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return False

    def _load(self) -> None:
        """Carga la configuración desde el archivo JSON.

        Si el archivo no existe, crea uno nuevo con los valores
        por defecto. Si existe pero está corrupto o incompleto,
        combina lo que se pueda leer con los defaults.
        """
        if not self._file_path.exists():
            logger.info(
                "Archivo de configuración no encontrado. "
                "Creando con valores por defecto: %s",
                self._file_path,
            )
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()
            return

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if not isinstance(loaded, dict):
                raise ValueError(
                    "El archivo de configuración no contiene un "
                    "objeto JSON válido"
                )

            # Combinar: defaults como base + valores del usuario
            self._settings = DEFAULT_SETTINGS.copy()
            self._settings.update(loaded)

            # Validar valores críticos
            self._validate()

            logger.info(
                "Configuración cargada desde %s (%d preferencias)",
                self._file_path, len(loaded),
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "Archivo de configuración corrupto: %s — "
                "Usando valores por defecto",
                str(e),
            )
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()

        except (OSError, PermissionError) as e:
            logger.error(
                "No se pudo leer el archivo de configuración: %s — "
                "Usando valores por defecto",
                str(e),
            )
            self._settings = DEFAULT_SETTINGS.copy()

    # =================================================================
    #  VALIDACIÓN
    # =================================================================

    def _validate(self) -> None:
        """Valida y corrige valores incoherentes en la configuración.

        Verifica que los valores cargados estén dentro de rangos
        aceptables. Si algún valor es inválido, lo reemplaza con
        el valor por defecto correspondiente.
        """
        # Validar tema
        if self._settings.get("theme") not in AVAILABLE_THEMES:
            logger.warning(
                "Tema inválido: '%s'. Usando '%s'",
                self._settings.get("theme"), DEFAULT_THEME,
            )
            self._settings["theme"] = DEFAULT_THEME

        # Validar baudrate (valores estándar)
        valid_baudrates = [
            300, 1200, 2400, 4800, 9600,
            19200, 38400, 57600, 115200,
        ]
        if self._settings.get("serial_baudrate") not in valid_baudrates:
            logger.warning(
                "Baudrate inválido: %s. Usando %d",
                self._settings.get("serial_baudrate"), DEFAULT_BAUDRATE,
            )
            self._settings["serial_baudrate"] = DEFAULT_BAUDRATE

        # Validar intervalo de actualización (mínimo 500ms, máximo 10s)
        interval = self._settings.get("ui_update_interval", UI_UPDATE_INTERVAL)
        if not isinstance(interval, (int, float)) or interval < 500:
            self._settings["ui_update_interval"] = UI_UPDATE_INTERVAL
        elif interval > 10000:
            self._settings["ui_update_interval"] = 10000

        # Validar intervalo de auto-guardado Excel (mínimo 10s, máximo 300s)
        excel_interval = self._settings.get(
            "excel_autosave_interval", EXCEL_AUTOSAVE_INTERVAL,
        )
        if not isinstance(excel_interval, (int, float)):
            self._settings["excel_autosave_interval"] = EXCEL_AUTOSAVE_INTERVAL
        elif excel_interval < 10:
            self._settings["excel_autosave_interval"] = 10
        elif excel_interval > 300:
            self._settings["excel_autosave_interval"] = 300

        # Validar max_samples (mínimo 10, máximo 1000)
        samples = self._settings.get("max_samples", MAX_SAMPLES)
        if not isinstance(samples, int) or samples < 10:
            self._settings["max_samples"] = MAX_SAMPLES
        elif samples > 1000:
            self._settings["max_samples"] = 1000

        # Validar directorios de exportación (deben ser cadenas no vacías)
        for dir_key in ["excel_directory", "graphs_directory", "reports_directory"]:
            dir_value = self._settings.get(dir_key, "")
            if not isinstance(dir_value, str) or not dir_value.strip():
                self._settings[dir_key] = DEFAULT_SETTINGS[dir_key]
                logger.warning(
                    "Directorio inválido para '%s'. Usando default.",
                    dir_key,
                )
