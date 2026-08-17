import csv
import os

# Rutas
INPUT_JUGADORES = "data/jugadores_pais.csv"
INPUT_SELECCION = "scripts/seleccion.csv"
OUTPUT = "data/jugadores_salida.csv"


def cargar_selecciones():
    """
    Carga seleccion.csv y retorna:
    {nombre_seleccion: id_seleccion}
    """
    seleccion_map = {}

    with open(INPUT_SELECCION, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = row["nombre"].strip()
            id_sel = int(row["id_seleccion"])
            seleccion_map[nombre] = id_sel

    return seleccion_map


def procesar_jugadores():
    seleccion_map = cargar_selecciones()

    jugadores = []

    with open(INPUT_JUGADORES, encoding="utf-8") as f:
        reader = csv.reader(f)

        # Saltar encabezado
        next(reader)

        for row in reader:
            if not row or len(row) < 2:
                continue

            nombre = row[0].strip().strip('"')
            seleccion = row[1].strip()

            if not nombre or not seleccion:
                continue

            if seleccion not in seleccion_map:
                print(f"[WARNING] Selección no encontrada: {seleccion}")
                continue

            jugadores.append((nombre, seleccion))

    # Escribir salida
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")

        # Header
        writer.writerow(["ID JUGADOR", "NOMBRE", "ID SELECCION", "SELECCION"])

        for i, (nombre, seleccion) in enumerate(jugadores, start=1):
            writer.writerow([
                i,
                nombre,
                seleccion_map[seleccion],
                seleccion
            ])

    print(f"Archivo generado: {OUTPUT}")
    print(f"Total jugadores: {len(jugadores)}")


if __name__ == "__main__":
    procesar_jugadores()