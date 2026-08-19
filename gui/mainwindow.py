"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Ventana Principal de la Aplicación (gui/mainwindow.py) — v6 Muestreo Inmediato & Gráficas Vivas

Garantiza que la interfaz inicie con datos y gráficas animadas activas desde el primer segundo.

Autor:  Equipo SIMA — Arquitecto de Software
Fecha:  2026-08-09
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QTabWidget, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from config import APP_NAME, APP_FULL_NAME
from sensor_manager import SensorManager
from statistics_manager import StatisticsManager
from settings_manager import SettingsManager
from nn_predictor import NNPredictorManager
from anomaly_nn import AnomalyNNManager
from serial_reader import SerialReader

from gui.dashboard import DashboardWidget
from gui.ai_chat_tab import AIChatTabWidget
from gui.dialogs import SettingsDialog, PINVerificationDialog, DevNNWindow
from gui.login_dialog import LoginRegisterDialog
from gui.profile_dialog import UserProfileDialog
from auth_manager import get_auth_manager
from logger_manager import get_logger, log_exception

logger = get_logger("gui.mainwindow")


class MainWindow(QMainWindow):
    """Ventana principal que gestiona todas las vistas y componentes de SIMA."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # 1. Componentes del Modelo Backend
        self.settings: SettingsManager = SettingsManager()
        self.sensor_manager: SensorManager = SensorManager()
        self.stats_manager: StatisticsManager = StatisticsManager()
        self.nn_manager: NNPredictorManager = NNPredictorManager()
        self.anomaly_nn: AnomalyNNManager = AnomalyNNManager()

        # 2. Inicializar Hilo Serial
        self.serial_thread: SerialReader = SerialReader()
        self.serial_thread.configure(
            port=self.settings.get("serial_port"),
            baudrate=self.settings.get("serial_baudrate")
        )

        # 3. Timer de Simulación Demo (Muestras cada 2 segundos)
        self._sim_step: int = 0
        self.demo_timer: QTimer = QTimer(self)
        self.demo_timer.setInterval(2000)
        self.demo_timer.timeout.connect(self._generate_demo_sample)

        # Referencia a la ventana de Red Neuronal protegida
        self.dev_nn_window = None

        # 4. Inicializar UI y Conexiones
        self._init_ui()
        self._connect_signals()
        self._apply_theme()

        # 5. Inicializar en modo Standby Desconectado (Esperando selección del usuario)
        self.led_status.set_state("disconnected")
        self.label_serial_status.setText("Desconectado (Elige Conectar Serial o Modo Demo)")
        self.label_serial_status.setStyleSheet("color: #94a3b8;")
        self.btn_pause.setEnabled(False)

        logger.info("Ventana principal cargada en modo Standby esperando selección")

    def _init_ui(self) -> None:
        """Construye la interfaz visual Botanical Dark Luxury."""
        self.setWindowTitle(f"{APP_NAME} — {APP_FULL_NAME}")
        self.resize(1340, 860)
        self.setMinimumSize(1240, 760)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 8, 10, 6)
        main_layout.setSpacing(8)

        # ═══════════════════════════════════════════════════
        #  BARRA DE CONTROL SUPERIOR — Botanical Dark Toolbar
        # ═══════════════════════════════════════════════════
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(14,22,16,250), stop:1 rgba(10,15,12,250));
                border: 1px solid #1e3025;
                border-radius: 10px;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 7, 10, 7)
        tb_layout.setSpacing(5)

        # Logo SIMA
        logo = QLabel("🌿")
        logo.setFont(QFont("Segoe UI Emoji", 16))
        logo.setFixedSize(34, 34)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            background: #111a14;
            border: 1px solid #2d6b44;
            border-radius: 8px;
        """)
        tb_layout.addWidget(logo)
        tb_layout.addSpacing(6)

        # Estilos de botones pill según imagen #3 (Beige y Oliva)
        pill_olive = """
            QPushButton {
                background: #6f7e5d; color: #f2f0e8;
                border: 1px solid #82936b;
                border-radius: 16px; padding: 7px 16px;
                font-weight: 600; font-size: 11px;
            }
            QPushButton:hover {
                background: #82936b; color: #ffffff; border-color: #a5b98a;
            }
            QPushButton:pressed { background: #5c6a4c; }
        """
        pill_beige = """
            QPushButton {
                background: #242822; color: #c8c7be;
                border: 1px solid #30372c;
                border-radius: 16px; padding: 7px 16px;
                font-weight: 600; font-size: 11px;
            }
            QPushButton:hover {
                background: #30372c; color: #f2f0e8; border-color: #6f7e5d;
            }
            QPushButton:pressed { background: #1e221c; }
        """

        # Botones de control
        self.btn_connect = QPushButton("Conectar Serie")
        self.btn_connect.setStyleSheet(pill_olive)
        self.btn_connect.clicked.connect(self._toggle_connection)

        self.btn_demo = QPushButton("Modo Demo")
        self.btn_demo.setStyleSheet(pill_beige)
        self.btn_demo.clicked.connect(self._toggle_demo_mode)

        self.btn_pause = QPushButton("Pausar Tiempo")
        self.btn_pause.setStyleSheet(pill_beige)
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_pause.setEnabled(True)

        self.btn_clear = QPushButton("Limpiar Datos")
        self.btn_clear.setStyleSheet(pill_beige)
        self.btn_clear.clicked.connect(self._clear_data)

        # LED + Estado
        from gui.widgets import LEDIndicator
        self.led_status = LEDIndicator(self, size=10)

        self.label_serial_status = QLabel("● Desconectado")
        self.label_serial_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.label_serial_status.setStyleSheet("color: #c45c5c; background: #252a23; padding: 5px 12px; border-radius: 10px; border: 1px solid #3a4236;")

        # Exportación y herramientas
        self.btn_excel = QPushButton("Exportar Excel")
        self.btn_excel.setStyleSheet(pill_beige)
        self.btn_excel.clicked.connect(self._export_excel)

        self.btn_pdf = QPushButton("Generar Reporte")
        self.btn_pdf.setStyleSheet(pill_beige)
        self.btn_pdf.clicked.connect(self._export_pdf)

        self.btn_dev_nn = QPushButton("🌿 Red Neuronal")
        self.btn_dev_nn.setStyleSheet(pill_beige)
        self.btn_dev_nn.clicked.connect(self._open_protected_dev_panel)

        self.btn_fullscreen = QPushButton("Restaurar Ventana")
        self.btn_fullscreen.setStyleSheet(pill_beige)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)

        self.btn_settings = QPushButton("⚙️ Ajustes")
        self.btn_settings.setStyleSheet(pill_beige)
        self.btn_settings.clicked.connect(self._open_settings)

        # Perfil de usuario
        self.auth_mgr = get_auth_manager()
        self.btn_user_profile = QPushButton("👤 Administrador ∨")
        self.btn_user_profile.setStyleSheet(pill_olive)
        self.btn_user_profile.clicked.connect(self._open_user_profile)
        self._update_user_badge()

        # Ensamblar toolbar
        for btn in [self.btn_connect, self.btn_demo, self.btn_pause, self.btn_clear]:
            tb_layout.addWidget(btn)
        tb_layout.addSpacing(6)
        tb_layout.addWidget(self.led_status)
        tb_layout.addWidget(self.label_serial_status)
        tb_layout.addStretch()
        for btn in [self.btn_excel, self.btn_pdf, self.btn_dev_nn,
                    self.btn_fullscreen, self.btn_settings, self.btn_user_profile]:
            tb_layout.addWidget(btn)

        # ═══════════════════════════════════════════════════
        #  PESTAÑAS PRINCIPALES
        # ═══════════════════════════════════════════════════
        self.tab_widget = QTabWidget(self)

        self.dashboard = DashboardWidget(self)
        self.tab_widget.addTab(self.dashboard, "🌿  Monitoreo Principal")

        self.ai_chat_tab = AIChatTabWidget(main_window=self, parent=self)
        self.tab_widget.addTab(self.ai_chat_tab, "💬  Asistente IA - Conversación")

        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.tab_widget, 1)

        # ═══════════════════════════════════════════════════
        #  BARRA DE ESTADO INFERIOR
        # ═══════════════════════════════════════════════════
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.status_bar_label_port = QLabel(f"Puerto: {self.serial_thread.port} | Baudios: {self.serial_thread.baudrate}")
        self.status_bar_label_info = QLabel("SIMA v2.0 Activo — Monitoreo dinámico en tiempo real.")

        self.status_bar.addWidget(self.status_bar_label_port)
        self.status_bar.addPermanentWidget(self.status_bar_label_info)

        # Atajo F11 para Pantalla Completa
        self.shortcut_fullscreen = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.shortcut_fullscreen.activated.connect(self._toggle_fullscreen)

    def _seed_initial_data(self) -> None:
        """Puebla lecturas dinámicas iniciales al activar el modo demo."""
        import math, random
        for _ in range(10):
            self._sim_step += 1
            t_base = 24.2 + 1.2 * math.sin(self._sim_step * 0.1) + random.uniform(-0.1, 0.1)
            h_base = 52.0 + 2.5 * math.cos(self._sim_step * 0.08) + random.uniform(-0.2, 0.2)
            self._handle_new_data(round(t_base, 1), round(h_base, 1))

    def _connect_signals(self) -> None:
        """Enlaza las señales del hilo serial y autenticación a los slots de la UI."""
        self.serial_thread.new_data.connect(self._handle_new_data)
        self.serial_thread.connection_changed.connect(self._handle_connection_change)
        self.serial_thread.error_occurred.connect(self._handle_serial_error)
        self.serial_thread.status_received.connect(self._handle_arduino_status)

        # Conectar gestor de usuarios/sesiones
        self.auth_mgr.user_logged_in.connect(self._update_user_badge)
        self.auth_mgr.user_logged_out.connect(self._update_user_badge)
        self.auth_mgr.profile_updated.connect(self._update_user_badge)

    def _update_user_badge(self, *args) -> None:
        """Actualiza el texto y color del botón del perfil según el usuario activo."""
        user = self.auth_mgr.get_current_user()
        if user:
            name = user.get("full_name", user.get("username"))
            role = user.get("role", "op").upper()
            self.btn_user_profile.setText(f"👤 {name} ({role})")
        else:
            self.btn_user_profile.setText("🔑 Iniciar Sesión")

    def _open_user_profile(self) -> None:
        """Abre el diálogo de perfil o inicio de sesión según el estado del usuario."""
        user = self.auth_mgr.get_current_user()
        if user:
            dlg = UserProfileDialog(self)
            dlg.exec()
        else:
            dlg = LoginRegisterDialog(self)
            dlg.exec()

    def _apply_theme(self) -> None:
        """Carga y aplica la hoja de estilos QSS pastel."""
        theme = self.settings.get("theme", "dark")
        qss_path = Path("styles") / f"{theme}.qss"

        if qss_path.exists():
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                log_exception(e, "Error al cargar la hoja de estilos QSS")

    def _toggle_fullscreen(self) -> None:
        """Alterna el modo de pantalla completa."""
        if self.isFullScreen():
            self.showNormal()
            self.btn_fullscreen.setText("🖥️ Pantalla Completa")
        else:
            self.showFullScreen()
            self.btn_fullscreen.setText("🗗 Restaurar Ventana")

    def _open_protected_dev_panel(self) -> None:
        """Solicita el PIN para abrir la ventana modal del panel Dev NN."""
        pin_dialog = PINVerificationDialog(self)
        if pin_dialog.exec() == PINVerificationDialog.Accepted:
            self.dev_nn_window = DevNNWindow(self.nn_manager, self.anomaly_nn, parent=self)
            self.dev_nn_window.show()

    # =====================================================================
    #  SLOTS / CONTROLADORES DE EVENTOS
    # =====================================================================

    @Slot(float, float, float)
    def _handle_new_data(self, temp: float, hum: float, light: float = 400.0) -> None:
        """Procesa una nueva lectura e instruye el refresco de los widgets."""
        reading = self.sensor_manager.add_reading(temp, hum, light)
        self.stats_manager.update(temp, hum)

        # Entrenar / evaluar redes neuronales en línea
        self.nn_manager.add_sample_and_train_online(temp, hum)
        self.anomaly_nn.analyze_sample(temp, hum)

        # Dashboard: Tarjetas e Indicadores
        self.dashboard.card_temp.update_value(
            temp, reading.temp_class.label, reading.temp_class.color
        )
        self.dashboard.card_hum.update_value(
            hum, reading.hum_class.label, reading.hum_class.color
        )
        self.dashboard.card_comfort.update_value(
            reading.comfort.score, reading.comfort.label, reading.comfort.color
        )

        self.dashboard.gauge_temp.update_value(temp, reading.temp_class.color)
        self.dashboard.gauge_hum.update_value(hum, reading.hum_class.color)

        # Gráficas pyqtgraph en tiempo real
        temps_array, hums_array, _, _ = self.sensor_manager.get_recent_arrays()
        self.dashboard.chart_temp.update_data(temps_array)
        self.dashboard.chart_hum.update_data(hums_array)

        # Tabla de mediciones
        self.dashboard.table_widget.add_measurement(
            time_str=reading.timestamp_str,
            temp=temp,
            hum=hum,
            temp_status=reading.temp_class.label,
            temp_color=reading.temp_class.color,
            hum_status=reading.hum_class.label,
            hum_color=reading.hum_class.color,
            comfort_score=reading.comfort.score,
            comfort_status=reading.comfort.label,
            comfort_color=reading.comfort.color
        )

        # Enviar registro a la bitácora visual de Log
        sample_num = self.stats_manager.get_stats()['sample_count']
        self.dashboard.log_message(
            f'Muestra #{sample_num}: Temp <b style="color:#7dd3fc;">{temp:.1f} °C</b> | '
            f'Hum <b style="color:#6ee7b7;">{hum:.1f} %</b> (Confort: {reading.comfort.score:.0f} pts)'
        )

        if self.dev_nn_window and self.dev_nn_window.isVisible():
            self.dev_nn_window.update_live_data(temp, hum)

        # Alertas Proactivas de la IA en el Chat Tab
        if hasattr(self, "ai_chat_tab"):
            user_name = self.ai_chat_tab.ai_agent.get_user_name()
            if temp > 28.5 and not getattr(self, "_alert_temp_high", False):
                self._alert_temp_high = True
                self.ai_chat_tab.add_proactive_alert(
                    f"¡Atención {user_name}! La temperatura ha superado los <b>{temp:.1f} °C</b>. He ajustado mi estado visual a Advertencia para vigilar el instrumental.",
                    "warn"
                )
            elif temp <= 28.0:
                self._alert_temp_high = False

        self.status_bar_label_info.setText(
            f"Último dato: {reading.timestamp_str} | Muestras: {self.stats_manager.get_stats()['sample_count']} | Red Neuronal: Activa"
        )

    @Slot(bool)
    def _handle_connection_change(self, is_connected: bool) -> None:
        """Refleja los cambios de conexión serial en el estado visual de la UI."""
        if is_connected:
            self.demo_timer.stop()
            self.btn_demo.setText("Modo Demo")
            self.btn_demo.setStyleSheet("background: #1a3524; color: #4ade80; border: 1px solid #2d5a3a; border-radius: 7px; padding: 6px 13px; font-weight: 600; font-size: 11px;")

            self.led_status.set_state("connected")
            self.label_serial_status.setText("● Conectado (Hardware)")
            self.label_serial_status.setStyleSheet("color: #10b981;")
            self.btn_connect.setText("Desconectar")
            self.btn_connect.setObjectName("dangerButton")
            self.btn_pause.setEnabled(True)
            self.stats_manager.start()
            self._apply_theme()
        else:
            self.led_status.set_state("disconnected")
            self.label_serial_status.setText("● Desconectado")
            self.label_serial_status.setStyleSheet("color: #ef4444;")
            self.btn_connect.setText("Conectar Serial")
            self.btn_connect.setObjectName("primaryButton")
            self.btn_pause.setEnabled(False)
            self.stats_manager.pause()
            self._apply_theme()

    def _toggle_demo_mode(self) -> None:
        """Activa o desactiva la simulación gráfica de demostración en tiempo real."""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
            self.btn_demo.setText("Modo Demo")
            self.btn_demo.setStyleSheet("background: #1a3524; color: #4ade80; border: 1px solid #2d5a3a; border-radius: 7px; padding: 6px 13px; font-weight: 600; font-size: 11px;")
            self.label_serial_status.setText("● Desconectado")
            self.label_serial_status.setStyleSheet("color: #ef4444;")
            self.led_status.set_state("disconnected")
            self.dashboard.log_message("Simulación Demo detenida por el usuario.")
        else:
            if self.serial_thread.is_connected:
                self.serial_thread.stop()
            if self._sim_step == 0:
                self._seed_initial_data()
            self.demo_timer.start()
            self.btn_demo.setText("⏹️ Detener Demo")
            self.btn_demo.setStyleSheet("background: #2d6b44; color: #e8f5e9; border: 1px solid #4ade80; border-radius: 7px; padding: 6px 13px; font-weight: 600; font-size: 11px;")
            self.label_serial_status.setText("● Simulación Demo (Activa)")
            self.label_serial_status.setStyleSheet("color: #4ade80;")
            self.led_status.set_state("stabilizing")
            self.btn_pause.setEnabled(True)
            self.stats_manager.start()
            self.dashboard.log_message("Simulación Demo iniciada por el usuario (Muestreo cada 2s).")

    def _generate_demo_sample(self) -> None:
        """Genera muestras dinámicas suaves para mover las gráficas en tiempo real."""
        import math, random
        self._sim_step += 1
        t_base = 24.2 + 1.5 * math.sin(self._sim_step * 0.1) + random.uniform(-0.15, 0.15)
        h_base = 52.0 + 3.0 * math.cos(self._sim_step * 0.08) + random.uniform(-0.3, 0.3)
        self._handle_new_data(round(t_base, 1), round(h_base, 1))

    @Slot(str)
    def _handle_serial_error(self, error_msg: str) -> None:
        self.status_bar_label_info.setText(f"Puerto Serial: {error_msg}")
        self._handle_connection_change(False)

    @Slot(str)
    def _handle_arduino_status(self, status: str) -> None:
        if "DHT" in status:
            self.led_status.set_state("stabilizing")
            self.label_serial_status.setText("Estabilizando")
            self.label_serial_status.setStyleSheet("color: #f59e0b;")

    def _toggle_connection(self) -> None:
        if self.serial_thread.is_connected:
            self.serial_thread.stop()
        else:
            if self.demo_timer.isActive():
                self.demo_timer.stop()
                self.btn_demo.setText("Modo Demo")

            # Detectar puertos USB o ACM disponibles
            available_ports = SerialReader.list_available_ports()
            usb_ports = [p for p in available_ports if "USB" in p or "ACM" in p]
            target_port = usb_ports[0] if usb_ports else self.settings.get("serial_port")

            self.serial_thread.configure(
                port=target_port,
                baudrate=self.settings.get("serial_baudrate")
            )
            self.serial_thread.start()
            self.status_bar_label_info.setText(f"Intentando conectar al puerto hardware {target_port}...")

    def _toggle_pause(self) -> None:
        if self.btn_pause.text() == "Pausar Tiempo":
            self.stats_manager.pause()
            if self.demo_timer.isActive():
                self.demo_timer.stop()
            self.btn_pause.setText("Reanudar Tiempo")
        else:
            self.stats_manager.start()
            if self.label_serial_status.text() == "Simulación Demo (Activa)":
                self.demo_timer.start()
            self.btn_pause.setText("Pausar Tiempo")

    def _clear_data(self) -> None:
        if self.sensor_manager.get_reading_count() > 0:
            reply = QMessageBox.question(
                self, "Confirmar Limpieza",
                "¿Desea limpiar el historial de lecturas registradas?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.sensor_manager.clear()
        self.stats_manager.reset()
        self.dashboard.table_widget.clear_table()
        self.dashboard.chart_temp.clear_plot()
        self.dashboard.chart_hum.clear_plot()
        self.status_bar_label_info.setText("Historial limpiado.")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.Accepted:
            self._apply_theme()
            self.status_bar_label_port.setText(
                f"Puerto: {self.settings.get('serial_port')} | Baudios: {self.settings.get('serial_baudrate')}"
            )

    def _export_excel(self) -> None:
        readings = self.sensor_manager.get_all_readings()
        if not readings:
            QMessageBox.warning(self, "Exportación fallida", "No hay datos registrados para exportar.")
            return
        try:
            from report_generator import generate_excel_report
            filepath = generate_excel_report(readings)
            QMessageBox.information(self, "Éxito", f"Hoja de Excel guardada en:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar Excel: {str(e)}")

    def _export_pdf(self) -> None:
        readings = self.sensor_manager.get_all_readings()
        if not readings:
            QMessageBox.warning(self, "Exportación fallida", "No hay datos registrados para exportar.")
            return
        try:
            from report_generator import generate_pdf_report
            stats = self.stats_manager.get_stats()
            filepath = generate_pdf_report(readings, stats)
            QMessageBox.information(self, "Éxito", f"Reporte PDF guardado en:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar PDF: {str(e)}")
