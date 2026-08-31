import json
from bs4 import BeautifulSoup
import requests
from trabajador import Trabajador
import re

URL_BASE = "https://www.milanuncios.com"

URL_LISTADO = (
    "https://www.milanuncios.com/ofertas-de-empleo-en-madrid/"
    "?dias=10&fromSearch=1&orden=date&s=peon&pagina=1"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

_PATRON_NUMERO = re.compile(r"(?<!\d)(?:\d[\s()./-]?){8}\d(?!\d)")

def obtener_urls_anuncios():
    """Devuelve los enlaces de los ``article`` del listado, página a página.

    Milanuncios puede publicar el mismo anuncio en más de una página, por lo
    que se eliminan duplicados conservando el orden de aparición. La búsqueda
    termina cuando el contenedor no existe, no contiene artículos o se alcanza
    un límite de seguridad.
    """

    from urllib.parse import urljoin

    urls: list[str] = []
    urls_vistas: set[str] = set()
    pagina = 1
    max_paginas = 100

    while pagina <= max_paginas:
        url_pagina = re.sub(
            r"([?&]pagina=)\d+",
            rf"\g<1>{pagina}",
            URL_LISTADO,
            count=1,
        )
        if "pagina=" not in url_pagina:
            separador = "&" if "?" in url_pagina else "?"
            url_pagina = f"{url_pagina}{separador}pagina={pagina}"

        try:
            respuesta = requests.get(url_pagina, headers=HEADERS, timeout=30)
            respuesta.raise_for_status()
        except requests.RequestException as exc:
            print(f"No se pudo cargar el listado {url_pagina}: {exc}")
            break

        soup = BeautifulSoup(respuesta.text, "html.parser")
        contenedor = soup.select_one(
            "div.ma-AdList.ma-AdList--listingCard3AdsPerRow"
        )
        if contenedor is None:
            print(f"No se encontró el contenedor de anuncios en la página {pagina}.")
            break

        articulos = contenedor.find_all("article")
        if not articulos:
            print(f"No hay artículos en la página {pagina}; fin del listado.")
            break

        encontrados_en_pagina = 0
        for articulo in articulos:
            enlace = articulo.select_one("a.ma-AdCardListingV2-TitleLink[href]")
            if enlace is None:
                enlace = articulo.find("a", href=True)
            if enlace is None:
                continue

            href = enlace.get("href", "").strip()
            if not href:
                continue
            url = urljoin(URL_BASE, href)
            if not url.startswith(("http://", "https://")) or url in urls_vistas:
                continue

            urls_vistas.add(url)
            urls.append(url)
            encontrados_en_pagina += 1

        print(f"Página {pagina}: {encontrados_en_pagina} enlaces nuevos.")
        if encontrados_en_pagina == 0:
            print("La página no contiene enlaces nuevos; fin del listado.")
            break
        pagina += 1

    return urls

def extraer_trabajador(url):

    respuesta = requests.get(url, headers=HEADERS, timeout=30)
    html = respuesta.text
    soup = BeautifulSoup(html, "html.parser")

    nombre = soup.find("h2", class_="ma-UserOverviewProfileName")
    nombre = nombre.get_text().strip() if nombre else "Nombre no encontrado"

    puesto = soup.find("h1")
    puesto = puesto.get_text().strip() if puesto else "Puesto no indicado"

    descripcion = soup.find("p", class_="ma-AdDetail-description")
    descripcion = descripcion.get_text().strip() if descripcion else "Sin descripción"

    seccion = soup.find("section", class_="ma-AdStatistics")
    parrafos = seccion.find_all("p") if seccion else []

    fecha = parrafos[0].get_text().strip() if len(parrafos) > 0 else "Fecha no disponible"
    actualizado = parrafos[1].get_text().strip() if len(parrafos) > 1 else "Actualización no disponible"

    tel = extraer_numero(descripcion)

    return Trabajador(nombre=nombre, puesto=puesto, url=url, numero=tel, descripcion=descripcion, fecha=fecha, actualizado=actualizado)

# Busca el json embebido en el HTML
def _extraer_initial_props(html):
    
    marcador = 'window.__INITIAL_PROPS__ = JSON.parse("'
    inicio = html.find(marcador)
    if inicio == -1:
        return None
    inicio += len(marcador)

    fin = html.find('");', inicio)
    if fin == -1:
        return None

    # Formatea el json
    json_escapado = html[inicio:fin]
    json_limpio = json_escapado.replace('\\"', '"').replace('\\\\', '\\')

    try:
        return json.loads(json_limpio)
    except json.JSONDecodeError:
        print("Error al parsear el JSON de __INITIAL_PROPS__.")
        return None

def extraer_numero(descripcion: str) -> str:

    for match in _PATRON_NUMERO.finditer(descripcion or ""):
        numero = re.sub(r"\D", "", match.group(0))
        if len(numero) == 9:
            return numero
    return "Número no encontrado"
