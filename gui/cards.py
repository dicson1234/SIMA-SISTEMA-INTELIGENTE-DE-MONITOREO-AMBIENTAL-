"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Tarjetas de Métrica — v4 Olive Nature Elegance

Tarjetas con icono circular, valor grande, estado cualitativo con dot indicator.
Diseño fiel a la tercera imagen de referencia: fondo oliva/gris oscuro, bordes limpios, tipografía warm cream.

Autor:  Equipo SIMA — Diseñador UX/UI
Fecha:  2026-08-18
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logger_manager import get_logger

logger = get_logger(__name__)

# ─── Paleta Oliva Nature Elegance ───
_BG_CARD   = "#1e221c"
_BORDER    = "#2e342b"
_TEXT      = "#f2f0e8"
_TEXT_DIM  = "#969890"
_GREEN     = "#a5b98a"
_BEIGE     = "#d8d0be"


class CardWidget(QFrame):
    """Tarjeta de métrica ambiental estilo Olive Nature Elegance."""

    def __init__(
        self,
        title: str,
        unit: str,
        icon_symbol: str = "🌡️",
        parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("cardFrame")

        self.title: str = title
        self.unit: str = unit
        self.icon_symbol: str = icon_symbol
        self._is_available: bool = True

        self._init_ui()

    def _init_ui(self) -> None:
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(6)

        # ── Header: Icon + Title ──
        header = QHBoxLayout()
        header.setSpacing(8)

        self.label_icon = QLabel(self.icon_symbol)
        self.label_icon.setFont(QFont("Segoe UI Emoji", 13))
        self.label_icon.setAlignment(Qt.AlignCenter)
        self.label_icon.setFixedSize(30, 30)
        self.label_icon.setStyleSheet(f"""
            background-color: #252a23;
            border: 1px solid {_BORDER};
            border-radius: 15px;
            color: {_GREEN};
        """)

        self.label_title = QLabel(self.title)
        self.label_title.setFont(QFont("Segoe UI", 9.5))
        self.label_title.setStyleSheet(f"color: {_TEXT_DIM}; background: transparent;")

        header.addWidget(self.label_icon)
        header.addWidget(self.label_title)
        header.addStretch()

        # ── Value Row ──
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)

        self.label_value = QLabel("--.-")
        self.label_value.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.label_value.setStyleSheet(f"color: {_TEXT}; background: transparent;")

        self.label_unit = QLabel(self.unit)
        self.label_unit.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.label_unit.setStyleSheet(f"color: {_BEIGE}; background: transparent;")
        self.label_unit.setAlignment(Qt.AlignBottom)
        self.label_unit.setContentsMargins(0, 0, 0, 5)

        value_layout.addWidget(self.label_value)
        value_layout.addWidget(self.label_unit)
        value_layout.addStretch()

        # ── Status Row ──
        self.label_status = QLabel("● Listo")
        self.label_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.label_status.setStyleSheet(f"color: {_GREEN}; background: transparent;")

        card_layout.addLayout(header)
        card_layout.addLayout(value_layout)
        card_layout.addWidget(self.label_status)

        self.setMinimumSize(150, 115)

    def update_value(self, value: float, status_label: str, status_color: str) -> None:
        if not self._is_available:
            return

        self.label_value.setText(f"{value:.1f}")
        self.label_status.setText(f"● {status_label}")
        self.label_status.setStyleSheet(f"color: {status_color}; background: transparent;")
        self.label_icon.setStyleSheet(f"""
            background-color: #252a23;
            border: 1px solid {status_color};
            border-radius: 15px;
            color: {status_color};
        """)

    def set_unavailable(self, message: str = "No disponible") -> None:
        self._is_available = False
        self.label_value.setText("---")
        self.label_status.setText(f"● {message}")
        self.label_status.setStyleSheet("color: #969890; background: transparent;")
        self.label_icon.setStyleSheet(f"""
            background-color: #252a23;
            border: 1px solid #2e342b;
            border-radius: 15px;
            color: #969890;
        """)
