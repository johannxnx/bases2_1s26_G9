# parse_mundial.py
"""
Parsea los HTMLs descargados de un mundial y genera CSVs listos para base de datos.

CSVs generados en data/{anio}/:
    partidos.csv          → id_partido, anio_mundial, fecha, etapa, equipo_local,
                             goles_local, goles_visitante, equipo_visitante, url_partido
    goles.csv             → id_partido, anio_mundial, minuto, jugador, equipo,
                             es_penal, es_autogol
    posiciones_finales.csv→ anio_mundial, posicion, seleccion, etapa_alcanzada,
                             pts, pj, pg, pe, pp, gf, gc, dif
    grupos.csv            → anio_mundial, grupo, posicion, seleccion, pts, pj,
                             pg, pe, pp, gf, gc, dif, clasificado

Uso:
    python parse_mundial.py            # parsea 1930 (por defecto)
    python parse_mundial.py 1934
    python parse_mundial.py 1930 1934

Requiere que los HTMLs estén en html/{anio}/
"""

import sys
import os
import re
import csv
from bs4 import BeautifulSoup, Tag

HTML_BASE = "html"
DATA_BASE = "data"


# ─── Utilidades ───────────────────────────────────────────────────────────────

def leer_html(anio, nombre_archivo):
    """
    Lee y parsea un archivo HTML de html/{anio}/{nombre_archivo}.
    Retorna un objeto BeautifulSoup o None si el archivo no existe.
    """
    ruta = os.path.join(HTML_BASE, str(anio), nombre_archivo)
    if not os.path.exists(ruta):
        print(f"  [FALTA] {ruta}")
        return None

    with open(ruta, "r", encoding="utf-8") as f:
        return BeautifulSoup(f, "html.parser")


def contenido_principal(soup):
    """Retorna el <main> o el div principal de contenido."""
    return soup.find("main") or soup.find("div", class_="main-content")


def guardar_csv(ruta, filas, columnas):
    """
    Guarda una lista de dicts como CSV.
    Crea el directorio si no existe.
    """
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)
    print(f"  Guardado: {ruta}  ({len(filas)} filas)")


# ─── Parser de resultados ─────────────────────────────────────────────────────

def parsear_resultados(anio, soup):
    """
    Parsea {anio}_resultados.html.

    Estructura HTML:
      <h3>Fecha: <strong>13-Jul-1930</strong></h3>
      <div class="... margen-y3 ...">   ← bloque de un partido
        <strong>1</strong>.             ← número de partido
        <a href="...grupo_1.php">1ra Ronda, Grupo 1</a>   ← etapa
        div.game                        ← equipos y resultado
      </div>

    Retorna (lista_partidos, lista_goles).
    Cada partido: id_partido, anio_mundial, fecha, etapa, equipo_local,
                  goles_local, goles_visitante, equipo_visitante, url_partido
    Cada gol: id_partido, anio_mundial, minuto, jugador, equipo,
              es_penal, es_autogol
    """
    main = contenido_principal(soup)
    if not main:
        return [], []

    partidos = []
    goles    = []

    fecha_actual = ""

    # Iterar todos los elementos hijos directos del main (h3 = fecha, div = partido)
    for elem in main.descendants:
        if not isinstance(elem, Tag):
            continue

        # Capturar fecha desde <h3>
        if elem.name == "h3":
            strong = elem.find("strong")
            if strong:
                fecha_actual = strong.get_text(strip=True)
            continue

        # Capturar bloques de partido
        clases = " ".join(elem.get("class", []))
        if "margen-y3" not in clases or "overflow-x-auto" not in clases:
            continue
        # Evitar procesar un bloque que ya es hijo de otro procesado
        if elem.find_parent("div", class_=lambda c: c and "margen-y3" in c and "overflow-x-auto" in " ".join(c)):
            continue

        partido, goles_partido = _extraer_partido(elem, anio, fecha_actual)
        if partido:
            partidos.append(partido)
            goles.extend(goles_partido)

    return partidos, goles


