"""SIMA 2.0 — Ventana principal con interfaz HTML/CSS/JS.

La lógica existente de SIMA permanece en MainWindow. Esta clase solo sustituye
la capa visual Qt por un WebView y expone un puente Qt <-> JavaScript.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QStatusBar, QVBoxLayout, QWidget
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

from auth_manager import get_auth_manager
from gui.ai_chat_tab import AIWorkerThread, AIChatTabWidget
from gui.dashboard import DashboardWidget
from gui.mainwindow import MainWindow
from gui.widgets import LEDIndicator


class SIMAWebBridge(QObject):
    """API visual expuesta al frontend sin mover la lógica de negocio a JS."""

    state_changed = Signal(str)
    status_changed = Signal(str)
    ai_response = Signal(str)
    user_changed = Signal(str)
    log_event = Signal(str)

    def __init__(self, window: "WebMainWindow") -> None:
        super().__init__(window)
        self.window = window
        self._worker: Optional[AIWorkerThread] = None

    @Slot(result=str)
    def get_snapshot(self) -> str:
        return json.dumps(self.window._web_snapshot(), ensure_ascii=False)

    @Slot()
    def connect_serial(self) -> None:
        self.window._toggle_connection()
        self.window._emit_web_snapshot()

    @Slot()
    def toggle_demo(self) -> None:
        self.window._toggle_demo_mode()
        self.window._emit_web_snapshot()

    @Slot()
    def toggle_pause(self) -> None:
        self.window._toggle_pause()
        self.window._emit_web_snapshot()

    @Slot()
    def clear_data(self) -> None:
        self.window._clear_data()
        self.window._emit_web_snapshot()

    @Slot()
    def export_excel(self) -> None:
        self.window._export_excel()

    @Slot()
    def export_pdf(self) -> None:
        self.window._export_pdf()

    @Slot()
    def open_neural_network(self) -> None:
        self.window._open_protected_dev_panel()

    @Slot()
    def toggle_fullscreen(self) -> None:
        self.window._toggle_fullscreen()

    @Slot()
    def open_settings(self) -> None:
        self.window._open_settings()
        self.window._emit_web_snapshot()

    @Slot()
    def open_profile(self) -> None:
        self.window._open_user_profile()

    def _process_ai_prompt(self, prompt: str) -> dict:
        temp, hum = 24.0, 50.0
        if hasattr(self.window, "sensor_manager") and self.window.sensor_manager.last_reading:
            temp = self.window.sensor_manager.last_reading.temperature
            hum = self.window.sensor_manager.last_reading.humidity

        nn1, nn2 = {}, {}
        if hasattr(self.window, "nn_manager"):
            nn1 = self.window.nn_manager.get_ai_agent_summary(temp, hum)
        if hasattr(self.window, "anomaly_nn"):
            nn2 = self.window.anomaly_nn.get_summary()

        try:
            return self.window.ai_chat_tab.ai_agent.process_user_request(
                prompt=prompt,
                nn1_summary=nn1,
                nn2_summary=nn2,
                current_temp=temp,
                current_hum=hum,
            )
        except Exception as e:
            return {
                "response": f"Sistema operativo. Telemetría actual: <b>{temp:.1f} °C</b> / <b>{hum:.1f} % RH</b>.",
                "action_taken": None,
                "action_details": str(e),
                "expression_state": "HAPPY",
            }

    @Slot(str, result=str)
    def send_message_sync(self, prompt: str) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return json.dumps({"response": "Escribe un mensaje.", "expression_state": "NORMAL"}, ensure_ascii=False)
        self.send_message(prompt)
        return json.dumps({"response": "Procesando con Google Gemini...", "expression_state": "THINKING"}, ensure_ascii=False)

    @Slot(str)
    def send_message(self, prompt: str) -> None:
        prompt = (prompt or "").strip()
        if not prompt:
            return

        temp, hum = 24.0, 50.0
        if hasattr(self.window, "sensor_manager") and self.window.sensor_manager.last_reading:
            temp = self.window.sensor_manager.last_reading.temperature
            hum = self.window.sensor_manager.last_reading.humidity

        nn1, nn2 = {}, {}
        if hasattr(self.window, "nn_manager"):
            nn1 = self.window.nn_manager.get_ai_agent_summary(temp, hum)
        if hasattr(self.window, "anomaly_nn"):
            nn2 = self.window.anomaly_nn.get_summary()

        ai_agent = self.window.ai_chat_tab.ai_agent

        # Cancelar cualquier worker anterior para evitar conflictos de hilos concurrentes
        if self._worker and self._worker.isRunning():
            try:
                self._worker.terminate()
                self._worker.wait()
            except Exception:
                pass

        # Crear e iniciar hilo asíncrono para no bloquear la interfaz GUI
        worker = AIWorkerThread(ai_agent, prompt, nn1, nn2, temp, hum, parent=self)
        worker.response_ready.connect(self._on_worker_response)
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        worker.start()

    def _on_worker_response(self, res_dict: dict) -> None:
        self.ai_response.emit(json.dumps(res_dict, ensure_ascii=False))

    @Slot()
    def reset_chat(self) -> None:
        self.window.ai_chat_tab.ai_agent.clear_conversation_history()

    @Slot(str)
    def quick_action(self, prompt: str) -> None:
        self.send_message(prompt)

    @Slot()
    def request_refresh(self) -> None:
        self.window._emit_web_snapshot()

    def _on_ai_response(self, response: dict) -> None:
        self.ai_response.emit(json.dumps(response, ensure_ascii=False))


class WebMainWindow(MainWindow):
    """MainWindow compatible que usa HTML/CSS/JS como interfaz visual."""

    def _init_ui(self) -> None:
        self.setWindowTitle("SIMA — Sistema Inteligente de Monitoreo Ambiental")
        self.resize(1440, 920)
        self.setMinimumSize(1050, 700)

        # Compatibilidad con los controladores existentes: estos widgets no se muestran.
        self.dashboard = DashboardWidget(self)
        self.dashboard.hide()
        self.ai_chat_tab = AIChatTabWidget(main_window=self, parent=self)
        self.ai_chat_tab.hide()

        self.btn_connect = QPushButton(self)
        self.btn_connect.setText("Conectar Serial")
        self.btn_demo = QPushButton(self)
        self.btn_demo.setText("Modo Demo")
        self.btn_pause = QPushButton(self)
        self.btn_pause.setText("Pausar Tiempo")
        self.btn_clear = QPushButton(self)
        self.btn_clear.setText("Limpiar Datos")
        self.btn_excel = QPushButton(self)
        self.btn_excel.setText("Exportar Excel")
        self.btn_pdf = QPushButton(self)
        self.btn_pdf.setText("Generar Reporte")
        self.btn_dev_nn = QPushButton(self)
        self.btn_dev_nn.setText("Red Neuronal")
        self.btn_fullscreen = QPushButton(self)
        self.btn_fullscreen.setText("Restaurar Ventana")
        self.btn_settings = QPushButton(self)
        self.btn_settings.setText("Ajustes")
        self.btn_user_profile = QPushButton(self)
        self.btn_user_profile.setText("Administrador")
        for widget in (
            self.btn_connect, self.btn_demo, self.btn_pause, self.btn_clear,
            self.btn_excel, self.btn_pdf, self.btn_dev_nn, self.btn_fullscreen,
            self.btn_settings, self.btn_user_profile,
        ):
            widget.hide()

        self.led_status = LEDIndicator(self, size=10)
        self.led_status.hide()
        self.label_serial_status = QLabel("● Desconectado", self)
        self.label_serial_status.hide()

        self.auth_mgr = get_auth_manager()

        self.status_bar = QStatusBar(self)
        self.status_bar_label_port = QLabel("", self)
        self.status_bar_label_info = QLabel("SIMA 2.0", self)
        self.status_bar.addWidget(self.status_bar_label_port)
        self.status_bar.addPermanentWidget(self.status_bar_label_info)
        self.setStatusBar(self.status_bar)
        self.status_bar.hide()

        host = QWidget(self)
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)

        self.web_view = QWebEngineView(host)
        host_layout.addWidget(self.web_view)
        self.setCentralWidget(host)

        self.web_bridge = SIMAWebBridge(self)
        self.web_channel = QWebChannel(self)
        self.web_channel.registerObject("bridge", self.web_bridge)
        self.web_view.page().setWebChannel(self.web_channel)
        self.web_view.loadFinished.connect(self._on_web_loaded)

        html_path = Path(__file__).resolve().parent.parent / "web" / "index.html"
        self.web_view.setUrl(QUrl.fromLocalFile(str(html_path.resolve())))

    def _on_web_loaded(self, ok: bool) -> None:
        if ok:
            self._emit_web_snapshot()

    def _web_snapshot(self) -> dict:
        reading = self.sensor_manager.last_reading
        stats = self.stats_manager.get_stats()
        connected = bool(self.serial_thread.is_connected)
        demo = bool(self.demo_timer.isActive())
        paused = self.btn_pause.text() == "Reanudar Tiempo"
        user = self.auth_mgr.get_current_user()

        return {
            "temperature": round(reading.temperature, 1) if reading else None,
            "humidity": round(reading.humidity, 1) if reading else None,
            "light": round(reading.light, 1) if reading else None,
            "temp_status": reading.temp_class.label if reading else "Sin lectura",
            "temp_color": reading.temp_class.color if reading else "#969890",
            "hum_status": reading.hum_class.label if reading else "Sin lectura",
            "hum_color": reading.hum_class.color if reading else "#969890",
            "comfort": round(reading.comfort.score, 0) if reading else None,
            "comfort_status": reading.comfort.label if reading else "Sin lectura",
            "sample_count": stats.get("sample_count", 0),
            "port": self.serial_thread.port,
            "baudrate": self.serial_thread.baudrate,
            "connected": connected,
            "demo": demo,
            "paused": paused,
            "user": user.get("full_name", user.get("username")) if user else None,
        }

    def _emit_web_snapshot(self) -> None:
        if hasattr(self, "web_bridge"):
            payload = json.dumps(self._web_snapshot(), ensure_ascii=False)
            self.web_bridge.state_changed.emit(payload)
            self.status_bar_label_port.setText(
                f"Puerto: {self.serial_thread.port} | Baudios: {self.serial_thread.baudrate}"
            )

    @Slot(float, float, float)
    def _handle_new_data(self, temp: float, hum: float, light: float = 400.0) -> None:
        super()._handle_new_data(temp, hum, light)
        self._emit_web_snapshot()

    @Slot(bool)
    def _handle_connection_change(self, is_connected: bool) -> None:
        super()._handle_connection_change(is_connected)
        self._emit_web_snapshot()

    @Slot(str)
    def _handle_serial_error(self, error_msg: str) -> None:
        super()._handle_serial_error(error_msg)
        self._emit_web_snapshot()

    @Slot(str)
    def _handle_arduino_status(self, status: str) -> None:
        super()._handle_arduino_status(status)
        self._emit_web_snapshot()

    def _update_user_badge(self, *args) -> None:
        super()._update_user_badge(*args)
        if hasattr(self, "web_bridge"):
            self.web_bridge.user_changed.emit(
                json.dumps(self._web_snapshot(), ensure_ascii=False)
            )
