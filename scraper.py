"""Scraper de Milanuncios: extrae datos de trabajadores desde el JSON embebido.

Estrategia:
  1. Hacer GET a la página de listado con requests
  2. Extraer el JSON de window.__INITIAL_PROPS__ del HTML
  3. Del JSON, obtener la URL de cada anuncio
  4. Hacer GET a la página de detalle de cada anuncio
  5. Extraer nombre (h2) y puesto (h1) del HTML de detalle
"""

import json
import re

import requests

from trabajador import Trabajador

URL_BASE = "https://www.milanuncios.com"

URL_LISTADO = (
    "https://www.milanuncios.com/ofertas-de-empleo-en-madrid/"
    "?dias=10&fromSearch=1&orden=date&s=peon&pagina=1"
)

# Cabeceras HTTP que imitan un navegador real.
# Sin estas cabeceras, Milanuncios puede bloquear la petición.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}


# ---------------------------------------------------------------------------
# Paso 1: Obtener URLs de anuncios desde el JSON embebido
# ---------------------------------------------------------------------------

def obtener_urls_anuncios():

    respuesta = requests.get(URL_LISTADO, headers=HEADERS, timeout=30)
    datos = _extraer_initial_props(respuesta.text)

    if datos is None:
        print("⚠ No se encontró __INITIAL_PROPS__ en la página de listado.")
        return []

    # Extraer la lista de anuncios del JSON
    anuncios = (
        datos
        .get("adListPagination", {})
        .get("adList", {})
        .get("ads", [])
    )

    if not anuncios:
        print("No se encontraron anuncios en el JSON.")
        return []

    # Construir la URL completa de cada anuncio
    urls = []
    for anuncio in anuncios:
        url_relativa = anuncio.get("url", "")
        if url_relativa:
            urls.append(URL_BASE + url_relativa)

    return urls

def extraer_trabajador(url):

    respuesta = requests.get(url, headers=HEADERS, timeout=30)
    html = respuesta.text

    match_nombre = re.search(
        r'<h2[^>]*class="ma-UserOverviewProfileName"[^>]*>([^<]+)', html
    )
    nombre = match_nombre.group(1).strip() if match_nombre else "Nombre no encontrado"

    match_puesto = re.search(r'<h1[^>]*>([^<]+)', html)
    puesto = match_puesto.group(1).strip() if match_puesto else "Puesto no indicado"

    return Trabajador(nombre=nombre, puesto=puesto, url=url)

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
        print("⚠ Error al parsear el JSON de __INITIAL_PROPS__.")
        return None