def _extraer_partido(bloque, anio, fecha):
    """
    Extrae datos de un bloque HTML de partido.
    Retorna (dict_partido, lista_goles).
    """
    # ── Número de partido ──
    strong = bloque.find("strong")
    num_partido = strong.get_text(strip=True) if strong else "?"

    # ── Etapa (link al grupo o fase) ──
    etapa = ""
    for a in bloque.find_all("a"):
        href = a.get("href", "")
        if "mundiales/" in href and "grupo" in href.lower() or \
           "fase" in href.lower() or "semis" in href.lower() or "final" in href.lower():
            etapa = a.get_text(strip=True)
            break
    # Fallback: buscar texto de etapa en el bloque sin link
    if not etapa:
        divs_etapa = bloque.find_all("div", class_="wpx-90")
        if divs_etapa:
            etapa = divs_etapa[0].get_text(strip=True)

    # ── Equipos y resultado desde div.game ──
    game = bloque.find("div", class_="game")
    if not game:
        return None, []

    equipo_local    = _extraer_equipo_local(game)
    equipo_visitante = _extraer_equipo_visitante(game)
    resultado, url_partido = _extraer_resultado(game)

    if not resultado:
        return None, []

    partes = resultado.split("-")
    if len(partes) != 2:
        return None, []

    goles_local      = partes[0].strip()
    goles_visitante  = partes[1].strip()

    id_partido = f"{anio}_{num_partido}"

    partido = {
        "id_partido":        id_partido,
        "anio_mundial":      anio,
        "fecha":             fecha,
        "etapa":             etapa,
        "equipo_local":      equipo_local,
        "goles_local":       goles_local,
        "goles_visitante":   goles_visitante,
        "equipo_visitante":  equipo_visitante,
        "url_partido":       url_partido,
    }

    # ── Goles ──
    goles = _extraer_goles(bloque, id_partido, anio, equipo_local, equipo_visitante)

    return partido, goles


def _extraer_equipo_local(game):
    """
    El equipo local es siempre el primer <img> dentro del div.game.
    Usar el atributo alt es más confiable que buscar por clase CSS,
    ya que 'negri' puede aparecer en el visitante en partidos donde
    el orden visual se invierte (ej: final 1930 Argentina vs Uruguay).
    """
    imgs = game.find_all("img")
    if imgs:
        return imgs[0].get("alt", "")
    # Fallback: primer div con width 129px
    divs = game.find_all("div", style=lambda s: s and "129px" in s)
    return divs[0].get_text(strip=True) if divs else ""


def _extraer_equipo_visitante(game):
    """
    El equipo visitante es siempre el segundo <img> dentro del div.game.
    """
    imgs = game.find_all("img")
    if len(imgs) >= 2:
        return imgs[1].get("alt", "")
    # Fallback: segundo div con width 129px
    divs = game.find_all("div", style=lambda s: s and "129px" in s)
    return divs[1].get_text(strip=True) if len(divs) >= 2 else ""


def _extraer_resultado(game):
    """Resultado (ej: '4 - 1') y URL del partido desde el link dentro del game."""
    a = game.find("a", href=lambda h: h and "/partidos/" in h)
    if a:
        return a.get_text(strip=True), a["href"]
    return None, None


def _extraer_goles(bloque, id_partido, anio, equipo_local, equipo_visitante):
    """
    Los goles están en pares de divs left.w-50:
      - div con clase 'a-right' → gol del equipo local
      - div con clase 'a-left'  → gol del equipo visitante

    Cada div de gol contiene:
      - el minuto en texto (ej: "19'")
      - el nombre del jugador
      - opcionalmente "(pen)" o "(en contra)"
    """
    goles = []

    # Encontrar todos los pares de divs de goles
    # Están dentro del rd-100 que contiene el game
    rd = bloque.find("div", class_="rd-100")
    if not rd:
        return goles

    # Los divs de goles tienen clase w-50
    divs_gol = rd.find_all("div", class_=lambda c: c and "w-50" in c)

    i = 0
    while i < len(divs_gol) - 1:
        div_izq = divs_gol[i]
        div_der = divs_gol[i + 1]
        i += 2

        # Gol local (izquierda, a-right)
        if "a-right" in " ".join(div_izq.get("class", [])):
            gol = _parsear_div_gol(div_izq, id_partido, anio, equipo_local)
            if gol:
                goles.append(gol)

        # Gol visitante (derecha, a-left)
        if "a-left" in " ".join(div_der.get("class", [])):
            gol = _parsear_div_gol(div_der, id_partido, anio, equipo_visitante)
            if gol:
                goles.append(gol)

    return goles


