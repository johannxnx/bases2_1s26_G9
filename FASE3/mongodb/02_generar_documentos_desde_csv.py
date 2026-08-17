"""
Genera los documentos MongoDB del proyecto a partir de los CSV consolidados.

Salida:
- mongodb/json_generado/selecciones.json
- mongodb/json_generado/jugadores.json
- mongodb/json_generado/mundiales.json

Uso basico:
    python 02_generar_documentos_desde_csv.py

Uso con insercion directa en MongoDB:
    python 02_generar_documentos_desde_csv.py --mongo-uri mongodb://localhost:27017/ --db mundiales_futbol

Notas:
- El script usa solo librerias estandar para transformar CSV a JSON.
- La insercion directa es opcional y requiere `pymongo`.
"""

# Permite usar referencias de tipos como list[dict[str, Any]] aun si la version
# de Python del entorno no evaluara inmediatamente esos tipos.
from __future__ import annotations

# argparse: permite recibir parametros desde linea de comandos.
import argparse
# csv: se usa para leer los archivos fuente del proyecto.
import csv
# json: se usa para exportar los documentos finales.
import json
# defaultdict: facilita agrupar datos por llave sin validar si existen antes.
from collections import defaultdict
# Path: permite construir rutas de forma segura e independiente del sistema.
from pathlib import Path
# Any: se usa para anotar funciones que aceptan varios tipos de valor.
from typing import Any


# ROOT_DIR apunta a la carpeta FASE3.
# __file__ es este archivo, parents[1] sube dos niveles:
# mongodb/02_generar_documentos_desde_csv.py -> FASE3
ROOT_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR apunta a la carpeta donde estan los CSV consolidados.
DATA_DIR = ROOT_DIR / "data" / "carga de datos"
# OUTPUT_DIR es donde se escribiran los JSON ya transformados al modelo MongoDB.
OUTPUT_DIR = Path(__file__).resolve().parent / "json_generado"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """
    Lee un archivo CSV y devuelve una lista de diccionarios.

    Cada fila queda como:
        {"columna1": "valor1", "columna2": "valor2", ...}

    Se prueban varias codificaciones porque muchos CSV generados en Windows
    pueden venir en utf-8, utf-8-sig, cp1252 o latin-1.
    """
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            # Se abre el archivo con la codificacion actual.
            with path.open("r", encoding=encoding, newline="") as handle:
                # DictReader usa la primera fila como nombres de columnas.
                reader = csv.DictReader(handle)
                # Convierte el iterador en una lista completa de filas.
                return [dict(row) for row in reader]
        except UnicodeDecodeError:
            # Si la codificacion falla, se intenta con la siguiente.
            continue
    # Si ninguna codificacion funciono, se lanza un error.
    raise UnicodeDecodeError("csv", b"", 0, 1, f"No se pudo leer {path}")


