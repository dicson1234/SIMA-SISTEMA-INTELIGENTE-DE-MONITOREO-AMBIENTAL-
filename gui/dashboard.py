"""
SIMA — Dashboard Principal · v4 Olive Nature Elegance

Layout definitivo del panel de monitoreo según la 3ra imagen de referencia:
  - Paleta Oliva / Beige / Tierra Elegante
  - Tarjetas grandes, limpias y profesionales con espaciado amplio
  - Medidores y gráficas en tonos oliva (#a5b98a / #82936b)

Autor:  Equipo SIMA
Fecha:  2026-08-18
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
    """Dashboard principal de SIMA con estética Olive Nature Elegance."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardSurface")
        self._init_ui()

    def _init_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        # ═══════════════════════════════════════════════════
        #  1. ENCABEZADO HERO
        # ═══════════════════════════════════════════════════
        hero = QFrame()
        hero.setObjectName("dashboardHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("🌿  Monitoreo Ambiental")
        title.setObjectName("dashboardTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))

        subtitle = QLabel("Visión en tiempo real del estado ambiental, tendencias y comportamiento del sistema.")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setFont(QFont("Segoe UI", 9.5))

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hero_layout.addLayout(title_col, 1)

        badge = QLabel("●  MONITOREO LISTO")
        badge.setObjectName("dashboardState")
        badge.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(badge)
        main.addWidget(hero)

        # ═══════════════════════════════════════════════════
        #  2. MÉTRICAS + GAUGES
        # ═══════════════════════════════════════════════════
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(10)

        # 3 Tarjetas de métricas
        self.card_temp = CardWidget(
            title="Temperatura", unit="°C", icon_symbol="🌡️", parent=self
        )
        self.card_hum = CardWidget(
            title="Humedad Relativa", unit="%", icon_symbol="💧", parent=self
        )
        self.card_comfort = CardWidget(
            title="Confort Ambiental", unit="pts", icon_symbol="🍃", parent=self
        )

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)
        for card in (self.card_temp, self.card_hum, self.card_comfort):
            cards_layout.addWidget(card, 1)
        metrics_row.addLayout(cards_layout, 3)

        # Panel de Gauges
        gauges_frame = QFrame()
        gauges_frame.setObjectName("dashboardGaugesCard")
        gauges_inner = QHBoxLayout(gauges_frame)
        gauges_inner.setContentsMargins(12, 10, 12, 10)
        gauges_inner.setSpacing(8)

        self.gauge_temp = GaugeWidget(
            title="TEMP. ACTUAL", unit="°C", min_val=-10.0, max_val=50.0, parent=self
        )
        self.gauge_hum = GaugeWidget(
            title="HUM. ACTUAL", unit="%", min_val=0.0, max_val=100.0, parent=self
        )
        gauges_inner.addWidget(self.gauge_temp)
        gauges_inner.addWidget(self.gauge_hum)
        metrics_row.addWidget(gauges_frame, 2)

        main.addLayout(metrics_row)

        # ═══════════════════════════════════════════════════
        #  3. BANNER DE CALIDAD DEL AIRE
        # ═══════════════════════════════════════════════════
        air = QFrame()
        air.setObjectName("airBanner")
        air_h = QHBoxLayout(air)
        air_h.setContentsMargins(14, 8, 14, 8)
        air_h.setSpacing(10)

        air_title = QLabel("🌫️  CALIDAD DEL AIRE")
        air_title.setObjectName("airBannerTitle")
        air_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        air_h.addWidget(air_title)

        for name, val in [("CO₂","-- ppm"),("PM2.5","-- µg/m³"),("PM10","-- µg/m³"),("VOCs","-- ppb"),("AQI","--")]:
            chip = QLabel(f"{name}  {val}")
            chip.setProperty("airChip", True)
            air_h.addWidget(chip)
        air_h.addStretch()

        phase = QLabel("FASE 2 · SENSORES AÉREOS")
        phase.setObjectName("airPhase")
        air_h.addWidget(phase)
        main.addWidget(air)

        # ═══════════════════════════════════════════════════
        #  4. ANALÍTICA: GRÁFICAS + HISTORIAL
        # ═══════════════════════════════════════════════════
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("dashboardSplitter")
        splitter.setHandleWidth(6)

        # Panel izquierdo: Gráficas
        charts_panel = QFrame()
        charts_panel.setObjectName("chartsPanel")
        charts_v = QVBoxLayout(charts_panel)
        charts_v.setContentsMargins(14, 12, 14, 12)
        charts_v.setSpacing(8)

        charts_header = QLabel("📈  Tendencias en tiempo real")
        charts_header.setObjectName("panelTitle")
        charts_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        charts_v.addWidget(charts_header)

        self.chart_temp = RealTimeChartWidget(
            title="Temperatura", unit="°C", color="#a5b98a", parent=self
        )
        self.chart_hum = RealTimeChartWidget(
            title="Humedad", unit="%", color="#82936b", parent=self
        )
        charts_v.addWidget(self.chart_temp, 1)
        charts_v.addWidget(self.chart_hum, 1)

        splitter.addWidget(charts_panel)

        # Panel derecho: Historial + Bitácora
        right_panel = QFrame()
        right_panel.setObjectName("historyPanel")
        right_v = QVBoxLayout(right_panel)
        right_v.setContentsMargins(0, 0, 0, 0)

        self.right_tabs = QTabWidget()
        self.right_tabs.setObjectName("dashboardInnerTabs")

        # Tab: Historial
        tab_hist = QWidget()
        hist_v = QVBoxLayout(tab_hist)
        hist_v.setContentsMargins(8, 8, 8, 8)
        self.table_widget = MeasurementTableWidget(parent=self)
        hist_v.addWidget(self.table_widget, 1)
        self.right_tabs.addTab(tab_hist, "📋  Historial de Muestras")

        # Tab: Bitácora
        tab_log = QWidget()
        log_v = QVBoxLayout(tab_log)
        log_v.setContentsMargins(10, 10, 10, 10)
        log_v.setSpacing(8)

        log_header = QHBoxLayout()
        log_title = QLabel("🧾  Bitácora del sistema")
        log_title.setObjectName("panelTitle")
        log_title.setFont(QFont("Segoe UI", 9.5, QFont.Bold))

        btn_clear = QPushButton("Limpiar")
        btn_clear.setObjectName("subtleButton")
        btn_clear.clicked.connect(lambda: self.log_console.clear())
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(btn_clear)

        self.log_console = QTextEdit()
        self.log_console.setObjectName("systemLog")
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("JetBrains Mono", 9.5))

        log_v.addLayout(log_header)
        log_v.addWidget(self.log_console, 1)
        self.right_tabs.addTab(tab_log, "📜  Bitácora & Eventos")

        right_v.addWidget(self.right_tabs, 1)
        splitter.addWidget(right_panel)
        splitter.setSizes([660, 440])

        main.addWidget(splitter, 1)

        self.log_message(
            '<span style="color:#a5b98a;">SIMA iniciado · monitoreo preparado.</span>'
        )

    def log_message(self, message: str) -> None:
        """Agrega un evento visual con timestamp."""
        now_str = datetime.now().strftime("%H:%M:%S")
        log_line = f'<span style="color:#a5b98a;">[{now_str}]</span> {message}'
        self.log_console.append(log_line)
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())