def _parsear_div_gol(div, id_partido, anio, equipo):
    """
    Extrae minuto, jugador, es_penal, es_autogol de un div de gol.
    Retorna None si el div está vacío (sin gol).
    """
    texto = div.get_text(separator=" ", strip=True)

    # Si no hay imagen de balón ni texto relevante, es div vacío
    img = div.find("img")
    if not img and not texto:
        return None

    # Buscar minuto con regex: "19'" o "19' "
    minuto_match = re.search(r"(\d+)'", texto)
    if not minuto_match:
        return None

    minuto = minuto_match.group(1)

    # Detectar penal y autogol
    es_penal   = "(pen)"    in texto.lower()
    es_autogol = "en contra" in texto.lower()

    # Extraer nombre del jugador
    # El nombre está en un div.overflow-x-auto o div.a-right/a-left dentro del div gol
    nombre_div = div.find("div", class_=lambda c: c and "overflow-x-auto" in c)
    if nombre_div:
        # Limpiar el nombre: quitar "(pen)", "(en contra)", espacios extra
        nombre = nombre_div.get_text(strip=True)
        nombre = re.sub(r"\(pen\)", "", nombre, flags=re.IGNORECASE).strip()
        nombre = re.sub(r"\(en contra\)", "", nombre, flags=re.IGNORECASE).strip()
    else:
        # Fallback: tomar el texto completo menos el minuto
        nombre = re.sub(r"\d+'", "", texto)
        nombre = re.sub(r"\(pen\)", "", nombre, flags=re.IGNORECASE)
        nombre = re.sub(r"\(en contra\)", "", nombre, flags=re.IGNORECASE).strip()

    if not nombre:
        return None

    return {
        "id_partido":  id_partido,
        "anio_mundial": anio,
        "minuto":      minuto,
        "jugador":     nombre,
        "equipo":      equipo,
        "es_penal":    "Si" if es_penal else "No",
        "es_autogol":  "Si" if es_autogol else "No",
    }


# ─── Parser de posiciones finales ─────────────────────────────────────────────

def parsear_posiciones_finales(anio, soup):
    """
    Parsea {anio}_posiciones_finales.html.
    Las posiciones están en tablas <table> con columnas:
    Posición | Selección | Etapa | PTS | PJ | PG | PE | PP | GF | GC | Dif
    """
    main = contenido_principal(soup)
    if not main:
        return []

    filas = []
    for tabla in main.find_all("table"):
        for tr in tabla.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]

            # Saltar encabezado y filas vacías
            if not celdas or celdas[0] == "Posición" or not any(celdas):
                continue
            if len(celdas) < 11:
                continue

            filas.append({
                "anio_mundial":    anio,
                "posicion":        celdas[0].rstrip("."),
                "seleccion":       celdas[1],
                "etapa_alcanzada": celdas[2],
                "pts":             celdas[3],
                "pj":              celdas[4],
                "pg":              celdas[5],
                "pe":              celdas[6],
                "pp":              celdas[7],
                "gf":              celdas[8],
                "gc":              celdas[9],
                "dif":             celdas[10],
            })

    return filas


# ─── Parser de grupos ─────────────────────────────────────────────────────────

