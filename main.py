import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from services.storage import Storage
from ui.main_window import MainWindow

def get_resource_path(relative_path):
    """Obtiene la ruta correcta del recurso, tanto en desarrollo como en ejecutable"""
    if getattr(sys, 'frozen', False):
        # Si está congelado (ejecutable)
        base_path = sys._MEIPASS
    else:
        # Si está en desarrollo
        base_path = os.path.dirname(__file__)
    
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Onto Ai")
    app.setOrganizationName("Onto Ai")
    app.setApplicationVersion("0.1.0")
    app.setWindowIcon(QIcon("resources/favicon.ico"))
    app.setWindowIcon(QIcon("resources/favicon.ico"))

    storage = Storage()

    window = MainWindow(storage)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
