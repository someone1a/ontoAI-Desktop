from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Session:
    id: Optional[int]
    coachee_id: int
    fecha: str
    notas: str
    pagado: bool = False
    monto: float = 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'coachee_id': self.coachee_id,
            'fecha': self.fecha,
            'notas': self.notas,
            'pagado': self.pagado,
            'monto': self.monto
        }

    @staticmethod
    def from_dict(data):
        return Session(
            id=data.get('id'),
            coachee_id=data['coachee_id'],
            fecha=data['fecha'],
            notas=data['notas'],
            pagado=data.get('pagado', False),
            monto=data.get('monto', 0.0)
        )