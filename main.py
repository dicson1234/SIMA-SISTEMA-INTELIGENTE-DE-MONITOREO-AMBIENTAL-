"""
SIMA — Sistema Inteligente de Monitoreo Ambiental
Punto de Entrada Principal (main.py)

Inicializa la aplicación PySide6, ajusta configuraciones de escalado de pantalla (DPI),
crea y visualiza la ventana principal (MainWindow) y gestiona la detención limpia.

Autor:  Equipo SIMA — Arquitecto de Software
Fecha:  2026-07-14
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from gui import MainWindow
from logger_manager import get_logger, log_exception

# Logger global
logger = get_logger("main")


def sigint_handler(*args) -> None:
    """Manejador para interrupción Ctrl+C en consola para una salida limpia."""
    logger.info("Interrupción del sistema (SIGINT) recibida. Cerrando SIMA...")
    QApplication.quit()


def main() -> None:
    """Función de inicio y orquestación principal."""
    logger.info("Iniciando SIMA (Sistema Inteligente de Monitoreo Ambiental)...")

    # Configurar manejador de interrupciones del teclado (Ctrl+C)
    signal.signal(signal.SIGINT, sigint_handler)

    # Nota: En PySide6 6.5+, el escalamiento HiDPI se habilita automáticamente.
    # No es necesario configurar AA_EnableHighDpiScaling ni AA_UseHighDpiPixmaps.

    app = QApplication(sys.argv)
    app.setApplicationName("SIMA")
    app.setApplicationVersion("1.0.0")

    # Si se ejecuta desde terminal, permitir que Python reciba la señal de Ctrl+C periódicamente
    # mediante un timer interno en el event loop de Qt
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.start(500)  # Chequear señales cada 500ms
    timer.timeout.connect(lambda: None)  # Permite que el intérprete de Python tome el control

    try:
        window = MainWindow()
        window.show()
        
        logger.info("Aplicación iniciada. Ejecutando Event Loop principal de Qt.")
        sys.exit(app.exec())
        
    except Exception as e:
        log_exception(logger, "Excepción fatal durante la ejecución de la aplicación", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
