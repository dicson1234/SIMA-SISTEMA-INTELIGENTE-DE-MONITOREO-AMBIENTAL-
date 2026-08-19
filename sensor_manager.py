"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo del Administrador de Datos de Sensores (Modelo)

Gestiona el almacenamiento en memoria de las mediciones de los sensores.
Actúa como la base del Modelo en el patrón MVVM, estructurando
cada lectura junto con su clasificación e índice de confort.

Responsabilidades:
    - Almacenar el historial de mediciones (para gráficas y tablas).
    - Orquestar la clasificación de cada lectura y cálculo de confort.
    - Proveer estructuras thread-safe o seguras para consultas.
    - Limpiar el historial en memoria cuando se requiera.

Autor:  Equipo SIMA — Ingeniero IoT
Fecha:  2026-07-14
"""

from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import threading

from config import MAX_SAMPLES, DATA_DATETIME_FORMAT
from classification import EnvironmentalClassifier, Classification, ComfortResult
from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


class SensorReading:
    """Representa una lectura completa y procesada de los sensores.

    Encapsula los valores crudos, la fecha y hora de adquisición,
    las clasificaciones cualitativas de cada variable y el resultado
    del índice de confort calculated.
    """

    def __init__(
        self,
        timestamp: datetime,
        temperature: float,
        humidity: float,
        light: float,
        temp_class: Classification,
        hum_class: Classification,
        light_class: Classification,
        comfort: ComfortResult,
    ) -> None:
        self.timestamp: datetime = timestamp
        self.temperature: float = temperature
        self.humidity: float = humidity
        self.light: float = light
        self.temp_class: Classification = temp_class
        self.hum_class: Classification = hum_class
        self.light_class: Classification = light_class
        self.comfort: ComfortResult = comfort

    @property
    def timestamp_str(self) -> str:
        """Retorna el timestamp formateado como cadena para la UI y reportes."""
        return self.timestamp.strftime(DATA_DATETIME_FORMAT)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la lectura a un diccionario plano."""
        return {
            "timestamp": self.timestamp_str,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "light": self.light,
            "temp_label": self.temp_class.label,
            "temp_color": self.temp_class.color,
            "hum_label": self.hum_class.label,
            "hum_color": self.hum_class.color,
            "light_label": self.light_class.label,
            "light_color": self.light_class.color,
            "comfort_score": self.comfort.score,
            "comfort_label": self.comfort.label,
            "comfort_color": self.comfort.color,
        }


class SensorManager:
    """Gestiona el modelo de datos y el historial de mediciones de sensores."""

    def __init__(self, max_chart_samples: int = MAX_SAMPLES) -> None:
        self._max_chart_samples: int = max_chart_samples
        self._recent_readings: deque[SensorReading] = deque(maxlen=max_chart_samples)
        self._all_readings: List[SensorReading] = []
        self._classifier: EnvironmentalClassifier = EnvironmentalClassifier()
        self._lock: threading.Lock = threading.Lock()
        
        logger.info(
            "SensorManager inicializado con buffer circular de %d muestras",
            max_chart_samples
        )

    def add_reading(self, temperature: float, humidity: float, light: float = 400.0) -> SensorReading:
        """Procesa, clasifica y almacena una nueva lectura de sensores.

        Args:
            temperature: Valor crudo de temperatura en °C.
            humidity: Valor crudo de humedad relativa en %.
            light: Valor crudo de luminosidad en Lux.

        Returns:
            La instancia de SensorReading generada y clasificada.
        """
        now = datetime.now()

        # Clasificación e índice de confort
        temp_class = self._classifier.classify_temperature(temperature)
        hum_class = self._classifier.classify_humidity(humidity)
        light_class = self._classifier.classify_light(light)
        comfort = self._classifier.compute_comfort(temperature, humidity, light)

        reading = SensorReading(
            timestamp=now,
            temperature=temperature,
            humidity=humidity,
            light=light,
            temp_class=temp_class,
            hum_class=hum_class,
            light_class=light_class,
            comfort=comfort,
        )

        with self._lock:
            self._recent_readings.append(reading)
            self._all_readings.append(reading)

        logger.debug(
            "Nueva lectura agregada: T=%.1f°C (%s), H=%.1f%% (%s), L=%.1f Lux (%s), Confort=%.1f (%s)",
            temperature, temp_class.label,
            humidity, hum_class.label,
            light, light_class.label,
            comfort.score, comfort.label
        )

        return reading

    @property
    def last_reading(self) -> Optional[SensorReading]:
        """Retorna la última lectura almacenada o None si el buffer está vacío."""
        with self._lock:
            return self._recent_readings[-1] if self._recent_readings else None

    def get_recent_readings(self) -> List[SensorReading]:
        """Retorna una copia de las últimas lecturas (para graficación)."""
        with self._lock:
            return list(self._recent_readings)

    def get_all_readings(self) -> List[SensorReading]:
        """Retorna el historial completo de lecturas de la sesión."""
        with self._lock:
            return list(self._all_readings)

    def get_recent_arrays(self) -> Tuple[List[float], List[float], List[float], List[float]]:
        """Retorna listas separadas de valores de tiempo real.

        Returns:
            Tupla conteniendo (temperaturas, humedades, luces, timestamps_epoch).
        """
        with self._lock:
            temps = [r.temperature for r in self._recent_readings]
            hums = [r.humidity for r in self._recent_readings]
            lights = [r.light for r in self._recent_readings]
            times = [r.timestamp.timestamp() for r in self._recent_readings]
        return temps, hums, lights, times

    def get_reading_count(self) -> int:
        """Retorna la cantidad total de lecturas guardadas en la sesión."""
        with self._lock:
            return len(self._all_readings)

    def clear(self) -> None:
        """Limpia todo el historial de datos en memoria."""
        with self._lock:
            self._recent_readings.clear()
            self._all_readings.clear()
        logger.info("Historial de datos en memoria limpiado")
