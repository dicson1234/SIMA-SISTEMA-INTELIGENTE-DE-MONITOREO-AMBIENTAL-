# Pestaña del Asistente IA Conversacional (gui/ai_chat_tab.py) — UI SIMA 2.0
import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPainter, QPixmap, QColor, QPainterPath

from gui.ai_avatar import AIFaceWidget
from ai_agent import AIAgentEngine
from logger_manager import get_logger, log_exception

logger = get_logger("ai_chat_tab")

BG_DARK = "#141714"
BG_CARD = "#1e221c"
BG_CARD2 = "#252a23"
BORDER = "#30372c"
BORDER_LIGHT = "#3a4236"
OLIVE = "#6f7e5d"
OLIVE_MID = "#82936b"
OLIVE_LIGHT = "#a5b98a"
BEIGE = "#d8d0be"
CREAM = "#e8e3d7"
BEIGE_DARK = "#bfb7a5"
TEXT_MAIN = "#f2f0e8"
TEXT_SEC = "#c8c7be"
TEXT_MUTED = "#969890"
USER_BG = "#3a4632"
AI_BG = "#242822"


class AIWorkerThread(QThread):
    """Hilo asíncrono para consultas de IA. La lógica existente se conserva."""
    response_ready = Signal(dict)

    def __init__(self, ai_agent, prompt, nn1, nn2, t, h, parent=None):
        super().__init__(parent)
        self.ai_agent = ai_agent
        self.prompt = prompt
        self.nn1 = nn1
        self.nn2 = nn2
        self.t = t
        self.h = h

    def run(self):
        try:
            res = self.ai_agent.process_user_request(
                prompt=self.prompt,
                nn1_summary=self.nn1,
                nn2_summary=self.nn2,
                current_temp=self.t,
                current_hum=self.h,
            )
        except Exception as e:
            log_exception("Error en AIWorkerThread", e)
            res = {
                "response": f"Sistema operativo a {self.t:.1f}°C / {self.h:.1f}% RH.",
                "action_taken": None,
                "action_details": None,
                "expression_state": "HAPPY",
            }
        self.response_ready.emit(res)


class _MetricTile(QFrame):
    """Tarjeta compacta de métrica, solo visual."""

    def __init__(self, title: str, icon: str, accent: str = OLIVE_LIGHT, parent=None):
        super().__init__(parent)
        self.setObjectName("aiMetricTile")
        self._accent = accent

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 11, 14, 11)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)

        icon_box = QLabel(icon)
        icon_box.setFixedSize(34, 34)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFont(QFont("Segoe UI Emoji", 14))
        icon_box.setStyleSheet(
            f"background:#242822;border:1px solid {BORDER};border-radius:11px;color:{accent};"
        )

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color:{TEXT_SEC};background:transparent;border:none;font-size:10.5px;font-weight:600;"
        )
        top.addWidget(icon_box)
        top.addWidget(title_lbl, 1)
        root.addLayout(top)

        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet(
            f"color:{TEXT_MAIN};background:transparent;border:none;font-size:21px;font-weight:700;"
        )
        root.addWidget(self.value_lbl)

        self.status_lbl = QLabel("Sin lectura")
        self.status_lbl.setStyleSheet(
            f"color:{TEXT_MUTED};background:transparent;border:none;font-size:9.5px;font-weight:600;"
        )
        root.addWidget(self.status_lbl)

    def set_data(self, value: str, status: str, status_color: str = OLIVE_LIGHT) -> None:
        self.value_lbl.setText(value)
        self.status_lbl.setText(f"● {status}")
        self.status_lbl.setStyleSheet(
            f"color:{status_color};background:transparent;border:none;font-size:9.5px;font-weight:600;"
        )


