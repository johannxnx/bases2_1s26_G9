"""
Consulta toda la informacion relacionada con una seleccion o pais.

Muestra:
- datos generales de la seleccion
- anios de participacion
- si ha sido sede y en que anios
- informacion de grupo
- partidos y resultados

Soporta dos fuentes:
1. Archivos JSON locales generados previamente
2. MongoDB, si se proporciona --mongo-uri

Ejemplos:
    python 04_consultar_pais.py Uruguay
    python 04_consultar_pais.py Uruguay --anio 1930
    python 04_consultar_pais.py Uruguay --grupo 3
    python 04_consultar_pais.py Uruguay --fecha 30-Jul-1930
    python 04_consultar_pais.py Uruguay --mongo-uri mongodb://localhost:27017/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
SELECCIONES_JSON = ROOT_DIR / "json_generado" / "selecciones.json"
MUNDIALES_JSON = ROOT_DIR / "json_generado" / "mundiales.json"


def make_separator(char: str = "=", length: int = 72) -> str:
    """Crea una linea separadora para el reporte."""
    return char * length


def add_section(lineas: list[str], titulo: str) -> None:
    """Agrega una seccion con encabezado y separadores."""
    lineas.append("")
    lineas.append(make_separator("-"))
    lineas.append(titulo)
    lineas.append(make_separator("-"))


def normalize_text(value: Any) -> str:
    """Normaliza texto para comparaciones case-insensitive."""
    if value is None:
        return ""
    return str(value).strip().lower()


def load_json(path: Path) -> list[dict[str, Any]]:
    """Carga un archivo JSON y devuelve su contenido."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_data_from_json() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Carga selecciones y mundiales desde los archivos JSON locales."""
    return load_json(SELECCIONES_JSON), load_json(MUNDIALES_JSON)


