"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Punto de Entrada Principal (main.py)

La lógica de negocio sigue viviendo en Python. La ventana visual usa
WebMainWindow para renderizar la interfaz con HTML/CSS/JavaScript.
"""

import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.web_mainwindow import WebMainWindow
from logger_manager import get_logger, log_exception

logger = get_logger("main")


def sigint_handler(*args) -> None:
    logger.info("Interrupción del sistema (SIGINT) recibida. Cerrando SIMA...")
    QApplication.quit()


def main() -> None:
    logger.info("Iniciando SIMA (interfaz HTML/CSS/JS)...")
    signal.signal(signal.SIGINT, sigint_handler)

    app = QApplication(sys.argv)
    app.setApplicationName("SIMA")
    app.setApplicationVersion("2.0.0")

    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    try:
        window = WebMainWindow()
        window.show()
        logger.info("SIMA 2.0 iniciado con frontend web embebido.")
        sys.exit(app.exec())
    except Exception as e:
        log_exception(logger, "Excepción fatal durante la ejecución de la aplicación", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
