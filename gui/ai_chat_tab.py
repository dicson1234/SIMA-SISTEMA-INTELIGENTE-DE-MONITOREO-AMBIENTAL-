"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Pestaña del Asistente IA Conversacional (gui/ai_chat_tab.py) — v6 Olive Nature Elegance

Rediseño fiel a la imagen de referencia #3:
  - Paleta Oliva / Beige / Tierra Elegante.
  - Encabezado con título "Asistente Conversacional IA", subtítulo y botón "Reiniciar Chat".
  - Panel izquierdo con tarjeta limpia del Asistente Ambiental (avatar circular integrado sin desbordamientos).
  - SIN barra horizontal flotante de estado ("SIMA AI — Estado: ..."). ELIMINADA POR COMPLETO.
  - Botones de Acciones Rápidas compactos y elegantes.
  - Burbujas de chat estilizadas (Usuario: verde oliva a la derecha; IA: tarjeta gris verdosa a la izquierda con hoja).

Autor:  Equipo SIMA — Diseñador UX/UI & Especialista IA
Fecha:  2026-08-18
"""

import datetime
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTextEdit, QLineEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QTimer
from PySide6.QtGui import QFont

from ai_agent import AIAgentEngine
from logger_manager import get_logger, log_exception

logger = get_logger("ai_chat_tab")


# ─── Paleta Oliva / Beige Nature Elegance ───
BG_DARK     = "#141714"
BG_CARD     = "#1e221c"
BG_CARD2    = "#252a23"
BORDER      = "#2e342b"
BORDER_HIGHLIGHT = "#3a4236"

OLIVE       = "#6f7e5d"
OLIVE_MID   = "#82936b"
OLIVE_LIGHT = "#a5b98a"

BEIGE       = "#d8d0be"
CREAM       = "#e8e3d7"
BEIGE_DARK  = "#bfb7a5"

TEXT_MAIN   = "#f2f0e8"
TEXT_SEC    = "#c8c7be"
TEXT_MUTED  = "#969890"

USER_BG     = "#30372c"
AI_BG       = "#242822"


class AIWorkerThread(QThread):
    """Hilo asíncrono para consultas de IA."""
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
                prompt=self.prompt, nn1_summary=self.nn1,
                nn2_summary=self.nn2, current_temp=self.t, current_hum=self.h
            )
        except Exception as e:
            log_exception("Error en AIWorkerThread", e)
            res = {
                "response": f"Sistema operativo a {self.t:.1f}°C / {self.h:.1f}% RH.",
                "action_taken": None, "action_details": None,
                "expression_state": "HAPPY"
            }
        self.response_ready.emit(res)


class AIChatTabWidget(QWidget):
    """Panel conversacional rediseñado según la 3ra imagen de referencia."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.ai_agent = AIAgentEngine(main_window=self.main_window)
        self._worker: Optional[AIWorkerThread] = None

        self._init_ui()

        # Timer para alertas proactivas (cada 30s)
        self._alert_timer = QTimer(self)
        self._alert_timer.setInterval(30000)
        self._alert_timer.timeout.connect(self._check_proactive)
        self._alert_timer.start()

    # ─────────────────────────── UI BUILD ───────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── 1. ENCABEZADO DE LA SECCIÓN IA ──
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(18, 14, 18, 14)
        h_layout.setSpacing(14)

        # Icono / Decoración ambiental sutil
        header_icon = QLabel("🌿")
        header_icon.setFont(QFont("Segoe UI Emoji", 20))
        header_icon.setFixedSize(40, 40)
        header_icon.setAlignment(Qt.AlignCenter)
        header_icon.setStyleSheet(f"""
            background-color: {BG_CARD2};
            border: 1px solid {BORDER_HIGHLIGHT};
            border-radius: 20px;
        """)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)

        lbl_title = QLabel("Asistente Conversacional IA")
        lbl_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {TEXT_MAIN};")

        lbl_sub = QLabel("Motor de conversación inteligente para análisis y consultas ambientales.")
        lbl_sub.setFont(QFont("Segoe UI", 9.5))
        lbl_sub.setStyleSheet(f"color: {TEXT_MUTED};")

        title_v.addWidget(lbl_title)
        title_v.addWidget(lbl_sub)

        # Botón Reiniciar Chat
        self.btn_reset_chat = QPushButton("🔄  Reiniciar Chat")
        self.btn_reset_chat.setCursor(Qt.PointingHandCursor)
        self.btn_reset_chat.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_CARD2};
                color: {TEXT_MAIN};
                border: 1px solid {BORDER_HIGHLIGHT};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {OLIVE};
                color: {TEXT_MAIN};
                border-color: {OLIVE_LIGHT};
            }}
        """)
        self.btn_reset_chat.clicked.connect(self._reset_chat)

        h_layout.addWidget(header_icon)
        h_layout.addLayout(title_v, 1)
        h_layout.addWidget(self.btn_reset_chat)

        root.addWidget(header_card)

        # ── 2. SPLITTER: PANEL IZQ (AVATAR+ACCIONES) + PANEL DER (CHAT) ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {BORDER}; border-radius: 3px; }}")

        # ━━━ PANEL IZQUIERDO: Tarjeta Asistente + Acciones Rápidas ━━━
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(10)

        # Tarjeta Asistente Ambiental (Avatar integrado en circulo beige/verde)
        asst_card = QFrame()
        asst_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        av = QVBoxLayout(asst_card)
        av.setContentsMargins(16, 20, 16, 20)
        av.setSpacing(12)
        av.setAlignment(Qt.AlignCenter)

        # Círculo ilustrativo del Asistente ambiental
        circle_container = QFrame()
        circle_container.setFixedSize(140, 140)
        circle_container.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
                    stop:0 {CREAM}, stop:0.75 {BEIGE}, stop:1.0 {BEIGE_DARK});
                border: 2px solid {OLIVE_MID};
                border-radius: 70px;
            }}
        """)
        circle_layout = QVBoxLayout(circle_container)
        circle_layout.setContentsMargins(0, 0, 0, 0)
        circle_layout.setAlignment(Qt.AlignCenter)

        lbl_leaf = QLabel("🌿")
        lbl_leaf.setFont(QFont("Segoe UI Emoji", 42))
        lbl_leaf.setAlignment(Qt.AlignCenter)
        lbl_leaf.setStyleSheet("background: transparent;")
        circle_layout.addWidget(lbl_leaf)

        lbl_asst_name = QLabel("Asistente Ambiental")
        lbl_asst_name.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_asst_name.setStyleSheet(f"color: {BEIGE};")
        lbl_asst_name.setAlignment(Qt.AlignCenter)

        lbl_asst_desc = QLabel("Estoy aquí para ayudarte a entender tus datos y cuidar nuestro entorno.")
        lbl_asst_desc.setFont(QFont("Segoe UI", 9))
        lbl_asst_desc.setStyleSheet(f"color: {TEXT_MUTED};")
        lbl_asst_desc.setWordWrap(True)
        lbl_asst_desc.setAlignment(Qt.AlignCenter)

        av.addWidget(circle_container, 0, Qt.AlignCenter)
        av.addWidget(lbl_asst_name)
        av.addWidget(lbl_asst_desc)

        # Tarjeta de Acciones Rápidas
        act_card = QFrame()
        act_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        acv = QVBoxLayout(act_card)
        acv.setContentsMargins(14, 14, 14, 14)
        acv.setSpacing(8)

        lbl_act = QLabel("🌿  Acciones Rápidas")
        lbl_act.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_act.setStyleSheet(f"color: {BEIGE};")
        acv.addWidget(lbl_act)

        btn_style = f"""
            QPushButton {{
                background-color: {BG_CARD2};
                color: {TEXT_MAIN};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 11.5px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {OLIVE};
                border-color: {OLIVE_LIGHT};
                color: {TEXT_MAIN};
            }}
        """
        for label, query in [
            ("📄  Generar Reporte PDF",      "Genera un reporte PDF completo"),
            ("📊  Exportar Hoja Excel",      "Exportar a Excel los datos actuales"),
            ("📝  Redactar Ensayo Técnico",   "Redacta un ensayo técnico ambiental"),
            ("🌡️  ¿Cómo está la temperatura?", "que tal la temperatura"),
        ]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked=False, q=query: self._send_quick(q))
            acv.addWidget(btn)

        lv.addWidget(asst_card)
        lv.addWidget(act_card)
        lv.addStretch()

        # ━━━ PANEL DERECHO: ÁREA DE CHAT ━━━
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        chat_frame = QFrame()
        chat_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        cfv = QVBoxLayout(chat_frame)
        cfv.setContentsMargins(0, 0, 0, 0)
        cfv.setSpacing(0)

        # Consola de chat (QTextEdit)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_DARK};
                border: none;
                color: {TEXT_MAIN};
                padding: 16px;
                border-radius: 12px 12px 0 0;
            }}
            QScrollBar:vertical {{
                background-color: {BG_DARK};
                width: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none; background: none;
            }}
        """)

        # Barra de entrada de texto inferior
        input_bar = QFrame()
        input_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD2};
                border-top: 1px solid {BORDER};
                border-radius: 0 0 12px 12px;
            }}
        """)
        ih = QHBoxLayout(input_bar)
        ih.setContentsMargins(12, 10, 12, 10)
        ih.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu mensaje o pregúntame algo...")
        self.input_field.setFont(QFont("Segoe UI", 10))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border: 1px solid {OLIVE_MID};
            }}
        """)
        self.input_field.returnPressed.connect(self._handle_send)

        self.btn_send = QPushButton("✈️")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setFixedSize(46, 40)
        self.btn_send.setFont(QFont("Segoe UI Emoji", 13))
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {OLIVE};
                color: {TEXT_MAIN};
                border: 1px solid {OLIVE_MID};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {OLIVE_MID};
            }}
        """)
        self.btn_send.clicked.connect(self._handle_send)

        ih.addWidget(self.input_field, 1)
        ih.addWidget(self.btn_send)

        cfv.addWidget(self.chat_display, 1)
        cfv.addWidget(input_bar)

        rv.addWidget(chat_frame)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([310, 690])

        root.addWidget(splitter, 1)

        # Mensaje de bienvenida inicial
        self._add_ai_bubble(
            "Hola, Dicson. Según los datos actuales, la temperatura es de <b>24.0°C</b> con una humedad del <b>50%</b>.<br>"
            "Se considera un clima confortable y templado para actividades cotidianas."
        )

    # ──────────────────── BURBUJAS DE CHAT ────────────────────

    def _ts(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def _add_user_bubble(self, text):
        """Burbuja del usuario a la derecha estilo Oliva Oscuro."""
        ts = self._ts()
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="25%"></td>'
            f'<td align="right">'
            f'<span style="background-color:{USER_BG}; color:{TEXT_MAIN}; '
            f'padding:10px 16px; border-radius:12px; font-size:13px; border: 1px solid {BORDER_HIGHLIGHT};">'
            f'{text}</span>'
            f'<br/><span style="color:{TEXT_MUTED}; font-size:10px;">{ts} 👤</span>'
            f'</td></tr></table>'
        )
        self.chat_display.append(html)
        self.chat_display.append("")
        self._scroll_bottom()

    def _add_ai_bubble(self, text):
        """Burbuja de la IA a la izquierda estilo Gris-Verdoso con badge de hoja."""
        ts = self._ts()
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td align="left">'
            f'<span style="background-color:{CREAM}; color:#252a23; padding:5px 8px; border-radius:12px; font-size:14px;">🌿</span> '
            f'<span style="background-color:{AI_BG}; color:{TEXT_MAIN}; '
            f'padding:12px 16px; border-radius:12px; font-size:13px; line-height:1.6; border: 1px solid {BORDER};">'
            f'{text}</span>'
            f'<br/><span style="color:{TEXT_MUTED}; font-size:10px; margin-left:36px;">{ts}</span>'
            f'</td>'
            f'<td width="15%"></td>'
            f'</tr></table>'
        )
        self.chat_display.append(html)
        self.chat_display.append("")
        self._scroll_bottom()

    def _scroll_bottom(self):
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ──────────────────── MANEJO DE MENSAJES ──────────────────

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
        self.chat_display.clear()
        self._add_ai_bubble("Conversación reiniciada. ¿En qué puedo ayudarte hoy?")

    def add_proactive_alert(self, text, expression_state="WARN"):
        """Publica una alerta proactiva en el chat."""
        self._add_ai_bubble(f"⚠️ <b>ALERTA:</b> {text}")

    # ──────────────────── MOTOR DE IA ─────────────────────────

    def _get_live_data(self):
        """Lee temperatura, humedad y resúmenes de NN desde la ventana principal."""
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
        self.btn_send.setEnabled(False)
        self.input_field.setEnabled(False)

        self.worker_thread = AIWorkerThread(self.ai_agent, query, nn1, nn2, t, h, parent=self)
        self.worker_thread.response_ready.connect(self._on_response)
        self.worker_thread.start()

    @Slot(dict)
    def _on_response(self, res):
        self.btn_send.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        text = res.get("response", "")
        self._add_ai_bubble(text)

    def _check_proactive(self):
        t, h, nn1, nn2 = self._get_live_data()
        alert = self.ai_agent.check_proactive_alerts(t, h, nn1, nn2)
        if alert:
            self._add_ai_bubble(alert["message"])
