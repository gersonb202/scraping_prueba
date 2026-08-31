import json
import re
from bs4 import BeautifulSoup
import requests
from trabajador import Trabajador

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

# Nueve dígitos exactos, permitiendo separadores habituales entre ellos.
# El límite de dígitos evita capturar una parte de un número más largo.
_PATRON_NUMERO = re.compile(r"(?<!\d)(?:\d[\s()./-]?){8}\d(?!\d)")

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
    soup = BeautifulSoup(html, "html.parser")

    nombre = soup.find("h2", class_="ma-UserOverviewProfileName")
    nombre = nombre.get_text().strip() if nombre else "Nombre no encontrado"

    puesto = soup.find("h1")
    puesto = puesto.get_text().strip() if puesto else "Puesto no indicado"



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

def extraer_numero(descripcion: str) -> str:

    for match in _PATRON_NUMERO.finditer(descripcion or ""):
        numero = re.sub(r"\D", "", match.group(0))
        if len(numero) == 9:
            return numero
    return "Número no encontrado"
