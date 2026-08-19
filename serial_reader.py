"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Módulo de Lectura Serial

Implementa un hilo dedicado (QThread) para la lectura continua
del puerto serial. Parsea el protocolo SIMA y emite señales Qt
que la capa de presentación consume de forma thread-safe.

Responsabilidades:
    - Abrir y mantener la conexión serial con Arduino.
    - Leer líneas de datos continuamente sin bloquear la UI.
    - Parsear el protocolo SIMA (datos, control, errores).
    - Emitir señales tipadas para cada tipo de evento.
    - Reconectar automáticamente si se pierde la conexión.
    - Manejar todas las excepciones sin cerrar la aplicación.

Señales emitidas:
    - new_data(float, float)      → Nueva lectura válida.
    - connection_changed(bool)    → Cambio de estado de conexión.
    - error_occurred(str)         → Error en comunicación serial.
    - status_received(str)        → Mensaje de estado del firmware.
    - protocol_info(str)          → Información del protocolo SIMA.

Autor:  Equipo SIMA — Ingeniero IoT
Fecha:  2026-07-14
"""

import time
from typing import List, Optional

import serial
from PySide6.QtCore import QThread, Signal

from config import (
    DEFAULT_PORT,
    DEFAULT_BAUDRATE,
    SERIAL_TIMEOUT,
    SERIAL_ENCODING,
    PROTOCOL_CONTROL_PREFIX,
    PROTOCOL_SEPARATOR,
    RECONNECT_INTERVAL,
    MAX_RECONNECT_ATTEMPTS,
)
from logger_manager import get_logger, log_serial_event

# Logger del módulo
logger = get_logger(__name__)


class SerialReader(QThread):
    """Hilo de lectura serial para el sistema SIMA.

    Lee continuamente el puerto serial en un hilo separado,
    parsea el protocolo SIMA y emite señales Qt que la ventana
    principal consume para actualizar la interfaz.

    El hilo maneja automáticamente:
        - Apertura y cierre seguro del puerto.
        - Reconexión automática con backoff si se pierde la conexión.
        - Parseo defensivo de líneas (descarta datos malformados).
        - Limpieza del buffer serial al conectar.

    Signals:
        new_data: Emitida cuando se recibe una lectura válida.
            Parámetros: (temperatura: float, humedad: float).
        connection_changed: Emitida cuando cambia el estado de conexión.
            Parámetro: (connected: bool).
        error_occurred: Emitida cuando ocurre un error de comunicación.
            Parámetro: (message: str).
        status_received: Emitida cuando Arduino envía un mensaje de estado.
            Parámetro: (status: str). Ej: "READY", "STABLE".
        protocol_info: Emitida cuando se recibe la cabecera del protocolo.
            Parámetro: (info: str). Ej: "v1:TEMP,HUM".

    Example:
        >>> reader = SerialReader()
        >>> reader.new_data.connect(on_new_data)
        >>> reader.connection_changed.connect(on_connection_change)
        >>> reader.configure(port="/dev/ttyUSB0", baudrate=9600)
        >>> reader.start()
        >>> # ... más tarde ...
        >>> reader.stop()
    """

    # =================================================================
    #  SEÑALES QT
    # =================================================================

    # Señal emitida con cada lectura válida: (temperatura, humedad, luz)
    new_data = Signal(float, float, float)

    # Señal emitida al cambiar el estado de conexión: (conectado)
    connection_changed = Signal(bool)

    # Señal emitida cuando ocurre un error: (mensaje)
    error_occurred = Signal(str)

    # Señal emitida con mensajes de estado del firmware: (estado)
    status_received = Signal(str)

    # Señal emitida con información del protocolo: (info)
    protocol_info = Signal(str)

    # =================================================================
    #  INICIALIZACIÓN
    # =================================================================

    def __init__(self, parent=None) -> None:
        """Inicializa el lector serial.

        Args:
            parent: Widget padre de Qt (opcional).
        """
        super().__init__(parent)

        # Parámetros de conexión (configurables antes de start())
        self._port: str = DEFAULT_PORT
        self._baudrate: int = DEFAULT_BAUDRATE

        # Estado interno
        self._serial: Optional[serial.Serial] = None
        self._running: bool = False
        self._connected: bool = False
        self._reconnect_count: int = 0
        self._last_data_timestamp: float = 0.0
        self._last_hardware_error: Optional[str] = None

        logger.info("SerialReader inicializado")

    # =================================================================
    #  CONFIGURACIÓN
    # =================================================================

    def configure(self, port: str, baudrate: int) -> None:
        """Configura los parámetros de conexión serial.

        Debe llamarse ANTES de start(). Si se llama mientras el
        hilo está corriendo, los cambios se aplican en la próxima
        reconexión.

        Args:
            port: Ruta del puerto serial (ej: "/dev/ttyUSB0").
            baudrate: Velocidad en baudios (ej: 9600).
        """
        self._port = port
        self._baudrate = baudrate
        logger.info(
            "SerialReader configurado: %s @ %d baud",
            port, baudrate,
        )

    @property
    def is_connected(self) -> bool:
        """Indica si el puerto serial está conectado y abierto.

        Returns:
            True si la conexión serial está activa.
        """
        return self._connected

    @property
    def port(self) -> str:
        """Retorna el puerto serial configurado.

        Returns:
            Ruta del puerto serial.
        """
        return self._port

    @property
    def baudrate(self) -> int:
        """Retorna la velocidad de baudios configurada.

        Returns:
            Velocidad en baudios.
        """
        return self._baudrate

    # =================================================================
    #  CONTROL DEL HILO
    # =================================================================

    def start(self, priority=QThread.InheritPriority) -> None:
        """Inicia la lectura serial en un hilo separado.

        Sobreescribe QThread.start() para establecer la bandera
        de ejecución antes de lanzar el hilo. Esto garantiza que
        el bucle while self._running se ejecute correctamente
        independientemente de si se llama start() o start_reading().

        Args:
            priority: Prioridad del hilo Qt (por defecto hereda del padre).
        """
        if self.isRunning():
            logger.warning("SerialReader ya está en ejecución")
            return

        self._running = True
        self._reconnect_count = 0
        super().start(priority)
        logger.info("SerialReader iniciado")

    def stop(self) -> None:
        """Detiene la lectura serial de forma segura.

        Establece la bandera de parada y espera a que el hilo
        termine limpiamente. Cierra el puerto serial si está abierto.
        """
        if not self.isRunning():
            return

        logger.info("Deteniendo SerialReader...")
        self._running = False

        # Esperar a que el hilo termine (máximo 5 segundos)
        if not self.wait(5000):
            logger.warning(
                "SerialReader no terminó en 5s — Forzando terminación"
            )
            self.terminate()
            self.wait(2000)

        self._close_port()
        self._connected = False
        self.connection_changed.emit(False)
        logger.info("SerialReader detenido")

    # Aliases para compatibilidad con el código existente
    start_reading = start
    stop_reading = stop

    # =================================================================
    #  BUCLE PRINCIPAL (EJECUTADO EN EL HILO)
    # =================================================================

    def run(self) -> None:
        """Bucle principal del hilo de lectura serial.

        Este método es ejecutado automáticamente por QThread.start().
        NO debe llamarse directamente.

        Flujo:
            1. Intentar conectar al puerto serial.
            2. Si se conecta: leer líneas continuamente.
            3. Si falla o se desconecta: intentar reconectar.
            4. Repetir hasta que se llame stop_reading().
        """
        logger.info(
            "Hilo serial iniciado — %s @ %d baud",
            self._port, self._baudrate,
        )

        while self._running:
            try:
                # Intentar conectar si no estamos conectados
                if not self._connected:
                    if not self._connect():
                        # Esperar antes de reintentar
                        self._wait_reconnect()
                        continue

                # Leer una línea del puerto serial
                self._read_line()

            except serial.SerialException as e:
                self._handle_disconnect(
                    f"Error serial: {e}"
                )

            except OSError as e:
                self._handle_disconnect(
                    f"Error de sistema: {e}"
                )

            except Exception as e:
                # Captura genérica — NUNCA debe morir el hilo
                logger.error(
                    "Error inesperado en hilo serial: %s — %s",
                    type(e).__name__, str(e),
                    exc_info=True,
                )
                self._handle_disconnect(
                    f"Error inesperado: {type(e).__name__}"
                )

        # Limpieza al salir del bucle
        self._close_port()
        logger.info("Hilo serial finalizado")

    # =================================================================
    #  CONEXIÓN
    # =================================================================

    def _connect(self) -> bool:
        """Intenta abrir la conexión con el puerto serial.

        Configura el puerto con los parámetros establecidos,
        limpia el buffer y espera un breve momento para que
        Arduino complete su reset (DTR).

        Returns:
            True si la conexión se estableció exitosamente.
        """
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=SERIAL_TIMEOUT,
                write_timeout=SERIAL_TIMEOUT,
            )

            # Arduino se resetea al abrir el puerto (DTR).
            # Esperamos a que el bootloader termine y el firmware
            # envíe la cabecera del protocolo.
            time.sleep(2.0)

            # Limpiar cualquier dato residual en el buffer
            self._serial.reset_input_buffer()

            # Marcar como conectado
            self._connected = True
            self._reconnect_count = 0

            log_serial_event(
                "CONECTADO",
                f"{self._port} @ {self._baudrate} baud",
            )
            self.connection_changed.emit(True)

            return True

        except serial.SerialException as e:
            logger.debug(
                "No se pudo conectar a %s: %s",
                self._port, str(e),
            )
            return False

        except OSError as e:
            logger.debug(
                "Puerto %s no disponible: %s",
                self._port, str(e),
            )
            return False

    def _close_port(self) -> None:
        """Cierra el puerto serial de forma segura.

        Verifica que el puerto esté abierto antes de intentar
        cerrarlo. Maneja excepciones silenciosamente porque
        esta función se llama durante la limpieza.
        """
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
                logger.debug("Puerto serial cerrado")
        except Exception as e:
            logger.debug("Error al cerrar puerto: %s", str(e))
        finally:
            self._serial = None

    # =================================================================
    #  LECTURA Y PARSEO
    # =================================================================

    def _read_line(self) -> None:
        """Lee y procesa una línea del puerto serial.

        Lee una línea completa (terminada en \\n), la decodifica
        y la despacha según el protocolo SIMA:
            - Líneas con '#': mensajes de control/estado/error.
            - Líneas sin '#': datos CSV de sensores.
            - Líneas vacías: ignoradas silenciosamente.
        """
        if not self._serial or not self._serial.is_open:
            self._handle_disconnect("Puerto cerrado inesperadamente")
            return

        # Leer una línea completa (bloquea hasta timeout)
        raw_line = self._serial.readline()

        # readline() retorna b'' si hay timeout (sin datos)
        if not raw_line:
            return

        # Decodificar y limpiar espacios/newlines
        try:
            line = raw_line.decode(SERIAL_ENCODING).strip()
        except UnicodeDecodeError:
            logger.warning(
                "Línea con caracteres inválidos: %r", raw_line
            )
            return

        # Ignorar líneas vacías
        if not line:
            return

        # Despachar según tipo de línea
        if line.startswith(PROTOCOL_CONTROL_PREFIX):
            self._process_control_line(line)
        else:
            self._process_data_line(line)

    def _process_control_line(self, line: str) -> None:
        """Procesa una línea de control del protocolo SIMA.

        Formatos reconocidos:
            #SIMA:v1:TEMP,HUM  → Cabecera del protocolo.
            #STATUS:READY      → Mensaje de estado.
            #ERROR:DHT11_FAIL  → Error del firmware.

        Args:
            line: Línea de control completa (con el prefijo #).
        """
        # Quitar el prefijo '#'
        content = line[1:]

        if content.startswith("SIMA:"):
            # Cabecera del protocolo: #SIMA:v1:TEMP,HUM
            protocol_info = content[5:]  # "v1:TEMP,HUM"
            logger.info("Protocolo SIMA detectado: %s", protocol_info)
            self.protocol_info.emit(protocol_info)

        elif content.startswith("STATUS:"):
            # Mensaje de estado: #STATUS:READY
            status = content[7:]
            logger.info("Estado del firmware: %s", status)
            self.status_received.emit(status)

        elif content.startswith("ERROR:"):
            # Error del firmware: #ERROR:DHT11_READ_FAIL
            error_msg = content[6:]
            self._last_hardware_error = error_msg
            logger.warning("Error del firmware: %s", error_msg)
            self.error_occurred.emit(f"Firmware: {error_msg}")

        else:
            # Línea de control no reconocida
            logger.debug("Línea de control desconocida: %s", line)

    def _process_data_line(self, line: str) -> None:
        """Procesa una línea de datos CSV o con cualquier formato numérico.

        Acepta formatos como: "25.3,62.0", "25.3 62.0", "T:25.3 H:62.0", "25.3;62.0".

        Args:
            line: Línea de datos (sin prefijo #).
        """
        try:
            import time, re
            floats = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", line)]
            if len(floats) >= 2:
                temperature = floats[0]
                humidity = floats[1]
                light = floats[2] if len(floats) >= 3 else 400.0

                if self._validate_reading(temperature, humidity, light):
                    self._last_data_timestamp = time.time()
                    self._last_hardware_error = None
                    self.new_data.emit(temperature, humidity, light)
                    return

            # Fallback tradicional por separador
            parts = line.split(PROTOCOL_SEPARATOR)
            if len(parts) >= 2:
                temperature = float(parts[0].strip())
                humidity = float(parts[1].strip())
                light = float(parts[2].strip()) if len(parts) >= 3 else 400.0

                if self._validate_reading(temperature, humidity, light):
                    self._last_data_timestamp = time.time()
                    self._last_hardware_error = None
                    self.new_data.emit(temperature, humidity, light)

        except (ValueError, IndexError) as e:
            logger.warning(
                "Línea de datos malformada: '%s' — %s",
                line, str(e),
            )

    def get_hardware_health(self) -> dict:
        """Evalúa la salud física real del sensor y la conexión serial."""
        import time
        now = time.time()
        time_since_data = (now - self._last_data_timestamp) if self._last_data_timestamp > 0 else 999.0

        if not self._connected:
            return {
                "status": "DISCONNECTED",
                "sensor_ok": False,
                "detail": "Puerto serial desconectado",
                "time_since_data": time_since_data
            }

        if self._last_hardware_error:
            return {
                "status": "SENSOR_FAULT",
                "sensor_ok": False,
                "detail": f"Falla reportada por Arduino: {self._last_hardware_error} (Pin D4/D2 desconectado)",
                "time_since_data": time_since_data
            }

        if time_since_data > 4.5:
            return {
                "status": "DATA_TIMEOUT",
                "sensor_ok": False,
                "detail": "Sin recepción de datos en los últimos 4.5s (Revisar Pin de Datos D4/D2 o VCC del sensor DHT)",
                "time_since_data": round(time_since_data, 1)
            }

        return {
            "status": "OK",
            "sensor_ok": True,
            "detail": "Hardware transmitiendo correctamente",
            "time_since_data": round(time_since_data, 1)
        }

    @staticmethod
    def _validate_reading(
        temperature: float,
        humidity: float,
        light: float = 400.0,
    ) -> bool:
        """Valida que los valores de lectura sean razonables.

        Filtra lecturas que están fuera de los rangos físicamente posibles:
            - Temperatura: -10°C a 60°C
            - Humedad: 0% a 100%
            - Luz: 0 Lux a 5000 Lux

        Args:
            temperature: Temperatura en °C.
            humidity: Humedad relativa en %.
            light: Luminosidad en Lux.

        Returns:
            True si los valores son razonables, False si no.
        """
        if temperature < -10.0 or temperature > 60.0:
            logger.warning(
                "Temperatura fuera de rango: %.1f°C", temperature
            )
            return False

        if humidity < 0.0 or humidity > 100.0:
            logger.warning(
                "Humedad fuera de rango: %.1f%%", humidity
            )
            return False

        if light < 0.0 or light > 5000.0:
            logger.warning(
                "Luminosidad fuera de rango: %.1f Lux", light
            )
            return False

        return True

    # =================================================================
    #  RECONEXIÓN AUTOMÁTICA
    # =================================================================

    def _handle_disconnect(self, reason: str) -> None:
        """Maneja la desconexión del puerto serial.

        Cierra el puerto, actualiza el estado y prepara la
        reconexión automática.

        Args:
            reason: Descripción de la causa de la desconexión.
        """
        if self._connected:
            log_serial_event("DESCONECTADO", reason)
            self._connected = False
            self.connection_changed.emit(False)
            self.error_occurred.emit(reason)

        self._close_port()
        self._reconnect_count += 1

    def _wait_reconnect(self) -> None:
        """Espera antes de intentar reconectar.

        Implementa un backoff simple: espera RECONNECT_INTERVAL
        entre intentos. Después de MAX_RECONNECT_ATTEMPTS intentos,
        reduce la frecuencia de intentos para no saturar el log.

        La espera se hace en intervalos pequeños para poder
        responder rápidamente a stop_reading().
        """
        if self._reconnect_count <= MAX_RECONNECT_ATTEMPTS:
            wait_time = RECONNECT_INTERVAL
        else:
            # Después de muchos intentos, esperar más (máximo 15s)
            wait_time = min(RECONNECT_INTERVAL * 3, 15.0)

        # Solo loguear cada ciertos intentos para no saturar
        if self._reconnect_count <= 3 or self._reconnect_count % 10 == 0:
            logger.info(
                "Reintento de conexión #%d en %.1fs — %s",
                self._reconnect_count, wait_time, self._port,
            )

        # Esperar en intervalos de 0.5s para poder parar rápidamente
        elapsed = 0.0
        while elapsed < wait_time and self._running:
            time.sleep(0.5)
            elapsed += 0.5

    # =================================================================
    #  DETECCIÓN DE PUERTOS
    # =================================================================

    @staticmethod
    def list_available_ports() -> List[str]:
        """Lista los puertos seriales disponibles en el sistema.

        Útil para el diálogo de configuración, donde el usuario
        selecciona el puerto de un combo box.

        Returns:
            Lista de rutas de puertos disponibles.
            Ejemplo: ["/dev/ttyUSB0", "/dev/ttyACM0"]
        """
        try:
            from serial.tools import list_ports
            ports = list_ports.comports()
            available = [port.device for port in ports]
            logger.debug("Puertos disponibles: %s", available)
            return sorted(available)

        except Exception as e:
            logger.error("Error al listar puertos: %s", str(e))
            return []
