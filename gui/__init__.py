"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Paquete de Interfaz Gráfica de Usuario (GUI)

Componentes expuestos:
    - MainWindow: Ventana principal de control y orquestación.
    - DashboardWidget: Tablero del layout central.
    - CardWidget: Tarjetas de métricas ambientales.
    - GaugeWidget: Indicadores circulares (gauges).
    - RealTimeChartWidget: Gráficas de monitoreo con pyqtgraph.
    - SettingsDialog: Diálogo de configuración.
    - AIChatTabWidget: Pestaña de Asistente IA Conversacional.
    - DevNNTabWidget: Panel de Redes Neuronales (Desarrollador).

Autor:  Equipo SIMA — Arquitecto de Software
Fecha:  2026-08-09
"""

from gui.mainwindow import MainWindow
from gui.dashboard import DashboardWidget
from gui.cards import CardWidget
from gui.gauges import GaugeWidget
from gui.charts import RealTimeChartWidget
from gui.dialogs import SettingsDialog

__all__ = [
    'MainWindow',
    'DashboardWidget',
    'CardWidget',
    'GaugeWidget',
    'RealTimeChartWidget',
    'SettingsDialog',
]
