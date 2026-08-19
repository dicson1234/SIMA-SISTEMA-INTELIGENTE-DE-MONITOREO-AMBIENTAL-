"""
SIMA — Dashboard principal · Botanical Glass UI

Mantiene la lógica de telemetría existente, pero reorganiza la interfaz para que
el panel de monitoreo comparta el mismo lenguaje visual del asistente ambiental:
glassmorphism oscuro, verdes botánicos, jerarquía clara y superficies con textura.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSplitter, QFrame, QTextEdit, QTabWidget, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.cards import CardWidget
from gui.gauges import GaugeWidget
from gui.charts import RealTimeChartWidget
from gui.widgets import MeasurementTableWidget


class DashboardWidget(QWidget):
    """Dashboard principal de SIMA con estilo Botanical Glass."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardSurface")
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ── Encabezado contextual ──────────────────────────────────────────
        header = QFrame()
        header.setObjectName("dashboardHero")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("🌿  Monitoreo Ambiental")
        title.setObjectName("dashboardTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))

        subtitle = QLabel(
            "Visión en tiempo real del estado ambiental, tendencias y comportamiento del sistema."
        )
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9))

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 1)

        state = QLabel("●  MONITOREO LISTO")
        state.setObjectName("dashboardState")
        state.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(state)
        main_layout.addWidget(header)

        # ── Métricas principales ────────────────────────────────────────────
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(10)

        self.card_temp = CardWidget(
            title="Temperatura", unit="°C", icon_symbol="🌡️", parent=self
        )
        self.card_hum = CardWidget(
            title="Humedad Relativa", unit="%", icon_symbol="💧", parent=self
        )
        self.card_comfort = CardWidget(
            title="Confort Ambiental", unit="pts", icon_symbol="🍃", parent=self
        )

        for card in (self.card_temp, self.card_hum, self.card_comfort):
            card.setObjectName("dashboardMetricCard")
            metrics_layout.addWidget(card, 1)

        top_layout.addLayout(metrics_layout, 3)

        gauges_card = QFrame()
        gauges_card.setObjectName("dashboardGaugesCard")
        gauges_layout = QHBoxLayout(gauges_card)
        gauges_layout.setContentsMargins(10, 8, 10, 8)
        gauges_layout.setSpacing(6)

        self.gauge_temp = GaugeWidget(
            title="Temp. Actual", unit="°C", min_val=-10.0, max_val=50.0, parent=self
        )
        self.gauge_hum = GaugeWidget(
            title="Hum. Actual", unit="%", min_val=0.0, max_val=100.0, parent=self
        )
        gauges_layout.addWidget(self.gauge_temp)
        gauges_layout.addWidget(self.gauge_hum)
        top_layout.addWidget(gauges_card, 2)

        main_layout.addLayout(top_layout)

        # ── Estado de calidad ambiental / siguiente fase ───────────────────
        air_banner = QFrame()
        air_banner.setObjectName("airBanner")
        air_h = QHBoxLayout(air_banner)
        air_h.setContentsMargins(12, 8, 12, 8)
        air_h.setSpacing(10)

        lbl_air_title = QLabel("🌫️  CALIDAD DEL AIRE")
        lbl_air_title.setObjectName("airBannerTitle")
        lbl_air_title.setFont(QFont("Segoe UI", 9, QFont.Bold))

        chips = [
            ("CO₂", "-- ppm"),
            ("PM2.5", "-- µg/m³"),
            ("PM10", "-- µg/m³"),
            ("VOCs", "-- ppb"),
            ("AQI", "--"),
        ]
        air_h.addWidget(lbl_air_title)
        for name, value in chips:
            chip = QLabel(f"{name}  {value}")
            chip.setProperty("airChip", True)
            air_h.addWidget(chip)
        air_h.addStretch()

        phase = QLabel("FASE 2 · SENSORES AÉREOS")
        phase.setObjectName("airPhase")
        air_h.addWidget(phase)
        main_layout.addWidget(air_banner)

        # ── Analítica principal ─────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("dashboardSplitter")
        splitter.setHandleWidth(8)

        charts_container = QFrame()
        charts_container.setObjectName("chartsPanel")
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setContentsMargins(12, 10, 12, 10)
        charts_layout.setSpacing(8)

        charts_title = QLabel("📈  Tendencias en tiempo real")
        charts_title.setObjectName("panelTitle")
        charts_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        charts_layout.addWidget(charts_title)

        self.chart_temp = RealTimeChartWidget(
            title="Temperatura en Vivo", unit="°C", color="#a7d28d", parent=self
        )
        self.chart_hum = RealTimeChartWidget(
            title="Humedad en Vivo", unit="%", color="#7ebc8d", parent=self
        )
        charts_layout.addWidget(self.chart_temp, 1)
        charts_layout.addWidget(self.chart_hum, 1)

        splitter.addWidget(charts_container)

        # Panel derecho: historial y bitácora
        right_panel = QFrame()
        right_panel.setObjectName("historyPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.right_tabs = QTabWidget()
        self.right_tabs.setObjectName("dashboardInnerTabs")

        tab_history = QWidget()
        layout_history = QVBoxLayout(tab_history)
        layout_history.setContentsMargins(8, 8, 8, 8)
        self.table_widget = MeasurementTableWidget(parent=self)
        layout_history.addWidget(self.table_widget, 1)
        self.right_tabs.addTab(tab_history, "📋  Historial de Muestras")

        tab_log = QWidget()
        layout_log = QVBoxLayout(tab_log)
        layout_log.setContentsMargins(8, 8, 8, 8)
        layout_log.setSpacing(8)

        log_header = QHBoxLayout()
        lbl_log_title = QLabel("🧾  Bitácora del sistema")
        lbl_log_title.setObjectName("panelTitle")
        lbl_log_title.setFont(QFont("Segoe UI", 9.5, QFont.Bold))

        btn_clear_log = QPushButton("Limpiar")
        btn_clear_log.setObjectName("subtleButton")
        btn_clear_log.clicked.connect(lambda: self.log_console.clear())
        log_header.addWidget(lbl_log_title)
        log_header.addStretch()
        log_header.addWidget(btn_clear_log)

        self.log_console = QTextEdit()
        self.log_console.setObjectName("systemLog")
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("Consolas", 9.5))

        layout_log.addLayout(log_header)
        layout_log.addWidget(self.log_console, 1)
        self.right_tabs.addTab(tab_log, "📜  Bitácora & Eventos")

        right_layout.addWidget(self.right_tabs, 1)
        splitter.addWidget(right_panel)
        splitter.setSizes([660, 440])

        main_layout.addWidget(splitter, 1)

        self.log_message(
            '<span style="color:#a7d28d;">SIMA iniciado · monitoreo preparado.</span>'
        )

    def log_message(self, message: str) -> None:
        """Agrega un evento visual con timestamp."""
        now_str = datetime.now().strftime("%H:%M:%S")
        log_line = f'<span style="color:#86a968;">[{now_str}]</span> {message}'
        self.log_console.append(log_line)
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())
