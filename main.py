from scraper import extraer_trabajador, obtener_urls_anuncios


def main():

    urls = obtener_urls_anuncios()

    if not urls:
        print("No se encontraron anuncios.")
        return

    for url in urls:
        print(f"Procesando URL: {url}")
        trabajador = extraer_trabajador(url)
        print(trabajador)
        print("-" * 40)

if __name__ == "__main__":
    main()
