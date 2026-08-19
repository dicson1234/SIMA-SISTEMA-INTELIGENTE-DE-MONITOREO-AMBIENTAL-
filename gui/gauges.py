"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Indicadores Circulares (Gauge Widgets)

Implementa el widget GaugeWidget que dibuja un dial de progreso circular
de estilo plano e industrial para representar temperatura o humedad de forma
altamente visual e interactiva.

Autor:  Equipo SIMA — Especialista en Visualización Científica
Fecha:  2026-07-14
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt, QRectF, QSize

from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


class GaugeWidget(QWidget):
    """Widget de dial circular de progreso para visualización industrial.

    Dibuja un arco circular de 240 grados (estilo velocímetro) con una aguja o
    relleno de progreso y un indicador digital central.
    """

    def __init__(
        self,
        title: str,
        unit: str,
        min_val: float = 0.0,
        max_val: float = 100.0,
        parent: QWidget = None
    ) -> None:
        """Inicializa el dial circular.

        Args:
            title: Etiqueta del indicador (ej. 'Temperatura').
            unit: Unidad de medida (ej. '°C').
            min_val: Rango mínimo de escala.
            max_val: Rango máximo de escala.
            parent: Widget contenedor.
        """
        super().__init__(parent)
        self.title: str = title
        self.unit: str = unit
        self.min_val: float = min_val
        self.max_val: float = max_val

        # Estado inicial
        self.value: float = min_val
        self.color_hex: str = "#3b82f6" # Color por defecto

        self.setMinimumSize(QSize(180, 180))

    def update_value(self, value: float, color_hex: str) -> None:
        """Actualiza el valor actual y el color del dial.

        Args:
            value: Lectura numérica del sensor.
            color_hex: Color de clasificación asociado.
        """
        # Limitar valor dentro de la escala
        self.value = max(self.min_val, min(value, self.max_val))
        self.color_hex = color_hex
        self.update() # Forzar redibujado

    def paintEvent(self, event) -> None:
        """Dibuja el componente con QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        
        # Calcular rectángulos del arco
        x = (width - size) / 2.0
        y = (height - size) / 2.0
        rect = QRectF(x, y, size, size)

        # Angulo inicial y extensión de un velocímetro industrial estándar (240°)
        # Qt mide en 1/16 de grado. 0° está a la derecha (3 en punto).
        start_angle = -30 * 16  # Iniciar abajo a la derecha
        span_angle = -240 * 16  # Arco hacia la izquierda (sentido horario)

        # 1. Dibujar pista de fondo (Arco gris apagado)
        pen_bg = QPen(QColor("#1e293b"), 12) # Grosor de 12px
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect, start_angle, span_angle)

        # 2. Calcular ángulo de progreso basado en el valor
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        ratio = max(0.0, min(ratio, 1.0))
        progress_span = int(ratio * -240 * 16)

        # 3. Dibujar arco de progreso (Coloreado dinámicamente)
        pen_fg = QPen(QColor(self.color_hex), 12)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        painter.drawArc(rect, start_angle, progress_span)

        # 4. Dibujar textos en el centro (Indicador Digital)
        # Título
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(
            QRectF(x, y + size * 0.25, size, size * 0.15),
            Qt.AlignCenter,
            self.title.upper()
        )

        # Valor
        painter.setPen(QColor("#f1f5f9"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(
            QRectF(x, y + size * 0.4, size, size * 0.25),
            Qt.AlignCenter,
            f"{self.value:.1f}"
        )

        # Unidad
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            QRectF(x, y + size * 0.65, size, size * 0.15),
            Qt.AlignCenter,
            self.unit
        )

        # 5. Dibujar marcas de límites (Mín y Máx) en los extremos
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor("#475569"))
        # Mínimo (abajo izquierda)
        painter.drawText(
            QRectF(x - 5, y + size * 0.8, size * 0.3, 20),
            Qt.AlignCenter,
            f"{self.min_val:.0f}"
        )
        # Máximo (abajo derecha)
        painter.drawText(
            QRectF(x + size * 0.7, y + size * 0.8, size * 0.3, 20),
            Qt.AlignCenter,
            f"{self.max_val:.0f}"
        )

        painter.end()
