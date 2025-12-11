from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QPushButton, QMessageBox,
                               QListWidgetItem, QGroupBox, QTableWidget,
                               QTableWidgetItem, QHeaderView, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import datetime


class PaymentsView(QWidget):
    """Vista de control de pagos"""
    
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.current_coachee = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Encabezado
        header_layout = QHBoxLayout()
        
        title = QLabel("Control de Pagos")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filtro por coachee
        header_layout.addWidget(QLabel("Filtrar por:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todos los coachees", None)
        self.filter_combo.addItem("Solo sesiones pendientes", "unpaid")
        self.filter_combo.currentIndexChanged.connect(self.load_payments)
        header_layout.addWidget(self.filter_combo)
        
        layout.addLayout(header_layout)
        
        # Resumen general
        summary_group = QGroupBox("Resumen General")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 13px; padding: 10px;")
        summary_layout.addWidget(self.summary_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Tabla de pagos por coachee
        coachees_group = QGroupBox("Pagos por Coachee")
        coachees_layout = QVBoxLayout()
        
        self.coachees_table = QTableWidget()
        self.coachees_table.setColumnCount(6)
        self.coachees_table.setHorizontalHeaderLabels([
            "Coachee", "Total Sesiones", "Pagadas", "Pendientes", 
            "Total Cobrado", "Total Pendiente"
        ])
        self.coachees_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.coachees_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.coachees_table.setEditTriggers(QTableWidget.NoEditTriggers)
        coachees_layout.addWidget(self.coachees_table)
        
        coachees_group.setLayout(coachees_layout)
        layout.addWidget(coachees_group, stretch=1)
        
        # Lista de sesiones pendientes
        pending_group = QGroupBox("Sesiones Pendientes de Pago")
        pending_layout = QVBoxLayout()
        
        self.pending_list = QListWidget()
        self.pending_list.itemDoubleClicked.connect(self.mark_as_paid)
        pending_layout.addWidget(self.pending_list)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.mark_paid_btn = QPushButton("Marcar como Pagada")
        self.mark_paid_btn.clicked.connect(self.mark_as_paid_selected)
        self.mark_paid_btn.setMinimumWidth(150)
        self.mark_paid_btn.setProperty("class", "primary")
        self.mark_paid_btn.setEnabled(False)
        buttons_layout.addWidget(self.mark_paid_btn)
        
        pending_layout.addLayout(buttons_layout)
        
        pending_group.setLayout(pending_layout)
        layout.addWidget(pending_group, stretch=1)
        
        self.setLayout(layout)
        
        # Conectar selección
        self.pending_list.itemClicked.connect(self.on_pending_selected)
        
        # Cargar datos
        self.load_coachees_filter()
        self.load_payments()
    
    def load_coachees_filter(self):
        """Carga los coachees en el filtro"""
        current_text = self.filter_combo.currentText()
        self.filter_combo.clear()
        self.filter_combo.addItem("Todos los coachees", None)
        self.filter_combo.addItem("Solo sesiones pendientes", "unpaid")
        
        coachees = self.storage.get_all_coachees()
        for coachee in coachees:
            self.filter_combo.addItem(coachee.nombre_completo, coachee.id)
        
        # Restaurar selección si es posible
        index = self.filter_combo.findText(current_text)
        if index >= 0:
            self.filter_combo.setCurrentIndex(index)
    
    def load_payments(self):
        """Carga todos los datos de pagos"""
        self.load_summary()
        self.load_coachees_table()
        self.load_pending_sessions()
    
    def load_summary(self):
        """Carga el resumen general de pagos"""
        coachees = self.storage.get_all_coachees()
        
        total_sessions = 0
        total_paid = 0
        total_unpaid = 0
        amount_paid = 0
        amount_pending = 0
        
        for coachee in coachees:
            summary = self.storage.get_payment_summary_by_coachee(coachee.id)
            total_sessions += summary['total_sessions']
            total_paid += summary['paid_sessions']
            total_unpaid += summary['unpaid_sessions']
            amount_paid += summary['total_paid']
            amount_pending += summary['total_pending']
        
        summary_text = f"""
        <b>Sesiones Totales:</b> {total_sessions}<br>
        <b>Sesiones Pagadas:</b> {total_paid} <span style='color: #4CAF50;'>(${amount_paid:.2f})</span><br>
        <b>Sesiones Pendientes:</b> {total_unpaid} <span style='color: #F44336;'>(${amount_pending:.2f})</span>
        """
        
        self.summary_label.setText(summary_text)
    
    def load_coachees_table(self):
        """Carga la tabla de pagos por coachee"""
        self.coachees_table.setRowCount(0)
        
        filter_data = self.filter_combo.currentData()
        coachees = self.storage.get_all_coachees()
        
        row = 0
        for coachee in coachees:
            summary = self.storage.get_payment_summary_by_coachee(coachee.id)
            
            # Filtrar si es necesario
            if filter_data == "unpaid" and summary['unpaid_sessions'] == 0:
                continue
            elif filter_data and filter_data != "unpaid" and coachee.id != filter_data:
                continue
            
            self.coachees_table.insertRow(row)
            
            # Nombre
            name_item = QTableWidgetItem(coachee.nombre_completo)
            self.coachees_table.setItem(row, 0, name_item)
            
            # Total sesiones
            total_item = QTableWidgetItem(str(summary['total_sessions']))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.coachees_table.setItem(row, 1, total_item)
            
            # Pagadas
            paid_item = QTableWidgetItem(str(summary['paid_sessions']))
            paid_item.setTextAlignment(Qt.AlignCenter)
            paid_item.setForeground(QColor("#4CAF50"))
            self.coachees_table.setItem(row, 2, paid_item)
            
            # Pendientes
            unpaid_item = QTableWidgetItem(str(summary['unpaid_sessions']))
            unpaid_item.setTextAlignment(Qt.AlignCenter)
            if summary['unpaid_sessions'] > 0:
                unpaid_item.setForeground(QColor("#F44336"))
            self.coachees_table.setItem(row, 3, unpaid_item)
            
            # Total cobrado
            paid_amount_item = QTableWidgetItem(f"${summary['total_paid']:.2f}")
            paid_amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.coachees_table.setItem(row, 4, paid_amount_item)
            
            # Total pendiente
            pending_amount_item = QTableWidgetItem(f"${summary['total_pending']:.2f}")
            pending_amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.coachees_table.setItem(row, 5, pending_amount_item)
            
            row += 1
    
    def load_pending_sessions(self):
        """Carga la lista de sesiones pendientes"""
        self.pending_list.clear()
        
        filter_data = self.filter_combo.currentData()
        coachees = self.storage.get_all_coachees()
        
        pending_count = 0
        
        for coachee in coachees:
            # Filtrar por coachee si es necesario
            if filter_data and filter_data != "unpaid" and coachee.id != filter_data:
                continue
            
            unpaid_sessions = self.storage.get_unpaid_sessions_by_coachee(coachee.id)
            
            for session in unpaid_sessions:
                session_date = datetime.strptime(session.fecha, "%Y-%m-%d %H:%M:%S")
                date_str = session_date.strftime("%d/%m/%Y")
                
                monto_str = f"${session.monto:.2f}" if hasattr(session, 'monto') and session.monto > 0 else "Sin monto"
                
                item_text = f"⏳ {coachee.nombre_completo} - {date_str} - {monto_str}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {'session': session, 'coachee': coachee})
                self.pending_list.addItem(item)
                pending_count += 1
        
        if pending_count == 0:
            item = QListWidgetItem("✅ No hay sesiones pendientes de pago")
            item.setFlags(Qt.NoItemFlags)
            self.pending_list.addItem(item)
    
    def on_pending_selected(self, item):
        """Maneja la selección de una sesión pendiente"""
        data = item.data(Qt.UserRole)
        self.mark_paid_btn.setEnabled(data is not None)
    
    def mark_as_paid_selected(self):
        """Marca como pagada la sesión seleccionada"""
        current_item = self.pending_list.currentItem()
        if not current_item:
            return
        
        self.mark_as_paid(current_item)
    
    def mark_as_paid(self, item):
        """Marca una sesión como pagada"""
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        session = data['session']
        coachee = data['coachee']
        
        # Preguntar por el monto si no lo tiene
        from PySide6.QtWidgets import QInputDialog
        
        current_amount = session.monto if hasattr(session, 'monto') else 0
        
        amount, ok = QInputDialog.getDouble(
            self,
            "Monto de la Sesión",
            f"Ingresa el monto pagado por {coachee.nombre_completo}:",
            current_amount,
            0,
            999999.99,
            2
        )
        
        if ok:
            try:
                self.storage.update_session_payment(session.id, True, amount)
                QMessageBox.information(
                    self, 
                    "Éxito", 
                    f"Sesión de {coachee.nombre_completo} marcada como pagada."
                )
                self.load_payments()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar el pago: {str(e)}")
    
    def set_coachee(self, coachee):
        """Filtra por un coachee específico"""
        self.current_coachee = coachee
        if coachee:
            index = self.filter_combo.findData(coachee.id)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)