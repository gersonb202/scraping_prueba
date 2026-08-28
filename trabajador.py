from dataclasses import dataclass
from typing import Optional

@dataclass
class Trabajador:
    nombre: str
    trabajo: str
    descripcion: Optional[str] = None

    def __str__(self):
        return (
            f"Nombre: {self.nombre}\n"
            f"Trabajo: {self.trabajo}\n"
            f"Descripcion: {self.descripcion if self.descripcion else "Sin descripción"}"
        )
