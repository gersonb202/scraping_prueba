from dataclasses import dataclass


@dataclass
class Trabajador:
    """Datos básicos de un anuncio de trabajo."""

    nombre: str
    puesto: str
    url: str

    def __str__(self):
        return (
            f"Nombre: {self.nombre}\n"
            f"Puesto: {self.puesto}\n"
            f"URL: {self.url}"
        )
