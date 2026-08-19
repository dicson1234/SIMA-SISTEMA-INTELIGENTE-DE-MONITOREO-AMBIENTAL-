"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Clasificación Ambiental

Contiene la lógica de clasificación de variables ambientales
y el cálculo del índice de confort térmico. Es lógica pura
sin dependencias de la interfaz gráfica.

Responsabilidades:
    - Clasificar temperatura en rangos cualitativos.
    - Clasificar humedad en rangos cualitativos.
    - Calcular el índice de confort ambiental (0-100).
    - Clasificar el índice de confort en categorías.
    - Proveer colores asociados a cada clasificación.

El módulo está diseñado para ser extensible: cuando se agreguen
sensores de calidad del aire (CO₂, VOC, PM2.5), solo se necesita
agregar nuevos métodos de clasificación y actualizar los pesos
del índice de confort en config.py.

Autor:  Equipo SIMA — Especialista en Monitoreo Ambiental
Fecha:  2026-07-14
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from config import (
    TEMP_RANGES,
    HUMIDITY_RANGES,
    LIGHT_RANGES,
    COMFORT_RANGES,
    COMFORT_IDEAL_TEMP,
    COMFORT_IDEAL_HUMIDITY,
    COMFORT_IDEAL_LIGHT,
    COMFORT_WEIGHTS,
)


# =====================================================================
#  ESTRUCTURAS DE DATOS
# =====================================================================

@dataclass(frozen=True)
class Classification:
    """Resultado de una clasificación ambiental.

    Encapsula el valor medido junto con su clasificación
    cualitativa, el color asociado y metadatos adicionales.

    Attributes:
        value: Valor numérico medido por el sensor.
        label: Etiqueta cualitativa (ej: "Confortable").
        color: Color hexadecimal asociado (ej: "#4CAF50").
        unit: Unidad de medida (ej: "°C", "%").

    Example:
        >>> c = Classification(25.3, "Cálida", "#FF9800", "°C")
        >>> print(f"{c.value}{c.unit} — {c.label}")
        25.3°C — Cálida
    """
    value: float
    label: str
    color: str
    unit: str = ""


@dataclass(frozen=True)
class ComfortResult:
    """Resultado del cálculo del índice de confort ambiental.

    Attributes:
        score: Puntaje de confort (0-100).
            0 = condiciones extremadamente desfavorables.
            100 = condiciones ideales.
        label: Etiqueta cualitativa (ej: "Bueno").
        color: Color hexadecimal asociado al nivel.
        temp_score: Contribución individual de la temperatura (0-100).
        humidity_score: Contribución individual de la humedad (0-100).
        light_score: Contribución individual de la luminosidad (0-100).
    """
    score: float
    label: str
    color: str
    temp_score: float
    humidity_score: float
    light_score: float = 0.0


# =====================================================================
#  CLASIFICADOR AMBIENTAL
# =====================================================================

