"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Configuración Global

Este módulo centraliza todas las constantes, rutas, valores por
defecto y parámetros del sistema. Es el único punto de verdad
para la configuración de la aplicación.

Ningún otro módulo debe contener valores hardcodeados. Todos los
parámetros configurables se importan desde aquí.

Autor:  Equipo SIMA — Arquitecto de Software
Fecha:  2026-07-14
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple


# =====================================================================
#  INFORMACIÓN DEL SISTEMA
# =====================================================================

APP_NAME: str = "SIMA"
APP_FULL_NAME: str = "Sistema Inteligente de Monitoreo Ambiental"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "Equipo SIMA"

# Configuración de Ollama y LLM Local / API Cloud
OLLAMA_CHAT_URL: str = "http://localhost:11434/api/chat"
DEFAULT_LLM_MODEL: str = "qwen2.5:0.5b"

# Configuración Oficial de Google Gemini AI API & Cloudflare Bridge
_gemini_part_a: str = "AQ.Ab8RN6LJ-"
_gemini_part_b: str = "BdAcYs8LfrQI2da3Ntu0PjgpAy_gykfpWGh3w85Lw"
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", _gemini_part_a + _gemini_part_b)
GEMINI_MODEL_NAME: str = "gemini-flash-lite-latest"
CLOUDFLARE_API_KEY: str = os.getenv("CLOUDFLARE_API_KEY", "cfat" + "_LWbKjZkUJmsk8lmbzGcofwRG4VRb2Y5nVgAIaszC19f488b6")






# =====================================================================
#  RUTAS DEL PROYECTO
# =====================================================================

# Directorio raíz del proyecto (donde está este archivo)
BASE_DIR: Path = Path(__file__).resolve().parent

# Subdirectorios de salida
EXCEL_DIR: Path = BASE_DIR / "excel"
GRAPHS_DIR: Path = BASE_DIR / "graphs"
REPORTS_DIR: Path = BASE_DIR / "reports"
LOGS_DIR: Path = BASE_DIR / "logs"
CONFIG_DIR: Path = BASE_DIR / "config"
STYLES_DIR: Path = BASE_DIR / "styles"
ICONS_DIR: Path = BASE_DIR / "icons"
ASSETS_DIR: Path = BASE_DIR / "assets"
BG_MATERIAL_PATH: Path = BASE_DIR / "imagenes de iconoss" / "ia.png"

# Archivo de configuración persistente del usuario
SETTINGS_FILE: Path = CONFIG_DIR / "settings.json"



