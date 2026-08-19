"""
SIMA GUI — Diálogo de Gestión de Perfil de Usuario (gui/profile_dialog.py)
Visualización y actualización de perfil, umbrales de alerta y usuarios registrados.

Autor: Equipo SIMA
Fecha: 2026-08-17
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QComboBox, QMessageBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from auth_manager import get_auth_manager


class UserProfileDialog(QDialog):
    """Diálogo modal para visualizar y editar el perfil de usuario activo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_mgr = get_auth_manager()
        self.setWindowTitle("👤 Mi Perfil de Usuario — SIMA Backend")
        self.setFixedSize(580, 620)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        user = self.auth_mgr.get_current_user() or {}

        # Badge y Encabezado de Perfil
        profile_card = QFrame()
        profile_card.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        card_layout = QHBoxLayout(profile_card)

        # Avatar iniciales
        avatar_color = user.get("avatar_color", "#3B82F6")
        initials = (user.get("full_name", "U")[:2]).upper()
        avatar_lbl = QLabel(initials)
        avatar_lbl.setFixedSize(56, 56)
        avatar_lbl.setFont(QFont("Inter", 18, QFont.Bold))
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_lbl.setStyleSheet(f"""
            background-color: {avatar_color};
            color: white;
            border-radius: 28px;
        """)
        card_layout.addWidget(avatar_lbl)

        # Info básica
        info_layout = QVBoxLayout()
        name_lbl = QLabel(user.get("full_name", "Usuario Desconocido"))
        name_lbl.setFont(QFont("Inter", 14, QFont.Bold))
        
        role_text = f"Rol: {user.get('role', 'operator').upper()} | Usuario: @{user.get('username', 'user')}"
        role_lbl = QLabel(role_text)
        role_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        
        email_lbl = QLabel(f"📧 {user.get('email', 'N/A')}")
        email_lbl.setStyleSheet("color: #CBD5E1; font-size: 11px;")

        info_layout.addWidget(name_lbl)
        info_layout.addWidget(role_lbl)
        info_layout.addWidget(email_lbl)
        card_layout.addLayout(info_layout)
        card_layout.addStretch()

        main_layout.addWidget(profile_card)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; border-radius: 8px; background: #0F172A; }
            QTabBar::tab { padding: 8px 14px; font-weight: bold; }
            QTabBar::tab:selected { background: #2563EB; color: white; border-radius: 4px; }
        """)

        # Pestaña 1: Configurar Perfil y Umbrales
        edit_tab = QWidget()
        edit_layout = QVBoxLayout(edit_tab)
        edit_layout.setSpacing(10)

        edit_layout.addWidget(QLabel("Nombre Completo:"))
        self.txt_fullname = QLineEdit(user.get("full_name", ""))
        self.txt_fullname.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.txt_fullname)

        edit_layout.addWidget(QLabel("Biografía / Descripción del Rol:"))
        self.txt_bio = QTextEdit(user.get("bio", ""))
        self.txt_bio.setFixedHeight(60)
        self.txt_bio.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.txt_bio)

        # Umbrales Ambientales Personalizados
        edit_layout.addWidget(QLabel("⚙️ Umbral Máximo de Alerta de Temperatura (°C):"))
        self.txt_temp = QLineEdit(str(user.get("temp_threshold", 30.0)))
        self.txt_temp.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.txt_temp)

        edit_layout.addWidget(QLabel("⚙️ Umbral Máximo de Alerta de Humedad (%):"))
        self.txt_hum = QLineEdit(str(user.get("hum_threshold", 70.0)))
        self.txt_hum.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.txt_hum)

        btn_save = QPushButton("💾 Guardar Cambios del Perfil")
        btn_save.setStyleSheet("""
            QPushButton { background: #2563EB; color: white; font-weight: bold; padding: 10px; border-radius: 6px; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn_save.clicked.connect(self._save_profile_changes)
        edit_layout.addWidget(btn_save)
        edit_layout.addStretch()

        self.tabs.addTab(edit_tab, "✏️ Editar Perfil y Umbrales")

        # Pestaña 2: Lista de Usuarios (Solo Admin o modo informativo)
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        
        users_layout.addWidget(QLabel("👥 Usuarios Registrados en el Backend SIMA:"))
        self.table_users = QTableWidget()
        self.table_users.setColumnCount(4)
        self.table_users.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre", "Rol"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_users.setStyleSheet("""
            QTableWidget { background: #1E293B; color: #F8FAFC; gridline-color: #334155; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; }
        """)
        self._load_users_table()
        users_layout.addWidget(self.table_users)

        self.tabs.addTab(users_tab, "👥 Listado de Usuarios")
        main_layout.addWidget(self.tabs)

        # Botones de Acción (Cerrar Sesión / Cerrar Ventana)
        bottom_layout = QHBoxLayout()
        btn_logout = QPushButton("🚪 Cerrar Sesión")
        btn_logout.setStyleSheet("""
            QPushButton { background: #DC2626; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background: #B91C1C; }
        """)
        btn_logout.clicked.connect(self._logout)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("padding: 8px 16px; background: #475569; color: white; border-radius: 6px;")
        btn_close.clicked.connect(self.accept)

        bottom_layout.addWidget(btn_logout)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)
        main_layout.addLayout(bottom_layout)

    def _load_users_table(self):
        all_users = self.auth_mgr.db.list_all_users()
        self.table_users.setRowCount(len(all_users))
        for row_idx, u in enumerate(all_users):
            self.table_users.setItem(row_idx, 0, QTableWidgetItem(str(u["id"])))
            self.table_users.setItem(row_idx, 1, QTableWidgetItem(u["username"]))
            self.table_users.setItem(row_idx, 2, QTableWidgetItem(u.get("full_name", "")))
            self.table_users.setItem(row_idx, 3, QTableWidgetItem(u["role"].upper()))

    def _save_profile_changes(self):
        fn = self.txt_fullname.text().strip()
        bio = self.txt_bio.toPlainText().strip()
        try:
            temp_val = float(self.txt_temp.text())
            hum_val = float(self.txt_hum.text())
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Los umbrales deben ser valores numéricos válidos.")
            return

        ok, msg = self.auth_mgr.update_profile(
            full_name=fn,
            bio=bio,
            temp_threshold=temp_val,
            hum_threshold=hum_val
        )
        if ok:
            QMessageBox.information(self, "Perfil Actualizado", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _logout(self):
        reply = QMessageBox.question(
            self, "Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión actual?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.auth_mgr.logout()
            self.accept()

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit, QTextEdit {
                background: #111827;
                border: 1px solid #4B5563;
                border-radius: 6px;
                padding: 6px;
                color: #F9FAFB;
                font-size: 13px;
            }
        """