class EnvironmentalClassifier:
    """Clasificador de variables ambientales.

    Evalúa los valores medidos por los sensores y los clasifica
    en categorías cualitativas con colores asociados. También
    calcula un índice de confort compuesto.

    El clasificador es stateless (sin estado interno): cada
    llamada a sus métodos es independiente. Esto facilita las
    pruebas unitarias y evita efectos secundarios.
    """

    # =================================================================
    #  CLASIFICACIÓN DE TEMPERATURA
    # =================================================================

    @staticmethod
    def classify_temperature(value: float) -> Classification:
        """Clasifica un valor de temperatura en una categoría."""
        label, color = _classify_value(value, TEMP_RANGES)
        return Classification(
            value=round(value, 1),
            label=label,
            color=color,
            unit="°C",
        )

    # =================================================================
    #  CLASIFICACIÓN DE HUMEDAD
    # =================================================================

    @staticmethod
    def classify_humidity(value: float) -> Classification:
        """Clasifica un valor de humedad relativa en una categoría."""
        label, color = _classify_value(value, HUMIDITY_RANGES)
        return Classification(
            value=round(value, 1),
            label=label,
            color=color,
            unit="%",
        )

    # =================================================================
    #  CLASIFICACIÓN DE LUMINOSIDAD
    # =================================================================

    @staticmethod
    def classify_light(value: float) -> Classification:
        """Clasifica un valor de luminosidad en Lux.

        Args:
            value: Luminosidad en Lux (0-1000).

        Returns:
            Classification con valor, etiqueta, color y unidad.
        """
        label, color = _classify_value(value, LIGHT_RANGES)
        return Classification(
            value=round(value, 1),
            label=label,
            color=color,
            unit="Lux",
        )

    # =================================================================
    #  ÍNDICE DE CONFORT
    # =================================================================

    @staticmethod
    def compute_comfort(
        temperature: float,
        humidity: float,
        light: Optional[float] = None,
        co2: Optional[float] = None,
        voc: Optional[float] = None,
        pm25: Optional[float] = None,
    ) -> ComfortResult:
        """Calcula el índice de confort ambiental compuesto (0-100)."""
        # Puntaje individual de temperatura
        temp_score = _gaussian_score(
            value=temperature,
            ideal=COMFORT_IDEAL_TEMP,
            sigma=8.0,
        )

        # Puntaje individual de humedad
        humidity_score = _gaussian_score(
            value=humidity,
            ideal=COMFORT_IDEAL_HUMIDITY,
            sigma=25.0,
        )

        # Puntaje individual de luminosidad
        light_val = light if light is not None else COMFORT_IDEAL_LIGHT
        light_score = _gaussian_score(
            value=light_val,
            ideal=COMFORT_IDEAL_LIGHT,
            sigma=250.0,
        )

        # --- Puntaje compuesto ponderado ---
        weight_temp = COMFORT_WEIGHTS.get("temperature", 0.4)
        weight_hum = COMFORT_WEIGHTS.get("humidity", 0.4)
        weight_light = COMFORT_WEIGHTS.get("light", 0.2) if light is not None else 0.0

        total_weight = weight_temp + weight_hum + weight_light
        if total_weight > 0:
            weight_temp /= total_weight
            weight_hum /= total_weight
            weight_light /= total_weight

        score = (temp_score * weight_temp) + (humidity_score * weight_hum) + (light_score * weight_light)

        # Clasificar el puntaje
        label, color = _classify_value(score, COMFORT_RANGES)

        return ComfortResult(
            score=round(score, 1),
            label=label,
            color=color,
            temp_score=round(temp_score, 1),
            humidity_score=round(humidity_score, 1),
            light_score=round(light_score, 1),
        )

    # =================================================================
    #  CLASIFICACIÓN FUTURA (PREPARADA)
    # =================================================================

    @staticmethod
    def classify_co2(value: float) -> Classification:
        """Clasifica la concentración de CO₂.

        Preparado para sensores CCS811 / MQ135.
        Los rangos siguen las recomendaciones de la ASHRAE:
            < 400 ppm  → Excelente (aire exterior)
            400-1000   → Bueno (interior ventilado)
            1000-2000  → Regular (ventilación insuficiente)
            2000-5000  → Malo (somnolencia, dolor de cabeza)
            > 5000     → Peligroso

        Args:
            value: Concentración de CO₂ en ppm.

        Returns:
            Classification con valor, etiqueta, color y unidad.
        """
        co2_ranges: List[Tuple[float, str, str]] = [
            (400.0,  "Excelente",  "#4CAF50"),
            (1000.0, "Bueno",      "#8BC34A"),
            (2000.0, "Regular",    "#FF9800"),
            (5000.0, "Malo",       "#F44336"),
            (99999,  "Peligroso",  "#9C27B0"),
        ]
        label, color = _classify_value(value, co2_ranges)
        return Classification(
            value=round(value, 0),
            label=label,
            color=color,
            unit="ppm",
        )

    @staticmethod
    def classify_pm25(value: float) -> Classification:
        """Clasifica la concentración de PM2.5.

        Preparado para sensores PMS5003 / SDS011.
        Los rangos siguen el AQI (Air Quality Index) de la EPA:
            0-12     → Bueno
            12.1-35  → Moderado
            35.1-55  → Insalubre (grupos sensibles)
            55.1-150 → Insalubre
            > 150    → Muy insalubre

        Args:
            value: Concentración de PM2.5 en µg/m³.

        Returns:
            Classification con valor, etiqueta, color y unidad.
        """
        pm25_ranges: List[Tuple[float, str, str]] = [
            (12.0,  "Bueno",                  "#4CAF50"),
            (35.0,  "Moderado",               "#FF9800"),
            (55.0,  "Insalubre (sensibles)",  "#FF5722"),
            (150.0, "Insalubre",              "#F44336"),
            (9999,  "Muy insalubre",          "#9C27B0"),
        ]
        label, color = _classify_value(value, pm25_ranges)
        return Classification(
            value=round(value, 1),
            label=label,
            color=color,
            unit="µg/m³",
        )


# =====================================================================
#  FUNCIONES AUXILIARES (PRIVADAS)
# =====================================================================

def _classify_value(
    value: float,
    ranges: List[Tuple[float, str, str]],
) -> Tuple[str, str]:
    """Clasifica un valor numérico según una lista de rangos.

    Recorre la lista de rangos en orden y retorna la primera
    coincidencia donde value < límite_superior.

    Args:
        value: Valor numérico a clasificar.
        ranges: Lista de tuplas (límite_superior, etiqueta, color).
            Debe estar ordenada de menor a mayor.

    Returns:
        Tupla (etiqueta, color_hex) de la clasificación.

    Raises:
        ValueError: Si la lista de rangos está vacía.
    """
    if not ranges:
        raise ValueError("La lista de rangos no puede estar vacía")

    for threshold, label, color in ranges:
        if value < threshold:
            return label, color

    # Si ningún rango coincide, usar el último
    _, label, color = ranges[-1]
    return label, color


def _gaussian_score(
    value: float,
    ideal: float,
    sigma: float,
) -> float:
    """Calcula un puntaje de 0-100 usando una función gaussiana.

    La función gaussiana produce una curva suave en forma de
    campana centrada en el valor ideal. Cuanto más lejos esté
    el valor del ideal, menor será el puntaje.

    Fórmula:
        score = 100 × exp(-0.5 × ((value - ideal) / sigma)²)

    Propiedades:
        - value == ideal → score = 100
        - value == ideal ± sigma → score ≈ 60.6
        - value == ideal ± 2*sigma → score ≈ 13.5
        - value == ideal ± 3*sigma → score ≈ 1.1

    Args:
        value: Valor medido.
        ideal: Valor ideal (centro de la campana).
        sigma: Desviación estándar (controla la anchura).
            Valores menores = más sensible a desviaciones.

    Returns:
        Puntaje entre 0.0 y 100.0.
    """
    import math
    deviation = (value - ideal) / sigma
    return 100.0 * math.exp(-0.5 * deviation * deviation)
