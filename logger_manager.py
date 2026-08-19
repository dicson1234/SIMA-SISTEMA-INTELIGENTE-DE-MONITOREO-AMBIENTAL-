"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Logging Centralizado

Proporciona un sistema de logging profesional con las siguientes
características:
    - Rotación automática de archivos por tamaño.
    - Salida dual: archivo + consola.
    - Formato unificado con timestamp, nivel, módulo y mensaje.
    - Loggers hijos por módulo para trazabilidad precisa.
    - Colores en consola para facilitar la depuración.

Uso en cualquier módulo del proyecto:
    from logger_manager import get_logger
    logger = get_logger(__name__)
    logger.info("Mensaje informativo")
    logger.error("Algo falló", exc_info=True)

Autor:  Equipo SIMA — Ingeniero de Software
Fecha:  2026-07-14
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import (
    LOGGER_NAME,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    LOGS_DIR,
)


# =====================================================================
#  FORMATEADOR CON COLORES PARA CONSOLA
# =====================================================================

class ColorFormatter(logging.Formatter):
    """Formateador que agrega colores ANSI a la salida de consola.

    Los colores facilitan la identificación rápida del nivel de
    severidad durante el desarrollo y la depuración.

    Attributes:
        COLORS: Diccionario de códigos ANSI por nivel de logging.
        RESET: Código ANSI para restablecer el color.
    """

    COLORS: dict = {
        logging.DEBUG:    "\033[36m",   # Cyan
        logging.INFO:     "\033[32m",   # Verde
        logging.WARNING:  "\033[33m",   # Amarillo
        logging.ERROR:    "\033[31m",   # Rojo
        logging.CRITICAL: "\033[1;31m", # Rojo negrita
    }
    RESET: str = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Formatea el registro de log con colores ANSI.

        Args:
            record: Registro de logging a formatear.

        Returns:
            Cadena formateada con códigos de color ANSI.
        """
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# =====================================================================
#  INICIALIZACIÓN DEL SISTEMA DE LOGGING
# =====================================================================

# Bandera para evitar inicialización múltiple.
# Se activa la primera vez que se llama a setup_logging().
_initialized: bool = False


def setup_logging(
    log_level: int = logging.DEBUG,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logging.Logger:
    """Configura e inicializa el sistema de logging de SIMA.

    Crea el logger raíz del proyecto con handlers para archivo
    y consola. Debe llamarse una única vez al inicio de la
    aplicación, típicamente desde main.py.

    Si se llama más de una vez, retorna el logger existente sin
    modificaciones para evitar handlers duplicados.

    Args:
        log_level: Nivel mínimo de logging (default: DEBUG).
            Opciones: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_to_console: Si True, muestra logs en la terminal.
        log_to_file: Si True, escribe logs en archivo con rotación.

    Returns:
        Logger raíz configurado del proyecto SIMA.

    Example:
        >>> from logger_manager import setup_logging
        >>> logger = setup_logging()
        >>> logger.info("Sistema de logging iniciado")
    """
    global _initialized

    # Obtener o crear el logger raíz del proyecto
    root_logger = logging.getLogger(LOGGER_NAME)

    # Evitar inicialización duplicada
    if _initialized:
        return root_logger

    root_logger.setLevel(log_level)

    # Formateador estándar (sin colores, para archivo)
    file_formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )

    # Formateador con colores (para consola)
    console_formatter = ColorFormatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )

    # --- Handler de archivo con rotación ---
    if log_to_file:
        file_handler = _create_file_handler(file_formatter)
        if file_handler:
            root_logger.addHandler(file_handler)

    # --- Handler de consola ---
    if log_to_console:
        console_handler = _create_console_handler(console_formatter)
        root_logger.addHandler(console_handler)

    _initialized = True

    # Registrar inicio del sistema de logging
    root_logger.info("=" * 60)
    root_logger.info(
        "Sistema de logging SIMA iniciado — %s",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    root_logger.info("Nivel de logging: %s", logging.getLevelName(log_level))
    root_logger.info("=" * 60)

    return root_logger


def _create_file_handler(
    formatter: logging.Formatter,
) -> Optional[RotatingFileHandler]:
    """Crea un handler de archivo con rotación automática.

    El archivo de log se nombra con la fecha actual para facilitar
    la organización. Cuando alcanza el tamaño máximo configurado
    en config.py, se rota automáticamente manteniendo N respaldos.

    Args:
        formatter: Formateador a aplicar al handler.

    Returns:
        RotatingFileHandler configurado, o None si falla la creación.
    """
    try:
        # Asegurar que el directorio de logs existe
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Nombre del archivo con fecha actual
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"sima_{today}.log"

        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)

        return handler

    except (OSError, PermissionError) as e:
        # Si no podemos crear el archivo, continuamos solo con consola
        print(
            f"[ADVERTENCIA] No se pudo crear el archivo de log: {e}",
            file=sys.stderr,
        )
        return None


def _create_console_handler(
    formatter: logging.Formatter,
) -> logging.StreamHandler:
    """Crea un handler para salida por consola (stderr).

    Args:
        formatter: Formateador con colores a aplicar.

    Returns:
        StreamHandler configurado para stderr.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    return handler


