from scraper import extraer_trabajador, obtener_urls_anuncios


def main():

    urls = obtener_urls_anuncios()

    if not urls:
        print("No se encontraron anuncios.")
        return

    trabajador = extraer_trabajador(urls[0])
    print(trabajador)

if __name__ == "__main__":
    main()
