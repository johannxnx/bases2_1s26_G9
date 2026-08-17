"""
Consulta informacion de un mundial por anio con filtros opcionales.

Soporta dos fuentes:
1. Archivo local JSON generado en mongodb/json_generado/mundiales.json
2. MongoDB, si se proporciona --mongo-uri

Ejemplos:
    python 03_consultar_mundial.py 2014
    python 03_consultar_mundial.py 2014 --grupo A
    python 03_consultar_mundial.py 2014 --pais Argentina
    python 03_consultar_mundial.py 2014 --fecha 13-Jul-2014
    python 03_consultar_mundial.py 2014 --pais Alemania --mongo-uri mongodb://localhost:27017/
"""

# Permite usar tipos modernos de Python sin evaluar inmediatamente las
# anotaciones de tipos.
from __future__ import annotations

# argparse permite leer parametros desde la terminal.
import argparse
# json permite cargar el archivo mundiales.json generado previamente.
import json
# Path ayuda a trabajar con rutas de archivos de forma segura.
from pathlib import Path
# Any se usa en funciones donde el valor puede ser de varios tipos.
from typing import Any


# ROOT_DIR apunta a la carpeta mongodb donde esta este script.
ROOT_DIR = Path(__file__).resolve().parent
# Ruta al archivo JSON generado en el paso de transformacion.
MUNDIALES_JSON = ROOT_DIR / "json_generado" / "mundiales.json"


def make_separator(char: str = "=", length: int = 72) -> str:
    """Crea una linea separadora para mejorar la presentacion del reporte."""
    return char * length


def add_section(lineas: list[str], titulo: str) -> None:
    """Agrega un encabezado de seccion al reporte."""
    lineas.append("")
    lineas.append(make_separator("-"))
    lineas.append(titulo)
    lineas.append(make_separator("-"))


def normalize_text(value: Any) -> str:
    """
    Convierte cualquier valor a texto comparable:
    - si es None devuelve cadena vacia
    - elimina espacios extremos
    - pasa todo a minusculas

    Esto permite comparar filtros sin depender de mayusculas/minusculas.
    """
    if value is None:
        return ""
    return str(value).strip().lower()


def load_from_json() -> list[dict[str, Any]]:
    """
    Carga todos los documentos del archivo local mundiales.json.

    Este modo es util cuando:
    - aun no se han insertado los datos en MongoDB
    - se quiere probar la consulta sobre los JSON generados
    """
    with MUNDIALES_JSON.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_from_mongodb(mongo_uri: str, db_name: str) -> list[dict[str, Any]]:
    """
    Carga la coleccion mundiales directamente desde MongoDB.

    Requiere tener instalada la libreria pymongo.
    """
    try:
        from pymongo import MongoClient
    except ImportError as exc:
        raise SystemExit("Para consultar desde MongoDB instala pymongo: pip install pymongo") from exc

    # Se conecta al servidor MongoDB.
    client = MongoClient(mongo_uri)
    # Se selecciona la base de datos.
    database = client[db_name]
    # Se recuperan todos los documentos de la coleccion mundiales.
    # El _id de MongoDB no se incluye para que la salida sea mas limpia.
    return list(database.mundiales.find({}, {"_id": 0}))


def find_mundial(mundiales: list[dict[str, Any]], anio: int) -> dict[str, Any] | None:
    """
    Busca y devuelve el documento del mundial correspondiente al anio indicado.
    Si no existe, devuelve None.
    """
    for mundial in mundiales:
        if mundial.get("anio") == anio:
            return mundial
    return None


def match_group(partido: dict[str, Any], grupo: str | None) -> bool:
    """
    Valida si un partido pertenece al grupo solicitado.

    Si no se envio parametro grupo, siempre devuelve True.
    Si se envio, verifica que la etapa del partido contenga "Grupo X".
    """
    if not grupo:
        return True
    etapa = normalize_text(partido.get("etapa"))
    grupo_text = normalize_text(grupo)
    return f"grupo {grupo_text}" in etapa


