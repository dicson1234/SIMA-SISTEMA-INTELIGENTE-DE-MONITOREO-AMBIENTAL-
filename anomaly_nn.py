"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Red Neuronal #2: Detector de Anomalías y Patrones de Riesgo (anomaly_nn.py)

Implementa una Red Neuronal Autoencoder / Clasificador de Anomalías en PyTorch
(con fallback en NumPy) que aprende continuamente los patrones normales del ambiente
y detecta desviaciones anómalas, picos térmicos o fallos de climatización.

Autor:  Equipo SIMA — Especialista en IA y Redes Neuronales
Fecha:  2026-07-31
"""

import os
import json
import time
import math
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from logger_manager import get_logger, log_exception

logger = get_logger("anomaly_nn")

# Intentar importar PyTorch
HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


if HAS_TORCH:
    class AutoencoderPyTorch(nn.Module):
        """Autoencoder Neuronal para Reducción de Dimensión y Detección de Anomalías.
        
        Arquitectura: 4 (Entradas) -> 8 -> 2 (Bottleneck Latente) -> 8 -> 4 (Salida Reconstruida)
        """
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(4, 8),
                nn.LeakyReLU(0.2),
                nn.Linear(8, 2),
                nn.LeakyReLU(0.2)
            )
            self.decoder = nn.Sequential(
                nn.Linear(2, 8),
                nn.LeakyReLU(0.2),
                nn.Linear(8, 4)
            )

        def forward(self, x):
            latent = self.encoder(x)
            reconstructed = self.decoder(latent)
            return reconstructed, latent


class AnomalyNNManager:
    """Gestor de la Red Neuronal #2 especializada en Detección de Anomalías y Patrones de Riesgo.
    
    Aprende la distribución estadística normal de Temperatura y Humedad (+ derivadas/delta).
    Si una lectura tiene un error de reconstrucción elevado, la marca como anomalía o riesgo.
    """

    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.model_dir / "anomaly_nn_model.pth"

        self.use_torch = HAS_TORCH
        self.trained_samples_count = 0
        self.anomaly_count = 0
        self.reconstruction_loss_history: List[float] = []
        self.last_risk_score: float = 0.0  # 0.0 a 100.0 %
        self.last_status: str = "Normal"

        # Buffer histórico para deltas [temp, hum, delta_temp, delta_hum]
        self.last_temp: Optional[float] = None
        self.last_hum: Optional[float] = None

        # Umbrales dinámicos de normalización
        self.temp_min = 0.0
        self.temp_max = 50.0
        self.hum_min = 0.0
        self.hum_max = 100.0

        if self.use_torch:
            self.model = AutoencoderPyTorch()
            self.optimizer = optim.Adam(self.model.parameters(), lr=0.005)
            self.criterion = nn.MSELoss()
            logger.info("Red Neuronal #2 (Autoencoder Detección Anomalías) iniciada con PyTorch.")
        else:
            self._init_numpy_weights()
            logger.info("PyTorch no disponible. Red Neuronal #2 iniciada con motor NumPy.")

        self.load_model()

    def _init_numpy_weights(self) -> None:
        """Inicialización de pesos para el motor NumPy."""
        np.random.seed(42)
        self.W1 = np.random.randn(4, 8) * 0.1
        self.b1 = np.zeros((1, 8))
        self.W2 = np.random.randn(8, 2) * 0.1
        self.b2 = np.zeros((1, 2))
        self.W3 = np.random.randn(2, 8) * 0.1
        self.b3 = np.zeros((1, 8))
        self.W4 = np.random.randn(8, 4) * 0.1
        self.b4 = np.zeros((1, 4))

    def _normalize_input(self, temp: float, hum: float, d_temp: float, d_hum: float) -> np.ndarray:
        """Normaliza las 4 características de entrada."""
        t_norm = (temp - self.temp_min) / (self.temp_max - self.temp_min + 1e-6)
        h_norm = (hum - self.hum_min) / (self.hum_max - self.hum_min + 1e-6)
        dt_norm = np.clip(d_temp / 5.0, -1.0, 1.0)
        dh_norm = np.clip(d_hum / 10.0, -1.0, 1.0)
        return np.array([t_norm, h_norm, dt_norm, dh_norm], dtype=np.float32)

    def analyze_sample(self, temp: float, hum: float) -> Dict[str, Any]:
        """Procesa una muestra en vivo, calcula el error de reconstrucción y entrena la red."""
        d_temp = 0.0 if self.last_temp is None else (temp - self.last_temp)
        d_hum = 0.0 if self.last_hum is None else (hum - self.last_hum)

        self.last_temp = temp
        self.last_hum = hum

        x_norm = self._normalize_input(temp, hum, d_temp, d_hum)

        if self.use_torch:
            x_tensor = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0)
            self.model.eval()
            with torch.no_grad():
                reconstructed, _ = self.model(x_tensor)
                recon_loss = self.criterion(reconstructed, x_tensor).item()

            # Entrenar online si es un comportamiento habitual
            self.model.train()
            self.optimizer.zero_grad()
            rec, _ = self.model(x_tensor)
            loss = self.criterion(rec, x_tensor)
            loss.backward()
            self.optimizer.step()

        else:
            # Forward pass NumPy
            z1 = np.dot(x_norm, self.W1) + self.b1
            a1 = np.maximum(0.2 * z1, z1)
            z2 = np.dot(a1, self.W2) + self.b2
            a2 = np.maximum(0.2 * z2, z2)
            z3 = np.dot(a2, self.W3) + self.b3
            a3 = np.maximum(0.2 * z3, z3)
            z4 = np.dot(a3, self.W4) + self.b4

            recon_loss = float(np.mean((z4 - x_norm) ** 2))

        self.trained_samples_count += 1
        self.reconstruction_loss_history.append(recon_loss)
        if len(self.reconstruction_loss_history) > 200:
            self.reconstruction_loss_history.pop(0)

        # Calcular nivel de riesgo (0% a 100%)
        # Un error de reconstrucción > 0.05 indica desviación severa
        risk_percentage = min(100.0, max(0.0, (recon_loss / 0.03) * 100.0))
        self.last_risk_score = round(risk_percentage, 1)

        is_anomaly = recon_loss > 0.025
        if is_anomaly:
            self.anomaly_count += 1
            self.last_status = "⚠️ ANOMALÍA DETECTADA"
        elif risk_percentage > 50.0:
            self.last_status = "⚡ RIESGO MODERADO"
        else:
            self.last_status = "✅ AMBIENTE NORMAL"

        return {
            "reconstruction_loss": recon_loss,
            "risk_percentage": self.last_risk_score,
            "is_anomaly": is_anomaly,
            "status": self.last_status,
            "total_anomalies": self.anomaly_count,
            "samples": self.trained_samples_count
        }

    # Alias de compatibilidad
    predict_anomaly = analyze_sample

    def get_summary(self) -> Dict[str, Any]:
        """Retorna un resumen formateado para el agente IA."""
        return {
            "nn_name": "Red Neuronal #2 (Detector de Anomalías & Riesgo Autoencoder)",
            "trained_samples": self.trained_samples_count,
            "risk_percentage": self.last_risk_score,
            "status": self.last_status,
            "total_anomalies": self.anomaly_count,
            "motor": "PyTorch" if self.use_torch else "NumPy"
        }

    def save_model(self) -> bool:
        """Guarda los pesos del Autoencoder."""
        try:
            if self.use_torch:
                torch.save({
                    "state_dict": self.model.state_dict(),
                    "samples": self.trained_samples_count,
                    "anomalies": self.anomaly_count
                }, self.model_path)
            return True
        except Exception as e:
            log_exception(e, "Error al guardar Red Neuronal #2")
            return False

    def load_model(self) -> bool:
        """Carga los pesos si existen."""
        if not self.model_path.exists():
            return False
        try:
            if self.use_torch:
                checkpoint = torch.load(self.model_path, weights_only=True)
                self.model.load_state_dict(checkpoint["state_dict"])
                self.trained_samples_count = checkpoint.get("samples", 0)
                self.anomaly_count = checkpoint.get("anomalies", 0)
            return True
        except Exception as e:
            logger.warning("No se pudieron cargar los pesos de la Red #2: %s", str(e))
            return False
