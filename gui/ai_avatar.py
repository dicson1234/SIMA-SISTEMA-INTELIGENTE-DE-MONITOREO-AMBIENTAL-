"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo del Avatar IA Expresivo con Ojos Digitales Pixeleados (gui/ai_avatar.py)

Widget interactivo de matriz de píxeles (Pixel Art Renderer) que dibuja la cara
y ojos del Asistente IA de SIMA en tiempo real. Soporta 10+ expresiones vivas:
NORMAL, HAPPY, WINK, THINKING, TALKING, SURPRISED, SLEEPY, WARN, ALERT, CONFUSED, LOVE.

Autor:  Equipo SIMA — Diseñador UX/UI & Especialista IA
Fecha:  2026-08-09
"""

import math
import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer, Slot, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient


class AIFaceWidget(QWidget):
    """Widget de la cara del Robot IA renderizado en Estilo Pixel-Art Cibernético Expresivo."""

    # Estados de Expresión
    STATE_NORMAL = "NORMAL"         # 🩵 Ojos píxel cian pastel, parpadeo alegre
    STATE_HAPPY = "HAPPY"           # 💚 Ojos en arco feliz ^ ^ + rubor rosado
    STATE_WINK = "WINK"             # 😉 Ojo guiñado píxel
    STATE_THINKING = "THINKING"     # 💜 Matriz giratoria en pensamiento
    STATE_TALKING = "TALKING"       # 💙 Ojos y boca modulados por voz
    STATE_SURPRISED = "SURPRISED"   # 😲 Ojos grandes O O
    STATE_SLEEPY = "SLEEPY"         # 😴 Ojos semicerrados - -
    STATE_WARN = "WARN"             # 🧡 Ojos píxel ámbar
    STATE_ALERT = "ALERT"           # 🔴 Ojos alerta rojo carmesí
    STATE_CONFUSED = "CONFUSED"     # 😵‍💫 Ojos asimétricos o.O
    STATE_LOVE = "LOVE"             # 💖 Ojos en forma de corazón píxel
    STATE_HOT = "HOT"               # 🔥 Ojos con sudor ambiental (>28°C)
    STATE_COLD = "COLD"             # ❄️ Ojos congelados/frescos (<15°C)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 240)
        self.setMaximumHeight(280)

        # Estado inicial
        self.current_state = self.STATE_NORMAL
        self.blink_progress = 0.0     # 0.0 = abierto, 1.0 = cerrado
        self.is_blinking = False
        self.pulse_phase = 0.0
        self.talk_phase = 0.0
        self.idle_look_x = 0.0
        self.idle_look_y = 0.0

        # Timer de animación continua (FPS constante)
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(35)  # ~30 FPS
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start()

        # Timer de parpadeo espontáneo
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(3200)
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start()

        # Timer de mirada aleatoria (para darle vida)
        self.look_timer = QTimer(self)
        self.look_timer.setInterval(4000)
        self.look_timer.timeout.connect(self._trigger_random_look)
        self.look_timer.start()

    def set_expression(self, state: str) -> None:
        """Establece la expresión del avatar entre las 12+ expresiones disponibles."""
        valid_states = [
            self.STATE_NORMAL, self.STATE_HAPPY, self.STATE_WINK,
            self.STATE_THINKING, self.STATE_TALKING, self.STATE_SURPRISED,
            self.STATE_SLEEPY, self.STATE_WARN, self.STATE_ALERT,
            self.STATE_CONFUSED, self.STATE_LOVE, self.STATE_HOT, self.STATE_COLD
        ]
        if state in valid_states:
            self.current_state = state
            self.update()


    def _trigger_blink(self) -> None:
        """Dispara un parpadeo de ojos aleatorio si no está pensando o guiñando."""
        if not self.is_blinking and self.current_state not in [self.STATE_THINKING, self.STATE_WINK, self.STATE_SLEEPY]:
            self.is_blinking = True
            self.blink_progress = 0.0
            self.blink_timer.setInterval(random.randint(2500, 5000))

    def _trigger_random_look(self) -> None:
        """Cambia sutilmente la dirección de la mirada para darle dinamismo."""
        if self.current_state == self.STATE_NORMAL:
            self.idle_look_x = random.choice([-2.0, 0.0, 0.0, 2.0])
            self.idle_look_y = random.choice([-1.0, 0.0, 1.0])
        else:
            self.idle_look_x = 0.0
            self.idle_look_y = 0.0

    def _update_animation(self) -> None:
        self.pulse_phase += 0.1
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase -= 2 * math.pi

        if self.current_state == self.STATE_TALKING:
            self.talk_phase += 0.25
            if self.talk_phase > 2 * math.pi:
                self.talk_phase -= 2 * math.pi

        if self.is_blinking:
            self.blink_progress += 0.18
            if self.blink_progress >= 2.0:
                self.blink_progress = 0.0
                self.is_blinking = False

        self.update()

    def paintEvent(self, event) -> None:
        """Renderiza la cara del robot con estilo Pixel Matrix sobre pantalla OLED."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)  # Fiel al Pixel Art

        w = self.width()
        h = self.height()

        # 1. Dibujar Pantalla / Visor del Robot (Chasis Glassmorphic Oscuro)
        margin = 12
        visor_rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)

        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0.0, QColor("#070b14"))
        bg_grad.setColorAt(1.0, QColor("#0f172a"))
        painter.setBrush(QBrush(bg_grad))

        border_col = self._get_primary_color()
        pen = QPen(border_col, 2)
        painter.setPen(pen)
        painter.drawRoundedRect(visor_rect, 18, 18)

        # 2. Configurar Grilla de Píxeles (Pixel Matrix)
        # Cada ojo es una grilla de 10x10 píxeles
        pixel_size = 7.0
        gap = 1.5
        eye_grid_cols = 10
        eye_grid_rows = 10

        grid_w = eye_grid_cols * (pixel_size + gap)
        grid_h = eye_grid_rows * (pixel_size + gap)

        center_x = w / 2.0
        center_y = h / 2.0 - 10.0
        eye_spacing = grid_w + 30.0

        left_origin = QPointF(center_x - eye_spacing / 2.0 - grid_w / 2.0 + self.idle_look_x * pixel_size,
                              center_y - grid_h / 2.0 + self.idle_look_y * pixel_size)
        right_origin = QPointF(center_x + eye_spacing / 2.0 - grid_w / 2.0 + self.idle_look_x * pixel_size,
                               center_y - grid_h / 2.0 + self.idle_look_y * pixel_size)

        # Matriz de píxeles para el ojo según la expresión
        left_matrix, right_matrix = self._get_pixel_matrices()

        # Si hay parpadeo, aplanar la matriz horizontalmente
        if self.is_blinking:
            left_matrix = self._apply_blink_matrix(left_matrix)
            right_matrix = self._apply_blink_matrix(right_matrix)

        # Renderizar Matriz Píxel del Ojo Izquierdo
        self._draw_pixel_matrix(painter, left_origin, left_matrix, pixel_size, gap)

        # Renderizar Matriz Píxel del Ojo Derecho
        self._draw_pixel_matrix(painter, right_origin, right_matrix, pixel_size, gap)

        # 3. Dibujar Rubor Rosado Píxel si está FELIZ o LOVE
        if self.current_state in [self.STATE_HAPPY, self.STATE_LOVE]:
            self._draw_pixel_blush(painter, left_origin, right_origin, grid_w, grid_h, pixel_size, gap)

        # 4. Dibujar Boca Píxel / Indicador de Voz
        self._draw_pixel_mouth(painter, center_x, center_y + grid_h / 2.0 + 20.0, pixel_size, gap)

    def _get_primary_color(self) -> QColor:
        """Devuelve el color pastel primario según el estado emocional."""
        if self.current_state == self.STATE_HAPPY:
            return QColor("#6ee7b7")     # Verde Menta Pastel
        elif self.current_state == self.STATE_THINKING:
            return QColor("#c084fc")   # Lavanda Pastel
        elif self.current_state == self.STATE_TALKING:
            return QColor("#7dd3fc")    # Cian Pastel
        elif self.current_state == self.STATE_WARN:
            return QColor("#fcd34d")     # Ámbar Pastel
        elif self.current_state == self.STATE_ALERT:
            return QColor("#f87171")    # Rojo Carmesí Pastel
        elif self.current_state == self.STATE_LOVE:
            return QColor("#f472b6")     # Rosa Pastel
        elif self.current_state == self.STATE_SLEEPY:
            return QColor("#818cf8")   # Índigo Pastel
        elif self.current_state == self.STATE_SURPRISED:
            return QColor("#38bdf8")   # Azul Pastel
        elif self.current_state == self.STATE_WINK:
            return QColor("#34d399")    # Verde Pastel
        elif self.current_state == self.STATE_HOT:
            return QColor("#fb923c")    # Naranja Ámbar Cálido
        elif self.current_state == self.STATE_COLD:
            return QColor("#38bdf8")    # Azul Hielo Frío
        return QColor("#7dd3fc")        # Cian Pastel por Defecto


    def _draw_pixel_matrix(
        self, painter: QPainter, origin: QPointF, matrix: list, pixel_size: float, gap: float
    ) -> None:
        """Dibuja una cuadrícula de píxeles digitales basados en una matriz 10x10."""
        color = self._get_primary_color()
        bg_pixel_color = QColor(color.red(), color.green(), color.blue(), 25)

        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0

        for r in range(rows):
            for c in range(cols):
                val = matrix[r][c]
                px = origin.x() + c * (pixel_size + gap)
                py = origin.y() + r * (pixel_size + gap)
                rect = QRectF(px, py, pixel_size, pixel_size)

                if val == 1:
                    # Píxel encendido con brillo
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(rect, 1.5, 1.5)
                elif val == 2:
                    # Píxel de brillo blanco
                    painter.setBrush(QBrush(QColor("#ffffff")))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(rect, 1.5, 1.5)
                else:
                    # Píxel apogado tenue (Da efecto de pantalla retro real)
                    painter.setBrush(QBrush(bg_pixel_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(rect, 1.0, 1.0)

    def _apply_blink_matrix(self, matrix: list) -> list:
        """Convierte cualquier matriz en una línea horizontal durante el parpadeo."""
        val = math.sin(self.blink_progress * math.pi / 2.0)
        if self.blink_progress > 1.0:
            val = math.sin((2.0 - self.blink_progress) * math.pi / 2.0)

        if val > 0.4:
            # Reemplazar con una sola línea horizontal de píxeles en la fila 5
            new_matrix = [[0]*10 for _ in range(10)]
            for c in range(2, 8):
                new_matrix[5][c] = 1
            return new_matrix
        return matrix

    def _get_pixel_matrices(self) -> tuple:
        """Devuelve las matrices 10x10 del ojo izquierdo y derecho según el estado."""
        # 1. NORMAL: Ojo rectangular redondeado con punto de luz blanco
        m_normal_left = [
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,2,2,1,1,1,1,1,0],
            [1,2,2,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,0,0],
        ]
        m_normal_right = [
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,2,2,1,1,1,1,1,0],
            [1,2,2,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,0,0],
        ]

        if self.current_state == self.STATE_HAPPY:
            # HAPPY: Arco feliz ^ ^
            m_happy = [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,1,1,0,0,0,0,1,1,0],
                [1,1,0,0,0,0,0,0,1,1],
                [1,0,0,0,0,0,0,0,0,1],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ]
            return m_happy, m_happy

        elif self.current_state == self.STATE_WINK:
            # WINK: Ojo izquierdo guiñado, derecho normal
            m_wink = [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,1,1,1,1,1,1,1,1,0],
                [1,1,1,1,1,1,1,1,1,1],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ]
            return m_wink, m_normal_right

        elif self.current_state == self.STATE_THINKING:
            # THINKING: Matriz en animación giratoria
            frame = int(self.pulse_phase * 2) % 4
            m_think = [[0]*10 for _ in range(10)]
            if frame == 0:
                for c in range(2, 8): m_think[2][c] = 1
            elif frame == 1:
                for r in range(2, 8): m_think[r][7] = 1
            elif frame == 2:
                for c in range(2, 8): m_think[7][c] = 1
            else:
                for r in range(2, 8): m_think[r][2] = 1
            return m_think, m_think

        elif self.current_state == self.STATE_SURPRISED:
            # SURPRISED: Anillo grande O O
            m_surprised = [
                [0,0,1,1,1,1,1,1,0,0],
                [0,1,1,1,1,1,1,1,1,0],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [0,1,1,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,1,1,0,0],
            ]
            return m_surprised, m_surprised

        elif self.current_state == self.STATE_SLEEPY:
            # SLEEPY: Ojos semicerrados flat - -
            m_sleepy = [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,1,1,1,1,1,1,1,1,0],
                [1,1,1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1,1,1],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ]
            return m_sleepy, m_sleepy

        elif self.current_state == self.STATE_LOVE:
            # LOVE: Forma de corazón píxel
            m_heart = [
                [0,0,0,0,0,0,0,0,0,0],
                [0,1,1,0,0,0,0,1,1,0],
                [1,1,1,1,0,0,1,1,1,1],
                [1,1,1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1,1,1],
                [0,1,1,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,0,0,1,1,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ]
            return m_heart, m_heart

        elif self.current_state == self.STATE_CONFUSED:
            # CONFUSED: Ojo izquierdo pequeño, ojo derecho grande
            m_small = [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ]
            return m_small, m_normal_right

        elif self.current_state == self.STATE_WARN:
            # WARN: Ojos con signo de admiración
            m_warn = [
                [0,0,1,1,1,1,1,1,0,0],
                [0,1,1,1,1,1,1,1,1,0],
                [1,1,0,0,1,1,0,0,1,1],
                [1,1,0,0,1,1,0,0,1,1],
                [1,1,0,0,1,1,0,0,1,1],
                [1,1,0,0,1,1,0,0,1,1],
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,0,0,1,1,0,0,1,1],
                [0,1,1,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,1,1,0,0],
            ]
            return m_warn, m_warn

        elif self.current_state == self.STATE_ALERT:
            # ALERT: Cruz de alerta roja
            m_alert = [
                [1,1,0,0,0,0,0,0,1,1],
                [1,1,1,0,0,0,0,1,1,1],
                [0,1,1,1,0,0,1,1,1,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,0,1,1,1,1,0,0,0],
                [0,0,1,1,1,1,1,1,0,0],
                [0,1,1,1,0,0,1,1,1,0],
                [1,1,1,0,0,0,0,1,1,1],
                [1,1,0,0,0,0,0,0,1,1],
            ]
            return m_alert, m_alert

        return m_normal_left, m_normal_right

    def _draw_pixel_blush(
        self, painter: QPainter, left: QPointF, right: QPointF, grid_w: float, grid_h: float, pixel_size: float, gap: float
    ) -> None:
        """Dibuja mejillas de rubor rosado en estilo píxel debajo de los ojos."""
        blush_color = QColor("#f472b6")  # Rosa Pastel
        painter.setBrush(QBrush(blush_color))
        painter.setPen(Qt.NoPen)

        # 3 píxeles rosados debajo de cada ojo
        for orig in [left, right]:
            py = orig.y() + grid_h + gap * 2
            for c in range(3, 7):
                px = orig.x() + c * (pixel_size + gap)
                rect = QRectF(px, py, pixel_size, pixel_size)
                painter.drawRoundedRect(rect, 1.0, 1.0)

    def _draw_pixel_mouth(self, painter: QPainter, cx: float, cy: float, pixel_size: float, gap: float) -> None:
        """Dibuja la boca en píxeles digitales o ecualizador si habla."""
        color = self._get_primary_color()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)

        if self.current_state == self.STATE_TALKING:
            # Animación de 4 barras de ecualizador de voz
            bar_count = 5
            total_w = bar_count * (pixel_size * 2 + gap)
            start_x = cx - total_w / 2.0

            for i in range(bar_count):
                h_pixels = int(2 + math.sin(self.talk_phase * 3 + i) * 2)
                h_pixels = max(1, min(4, h_pixels))
                x = start_x + i * (pixel_size * 2 + gap)
                for r in range(h_pixels):
                    rect = QRectF(x, cy - r * (pixel_size + gap), pixel_size * 1.8, pixel_size)
                    painter.drawRoundedRect(rect, 1.0, 1.0)
        else:
            # Sonrisa curva de 6 píxeles
            smile_offsets = [(-3, 0), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 0)]
            for ox, oy in smile_offsets:
                px = cx + ox * (pixel_size + gap)
                py = cy + oy * (pixel_size + gap)
                rect = QRectF(px, py, pixel_size, pixel_size)
                painter.drawRoundedRect(rect, 1.0, 1.0)


