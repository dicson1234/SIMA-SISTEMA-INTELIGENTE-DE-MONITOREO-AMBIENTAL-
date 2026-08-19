"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Gráficas en Tiempo Real (Real-time Charts) — v2 Premium

Implementa el widget RealTimeChartWidget utilizando pyqtgraph para trazar
curvas de temperatura y humedad en tiempo real con diseño premium:
  - Gradiente de relleno bajo la curva (fill gradient).
  - Efecto de brillo (glow) en la línea principal.
  - Línea de promedio dinámico (dashed).
  - Indicadores de valor actual, mín/máx y promedio en tiempo real.
  - Estética industrial moderna tipo SCADA / Grafana.

Autor:  Equipo SIMA — Especialista en Visualización Científica
Fecha:  2026-07-14
"""

from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush
import pyqtgraph as pg

from config import MAX_SAMPLES


class RealTimeChartWidget(QFrame):
    """Widget de graficación en tiempo real premium para variables ambientales.

    Muestra una curva en tiempo real con efectos visuales avanzados:
    gradiente de relleno, glow, línea de promedio y estadísticas en vivo.
    """

    def __init__(
        self,
        title: str,
        unit: str,
        color: str = "#3b82f6",
        max_samples: int = MAX_SAMPLES,
        parent: QWidget = None
    ) -> None:
        """Inicializa el widget gráfico premium.

        Args:
            title: Título de la curva (ej. 'Temperatura').
            unit: Unidad física (ej. '°C').
            color: Color HEX de la línea de ploteo.
            max_samples: Límite de muestras a graficar simultáneamente.
            parent: Widget contenedor.
        """
        super().__init__(parent)
        self.setObjectName("plotContainer")
        self.max_samples: int = max_samples
        self.color: str = color
        self.title: str = title
        self.unit: str = unit
        self._data_buffer: List[float] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Configura el lienzo premium con header de estadísticas y pyqtgraph."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # ── HEADER: Título + Valor actual ──
        header = QHBoxLayout()
        header.setSpacing(8)

        # Indicador de color (dot)
        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 10))
        dot.setStyleSheet(f"color: {self.color}; background: transparent;")
        dot.setFixedWidth(16)

        self.label_title = QLabel(self.title.upper())
        self.label_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.label_title.setStyleSheet("color: #94a3b8; background: transparent;")

        self.label_current = QLabel(f"--.- {self.unit}")
        self.label_current.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_current.setStyleSheet(f"color: {self.color}; background: transparent;")
        self.label_current.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(dot)
        header.addWidget(self.label_title)
        header.addStretch()
        header.addWidget(self.label_current)

        # ── SUB-HEADER: Estadísticas mín/máx/prom ──
        self.label_stats = QLabel("Mín: --.-  ·  Máx: --.-  ·  Prom: --.-")
        self.label_stats.setFont(QFont("Segoe UI", 8))
        self.label_stats.setStyleSheet("color: #475569; background: transparent;")
        self.label_stats.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ── GRÁFICA pyqtgraph ──
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#080c14')
        self.plot_widget.setMenuEnabled(False)

        # Estilizar ejes
        for axis_name in ['left', 'bottom']:
            axis = self.plot_widget.getAxis(axis_name)
            axis.setPen(pg.mkPen(color='#1e293b', width=1))
            axis.setTextPen(pg.mkPen(color='#475569'))
            axis.setStyle(tickLength=-6)

        self.plot_widget.getAxis('bottom').setLabel('Últimas Muestras', color='#334155')
        self.plot_widget.getAxis('left').setLabel(self.unit, color='#334155')

        # Grilla ultra-sutil
        self.plot_widget.showGrid(x=True, y=True, alpha=0.06)
        self.plot_widget.getViewBox().setMouseMode(pg.ViewBox.RectMode)

        # Color base
        c = QColor(self.color)

        # 1. Curva de relleno (fill area) — gradiente bajo la curva
        self.fill_curve = pg.PlotCurveItem(pen=pg.mkPen(None))
        self.zero_curve = pg.PlotCurveItem(pen=pg.mkPen(None))
        fill_brush = QBrush(QColor(c.red(), c.green(), c.blue(), 20))
        self.fill_area = pg.FillBetweenItem(
            self.fill_curve, self.zero_curve, brush=fill_brush
        )
        self.plot_widget.addItem(self.fill_area)

        # 2. Efecto GLOW (línea ancha semitransparente detrás)
        glow_pen = pg.mkPen(
            color=QColor(c.red(), c.green(), c.blue(), 40), width=10
        )
        self.glow_curve = self.plot_widget.plot(pen=glow_pen)

        # 3. Línea principal de datos
        main_pen = pg.mkPen(color=self.color, width=2.5)
        self.curve = self.plot_widget.plot(pen=main_pen, name=self.title)

        # 4. Punto del valor actual (último dato)
        self.current_dot = pg.ScatterPlotItem(
            size=10, pen=pg.mkPen('#0a0e17', width=2),
            brush=pg.mkBrush(self.color)
        )
        self.plot_widget.addItem(self.current_dot)

        # 5. Línea de promedio (dashed amarilla)
        self.avg_line = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen(color='#fbbf24', width=1.2, style=Qt.DashLine),
            label='Prom: --.-',
            labelOpts={
                'color': '#fbbf24',
                'position': 0.92,
                'fill': QColor(0, 0, 0, 150),
                'movable': False
            }
        )
        self.avg_line.setVisible(False)
        self.plot_widget.addItem(self.avg_line)

        # Ensamblar layout
        layout.addLayout(header)
        layout.addWidget(self.label_stats)
        layout.addWidget(self.plot_widget, 1)

    def update_data(self, data_vector: List[float]) -> None:
        """Actualiza la curva y estadísticas con el vector de datos actual.

        Args:
            data_vector: Lista de valores reales (temperaturas o humedades).
        """
        if not data_vector:
            return

        plot_data = data_vector[-self.max_samples:] if len(data_vector) > self.max_samples else data_vector
        self._data_buffer = list(plot_data)

        x = list(range(len(plot_data)))
        y = list(plot_data)

        # Actualizar curvas
        self.curve.setData(x, y)
        self.glow_curve.setData(x, y)
        self.fill_curve.setData(x, y)
        self.zero_curve.setData(x, [min(y)] * len(y))

        # Punto del último valor
        self.current_dot.setData([x[-1]], [y[-1]])

        # Calcular estadísticas
        current = y[-1]
        min_val = min(y)
        max_val = max(y)
        avg_val = sum(y) / len(y)

        # Actualizar etiquetas
        self.label_current.setText(f"{current:.1f} {self.unit}")
        self.label_stats.setText(
            f"Mín: {min_val:.1f}  ·  Máx: {max_val:.1f}  ·  Prom: {avg_val:.1f}"
        )

        # Actualizar línea de promedio
        self.avg_line.setValue(avg_val)
        self.avg_line.label.setText(f"Prom: {avg_val:.1f}")
        self.avg_line.setVisible(True)

    def clear_plot(self) -> None:
        """Limpia la curva de la gráfica actual y restablece estadísticas."""
        self.curve.clear()
        self.glow_curve.clear()
        self.fill_curve.clear()
        self.zero_curve.clear()
        self.current_dot.clear()
        self.avg_line.setVisible(False)
        self.label_current.setText(f"--.- {self.unit}")
        self.label_stats.setText("Mín: --.-  ·  Máx: --.-  ·  Prom: --.-")
        self._data_buffer.clear()
