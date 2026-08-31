from dataclasses import dataclass

@dataclass
class Trabajador:

    nombre: str
    puesto: str
    url: str
    numero: str
    descripcion: str
    fecha: str
    actualizado: str

    def __str__(self):
        return (
            f"Nombre: {self.nombre}\n"
            f"Puesto: {self.puesto}\n"
            f"URL: {self.url}"
            f"Numero: {self.numero}\n"
            f"Descripcion: {self.descripcion}\n"
            f"Fecha: {self.fecha}\n"
            f"Actualizado: {self.actualizado}\n"
        )
