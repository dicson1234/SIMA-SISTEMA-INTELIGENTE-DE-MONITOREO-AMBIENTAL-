"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Gestión de Estadísticas (Motor Estadístico)

Calcula de forma incremental y eficiente las estadísticas de la sesión,
como máximos, mínimos, promedios, cantidad de muestras y tiempo total
de monitoreo.

Responsabilidades:
    - Mantener actualizadas las estadísticas (O(1)) ante cada lectura.
    - Medir el tiempo de monitoreo acumulado.
    - Proveer un método de exportación de estadísticas en formato diccionario.
    - Reiniciar las métricas al limpiar la sesión.

Autor:  Equipo SIMA — Especialista en Adquisición de Datos
Fecha:  2026-07-14
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading

from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


class StatisticsManager:
    """Calcula y mantiene las estadísticas de la sesión de monitoreo.

    Utiliza operaciones de actualización incremental para optimizar
    el rendimiento en sistemas embebidos o ejecuciones continuas
    de largo plazo.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self.reset()

    def reset(self) -> None:
        """Reinicia todos los acumuladores y variables estadísticas."""
        with self._lock:
            # Tiempos de monitoreo
            self._start_time: Optional[datetime] = None
            self._last_update_time: Optional[datetime] = None
            self._paused_duration: timedelta = timedelta()
            self._is_running: bool = False

            # Contadores
            self._sample_count: int = 0

            # Estadísticas de Temperatura
            self._temp_min: float = float('inf')
            self._temp_max: float = float('-inf')
            self._temp_sum: float = 0.0

            # Estadísticas de Humedad
            self._hum_min: float = float('inf')
            self._hum_max: float = float('-inf')
            self._hum_sum: float = 0.0

        logger.info("Estadísticas reiniciadas")

    def start(self) -> None:
        """Inicia o reanuda la medición del tiempo de monitoreo."""
        with self._lock:
            if not self._is_running:
                now = datetime.now()
                if self._start_time is None:
                    self._start_time = now
                self._last_update_time = now
                self._is_running = True
                logger.info("Monitoreo estadístico de tiempo iniciado/reanudado")

    def pause(self) -> None:
        """Pausa la medición del tiempo de monitoreo."""
        with self._lock:
            if self._is_running:
                now = datetime.now()
                if self._last_update_time:
                    self._paused_duration += (now - self._last_update_time)
                self._is_running = False
                logger.info("Monitoreo estadístico de tiempo pausado")

    def update(self, temperature: float, humidity: float) -> None:
        """Actualiza las estadísticas con una nueva muestra.

        Args:
            temperature: Valor de temperatura de la nueva muestra.
            humidity: Valor de humedad de la nueva muestra.
        """
        with self._lock:
            # Aseguramos que esté corriendo la medición del tiempo
            if not self._is_running:
                now = datetime.now()
                if self._start_time is None:
                    self._start_time = now
                self._last_update_time = now
                self._is_running = True

            # Incrementar muestras
            self._sample_count += 1

            # Procesar Temperatura
            if temperature < self._temp_min:
                self._temp_min = temperature
            if temperature > self._temp_max:
                self._temp_max = temperature
            self._temp_sum += temperature

            # Procesar Humedad
            if humidity < self._hum_min:
                self._hum_min = humidity
            if humidity > self._hum_max:
                self._hum_max = humidity
            self._hum_sum += humidity

            # Registrar tiempo actual de actualización
            self._last_update_time = datetime.now()

    @property
    def elapsed_time(self) -> timedelta:
        """Retorna el tiempo total transcurrido en el monitoreo activo."""
        with self._lock:
            if self._start_time is None:
                return timedelta()

            if self._is_running and self._last_update_time:
                now = datetime.now()
                total_duration = now - self._start_time
                return total_duration
            elif self._last_update_time:
                return self._last_update_time - self._start_time
            
            return timedelta()

    def get_elapsed_time_str(self) -> str:
        """Retorna el tiempo de monitoreo formateado en HH:MM:SS."""
        elapsed = self.elapsed_time
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene una vista consolidada de todas las estadísticas de la sesión.

        Returns:
            Diccionario estructurado con las métricas calculadas.
        """
        with self._lock:
            count = self._sample_count
            has_data = count > 0

            return {
                "sample_count": count,
                "elapsed_time_str": self.get_elapsed_time_str(),
                "elapsed_seconds": self.elapsed_time.total_seconds(),
                
                # Temperatura
                "temp_min": round(self._temp_min, 1) if has_data else None,
                "temp_max": round(self._temp_max, 1) if has_data else None,
                "temp_avg": round(self._temp_sum / count, 1) if has_data else 0.0,
                
                # Humedad
                "hum_min": round(self._hum_min, 1) if has_data else None,
                "hum_max": round(self._hum_max, 1) if has_data else None,
                "hum_avg": round(self._hum_sum / count, 1) if has_data else 0.0,

            }
