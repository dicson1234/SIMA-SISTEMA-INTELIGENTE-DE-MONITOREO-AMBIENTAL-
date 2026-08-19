"""
SIMA GUI — Diálogo de Inicio de Sesión y Registro de Usuarios (gui/login_dialog.py)
Interfaz moderna en PySide6 para autenticación de usuarios y perfiles.

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QComboBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from auth_manager import get_auth_manager


class LoginRegisterDialog(QDialog):
    """Diálogo modal para Iniciar Sesión y Registrar Cuentas de Usuario."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_mgr = get_auth_manager()
        self.setWindowTitle("🔑 Autenticación de Usuario — SIMA Backend")
        self.setFixedSize(450, 520)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Encabezado
        header_layout = QVBoxLayout()
        header_title = QLabel("SIMA Backend Platform")
        header_title.setFont(QFont("Inter", 16, QFont.Bold))
        header_title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Gestión de Usuarios, Perfiles y Control de Acceso")
        subtitle.setFont(QFont("Inter", 10))
        subtitle.setStyleSheet("color: #9CA3AF;")
        subtitle.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(header_title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Tab Widget (Iniciar Sesión / Registrarse)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #374151; border-radius: 8px; background: #1F2937; }
            QTabBar::tab { padding: 8px 16px; margin: 2px; font-weight: bold; }
            QTabBar::tab:selected { background: #3B82F6; color: white; border-radius: 4px; }
        """)

        # Pestaña 1: Login
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_layout.setSpacing(12)
        login_layout.setContentsMargins(16, 20, 16, 20)

        login_layout.addWidget(QLabel("Nombre de Usuario:"))
        self.txt_login_user = QLineEdit()
        self.txt_login_user.setPlaceholderText("ej. admin")
        self.txt_login_user.setStyleSheet(self._input_style())
        login_layout.addWidget(self.txt_login_user)

        login_layout.addWidget(QLabel("Contraseña:"))
        self.txt_login_pass = QLineEdit()
        self.txt_login_pass.setEchoMode(QLineEdit.Password)
        self.txt_login_pass.setPlaceholderText("••••••••")
        self.txt_login_pass.setStyleSheet(self._input_style())
        login_layout.addWidget(self.txt_login_pass)

        # Botón auto-rellenar demo
        btn_quick_admin = QPushButton("⚡ Cargar Credenciales Demo (Admin)")
        btn_quick_admin.setStyleSheet("background: transparent; color: #60A5FA; border: none; font-size: 11px;")
        btn_quick_admin.clicked.connect(self._fill_quick_admin)
        login_layout.addWidget(btn_quick_admin, alignment=Qt.AlignRight)

        btn_login = QPushButton("🔐 Iniciar Sesión")
        btn_login.setStyleSheet(self._btn_primary_style())
        btn_login.clicked.connect(self._handle_login)
        login_layout.addWidget(btn_login)
        login_layout.addStretch()

        # Pestaña 2: Registro
        register_tab = QWidget()
        reg_layout = QVBoxLayout(register_tab)
        reg_layout.setSpacing(8)
        reg_layout.setContentsMargins(16, 12, 16, 12)

        reg_layout.addWidget(QLabel("Nombre de Usuario:"))
        self.txt_reg_user = QLineEdit()
        self.txt_reg_user.setPlaceholderText("ej. dicson_dev")
        self.txt_reg_user.setStyleSheet(self._input_style())
        reg_layout.addWidget(self.txt_reg_user)

        reg_layout.addWidget(QLabel("Nombre Completo:"))
        self.txt_reg_fullname = QLineEdit()
        self.txt_reg_fullname.setPlaceholderText("ej. Dicson Pérez")
        self.txt_reg_fullname.setStyleSheet(self._input_style())
        reg_layout.addWidget(self.txt_reg_fullname)

        reg_layout.addWidget(QLabel("Correo Electrónico:"))
        self.txt_reg_email = QLineEdit()
        self.txt_reg_email.setPlaceholderText("ej. usuario@ejemplo.com")
        self.txt_reg_email.setStyleSheet(self._input_style())
        reg_layout.addWidget(self.txt_reg_email)

        reg_layout.addWidget(QLabel("Contraseña:"))
        self.txt_reg_pass = QLineEdit()
        self.txt_reg_pass.setEchoMode(QLineEdit.Password)
        self.txt_reg_pass.setPlaceholderText("••••••••")
        self.txt_reg_pass.setStyleSheet(self._input_style())
        reg_layout.addWidget(self.txt_reg_pass)

        reg_layout.addWidget(QLabel("Rol de Usuario / Perfil:"))
        self.cb_reg_role = QComboBox()
        self.cb_reg_role.addItems([
            "operator — Operador de Sensores",
            "analyst — Analista Ambiental",
            "admin — Administrador del Sistema"
        ])
        self.cb_reg_role.setStyleSheet(self._input_style())
        reg_layout.addWidget(self.cb_reg_role)

        btn_register = QPushButton("✨ Crear Cuenta de Usuario")
        btn_register.setStyleSheet(self._btn_success_style())
        btn_register.clicked.connect(self._handle_register)
        reg_layout.addWidget(btn_register)

        self.tabs.addTab(login_tab, "🔑 Iniciar Sesión")
        self.tabs.addTab(register_tab, "👤 Registrarse")
        main_layout.addWidget(self.tabs)

    def _fill_quick_admin(self):
        self.txt_login_user.setText("admin")
        self.txt_login_pass.setText("admin123")

    def _handle_login(self):
        user = self.txt_login_user.text().strip()
        pwd = self.txt_login_pass.text()

        if not user or not pwd:
            QMessageBox.warning(self, "Campos Incompletos", "Por favor ingrese usuario y contraseña.")
            return

        ok, msg = self.auth_mgr.login(user, pwd)
        if ok:
            QMessageBox.information(self, "Bienvenido", f"¡Sesión iniciada correctamente!\n{msg}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error de Inicio de Sesión", msg)

    def _handle_register(self):
        username = self.txt_reg_user.text().strip()
        fullname = self.txt_reg_fullname.text().strip()
        email = self.txt_reg_email.text().strip()
        pwd = self.txt_reg_pass.text()
        role_raw = self.cb_reg_role.currentText().split(" ")[0]

        if not username or not fullname or not email or not pwd:
            QMessageBox.warning(self, "Campos Incompletos", "Por favor complete todos los campos requeridos.")
            return

        ok, msg = self.auth_mgr.register(
            username=username,
            email=email,
            password=pwd,
            full_name=fullname,
            role=role_raw
        )

        if ok:
            QMessageBox.information(self, "Registro Exitoso", f"Cuenta creada correctamente.\n{msg}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error de Registro", msg)

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit, QComboBox {
                background: #111827;
                border: 1px solid #4B5563;
                border-radius: 6px;
                padding: 8px;
                color: #F9FAFB;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3B82F6;
            }
        """

    @staticmethod
    def _btn_primary_style() -> str:
        return """
            QPushButton {
                background: #2563EB;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #1D4ED8; }
        """

    @staticmethod
    def _btn_success_style() -> str:
        return """
            QPushButton {
                background: #059669;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #047857; }
        """
