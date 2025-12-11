from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QListWidget,
                               QTabWidget, QListWidgetItem, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from ui.calendar_view import CalendarView
from ui.coachee_form import CoacheeForm
from ui.sessions_view import SessionsView
from ui.settings import SettingsView


class MainWindow(QMainWindow):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setWindowTitle("Gestión de Coachees")
        self.setMinimumSize(1000, 700)

        self.setup_ui()
        self.load_coachees()
        self.apply_theme()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(500)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Coachees")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        left_layout.addWidget(header)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar coachee...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        self.coachees_list = QListWidget()
        self.coachees_list.itemClicked.connect(self.on_coachee_selected)
        left_layout.addWidget(self.coachees_list)

        add_btn = QPushButton("Agregar Coachee")
        add_btn.clicked.connect(self.open_add_coachee_form)
        add_btn.setProperty("class", "primary")
        add_btn.setMinimumHeight(40)
        left_layout.addWidget(add_btn)

        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.sessions_view = SessionsView(self.storage)
        self.tabs.addTab(self.sessions_view, "Sesiones")

        self.calendar_view = CalendarView(self.storage)
        self.calendar_view.session_scheduled.connect(self.on_session_scheduled)
        self.tabs.addTab(self.calendar_view, "Calendario")

        self.settings_view = SettingsView(self.storage)
        self.settings_view.theme_changed.connect(self.on_theme_changed)
        self.tabs.addTab(self.settings_view, "Configuración")

        right_layout.addWidget(self.tabs)
        right_panel.setLayout(right_layout)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def load_coachees(self):
        self.coachees_list.clear()
        coachees = self.storage.get_all_coachees()

        for coachee in coachees:
            item = QListWidgetItem(coachee.nombre_completo)
            item.setData(Qt.UserRole, coachee)
            self.coachees_list.addItem(item)

    def on_search(self, text):
        if text.strip():
            self.coachees_list.clear()
            coachees = self.storage.search_coachees(text)

            for coachee in coachees:
                item = QListWidgetItem(coachee.nombre_completo)
                item.setData(Qt.UserRole, coachee)
                self.coachees_list.addItem(item)
        else:
            self.load_coachees()

    def on_coachee_selected(self, item):
        coachee = item.data(Qt.UserRole)
        self.sessions_view.set_coachee(coachee)
        self.tabs.setCurrentIndex(0)

    def open_add_coachee_form(self):
        form = CoacheeForm(self.storage, self)
        form.coachee_added.connect(self.load_coachees)
        form.exec()

    def on_session_scheduled(self):
        """Maneja cuando una nueva sesión es programada"""
        pass

    def on_theme_changed(self, theme):
        self.apply_theme()

    def apply_theme(self):
        theme = self.storage.get_setting('theme', 'light')

        if theme == 'dark':
            stylesheet = """
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }

                QLabel {
                    color: #e0e0e0;
                }

                QLineEdit, QTextEdit, QListWidget, QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px;
                }

                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #0d7377;
                }

                QPushButton {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px 16px;
                    min-height: 30px;
                }

                QPushButton:hover {
                    background-color: #3d3d3d;
                }

                QPushButton:pressed {
                    background-color: #1a1a1a;
                }

                QPushButton[class="primary"] {
                    background-color: #0d7377;
                    color: white;
                    border: none;
                }

                QPushButton[class="primary"]:hover {
                    background-color: #0a5c5f;
                }

                QPushButton[class="primary"]:pressed {
                    background-color: #084447;
                }

                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                    background-color: #1e1e1e;
                }

                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3d3d3d;
                    padding: 10px 20px;
                    min-width: 100px;
                }

                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    border-bottom: 2px solid #0d7377;
                }

                QTabBar::tab:hover {
                    background-color: #3d3d3d;
                }

                QListWidget::item {
                    padding: 10px;
                    border-radius: 4px;
                }

                QListWidget::item:selected {
                    background-color: #0d7377;
                    color: white;
                }

                QListWidget::item:hover {
                    background-color: #3d3d3d;
                }

                QGroupBox {
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-weight: bold;
                }

                QGroupBox::title {
                    color: #e0e0e0;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }

                QRadioButton {
                    color: #e0e0e0;
                    spacing: 8px;
                }

                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 9px;
                    border: 2px solid #3d3d3d;
                    background-color: #2d2d2d;
                }

                QRadioButton::indicator:checked {
                    background-color: #0d7377;
                    border: 2px solid #0d7377;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #e0e0e0;
                    margin-right: 10px;
                }

                QMessageBox {
                    background-color: #1e1e1e;
                }

                QDialog {
                    background-color: #1e1e1e;
                }
            """
        else:
            stylesheet = """
                QMainWindow, QWidget {
                    background-color: #f5f5f5;
                    color: #333333;
                }

                QLabel {
                    color: #333333;
                }

                QLineEdit, QTextEdit, QListWidget, QComboBox {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                }

                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #14A79B;
                }

                QPushButton {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px 16px;
                    min-height: 30px;
                }

                QPushButton:hover {
                    background-color: #f0f0f0;
                }

                QPushButton:pressed {
                    background-color: #e0e0e0;
                }

                QPushButton[class="primary"] {
                    background-color: #14A79B;
                    color: white;
                    border: none;
                }

                QPushButton[class="primary"]:hover {
                    background-color: #128b7f;
                }

                QPushButton[class="primary"]:pressed {
                    background-color: #0f6f65;
                }

                QTabWidget::pane {
                    border: 1px solid #ddd;
                    background-color: white;
                }

                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #ddd;
                    padding: 10px 20px;
                    min-width: 100px;
                }

                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 2px solid #14A79B;
                }

                QTabBar::tab:hover {
                    background-color: #e8e8e8;
                }

                QListWidget::item {
                    padding: 10px;
                    border-radius: 4px;
                }

                QListWidget::item:selected {
                    background-color: #14A79B;
                    color: white;
                }

                QListWidget::item:hover {
                    background-color: #e8e8e8;
                }

                QGroupBox {
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-weight: bold;
                }

                QGroupBox::title {
                    color: #333333;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }

                QRadioButton {
                    color: #333333;
                    spacing: 8px;
                }

                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 9px;
                    border: 2px solid #ddd;
                    background-color: white;
                }

                QRadioButton::indicator:checked {
                    background-color: #14A79B;
                    border: 2px solid #14A79B;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #333333;
                    margin-right: 10px;
                }

                QMessageBox {
                    background-color: white;
                }

                QDialog {
                    background-color: white;
                }
            """

        self.setStyleSheet(stylesheet)
