from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Session:
    id: Optional[int]
    coachee_id: int
    fecha: str
    notas: str

    def to_dict(self):
        return {
            'id': self.id,
            'coachee_id': self.coachee_id,
            'fecha': self.fecha,
            'notas': self.notas
        }

    @staticmethod
    def from_dict(data):
        return Session(
            id=data.get('id'),
            coachee_id=data['coachee_id'],
            fecha=data['fecha'],
            notas=data['notas']
        )
