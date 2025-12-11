from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QTextEdit, QPushButton, QMessageBox,
                               QDialog, QComboBox, QListWidgetItem, QGroupBox,
                               QCheckBox, QDoubleSpinBox, QFormLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from datetime import datetime
from services.ai_providers import AIProviderFactory


class PaymentDialog(QDialog):
    """Diálogo para marcar el pago de una sesión"""
    
    def __init__(self, storage, session, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.session = session
        self.setWindowTitle("Actualizar Estado de Pago")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Estado de Pago de la Sesión")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Info de la sesión
        session_date = datetime.strptime(self.session.fecha, "%Y-%m-%d %H:%M:%S")
        date_str = session_date.strftime("%d/%m/%Y %H:%M")
        
        info_label = QLabel(f"Sesión del {date_str}")
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Obtener precio por defecto de configuración
        default_price = self.storage.get_setting('session_price', 0.0)
        
        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Checkbox de pagado
        self.paid_checkbox = QCheckBox()
        self.paid_checkbox.setChecked(self.session.pagado)
        self.paid_checkbox.toggled.connect(self.on_paid_toggled)
        form_layout.addRow("Sesión Pagada:", self.paid_checkbox)
        
        # Monto
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setPrefix("$ ")
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setMaximum(999999.99)
        
        # Usar el monto guardado o el precio por defecto si está pagado
        if hasattr(self.session, 'monto') and self.session.monto > 0:
            self.amount_spinbox.setValue(self.session.monto)
        elif self.session.pagado and default_price > 0:
            self.amount_spinbox.setValue(default_price)
        else:
            self.amount_spinbox.setValue(default_price if default_price > 0 else 0)
        
        self.amount_spinbox.setEnabled(self.session.pagado)
        form_layout.addRow("Monto:", self.amount_spinbox)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_payment)
        save_btn.setMinimumWidth(100)
        save_btn.setProperty("class", "primary")
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def on_paid_toggled(self, checked):
        """Habilita/deshabilita el campo de monto"""
        self.amount_spinbox.setEnabled(checked)
    
    def save_payment(self):
        """Guarda el estado de pago"""
        try:
            pagado = self.paid_checkbox.isChecked()
            monto = self.amount_spinbox.value() if pagado else 0
            
            self.storage.update_session_payment(self.session.id, pagado, monto)
            QMessageBox.information(self, "Éxito", "Estado de pago actualizado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar el pago: {str(e)}")


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

        # Encabezado con información del coachee
        header_layout = QVBoxLayout()
        
        self.coachee_label = QLabel("Selecciona un coachee para ver sus sesiones")
        self.coachee_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.coachee_label)
        
        # Resumen de pagos
        self.payment_summary_label = QLabel()
        self.payment_summary_label.setStyleSheet("color: gray; font-size: 12px;")
        self.payment_summary_label.setVisible(False)
        header_layout.addWidget(self.payment_summary_label)
        
        layout.addLayout(header_layout)

        sessions_group = QGroupBox("Historial de Sesiones")
        sessions_layout = QVBoxLayout()

        self.sessions_list = QListWidget()
        self.sessions_list.itemClicked.connect(self.on_session_selected)
        self.sessions_list.itemDoubleClicked.connect(self.on_session_double_clicked)
        sessions_layout.addWidget(self.sessions_list)

        sessions_group.setLayout(sessions_layout)
        layout.addWidget(sessions_group, stretch=1)

        notes_group = QGroupBox("Notas de Sesión")
        notes_layout = QVBoxLayout()

        self.notas_input = QTextEdit()
        self.notas_input.setPlaceholderText("Escribe las notas de la sesión aquí...")
        notes_layout.addWidget(self.notas_input)
        
        # Sección de pago mejorada
        payment_group = QGroupBox("Estado de Pago")
        payment_group_layout = QVBoxLayout()
        payment_group_layout.setSpacing(15)
        
        # Checkbox de pagado con descripción
        payment_check_layout = QHBoxLayout()
        self.payment_checkbox = QCheckBox("Marcar sesión como pagada")
        self.payment_checkbox.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.payment_checkbox.toggled.connect(self.on_payment_checkbox_toggled)
        payment_check_layout.addWidget(self.payment_checkbox)
        payment_check_layout.addStretch()
        payment_group_layout.addLayout(payment_check_layout)
        
        # Monto con layout separado
        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(10)
        amount_label = QLabel("Monto a cobrar:")
        amount_label.setStyleSheet("font-weight: bold;")
        amount_layout.addWidget(amount_label)
        
        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setPrefix("$ ")
        self.payment_amount.setDecimals(2)
        self.payment_amount.setMaximum(999999.99)
        self.payment_amount.setMinimumWidth(120)
        self.payment_amount.setEnabled(False)
        amount_layout.addWidget(self.payment_amount)
        
        amount_layout.addStretch()
        payment_group_layout.addLayout(amount_layout)
        
        payment_group.setLayout(payment_group_layout)
        notes_layout.addWidget(payment_group)

        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group, stretch=2)

        buttons_layout = QHBoxLayout()

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
            self.load_payment_summary()
            self.notas_input.clear()
            self.payment_checkbox.setChecked(False)
            self.payment_amount.setValue(0)
        else:
            self.coachee_label.setText("Selecciona un coachee para ver sus sesiones")
            self.setEnabled(False)
            self.sessions_list.clear()
            self.notas_input.clear()
            self.payment_summary_label.setVisible(False)

    def load_payment_summary(self):
        """Carga el resumen de pagos del coachee actual"""
        if not self.current_coachee:
            return
        
        summary = self.storage.get_payment_summary_by_coachee(self.current_coachee.id)
        
        summary_text = f"Total sesiones: {summary['total_sessions']} | "
        summary_text += f"Pagadas: {summary['paid_sessions']} (${summary['total_paid']:.2f}) | "
        summary_text += f"Pendientes: {summary['unpaid_sessions']} (${summary['total_pending']:.2f})"
        
        self.payment_summary_label.setText(summary_text)
        self.payment_summary_label.setVisible(True)

    def load_sessions(self):
        self.sessions_list.clear()

        if self.current_coachee:
            sessions = self.storage.get_sessions_by_coachee(self.current_coachee.id)

            for session in sessions:
                # Formatear fecha
                session_date = datetime.strptime(session.fecha, "%Y-%m-%d %H:%M:%S")
                date_str = session_date.strftime("%d/%m/%Y")
                
                # Icono de pago
                payment_icon = "✅" if session.pagado else "⏳"
                
                # Texto del item
                item_text = f"{payment_icon} {date_str} - {session.notas[:50]}..."
                if session.pagado and hasattr(session, 'monto') and session.monto > 0:
                    item_text += f" [${session.monto:.2f}]"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, session)
                self.sessions_list.addItem(item)

    def on_session_selected(self, item):
        session = item.data(Qt.UserRole)
        if session:
            self.notas_input.setPlainText(session.notas)
            self.payment_checkbox.setChecked(session.pagado)
            
            # Cargar monto o precio por defecto
            if hasattr(session, 'monto') and session.monto > 0:
                self.payment_amount.setValue(session.monto)
            else:
                # Cargar precio por defecto de configuración
                default_price = self.storage.get_setting('session_price', 0.0)
                self.payment_amount.setValue(default_price)
    
    def on_payment_checkbox_toggled(self, checked):
        """Habilita/deshabilita el campo de monto cuando se marca pagada"""
        self.payment_amount.setEnabled(checked)
        if checked:
            # Si está vacío o en 0, cargar el precio por defecto
            if self.payment_amount.value() == 0:
                default_price = self.storage.get_setting('session_price', 0.0)
                self.payment_amount.setValue(default_price)
    
    def on_session_double_clicked(self, item):
        """Abre el diálogo de pago al hacer doble clic"""
        session = item.data(Qt.UserRole)
        if session:
            self.open_payment_dialog(session)

    def open_payment_dialog(self, session):
        """Abre el diálogo para actualizar el pago"""
        dialog = PaymentDialog(self.storage, session, self)
        if dialog.exec():
            self.load_sessions()
            self.load_payment_summary()
            # Actualizar la sesión seleccionada
            current_item = self.sessions_list.currentItem()
            if current_item:
                updated_session = current_item.data(Qt.UserRole)
                # Recargar datos de la sesión
                sessions = self.storage.get_sessions_by_coachee(self.current_coachee.id)
                for s in sessions:
                    if s.id == session.id:
                        self.payment_checkbox.setChecked(s.pagado)
                        self.payment_amount.setValue(s.monto)
                        break

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
            notas=notas,
            pagado=self.payment_checkbox.isChecked(),
            monto=self.payment_amount.value() if self.payment_checkbox.isChecked() else 0
        )

        try:
            self.storage.add_session(session)
            QMessageBox.information(self, "Éxito", "Sesión guardada correctamente.")
            self.load_sessions()
            self.load_payment_summary()
            self.notas_input.clear()
            self.payment_checkbox.setChecked(False)
            self.payment_amount.setValue(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la sesión: {str(e)}")

    def open_ai_dialog(self):
        notas = self.notas_input.toPlainText().strip()

        if not notas:
            QMessageBox.warning(self, "Validación", "Por favor escribe algunas notas antes de consultar a la IA.")
            return

        dialog = AIConsultDialog(self.storage, notas, self)
        dialog.exec()