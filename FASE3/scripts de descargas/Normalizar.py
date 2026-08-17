"""
normalizar.py
=============
Lee los CSVs crudos de data/{anio}/ (generados por parserFinal.py)
y produce CSVs normalizados en data/normalizado/ listos para importar a Oracle.

Un CSV por cada tabla de la base de datos:
    seleccion.csv
    jugador_pais.csv
    mundial.csv
    grupo.csv
    partido.csv
    posicion_grupo.csv
    gol.csv
    goleador.csv
    posicion_final.csv
    tipo_premio.csv
    premio.csv
    equipo_ideal.csv
    tarjeta.csv

Los IDs se manejan así:
    - ID_SELECCION   → fijo, viene de scripts/seleccion.csv
    - ID_JUGADOR     → fijo, viene de scripts/jugadores_pais.csv
    - ID_TIPO_PREMIO → fijo, viene de scripts/tipo_premio.csv  (lo generás vos)
    - ANIO           → clave natural de MUNDIAL, no necesita ID propio
    - (ANIO, ID_GRUPO) → clave compuesta natural, no necesita ID propio
    - Todos los demás → incremental global generado aquí

Uso:
    python normalizar.py           # procesa todos los años en data/
    python normalizar.py 1930 1934 # solo esos años

IMPORTANTE: procesá los años en orden ascendente para que los IDs
            incrementales sean reproducibles y estables.
"""

import os
import sys
import csv
import re

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR   = os.path.dirname(_SCRIPT_DIR)

DATA_DIR  = os.path.join(_BASE_DIR, "data")
NORM_DIR  = os.path.join(DATA_DIR, "normalizado")


# ─── Utilidades de lectura / escritura ───────────────────────────────────────

