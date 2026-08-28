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
    def _inferir_nombre(self, elemento: Tag) -> str:

        for tag in ["h1", "h2", "h3", "strong", "b"]:
            found = elemento.find(tag)
            if found:
                nombre = found.get_text(strip=True)
                if nombre and not _PATTERN.fullmatch(nombre):
                    return nombre[:100]

        for enlace in elemento.find_all("a", href=True):
            texto_enlace = enlace.get_text(strip=True)
            if texto_enlace and not _PATTERN.fullmatch(texto_enlace):
                return texto_enlace[:100]

        fragmentos = [
            t.strip()
            for t in elemento.strings
            if t.strip() and not _PATTERN.fullmatch(t.strip())
        ]
        if fragmentos:
            return fragmentos[0][:100]

        return "Desconocido"

    def _inferir_descripcion(self, elemento: Tag, texto_completo: str) -> str:
        
        parrafo = elemento.find("p")
        if parrafo:
            desc = parrafo.get_text(strip=True)
            if desc:
                return desc[:200]

        for tag in elemento.find_all(True):
            for attr in ("title", "alt"):
                valor = tag.get(attr, "")
                if valor and len(valor) > 5:
                    return str(valor)[:200]

        if texto_completo:
            return texto_completo[:200]

        return "Sin descripción"