"""
parserFinal.py
==============
Parsea todos los HTMLs de html/{anio}/ y genera CSVs crudos en data/{anio}/.

CSVs generados por año en data/{anio}/:
    mundial.csv           → info general del mundial
    grupos.csv            → grupos con sus selecciones
    partidos.csv          → todos los partidos (fase grupos + fase final)
    goles.csv             → goles por partido
    goleadores.csv        → tabla de goleadores del mundial
    posiciones_grupo.csv  → tabla de posiciones por grupo
    posiciones_finales.csv→ clasificación final del mundial
    premios.csv           → premios individuales (Balón de Oro, etc.)
    equipo_ideal.csv      → equipo ideal del mundial
    tarjetas.csv          → tarjetas amarillas y rojas por jugador
    planteles.csv         → jugadores por selección

Uso:
    python parserFinal.py              # parsea todos los años en html/
    python parserFinal.py 1930         # solo 1930
    python parserFinal.py 1930 1934    # varios años

Estructura esperada:
    html/{anio}/{anio}_mundial.html
    html/{anio}/{anio}_resultados.html
    html/{anio}/{anio}_grupo_1.html   (o grupo_a.html, etc.)
    html/{anio}/{anio}_goleadores.html
    html/{anio}/{anio}_posiciones_finales.html
    html/{anio}/{anio}_premios.html
    html/{anio}/{anio}_tarjetas.html   (si existe)
    html/{anio}/{anio}_planteles.html  (si existe)
"""

import sys
import os
import re
import csv
from bs4 import BeautifulSoup, Tag

# ─── Rutas base ───────────────────────────────────────────────────────────────
# El script vive en scripts/, así que html/ y data/ están un nivel arriba
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR   = os.path.dirname(_SCRIPT_DIR)

HTML_BASE = os.path.join(_BASE_DIR, "html")
DATA_BASE = os.path.join(_BASE_DIR, "data")


# ─── Utilidades generales ─────────────────────────────────────────────────────

def leer_html(anio, nombre_archivo):
    """
    Lee html/{anio}/{nombre_archivo} y retorna un BeautifulSoup.
    Retorna None si el archivo no existe.
    """
    ruta = os.path.join(HTML_BASE, str(anio), nombre_archivo)
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "html.parser")


def guardar_csv(ruta, filas, columnas):
    """
    Guarda una lista de dicts como CSV con las columnas indicadas.
    Crea el directorio si no existe.
    Si filas está vacío, igual crea el archivo con solo el encabezado
    para que normalizar.py pueda verificar su existencia.
    """
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        writer.writeheader()
        if filas:
            writer.writerows(filas)
    print(f"    Guardado: {os.path.relpath(ruta)}  ({len(filas)} filas)")


def contenido_principal(soup):
    """Retorna el <main> o el div de contenido principal."""
    return soup.find("main") or soup.find("div", class_="main-content") or soup.find("body")


def texto_limpio(tag):
    """Texto de un tag sin espacios extra."""
    return tag.get_text(strip=True) if tag else ""


# ─── 1. MUNDIAL ──────────────────────────────────────────────────────────────

def parsear_mundial(anio, soup):
    """
    Parsea {anio}_mundial.html.
    Extrae: organizador, campeón, num_selecciones, num_partidos, goles, promedio_gol.
    """
    d = {
        "anio": anio,
        "organizador": "",
        "campeon": "",
        "num_selecciones": "",
        "num_partidos": "",
        "goles": "",
        "promedio_gol": "",
    }

    texto_total = soup.get_text(" ", strip=True)

    m = re.search(r"Organizador:\s*([^\-]+)", texto_total)
    if m:
        d["organizador"] = m.group(1).strip()

    m = re.search(r"Selecciones[:\s]+(\d+)", texto_total)
    if m:
        d["num_selecciones"] = m.group(1)

    m = re.search(r"Partidos[:\s]+(\d+)", texto_total)
    if m:
        d["num_partidos"] = m.group(1)

    m = re.search(r"Goles[:\s]+(\d+)", texto_total)
    if m:
        d["goles"] = m.group(1)

    m = re.search(r"Promedio de Gol[:\s]+([\d.]+)", texto_total)
    if m:
        d["promedio_gol"] = m.group(1)

    # Campeón: primer enlace a /selecciones/ en el cuerpo
    for a in soup.find_all("a", href=lambda h: h and "/selecciones/" in str(h)):
        t = texto_limpio(a)
        if t:
            d["campeon"] = t
            break

    return [d]


# ─── 2. GRUPOS ───────────────────────────────────────────────────────────────

