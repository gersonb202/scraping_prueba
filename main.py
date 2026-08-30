"""Punto de entrada del scraper personal de Milanuncios."""

import argparse
import logging
import sys

from exportador import ExportadorTrabajadores
from scraper import LISTADO_POR_DEFECTO, ScraperTrabajadores


def _configurar_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def _parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrae anuncios de empleo de Milanuncios y los guarda en TXT."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=LISTADO_POR_DEFECTO,
        help="URL de búsqueda (por defecto: búsqueda de peón en Madrid).",
    )
    parser.add_argument("--salida", default="trabajadores.txt", metavar="ARCHIVO")
    parser.add_argument("--timeout", type=int, default=20, metavar="SEGUNDOS")
    parser.add_argument("--max-paginas", type=int, default=100, metavar="N")
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Muestra el navegador de Chromium durante la ejecución.",
    )
    parser.add_argument("--verbose", action="store_true", help="Activa logs de depuración.")
    return parser.parse_args()


def main() -> int:
    args = _parsear_argumentos()
    _configurar_logging(args.verbose)
    logger = logging.getLogger("main")
    logger.info("Iniciando scraping en: %s", args.url)

    try:
        trabajadores = ScraperTrabajadores(
            url=args.url,
            timeout=args.timeout,
            max_paginas=args.max_paginas,
            headed=args.visible,
        ).obtener_trabajadores()
    except (ValueError, RuntimeError) as exc:
        logger.error("No se pudo ejecutar el scraper: %s", exc)
        return 1

    if not trabajadores:
        logger.warning("No se encontraron anuncios válidos.")
        return 0

    print(f"\n{'─' * 70}")
    print(f"  Se encontraron {len(trabajadores)} anuncio(s):")
    print(f"{'─' * 70}")
    for indice, trabajador in enumerate(trabajadores, 1):
        print(f"\n[{indice}]\n{trabajador}")

    ExportadorTrabajadores(ruta_archivo=args.salida).exportar(trabajadores)
    return 0


if __name__ == "__main__":
    sys.exit(main())
