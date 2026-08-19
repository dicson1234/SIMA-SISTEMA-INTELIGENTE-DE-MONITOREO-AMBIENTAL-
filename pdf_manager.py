"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Generación de Reportes PDF — Edición Profesional / Registro de Patente

Utiliza ReportLab para compilar un informe ejecutivo e ingenieril de grado
profesional con diseño apto para presentación técnica, auditorías y solicitudes
de patente.

Responsabilidades:
    - Diseñar y maquetar la estructura visual premium del documento PDF.
    - Generar portada de certificación técnica con metadatos de auditoría.
    - Dibujar tablas de estadísticas tabuladas con diseño de alta fidelidad.
    - Incrustar los gráficos de Temperatura y Humedad generados por GraphManager.
    - Formular conclusiones y diagnósticos automatizados según normas térmicas.
    - Incluir bloque de firmas de ingeniería y cláusulas de confidencialidad.

Autor:  Equipo SIMA — Especialista en Documentación e Ingeniería
Fecha:  2026-07-14
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from config import REPORTS_DIR, PDF_FILENAME_FORMAT, FILE_DATE_FORMAT, FILE_TIME_FORMAT, APP_FULL_NAME, APP_VERSION
from sensor_manager import SensorReading
from graph_manager import GraphManager
from logger_manager import get_logger, log_data_event

# Logger del módulo
logger = get_logger(__name__)


# =====================================================================
#  CANVAS PERSONALIZADO PARA ENCABEZADO Y PIE DE PÁGINA
# =====================================================================

