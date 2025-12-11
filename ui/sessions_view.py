from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QTextEdit, QPushButton, QMessageBox,
                               QDialog, QComboBox, QListWidgetItem, QGroupBox)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from datetime import datetime
from services.ai_providers import AIProviderFactory


class AIConsultDialog(QDialog):
    def __init__(self, storage, notas_text, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.notas_text = notas_text
        self.setWindowTitle("Consultar IA")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Consulta a Proveedor de IA")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        provider_label = QLabel("Seleccionar Proveedor:")
        layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "GroqCloud", "GPT4All", "Mixtral", "Gemini"])

        saved_provider = self.storage.get_setting('ai_provider', 'OpenAI')
        index = self.provider_combo.findText(saved_provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)

        layout.addWidget(self.provider_combo)

        prompt_label = QLabel("Pregunta o instrucción:")
        layout.addWidget(prompt_label)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Ejemplo: Resume los puntos clave de estas notas...")
        self.prompt_input.setMaximumHeight(100)

        default_prompt = f"Analiza las siguientes notas de sesión de coaching:\n\n{self.notas_text}\n\nPor favor, proporciona un resumen de los puntos clave y sugerencias para la próxima sesión."
        self.prompt_input.setPlainText(default_prompt)

        layout.addWidget(self.prompt_input)

        response_label = QLabel("Respuesta:")
        layout.addWidget(response_label)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setPlaceholderText("La respuesta de la IA aparecerá aquí...")
        layout.addWidget(self.response_output)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.consult_btn = QPushButton("Consultar")
        self.consult_btn.clicked.connect(self.consult_ai)
        self.consult_btn.setMinimumWidth(120)
        self.consult_btn.setProperty("class", "primary")
        buttons_layout.addWidget(self.consult_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(120)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def consult_ai(self):
        provider_name = self.provider_combo.currentText()
        prompt = self.prompt_input.toPlainText().strip()

        if not prompt:
            QMessageBox.warning(self, "Validación", "Por favor ingresa una pregunta o instrucción.")
            return

        provider_config = self.storage.get_setting(f'ai_config_{provider_name}', {})

        if not provider_config:
            QMessageBox.warning(
                self,
                "Configuración requerida",
                f"Por favor configura el proveedor {provider_name} en la pestaña de Configuración."
            )
            return

        self.consult_btn.setEnabled(False)
        self.consult_btn.setText("Consultando...")
        self.response_output.setPlainText("Generando respuesta...")

        try:
            provider = AIProviderFactory.create_provider(provider_name, provider_config)

            if provider:
                response = provider.generate_response(prompt)
                self.response_output.setPlainText(response)
            else:
                self.response_output.setPlainText("Error: No se pudo crear el proveedor de IA.")
        except Exception as e:
            self.response_output.setPlainText(f"Error al consultar IA: {str(e)}")
        finally:
            self.consult_btn.setEnabled(True)
            self.consult_btn.setText("Consultar")


class SessionsView(QWidget):
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.current_coachee = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        self.coachee_label = QLabel("Selecciona un coachee para ver sus sesiones")
        self.coachee_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.coachee_label)

        sessions_group = QGroupBox("Historial de Sesiones")
        sessions_layout = QVBoxLayout()

        self.sessions_list = QListWidget()
        self.sessions_list.itemClicked.connect(self.on_session_selected)
        sessions_layout.addWidget(self.sessions_list)

        sessions_group.setLayout(sessions_layout)
        layout.addWidget(sessions_group, stretch=1)

        notes_group = QGroupBox("Notas de Sesión")
        notes_layout = QVBoxLayout()

        self.notas_input = QTextEdit()
        self.notas_input.setPlaceholderText("Escribe las notas de la sesión aquí...")
        notes_layout.addWidget(self.notas_input)

        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group, stretch=2)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.ai_btn = QPushButton("Consultar IA")
        self.ai_btn.clicked.connect(self.open_ai_dialog)
        self.ai_btn.setMinimumWidth(130)
        buttons_layout.addWidget(self.ai_btn)

        self.save_btn = QPushButton("Guardar Sesión")
        self.save_btn.clicked.connect(self.save_session)
        self.save_btn.setMinimumWidth(130)
        self.save_btn.setProperty("class", "primary")
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setEnabled(False)

    def set_coachee(self, coachee):
        self.current_coachee = coachee
        if coachee:
            self.coachee_label.setText(f"Sesiones de: {coachee.nombre_completo}")
            self.setEnabled(True)
            self.load_sessions()
            self.notas_input.clear()
        else:
            self.coachee_label.setText("Selecciona un coachee para ver sus sesiones")
            self.setEnabled(False)
            self.sessions_list.clear()
            self.notas_input.clear()

    def load_sessions(self):
        self.sessions_list.clear()

        if self.current_coachee:
            sessions = self.storage.get_sessions_by_coachee(self.current_coachee.id)

            for session in sessions:
                item_text = f"{session.fecha} - {session.notas[:50]}..."
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, session)
                self.sessions_list.addItem(item)

    def on_session_selected(self, item):
        session = item.data(Qt.UserRole)
        if session:
            self.notas_input.setPlainText(session.notas)

    def save_session(self):
        if not self.current_coachee:
            QMessageBox.warning(self, "Validación", "Por favor selecciona un coachee primero.")
            return

        notas = self.notas_input.toPlainText().strip()

        if not notas:
            QMessageBox.warning(self, "Validación", "Por favor escribe las notas de la sesión.")
            return

        from models.session import Session
        session = Session(
            id=None,
            coachee_id=self.current_coachee.id,
            fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            notas=notas
        )

        try:
            self.storage.add_session(session)
            QMessageBox.information(self, "Éxito", "Sesión guardada correctamente.")
            self.load_sessions()
            self.notas_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la sesión: {str(e)}")

    def open_ai_dialog(self):
        notas = self.notas_input.toPlainText().strip()

        if not notas:
            QMessageBox.warning(self, "Validación", "Por favor escribe algunas notas antes de consultar a la IA.")
            return

        dialog = AIConsultDialog(self.storage, notas, self)
        dialog.exec()
