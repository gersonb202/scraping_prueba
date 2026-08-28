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


    def _descargar_pagina(self) -> Optional[str]:
        """Realiza la petición HTTP y devuelve el HTML como cadena."""
        try:
            response = requests.get(
                self.url, headers=_HEADERS, timeout=self.timeout
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            logger.error("Tiempo de espera agotado al conectar con %s", self.url)
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con %s", self.url)
        except requests.exceptions.HTTPError as exc:
            logger.error("Error HTTP %s al obtener %s", exc.response.status_code, self.url)
        return None

    def _extraer_trabajadores(self) -> list[Trabajador]:
        """
        Recorre el DOM buscando nodos cuyo texto coincida con un oficio
        conocido y trata de inferir nombre y descripción del contexto.
        """
        encontrados: list[Trabajador] = []
        vistos: set[str] = set()

        candidatos: list[Tag] = self._soup.find_all(
            ["div", "article", "section", "li", "tr", "span", "p", "h1", "h2", "h3"]
        )

        for elemento in candidatos:
            texto = elemento.get_text(separator=" ", strip=True)
            match = _PATTERN.search(texto)
            if not match:
                continue

            oficio = match.group(0).upper()
            nombre = self._inferir_nombre(elemento)
            descripcion = self._inferir_descripcion(elemento, texto)

            clave = (nombre.lower(), oficio)
            if clave in vistos:
                continue
            vistos.add(clave)

            encontrados.append(
                Trabajador(nombre=nombre, trabajo=oficio, descripcion=descripcion)
            )

        return encontrados