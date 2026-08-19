"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Red Neuronal Predictiva y Aprendizaje Continuo (nn_predictor.py)

Implementa una Red Neuronal Artificial (MLP) para predicción de series temporales
de variables ambientales (Temperatura y Humedad), ofreciendo aprendizaje en línea (Online Learning).
A medida que el sistema recolecta datos de los sensores, la red realiza pasos de optimización
retropropagando los errores de predicción, incrementando de manera continua su precisión ("cuanto más datos toma, más inteligente se vuelve").

Diseñado para integrarse posteriormente con Agentes Conversacionales IA (LLM/Asistentes Inteligentes),
proporcionando diagnósticos estructurados y proyecciones ambientales.

Autor:  Equipo SIMA — Especialista en IA y Redes Neuronales
Fecha:  2026-07-31
"""

import os
import json
import math
import time
from pathlib import Path
from collections import deque
from typing import List, Tuple, Dict, Any, Optional

import numpy as np

from logger_manager import get_logger, log_exception

logger = get_logger("nn_predictor")

# Detectar PyTorch
HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
    logger.info("PyTorch detectado. Se utilizará el motor acelerado de PyTorch para la Red Neuronal.")
except ImportError:
    logger.info("PyTorch no detectado o en instalación. Se utilizará el motor neuronal basado en NumPy.")


# =====================================================================
#  MODELO PYTORCH (Si está disponible)
# =====================================================================

if HAS_TORCH:
    class PyTorchEnvironmentalNN(nn.Module):
        """Red Neuronal Multicapa (MLP) en PyTorch para predicción de parámetros ambientales."""

        def __init__(self, input_dim: int = 10, hidden_dim1: int = 32, hidden_dim2: int = 16, output_dim: int = 2):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden_dim1),
                nn.LeakyReLU(0.1),
                nn.Linear(hidden_dim1, hidden_dim2),
                nn.LeakyReLU(0.1),
                nn.Linear(hidden_dim2, output_dim)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)


# =====================================================================
#  MODELO NUMPY (Fallback liviano ultra-rápido)
# =====================================================================

class NumPyEnvironmentalNN:
    """Red Neuronal Multicapa (MLP 10 -> 32 -> 16 -> 2) implementada en NumPy con Adam Optimizer."""

    def __init__(self, input_dim: int = 10, hidden1: int = 32, hidden2: int = 16, output_dim: int = 2):
        self.input_dim = input_dim
        self.hidden1 = hidden1
        self.hidden2 = hidden2
        self.output_dim = output_dim

        # Inicialización Xavier / He
        self.W1 = np.random.randn(input_dim, hidden1) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros((1, hidden1))
        self.W2 = np.random.randn(hidden1, hidden2) * np.sqrt(2.0 / hidden1)
        self.b2 = np.zeros((1, hidden2))
        self.W3 = np.random.randn(hidden2, output_dim) * np.sqrt(2.0 / hidden2)
        self.b3 = np.zeros((1, output_dim))

        # Momentos para Optimizer Adam
        self.mW1, self.vW1 = np.zeros_like(self.W1), np.zeros_like(self.W1)
        self.mb1, self.vb1 = np.zeros_like(self.b1), np.zeros_like(self.b1)
        self.mW2, self.vW2 = np.zeros_like(self.W2), np.zeros_like(self.W2)
        self.mb2, self.vb2 = np.zeros_like(self.b2), np.zeros_like(self.b2)
        self.mW3, self.vW3 = np.zeros_like(self.W3), np.zeros_like(self.W3)
        self.mb3, self.vb3 = np.zeros_like(self.b3), np.zeros_like(self.b3)
        self.t = 0

    def relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0.01 * x, x)

    def drelu(self, x: np.ndarray) -> np.ndarray:
        dx = np.ones_like(x)
        dx[x < 0] = 0.01
        return dx

    def forward(self, X: np.ndarray) -> np.ndarray:
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.relu(self.z2)
        self.z3 = np.dot(self.a2, self.W3) + self.b3
        return self.z3

    def train_step(self, X: np.ndarray, y: np.ndarray, lr: float = 0.005) -> float:
        """Paso de retropropagación y actualización Adam."""
        N = X.shape[0]
        y_pred = self.forward(X)
        loss = float(np.mean((y_pred - y) ** 2))

        # Backward pass
        grad_y = 2.0 * (y_pred - y) / N
        dW3 = np.dot(self.a2.T, grad_y)
        db3 = np.sum(grad_y, axis=0, keepdims=True)

        da2 = np.dot(grad_y, self.W3.T)
        dz2 = da2 * self.drelu(self.z2)
        dW2 = np.dot(self.a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)

        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * self.drelu(self.z1)
        dW1 = np.dot(X.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)

        # Actualización Adam
        self.t += 1
        beta1, beta2, eps = 0.9, 0.999, 1e-8

        for param, dparam, m, v in [
            (self.W1, dW1, self.mW1, self.vW1), (self.b1, db1, self.mb1, self.vb1),
            (self.W2, dW2, self.mW2, self.vW2), (self.b2, db2, self.mb2, self.vb2),
            (self.W3, dW3, self.mW3, self.vW3), (self.b3, db3, self.mb3, self.vb3)
        ]:
            m[:] = beta1 * m + (1 - beta1) * dparam
            v[:] = beta2 * v + (1 - beta2) * (dparam ** 2)
            m_hat = m / (1 - beta1 ** self.t)
            v_hat = v / (1 - beta2 ** self.t)
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)

        return loss

    def get_weights_dict(self) -> Dict[str, list]:
        return {
            "W1": self.W1.tolist(), "b1": self.b1.tolist(),
            "W2": self.W2.tolist(), "b2": self.b2.tolist(),
            "W3": self.W3.tolist(), "b3": self.b3.tolist(),
            "t": self.t
        }

    def load_weights_dict(self, d: Dict[str, list]) -> None:
        self.W1 = np.array(d["W1"])
        self.b1 = np.array(d["b1"])
        self.W2 = np.array(d["W2"])
        self.b2 = np.array(d["b2"])
        self.W3 = np.array(d["W3"])
        self.b3 = np.array(d["b3"])
        self.t = d.get("t", 0)


# =====================================================================
#  GESTOR PRINCIPAL DE RED NEURONAL (NN MANAGER)
# =====================================================================

class NNPredictorManager:
    """Orquestador de Aprendizaje Continuo en Línea y Predicciones de Calidad del Aire."""

    def __init__(self, window_size: int = 5, model_dir: str = "models") -> None:
        self.window_size = window_size  # Usar 5 muestras pasadas de [Temp, Hum] = 10 entradas
        self.input_dim = window_size * 2
        self.output_dim = 2  # [Temp_siguiente, Hum_siguiente]

        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_file = self.model_dir / "nn_environmental_model.pth"
        self.json_file = self.model_dir / "nn_environmental_model.json"

        # Historiales y Métricas
        self.history_buffer = deque(maxlen=200) # Mantener ultimas 200 lecturas
        self.trained_samples_count: int = 0
        self.epochs_completed: int = 0
        self.current_loss: float = 1.0
        self.loss_history: List[float] = []
        self.learning_rate: float = 0.005

        # Normalización estática estimada (Temp: 0-50 °C, Hum: 0-100 %)
        self.temp_min, self.temp_max = 0.0, 50.0
        self.hum_min, self.hum_max = 0.0, 100.0

        # Inicialización del Motor de Red Neuronal
        self.use_torch = HAS_TORCH
        if self.use_torch:
            self.model = PyTorchEnvironmentalNN(self.input_dim, 32, 16, self.output_dim)
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
            self.criterion = nn.MSELoss()
        else:
            self.numpy_model = NumPyEnvironmentalNN(self.input_dim, 32, 16, self.output_dim)

        self._load_saved_model()

    def _normalize(self, temp: float, hum: float) -> Tuple[float, float]:
        """Escala temperatura y humedad al rango [0, 1]."""
        nt = (temp - self.temp_min) / (self.temp_max - self.temp_min)
        nh = (hum - self.hum_min) / (self.hum_max - self.hum_min)
        return max(0.0, min(1.0, nt)), max(0.0, min(1.0, nh))

    def _denormalize(self, norm_t: float, norm_h: float) -> Tuple[float, float]:
        """Desescala valores [0, 1] a sus magnitudes reales."""
        t = norm_t * (self.temp_max - self.temp_min) + self.temp_min
        h = norm_h * (self.hum_max - self.hum_min) + self.hum_min
        return round(float(t), 2), round(float(h), 2)

    def add_sample_and_train_online(self, temp: float, hum: float) -> Dict[str, Any]:
        """Recibe una nueva lectura ambiental en vivo, actualiza el buffer y entrena la red en línea.

        Returns:
            Diccionario con el estado actualizado del entrenamiento (loss, total_samples, predictions).
        """
        # Normalizar e insertar en buffer
        norm_t, norm_h = self._normalize(temp, hum)
        self.history_buffer.append((norm_t, norm_h))

        result = {
            "trained": False,
            "loss": self.current_loss,
            "trained_samples": self.trained_samples_count,
            "prediction_next": None,
            "prediction_future": None,
        }

        # Necesitamos al menos window_size + 1 muestras para formar (X, y)
        if len(self.history_buffer) < self.window_size + 1:
            return result

        # Construir lote de entrenamiento a partir del buffer
        X_list = []
        y_list = []

        buf = list(self.history_buffer)
        for i in range(len(buf) - self.window_size):
            # X: secuencia de window_size muestras -> array de tamaño 10
            x_seq = []
            for t_val, h_val in buf[i : i + self.window_size]:
                x_seq.extend([t_val, h_val])
            # y: muestra posterior inmediata
            target = buf[i + self.window_size]
            X_list.append(x_seq)
            y_list.append(target)

        X_arr = np.array(X_list, dtype=np.float32)
        y_arr = np.array(y_list, dtype=np.float32)

        # Paso de Entrenamiento (Mini-batch Online Gradient Step)
        if self.use_torch:
            self.model.train()
            X_tensor = torch.tensor(X_arr, dtype=torch.float32)
            y_tensor = torch.tensor(y_arr, dtype=torch.float32)

            self.optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss_val = self.criterion(outputs, y_tensor)
            loss_val.backward()
            self.optimizer.step()
            loss = float(loss_val.item())
        else:
            loss = self.numpy_model.train_step(X_arr, y_arr, lr=self.learning_rate)

        # Actualizar métricas
        self.current_loss = round(loss, 6)
        self.trained_samples_count += 1
        self.epochs_completed += 1
        self.loss_history.append(self.current_loss)
        if len(self.loss_history) > 100:
            self.loss_history.pop(0)

        # Realizar Predicciones en Vivo
        pred_next, pred_future = self.predict_future()

        result["trained"] = True
        result["loss"] = self.current_loss
        result["trained_samples"] = self.trained_samples_count
        result["prediction_next"] = pred_next
        result["prediction_future"] = pred_future

        # Auto-guardado periódico cada 20 pasos de aprendizaje
        if self.trained_samples_count % 20 == 0:
            self.save_model()

        return result

    def predict_future(self) -> Tuple[Optional[Dict[str, float]], Optional[Dict[str, float]]]:
        """Genera la predicción del siguiente paso (+1 muestra) y proyección a futuro (+5 muestras)."""
        if len(self.history_buffer) < self.window_size:
            return None, None

        buf = list(self.history_buffer)
        current_seq = []
        for t_val, h_val in buf[-self.window_size:]:
            current_seq.extend([t_val, h_val])

        seq_arr = np.array([current_seq], dtype=np.float32)

        # 1. Predicción +1 muestra
        if self.use_torch:
            self.model.eval()
            with torch.no_grad():
                out = self.model(torch.tensor(seq_arr, dtype=torch.float32)).numpy()[0]
        else:
            out = self.numpy_model.forward(seq_arr)[0]

        pred_t1, pred_h1 = self._denormalize(out[0], out[1])

        # 2. Predicción autoregresiva a +5 pasos (Multi-step forecast)
        sim_seq = deque(current_seq, maxlen=self.input_dim)
        fut_out = out.copy()
        for _ in range(5):
            # Insertar última predicción normalizada
            sim_seq.append(fut_out[0])
            sim_seq.append(fut_out[1])
            s_arr = np.array([list(sim_seq)], dtype=np.float32)
            if self.use_torch:
                with torch.no_grad():
                    fut_out = self.model(torch.tensor(s_arr, dtype=torch.float32)).numpy()[0]
            else:
                fut_out = self.numpy_model.forward(s_arr)[0]

        pred_t5, pred_h5 = self._denormalize(fut_out[0], fut_out[1])

        pred_next = {"temp": pred_t1, "hum": pred_h1}
        pred_future = {"temp": pred_t5, "hum": pred_h5}

        return pred_next, pred_future

    def get_intelligence_level(self) -> Dict[str, Any]:
        """Calcula el porcentaje de nivel de inteligencia y estado del modelo."""
        # Un nivel de inteligencia basado en muestras procesadas y error (loss)
        # 0 muestras -> 0%, 100+ muestras -> 95%+ conforme la pérdida cae
        sample_score = min(70.0, (self.trained_samples_count / 150.0) * 70.0)
        loss_score = max(0.0, (1.0 - min(1.0, self.current_loss * 50.0)) * 30.0)
        intelligence = round(sample_score + loss_score, 1)

        return {
            "intelligence_percentage": intelligence,
            "trained_samples": self.trained_samples_count,
            "epochs": self.epochs_completed,
            "current_loss": self.current_loss,
            "status": "Aprendiendo en Vivo" if self.trained_samples_count > 0 else "Inicializando Red",
        }

    def get_ai_agent_summary(self, current_temp: float, current_hum: float) -> Dict[str, Any]:
        """Genera un reporte resumido estructurado diseñado para ser consumido por un Agente IA (LLM)."""
        pred_next, pred_future = self.predict_future()
        intel = self.get_intelligence_level()

        # Determinación de tendencias
        temp_trend = "Estable"
        hum_trend = "Estable"
        if pred_future:
            t_diff = pred_future["temp"] - current_temp
            h_diff = pred_future["hum"] - current_hum
            if t_diff > 0.4:
                temp_trend = f"En Aumento (+{round(t_diff, 1)}°C predicho a 5min)"
            elif t_diff < -0.4:
                temp_trend = f"En Descenso ({round(t_diff, 1)}°C predicho a 5min)"

            if h_diff > 1.5:
                hum_trend = f"En Aumento (+{round(h_diff, 1)}% predicho a 5min)"
            elif h_diff < -1.5:
                hum_trend = f"En Descenso ({round(h_diff, 1)}% predicho a 5min)"

        return {
            "nn_architecture": "MLP (10 -> 32 -> 16 -> 2)",
            "motor": "PyTorch Accelerated" if self.use_torch else "NumPy Engine",
            "intelligence_level": f"{intel['intelligence_percentage']}%",
            "trained_samples": self.trained_samples_count,
            "mse_loss": self.current_loss,
            "current_conditions": {"temp": current_temp, "hum": current_hum},
            "predictions": {
                "next_step": pred_next,
                "future_5steps": pred_future,
            },
            "trends": {
                "temp_trend": temp_trend,
                "hum_trend": hum_trend,
            },
            "ai_insights": (
                f"Red Neuronal SIMA activa con {self.trained_samples_count} muestras aprendidas. "
                f"Proyección a corto plazo: Temperatura {temp_trend.lower()} y Humedad {hum_trend.lower()}."
            )
        }

    def save_model(self) -> bool:
        """Persiste los pesos de la red neuronal y las métricas en disco."""
        try:
            meta = {
                "trained_samples_count": self.trained_samples_count,
                "epochs_completed": self.epochs_completed,
                "current_loss": self.current_loss,
                "learning_rate": self.learning_rate,
                "use_torch": self.use_torch,
            }

            if self.use_torch:
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "meta": meta
                }, self.model_file)
            else:
                meta["weights"] = self.numpy_model.get_weights_dict()
                with open(self.json_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)

            logger.info("Pesos de la Red Neuronal guardados exitosamente (%d muestras)", self.trained_samples_count)
            return True
        except Exception as e:
            log_exception(e, "Error al guardar el modelo de Red Neuronal")
            return False

    def _load_saved_model(self) -> bool:
        """Carga el modelo guardado si existe."""
        try:
            if self.use_torch and self.model_file.exists():
                checkpoint = torch.load(self.model_file)
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
                meta = checkpoint.get("meta", {})
                self.trained_samples_count = meta.get("trained_samples_count", 0)
                self.epochs_completed = meta.get("epochs_completed", 0)
                self.current_loss = meta.get("current_loss", 1.0)
                logger.info("Modelo de Red Neuronal PyTorch cargado (%d muestras previas)", self.trained_samples_count)
                return True

            elif not self.use_torch and self.json_file.exists():
                with open(self.json_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self.trained_samples_count = meta.get("trained_samples_count", 0)
                self.epochs_completed = meta.get("epochs_completed", 0)
                self.current_loss = meta.get("current_loss", 1.0)
                if "weights" in meta:
                    self.numpy_model.load_weights_dict(meta["weights"])
                logger.info("Modelo de Red Neuronal NumPy cargado (%d muestras previas)", self.trained_samples_count)
                return True
        except Exception as e:
            log_exception(e, "No se pudo cargar checkpoint previo de la Red Neuronal")
        return False

    def reset_model(self) -> None:
        """Reinicia los pesos y el historial de aprendizaje de la red."""
        if self.use_torch:
            self.model = PyTorchEnvironmentalNN(self.input_dim, 32, 16, self.output_dim)
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        else:
            self.numpy_model = NumPyEnvironmentalNN(self.input_dim, 32, 16, self.output_dim)

        self.history_buffer.clear()
        self.trained_samples_count = 0
        self.epochs_completed = 0
        self.current_loss = 1.0
        self.loss_history.clear()
        logger.info("Red Neuronal reiniciada a sus pesos iniciales.")
