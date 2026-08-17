# MongoDB - Fase 3

Esta carpeta contiene los scripts base para la parte NoSQL del proyecto usando 3 colecciones:

- `mundiales`
- `jugadores`
- `selecciones`

## Script incluido

- `01_crear_colecciones.js`
- `02_generar_documentos_desde_csv.py`
- `03_consultar_mundial.py`
- `04_consultar_pais.py`

Este script:

- crea la base `mundiales_futbol`
- crea las 3 colecciones
- define validadores con `$jsonSchema`
- crea indices para consultas por anio, jugador, seleccion, sede y partidos

El script `02_generar_documentos_desde_csv.py`:

- lee los CSV consolidados en `FASE3/data/carga de datos`
- transforma los datos al modelo documental definido en MongoDB
- genera archivos JSON listos para importar
- opcionalmente puede insertar directo en MongoDB si tienes `pymongo`

El script `03_consultar_mundial.py`:

- recibe como parametro principal el anio del mundial
- despliega resumen del torneo, grupos, posiciones y partidos
- permite filtros opcionales por `grupo`, `pais` y `fecha`
- puede leer desde `json_generado/mundiales.json` o desde MongoDB

El script `04_consultar_pais.py`:

- recibe como parametro principal el pais o seleccion
- muestra participaciones, sedes y campeonatos
- muestra informacion de grupo, partidos y resultados
- permite filtros opcionales por `anio`, `grupo` y `fecha`
- puede leer desde JSON o desde MongoDB

## Ejecucion

```bash
mongosh "mongodb://localhost:27017/mundiales_futbol" .\01_crear_colecciones.js
```

```bash
python 02_generar_documentos_desde_csv.py
```

Genera:

- `json_generado/selecciones.json`
- `json_generado/jugadores.json`
- `json_generado/mundiales.json`

Para insertar directamente en MongoDB:

```bash
python 02_generar_documentos_desde_csv.py --mongo-uri mongodb://localhost:27017/ --db mundiales_futbol
```

## Consulta por anio

```bash
python 03_consultar_mundial.py 2014
python 03_consultar_mundial.py 2014 --pais Argentina
python 03_consultar_mundial.py 2014 --grupo A
python 03_consultar_mundial.py 2014 --fecha 13-Jul-2014
```

## Consulta por pais

```bash
python 04_consultar_pais.py Uruguay
python 04_consultar_pais.py Uruguay --anio 1930
python 04_consultar_pais.py Uruguay --grupo 3
python 04_consultar_pais.py Uruguay --fecha 30-Jul-1930
```

## Modelo general

### `selecciones`

Guarda el catalogo de selecciones y datos derivados:

- `id_seleccion`
- `nombre`
- `participaciones`
- `sedes`
- `total_participaciones`
- `fue_campeon`
- `anios_campeon`

### `jugadores`

Guarda el catalogo de jugadores y sus participaciones por mundial:

- `id_jugador`
- `nombre`
- `id_seleccion`
- `seleccion`
- `altura`
- `fecha_nacimiento`
- `nacionalidad`
- `participaciones`

### `mundiales`

Un documento por anio del mundial con la mayor parte de la informacion embebida:

- resumen del mundial
- organizador
- campeon
- grupos
- posiciones por grupo
- posiciones finales
- partidos
- detalle de goles
- goleadores
- premios
- equipo ideal
- tarjetas

## Nota

Este folder cubre la parte de creacion de colecciones y estructura documental.
Tambien incluye el script de transformacion desde los CSV consolidados a documentos JSON compatibles con las 3 colecciones del proyecto.
