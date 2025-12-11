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
                FOREIGN KEY (coachee_id) REFERENCES coachees (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Nueva tabla para sesiones programadas
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

        conn.commit()
        conn.close()

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
            INSERT INTO sessions (coachee_id, fecha, notas)
            VALUES (?, ?, ?)
        ''', (session.coachee_id, session.fecha, session.notas))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def get_sessions_by_coachee(self, coachee_id: int) -> List[Session]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, coachee_id, fecha, notas FROM sessions
            WHERE coachee_id = ?
            ORDER BY fecha DESC
        ''', (coachee_id,))

        rows = cursor.fetchall()
        conn.close()

        return [Session(id=row[0], coachee_id=row[1], fecha=row[2], notas=row[3]) for row in rows]

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
