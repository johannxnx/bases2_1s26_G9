/*
================================================================================
PROCEDIMIENTO: sp_info_mundial
================================================================================
DESCRIPCIÓN:
    Genera un reporte completo sobre un Mundial de Fútbol. El reporte incluye
    información general del torneo, clasificación de grupos, detalles de partidos
    y ranking de máximos goleadores.

PARAMETROS DE ENTRADA:
    p_anio          (NUMBER, REQUERIDO):
        - Año del Mundial a consultar
        - Ejemplo: 2022, 2018, 2014, etc.
        
    p_id_grupo      (VARCHAR2, OPCIONAL, DEFAULT NULL):
        - Identificador del grupo a filtrar (ej: 'A', 'B', 'C', etc.)
        - Si es NULL, muestra información de todos los grupos
        - Filtra tanto en sección de grupos como en partidos
        
    p_id_seleccion  (NUMBER, OPCIONAL, DEFAULT NULL):
        - ID de la selección para filtrar información específica
        - Si es NULL, muestra todas las selecciones
        - Filtra en grupos, partidos y goleadores
        
    p_etapa         (VARCHAR2, OPCIONAL, DEFAULT NULL):
        - Etapa del torneo a filtrar (ej: 'Grupo', 'Octavos', 'Cuartos', etc.)
        - Si es NULL, muestra todas las etapas
        - Solo afecta a la sección de partidos

SALIDA:
    Reporte formateado mediante DBMS_OUTPUT con información estructurada
    por secciones (información general, grupos, partidos, goleadores)

MANEJO DE ERRORES:
    - Valida que el año exista en la tabla MUNDIAL
    - OTHERS: Error general capturado

TABLAS UTILIZADAS:
    - MUNDIAL: Información general del torneo (organizador, campeón, estadísticas)
    - SELECCION: Datos de países/selecciones
    - GRUPO: Definición de grupos y selecciones por grupo
    - POSICION_GRUPO: Clasificación de selecciones en la fase de grupos
    - PARTIDO: Detalles de los partidos (fechas, resultados, etapas)
    - GOLEADOR: Máximos goleadores del torneo
    - JUGADOR_PAIS: Información de jugadores

FECHA DE CREACIÓN: 20/03/2026
================================================================================
*/

CREATE OR REPLACE PROCEDURE sp_info_mundial (
    p_anio          IN NUMBER,
    p_id_grupo      IN VARCHAR2 DEFAULT NULL,
    p_id_seleccion  IN NUMBER DEFAULT NULL,
    p_etapa         IN VARCHAR2 DEFAULT NULL
)
AS
    -- Variable auxiliar para validación de año
    v_count NUMBER;
