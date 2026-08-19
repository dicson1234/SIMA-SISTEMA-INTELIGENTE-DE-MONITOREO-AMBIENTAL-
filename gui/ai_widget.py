"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Interfaz para Redes Neuronales e IA Conversacional con "Brazos" y Memoria (gui/ai_widget.py)

Proporciona la pestaña dedicada a la Red Neuronal Predictiva #1, Red Neuronal de Anomalías #2,
y la consola conversacional Qwen2.5 asíncrona (QThread) con memoria de chat y capacidades de acción.

Autor:  Equipo SIMA — Diseñador UX/UI & Especialista IA
Fecha:  2026-07-31
"""

from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QProgressBar, QTextEdit, QLineEdit, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QColor

import pyqtgraph as pg

from nn_predictor import NNPredictorManager
from anomaly_nn import AnomalyNNManager
from ai_agent import AIAgentEngine
from logger_manager import get_logger

logger = get_logger("ai_widget")


class AIWorkerThread(QThread):
    """Hilo secundario asíncrono para procesar solicitudes de la LLM sin congelar la GUI."""
    response_ready = Signal(dict)

    def __init__(
        self,
        ai_agent: AIAgentEngine,
        prompt: str,
        nn1_summary: Dict[str, Any],
        nn2_summary: Dict[str, Any],
        curr_t: float,
        curr_h: float
    ) -> None:
        super().__init__()
        self.ai_agent = ai_agent
        self.prompt = prompt
        self.nn1_summary = nn1_summary
        self.nn2_summary = nn2_summary
        self.curr_t = curr_t
        self.curr_h = curr_h

    def run(self) -> None:
        """Ejecuta el llamado HTTP a Ollama en segundo plano."""
        res = self.ai_agent.process_user_request(
            prompt=self.prompt,
            nn1_summary=self.nn1_summary,
            nn2_summary=self.nn2_summary,
            current_temp=self.curr_t,
            current_hum=self.curr_h
        )
        self.response_ready.emit(res)


class AINeuralNetworkWidget(QWidget):
    """Pestaña dedicada para las 2 Redes Neuronales y la IA Conversacional Qwen2.5 con 'Brazos' y Memoria."""

    def __init__(
        self,
        nn_manager: NNPredictorManager,
        anomaly_nn: Optional[AnomalyNNManager] = None,
        main_window: Optional[QWidget] = None,
        parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.nn_manager = nn_manager
        self.anomaly_nn = anomaly_nn if anomaly_nn else AnomalyNNManager()
        self.main_window = main_window

        # Inicializar motor conversacional con "Brazos" y memoria
        self.ai_agent = AIAgentEngine(main_window=self.main_window)
        self.worker_thread: Optional[AIWorkerThread] = None

        # Buffers para gráficas en vivo
        self.history_real_temp: List[float] = []
        self.history_pred_temp: List[float] = []
        self.history_real_hum: List[float] = []
        self.history_pred_hum: List[float] = []

        self._init_ui()
        self._update_display()

    def _init_ui(self) -> None:
        """Construye la interfaz visual con métricas de 2 Redes Neuronales, gráficas y Chat Qwen2.5 asíncrono."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # =====================================================================
        #  ENCABEZADO SUPERIOR
        # =====================================================================
        header_frame = QFrame()
        header_frame.setObjectName("cardFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_box = QVBoxLayout()
        lbl_title = QLabel("🧠  SISTEMA MULTI-RED NEURONAL & IA CONVERSACIONAL QWEN2.5")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_title.setStyleSheet("color: #38bdf8;")

        lbl_subtitle = QLabel(
            f"Red #1: Predictor MLP | Red #2: Autoencoder Anomalías | LLM: {self.ai_agent.active_model} (Memoria Conversacional Activa)"
        )
        lbl_subtitle.setFont(QFont("Segoe UI", 9))
        lbl_subtitle.setStyleSheet("color: #94a3b8;")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_subtitle)

        # Botones de control del modelo
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_train_now = QPushButton("⚡ Entrenar Paso")
        self.btn_train_now.clicked.connect(self._manual_train_step)

        self.btn_save_model = QPushButton("💾 Guardar Redes")
        self.btn_save_model.clicked.connect(self._save_model)

        self.btn_reset_model = QPushButton("🔄 Resetear Pesos")
        self.btn_reset_model.clicked.connect(self._reset_model)

        btn_box.addWidget(self.btn_train_now)
        btn_box.addWidget(self.btn_save_model)
        btn_box.addWidget(self.btn_reset_model)

        header_layout.addLayout(title_box, 3)
        header_layout.addLayout(btn_box, 2)

        # =====================================================================
        #  TARJETAS DE ESTADO Y MÉTRICAS DUALES (METRICS CARDS)
        # =====================================================================
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        # Tarjeta 1: Nivel de Inteligencia (Red #1)
        self.card_intel = self._create_metric_card("Inteligencia Red #1", "0.0%", "⚡", "#8b5cf6")
        self.progress_intel = QProgressBar()
        self.progress_intel.setRange(0, 100)
        self.progress_intel.setValue(0)
        self.progress_intel.setTextVisible(False)
        self.progress_intel.setMaximumHeight(8)
        self.progress_intel.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #ec4899);
                border-radius: 4px;
            }
        """)
        self.card_intel.layout().addWidget(self.progress_intel)

        # Tarjeta 2: Riesgo Ambiental (Red #2)
        self.card_risk = self._create_metric_card("Riesgo Red #2", "0.0%", "🛡️", "#10b981")

        # Tarjeta 3: Pérdida MSE (Red #1)
        self.card_loss = self._create_metric_card("Error MSE", "1.0000", "🎯", "#3b82f6")

        # Tarjeta 4: Predicción Temperatura (+5m)
        self.card_pred_temp = self._create_metric_card("Temp. Predicha (+5m)", "-- °C", "🔮", "#f59e0b")

        # Tarjeta 5: Predicción Humedad (+5m)
        self.card_pred_hum = self._create_metric_card("Hum. Predicha (+5m)", "-- %", "💧", "#06b6d4")

        cards_layout.addWidget(self.card_intel)
        cards_layout.addWidget(self.card_risk)
        cards_layout.addWidget(self.card_loss)
        cards_layout.addWidget(self.card_pred_temp)
        cards_layout.addWidget(self.card_pred_hum)

        # =====================================================================
        #  PANEL INFERIOR: GRÁFICAS DE CONVERGENCIA + ASISTENTE CONVERSACIONAL
        # =====================================================================
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        # Panel Izquierdo: Gráficas Predictivas y Convergencia
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Gráfica 1: Predicción en Vivo vs Datos Reales
        chart_pred_frame = QFrame()
        chart_pred_frame.setObjectName("cardFrame")
        chart_pred_v = QVBoxLayout(chart_pred_frame)
        chart_pred_v.setContentsMargins(10, 8, 10, 8)

        lbl_chart1 = QLabel("📈  PREDICCIÓN EN TIEMPO REAL (Temp. Real vs. Red Neuronal #1)")
        lbl_chart1.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_chart1.setStyleSheet("color: #94a3b8;")

        self.plot_predictions = pg.PlotWidget()
        self.plot_predictions.setBackground("#0b132b")
        self.plot_predictions.showGrid(x=True, y=True, alpha=0.3)
        self.plot_predictions.setLabel("left", "Temperatura (°C)")
        self.plot_predictions.setLabel("bottom", "Muestras")

        self.curve_real_temp = self.plot_predictions.plot(pen=pg.mkPen("#3b82f6", width=2), name="Temp. Real")
        self.curve_pred_temp = self.plot_predictions.plot(pen=pg.mkPen("#f59e0b", width=2, style=Qt.DashLine), name="Temp. Predicha (NN)")

        chart_pred_v.addWidget(lbl_chart1)
        chart_pred_v.addWidget(self.plot_predictions)

        # Gráfica 2: Curva de Aprendizaje Continuo (Pérdida MSE)
        chart_loss_frame = QFrame()
        chart_loss_frame.setObjectName("cardFrame")
        chart_loss_v = QVBoxLayout(chart_loss_frame)
        chart_loss_v.setContentsMargins(10, 8, 10, 8)

        lbl_chart2 = QLabel("📉  CURVA DE APRENDIZAJE CONTINUO (Evolución del Error MSE)")
        lbl_chart2.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_chart2.setStyleSheet("color: #94a3b8;")

        self.plot_loss = pg.PlotWidget()
        self.plot_loss.setBackground("#0b132b")
        self.plot_loss.showGrid(x=True, y=True, alpha=0.3)
        self.plot_loss.setLabel("left", "Pérdida MSE")
        self.plot_loss.setLabel("bottom", "Iteraciones")

        self.curve_loss = self.plot_loss.plot(pen=pg.mkPen("#10b981", width=2))

        chart_loss_v.addWidget(lbl_chart2)
        chart_loss_v.addWidget(self.plot_loss)

        left_layout.addWidget(chart_pred_frame, 3)
        left_layout.addWidget(chart_loss_frame, 2)

        # Panel Derecho: Asistente Conversacional & Consola IA con "Brazos"
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Consola Diagnóstica IA
        ai_chat_frame = QFrame()
        ai_chat_frame.setObjectName("tableContainer")
        ai_chat_v = QVBoxLayout(ai_chat_frame)
        ai_chat_v.setContentsMargins(10, 10, 10, 10)

        lbl_ai_header = QLabel("🤖  ASISTENTE CONVERSACIONAL QWEN2.5 (Memoria Chat & Brazos)")
        lbl_ai_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_ai_header.setStyleSheet("color: #ec4899;")

        self.txt_ai_console = QTextEdit()
        self.txt_ai_console.setReadOnly(True)
        self.txt_ai_console.setFont(QFont("Segoe UI", 9))
        self.txt_ai_console.setStyleSheet("""
            QTextEdit {
                background-color: #080c14;
                border: 1px solid #1e293b;
                color: #e2e8f0;
                padding: 8px;
            }
        """)

        # Entrada de prompt para el usuario
        chat_input_layout = QHBoxLayout()
        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText("Escriba su orden o continúe la conversación...")
        self.input_prompt.returnPressed.connect(self._handle_user_prompt)

        self.btn_send_prompt = QPushButton("Enviar u Ordenar")
        self.btn_send_prompt.setObjectName("primaryButton")
        self.btn_send_prompt.clicked.connect(self._handle_user_prompt)

        chat_input_layout.addWidget(self.input_prompt)
        chat_input_layout.addWidget(self.btn_send_prompt)

        # Botones de accesos rápidos a "BRAZOS" (Acciones Ejecutables)
        quick_ai_layout = QHBoxLayout()
        quick_ai_layout.setSpacing(6)

        btn_arm_pdf = QPushButton("📄 Generar PDF")
        btn_arm_pdf.clicked.connect(lambda: self._send_quick_query("Genera un reporte PDF completo"))

        btn_arm_excel = QPushButton("📊 Exportar Excel")
        btn_arm_excel.clicked.connect(lambda: self._send_quick_query("Exportar a Excel los datos actuales"))

        btn_arm_essay = QPushButton("📝 Redactar Ensayo")
        btn_arm_essay.clicked.connect(lambda: self._send_quick_query("Redacta un ensayo e informe técnico de investigación ambiental"))

        btn_arm_risk = QPushButton("🛡️ Analizar Riesgo (Red #2)")
        btn_arm_risk.clicked.connect(lambda: self._send_quick_query("¿Cuál es el estado de riesgo detectado por la Red Neuronal 2?"))

        quick_ai_layout.addWidget(btn_arm_pdf)
        quick_ai_layout.addWidget(btn_arm_excel)
        quick_ai_layout.addWidget(btn_arm_essay)
        quick_ai_layout.addWidget(btn_arm_risk)

        ai_chat_v.addWidget(lbl_ai_header)
        ai_chat_v.addWidget(self.txt_ai_console)
        ai_chat_v.addLayout(quick_ai_layout)
        ai_chat_v.addLayout(chat_input_layout)

        right_layout.addWidget(ai_chat_frame)

        splitter.addWidget(left_box)
        splitter.addWidget(right_box)
        splitter.setSizes([550, 400])

        # Integración al layout principal
        main_layout.addWidget(header_frame)
        main_layout.addLayout(cards_layout)
        main_layout.addWidget(splitter, 1)

        # Mensaje de bienvenida inicial en consola IA
        self._append_ai_msg(
            f"<b>[SISTEMA IA SIMA]</b> Asistente <b>Qwen2.5</b> inicializado con <b>Memoria Conversacional (Chat Multi-turno)</b> y 'Brazos' activos.<br>"
            f"• <b>Red Neuronal #1 (Predictor MLP):</b> Aprendizaje continuo activado.<br>"
            f"• <b>Red Neuronal #2 (Detector de Anomalías Autoencoder):</b> En línea.<br>"
            f"<i>Puedes dialogar fluidamente, hacer preguntas de seguimiento o pedir acciones como 'Genera un PDF', 'Exportar Excel' o 'Redacta un ensayo'.</i>"
        )

    def _create_metric_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(f"{icon} {title}")
        lbl_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_title.setStyleSheet("color: #94a3b8;")

        lbl_val = QLabel(value)
        lbl_val.setObjectName("cardValLabel")
        lbl_val.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return card

    @Slot(float, float)
    def update_live_data(self, temp: float, hum: float) -> None:
        """Slot llamado cada vez que llega una nueva lectura de sensores."""
        # 1. Entrenar Red Neuronal #1 (Predictor)
        train_res = self.nn_manager.add_sample_and_train_online(temp, hum)

        # 2. Entrenar y Analizar Red Neuronal #2 (Detector de Anomalías)
        anomaly_res = self.anomaly_nn.analyze_sample(temp, hum)

        # Actualizar historiales de visualización
        self.history_real_temp.append(temp)
        self.history_real_hum.append(hum)
        if len(self.history_real_temp) > 100:
            self.history_real_temp.pop(0)
            self.history_real_hum.pop(0)

        pred_next = train_res.get("prediction_next")
        if pred_next:
            self.history_pred_temp.append(pred_next["temp"])
            self.history_pred_hum.append(pred_next["hum"])
            if len(self.history_pred_temp) > 100:
                self.history_pred_temp.pop(0)
                self.history_pred_hum.pop(0)

        # Refrescar interfaz visual
        self._update_display(train_res, anomaly_res)

    def _update_display(
        self,
        train_res: Optional[Dict[str, Any]] = None,
        anomaly_res: Optional[Dict[str, Any]] = None
    ) -> None:
        """Actualiza tarjetas, progresos y gráficas con el estado actual de las dos redes."""
        intel_info = self.nn_manager.get_intelligence_level()
        anomaly_info = self.anomaly_nn.get_summary()

        # Actualizar Tarjetas Red #1
        intel_pct = intel_info["intelligence_percentage"]
        self.progress_intel.setValue(int(intel_pct))
        self.card_intel.findChild(QLabel, "cardValLabel").setText(f"{intel_pct}%")

        self.card_loss.findChild(QLabel, "cardValLabel").setText(
            f"{self.nn_manager.current_loss:.5f}"
        )

        # Actualizar Tarjeta Red #2 (Riesgo / Anomalías)
        risk_pct = anomaly_info["risk_percentage"]
        risk_color = "#10b981" if risk_pct < 30.0 else ("#f59e0b" if risk_pct < 70.0 else "#ef4444")
        self.card_risk.findChild(QLabel, "cardValLabel").setText(f"{risk_pct}%")
        self.card_risk.findChild(QLabel, "cardValLabel").setStyleSheet(f"color: {risk_color};")

        pred_future = train_res.get("prediction_future") if train_res else None
        if not pred_future:
            _, pred_future = self.nn_manager.predict_future()

        if pred_future:
            self.card_pred_temp.findChild(QLabel, "cardValLabel").setText(f"{pred_future['temp']} °C")
            self.card_pred_hum.findChild(QLabel, "cardValLabel").setText(f"{pred_future['hum']} %")
        else:
            self.card_pred_temp.findChild(QLabel, "cardValLabel").setText("Recopilando...")
            self.card_pred_hum.findChild(QLabel, "cardValLabel").setText("Recopilando...")

        # Actualizar Gráfica de Predicciones vs Realidad
        if self.history_real_temp:
            self.curve_real_temp.setData(self.history_real_temp)
            if self.history_pred_temp:
                self.curve_pred_temp.setData(self.history_pred_temp)

        # Actualizar Gráfica de Pérdida
        if self.nn_manager.loss_history:
            self.curve_loss.setData(self.nn_manager.loss_history)

    def _manual_train_step(self) -> None:
        """Fuerza un paso adicional de entrenamiento en ambas redes."""
        if self.history_real_temp:
            last_t = self.history_real_temp[-1]
            last_h = self.history_real_hum[-1]
            res1 = self.nn_manager.add_sample_and_train_online(last_t, last_h)
            res2 = self.anomaly_nn.analyze_sample(last_t, last_h)
            self._update_display(res1, res2)
            self._append_ai_msg(
                f"<b>[ENTRENAMIENTO MANUAL DUAL]</b> Red #1 MSE: {self.nn_manager.current_loss:.6f} | Red #2 Riesgo: {res2['risk_percentage']}%"
            )
        else:
            QMessageBox.warning(self, "Atención", "Aún no se han recibido muestras de sensores para entrenar.")

    def _save_model(self) -> None:
        """Guarda ambas redes neuronales a disco."""
        ok1 = self.nn_manager.save_model()
        ok2 = self.anomaly_nn.save_model()
        if ok1 and ok2:
            QMessageBox.information(
                self, "Guardadoitosamente",
                f"Pesos de ambas Redes Neuronales guardados en <code>models/</code>."
            )
            self._append_ai_msg("<b>[SISTEMA NN]</b> Pesos de las Redes 1 y 2 guardados correctamente.")

    def _reset_model(self) -> None:
        """Resetea los pesos de ambas redes e historial de chat previa confirmación."""
        reply = QMessageBox.question(
            self, "Confirmar Reset",
            "¿Desea reiniciar los pesos de ambas redes neuronales y el historial de la conversación?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.nn_manager.reset_model()
            self.anomaly_nn = AnomalyNNManager()
            self.ai_agent.clear_conversation_history()
            self.history_real_temp.clear()
            self.history_pred_temp.clear()
            self.history_real_hum.clear()
            self.history_pred_hum.clear()
            self._update_display()
            self._append_ai_msg("<b>[SISTEMA NN]</b> Pesos de las redes e historial conversacional reiniciados a cero.")

    def _handle_user_prompt(self) -> None:
        """Procesa una orden o consulta ingresada por el usuario convocando al Agente de forma asíncrona."""
        prompt = self.input_prompt.text().strip()
        if not prompt:
            return
        self.input_prompt.clear()
        self._append_ai_msg(f"<b>[USUARIO]:</b> {prompt}")
        self._generate_ai_response(prompt)

    def _send_quick_query(self, query_type: str) -> None:
        """Procesa órdenes o accesos rápidos de botones."""
        self._append_ai_msg(f"<b>[ACCION RAPIDA DE BOTON]:</b> <i>{query_type}</i>")
        self._generate_ai_response(query_type)

    def _generate_ai_response(self, query: str) -> None:
        """Lanza un hilo secundario asíncrono para consultar la IA sin bloquear la interfaz."""
        if self.worker_thread and self.worker_thread.isRunning():
            self._append_ai_msg("<i>⏳ La IA está procesando la solicitud anterior, por favor espere un segundo...</i>")
            return

        curr_t = self.history_real_temp[-1] if self.history_real_temp else 22.0
        curr_h = self.history_real_hum[-1] if self.history_real_hum else 50.0

        nn1_summary = self.nn_manager.get_ai_agent_summary(curr_t, curr_h)
        nn2_summary = self.anomaly_nn.get_summary()

        self._append_ai_msg("<i>⏳ Pensando y analizando datos con Qwen2.5...</i>")

        # Crear y ejecutar el hilo asíncrono QThread
        self.worker_thread = AIWorkerThread(
            ai_agent=self.ai_agent,
            prompt=query,
            nn1_summary=nn1_summary,
            nn2_summary=nn2_summary,
            curr_t=curr_t,
            curr_h=curr_h
        )
        self.worker_thread.response_ready.connect(self._on_ai_response_received)
        self.worker_thread.start()

    @Slot(dict)
    def _on_ai_response_received(self, res: Dict[str, Any]) -> None:
        """Slot ejecutado cuando el hilo de la IA responde."""
        response_html = res.get("response", "")
        self._append_ai_msg(response_html)

    def _append_ai_msg(self, html_msg: str) -> None:
        """Añade un mensaje HTML formateado al panel de diálogo de la IA."""
        self.txt_ai_console.append(html_msg)
        self.txt_ai_console.append("")
        self.txt_ai_console.moveCursor(self.txt_ai_console.textCursor().MoveOperation.End)
