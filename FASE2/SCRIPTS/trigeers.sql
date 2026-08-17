/* ============================================================ */
/* ARCHIVO DE TRIGGERS DE AUDITORIA                             */
/* Cada trigger registra INSERT, UPDATE, DELETE en tabla LOG    */
/* ============================================================ */

/* ============================================================ */
/* 1.  SELECCION - Auditoría de cambios en tabla SELECCION     */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_SELECCION_INSERT DISABLE;
-- Desactiva trigger anterior (se reemplazará con nuevo)

-- Crea trigger que registra cada cambio (INSERT, UPDATE, DELETE) en tabla SELECCION
-- Se ejecuta DESPUÉS de la operación, para cada fila modificada
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_SELECCION_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.SELECCION
FOR EACH ROW
DECLARE
    -- Variable local que almacenará el tipo de operación
    v_op VARCHAR2(10);
BEGIN
    -- Detecta qué tipo de operación se realizó y la guarda en v_op
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    -- Inserta registro de auditoría en tabla de LOG correspondiente
    INSERT INTO PROYECTO2BASES2.LOG_SELECCION
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_SELECCION.NEXTVAL,  -- ID único generado secuencialmente
            SYSTIMESTAMP,                                 -- Fecha/hora actual
            v_op,                                        -- Tipo de operación
            1,                                           -- Cantidad de registros afectados
            0,                                           -- Fragmentación (sin fragmentación)
            'Trigger auto '||v_op);                      -- Descripción del evento
END;
/ 
-- Habilita el trigger para que quede activo
ALTER TRIGGER PROYECTO2BASES2.TRG_SELECCION_LOG ENABLE;

/* ============================================================ */
/* 2.  MUNDIAL - Auditoría de cambios en tabla MUNDIAL         */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_MUNDIAL_INSERT DISABLE;

CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_MUNDIAL_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.MUNDIAL
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    -- Determina el tipo de operación (INSERT, UPDATE o DELETE)
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    -- Registra el evento de cambio en la tabla de auditoría LOG_MUNDIAL
    INSERT INTO PROYECTO2BASES2.LOG_MUNDIAL
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_MUNDIAL.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_MUNDIAL_LOG ENABLE;

/* ============================================================ */
/* 3.  PARTIDO - Auditoría de cambios en tabla PARTIDO         */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_PARTIDO_INSERT DISABLE;

-- Trigger que registra INSERT, UPDATE, DELETE en tabla PARTIDO
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_PARTIDO_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.PARTIDO
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    -- Identifica el tipo de operación realizada
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    -- Registra la operación en LOG_PARTIDO con timestamp y tipo de cambio
    INSERT INTO PROYECTO2BASES2.LOG_PARTIDO
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_PARTIDO.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_PARTIDO_LOG ENABLE;

/* ============================================================ */
/* 4.  JUGADOR_PAIS - Auditoría de cambios en JUGADOR_PAIS    */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_JUGADOR_PAIS_INSERT DISABLE;

-- Registra cambios en relación entre jugadores y países
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_JUGADOR_PAIS_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.JUGADOR_PAIS
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_JUGADOR_PAIS
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_JUGADOR_PAIS.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_JUGADOR_PAIS_LOG ENABLE;

/* ============================================================ */
/* 5.  GOL - Auditoría de cambios en tabla GOL                */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_GOL_INSERT DISABLE;

-- Registra inserciones, actualizaciones y eliminaciones de goles
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_GOL_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.GOL
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_GOL
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_GOL.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_GOL_LOG ENABLE;

/* ============================================================ */
/* 6.  DETALLE_JUGADOR - Auditoría de detalles del jugador    */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_DETALLE_JUGADOR_INSERT DISABLE;

-- Registra cambios en información detallada de jugadores
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_DETALLE_JUGADOR_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.DETALLE_JUGADOR
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_DETALLE_JUGADOR
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_DETALLE_JUGADOR.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_DETALLE_JUGADOR_LOG ENABLE;

