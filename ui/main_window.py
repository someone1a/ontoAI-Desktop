from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QListWidget,
                               QTabWidget, QListWidgetItem, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from ui.calendar_view import CalendarView
from ui.coachee_form import CoacheeForm
from ui.sessions_view import SessionsView
from ui.summaries_view import SummariesView
from ui.payments_view import PaymentsView
from ui.settings import SettingsView


class MainWindow(QMainWindow):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setWindowTitle("Onto AI - Preview")
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

        self.summaries_view = SummariesView(self.storage)
        self.tabs.addTab(self.summaries_view, "Resúmenes")

        self.payments_view = PaymentsView(self.storage)
        self.tabs.addTab(self.payments_view, "Pagos")

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
        self.summaries_view.set_coachee(coachee)
        self.payments_view.set_coachee(coachee)
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
            # Modo oscuro con adaptación de la paleta
            stylesheet = """
                QMainWindow, QWidget {
                    background-color: #1a1a1a;
                    color: #E7DCC3;
                }

                QLabel {
                    color: #E7DCC3;
                }

                QLineEdit, QTextEdit, QListWidget, QComboBox {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }

                QLineEdit:focus, QTextEdit:focus {
                    border: 2px solid #0B4A4A;
                    background-color: #2d2d2d;
                }

                QPushButton {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                    border-radius: 6px;
                    padding: 10px 20px;
                    min-height: 35px;
                    font-weight: 500;
                    font-size: 13px;
                }

                QPushButton:hover {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border: 1px solid #0B4A4A;
                }

                QPushButton:pressed {
                    background-color: #083838;
                }

                QPushButton[class="primary"] {
                    background-color: #C86F44;
                    color: #FFFFFF;
                    border: none;
                    font-weight: 600;
                }

                QPushButton[class="primary"]:hover {
                    background-color: #B35F35;
                }

                QPushButton[class="primary"]:pressed {
                    background-color: #A04F25;
                }

                QPushButton:disabled {
                    background-color: #1a1a1a;
                    color: #666666;
                    border: 1px solid #333333;
                }

                QTabWidget::pane {
                    border: 1px solid #0B4A4A;
                    background-color: #1a1a1a;
                    border-radius: 4px;
                }

                QTabBar::tab {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                    padding: 12px 24px;
                    min-width: 100px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    margin-right: 2px;
                }

                QTabBar::tab:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border-bottom: 3px solid #C86F44;
                    font-weight: 600;
                }

                QTabBar::tab:hover {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QListWidget::item {
                    padding: 12px;
                    border-radius: 6px;
                    margin: 2px 0px;
                }

                QListWidget::item:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QListWidget::item:hover {
                    background-color: #2d2d2d;
                }

                QGroupBox {
                    border: 2px solid #0B4A4A;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 15px;
                    font-weight: 600;
                    font-size: 14px;
                    color: #E7DCC3;
                }

                QGroupBox::title {
                    color: #E7DCC3;
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px;
                    background-color: #1a1a1a;
                }

                QRadioButton {
                    color: #E7DCC3;
                    spacing: 8px;
                }

                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid #0B4A4A;
                    background-color: #2a2a2a;
                }

                QRadioButton::indicator:checked {
                    background-color: #C86F44;
                    border: 2px solid #C86F44;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #E7DCC3;
                    margin-right: 10px;
                }

                QMessageBox {
                    background-color: #1a1a1a;
                }

                QDialog {
                    background-color: #1a1a1a;
                }

                QDateEdit, QDateTimeEdit, QDoubleSpinBox, QSpinBox {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                    border-radius: 6px;
                    padding: 8px;
                }

                QCheckBox {
                    color: #E7DCC3;
                    spacing: 8px;
                }

                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #0B4A4A;
                    background-color: #2a2a2a;
                }

                QCheckBox::indicator:checked {
                    background-color: #C86F44;
                    border: 2px solid #C86F44;
                }

                QTableWidget {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                    border-radius: 6px;
                    gridline-color: #0B4A4A;
                }

                QTableWidget::item {
                    padding: 8px;
                }

                QTableWidget::item:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QHeaderView::section {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                }

                QCalendarWidget QWidget {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                }

                QCalendarWidget QToolButton {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border-radius: 4px;
                    padding: 5px;
                }

                QCalendarWidget QMenu {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                }

                QCalendarWidget QSpinBox {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    border: 1px solid #0B4A4A;
                }

                QCalendarWidget QAbstractItemView:enabled {
                    background-color: #2a2a2a;
                    color: #E7DCC3;
                    selection-background-color: #0B4A4A;
                    selection-color: #FFFFFF;
                }
            """
        else:
            # Modo claro con la paleta especificada
            stylesheet = """
                QMainWindow, QWidget {
                    background-color: #E7DCC3;
                    color: #0B4A4A;
                }

                QLabel {
                    color: #0B4A4A;
                    font-weight: 500;
                }
                
                QFormLayout QLabel {
                    color: #0B4A4A;
                    font-weight: 600;
                    font-size: 13px;
                }

                QLineEdit, QTextEdit, QListWidget, QComboBox {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    border-radius: 8px;
                    padding: 12px 15px;
                    font-size: 14px;
                    font-weight: 500;
                    selection-background-color: #0B4A4A;
                    selection-color: #FFFFFF;
                }

                QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                    border: 2px solid #0B4A4A;
                    background-color: #FFFFFF;
                    outline: none;
                }
                
                QLineEdit:hover, QTextEdit:hover, QComboBox:hover {
                    border: 2px solid #0B4A4A;
                }
                
                QLineEdit::placeholder, QTextEdit::placeholder {
                    color: #AFC2B6;
                    font-style: italic;
                    font-weight: 400;
                }
                
                QLineEdit[echoMode="2"] {
                    font-family: "Courier New", monospace;
                    letter-spacing: 2px;
                }

                QPushButton {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    border-radius: 6px;
                    padding: 10px 20px;
                    min-height: 35px;
                    font-weight: 500;
                    font-size: 13px;
                }

                QPushButton:hover {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border: 2px solid #0B4A4A;
                }

                QPushButton:pressed {
                    background-color: #083838;
                    color: #FFFFFF;
                }

                QPushButton[class="primary"] {
                    background-color: #C86F44;
                    color: #FFFFFF;
                    border: none;
                    font-weight: 600;
                }

                QPushButton[class="primary"]:hover {
                    background-color: #B35F35;
                }

                QPushButton[class="primary"]:pressed {
                    background-color: #A04F25;
                }

                QPushButton:disabled {
                    background-color: #C4B499;
                    color: #999999;
                    border: 2px solid #C4B499;
                }

                QTabWidget::pane {
                    border: 2px solid #0B4A4A;
                    background-color: #FFFFFF;
                    border-radius: 4px;
                }

                QTabBar::tab {
                    background-color: #C4B499;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    padding: 12px 24px;
                    min-width: 100px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    margin-right: 2px;
                }

                QTabBar::tab:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border-bottom: 3px solid #C86F44;
                    font-weight: 600;
                }

                QTabBar::tab:hover {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QListWidget::item {
                    padding: 12px;
                    border-radius: 6px;
                    margin: 2px 0px;
                }

                QListWidget::item:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QListWidget::item:hover {
                    background-color: #AFC2B6;
                    color: #0B4A4A;
                }

                QGroupBox {
                    border: 2px solid #0B4A4A;
                    border-radius: 8px;
                    margin-top: 20px;
                    padding-top: 20px;
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-bottom: 15px;
                    font-weight: 600;
                    font-size: 14px;
                    color: #0B4A4A;
                    background-color: #FFFFFF;
                }

                QGroupBox::title {
                    color: #0B4A4A;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 15px;
                    top: -8px;
                    padding: 0 10px;
                    background-color: #E7DCC3;
                    font-weight: 700;
                    font-size: 15px;
                }

                QRadioButton {
                    color: #0B4A4A;
                    spacing: 10px;
                    font-weight: 500;
                    font-size: 13px;
                }

                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid #0B4A4A;
                    background-color: #FFFFFF;
                }

                QRadioButton::indicator:checked {
                    background-color: #C86F44;
                    border: 2px solid #C86F44;
                }

                QComboBox::drop-down {
                    border: none;
                    width: 35px;
                    background-color: transparent;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }

                QComboBox::down-arrow {
                    image: none;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 6px solid #0B4A4A;
                    margin-right: 8px;
                }
                
                QComboBox QAbstractItemView {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    selection-background-color: #0B4A4A;
                    selection-color: #FFFFFF;
                    border: 2px solid #0B4A4A;
                    border-radius: 6px;
                    padding: 5px;
                    outline: none;
                }
                
                QComboBox QAbstractItemView::item {
                    padding: 8px 12px;
                    border-radius: 4px;
                }
                
                QComboBox QAbstractItemView::item:hover {
                    background-color: #AFC2B6;
                    color: #0B4A4A;
                }

                QMessageBox {
                    background-color: #FFFFFF;
                }

                QDialog {
                    background-color: #E7DCC3;
                }

                QDoubleSpinBox, QSpinBox {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-weight: 600;
                    font-size: 15px;
                }
                
                QDoubleSpinBox:focus, QSpinBox:focus {
                    border: 2px solid #0B4A4A;
                }
                
                QDoubleSpinBox:hover, QSpinBox:hover {
                    border: 2px solid #0B4A4A;
                }
                
                QDoubleSpinBox::up-button, QSpinBox::up-button {
                    background-color: transparent;
                    border: none;
                    border-top-right-radius: 6px;
                    width: 25px;
                    subcontrol-position: top right;
                }
                
                QDoubleSpinBox::down-button, QSpinBox::down-button {
                    background-color: transparent;
                    border: none;
                    border-bottom-right-radius: 6px;
                    width: 25px;
                    subcontrol-position: bottom right;
                }
                
                QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
                QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                    background-color: #AFC2B6;
                }
                
                QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-bottom: 5px solid #0B4A4A;
                    width: 10px;
                    height: 10px;
                }
                
                QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #0B4A4A;
                    width: 10px;
                    height: 10px;
                }

                QDateEdit, QDateTimeEdit {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-weight: 500;
                    font-size: 14px;
                }
                
                QDateEdit:focus, QDateTimeEdit:focus {
                    border: 2px solid #0B4A4A;
                }
                
                QDateEdit:hover, QDateTimeEdit:hover {
                    border: 2px solid #0B4A4A;
                }
                
                QDateEdit::drop-down, QDateTimeEdit::drop-down {
                    border: none;
                    width: 30px;
                    background-color: transparent;
                }
                
                QDateEdit::down-arrow, QDateTimeEdit::down-arrow {
                    image: none;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 6px solid #0B4A4A;
                }

                QCheckBox {
                    color: #0B4A4A;
                    spacing: 10px;
                    font-weight: 500;
                    font-size: 13px;
                }

                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #0B4A4A;
                    background-color: #FFFFFF;
                }

                QCheckBox::indicator:checked {
                    background-color: #C86F44;
                    border: 2px solid #C86F44;
                }

                QTableWidget {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                    border-radius: 6px;
                    gridline-color: #AFC2B6;
                }

                QTableWidget::item {
                    padding: 8px;
                }

                QTableWidget::item:selected {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                }

                QHeaderView::section {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                }

                QCalendarWidget QWidget {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                }

                QCalendarWidget QToolButton {
                    background-color: #0B4A4A;
                    color: #FFFFFF;
                    border-radius: 4px;
                    padding: 5px;
                }

                QCalendarWidget QToolButton:hover {
                    background-color: #C86F44;
                }

                QCalendarWidget QMenu {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                }

                QCalendarWidget QSpinBox {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    border: 2px solid #AFC2B6;
                }

                QCalendarWidget QAbstractItemView:enabled {
                    background-color: #FFFFFF;
                    color: #0B4A4A;
                    selection-background-color: #0B4A4A;
                    selection-color: #FFFFFF;
                }
            """

        self.setStyleSheet(stylesheet)