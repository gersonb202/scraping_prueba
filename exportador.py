import logging
from pathlib import Path

from trabajador import Trabajador

logger = logging.getLogger(__name__)

class ExportadorTrabajodores:
    def __init__(self, ruta_archivo: str = "trabajadores.txt") -> None:
        self.ruta = Path(ruta_archivo)

    def exportar(self, trabajadores: list[Trabajador]) -> None:
        if not trabajadores:
            logger.warning("No hay trabajadores para exportar.")
            return

    self.ruta.parent.mkdir(parents=True, exist_ok=True)

    try:
            with self.ruta.open(mode="w", encoding="utf-8") as archivo:
                archivo.write(
                    f"{'=' * 60}\n"
                    f"  LISTADO DE TRABAJADORES — {len(trabajadores)} registro(s)\n"
                    f"{'=' * 60}\n\n"
                )
                for idx, trabajador in enumerate(trabajadores, start=1):
                    archivo.write(f"{idx:>3}. {trabajador}\n")

                archivo.write(f"\n{'=' * 60}\n")

            logger.info("Archivo exportado correctamente → %s", self.ruta.resolve())
            print(f"\n✅  Exportados {len(trabajadores)} trabajadores → {self.ruta.resolve()}")

    except OSError as exc:
        logger.error("Error al escribir el archivo %s: %s", self.ruta, exc)
        raise