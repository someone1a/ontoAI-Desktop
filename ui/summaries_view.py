from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QTextEdit, QPushButton, QMessageBox,
                               QDialog, QComboBox, QListWidgetItem, QGroupBox,
                               QDateEdit, QFormLayout, QProgressDialog)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from datetime import datetime, timedelta
from services.ai_providers import AIProviderFactory


class SummaryGeneratorThread(QThread):
    """Thread para generar resúmenes en segundo plano"""
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, provider, prompt):
        super().__init__()
        self.provider = provider
        self.prompt = prompt
        
    def run(self):
        try:
            response = self.provider.generate_response(self.prompt)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class GenerateSummaryDialog(QDialog):
    """Diálogo para generar un nuevo resumen"""
    
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("Generar Resumen con IA")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.generator_thread = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Generar Resumen con IA")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Formulario de configuración
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Selector de coachee
        self.coachee_combo = QComboBox()
        self.coachee_combo.addItem("Todos los coachees", None)
        coachees = self.storage.get_all_coachees()
        for coachee in coachees:
            self.coachee_combo.addItem(coachee.nombre_completo, coachee.id)
        self.coachee_combo.currentIndexChanged.connect(self.on_coachee_changed)
        form_layout.addRow("Coachee:", self.coachee_combo)
        
        # Tipo de resumen
        self.summary_type_combo = QComboBox()
        self.summary_type_combo.addItems([
            "Resumen General",
            "Análisis de Progreso",
            "Patrones y Tendencias",
            "Objetivos y Logros",
            "Áreas de Mejora",
            "Recomendaciones"
        ])
        form_layout.addRow("Tipo de Resumen:", self.summary_type_combo)
        
        # Rango de fechas
        date_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(QLabel("Desde:"))
        date_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(QLabel("Hasta:"))
        date_layout.addWidget(self.date_to)
        
        form_layout.addRow("Período:", date_layout)
        
        # Proveedor de IA
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "GroqCloud", "GPT4All", "Mixtral", "Gemini"])
        saved_provider = self.storage.get_setting('ai_provider', 'OpenAI')
        index = self.provider_combo.findText(saved_provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)
        form_layout.addRow("Proveedor IA:", self.provider_combo)
        
        layout.addLayout(form_layout)
        
        # Info de sesiones
        self.sessions_info = QLabel()
        self.sessions_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.sessions_info)
        
        # Área de vista previa/resultado
        preview_label = QLabel("Resumen generado:")
        layout.addWidget(preview_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("El resumen generado aparecerá aquí...")
        layout.addWidget(self.result_text)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.generate_btn = QPushButton("Generar Resumen")
        self.generate_btn.clicked.connect(self.generate_summary)
        self.generate_btn.setMinimumWidth(150)
        self.generate_btn.setProperty("class", "primary")
        buttons_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self.save_summary)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("Cerrar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Actualizar info inicial
        self.on_coachee_changed()
    
    def on_coachee_changed(self):
        """Actualiza la información de sesiones disponibles"""
        coachee_id = self.coachee_combo.currentData()
        date_from_str = self.date_from.date().toString("yyyy-MM-dd")
        date_to_str = self.date_to.date().toString("yyyy-MM-dd") + " 23:59:59"
        
        if coachee_id:
            sessions = self.storage.get_sessions_by_date_range(coachee_id, date_from_str, date_to_str)
            coachee = self.storage.get_coachee(coachee_id)
            self.sessions_info.setText(
                f"Se encontraron {len(sessions)} sesiones para {coachee.nombre_completo} en el período seleccionado."
            )
        else:
            total_sessions = 0
            for coachee in self.storage.get_all_coachees():
                sessions = self.storage.get_sessions_by_date_range(coachee.id, date_from_str, date_to_str)
                total_sessions += len(sessions)
            self.sessions_info.setText(
                f"Se encontraron {total_sessions} sesiones en total para el período seleccionado."
            )
    
    def generate_summary(self):
        """Genera el resumen usando IA"""
        coachee_id = self.coachee_combo.currentData()
        summary_type = self.summary_type_combo.currentText()
        date_from_str = self.date_from.date().toString("yyyy-MM-dd")
        date_to_str = self.date_to.date().toString("yyyy-MM-dd") + " 23:59:59"
        provider_name = self.provider_combo.currentText()
        
        # Obtener configuración del proveedor
        provider_config = self.storage.get_setting(f'ai_config_{provider_name}', {})
        if not provider_config:
            QMessageBox.warning(
                self,
                "Configuración requerida",
                f"Por favor configura el proveedor {provider_name} en la pestaña de Configuración."
            )
            return
        
        # Recopilar sesiones
        sessions_text = ""
        sessions_count = 0
        
        if coachee_id:
            sessions = self.storage.get_sessions_by_date_range(coachee_id, date_from_str, date_to_str)
            coachee = self.storage.get_coachee(coachee_id)
            
            if not sessions:
                QMessageBox.warning(self, "Sin datos", "No hay sesiones en el período seleccionado.")
                return
            
            sessions_text = f"Sesiones de coaching de {coachee.nombre_completo}:\n\n"
            for i, session in enumerate(sessions, 1):
                sessions_text += f"Sesión {i} - {session.fecha}:\n{session.notas}\n\n"
            sessions_count = len(sessions)
        else:
            all_sessions = []
            for coachee in self.storage.get_all_coachees():
                sessions = self.storage.get_sessions_by_date_range(coachee.id, date_from_str, date_to_str)
                for session in sessions:
                    all_sessions.append((coachee, session))
            
            if not all_sessions:
                QMessageBox.warning(self, "Sin datos", "No hay sesiones en el período seleccionado.")
                return
            
            sessions_text = "Sesiones de coaching de todos los coachees:\n\n"
            for i, (coachee, session) in enumerate(all_sessions, 1):
                sessions_text += f"Sesión {i} - {coachee.nombre_completo} - {session.fecha}:\n{session.notas}\n\n"
            sessions_count = len(all_sessions)
        
        # Crear prompt según el tipo de resumen
        prompts = {
            "Resumen General": f"Por favor, genera un resumen ejecutivo completo de las siguientes {sessions_count} sesiones de coaching. Incluye los temas principales discutidos, conclusiones importantes y el contexto general del trabajo de coaching.\n\n{sessions_text}",
            
            "Análisis de Progreso": f"Analiza el progreso observado a través de estas {sessions_count} sesiones de coaching. Identifica mejoras, cambios positivos, hitos alcanzados y la evolución del coachee a lo largo del tiempo.\n\n{sessions_text}",
            
            "Patrones y Tendencias": f"Identifica patrones recurrentes, tendencias y temas comunes en estas {sessions_count} sesiones de coaching. Analiza qué aspectos aparecen con frecuencia y qué pueden indicar.\n\n{sessions_text}",
            
            "Objetivos y Logros": f"Resume los objetivos establecidos y los logros alcanzados según estas {sessions_count} sesiones de coaching. Evalúa el cumplimiento de metas y destaca los éxitos principales.\n\n{sessions_text}",
            
            "Áreas de Mejora": f"Identifica las áreas de mejora, desafíos pendientes y oportunidades de desarrollo observadas en estas {sessions_count} sesiones de coaching. Proporciona un análisis constructivo.\n\n{sessions_text}",
            
            "Recomendaciones": f"Basándote en estas {sessions_count} sesiones de coaching, proporciona recomendaciones específicas y accionables para las próximas sesiones. Incluye sugerencias de enfoques, temas a abordar y estrategias.\n\n{sessions_text}"
        }
        
        prompt = prompts.get(summary_type, prompts["Resumen General"])
        
        # Crear proveedor y generar en segundo plano
        try:
            provider = AIProviderFactory.create_provider(provider_name, provider_config)
            if not provider:
                QMessageBox.critical(self, "Error", "No se pudo crear el proveedor de IA.")
                return
            
            # Deshabilitar botón y mostrar progreso
            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("Generando...")
            self.result_text.setPlainText("Generando resumen con IA, por favor espera...")
            
            # Crear y ejecutar thread
            self.generator_thread = SummaryGeneratorThread(provider, prompt)
            self.generator_thread.finished.connect(self.on_generation_finished)
            self.generator_thread.error.connect(self.on_generation_error)
            self.generator_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar resumen: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Generar Resumen")
    
    def on_generation_finished(self, response):
        """Maneja la respuesta exitosa de la generación"""
        self.result_text.setPlainText(response)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generar Resumen")
        self.save_btn.setEnabled(True)
        self.generator_thread = None
    
    def on_generation_error(self, error_msg):
        """Maneja errores en la generación"""
        self.result_text.setPlainText(f"Error al generar resumen: {error_msg}")
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generar Resumen")
        self.generator_thread = None
        QMessageBox.critical(self, "Error", f"Error al generar resumen: {error_msg}")
    
    def save_summary(self):
        """Guarda el resumen generado"""
        content = self.result_text.toPlainText().strip()
        if not content or content.startswith("Error") or content.startswith("Generando"):
            QMessageBox.warning(self, "Validación", "No hay un resumen válido para guardar.")
            return
        
        coachee_id = self.coachee_combo.currentData()
        if not coachee_id:
            QMessageBox.warning(
                self, 
                "Validación", 
                "Por favor selecciona un coachee específico para guardar el resumen."
            )
            return
        
        summary_type = self.summary_type_combo.currentText()
        date_from_str = self.date_from.date().toString("yyyy-MM-dd")
        date_to_str = self.date_to.date().toString("yyyy-MM-dd")
        provider_name = self.provider_combo.currentText()
        
        coachee = self.storage.get_coachee(coachee_id)
        title = f"{summary_type} - {coachee.nombre_completo} ({date_from_str} a {date_to_str})"
        
        summary_data = {
            'coachee_id': coachee_id,
            'title': title,
            'summary_type': summary_type,
            'content': content,
            'date_from': date_from_str,
            'date_to': date_to_str,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ai_provider': provider_name
        }
        
        try:
            self.storage.add_summary(summary_data)
            QMessageBox.information(self, "Éxito", "Resumen guardado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el resumen: {str(e)}")


class SummariesView(QWidget):
    """Vista principal de resúmenes"""
    
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.current_coachee = None
        self.setup_ui()
        self.load_summaries()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Encabezado
        header_layout = QHBoxLayout()
        
        title = QLabel("Resúmenes Generados por IA")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón para generar nuevo resumen
        generate_btn = QPushButton("Generar Nuevo Resumen")
        generate_btn.clicked.connect(self.open_generate_dialog)
        generate_btn.setProperty("class", "primary")
        generate_btn.setMinimumWidth(180)
        header_layout.addWidget(generate_btn)
        
        layout.addLayout(header_layout)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Filtrar por coachee:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todos", None)
        self.filter_combo.currentIndexChanged.connect(self.load_summaries)
        filters_layout.addWidget(self.filter_combo)
        
        filters_layout.addWidget(QLabel("Tipo:"))
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("Todos los tipos", None)
        self.type_filter_combo.addItems([
            "Resumen General",
            "Análisis de Progreso",
            "Patrones y Tendencias",
            "Objetivos y Logros",
            "Áreas de Mejora",
            "Recomendaciones"
        ])
        self.type_filter_combo.currentIndexChanged.connect(self.load_summaries)
        filters_layout.addWidget(self.type_filter_combo)
        
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        # Layout principal con lista y detalle
        main_layout = QHBoxLayout()
        
        # Lista de resúmenes
        list_group = QGroupBox("Resúmenes Guardados")
        list_layout = QVBoxLayout()
        
        self.summaries_list = QListWidget()
        self.summaries_list.itemClicked.connect(self.on_summary_selected)
        list_layout.addWidget(self.summaries_list)
        
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group, stretch=1)
        
        # Detalle del resumen
        detail_group = QGroupBox("Detalle del Resumen")
        detail_layout = QVBoxLayout()
        
        self.detail_title = QLabel()
        self.detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.detail_title.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)
        
        self.detail_info = QLabel()
        self.detail_info.setStyleSheet("color: gray; font-size: 11px;")
        self.detail_info.setWordWrap(True)
        detail_layout.addWidget(self.detail_info)
        
        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        detail_layout.addWidget(self.detail_content)
        
        # Botones de acciones
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.delete_summary)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumWidth(100)
        actions_layout.addWidget(self.delete_btn)
        
        detail_layout.addLayout(actions_layout)
        
        detail_group.setLayout(detail_layout)
        main_layout.addWidget(detail_group, stretch=2)
        
        layout.addLayout(main_layout)
        
        self.setLayout(layout)
        
        # Cargar coachees para el filtro
        self.load_coachees_filter()
    
    def load_coachees_filter(self):
        """Carga los coachees en el combo de filtro"""
        self.filter_combo.clear()
        self.filter_combo.addItem("Todos", None)
        
        coachees = self.storage.get_all_coachees()
        for coachee in coachees:
            self.filter_combo.addItem(coachee.nombre_completo, coachee.id)
    
    def load_summaries(self):
        """Carga los resúmenes según los filtros"""
        self.summaries_list.clear()
        self.detail_title.clear()
        self.detail_info.clear()
        self.detail_content.clear()
        self.delete_btn.setEnabled(False)
        
        coachee_id = self.filter_combo.currentData()
        summary_type = self.type_filter_combo.currentText()
        if summary_type == "Todos los tipos":
            summary_type = None
        
        # Obtener resúmenes
        if coachee_id:
            summaries = self.storage.get_summaries_by_coachee(coachee_id)
        else:
            summaries = self.storage.get_all_summaries()
        
        # Filtrar por tipo si es necesario
        if summary_type:
            summaries = [s for s in summaries if s['summary_type'] == summary_type]
        
        # Agregar a la lista
        for summary in summaries:
            coachee = self.storage.get_coachee(summary['coachee_id'])
            if not coachee:
                continue
            
            created_date = datetime.strptime(summary['created_at'], "%Y-%m-%d %H:%M:%S")
            date_str = created_date.strftime("%d/%m/%Y")
            
            item_text = f"{summary['summary_type']} - {coachee.nombre_completo}\n{date_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, summary)
            self.summaries_list.addItem(item)
        
        if not summaries:
            item = QListWidgetItem("No hay resúmenes guardados")
            item.setFlags(Qt.NoItemFlags)
            self.summaries_list.addItem(item)
    
    def on_summary_selected(self, item):
        """Maneja la selección de un resumen"""
        summary = item.data(Qt.UserRole)
        if not summary:
            return
        
        coachee = self.storage.get_coachee(summary['coachee_id'])
        if not coachee:
            return
        
        # Mostrar título
        self.detail_title.setText(summary['title'])
        
        # Mostrar información
        created_date = datetime.strptime(summary['created_at'], "%Y-%m-%d %H:%M:%S")
        date_str = created_date.strftime("%d/%m/%Y %H:%M")
        
        period_str = ""
        if summary.get('date_from') and summary.get('date_to'):
            date_from = datetime.strptime(summary['date_from'], "%Y-%m-%d").strftime("%d/%m/%Y")
            date_to = datetime.strptime(summary['date_to'], "%Y-%m-%d").strftime("%d/%m/%Y")
            period_str = f"Período analizado: {date_from} - {date_to}"
        
        info_text = f"Tipo: {summary['summary_type']}\n"
        info_text += f"Creado: {date_str}\n"
        if period_str:
            info_text += f"{period_str}\n"
        info_text += f"Generado con: {summary.get('ai_provider', 'N/A')}"
        
        self.detail_info.setText(info_text)
        
        # Mostrar contenido
        self.detail_content.setPlainText(summary['content'])
        
        self.delete_btn.setEnabled(True)
    
    def open_generate_dialog(self):
        """Abre el diálogo para generar un nuevo resumen"""
        dialog = GenerateSummaryDialog(self.storage, self)
        if dialog.exec():
            self.load_coachees_filter()
            self.load_summaries()
    
    def delete_summary(self):
        """Elimina el resumen seleccionado"""
        current_item = self.summaries_list.currentItem()
        if not current_item:
            return
        
        summary = current_item.data(Qt.UserRole)
        if not summary:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Estás seguro de que deseas eliminar este resumen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage.delete_summary(summary['id'])
                self.load_summaries()
                QMessageBox.information(self, "Éxito", "Resumen eliminado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar el resumen: {str(e)}")
    
    def set_coachee(self, coachee):
        """Establece el coachee actual y filtra los resúmenes"""
        self.current_coachee = coachee
        if coachee:
            index = self.filter_combo.findData(coachee.id)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)