"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Generación de Gráficas Científicas — v2 Premium

Utiliza matplotlib con el backend no interactivo 'Agg' para renderizar
y exportar gráficas PNG de calidad profesional a partir de los datos
históricos. Diseñadas para su inserción directa en el reporte PDF
con estética de publicación científica.

Responsabilidades:
    - Generar gráficas de Temperatura y Humedad con diseño premium.
    - Aplicar estilos profesionales (gradientes, anotaciones, grid).
    - Asegurar la ejecución segura en hilos secundarios (thread-safe).

Autor:  Equipo SIMA — Especialista en Visualización Científica
Fecha:  2026-07-14
"""

import matplotlib
# Configurar backend no interactivo antes de importar pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import numpy as np

from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from config import GRAPHS_DIR
from sensor_manager import SensorReading
from logger_manager import get_logger, log_data_event

# Logger del módulo
logger = get_logger(__name__)

# Configuración de estilo global premium
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'axes.facecolor': '#f8fafc',
    'figure.facecolor': '#ffffff',
    'axes.edgecolor': '#cbd5e1',
    'axes.labelcolor': '#334155',
    'xtick.color': '#64748b',
    'ytick.color': '#64748b',
    'text.color': '#1e293b',
    'grid.color': '#e2e8f0',
    'grid.alpha': 0.7,
    'grid.linestyle': '--',
    'grid.linewidth': 0.5,
})


class GraphManager:
    """Gestiona la generación de archivos de imagen PNG con las curvas históricas de sensores."""

    def __init__(self, output_directory: Path = GRAPHS_DIR) -> None:
        """Inicializa el gestor de gráficas.

        Args:
            output_directory: Carpeta destino para guardar las imágenes generadas.
        """
        self.output_dir: Path = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_plots(self, readings: List[SensorReading]) -> Tuple[Path, Path]:
        """Genera y guarda las gráficas de Temperatura y Humedad.

        Args:
            readings: Lista de SensorReading con los datos históricos.

        Returns:
            Tupla conteniendo (Ruta_Temperatura_PNG, Ruta_Humedad_PNG).
        """
        if not readings:
            raise ValueError("No hay lecturas disponibles para graficar.")

        # Extraer vectores de datos
        timestamps: List[datetime] = [r.timestamp for r in readings]
        temperatures: List[float] = [r.temperature for r in readings]
        humidities: List[float] = [r.humidity for r in readings]

        # Rutas de salida
        temp_path = self.output_dir / "Temperatura.png"
        hum_path = self.output_dir / "Humedad.png"

        # Generar gráfica de Temperatura
        self._plot_premium_metric(
            x=timestamps,
            y=temperatures,
            title="Comportamiento Térmico — Temperatura vs Tiempo",
            ylabel="Temperatura (°C)",
            color="#2563eb",
            gradient_colors=("#dbeafe", "#eff6ff"),
            ideal_value=22.0,
            ideal_label="Zona de Confort (22°C)",
            output_path=temp_path
        )

        # Generar gráfica de Humedad
        self._plot_premium_metric(
            x=timestamps,
            y=humidities,
            title="Comportamiento Higrométrico — Humedad vs Tiempo",
            ylabel="Humedad Relativa (%)",
            color="#059669",
            gradient_colors=("#d1fae5", "#ecfdf5"),
            ideal_value=45.0,
            ideal_label="Nivel Óptimo (45%)",
            output_path=hum_path
        )

        log_data_event("GRAFICAS_EXPORTADAS", f"Temp y Hum guardadas en {self.output_dir}")
        return temp_path, hum_path

    def _plot_premium_metric(
        self,
        x: List[datetime],
        y: List[float],
        title: str,
        ylabel: str,
        color: str,
        gradient_colors: Tuple[str, str],
        ideal_value: float,
        ideal_label: str,
        output_path: Path
    ) -> None:
        """Renderiza una gráfica individual con diseño profesional de publicación."""
        fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)

        y_arr = np.array(y)

        # Línea principal con trazo grueso y suave
        ax.plot(x, y, color=color, linewidth=2.0, antialiased=True,
                label=ylabel, zorder=5)

        # Relleno de área bajo la curva con gradiente
        ax.fill_between(x, y, color=gradient_colors[0], alpha=0.5, zorder=2)

        # Línea de referencia ideal (dashed)
        ax.axhline(y=ideal_value, color='#f59e0b', linewidth=1.2,
                   linestyle='--', alpha=0.8, label=ideal_label, zorder=3)

        # Línea de promedio
        avg_val = float(np.mean(y_arr))
        ax.axhline(y=avg_val, color='#8b5cf6', linewidth=1.0,
                   linestyle=':', alpha=0.7,
                   label=f'Promedio: {avg_val:.1f}', zorder=3)

        # Marcar mínimo y máximo
        min_idx = int(np.argmin(y_arr))
        max_idx = int(np.argmax(y_arr))

        ax.scatter([x[min_idx]], [y[min_idx]], color='#3b82f6', s=50,
                   zorder=6, edgecolors='white', linewidths=1.5)
        ax.annotate(f'Mín: {y[min_idx]:.1f}', (x[min_idx], y[min_idx]),
                    textcoords="offset points", xytext=(8, -18),
                    fontsize=8, color='#3b82f6', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor='#3b82f6', alpha=0.9))

        ax.scatter([x[max_idx]], [y[max_idx]], color='#ef4444', s=50,
                   zorder=6, edgecolors='white', linewidths=1.5)
        ax.annotate(f'Máx: {y[max_idx]:.1f}', (x[max_idx], y[max_idx]),
                    textcoords="offset points", xytext=(8, 10),
                    fontsize=8, color='#ef4444', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor='#ef4444', alpha=0.9))

        # Título y etiquetas
        ax.set_title(title, fontsize=13, fontweight='bold', pad=14,
                     color='#0f172a')
        ax.set_ylabel(ylabel, fontsize=10, fontweight='semibold',
                      color='#334155')
        ax.set_xlabel("Hora de Registro", fontsize=10, fontweight='semibold',
                      color='#334155')

        # Formatear eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()

        # Grid profesional
        ax.grid(True, linestyle='--', alpha=0.4, color='#cbd5e1')
        ax.set_axisbelow(True)

        # Bordes limpios (solo izq + abajo)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#94a3af')
        ax.spines['bottom'].set_color('#94a3af')
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)

        # Leyenda profesional
        legend = ax.legend(
            loc='upper right', fontsize=8, framealpha=0.95,
            edgecolor='#cbd5e1', fancybox=True, shadow=False,
            borderpad=0.8
        )
        legend.get_frame().set_linewidth(0.5)

        # Cuadro estadístico en esquina inferior derecha
        stats_text = (
            f"n = {len(y)} muestras\n"
            f"μ = {avg_val:.1f}\n"
            f"σ = {float(np.std(y_arr)):.2f}\n"
            f"Rango: [{float(np.min(y_arr)):.1f}, {float(np.max(y_arr)):.1f}]"
        )
        props = dict(boxstyle='round,pad=0.5', facecolor='#f8fafc',
                     edgecolor='#cbd5e1', alpha=0.95)
        ax.text(0.02, 0.02, stats_text, transform=ax.transAxes,
                fontsize=7.5, verticalalignment='bottom',
                fontfamily='monospace', color='#475569', bbox=props)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='white',
                    bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)