def parsear_grupo(anio, numero_grupo, soup):
    """
    Parsea {anio}_grupo_{n}.html.
    Extrae tabla de posiciones del grupo.
    Columnas: Posición | Selección | PTS | PJ | PG | PE | PP | GF | GC | Dif | Clasificado
    """
    main = contenido_principal(soup)
    if not main:
        return [], []

    filas_tabla = []
    partidos    = []
    goles       = []

    # ── Tabla de posiciones del grupo ──
    tabla = main.find("table")
    if tabla:
        for tr in tabla.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not celdas or celdas[0] == "Posición" or not any(celdas):
                continue
            if len(celdas) < 10:
                continue

            clasificado = celdas[10] if len(celdas) > 10 else ""

            filas_tabla.append({
                "anio_mundial":  anio,
                "grupo":         numero_grupo,
                "posicion":      celdas[0].rstrip("."),
                "seleccion":     celdas[1],
                "pts":           celdas[2],
                "pj":            celdas[3],
                "pg":            celdas[4],
                "pe":            celdas[5],
                "pp":            celdas[6],
                "gf":            celdas[7],
                "gc":            celdas[8],
                "dif":           celdas[9],
                "clasificado":   clasificado,
            })

    # ── Partidos del grupo (con goles) ──
    for bloque in main.find_all("div"):
        clases = " ".join(bloque.get("class", []))
        if "margen-y3" not in clases or "overflow-x-auto" not in clases:
            continue
        if bloque.find_parent("div", class_=lambda c: c and "margen-y3" in " ".join(c) and "overflow-x-auto" in " ".join(c)):
            continue

        # Extraer fecha del bloque (está dentro del propio bloque en los grupos)
        fecha = ""
        fecha_div = bloque.find("div", class_="wpx-100")
        if fecha_div:
            fecha = fecha_div.get_text(strip=True)

        strong = bloque.find("strong")
        num_partido = strong.get_text(strip=True) if strong else "?"
        id_partido  = f"{anio}_g{numero_grupo}_{num_partido}"

        game = bloque.find("div", class_="game")
        if not game:
            continue

        equipo_local     = _extraer_equipo_local(game)
        equipo_visitante = _extraer_equipo_visitante(game)
        resultado, url   = _extraer_resultado(game)

        if not resultado:
            continue

        partes = resultado.split("-")
        if len(partes) != 2:
            continue

        partidos.append({
            "id_partido":       id_partido,
            "anio_mundial":     anio,
            "grupo":            numero_grupo,
            "fecha":            fecha,
            "equipo_local":     equipo_local,
            "goles_local":      partes[0].strip(),
            "goles_visitante":  partes[1].strip(),
            "equipo_visitante": equipo_visitante,
            "url_partido":      url or "",
        })

        goles_partido = _extraer_goles(bloque, id_partido, anio, equipo_local, equipo_visitante)
        goles.extend(goles_partido)

    return filas_tabla, partidos, goles


# ─── Parser premios
def parsear_premios(anio, soup):
    main = contenido_principal(soup)
    if not main:
        return []

    premios = []

    bloques = main.find_all("div", class_=lambda c: c and "margen-y15" in c)

    for bloque in bloques:
        nombre_premio_tag = bloque.find("p", class_="negri")
        if not nombre_premio_tag:
            continue

        nombre_premio = nombre_premio_tag.get_text(strip=True)

        valor_tag = bloque.find("p", class_="margen-b0")
        if not valor_tag:
            continue

        # Caso: sin ganador
        if "-" in valor_tag.get_text():
            continue

        # Buscar jugador
        a = valor_tag.find("a")
        if not a:
            continue

        jugador = a.get_text(strip=True)

        # Buscar selección (en el alt del img)
        img = valor_tag.find("img")
        seleccion = img.get("alt") if img else ""

        premios.append({
            "anio_mundial": anio,
            "premio": nombre_premio,
            "jugador": jugador,
            "seleccion": seleccion
        })

    return premios


# parsear goles individuales
def parsear_goleadores(anio, soup):
    main = contenido_principal(soup)
    if not main:
        return []

    goleadores = []

    # Buscar tablas (la página de goleadores siempre usa tablas)
    for tabla in main.find_all("table"):
        for tr in tabla.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]

            # Saltar encabezados o filas inválidas
            if not celdas:
                continue

            # Detectar encabezados repetidos
            texto_fila = " ".join(celdas).lower()

            if (
                "jugador" in texto_fila and
                "goles" in texto_fila
            ):
                continue
            
            # Normalmente: Pos | Jugador | Selección | Goles
            if len(celdas) < 4:
                continue

            jugador   = celdas[1]
            seleccion = celdas[2]
            goles     = celdas[3]

            goleadores.append({
                "anio_mundial": anio,
                "jugador": jugador,
                "seleccion": seleccion,
                "goles": goles
            })

    return goleadores


# ─── Orquestador principal ────────────────────────────────────────────────────