def match_country(partido: dict[str, Any], pais: str | None) -> bool:
    """
    Valida si en el partido participa la seleccion indicada.

    Compara el pais enviado contra el local y el visitante.
    """
    if not pais:
        return True

    pais_text = normalize_text(pais)
    local = normalize_text(partido.get("local", {}).get("nombre"))
    visitante = normalize_text(partido.get("visitante", {}).get("nombre"))
    return pais_text == local or pais_text == visitante


def match_date(partido: dict[str, Any], fecha: str | None) -> bool:
    """
    Valida si el partido corresponde exactamente a la fecha solicitada.
    """
    if not fecha:
        return True
    return normalize_text(partido.get("fecha")) == normalize_text(fecha)


def filtrar_partidos(
    partidos: list[dict[str, Any]],
    grupo: str | None = None,
    pais: str | None = None,
    fecha: str | None = None,
) -> list[dict[str, Any]]:
    """
    Recorre la lista de partidos y devuelve solo los que cumplen todos
    los filtros enviados por el usuario.
    """
    return [
        partido
        for partido in partidos
        if match_group(partido, grupo) and match_country(partido, pais) and match_date(partido, fecha)
    ]


def infer_group_positions(
    posiciones_grupo: list[dict[str, Any]], grupo: str | None = None, pais: str | None = None
) -> list[dict[str, Any]]:
    """
    Filtra las posiciones de grupo del mundial segun:
    - grupo especifico
    - pais especifico
    """
    resultado = []
    for posicion in posiciones_grupo:
        if grupo and normalize_text(posicion.get("id_grupo")) != normalize_text(grupo):
            continue
        if pais and normalize_text(posicion.get("seleccion")) != normalize_text(pais):
            continue
        resultado.append(posicion)
    return resultado


def infer_groups(
    grupos: list[dict[str, Any]], grupo: str | None = None, pais: str | None = None
) -> list[dict[str, Any]]:
    """
    Filtra la seccion de grupos del mundial.

    Permite:
    - dejar solo un grupo especifico
    - dejar solo el grupo donde aparezca una seleccion dada
    """
    resultado = []
    for item in grupos:
        if grupo and normalize_text(item.get("id_grupo")) != normalize_text(grupo):
            continue
        if pais:
            selecciones = [normalize_text(nombre) for nombre in item.get("selecciones", [])]
            if normalize_text(pais) not in selecciones:
                continue
        resultado.append(item)
    return resultado


def filter_goleadores(goleadores: list[dict[str, Any]], pais: str | None = None) -> list[dict[str, Any]]:
    """Filtra goleadores opcionalmente por pais."""
    if not pais:
        return goleadores
    pais_text = normalize_text(pais)
    return [item for item in goleadores if normalize_text(item.get("seleccion")) == pais_text]


def filter_equipo_ideal(equipo_ideal: list[dict[str, Any]], pais: str | None = None) -> list[dict[str, Any]]:
    """Filtra equipo ideal opcionalmente por pais."""
    if not pais:
        return equipo_ideal
    pais_text = normalize_text(pais)
    return [item for item in equipo_ideal if normalize_text(item.get("seleccion")) == pais_text]


def format_bool_flag(value: Any) -> str:
    """
    Convierte valores booleanos o equivalentes a texto legible para mostrar
    en consola.
    """
    if value is None:
        return "N/D"
    if isinstance(value, bool):
        return "SI" if value else "NO"
    return str(value)


