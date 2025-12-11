from dataclasses import dataclass
from typing import Optional


@dataclass
class Coachee:
    id: Optional[int]
    nombre: str
    apellido: str
    email: Optional[str]
    telefono: str

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'telefono': self.telefono
        }

    @staticmethod
    def from_dict(data):
        return Coachee(
            id=data.get('id'),
            nombre=data['nombre'],
            apellido=data['apellido'],
            email=data.get('email'),
            telefono=data['telefono']
        )
