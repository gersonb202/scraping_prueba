from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from trabajador import Trabajador

logger = logging.getLogger(__name__)

LISTADO_POR_DEFECTO = (
    "https://www.milanuncios.com/ofertas-de-empleo-en-madrid/"
    "?dias=10&fromSearch=1&orden=date&s=peon&pagina=1"
)

ARTICLE_SELECTOR = 'article[data-testid="AD_CARD"]'
TITLE_SELECTOR = "a.ma-AdCardListingV2-TitleLink"
DESCRIPTION_SELECTOR = "p.ma-AdDetail-description"
STATISTICS_SELECTOR = "section.ma-AdStatistics p.ma-AdDetail-time"

_NUMERO_RE = re.compile(r"(?<!\d)(?:\d[\s()./-]?){5,}\d(?!\d)")


def normalizar_texto(valor: str) -> str:

    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", valor) # Quita acentos, espacios y otros signos
        if not unicodedata.combining(caracter)
    )
    return " ".join(sin_acentos.casefold().split())


def extraer_numero(descripcion: str) -> Optional[str]:

    candidatos: list[str] = []
    for match in _NUMERO_RE.finditer(descripcion):
        bruto = match.group(0)
        if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,4}", bruto):
            continue
        digitos = re.sub(r"\D", "", bruto)
        
        if len(digitos) in {11, 13} and digitos.startswith(("34", "0034")):
            digitos = digitos[-9:]
        if 6 <= len(digitos) <= 15:
            candidatos.append(digitos)

    if not candidatos:
        return None
    return next((numero for numero in candidatos if len(numero) == 9), candidatos[0])


def _texto(locator: Any, timeout_ms: int) -> str:
    """Lee el primer elemento de un locator sin hacer fallar el anuncio."""

    try:
        return " ".join(locator.first.inner_text(timeout=timeout_ms).split())
    except Exception:
        return ""


