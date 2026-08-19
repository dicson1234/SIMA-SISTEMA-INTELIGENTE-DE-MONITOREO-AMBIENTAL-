"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Gráficas en Tiempo Real — v3 Botanical Dark Luxury

Gráficas pyqtgraph con estética forestal profunda:
  - Fondo ultra-oscuro con trazos verde esmeralda
  - Gradiente de relleno bajo la curva (botanical green)
  - Efecto glow en la línea principal
  - Línea de promedio dinámico (dashed)
  - Indicadores de valor actual, mín/máx y promedio
  - Ejes y grilla en tonos musgo sutil

Autor:  Equipo SIMA — Visualización Científica
Fecha:  2026-08-18
"""

from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush
import pyqtgraph as pg

from config import MAX_SAMPLES


class RealTimeChartWidget(QFrame):
    """Widget de graficación en tiempo real con estética Botanical Dark."""

    def __init__(
        self,
        title: str,
        unit: str,
        color: str = "#4ade80",
        max_samples: int = MAX_SAMPLES,
        parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("plotContainer")
        self.max_samples: int = max_samples
        self.color: str = color
        self.title: str = title
        self.unit: str = unit
        self._data_buffer: List[float] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # ── HEADER: Título + Valor actual ──
        header = QHBoxLayout()
        header.setSpacing(8)

        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 10))
        dot.setStyleSheet(f"color: {self.color}; background: transparent;")
        dot.setFixedWidth(16)

        self.label_title = QLabel(self.title.upper() + " EN VIVO")
        self.label_title.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
        self.label_title.setStyleSheet("color: #7da88a; background: transparent; letter-spacing: 0.5px;")

        self.label_current = QLabel(f"--.- {self.unit}")
        self.label_current.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_current.setStyleSheet(f"color: {self.color}; background: transparent;")
        self.label_current.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(dot)
        header.addWidget(self.label_title)
        header.addStretch()
        header.addWidget(self.label_current)

        # ── SUB-HEADER: Estadísticas ──
        stats_bar = QHBoxLayout()
        stats_bar.setSpacing(16)

        self.lbl_min = QLabel("Mín: --.-")
        self.lbl_max = QLabel("Máx: --.-")
        self.lbl_avg = QLabel("Prom: --.-")

        for lbl in [self.lbl_min, self.lbl_max, self.lbl_avg]:
            lbl.setFont(QFont("Segoe UI", 8.5))
            lbl.setStyleSheet("color: #4a6b55; background: transparent;")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        stats_bar.addStretch()
        stats_bar.addWidget(self.lbl_min)
        stats_bar.addWidget(self.lbl_max)
        stats_bar.addWidget(self.lbl_avg)

        # ── GRÁFICA pyqtgraph ──
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#080d0a')
        self.plot_widget.setMenuEnabled(False)

        # Estilizar ejes con tonos musgo
        for axis_name in ['left', 'bottom']:
            axis = self.plot_widget.getAxis(axis_name)
            axis.setPen(pg.mkPen(color='#1e3025', width=1))
            axis.setTextPen(pg.mkPen(color='#4a6b55'))
            axis.setStyle(tickLength=-5)

        self.plot_widget.getAxis('bottom').setLabel('Muestras', color='#4a6b55')
        self.plot_widget.getAxis('left').setLabel(self.unit, color='#4a6b55')

        # Grilla ultra-sutil verde
        self.plot_widget.showGrid(x=True, y=True, alpha=0.05)
        self.plot_widget.getViewBox().setMouseMode(pg.ViewBox.RectMode)

        c = QColor(self.color)

        # 1. Relleno bajo la curva
        self.fill_curve = pg.PlotCurveItem(pen=pg.mkPen(None))
        self.zero_curve = pg.PlotCurveItem(pen=pg.mkPen(None))
        fill_brush = QBrush(QColor(c.red(), c.green(), c.blue(), 25))
        self.fill_area = pg.FillBetweenItem(
            self.fill_curve, self.zero_curve, brush=fill_brush
        )
        self.plot_widget.addItem(self.fill_area)

        # 2. Glow (línea ancha semitransparente)
        glow_pen = pg.mkPen(
            color=QColor(c.red(), c.green(), c.blue(), 35), width=10
        )
        self.glow_curve = self.plot_widget.plot(pen=glow_pen)

        # 3. Línea principal
        main_pen = pg.mkPen(color=self.color, width=2.5)
        self.curve = self.plot_widget.plot(pen=main_pen, name=self.title)

        # 4. Punto del último valor
        self.current_dot = pg.ScatterPlotItem(
            size=10, pen=pg.mkPen('#080d0a', width=2),
            brush=pg.mkBrush(self.color)
        )
        self.plot_widget.addItem(self.current_dot)

        # 5. Línea de promedio
        self.avg_line = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen(color='#a7f3d0', width=1.0, style=Qt.DashLine),
            label='Prom: --.-',
            labelOpts={
                'color': '#a7f3d0',
                'position': 0.92,
                'fill': QColor(10, 15, 12, 180),
                'movable': False
            }
        )
        self.avg_line.setVisible(False)
        self.plot_widget.addItem(self.avg_line)

        # Ensamblar
        layout.addLayout(header)
        layout.addLayout(stats_bar)
        layout.addWidget(self.plot_widget, 1)

    def update_data(self, data_vector: List[float]) -> None:
        if not data_vector:
            return

        plot_data = data_vector[-self.max_samples:] if len(data_vector) > self.max_samples else data_vector
        self._data_buffer = list(plot_data)

        x = list(range(len(plot_data)))
        y = list(plot_data)

        self.curve.setData(x, y)
        self.glow_curve.setData(x, y)
        self.fill_curve.setData(x, y)
        self.zero_curve.setData(x, [min(y)] * len(y))

        self.current_dot.setData([x[-1]], [y[-1]])

        current = y[-1]
        min_val = min(y)
        max_val = max(y)
        avg_val = sum(y) / len(y)

        self.label_current.setText(f"{current:.1f} {self.unit}")
        self.lbl_min.setText(f"Mín: {min_val:.1f}")
        self.lbl_max.setText(f"Máx: {max_val:.1f}")
        self.lbl_avg.setText(f"Prom: {avg_val:.1f}")

        self.avg_line.setValue(avg_val)
        self.avg_line.label.setText(f"Prom: {avg_val:.1f}")
        self.avg_line.setVisible(True)

    def clear_plot(self) -> None:
        self.curve.clear()
        self.glow_curve.clear()
        self.fill_curve.clear()
        self.zero_curve.clear()
        self.current_dot.clear()
        self.avg_line.setVisible(False)
        self.label_current.setText(f"--.- {self.unit}")
        self.lbl_min.setText("Mín: --.-")
        self.lbl_max.setText("Máx: --.-")
        self.lbl_avg.setText("Prom: --.-")
        self._data_buffer.clear()
