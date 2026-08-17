/*
================================================================================
PROCEDIMIENTO: sp_info_pais
================================================================================
DESCRIPCIÓN:
    Genera un reporte completo de información sobre una selección de país en los
    Mundiales de Fútbol. El reporte incluye historial de participación, 
    desempeño por año, goleadores, tarjetas disciplinarias y detalle de jugadores.

PARÁMETROS DE ENTRADA:
    p_id_seleccion     (NUMBER, REQUERIDO):
        - Identificador único de la selección/país
        - Referencia a la tabla SELECCION
        
    p_anio             (NUMBER, OPCIONAL, DEFAULT NULL):
        - Año específico para filtrar la información
        - Si es NULL, se muestran todos los años disponibles
        
    p_mostrar_detalles (VARCHAR2, OPCIONAL, DEFAULT 'S'):
        - 'S': Muestra información detallada (goleadores, tarjetas, jugadores)
        - Cualquier otro valor: Solo muestra resumen general

SALIDA:
    Reporte formateado mediante DBMS_OUTPUT con información estructurada
    por secciones (años, sede, desempeño, detalles)

MANEJO DE ERRORES:
    - NO_DATA_FOUND: País con ID no encontrado
    - OTHERS: Error general

TABLAS UTILIZADAS:
    - SELECCION: Obtiene nombre del país
    - POSICION_GRUPO: Historial de participación en grupos
    - POSICION_FINAL: Posición final en el mundial
    - MUNDIAL: Información sobre los mundiales (sedes)
    - PARTIDO: Detalles de partidos (goles, resultados)
    - GOLEADOR: Máximos goleadores por año
    - JUGADOR_PAIS: Información de jugadores
    - TARJETA: Tarjetas disciplinarias
    - DETALLE_JUGADOR: Información detallada de jugadores en mundiales

FECHA DE CREACIÓN: 20/03/2026
================================================================================
*/

CREATE OR REPLACE PROCEDURE sp_info_pais (
    p_id_seleccion     IN NUMBER,
    p_anio             IN NUMBER   DEFAULT NULL,
    p_mostrar_detalles IN VARCHAR2 DEFAULT 'S'
)
AS
    -- Variables locales
    v_nombre_pais VARCHAR2(100);  -- Almacena el nombre de la selección/país
    v_count       NUMBER;         -- Contador auxiliar para validaciones
