"""
normalizar_jugadores.py
=======================
Lee los CSVs crudos generados por ParserJugadores.py y produce dos CSVs
normalizados listos para importar a Oracle:

    data/normalizado/jugadores_completos_normalizados.csv
        → tabla JUGADOR_PAIS (columnas con IDs resueltos)

    data/normalizado/detalles_jugadores_normalizados.csv
        → tabla DETALLE_JUGADOR (columnas con IDs resueltos)

Fuentes de IDs fijos:
    scripts/jugadores_pais.csv   → ID_JUGADOR por nombre (separador ";")
    scripts/seleccion.csv        → ID_SELECCION por nombre de país

Estrategia de matching de jugadores:
    El CSV de jugadores_pais viene en formato "Apellido, Nombre" (con coma).
    Los HTMLs entregan el nombre como "Nombre Apellido" (sin coma).
    El normalizador construye un índice con múltiples variantes de cada nombre
    (con/sin coma, invertido, sin tildes) para maximizar los matches.

Uso:
    python scripts/normalizar_jugadores.py

Los archivos de entrada se esperan en:
    data/jugadores_completo.csv
    data/detalle_jugadorM.csv
"""

import os
import sys
import csv
import re
import unicodedata

# ─── Rutas ────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR   = os.path.dirname(_SCRIPT_DIR)

DATA_DIR  = os.path.join(_BASE_DIR, "data")
NORM_DIR  = os.path.join(DATA_DIR, "normalizado")

# Archivos de entrada (CSVs crudos)
RUTA_JUG_CRUDO = os.path.join(DATA_DIR, "jugadores_completo.csv")
RUTA_DET_CRUDO = os.path.join(DATA_DIR, "detalle_jugadorM.csv")

# Archivos de salida (normalizados)
RUTA_JUG_NORM = os.path.join(NORM_DIR, "jugadores_completos_normalizados.csv")
RUTA_DET_NORM = os.path.join(NORM_DIR, "detalles_jugadores_normalizados.csv")

# Archivos de referencia con IDs fijos
RUTA_JUG_REF = os.path.join(_SCRIPT_DIR, "jugadores_pais.csv")
RUTA_SEL_REF = os.path.join(_SCRIPT_DIR, "seleccion.csv")

# Columnas de salida — reflejan exactamente las tablas Oracle
COL_JUG_NORM = [
    "id_jugador", "nombre", "id_seleccion", "seleccion",
    "altura", "fecha_nacimiento", "nacionalidad",
]

COL_DET_NORM = [
    "id_jugador", "nombre", "anio", "camiseta", "posicion",
    "jugo", "jugo_titular", "capitan", "no_jugo",
    "goles", "prom_goles", "tarjeta_amarilla", "tarjeta_roja",
    "pg", "pe", "pp", "pos_final",
]


# ─── Normalización de texto para matching ─────────────────────────────────────

def _norm_str(s):
    """
    Normaliza un string para matching:
    - minúsculas
    - sin acentos (preserva ñ porque se reconstruye con NFC)
    - sin espacios extra
    """
    if not s:
        return ""
    s = s.strip().lower()
    nfd = unicodedata.normalize("NFD", s)
    resultado = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", resultado)


def _variantes(nombre):
    """
    Genera todas las variantes de matching de un nombre.
    Entrada puede ser:
        "Messi, Lionel"   → con coma (formato jugadores_pais.csv)
        "Lionel Messi"    → sin coma (formato HTML)
        "Messi"           → solo apellido
    Retorna lista de strings, todos en minúsculas normalizadas.
    """
    variantes = set()
    nombre = nombre.strip()
    if not nombre:
        return variantes

    # Versión original (minúsculas)
    variantes.add(nombre.lower())
    variantes.add(_norm_str(nombre))

    if "," in nombre:
        # "Apellido, Nombre"
        partes    = nombre.split(",", 1)
        apellido  = partes[0].strip()
        pnombre   = partes[1].strip()

        # "Nombre Apellido" (sin coma)
        inv = f"{pnombre} {apellido}"
        variantes.add(inv.lower())
        variantes.add(_norm_str(inv))

        # "Apellido Nombre" (sin coma, sin invertir)
        sin_coma = f"{apellido} {pnombre}"
        variantes.add(sin_coma.lower())
        variantes.add(_norm_str(sin_coma))

        # Solo apellido
        variantes.add(apellido.lower())
        variantes.add(_norm_str(apellido))
    else:
        # "Nombre Apellido" o nombre único
        # Intentar crear "Apellido, Nombre"
        partes = nombre.rsplit(" ", 1)
        if len(partes) == 2:
            con_coma = f"{partes[1]}, {partes[0]}"
            variantes.add(con_coma.lower())
            variantes.add(_norm_str(con_coma))
        # Solo la última palabra (apellido)
        variantes.add(nombre.split()[-1].lower())
        variantes.add(_norm_str(nombre.split()[-1]))

    return variantes


