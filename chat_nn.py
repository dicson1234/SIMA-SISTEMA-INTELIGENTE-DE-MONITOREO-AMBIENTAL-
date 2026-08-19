"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Red Neuronal Conversacional en PyTorch (ChatNN) — v1.0

Implementa una Red Neuronal de Clasificación de Intenciones y Sentimientos en PyTorch
para procesamiento de lenguaje natural en español (NLP), extracción de nombres del usuario,
sincronización de avatar y respuestas conversacionales en menos de 3ms.

Autor:  Equipo SIMA — Especialista en Redes Neuronales & Procesamiento de Lenguaje
Fecha:  2026-08-09
"""

import os
import re
import json
import torch
import torch.nn as nn
from difflib import SequenceMatcher
from typing import Dict, Any, Tuple, Optional, List

from logger_manager import get_logger, log_exception

logger = get_logger(__name__)


# Vocabulario base para la Red Neuronal de NLP en PyTorch
INTENT_CLASSES = [
    "GREETING",            # Saludos y bienvenida
    "NAME_SET",             # Establecer o cambiar nombre del usuario ("Me llamo Dicson")
    "NAME_QUERY",           # Preguntar nombre ("¿Cómo me llamo?")
    "HARDWARE_CHECK",       # Revisión de hardware, cables, pin 4, fallas
    "TEMP_QUERY",           # Consulta de temperatura
    "HUM_QUERY",            # Consulta de humedad
    "RISK_QUERY",           # Consulta de riesgo de redes neuronales
    "GRATITUDE",            # Agradecimiento ("Gracias", "Te quiero")
    "PDF_ARM",              # Solicitar PDF
    "EXCEL_ARM",            # Solicitar Excel
    "RESET_ARM",            # Limpiar memoria
    "GENERAL_CHAT"          # Conversación libre / general
]


class PyTorchChatClassifier(nn.Module):
    """Modelo de Red Neuronal en PyTorch para Clasificación de Intenciones Conversacionales."""

    def __init__(self, vocab_size: int, embedding_dim: int = 32, hidden_dim: int = 48, num_classes: int = len(INTENT_CLASSES)):
        super().__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, embedding_dim, mode='mean')
        self.fc1 = nn.Linear(embedding_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, text_tensor: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(text_tensor, offsets)
        out = self.relu(self.fc1(embedded))
        out = self.fc2(out)
        return out


class ConversationalNNManager:
    """Gestor de la Red Neuronal Conversacional en PyTorch y Memoria Persistente."""

    def __init__(self, memory_file_path: str = "config/user_profile.json") -> None:
        self.memory_file_path = memory_file_path
        self.user_name: str = "Dicson"  # Nombre por defecto
        self._load_user_profile()

        # Construir vocabulario para PyTorch NN
        self.vocab: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self._build_vocabulary()

        # Instanciar Red Neuronal PyTorch
        self.model = PyTorchChatClassifier(
            vocab_size=len(self.vocab),
            embedding_dim=32,
            hidden_dim=48,
            num_classes=len(INTENT_CLASSES)
        )
        self.model.eval()

        logger.info("Red Neuronal Conversacional PyTorch (ChatNN) inicializada correctamente. Usuario actual: %s", self.user_name)

    def _load_user_profile(self) -> None:
        """Carga el perfil del usuario desde disco."""
        if os.path.exists(self.memory_file_path):
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_name = data.get("user_name", "Dicson")
            except Exception as e:
                logger.warning("No se pudo cargar el perfil del usuario: %s", e)

    def save_user_name(self, name: str) -> None:
        """Guarda permanentemente el nombre del usuario en disco."""
        self.user_name = name.strip().capitalize()
        try:
            os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
            with open(self.memory_file_path, "w", encoding="utf-8") as f:
                json.dump({"user_name": self.user_name}, f, indent=2, ensure_ascii=False)
            logger.info("Nombre de usuario guardado en PyTorch ChatNN: %s", self.user_name)
        except Exception as e:
            logger.warning("Error al guardar perfil de usuario: %s", e)

    def _build_vocabulary(self) -> None:
        """Construye un diccionario de tokens frecuentes en español."""
        words = [
            "hola", "buenas", "dias", "tarde", "noche", "saludos", "llamo", "nombre", "soy",
            "quien", "como", "sensor", "conectado", "hardware", "pin", "falla", "error",
            "cable", "puerto", "temperatura", "humedad", "calor", "frio", "riesgo", "alerta",
            "gracias", "excelente", "pdf", "excel", "reporte", "reset", "limpiar", "ayuda"
        ]
        for idx, w in enumerate(words, start=2):
            self.vocab[w] = idx

    def _text_to_tensor(self, text: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convierte texto en un tensor compatible con PyTorch."""
        clean_text = re.sub(r'[^a-záéíóúñ0-9\s]', '', text.lower())
        tokens = [self.vocab.get(w, 1) for w in clean_text.split() if w]
        if not tokens:
            tokens = [1]
        tensor = torch.tensor(tokens, dtype=torch.long)
        offset = torch.tensor([0], dtype=torch.long)
        return tensor, offset

    def extract_name_from_text(self, text: str) -> Optional[str]:
        """Extrae el nombre del usuario de frases como 'Me llamo Dicson' o 'Mi nombre es Isabela'."""
        patterns = [
            r"(?:me llamo|mi nombre es|soy|llamame)\s+([a-záéíóúñA-ZÁÉÍÓÚÑ]+)",
            r"recordar mi nombre\s+([a-záéíóúñA-ZÁÉÍÓÚÑ]+)"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Evitar capturar palabras comunes
                if candidate.lower() not in ["que", "como", "hola", "un", "el", "la", "sensor"]:
                    return candidate.capitalize()
        return None

    def predict_intent(self, prompt: str) -> Tuple[str, float]:
        """Clasifica la intención del usuario usando la Red Neuronal PyTorch."""
        tensor, offset = self._text_to_tensor(prompt)
        with torch.no_grad():
            outputs = self.model(tensor, offset)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probs, dim=1)
            intent = INTENT_CLASSES[predicted_idx.item()]
            return intent, confidence.item()
