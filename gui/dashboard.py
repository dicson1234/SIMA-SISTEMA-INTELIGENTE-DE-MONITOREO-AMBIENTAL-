"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo del Dashboard Central (Layout Organizador) — v6 Diseño Pastel Especializado

Orquesta la disposición del panel central con tarjetas de métricas actuales,
gauges circulares, gráficas en tiempo real ampliadas y un panel lateral con pestañas
independientes para "Historial de Lecturas" (espacio completo) y "Bitácora de Logs".

Autor:  Equipo SIMA — Diseñador UX/UI & Especialista en Software
Fecha:  2026-08-09
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
    """Layout central y panel organizador principal de widgets visuales de SIMA."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Construye e integra la rejilla de visualización."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        # =====================================================================
        #  1. FILA SUPERIOR: TARJETAS DE MÉTRICA ACTUALES + GAUGES
        # =====================================================================
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # Sub-sección Tarjetas de Métrica Activas
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)

        self.card_temp = CardWidget(
            title="Temperatura", unit="°C", icon_symbol="🌡️", parent=self
        )
        self.card_hum = CardWidget(
            title="Humedad", unit="%", icon_symbol="💧", parent=self
        )
        self.card_comfort = CardWidget(
            title="Confort Ambiental", unit="pts", icon_symbol="🏠", parent=self
        )

        cards_layout.addWidget(self.card_temp)
        cards_layout.addWidget(self.card_hum)
        cards_layout.addWidget(self.card_comfort)

        # Sub-sección Gauges circulares
        gauges_card = QFrame()
        gauges_card.setObjectName("cardFrame")
        gauges_layout = QHBoxLayout(gauges_card)
        gauges_layout.setContentsMargins(8, 4, 8, 4)
        gauges_layout.setSpacing(8)

        self.gauge_temp = GaugeWidget(
            title="Temp. Actual", unit="°C",
            min_val=-10.0, max_val=50.0, parent=self
        )
        self.gauge_hum = GaugeWidget(
            title="Hum. Actual", unit="%",
            min_val=0.0, max_val=100.0, parent=self
        )

        gauges_layout.addWidget(self.gauge_temp)
        gauges_layout.addWidget(self.gauge_hum)

        top_layout.addLayout(cards_layout, 3)
        top_layout.addWidget(gauges_card, 2)

        # =====================================================================
        #  2. BANNER ULTRA-COMPACTO: CALIDAD DE AIRE FUTURA (FASE 2)
        # =====================================================================
        air_banner = QFrame()
        air_banner.setStyleSheet("""
            QFrame {
                background-color: #0b0914;
                border: 1px dashed #312e81;
                border-radius: 6px;
                padding: 2px 8px;
            }
        """)
        air_h = QHBoxLayout(air_banner)
        air_h.setContentsMargins(8, 3, 8, 3)
        air_h.setSpacing(12)

        lbl_air_title = QLabel("🌫️  Fase 2 (Próximamente):")
        lbl_air_title.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
        lbl_air_title.setStyleSheet("color: #a5b4fc;")

        lbl_co2 = QLabel("CO₂: -- ppm")
        lbl_co2.setStyleSheet("color: #64748b; font-size: 11px;")

        lbl_pm25 = QLabel("PM2.5: -- µg/m³")
        lbl_pm25.setStyleSheet("color: #64748b; font-size: 11px;")

        lbl_voc = QLabel("VOCs: -- ppb")
        lbl_voc.setStyleSheet("color: #64748b; font-size: 11px;")

        lbl_aqi = QLabel("AQI: --")
        lbl_aqi.setStyleSheet("color: #64748b; font-size: 11px;")

        air_h.addWidget(lbl_air_title)
        air_h.addWidget(lbl_co2)
        air_h.addWidget(lbl_pm25)
        air_h.addWidget(lbl_voc)
        air_h.addWidget(lbl_aqi)
        air_h.addStretch()

        # =====================================================================
        #  3. SECCIÓN PRINCIPAL: GRÁFICAS AMPLIADAS (IZQ) + PANEL DERECHO CON PESTAÑAS
        # =====================================================================
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # Panel Izquierdo: Gráficas en tiempo real
        charts_container = QWidget()
        charts_layout_v = QVBoxLayout(charts_container)
        charts_layout_v.setContentsMargins(0, 0, 0, 0)
        charts_layout_v.setSpacing(6)

        self.chart_temp = RealTimeChartWidget(
            title="Temperatura en Vivo", unit="°C",
            color="#7dd3fc", parent=self
        )
        self.chart_hum = RealTimeChartWidget(
            title="Humedad en Vivo", unit="%",
            color="#6ee7b7", parent=self
        )

        charts_layout_v.addWidget(self.chart_temp, 1)
        charts_layout_v.addWidget(self.chart_hum, 1)

        splitter.addWidget(charts_container)

        # Panel Derecho: Pestañas secundarias para Tabla de Muestras y Log del Sistema
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e293b;
                border-radius: 8px;
                background-color: #0b0f19;
            }
            QTabBar::tab {
                background: #111827;
                color: #94a3b8;
                padding: 6px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #1e1b4b;
                color: #c4b5fd;
                border-bottom: 2px solid #818cf8;
            }
        """)

        # Pestaña 1: HISTORIAL DE LECTURAS (Con máximo espacio vertical)
        tab_history = QWidget()
        layout_history = QVBoxLayout(tab_history)
        layout_history.setContentsMargins(6, 6, 6, 6)
        layout_history.setSpacing(4)

        self.table_widget = MeasurementTableWidget(parent=self)
        layout_history.addWidget(self.table_widget, 1)

        self.right_tabs.addTab(tab_history, "📋 Historial de Muestras")

        # Pestaña 2: BITÁCORA Y LOG DE EVENTOS EN VIVO (Panel dedicado)
        tab_log = QWidget()
        layout_log = QVBoxLayout(tab_log)
        layout_log.setContentsMargins(6, 6, 6, 6)
        layout_log.setSpacing(6)

        log_header = QHBoxLayout()
        lbl_log_title = QLabel("📜 Bitácora de Eventos & Logs")
        lbl_log_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_log_title.setStyleSheet("color: #c084fc;")

        btn_clear_log = QPushButton("Limpiar Log")
        btn_clear_log.setStyleSheet("padding: 2px 8px; font-size: 10px; background-color: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; border-radius: 4px;")
        btn_clear_log.clicked.connect(lambda: self.log_console.clear())

        log_header.addWidget(lbl_log_title)
        log_header.addStretch()
        log_header.addWidget(btn_clear_log)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #050811;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        layout_log.addLayout(log_header)
        layout_log.addWidget(self.log_console, 1)

        self.right_tabs.addTab(tab_log, "📜 Bitácora & Log del Sistema")

        splitter.addWidget(self.right_tabs)
        splitter.setSizes([580, 420])

        # Ensamblar layout principal
        main_layout.addLayout(top_layout)
        main_layout.addWidget(air_banner)
        main_layout.addWidget(splitter, 1)

        self.log_message('<span style="color:#34d399;">Sistema de Monitoreo SIMA iniciado. Muestreo cada 2s activo.</span>')

    def log_message(self, message: str) -> None:
        """Agrega un mensaje de evento a la consola de log visual con timestamp."""
        now_str = datetime.now().strftime("%H:%M:%S")
        log_line = f'<span style="color:#818cf8;">[{now_str}]</span> {message}'
        self.log_console.append(log_line)
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())