def format_match(partido: dict[str, Any]) -> str:
    """
    Convierte un partido en una sola linea de texto amigable para imprimir.

    Ejemplo:
    #1 | 13-Jul-1930 | Grupo 1 | Francia 4 - 1 Mexico | TE: NO | Penales: NO
    """
    local = partido.get("local", {})
    visitante = partido.get("visitante", {})

    # Construye la parte principal del marcador.
    base = (
        f"#{partido.get('num_partido')} | {partido.get('fecha')} | {partido.get('etapa')} | "
        f"{local.get('nombre')} {local.get('goles')} - {visitante.get('goles')} {visitante.get('nombre')}"
    )

    # Acumula informacion adicional solo si existe.
    extras = []
    if partido.get("tiempo_extra") is not None:
        extras.append(f"TE: {format_bool_flag(partido.get('tiempo_extra'))}")
    if partido.get("penales") is not None:
        extras.append(f"Penales: {format_bool_flag(partido.get('penales'))}")
    if partido.get("penales_local") is not None or partido.get("penales_visitante") is not None:
        extras.append(
            f"Marcador penales: {partido.get('penales_local', 0)} - {partido.get('penales_visitante', 0)}"
        )

    if extras:
        return base + " | " + " | ".join(extras)
    return base


def format_goleador(item: dict[str, Any]) -> str:
    """Formatea una fila de goleadores."""
    return (
        f"- {item.get('jugador')} | {item.get('seleccion')} | "
        f"Goles: {item.get('goles')} | Partidos: {item.get('partidos')} | "
        f"Promedio: {item.get('promedio')}"
    )


def format_equipo_ideal(item: dict[str, Any]) -> str:
    """Formatea una fila del equipo ideal."""
    return f"- {item.get('posicion')}: {item.get('jugador')} ({item.get('seleccion')})"


def consultar_mundial(
    anio: int,
    grupo: str | None = None,
    pais: str | None = None,
    fecha: str | None = None,
    mongo_uri: str | None = None,
    db_name: str = "mundiales_futbol",
) -> str:
    """
    Devuelve un reporte completo de un mundial.

    Parametros:
    - anio: mundial a consultar
    - grupo: filtra informacion de un grupo especifico
    - pais: filtra partidos y grupos donde participe el pais
    - fecha: filtra partidos de una fecha exacta
    - mongo_uri: si se proporciona, consulta desde MongoDB
    - db_name: nombre de la base de datos
    """
    # Si se envio mongo_uri, la consulta se hace sobre MongoDB.
    # Si no, se usa el archivo JSON local.
    mundiales = load_from_mongodb(mongo_uri, db_name) if mongo_uri else load_from_json()

    # Busca el documento correspondiente al anio solicitado.
    mundial = find_mundial(mundiales, anio)

    if not mundial:
        return f"No se encontro informacion para el mundial {anio}."

    # Se filtran las distintas secciones del documento segun los parametros.
    grupos_filtrados = infer_groups(mundial.get("grupos", []), grupo=grupo, pais=pais)
    posiciones_filtradas = infer_group_positions(
        mundial.get("posiciones_grupo", []), grupo=grupo, pais=pais
    )
    partidos_filtrados = filtrar_partidos(
        mundial.get("partidos", []), grupo=grupo, pais=pais, fecha=fecha
    )
    goleadores_filtrados = filter_goleadores(mundial.get("goleadores", []), pais=pais)
    equipo_ideal_filtrado = filter_equipo_ideal(mundial.get("equipo_ideal", []), pais=pais)

    # Se construye un reporte de texto linea por linea.
    lineas: list[str] = []
    lineas.append(make_separator())
    lineas.append(f"REPORTE DEL MUNDIAL {mundial['anio']}")
    lineas.append(make_separator())
    lineas.append(
        f"Organizador : {mundial.get('organizador', {}).get('nombre')}"
    )
    lineas.append(
        f"Campeon     : {mundial.get('campeon', {}).get('nombre')}"
    )
    lineas.append(
        f"Selecciones : {mundial.get('num_selecciones')} | "
        f"Partidos: {mundial.get('num_partidos')} | "
        f"Goles: {mundial.get('goles')} | "
        f"Promedio: {mundial.get('promedio_gol')}"
    )

    # Si hubo filtros, se agregan al reporte para dejar claro que se aplico.
    filtros_aplicados = []
    if grupo:
        filtros_aplicados.append(f"grupo={grupo}")
    if pais:
        filtros_aplicados.append(f"pais={pais}")
    if fecha:
        filtros_aplicados.append(f"fecha={fecha}")
    if filtros_aplicados:
        lineas.append("Filtros     : " + ", ".join(filtros_aplicados))

    # Seccion de grupos.
    add_section(lineas, f"GRUPOS ({len(grupos_filtrados)})")
    if grupos_filtrados:
        for item in grupos_filtrados:
            lineas.append(f"Grupo {item.get('id_grupo')}: {', '.join(item.get('selecciones', []))}")
    else:
        lineas.append("No hay grupos que coincidan con el filtro.")

    # Seccion de posiciones.
    add_section(lineas, f"POSICIONES DE GRUPO ({len(posiciones_filtradas)})")
    if posiciones_filtradas:
        for pos in posiciones_filtradas:
            lineas.append(
                f"- Grupo {pos.get('id_grupo')} | {pos.get('seleccion')} | "
                f"PTS={pos.get('pts')} PJ={pos.get('pj')} PG={pos.get('pg')} "
                f"PE={pos.get('pe')} PP={pos.get('pp')} GF={pos.get('gf')} "
                f"GC={pos.get('gc')} DIF={pos.get('diferencia')} "
                f"Clasificado={pos.get('clasificado')}"
            )
    else:
        lineas.append("No hay posiciones de grupo que coincidan con el filtro.")

    # Seccion de partidos y resultados.
    add_section(lineas, f"PARTIDOS Y RESULTADOS ({len(partidos_filtrados)})")
    if partidos_filtrados:
        for partido in partidos_filtrados:
            lineas.append(f"- {format_match(partido)}")
    else:
        lineas.append("No hay partidos que coincidan con el filtro.")

    # Seccion de goleadores.
    add_section(lineas, f"GOLEADORES ({len(goleadores_filtrados)})")
    if goleadores_filtrados:
        for item in goleadores_filtrados:
            lineas.append(format_goleador(item))
    else:
        lineas.append("No hay goleadores que coincidan con el filtro.")

    # Seccion de equipo ideal.
    add_section(lineas, f"EQUIPO IDEAL ({len(equipo_ideal_filtrado)})")
    if equipo_ideal_filtrado:
        for item in equipo_ideal_filtrado:
            lineas.append(format_equipo_ideal(item))
    else:
        lineas.append("No hay jugadores de equipo ideal que coincidan con el filtro.")

    lineas.append("")
    lineas.append(make_separator())

    # Se devuelve el texto final unido por saltos de linea.
    return "\n".join(lineas)


