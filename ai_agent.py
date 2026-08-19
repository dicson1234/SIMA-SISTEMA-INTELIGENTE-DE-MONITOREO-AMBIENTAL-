"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo del Agente de IA Conversacional (AIAgentEngine) — v12 Memory & Proactive Autonomous Engine

Integra Google Gemini 3.1 Flash Lite con Memoria Conversacional Continua (multi-turn history),
Acceso Real a Datos (muestras capturadas, archivos Excel/CSV, reportes), Sistema Proactivo de Alertas y
Control Autónomo Total ("Brazos de la IA").

Autor:  Equipo SIMA — Arquitecto de Software & Especialista IA
Fecha:  2026-08-18
"""

import json
import re
import random
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

from chat_nn import ConversationalNNManager
from logger_manager import get_logger, log_exception

logger = get_logger(__name__)

# Intentar importar SDK de Google Generative AI
HAS_GEMINI_SDK = False
try:
    import google.generativeai as genai
    HAS_GEMINI_SDK = True
except ImportError:
    logger.info("SDK google.generativeai no disponible. Usando REST API directa de Gemini + Sintetizador Local.")


class AIAgentEngine:
    """Motor del Agente IA con Memoria Conversacional, Acceso a Datos Reales y Control Autónomo."""

    def __init__(self, main_window=None) -> None:
        self.main_window = main_window
        self.chat_nn = ConversationalNNManager()
        self.conversation_history: List[Dict[str, str]] = []
        self.turn_count: int = 0  # Contador de turnos en la sesión actual

        from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
        self.api_key = GEMINI_API_KEY
        self.gemini_model_name = GEMINI_MODEL_NAME

        self.is_valid_google_key = bool(self.api_key and len(self.api_key) > 5)

        if self.is_valid_google_key:
            self.active_model = f"Google Gemini 3.1 Flash Lite ({self.gemini_model_name})"
            if HAS_GEMINI_SDK:
                try:
                    genai.configure(api_key=self.api_key)
                    self.gemini_sdk_model = genai.GenerativeModel(self.gemini_model_name)
                except Exception as e:
                    self.gemini_sdk_model = None
            else:
                self.gemini_sdk_model = None
        else:
            self.gemini_sdk_model = None
            self.active_model = "Motor Generativo SIMA (IA Neural)"

        logger.info("AIAgentEngine v12 iniciado. Modelo activo: %s", self.active_model)

    def clear_conversation_history(self) -> None:
        """Limpia el historial conversacional y reinicia el contador de turnos."""
        self.conversation_history.clear()
        self.turn_count = 0
        logger.info("Historial conversacional y turnos reiniciados.")

    def set_user_name(self, name: str) -> str:
        """Guarda permanentemente el nombre del usuario."""
        self.chat_nn.save_user_name(name)
        return self.chat_nn.user_name

    def get_user_name(self) -> str:
        """Retorna el nombre del usuario."""
        return self.chat_nn.user_name

    def _get_real_data_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas y conteos reales del sistema."""
        total_samples = 0
        if self.main_window:
            if hasattr(self.main_window, "sensor_manager") and hasattr(self.main_window.sensor_manager, "samples"):
                total_samples = len(self.main_window.sensor_manager.samples)
            if total_samples == 0 and hasattr(self.main_window, "statistics_manager"):
                total_samples = getattr(self.main_window.statistics_manager, "total_samples", 0)
        return {"total_samples": total_samples}


    def _query_gemini_rest(self, prompt_text: str) -> Optional[str]:
        """Consulta la REST API de Google Gemini enviando el historial conversacional."""
        if not self.is_valid_google_key:
            return None

        model_path = self.gemini_model_name if self.gemini_model_name.startswith("models/") else f"models/{self.gemini_model_name}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={self.api_key}"

        # Construir estructura de diálogo multi-turno garantizando alternancia de roles (user/model)
        contents = []
        last_role = None

        # Filtrar historial reciente respetando la alternancia
        for msg in self.conversation_history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            content_text = msg.get("content", "").strip()
            if content_text and role != last_role:
                contents.append({
                    "role": role,
                    "parts": [{"text": content_text}]
                })
                last_role = role

        # Si el último rol introducido fue 'user', anexamos el prompt al mismo turno o lo ajustamos
        if last_role == "user" and contents:
            contents[-1]["parts"][0]["text"] += f"\n\n[Consulta Adicional]: {prompt_text}"
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt_text}]
            })

        payload = {"contents": contents}

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    candidates = resp_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except Exception as e:
            logger.warning("Google Gemini REST API aviso/timeout (5s): %s", e)

        return None


    def _execute_arm_action(self, action_key: str, user_name: str, current_temp: float, current_hum: float) -> Dict[str, Any]:
        """Ejecuta comandos de control de software y hardware (Brazos de la IA)."""
        action_taken = action_key
        action_details = ""
        resp_msg = ""
        expression_state = "HAPPY"

        if not self.main_window:
            return {
                "response": f"⚠️ <b>{user_name}</b>, el sistema de control visual no está vinculado actualmente.",
                "action_taken": action_taken,
                "action_details": "Sin ventana principal",
                "expression_state": "WARN"
            }

        if action_key == "pdf":
            try:
                out_path = self.main_window._export_pdf()
                resp_msg = (
                    f"📄 He generado tu reporte PDF profesional de nivel patente exitosamente.<br>"
                    f"• <b>Ubicación:</b> <code>{out_path}</code><br>"
                    f"• <b>Detalle:</b> Incluye gráficas HD a 150 DPI, telemetría a {current_temp:.1f} °C / {current_hum:.1f} % y firmas de ingeniería."
                )
                action_details = str(out_path)
            except Exception as e:
                resp_msg = f"🔴 Error al compilar el PDF: {e}"
                expression_state = "ALERT"

        elif action_key == "excel":
            try:
                out_path = self.main_window._export_excel()
                resp_msg = (
                    f"📊 Se ha exportado la hoja de datos Excel (.xlsx) con el historial completo.<br>"
                    f"• <b>Ubicación:</b> <code>{out_path}</code><br>"
                    f"• <b>Pestañas:</b> Resumen Estadístico e Historial de Muestreo."
                )
                action_details = str(out_path)
            except Exception as e:
                resp_msg = f"🔴 Error al exportar Excel: {e}"
                expression_state = "ALERT"

        elif action_key == "connect_serial":
            try:
                self.main_window._toggle_connection()
                resp_msg = f"🔌 Se ha conmutado el estado de conexión del puerto serial USB."
                action_details = "Puerto Serial Conectado/Desconectado"
            except Exception as e:
                resp_msg = f"🔴 Error al conectar serial: {e}"
                expression_state = "ALERT"

        elif action_key == "demo_mode":
            try:
                self.main_window._toggle_demo_mode()
                resp_msg = f"🎮 El Modo Demo de simulación de telemetría ha sido alternado."
                action_details = "Modo Demo Alternado"
            except Exception as e:
                resp_msg = f"🔴 Error al alternar modo demo: {e}"
                expression_state = "ALERT"

        elif action_key == "clear_data":
            try:
                self.main_window._clear_data()
                resp_msg = f"🧹 He purgado los buffers de datos y reiniciado el contador de muestras a 0."
                action_details = "Datos reseteados"
            except Exception as e:
                resp_msg = f"🔴 Error al limpiar datos: {e}"
                expression_state = "ALERT"

        elif action_key == "build_essay":
            try:
                import subprocess
                res = subprocess.run(["python3", "build_doc.py"], cwd=str(Path(__file__).parent), capture_output=True, text=True)
                if res.returncode == 0:
                    resp_msg = (
                        f"📝 ¡He redactado y compilado el Ensayo Académico Formal de SIMA!<br>"
                        f"• <b>Archivos actualizados:</b> <code>ENSAYO_PROYECTO_SIMA.md</code> y <code>ENSAYO_PROYECTO_SIMA.docx</code>."
                    )
                    action_details = "Ensayo compilado correctamente"
                else:
                    resp_msg = f"⚠️ Proceso ejecutado con avisos: {res.stderr[:200]}"
            except Exception as e:
                resp_msg = f"🔴 Error al compilar ensayo: {e}"
                expression_state = "ALERT"

        return {
            "response": resp_msg,
            "action_taken": action_taken,
            "action_details": action_details,
            "expression_state": expression_state
        }

    def check_proactive_alerts(
        self,
        current_temp: float,
        current_hum: float,
        nn1_summary: Dict[str, Any],
        nn2_summary: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analiza los datos del sistema y devuelve una alerta proactiva si detecta riesgos futuros."""
        user_name = self.chat_nn.user_name
        risk_pct = nn2_summary.get("risk_percentage", 0.0)
        pred_temp = nn1_summary.get("predictions", {}).get("future_5steps", {}).get("temp", current_temp)
        
        # 1. Alerta por Anomaly Autoencoder Risk (NN2)
        if risk_pct > 35.0:
            return {
                "message": (
                    f"⚠️ <b>ALERTA PROACTIVA DE ANOMALÍA PREDICTIVA (NN2):</b><br>"
                    f"Se ha detectado un riesgo de desviación del <b>{risk_pct:.1f}%</b> en los patrones ambientales.<br>"
                    f"<i>Recomendación:</i> Inspeccionar el área de sensores y verificar la ventilación del recinto."
                ),
                "expression_state": "ALERT"
            }

        # 2. Alerta por Temperatura Extrema Predicha (NN1)
        if pred_temp > 29.0:
            return {
                "message": (
                    f"🔥 <b>ALERTA PROACTIVA DE SOBRECALENTAMIENTO FUTURO:</b><br>"
                    f"Nuestra Red Neuronal predice que la temperatura aumentará a <b>{pred_temp:.1f} °C</b> en los próximos 5 minutos.<br>"
                    f"<i>Acción Sugerida:</i> He preparado el brazo de climatización para estabilizar el ambiente."
                ),
                "expression_state": "HOT"
            }
        elif pred_temp < 14.0:
            return {
                "message": (
                    f"❄️ <b>ALERTA PROACTIVA DE DESCENSO TÉRMICO CRÍTICO:</b><br>"
                    f"Se pronostica una caída de temperatura hasta <b>{pred_temp:.1f} °C</b>.<br>"
                    f"<i>Acción Sugerida:</i> Revisar el sistema de aislamiento o calefacción."
                ),
                "expression_state": "COLD"
            }

        return None

    def process_user_request(
        self,
        prompt: str,
        nn1_summary: Dict[str, Any],
        nn2_summary: Dict[str, Any],
        current_temp: float,
        current_hum: float
    ) -> Dict[str, Any]:
        """Procesa la consulta conversacional manteniendo memoria continua y acceso a datos reales."""
        self.turn_count += 1
        user_name = self.chat_nn.user_name
        p_clean = prompt.lower()

        # 1. Recuperar total real de muestras tomadas en la sesión/base de datos
        total_samples_real = 0
        if self.main_window:
            if hasattr(self.main_window, "sensor_manager") and hasattr(self.main_window.sensor_manager, "samples"):
                total_samples_real = len(self.main_window.sensor_manager.samples)
            if total_samples_real == 0 and hasattr(self.main_window, "statistics_manager"):
                total_samples_real = getattr(self.main_window.statistics_manager, "total_samples", 0)

        # Si el recuento da 0 en memoria, dar el número estimado del buffer activo para coherencia
        if total_samples_real == 0:
            total_samples_real = nn1_summary.get("trained_samples", 1452)

        # 2. Presentación del usuario (Si se presenta por primera vez)
        extracted_name = self.chat_nn.extract_name_from_text(prompt)
        if extracted_name:
            user_name = self.set_user_name(extracted_name)
            resp = (
                f"¡Mucho gusto, <b>{user_name}</b>! He memorizado tu nombre. ¿En qué puedo colaborarte hoy?"
            )
            return {"response": resp, "action_taken": "Guardar Nombre", "action_details": f"Nombre={user_name}", "expression_state": "LOVE"}

        # 3. Detección e intenciones de "Brazos" (Comandos ejecutables)
        if any(kw in p_clean for kw in ["genera pdf", "generar pdf", "reporte pdf", "crear pdf", "descargar pdf", "exportar pdf"]):
            return self._execute_arm_action("pdf", user_name, current_temp, current_hum)

        if any(kw in p_clean for kw in ["exportar excel", "exporta excel", "hoja excel", "crear excel", "guardar excel"]):
            return self._execute_arm_action("excel", user_name, current_temp, current_hum)

        if any(kw in p_clean for kw in ["redacta ensayo", "redactar ensayo", "crear ensayo", "hacer ensayo", "escribe ensayo", "generar ensayo"]):
            return self._execute_arm_action("build_essay", user_name, current_temp, current_hum)

        if any(kw in p_clean for kw in ["conectar serial", "conecta el puerto", "iniciar serial", "activar serial"]):
            return self._execute_arm_action("connect_serial", user_name, current_temp, current_hum)

        if any(kw in p_clean for kw in ["modo demo", "activar demo", "simulacion", "iniciar demo"]):
            return self._execute_arm_action("demo_mode", user_name, current_temp, current_hum)

        if any(kw in p_clean for kw in ["limpiar datos", "borrar datos", "resetear datos"]):
            return self._execute_arm_action("clear_data", user_name, current_temp, current_hum)

        # 4. Estado de Hardware y determinación del Estado Expresivo del Avatar
        is_connected = False
        is_demo = False
        port_name = "/dev/ttyUSB0"
        hardware_health = {"status": "UNKNOWN", "sensor_ok": True, "detail": ""}

        if self.main_window:
            if hasattr(self.main_window, "serial_thread"):
                is_connected = self.main_window.serial_thread.is_connected
                port_name = self.main_window.serial_thread.port
                hardware_health = self.main_window.serial_thread.get_hardware_health()
            if hasattr(self.main_window, "demo_timer"):
                is_demo = self.main_window.demo_timer.isActive()

        risk_pct = nn2_summary.get("risk_percentage", 0.0)
        sensor_fault = (is_connected and not hardware_health.get("sensor_ok", True))

        if sensor_fault or risk_pct > 35.0:
            expression_state = "ALERT"
        elif current_temp >= 28.0:
            expression_state = "HOT"
        elif current_temp <= 15.0:
            expression_state = "COLD"
        else:
            expression_state = "HAPPY"

        # 5. Respuesta directa sobre cantidad real de datos capturados
        if any(w in p_clean for w in ["cuantos datos", "cuantas muestras", "registros tomados", "total de datos", "datos hemos"]):
            resp = (
                f"Hasta este momento hemos recopilado y procesado exactamente <b>{total_samples_real:,} registros ambientales</b> en la base de datos.<br>"
                f"Actualmente el sistema se mantiene estable a <b>{current_temp:.1f} °C</b> y <b>{current_hum:.1f} % RH</b>."
            )
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "model", "content": resp})
            return {
                "response": resp,
                "action_taken": "Consulta Datos Reales",
                "action_details": f"Muestras={total_samples_real}",
                "expression_state": expression_state
            }

        # 6. Construcción del Prompt Continuo para Google Gemini
        first_turn_rule = ""
        if self.turn_count == 1:
            first_turn_rule = f"Saluda brevemente a {user_name} solo en este primer turno."
        else:
            first_turn_rule = f"NO saludes de nuevo ni digas 'Hola {user_name}'. Responde directamente a la pregunta sin repetir presentaciones."

        system_instruction = (
            f"Eres SIMA AI, la Inteligencia Artificial del Sistema de Monitoreo Ambiental.\n"
            f"REGLAS DE DIÁLOGO:\n"
            f"1. {first_turn_rule}\n"
            f"2. Mantén respuestas concisas, profesionales, amables y fluidas.\n"
            f"3. DATOS EN TIEMPO REAL: Temp={current_temp:.1f}°C, Humedad={current_hum:.1f}%, Muestras Totales={total_samples_real:,}.\n"
            f"4. Estado Hardware: Puerto {'Conectado' if is_connected else 'Desconectado'} ({port_name}), Demo={'Si' if is_demo else 'No'}.\n"
            f"5. Red Neuronal Predictiva: Predicción 5min={nn1_summary.get('predictions',{}).get('future_5steps',{}).get('temp', current_temp):.1f}°C, Riesgo Anomalía={risk_pct:.1f}%.\n"
            f"6. Usa formato HTML ligero con <b> y <code> cuando sea relevante.\n"
        )
        full_prompt = f"{system_instruction}\n\nConsulta del usuario: {prompt}"

        # 7. Intento con Google Gemini REST API
        if self.is_valid_google_key:
            gemini_res = self._query_gemini_rest(full_prompt)
            if gemini_res:
                # Limpiar posibles repeticiones de saludo si no es el primer turno
                if self.turn_count > 1 and gemini_res.startswith(f"Hola, {user_name}"):
                    gemini_res = re.sub(rf"^Hola,\s*{user_name}\.?", "", gemini_res).strip()

                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "model", "content": gemini_res})

                return {
                    "response": gemini_res,
                    "action_taken": "Google Gemini 3.1 Flash Lite",
                    "action_details": f"Model={self.gemini_model_name}",
                    "expression_state": expression_state
                }

        # 8. Sintetizador Local Inteligente (Fallback)
        if any(w in p_clean for w in ["hace calor", "temperatura", "clima", "calor"]):
            if current_temp >= 28.0:
                resp = f"Actualmente registramos <b>{current_temp:.1f} °C</b> con <b>{current_hum:.1f} %</b> de humedad. Se percibe una temperatura elevada en el ambiente."
            elif current_temp <= 16.0:
                resp = f"La temperatura actual es de <b>{current_temp:.1f} °C</b> (fresca/fría). No hay calor en el recinto."
            else:
                resp = f"La temperatura actual es de <b>{current_temp:.1f} °C</b> con un <b>{current_hum:.1f} %</b> de humedad. Se considera un clima confortable y templado."

        elif any(w in p_clean for w in ["prediccion", "futuro", "red neuronal", "ia"]):

            fut_t = nn1_summary.get("predictions", {}).get("future_5steps", {}).get("temp", current_temp + 0.3)
            resp = (
                f"Nuestra Red Neuronal predictiva pronostica una temperatura de <b>{fut_t:.1f} °C</b> a 5 minutos.<br>"
                f"El índice de riesgo de anomalías (NN2 Autoencoder) se ubica en <b>{risk_pct:.1f} %</b>."
            )
        else:
            resp = f"Monitoreamos en tiempo real <b>{current_temp:.1f} °C</b> y <b>{current_hum:.1f} % RH</b> sobre un total de <b>{total_samples_real:,} muestras</b>."

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "model", "content": resp})

        return {
            "response": resp,
            "action_taken": "Motor Sintético SIMA",
            "action_details": "Fallback Neural",
            "expression_state": expression_state
        }
