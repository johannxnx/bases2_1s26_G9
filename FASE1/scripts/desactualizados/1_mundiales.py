# descarga_mundial.py
"""
Descarga todas las páginas HTML de un mundial dado usando Firefox (Selenium).
El sitio bloquea requests directos con 403, por eso se usa el navegador real.

Dependencias:
    pip install selenium beautifulsoup4 pandas
    brew install geckodriver

Uso:
    python descarga_mundial.py               # descarga el mundial 1930 (por defecto)
    python descarga_mundial.py 1934          # descarga el mundial 1934
    python descarga_mundial.py 1930 1934 1938  # descarga varios mundiales

Cómo funciona:
    1. Accede a /{año}_mundial.php y extrae todos los links del mismo mundial.
    2. Guarda cada HTML en html/{año}/nombre_pagina.html
    3. Espera entre 10 y 20 segundos entre cada descarga para no saturar el servidor.
    4. Si una página ya existe, la salta (permite reanudar descargas interrumpidas).
"""

import sys
import os
import time
import random
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

BASE_URL = "https://www.losmundialesdefutbol.com/"


# ─── Utilidades ───────────────────────────────────────────────────────────────

def crear_driver(headless=False):
    """
    Crea y retorna un driver de Firefox.
    headless=True  → Firefox corre en segundo plano (sin ventana visible).
    headless=False → Puedes ver el navegador trabajar en tiempo real.
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    return driver


def nombre_archivo(url):
    """
    Convierte una URL en un nombre de archivo .html.
    Ejemplo: .../mundiales/1930_grupo_1.php → 1930_grupo_1.html
    """
    base = url.rstrip("/").split("/")[-1]   # 1930_grupo_1.php
    return base.replace(".php", ".html")    # 1930_grupo_1.html


# ─── Paso 1: descubrir todos los links del mundial ───────────────────────────

def descubrir_links_mundial(driver, anio):
    """
    Navega a /{anio}_mundial.php y extrae todos los links que corresponden
    a páginas del mismo mundial (resultados, grupos, goleadores, etc.).

    Retorna una lista de URLs absolutas únicas, sin duplicados.
    """
    url_principal = urljoin(BASE_URL, f"mundiales/{anio}_mundial.php")
    print(f"  Accediendo a página principal: {url_principal}")

    driver.get(url_principal)
    time.sleep(3)   # esperar a que cargue el DOM

    soup = BeautifulSoup(driver.page_source, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        url_abs = urljoin(BASE_URL, href)

        # Quedarse solo con páginas de este mundial en /mundiales/
        # Excluir la página principal del mundial (ya la tenemos)
        # y excluir links a partidos individuales (/partidos/)
        if (
            f"/mundiales/{anio}_" in url_abs
            and "/partidos/" not in url_abs
        ):
            links.append(url_abs)

    # Agregar siempre la página principal también
    links.insert(0, url_principal)

    # Eliminar duplicados conservando orden
    links = list(dict.fromkeys(links))

    print(f"  Links encontrados para {anio}: {len(links)}")
    for l in links:
        print(f"    {l}")

    return links


# ─── Paso 2: descargar los HTMLs ─────────────────────────────────────────────

def descargar_mundial(anio):
    """
    Descarga todas las páginas de un mundial y las guarda en html/{anio}/.
    """
    directorio = os.path.join("html", str(anio))
    os.makedirs(directorio, exist_ok=True)

    print(f"  Mundial {anio}")

    print("\nAbriendo Firefox...")
    driver = crear_driver(headless=False)   # cambiar a True para modo invisible

    try:
        # ── Descubrir links ──
        links = descubrir_links_mundial(driver, anio)

        # ── Filtrar los que ya existen ──
        pendientes = []
        for url in links:
            nombre = nombre_archivo(url)
            ruta = os.path.join(directorio, nombre)
            if os.path.exists(ruta):
                print(f"  Ya existe, saltando: {nombre}")
            else:
                pendientes.append(url)

        total = len(pendientes)
        print(f"\nPendientes: {total} páginas\n")

        if total == 0:
            print("  Todo ya descargado.")
            return

        # ── Descargar ──
        for i, url in enumerate(pendientes, 1):
            nombre = nombre_archivo(url)
            ruta   = os.path.join(directorio, nombre)

            print(f"[{i:>2}/{total}] Descargando: {nombre}")

            try:
                driver.get(url)
                time.sleep(3)   # esperar carga completa

                html  = driver.page_source
                chars = len(html)
                print(f"           Tamaño: {chars:,} chars")

                if chars < 500:
                    print("           ADVERTENCIA: respuesta muy corta, puede ser error.")

                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)

            except Exception as e:
                print(f"           ERROR: {e}")

            # Delay entre 10 y 20 segundos (excepto después del último)
            if i < total:
                espera = random.randint(40, 60)
                print(f"           Esperando {espera}s...\n")
                time.sleep(espera)

    finally:
        driver.quit()
        print("\nFirefox cerrado.")

    print(f"\nMundial {anio} descargado en: html/{anio}/")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Leer años desde argumentos de línea de comandos, o usar 1930 por defecto
    if len(sys.argv) > 1:
        anios = [int(a) for a in sys.argv[1:]]
    else:
        anios = [1930]

    print(f"Mundiales a descargar: {anios}")
    print("Firefox se abrirá automáticamente. No lo cierres mientras corre.\n")

    for anio in anios:
        descargar_mundial(anio)

    print("\n¡Descarga completada!")
    print("Siguiente paso: ejecutar  python parse_mundial.py")