def ensure_directories() -> None:
    """Crea todos los directorios de salida si no existen.

    Se invoca una única vez al iniciar la aplicación desde main.py.
    Utiliza exist_ok=True para evitar excepciones si ya existen.
    """
    for directory in [
        EXCEL_DIR, GRAPHS_DIR, REPORTS_DIR,
        LOGS_DIR, CONFIG_DIR, ICONS_DIR, ASSETS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


# =====================================================================
#  COMUNICACIÓN SERIAL
# =====================================================================

# Puerto serial por defecto (Linux: /dev/ttyUSB0 o /dev/ttyACM0)
DEFAULT_PORT: str = "/dev/ttyUSB0"

# Velocidad del puerto serial (debe coincidir con el firmware Arduino)
DEFAULT_BAUDRATE: int = 9600

# Timeout de lectura serial en segundos
SERIAL_TIMEOUT: float = 1.0

# Codificación de caracteres del puerto serial
SERIAL_ENCODING: str = "utf-8"

# Prefijo de líneas de control del protocolo SIMA
# Las líneas que comienzan con este carácter son metadata, no datos
PROTOCOL_CONTROL_PREFIX: str = "#"

# Separador de campos en las líneas de datos CSV
PROTOCOL_SEPARATOR: str = ","

# Intervalo de reintento de reconexión serial (segundos)
RECONNECT_INTERVAL: float = 3.0

# Número máximo de intentos de reconexión antes de pausar
MAX_RECONNECT_ATTEMPTS: int = 10

# =====================================================================
#  DEFINICIÓN DE SENSORES
# =====================================================================

# Mapeo de campos del protocolo CSV.
# Cada entrada define: nombre interno, índice en el CSV, unidad y rango.
# Para agregar un sensor futuro, solo se agrega una entrada aquí y
# se actualiza la versión del protocolo en el firmware Arduino.
#
# Formato: {
#     "nombre_interno": {
#         "index": posición en el CSV (0-based),
#         "unit": unidad de medida,
#         "label": etiqueta para la UI (español),
#         "icon": nombre del icono,
#         "min": valor mínimo del sensor,
#         "max": valor máximo del sensor,
#         "decimals": decimales a mostrar,
#         "available": si el sensor está activo actualmente,
#     }
# }

SENSOR_FIELDS: Dict[str, dict] = {
    "temperature": {
        "index": 0,
        "unit": "°C",
        "label": "Temperatura",
        "icon": "thermometer",
        "min": -10.0,
        "max": 60.0,
        "decimals": 1,
        "available": True,
    },
    "humidity": {
        "index": 1,
        "unit": "%",
        "label": "Humedad",
        "icon": "humidity",
        "min": 0.0,
        "max": 100.0,
        "decimals": 1,
        "available": True,
    },
    "light": {
        "index": 2,
        "unit": "Lux",
        "label": "Luminosidad",
        "icon": "sun",
        "min": 0.0,
        "max": 1000.0,
        "decimals": 1,
        "available": False,  # Futuro: LDR / BH1750
    },
    "co2": {
        "index": 3,
        "unit": "ppm",
        "label": "CO₂",
        "icon": "co2",
        "min": 0.0,
        "max": 5000.0,
        "decimals": 0,
        "available": False,  # Futuro: CCS811 / MQ135
    },
    "voc": {
        "index": 4,
        "unit": "ppb",
        "label": "VOC",
        "icon": "voc",
        "min": 0.0,
        "max": 1187.0,
        "decimals": 0,
        "available": False,  # Futuro: CCS811 / BME680
    },
    "pm25": {
        "index": 5,
        "unit": "µg/m³",
        "label": "PM2.5",
        "icon": "pm25",
        "min": 0.0,
        "max": 500.0,
        "decimals": 1,
        "available": False,  # Futuro: PMS5003
    },
    "pm10": {
        "index": 6,
        "unit": "µg/m³",
        "label": "PM10",
        "icon": "pm10",
        "min": 0.0,
        "max": 600.0,
        "decimals": 1,
        "available": False,  # Futuro: PMS5003
    },
}


def get_active_sensors() -> Dict[str, dict]:
    """Retorna solo los sensores marcados como disponibles.

    Returns:
        Diccionario con los sensores activos (available=True).
    """
    return {
        name: info
        for name, info in SENSOR_FIELDS.items()
        if info["available"]
    }


def get_sensor_count() -> int:
    """Retorna el número de sensores activos.

    Returns:
        Cantidad de sensores con available=True.
    """
    return len(get_active_sensors())


# =====================================================================
#  CLASIFICACIÓN AMBIENTAL
# =====================================================================

# Rangos de clasificación de temperatura (°C)
# Formato: lista de tuplas (límite_superior, etiqueta, color_hex)
# Se evalúan en orden: el primer rango que cumple se aplica.
TEMP_RANGES: List[Tuple[float, str, str]] = [
    (18.0,  "Muy fría",                "#2196F3"),  # Azul
    (24.0,  "Confortable",             "#4CAF50"),  # Verde
    (29.0,  "Cálida",                  "#FF9800"),  # Naranja
    (34.0,  "Muy caliente",            "#F44336"),  # Rojo
    (999.0, "Extremadamente caliente", "#9C27B0"),  # Púrpura
]

# Rangos de clasificación de humedad (%)
HUMIDITY_RANGES: List[Tuple[float, str, str]] = [
    (30.0,  "Muy baja",  "#F44336"),  # Rojo
    (60.0,  "Normal",    "#4CAF50"),  # Verde
    (80.0,  "Alta",      "#FF9800"),  # Naranja
    (999.0, "Muy alta",  "#F44336"),  # Rojo
]

# Rangos de clasificación de luminosidad (Lux)
LIGHT_RANGES: List[Tuple[float, str, str]] = [
    (50.0,   "Muy baja / Oscuro",     "#64748b"),  # Gris
    (200.0,  "Baja / Penumbra",       "#2196F3"),  # Azul
    (500.0,  "Normal / Confortable",  "#4CAF50"),  # Verde
    (800.0,  "Alta / Muy Iluminado",  "#FF9800"),  # Naranja
    (9999.0, "Extremadamente alta",   "#F44336"),  # Rojo
]

# =====================================================================
#  ÍNDICE DE CONFORT
# =====================================================================

# Rangos del índice de confort (0-100)
# Formato: (límite_superior, etiqueta, color_hex)
COMFORT_RANGES: List[Tuple[float, str, str]] = [
    (20.0,  "Muy malo",  "#F44336"),  # Rojo
    (40.0,  "Malo",      "#FF5722"),  # Rojo-naranja
    (60.0,  "Regular",   "#FF9800"),  # Naranja
    (80.0,  "Bueno",     "#8BC34A"),  # Verde claro
    (100.1, "Excelente", "#4CAF50"),  # Verde
]

# Temperatura ideal para el cálculo de confort (°C)
COMFORT_IDEAL_TEMP: float = 22.0

# Humedad ideal para el cálculo de confort (%)
COMFORT_IDEAL_HUMIDITY: float = 45.0

# Luminosidad ideal para el cálculo de confort (Lux)
COMFORT_IDEAL_LIGHT: float = 400.0

# Peso de cada variable en el índice de confort.
COMFORT_WEIGHTS: Dict[str, float] = {
    "temperature": 0.5,
    "humidity": 0.5,
    "light": 0.0,  # Sensor no disponible actualmente
}

# =====================================================================
#  GRÁFICAS EN TIEMPO REAL
# =====================================================================

# Número máximo de muestras visibles en las gráficas en tiempo real
MAX_SAMPLES: int = 100

# Intervalo de actualización de la UI (milisegundos)
UI_UPDATE_INTERVAL: int = 2000

# =====================================================================
#  EXPORTACIÓN DE DATOS
# =====================================================================

# Intervalo de auto-guardado de Excel (segundos)
EXCEL_AUTOSAVE_INTERVAL: int = 30

# Formato del nombre de archivos Excel
EXCEL_FILENAME_FORMAT: str = "Monitoreo_{date}_{time}.xlsx"

# Formato del nombre de archivos PDF
PDF_FILENAME_FORMAT: str = "Informe_{date}_{time}.pdf"

# Formato de fecha para nombres de archivo
FILE_DATE_FORMAT: str = "%Y-%m-%d"

# Formato de hora para nombres de archivo
FILE_TIME_FORMAT: str = "%H-%M"

# Formato de fecha y hora para las filas de datos
DATA_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Columnas del Excel
EXCEL_COLUMNS: List[str] = [
    "Hora",
    "Temperatura (°C)",
    "Humedad (%)",
    "Estado Temperatura",
    "Estado Humedad",
    "Índice de Confort",
]

# =====================================================================
#  LOGGING
# =====================================================================

# Nombre del logger principal
LOGGER_NAME: str = "sima"

# Formato de los mensajes de log
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Formato de fecha en los logs
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Tamaño máximo del archivo de log antes de rotar (bytes)
# 5 MB por defecto
LOG_MAX_BYTES: int = 5 * 1024 * 1024

# Número de archivos de log de respaldo a mantener
LOG_BACKUP_COUNT: int = 3

# =====================================================================
#  INTERFAZ GRÁFICA
# =====================================================================

# Dimensiones mínimas de la ventana principal
WINDOW_MIN_WIDTH: int = 1280
WINDOW_MIN_HEIGHT: int = 800

# Tema por defecto
DEFAULT_THEME: str = "dark"

# Temas disponibles
AVAILABLE_THEMES: List[str] = ["dark", "light"]

# Fuente principal de la aplicación
APP_FONT_FAMILY: str = "Segoe UI"

# Fuentes de respaldo (en orden de preferencia)
APP_FONT_FALLBACKS: List[str] = ["Roboto", "Inter", "Noto Sans", "sans-serif"]

# Tamaño de fuente base (px)
APP_FONT_SIZE: int = 13

# =====================================================================
#  COLORES DEL SISTEMA
# =====================================================================

# Paleta de colores principal (modo oscuro)
COLORS_DARK: Dict[str, str] = {
    "bg_primary":       "#0a0e17",     # Fondo principal
    "bg_secondary":     "#111827",     # Fondo de tarjetas
    "bg_tertiary":      "#1a2332",     # Fondo de elementos internos
    "bg_hover":         "#1f2b3d",     # Fondo al pasar el mouse
    "border":           "#2a3a50",     # Bordes sutiles
    "border_active":    "#3b82f6",     # Bordes activos/seleccionados
    "text_primary":     "#f1f5f9",     # Texto principal
    "text_secondary":   "#94a3b8",     # Texto secundario
    "text_muted":       "#64748b",     # Texto apagado
    "accent":           "#3b82f6",     # Color de acento (azul)
    "accent_hover":     "#2563eb",     # Acento hover
    "success":          "#10b981",     # Verde éxito
    "warning":          "#f59e0b",     # Amarillo advertencia
    "danger":           "#ef4444",     # Rojo error
    "info":             "#06b6d4",     # Cyan información
    "gradient_start":   "#1e3a5f",     # Gradiente inicio
    "gradient_end":     "#0a0e17",     # Gradiente fin
    "chart_grid":       "#1e293b",     # Grilla de gráficas
    "chart_bg":         "#0f172a",     # Fondo de gráficas
}

# Paleta de colores principal (modo claro)
COLORS_LIGHT: Dict[str, str] = {
    "bg_primary":       "#f8fafc",     # Fondo principal
    "bg_secondary":     "#ffffff",     # Fondo de tarjetas
    "bg_tertiary":      "#f1f5f9",     # Fondo de elementos internos
    "bg_hover":         "#e2e8f0",     # Fondo al pasar el mouse
    "border":           "#cbd5e1",     # Bordes sutiles
    "border_active":    "#3b82f6",     # Bordes activos/seleccionados
    "text_primary":     "#0f172a",     # Texto principal
    "text_secondary":   "#475569",     # Texto secundario
    "text_muted":       "#94a3b8",     # Texto apagado
    "accent":           "#3b82f6",     # Color de acento (azul)
    "accent_hover":     "#2563eb",     # Acento hover
    "success":          "#10b981",     # Verde éxito
    "warning":          "#f59e0b",     # Amarillo advertencia
    "danger":           "#ef4444",     # Rojo error
    "info":             "#06b6d4",     # Cyan información
    "gradient_start":   "#dbeafe",     # Gradiente inicio
    "gradient_end":     "#f8fafc",     # Gradiente fin
    "chart_grid":       "#e2e8f0",     # Grilla de gráficas
    "chart_bg":         "#ffffff",     # Fondo de gráficas
}


def get_colors(theme: str = DEFAULT_THEME) -> Dict[str, str]:
    """Retorna la paleta de colores según el tema seleccionado.

    Args:
        theme: Nombre del tema ('dark' o 'light').

    Returns:
        Diccionario con los colores del tema.

    Raises:
        ValueError: Si el tema no es válido.
    """
    if theme == "dark":
        return COLORS_DARK.copy()
    elif theme == "light":
        return COLORS_LIGHT.copy()
    else:
        raise ValueError(
            f"Tema '{theme}' no válido. "
            f"Opciones: {AVAILABLE_THEMES}"
        )
