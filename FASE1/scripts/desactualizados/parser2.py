"""
parser2.py
==========
Parsea todos los HTMLs descargados por 1_mundiales.py y genera CSVs.

Estructura esperada:
    html/{anio}/{anio}_mundial.html
    html/{anio}/{anio}_resultados.html
    html/{anio}/{anio}_grupo_a.html ... grupo_h.html
    html/{anio}/{anio}_goleadores.html
    html/{anio}/{anio}_posiciones_finales.html
    html/{anio}/{anio}_premios.html
    html/{anio}/{anio}_tarjetas.html

CSVs generados en data/:
    mundiales.csv, partidos.csv, grupos.csv,
    posiciones_grupo.csv, goles_partido.csv,
    goleadores.csv, posiciones_finales.csv,
    premios.csv, tarjetas.csv

Uso:
    python parser2.py           # parsea todos los años en html/
    python parser2.py 2022      # solo 2022
    python parser2.py 2022 2018 # varios años
"""

import os, sys, csv, re, unicodedata
from bs4 import BeautifulSoup

HTML_DIR = "html"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZACIÓN DE CARACTERES
# ─────────────────────────────────────────────────────────────────────────────

def normalizar_texto(texto):
    """
    Normaliza texto eliminando acentos, tildes y caracteres especiales.
    Preserva ñ y mantiene caracteres alfanuméricos.
    
    Ejemplo: "José Martínez" → "Jose Martinez"
    Ejemplo: "Peña" → "Pena"
    """
    if not texto:
        return texto
    
    texto = str(texto).strip()
    
    # Mapeo especial para ñ y Ñ (preservar)
    # Se procesa primero para no perderla en NFD
    texto_proc = texto
    
    # Convertir a forma NFD (descompuesta) para separar base de acentos
    texto_nfd = unicodedata.normalize('NFD', texto_proc)
    
    # Remover marcas diacríticas (acentos, etc.)
    # Pero preservar caracteres base como ñ
    resultado = ''.join(
        c for c in texto_nfd 
        if unicodedata.category(c) != 'Mn'  # Mn = Marca diacrítica
    )
    
    # Convertir de vuelta a forma NFC (compuesta) para consistencia
    resultado = unicodedata.normalize('NFC', resultado)
    
    return resultado

def normalizar_nombre(nombre):
    """
    Normaliza un nombre de persona.
    - Elimina/normaliza acentos y tildes
    - Convierte a título (Primera letra mayúscula)
    - Limpia espacios extras
    """
    if not nombre:
        return ""
    
    nombre = normalizar_texto(nombre).strip()
    # Convertir cada palabra a título
    return " ".join(word.capitalize() for word in nombre.split())


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

def leer_html(anio, nombre):
    ruta = os.path.join(HTML_DIR, str(anio), f"{nombre}.html")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "html.parser")