def _detectar_grupos(anio):
    """
    Detecta qué archivos de grupos existen para el año dado.
    Soporta: grupo_1..grupo_8, grupo_a..grupo_j, y mezclas.
    Retorna lista de (identificador_grupo, nombre_archivo).
    Ej: [("1", "1930_grupo_1.html"), ("2", "1930_grupo_2.html")]
    """
    encontrados = []
    dir_html = os.path.join(HTML_BASE, str(anio))

    # Buscar numéricos primero (1..8)
    for n in range(1, 9):
        nombre = f"{anio}_grupo_{n}.html"
        if os.path.exists(os.path.join(dir_html, nombre)):
            encontrados.append((str(n), nombre))

    # Luego letras (a..j)
    for letra in "abcdefghij":
        nombre = f"{anio}_grupo_{letra}.html"
        if os.path.exists(os.path.join(dir_html, nombre)):
            encontrados.append((letra.upper(), nombre))

    return encontrados


def parsear_grupos(anio):
    """
    Parsea todos los {anio}_grupo_X.html del año.
    Retorna (lista_grupos, lista_posiciones_grupo, lista_partidos_grupo, lista_goles_grupo).

    grupos.csv:            anio, id_grupo, selecciones
    posiciones_grupo.csv:  anio, id_grupo, seleccion, pts, pj, pg, pe, pp, gf, gc, diferencia, clasificado
    partidos.csv:          (se agrega a los partidos de resultados)
    goles.csv:             (se agrega a los goles de resultados)
    """
    grupos_lista     = []
    posiciones_lista = []
    partidos_lista   = []
    goles_lista      = []

    archivos = _detectar_grupos(anio)
    if not archivos:
        print(f"    [INFO] No se encontraron archivos de grupos para {anio}")
        return grupos_lista, posiciones_lista, partidos_lista, goles_lista

    for id_grupo, nombre_archivo in archivos:
        soup = leer_html(anio, nombre_archivo)
        if not soup:
            continue

        print(f"    Parseando grupo {id_grupo}...")

        # ── Selecciones del grupo ──
        selecciones = []
        for img in soup.find_all("img", src=lambda s: s and "banderas" in str(s) and "_sml" in str(s)):
            alt = img.get("alt", "").strip()
            if alt and alt not in selecciones:
                selecciones.append(alt)

        grupos_lista.append({
            "anio":       anio,
            "id_grupo":   id_grupo,
            "selecciones": ", ".join(selecciones),
        })

        # ── Tabla de posiciones del grupo ──
        for tabla in soup.find_all("table"):
            primera = tabla.find("tr")
            if not primera:
                continue
            encabezados_th = [td.get_text(strip=True).upper()
                              for td in primera.find_all(["td", "th"])]
            # Verificar que es tabla de posiciones
            if "PTS" not in encabezados_th and "PT" not in encabezados_th:
                continue

            for fila in tabla.find_all("tr")[1:]:
                celdas = fila.find_all(["td", "th"])
                if len(celdas) < 5:
                    continue
                textos = [c.get_text(strip=True) for c in celdas]
                img_b  = fila.find("img", src=lambda s: s and "banderas" in str(s))
                pais   = img_b.get("alt", "").strip() if img_b else textos[1] if len(textos) > 1 else ""

                if not pais:
                    continue

                posiciones_lista.append({
                    "anio":        anio,
                    "id_grupo":    id_grupo,
                    "seleccion":   pais,
                    "pts":         textos[2]  if len(textos) > 2  else "",
                    "pj":          textos[3]  if len(textos) > 3  else "",
                    "pg":          textos[4]  if len(textos) > 4  else "",
                    "pe":          textos[5]  if len(textos) > 5  else "",
                    "pp":          textos[6]  if len(textos) > 6  else "",
                    "gf":          textos[7]  if len(textos) > 7  else "",
                    "gc":          textos[8]  if len(textos) > 8  else "",
                    "diferencia":  textos[9]  if len(textos) > 9  else "",
                    "clasificado": textos[10] if len(textos) > 10 else "",
                })

        # ── Partidos del grupo (con sus goles) ──
        divs_partido = soup.find_all(
            "div",
            class_=lambda c: c and "margen-y3" in c and ("pad-y5" in c or "overflow-x-auto" in c)
        )
        for div in divs_partido:
            # Evitar divs anidados
            padre = div.find_parent(
                "div",
                class_=lambda c: c and "margen-y3" in c
            )
            if padre and padre != div:
                continue

            imgs_band = [i for i in div.find_all("img")
                         if "banderas" in i.get("src", "") and "_min" in i.get("src", "")]
            if len(imgs_band) < 2:
                continue

            local      = imgs_band[0].get("alt", "").strip()
            visitante  = imgs_band[1].get("alt", "").strip()
            num_tag    = div.find("strong")
            num_par    = num_tag.get_text(strip=True) if num_tag else ""

            # Fecha dentro del bloque
            texto_div = div.get_text(" ", strip=True)
            m_fecha   = re.search(r"(\d{1,2}-\w+-\d{4})", texto_div)
            fecha     = m_fecha.group(1) if m_fecha else ""

            # Marcador
            a_marc = div.find("a", href=lambda h: h and "/partidos/" in str(h))
            if not a_marc:
                continue
            marcador = a_marc.get_text(strip=True)
            m_res    = re.match(r"(\d+)\s*[-–]\s*(\d+)", marcador)
            if not m_res:
                continue
            goles_l = m_res.group(1)
            goles_v = m_res.group(2)

            id_partido_str = f"{anio}_g{id_grupo}_{num_par}"

            partidos_lista.append({
                "anio":            anio,
                "id_partido_str":  id_partido_str,
                "num_partido":     num_par,
                "fuente":          f"grupo_{id_grupo}",
                "fecha":           fecha,
                "etapa":           f"Grupo {id_grupo}",
                "local":           local,
                "visitante":       visitante,
                "goles_local":     goles_l,
                "goles_visitante": goles_v,
                "tiempo_extra":    "NO",
                "penales":         "NO",
                "penales_local":   "",
                "penales_visitante": "",
            })

            # Goles del partido
            rd = div.find("div", class_=lambda c: c and "rd-100" in c)
            if rd:
                goles_extraidos = _extraer_goles_de_rd(
                    rd, id_partido_str, anio, local, visitante
                )
                goles_lista.extend(goles_extraidos)

    return grupos_lista, posiciones_lista, partidos_lista, goles_lista


