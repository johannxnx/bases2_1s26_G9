"""
ParserJugadores.py
==================
Parsea todos los HTMLs de html/data_jugadores/ y genera dos CSVs en data/:

    jugadores_completo.csv
        jugador, seleccion_nacionalidad, altura, fecha_nac, posicion,
        num_camiseta, mundiales

    detalle_jugadorM.csv
        jugador, seleccion_nacionalidad, mundial, camiseta, posicion,
        jugo, jugo_titular, capitan, no_jugo, goles, prom_goles,
        tarjeta_amarilla, tarjeta_roja, pg, pe, pp, pos_final

Cada HTML corresponde a un jugador (ej: lionel_messi.html).
Los HTMLs están en html/data_jugadores/ (relativo a la raíz del proyecto).

Uso:
    python scripts/ParserJugadores.py
    python scripts/ParserJugadores.py lionel_messi.html  # solo ese archivo

Estructura HTML esperada (losmundialesdefutbol.com):
  - Ficha de jugador: tabla con Fecha de Nacimiento, Posición, Números de
    camiseta, Altura, Nombre completo, etc.
  - Selección Nacional: imagen con alt="Nombre País"
  - Detalle de Mundiales Jugados: tabla con columnas:
    Mundial | Camiseta | Posición | Jugó | Titular | Capitán | No Jugó |
    Goles | Prom.Gol | Amar. | Roja | PG | PE | PP | Pos.Final
"""

import sys
import os
import re
import csv
from bs4 import BeautifulSoup, Tag

# ─── Rutas ────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR   = os.path.dirname(_SCRIPT_DIR)

HTML_JUG_DIR = os.path.join(_BASE_DIR, "html", "data_jugadores")
DATA_DIR     = os.path.join(_BASE_DIR, "data")

COL_JUGADORES = [
    "jugador", "seleccion_nacionalidad", "altura", "fecha_nac",
    "posicion", "num_camiseta", "mundiales",
]

COL_DETALLE = [
    "jugador", "seleccion_nacionalidad", "mundial", "camiseta", "posicion",
    "jugo", "jugo_titular", "capitan", "no_jugo", "goles", "prom_goles",
    "tarjeta_amarilla", "tarjeta_roja", "pg", "pe", "pp", "pos_final",
]


# ─── Utilidades ───────────────────────────────────────────────────────────────

def _texto(tag):
    return tag.get_text(strip=True) if tag else ""


def _num(val):
    """Convierte a número entero o retorna vacío."""
    if val is None:
        return ""
    s = str(val).strip().replace(",", ".")
    m = re.search(r"-?\d+", s)
    return m.group(0) if m else ""


def _float_str(val):
    """Retorna el float como string o vacío."""
    if val is None:
        return ""
    s = str(val).strip()
    m = re.match(r"-?\d+[\.,]\d+", s)
    if m:
        return m.group(0).replace(",", ".")
    m2 = re.match(r"-?\d+", s)
    return m2.group(0) if m2 else ""


def _limpiar_nombre(nombre):
    """
    Limpia espacios extra del nombre del jugador.
    No invierte ni transforma el orden — se guarda tal como viene del HTML.
    """
    return " ".join(nombre.split()) if nombre else ""


# ─── Parser principal de un jugador ──────────────────────────────────────────