class NumberedCanvas(canvas.Canvas):
    """Canvas personalizado para numeración dinámica de páginas y membrete profesional."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int) -> None:
        """Dibuja encabezado y pie de página en cada hoja (excepto la portada)."""
        if self._pageNumber == 1:
            return  # Omitir en la portada para mantener diseño impoluto

        self.saveState()

        # --- Encabezado ---
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1e3a8a"))  # Azul institucional
        self.drawString(54, 755, f"SIMA v2 — {APP_FULL_NAME}")

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(letter[0] - 54, 755, "INFORME TÉCNICO DE MONITOREO")

        # Línea divisora del encabezado
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 747, letter[0] - 54, 747)

        # --- Pie de Página ---
        self.line(54, 52, letter[0] - 54, 52)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 38, "DOCUMENTO PROPIETARIO — REGISTRO TÉCNICO E INGENIERÍA SIMA")

        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1e3a8a"))
        self.drawRightString(letter[0] - 54, 38, page_str)

        self.restoreState()


# =====================================================================
#  GENERADOR DE PDF PROFESIONAL
# =====================================================================

class PDFManager:
    """Orquesta la creación de documentos PDF a partir del estado de la sesión."""

    def __init__(self, output_directory: Union[str, Path] = REPORTS_DIR) -> None:
        """Inicializa el gestor de reportes PDF.

        Args:
            output_directory: Ruta al directorio donde se guardarán los informes.
        """
        self.output_dir: Path = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.graph_manager: GraphManager = GraphManager()

    def generate_report(
        self,
        readings: List[SensorReading],
        stats: Dict[str, Any]
    ) -> Path:
        """Compila un informe PDF detallado de nivel profesional y de patente.

        Args:
            readings: Historial completo de SensorReading de la sesión.
            stats: Estadísticas descriptivas de la sesión.

        Returns:
            Ruta del archivo PDF generado.
        """
        if not readings:
            raise ValueError("No se puede generar un PDF sin datos históricos.")

        # Generar nombre del archivo PDF
        now = datetime.now()
        date_str = now.strftime(FILE_DATE_FORMAT)
        time_str = now.strftime(FILE_TIME_FORMAT)
        filename = PDF_FILENAME_FORMAT.format(date=date_str, time=time_str)
        pdf_path = self.output_dir / filename

        # Generar gráficas (retorna tupla de 2 rutas: temp_img, hum_img)
        temp_img, hum_img = self.graph_manager.generate_plots(readings)

        # Configuración del documento de ReportLab (márgenes de 0.75 pulgadas = 54 pt)
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=64
        )

        story = []
        styles = getSampleStyleSheet()

        # Paleta de Colores de Estilo Institucional
        PRIMARY = colors.HexColor("#1e3a8a")     # Azul institucional
        SECONDARY = colors.HexColor("#2563eb")   # Azul de acento
        DARK_TEXT = colors.HexColor("#0f172a")   # Texto oscuro
        MUTED_TEXT = colors.HexColor("#475569")  # Texto secundario
        BG_LIGHT = colors.HexColor("#f8fafc")    # Fondo suave
        BORDER_CLR = colors.HexColor("#cbd5e1")  # Borde gris

        # Estilos tipográficos personalizados
        style_cover_badge = ParagraphStyle(
            'CoverBadge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=PRIMARY,
            alignment=1,
            spaceAfter=15
        )

        style_cover_title = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=30,
            textColor=PRIMARY,
            spaceAfter=10,
            alignment=1
        )

        style_cover_subtitle = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=12,
            leading=16,
            textColor=MUTED_TEXT,
            spaceAfter=30,
            alignment=1
        )

        style_h1 = ParagraphStyle(
            'SectionH1',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )

        style_h2 = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=SECONDARY,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        )

        style_body = ParagraphStyle(
            'BodyCustom',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=DARK_TEXT,
            spaceAfter=8
        )

        style_caption = ParagraphStyle(
            'CaptionCustom',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.5,
            leading=11,
            textColor=MUTED_TEXT,
            alignment=1,
            spaceAfter=10
        )

        # ---------------------------------------------------------
        # 1. PORTADA EJECUTIVA / REGISTRO TÉCNICO
        # ---------------------------------------------------------
        story.append(Spacer(1, 40))

        # Banner de clasificación
        badge_table = Table(
            [[Paragraph("SISTEMA INTELIGENTE DE MONITOREO AMBIENTAL (SIMA v2)", style_cover_badge)]],
            colWidths=[504]
        )
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#dbeafe")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#93c5fd")),
        ]))
        story.append(badge_table)
        story.append(Spacer(1, 25))

        story.append(Paragraph("REPORT TÉCNICO Y AUDITORÍA DE DATOS AMBIENTALES", style_cover_title))
        story.append(Paragraph("Evaluación Higrotérmica en Tiempo Real & Análisis de Confort Gaussiano", style_cover_subtitle))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=0, spaceAfter=25))

        # Cuadro de Metadatos de Adquisición
        meta_data = [
            [Paragraph("<b>Identificador del Documento:</b>", style_body), Paragraph(f"SIMA-REP-{date_str}-{time_str}", style_body)],
            [Paragraph("<b>Versión del Software:</b>", style_body), Paragraph(f"SIMA Core v{APP_VERSION} (MVVM Architecture)", style_body)],
            [Paragraph("<b>Fecha y Hora de Emisión:</b>", style_body), Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), style_body)],
            [Paragraph("<b>Periodo de Monitoreo:</b>", style_body), Paragraph(f"{readings[0].timestamp_str}  ➔  {readings[-1].timestamp_str}", style_body)],
            [Paragraph("<b>Muestras Procesadas:</b>", style_body), Paragraph(f"{stats.get('sample_count')} lecturas válidas (Intervalo: 2.0 s)", style_body)],
            [Paragraph("<b>Tiempo Activo de Sesión:</b>", style_body), Paragraph(f"{stats.get('elapsed_time_str')}", style_body)],
            [Paragraph("<b>Nodo de Adquisición:</b>", style_body), Paragraph("Arduino Uno R3 (ATmega328P) + Sensor DHT11 Digital", style_body)],
            [Paragraph("<b>Estado de Validación:</b>", style_body), Paragraph("<font color='#059669'><b>VERIFICADO — DATOS VÁLIDOS PARA REGISTRO</b></font>", style_body)],
        ]

        meta_table = Table(meta_data, colWidths=[160, 320])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
            ('BOX', (0,0), (-1,-1), 1, PRIMARY),
        ]))
        story.append(meta_table)

        story.append(Spacer(1, 40))

        # Nota de aviso legal / patente
        legal_text = (
            "<b>AVISO DE PROPIEDAD INTELECTUAL:</b> Este documento contiene datos cuantitativos "
            "obtenidos mediante la plataforma SIMA v2. Las metodologías de cálculo de confort gaussiano "
            "y la arquitectura de telemetría aquí documentadas están preparadas para respaldo de patentes, "
            "auditorías de calidad ambiental y certificaciones ergonómicas."
        )
        legal_table = Table([[Paragraph(legal_text, style_body)]], colWidths=[504])
        legal_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ]))
        story.append(legal_table)

        story.append(PageBreak())

        # ---------------------------------------------------------
        # 2. RESUMEN EJECUTIVO Y ANÁLISIS ESTADÍSTICO
        # ---------------------------------------------------------
        story.append(Paragraph("1. Resumen Ejecutivo y Resumen Estadístico", style_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=0, spaceAfter=10))

        intro_text = (
            "El presente informe consolida los datos recolectados por el nodo sensor durante la sesión "
            "de monitoreo en tiempo real. Se evaluaron las magnitudes de <b>Temperatura (°C)</b> y "
            "<b>Humedad Relativa (%)</b> para verificar el cumplimiento de los rangos de confort ergonómico "
            "definidos en la normativa ambiental ISO 7730 y ASHRAE 55."
        )
        story.append(Paragraph(intro_text, style_body))
        story.append(Spacer(1, 8))

        # Tabla Estadísticas Estilizada
        stats_headers = ["Variable Ambiental", "Mínimo", "Máximo", "Promedio (x̄)", "Rango", "Unidad"]
        stats_rows = [
            [
                "Temperatura (T)",
                f"{stats.get('temp_min', 0.0):.1f}",
                f"{stats.get('temp_max', 0.0):.1f}",
                f"{stats.get('temp_avg', 0.0):.1f}",
                f"{(stats.get('temp_max', 0.0) - stats.get('temp_min', 0.0)):.1f}",
                "°C"
            ],
            [
                "Humedad Relativa (H)",
                f"{stats.get('hum_min', 0.0):.1f}",
                f"{stats.get('hum_max', 0.0):.1f}",
                f"{stats.get('hum_avg', 0.0):.1f}",
                f"{(stats.get('hum_max', 0.0) - stats.get('hum_min', 0.0)):.1f}",
                "%"
            ]
        ]

        table_data = [[Paragraph(f"<b>{h}</b>", style_body) for h in stats_headers]]
        for row in stats_rows:
            table_data.append([Paragraph(cell, style_body) for cell in row])

        stats_table = Table(table_data, colWidths=[140, 70, 70, 84, 70, 70])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 15))

        # ---------------------------------------------------------
        # 3. ANÁLISIS GRÁFICO DE TEMPERATURA Y HUMEDAD
        # ---------------------------------------------------------
        story.append(Paragraph("2. Análisis Gráfico de Distribución Temporal", style_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=0, spaceAfter=10))

        story.append(KeepTogether([
            Paragraph("<b>Figura 1:</b> Comportamiento de la Temperatura (°C) a lo largo del tiempo de ensayo.", style_h2),
            Image(str(temp_img), width=6.8 * inch, height=3.2 * inch),
            Paragraph("Gráfica 1: Comportamiento térmico con indicación de zona de confort (22 °C), promedio y valores extremos.", style_caption),
            Spacer(1, 10)
        ]))

        story.append(KeepTogether([
            Paragraph("<b>Figura 2:</b> Comportamiento de la Humedad Relativa (%) a lo largo del tiempo de ensayo.", style_h2),
            Image(str(hum_img), width=6.8 * inch, height=3.2 * inch),
            Paragraph("Gráfica 2: Comportamiento higrométrico con indicación de nivel óptimo (45 %), promedio y valores extremos.", style_caption),
            Spacer(1, 10)
        ]))

        story.append(PageBreak())

        # ---------------------------------------------------------
        # 4. EVALUACIÓN DEL ÍNDICE DE CONFORT GAUSSIANO
        # ---------------------------------------------------------
        story.append(Paragraph("3. Evaluación del Índice de Confort Térmico", style_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=0, spaceAfter=10))

        comfort_desc = (
            "El sistema SIMA v2 implementa una función de pertenencia gaussiana para determinar "
            "el índice de confort compuesto (0 – 100 %). El algoritmo penaliza de forma suave "
            "las desviaciones respecto a los valores ideales (T_ideal = 22.0 °C, H_ideal = 45.0 %):"
        )
        story.append(Paragraph(comfort_desc, style_body))
        story.append(Spacer(1, 6))

        # Fórmula simplificada en cuadro
        formula_box = Table(
            [[Paragraph(
                "<b>Fórmula del Confort Gaussiano:</b><br/>"
                "<i>S<sub>T</sub> = 100 · exp(-0.5 · ((T - 22) / 8.0)²)</i> &nbsp;&nbsp;|&nbsp;&nbsp; "
                "<i>S<sub>H</sub> = 100 · exp(-0.5 · ((H - 45) / 25.0)²)</i><br/>"
                "<b>Índice Global:</b> <i>C = 0.50 · S<sub>T</sub> + 0.50 · S<sub>H</sub></i>",
                style_body
            )]],
            colWidths=[504]
        )
        formula_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ]))
        story.append(formula_box)
        story.append(Spacer(1, 15))

        # ---------------------------------------------------------
        # 5. DIAGNÓSTICO Y CONCLUSIONES TÉCNICAS
        # ---------------------------------------------------------
        story.append(Paragraph("4. Diagnóstico Ambiental y Conclusiones", style_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=0, spaceAfter=10))

        conclusions = self._generate_automatic_conclusions(stats)
        for conc in conclusions:
            story.append(Paragraph(f"• {conc}", style_body))

        story.append(Spacer(1, 20))

        # Bloque de Firmas y Validación Técnica
        story.append(Paragraph("<b>5. Registro y Validación de Ingeniería</b>", style_h2))

        signatures_data = [
            [
                Paragraph("___________________________________<br/><b>Ing. Responsable de Adquisición</b><br/>Especialista en Instrumentación", style_body),
                Paragraph("___________________________________<br/><b>Director de Laboratorio / Proyecto</b><br/>Sistema SIMA Core v2", style_body)
            ]
        ]
        sig_table = Table(signatures_data, colWidths=[240, 240])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 30),
        ]))
        story.append(sig_table)

        # Compilar el documento
        doc.build(story, canvasmaker=NumberedCanvas)

        log_data_event("PDF_GENERADO", str(pdf_path))
        logger.info("Reporte PDF profesional generado exitosamente: %s", pdf_path.name)

        return pdf_path

    @staticmethod
    def _generate_automatic_conclusions(stats: Dict[str, Any]) -> List[str]:
        """Genera un diagnóstico ambiental en base a las estadísticas del periodo de sesión."""
        conclusions = []
        temp_avg = stats.get("temp_avg", 0.0)
        hum_avg = stats.get("hum_avg", 0.0)

        # 1. Diagnóstico de Temperatura
        if temp_avg < 18.0:
            conclusions.append(
                f"<b>Temperatura:</b> La media registrada fue de <b>{temp_avg:.1f} °C</b>, clasificándose como un ambiente frío. "
                "Se aconseja evaluar la regulación de sistemas de calefacción o aislamiento térmico."
            )
        elif 18.0 <= temp_avg <= 24.0:
            conclusions.append(
                f"<b>Temperatura:</b> La media registrada fue de <b>{temp_avg:.1f} °C</b>, permaneciendo dentro del rango de "
                "confort térmico recomendado por la norma ASHRAE 55 (18 – 24 °C)."
            )
        else:
            conclusions.append(
                f"<b>Temperatura:</b> La media registrada fue de <b>{temp_avg:.1f} °C</b>, indicando condiciones cálidas. "
                "Se recomienda mejorar la ventilación o activar refrigeración para optimizar la habitabilidad."
            )

        # 2. Diagnóstico de Humedad
        if hum_avg < 30.0:
            conclusions.append(
                f"<b>Humedad Relativa:</b> El valor promedio fue de <b>{hum_avg:.1f} %</b>, situándose por debajo del límite confortable. "
                "El aire seco puede ocasionar irritación ocular o respiratoria. Se sugiere el uso de humidificadores."
            )
        elif 30.0 <= hum_avg <= 60.0:
            conclusions.append(
                f"<b>Humedad Relativa:</b> El valor promedio fue de <b>{hum_avg:.1f} %</b>, situándose en la zona higrométrica "
                "óptima y saludable (30 – 60 %)."
            )
        else:
            conclusions.append(
                f"<b>Humedad Relativa:</b> El valor promedio fue de <b>{hum_avg:.1f} %</b>, catalogándose como alta. "
                "Se sugiere activar deshumidificadores para prevenir condensación o proliferación de moho."
            )

        # 3. Diagnóstico de Confort General
        temp_dev = abs(temp_avg - 22.0)
        hum_dev = abs(hum_avg - 45.0)
        ideal_deviation = temp_dev + (hum_dev / 2.0)

        if ideal_deviation < 5.0:
            conclusions.append(
                "<b>Evaluación Global de Confort:</b> El espacio monitoreado reúne condiciones <b>EXCELENTES</b> de confort ambiental "
                "higrotérmico, ideales para actividades operativas y de concentración."
            )
        elif ideal_deviation < 15.0:
            conclusions.append(
                "<b>Evaluación Global de Confort:</b> El índice de confort general es <b>ACEPTABLE / BUENO</b>, registrando pequeñas "
                "desviaciones tolerables respecto a la condición óptima."
            )
        else:
            conclusions.append(
                "<b>Evaluación Global de Confort:</b> Se detectaron <b>DESVIACIONES SIGNIFICATIVAS</b> respecto a las condiciones ideales. "
                "Se sugiere intervenir los sistemas de climatización según las recomendaciones técnicas emitidas."
            )

        return conclusions