# ─── Carga de tablas de referencia (IDs fijos) ───────────────────────────────

def _leer_csv(ruta, sep=","):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=sep))


def cargar_selecciones():
    """
    Carga scripts/seleccion.csv.
    Retorna dict nombre_pais → id_seleccion.
    """
    filas = _leer_csv(RUTA_SEL_REF)
    if not filas:
        print(f"  [ERROR] No se encontró {RUTA_SEL_REF}")
        sys.exit(1)

    sel_map = {}
    primera = filas[0]
    if "id_seleccion" in primera:
        for r in filas:
            nombre = (r.get("nombre") or "").strip()
            if nombre:
                sel_map[nombre] = int(r["id_seleccion"])
    else:
        nombres = sorted(set(
            (r.get("nombre") or r.get("seleccion") or "").strip()
            for r in filas
        ))
        for i, n in enumerate(nombres, 1):
            if n:
                sel_map[n] = i

    print(f"  [seleccion]      {len(sel_map)} países cargados")
    return sel_map


def cargar_jugadores_ref():
    """
    Carga scripts/jugadores_pais.csv (separador ";").
    Retorna:
        jug_ref   → lista de dicts con id_jugador, nombre, id_seleccion, seleccion
        jug_index → dict variante_nombre → id_jugador  (para matching)
    """
    # Detectar separador
    if not os.path.exists(RUTA_JUG_REF):
        print(f"  [ADVERTENCIA] No se encontró {RUTA_JUG_REF}")
        return [], {}

    with open(RUTA_JUG_REF, encoding="utf-8") as f:
        primera_linea = f.readline()
        sep = ";" if ";" in primera_linea else ","
        f.seek(0)
        filas = list(csv.DictReader(f, delimiter=sep))

    jug_ref   = []
    jug_index = {}   # variante_nombre → id_jugador

    for r in filas:
        id_j  = (r.get("ID JUGADOR") or r.get("id_jugador") or r.get("ID_JUGADOR") or "").strip()
        nom   = (r.get("NOMBRE")     or r.get("nombre") or "").strip()
        id_s  = (r.get("ID SELECCION") or r.get("id_seleccion") or r.get("ID_SELECCION") or "").strip()
        sel   = (r.get("SELECCION")  or r.get("seleccion") or "").strip()

        if not id_j or not nom:
            continue

        id_j_int = int(id_j)
        jug_ref.append({
            "id_jugador":   id_j_int,
            "nombre":       nom,
            "id_seleccion": int(id_s) if id_s.isdigit() else None,
            "seleccion":    sel,
        })

        # Indexar todas las variantes del nombre
        for v in _variantes(nom):
            if v:
                jug_index[v] = id_j_int

    print(f"  [jugadores_ref]  {len(jug_ref)} jugadores cargados, {len(jug_index)} variantes indexadas")
    return jug_ref, jug_index


def buscar_id_jugador(nombre, jug_index):
    """
    Busca el ID de un jugador por nombre en el índice.
    Prueba múltiples variantes. Retorna int o None.
    """
    if not nombre:
        return None
    for v in _variantes(nombre):
        if v and v in jug_index:
            return jug_index[v]
    return None


def _to_int_o_none(val):
    if val is None or str(val).strip() in ("", "-", "0.00"):
        return None
    try:
        return int(str(val).strip().split(".")[0])
    except ValueError:
        return None


def _to_float_o_none(val):
    if val is None or str(val).strip() in ("", "-"):
        return None
    try:
        return float(str(val).strip().replace(",", "."))
    except ValueError:
        return None


# ─── Normalizar jugadores_completo.csv → JUGADOR_PAIS ─────────────────────────

