"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Panel de Diagnóstico de Redes Neuronales para Desarrolladores (gui/dev_nn_tab.py)

Interfaz avanzada de PyQtGraph con gráficas en vivo de convergencia MSE,
predicción vs real, y tarjetas de métricas con estética pastel premium.

Autor:  Equipo SIMA — Diseñador UX/UI & Desarrollador IA
Fecha:  2026-08-09
"""

from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor

import pyqtgraph as pg

from nn_predictor import NNPredictorManager
from anomaly_nn import AnomalyNNManager
from logger_manager import get_logger

logger = get_logger("dev_nn_tab")


class DevNNTabWidget(QWidget):
    """Panel de diagnóstico con gráficas PyQtGraph en vivo y tarjetas de métricas pastel."""

    def __init__(
        self,
        nn_manager: NNPredictorManager,
        anomaly_nn: Optional[AnomalyNNManager] = None,
        parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.nn_manager = nn_manager
        self.anomaly_nn = anomaly_nn if anomaly_nn else AnomalyNNManager()

        # Buffers para gráficas en vivo
        self.history_real_temp: List[float] = []
        self.history_pred_temp: List[float] = []
        self.history_real_hum: List[float] = []
        self.history_pred_hum: List[float] = []

        self._init_ui()
        self._update_display()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        # Encabezado Desarrollador
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f172a, stop:0.5 #1a0d2e, stop:1 #0f172a);
                border: 1px solid #4338ca;
                border-radius: 10px;
            }
        """)
        header_h = QHBoxLayout(header_frame)
        header_h.setContentsMargins(18, 12, 18, 12)

        v_title = QVBoxLayout()
        lbl_title = QLabel("🧠  PANEL DE DESARROLLADOR — DIAGNÓSTICO NEURONAL")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_title.setStyleSheet("color: #c084fc;")

        lbl_sub = QLabel("PyTorch · Red #1 (Predictor MLP) · Red #2 (Autoencoder Anomalías) · Entrenamiento Continuo")
        lbl_sub.setFont(QFont("Segoe UI", 9))
        lbl_sub.setStyleSheet("color: #a78bfa;")

        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)

        # Botones de control
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        dev_btn_style = """
            QPushButton {
                background-color: #1e1b4b; color: #c4b5fd; border: 1px solid #4338ca;
                border-radius: 6px; padding: 7px 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #4338ca; color: #ede9fe; }
        """

        self.btn_train_now = QPushButton("⚡ Entrenar Paso")
        self.btn_train_now.setStyleSheet(dev_btn_style)
        self.btn_train_now.clicked.connect(self._manual_train_step)

        self.btn_save_model = QPushButton("💾 Guardar Redes")
        self.btn_save_model.setStyleSheet(dev_btn_style)
        self.btn_save_model.clicked.connect(self._save_model)

        self.btn_reset_model = QPushButton("🔄 Resetear Pesos")
        self.btn_reset_model.setStyleSheet(dev_btn_style.replace("#1e1b4b", "#2d1515").replace("#4338ca", "#991b1b").replace("#c4b5fd", "#fca5a5"))
        self.btn_reset_model.clicked.connect(self._reset_model)

        btn_box.addWidget(self.btn_train_now)
        btn_box.addWidget(self.btn_save_model)
        btn_box.addWidget(self.btn_reset_model)

        header_h.addLayout(v_title, 3)
        header_h.addLayout(btn_box, 2)

        # Tarjetas de Métricas Pastel
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        self.card_intel = self._create_metric_card("Inteligencia Red #1", "0.0%", "⚡", "#a78bfa")
        self.progress_intel = QProgressBar()
        self.progress_intel.setRange(0, 100)
        self.progress_intel.setValue(0)
        self.progress_intel.setTextVisible(False)
        self.progress_intel.setMaximumHeight(8)
        self.progress_intel.setStyleSheet("""
            QProgressBar {
                background-color: #1e1b4b;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #f472b6);
                border-radius: 4px;
            }
        """)
        self.card_intel.layout().addWidget(self.progress_intel)

        self.card_risk = self._create_metric_card("Riesgo Red #2", "0.0%", "🛡️", "#6ee7b7")
        self.card_loss = self._create_metric_card("Error MSE", "1.0000", "🎯", "#7dd3fc")
        self.card_pred_temp = self._create_metric_card("Temp. +5min", "-- °C", "🔮", "#fcd34d")
        self.card_pred_hum = self._create_metric_card("Hum. +5min", "-- %", "💧", "#67e8f9")

        cards_layout.addWidget(self.card_intel)
        cards_layout.addWidget(self.card_risk)
        cards_layout.addWidget(self.card_loss)
        cards_layout.addWidget(self.card_pred_temp)
        cards_layout.addWidget(self.card_pred_hum)

        # Gráficas PyQtGraph con Estilo Pastel SCADA
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # Gráfica 1: Predicción en Vivo
        chart_pred_frame = QFrame()
        chart_pred_frame.setStyleSheet("QFrame { background-color: #0a0e17; border: 1px solid #1e293b; border-radius: 10px; }")
        chart_pred_v = QVBoxLayout(chart_pred_frame)
        chart_pred_v.setContentsMargins(12, 10, 12, 10)

        lbl_chart1 = QLabel("📈  PREDICCIÓN EN TIEMPO REAL — Temp. Real vs. Red Neuronal #1")
        lbl_chart1.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_chart1.setStyleSheet("color: #7dd3fc;")

        self.plot_predictions = pg.PlotWidget()
        self.plot_predictions.setBackground("#070b14")
        self.plot_predictions.showGrid(x=True, y=True, alpha=0.15)
        self.plot_predictions.setLabel("left", "Temperatura (°C)", color="#94a3b8")
        self.plot_predictions.setLabel("bottom", "Muestras", color="#94a3b8")
        self.plot_predictions.getAxis("left").setPen(pg.mkPen("#334155"))
        self.plot_predictions.getAxis("bottom").setPen(pg.mkPen("#334155"))

        self.curve_real_temp = self.plot_predictions.plot(
            pen=pg.mkPen(color="#7dd3fc", width=2.5), name="Temp. Real"
        )
        self.curve_pred_temp = self.plot_predictions.plot(
            pen=pg.mkPen(color="#fcd34d", width=2, style=Qt.DashLine), name="Temp. Predicha"
        )

        chart_pred_v.addWidget(lbl_chart1)
        chart_pred_v.addWidget(self.plot_predictions)

        # Gráfica 2: Curva de Convergencia MSE
        chart_loss_frame = QFrame()
        chart_loss_frame.setStyleSheet("QFrame { background-color: #0a0e17; border: 1px solid #1e293b; border-radius: 10px; }")
        chart_loss_v = QVBoxLayout(chart_loss_frame)
        chart_loss_v.setContentsMargins(12, 10, 12, 10)

        lbl_chart2 = QLabel("📉  CURVA DE APRENDIZAJE CONTINUO — Evolución del Error MSE")
        lbl_chart2.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_chart2.setStyleSheet("color: #6ee7b7;")

        self.plot_loss = pg.PlotWidget()
        self.plot_loss.setBackground("#070b14")
        self.plot_loss.showGrid(x=True, y=True, alpha=0.15)
        self.plot_loss.setLabel("left", "Pérdida MSE", color="#94a3b8")
        self.plot_loss.setLabel("bottom", "Iteraciones", color="#94a3b8")
        self.plot_loss.getAxis("left").setPen(pg.mkPen("#334155"))
        self.plot_loss.getAxis("bottom").setPen(pg.mkPen("#334155"))

        self.curve_loss = self.plot_loss.plot(
            pen=pg.mkPen(color="#6ee7b7", width=2.5)
        )

        chart_loss_v.addWidget(lbl_chart2)
        chart_loss_v.addWidget(self.plot_loss)

        splitter.addWidget(chart_pred_frame)
        splitter.addWidget(chart_loss_frame)
        splitter.setSizes([500, 500])

        main_layout.addWidget(header_frame)
        main_layout.addLayout(cards_layout)
        main_layout.addWidget(splitter, 1)

    def _create_metric_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #0f0d1a;
                border: 1px solid #1e1b4b;
                border-radius: 10px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        lbl_title = QLabel(f"{icon} {title}")
        lbl_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_title.setStyleSheet("color: #94a3b8; border: none; background: transparent;")

        lbl_val = QLabel(value)
        lbl_val.setObjectName("cardValLabel")
        lbl_val.setFont(QFont("Segoe UI", 17, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color}; border: none; background: transparent;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return card

    @Slot(float, float)
    def update_live_data(self, temp: float, hum: float) -> None:
        """Actualiza historiales de ambas redes neuronales y refresca gráficas."""
        train_res = self.nn_manager.add_sample_and_train_online(temp, hum)
        anomaly_res = self.anomaly_nn.analyze_sample(temp, hum)

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

        self._update_display(train_res, anomaly_res)

    def _update_display(
        self,
        train_res: Optional[Dict[str, Any]] = None,
        anomaly_res: Optional[Dict[str, Any]] = None
    ) -> None:
        intel_info = self.nn_manager.get_intelligence_level()
        anomaly_info = self.anomaly_nn.get_summary()

        intel_pct = intel_info["intelligence_percentage"]
        self.progress_intel.setValue(int(intel_pct))
        val_label = self.card_intel.findChild(QLabel, "cardValLabel")
        if val_label:
            val_label.setText(f"{intel_pct}%")

        loss_label = self.card_loss.findChild(QLabel, "cardValLabel")
        if loss_label:
            loss_label.setText(f"{self.nn_manager.current_loss:.5f}")

        risk_pct = anomaly_info["risk_percentage"]
        risk_color = "#6ee7b7" if risk_pct < 30.0 else ("#fcd34d" if risk_pct < 70.0 else "#f87171")
        risk_label = self.card_risk.findChild(QLabel, "cardValLabel")
        if risk_label:
            risk_label.setText(f"{risk_pct}%")
            risk_label.setStyleSheet(f"color: {risk_color}; border: none; background: transparent;")

        pred_future = train_res.get("prediction_future") if train_res else None
        if not pred_future:
            _, pred_future = self.nn_manager.predict_future()

        if pred_future:
            pt_label = self.card_pred_temp.findChild(QLabel, "cardValLabel")
            if pt_label:
                pt_label.setText(f"{pred_future['temp']} °C")
            ph_label = self.card_pred_hum.findChild(QLabel, "cardValLabel")
            if ph_label:
                ph_label.setText(f"{pred_future['hum']} %")

        # Actualizar gráficas PyQtGraph
        if self.history_real_temp:
            self.curve_real_temp.setData(self.history_real_temp)
            if self.history_pred_temp:
                self.curve_pred_temp.setData(self.history_pred_temp)

        if self.nn_manager.loss_history:
            self.curve_loss.setData(self.nn_manager.loss_history)

    def _manual_train_step(self) -> None:
        if self.history_real_temp:
            last_t = self.history_real_temp[-1]
            last_h = self.history_real_hum[-1]
            res1 = self.nn_manager.add_sample_and_train_online(last_t, last_h)
            res2 = self.anomaly_nn.analyze_sample(last_t, last_h)
            self._update_display(res1, res2)
        else:
            QMessageBox.warning(self, "Atención", "Aún no hay muestras de sensores registradas.")

    def _save_model(self) -> None:
        ok1 = self.nn_manager.save_model()
        ok2 = self.anomaly_nn.save_model()
        if ok1 and ok2:
            QMessageBox.information(self, "Éxito", "Pesos de las Redes Neuronales guardados correctamente.")

    def _reset_model(self) -> None:
        reply = QMessageBox.question(
            self, "Confirmar Reset",
            "¿Desea reiniciar los pesos de ambas redes neuronales?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.nn_manager.reset_model()
            self.anomaly_nn = AnomalyNNManager()
            self.history_real_temp.clear()
            self.history_pred_temp.clear()
            self.history_real_hum.clear()
            self.history_pred_hum.clear()
            self._update_display()
