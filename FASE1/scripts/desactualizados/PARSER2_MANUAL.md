# parser2.py — Documentación

## Descripción
Parsea archivos HTML de mundiales y genera CSVs normalizados. Incluye normalización automática de caracteres (acentos, tildes, ñ).

## Requisito
```powershell
pip install beautifulsoup4
```

## Uso
```powershell
cd scripts
python parser2.py              # Todos los años
python parser2.py 2022         # Solo 2022
python parser2.py 2022 2018    # Varios años
```

## Estructura HTML esperada
```
html/{anio}/{anio}_mundial.html
html/{anio}/{anio}_resultados.html
html/{anio}/{anio}_grupo_a.html (a-h)
html/{anio}/{anio}_goleadores.html
html/{anio}/{anio}_posiciones_finales.html
html/{anio}/{anio}_premios.html
html/{anio}/{anio}_tarjetas.html
```

## CSVs Generados
| Archivo | Descripción |
|---------|-------------|
| `mundiales.csv` | General del mundial |
| `partidos.csv` | Todos los partidos |
| `grupos.csv` | Información de grupos |
| `posiciones_grupo.csv` | Posiciones por grupo |
| `goles_partido.csv` | Goles con minuto/jugador |
| `goleadores.csv` | Top goleadores |
| `posiciones_finales.csv` | Ranking final |
| `premios.csv` | Premios individuales |
| `equipo_ideal.csv` | XI ideal del torneo |
| `tarjetas.csv` | Amarillas/rojas |

## Datos Normalizados
Además genera en `data/normalizado/`:
- Archivos normalizados con IDs relaccionados
- IDs de selecciones desde `seleccion.csv`
- IDs de jugadores desde `jugadores_pais.csv`
- Requiere: `seleccion.csv` en misma carpeta o directorio padre

## Funciones Principales
- `parsear_mundial()` → mundiales.csv
- `parsear_resultados()` → partidos.csv
- `parsear_grupos()` → grupos, posiciones_grupo, goles
- `parsear_goleadores()` → goleadores.csv
- `parsear_posiciones_finales()` → posiciones_finales.csv
- `parsear_premios()` → premios.csv, equipo_ideal.csv
- `parsear_tarjetas()` → tarjetas.csv
- `normalizar()` → CSVs normalizados con IDs