class ScraperTrabajadores:
    """Recorre el listado y extrae anuncios individuales con Playwright."""

    def __init__(
        self,
        url: str = LISTADO_POR_DEFECTO,
        timeout: int = 20,
        max_paginas: int = 100,
        headed: bool = False,
    ) -> None:
        self.url = self._validar_url(url)
        if timeout <= 0:
            raise ValueError("El timeout debe ser mayor que cero.")
        if max_paginas <= 0:
            raise ValueError("max_paginas debe ser mayor que cero.")
        self.timeout_ms = timeout * 1000
        self.max_paginas = max_paginas
        self.headed = headed

    @staticmethod
    def _validar_url(url: str) -> str:
        partes = urlsplit(url)
        if partes.scheme not in {"http", "https"} or not partes.netloc:
            raise ValueError("La URL debe incluir un esquema http:// o https://.")
        return url

    @staticmethod
    def url_pagina(url: str, pagina: int) -> str:

        partes = urlsplit(url)
        parametros = [(clave, valor) for clave, valor in parse_qsl(partes.query)]
        actualizado = False
        nuevos: list[tuple[str, str]] = []
        for clave, valor in parametros:
            if clave == "pagina":
                if not actualizado:
                    nuevos.append((clave, str(pagina)))
                    actualizado = True
            else:
                nuevos.append((clave, valor))
        if not actualizado:
            nuevos.append(("pagina", str(pagina)))
        return urlunsplit(
            (partes.scheme, partes.netloc, partes.path, urlencode(nuevos), partes.fragment)
        )

    def obtener_trabajadores(self) -> list[Trabajador]:
        """Obtiene anuncios únicos; los errores de un anuncio no detienen el lote."""

        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Falta Playwright. Instálalo con 'pip install -r requirements.txt' "
                "y después ejecuta 'playwright install chromium'."
            ) from exc

        anuncios: list[Trabajador] = []
        urls_vistas: set[str] = set()
        nombres_vistos: set[str] = set()

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=not self.headed)
                context = browser.new_context(locale="es-ES")

                def _cerrar_tab_nueva(page: Any) -> None:
                    try:
                        if page.url in ("about:blank", ""):
                            page.close()
                            logger.debug("Pestaña nueva inesperada cerrada.")
                    except Exception:
                        pass

                context.on("page", _cerrar_tab_nueva)

                listado_page = context.new_page()
                detalle_page = context.new_page()

                COOKIE_SELECTORS = [
                    "button#didomi-notice-agree-button",
                    "button[id*='accept']",
                    "button[class*='accept']",
                    "[aria-label*='Aceptar']",
                    "[aria-label*='Accept']",
                ]

                def _aceptar_cookies(page: Any) -> None:
                    for selector in COOKIE_SELECTORS:
                        try:
                            btn = page.locator(selector).first
                            if btn.is_visible(timeout=3000):
                                btn.click(timeout=3000)
                                logger.debug("Banner de cookies aceptado (%s).", selector)
                                return
                        except Exception:
                            continue

                try:
                    for pagina in range(1, self.max_paginas + 1):
                        url_pagina = self.url_pagina(self.url, pagina)
                        enlaces = self._enlaces_de_pagina(listado_page, url_pagina, _aceptar_cookies)
                        if not enlaces:
                            logger.info("No hay anuncios en la página %d; fin del listado.", pagina)
                            break

                        enlaces_nuevos = [enlace for enlace in enlaces if enlace not in urls_vistas]
                        if not enlaces_nuevos:
                            logger.info("La página %d no contiene enlaces nuevos; fin.", pagina)
                            break
                        urls_vistas.update(enlaces_nuevos)

                        for enlace in enlaces_nuevos:
                            trabajador = self._extraer_detalle(detalle_page, enlace, _aceptar_cookies)
                            if trabajador is None:
                                continue
                            clave_nombre = normalizar_texto(trabajador.nombre)
                            if not clave_nombre or clave_nombre in nombres_vistos:
                                logger.debug("Anuncio omitido por nombre repetido: %s", enlace)
                                continue
                            nombres_vistos.add(clave_nombre)
                            anuncios.append(trabajador)
                            logger.info("Extraído %s (%s)", trabajador.nombre, enlace)
                finally:
                    context.close()
                    browser.close()
        except PlaywrightError as exc:
            raise RuntimeError(f"Playwright no pudo completar el scraping: {exc}") from exc

        logger.info("Encontrados %d trabajadores.", len(anuncios))
        return anuncios

    def _enlaces_de_pagina(self, page: Any, url: str, _aceptar_cookies: Any = None) -> list[str]:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            if _aceptar_cookies:
                _aceptar_cookies(page)
            page.wait_for_selector(ARTICLE_SELECTOR, state="attached", timeout=self.timeout_ms)
        except Exception as exc:
            logger.warning("No se pudo cargar el listado %s: %s", url, exc)
            return []

        articulos = page.locator(ARTICLE_SELECTOR)
        enlaces: list[str] = []
        for indice in range(articulos.count()):
            articulo = articulos.nth(indice)
            enlace = articulo.locator(TITLE_SELECTOR).first
            href = enlace.get_attribute("href")
            if not href:
                href = articulo.locator("a[href]").first.get_attribute("href")
            if not href:
                continue
            absoluto = urljoin(url, href)
            if absoluto.startswith(("http://", "https://")) and absoluto not in enlaces:
                enlaces.append(absoluto)
        logger.info("Página %s: %d enlaces de anuncios.", url, len(enlaces))
        return enlaces

    def _extraer_detalle(self, page: Any, url: str, _aceptar_cookies: Any = None) -> Optional[Trabajador]:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            if _aceptar_cookies:
                _aceptar_cookies(page)
            page.wait_for_selector("h1, h2", state="attached", timeout=self.timeout_ms)
        except Exception as exc:
            logger.warning("No se pudo cargar el anuncio %s: %s", url, exc)
            return None

        nombre = _texto(page.locator("h2"), self.timeout_ms)
        puesto = _texto(page.locator("h1"), self.timeout_ms)
        descripcion = _texto(page.locator(DESCRIPTION_SELECTOR), self.timeout_ms)
        fechas = [
            " ".join(texto.split())
            for texto in page.locator(STATISTICS_SELECTOR).all_inner_texts()
            if texto.strip()
        ]
        if not nombre:
            logger.warning("Anuncio sin h2 (nombre), omitido: %s", url)
            return None

        return Trabajador(
            nombre=nombre,
            puesto=puesto or "Puesto no indicado",
            url=url,
            numero=extraer_numero(descripcion),
            fecha_publicacion=fechas[0] if fechas else None,
            fecha_edicion=fechas[1] if len(fechas) > 1 else None,
            descripcion=descripcion or None,
        )
