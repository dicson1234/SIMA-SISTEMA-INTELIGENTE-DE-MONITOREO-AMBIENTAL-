"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Pestaña del Asistente IA Conversacional (gui/ai_chat_tab.py) — v5 Botanical Dark Redesign

Layout fiel a la imagen de referencia:
  ┌─────────────────────────────────────────────────────────────┐
  │  [Temp]  [Humedad]  [PM2.5]  [PM10]  [Luminosidad]         │  ← 5 Metric Cards
  ├────────────────┬────────────────────────────────────────────┤
  │ 🌿 Asistente   │  Chat conversacional con burbujas          │
  │  Ambiental     │  ┌────────────────────────┐                │
  │                │  │ 🌿 respuesta IA        │  timestamp     │
  │  [Pixel Avatar]│  └────────────────────────┘                │
  │                │                 ┌──────────┐               │
  │  ──────────    │                 │ user msg │ timestamp 👤  │
  │ ⚡ Acciones    │                 └──────────┘               │
  │  [PDF] [Excel] │  ┌─────────────────────────────┐ ┌──────┐ │
  │  [Ensayo][Tmp] │  │  Escribe tu mensaje...      │ │  ✈️  │ │
  └────────────────┴──┴─────────────────────────────┴─┴──────┘ ┘

