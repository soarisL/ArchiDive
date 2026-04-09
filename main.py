"""
ArchiDive — Conversor de Planta Baixa para Ambiente 3D/VR
Ponto de entrada principal da aplicação.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, APP_NAME, APP_VERSION
from backend import Backend
from frontend import MainWindow


def setup_logging():
    """Configura o sistema de logging."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info(f"Iniciando {APP_NAME} v{APP_VERSION}")


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("ArchiDive")

    # Fonte global padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Habilita High DPI
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    backend = Backend()
    window = MainWindow(backend)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()