# ─── 3. RESULTADOS (fase eliminatoria + resultados generales) ─────────────────

def parsear_resultados(anio, soup):
    """
    Parsea {anio}_resultados.html y {anio}_fase_final.html.
    Retorna (lista_partidos, lista_goles).
    Los partidos de grupos YA vienen de parsear_grupos(), aquí solo viene
    la fase final + partidos de mundiales sin grupos (1934, etc.).
    """
    partidos = []
    goles    = []

    main = contenido_principal(soup)
    if not main:
        return partidos, goles

    fecha_actual = ""

    for elem in main.descendants:
        if not isinstance(elem, Tag):
            continue

        # Capturar fecha desde <h3> o <h2>
        if elem.name in ("h3", "h2"):
            strong = elem.find("strong")
            if strong:
                t = strong.get_text(strip=True)
                m = re.search(r"\d{1,2}-\w+-\d{4}", t)
                if m:
                    fecha_actual = m.group(0)
            continue

        # Bloques de partido
        clases = set(elem.get("class", []))
        es_bloque = (
            ("margen-y3" in clases and "pad-y5" in clases) or
            ("margen-y3" in clases and "overflow-x-auto" in clases)
        )
        if not es_bloque:
            continue

        # Evitar procesar divs anidados dentro de otro bloque partido
        padre = elem.find_parent(
            "div",
            class_=lambda c: c and "margen-y3" in c
        )
        if padre and padre != elem:
            continue

        imgs_band = [i for i in elem.find_all("img")
                     if "banderas" in i.get("src", "") and "_min" in i.get("src", "")]
        if len(imgs_band) < 2:
            continue

        local     = imgs_band[0].get("alt", "").strip()
        visitante = imgs_band[1].get("alt", "").strip()
        num_tag   = elem.find("strong")
        num_par   = num_tag.get_text(strip=True) if num_tag else ""

        # Etapa (enlace al grupo o fase)
        etapa = ""
        for a in elem.find_all("a"):
            href = a.get("href", "")
            if any(k in href for k in ["grupo", "fase", "final", "semis", "cuartos"]):
                etapa = a.get_text(strip=True)
                break
        if not etapa:
            # Texto libre que indique etapa
            texto_elem = elem.get_text(" ", strip=True)
            for kw in ["Final", "Semifinal", "Cuartos", "Octavos", "Tercero"]:
                if kw.lower() in texto_elem.lower():
                    etapa = kw
                    break

        # Marcador
        a_marc = elem.find("a", href=lambda h: h and "/partidos/" in str(h))
        if not a_marc:
            continue
        marcador = a_marc.get_text(strip=True)
        m_res    = re.match(r"(\d+)\s*[-–]\s*(\d+)", marcador)
        if not m_res:
            continue
        goles_l = m_res.group(1)
        goles_v = m_res.group(2)

        # Detectar tiempo extra y penales
        texto_completo = elem.get_text(" ", strip=True).lower()
        tiempo_extra   = "SI" if "tiempo extra"  in texto_completo else "NO"
        penales        = "SI" if "por penales"   in texto_completo else "NO"

        pen_l = pen_v = ""
        if penales == "SI":
            m_pen = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*por penales", texto_completo)
            if m_pen:
                pen_l = m_pen.group(1)
                pen_v = m_pen.group(2)

        # Fecha interna al bloque (para partidos de grupos en resultados)
        if not fecha_actual:
            m_fi = re.search(r"\d{1,2}-\w+-\d{4}", elem.get_text(" "))
            if m_fi:
                fecha_actual = m_fi.group(0)

        id_partido_str = f"{anio}_r_{num_par}"

        partidos.append({
            "anio":             anio,
            "id_partido_str":   id_partido_str,
            "num_partido":      num_par,
            "fuente":           "resultados",
            "fecha":            fecha_actual,
            "etapa":            etapa,
            "local":            local,
            "visitante":        visitante,
            "goles_local":      goles_l,
            "goles_visitante":  goles_v,
            "tiempo_extra":     tiempo_extra,
            "penales":          penales,
            "penales_local":    pen_l,
            "penales_visitante": pen_v,
        })

        rd = elem.find("div", class_=lambda c: c and "rd-100" in c)
        if rd:
            goles_extraidos = _extraer_goles_de_rd(
                rd, id_partido_str, anio, local, visitante
            )
            goles.extend(goles_extraidos)

    return partidos, goles


