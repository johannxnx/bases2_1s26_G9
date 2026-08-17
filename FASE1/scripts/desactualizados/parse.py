from bs4 import BeautifulSoup
import pandas as pd
import os

HTML_DIR = "html"

jugadores_data = []
selecciones = set()

def parsear_archivo(file):
    ruta = os.path.join(HTML_DIR, file)

    with open(ruta, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # ─── obtener nombre de selección ───
    h1 = soup.find("h1")
    if not h1:
        return

    texto = h1.text.strip()
    seleccion = texto.replace("Jugadores de ", "").split(" en")[0].strip()

    selecciones.add(seleccion)

    # ─── obtener jugadores ───
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/jugadores/" in href:
            nombre = a.text.strip()

            if nombre:  # evitar vacíos
                jugadores_data.append({
                    "nombre": nombre,
                    "seleccion": seleccion
                })


def procesar_todos():
    for file in os.listdir(HTML_DIR):
        if file.endswith(".html"):
            print("Procesando:", file)
            parsear_archivo(file)


def guardar_csv():
    os.makedirs("data", exist_ok=True)

    df = pd.DataFrame(jugadores_data)

    df = df.drop_duplicates()

    df.to_csv("data/jugadores_pais.csv", index=False)

    print("\nCSV generado correctamente: data/jugadores_pais.csv")


if __name__ == "__main__":
    procesar_todos()
    guardar_csv()