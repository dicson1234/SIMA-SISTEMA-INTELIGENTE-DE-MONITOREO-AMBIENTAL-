"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Diálogos de la Interfaz (gui/dialogs.py)

Implementa la ventana modal de configuración (SettingsDialog), el diálogo de
verificación de PIN de seguridad (PINVerificationDialog) y la ventana modal
del Panel de Redes Neuronales (DevNNWindow).

Autor:  Equipo SIMA — Diseñador UX/UI
Fecha:  2026-08-09
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QFormLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from settings_manager import SettingsManager
from serial_reader import SerialReader


class PINVerificationDialog(QDialog):
    """Diálogo modal de autenticación con clave/PIN para el panel de desarrollador."""

    VALID_PINS = ["0406", "040620047"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("🔐 Acceso Restringido — Panel Desarrollador")
        self.setModal(True)
        self.resize(380, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("🔒  ÁREA DE PROGRAMADOR / DEV")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_title.setStyleSheet("color: #c084fc;")

        lbl_desc = QLabel("Ingrese la contraseña de 4 dígitos o PIN de programador para acceder a los pesos e hiperparámetros de las Redes Neuronales:")
        lbl_desc.setWordWrap(True)
        lbl_desc.setFont(QFont("Segoe UI", 9))
        lbl_desc.setStyleSheet("color: #94a3b8;")

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.Password)
        self.txt_pin.setPlaceholderText("Clave / PIN (Ej. 0406)...")
        self.txt_pin.setFont(QFont("Segoe UI", 11))
        self.txt_pin.returnPressed.connect(self._verify_pin)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_ok = QPushButton("Verificar Acceso")
        btn_ok.setObjectName("primaryButton")
        btn_ok.clicked.connect(self._verify_pin)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(self.txt_pin)
        layout.addLayout(btn_box)

    def _verify_pin(self) -> None:
        entered = self.txt_pin.text().strip()
        if entered in self.VALID_PINS:
            self.accept()
        else:
            QMessageBox.warning(
                self, "Acceso Denegado",
                "PIN o contraseña incorrecta. El acceso al panel de diagnóstico está restringido."
            )
            self.txt_pin.clear()


class DevNNWindow(QDialog):
    """Ventana modal independiente del Panel de Diagnóstico de Redes Neuronales (Área Dev)."""

    def __init__(self, nn_manager, anomaly_nn, parent=None) -> None:
        super().__init__(parent)
        self.nn_manager = nn_manager
        self.anomaly_nn = anomaly_nn
        self._init_ui()

    def _init_ui(self) -> None:
        from gui.dev_nn_tab import DevNNTabWidget

        self.setWindowTitle("🛠️ Panel Avanzado de Redes Neuronales & Diagnóstico Dev")
        self.resize(1000, 680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.dev_tab = DevNNTabWidget(self.nn_manager, self.anomaly_nn, parent=self)
        layout.addWidget(self.dev_tab)

    def update_live_data(self, temp: float, hum: float) -> None:
        self.dev_tab.update_live_data(temp, hum)


class SettingsDialog(QDialog):
    """Diálogo de configuración interactivo con acceso seguro al área Dev."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.settings: SettingsManager = SettingsManager()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Configuración del Sistema SIMA")
        self.setModal(True)
        self.resize(480, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_title = QLabel("⚙️  CONFIGURACIÓN & AJUSTES DE SISTEMA")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_title.setStyleSheet("color: #7dd3fc;")

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.combo_port = QComboBox()
        available_ports = SerialReader.list_available_ports()
        self.combo_port.addItems(available_ports)

        current_port = self.settings.get("serial_port")
        if current_port in available_ports:
            self.combo_port.setCurrentText(current_port)
        elif current_port:
            self.combo_port.addItem(current_port)
            self.combo_port.setCurrentText(current_port)

        form_layout.addRow("Puerto Serial:", self.combo_port)

        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["300", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.combo_baud.setCurrentText(str(self.settings.get("serial_baudrate")))
        form_layout.addRow("Velocidad (Baudios):", self.combo_baud)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["dark", "light"])
        self.combo_theme.setCurrentText(self.settings.get("theme"))
        form_layout.addRow("Tema de Interfaz:", self.combo_theme)

        self.layout_excel_dir = QHBoxLayout()
        self.label_excel_dir = QLabel(self._truncate_path(self.settings.get("excel_directory")))
        self.btn_excel_browse = QPushButton("Explorar...")
        self.btn_excel_browse.clicked.connect(self._browse_excel_dir)
        self.layout_excel_dir.addWidget(self.label_excel_dir, 1)
        self.layout_excel_dir.addWidget(self.btn_excel_browse)
        form_layout.addRow("Guardar Excel en:", self.layout_excel_dir)

        self.layout_pdf_dir = QHBoxLayout()
        self.label_pdf_dir = QLabel(self._truncate_path(self.settings.get("reports_directory")))
        self.btn_pdf_browse = QPushButton("Explorar...")
        self.btn_pdf_browse.clicked.connect(self._browse_pdf_dir)
        self.layout_pdf_dir.addWidget(self.label_pdf_dir, 1)
        self.layout_pdf_dir.addWidget(self.btn_pdf_browse)
        form_layout.addRow("Guardar PDF en:", self.layout_pdf_dir)

        # Botón para acceder al panel de Redes Neuronales Protegido
        self.btn_dev_nn = QPushButton("🧠  Abrir Panel Red Neuronal & Dev (Protegido)")
        self.btn_dev_nn.setStyleSheet("background-color: #1e1b4b; color: #c084fc; border: 1px solid #4338ca; padding: 8px; border-radius: 6px; font-weight: bold;")
        self.btn_dev_nn.clicked.connect(self._open_protected_dev_panel)

        form_layout.addRow("Área Desarrollador:", self.btn_dev_nn)

        layout.addWidget(lbl_title)
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        self.button_box.accepted.connect(self._save_settings)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _open_protected_dev_panel(self) -> None:
        """Abre la ventana modal del panel Dev tras solicitar el PIN."""
        pin_dialog = PINVerificationDialog(self)
        if pin_dialog.exec() == PINVerificationDialog.Accepted:
            parent = self.parent()
            if parent and hasattr(parent, "nn_manager") and hasattr(parent, "anomaly_nn"):
                dev_win = DevNNWindow(parent.nn_manager, parent.anomaly_nn, parent=parent)
                dev_win.exec()

    def _browse_excel_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta para Guardar Excel",
            self.settings.get("excel_directory")
        )
        if directory:
            self.settings.set("excel_directory", directory, auto_save=False)
            self.label_excel_dir.setText(self._truncate_path(directory))

    def _browse_pdf_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta para Informes PDF",
            self.settings.get("reports_directory")
        )
        if directory:
            self.settings.set("reports_directory", directory, auto_save=False)
            self.label_pdf_dir.setText(self._truncate_path(directory))

    def _save_settings(self) -> None:
        port = self.combo_port.currentText()
        if not port:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar o escribir un puerto serial válido.")
            return

        self.settings.set("serial_port", port, auto_save=False)
        self.settings.set("serial_baudrate", int(self.combo_baud.currentText()), auto_save=False)
        self.settings.set("theme", self.combo_theme.currentText(), auto_save=False)

        if self.settings.save():
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar las configuraciones en el archivo.")
            self.reject()

    @staticmethod
    def _truncate_path(path_str: str, max_chars: int = 35) -> str:
        if len(path_str) <= max_chars:
            return path_str
        return "..." + path_str[-(max_chars - 3):]
