from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Trabajador:

    nombre: str
    puesto: str
    url: str
    numero: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    fecha_edicion: Optional[str] = None
    descripcion: Optional[str] = None
    fuente: str = "Milanuncios"

    @property
    def trabajo(self) -> str:

        return self.puesto

    def __str__(self) -> str:
        return (
            f"Nombre: {self.nombre}\n"
            f"Puesto: {self.puesto}\n"
            f"Número: {self.numero or 'No encontrado'}\n"
            f"Fecha publicación: {self.fecha_publicacion or 'No disponible'}\n"
            f"Fecha edición: {self.fecha_edicion or 'No disponible'}\n"
            f"Descripción: {self.descripcion or 'Sin descripción'}\n"
            f"Enlace: {self.url}"
        )