def leer_csv(ruta):
    """Lee un CSV y retorna lista de dicts. Retorna [] si no existe."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escribir_csv(nombre, campos, filas, modo="w"):
    """
    Escribe filas en data/normalizado/{nombre}.csv.
    modo='w' → crea/sobreescribe (primer año o al inicio)
    modo='a' → agrega filas (años siguientes)
    """
    os.makedirs(NORM_DIR, exist_ok=True)
    ruta = os.path.join(NORM_DIR, f"{nombre}.csv")
    with open(ruta, modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if modo == "w":
            w.writeheader()
        w.writerows(filas)
    return len(filas)


def _to_int(val):
    """Convierte a int o retorna None si está vacío o no es numérico."""
    if val is None:
        return None
    s = str(val).strip().replace(".", "")
    try:
        return int(s)
    except ValueError:
        return None


def _to_float(val):
    """Convierte a float o retorna None."""
    if val is None:
        return None
    try:
        return float(str(val).strip())
    except ValueError:
        return None


# ─── Carga de tablas maestras (IDs fijos) ────────────────────────────────────

def cargar_selecciones():
    """
    Carga scripts/seleccion.csv.
    Retorna:
        sel_map  → dict  nombre → id_seleccion
        sel_rows → lista de dicts para escribir seleccion.csv normalizado
    """
    ruta = os.path.join(_SCRIPT_DIR, "seleccion.csv")
    filas = leer_csv(ruta)
    if not filas:
        print(f"  [ERROR] No se encontró {ruta}")
        sys.exit(1)

    sel_map  = {}
    sel_rows = []
    primera  = filas[0]

    if "id_seleccion" in primera:
        for r in filas:
            nombre = r.get("nombre", "").strip()
            if nombre:
                sel_map[nombre] = int(r["id_seleccion"])
                sel_rows.append({"id_seleccion": int(r["id_seleccion"]), "nombre": nombre})
    else:
        # Solo tiene la columna "seleccion" sin IDs — generamos alfabéticos
        nombres = sorted(set(
            r.get("nombre", r.get("seleccion", "")).strip()
            for r in filas
        ))
        for i, n in enumerate(nombres, 1):
            if n:
                sel_map[n] = i
                sel_rows.append({"id_seleccion": i, "nombre": n})

    print(f"  [seleccion]   {len(sel_map)} países cargados")
    return sel_map, sel_rows


def cargar_jugadores():
    """
    Carga scripts/jugadores_pais.csv.
    El CSV usa ';' como separador y tiene columnas:
        ID JUGADOR;NOMBRE;ID SELECCION;SELECCION

    Retorna:
        jug_rows → lista de dicts normalizados para escribir jugador_pais.csv
        jug_map  → dict  nombre_normalizado → id_jugador  (para matching)
    """
    ruta = os.path.join(_SCRIPT_DIR, "jugadores_pais.csv")
    if not os.path.exists(ruta):
        print(f"  [ADVERTENCIA] No se encontró {ruta}")
        return [], {}

    filas = []
    with open(ruta, encoding="utf-8") as f:
        # Detectar separador
        primera_linea = f.readline()
        sep = ";" if ";" in primera_linea else ","
        f.seek(0)
        reader = csv.DictReader(f, delimiter=sep)
        for r in reader:
            filas.append(r)

    jug_rows = []
    jug_map  = {}   # {nombre_normalizado: id_jugador}

    for r in filas:
        # Nombres de columna con o sin espacios
        id_j  = r.get("ID JUGADOR") or r.get("id_jugador") or r.get("ID_JUGADOR", "")
        nom   = r.get("NOMBRE")     or r.get("nombre", "")
        id_s  = r.get("ID SELECCION") or r.get("id_seleccion") or r.get("ID_SELECCION", "")
        sel   = r.get("SELECCION")  or r.get("seleccion", "")

        id_j  = str(id_j).strip()
        nom   = nom.strip()
        id_s  = str(id_s).strip()
        sel   = sel.strip()

        if not id_j or not nom:
            continue

        id_j_int = int(id_j)

        jug_rows.append({
            "id_jugador":   id_j_int,
            "nombre":       nom,
            "id_seleccion": _to_int(id_s),
            "seleccion":    sel,
        })

        # Construir índice de matching (varios formatos del mismo nombre)
        _indexar_jugador(nom, id_j_int, jug_map)

    print(f"  [jugador_pais] {len(jug_rows)} jugadores cargados")
    return jug_rows, jug_map


def _normalizar_str(s):
    """
    Normaliza un string para matching:
    - minúsculas
    - sin acentos
    Preserva ñ.
    """
    import unicodedata
    if not s:
        return ""
    s = s.strip().lower()
    nfd = unicodedata.normalize("NFD", s)
    resultado = "".join(
        c for c in nfd
        if unicodedata.category(c) != "Mn"
    )
    return unicodedata.normalize("NFC", resultado)


def _indexar_jugador(nombre, id_jugador, indice):
    """
    Agrega variantes del nombre al índice de matching.
    Soporta:
        "Apellido, Nombre"   (formato CSV)
        "Nombre Apellido"    (formato HTML)
    Y versiones normalizadas (sin acentos) de ambas.
    """
    def _add(clave, val):
        clave_norm = _normalizar_str(clave)
        indice[clave.strip().lower()] = val
        if clave_norm != clave.strip().lower():
            indice[clave_norm] = val

    _add(nombre, id_jugador)

    if "," in nombre:
        # "Apellido, Nombre" → también guardar "Nombre Apellido"
        partes    = nombre.split(",", 1)
        apellido  = partes[0].strip()
        pnombre   = partes[1].strip()
        _add(f"{pnombre} {apellido}", id_jugador)
        _add(f"{apellido} {pnombre}", id_jugador)  # sin coma
    elif " " in nombre:
        # "Nombre Apellido" → también guardar "Apellido, Nombre"
        partes   = nombre.rsplit(" ", 1)
        _add(f"{partes[1]}, {partes[0]}", id_jugador)


def buscar_jugador(nombre, jug_map):
    """
    Busca el ID de un jugador por nombre en el índice.
    Retorna id_jugador (int) o None si no se encuentra.
    """
    if not nombre:
        return None
    # Intentar directo
    clave = nombre.strip().lower()
    if clave in jug_map:
        return jug_map[clave]
    # Intentar normalizado (sin acentos)
    clave_norm = _normalizar_str(nombre)
    if clave_norm in jug_map:
        return jug_map[clave_norm]
    return None


def cargar_tipos_premio():
    """
    Carga scripts/tipo_premio.csv.
    Si no existe, usa los tipos estándar conocidos.
    Retorna:
        tp_map  → dict  nombre → id_tipo_premio
        tp_rows → lista de dicts para escribir tipo_premio.csv normalizado
    """
    # Tipos estándar si no hay archivo
    TIPOS_ESTANDAR = [
        "Balón de Oro", "Balón de Plata", "Balón de Bronce",
        "Botín de Oro", "Botín de Plata", "Botín de Bronce",
        "Guante de Oro", "Mejor Jugador Joven", "FIFA Fair Play",
        "Premio Fair Play", "Mejor Portero",
    ]

    ruta = os.path.join(_SCRIPT_DIR, "tipo_premio.csv")
    if os.path.exists(ruta):
        filas = leer_csv(ruta)
    else:
        filas = [{"id_tipo_premio": str(i+1), "nombre": n}
                 for i, n in enumerate(TIPOS_ESTANDAR)]
        print(f"  [INFO] tipo_premio.csv no encontrado — usando {len(TIPOS_ESTANDAR)} tipos estándar")

    tp_map  = {}
    tp_rows = []
    for r in filas:
        nombre = r.get("nombre", "").strip()
        id_tp  = _to_int(r.get("id_tipo_premio", ""))
        if nombre and id_tp:
            tp_map[nombre]  = id_tp
            tp_rows.append({"id_tipo_premio": id_tp, "nombre": nombre})

    return tp_map, tp_rows


def sid(nombre, sel_map):
    """Retorna id_seleccion para un nombre de país, o None."""
    return sel_map.get((nombre or "").strip())


# ─── Clase de contadores globales ────────────────────────────────────────────

class Contadores:
    """
    Mantiene los contadores incrementales globales para los IDs de tablas
    que no tienen IDs fijos externos.
    Se usa una sola instancia durante toda la ejecución de normalizar.py.
    """
    def __init__(self):
        self.partido        = 0
        self.posicion_grupo = 0
        self.gol            = 0
        self.goleador       = 0
        self.posicion_final = 0
        self.premio         = 0
        self.equipo_ideal   = 0
        self.tarjeta        = 0

    def sig_partido(self):
        self.partido += 1
        return self.partido

    def sig_posicion_grupo(self):
        self.posicion_grupo += 1
        return self.posicion_grupo

    def sig_gol(self):
        self.gol += 1
        return self.gol

    def sig_goleador(self):
        self.goleador += 1
        return self.goleador

    def sig_posicion_final(self):
        self.posicion_final += 1
        return self.posicion_final

    def sig_premio(self):
        self.premio += 1
        return self.premio

    def sig_equipo_ideal(self):
        self.equipo_ideal += 1
        return self.equipo_ideal

    def sig_tarjeta(self):
        self.tarjeta += 1
        return self.tarjeta


# ─── Normalización por año ────────────────────────────────────────────────────

def normalizar_anio(anio, sel_map, jug_map, tp_map, contadores, partido_map):
    """
    Procesa data/{anio}/*.csv y agrega filas a data/normalizado/*.csv.

    partido_map: dict global (anio, id_partido_str) → id_partido
                 Se llena aquí y se pasa a la siguiente iteración para que
                 los goles puedan referenciar el ID correcto de su partido.
    """
    dir_anio = os.path.join(DATA_DIR, str(anio))
    print(f"\n  Normalizando {anio}...")

    # Determinar modo: 'w' solo para el primer año (para crear el archivo),
    # 'a' para los siguientes. La lógica se maneja afuera; aquí siempre 'a'
    # porque ya se inicializaron los archivos con encabezado antes del loop.
    modo = "a"

    def _sid(nombre):
        return sid(nombre, sel_map)

    def _jug(nombre):
        return buscar_jugador(nombre, jug_map)

    # ── 1. MUNDIAL ──────────────────────────────────────────────────────────
    filas_mundial = leer_csv(os.path.join(dir_anio, "mundial.csv"))
    out_mundial   = []
    for r in filas_mundial:
        org  = (r.get("organizador") or "").strip()
        camp = (r.get("campeon") or "").strip()
        out_mundial.append({
            "anio":             anio,
            "id_organizador":   _sid(org),
            "organizador":      org,
            "id_campeon":       _sid(camp),
            "campeon":          camp,
            "num_selecciones":  _to_int(r.get("num_selecciones")),
            "num_partidos":     _to_int(r.get("num_partidos")),
            "goles":            _to_int(r.get("goles")),
            "promedio_gol":     _to_float(r.get("promedio_gol")),
        })
    n = escribir_csv("mundial", [
        "anio", "id_organizador", "organizador",
        "id_campeon", "campeon",
        "num_selecciones", "num_partidos", "goles", "promedio_gol"
    ], out_mundial, modo)
    print(f"    [mundial]           {n} filas")

    # ── 2. GRUPO ────────────────────────────────────────────────────────────
    # PK compuesta (anio, id_grupo) → no necesita ID incremental
    filas_grupos = leer_csv(os.path.join(dir_anio, "grupos.csv"))
    out_grupos   = []
    for r in filas_grupos:
        id_g = (r.get("id_grupo") or "").strip()
        out_grupos.append({
            "anio":       anio,
            "id_grupo":   id_g,
            "selecciones": (r.get("selecciones") or "").strip(),
        })
    n = escribir_csv("grupo", ["anio", "id_grupo", "selecciones"],
                     out_grupos, modo)
    print(f"    [grupo]             {n} filas")

    # ── 3. PARTIDO ──────────────────────────────────────────────────────────
    # ID incremental global. También llenamos partido_map para los goles.
    filas_partidos = leer_csv(os.path.join(dir_anio, "partidos.csv"))
    out_partidos   = []
    for r in filas_partidos:
        id_p = contadores.sig_partido()
        clave = (anio, r.get("id_partido_str", ""))
        partido_map[clave] = id_p

        out_partidos.append({
            "id_partido":         id_p,
            "anio":               anio,
            "num_partido":        _to_int(r.get("num_partido_seq") or r.get("num_partido")),
            "fecha":              (r.get("fecha") or "").strip(),
            "etapa":              (r.get("etapa") or "").strip(),
            "id_local":           _sid(r.get("local", "")),
            "local":              (r.get("local") or "").strip(),
            "id_visitante":       _sid(r.get("visitante", "")),
            "visitante":          (r.get("visitante") or "").strip(),
            "goles_local":        _to_int(r.get("goles_local")),
            "goles_visitante":    _to_int(r.get("goles_visitante")),
            "tiempo_extra":       (r.get("tiempo_extra") or "NO").strip(),
            "penales":            (r.get("penales") or "NO").strip(),
            "penales_local":      _to_int(r.get("penales_local")),
            "penales_visitante":  _to_int(r.get("penales_visitante")),
        })
    n = escribir_csv("partido", [
        "id_partido", "anio", "num_partido", "fecha", "etapa",
        "id_local", "local", "id_visitante", "visitante",
        "goles_local", "goles_visitante",
        "tiempo_extra", "penales", "penales_local", "penales_visitante"
    ], out_partidos, modo)
    print(f"    [partido]           {n} filas")

    # ── 4. POSICION_GRUPO ────────────────────────────────────────────────────
    filas_pg = leer_csv(os.path.join(dir_anio, "posiciones_grupo.csv"))
    out_pg   = []
    for r in filas_pg:
        id_pg  = contadores.sig_posicion_grupo()
        id_g   = (r.get("id_grupo") or "").strip()
        pais   = (r.get("seleccion") or "").strip()

        # Clasificado: cualquier valor no vacío que no sea "NO" → "SI"
        clas_raw = (r.get("clasificado") or "").strip()
        clas     = "SI" if clas_raw and clas_raw.upper() not in ("NO", "0", "") else "NO"

        out_pg.append({
            "id_posicion_grupo": id_pg,
            "anio":              anio,
            "id_grupo":          id_g,
            "id_seleccion":      _sid(pais),
            "seleccion":         pais,
            "pts":               _to_int(r.get("pts")),
            "pj":                _to_int(r.get("pj")),
            "pg":                _to_int(r.get("pg")),
            "pe":                _to_int(r.get("pe")),
            "pp":                _to_int(r.get("pp")),
            "gf":                _to_int(r.get("gf")),
            "gc":                _to_int(r.get("gc")),
            "diferencia":        _to_int(r.get("diferencia")),
            "clasificado":       clas,
        })
    n = escribir_csv("posicion_grupo", [
        "id_posicion_grupo", "anio", "id_grupo", "id_seleccion", "seleccion",
        "pts", "pj", "pg", "pe", "pp", "gf", "gc", "diferencia", "clasificado"
    ], out_pg, modo)
    print(f"    [posicion_grupo]    {n} filas")

    # ── 5. GOL ───────────────────────────────────────────────────────────────
    filas_goles = leer_csv(os.path.join(dir_anio, "goles.csv"))
    out_goles   = []
    for r in filas_goles:
        id_g  = contadores.sig_gol()
        clave = (anio, r.get("id_partido_str", ""))
        id_p  = partido_map.get(clave)   # None si no se encontró el partido

        equipo   = (r.get("equipo") or "").strip()
        jugador  = (r.get("jugador") or "").strip()
        minuto   = _to_int(r.get("minuto"))

        # Ignorar goles con minuto nulo (datos incompletos)
        if minuto is None:
            continue

        out_goles.append({
            "id_gol":       id_g,
            "id_partido":   id_p,
            "anio":         anio,
            "id_seleccion": _sid(equipo),
            "equipo":       equipo,
            "id_jugador":   _jug(jugador),
            "jugador":      jugador,
            "minuto":       minuto,
            "es_penal":     (r.get("es_penal") or "NO").strip(),
            "es_autogol":   (r.get("es_autogol") or "NO").strip(),
        })
    n = escribir_csv("gol", [
        "id_gol", "id_partido", "anio",
        "id_seleccion", "equipo",
        "id_jugador", "jugador",
        "minuto", "es_penal", "es_autogol"
    ], out_goles, modo)
    print(f"    [gol]               {n} filas")

    # ── 6. GOLEADOR ──────────────────────────────────────────────────────────
    filas_gle = leer_csv(os.path.join(dir_anio, "goleadores.csv"))
    out_gle   = []
    for r in filas_gle:
        id_gle  = contadores.sig_goleador()
        pais    = (r.get("seleccion") or "").strip()
        jugador = (r.get("jugador") or "").strip()
        out_gle.append({
            "id_goleador":  id_gle,
            "anio":         anio,
            "id_seleccion": _sid(pais),
            "seleccion":    pais,
            "id_jugador":   _jug(jugador),
            "jugador":      jugador,
            "goles":        _to_int(r.get("goles")),
            "partidos":     _to_int(r.get("partidos")),
            "promedio":     _to_float(r.get("promedio")),
        })
    n = escribir_csv("goleador", [
        "id_goleador", "anio",
        "id_seleccion", "seleccion",
        "id_jugador", "jugador",
        "goles", "partidos", "promedio"
    ], out_gle, modo)
    print(f"    [goleador]          {n} filas")

    # ── 7. POSICION_FINAL ────────────────────────────────────────────────────
    filas_pf = leer_csv(os.path.join(dir_anio, "posiciones_finales.csv"))
    out_pf   = []
    for r in filas_pf:
        id_pf = contadores.sig_posicion_final()
        pais  = (r.get("seleccion") or "").strip()
        out_pf.append({
            "id_posicion_final": id_pf,
            "anio":              anio,
            "posicion":          _to_int(r.get("posicion")),
            "id_seleccion":      _sid(pais),
            "seleccion":         pais,
        })
    n = escribir_csv("posicion_final", [
        "id_posicion_final", "anio", "posicion", "id_seleccion", "seleccion"
    ], out_pf, modo)
    print(f"    [posicion_final]    {n} filas")

    # ── 8. PREMIO ────────────────────────────────────────────────────────────
    filas_pr = leer_csv(os.path.join(dir_anio, "premios.csv"))
    out_pr   = []
    for r in filas_pr:
        tipo_nombre = (r.get("tipo_premio") or "").strip()
        id_tp       = tp_map.get(tipo_nombre)
        jugador     = (r.get("jugador") or "").strip()
        pais        = (r.get("seleccion") or "").strip()

        if not tipo_nombre:
            continue

        id_pre = contadores.sig_premio()
        out_pr.append({
            "id_premio":      id_pre,
            "anio":           anio,
            "id_tipo_premio": id_tp,
            "tipo_premio":    tipo_nombre,
            "id_jugador":     _jug(jugador),
            "jugador":        jugador,
            "id_seleccion":   _sid(pais),
            "seleccion":      pais,
        })
    n = escribir_csv("premio", [
        "id_premio", "anio", "id_tipo_premio", "tipo_premio",
        "id_jugador", "jugador", "id_seleccion", "seleccion"
    ], out_pr, modo)
    print(f"    [premio]            {n} filas")

    # ── 9. EQUIPO_IDEAL ──────────────────────────────────────────────────────
    filas_ei = leer_csv(os.path.join(dir_anio, "equipo_ideal.csv"))
    out_ei   = []
    for r in filas_ei:
        id_ei   = contadores.sig_equipo_ideal()
        jugador = (r.get("jugador") or "").strip()
        pais    = (r.get("seleccion") or "").strip()
        out_ei.append({
            "id_equipo_ideal": id_ei,
            "anio":            anio,
            "posicion":        (r.get("posicion") or "").strip(),
            "id_jugador":      _jug(jugador),
            "jugador":         jugador,
            "id_seleccion":    _sid(pais),
            "seleccion":       pais,
        })
    n = escribir_csv("equipo_ideal", [
        "id_equipo_ideal", "anio", "posicion",
        "id_jugador", "jugador", "id_seleccion", "seleccion"
    ], out_ei, modo)
    print(f"    [equipo_ideal]      {n} filas")

    # ── 10. TARJETA ──────────────────────────────────────────────────────────
    filas_t = leer_csv(os.path.join(dir_anio, "tarjetas.csv"))
    out_t   = []
    for r in filas_t:
        id_t    = contadores.sig_tarjeta()
        jugador = (r.get("jugador") or "").strip()
        pais    = (r.get("seleccion") or "").strip()
        out_t.append({
            "id_tarjeta":   id_t,
            "anio":         anio,
            "id_seleccion": _sid(pais),
            "seleccion":    pais,
            "id_jugador":   _jug(jugador),
            "jugador":      jugador,
            "amarillas":    _to_int(r.get("amarillas")) or 0,
            "rojas":        _to_int(r.get("rojas")) or 0,
        })
    n = escribir_csv("tarjeta", [
        "id_tarjeta", "anio",
        "id_seleccion", "seleccion",
        "id_jugador", "jugador",
        "amarillas", "rojas"
    ], out_t, modo)
    print(f"    [tarjeta]           {n} filas")


# ─── Inicializar archivos de salida (encabezados) ─────────────────────────────

def inicializar_archivos_normalizados(sel_rows, jug_rows, tp_rows):
    """
    Crea data/normalizado/ y escribe los archivos con solo los encabezados
    (o con datos fijos para seleccion, jugador_pais, tipo_premio).
    Esto garantiza que el modo 'a' funcione desde la primera iteración.
    """
    os.makedirs(NORM_DIR, exist_ok=True)

    # Tablas maestras con datos fijos — se escriben completas de una vez
    escribir_csv("seleccion",   ["id_seleccion", "nombre"],
                 sel_rows, "w")
    print(f"  [seleccion]         {len(sel_rows)} filas escritas")

    escribir_csv("jugador_pais",
                 ["id_jugador", "nombre", "id_seleccion", "seleccion"],
                 jug_rows, "w")
    print(f"  [jugador_pais]      {len(jug_rows)} filas escritas")

    escribir_csv("tipo_premio",  ["id_tipo_premio", "nombre"],
                 tp_rows, "w")
    print(f"  [tipo_premio]       {len(tp_rows)} filas escritas")

    # Tablas con IDs incrementales — solo escribir encabezado ahora
    tablas_incrementales = {
        "mundial":          ["anio", "id_organizador", "organizador",
                             "id_campeon", "campeon",
                             "num_selecciones", "num_partidos", "goles", "promedio_gol"],
        "grupo":            ["anio", "id_grupo", "selecciones"],
        "partido":          ["id_partido", "anio", "num_partido", "fecha", "etapa",
                             "id_local", "local", "id_visitante", "visitante",
                             "goles_local", "goles_visitante",
                             "tiempo_extra", "penales", "penales_local", "penales_visitante"],
        "posicion_grupo":   ["id_posicion_grupo", "anio", "id_grupo",
                             "id_seleccion", "seleccion",
                             "pts", "pj", "pg", "pe", "pp", "gf", "gc",
                             "diferencia", "clasificado"],
        "gol":              ["id_gol", "id_partido", "anio",
                             "id_seleccion", "equipo",
                             "id_jugador", "jugador",
                             "minuto", "es_penal", "es_autogol"],
        "goleador":         ["id_goleador", "anio",
                             "id_seleccion", "seleccion",
                             "id_jugador", "jugador",
                             "goles", "partidos", "promedio"],
        "posicion_final":   ["id_posicion_final", "anio", "posicion",
                             "id_seleccion", "seleccion"],
        "premio":           ["id_premio", "anio", "id_tipo_premio", "tipo_premio",
                             "id_jugador", "jugador", "id_seleccion", "seleccion"],
        "equipo_ideal":     ["id_equipo_ideal", "anio", "posicion",
                             "id_jugador", "jugador", "id_seleccion", "seleccion"],
        "tarjeta":          ["id_tarjeta", "anio",
                             "id_seleccion", "seleccion",
                             "id_jugador", "jugador",
                             "amarillas", "rojas"],
    }
    for nombre, campos in tablas_incrementales.items():
        escribir_csv(nombre, campos, [], "w")


# ─── Resumen final ────────────────────────────────────────────────────────────

def imprimir_resumen():
    print(f"\n{'='*60}")
    print(f"  NORMALIZACIÓN COMPLETADA")
    print(f"  Archivos en: {NORM_DIR}/")
    print(f"{'='*60}")
    for arch in sorted(os.listdir(NORM_DIR)):
        if not arch.endswith(".csv"):
            continue
        with open(os.path.join(NORM_DIR, arch), encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1   # -1 por el encabezado
        print(f"  {arch:<35} {n:>6} filas")


def detectar_anios_data():
    """Detecta años disponibles en data/ (excluye la carpeta 'normalizado')."""
    if not os.path.exists(DATA_DIR):
        return []
    return sorted([
        int(c) for c in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, c))
        and c.isdigit()
    ])


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  NORMALIZACIÓN DE DATOS DE MUNDIALES")
    print(f"{'='*60}")

    # Detectar años
    if len(sys.argv) > 1:
        anios = [int(a) for a in sys.argv[1:]]
    else:
        anios = detectar_anios_data()

    if not anios:
        print("No se encontraron años en data/. Ejecuta primero parserFinal.py")
        sys.exit(1)

    print(f"  Años a normalizar: {anios}")

    # Cargar tablas maestras (IDs fijos)
    print(f"\n  Cargando tablas maestras...")
    sel_map, sel_rows = cargar_selecciones()
    jug_rows, jug_map = cargar_jugadores()
    tp_map, tp_rows   = cargar_tipos_premio()

    # Inicializar archivos de salida
    print(f"\n  Inicializando archivos de salida...")
    inicializar_archivos_normalizados(sel_rows, jug_rows, tp_rows)

    # Contadores globales — una única instancia para todos los años
    contadores  = Contadores()
    partido_map = {}   # (anio, id_partido_str) → id_partido — se llena durante el proceso

    # Procesar cada año
    for anio in anios:
        normalizar_anio(anio, sel_map, jug_map, tp_map, contadores, partido_map)

    # Resumen
    imprimir_resumen()