from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QCalendarWidget, QListWidget,
                               QDialog, QFormLayout, QLineEdit, QTextEdit,
                               QDateTimeEdit, QMessageBox, QListWidgetItem,
                               QGroupBox, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, QDate, QDateTime, QTimer, Signal
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from datetime import datetime, timedelta
import json


class SessionScheduleDialog(QDialog):
    """Diálogo para programar una nueva sesión"""
    
    def __init__(self, storage, selected_date=None, coachee=None, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.selected_date = selected_date or QDateTime.currentDateTime()
        self.coachee = coachee
        self.setWindowTitle("Programar Sesión")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Nueva Sesión Programada")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Selector de coachee
        self.coachee_combo = QComboBox()
        coachees = self.storage.get_all_coachees()
        for coachee in coachees:
            self.coachee_combo.addItem(coachee.nombre_completo, coachee.id)
        
        if self.coachee:
            index = self.coachee_combo.findData(self.coachee.id)
            if index >= 0:
                self.coachee_combo.setCurrentIndex(index)
        
        form_layout.addRow("Coachee *:", self.coachee_combo)
        
        # Fecha y hora
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(self.selected_date)
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Fecha y Hora *:", self.datetime_edit)
        
        # Duración
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["30 minutos", "45 minutos", "1 hora", "1.5 horas", "2 horas"])
        self.duration_combo.setCurrentIndex(2)  # 1 hora por defecto
        form_layout.addRow("Duración:", self.duration_combo)
        
        # Título
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ej: Sesión de seguimiento")
        form_layout.addRow("Título:", self.title_input)
        
        # Notas
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas u objetivos de la sesión...")
        self.notes_input.setMaximumHeight(100)
        form_layout.addRow("Notas:", self.notes_input)
        
        # Notificaciones
        self.notify_checkbox = QCheckBox("Activar notificaciones")
        self.notify_checkbox.setChecked(True)
        form_layout.addRow("", self.notify_checkbox)
        
        self.notify_time_combo = QComboBox()
        self.notify_time_combo.addItems([
            "5 minutos antes",
            "15 minutos antes",
            "30 minutos antes",
            "1 hora antes",
            "1 día antes"
        ])
        self.notify_time_combo.setCurrentIndex(2)
        form_layout.addRow("Recordatorio:", self.notify_time_combo)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_schedule)
        save_btn.setMinimumWidth(100)
        save_btn.setProperty("class", "primary")
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def save_schedule(self):
        if self.coachee_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validación", "Por favor selecciona un coachee.")
            return
        
        coachee_id = self.coachee_combo.currentData()
        scheduled_time = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        title = self.title_input.text().strip() or "Sesión de coaching"
        notes = self.notes_input.toPlainText().strip()
        
        # Calcular duración en minutos
        duration_text = self.duration_combo.currentText()
        duration_map = {
            "30 minutos": 30,
            "45 minutos": 45,
            "1 hora": 60,
            "1.5 horas": 90,
            "2 horas": 120
        }
        duration = duration_map.get(duration_text, 60)
        
        # Configurar notificación
        notify_enabled = self.notify_checkbox.isChecked()
        notify_time = self.notify_time_combo.currentText() if notify_enabled else None
        
        schedule_data = {
            'coachee_id': coachee_id,
            'scheduled_time': scheduled_time,
            'title': title,
            'notes': notes,
            'duration': duration,
            'notify_enabled': notify_enabled,
            'notify_time': notify_time,
            'status': 'scheduled'
        }
        
        try:
            self.storage.add_scheduled_session(schedule_data)
            QMessageBox.information(self, "Éxito", "Sesión programada correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al programar la sesión: {str(e)}")