# =====================================================================
#  FUNCIÓN PRINCIPAL DE ACCESO
# =====================================================================

def get_logger(module_name: str) -> logging.Logger:
    """Obtiene un logger hijo para un módulo específico.

    Cada módulo del proyecto debe llamar a esta función para
    obtener su propio logger. El logger hijo hereda la configuración
    del logger raíz (handlers, nivel, formato) y agrega el nombre
    del módulo al registro para trazabilidad.

    Si el sistema de logging aún no ha sido inicializado (caso de
    importación durante tests o uso independiente), se inicializa
    automáticamente con valores por defecto.

    Args:
        module_name: Nombre del módulo, típicamente __name__.
            Ejemplo: "serial_reader", "gui.mainwindow".

    Returns:
        Logger configurado para el módulo solicitado.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Módulo serial_reader iniciado")
        # Output: 2026-07-14 18:30:00 | INFO     | sima.serial_reader | Módulo serial_reader iniciado
    """
    global _initialized

    # Auto-inicialización si no se ha llamado a setup_logging()
    if not _initialized:
        setup_logging()

    # Crear logger hijo bajo el namespace del proyecto
    # Ejemplo: "sima.serial_reader", "sima.gui.mainwindow"
    return logging.getLogger(f"{LOGGER_NAME}.{module_name}")


# =====================================================================
#  FUNCIONES AUXILIARES
# =====================================================================

def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Exception,
) -> None:
    """Registra una excepción con traceback completo.

    Función de conveniencia para registrar excepciones de forma
    consistente en todo el proyecto. Incluye el tipo de excepción,
    el mensaje y el traceback completo.

    Args:
        logger: Logger del módulo que capturó la excepción.
        message: Mensaje descriptivo del contexto del error.
        exc: La excepción capturada.

    Example:
        >>> try:
        ...     result = 1 / 0
        ... except ZeroDivisionError as e:
        ...     log_exception(logger, "Error en cálculo", e)
    """
    logger.error(
        "%s — %s: %s",
        message,
        type(exc).__name__,
        str(exc),
        exc_info=True,
    )


def log_serial_event(event: str, detail: str = "") -> None:
    """Registra un evento relacionado con la comunicación serial.

    Función especializada para eventos del puerto serial, que
    son los más frecuentes y críticos del sistema.

    Args:
        event: Tipo de evento (ej: "CONECTADO", "DESCONECTADO").
        detail: Detalle adicional (ej: "/dev/ttyUSB0 @ 9600").
    """
    logger = get_logger("serial")
    if detail:
        logger.info("Serial [%s] — %s", event, detail)
    else:
        logger.info("Serial [%s]", event)


def log_data_event(event: str, detail: str = "") -> None:
    """Registra un evento relacionado con exportación de datos.

    Función especializada para eventos de guardado de archivos
    (Excel, PDF, CSV, gráficas).

    Args:
        event: Tipo de evento (ej: "EXCEL_GUARDADO", "PDF_GENERADO").
        detail: Detalle adicional (ej: ruta del archivo).
    """
    logger = get_logger("data")
    if detail:
        logger.info("Data [%s] — %s", event, detail)
    else:
        logger.info("Data [%s]", event)
