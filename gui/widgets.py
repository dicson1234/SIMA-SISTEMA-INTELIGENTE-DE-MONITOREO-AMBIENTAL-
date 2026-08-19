"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Widgets Reutilizables de Interfaz

Define componentes visuales especializados y reutilizables en la aplicación:
    - LEDIndicator: Representación gráfica de un diodo LED industrial para estados.
    - MeasurementTableWidget: Tabla optimizada para listar lecturas de sensores.

Autor:  Equipo SIMA — Diseñador UX/UI
Fecha:  2026-07-14
"""

from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen
from PySide6.QtCore import Qt, QSize

from config import EXCEL_COLUMNS
from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


# =====================================================================
#  INDICADOR LED INDUSTRIAL (DIBUJADO CON QPAINTER)
# =====================================================================

class LEDIndicator(QWidget):
    """Widget que simula un diodo LED de panel de control industrial.

    Dibuja un círculo con gradientes y sombras para dar una apariencia
    realista 3D y brillo de encendido/apagado.
    """

    def __init__(self, parent: QWidget = None, size: int = 16) -> None:
        """Inicializa el indicador LED.

        Args:
            parent: Widget contenedor.
            size: Diámetro del LED en píxeles.
        """
        super().__init__(parent)
        self._size: int = size

        # Colores por defecto para los estados (Hex)
        self._colors = {
            "green":  {"on": "#10b981", "off": "#047857", "glow": "#34d399"}, # Conectado
            "red":    {"on": "#ef4444", "off": "#b91c1c", "glow": "#f87171"}, # Desconectado
            "orange": {"on": "#f59e0b", "off": "#b45309", "glow": "#fbbf24"}, # Estabilizando / Alerta
            "gray":   {"on": "#64748b", "off": "#475569", "glow": "#94a3b8"}  # Apagado total
        }

        # Estado inicial (Apagado / Desconectado)
        self._color_key: str = "red"
        self._is_on: bool = True

        # Configurar tamaño del widget
        self.setFixedSize(QSize(size + 6, size + 6))

    def set_state(self, status: str) -> None:
        """Cambia el estado visual del LED.

        Args:
            status: Clave del estado ('connected' -> verde,
                    'disconnected' -> rojo, 'stabilizing' -> naranja,
                    'inactive' -> gris).
        """
        mapping = {
            "connected": "green",
            "disconnected": "red",
            "stabilizing": "orange",
            "inactive": "gray"
        }

        new_color = mapping.get(status, "gray")
        if self._color_key != new_color:
            self._color_key = new_color
            self.update() # Forzar redibujado de la UI

    def paintEvent(self, event) -> None:
        """Dibuja el LED utilizando QPainter en cada refresco de la pantalla."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        radius = self._size / 2.0
        center_x = width / 2.0
        center_y = height / 2.0

        # Obtener paleta de color activa
        palette = self._colors[self._color_key]
        base_color = QColor(palette["on"] if self._is_on else palette["off"])
        glow_color = QColor(palette["glow"])
        border_color = QColor(palette["off"])

        # 1. Dibujar el Brillo de Fondo (Glow Effect)
        if self._is_on:
            glow_grad = QRadialGradient(center_x, center_y, radius * 1.3)
            glow_grad.setColorAt(0.0, glow_color)
            glow_grad.setColorAt(0.8, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 100))
            glow_grad.setColorAt(1.0, Qt.transparent)
            painter.setBrush(QBrush(glow_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - radius * 1.3, center_y - radius * 1.3, radius * 2.6, radius * 2.6)

        # 2. Dibujar el Cuerpo del LED (3D Gradient)
        radial_grad = QRadialGradient(center_x - radius * 0.3, center_y - radius * 0.3, radius)
        radial_grad.setColorAt(0.0, QColor("#ffffff")) # Punto de luz
        radial_grad.setColorAt(0.2, glow_color)
        radial_grad.setColorAt(0.8, base_color)
        radial_grad.setColorAt(1.0, border_color)

        painter.setBrush(QBrush(radial_grad))
        painter.setPen(QPen(border_color, 1))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        painter.end()


# =====================================================================
#  TABLA DE MEDICIONES HISTÓRICAS
# =====================================================================

class MeasurementTableWidget(QTableWidget):
    """Widget de tabla especializado para listar los datos recolectados de sensores.

    Proporciona inserción thread-safe, estilos limpios y scroll automático.
    Columnas: Hora | Temp | Hum | Estado Temp | Estado Hum | Confort
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Configura la estructura inicial de la tabla."""
        self.setColumnCount(len(EXCEL_COLUMNS))
        self.setHorizontalHeaderLabels(EXCEL_COLUMNS)

        # Deshabilitar edición directa de celdas
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Selección de fila completa
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)

        # Ajustar cabeceras para expandirse de forma homogénea
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Ancho exacto para columna hora

        self.verticalHeader().setVisible(False) # Ocultar número de fila
        self.setAlternatingRowColors(True)     # Activar filas alternas

    def add_measurement(
        self,
        time_str: str,
        temp: float,
        hum: float,
        temp_status: str,
        temp_color: str,
        hum_status: str,
        hum_color: str,
        comfort_score: float,
        comfort_status: str,
        comfort_color: str
    ) -> None:
        """Inserta un nuevo registro de medición en la fila inferior de la tabla.

        Args:
            time_str: Timestamp de la lectura.
            temp: Temperatura.
            hum: Humedad.
            temp_status: Clasificación de temperatura.
            temp_color: Color HEX de temperatura.
            hum_status: Clasificación de humedad.
            hum_color: Color HEX de humedad.
            comfort_score: Valor del confort (0-100).
            comfort_status: Clasificación cualitativa del confort.
            comfort_color: Color HEX del confort.
        """
        row = self.rowCount()
        self.insertRow(row)

        # 1. Crear celdas (6 columnas: Hora, Temp, Hum, Est.Temp, Est.Hum, Confort)
        item_time = QTableWidgetItem(time_str)
        item_temp = QTableWidgetItem(f"{temp:.1f} °C")
        item_hum = QTableWidgetItem(f"{hum:.1f} %")
        item_temp_status = QTableWidgetItem(temp_status)
        item_hum_status = QTableWidgetItem(hum_status)

        comfort_txt = f"{comfort_score:.0f} — {comfort_status}"
        item_comfort = QTableWidgetItem(comfort_txt)

        # 2. Alinear textos
        item_time.setTextAlignment(Qt.AlignCenter)
        item_temp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_hum.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_temp_status.setTextAlignment(Qt.AlignCenter)
        item_hum_status.setTextAlignment(Qt.AlignCenter)
        item_comfort.setTextAlignment(Qt.AlignCenter)

        # 3. Colorear fondos de etiquetas de estado sutilmente
        item_temp_status.setBackground(QColor(self._hex_to_rgba(temp_color, 40)))
        item_temp_status.setForeground(QColor(temp_color))

        item_hum_status.setBackground(QColor(self._hex_to_rgba(hum_color, 40)))
        item_hum_status.setForeground(QColor(hum_color))

        item_comfort.setBackground(QColor(self._hex_to_rgba(comfort_color, 40)))
        item_comfort.setForeground(QColor(comfort_color))

        # 4. Cargar celdas a la fila (6 columnas)
        self.setItem(row, 0, item_time)
        self.setItem(row, 1, item_temp)
        self.setItem(row, 2, item_hum)
        self.setItem(row, 3, item_temp_status)
        self.setItem(row, 4, item_hum_status)
        self.setItem(row, 5, item_comfort)

        # 5. Desplazar scroll automáticamente al final
        self.scrollToBottom()

    def clear_table(self) -> None:
        """Limpia todos los registros visualizados en la tabla."""
        self.setRowCount(0)

    @staticmethod
    def _hex_to_rgba(hex_str: str, alpha: int) -> str:
        """Convierte un color HEX (ej. #ef4444) a una cadena rgba compatible con QColor."""
        hex_clean = hex_str.lstrip('#')
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
