import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from services.storage import Storage
from ui.main_window import MainWindow


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