BEGIN
    -- Obtiene el nombre de la selección desde la tabla SELECCION
    -- Si no existe lanzará NO_DATA_FOUND manejada en EXCEPTION
    SELECT NOMBRE INTO v_nombre_pais
    FROM SELECCION WHERE ID_SELECCION = p_id_seleccion;

    -- Imprime encabezado del reporte
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');
    DBMS_OUTPUT.PUT_LINE('INFORMACIÓN DE ' || UPPER(v_nombre_pais));
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');

    -- ========== SECCIÓN 1: AÑOS DE PARTICIPACIÓN ==========
    -- Muestra un listado de todos los años en que el país ha participado
    -- con su posición final (Campeón, Subcampeón, Semifinalista, etc.)
    -- Consulta: JOIN entre POSICION_GRUPO y POSICION_FINAL para obtener datos
    -- Ordenado por año descendente (de más reciente a más antiguo)
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('AÑOS DE PARTICIPACIÓN:');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    FOR rec_anio IN (
        -- Selecciona años distintos con posición final
        -- LEFT JOIN permite mostrar años sin posición final registrada
        SELECT DISTINCT pg.ANIO, pf.POSICION
        FROM POSICION_GRUPO pg
        LEFT JOIN POSICION_FINAL pf
            ON pg.ANIO = pf.ANIO AND pg.ID_SELECCION = pf.ID_SELECCION
        WHERE pg.ID_SELECCION = p_id_seleccion
        AND (p_anio IS NULL OR pg.ANIO = p_anio)
        ORDER BY pg.ANIO DESC
    ) LOOP
        -- Muestra año con clasificación descriptiva según posición final:
        -- Posición 1: CAMPEÓN | Posición 2: Subcampeón | Posiciones 3-4: Semifinalista
        DBMS_OUTPUT.PUT_LINE('  ' || rec_anio.ANIO ||
            CASE WHEN rec_anio.POSICION = 1 THEN '  CAMPEÓN'
                 WHEN rec_anio.POSICION = 2 THEN '  Subcampeón'
                 WHEN rec_anio.POSICION <= 4 THEN '  Semifinalista'
                 ELSE '  (Posición: ' || rec_anio.POSICION || ')'
            END);
    END LOOP;

    -- ========== SECCIÓN 2: SEDE (MUNDIALES ORGANIZADOS) ==========
    -- Muestra los años en que el país fue organizador/sede de un Mundial
    -- Si nunca fue sede, muestra un mensaje indicando esto
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('SEDE DE MUNDIALES:');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    -- Verifica si el país ha sido organizador de algún mundial
    SELECT COUNT(*) INTO v_count FROM MUNDIAL WHERE ID_ORGANIZADOR = p_id_seleccion;

    IF v_count > 0 THEN
        -- Si fue organizador, lista todos los años en que organizó mundiales
        FOR rec_sede IN (
            SELECT ANIO FROM MUNDIAL WHERE ID_ORGANIZADOR = p_id_seleccion ORDER BY ANIO
        ) LOOP
            DBMS_OUTPUT.PUT_LINE('  Organizador en ' || rec_sede.ANIO);
        END LOOP;
    ELSE
        -- Si nunca fue organizador, muestra este mensaje
        DBMS_OUTPUT.PUT_LINE('  No ha sido sede');
    END IF;

    -- ========== SECCIÓN 3: DESEMPEÑO POR MUNDIAL ==========
    -- Muestra estadísticas detalladas de cada mundial: partidos jugados, ganados,
    -- empatados, perdidos, goles a favor y goles en contra
    -- Utiliza CASE statements para contar resultados según si el país fue local o visitante
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('DESEMPEÑO POR MUNDIAL:');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    FOR rec_desem IN (
        SELECT
            m.ANIO,
            -- Cuenta todos los partidos donde el país participó (como local o visitante)
            COUNT(CASE WHEN (p.ID_LOCAL = p_id_seleccion OR p.ID_VISITANTE = p_id_seleccion) THEN 1 END) AS PARTIDOS,
            -- Cuenta partidos ganados: verificando si fue local y ganó, o visitante y ganó
            SUM(CASE WHEN (p.ID_LOCAL = p_id_seleccion AND p.GOLES_LOCAL > p.GOLES_VISITANTE)
                     OR   (p.ID_VISITANTE = p_id_seleccion AND p.GOLES_VISITANTE > p.GOLES_LOCAL)
                     THEN 1 ELSE 0 END) AS GANADOS,
            -- Cuenta partidos empatados
            SUM(CASE WHEN (p.ID_LOCAL = p_id_seleccion AND p.GOLES_LOCAL = p.GOLES_VISITANTE)
                     OR   (p.ID_VISITANTE = p_id_seleccion AND p.GOLES_VISITANTE = p.GOLES_LOCAL)
                     THEN 1 ELSE 0 END) AS EMPATADOS,
            -- Cuenta partidos perdidos
            SUM(CASE WHEN (p.ID_LOCAL = p_id_seleccion AND p.GOLES_LOCAL < p.GOLES_VISITANTE)
                     OR   (p.ID_VISITANTE = p_id_seleccion AND p.GOLES_VISITANTE < p.GOLES_LOCAL)
                     THEN 1 ELSE 0 END) AS PERDIDOS,
            -- Suma goles a favor (según si fue local o visitante)
            SUM(CASE WHEN p.ID_LOCAL     = p_id_seleccion THEN p.GOLES_LOCAL
                     WHEN p.ID_VISITANTE = p_id_seleccion THEN p.GOLES_VISITANTE
                     ELSE 0 END) AS GOLES,
            -- Suma goles en contra (goles del equipo adversario)
            SUM(CASE WHEN p.ID_LOCAL     = p_id_seleccion THEN p.GOLES_VISITANTE
                     WHEN p.ID_VISITANTE = p_id_seleccion THEN p.GOLES_LOCAL
                     ELSE 0 END) AS GOLES_CONTRA
        FROM MUNDIAL m
        LEFT JOIN PARTIDO p ON m.ANIO = p.ANIO
        WHERE (p.ID_LOCAL = p_id_seleccion OR p.ID_VISITANTE = p_id_seleccion OR p.ANIO IS NULL)
        AND (p_anio IS NULL OR m.ANIO = p_anio)
        GROUP BY m.ANIO
        ORDER BY m.ANIO DESC
    ) LOOP
        -- Solo muestra años donde hubo partidos jugados
        IF rec_desem.PARTIDOS > 0 THEN
            DBMS_OUTPUT.PUT_LINE('  ' || rec_desem.ANIO || ': ' ||
                rec_desem.PARTIDOS || 'PJ | ' ||  -- PJ: Partidos Jugados
                rec_desem.GANADOS  || 'G '    ||  -- G: Ganados
                rec_desem.EMPATADOS|| 'E '    ||  -- E: Empatados
                rec_desem.PERDIDOS || 'P | '  ||  -- P: Perdidos
                rec_desem.GOLES    || 'GF - ' ||  -- GF: Goles a Favor
                rec_desem.GOLES_CONTRA || 'GC');  -- GC: Goles en Contra
        END IF;
    END LOOP;

    -- ========== SECCIÓN 4: DETALLES (Opcional) ==========
    -- Esta sección se muestra solo si p_mostrar_detalles = 'S' (valor por defecto)
    -- Incluye: Máximos goleadores, Tarjetas disciplinarias, Detalle de jugadores
    IF p_mostrar_detalles = 'S' THEN

        -- ========== SUBSECCIÓN 4.1: GOLEADORES ==========
        -- Muestra los 3 máximos goleadores por año
        -- Utiliza ROW_NUMBER() OVER para ranking dentro de cada año
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('MÁXIMOS GOLEADORES:');
        DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

        FOR rec_gol IN (
            SELECT ANIO, NOMBRE AS JUGADOR, GOLES
            FROM (
                -- Subquery: Asigna ranking a goleadores por año
                SELECT
                    g.ANIO,
                    jp.NOMBRE,
                    g.GOLES,
                    -- ROW_NUMBER() asigna número secuencial ordenado por goles descendente
                    -- Se reinicia para cada año (PARTITION BY ANIO)
                    ROW_NUMBER() OVER (PARTITION BY g.ANIO ORDER BY g.GOLES DESC) AS RN
                FROM GOLEADOR g
                JOIN JUGADOR_PAIS jp ON g.ID_JUGADOR = jp.ID_JUGADOR
                WHERE g.ID_SELECCION = p_id_seleccion
                AND (p_anio IS NULL OR g.ANIO = p_anio)
            )
            -- Filtra para mostrar solo los 3 principales (RN <= 3)
            WHERE RN <= 3
            ORDER BY ANIO DESC
        ) LOOP
            DBMS_OUTPUT.PUT_LINE('  ' || rec_gol.ANIO || ': ' ||
                RPAD(rec_gol.JUGADOR, 25) || ' - ' || rec_gol.GOLES || ' goles');
        END LOOP;

        -- ========== SUBSECCIÓN 4.2: TARJETAS DISCIPLINARIAS ==========
        -- Muestra el conteo total de tarjetas amarillas y rojas por año
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('TARJETAS DISCIPLINARIAS:');
        DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

        FOR rec_tarjeta IN (
            -- Suma tarjetas por año
            SELECT
                ANIO,
                SUM(AMARILLAS) AS AMARILLAS,
                SUM(ROJAS)     AS ROJAS
            FROM TARJETA
            WHERE ID_SELECCION = p_id_seleccion
            AND (p_anio IS NULL OR ANIO = p_anio)
            GROUP BY ANIO
            ORDER BY ANIO DESC
        ) LOOP
            DBMS_OUTPUT.PUT_LINE('  ' || rec_tarjeta.ANIO || ': ' ||
                rec_tarjeta.AMARILLAS || ' amarillas | ' ||
                rec_tarjeta.ROJAS     || ' rojas');
        END LOOP;

        -- ========== SUBSECCIÓN 4.3: DETALLE DE JUGADORES ==========
        -- Muestra información completa de cada jugador en cada mundial:
        -- Nombre, año, posición, número de camiseta, partidos, goles y tarjetas
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('DETALLE DE JUGADORES:');
        DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

        FOR rec_jug IN (
            SELECT
                jp.NOMBRE,
                dj.ANIO,
                dj.POSICION,
                dj.CAMISETA,
                dj.JUGO,           -- Partidos jugados
                dj.JUGO_TITULAR,   -- Partidos como titular
                dj.GOLES,
                dj.TARJETA_AMARILLA,
                dj.TARJETA_ROJA
            FROM DETALLE_JUGADOR dj
            JOIN JUGADOR_PAIS jp ON dj.ID_JUGADOR = jp.ID_JUGADOR
            WHERE jp.ID_SELECCION = p_id_seleccion
            AND (p_anio IS NULL OR dj.ANIO = p_anio)
            -- Ordena: primero por año descendente, luego por posición, luego por nombre
            ORDER BY dj.ANIO DESC, dj.POSICION, jp.NOMBRE
        ) LOOP
            DBMS_OUTPUT.PUT_LINE('  ' || rec_jug.ANIO || ' | ' ||
                RPAD(rec_jug.NOMBRE, 25)   || ' | ' ||
                RPAD(NVL(rec_jug.POSICION, '-'), 12) || ' | ' ||
                'Camiseta: ' || NVL(TO_CHAR(rec_jug.CAMISETA), '-') || ' | ' ||
                'Partidos: ' || NVL(TO_CHAR(rec_jug.JUGO), '0')     || ' | ' ||
                'Goles: '    || NVL(TO_CHAR(rec_jug.GOLES), '0')    || ' | ' ||
                'TA: ' || NVL(TO_CHAR(rec_jug.TARJETA_AMARILLA), '0') ||
                ' TR: ' || NVL(TO_CHAR(rec_jug.TARJETA_ROJA), '0'));
        END LOOP;

    END IF;

    -- Pie del reporte
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');

-- ========== MANEJO DE ERRORES ==========
EXCEPTION
    -- NO_DATA_FOUND: Se lanza cuando no existe registro en la tabla SELECCION
    --                 con el ID proporcionado
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: País con ID ' || p_id_seleccion || ' no encontrado.');
    -- OTHERS: Captura cualquier otro error no previsto
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: ' || SQLERRM);
END sp_info_pais;
/