# ─── 4. EXTRACCIÓN DE GOLES (helper compartido) ───────────────────────────────

def _extraer_goles_de_rd(rd, id_partido_str, anio, local, visitante):
    """
    Extrae goles de un div rd-100.
    Izquierda (pad-r2 o a-right) → equipo local.
    Derecha  (pad-l2 o a-left)  → equipo visitante.
    """
    goles = []

    def _parsear_bloque(bloque, equipo):
        # Minuto
        texto = bloque.get_text(" ", strip=True)
        m_min = re.search(r"(\d+\+?\d*)'", texto)
        if not m_min:
            return
        minuto = m_min.group(1)

        # Jugador — busca el div de overflow-x-auto dentro del bloque
        div_jug = bloque.find("div", class_=lambda c: c and "overflow-x-auto" in c)
        if div_jug:
            texto_jug = div_jug.get_text(" ", strip=True)
        else:
            texto_jug = texto

        es_penal   = "(pen)" in texto_jug.lower()
        es_autogol = "en contra" in texto_jug.lower()

        jugador = re.sub(r"\(pen\)",         "", texto_jug, flags=re.IGNORECASE)
        jugador = re.sub(r"\(en contra\)",   "", jugador,   flags=re.IGNORECASE)
        jugador = re.sub(r"\d+\+?\d*'",      "", jugador).strip()

        if not jugador:
            return

        goles.append({
            "anio":           anio,
            "id_partido_str": id_partido_str,
            "equipo":         equipo,
            "jugador":        jugador,
            "minuto":         minuto,
            "es_penal":       "SI" if es_penal   else "NO",
            "es_autogol":     "SI" if es_autogol else "NO",
        })

    # Goles locales: div con pad-r2 y w-50, o a-right y w-50
    for b in rd.find_all("div", class_=lambda c: c and "w-50" in c and
                          ("pad-r2" in c or "a-right" in c)):
        _parsear_bloque(b, local)

    # Goles visitantes: div con pad-l2 y w-50, o a-left y w-50
    for b in rd.find_all("div", class_=lambda c: c and "w-50" in c and
                          ("pad-l2" in c or "a-left" in c)):
        _parsear_bloque(b, visitante)

    return goles


# ─── 5. GOLEADORES ───────────────────────────────────────────────────────────

