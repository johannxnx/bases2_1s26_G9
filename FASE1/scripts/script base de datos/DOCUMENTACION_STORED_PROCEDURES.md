# Documentación Completa de Stored Procedures
## Base de Datos de Mundiales de Fútbol

---

## 📋 Tabla de Contenidos
1. [SP_INFO_MUNDIAL](#sp_info_mundial)
2. [SP_INFO_PAIS](#sp_info_pais)
3. [Cómo Funcionan Internamente](#cómo-funcionan-internamente)
4. [Ejemplos Prácticos](#ejemplos-prácticos)
5. [Tablas de Referencia](#tablas-de-referencia)
6. [Instalación](#instalación)

---

## SP_INFO_MUNDIAL

### Descripción General
Genera un reporte completo sobre un **Mundial de Fútbol específico**. Muestra toda la información organizada en 4 secciones principales:
- **Información General**: Organizador, campeón, cantidad de equipos, partidos totales, goles y promedios
- **Fase de Grupos**: Clasificación por grupo con tabla de posiciones
- **Partidos**: Resultados de todos los encuentros con fechas y etapas
- **Máximos Goleadores**: Ranking de los jugadores que más goles marcaron en el torneo

### Sintaxis Oficial
```sql
CREATE OR REPLACE PROCEDURE sp_info_mundial (
    p_anio          IN NUMBER,
    p_id_grupo      IN VARCHAR2 DEFAULT NULL,
    p_id_seleccion  IN NUMBER DEFAULT NULL,
    p_etapa         IN VARCHAR2 DEFAULT NULL
)
```

### Parámetros Detallados

#### **p_anio** (NUMBER) - ⚠️ OBLIGATORIO
- **Propósito**: Especifica el año del mundial a consultar
- **Validación**: Se verifica que exista en la tabla MUNDIAL, si no → Error
- **Valores válidos**: 1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022
- **Cómo funciona**: Este parámetro filtra TODAS las consultas del procedure
  ```sql
  WHERE p.ANIO = p_anio  -- Aparece en casi todas las subconsultas
  ```

#### **p_id_grupo** (VARCHAR2) - Opcional (DEFAULT: NULL)
- **Propósito**: Filtrar resultados por grupo específico
- **Valores típicos**: 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'
- **Si es NULL**: Se muestran todos los grupos
- **Cómo funciona**: Filtra en dos secciones:
  1. **GRUPOS**: `WHERE ID_GRUPO = p_id_grupo`
  2. **PARTIDOS**: Muestra only partidos de selecciones que jugaron en ese grupo
     ```sql
     p.ID_LOCAL IN (SELECT ID_SELECCION FROM POSICION_GRUPO 
                   WHERE ID_GRUPO = p_id_grupo)
     ```

#### **p_id_seleccion** (NUMBER) - Opcional (DEFAULT: NULL)
- **Propósito**: Filtrar información específica de un país
- **Formato**: ID numérico de la tabla SELECCION
- **Ejemplos de IDs comunes**:
  - 1 = Alemania
  - 6 = Argentina
  - 11 = Brasil
  - 36 = Francia
  - 44 = Inglaterra
  - 51 = Italia
  - 80 = Uruguay
- **Si es NULL**: Se muestran todos los países
- **Cómo funciona**: Filtra en:
  1. **GRUPOS**: `WHERE ID_SELECCION = p_id_seleccion` en tabla POSICION_GRUPO
  2. **PARTIDOS**: `WHERE ID_LOCAL = p_id_seleccion OR ID_VISITANTE = p_id_seleccion`
  3. **GOLEADORES**: `WHERE ID_SELECCION = p_id_seleccion`

#### **p_etapa** (VARCHAR2) - Opcional (DEFAULT: NULL)
- **Propósito**: Filtrar partidos por fase del torneo
- **Valores típicos**: 'Grupo', 'Octavos de final', 'Cuartos de final', 'Semifinal', 'Tercero y cuarto lugar', 'Final'
- **Si es NULL**: Se muestran todas las etapas
- **Cómo funciona**: Solo afecta sección PARTIDOS
  ```sql
  WHERE p.ETAPA = p_etapa
  ```

### Ejemplos de Uso Progresivos

```sql
-- NIVEL 1: Ver TODO sobre un mundial completo
EXEC sp_info_mundial(2022);
-- Retorna: Información general, todos los grupos (A-H), todos los partidos, todos los goleadores

-- NIVEL 2: Filtrar por grupo específico
EXEC sp_info_mundial(2022, 'A');
-- Retorna: Información general, solo Grupo A, partidos del Grupo A, goleadores del Grupo A

-- NIVEL 3: Información de un país en un mundial
EXEC sp_info_mundial(2022, NULL, 6);  -- Argentina
-- Retorna: Información general, grupo de Argentina (Grupo C), partidos de Argentina, goleadores de Argentina

-- NIVEL 4: Información de un país en una etapa específica
EXEC sp_info_mundial(2022, NULL, 6, 'Semifinal');  -- Argentina en Semifinal
-- Retorna: Información general, solo el partido de semifinal de Argentina

-- NIVEL 5: Combo - Grupo específico con país específico
EXEC sp_info_mundial(2022, 'A', 44);  -- Grupo A, Inglaterra
-- Retorna: Información general, Grupo A, partidos de Inglaterra en Grupo A, goleadores de Inglaterra
```

### Ejecución Paso a Paso (Internamente)

1. **Validar año**: Verifica que `p_anio` exista en tabla MUNDIAL
2. **Información general**: JOIN entre MUNDIAL, SELECCION
3. **Grupos**: Itera por cada grupo disponible
4. **Posiciones**: Para cada grupo, ejecuta query con CASE statements para calcular:
   - PJ (Partidos Jugados)
   - PG, PE, PP (Goles/Empatados/Perdidos)
   - GF, GC (Goles a Favor/Contra)
   - DIF (Diferencia = GF - GC)
   - PTS (Puntos = victoria*3 + empate*1)
5. **Partidos**: Ejecuta query con LEFT JOINs a SELECCION para obtener nombres, ordena por FECHA
6. **Goleadores**: Query con ROW_NUMBER() OVER PARTITION BY para ranking, ordena por GOLES DESC

---

## SP_INFO_PAIS

### Descripción General
Genera un reporte histórico sobre **un país específico a través de todos los mundiales**. Muestra su participación completa, desempeño, récords y datos de jugadores. Ideal para consultar la "biografía" de una selección.

**Secciones que muestra:**
- **Años de participación**: Listado de todos los mundiales en que participó
- **Mundiales organizados**: Si fue sede en algún año
- **Desempeño por mundial**: Estadísticas de cada participación
- **Detalles opcionales**: Goleadores, tarjetas disciplinarias, información de jugadores

### Parámetros

| Parámetro | Tipo | Obligatorio | Descripción | Ejemplo |
|-----------|------|-------------|-------------|---------|
| `p_id_seleccion` | NUMBER | Si | ID del país | 6 (Argentina) |
| `p_anio` | NUMBER | Opcional | Filtrar por año específico | 2022 |
| `p_mostrar_detalles` | VARCHAR2 | Opcional | 'S' = detalles, 'N' = resumen | 'S' |

### Ejemplos de Uso

```sql
-- Mostrar toda la información de Argentina
EXEC sp_info_pais(6);

-- Mostrar información de Brasil solo en 2002
EXEC sp_info_pais(11, 2002);

-- Mostrar información de Alemania sin detalles de goleadores/tarjetas
EXEC sp_info_pais(1, NULL, 'N');

-- Mostrar información de Uruguay en 1950
EXEC sp_info_pais(80, 1950);
```

### Output
Genera un reporte con:
- Años de participación (con posiciones finales)
- Mundiales organizados (si aplica)
- Desempeño por mundial (partidos, victorias, goles)
- Máximos goleadores (si p_mostrar_detalles = 'S')
- Tarjetas disciplinarias (si p_mostrar_detalles = 'S')

---

## 3. Encontrar IDs de Países

Para saber qué ID usar en los parámetros:

```sql
-- Ver todos los países
SELECT ID_SELECCION, NOMBRE FROM SELECCION ORDER BY NOMBRE;

-- Buscar un país específico
SELECT ID_SELECCION, NOMBRE FROM SELECCION WHERE NOMBRE LIKE '%Argen%';
SELECT ID_SELECCION, NOMBRE FROM SELECCION WHERE NOMBRE = 'Brasil';
```

### IDs más comunes:
- 1 = Alemania
- 6 = Argentina
- 11 = Brasil
- 34 = España
- 36 = Francia
- 44 = Inglaterra
- 51 = Italia
- 69 = Rusia
- 74 = Suiza
- 80 = Uruguay
- 85 = Yugoslavia

---

## 4. Cómo Crear los Procedures

### En SQL Developer o SQL*Plus:

```sql
-- 1. Copiar el contenido del archivo stored_procedures.sql
-- 2. Ejecutar en tu conexión a la BD

@C:/ruta/al/archivo/stored_procedures.sql

-- 3. Verificar que se crearon correctamente
SELECT OBJECT_NAME FROM USER_OBJECTS 
WHERE OBJECT_TYPE = 'PROCEDURE' 
AND OBJECT_NAME LIKE 'SP_INFO%';
```

### O crear manualmente:

```sql
-- Para el primer procedure
CREATE OR REPLACE PROCEDURE sp_info_mundial (
    p_anio              IN NUMBER,
    p_id_grupo          IN VARCHAR2 DEFAULT NULL,
    p_id_seleccion      IN NUMBER DEFAULT NULL,
    p_etapa             IN VARCHAR2 DEFAULT NULL
)
AS
BEGIN
    -- ... código del procedure ...
END sp_info_mundial;
/

-- Para el segundo procedure
CREATE OR REPLACE PROCEDURE sp_info_pais (
    p_id_seleccion      IN NUMBER,
    p_anio              IN NUMBER DEFAULT NULL,
    p_mostrar_detalles  IN VARCHAR2 DEFAULT 'S'
)
AS
BEGIN
    -- ... código del procedure ...
END sp_info_pais;
/
```

---

## 5. Configuración de Output

Para ver correctamente los resultados en SQL*Plus:

```sql
SET PAGESIZE 0
SET LINESIZE 200
SET LONG 20000
SET TRIMSPOOL ON
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING OFF
```

---

## 6. Parámetros por Defecto

### P_ANIO
- **Obligatorio** para `sp_info_mundial`
- Años disponibles: 1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022

### P_ETAPA
Valores típicos: 'Grupo', 'Octavos de final', 'Cuartos de final', 'Semifinal', 'Tercer lugar', 'Final'

### P_ID_GRUPO
Valores típicos: A, B, C, D, E, F, G, H (depende del año)

---

## Notas Importantes

1. **NULL en parámetros opcionales = sin filtro**
   ```sql
   EXEC sp_info_mundial(2022, NULL, NULL, NULL);  -- Muestra TODO
   ```

2. **Los procedures usan DBMS_OUTPUT.PUT_LINE()**
   - Asegúrate de tener habilitado el output
   - En SQL Developer: Ver > Dbms Output

3. **Manejo de errores**
   - Si el año no existe, muestra mensaje de error
   - Si el país no existe, muestra mensaje de error
   - Los parámetros opcionales filtrán, no dan error

4. **Performance**
   - Los procedures optimizados para BD con ~2000 registros
   - Pueden tardar unos segundos en mundiales grandes

---

## Casos de Uso Típicos

```sql
-- Análisis de mundial específico
EXEC sp_info_mundial(2022);

-- Comparar desempeño de dos países en un año
EXEC sp_info_mundial(1986, NULL, 6);  -- Argentina 1986
EXEC sp_info_mundial(1986, NULL, 11); -- Brasil 1986

-- Historial completo de un país
EXEC sp_info_pais(34);  -- Historia de España

-- Análisis de desempeño agrupado
EXEC sp_info_pais(36, NULL, 'N');  -- Francia sin detalles
```
