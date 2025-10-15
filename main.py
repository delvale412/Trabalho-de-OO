# Salve este arquivo como: main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui import MenuPrincipal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MenuPrincipal()
    menu.show()
    sys.exit(app.exec())