def guardar_csv(nombre, campos, filas):
    if not filas:
        return 0
    ruta = os.path.join(DATA_DIR, f"{nombre}.csv")
    modo = "a" if os.path.exists(ruta) else "w"
    with open(ruta, modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if modo == "w":
            w.writeheader()
        w.writerows(filas)
    return len(filas)

def cargar_csv_crudo(nombre, carpeta=DATA_DIR):
    """
    Carga un CSV crudo (ya con columnas separadas).
    
    Esto permite que si los datos ya vienen separados por columnas
    (ej: de una fuente externa), se pueden cargar directamente sin 
    necesidad de parsear HTML.
    
    Retorna lista de diccionarios con datos del CSV.
    """
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    if not os.path.exists(ruta):
        return None
    
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        print(f"  [ERROR cargando {nombre}.csv] {e}")
        return None

def num_o_none(texto):
    t = str(texto).replace(".","").strip()
    try:    return int(t)
    except: return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. MUNDIAL  →  mundiales.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_mundial(anio):
    soup = leer_html(anio, f"{anio}_mundial")
    if not soup:
        print(f"  [NO ENCONTRADO] {anio}_mundial.html"); return []

    d = {"anio": anio, "organizador": "", "campeon": "",
         "num_selecciones": None, "num_partidos": None,
         "goles": None, "promedio_gol": None}

    # Info general está en un bloque de texto con guiones
    tag_org = soup.find(string=lambda t: t and "Organizador:" in t)
    if tag_org:
        texto = tag_org.find_parent().get_text(" ", strip=True)
        m = re.search(r"Organizador:\s*([^\-]+)",   texto)
        if m: d["organizador"]     = m.group(1).strip()
        m = re.search(r"Selecciones:\s*(\d+)",      texto)
        if m: d["num_selecciones"] = int(m.group(1))
        m = re.search(r"Partidos:\s*(\d+)",         texto)
        if m: d["num_partidos"]    = int(m.group(1))
        m = re.search(r"Goles:\s*(\d+)",            texto)
        if m: d["goles"]           = int(m.group(1))
        m = re.search(r"Promedio de Gol:\s*([\d.]+)", texto)
        if m: d["promedio_gol"]    = float(m.group(1))

    # Campeón: primer enlace a /selecciones/ en el contenido principal
    for a in soup.find_all("a", href=lambda h: h and "/selecciones/" in str(h)):
        texto = a.get_text(strip=True)
        if texto:
            d["campeon"] = texto; break

    campos = ["anio","organizador","campeon","num_selecciones",
              "num_partidos","goles","promedio_gol"]
    n = guardar_csv("mundiales", campos, [d])
    print(f"  [mundiales]          {anio}: {n} fila")
    return [d]


# ─────────────────────────────────────────────────────────────────────────────
# 2. PARTIDOS  →  partidos.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_resultados(anio):
    soup = leer_html(anio, f"{anio}_resultados")
    if not soup:
        print(f"  [NO ENCONTRADO] {anio}_resultados.html"); return []

    partidos     = []
    fecha_actual = None
    body         = soup.find("body")

    for elem in body.descendants:
        if not hasattr(elem, "name") or not elem.name:
            continue

        # Fecha en H3
        if elem.name == "h3":
            t = elem.get_text(strip=True)
            m = re.search(r"(\d{1,2}-\w+-\d{4})", t)
            if m: fecha_actual = m.group(1)
            continue

        # Partido: div con clase 'margen-y3' y 'pad-y5' y banderas
        clases = elem.get("class", [])
        if elem.name == "div" and "margen-y3" in clases and "pad-y5" in clases:
            imgs_band = [i for i in elem.find_all("img")
                         if "banderas" in i.get("src","") and "_min" in i.get("src","")]
            if len(imgs_band) < 2:
                continue

            local     = imgs_band[0].get("alt","").strip()
            visitante = imgs_band[1].get("alt","").strip()

            num_tag     = elem.find("strong")
            num_partido = num_o_none(num_tag.get_text()) if num_tag else None

            etapa_a = elem.find("a", href=lambda h: h and
                                ("grupo" in str(h) or "fase_final" in str(h)))
            etapa   = etapa_a.get_text(strip=True) if etapa_a else ""

            marcador_a = elem.find("a", href=lambda h: h and "/partidos/" in str(h))
            marcador   = marcador_a.get_text(strip=True) if marcador_a else ""
            m_res      = re.match(r"(\d+)\s*-\s*(\d+)", marcador)
            goles_l    = int(m_res.group(1)) if m_res else None
            goles_v    = int(m_res.group(2)) if m_res else None

            texto_full = elem.get_text(" ", strip=True)
            tiempo_extra = "SI" if "tiempo extra"  in texto_full.lower() else "NO"
            penales      = "SI" if "por penales"   in texto_full.lower() else "NO"

            pen_l = pen_v = None
            if penales == "SI":
                m_pen = re.search(r"(\d+)\s*-\s*(\d+)\s*por penales", texto_full)
                if m_pen:
                    pen_l = int(m_pen.group(1))
                    pen_v = int(m_pen.group(2))

            partidos.append({
                "anio": anio, "num_partido": num_partido,
                "fecha": fecha_actual, "etapa": etapa,
                "local": local, "visitante": visitante,
                "goles_local": goles_l, "goles_visitante": goles_v,
                "tiempo_extra": tiempo_extra, "penales": penales,
                "penales_local": pen_l, "penales_visitante": pen_v,
            })

    campos = ["anio","num_partido","fecha","etapa","local","visitante",
              "goles_local","goles_visitante","tiempo_extra","penales",
              "penales_local","penales_visitante"]
    n = guardar_csv("partidos", campos, partidos)
    print(f"  [partidos]           {anio}: {n} partidos")
    return partidos


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: extraer goles de un div rd-100
# Estructura: izquierda = goles local (pad-r2), derecha = goles visitante (pad-l2)
# ─────────────────────────────────────────────────────────────────────────────

def extraer_goles_de_rd100(rd, anio, grupo, num_partido, fecha, local, visitante):
    goles = []

    def parsear_bloque(bloque, equipo):
        div_min = bloque.find("div", class_=lambda c: c and "margen-r5" in c)
        if not div_min:
            return
        texto_min = div_min.get_text(" ", strip=True)
        m = re.search(r"(\d+\+?\d*)'?", texto_min)
        if not m:
            return
        minuto = m.group(1)
        div_jug = bloque.find("div", class_=lambda c: c and "overflow-x-auto" in c)
        if not div_jug:
            return
        texto_jug = div_jug.get_text(" ", strip=True)
        es_pen    = "(pen)" in texto_jug.lower()
        jugador   = re.sub(r"\(pen\)", "", texto_jug, flags=re.IGNORECASE).strip()
        if jugador:
            goles.append({
                "anio": anio, "grupo": grupo,
                "num_partido": num_partido, "fecha": fecha,
                "local": local, "visitante": visitante,
                "equipo": equipo,
                "minuto": minuto, 
                "jugador": normalizar_nombre(jugador),  # Normaliza tildes/ñs
                "es_penal": "SI" if es_pen else "NO",
            })

    for b in rd.find_all("div", class_=lambda c: c and "pad-r2" in c and "w-50" in c):
        parsear_bloque(b, local)
    for b in rd.find_all("div", class_=lambda c: c and "pad-l2" in c and "w-50" in c):
        parsear_bloque(b, visitante)

    return goles

def parsear_grupos(anio):
    todos_grupos     = []
    todas_posiciones = []
    todos_goles      = []

    for letra in "abcdefghij":
        soup = leer_html(anio, f"{anio}_grupo_{letra}")
        if not soup:
            break

        nombre_grupo = f"Grupo {letra.upper()}"

        # ── Selecciones del grupo (banderas _sml) ─────────────────────────
        selecciones_grupo = []
        for img in soup.find_all("img", src=lambda s: s and "_sml" in str(s)):
            alt = img.get("alt","").strip()
            if alt and alt not in selecciones_grupo:
                selecciones_grupo.append(alt)

        todos_grupos.append({
            "anio": anio, "grupo": nombre_grupo,
            "selecciones": ", ".join(selecciones_grupo),
        })

        # ── Tabla de posiciones ───────────────────────────────────────────
        for tabla in soup.find_all("table"):
            primera_fila = tabla.find("tr")
            if not primera_fila:
                continue
            encabezados = [td.get_text(strip=True) for td in primera_fila.find_all("td")]
            if "PTS" not in encabezados:
                continue
            for fila in tabla.find_all("tr")[1:]:
                celdas = fila.find_all("td")
                if len(celdas) < 5:
                    continue
                textos = [c.get_text(strip=True) for c in celdas]
                img    = fila.find("img", src=lambda s: s and "banderas" in s)
                pais   = img.get("alt","").strip() if img else ""
                if not pais or not textos[0]:
                    continue
                todas_posiciones.append({
                    "anio": anio, "grupo": nombre_grupo, "pais": pais,
                    "pts":        num_o_none(textos[2]),
                    "pj":         num_o_none(textos[3]),
                    "pg":         num_o_none(textos[4]),
                    "pe":         num_o_none(textos[5]),
                    "pp":         num_o_none(textos[6]),
                    "gf":         num_o_none(textos[7]),
                    "gc":         num_o_none(textos[8]),
                    "diferencia": num_o_none(textos[9]) if len(textos) > 9 else None,
                    "clasificado": textos[10].strip()   if len(textos) > 10 else "",
                })

        # ── Partidos y goles del grupo ─────────────────────────────────────
        # Los partidos usan div con clases margen-y3 y pad-y5
        divs_partido = soup.find_all("div", class_=lambda c: c and "margen-y3" in c and "pad-y5" in c)

        for div in divs_partido:
            strong      = div.find("strong")
            num_partido = num_o_none(strong.get_text()) if strong else None

            imgs = [i for i in div.find_all("img")
                    if "banderas" in i.get("src","") and "_min" in i.get("src","")]
            if len(imgs) < 2:
                continue
            local     = imgs[0].get("alt","").strip()
            visitante = imgs[1].get("alt","").strip()

            texto_div = div.get_text(" ", strip=True)
            m_fecha   = re.search(r"(\d{1,2}-\w+-\d{4})", texto_div)
            fecha     = m_fecha.group(1) if m_fecha else ""

            rd = div.find("div", class_=lambda c: c and "rd-100" in c)
            if rd:
                goles = extraer_goles_de_rd100(
                    rd, anio, nombre_grupo, num_partido, fecha, local, visitante
                )
                todos_goles.extend(goles)

    campos_g  = ["anio","grupo","selecciones"]
    campos_p  = ["anio","grupo","pais","pts","pj","pg","pe","pp",
                 "gf","gc","diferencia","clasificado"]
    campos_gl = ["anio","grupo","num_partido","fecha","local","visitante",
                 "equipo","minuto","jugador","es_penal"]

    n1 = guardar_csv("grupos",           campos_g,  todos_grupos)
    n2 = guardar_csv("posiciones_grupo", campos_p,  todas_posiciones)
    n3 = guardar_csv("goles_partido",    campos_gl, todos_goles)
    print(f"  [grupos]             {anio}: {n1} grupos | {n2} posiciones | {n3} goles")
    return todos_grupos, todas_posiciones, todos_goles


# ─────────────────────────────────────────────────────────────────────────────
# 4. GOLEADORES  →  goleadores.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_goleadores(anio):
    soup = leer_html(anio, f"{anio}_goleadores")
    if not soup:
        print(f"  [NO ENCONTRADO] {anio}_goleadores.html"); return []

    goleadores = []
    for tabla in soup.find_all("table"):
        for fila in tabla.find_all("tr"):
            celdas = fila.find_all("td")
            if len(celdas) < 3:
                continue
            textos = [c.get_text(strip=True) for c in celdas]

            img_band = fila.find("img", src=lambda s: s and "banderas" in s)
            pais     = img_band.get("alt","").strip() if img_band else ""

            enlace  = fila.find("a", href=lambda h: h and "/jugadores/" in str(h))
            jugador = enlace.get_text(strip=True) if enlace else ""
            if not jugador:
                continue

            numeros = [int(t.replace("*","")) for t in textos
                       if t.replace("*","").isdigit()]
            floats  = [float(t) for t in textos
                       if re.match(r"^\d+\.\d+$", t)]

            goleadores.append({
                "anio": anio, 
                "jugador": normalizar_nombre(jugador),  # Normaliza tildes/ñs
                "pais": pais,
                "goles":    numeros[0] if len(numeros) > 0 else None,
                "partidos": numeros[1] if len(numeros) > 1 else None,
                "promedio": floats[0]  if floats else None,
            })

    campos = ["anio","jugador","pais","goles","partidos","promedio"]
    n = guardar_csv("goleadores", campos, goleadores)
    print(f"  [goleadores]         {anio}: {n} jugadores")
    return goleadores


# ─────────────────────────────────────────────────────────────────────────────
# 5. POSICIONES FINALES  →  posiciones_finales.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_posiciones_finales(anio):
    soup = leer_html(anio, f"{anio}_posiciones_finales")
    if not soup:
        print(f"  [NO ENCONTRADO] {anio}_posiciones_finales.html"); return []

    posiciones = []
    for tabla in soup.find_all("table"):
        for fila in tabla.find_all("tr"):
            celdas = fila.find_all("td")
            if len(celdas) < 2:
                continue
            textos  = [c.get_text(strip=True) for c in celdas]
            img     = fila.find("img", src=lambda s: s and "banderas" in s)
            pais    = img.get("alt","").strip() if img else ""
            pos_str = textos[0].replace(".","").strip()
            pos     = int(pos_str) if pos_str.isdigit() else None
            if pos and pais:
                posiciones.append({"anio": anio, "posicion": pos, "pais": pais})

    campos = ["anio","posicion","pais"]
    n = guardar_csv("posiciones_finales", campos, posiciones)
    print(f"  [posiciones_finales] {anio}: {n} selecciones")
    return posiciones


# ─────────────────────────────────────────────────────────────────────────────
# 6. PREMIOS  →  premios.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_premios(anio):
    soup = leer_html(anio, f"{anio}_premios")
    if not soup:
        print(f"  [NO ENCONTRADO] {anio}_premios.html"); return []

    premios        = []
    equipo_ideal   = []

    PREMIOS_INDIVIDUALES = [
        "Balón de Oro","Balón de Plata","Balón de Bronce",
        "Botín de Oro","Botín de Plata","Botín de Bronce",
        "Guante de Oro","Mejor Jugador Joven","FIFA Fair Play",
    ]

    POSICIONES_EQUIPO = ["Arquero","Defensores","Mediocampistas",
                         "Volantes","Delanteros","Entrenador"]

    for p in soup.find_all("p", class_=lambda c: c and "negri" in c):
        texto = p.get_text(strip=True)

        # ── Premios individuales ──────────────────────────────────────────
        if texto in PREMIOS_INDIVIDUALES:
            p_jugador = p.find_next_sibling("p")
            if not p_jugador:
                continue
            enlace  = p_jugador.find("a")
            img     = p_jugador.find("img", src=lambda s: s and "banderas" in s)
            jugador = enlace.get_text(strip=True) if enlace else ""
            pais    = img.get("alt","").strip() if img else ""
            if jugador:
                premios.append({"anio": anio, "tipo_premio": texto,
                                "jugador": normalizar_nombre(jugador),  # Normaliza tildes/ñs
                                "pais": pais})

        # ── Equipo Ideal ──────────────────────────────────────────────────
        elif texto == "Equipo Ideal":
            contenedor = p.find_parent("div").find_parent("div")
            if not contenedor:
                continue

            posicion_actual = ""
            for div in contenedor.find_all("div", class_=lambda c: c and "rd-100-25" in c):
                texto_div = div.get_text(" ", strip=True)

                # Detectar posición (primera palabra antes del salto)
                for pos in POSICIONES_EQUIPO:
                    if texto_div.startswith(pos):
                        posicion_actual = pos.rstrip(":")
                        break

                # Extraer todos los jugadores del bloque
                for a in div.find_all("a", href=lambda h: h and "/jugadores/" in str(h)):
                    img_band = a.find_previous_sibling("img")
                    if not img_band:
                        img_band = a.find_parent().find("img",
                                   src=lambda s: s and "banderas" in str(s))
                    jugador = a.get_text(strip=True)
                    pais    = img_band.get("alt","").strip() if img_band else ""
                    if jugador:
                        equipo_ideal.append({
                            "anio": anio, "posicion": posicion_actual,
                            "jugador": normalizar_nombre(jugador),  # Normaliza tildes/ñs
                            "pais": pais,
                        })

            # Entrenador (fuera de rd-100-25, en div con texto "Entrenador:")
            for div in contenedor.find_all("div"):
                t = div.get_text(" ", strip=True)
                if t.startswith("Entrenador:"):
                    img_band = div.find("img", src=lambda s: s and "banderas" in str(s))
                    pais     = img_band.get("alt","").strip() if img_band else ""
                    # Nombre del entrenador: texto después de la bandera
                    nombre   = re.sub(r"Entrenador:", "", t).strip()
                    # Quitar el alt de la imagen si quedó pegado
                    if img_band:
                        nombre = nombre.replace(pais, "").strip()
                    if nombre:
                        equipo_ideal.append({
                            "anio": anio, "posicion": "Entrenador",
                            "jugador": nombre, "pais": pais,
                        })
                    break

    # Guardar premios individuales
    campos_p = ["anio","tipo_premio","jugador","pais"]
    n1 = guardar_csv("premios", campos_p, premios)

    # Guardar equipo ideal en CSV separado
    campos_e = ["anio","posicion","jugador","pais"]
    n2 = guardar_csv("equipo_ideal", campos_e, equipo_ideal)

    print(f"  [premios]            {anio}: {n1} premios | {n2} jugadores equipo ideal")
    return premios, equipo_ideal


# ─────────────────────────────────────────────────────────────────────────────
# 7. TARJETAS  →  tarjetas.csv
# ─────────────────────────────────────────────────────────────────────────────

def parsear_tarjetas(anio):
    soup = leer_html(anio, f"{anio}_tarjetas")
    if not soup:
        return []

    tarjetas = []
    for tabla in soup.find_all("table"):
        primera_fila = tabla.find("tr")
        if not primera_fila:
            continue
        encabezados = [td.get_text(strip=True) for td in primera_fila.find_all("td")]
        if not any(e in encabezados for e in ["TA","TR","Jugador","Amarillas","Rojas"]):
            continue
        for fila in tabla.find_all("tr")[1:]:
            celdas  = fila.find_all("td")
            if len(celdas) < 3:
                continue
            textos  = [c.get_text(strip=True) for c in celdas]
            img     = fila.find("img", src=lambda s: s and "banderas" in s)
            pais    = img.get("alt","").strip() if img else ""
            enlace  = fila.find("a", href=lambda h: h and "/jugadores/" in str(h))
            jugador = enlace.get_text(strip=True) if enlace else ""
            if not jugador:
                continue
            numeros = [int(t) for t in textos if t.isdigit()]
            tarjetas.append({
                "anio": anio, 
                "jugador": normalizar_nombre(jugador),  # Normaliza tildes/ñs
                "pais": pais,
                "amarillas": numeros[0] if len(numeros) > 0 else None,
                "rojas":     numeros[1] if len(numeros) > 1 else None,
            })

    campos = ["anio","jugador","pais","amarillas","rojas"]
    n = guardar_csv("tarjetas", campos, tarjetas)
    print(f"  [tarjetas]           {anio}: {n} jugadores")
    return tarjetas


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def parsear_anio(anio):
    print(f"\n{'='*52}")
    print(f"  Parseando Mundial {anio}")
    print(f"{'='*52}")
    parsear_mundial(anio)
    parsear_resultados(anio)
    parsear_grupos(anio)
    parsear_goleadores(anio)
    parsear_posiciones_finales(anio)
    parsear_premios(anio)
    parsear_tarjetas(anio)

def detectar_anios():
    if not os.path.exists(HTML_DIR):
        return []
    return sorted([int(c) for c in os.listdir(HTML_DIR)
                   if os.path.isdir(os.path.join(HTML_DIR, c)) and c.isdigit()])


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZACIÓN
# Lee los CSVs crudos de data/ y produce CSVs normalizados en data/normalizado/
# Los IDs de seleccion son fijos — se leen desde seleccion.csv en la raíz.
#
# Orden de carga en BD:
#   1. seleccion        (tabla maestra sin dependencias)
#   2. mundial          (depende de seleccion)
#   3. grupo            (depende de mundial)
#   4. partido          (depende de mundial, seleccion)
#   5. posicion_grupo   (depende de grupo, seleccion)
#   6. gol              (depende de partido, seleccion)
#   7. goleador         (depende de mundial, seleccion)
#   8. posicion_final   (depende de mundial, seleccion)
#   9. premio           (depende de mundial, seleccion)
#  10. equipo_ideal     (depende de mundial, seleccion)
#  11. tarjeta          (depende de mundial, seleccion)
#  12. jugador_pais     (depende de seleccion)
# ─────────────────────────────────────────────────────────────────────────────

import csv as _csv

NORM_DIR = os.path.join(DATA_DIR, "normalizado")

def _leer(nombre, carpeta=DATA_DIR):
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(_csv.DictReader(f))

def _escribir(nombre, campos, filas):
    os.makedirs(NORM_DIR, exist_ok=True)
    ruta = os.path.join(NORM_DIR, f"{nombre}.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def _match_jugador(nombre, jugador_idx_exacto, jugador_idx_invertido):
    """
    Busca el id_jugador dado un nombre.
    Soporta múltiples formatos:
      - "Nombre Apellido" (HTML)
      - "Apellido, Nombre" (CSV con coma)
    
    Estrategia de matching:
      1. Busca exacto en ambos índices
      2. Intenta invertir si tiene coma o espacios
      3. Busca versión normalizada (sin acentos)
    """
    if not nombre:
        return None
    
    n = nombre.strip().lower()
    
    # 1. Buscar directo (ya en el índice exacto)
    if n in jugador_idx_exacto:
        return jugador_idx_exacto[n]
    if n in jugador_idx_invertido:
        return jugador_idx_invertido[n]
    
    # 2. Buscar también versión normalizada (sin acentos/tildes)
    n_norm = normalizar_texto(n).lower()
    if n_norm in jugador_idx_exacto:
        return jugador_idx_exacto[n_norm]
    if n_norm in jugador_idx_invertido:
        return jugador_idx_invertido[n_norm]
    
    # 3. Si tiene coma, es formato "Apellido, Nombre" - convertir a "Nombre Apellido"
    if "," in n:
        partes = [p.strip() for p in n.split(",", 1)]
        invertido = f"{partes[1]} {partes[0]}".lower()
        if invertido in jugador_idx_exacto:
            return jugador_idx_exacto[invertido]
        if invertido in jugador_idx_invertido:
            return jugador_idx_invertido[invertido]
        # Probar también versión normalizada
        invertido_norm = normalizar_texto(invertido).lower()
        if invertido_norm in jugador_idx_exacto:
            return jugador_idx_exacto[invertido_norm]
        if invertido_norm in jugador_idx_invertido:
            return jugador_idx_invertido[invertido_norm]
    
    # 4. Si NO tiene coma pero tiene espacios, es "Nombre Apellido" - intentar invertir a "Apellido Nombre"
    if " " in n and "," not in n:
        partes = n.rsplit(" ", 1)  # Últimas 2 palabras
        if len(partes) == 2:
            invertido = f"{partes[1]}, {partes[0]}".lower()
            if invertido in jugador_idx_exacto:
                return jugador_idx_exacto[invertido]
            if invertido in jugador_idx_invertido:
                return jugador_idx_invertido[invertido]
            # Probar también versión normalizada
            invertido_norm = normalizar_texto(invertido).lower()
            if invertido_norm in jugador_idx_exacto:
                return jugador_idx_exacto[invertido_norm]
            if invertido_norm in jugador_idx_invertido:
                return jugador_idx_invertido[invertido_norm]
    
    return None

def normalizar():
    print(f"\n{'='*52}")
    print("  NORMALIZANDO datos...")
    print(f"{'='*52}")

    # ── Leer todos los CSVs crudos ────────────────────────────────────────────
    mundiales    = _leer("mundiales")
    partidos     = _leer("partidos")
    grupos       = _leer("grupos")
    pos_grupo    = _leer("posiciones_grupo")
    goles        = _leer("goles_partido")
    goleadores   = _leer("goleadores")
    pos_finales  = _leer("posiciones_finales")
    premios      = _leer("premios")
    equipo_ideal = _leer("equipo_ideal")
    tarjetas     = _leer("tarjetas")
    jugadores    = _leer("jugadores_pais")  # Busca en scripts/data/

    # Si no hay datos, buscar en la carpeta padre (bases2_1s26_G9/data/)
    if not jugadores:
        # Usar sys.argv[0] para obtener la ruta del script actual
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        parent_data_path = os.path.join(os.path.dirname(script_dir), "data")
        if os.path.exists(parent_data_path):
            jugadores = _leer("jugadores_pais", carpeta=parent_data_path)
    
    if not jugadores:
        print("  [ADVERTENCIA] No se encontró jugadores_pais.csv")
        print("              Búscalo en: ./data/ o ../data/")
        print("              Los id_jugador en goles/premios/etc serán NULL")
    
    # Construir índices de jugadores para match por nombre
    # Soporta dos formatos: "Nombre Apellido" y "Apellido, Nombre"
    # También crea índices con versión normalizada (sin acentos)
    _jug_exacto    = {}
    _jug_invertido = {}
    for _i, _r in enumerate(jugadores, 1):
        # Intentar obtener id_jugador; si no existe, usar el índice
        _nom = (_r.get("nombre") or _r.get("NOMBRE","")).strip()
        _id  = int(_r.get("id_jugador") or _r.get("ID JUGADOR") or _i)
        
        if not _nom:
            continue
        
        _nom_lower = _nom.lower()
        
        # Índice 1: Nombre EXACTO como está en el CSV (ej: "Achilier, Gabriel")
        _jug_exacto[_nom_lower] = _id
        
        # Índice 1b: También versión normalizada (sin acentos/tildes)
        _nom_norm = normalizar_texto(_nom_lower).lower()
        if _nom_norm != _nom_lower:  # Solo si tiene diferencia
            _jug_exacto[_nom_norm] = _id
        
        # Índice 2: Si tiene coma, guardar también sin comas y parseado
        if "," in _nom_lower:
            # "Valencia, Enner" → también buscar "Valencia Enner" o "Enner Valencia"
            _partes = _nom_lower.split(",", 1)
            _apellido = _partes[0].strip()
            _nombre = _partes[1].strip()
            
            # Guardar como "Apellido Nombre" (sin coma)
            _sin_coma = f"{_apellido} {_nombre}"
            _jug_invertido[_sin_coma] = _id
            
            # Guardar como "Nombre Apellido" (invertido)
            _invertido = f"{_nombre} {_apellido}"
            _jug_invertido[_invertido] = _id
            
            # También versiones normalizadas
            _sin_coma_norm = normalizar_texto(_sin_coma).lower()
            _invertido_norm = normalizar_texto(_invertido).lower()
            if _sin_coma_norm != _sin_coma:
                _jug_invertido[_sin_coma_norm] = _id
            if _invertido_norm != _invertido:
                _jug_invertido[_invertido_norm] = _id
        
        # Índice 3: Si NO tiene coma, crear versión con coma
        elif " " in _nom_lower:
            # "Juan Pérez" → también buscar "Pérez, Juan"
            _partes_esp = _nom_lower.rsplit(" ", 1)
            if len(_partes_esp) == 2:
                _con_coma = f"{_partes_esp[1]}, {_partes_esp[0]}"
                _jug_invertido[_con_coma] = _id
                
                # También versión normalizada
                _con_coma_norm = normalizar_texto(_con_coma).lower()
                if _con_coma_norm != _con_coma:
                    _jug_invertido[_con_coma_norm] = _id

    # ── 1. SELECCION — IDs fijos desde seleccion.csv ──────────────────────────
    # Busca seleccion.csv en: carpeta del script → directorio actual → data/
    _script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    sel_ref = _leer("seleccion", carpeta=_script_dir)
    if not sel_ref:
        sel_ref = _leer("seleccion", carpeta=".")
    if not sel_ref:
        sel_ref = _leer("seleccion", carpeta=DATA_DIR)
    if not sel_ref:
        print("  [ERROR] No se encontró seleccion.csv")
        print(f"         Colócalo en: {_script_dir}")
        print("         con columnas: id_seleccion, nombre")
        return

    # Construir mapa nombre → id_seleccion
    # Soporta dos formatos:
    #   - Con IDs: columnas id_seleccion + nombre
    #   - Sin IDs: columna seleccion (genera IDs alfabéticos)
    sel_map = {}
    primera = sel_ref[0]
    if "id_seleccion" in primera and "nombre" in primera:
        # Ya tiene IDs definidos
        for r in sel_ref:
            if r["nombre"].strip():
                sel_map[r["nombre"].strip()] = int(r["id_seleccion"])
    else:
        # Solo tiene nombres — generar IDs alfabéticos
        nombres = sorted(
            (r.get("nombre") or r.get("seleccion") or "").strip()
            for r in sel_ref
        )
        sel_map = {n: i+1 for i, n in enumerate(n for n in nombres if n)}

    filas_sel = [{"id_seleccion": v, "nombre": k}
                 for k, v in sorted(sel_map.items(), key=lambda x: x[1])]
    n = _escribir("seleccion", ["id_seleccion","nombre"], filas_sel)
    print(f"  [seleccion]          {n} países (IDs fijos desde seleccion.csv)")

    def sid(nombre):
        """Retorna el id_seleccion para un nombre de país."""
        return sel_map.get((nombre or "").strip())

    # ── 2. MUNDIAL ────────────────────────────────────────────────────────────
    filas = []
    for r in mundiales:
        filas.append({
            "id_mundial":      int(r["anio"]),
            "anio":            int(r["anio"]),
            "id_organizador":  sid(r.get("organizador","")),
            "organizador":     r.get("organizador",""),
            "id_campeon":      sid(r.get("campeon","")),
            "campeon":         r.get("campeon",""),
            "num_selecciones": r.get("num_selecciones") or None,
            "num_partidos":    r.get("num_partidos") or None,
            "goles":           r.get("goles") or None,
            "promedio_gol":    r.get("promedio_gol") or None,
        })
    n = _escribir("mundial", ["id_mundial","anio","id_organizador","organizador",
                               "id_campeon","campeon","num_selecciones",
                               "num_partidos","goles","promedio_gol"], filas)
    print(f"  [mundial]            {n} mundiales")

    # ── 3. GRUPO ──────────────────────────────────────────────────────────────
    filas     = []
    grupo_map = {}
    id_g      = 1
    for r in grupos:
        key = (int(r["anio"]), r["grupo"].strip())
        grupo_map[key] = id_g
        filas.append({"id_grupo": id_g, "anio": int(r["anio"]),
                      "nombre": r["grupo"].strip()})
        id_g += 1
    n = _escribir("grupo", ["id_grupo","anio","nombre"], filas)
    print(f"  [grupo]              {n} grupos")

    # ── 4. PARTIDO ────────────────────────────────────────────────────────────
    filas       = []
    partido_map = {}
    id_p        = 1
    for r in partidos:
        anio = int(r["anio"])
        num  = int(r["num_partido"]) if r.get("num_partido") else None
        partido_map[(anio, num)] = id_p
        filas.append({
            "id_partido":        id_p,
            "anio":              anio,
            "num_partido":       num,
            "fecha":             r.get("fecha",""),
            "etapa":             r.get("etapa",""),
            "id_local":          sid(r.get("local","")),
            "local":             r.get("local",""),
            "id_visitante":      sid(r.get("visitante","")),
            "visitante":         r.get("visitante",""),
            "goles_local":       r.get("goles_local") or None,
            "goles_visitante":   r.get("goles_visitante") or None,
            "tiempo_extra":      r.get("tiempo_extra",""),
            "penales":           r.get("penales",""),
            "penales_local":     r.get("penales_local") or None,
            "penales_visitante": r.get("penales_visitante") or None,
        })
        id_p += 1
    n = _escribir("partido", [
        "id_partido","anio","num_partido","fecha","etapa",
        "id_local","local","id_visitante","visitante",
        "goles_local","goles_visitante","tiempo_extra",
        "penales","penales_local","penales_visitante"
    ], filas)
    print(f"  [partido]            {n} partidos")

    # ── 5. POSICION_GRUPO ─────────────────────────────────────────────────────
    filas  = []
    id_pg  = 1
    for r in pos_grupo:
        anio = int(r["anio"])
        filas.append({
            "id_posicion_grupo": id_pg,
            "id_grupo":          grupo_map.get((anio, r["grupo"].strip())),
            "anio":              anio,
            "grupo":             r["grupo"].strip(),
            "id_seleccion":      sid(r.get("pais","")),
            "pais":              r.get("pais",""),
            "pts":               r.get("pts") or None,
            "pj":                r.get("pj") or None,
            "pg":                r.get("pg") or None,
            "pe":                r.get("pe") or None,
            "pp":                r.get("pp") or None,
            "gf":                r.get("gf") or None,
            "gc":                r.get("gc") or None,
            "diferencia":        r.get("diferencia") or None,
            "clasificado":       r.get("clasificado",""),
        })
        id_pg += 1
    n = _escribir("posicion_grupo", [
        "id_posicion_grupo","id_grupo","anio","grupo","id_seleccion","pais",
        "pts","pj","pg","pe","pp","gf","gc","diferencia","clasificado"
    ], filas)
    print(f"  [posicion_grupo]     {n} filas")

    # ── 6. GOL ────────────────────────────────────────────────────────────────
    filas  = []
    id_gol = 1
    for r in goles:
        anio = int(r["anio"])
        num  = int(r["num_partido"]) if r.get("num_partido") else None
        jugador = r.get("jugador","").strip()
        filas.append({
            "id_gol":       id_gol,
            "id_partido":   partido_map.get((anio, num)),
            "anio":         anio,
            "num_partido":  num,
            "id_seleccion": sid(r.get("equipo","")),
            "equipo":       r.get("equipo",""),
            "id_jugador":   _match_jugador(jugador, _jug_exacto, _jug_invertido),
            "jugador":      jugador,
            "minuto":       r.get("minuto") or None,
            "es_penal":     r.get("es_penal",""),
        })
        id_gol += 1
    n = _escribir("gol", [
        "id_gol","id_partido","anio","num_partido",
        "id_seleccion","equipo","id_jugador","jugador","minuto","es_penal"
    ], filas)
    print(f"  [gol]                {n} goles")

    # ── 7. GOLEADOR ───────────────────────────────────────────────────────────
    filas  = []
    id_gle = 1
    for r in goleadores:
        jugador = r.get("jugador","").strip()
        filas.append({
            "id_goleador":  id_gle,
            "anio":         int(r["anio"]),
            "id_seleccion": sid(r.get("pais","")),
            "pais":         r.get("pais",""),
            "id_jugador":   _match_jugador(jugador, _jug_exacto, _jug_invertido),
            "jugador":      jugador,
            "goles":        r.get("goles") or None,
            "partidos":     r.get("partidos") or None,
            "promedio":     r.get("promedio") or None,
        })
        id_gle += 1
    n = _escribir("goleador", [
        "id_goleador","anio","id_seleccion","pais",
        "id_jugador","jugador","goles","partidos","promedio"
    ], filas)
    print(f"  [goleador]           {n} jugadores")

    # ── 8. POSICION_FINAL ─────────────────────────────────────────────────────
    filas = []
    id_pf = 1
    for r in pos_finales:
        filas.append({
            "id_posicion_final": id_pf,
            "anio":              int(r["anio"]),
            "posicion":          r.get("posicion") or None,
            "id_seleccion":      sid(r.get("pais","")),
            "pais":              r.get("pais",""),
        })
        id_pf += 1
    n = _escribir("posicion_final", [
        "id_posicion_final","anio","posicion","id_seleccion","pais"
    ], filas)
    print(f"  [posicion_final]     {n} selecciones")

    # ── 9. PREMIO ─────────────────────────────────────────────────────────────
    filas  = []
    id_pre = 1
    for r in premios:
        jugador = r.get("jugador","").strip()
        filas.append({
            "id_premio":    id_pre,
            "anio":         int(r["anio"]),
            "tipo_premio":  r.get("tipo_premio",""),
            "id_jugador":   _match_jugador(jugador, _jug_exacto, _jug_invertido),
            "jugador":      jugador,
            "id_seleccion": sid(r.get("pais","")),
            "pais":         r.get("pais",""),
        })
        id_pre += 1
    n = _escribir("premio", [
        "id_premio","anio","tipo_premio","id_jugador","jugador","id_seleccion","pais"
    ], filas)
    print(f"  [premio]             {n} premios")

    # ── 10. EQUIPO_IDEAL ──────────────────────────────────────────────────────
    filas = []
    id_ei = 1
    for r in equipo_ideal:
        jugador = r.get("jugador","").strip()
        filas.append({
            "id_equipo_ideal": id_ei,
            "anio":            int(r["anio"]),
            "posicion":        r.get("posicion",""),
            "id_jugador":      _match_jugador(jugador, _jug_exacto, _jug_invertido),
            "jugador":         jugador,
            "id_seleccion":    sid(r.get("pais","")),
            "pais":            r.get("pais",""),
        })
        id_ei += 1
    n = _escribir("equipo_ideal", [
        "id_equipo_ideal","anio","posicion","id_jugador","jugador","id_seleccion","pais"
    ], filas)
    print(f"  [equipo_ideal]       {n} jugadores")

    # ── 11. TARJETA ───────────────────────────────────────────────────────────
    filas  = []
    id_tar = 1
    for r in tarjetas:
        jugador = r.get("jugador","").strip()
        filas.append({
            "id_tarjeta":   id_tar,
            "anio":         int(r["anio"]),
            "id_seleccion": sid(r.get("pais","")),
            "pais":         r.get("pais",""),
            "id_jugador":   _match_jugador(jugador, _jug_exacto, _jug_invertido),
            "jugador":      jugador,
            "amarillas":    r.get("amarillas") or None,
            "rojas":        r.get("rojas") or None,
        })
        id_tar += 1
    n = _escribir("tarjeta", [
        "id_tarjeta","anio","id_seleccion","pais","id_jugador","jugador","amarillas","rojas"
    ], filas)
    print(f"  [tarjeta]            {n} jugadores")

    # ── 12. JUGADOR_PAIS ──────────────────────────────────────────────────────
    filas  = []
    id_jug = 1
    for r in jugadores:
        filas.append({
            "id_jugador":   id_jug,
            "nombre":       r.get("nombre",""),
            "id_seleccion": sid(r.get("seleccion","")),
            "seleccion":    r.get("seleccion",""),
        })
        id_jug += 1
    n = _escribir("jugador_pais", [
        "id_jugador","nombre","id_seleccion","seleccion"
    ], filas)
    print(f"  [jugador_pais]       {n} jugadores")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print(f"\n{'='*52}")
    print(f"  CSVs normalizados → {NORM_DIR}/")
    print(f"{'='*52}")
    for arch in sorted(os.listdir(NORM_DIR)):
        if arch.endswith(".csv"):
            with open(os.path.join(NORM_DIR, arch), encoding="utf-8") as f:
                filas_n = sum(1 for _ in f) - 1
            print(f"  {arch:<35} {filas_n:>5} filas")

if __name__ == "__main__":
    for arch in ["mundiales","partidos","grupos","posiciones_grupo",
                 "goles_partido","goleadores","posiciones_finales","premios","equipo_ideal","tarjetas"]:
        ruta = os.path.join(DATA_DIR, f"{arch}.csv")
        if os.path.exists(ruta):
            os.remove(ruta)

    anios = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else detectar_anios()
    if not anios:
        print("No se encontraron años en html/. Descarga primero con 1_mundiales.py")
        sys.exit(1)

    print(f"Años a parsear: {anios}")
    for anio in anios:
        parsear_anio(anio)

    print(f"\n{'='*52}")
    print("COMPLETADO - CSVs en ./data/")
    print(f"{'='*52}")
    for arch in sorted(os.listdir(DATA_DIR)):
        if arch.endswith(".csv"):
            with open(os.path.join(DATA_DIR, arch), encoding="utf-8") as f:
                filas = sum(1 for _ in f) - 1
            print(f"  {arch:<35} {filas:>4} filas")

    normalizar()