def parsear_mundial(anio):
    """
    Parsea todos los HTMLs de un mundial y guarda los CSVs en data/{anio}/.
    """
    print(f"\n{'='*60}")
    print(f"  Parseando Mundial {anio}")
    print(f"{'='*60}\n")

    directorio_out = os.path.join(DATA_BASE, str(anio))
    os.makedirs(directorio_out, exist_ok=True)

    todos_partidos          = []
    todos_goles             = []
    todas_pos_finales       = []
    todas_pos_grupos        = []
    todos_partidos_grupos   = []
    todos_goles_grupos      = []

    # ── Resultados generales ──
    soup_res = leer_html(anio, f"{anio}_resultados.html")
    if soup_res:
        print("Parseando resultados...")
        partidos, goles = parsear_resultados(anio, soup_res)
        todos_partidos.extend(partidos)
        todos_goles.extend(goles)
        print(f"  {len(partidos)} partidos, {len(goles)} goles encontrados")
        
    # ── Premios ──
    soup_premios = leer_html(anio, f"{anio}_premios.html")
    if soup_premios:
        print("Parseando premios...")
        premios = parsear_premios(anio, soup_premios)
        print(f"  {len(premios)} premios encontrados")
    else:
        premios = []
        
    # ── Goleadores ──
    soup_goleadores = leer_html(anio, f"{anio}_goleadores.html")
    if soup_goleadores:
        print("Parseando goleadores...")
        goleadores = parsear_goleadores(anio, soup_goleadores)
        print(f"  {len(goleadores)} goleadores encontrados")
    else:
        goleadores = []

    # ── Posiciones finales ──
    soup_pos = leer_html(anio, f"{anio}_posiciones_finales.html")
    if soup_pos:
        print("Parseando posiciones finales...")
        filas = parsear_posiciones_finales(anio, soup_pos)
        todas_pos_finales.extend(filas)
        print(f"  {len(filas)} posiciones encontradas")

    # ── Grupos (se detectan automáticamente del 1 al 8) ──
    for n in range(1, 9):
        nombre = f"{anio}_grupo_{n}.html"
        soup_g = leer_html(anio, nombre)
        if soup_g:
            print(f"Parseando grupo {n}...")
            tabla, partidos_g, goles_g = parsear_grupo(anio, n, soup_g)
            todas_pos_grupos.extend(tabla)
            todos_partidos_grupos.extend(partidos_g)
            todos_goles_grupos.extend(goles_g)
            print(f"  {len(tabla)} posiciones, {len(partidos_g)} partidos, {len(goles_g)} goles")

    # ── Guardar CSVs ──
    print("\nGuardando CSVs...")

    if todos_partidos:
        guardar_csv(
            os.path.join(directorio_out, "partidos.csv"),
            todos_partidos,
            ["id_partido", "anio_mundial", "fecha", "etapa",
             "equipo_local", "goles_local", "goles_visitante",
             "equipo_visitante", "url_partido"]
        )

    if todos_goles:
        guardar_csv(
            os.path.join(directorio_out, "goles.csv"),
            todos_goles,
            ["id_partido", "anio_mundial", "minuto", "jugador",
             "equipo", "es_penal", "es_autogol"]
        )

    if todas_pos_finales:
        guardar_csv(
            os.path.join(directorio_out, "posiciones_finales.csv"),
            todas_pos_finales,
            ["anio_mundial", "posicion", "seleccion", "etapa_alcanzada",
             "pts", "pj", "pg", "pe", "pp", "gf", "gc", "dif"]
        )

    if todas_pos_grupos:
        guardar_csv(
            os.path.join(directorio_out, "grupos.csv"),
            todas_pos_grupos,
            ["anio_mundial", "grupo", "posicion", "seleccion",
             "pts", "pj", "pg", "pe", "pp", "gf", "gc", "dif", "clasificado"]
        )

    if todos_partidos_grupos:
        guardar_csv(
            os.path.join(directorio_out, "partidos_grupos.csv"),
            todos_partidos_grupos,
            ["id_partido", "anio_mundial", "grupo", "fecha",
             "equipo_local", "goles_local", "goles_visitante",
             "equipo_visitante", "url_partido"]
        )

    if todos_goles_grupos:
        guardar_csv(
            os.path.join(directorio_out, "goles_grupos.csv"),
            todos_goles_grupos,
            ["id_partido", "anio_mundial", "minuto", "jugador",
             "equipo", "es_penal", "es_autogol"]
        )
        
    if premios:
        guardar_csv(
            os.path.join(directorio_out, "premios.csv"),
            premios,
            ["anio_mundial", "premio", "jugador", "seleccion"]
        )
        
    if goleadores:
        guardar_csv(
            os.path.join(directorio_out, "goleadores.csv"),
            goleadores,
            ["anio_mundial", "jugador", "seleccion", "goles"]
        )

    print(f"\nCSVs guardados en: data/{anio}/")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        anios = [int(a) for a in sys.argv[1:]]
    else:
        anios = [1930]

    for anio in anios:
        parsear_mundial(anio)

    print("\n¡Parseo completado!")