from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QLineEdit, QPushButton, QMessageBox,
                               QGroupBox, QFormLayout, QFileDialog, QRadioButton,
                               QButtonGroup, QDoubleSpinBox)
from PySide6.QtCore import Signal
from services.ai_providers import AIProviderFactory


class SettingsView(QWidget):
    theme_changed = Signal(str)

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Configuración")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        appearance_group = QGroupBox("Apariencia")
        appearance_layout = QVBoxLayout()

        theme_label = QLabel("Modo de Tema:")
        appearance_layout.addWidget(theme_label)

        theme_buttons_layout = QHBoxLayout()
        self.theme_button_group = QButtonGroup(self)

        self.light_radio = QRadioButton("Modo Claro")
        self.dark_radio = QRadioButton("Modo Oscuro")

        self.theme_button_group.addButton(self.light_radio, 0)
        self.theme_button_group.addButton(self.dark_radio, 1)

        self.light_radio.toggled.connect(self.on_theme_changed)

        theme_buttons_layout.addWidget(self.light_radio)
        theme_buttons_layout.addWidget(self.dark_radio)
        theme_buttons_layout.addStretch()

        appearance_layout.addLayout(theme_buttons_layout)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        ai_group = QGroupBox("Proveedor de IA")
        ai_layout = QVBoxLayout()

        provider_label = QLabel("Seleccionar Proveedor:")
        ai_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "GroqCloud", "GPT4All", "Mixtral", "Gemini"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        ai_layout.addWidget(self.provider_combo)

        self.config_form = QFormLayout()
        self.config_form.setSpacing(10)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Ingrese su API Key")
        self.config_form.addRow("API Key:", self.api_key_input)

        self.model_input = QComboBox()
        self.model_input.setEditable(True)
        self.config_form.addRow("Modelo:", self.model_input)

        self.model_path_layout = QHBoxLayout()
        self.model_path_input = QLineEdit()
        self.model_path_input.setPlaceholderText("Ruta del modelo local")
        self.model_path_layout.addWidget(self.model_path_input)

        browse_btn = QPushButton("Examinar")
        browse_btn.clicked.connect(self.browse_model_path)
        self.model_path_layout.addWidget(browse_btn)

        self.model_path_widget = QWidget()
        self.model_path_widget.setLayout(self.model_path_layout)
        self.config_form.addRow("Ruta del Modelo:", self.model_path_widget)

        ai_layout.addLayout(self.config_form)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        test_btn = QPushButton("Test de Conexión")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setMinimumWidth(130)
        buttons_layout.addWidget(test_btn)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_ai_settings)
        save_btn.setMinimumWidth(130)
        save_btn.setProperty("class", "primary")
        buttons_layout.addWidget(save_btn)

        ai_layout.addLayout(buttons_layout)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Grupo de configuración de pagos
        payments_group = QGroupBox("Configuración de Pagos")
        payments_layout = QVBoxLayout()

        pricing_form = QFormLayout()
        pricing_form.setSpacing(10)

        self.session_price_input = QDoubleSpinBox()
        self.session_price_input.setPrefix("$ ")
        self.session_price_input.setDecimals(2)
        self.session_price_input.setMinimum(0)
        self.session_price_input.setMaximum(999999.99)
        self.session_price_input.setSingleStep(10.00)
        pricing_form.addRow("Precio por Sesión:", self.session_price_input)

        payments_layout.addLayout(pricing_form)

        # Botón guardar pagos
        payments_buttons_layout = QHBoxLayout()
        payments_buttons_layout.addStretch()

        save_payments_btn = QPushButton("Guardar Precio")
        save_payments_btn.clicked.connect(self.save_payment_settings)
        save_payments_btn.setMinimumWidth(130)
        save_payments_btn.setProperty("class", "primary")
        payments_buttons_layout.addWidget(save_payments_btn)

        payments_layout.addLayout(payments_buttons_layout)

        payments_group.setLayout(payments_layout)
        layout.addWidget(payments_group)

        layout.addStretch()

        self.setLayout(layout)
        self.on_provider_changed(self.provider_combo.currentText())

    def load_settings(self):
        theme = self.storage.get_setting('theme', 'light')
        if theme == 'dark':
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        provider = self.storage.get_setting('ai_provider', 'OpenAI')
        index = self.provider_combo.findText(provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)

        self.load_provider_config(provider)

        # Cargar precio por sesión
        session_price = self.storage.get_setting('session_price', 0.0)
        self.session_price_input.setValue(session_price)

    def load_provider_config(self, provider_name):
        config = self.storage.get_setting(f'ai_config_{provider_name}', {})

        if provider_name == "GPT4All":
            self.model_path_input.setText(config.get('model_path', ''))
        else:
            self.api_key_input.setText(config.get('api_key', ''))

            model = config.get('model', '')
            if model:
                index = self.model_input.findText(model)
                if index >= 0:
                    self.model_input.setCurrentIndex(index)
                else:
                    self.model_input.setCurrentText(model)

    def on_theme_changed(self):
        theme = 'dark' if self.dark_radio.isChecked() else 'light'
        self.storage.save_setting('theme', theme)
        self.theme_changed.emit(theme)

    def on_provider_changed(self, provider_name):
        is_gpt4all = provider_name == "GPT4All"

        self.api_key_input.setVisible(not is_gpt4all)
        self.model_input.setVisible(not is_gpt4all)
        self.model_path_widget.setVisible(is_gpt4all)

        label_api = self.config_form.labelForField(self.api_key_input)
        if label_api:
            label_api.setVisible(not is_gpt4all)

        label_model = self.config_form.labelForField(self.model_input)
        if label_model:
            label_model.setVisible(not is_gpt4all)

        self.model_input.clear()

        if provider_name == "OpenAI":
            self.model_input.addItems(["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"])
        elif provider_name == "GroqCloud" or provider_name == "Mixtral":
            self.model_input.addItems(["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
        elif provider_name == "Gemini":
            self.model_input.addItems(["gemini-pro", "gemini-pro-vision"])

        self.load_provider_config(provider_name)

    def browse_model_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Modelo GPT4All",
            "",
            "Model Files (*.bin *.gguf);;All Files (*)"
        )

        if file_path:
            self.model_path_input.setText(file_path)

    def save_ai_settings(self):
        provider_name = self.provider_combo.currentText()

        if provider_name == "GPT4All":
            model_path = self.model_path_input.text().strip()

            if not model_path:
                QMessageBox.warning(self, "Validación", "Por favor selecciona la ruta del modelo.")
                return

            config = {'model_path': model_path}
        else:
            api_key = self.api_key_input.text().strip()
            model = self.model_input.currentText().strip()

            if not api_key:
                QMessageBox.warning(self, "Validación", "Por favor ingresa tu API Key.")
                return

            if not model:
                QMessageBox.warning(self, "Validación", "Por favor selecciona un modelo.")
                return

            config = {
                'api_key': api_key,
                'model': model
            }

        self.storage.save_setting('ai_provider', provider_name)
        self.storage.save_setting(f'ai_config_{provider_name}', config)

        QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")

    def test_connection(self):
        provider_name = self.provider_combo.currentText()
        config = {}

        if provider_name == "GPT4All":
            model_path = self.model_path_input.text().strip()
            if not model_path:
                QMessageBox.warning(self, "Validación", "Por favor selecciona la ruta del modelo.")
                return
            config = {'model_path': model_path}
        else:
            api_key = self.api_key_input.text().strip()
            model = self.model_input.currentText().strip()

            if not api_key:
                QMessageBox.warning(self, "Validación", "Por favor ingresa tu API Key.")
                return

            if not model:
                QMessageBox.warning(self, "Validación", "Por favor selecciona un modelo.")
                return

            config = {
                'api_key': api_key,
                'model': model
            }

        try:
            provider = AIProviderFactory.create_provider(provider_name, config)

            if provider:
                success, message = provider.test_connection()

                if success:
                    QMessageBox.information(self, "Test de Conexión", message)
                else:
                    QMessageBox.warning(self, "Test de Conexión", message)
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear el proveedor de IA.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al probar la conexión: {str(e)}")
    def save_payment_settings(self):
        """Guarda la configuración de precios de sesiones"""
        try:
            session_price = self.session_price_input.value()

            self.storage.save_setting('session_price', session_price)
            QMessageBox.information(self, "Éxito", "Configuración de pagos guardada correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la configuración: {str(e)}")