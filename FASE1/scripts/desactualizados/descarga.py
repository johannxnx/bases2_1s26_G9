from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import random
import os

HTML_DIR = "html"

# ─── Lista completa de selecciones (extraída del HTML inspeccionado) ──────────
# Si el sitio agrega nuevas selecciones en el futuro, agregalas aquí.

URLS_SELECCIONES = [
    "https://www.losmundialesdefutbol.com/jugadores_indice/alemania.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/alemania_oriental.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/angola.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/arabia_saudita.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/argelia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/argentina.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/australia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/austria.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/belgica.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/bolivia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/bosnia_herzegovina.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/brasil.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/bulgaria.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/cabo_verde.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/camerun.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/canada.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/catar.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/chile.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/china.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/colombia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/corea_del_norte.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/corea_del_sur.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/costa_de_marfil.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/costa_rica.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/croacia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/cuba.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/curazao.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/dinamarca.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/ecuador.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/egipto.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/el_salvador.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/emiratos_arabes.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/escocia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/eslovaquia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/eslovenia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/espana.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/estados_unidos.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/francia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/gales.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/ghana.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/grecia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/haiti.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/honduras.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/hungria.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/indonesia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/inglaterra.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/iran.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/iraq.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/irlanda.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/irlanda_del_norte.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/islandia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/israel.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/italia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/jamaica.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/japon.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/jordania.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/kuwait.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/marruecos.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/mexico.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/nigeria.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/noruega.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/nueva_zelanda.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/holanda.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/panama.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/paraguay.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/peru.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/polonia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/portugal.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/rd_congo.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/republica_checa.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/rumania.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/rusia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/senegal.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/serbia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/sudafrica.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/suecia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/suiza.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/togo.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/trinidad_y_tobago.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/tunez.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/turquia.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/ucrania.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/uruguay.php",
    "https://www.losmundialesdefutbol.com/jugadores_indice/uzbekistan.php"
]

# ─── Selenium con Firefox ─────────────────────────────────────────────────────

def crear_driver():
    """Crea y retorna un driver de Firefox."""
    options = Options()
    # Modo headless = Firefox corre en segundo plano sin abrir ventana visible.
    # Si quieres VER el navegador trabajar, comenta la línea siguiente:
    # options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    return driver


def descargar_paginas():
    os.makedirs(HTML_DIR, exist_ok=True)
    total = len(URLS_SELECCIONES)

    # Filtrar las que ya existen (permite reanudar si se interrumpe)
    pendientes = []
    for url in URLS_SELECCIONES:
        nombre_html = url.rstrip("/").split("/")[-1].replace(".php", ".html")
        if os.path.exists(os.path.join(HTML_DIR, nombre_html)):
            print(f"  Ya existe, saltando: {nombre_html}")
        else:
            pendientes.append(url)

    print(f"\nPendientes: {len(pendientes)} de {total} selecciones\n")

    if not pendientes:
        print("Todo ya descargado.")
        return

    print("Abriendo Firefox...")
    driver = crear_driver()

    try:
        for i, url in enumerate(pendientes, 1):
            nombre_html = url.rstrip("/").split("/")[-1].replace(".php", ".html")
            ruta_destino = os.path.join(HTML_DIR, nombre_html)

            print(f"[{i:>2}/{len(pendientes)}] Navegando a: {nombre_html}")

            try:
                driver.get(url)

                # Esperar a que la página cargue completamente
                # (Selenium espera el DOM, pero damos 3s extra por si acaso)
                time.sleep(3)

                # Obtener el HTML tal como lo renderizó el navegador
                html = driver.page_source
                chars = len(html)
                print(f"           Tamaño: {chars} chars")

                if chars < 500:
                    print(f"           ADVERTENCIA: página muy corta, puede ser error.")

                with open(ruta_destino, "w", encoding="utf-8") as f:
                    f.write(html)

            except Exception as e:
                print(f"           ERROR en {url}: {e}")

            # Delay aleatorio entre páginas (excepto la última)
            if i < len(pendientes):
                espera = random.randint(10, 20)
                print(f"           Esperando {espera}s...\n")
                time.sleep(espera)

    finally:
        # Siempre cerrar el navegador al terminar o si hay error
        driver.quit()
        print("\nFirefox cerrado.")

    print("\nDescarga finalizada. Archivos en carpeta 'html/'")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Total selecciones en lista: {len(URLS_SELECCIONES)}")
    print("Firefox se abrirá automáticamente. No lo cierres.\n")
    descargar_paginas()