def normalizar_jugadores(sel_map, jug_ref, jug_index):
    """
    Lee data/jugadores_completo.csv y produce jugadores_completos_normalizados.csv.

    Estrategia de IDs:
      - Si el jugador existe en jugadores_pais.csv → usa ese ID_JUGADOR
      - Si NO existe → asigna un ID nuevo (máx existente + 1) y lo reporta
        para que el usuario lo agregue al CSV de referencia si lo desea.

    La columna SELECCION del CSV de referencia es la principal para
    ID_SELECCION. Si no está en el mapa de selecciones, queda NULL.
    """
    filas_crudas = _leer_csv(RUTA_JUG_CRUDO)
    if not filas_crudas:
        print(f"  [ADVERTENCIA] {RUTA_JUG_CRUDO} vacío o no encontrado")
        return 0

    # ID máximo actual para asignar IDs nuevos si hace falta
    id_max = max((r["id_jugador"] for r in jug_ref), default=0)

    # Mapa nombre_normalizado → fila de referencia (para no duplicar en salida)
    jug_ref_dict = {r["id_jugador"]: r for r in jug_ref}

    salida      = []
    sin_match   = []

    for r in filas_crudas:
        nombre   = (r.get("jugador") or "").strip()
        seleccion = (r.get("seleccion_nacionalidad") or "").strip()

        id_jug = buscar_id_jugador(nombre, jug_index)

        if id_jug is None:
            # Jugador no encontrado en el CSV de referencia
            id_max += 1
            id_jug  = id_max
            sin_match.append(f"  [NUEVO] {nombre!r} (id asignado: {id_jug})")

        # Obtener selección de la fila de referencia si existe
        ref = jug_ref_dict.get(id_jug, {})
        sel_final = ref.get("seleccion") or seleccion
        id_sel    = (
            ref.get("id_seleccion") or
            sel_map.get(sel_final)
        )

        salida.append({
            "id_jugador":        id_jug,
            "nombre":            nombre,
            "id_seleccion":      id_sel,
            "seleccion":         sel_final,
            "altura":            (r.get("altura") or "").strip(),
            "fecha_nacimiento":  (r.get("fecha_nac") or "").strip(),
            # nacionalidad: el HTML solo expone la selección principal
            # Se puede ampliar si el sitio tuviera múltiples nacionalidades
            "nacionalidad":      sel_final,
        })

    os.makedirs(NORM_DIR, exist_ok=True)
    with open(RUTA_JUG_NORM, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COL_JUG_NORM, extrasaction="ignore")
        w.writeheader()
        w.writerows(salida)

    if sin_match:
        print(f"  [ADVERTENCIA] {len(sin_match)} jugadores sin match en jugadores_pais.csv:")
        for msg in sin_match[:20]:   # mostrar solo los primeros 20
            print(msg)
        if len(sin_match) > 20:
            print(f"  ... y {len(sin_match)-20} más")

    print(f"  [jugadores_completos_normalizados.csv]  {len(salida)} filas → {RUTA_JUG_NORM}")
    return len(salida)


# ─── Normalizar detalle_jugadorM.csv → DETALLE_JUGADOR ────────────────────────

def normalizar_detalles(jug_index):
    """
    Lee data/detalle_jugadorM.csv y produce detalles_jugadores_normalizados.csv.

    PK de DETALLE_JUGADOR es (ID_JUGADOR, ANIO) → una fila por jugador/mundial.
    Si un jugador no tiene ID conocido, id_jugador queda NULL (Oracle rechazará
    la fila por FK, así que se recomienda resolver primero los matches).
    """
    filas_crudas = _leer_csv(RUTA_DET_CRUDO)
    if not filas_crudas:
        print(f"  [ADVERTENCIA] {RUTA_DET_CRUDO} vacío o no encontrado")
        return 0

    salida = []
    pks_vistos = set()   # para evitar duplicados (id_jugador, anio)

    for r in filas_crudas:
        nombre  = (r.get("jugador") or "").strip()
        anio    = (r.get("mundial") or "").strip()

        if not nombre or not anio:
            continue

        id_jug = buscar_id_jugador(nombre, jug_index)

        # Evitar duplicados de PK
        pk = (id_jug, anio)
        if pk in pks_vistos:
            continue
        pks_vistos.add(pk)

        def _i(col):
            return _to_int_o_none(r.get(col))

        def _f(col):
            return _to_float_o_none(r.get(col))

        salida.append({
            "id_jugador":       id_jug,
            "nombre":           nombre,
            "anio":             anio,
            "camiseta":         (r.get("camiseta") or "").strip(),
            "posicion":         (r.get("posicion") or "").strip(),
            "jugo":             _i("jugo"),
            "jugo_titular":     _i("jugo_titular"),
            "capitan":          _i("capitan"),
            "no_jugo":          _i("no_jugo"),
            "goles":            _i("goles"),
            "prom_goles":       _f("prom_goles"),
            "tarjeta_amarilla": _i("tarjeta_amarilla"),
            "tarjeta_roja":     _i("tarjeta_roja"),
            "pg":               _i("pg"),
            "pe":               _i("pe"),
            "pp":               _i("pp"),
            "pos_final":        _i("pos_final"),
        })

    os.makedirs(NORM_DIR, exist_ok=True)
    with open(RUTA_DET_NORM, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COL_DET_NORM, extrasaction="ignore")
        w.writeheader()
        w.writerows(salida)

    print(f"  [detalles_jugadores_normalizados.csv]   {len(salida)} filas → {RUTA_DET_NORM}")
    return len(salida)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  NORMALIZACIÓN DE JUGADORES")
    print(f"{'='*60}\n")

    # Cargar tablas de referencia
    print("  Cargando tablas de referencia...")
    sel_map            = cargar_selecciones()
    jug_ref, jug_index = cargar_jugadores_ref()

    print("\n  Normalizando jugadores_completo.csv...")
    normalizar_jugadores(sel_map, jug_ref, jug_index)

    print("\n  Normalizando detalle_jugadorM.csv...")
    normalizar_detalles(jug_index)

    print(f"\n{'='*60}")
    print("  COMPLETADO")
    print(f"  Archivos en: {NORM_DIR}/")
    print(f"{'='*60}")