BEGIN
    -- Verifica que el año del mundial exista en la base de datos
    SELECT COUNT(*) INTO v_count FROM MUNDIAL WHERE ANIO = p_anio;
    IF v_count = 0 THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: Año ' || p_anio || ' no encontrado.');
        RETURN;
    END IF;

    -- ========== SECCIÓN 1: INFORMACIÓN GENERAL DEL MUNDIAL ==========
    -- Muestra datos generales: organizador, campeón, número de selecciones,
    -- partidos, goles totales y promedio de goles por partido
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');
    DBMS_OUTPUT.PUT_LINE('MUNDIAL ' || p_anio);
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');

    FOR rec IN (
        -- Obtiene información general del mundial
        SELECT
            s_org.NOMBRE AS ORGANIZADOR,  -- País sede del torneo
            s_cam.NOMBRE AS CAMPEON,      -- País campeón
            m.NUM_SELECCIONES,            -- Cantidad de países participantes
            m.NUM_PARTIDOS,               -- Total de partidos jugados
            m.GOLES,                      -- Goles totales marcados en el torneo
            m.PROMEDIO_GOL                -- Promedio de goles por partido
        FROM MUNDIAL m
        LEFT JOIN SELECCION s_org ON m.ID_ORGANIZADOR = s_org.ID_SELECCION
        LEFT JOIN SELECCION s_cam ON m.ID_CAMPEON = s_cam.ID_SELECCION
        WHERE m.ANIO = p_anio
    ) LOOP
        DBMS_OUTPUT.PUT_LINE('Organizador: ' || rec.ORGANIZADOR);
        DBMS_OUTPUT.PUT_LINE('Campeón: '     || rec.CAMPEON);
        DBMS_OUTPUT.PUT_LINE('Selecciones: ' || rec.NUM_SELECCIONES);
        DBMS_OUTPUT.PUT_LINE('Partidos: '    || rec.NUM_PARTIDOS);
        DBMS_OUTPUT.PUT_LINE('Goles totales: '|| rec.GOLES);
        DBMS_OUTPUT.PUT_LINE('Promedio goles por partido: ' || rec.PROMEDIO_GOL);
    END LOOP;

    -- ========== SECCIÓN 2: FASE DE GRUPOS ==========
    -- Muestra la clasificación de cada grupo con estadísticas de cada selección
    -- PJ=Partidos Jugados, PG=Partidos Ganados, PE=Partidos Empatados, PP=Perdidos
    -- GF=Goles a Favor, GC=Goles en Contra, DIF=Diferencia de goles, PTS=Puntos
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');
    DBMS_OUTPUT.PUT_LINE('GRUPOS');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    FOR rec_grupo IN (
        -- Obtiene lista de grupos del año, con filtro opcional por grupo específico
        SELECT DISTINCT ID_GRUPO, SELECCIONES
        FROM GRUPO
        WHERE ANIO = p_anio
        AND (p_id_grupo IS NULL OR ID_GRUPO = p_id_grupo)
        ORDER BY ID_GRUPO
    ) LOOP
        DBMS_OUTPUT.PUT_LINE('');
        -- Muestra nombre del grupo y cantidad de selecciones en él
        DBMS_OUTPUT.PUT_LINE('GRUPO ' || rec_grupo.ID_GRUPO || ': ' || rec_grupo.SELECCIONES);

        FOR rec_pos IN (
            -- Obtiene la clasificación de cada selección en el grupo, ordenada por puntos
            -- y diferencia de goles (criterio de desempate en competencias reales)
            SELECT
                s.NOMBRE,
                pg.PJ,          -- Partidos jugados
                pg.PG,          -- Partidos ganados
                pg.PE,          -- Partidos empatados
                pg.PP,          -- Partidos perdidos
                pg.GF,          -- Goles a favor
                pg.GC,          -- Goles en contra
                pg.DIFERENCIA,  -- Diferencia de goles (GF - GC)
                pg.PTS,         -- Puntos totales (victoria=3, empate=1, derrota=0)
                DECODE(pg.CLASIFICADO, 'SI', 'Clasificado', 'NO', 'Eliminado', pg.CLASIFICADO) AS CLASIFICADO
            FROM POSICION_GRUPO pg
            JOIN SELECCION s ON pg.ID_SELECCION = s.ID_SELECCION
            WHERE pg.ANIO = p_anio
            AND pg.ID_GRUPO = rec_grupo.ID_GRUPO
            AND (p_id_seleccion IS NULL OR pg.ID_SELECCION = p_id_seleccion)
            -- Ordena por puntos descendente, luego por diferencia de goles
            ORDER BY pg.PTS DESC, pg.DIFERENCIA DESC
        ) LOOP
            DBMS_OUTPUT.PUT_LINE('  ' || RPAD(rec_pos.NOMBRE, 25) ||
                ' PJ:' || rec_pos.PJ ||
                ' PG:' || rec_pos.PG ||
                ' PE:' || rec_pos.PE ||
                ' PP:' || rec_pos.PP ||
                ' GF:' || rec_pos.GF ||
                ' GC:' || rec_pos.GC ||
                ' DIF:' || rec_pos.DIFERENCIA ||
                ' PTS:' || rec_pos.PTS ||
                ' ' || rec_pos.CLASIFICADO);
        END LOOP;
    END LOOP;

    -- ========== SECCIÓN 3: DETALLE DE PARTIDOS ==========
    -- Muestra todos los partidos del torneo con resultados, fecha y etapa
    -- Incluye información de penales si aplica
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');
    DBMS_OUTPUT.PUT_LINE('PARTIDOS');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    FOR rec_partido IN (
        -- Obtiene detalles de todos los partidos con filtros opcionales
        -- Los filtros pueden ser por grupo, selección específica y/o etapa
        SELECT
            p.FECHA,              -- Fecha del partido
            p.ETAPA,              -- Etapa (Grupo, Octavos, Cuartos, Semis, Final)
            s_local.NOMBRE AS LOCAL,      -- Equipo local
            s_visit.NOMBRE AS VISITANTE,  -- Equipo visitante
            p.GOLES_LOCAL,        -- Goles del local
            p.GOLES_VISITANTE,    -- Goles del visitante
            -- Información de penales (aparece solo si el partido se definió por penales)
            DECODE(p.PENALES, 'Si', ' (' || p.PENALES_LOCAL || '-' || p.PENALES_VISITANTE || ' pen)', '') AS PENALES_STR
        FROM PARTIDO p
        LEFT JOIN SELECCION s_local ON p.ID_LOCAL  = s_local.ID_SELECCION
        LEFT JOIN SELECCION s_visit ON p.ID_VISITANTE = s_visit.ID_SELECCION
        WHERE p.ANIO = p_anio
        -- Filtra por grupo si se proporciona (partidos de selecciones del grupo)
        AND (p_id_grupo IS NULL OR
             p.ID_LOCAL IN (SELECT ID_SELECCION FROM POSICION_GRUPO
                            WHERE ANIO = p_anio AND ID_GRUPO = p_id_grupo)
             OR
             p.ID_VISITANTE IN (SELECT ID_SELECCION FROM POSICION_GRUPO
                                WHERE ANIO = p_anio AND ID_GRUPO = p_id_grupo))
        -- Filtra por selección si se proporciona (solo partidos de esa país)
        AND (p_id_seleccion IS NULL OR p.ID_LOCAL = p_id_seleccion OR p.ID_VISITANTE = p_id_seleccion)
        -- Filtra por etapa si se proporciona (grup, octavos, cuartos, etc.)
        AND (p_etapa IS NULL OR p.ETAPA = p_etapa)
        -- Ordena por fecha y número de partido
        ORDER BY p.FECHA, p.NUM_PARTIDO
    ) LOOP
        -- Muestra resultado en formato: LOCAL Goles-Goles VISITANTE [Fecha | Etapa] (info penales)
        DBMS_OUTPUT.PUT_LINE(
            RPAD(rec_partido.LOCAL, 22) || ' ' ||
            rec_partido.GOLES_LOCAL || '-' || rec_partido.GOLES_VISITANTE || ' ' ||
            RPAD(rec_partido.VISITANTE, 22) ||
            '  [' || rec_partido.FECHA || ' | ' || rec_partido.ETAPA || ']' ||
            rec_partido.PENALES_STR
        );
    END LOOP;

    -- ========== SECCIÓN 4: MÁXIMOS GOLEADORES DEL TORNEO ==========
    -- Muestra los jugadores que más goles marcaron en el torneo
    -- Incluye jugador, su selección, cantidad de goles y promedio
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');
    DBMS_OUTPUT.PUT_LINE('TOP GOLEADORES');
    DBMS_OUTPUT.PUT_LINE('────────────────────────────────────────────────────────────');

    FOR rec_gol IN (
        -- Obtiene lista de goleadores ordenados por cantidad de goles (descendente)
        -- Como desempate usa el promedio de goles (promedio descendente)
        SELECT
            jp.NOMBRE AS JUGADOR,   -- Nombre del jugador
            s.NOMBRE  AS SELECCION, -- País al que representa
            g.GOLES,                -- Total de goles en el torneo
            g.PARTIDOS,             -- Partidos que participó
            g.PROMEDIO              -- Promedio de goles por partido
        FROM GOLEADOR g
        JOIN JUGADOR_PAIS jp ON g.ID_JUGADOR    = jp.ID_JUGADOR
        JOIN SELECCION    s  ON g.ID_SELECCION  = s.ID_SELECCION
        WHERE g.ANIO = p_anio
        -- Filtra por selección si se proporciona
        AND (p_id_seleccion IS NULL OR g.ID_SELECCION = p_id_seleccion)
        -- Ordena por cantidad de goles descendente, promedio como desempate
        ORDER BY g.GOLES DESC, g.PROMEDIO DESC
    ) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || RPAD(rec_gol.JUGADOR, 25) ||
            ' (' || rec_gol.SELECCION || ') - ' ||
            rec_gol.GOLES || ' goles en ' || rec_gol.PARTIDOS || ' partidos');
    END LOOP;

    -- Pie del reporte
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('════════════════════════════════════════════════════════════');

-- ========== MANEJO DE ERRORES ==========
EXCEPTION
    -- OTHERS: Captura cualquier error no previsto durante la ejecución
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: ' || SQLERRM);
END sp_info_mundial;
/