def load_data_from_mongodb(mongo_uri: str, db_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Carga selecciones y mundiales desde MongoDB."""
    try:
        from pymongo import MongoClient
    except ImportError as exc:
        raise SystemExit("Para consultar desde MongoDB instala pymongo: pip install pymongo") from exc

    client = MongoClient(mongo_uri)
    database = client[db_name]
    selecciones = list(database.selecciones.find({}, {"_id": 0}))
    mundiales = list(database.mundiales.find({}, {"_id": 0}))
    return selecciones, mundiales


def find_country(selecciones: list[dict[str, Any]], pais: str) -> dict[str, Any] | None:
    """Busca una seleccion por nombre exacto normalizado."""
    target = normalize_text(pais)
    for seleccion in selecciones:
        if normalize_text(seleccion.get("nombre")) == target:
            return seleccion
    return None


def match_country_name(value: Any, pais: str) -> bool:
    """Compara un nombre cualquiera con el pais solicitado."""
    return normalize_text(value) == normalize_text(pais)


def match_group_value(value: Any, grupo: str | None) -> bool:
    """Valida si el valor de grupo coincide con el filtro enviado."""
    if not grupo:
        return True
    return normalize_text(value) == normalize_text(grupo)


def match_date_value(value: Any, fecha: str | None) -> bool:
    """Valida si la fecha coincide con el filtro enviado."""
    if not fecha:
        return True
    return normalize_text(value) == normalize_text(fecha)


def filter_mundiales_by_country(
    mundiales: list[dict[str, Any]], pais: str, anio: int | None = None
) -> list[dict[str, Any]]:
    """Devuelve los mundiales en los que la seleccion participo."""
    resultado = []
    for mundial in mundiales:
        if anio is not None and mundial.get("anio") != anio:
            continue
        for grupo in mundial.get("grupos", []):
            if any(match_country_name(nombre, pais) for nombre in grupo.get("selecciones", [])):
                resultado.append(mundial)
                break
    return resultado


def filter_groups_for_country(
    mundial: dict[str, Any], pais: str, grupo: str | None = None
) -> list[dict[str, Any]]:
    """Obtiene los grupos del mundial donde aparece la seleccion."""
    resultado = []
    for item in mundial.get("grupos", []):
        if not any(match_country_name(nombre, pais) for nombre in item.get("selecciones", [])):
            continue
        if grupo and not match_group_value(item.get("id_grupo"), grupo):
            continue
        resultado.append(item)
    return resultado


def filter_group_positions_for_country(
    mundial: dict[str, Any], pais: str, grupo: str | None = None
) -> list[dict[str, Any]]:
    """Obtiene las posiciones de grupo de la seleccion en un mundial."""
    resultado = []
    for item in mundial.get("posiciones_grupo", []):
        if not match_country_name(item.get("seleccion"), pais):
            continue
        if grupo and not match_group_value(item.get("id_grupo"), grupo):
            continue
        resultado.append(item)
    return resultado


def filter_matches_for_country(
    mundial: dict[str, Any],
    pais: str,
    grupo: str | None = None,
    fecha: str | None = None,
) -> list[dict[str, Any]]:
    """Obtiene los partidos del mundial donde juega la seleccion."""
    resultado = []
    for partido in mundial.get("partidos", []):
        local = partido.get("local", {}).get("nombre")
        visitante = partido.get("visitante", {}).get("nombre")
        if not (match_country_name(local, pais) or match_country_name(visitante, pais)):
            continue
        if grupo and f"grupo {normalize_text(grupo)}" not in normalize_text(partido.get("etapa")):
            continue
        if fecha and not match_date_value(partido.get("fecha"), fecha):
            continue
        resultado.append(partido)
    return resultado


def filter_goleadores_for_country(mundial: dict[str, Any], pais: str) -> list[dict[str, Any]]:
    """Obtiene los goleadores del mundial que pertenecen a la seleccion consultada."""
    resultado = []
    for item in mundial.get("goleadores", []):
        if match_country_name(item.get("seleccion"), pais):
            resultado.append(item)
    return resultado


def format_match(partido: dict[str, Any]) -> str:
    """Formatea una linea de partido para salida en consola."""
    local = partido.get("local", {})
    visitante = partido.get("visitante", {})
    extras = []
    if partido.get("tiempo_extra") is not None:
        extras.append(f"TE: {partido.get('tiempo_extra')}")
    if partido.get("penales") is not None:
        extras.append(f"Penales: {partido.get('penales')}")
    if partido.get("penales_local") is not None or partido.get("penales_visitante") is not None:
        extras.append(
            f"Marcador penales: {partido.get('penales_local', 0)} - {partido.get('penales_visitante', 0)}"
        )

    base = (
        f"#{partido.get('num_partido')} | {partido.get('fecha')} | {partido.get('etapa')} | "
        f"{local.get('nombre')} {local.get('goles')} - {visitante.get('goles')} {visitante.get('nombre')}"
    )
    return base + (" | " + " | ".join(extras) if extras else "")


def format_goleador(item: dict[str, Any]) -> str:
    """Formatea una linea de goleador para salida en consola."""
    return (
        f"{item.get('jugador')} | Goles: {item.get('goles')} | "
        f"Partidos: {item.get('partidos')} | Promedio: {item.get('promedio')}"
    )


def consultar_pais(
    pais: str,
    anio: int | None = None,
    grupo: str | None = None,
    fecha: str | None = None,
    mongo_uri: str | None = None,
    db_name: str = "mundiales_futbol",
) -> str:
    """
    Genera un reporte completo para un pais o seleccion.

    Parametros:
    - pais: nombre de la seleccion
    - anio: filtra a un mundial especifico
    - grupo: filtra a un grupo especifico
    - fecha: filtra partidos por fecha exacta
    - mongo_uri: si se envia, consulta desde MongoDB
    - db_name: base de datos a consultar
    """
    selecciones, mundiales = (
        load_data_from_mongodb(mongo_uri, db_name) if mongo_uri else load_data_from_json()
    )

    seleccion = find_country(selecciones, pais)
    if not seleccion:
        return f"No se encontro informacion para la seleccion '{pais}'."

    mundiales_participados = filter_mundiales_by_country(mundiales, pais, anio=anio)

    lineas: list[str] = []
    lineas.append(make_separator())
    lineas.append(f"REPORTE DE LA SELECCION: {seleccion.get('nombre')}")
    lineas.append(make_separator())
    lineas.append(f"Participaciones : {seleccion.get('total_participaciones')}")
    lineas.append(
        "Anios participacion : "
        + (", ".join(str(valor) for valor in seleccion.get("participaciones", [])) or "Ninguno")
    )
    lineas.append(
        f"Fue sede        : {'SI' if seleccion.get('sedes') else 'NO'}"
    )
    lineas.append(
        "Anios sede      : "
        + (", ".join(str(valor) for valor in seleccion.get("sedes", [])) or "Ninguno")
    )
    lineas.append(
        f"Fue campeon     : {'SI' if seleccion.get('fue_campeon') else 'NO'}"
    )
    lineas.append(
        "Anios campeon   : "
        + (", ".join(str(valor) for valor in seleccion.get("anios_campeon", [])) or "Ninguno")
    )

    filtros_aplicados = []
    if anio is not None:
        filtros_aplicados.append(f"anio={anio}")
    if grupo:
        filtros_aplicados.append(f"grupo={grupo}")
    if fecha:
        filtros_aplicados.append(f"fecha={fecha}")
    if filtros_aplicados:
        lineas.append("Filtros         : " + ", ".join(filtros_aplicados))

    add_section(lineas, f"MUNDIALES ENCONTRADOS ({len(mundiales_participados)})")
    if not mundiales_participados:
        lineas.append("No hay mundiales que coincidan con el filtro.")
        lineas.append(make_separator())
        return "\n".join(lineas)

    for mundial in mundiales_participados:
        groups = filter_groups_for_country(mundial, pais, grupo=grupo)
        positions = filter_group_positions_for_country(mundial, pais, grupo=grupo)
        matches = filter_matches_for_country(mundial, pais, grupo=grupo, fecha=fecha)
        goleadores = filter_goleadores_for_country(mundial, pais)

        lineas.append(f"Mundial {mundial.get('anio')}")
        lineas.append(
            f"  Organizador: {mundial.get('organizador', {}).get('nombre')} | "
            f"Campeon: {mundial.get('campeon', {}).get('nombre')}"
        )

        if groups:
            for item in groups:
                lineas.append(f"  Grupo: {item.get('id_grupo')} -> {', '.join(item.get('selecciones', []))}")
        else:
            lineas.append("  Grupo: No disponible con el filtro actual.")

        if positions:
            for pos in positions:
                lineas.append(
                    "  Posicion grupo: "
                    f"Grupo {pos.get('id_grupo')} | "
                    f"PTS={pos.get('pts')} PJ={pos.get('pj')} PG={pos.get('pg')} "
                    f"PE={pos.get('pe')} PP={pos.get('pp')} GF={pos.get('gf')} "
                    f"GC={pos.get('gc')} DIF={pos.get('diferencia')} "
                    f"Clasificado={pos.get('clasificado')}"
                )
        else:
            lineas.append("  Posicion grupo: No disponible con el filtro actual.")

        if matches:
            lineas.append(f"  Partidos ({len(matches)}):")
            for partido in matches:
                lineas.append("    - " + format_match(partido))
        else:
            lineas.append("  Partidos: No hay partidos que coincidan con el filtro.")

        if goleadores:
            lineas.append(f"  Goleadores ({len(goleadores)}):")
            for goleador in goleadores:
                lineas.append("    - " + format_goleador(goleador))
        else:
            lineas.append("  Goleadores: No hay registros para esta seleccion en este mundial.")

        lineas.append("")

    lineas.append(make_separator())
    return "\n".join(lineas)


def main() -> None:
    """Permite ejecutar la consulta desde terminal."""
    parser = argparse.ArgumentParser(description="Consulta toda la informacion de una seleccion.")
    parser.add_argument("pais", help="Nombre del pais o seleccion.")
    parser.add_argument("--anio", type=int, help="Filtra por un mundial especifico.")
    parser.add_argument("--grupo", help="Filtra por grupo especifico.")
    parser.add_argument("--fecha", help="Filtra partidos por fecha exacta.")
    parser.add_argument("--mongo-uri", help="URI de MongoDB para consultar directamente desde la BD.")
    parser.add_argument("--db", default="mundiales_futbol", help="Base de datos de MongoDB.")
    args = parser.parse_args()

    reporte = consultar_pais(
        pais=args.pais,
        anio=args.anio,
        grupo=args.grupo,
        fecha=args.fecha,
        mongo_uri=args.mongo_uri,
        db_name=args.db,
    )
    print(reporte)


if __name__ == "__main__":
    main()