def main() -> None:
    """
    Punto de entrada del script cuando se ejecuta desde terminal.

    Permite llamar la funcion consultar_mundial pasando:
    - anio obligatorio
    - filtros opcionales
    - origen de datos opcional desde MongoDB
    """
    parser = argparse.ArgumentParser(description="Consulta un mundial por anio con filtros opcionales.")
    parser.add_argument("anio", type=int, help="Anio del mundial a consultar.")
    parser.add_argument("--grupo", help="Grupo a filtrar, por ejemplo: A, B, 1, 2.")
    parser.add_argument("--pais", help="Pais o seleccion a filtrar.")
    parser.add_argument("--fecha", help="Fecha exacta del partido, por ejemplo: 13-Jul-2014.")
    parser.add_argument("--mongo-uri", help="URI de MongoDB para consultar la coleccion mundiales.")
    parser.add_argument("--db", default="mundiales_futbol", help="Base de datos de MongoDB.")
    args = parser.parse_args()

    # Ejecuta la consulta y genera el texto del reporte.
    reporte = consultar_mundial(
        anio=args.anio,
        grupo=args.grupo,
        pais=args.pais,
        fecha=args.fecha,
        mongo_uri=args.mongo_uri,
        db_name=args.db,
    )
    # Imprime el resultado en consola.
    print(reporte)


# Ejecuta main solo si este archivo se corre directamente.
if __name__ == "__main__":
    main()