def parsear_goleadores(anio, soup):
    """
    Parsea {anio}_goleadores.html.
    Retorna lista de dicts: anio, jugador, seleccion, goles, partidos, promedio.
    """
    goleadores = []
    main = contenido_principal(soup)
    if not main:
        return goleadores

    for tabla in main.find_all("table"):
        for fila in tabla.find_all("tr"):
            celdas  = fila.find_all(["td", "th"])
            if len(celdas) < 3:
                continue
            textos  = [c.get_text(strip=True) for c in celdas]

            # Saltar encabezados
            if textos[0].lower() in ("pos", "posición", "posicion", "#", "jugador"):
                continue
            texto_fila = " ".join(textos).lower()
            if "jugador" in texto_fila and "goles" in texto_fila:
                continue

            # Jugador desde enlace
            enlace  = fila.find("a", href=lambda h: h and "/jugadores/" in str(h))
            jugador = enlace.get_text(strip=True) if enlace else ""

            # País desde imagen de bandera
            img_b   = fila.find("img", src=lambda s: s and "banderas" in str(s))
            pais    = img_b.get("alt", "").strip() if img_b else ""

            if not jugador:
                continue

            # Números: el primero suele ser goles, el segundo partidos
            numeros = []
            floats  = []
            for t in textos:
                t2 = t.replace("*", "").strip()
                if t2.isdigit():
                    numeros.append(t2)
                elif re.match(r"^\d+\.\d+$", t2):
                    floats.append(t2)

            goleadores.append({
                "anio":      anio,
                "jugador":   jugador,
                "seleccion": pais,
                "goles":     numeros[0] if numeros else "",
                "partidos":  numeros[1] if len(numeros) > 1 else "",
                "promedio":  floats[0]  if floats else "",
            })

    return goleadores


# ─── 6. POSICIONES FINALES ────────────────────────────────────────────────────

def parsear_posiciones_finales(anio, soup):
    """
    Parsea {anio}_posiciones_finales.html.
    Retorna lista de dicts: anio, posicion, seleccion.
    """
    posiciones = []
    main = contenido_principal(soup)
    if not main:
        return posiciones

    for tabla in main.find_all("table"):
        for fila in tabla.find_all("tr"):
            celdas = fila.find_all(["td", "th"])
            if len(celdas) < 2:
                continue
            textos = [c.get_text(strip=True) for c in celdas]

            # Saltar encabezado
            if textos[0].lower() in ("posición", "posicion", "pos", "#"):
                continue

            pos_str = textos[0].replace(".", "").strip()
            if not pos_str.isdigit():
                continue

            img_b = fila.find("img", src=lambda s: s and "banderas" in str(s))
            pais  = img_b.get("alt", "").strip() if img_b else (textos[1] if len(textos) > 1 else "")

            if not pais:
                continue

            posiciones.append({
                "anio":     anio,
                "posicion": pos_str,
                "seleccion": pais,
            })

    return posiciones


# ─── 7. PREMIOS ──────────────────────────────────────────────────────────────

# Nombres de premios individuales conocidos
PREMIOS_INDIVIDUALES = {
    "Balón de Oro", "Balón de Plata", "Balón de Bronce",
    "Botín de Oro", "Botín de Plata", "Botín de Bronce",
    "Guante de Oro", "Mejor Jugador Joven", "FIFA Fair Play",
    "Premio Fair Play", "Mejor Portero",
}

# Prefijos de posición que aparecen como NavigableString al inicio de cada
# div rd-100-25 dentro del bloque Equipo Ideal. Ej: "Arquero:"
POSICIONES_EQUIPO_IDEAL = [
    "Arquero", "Defensores", "Mediocampistas",
    "Volantes", "Delanteros", "Entrenador",
]