class _ForestChatFrame(QFrame):
    """Marco de chat con imagen ambiental sutil y velo oscuro."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pix = QPixmap("assets/hero_forest.png")
        self.setObjectName("forestChatFrame")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor(BG_CARD))
        if not self._pix.isNull():
            scaled = self._pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
            p.save()
            p.setClipPath(path)
            p.setOpacity(0.24)
            p.drawPixmap(x, y, scaled)
            p.setOpacity(0.78)
            p.fillRect(self.rect(), QColor("#101510"))
            p.restore()
        p.end()
        super().paintEvent(event)


class ChatBubbleWidget(QWidget):
    """Burbuja nativa con avatar, texto y hora."""

    def __init__(self, text: str, is_user: bool, ts: str, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(7, 4, 7, 4)
        outer.setSpacing(8)

        bubble = QFrame()
        bg_col = USER_BG if is_user else AI_BG
        bd_col = "#4a5940" if is_user else BORDER
        bubble.setStyleSheet(
            f"QFrame{{background-color:{bg_col};border:1px solid {bd_col};border-radius:14px;}}"
        )
        bv = QVBoxLayout(bubble)
        bv.setContentsMargins(14, 10, 14, 8)
        bv.setSpacing(3)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.PlainText if is_user else Qt.AutoText)
        lbl.setStyleSheet(
            f"color:{TEXT_MAIN};background:transparent;border:none;font-size:12.5px;"
        )
        lbl.setMaximumWidth(620)

        ts_lbl = QLabel(ts)
        ts_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ts_lbl.setStyleSheet(
            f"color:{TEXT_MUTED};background:transparent;border:none;font-size:9px;"
        )
        bv.addWidget(lbl)
        bv.addWidget(ts_lbl)

        if is_user:
            outer.addStretch(1)
            outer.addWidget(bubble, 0, Qt.AlignTop)
            outer.addWidget(self._avatar("●", BG_CARD2, BORDER_LIGHT), 0, Qt.AlignTop)
        else:
            outer.addWidget(self._avatar("🌿", BEIGE, BEIGE_DARK), 0, Qt.AlignTop)
            outer.addWidget(bubble, 0, Qt.AlignTop)
            outer.addStretch(1)

    @staticmethod
    def _avatar(symbol: str, bg: str, border: str) -> QLabel:
        av = QLabel(symbol)
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignCenter)
        av.setFont(QFont("Segoe UI Emoji", 10))
        av.setStyleSheet(
            f"background:{bg};border:1px solid {border};border-radius:17px;color:#141714;"
        )
        return av


class AIChatTabWidget(QWidget):
    """Panel IA rediseñado. Solo cambia composición/estética de la UI."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.ai_agent = AIAgentEngine(main_window=self.main_window)
        self._worker: Optional[AIWorkerThread] = None

        self._init_ui()

        self._alert_timer = QTimer(self)
        self._alert_timer.setInterval(30000)
        self._alert_timer.timeout.connect(self._check_proactive)
        self._alert_timer.start()

        self._metrics_timer = QTimer(self)
        self._metrics_timer.setInterval(2000)
        self._metrics_timer.timeout.connect(self._refresh_metric_strip)
        self._metrics_timer.start()
        self._refresh_metric_strip()

    def paintEvent(self, event):
        """Fondo oscuro natural de la pestaña."""
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG_DARK))
        fern = QPixmap("assets/fern_corners.png")
        if not fern.isNull():
            scaled = fern.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.setOpacity(0.18)
            p.drawPixmap((self.width() - scaled.width()) // 2, self.height() - scaled.height(), scaled)
        p.end()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Fila de métricas inspirada en la referencia.
        metrics_frame = QFrame()
        metrics_frame.setObjectName("aiMetricsStrip")
        metrics_frame.setStyleSheet(
            f"QFrame#aiMetricsStrip{{background:#1b1f1a;border:1px solid {BORDER};border-radius:16px;}}"
        )
        metrics = QHBoxLayout(metrics_frame)
        metrics.setContentsMargins(10, 10, 10, 10)
        metrics.setSpacing(8)

        self.metric_temp = _MetricTile("Temperatura", "♨", OLIVE_LIGHT)
        self.metric_hum = _MetricTile("Humedad Relativa", "◉", OLIVE_LIGHT)
        self.metric_pm25 = _MetricTile("PM2.5", "••", OLIVE_LIGHT)
        self.metric_pm10 = _MetricTile("PM10", "••", "#d4a94e")
        self.metric_light = _MetricTile("Luminosidad", "☀", "#d4a94e")
        for tile in (self.metric_temp, self.metric_hum, self.metric_pm25, self.metric_pm10, self.metric_light):
            tile.setMinimumHeight(104)
            metrics.addWidget(tile, 1)
        root.addWidget(metrics_frame)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(
            f"QSplitter::handle{{background:{BORDER};border-radius:3px;}}"
            f"QSplitter::handle:hover{{background:{OLIVE};}}"
        )

        # Panel izquierdo: avatar pixel + acciones.
        left = QWidget()
        left.setStyleSheet("background:transparent;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(10)

        asst_card = QFrame()
        asst_card.setObjectName("assistantCard")
        asst_card.setStyleSheet(
            f"QFrame#assistantCard{{background:#1b1f1a;border:1px solid {BORDER};border-radius:16px;}}"
        )
        av = QVBoxLayout(asst_card)
        av.setContentsMargins(14, 16, 14, 16)
        av.setSpacing(9)

        title = QLabel("🌿  Asistente Ambiental")
        title.setStyleSheet(
            f"color:{OLIVE_LIGHT};background:transparent;border:none;font-size:14px;font-weight:700;"
        )
        av.addWidget(title)

        circle_container = QFrame()
        circle_container.setFixedSize(178, 178)
        circle_container.setStyleSheet(
            f"QFrame{{background:qradialgradient(cx:0.5,cy:0.5,radius:0.62,"
            f"fx:0.5,fy:0.5,stop:0 #151b16,stop:0.78 #111611,stop:1 {OLIVE_MID});"
            f"border:2px solid {OLIVE_MID};border-radius:89px;}}"
        )
        circle_layout = QVBoxLayout(circle_container)
        circle_layout.setContentsMargins(7, 7, 7, 7)
        circle_layout.setAlignment(Qt.AlignCenter)

        self.avatar_face = AIFaceWidget(circle_container)
        self.avatar_face.setFixedSize(150, 130)
        circle_layout.addWidget(self.avatar_face, 0, Qt.AlignCenter)

        av.addWidget(circle_container, 0, Qt.AlignCenter)
        desc = QLabel("Estoy aquí para ayudarte a entender tus datos y cuidar nuestro entorno.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            f"color:{TEXT_MUTED};background:transparent;border:none;font-size:9.5px;"
        )
        av.addWidget(desc)

        actions = QFrame()
        actions.setStyleSheet(
            f"QFrame{{background:#1b1f1a;border:1px solid {BORDER};border-radius:16px;}}"
        )
        act = QVBoxLayout(actions)
        act.setContentsMargins(12, 12, 12, 12)
        act.setSpacing(7)
        act_title = QLabel("⚡  Acciones Rápidas")
        act_title.setStyleSheet(
            f"color:{OLIVE_LIGHT};background:transparent;border:none;font-size:11px;font-weight:700;"
        )
        act.addWidget(act_title)

        btn_style = (
            f"QPushButton{{background:#242822;color:{TEXT_MAIN};border:1px solid {BORDER};"
            f"border-radius:10px;padding:9px 12px;font-size:11px;text-align:left;}}"
            f"QPushButton:hover{{background:{BEIGE};color:#141714;border-color:{BEIGE_DARK};font-weight:700;}}"
        )
        for label, query in [
            ("📄  Generar Reporte PDF", "Genera un reporte PDF completo"),
            ("📊  Exportar Hoja Excel", "Exportar a Excel los datos actuales"),
            ("📝  Redactar Ensayo Técnico", "Redacta un ensayo técnico ambiental"),
            ("🌡️  ¿Cómo está la temperatura?", "que tal la temperatura"),
        ]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked=False, q=query: self._send_quick(q))
            act.addWidget(btn)

        lv.addWidget(asst_card, 1)
        lv.addWidget(actions, 0)

        # Panel derecho: chat forestal.
        right = QWidget()
        right.setStyleSheet("background:transparent;")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)

        chat_frame = _ForestChatFrame()
        chat_frame.setStyleSheet(
            f"QFrame#forestChatFrame{{border:1px solid {BORDER};border-radius:16px;background:{BG_CARD};}}"
        )
        cfv = QVBoxLayout(chat_frame)
        cfv.setContentsMargins(0, 0, 0, 0)
        cfv.setSpacing(0)

        chat_header = QFrame()
        chat_header.setStyleSheet(
            f"QFrame{{background:rgba(20,23,20,0.82);border:none;border-bottom:1px solid {BORDER};}}"
        )
        ch = QHBoxLayout(chat_header)
        ch.setContentsMargins(14, 9, 14, 9)
        chat_title = QLabel("Asistente Conversacional IA")
        chat_title.setStyleSheet(
            f"color:{TEXT_MAIN};background:transparent;border:none;font-size:12px;font-weight:700;"
        )
        chat_state = QLabel("● En línea")
        chat_state.setStyleSheet(
            f"color:{OLIVE_LIGHT};background:transparent;border:none;font-size:9.5px;font-weight:700;"
        )
        self.btn_reset_chat = QPushButton("Reiniciar Chat")
        self.btn_reset_chat.setCursor(Qt.PointingHandCursor)
        self.btn_reset_chat.setStyleSheet(
            f"QPushButton{{background:{BEIGE};color:#141714;border:1px solid {BEIGE_DARK};"
            f"border-radius:10px;padding:6px 12px;font-size:10.5px;font-weight:700;}}"
            f"QPushButton:hover{{background:{CREAM};border-color:{OLIVE};}}"
        )
        self.btn_reset_chat.clicked.connect(self._reset_chat)
        ch.addWidget(chat_title)
        ch.addWidget(chat_state)
        ch.addStretch(1)
        ch.addWidget(self.btn_reset_chat)
        cfv.addWidget(chat_header)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setStyleSheet(
            f"QScrollArea#chatScroll{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{background:transparent;width:7px;}}"
            f"QScrollBar::handle:vertical{{background:{BORDER_LIGHT};border-radius:3px;min-height:24px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{OLIVE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;border:none;background:transparent;}}"
        )
        self._chat_container = QWidget()
        self._chat_container.setStyleSheet("background:transparent;border:none;")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(12, 10, 12, 10)
        self._chat_layout.setSpacing(5)
        self._chat_layout.addStretch(1)
        self.chat_scroll.setWidget(self._chat_container)
        cfv.addWidget(self.chat_scroll, 1)

        input_bar = QFrame()
        input_bar.setStyleSheet(
            f"QFrame{{background:#252a23;border:none;border-top:1px solid {BORDER};}}"
        )
        ih = QHBoxLayout(input_bar)
        ih.setContentsMargins(12, 9, 12, 9)
        ih.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu mensaje o pregúntame algo...")
        self.input_field.setStyleSheet(
            f"QLineEdit{{background:#1b1f1a;border:1px solid {BORDER};border-radius:11px;"
            f"padding:10px 14px;color:{TEXT_MAIN};}}"
            f"QLineEdit:focus{{border-color:{OLIVE_MID};}}"
        )
        self.input_field.returnPressed.connect(self._handle_send)

        self.btn_send = QPushButton("➤")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setFixedSize(48, 40)
        self.btn_send.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.btn_send.setStyleSheet(
            f"QPushButton{{background:{OLIVE};color:{TEXT_MAIN};border:1px solid {OLIVE_MID};border-radius:10px;}}"
            f"QPushButton:hover{{background:{OLIVE_MID};border-color:{OLIVE_LIGHT};}}"
        )
        self.btn_send.clicked.connect(self._handle_send)

        ih.addWidget(self.input_field, 1)
        ih.addWidget(self.btn_send)
        cfv.addWidget(input_bar)

        rv.addWidget(chat_frame, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([340, 760])
        root.addWidget(splitter, 1)

        self._add_ai_bubble(
            "Hola, Dicson. Según los datos actuales, la temperatura es de <b>24.0°C</b> con una humedad del <b>50%</b>.<br>"
            "Se considera un clima confortable y templado para actividades cotidianas."
        )

    def _refresh_metric_strip(self):
        """Actualiza únicamente las tarjetas visuales de esta pestaña."""
        t, h = 24.0, 50.0
        light = None
        temp_label = "Confortable"
        hum_label = "Óptimo"
        light_label = "Moderada"
        if self.main_window:
            sm = getattr(self.main_window, "sensor_manager", None)
            if sm and sm.last_reading:
                reading = sm.last_reading
                t = reading.temperature
                h = reading.humidity
                light = reading.light
                temp_label = reading.temp_class.label
                hum_label = reading.hum_class.label
                light_label = reading.light_class.label

        self.metric_temp.set_data(f"{t:.1f} °C", temp_label)
        self.metric_hum.set_data(f"{h:.1f} %", hum_label)
        self.metric_light.set_data(
            f"{light:.0f} lux" if light is not None else "-- lux",
            light_label if light is not None else "Sin lectura",
            "#d4a94e",
        )
        self.metric_pm25.set_data("-- µg/m³", "Sensor no disponible", TEXT_MUTED)
        self.metric_pm10.set_data("-- µg/m³", "Sensor no disponible", TEXT_MUTED)

    def _ts(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def _add_user_bubble(self, text):
        self._chat_layout.insertWidget(
            self._chat_layout.count() - 1,
            ChatBubbleWidget(text, True, self._ts()),
        )
        self._scroll_bottom()

    def _add_ai_bubble(self, text):
        self._chat_layout.insertWidget(
            self._chat_layout.count() - 1,
            ChatBubbleWidget(text, False, self._ts()),
        )
        self._scroll_bottom()

    def _clear_bubbles(self):
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scroll_bottom(self):
        QTimer.singleShot(
            0,
            lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ),
        )

    def _handle_send(self):
        prompt = self.input_field.text().strip()
        if not prompt:
            return
        self.input_field.clear()
        self._add_user_bubble(prompt)
        self._generate_response(prompt)

    def _send_quick(self, query):
        self._add_user_bubble(query)
        self._generate_response(query)

    def _reset_chat(self):
        self.ai_agent.clear_conversation_history()
        self._clear_bubbles()
        self.avatar_face.set_expression(AIFaceWidget.STATE_NORMAL)
        self._add_ai_bubble("Conversación reiniciada. ¿En qué puedo ayudarte hoy?")

    def add_proactive_alert(self, text, expression_state="WARN"):
        self._add_ai_bubble(f"⚠️ <b>ALERTA:</b> {text}")
        self.avatar_face.set_expression(expression_state)

    def _get_live_data(self):
        t, h = 24.0, 50.0
        nn1, nn2 = {}, {}
        if self.main_window:
            sm = getattr(self.main_window, "sensor_manager", None)
            if sm and sm.last_reading:
                t = sm.last_reading.temperature
                h = sm.last_reading.humidity
            nm = getattr(self.main_window, "nn_manager", None)
            if nm:
                nn1 = nm.get_ai_agent_summary(t, h)
            an = getattr(self.main_window, "anomaly_nn", None)
            if an:
                nn2 = an.get_summary()
        return t, h, nn1, nn2

    def _generate_response(self, query):
        t, h, nn1, nn2 = self._get_live_data()
        self.avatar_face.set_expression(AIFaceWidget.STATE_THINKING)
        self.btn_send.setEnabled(False)
        self.input_field.setEnabled(False)

        self.worker_thread = AIWorkerThread(
            self.ai_agent, query, nn1, nn2, t, h, parent=self
        )
        self.worker_thread.response_ready.connect(self._on_response)
        self.worker_thread.start()

    @Slot(dict)
    def _on_response(self, res):
        self.btn_send.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        text = res.get("response", "")
        expr = res.get("expression_state", AIFaceWidget.STATE_HAPPY)

        self.avatar_face.set_expression(AIFaceWidget.STATE_TALKING)
        self._add_ai_bubble(text)
        QTimer.singleShot(1200, lambda: self.avatar_face.set_expression(expr))

    def _check_proactive(self):
        t, h, nn1, nn2 = self._get_live_data()
        alert = self.ai_agent.check_proactive_alerts(t, h, nn1, nn2)
        if alert:
            self._add_ai_bubble(alert["message"])
            self.avatar_face.set_expression(
                alert.get("expression_state", AIFaceWidget.STATE_WARN)
            )
