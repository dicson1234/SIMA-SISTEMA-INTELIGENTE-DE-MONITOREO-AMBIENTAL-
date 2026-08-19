"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Tarjetas de Monitoreo (Widgets de Métrica)

Implementa el widget CardWidget que muestra información en tiempo real
de una variable de sensor, incluyendo el valor crudo en gran formato,
icono, unidad, etiqueta descriptiva y estado cualitativo coloreado.

Autor:  Equipo SIMA — Diseñador UX/UI
Fecha:  2026-07-14
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from logger_manager import get_logger

# Logger del módulo
logger = get_logger(__name__)


class CardWidget(QFrame):
    """Tarjeta de métrica ambiental para mostrar datos del dashboard principal.

    Admite actualizaciones dinámicas de valor, estado y colores asociados,
    además de soportar un estado de 'Inactivo' (para sensores no disponibles).
    """

    def __init__(
        self,
        title: str,
        unit: str,
        icon_symbol: str = "⚡",
        parent: QWidget = None
    ) -> None:
        """Inicializa la tarjeta de métrica.

        Args:
            title: Nombre de la variable ambiental (ej. 'Temperatura').
            unit: Unidad de medida (ej. '°C').
            icon_symbol: Carácter Unicode representativo para el widget.
            parent: Widget contenedor.
        """
        super().__init__(parent)
        self.setObjectName("cardFrame") # Para mapear con la hoja de estilos (.qss)
        
        self.title: str = title
        self.unit: str = unit
        self.icon_symbol: str = icon_symbol
        self._is_available: bool = True

        self._init_ui()

    def _init_ui(self) -> None:
        """Construye el layout jerárquico y widgets internos de la tarjeta."""
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(15, 12, 15, 12)
        card_layout.setSpacing(6)

        # --- Fila Superior: Icono + Título ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icono minimalista
        self.label_icon = QLabel(self.icon_symbol)
        self.label_icon.setFont(QFont("Segoe UI", 16))
        self.label_icon.setStyleSheet("color: #3b82f6;") # Azul por defecto
        
        # Título
        self.label_title = QLabel(self.title)
        self.label_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.label_title.setStyleSheet("color: #94a3b8;") # Gris secundario

        header_layout.addWidget(self.label_icon)
        header_layout.addWidget(self.label_title)
        header_layout.addStretch()

        # --- Fila Central: Valor Principal + Unidad ---
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)

        self.label_value = QLabel("--.-")
        self.label_value.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.label_value.setStyleSheet("color: #f1f5f9;") # Blanco/Gris brillante
        
        self.label_unit = QLabel(self.unit)
        self.label_unit.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.label_unit.setStyleSheet("color: #94a3b8;")
        self.label_unit.setAlignment(Qt.AlignBottom)
        self.label_unit.setContentsMargins(0, 0, 0, 8) # Elevar unidad respecto al valor

        value_layout.addWidget(self.label_value)
        value_layout.addWidget(self.label_unit)
        value_layout.addStretch()

        # --- Fila Inferior: Estado Cualitativo ---
        self.label_status = QLabel("Listo")
        self.label_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.label_status.setContentsMargins(8, 4, 8, 4)
        self.label_status.setStyleSheet(
            "background-color: rgba(59, 130, 246, 0.15); color: #3b82f6; border-radius: 4px;"
        )
        self.label_status.setAlignment(Qt.AlignCenter)

        # Layout horizontal para envolver la etiqueta de estado y que no se estire completa
        status_wrapper = QHBoxLayout()
        status_wrapper.addWidget(self.label_status)
        status_wrapper.addStretch()

        # Armar la tarjeta
        card_layout.addLayout(header_layout)
        card_layout.addLayout(value_layout)
        card_layout.addLayout(status_wrapper)

        # Tamaño mínimo recomendado
        self.setMinimumSize(180, 140)

    def update_value(self, value: float, status_label: str, status_color: str) -> None:
        """Actualiza la información mostrada por la tarjeta.

        Args:
            value: Valor numérico actual.
            status_label: Etiqueta cualitativa (ej. 'Confortable').
            status_color: Color HEX representativo de la clasificación.
        """
        if not self._is_available:
            return

        # Actualizar valor numérico
        self.label_value.setText(f"{value:.1f}")

        # Actualizar estado cualitativo con estilo dinámico sutil
        self.label_status.setText(status_label)
        rgba_bg = self._hex_to_rgba(status_color, 40)
        self.label_status.setStyleSheet(
            f"background-color: {rgba_bg}; color: {status_color}; border-radius: 4px; padding: 2px 6px;"
        )
        
        # Opcional: Colorear el icono con el color de estado
        self.label_icon.setStyleSheet(f"color: {status_color};")

    def set_unavailable(self, message: str = "No disponible") -> None:
        """Configura la tarjeta en modo 'Inactivo' para sensores futuros no instalados."""
        self._is_available = False
        self.label_value.setText("---")
        self.label_status.setText(message)
        self.label_status.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.1); color: #64748b; border-radius: 4px; padding: 2px 6px;"
        )
        self.label_icon.setStyleSheet("color: #475569;")

    @staticmethod
    def _hex_to_rgba(hex_str: str, alpha: int) -> str:
        """Helper para convertir color Hex a cadena compatible RGBA."""
        hex_clean = hex_str.lstrip('#')
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