class AIFaceContainer(QFrame):
    """Contenedor elegante que engloba la cara del robot con su etiqueta de estado pastel."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.avatar_face = AIFaceWidget(self)

        self.lbl_status = QLabel("🩵 SIMA AI — Estado: En línea")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #7dd3fc; background-color: #070b14; border-radius: 8px; padding: 6px;")

        layout.addWidget(self.avatar_face)
        layout.addWidget(self.lbl_status)

    def set_state(self, state: str, status_msg: str = "") -> None:
        """Actualiza la cara y la etiqueta de estado con colores pastel."""
        self.avatar_face.set_expression(state)
        if not status_msg:
            if state == AIFaceWidget.STATE_NORMAL:
                status_msg = "🩵 SIMA AI — Estado: En línea"
            elif state == AIFaceWidget.STATE_HAPPY:
                status_msg = "💚 SIMA AI — Estado: Contento & Confortable"
            elif state == AIFaceWidget.STATE_WINK:
                status_msg = "😉 SIMA AI — Estado: Saludo Amigable"
            elif state == AIFaceWidget.STATE_THINKING:
                status_msg = "💜 SIMA AI — Estado: Procesando Solicitud..."
            elif state == AIFaceWidget.STATE_TALKING:
                status_msg = "💙 SIMA AI — Estado: Respondiendo..."
            elif state == AIFaceWidget.STATE_WARN:
                status_msg = "🧡 SIMA AI — Estado: Advertencia Ambiental"
            elif state == AIFaceWidget.STATE_ALERT:
                status_msg = "🔴 SIMA AI — Estado: Riesgo Detectado"
            elif state == AIFaceWidget.STATE_LOVE:
                status_msg = "💖 SIMA AI — Estado: Agradecido"
            elif state == AIFaceWidget.STATE_HOT:
                status_msg = "🔥 SIMA AI — Estado: Temperatura Alta (>28°C)"
            elif state == AIFaceWidget.STATE_COLD:
                status_msg = "❄️ SIMA AI — Estado: Clima Fresco/Frío (<15°C)"

        style_color = "#7dd3fc"
        if state in [AIFaceWidget.STATE_HAPPY, AIFaceWidget.STATE_WINK]:
            style_color = "#6ee7b7"
        elif state == AIFaceWidget.STATE_THINKING:
            style_color = "#c084fc"
        elif state == AIFaceWidget.STATE_WARN:
            style_color = "#fcd34d"
        elif state == AIFaceWidget.STATE_ALERT:
            style_color = "#f87171"
        elif state == AIFaceWidget.STATE_LOVE:
            style_color = "#f472b6"
        elif state == AIFaceWidget.STATE_HOT:
            style_color = "#fb923c"
        elif state == AIFaceWidget.STATE_COLD:
            style_color = "#38bdf8"

        self.lbl_status.setText(status_msg)
        self.lbl_status.setStyleSheet(f"color: {style_color}; background-color: #070b14; border-radius: 8px; padding: 6px;")