def parsear_jugador(ruta_html):
    """
    Parsea un HTML de jugador y retorna:
        (dict_jugador, lista_de_dicts_detalle)

    Si el HTML no tiene datos suficientes retorna (None, []).
    """
    with open(ruta_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    main = soup.find("main") or soup.find("div", class_="main-content")
    if not main:
        return None, []

    # ── Nombre del jugador ────────────────────────────────────────────────────
    # Viene en el <h2 class="t-enc-1"> dentro del primer bloque margen-y15
    h2_nombre = main.find("h2", class_="t-enc-1")
    nombre = _limpiar_nombre(_texto(h2_nombre)) if h2_nombre else ""
    if not nombre:
        # Fallback: título de la página
        h1 = main.find("h1")
        if h1:
            t = _texto(h1)
            # Eliminar el sufijo " en los Mundiales de Fútbol"
            nombre = re.sub(r"\s+en los Mundiales.*", "", t, flags=re.IGNORECASE).strip()

    if not nombre:
        return None, []

    # ── Ficha del jugador (tabla de datos personales) ─────────────────────────
    fecha_nac    = ""
    posicion     = ""
    num_camiseta = ""
    altura       = ""

    # La ficha está en la primera tabla dentro del bloque rd-100-70
    bloque_ficha = main.find("div", class_=lambda c: c and "rd-100-70" in c)
    if bloque_ficha:
        tabla_ficha = bloque_ficha.find("table")
        if tabla_ficha:
            for fila in tabla_ficha.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) < 2:
                    continue
                etiqueta = _texto(celdas[0]).lower()
                valor    = _texto(celdas[1])

                if "fecha de nacimiento" in etiqueta:
                    fecha_nac = valor
                elif "posición" in etiqueta or "posicion" in etiqueta:
                    posicion = valor
                elif "camiseta" in etiqueta:
                    # "19 y 10"  →  "19, 10"   |   "13"  →  "13"
                    num_camiseta = re.sub(r"\s+y\s+", ", ", valor)
                elif "altura" in etiqueta:
                    # "1.70 m / 5' 7\""  →  "1.70 m"
                    altura = valor.split("/")[0].strip()

    # ── Selección Nacional ────────────────────────────────────────────────────
    seleccion = ""
    bloque_sel = main.find("div", class_=lambda c: c and "rd-100-30" in c)
    if bloque_sel:
        img_band = bloque_sel.find("img", src=lambda s: s and "banderas" in str(s))
        if img_band:
            seleccion = img_band.get("alt", "").strip()

    # ── Lista de mundiales (para el campo "mundiales" de jugadores_completo) ─
    mundiales_lista = []

    # ── Tabla de detalle por mundial ──────────────────────────────────────────
    detalles = []

    # Buscar el bloque "Detalle de Mundiales Jugados"
    bloque_detalle = None
    for h3 in main.find_all(["h3", "h2"]):
        if "detalle de mundiales" in _texto(h3).lower():
            bloque_detalle = h3.find_parent("div")
            break

    if bloque_detalle:
        tabla_det = bloque_detalle.find("table")
        if tabla_det:
            filas = tabla_det.find_all("tr")
            for fila in filas:
                celdas = fila.find_all("td")

                # Saltar encabezados (t-enc-4, t-enc-5) y filas de separador/total
                clases_fila = " ".join(fila.get("class", []))
                if "t-enc" in clases_fila:
                    continue
                # Filas de separador (div linea-2) o totales (sin enlace a mundial)
                if len(celdas) < 15:
                    continue

                # Verificar que la primera celda tiene un enlace a un mundial
                a_mundial = celdas[0].find("a", href=lambda h: h and "mundiales" in str(h))
                if not a_mundial:
                    continue

                anio_mundial = _texto(a_mundial)
                if not anio_mundial.isdigit():
                    continue

                mundiales_lista.append(anio_mundial)

                # Camiseta: texto después de la imagen de bandera en la celda [1]
                celda_camiseta = celdas[1]
                texto_camiseta = _texto(celda_camiseta)
                # Quitar el nombre del país si quedó pegado (alt de la imagen)
                img_c = celda_camiseta.find("img")
                pais_c = img_c.get("alt", "").strip() if img_c else ""
                if pais_c:
                    texto_camiseta = texto_camiseta.replace(pais_c, "").strip()
                camiseta_det = texto_camiseta.strip()

                # Posición en este mundial (celda [2])
                posicion_det = _texto(celdas[2])

                # Columnas numéricas [3..14]
                # [3]=Jugó [4]=Titular [5]=Capitán [6]=NoJugó
                # [7]=Goles [8]=PromGol [9]=Amar [10]=Roja
                # [11]=PG [12]=PE [13]=PP [14]=PosFinal
                def _c(idx):
                    t = _texto(celdas[idx]) if idx < len(celdas) else ""
                    return t if t not in ("", "-") else "0"

                jugo          = _c(3)
                jugo_titular  = _c(4)
                capitan       = _c(5)
                no_jugo       = _c(6)
                goles         = _c(7)
                prom_goles    = _c(8)
                tarj_am       = _c(9)
                tarj_roja     = _c(10)
                pg            = _c(11)
                pe            = _c(12)
                pp            = _c(13)
                pos_final_det = _c(14)

                detalles.append({
                    "jugador":             nombre,
                    "seleccion_nacionalidad": seleccion,
                    "mundial":             anio_mundial,
                    "camiseta":            camiseta_det,
                    "posicion":            posicion_det,
                    "jugo":                jugo,
                    "jugo_titular":        jugo_titular,
                    "capitan":             capitan,
                    "no_jugo":             no_jugo,
                    "goles":               goles,
                    "prom_goles":          prom_goles,
                    "tarjeta_amarilla":    tarj_am,
                    "tarjeta_roja":        tarj_roja,
                    "pg":                  pg,
                    "pe":                  pe,
                    "pp":                  pp,
                    "pos_final":           pos_final_det,
                })

    jugador_dict = {
        "jugador":               nombre,
        "seleccion_nacionalidad": seleccion,
        "altura":                altura,
        "fecha_nac":             fecha_nac,
        "posicion":              posicion,
        "num_camiseta":          num_camiseta,
        "mundiales":             ", ".join(sorted(set(mundiales_lista))),
    }

    return jugador_dict, detalles