/* ============================================================ */
/* 7.  EQUIPO_IDEAL - Auditoría del equipo ideal              */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_EQUIPO_IDEAL_INSERT DISABLE;

-- Registra cambios en el equipo ideal (formación destacada)
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_EQUIPO_IDEAL_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.EQUIPO_IDEAL
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_EQUIPO_IDEAL
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_EQUIPO_IDEAL.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_EQUIPO_IDEAL_LOG ENABLE;

/* ============================================================ */
/* 8.  GOLEADOR - Auditoría de tabla GOLEADOR               */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_GOLEADOR_INSERT DISABLE;

-- Registra cambios en información de goleadores
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_GOLEADOR_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.GOLEADOR
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_GOLEADOR
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_GOLEADOR.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_GOLEADOR_LOG ENABLE;

/* ============================================================ */
/* 9.  POSICION_GRUPO - Auditoría de posiciones en grupos    */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_POSICION_GRUPO_INSERT DISABLE;

-- Registra cambios en tabla de posiciones de grupo
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_POSICION_GRUPO_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.POSICION_GRUPO
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_POSICION_GRUPO
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_POSICION_GRUPO.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_POSICION_GRUPO_LOG ENABLE;

/* ============================================================ */
/* 10. POSICION_FINAL - Auditoría de posiciones finales       */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_POSICION_FINAL_INSERT DISABLE;

-- Registra cambios en clasificación final de equipos
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_POSICION_FINAL_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.POSICION_FINAL
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_POSICION_FINAL
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_POSICION_FINAL.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_POSICION_FINAL_LOG ENABLE;

/* ============================================================ */
/* 11. GRUPO - Auditoría de tabla GRUPO                      */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_GRUPO_INSERT DISABLE;

-- Registra cambios en información de grupos
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_GRUPO_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.GRUPO
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_GRUPO
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_GRUPO.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_GRUPO_LOG ENABLE;

/* ============================================================ */
/* 12. PREMIO - Auditoría de tabla PREMIO                    */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_PREMIO_INSERT DISABLE;

-- Registra cambios en información de premios/distinciones
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_PREMIO_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.PREMIO
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_PREMIO
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_PREMIO.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_PREMIO_LOG ENABLE;

/* ============================================================ */
/* 13. TARJETA - Auditoría de tabla TARJETA                  */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_TARJETA_INSERT DISABLE;

-- Registra cambios en información de tarjetas (rojas/amarillas)
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_TARJETA_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.TARJETA
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_TARJETA
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_TARJETA.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_TARJETA_LOG ENABLE;

/* ============================================================ */
/* 14. TIPO_PREMIO - Auditoría de tipos de premio             */
/* ============================================================ */
ALTER TRIGGER PROYECTO2BASES2.TRG_TIPO_PREMIO_INSERT DISABLE;

-- Registra cambios en tabla de categorías de premios
CREATE OR REPLACE TRIGGER PROYECTO2BASES2.TRG_TIPO_PREMIO_LOG
AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.TIPO_PREMIO
FOR EACH ROW
DECLARE
    v_op VARCHAR2(10);
BEGIN
    IF INSERTING THEN
        v_op := 'INSERT';
    ELSIF UPDATING THEN
        v_op := 'UPDATE';
    ELSIF DELETING THEN
        v_op := 'DELETE';
    END IF;

    INSERT INTO PROYECTO2BASES2.LOG_TIPO_PREMIO
           (ID_LOG, FECHA_REGISTRO, OPERACION,
            CANTIDAD_REGISTROS, FRAGMENTACION_PORCENT, DESCRIPCION)
    VALUES (PROYECTO2BASES2.SEQ_LOG_TIPO_PREMIO.NEXTVAL,
            SYSTIMESTAMP,
            v_op,
            1,
            0,
            'Trigger auto '||v_op);
END;
/ 
ALTER TRIGGER PROYECTO2BASES2.TRG_TIPO_PREMIO_LOG ENABLE;
