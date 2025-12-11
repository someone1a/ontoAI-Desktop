from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt, Signal
import re


class CoacheeForm(QDialog):
    coachee_added = Signal()

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("Agregar Coachee")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Nuevo Coachee")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ingrese el nombre")
        form_layout.addRow("Nombre *:", self.nombre_input)

        self.apellido_input = QLineEdit()
        self.apellido_input.setPlaceholderText("Ingrese el apellido")
        form_layout.addRow("Apellido *:", self.apellido_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ejemplo@email.com (opcional)")
        form_layout.addRow("Email:", self.email_input)

        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("+54 11 1234-5678")
        form_layout.addRow("Teléfono *:", self.telefono_input)

        layout.addLayout(form_layout)

        required_label = QLabel("* Campos obligatorios")
        required_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(required_label)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_coachee)
        save_btn.setMinimumWidth(100)
        save_btn.setProperty("class", "primary")
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def validate_email(self, email: str) -> bool:
        if not email:
            return True

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def save_coachee(self):
        nombre = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        email = self.email_input.text().strip()
        telefono = self.telefono_input.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
            self.nombre_input.setFocus()
            return

        if not apellido:
            QMessageBox.warning(self, "Validación", "El apellido es obligatorio.")
            self.apellido_input.setFocus()
            return

        if not telefono:
            QMessageBox.warning(self, "Validación", "El teléfono es obligatorio.")
            self.telefono_input.setFocus()
            return

        if email and not self.validate_email(email):
            QMessageBox.warning(self, "Validación", "El formato del email no es válido.")
            self.email_input.setFocus()
            return

        from models.coachee import Coachee
        coachee = Coachee(
            id=None,
            nombre=nombre,
            apellido=apellido,
            email=email if email else None,
            telefono=telefono
        )

        try:
            self.storage.add_coachee(coachee)
            self.coachee_added.emit()
            QMessageBox.information(self, "Éxito", "Coachee agregado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el coachee: {str(e)}")
