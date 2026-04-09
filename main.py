"""
ArchiDive — Conversor de Planta Baixa para Ambiente 3D/VR
Ponto de entrada principal da aplicação.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from archidive.backend import Backend
from archidive.frontend import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ArchiDive")
    app.setApplicationVersion("1.0.0")
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
