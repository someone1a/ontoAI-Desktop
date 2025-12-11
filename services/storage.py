import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from models.coachee import Coachee
from models.session import Session


class Storage:
    def __init__(self, db_path: str = "onto-ai.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coachees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                email TEXT,
                telefono TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coachee_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                notas TEXT NOT NULL,
                pagado INTEGER DEFAULT 0,
                monto REAL DEFAULT 0,
                FOREIGN KEY (coachee_id) REFERENCES coachees (id)
            )
        ''')

        # Verificar si existen las columnas pagado y monto, si no agregarlas
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'pagado' not in columns:
            cursor.execute('ALTER TABLE sessions ADD COLUMN pagado INTEGER DEFAULT 0')
        
        if 'monto' not in columns:
            cursor.execute('ALTER TABLE sessions ADD COLUMN monto REAL DEFAULT 0')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coachee_id INTEGER NOT NULL,
                scheduled_time TEXT NOT NULL,
                title TEXT,
                notes TEXT,
                duration INTEGER DEFAULT 60,
                notify_enabled INTEGER DEFAULT 1,
                notify_time TEXT,
                status TEXT DEFAULT 'scheduled',
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (coachee_id) REFERENCES coachees (id)
            )
        ''')

        # Nueva tabla para resúmenes generados por IA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coachee_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary_type TEXT NOT NULL,
                content TEXT NOT NULL,
                sessions_included TEXT,
                date_from TEXT,
                date_to TEXT,
                created_at TEXT NOT NULL,
                ai_provider TEXT,
                FOREIGN KEY (coachee_id) REFERENCES coachees (id)
            )
        ''')

        conn.commit()
        conn.close()

    # Métodos para resúmenes
    def add_summary(self, summary_data: dict) -> int:
        """Agrega un nuevo resumen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO summaries (
                coachee_id, title, summary_type, content, 
                sessions_included, date_from, date_to, 
                created_at, ai_provider
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            summary_data['coachee_id'],
            summary_data['title'],
            summary_data['summary_type'],
            summary_data['content'],
            summary_data.get('sessions_included', ''),
            summary_data.get('date_from', ''),
            summary_data.get('date_to', ''),
            summary_data['created_at'],
            summary_data.get('ai_provider', '')
        ))

        summary_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return summary_id

    def get_summaries_by_coachee(self, coachee_id: int) -> list:
        """Obtiene todos los resúmenes de un coachee"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, title, summary_type, content,
                   sessions_included, date_from, date_to,
                   created_at, ai_provider
            FROM summaries
            WHERE coachee_id = ?
            ORDER BY created_at DESC
        ''', (coachee_id,))

        rows = cursor.fetchall()
        conn.close()

        summaries = []
        for row in rows:
            summaries.append({
                'id': row[0],
                'coachee_id': row[1],
                'title': row[2],
                'summary_type': row[3],
                'content': row[4],
                'sessions_included': row[5],
                'date_from': row[6],
                'date_to': row[7],
                'created_at': row[8],
                'ai_provider': row[9]
            })

        return summaries

    def get_all_summaries(self) -> list:
        """Obtiene todos los resúmenes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, title, summary_type, content,
                   sessions_included, date_from, date_to,
                   created_at, ai_provider
            FROM summaries
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        summaries = []
        for row in rows:
            summaries.append({
                'id': row[0],
                'coachee_id': row[1],
                'title': row[2],
                'summary_type': row[3],
                'content': row[4],
                'sessions_included': row[5],
                'date_from': row[6],
                'date_to': row[7],
                'created_at': row[8],
                'ai_provider': row[9]
            })

        return summaries

    def delete_summary(self, summary_id: int):
        """Elimina un resumen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM summaries WHERE id = ?', (summary_id,))

        conn.commit()
        conn.close()

    def get_sessions_by_date_range(self, coachee_id: int, date_from: str, date_to: str) -> List[Session]:
        """Obtiene sesiones de un coachee en un rango de fechas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, fecha, notas, pagado, monto FROM sessions
            WHERE coachee_id = ? AND fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        ''', (coachee_id, date_from, date_to))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            session = Session(id=row[0], coachee_id=row[1], fecha=row[2], notas=row[3])
            session.pagado = bool(row[4]) if len(row) > 4 else False
            session.monto = row[5] if len(row) > 5 else 0
            sessions.append(session)
        return sessions

    # Métodos existentes...
    def add_scheduled_session(self, session_data: dict) -> int:
        """Agrega una sesión programada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scheduled_sessions (
                coachee_id, scheduled_time, title, notes, 
                duration, notify_enabled, notify_time, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data['coachee_id'],
            session_data['scheduled_time'],
            session_data.get('title', ''),
            session_data.get('notes', ''),
            session_data.get('duration', 60),
            1 if session_data.get('notify_enabled', True) else 0,
            session_data.get('notify_time', ''),
            session_data.get('status', 'scheduled')
        ))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def get_sessions_by_date(self, date_str: str) -> list:
        """Obtiene todas las sesiones programadas para una fecha específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, scheduled_time, title, notes, 
                   duration, notify_enabled, notify_time, status, notified
            FROM scheduled_sessions
            WHERE date(scheduled_time) = ?
            ORDER BY scheduled_time
        ''', (date_str,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'coachee_id': row[1],
                'scheduled_time': row[2],
                'title': row[3],
                'notes': row[4],
                'duration': row[5],
                'notify_enabled': bool(row[6]),
                'notify_time': row[7],
                'status': row[8],
                'notified': bool(row[9])
            })

        return sessions

    def get_all_scheduled_sessions(self) -> list:
        """Obtiene todas las sesiones programadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, scheduled_time, title, notes, 
                   duration, notify_enabled, notify_time, status, notified
            FROM scheduled_sessions
            ORDER BY scheduled_time
        ''')

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'coachee_id': row[1],
                'scheduled_time': row[2],
                'title': row[3],
                'notes': row[4],
                'duration': row[5],
                'notify_enabled': bool(row[6]),
                'notify_time': row[7],
                'status': row[8],
                'notified': bool(row[9])
            })

        return sessions

    def get_sessions_by_coachee_calendar(self, coachee_id: int) -> list:
        """Obtiene todas las sesiones programadas para un coachee específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, scheduled_time, title, notes, 
                   duration, notify_enabled, notify_time, status, notified
            FROM scheduled_sessions
            WHERE coachee_id = ?
            ORDER BY scheduled_time DESC
        ''', (coachee_id,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'coachee_id': row[1],
                'scheduled_time': row[2],
                'title': row[3],
                'notes': row[4],
                'duration': row[5],
                'notify_enabled': bool(row[6]),
                'notify_time': row[7],
                'status': row[8],
                'notified': bool(row[9])
            })

        return sessions

    def update_session_status(self, session_id: int, status: str):
        """Actualiza el estado de una sesión programada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE scheduled_sessions
            SET status = ?
            WHERE id = ?
        ''', (status, session_id))

        conn.commit()
        conn.close()

    def mark_session_notified(self, session_id: int):
        """Marca una sesión como notificada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE scheduled_sessions
            SET notified = 1
            WHERE id = ?
        ''', (session_id,))

        conn.commit()
        conn.close()

    def delete_scheduled_session(self, session_id: int):
        """Elimina una sesión programada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM scheduled_sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()

    def add_coachee(self, coachee: Coachee) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO coachees (nombre, apellido, email, telefono)
            VALUES (?, ?, ?, ?)
        ''', (coachee.nombre, coachee.apellido, coachee.email, coachee.telefono))

        coachee_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return coachee_id

    def get_all_coachees(self) -> List[Coachee]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nombre, apellido, email, telefono FROM coachees ORDER BY apellido, nombre')
        rows = cursor.fetchall()
        conn.close()

        return [Coachee(id=row[0], nombre=row[1], apellido=row[2], email=row[3], telefono=row[4]) for row in rows]

    def search_coachees(self, query: str) -> List[Coachee]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        cursor.execute('''
            SELECT id, nombre, apellido, email, telefono FROM coachees
            WHERE nombre LIKE ? OR apellido LIKE ? OR email LIKE ? OR telefono LIKE ?
            ORDER BY apellido, nombre
        ''', (search_pattern, search_pattern, search_pattern, search_pattern))

        rows = cursor.fetchall()
        conn.close()

        return [Coachee(id=row[0], nombre=row[1], apellido=row[2], email=row[3], telefono=row[4]) for row in rows]

    def get_coachee(self, coachee_id: int) -> Optional[Coachee]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nombre, apellido, email, telefono FROM coachees WHERE id = ?', (coachee_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Coachee(id=row[0], nombre=row[1], apellido=row[2], email=row[3], telefono=row[4])
        return None

    def add_session(self, session: Session) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sessions (coachee_id, fecha, notas, pagado, monto)
            VALUES (?, ?, ?, ?, ?)
        ''', (session.coachee_id, session.fecha, session.notas, 
              1 if session.pagado else 0, session.monto if hasattr(session, 'monto') else 0))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def get_sessions_by_coachee(self, coachee_id: int) -> List[Session]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, fecha, notas, pagado, monto FROM sessions
            WHERE coachee_id = ?
            ORDER BY fecha DESC
        ''', (coachee_id,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            session = Session(id=row[0], coachee_id=row[1], fecha=row[2], notas=row[3])
            session.pagado = bool(row[4]) if len(row) > 4 else False
            session.monto = row[5] if len(row) > 5 else 0
            sessions.append(session)
        return sessions

    def update_session_payment(self, session_id: int, pagado: bool, monto: float = 0):
        """Actualiza el estado de pago de una sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sessions
            SET pagado = ?, monto = ?
            WHERE id = ?
        ''', (1 if pagado else 0, monto, session_id))

        conn.commit()
        conn.close()

    def get_unpaid_sessions_by_coachee(self, coachee_id: int) -> List[Session]:
        """Obtiene todas las sesiones no pagadas de un coachee"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, fecha, notas, pagado, monto FROM sessions
            WHERE coachee_id = ? AND pagado = 0
            ORDER BY fecha DESC
        ''', (coachee_id,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            session = Session(id=row[0], coachee_id=row[1], fecha=row[2], notas=row[3])
            session.pagado = bool(row[4])
            session.monto = row[5]
            sessions.append(session)
        return sessions

    def get_payment_summary_by_coachee(self, coachee_id: int) -> dict:
        """Obtiene un resumen de pagos por coachee"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN pagado = 1 THEN 1 ELSE 0 END) as paid_sessions,
                SUM(CASE WHEN pagado = 0 THEN 1 ELSE 0 END) as unpaid_sessions,
                SUM(CASE WHEN pagado = 1 THEN monto ELSE 0 END) as total_paid,
                SUM(CASE WHEN pagado = 0 THEN monto ELSE 0 END) as total_pending
            FROM sessions
            WHERE coachee_id = ?
        ''', (coachee_id,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_sessions': row[0] or 0,
            'paid_sessions': row[1] or 0,
            'unpaid_sessions': row[2] or 0,
            'total_paid': row[3] or 0,
            'total_pending': row[4] or 0
        }

    def save_setting(self, key: str, value):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        value_str = json.dumps(value) if not isinstance(value, str) else value
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value_str))

        conn.commit()
        conn.close()

    def get_setting(self, key: str, default=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
        return default