class CalendarView(QWidget):
    """Vista principal del calendario con sesiones programadas"""
    
    session_scheduled = Signal()
    
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.selected_date = QDate.currentDate()
        self.setup_ui()
        self.setup_notification_timer()
        self.load_sessions()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Encabezado
        header_layout = QHBoxLayout()
        
        title = QLabel("Calendario de Sesiones")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón para programar sesión
        schedule_btn = QPushButton("Programar Sesión")
        schedule_btn.clicked.connect(self.open_schedule_dialog)
        schedule_btn.setProperty("class", "primary")
        schedule_btn.setMinimumWidth(150)
        header_layout.addWidget(schedule_btn)
        
        layout.addLayout(header_layout)
        
        # Layout principal con calendario y lista
        main_layout = QHBoxLayout()
        
        # Calendario
        calendar_group = QGroupBox("Calendario")
        calendar_layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        self.calendar.setMinimumWidth(350)
        calendar_layout.addWidget(self.calendar)
        
        calendar_group.setLayout(calendar_layout)
        main_layout.addWidget(calendar_group, stretch=1)
        
        # Lista de sesiones del día
        sessions_group = QGroupBox("Sesiones del Día")
        sessions_layout = QVBoxLayout()
        
        self.date_label = QLabel(f"Sesiones para {self.selected_date.toString('dd/MM/yyyy')}")
        self.date_label.setStyleSheet("font-weight: bold;")
        sessions_layout.addWidget(self.date_label)
        
        self.sessions_list = QListWidget()
        self.sessions_list.itemDoubleClicked.connect(self.on_session_double_clicked)
        sessions_layout.addWidget(self.sessions_list)
        
        # Botones de acciones
        actions_layout = QHBoxLayout()
        
        self.complete_btn = QPushButton("Marcar Completada")
        self.complete_btn.clicked.connect(self.mark_as_completed)
        self.complete_btn.setEnabled(False)
        actions_layout.addWidget(self.complete_btn)
        
        self.cancel_btn = QPushButton("Cancelar Sesión")
        self.cancel_btn.clicked.connect(self.cancel_session)
        self.cancel_btn.setEnabled(False)
        actions_layout.addWidget(self.cancel_btn)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.delete_session)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        sessions_layout.addLayout(actions_layout)
        
        sessions_group.setLayout(sessions_layout)
        main_layout.addWidget(sessions_group, stretch=1)
        
        layout.addLayout(main_layout)
        
        # Lista de próximas sesiones
        upcoming_group = QGroupBox("Próximas Sesiones")
        upcoming_layout = QVBoxLayout()
        
        self.upcoming_list = QListWidget()
        self.upcoming_list.setMaximumHeight(150)
        upcoming_layout.addWidget(self.upcoming_list)
        
        upcoming_group.setLayout(upcoming_layout)
        layout.addWidget(upcoming_group)
        
        self.setLayout(layout)
        
        # Conectar selección de sesión
        self.sessions_list.itemClicked.connect(self.on_session_selected)
    
    def setup_notification_timer(self):
        """Configura el timer para verificar notificaciones"""
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(60000)  # Verificar cada minuto
        
    def check_notifications(self):
        """Verifica si hay sesiones que requieren notificación"""
        try:
            now = datetime.now()
            sessions = self.storage.get_all_scheduled_sessions()
            
            for session in sessions:
                if session.get('status') != 'scheduled':
                    continue
                
                if not session.get('notify_enabled'):
                    continue
                
                scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                notify_time_str = session.get('notify_time', '30 minutos antes')
                
                # Calcular tiempo de notificación
                notify_minutes = {
                    '5 minutos antes': 5,
                    '15 minutos antes': 15,
                    '30 minutos antes': 30,
                    '1 hora antes': 60,
                    '1 día antes': 1440
                }.get(notify_time_str, 30)
                
                notify_time = scheduled_time - timedelta(minutes=notify_minutes)
                
                # Verificar si es momento de notificar (con ventana de 1 minuto)
                if notify_time <= now <= notify_time + timedelta(minutes=1):
                    if not session.get('notified', False):
                        self.show_notification(session)
                        self.storage.mark_session_notified(session['id'])
        except Exception as e:
            print(f"Error checking notifications: {e}")
    
    def show_notification(self, session):
        """Muestra una notificación para una sesión"""
        coachee = self.storage.get_coachee(session['coachee_id'])
        if not coachee:
            return
        
        scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
        time_str = scheduled_time.strftime("%H:%M")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Recordatorio de Sesión")
        msg.setText(f"Sesión Próxima con {coachee.nombre_completo}")
        msg.setInformativeText(
            f"Título: {session.get('title', 'Sesión de coaching')}\n"
            f"Hora: {time_str}\n"
            f"Duración: {session.get('duration', 60)} minutos"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def load_sessions(self):
        """Carga todas las sesiones programadas"""
        self.update_calendar_highlights()
        self.load_day_sessions()
        self.load_upcoming_sessions()
    
    def update_calendar_highlights(self):
        """Actualiza los resaltados del calendario"""
        try:
            sessions = self.storage.get_all_scheduled_sessions()
            
            # Formato para días con sesiones
            format_scheduled = QTextCharFormat()
            format_scheduled.setBackground(QColor("#14A79B"))
            format_scheduled.setForeground(QColor("white"))
            
            format_completed = QTextCharFormat()
            format_completed.setBackground(QColor("#4CAF50"))
            format_completed.setForeground(QColor("white"))
            
            format_cancelled = QTextCharFormat()
            format_cancelled.setBackground(QColor("#F44336"))
            format_cancelled.setForeground(QColor("white"))
            
            # Limpiar formatos previos
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
            
            # Aplicar formatos
            for session in sessions:
                scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                date = QDate(scheduled_time.year, scheduled_time.month, scheduled_time.day)
                
                status = session.get('status', 'scheduled')
                if status == 'completed':
                    self.calendar.setDateTextFormat(date, format_completed)
                elif status == 'cancelled':
                    self.calendar.setDateTextFormat(date, format_cancelled)
                else:
                    self.calendar.setDateTextFormat(date, format_scheduled)
        except Exception as e:
            print(f"Error updating calendar: {e}")
    
    def load_day_sessions(self):
        """Carga las sesiones del día seleccionado"""
        self.sessions_list.clear()
        
        try:
            date_str = self.selected_date.toString("yyyy-MM-dd")
            sessions = self.storage.get_sessions_by_date(date_str)
            
            for session in sessions:
                coachee = self.storage.get_coachee(session['coachee_id'])
                if not coachee:
                    continue
                
                scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                time_str = scheduled_time.strftime("%H:%M")
                
                status_icons = {
                    'scheduled': '📅',
                    'completed': '✅',
                    'cancelled': '❌'
                }
                status_icon = status_icons.get(session.get('status', 'scheduled'), '📅')
                
                item_text = f"{status_icon} {time_str} - {coachee.nombre_completo} - {session.get('title', 'Sesión')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, session)
                self.sessions_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading day sessions: {e}")
    
    def load_upcoming_sessions(self):
        """Carga las próximas sesiones programadas"""
        self.upcoming_list.clear()
        
        try:
            now = datetime.now()
            sessions = self.storage.get_all_scheduled_sessions()
            
            upcoming = []
            for session in sessions:
                if session.get('status') != 'scheduled':
                    continue
                
                scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                if scheduled_time > now:
                    upcoming.append(session)
            
            upcoming.sort(key=lambda x: x['scheduled_time'])
            
            for session in upcoming[:10]:  # Mostrar solo las próximas 10
                coachee = self.storage.get_coachee(session['coachee_id'])
                if not coachee:
                    continue
                
                scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
                datetime_str = scheduled_time.strftime("%d/%m/%Y %H:%M")
                
                item_text = f"{datetime_str} - {coachee.nombre_completo}"
                item = QListWidgetItem(item_text)
                self.upcoming_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading upcoming sessions: {e}")
    
    def on_date_selected(self, date):
        """Maneja la selección de una fecha en el calendario"""
        self.selected_date = date
        self.date_label.setText(f"Sesiones para {date.toString('dd/MM/yyyy')}")
        self.load_day_sessions()
        self.on_session_selected(None)
    
    def on_session_selected(self, item):
        """Maneja la selección de una sesión"""
        has_selection = item is not None
        if has_selection:
            session = item.data(Qt.UserRole)
            status = session.get('status', 'scheduled')
            self.complete_btn.setEnabled(status == 'scheduled')
            self.cancel_btn.setEnabled(status == 'scheduled')
            self.delete_btn.setEnabled(True)
        else:
            self.complete_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def on_session_double_clicked(self, item):
        """Maneja el doble clic en una sesión"""
        session = item.data(Qt.UserRole)
        coachee = self.storage.get_coachee(session['coachee_id'])
        
        if not coachee:
            return
        
        scheduled_time = datetime.strptime(session['scheduled_time'], "%Y-%m-%d %H:%M:%S")
        datetime_str = scheduled_time.strftime("%d/%m/%Y %H:%M")
        
        details = f"""
Coachee: {coachee.nombre_completo}
Fecha y Hora: {datetime_str}
Duración: {session.get('duration', 60)} minutos
Título: {session.get('title', 'Sesión de coaching')}
Estado: {session.get('status', 'scheduled')}

Notas:
{session.get('notes', 'Sin notas')}
        """
        
        QMessageBox.information(self, "Detalles de la Sesión", details.strip())
    
    def open_schedule_dialog(self):
        """Abre el diálogo para programar una nueva sesión"""
        selected_datetime = QDateTime(self.selected_date, QDateTime.currentDateTime().time())
        dialog = SessionScheduleDialog(self.storage, selected_datetime, parent=self)
        if dialog.exec():
            self.load_sessions()
            self.session_scheduled.emit()
    
    def mark_as_completed(self):
        """Marca una sesión como completada"""
        current_item = self.sessions_list.currentItem()
        if not current_item:
            return
        
        session = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Marcar esta sesión como completada?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage.update_session_status(session['id'], 'completed')
                self.load_sessions()
                QMessageBox.information(self, "Éxito", "Sesión marcada como completada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar la sesión: {str(e)}")
    
    def cancel_session(self):
        """Cancela una sesión programada"""
        current_item = self.sessions_list.currentItem()
        if not current_item:
            return
        
        session = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Cancelar esta sesión?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage.update_session_status(session['id'], 'cancelled')
                self.load_sessions()
                QMessageBox.information(self, "Éxito", "Sesión cancelada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cancelar la sesión: {str(e)}")
    
    def delete_session(self):
        """Elimina una sesión del calendario"""
        current_item = self.sessions_list.currentItem()
        if not current_item:
            return
        
        session = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Estás seguro de que deseas eliminar esta sesión del calendario?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage.delete_scheduled_session(session['id'])
                self.load_sessions()
                QMessageBox.information(self, "Éxito", "Sesión eliminada del calendario.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar la sesión: {str(e)}")