def parsear_premios(anio, soup):
    """
    Parsea {anio}_premios.html.
    Retorna (lista_premios, lista_equipo_ideal).

    Estructura real del HTML:
      Cada bloque de premio es un <div rd-100-30> (o similar) con:
        <p class="negri">Nombre del Premio</p>
        <p class="margen-b0"><img alt="Pais"/>  <a>Jugador o Selección</a></p>
      Si el ganador es "-" la segunda <p> tiene solo el texto "-".

      El bloque "Equipo Ideal" contiene divs rd-100-25 donde el primer
      NavigableString (hijo directo) indica la posición: "Arquero:", "Defensores:", etc.
      Luego hay pares <img alt="Pais"/> <a>Jugador</a> para cada jugador.

    premios.csv:      anio, tipo_premio, jugador, seleccion
    equipo_ideal.csv: anio, posicion, jugador, seleccion
    """
    premios      = []
    equipo_ideal = []
    main = contenido_principal(soup)
    if not main:
        return premios, equipo_ideal

    for p in main.find_all("p", class_=lambda c: c and "negri" in c):
        nombre_premio = p.get_text(strip=True)

        # ── Premios individuales ──────────────────────────────────────────────
        if nombre_premio in PREMIOS_INDIVIDUALES:
            p_sig = p.find_next_sibling("p")
            if not p_sig:
                continue
            # Si el texto es solo "-" no hay ganador
            if p_sig.get_text(strip=True) == "-":
                continue
            enlace  = p_sig.find("a")
            img_b   = p_sig.find("img", src=lambda s: s and "banderas" in str(s))
            jugador = enlace.get_text(strip=True) if enlace else ""
            pais    = img_b.get("alt", "").strip() if img_b else ""
            # FIFA Fair Play puede ser una selección (el enlace apunta a /selecciones/)
            # Lo registramos igual; el nombre del jugador quedará vacío solo si no hay enlace
            if jugador and jugador != "-":
                premios.append({
                    "anio":        anio,
                    "tipo_premio": nombre_premio,
                    "jugador":     jugador,
                    "seleccion":   pais,
                })

        # ── Equipo Ideal ──────────────────────────────────────────────────────
        elif "Equipo Ideal" in nombre_premio:
            # Subir hasta el contenedor que tiene los divs rd-100-25
            # La jerarquía es: <div w-100> > <div> > <p negri>Equipo Ideal</p>
            #                                       > <div margen-l5> > <div rd-100-25>...
            contenedor_w100 = p.find_parent(
                "div", class_=lambda c: c and "w-100" in c
            ) or p.find_parent("div")

            if not contenedor_w100:
                continue

            for div in contenedor_w100.find_all(
                "div", class_=lambda c: c and "rd-100-25" in c
            ):
                # La posición es el primer NavigableString directo del div
                # Ej: "Arquero:", "Defensores:", "Mediocampistas:", etc.
                posicion_actual = ""
                from bs4 import NavigableString as _NS
                for hijo in div.children:
                    if isinstance(hijo, _NS):
                        texto_hijo = str(hijo).strip().rstrip(":")
                        for pos in POSICIONES_EQUIPO_IDEAL:
                            if texto_hijo.lower().startswith(pos.lower()):
                                posicion_actual = pos
                                break
                    if posicion_actual:
                        break

                # Jugadores: pares img + a dentro del div
                for a in div.find_all("a", href=lambda h: h and "/jugadores/" in str(h)):
                    # La imagen de bandera está justo antes del <a> (hermano anterior)
                    img_b = None
                    for prev in a.previous_siblings:
                        if hasattr(prev, "name") and prev.name == "img":
                            img_b = prev
                            break
                    jugador = a.get_text(strip=True)
                    pais    = img_b.get("alt", "").strip() if img_b else ""
                    if jugador:
                        equipo_ideal.append({
                            "anio":      anio,
                            "posicion":  posicion_actual,
                            "jugador":   jugador,
                            "seleccion": pais,
                        })

    return premios, equipo_ideal


# ─── 8. TARJETAS ─────────────────────────────────────────────────────────────

def parsear_tarjetas(anio, soup):
    """
    Parsea {anio}_tarjetas.html.
    Retorna lista de dicts: anio, jugador, seleccion, amarillas, rojas.

    Estructura real del HTML:
      <table>
        <tr class="t-enc-2">   ← encabezado con "Tarjetas Amarillas", "Tarjetas Rojas"
        <tr class="a-top">     ← fila de datos
          <td></td>                         (vacía, posición)
          <td colspan="2"><img/><a/></td>   (bandera + jugador)
          <td>  <div>N <div class="am"/></div> </td>   (amarillas, puede ser "-")
          <td>  <div>N <div class="rd"/></div> </td>   (rojas, puede ser "-")
          <td>(RD / 2TA)</td>
          <td>partidos</td>
          <td>Selección</td>
        </tr>
      </table>

    El número de amarillas/rojas se extrae del texto de la celda correspondiente.
    La celda puede contener "-" si no tiene tarjetas de ese tipo.
    Las posiciones son: [0]=vacío, [1]=jugador+bandera (colspan=2), [2]=amarillas,
                        [3]=rojas, [4]=(RD/2TA), [5]=partidos, [6]=selección.
    """
    tarjetas = []
    main = contenido_principal(soup)
    if not main:
        return tarjetas

    for tabla in main.find_all("table"):
        primera = tabla.find("tr")
        if not primera:
            continue
        enc_texto = primera.get_text(" ", strip=True).lower()
        # Verificar que es tabla de tarjetas por texto del encabezado
        if not any(k in enc_texto for k in ["amarilla", "roja", "tarjeta"]):
            continue

        for fila in tabla.find_all("tr")[1:]:
            # Jugador desde enlace /jugadores/
            enlace  = fila.find("a", href=lambda h: h and "/jugadores/" in str(h))
            jugador = enlace.get_text(strip=True) if enlace else ""
            if not jugador:
                continue

            # País desde imagen de bandera
            img_b = fila.find("img", src=lambda s: s and "banderas" in str(s))
            pais  = img_b.get("alt", "").strip() if img_b else ""

            # Amarillas y rojas: buscar por clase del div indicador
            # <div class="am"> → amarilla    <div class="rd"> → roja
            celdas = fila.find_all("td")

            amarillas = "0"
            rojas     = "0"

            for celda in celdas:
                # Si la celda tiene el div indicador de amarilla
                if celda.find("div", class_="am"):
                    m = re.search(r"(\d+)", celda.get_text(" ", strip=True))
                    amarillas = m.group(1) if m else "0"
                # Si la celda tiene el div indicador de roja
                elif celda.find("div", class_="rd"):
                    m = re.search(r"(\d+)", celda.get_text(" ", strip=True))
                    rojas = m.group(1) if m else "0"

            # Fallback: si no hay divs am/rd, intentar por posición de celda
            # (estructura más antigua: [1]=jugador, [2]=amarillas, [3]=rojas)
            if amarillas == "0" and rojas == "0" and len(celdas) >= 4:
                t_am = celdas[2].get_text(strip=True) if len(celdas) > 2 else "-"
                t_rd = celdas[3].get_text(strip=True) if len(celdas) > 3 else "-"
                if t_am.isdigit():
                    amarillas = t_am
                if t_rd.isdigit():
                    rojas = t_rd

            tarjetas.append({
                "anio":      anio,
                "jugador":   jugador,
                "seleccion": pais,
                "amarillas": amarillas,
                "rojas":     rojas,
            })

    return tarjetas


