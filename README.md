# Scraper personal de anuncios de empleo

Extrae anuncios de Milanuncios mediante Playwright. Para cada anuncio guarda
nombre, puesto, teléfono detectado en la descripción, fechas, descripción y
enlace en un archivo de texto.

## Instalación

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
playwright install chromium
```

## Uso

La URL de búsqueda de peón en Madrid es el valor por defecto:

```bash
python main.py --salida datos/trabajadores.txt
```

También se puede proporcionar otra búsqueda y limitar la paginación:

```bash
python main.py "https://www.milanuncios.com/ofertas-de-empleo-en-madrid/?dias=10&orden=date&s=peon&pagina=1" --max-paginas 5 --verbose
```

`--visible` muestra Chromium para depurar selectores. El scraper detiene la
paginación cuando una página no tiene tarjetas o no aporta enlaces nuevos.

Las pruebas que no necesitan navegador se ejecutan con:

```bash
python -m unittest discover -s tests -v
```

Los portales pueden cambiar su HTML, usar JavaScript, limitar peticiones o
prohibir automatización. Usa una frecuencia baja, revisa sus condiciones y
conserva solo los datos necesarios para tu finalidad personal.
