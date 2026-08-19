"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Indicadores Circulares — v8 Botanical Glow
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QSize

from logger_manager import get_logger

logger = get_logger(__name__)

class GaugeWidget(QWidget):
    """Dial circular 240° con estética Botanical Dark Luxury."""

    def __init__(self, title: str, unit: str,
                 min_val: float = 0.0, max_val: float = 100.0,
                 parent: QWidget = None) -> None:
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val

        self.value = min_val
        self.color_hex = "#82936b"      # oliva por defecto (antes azul)
        self._has_data = False          # muestra --.- hasta recibir datos

        self.setMinimumSize(QSize(180, 180))

    def update_value(self, value: float, color_hex: str) -> None:
        self.value = max(self.min_val, min(value, self.max_val))
        self.color_hex = color_hex
        self._has_data = True
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20

        x = (width - size) / 2.0
        y = (height - size) / 2.0
        rect = QRectF(x, y, size, size)

        start_angle = -30 * 16
        span_angle = -240 * 16

        # 1. Pista de fondo botanical
        pen_bg = QPen(QColor("#2e342b"), 10)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect, start_angle, span_angle)

        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        ratio = max(0.0, min(ratio, 1.0))
        progress_span = int(ratio * -240 * 16)

        c = QColor(self.color_hex)

        if self._has_data and progress_span != 0:
            # 2. Halo glow suave
            pen_glow = QPen(QColor(c.red(), c.green(), c.blue(), 45), 18)
            pen_glow.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_glow)
            painter.drawArc(rect, start_angle, progress_span)

            # 3. Arco de progreso
            pen_fg = QPen(c, 10)
            pen_fg.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fg)
            painter.drawArc(rect, start_angle, progress_span)

        # 4. Textos centrales
        painter.setPen(QColor("#969890"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(QRectF(x, y + size * 0.25, size, size * 0.15),
                         Qt.AlignCenter, self.title.upper())

        painter.setPen(QColor("#f2f0e8"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(QRectF(x, y + size * 0.4, size, size * 0.25),
                         Qt.AlignCenter,
                         f"{self.value:.1f}" if self._has_data else "--.-")

        painter.setPen(QColor("#969890"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(x, y + size * 0.65, size, size * 0.15),
                         Qt.AlignCenter, self.unit)

        # 5. Límites mín/máx
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor("#6a6e66"))
        painter.drawText(QRectF(x - 5, y + size * 0.8, size * 0.3, 20),
                         Qt.AlignCenter, f"{self.min_val:.0f}")
        painter.drawText(QRectF(x + size * 0.7, y + size * 0.8, size * 0.3, 20),
                         Qt.AlignCenter, f"{self.max_val:.0f}")

        painter.end()
