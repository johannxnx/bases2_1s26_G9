# Documentación Completa de Stored Procedures
## Base de Datos de Mundiales de Fútbol

---

## Tabla de Contenidos
1. [Resumen General](#resumen-general)
2. [SP_INFO_MUNDIAL](#sp_info_mundial)
3. [SP_INFO_PAIS](#sp_info_pais)
4. [Cómo Funcionan Internamente](#cómo-funcionan-internamente)
5. [Guía de IDs de Países](#guía-de-ids-de-países)
6. [Solución de Problemas](#solución-de-problemas)

---

## Resumen General

### ¿Qué son estos Stored Procedures?
Son dos funciones SQL especializadas que generan reportes complejos sobre **datos de Mundiales de Fútbol**. 

| Procedure | Propósito | Enfoque |
|-----------|-----------|---------|
| **sp_info_mundial** | Información de un mundial en un año específico | **Temporal** (un año, múltiples países) |
| **sp_info_pais** | Información histórica de un país | **Histórico** (un país, múltiples años) |

### Flujo de Datos General

```
┌─────────────────────────────────────────────┐
│      Base de Datos MUNDIAL                  │
│  (Tablas: MUNDIAL, SELECCION, GRUPO, etc)  │
└────────────┬────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────────────┐ ┌─▼────────────────┐
│ sp_info_mundial│ │ sp_info_pais     │
│ (Por año)      │ │ (Por país)       │
└────────────────┘ └──────────────────┘
```

---

# SP_INFO_MUNDIAL

## Descripción General

Genera un **reporte completo sobre un Mundial de Fútbol específico**. Es como entrar a Wikipedia y seleccionar la página de una edición del mundial.

**¿Qué muestra?**
1. **Información general del torneo** (organizador, campeón, estadísticas)
2. **Fase de grupos** (clasificaciones con tabla de posiciones)
3. **Detalles de partidos** (resultados, fechas, etapas)
4. **Máximos goleadores** (ranking de artilleros)

---

## 📝 Sintaxis Oficial

```sql
CREATE OR REPLACE PROCEDURE sp_info_mundial (
    p_anio          IN NUMBER,
    p_id_grupo      IN VARCHAR2 DEFAULT NULL,
    p_id_seleccion  IN NUMBER DEFAULT NULL,
    p_etapa         IN VARCHAR2 DEFAULT NULL
)
```

---

## Parámetros Detallados

### p_anio (NUMBER) - ⚠️ OBLIGATORIO

**¿Para qué?** Especifica qué mundial consultar

| Atributo | Valor |
|----------|-------|
| **Tipo** | NUMBER |
| **Valores válidos** | 1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022 |
| **Si no existe** | ERROR: Año X no encontrado |

**Cómo funciona internamente:**
```sql
-- Se valida primero
SELECT COUNT(*) INTO v_count FROM MUNDIAL WHERE ANIO = p_anio;
IF v_count = 0 THEN
    DBMS_OUTPUT.PUT_LINE('ERROR: Año ' || p_anio || ' no encontrado.');
    RETURN;  -- Detiene la ejecución
END IF;

-- Luego todas las queries lo usan
WHERE m.ANIO = p_anio
WHERE pg.ANIO = p_anio
WHERE p.ANIO = p_anio
WHERE g.ANIO = p_anio
```

---

### p_id_grupo (VARCHAR2) - Opcional

**¿Para qué?** Filtrar por grupos específicos (A, B, C, D, etc.)

| Atributo | Valor |
|----------|-------|
| **Default** | NULL (sin filtro = todos los grupos) |
| **Valores típicos** | 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H' |
| **Nota** | Cantidad de grupos varía por año (1930 sin grupos, 2022 con 8) |

**Cómo funciona internamente:**
```sql
-- En GRUPOS, filtra grupos específicos
WHERE ANIO = p_anio
AND (p_id_grupo IS NULL OR ID_GRUPO = p_id_grupo)

-- En PARTIDOS, muestra solo equipos del grupo
WHERE p.ID_LOCAL IN (
    SELECT ID_SELECCION FROM POSICION_GRUPO
    WHERE ANIO = p_anio AND ID_GRUPO = p_id_grupo
)
OR
p.ID_VISITANTE IN (
    SELECT ID_SELECCION FROM POSICION_GRUPO
    WHERE ANIO = p_anio AND ID_GRUPO = p_id_grupo
)
```

**Ejemplo visual:**
```
p_id_grupo = 'A' →  Muestra:
  ├─ Grupo A (2 partidas)
  ├─ Tabla de posiciones del Grupo A
  ├─ Todos los partidos de equipos en Grupo A
  └─ Goleadores que jugaron en Grupo A
```

---

### p_id_seleccion (NUMBER) - Opcional

**¿Para qué?** Filtrar información de un país específico

| Atributo | Valor |
|----------|-------|
| **Default** | NULL (sin filtro = todos los países) |
| **Formato** | ID numérico (consulta tabla SELECCION) |
| **Ejemplo** | 6 = Argentina, 11 = Brasil |

**Cómo funciona internamente:**
```sql
-- Se aplica en tres secciones:

-- 1. GRUPOS - mostrar solo grupo de ese país
WHERE ANIO = p_anio
AND (p_id_seleccion IS NULL OR pg.ID_SELECCION = p_id_seleccion)

-- 2. PARTIDOS - mostrar solo partidos donde jugó
WHERE p.ID_LOCAL = p_id_seleccion 
OR p.ID_VISITANTE = p_id_seleccion

-- 3. GOLEADORES - mostrar goleadores de ese país
WHERE g.ID_SELECCION = p_id_seleccion
```

**Ejemplo visual:**
```
p_id_seleccion = 6 (Argentina) →  Muestra:
  ├─ Grupo de Argentina en 2022 (Grupo C)
  ├─ Tabla de posiciones del Grupo C, pero destaca Argentina
  ├─ Solo partidos de Argentina
  │  ├─ Argentina 1 - 2 Arabia Saudita
  │  ├─ Argentina 2 - 0 México
  │  ├─ Argentina 2 - 1 Polonia
  │  └─ ... hasta Final o eliminación
  └─ Goleadores de Argentina
```

---

### p_etapa (VARCHAR2) - Opcional

**¿Para qué?** Filtrar partidos por fase del torneo

| Atributo | Valor |
|----------|-------|
| **Default** | NULL (sin filtro = todas las etapas) |
| **Valores típicos** | 'Grupo', 'Octavos de final', 'Cuartos de final', 'Semifinal', 'Tercero y cuarto lugar', 'Final' |
| **Afecta** | **Solo la sección PARTIDOS** |

**Cómo funciona internamente:**
```sql
-- En PARTIDOS
WHERE p.ANIO = p_anio
AND (p_etapa IS NULL OR p.ETAPA = p_etapa)

-- En GRUPOS y GOLEADORES no aplica este filtro
```

**Ejemplo visual:**
```
p_etapa = 'Final' →  Muestra:
  ├─ Información general (sigue igual)
  ├─ GRUPOS (sigue igual)
  ├─ PARTIDOS (solo la Final)
  │  ├─ Argentina 3 - 3 Francia (después penales 4-2)
  └─ GOLEADORES (sigue igual)

p_etapa = 'Grupo' →  Muestra:
  ├─ Información general (sigue igual)
  ├─ GRUPOS (sigue igual)
  ├─ PARTIDOS (solo partidos de grupo, no octavos en adelante)
  └─ GOLEADORES (sigue igual)
```

---

## 💡 Ejemplos de Uso Progresivos

### Ejemplo 1: Ver TODO sobre un mundial
```sql
EXEC sp_info_mundial(2022);
```
**Retorna:**
- Información general del 2022 (Qatar como sede, Argentina campeón, 32 equipos)
- 8 Grupos (A al H) con posiciones
- Todos los 64 partidos jugados
- Top 10 goleadores del torneo

---

### Ejemplo 2: Filtrar por grupo
```sql
EXEC sp_info_mundial(2022, 'A');
```
**Retorna:**
- Información general del 2022
- **SOLO Grupo A** (Qatar, Ecuador, Senegal, Holanda)
- **SOLO partidos** del Grupo A (6 partidos: 4 de cada equipo)
- **SOLO goleadores** que jugaron en Grupo A

---

### Ejemplo 3: Data de un país en un mundial
```sql
EXEC sp_info_mundial(2022, NULL, 6);  -- 6 = Argentina
```
**Retorna:**
- Información general del 2022
- Grupo de Argentina (Grupo C: Argentina, Polonia, México, Arabia Saudita)
- **SOLO partidos de Argentina** (7 partidos en total debido a que llegó a la Final)
- **SOLO goleadores de Argentina**

---

### Ejemplo 4: Un país en una etapa específica
```sql
EXEC sp_info_mundial(2022, NULL, 6, 'Semifinal');
```
**Retorna:**
- Información general del 2022
- Grupo de Argentina
- **SOLO el partido de Semifinal** (Argentina 3 - 0 Croacia)
- Goleadores de Argentina (incluye goles antes de semifinal porque GOLEADORES no filtra por etapa)

---

### Ejemplo 5: Combo - Grupo + País + Etapa
```sql
EXEC sp_info_mundial(2022, 'A', 44, 'Grupo');  -- Grupo A, Inglaterra, solo fase de grupos
```
**Retorna:**
- Información general del 2022
- **SOLO Grupo A**
- **SOLO partidos de Inglaterra en Grupo A** (3 partidos en fase de grupos)
- Goleadores de Inglaterra en todo el torneo

---

## 🔍 Ejecución Paso a Paso (Internamente)

### Paso 1: Validación
```
¿Existe el año p_anio en tabla MUNDIAL?
   ├─ No → ERROR y termina
   └─ Sí → Continúa
```

### Paso 2: Información General
```
JOIN MUNDIAL con SELECCION (2 veces)
  ├─ LEFT JOIN s_org: Nombre del organizador
  ├─ LEFT JOIN s_cam: Nombre del campeón
  └─ Retorna: Año, organizador, campeón, # equipos, # partidos, goles, promedio
```

### Paso 3: Fase de Grupos
```
LOOP sobre cada grupo único del año
  ├─ Filtra: WHERE ANIO = p_anio AND ID_GRUPO ...
  └─ Para cada grupo:
      └─ LOOP sobre POSICION_GRUPO
          ├─ Calcula: PJ, PG, PE, PP via CASE statements
          ├─ Calcula: GF, GC sumando GOALS en tabla PARTIDO
          ├─ Calcula: DIF = GF - GC
          ├─ Calcula: PTS = (PG * 3) + PE
          └─ Ordena por: PTS DESC, DIF DESC
```

### Paso 4: Partidos
```
Query sobre tabla PARTIDO
  ├─ LEFT JOINs para obtener nombres de países
  ├─ Filtra por: ANIO, (opcional) grupo, (opcional) selección, (opcional) etapa
  ├─ Incluye: Resultado, fecha, etapa, penales si aplica
  └─ Ordena por: FECHA, NUM_PARTIDO
```

### Paso 5: Goleadores
```
Query sobre tabla GOLEADOR
  ├─ JOINs con JUGADOR_PAIS y SELECCION
  ├─ Filtra por: ANIO, (opcional) selección
  ├─ Retorna: Nombre jugador, país, goles, partidos, promedio
  └─ Ordena por: GOLES DESC, PROMEDIO DESC
```

---

# SP_INFO_PAIS

## Descripción General

Genera un **reporte histórico sobre un país específico a través de TODOS los mundiales**. Es como ver la "biografía" completa de una selección.

**¿Qué muestra?**
1. **Años de participación** (listado de todos los mundiales en que jugó)
2. **Mundiales organizados** (si fue sede)
3. **Desempeño por mundial** (estadísticas de cada año: P, V, E, D, GF, GC)
4. **Detalles opcionales** (máximos goleadores, tarjetas, jugadores)

---

## Sintaxis Oficial

```sql
CREATE OR REPLACE PROCEDURE sp_info_pais (
    p_id_seleccion     IN NUMBER,
    p_anio             IN NUMBER DEFAULT NULL,
    p_mostrar_detalles IN VARCHAR2 DEFAULT 'S'
)
```

---

## Parámetros Detallados

### p_id_seleccion (NUMBER) - ⚠️ OBLIGATORIO

**¿Para qué?** Especifica qué país consultar

| Atributo | Valor |
|----------|-------|
| **Tipo** | NUMBER |
| **Fuente** | ID de tabla SELECCION |
| **Si no existe** | ERROR: País con ID X no encontrado |

**Cómo validar el ID:**
```sql
-- Ver todos los países
SELECT ID_SELECCION, NOMBRE FROM SELECCION ORDER BY NOMBRE;

-- Buscar uno específico
SELECT ID_SELECCION FROM SELECCION WHERE NOMBRE = 'Argentina';
```

**IDs más comunes y usados:**

| ID | País | Participaciones |
|----|------|-----------------|
| 1 | Alemania | 19 |
| 6 | Argentina | 17 |
| 11 | Brasil | 21 |
| 36 | Francia | 15 |
| 44 | Inglaterra | 15 |
| 51 | Italia | 17 |
| 80 | Uruguay | 15 |

---

### p_anio (NUMBER) - Opcional

**¿Para qué?** Filtrar a un año específico en lugar de mostrar todos

| Atributo | Valor |
|----------|-------|
| **Default** | NULL (sin filtro = todos los años) |
| **Valores válidos** | Cualquier año en que participó el país |
| **Si el país no participó ese año** | No muestra datos de ese año |

**Cómo funciona internamente:**
```sql
-- En AÑOS DE PARTICIPACIÓN
WHERE pg.ID_SELECCION = p_id_seleccion
AND (p_anio IS NULL OR pg.ANIO = p_anio)

-- En DESEMPEÑO POR MUNDIAL
WHERE pg.ID_SELECCION = p_id_seleccion
AND (p_anio IS NULL OR pg.ANIO = p_anio)

-- En DETALLES (cuando p_mostrar_detalles = 'S')
WHERE g.ID_SELECCION = p_id_seleccion
AND (p_anio IS NULL OR g.ANIO = p_anio)
```

**Ejemplo visual:**
```
p_id_seleccion = 6, p_anio = NULL →  Muestra:
  ├─ Años: 1930, 1934, 1938, 1950, ... 2022 (17 mundiales)
  ├─ Sede: No (Argentina nunca fue sede)
  └─ Desempeño: dato de CADA mundo participado

p_id_seleccion = 6, p_anio = 2022 →  Muestra:
  ├─ Años: 2022 SOLAMENTE
  ├─ Sede: No
  └─ Desempeño: solo datos de 2022
```

---

### p_mostrar_detalles (VARCHAR2) - Opcional

**¿Para qué?** Controlar el nivel de detalle del reporte

| Atributo | Valor |
|----------|-------|
| **Default** | 'S' (sí mostrar detalles) |
| **Si = 'S'** | Muestra: Goleadores, Tarjetas, Jugadores |
| **Si ≠ 'S'** | Muestra: Solo resumen general (años, sede, desempeño) |

**Cómo funciona internamente:**
```sql
IF p_mostrar_detalles = 'S' THEN
    -- Muestra GOLEADORES
    FOR rec_gol IN (SELECT top 3 goleadores por año) LOOP
        DBMS_OUTPUT.PUT_LINE(...);
    END LOOP;
    
    -- Muestra TARJETAS
    FOR rec_tarjeta IN (SELECT amarillas y rojas por año) LOOP
        DBMS_OUTPUT.PUT_LINE(...);
    END LOOP;
    
    -- Muestra DETALLE JUGADORES
    FOR rec_jug IN (SELECT info completa de cada jugador) LOOP
        DBMS_OUTPUT.PUT_LINE(...);
    END LOOP;
END IF;
```

---

## Ejemplos de Uso Progresivos

### Ejemplo 1: Ver TODO sobre un país (completo)
```sql
EXEC sp_info_pais(6);  -- Argentina con todos los detalles
```
**Retorna:**
- Años de participación (1930-2022: 17 mundiales)
- Sede: No
- Desempeño por año (17 filas con estadísticas)
- Top 3 goleadores en CADA año
- Tarjetas amarillas y rojas en CADA año
- Información de CADA jugador que participó en CADA mundial

---

### Ejemplo 2: Filtrar por año específico
```sql
EXEC sp_info_pais(6, 2022);  -- Argentina solo 2022
```
**Retorna:**
- Años: 2022 solamente
- Sede: No
- Desempeño en 2022 (1 fila)
- Top 3 goleadores de Argentina en 2022
- Tarjetas de Argentina en 2022
- Todas los jugadores de Argentina en 2022

---

### Ejemplo 3: Resumen sin detalles
```sql
EXEC sp_info_pais(11, NULL, 'N');  -- Brasil sin detalles
```
**Retorna:**
- Años de participación (21 mundiales)
- Sede: Sí, en 1950 y 2014
- Desempeño por año (21 filas)
- **NADA de detalles** (sin goleadores, tarjetas, jugadores)

---

### Ejemplo 4: Un año específico sin detalles
```sql
EXEC sp_info_pais(1, 2022, 'N');  -- Alemania 2022, resumen
```
**Retorna:**
- Año: 2022
- Desempeño en 2022
- SIN información de goleadores ni jugadores

---

## Ejecución Paso a Paso (Internamente)

### Paso 1: Obtener nombre del país
```
SELECT NOMBRE INTO v_nombre_pais FROM SELECCION 
WHERE ID_SELECCION = p_id_seleccion
  ├─ No existe → EXCEPTION NO_DATA_FOUND
  └─ Existe → Continúa con variable v_nombre_pais
```

### Paso 2: Años de Participación
```
LOOP sobre POSICION_GRUPO (filtrado por país)
  ├─ LEFT JOIN con POSICION_FINAL
  ├─ Mostrar con CASE statement:
  │  ├─ POSICION = 1 → "CAMPEÓN"
  │  ├─ POSICION = 2 → "Subcampeón"
  │  ├─ POSICION <= 4 → "Semifinalista"
  │  └─ Otras → "Posición N"
  └─ Ordenar por ANIO DESC (más reciente primero)
```

### Paso 3: Sede de Mundiales
```
COUNT(*) FROM MUNDIAL WHERE ID_ORGANIZADOR = p_id_seleccion
  ├─ count = 0 → "No ha sido sede"
  └─ count > 0 → LOOP over años y mostrar
```

### Paso 4: Desempeño por Mundial
```
Compleja query sobre MUNDIAL y PARTIDO
  ├─ CASE statements para:
  │  ├─ Contar GANADOS: (LOCAL y GOLES_LOCAL > GOLES_VISITANTE)
  │  │                   OR (VISITANTE y GOLES_VISITANTE > GOLES_LOCAL)
  │  ├─ Contar EMPATADOS: GOLES_LOCAL = GOLES_VISITANTE
  │  ├─ Contar PERDIDOS: GOLES_LOCAL < GOLES_VISITANTE (similar)
  │  ├─ Sumar GOLES a favor: si LOCAL → GOLES_LOCAL, si VISITANTE → GOLES_VISITANTE
  │  └─ Sumar GOLES contra: lo opuesto
  ├─ GROUP BY ANIO
  └─ ORDER BY ANIO DESC
```

### Paso 5: Detalles (si p_mostrar_detalles = 'S')

#### 5A: Máximos Goleadores
```
Subquery con ROW_NUMBER() OVER PARTITION BY ANIO
  ├─ Ranking dentro de cada año
  ├─ TOP 3 (WHERE RN <= 3)
  ├─ Mostrar: Año, Jugador, # goles
  └─ Ordenar por ANIO DESC
```

#### 5B: Tarjetas Disciplinarias
```
Suma AMARILLAS y ROJAS por ANIO
  ├─ GROUP BY ANIO
  ├─ Mostrar: Año, # amarillas, # rojas
  └─ Ordenar por ANIO DESC
```

#### 5C: Detalle de Jugadores
```
JOIN DETALLE_JUGADOR con JUGADOR_PAIS
  ├─ Mostrar para CADA jugador:
  │  ├─ Nombre, Año, Posición
  │  ├─ Número de camiseta
  │  ├─ Partidos jugados, goles
  │  ├─ Tarjetas amarillas, tarjetas rojas
  ├─ GROUP BY ANIO, POSICION, NOMBRE
  └─ Ordenar por ANIO DESC, POSICION, NOMBRE
```

---

## Guía de IDs de Países

### Cómo obtenerlos
```sql
SELECT ID_SELECCION, NOMBRE FROM SELECCION ORDER BY ID_SELECCION;
```

### Tabelaompleta (primeros 50)
| ID | País | ID | País |
|----|------|----|----|
| 1 | Alemania | 26 | Dinamarca |
| 2 | Angola | 27 | Escocia |
| 3 | Arabia Saudita | 28 | Eslovaquia |
| 4 | Argelia | 29 | Eslovenia |
| 5 | Australia | 30 | España |
| 6 | Argentina | 31 | Estados Unidos |
| 7 | Austria | 32 | Estonia |
| 8 | Azerbaiyán | 33 | Etiopia |
| 9 | Bahamas | 34 | Filipinas |
| 10 | Bélgica | 35 | Finlandia |
| 11 | Brasil | 36 | Francia |
| 12 | Camerún | 37 | Gales |
| 13 | Canadá | 38 | Georgia |
| 14 | Catar | 39 | Ghana |
| 15 | Chile | 40 | Gibraltar |
| 16 | China | 41 | Grecia |
| 17 | Chipre | 42 | Grenada |
| 18 | Colombia | 43 | Guatemala |
| 19 | Corea del Norte | 44 | Holanda |
| 20 | Corea del Sur | 45 | Honduras |
| 21 | Costa Rica | 46 | Hong Kong |
| 22 | Croacia | 47 | Hungría |
| 23 | Cuba | 48 | India |
| 24 | Curazao | 49 | Indonesia |
| 25 | Dinamarca | 50 | Irán |

---

## Solución de Problemas

### Problema 1: No veo output
**Causa:** DBMS_OUTPUT no está habilitado

**Solución:**
```sql
-- En SQL Developer
View > Dbms Output > Green + button

-- En SQL*Plus
SET ECHO OFF
SET FEEDBACK OFF
```

### Problema 2: ERROR: Año X no encontrado
**Causa:** El año no existe en la tabla MONDIAL

**Solución:**
```sql
-- Ver años disponibles
SELECT DISTINCT ANIO FROM MUNDIAL ORDER BY ANIO;
```

### Problema 3: ERROR: País con ID X no encontrado
**Causa:** El ID no existe en tabla SELECCION

**Solución:**
```sql
-- Buscar el ID correcto
SELECT ID_SELECCION, NOMBRE FROM SELECCION WHERE NOMBRE LIKE '%Argentina%';
```

### Problema 4: No muestra información aunque el país y año existen
**Causa:** El país no participó en ese edición del mundial

**Solución:** Verificar que el país participó en ese año:
```sql
SELECT * FROM POSICION_GRUPO 
WHERE ID_SELECCION = X 
AND ANIO = Y;
```

---

## Notas Importantes

1. **NULL en parámetros opcionales = sin filtro**
   - `EXEC sp_info_mundial(2022, NULL, NULL, NULL)` → Muestra TODO del 2022

2. **DBMS_OUTPUT.PUT_LINE()**
   - Ambos procedures usan esta función para imprimir
   - Asegúrate que esté habilitada en tu IDE

3. **Manejo de errores**
   - Ambos procedures capturan excepciones y muestran mensajes
   - Si cae una exception, imprime el SQLERRM

4. **Rendimiento**
   - Procedures con muchos LOOPs (sp_info_pais con todos los detalles)
   - Pueden tardar un poco si hay muchos datos

5. **LEFT JOINs vs INNER JOINs**
   - Utilizan LEFT JOINs para mostrar datos incluso si falta información relacionada
   - Ejemplo: Mundial sin organizador específico

---

## Verificación de Instalación

```sql
-- Verificar que ambos procedures existen
SELECT OBJECT_NAME, OBJECT_TYPE 
FROM USER_OBJECTS 
WHERE OBJECT_TYPE = 'PROCEDURE' 
AND OBJECT_NAME LIKE 'SP_INFO%'
ORDER BY OBJECT_NAME;

-- Debería retornar:
-- SP_INFO_MUNDIAL    PROCEDURE
-- SP_INFO_PAIS       PROCEDURE
```

---

## Relación entre los Procedures

```
        MUNDIAL 2022
           /      \
          /        \
    sp_info_mundial  sp_info_pais(p_anio=2022)
        |                    |
        │                    │
    "Dame TODO              "Dame TODO
     sobre 2022"            de ARGENTINA
     (32 países)             (en 2022 y otros años)"
        │                    │
        ├─ 8 Grupos         ├─ 17 mundiales
        ├─ 64 partidos      ├─ Estadísticas históricas
        ├─ Top goleadores   └─ Detalles de jugadores
        └─ Estadísticas
```

---

## Contacto/Soporte

Para problemascon estos procedures:
1. Revisar las queries originales en `sp_info_mundial.sql` y `sp_info_pais.sql`
2. Verificar estructura de tablas (`DESC MUNDIAL`, `DESC SELECCION`, etc.)
3. Comprobar que los datos existan en la base de datos

---

**Última actualización:** 20 de marzo de 2026
**Versión:** 2.0 (Completamente documentada - Sin emojis)