# ─── Guardar CSV ─────────────────────────────────────────────────────────────

def guardar_csv(ruta, filas, columnas, modo="w"):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, modo, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        if modo == "w":
            writer.writeheader()
        writer.writerows(filas)


# ─── Orquestador ─────────────────────────────────────────────────────────────

def parsear_todos(archivos=None):
    """
    Parsea todos los HTMLs de html/data_jugadores/ (o solo los indicados).
    """
    if not os.path.exists(HTML_JUG_DIR):
        print(f"[ERROR] No se encontró el directorio: {HTML_JUG_DIR}")
        sys.exit(1)

    if archivos:
        lista = archivos
    else:
        lista = sorted(
            f for f in os.listdir(HTML_JUG_DIR)
            if f.endswith(".html")
        )

    if not lista:
        print("[ADVERTENCIA] No se encontraron archivos .html")
        return

    print(f"Archivos a parsear: {len(lista)}")

    ruta_jug = os.path.join(DATA_DIR, "jugadores_completo.csv")
    ruta_det = os.path.join(DATA_DIR, "detalle_jugadorM.csv")

    # Inicializar archivos con encabezado
    guardar_csv(ruta_jug, [], COL_JUGADORES, "w")
    guardar_csv(ruta_det, [], COL_DETALLE,   "w")

    total_jugadores = 0
    total_detalles  = 0
    errores         = 0

    for nombre_archivo in lista:
        ruta = os.path.join(HTML_JUG_DIR, nombre_archivo)
        if not os.path.exists(ruta):
            print(f"  [FALTA] {nombre_archivo}")
            errores += 1
            continue

        try:
            jug, detalles = parsear_jugador(ruta)
        except Exception as e:
            print(f"  [ERROR] {nombre_archivo}: {e}")
            errores += 1
            continue

        if not jug:
            print(f"  [VACÍO] {nombre_archivo} — no se extrajo nombre")
            errores += 1
            continue

        # Escribir en modo append
        guardar_csv(ruta_jug, [jug],    COL_JUGADORES, "a")
        guardar_csv(ruta_det, detalles, COL_DETALLE,   "a")

        total_jugadores += 1
        total_detalles  += len(detalles)

    print(f"\n{'='*55}")
    print(f"  Parseo completado")
    print(f"  Jugadores procesados : {total_jugadores}")
    print(f"  Filas de detalle     : {total_detalles}")
    print(f"  Errores              : {errores}")
    print(f"  jugadores_completo.csv → {ruta_jug}")
    print(f"  detalle_jugadorM.csv   → {ruta_det}")
    print(f"{'='*55}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parsear_todos(sys.argv[1:])
    else:
        parsear_todos()