import logging
import re
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from trabajador import Trabajador

logger = logging.getLogger(__name__)

OFICIOS_CONOCIDOS: list[str] = [
    "FONTANERO",
    "PLADURISTA",
    "ELECTRICISTA",
    "PINTOR",
    "ALBAÑIL",
    "CARPINTERO",
    "CERRAJERO",
    "CRISTALERO",
    "SOLDADOR",
    "JARDINERO",
    "LIMPIADOR",
    "REFORMAS",
    "CLIMATIZACIÓN",
    "INSTALADOR",
    "MECÁNICO",
]

_PATTERN = re.compile(
    "|".join(re.escape(o) for o in OFICIOS_CONOCIDOS),
    flags=re.IGNORECASE,
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


class ScraperTrabajadores:

    def __init__(self, url: str, timeout: int = 10) -> None:
        self.url = url
        self.timeout = timeout
        self._soup: Optional[BeautifulSoup] = None

    def obtener_trabajadores(self) -> list[Trabajador]:

        html = self._descargar_pagina()
        if not html:
            return []

        self._soup = BeautifulSoup(html, "html.parser")
        trabajadores = self._extraer_trabajadores()

        logger.info("Encontrados %d trabajadores en %s", len(trabajadores), self.url)
        return trabajadores