Autor:  Equipo SIMA — Diseñador UX/UI & Especialista IA
Fecha:  2026-08-18
"""

import datetime
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTextEdit, QLineEdit, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QColor, QPalette

from gui.ai_avatar import AIFaceContainer, AIFaceWidget
from ai_agent import AIAgentEngine
from logger_manager import get_logger, log_exception

logger = get_logger("ai_chat_tab")


# ─── Colores del Tema Botanical Dark ───
BG_DARK   = "#0b100d"
BG_CARD   = "#111a14"
BG_CARD2  = "#162019"
BORDER    = "#1e3025"
GREEN     = "#4ade80"
GREEN_DIM = "#2d5a3a"
TEXT      = "#d1fae5"
TEXT_DIM  = "#6b8f78"
USER_BG   = "#1a3524"
AI_BG     = "#132218"


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
            log_exception(e, "Error en AIWorkerThread")
            res = {
                "response": f"Sistema operativo a {self.t:.1f}°C / {self.h:.1f}% RH.",
                "action_taken": None, "action_details": None,
                "expression_state": "HAPPY"
            }
        self.response_ready.emit(res)


class MetricCard(QFrame):
    """Mini tarjeta de métrica para la fila superior."""

    def __init__(self, icon, title, value, status, status_color=GREEN, parent=None):
        super().__init__(parent)
        self.setFixedHeight(78)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setFont(QFont("Segoe UI Emoji", 16))
        lbl_icon.setFixedWidth(30)

        v = QVBoxLayout()
        v.setSpacing(1)

        lbl_t = QLabel(title)
        lbl_t.setFont(QFont("Segoe UI", 8))
        lbl_t.setStyleSheet(f"color: {TEXT_DIM};")

        self.lbl_v = QLabel(value)
        self.lbl_v.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_v.setStyleSheet("color: #ffffff;")

        self.lbl_s = QLabel(f"● {status}")
        self.lbl_s.setFont(QFont("Segoe UI", 7.5, QFont.Bold))
        self.lbl_s.setStyleSheet(f"color: {status_color};")

        v.addWidget(lbl_t)
        v.addWidget(self.lbl_v)
        v.addWidget(self.lbl_s)
        h.addWidget(lbl_icon)
        h.addLayout(v, 1)

    def update_data(self, value, status, color=GREEN):
        self.lbl_v.setText(value)
        self.lbl_s.setText(f"● {status}")
        self.lbl_s.setStyleSheet(f"color: {color};")


class AIChatTabWidget(QWidget):
    """Panel conversacional rediseñado fiel a la imagen de referencia."""

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
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        # ── 1. FILA SUPERIOR: 5 METRIC CARDS ──
        metrics = QHBoxLayout()
        metrics.setSpacing(8)
        self.c_temp = MetricCard("🌡️", "Temperatura",       "24.0 °C",    "Confortable")
        self.c_hum  = MetricCard("💧", "Humedad Relativa",   "50.0 %",     "Óptimo")
        self.c_pm25 = MetricCard("🫧", "PM2.5",              "12 µg/m³",   "Bueno")
        self.c_pm10 = MetricCard("💛", "PM10",               "28 µg/m³",   "Bueno")
        self.c_lux  = MetricCard("☀️", "Luminosidad",        "650 lux",    "Moderada", "#a3e635")
        for c in [self.c_temp, self.c_hum, self.c_pm25, self.c_pm10, self.c_lux]:
            metrics.addWidget(c)
        root.addLayout(metrics)

        # ── 2. SPLITTER: PANEL IZQ (AVATAR+ACCIONES) + PANEL DER (CHAT) ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {BORDER}; border-radius: 2px; }}")

        # ━━━ PANEL IZQUIERDO ━━━
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(10)

        # Tarjeta Asistente Ambiental
        asst_card = QFrame()
        asst_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        av = QVBoxLayout(asst_card)
        av.setContentsMargins(14, 14, 14, 14)
        av.setSpacing(8)

        lbl_asst = QLabel("🌿  Asistente Ambiental")
        lbl_asst.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_asst.setStyleSheet(f"color: {GREEN};")
        av.addWidget(lbl_asst)

        # Avatar Pixeleado
        self.avatar_container = AIFaceContainer(self)
        self.avatar_container.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #070d09;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        av.addWidget(self.avatar_container)

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
        acv.setContentsMargins(14, 12, 14, 12)
        acv.setSpacing(6)

        lbl_act = QLabel("⚡  Acciones Rápidas")
        lbl_act.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
        lbl_act.setStyleSheet(f"color: {TEXT_DIM};")
        acv.addWidget(lbl_act)

        btn_style = f"""
            QPushButton {{
                background-color: {BG_CARD2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {GREEN_DIM};
                border-color: {GREEN};
            }}
        """
        for label, query in [
            ("📄  Generar Reporte PDF",      "Genera un reporte PDF completo"),
            ("📊  Exportar Hoja Excel",      "Exportar a Excel los datos actuales"),
            ("📝  Redactar Ensayo Técnico",   "Redacta un ensayo técnico ambiental"),
            ("🌡️  ¿Cómo está la temperatura?", "que tal la temperatura"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked=False, q=query: self._send_quick(q))
            acv.addWidget(btn)

        lv.addWidget(asst_card)
        lv.addWidget(act_card)
        lv.addStretch()

        # ━━━ PANEL DERECHO: CHAT ━━━
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        # Contenedor del chat con fondo botánico
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

        # Consola de chat — usar HTML con tablas para burbujas
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10.5))
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a110d;
                border: none;
                color: {TEXT};
                padding: 16px;
                border-radius: 12px 12px 0 0;
            }}
            QScrollBar:vertical {{
                background-color: #0a110d;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none; background: none;
            }}
        """)

        # Barra de entrada inferior
        input_bar = QFrame()
        input_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD2};
                border-top: 1px solid {BORDER};
                border-radius: 0 0 12px 12px;
            }}
        """)
        ih = QHBoxLayout(input_bar)
        ih.setContentsMargins(12, 8, 12, 8)
        ih.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu mensaje o pregúntame algo...")
        self.input_field.setFont(QFont("Segoe UI", 10.5))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT};
            }}
            QLineEdit:focus {{
                border: 1px solid {GREEN};
            }}
        """)
        self.input_field.returnPressed.connect(self._handle_send)

        self.btn_send = QPushButton("✈️")
        self.btn_send.setFixedSize(44, 40)
        self.btn_send.setFont(QFont("Segoe UI Emoji", 14))
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_DIM};
                color: #ffffff;
                border: 1px solid {GREEN};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {GREEN};
                color: #000000;
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
        splitter.setSizes([300, 700])

        root.addWidget(splitter, 1)

        # Mensaje de bienvenida
        self._add_ai_bubble(
            "La temperatura actual es de <b>24.0°C</b> con una humedad del <b>50%</b>.<br>"
            "Se considera un clima confortable y templado para realizar actividades al aire libre."
        )

    # ─────────────────── TELEMETRÍA EN VIVO ───────────────────

    def update_telemetry(self, temp, hum):
        t_st = "Confortable" if 18 <= temp <= 26 else ("Elevada" if temp > 26 else "Fresca")
        t_cl = GREEN if 18 <= temp <= 26 else ("#fb923c" if temp > 26 else "#38bdf8")
        self.c_temp.update_data(f"{temp:.1f} °C", t_st, t_cl)
        h_st = "Óptimo" if 40 <= hum <= 65 else ("Seco" if hum < 40 else "Húmedo")
        self.c_hum.update_data(f"{hum:.1f} %", h_st, GREEN)

    # ──────────────────── BURBUJAS DE CHAT ────────────────────

    def _ts(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def _add_user_bubble(self, text):
        """Burbuja del usuario a la derecha."""
        ts = self._ts()
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="30%"></td>'
            f'<td align="right">'
            f'<span style="background-color:{USER_BG}; color:#ffffff; '
            f'padding:8px 14px; border-radius:10px; font-size:13px;">'
            f'{text}</span>'
            f'<br/><span style="color:#6b7b6f; font-size:10px;">{ts} 👤</span>'
            f'</td></tr></table>'
        )
        self.chat_display.append(html)
        self.chat_display.append("")
        self._scroll_bottom()

    def _add_ai_bubble(self, text):
        """Burbuja de la IA a la izquierda con ícono de hoja."""
        ts = self._ts()
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td align="left">'
            f'<span style="color:{GREEN}; font-size:16px;">🌿</span> '
            f'<span style="background-color:{AI_BG}; color:{TEXT}; '
            f'padding:10px 14px; border-radius:10px; font-size:13px; line-height:1.6;">'
            f'{text}</span>'
            f'<br/><span style="color:#6b7b6f; font-size:10px;">{ts}</span>'
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
        self.avatar_container.set_state(AIFaceWidget.STATE_NORMAL, "🌿 SIMA AI — Chat Reiniciado")
        self._add_ai_bubble("Conversación reiniciada. ¿En qué puedo colaborarte?")

    def add_proactive_alert(self, text, expression_state="WARN"):
        """Publica una alerta proactiva en el chat."""
        self._add_ai_bubble(f"⚠️ <b>ALERTA:</b> {text}")
        self.avatar_container.set_state(expression_state)

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
                self.update_telemetry(t, h)
            nm = getattr(self.main_window, "nn_manager", None)
            if nm:
                nn1 = nm.get_ai_agent_summary(t, h)
            an = getattr(self.main_window, "anomaly_nn", None)
            if an:
                nn2 = an.get_summary()
        return t, h, nn1, nn2

    def _generate_response(self, query):
        t, h, nn1, nn2 = self._get_live_data()
        self.avatar_container.set_state(AIFaceWidget.STATE_THINKING, "💚 Consultando con Gemini...")

        self.worker_thread = AIWorkerThread(self.ai_agent, query, nn1, nn2, t, h, parent=self)
        self.worker_thread.response_ready.connect(self._on_response)
        self.worker_thread.start()


    @Slot(dict)
    def _on_response(self, res):
        text = res.get("response", "")
        expr = res.get("expression_state", AIFaceWidget.STATE_HAPPY)

        self.avatar_container.set_state(AIFaceWidget.STATE_TALKING)
        self._add_ai_bubble(text)
        QTimer.singleShot(1200, lambda: self.avatar_container.set_state(expr))



    def _check_proactive(self):
        t, h, nn1, nn2 = self._get_live_data()
        alert = self.ai_agent.check_proactive_alerts(t, h, nn1, nn2)
        if alert:
            self._add_ai_bubble(alert["message"])
            self.avatar_container.set_state(alert["expression_state"])