# ─── 9. PLANTELES ────────────────────────────────────────────────────────────

def parsear_planteles(anio, soup):
    """
    Parsea {anio}_planteles.html.

    IMPORTANTE: este HTML es un índice de links a páginas individuales
    por selección (ej: 1982_argentina_jugadores.php). No contiene los
    jugadores directamente. Lo que sí podemos extraer es:
      - La lista de selecciones que participaron (desde los alt de las banderas)

    Retorna lista de dicts: anio, seleccion
    (dorsal y posicion quedan vacíos — están en páginas separadas no descargadas)

    Si en el futuro se descargan los HTMLs individuales de planteles,
    este parser deberá extenderse para leerlos desde html/{anio}/planteles/.
    """
    planteles = []
    main = contenido_principal(soup)
    if not main:
        return planteles

    selecciones_vistas = set()

    # Extraer selecciones desde los links con imágenes de bandera
    for a in main.find_all("a", href=lambda h: h and "jugadores.php" in str(h)):
        img_b = a.find("img", src=lambda s: s and "banderas" in str(s))
        if img_b:
            pais = img_b.get("alt", "").strip()
        else:
            pais = a.get_text(strip=True)

        if pais and pais not in selecciones_vistas:
            selecciones_vistas.add(pais)
            planteles.append({
                "anio":      anio,
                "seleccion": pais,
                "dorsal":    "",
                "jugador":   "",
                "posicion":  "",
            })

    return planteles


# ─── ORQUESTADOR PRINCIPAL ────────────────────────────────────────────────────