def clean_text(value: Any) -> str | None:
    """
    Limpia un valor textual:
    - convierte a string
    - elimina espacios extra al inicio y al final
    - devuelve None si queda vacio
    """
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def parse_int(value: Any) -> int | None:
    """
    Convierte un valor a entero.

    Se usa int(float(...)) para soportar casos como "6.0" en los CSV.
    Si el valor esta vacio o no se puede convertir, devuelve None.
    """
    text = clean_text(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    """
    Convierte un valor a flotante.
    Si el valor esta vacio o no se puede convertir, devuelve None.
    """
    text = clean_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_yes_no(value: Any) -> bool | None:
    """
    Convierte valores tipo SI/NO a booleanos.

    Ejemplos:
    - "SI" -> True
    - "NO" -> False
    - "" -> None
    """
    text = clean_text(value)
    if text is None:
        return None
    normalized = text.upper()
    if normalized in {"SI", "SÍ", "YES", "TRUE"}:
        return True
    if normalized in {"NO", "FALSE"}:
        return False
    return None


def split_group_selections(value: Any) -> list[str]:
    """
    Convierte una cadena como:
        "Argentina, Chile, Francia, México"
    en:
        ["Argentina", "Chile", "Francia", "México"]
    """
    text = clean_text(value)
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def write_json(path: Path, data: list[dict[str, Any]]) -> None:
    """
    Escribe una lista de documentos en formato JSON legible.
    Crea la carpeta si no existe.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        # ensure_ascii=False conserva tildes y caracteres especiales.
        # indent=2 hace el archivo legible para revision manual.
        json.dump(data, handle, ensure_ascii=False, indent=2)


def sort_participaciones(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena participaciones de jugador por anio y luego por camiseta."""
    return sorted(items, key=lambda item: (item.get("anio") or 0, item.get("camiseta") or ""))


def sort_by_year(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena una lista de objetos usando el campo 'anio'."""
    return sorted(items, key=lambda item: item.get("anio") or 0)


def load_source_data() -> dict[str, list[dict[str, str]]]:
    """
    Define todos los archivos fuente que alimentan el modelo documental
    y los carga en memoria.
    """
    files = {
        "seleccion": DATA_DIR / "seleccion.csv",
        "jugadores": DATA_DIR / "jugadores_completos_final.csv",
        "detalle_jugadores": DATA_DIR / "detalles_jugadores_final.csv",
        "mundial": DATA_DIR / "mundial.csv",
        "grupo": DATA_DIR / "grupo.csv",
        "posicion_grupo": DATA_DIR / "posicion_grupo.csv",
        "posicion_final": DATA_DIR / "posicion_final.csv",
        "partido": DATA_DIR / "partido.csv",
        "gol": DATA_DIR / "gol.csv",
        "goleador": DATA_DIR / "goleador.csv",
        "premio": DATA_DIR / "premio.csv",
        "tipo_premio": DATA_DIR / "tipo_premio.csv",
        "equipo_ideal": DATA_DIR / "equipo_ideal.csv",
        "tarjeta": DATA_DIR / "tarjeta.csv",
    }
    # Devuelve un diccionario donde cada llave representa un dataset fuente.
    return {name: read_csv_rows(path) for name, path in files.items()}


def build_lookups(data: dict[str, list[dict[str, str]]]) -> dict[str, dict[Any, Any]]:
    """
    Construye diccionarios auxiliares para buscar rapidamente nombres por ID.

    Esto evita recorrer listas completas cada vez que necesitamos:
    - nombre de una seleccion por id
    - nombre de un jugador por id
    - nombre del tipo de premio por id
    """
    selection_by_id: dict[int, str] = {}
    player_by_id: dict[int, dict[str, Any]] = {}
    prize_type_by_id: dict[int, str] = {}

    # Catalogo de selecciones por id.
    for row in data["seleccion"]:
        id_seleccion = parse_int(row.get("id_seleccion"))
        if id_seleccion is not None:
            selection_by_id[id_seleccion] = clean_text(row.get("nombre")) or ""

    # Catalogo de jugadores por id, guardando nombre y seleccion base.
    for row in data["jugadores"]:
        id_jugador = parse_int(row.get("id_jugador"))
        if id_jugador is not None:
            player_by_id[id_jugador] = {
                "nombre": clean_text(row.get("nombre")),
                "id_seleccion": parse_int(row.get("id_seleccion")),
            }

    # Catalogo de tipos de premio por id.
    for row in data["tipo_premio"]:
        id_tipo = parse_int(row.get("id_tipo_premio"))
        if id_tipo is not None:
            prize_type_by_id[id_tipo] = clean_text(row.get("nombre")) or ""

    return {
        "selection_by_id": selection_by_id,
        "player_by_id": player_by_id,
        "prize_type_by_id": prize_type_by_id,
    }


def build_selecciones(
    data: dict[str, list[dict[str, str]]], lookups: dict[str, dict[Any, Any]]
) -> list[dict[str, Any]]:
    """
    Construye la coleccion 'selecciones'.

    Ademas de id y nombre, calcula:
    - participaciones: anios donde jugo partidos
    - sedes: anios donde fue organizador
    - campeonatos: anios donde salio campeon
    """
    selection_by_id = lookups["selection_by_id"]
    # Sets para evitar duplicados naturales.
    participaciones: dict[int, set[int]] = defaultdict(set)
    sedes: dict[int, set[int]] = defaultdict(set)
    campeonatos: dict[int, set[int]] = defaultdict(set)

    # Se recorren los partidos para saber en que anios participo cada seleccion.
    for row in data["partido"]:
        anio = parse_int(row.get("anio"))
        id_local = parse_int(row.get("id_local"))
        id_visitante = parse_int(row.get("id_visitante"))
        if anio is not None and id_local is not None:
            participaciones[id_local].add(anio)
        if anio is not None and id_visitante is not None:
            participaciones[id_visitante].add(anio)

    # Se recorre el archivo mundial para detectar sedes y campeones.
    for row in data["mundial"]:
        anio = parse_int(row.get("anio"))
        organizador = parse_int(row.get("id_organizador"))
        campeon = parse_int(row.get("id_campeon"))
        if anio is not None and organizador is not None:
            sedes[organizador].add(anio)
        if anio is not None and campeon is not None:
            campeonatos[campeon].add(anio)

    documents: list[dict[str, Any]] = []
    for row in data["seleccion"]:
        id_seleccion = parse_int(row.get("id_seleccion"))
        if id_seleccion is None:
            continue
        # Se convierten los sets en listas ordenadas para guardar el documento.
        anios_participacion = sorted(participaciones.get(id_seleccion, set()))
        anios_sede = sorted(sedes.get(id_seleccion, set()))
        anios_campeon = sorted(campeonatos.get(id_seleccion, set()))

        # Se arma el documento final de la coleccion.
        documents.append(
            {
                "id_seleccion": id_seleccion,
                "nombre": clean_text(row.get("nombre")),
                "participaciones": anios_participacion,
                "sedes": anios_sede,
                "total_participaciones": len(anios_participacion),
                "fue_campeon": len(anios_campeon) > 0,
                "anios_campeon": anios_campeon,
            }
        )

    # Se devuelve la lista ordenada por id para tener salida consistente.
    return sorted(documents, key=lambda item: item["id_seleccion"])


def build_jugadores(
    data: dict[str, list[dict[str, str]]], lookups: dict[str, dict[Any, Any]]
) -> list[dict[str, Any]]:
    """
    Construye la coleccion 'jugadores'.

    La informacion se toma de:
    - jugadores_completos_final.csv para datos generales
    - detalles_jugadores_final.csv para participaciones por mundial
    """
    selection_by_id = lookups["selection_by_id"]
    # Agrupa las participaciones por id de jugador.
    details_by_player: dict[int, list[dict[str, Any]]] = defaultdict(list)

    # Primero se cargan los detalles por anio en la estructura auxiliar.
    for row in data["detalle_jugadores"]:
        id_jugador = parse_int(row.get("id_jugador"))
        if id_jugador is None:
            continue
        details_by_player[id_jugador].append(
            {
                "anio": parse_int(row.get("anio")),
                "camiseta": clean_text(row.get("camiseta")),
                "posicion": clean_text(row.get("posicion")),
                "jugo": parse_int(row.get("jugo")),
                "jugo_titular": parse_int(row.get("jugo_titular")),
                "capitan": parse_int(row.get("capitan")),
                "no_jugo": parse_int(row.get("no_jugo")),
                "goles": parse_int(row.get("goles")),
                "prom_goles": parse_float(row.get("prom_goles")),
                "tarjeta_amarilla": parse_int(row.get("tarjeta_amarilla")),
                "tarjeta_roja": parse_int(row.get("tarjeta_roja")),
                "pg": parse_int(row.get("pg")),
                "pe": parse_int(row.get("pe")),
                "pp": parse_int(row.get("pp")),
                "pos_final": parse_int(row.get("pos_final")),
            }
        )

    documents: list[dict[str, Any]] = []
    # Luego se recorre el archivo maestro de jugadores.
    for row in data["jugadores"]:
        id_jugador = parse_int(row.get("id_jugador"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if id_jugador is None or id_seleccion is None:
            continue

        # Se arma un documento por jugador, embebiendo sus participaciones.
        documents.append(
            {
                "id_jugador": id_jugador,
                "nombre": clean_text(row.get("nombre")),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion, ""),
                "altura": clean_text(row.get("altura")),
                "fecha_nacimiento": clean_text(row.get("fecha_nacimiento")),
                "nacionalidad": clean_text(row.get("nacionalidad")),
                "participaciones": sort_participaciones(details_by_player.get(id_jugador, [])),
            }
        )

    return sorted(documents, key=lambda item: item["id_jugador"])


def build_mundiales(
    data: dict[str, list[dict[str, str]]], lookups: dict[str, dict[Any, Any]]
) -> list[dict[str, Any]]:
    """
    Construye la coleccion principal 'mundiales'.

    Cada documento representa un mundial completo e incluye arreglos embebidos:
    - grupos
    - posiciones_grupo
    - posiciones_finales
    - partidos
    - goles_detalle
    - goleadores
    - premios
    - equipo_ideal
    - tarjetas
    """
    selection_by_id = lookups["selection_by_id"]
    player_by_id = lookups["player_by_id"]
    prize_type_by_id = lookups["prize_type_by_id"]

    # Aqui se iran guardando los documentos por anio.
    mundial_docs: dict[int, dict[str, Any]] = {}
    # Este lookup permite encontrar rapidamente un partido por id
    # para luego insertarle sus goles.
    partidos_por_id: dict[int, dict[str, Any]] = {}

    # Paso 1: crear la estructura base de cada mundial.
    for row in data["mundial"]:
        anio = parse_int(row.get("anio"))
        id_organizador = parse_int(row.get("id_organizador"))
        id_campeon = parse_int(row.get("id_campeon"))
        if anio is None or id_organizador is None or id_campeon is None:
            continue

        mundial_docs[anio] = {
            "anio": anio,
            "organizador": {
                "id_seleccion": id_organizador,
                "nombre": clean_text(row.get("organizador")) or selection_by_id.get(id_organizador, ""),
            },
            "campeon": {
                "id_seleccion": id_campeon,
                "nombre": clean_text(row.get("campeon")) or selection_by_id.get(id_campeon, ""),
            },
            "num_selecciones": parse_int(row.get("num_selecciones")),
            "num_partidos": parse_int(row.get("num_partidos")),
            "goles": parse_int(row.get("goles")),
            "promedio_gol": parse_float(row.get("promedio_gol")),
            "grupos": [],
            "posiciones_grupo": [],
            "posiciones_finales": [],
            "partidos": [],
            "goleadores": [],
            "premios": [],
            "equipo_ideal": [],
            "tarjetas": [],
        }

    # Paso 2: agregar grupos a cada mundial.
    for row in data["grupo"]:
        anio = parse_int(row.get("anio"))
        if anio not in mundial_docs:
            continue
        mundial_docs[anio]["grupos"].append(
            {
                "id_grupo": clean_text(row.get("id_grupo")),
                "selecciones": split_group_selections(row.get("selecciones")),
            }
        )

    # Paso 3: agregar posiciones de grupo.
    for row in data["posicion_grupo"]:
        anio = parse_int(row.get("anio"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs or id_seleccion is None:
            continue
        mundial_docs[anio]["posiciones_grupo"].append(
            {
                "id_grupo": clean_text(row.get("id_grupo")),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion),
                "pts": parse_int(row.get("pts")),
                "pj": parse_int(row.get("pj")),
                "pg": parse_int(row.get("pg")),
                "pe": parse_int(row.get("pe")),
                "pp": parse_int(row.get("pp")),
                "gf": parse_int(row.get("gf")),
                "gc": parse_int(row.get("gc")),
                "diferencia": parse_int(row.get("diferencia")),
                "clasificado": clean_text(row.get("clasificado")),
            }
        )

    # Paso 4: agregar posiciones finales.
    for row in data["posicion_final"]:
        anio = parse_int(row.get("anio"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs or id_seleccion is None:
            continue
        mundial_docs[anio]["posiciones_finales"].append(
            {
                "posicion": parse_int(row.get("posicion")),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion),
            }
        )

    # Paso 5: agregar partidos y construir el indice partidos_por_id.
    for row in data["partido"]:
        anio = parse_int(row.get("anio"))
        id_partido = parse_int(row.get("id_partido"))
        id_local = parse_int(row.get("id_local"))
        id_visitante = parse_int(row.get("id_visitante"))
        if anio not in mundial_docs or id_partido is None or id_local is None or id_visitante is None:
            continue

        partido_doc = {
            "id_partido": id_partido,
            "num_partido": parse_int(row.get("num_partido")),
            "fecha": clean_text(row.get("fecha")),
            "etapa": clean_text(row.get("etapa")),
            "local": {
                "id_seleccion": id_local,
                "nombre": clean_text(row.get("local")) or selection_by_id.get(id_local, ""),
                "goles": parse_int(row.get("goles_local")),
            },
            "visitante": {
                "id_seleccion": id_visitante,
                "nombre": clean_text(row.get("visitante")) or selection_by_id.get(id_visitante, ""),
                "goles": parse_int(row.get("goles_visitante")),
            },
            "tiempo_extra": clean_text(row.get("tiempo_extra")),
            "penales": clean_text(row.get("penales")),
            "penales_local": parse_int(row.get("penales_local")),
            "penales_visitante": parse_int(row.get("penales_visitante")),
            "goles_detalle": [],
        }
        mundial_docs[anio]["partidos"].append(partido_doc)
        partidos_por_id[id_partido] = partido_doc

    # Paso 6: insertar goles dentro del partido correspondiente.
    for row in data["gol"]:
        id_partido = parse_int(row.get("id_partido"))
        id_gol = parse_int(row.get("id_gol"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        id_jugador = parse_int(row.get("id_jugador"))
        if id_partido not in partidos_por_id or id_gol is None:
            continue
        player_info = player_by_id.get(id_jugador, {}) if id_jugador is not None else {}
        partidos_por_id[id_partido]["goles_detalle"].append(
            {
                "id_gol": id_gol,
                "minuto": parse_int(row.get("minuto")),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion) if id_seleccion is not None else None,
                "id_jugador": id_jugador,
                "jugador": player_info.get("nombre"),
                "es_penal": parse_yes_no(row.get("es_penal")),
                "es_autogol": parse_yes_no(row.get("es_autogol")),
            }
        )

    # Paso 7: agregar goleadores por mundial.
    for row in data["goleador"]:
        anio = parse_int(row.get("anio"))
        id_jugador = parse_int(row.get("id_jugador"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs:
            continue
        player_info = player_by_id.get(id_jugador, {}) if id_jugador is not None else {}
        mundial_docs[anio]["goleadores"].append(
            {
                "id_jugador": id_jugador,
                "jugador": player_info.get("nombre"),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion) if id_seleccion is not None else None,
                "goles": parse_int(row.get("goles")),
                "partidos": parse_int(row.get("partidos")),
                "promedio": parse_float(row.get("promedio")),
            }
        )

    # Paso 8: agregar premios por mundial.
    for row in data["premio"]:
        anio = parse_int(row.get("anio"))
        id_tipo = parse_int(row.get("id_tipo_premio"))
        id_jugador = parse_int(row.get("id_jugador"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs:
            continue
        player_info = player_by_id.get(id_jugador, {}) if id_jugador is not None else {}
        mundial_docs[anio]["premios"].append(
            {
                "id_tipo_premio": id_tipo,
                "premio": prize_type_by_id.get(id_tipo),
                "id_jugador": id_jugador,
                "jugador": player_info.get("nombre"),
                "id_seleccion": id_seleccion,
                "seleccion": selection_by_id.get(id_seleccion) if id_seleccion is not None else None,
            }
        )

    # Paso 9: agregar equipo ideal.
    for row in data["equipo_ideal"]:
        anio = parse_int(row.get("anio"))
        id_jugador = parse_int(row.get("id_jugador"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs:
            continue
        mundial_docs[anio]["equipo_ideal"].append(
            {
                "posicion": clean_text(row.get("posicion")),
                "id_jugador": id_jugador,
                "jugador": clean_text(row.get("jugador")),
                "id_seleccion": id_seleccion,
                "seleccion": clean_text(row.get("seleccion")) or selection_by_id.get(id_seleccion) if id_seleccion is not None else None,
            }
        )

    # Paso 10: agregar tarjetas por mundial.
    for row in data["tarjeta"]:
        anio = parse_int(row.get("anio"))
        id_jugador = parse_int(row.get("id_jugador"))
        id_seleccion = parse_int(row.get("id_seleccion"))
        if anio not in mundial_docs:
            continue
        mundial_docs[anio]["tarjetas"].append(
            {
                "id_jugador": id_jugador,
                "jugador": clean_text(row.get("jugador")),
                "id_seleccion": id_seleccion,
                "seleccion": clean_text(row.get("seleccion")) or selection_by_id.get(id_seleccion) if id_seleccion is not None else None,
                "amarillas": parse_int(row.get("amarillas")),
                "rojas": parse_int(row.get("rojas")),
            }
        )

    # Paso 11: ordenar internamente cada arreglo para que los JSON salgan
    # consistentes y faciles de revisar/importar.
    documents = []
    for anio in sorted(mundial_docs):
        doc = mundial_docs[anio]
        doc["grupos"] = sorted(doc["grupos"], key=lambda item: item.get("id_grupo") or "")
        doc["posiciones_grupo"] = sorted(
            doc["posiciones_grupo"],
            key=lambda item: (item.get("id_grupo") or "", item.get("pts") is None, -(item.get("pts") or 0), item.get("seleccion") or ""),
        )
        doc["posiciones_finales"] = sorted(doc["posiciones_finales"], key=lambda item: item.get("posicion") or 0)
        doc["partidos"] = sorted(doc["partidos"], key=lambda item: item.get("num_partido") or 0)
        for partido in doc["partidos"]:
            partido["goles_detalle"] = sorted(
                partido["goles_detalle"], key=lambda item: ((item.get("minuto") or 0), item.get("id_gol") or 0)
            )
        doc["goleadores"] = sorted(doc["goleadores"], key=lambda item: (-(item.get("goles") or 0), item.get("jugador") or ""))
        doc["premios"] = sorted(doc["premios"], key=lambda item: (item.get("id_tipo_premio") or 0, item.get("jugador") or ""))
        doc["equipo_ideal"] = sorted(doc["equipo_ideal"], key=lambda item: (item.get("posicion") or "", item.get("jugador") or ""))
        doc["tarjetas"] = sorted(doc["tarjetas"], key=lambda item: (-(item.get("rojas") or 0), -(item.get("amarillas") or 0), item.get("jugador") or ""))
        documents.append(doc)

    # Devuelve la coleccion completa lista para exportar o insertar.
    return documents


def export_documents() -> dict[str, list[dict[str, Any]]]:
    """
    Orquesta la transformacion completa:
    1. carga CSV
    2. crea lookups auxiliares
    3. construye las 3 colecciones
    4. escribe los JSON finales a disco
    """
    data = load_source_data()
    lookups = build_lookups(data)

    collections = {
        "selecciones": build_selecciones(data, lookups),
        "jugadores": build_jugadores(data, lookups),
        "mundiales": build_mundiales(data, lookups),
    }

    write_json(OUTPUT_DIR / "selecciones.json", collections["selecciones"])
    write_json(OUTPUT_DIR / "jugadores.json", collections["jugadores"])
    write_json(OUTPUT_DIR / "mundiales.json", collections["mundiales"])

    return collections


def insert_into_mongodb(mongo_uri: str, db_name: str, collections: dict[str, list[dict[str, Any]]]) -> None:
    """
    Inserta los documentos generados directamente en MongoDB.

    Requiere pymongo. Antes de insertar:
    - limpia el contenido existente de cada coleccion
    - inserta todos los documentos nuevos
    """
    try:
        from pymongo import MongoClient
    except ImportError as exc:
        raise SystemExit(
            "Para insertar directo en MongoDB necesitas instalar pymongo: pip install pymongo"
        ) from exc

    client = MongoClient(mongo_uri)
    database = client[db_name]

    for name, documents in collections.items():
        database[name].delete_many({})
        if documents:
            database[name].insert_many(documents)

    print(f"Datos insertados correctamente en MongoDB: {db_name}")


def main() -> None:
    """
    Punto de entrada del script.

    Permite dos modos:
    - generar JSON solamente
    - generar JSON e insertar en MongoDB si se pasa --mongo-uri
    """
    parser = argparse.ArgumentParser(description="Genera documentos MongoDB desde CSV consolidados.")
    parser.add_argument("--mongo-uri", help="URI de MongoDB para insertar directamente los documentos.")
    parser.add_argument("--db", default="mundiales_futbol", help="Nombre de la base de datos destino.")
    args = parser.parse_args()

    # Siempre se generan primero los JSON.
    collections = export_documents()

    # Se muestra un resumen de lo generado.
    print(f"JSON generado en: {OUTPUT_DIR}")
    print(f"Selecciones: {len(collections['selecciones'])}")
    print(f"Jugadores: {len(collections['jugadores'])}")
    print(f"Mundiales: {len(collections['mundiales'])}")

    # Si el usuario proporciona URI, tambien se insertan los datos en MongoDB.
    if args.mongo_uri:
        insert_into_mongodb(args.mongo_uri, args.db, collections)


# Ejecuta main solo cuando el archivo se corre directamente.
if __name__ == "__main__":
    main()
