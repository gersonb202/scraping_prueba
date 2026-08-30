"""Exportación legible de anuncios de trabajo."""

import logging
from pathlib import Path

from trabajador import Trabajador

logger = logging.getLogger(__name__)


class ExportadorTrabajadores:
    def __init__(self, ruta_archivo: str = "/home/gerson/Proyectos/scraping_trabajador/datos/trabajadores.txt") -> None:
        self.ruta = Path(ruta_archivo)

    def exportar(self, trabajadores: list[Trabajador]) -> None:
        if not trabajadores:
            logger.warning("No hay trabajadores para exportar.")
            return

        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.ruta.open(mode="w", encoding="utf-8", newline="\n") as archivo:
                archivo.write(
                    f"{'=' * 70}\n"
                    f"  LISTADO DE ANUNCIOS — {len(trabajadores)} registro(s)\n"
                    f"{'=' * 70}\n"
                )
                for indice, trabajador in enumerate(trabajadores, start=1):
                    archivo.write(f"\n{'-' * 70}\n[{indice}]\n{trabajador}\n")
                archivo.write(f"\n{'=' * 70}\n")
        except OSError as exc:
            logger.error("Error al escribir el archivo %s: %s", self.ruta, exc)
            raise

        logger.info("Archivo exportado correctamente → %s", self.ruta.resolve())
        print(f"\nExportados {len(trabajadores)} anuncios → {self.ruta.resolve()}")


# Alias temporal para código que importaba el nombre con la errata original.
ExportadorTrabajodores = ExportadorTrabajadores