def parsear_anio(anio):
    """
    Parsea todos los HTMLs de html/{anio}/ y guarda CSVs en data/{anio}/.
    """
    print(f"\n{'='*60}")
    print(f"  Parseando Mundial {anio}")
    print(f"{'='*60}")

    directorio_out = os.path.join(DATA_BASE, str(anio))
    os.makedirs(directorio_out, exist_ok=True)

    # ── 1. Mundial ──
    soup = leer_html(anio, f"{anio}_mundial.html")
    if soup:
        filas = parsear_mundial(anio, soup)
    else:
        print(f"  [FALTA] {anio}_mundial.html")
        filas = []
    guardar_csv(
        os.path.join(directorio_out, "mundial.csv"),
        filas,
        ["anio", "organizador", "campeon", "num_selecciones",
         "num_partidos", "goles", "promedio_gol"]
    )

    # ── 2. Grupos ──
    grupos, posiciones_grupo, partidos_grupo, goles_grupo = parsear_grupos(anio)
    guardar_csv(
        os.path.join(directorio_out, "grupos.csv"),
        grupos,
        ["anio", "id_grupo", "selecciones"]
    )
    guardar_csv(
        os.path.join(directorio_out, "posiciones_grupo.csv"),
        posiciones_grupo,
        ["anio", "id_grupo", "seleccion", "pts", "pj", "pg", "pe",
         "pp", "gf", "gc", "diferencia", "clasificado"]
    )

    # ── 3. Resultados generales ──
    todos_partidos = list(partidos_grupo)
    todos_goles    = list(goles_grupo)

    soup_res = leer_html(anio, f"{anio}_resultados.html")
    if soup_res:
        partidos_res, goles_res = parsear_resultados(anio, soup_res)
        todos_partidos.extend(partidos_res)
        todos_goles.extend(goles_res)
    else:
        print(f"  [FALTA] {anio}_resultados.html")

    # Fase final (si existe como archivo separado)
    soup_ff = leer_html(anio, f"{anio}_fase_final.html")
    if soup_ff:
        partidos_ff, goles_ff = parsear_resultados(anio, soup_ff)
        # Evitar duplicados por id_partido_str
        ids_ya = {p["id_partido_str"] for p in todos_partidos}
        for p in partidos_ff:
            if p["id_partido_str"] not in ids_ya:
                todos_partidos.append(p)
                ids_ya.add(p["id_partido_str"])
        todos_goles.extend(goles_ff)

    # Re-numerar partidos de forma limpia por año (1, 2, 3, ...)
    # para que num_partido sea consistente dentro del año
    for i, p in enumerate(todos_partidos, 1):
        p["num_partido_seq"] = str(i)

    guardar_csv(
        os.path.join(directorio_out, "partidos.csv"),
        todos_partidos,
        ["anio", "id_partido_str", "num_partido", "num_partido_seq",
         "fuente", "fecha", "etapa", "local", "visitante",
         "goles_local", "goles_visitante",
         "tiempo_extra", "penales", "penales_local", "penales_visitante"]
    )
    guardar_csv(
        os.path.join(directorio_out, "goles.csv"),
        todos_goles,
        ["anio", "id_partido_str", "equipo", "jugador",
         "minuto", "es_penal", "es_autogol"]
    )

    # ── 4. Goleadores ──
    soup_g = leer_html(anio, f"{anio}_goleadores.html")
    filas_g = parsear_goleadores(anio, soup_g) if soup_g else []
    guardar_csv(
        os.path.join(directorio_out, "goleadores.csv"),
        filas_g,
        ["anio", "jugador", "seleccion", "goles", "partidos", "promedio"]
    )

    # ── 5. Posiciones finales ──
    soup_pf = leer_html(anio, f"{anio}_posiciones_finales.html")
    filas_pf = parsear_posiciones_finales(anio, soup_pf) if soup_pf else []
    guardar_csv(
        os.path.join(directorio_out, "posiciones_finales.csv"),
        filas_pf,
        ["anio", "posicion", "seleccion"]
    )

    # ── 6. Premios y Equipo Ideal ──
    soup_pr  = leer_html(anio, f"{anio}_premios.html")
    if soup_pr:
        premios, equipo_ideal = parsear_premios(anio, soup_pr)
    else:
        premios, equipo_ideal = [], []
    guardar_csv(
        os.path.join(directorio_out, "premios.csv"),
        premios,
        ["anio", "tipo_premio", "jugador", "seleccion"]
    )
    guardar_csv(
        os.path.join(directorio_out, "equipo_ideal.csv"),
        equipo_ideal,
        ["anio", "posicion", "jugador", "seleccion"]
    )

    # ── 7. Tarjetas ──
    soup_t  = leer_html(anio, f"{anio}_tarjetas.html")
    filas_t = parsear_tarjetas(anio, soup_t) if soup_t else []
    guardar_csv(
        os.path.join(directorio_out, "tarjetas.csv"),
        filas_t,
        ["anio", "jugador", "seleccion", "amarillas", "rojas"]
    )

    # ── 8. Planteles ──
    soup_pl  = leer_html(anio, f"{anio}_planteles.html")
    filas_pl = parsear_planteles(anio, soup_pl) if soup_pl else []
    guardar_csv(
        os.path.join(directorio_out, "planteles.csv"),
        filas_pl,
        ["anio", "seleccion", "dorsal", "jugador", "posicion"]
    )

    print(f"\n  Completado: data/{anio}/")


def detectar_anios():
    """Detecta automáticamente todos los años disponibles en html/."""
    if not os.path.exists(HTML_BASE):
        return []
    return sorted([
        int(c) for c in os.listdir(HTML_BASE)
        if os.path.isdir(os.path.join(HTML_BASE, c)) and c.isdigit()
    ])


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        anios = [int(a) for a in sys.argv[1:]]
    else:
        anios = detectar_anios()
        if not anios:
            print("No se encontraron años en html/. Verifica la ruta.")
            sys.exit(1)

    print(f"Años a parsear: {anios}")
    for anio in anios:
        parsear_anio(anio)

    print(f"\n{'='*60}")
    print("  Parseo completado.")
    print(f"  CSVs guardados en: {DATA_BASE}/")
    print(f"{'='*60}")