-- ============================================================
-- PROYECTO FASE 1 - Sistemas de Bases de Datos 2
-- Oracle 21c - Script 01: Creación de tablas
-- ============================================================

BEGIN
    FOR t IN (
        SELECT table_name FROM user_tables
        WHERE table_name IN (
            'EQUIPO_IDEAL','TARJETA','PREMIO','POSICION_FINAL',
            'GOLEADOR','GOL','POSICION_GRUPO','PARTIDO',
            'GRUPO','JUGADOR_PAIS','MUNDIAL','SELECCION'
        )
    ) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
    END LOOP;
END;
/

-- ============================================================
-- 1. SELECCION
-- ============================================================
CREATE TABLE SELECCION (
    ID_SELECCION    NUMBER          NOT NULL,
    NOMBRE          VARCHAR2(100)   NOT NULL,
    CONSTRAINT PK_SELECCION PRIMARY KEY (ID_SELECCION)
);

-- ============================================================
-- 2. JUGADOR_PAIS
-- ============================================================
CREATE TABLE JUGADOR_PAIS ( -- agregar info, posicion, camiseta, nacimiento, nacionalidades, lugar de nacimiento, altura, 
    ID_JUGADOR      NUMBER          NOT NULL,
    NOMBRE          VARCHAR2(200)   NOT NULL,
    ID_SELECCION    NUMBER          NOT NULL,
    SELECCION       VARCHAR2(100), -- es redundante ya 
    CONSTRAINT PK_JUGADOR_PAIS PRIMARY KEY (ID_JUGADOR),
    CONSTRAINT FK_JUGADOR_SEL  FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION)
);

-- otra tabla que relacione jugadores con el mundial (muchos a muchos)

-- ============================================================
-- 3. MUNDIAL
-- ============================================================
CREATE TABLE MUNDIAL (
    ANIO                NUMBER(4)       NOT NULL,
    ID_ORGANIZADOR      NUMBER,
    ORGANIZADOR         VARCHAR2(100), 
    ID_CAMPEON          NUMBER,
    CAMPEON             VARCHAR2(100),
    NUM_SELECCIONES     NUMBER,
    NUM_PARTIDOS        NUMBER,
    GOLES               NUMBER,
    PROMEDIO_GOL        NUMBER(5,2),
    CONSTRAINT PK_MUNDIAL     PRIMARY KEY (ANIO),
    CONSTRAINT FK_MUN_ORG     FOREIGN KEY (ID_ORGANIZADOR)
        REFERENCES SELECCION(ID_SELECCION),
    CONSTRAINT FK_MUN_CAMPEON FOREIGN KEY (ID_CAMPEON)
        REFERENCES SELECCION(ID_SELECCION)
);

-- ============================================================
-- 4. GRUPO
-- ============================================================
CREATE TABLE GRUPO (
    ANIO            NUMBER(4)       NOT NULL,
    ID_GRUPO        VARCHAR2(5)     NOT NULL, --1,2,3,4, o 1,b,c,d,e
    SELECCIONES     VARCHAR2(500),

    CONSTRAINT PK_GRUPO PRIMARY KEY (ANIO, ID_GRUPO),

    CONSTRAINT FK_GRUPO_MUN FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO)
);

-- ============================================================
-- 5. PARTIDO
-- ============================================================
CREATE TABLE PARTIDO (
    ID_PARTIDO          NUMBER          NOT NULL,
    ANIO                NUMBER(4)       NOT NULL,
    NUM_PARTIDO         NUMBER          NOT NULL,
    FECHA               VARCHAR2(20),
    ETAPA               VARCHAR2(100),
    ID_LOCAL            NUMBER,
    ID_VISITANTE        NUMBER,
    GOLES_LOCAL         NUMBER,
    GOLES_VISITANTE     NUMBER,
    TIEMPO_EXTRA        VARCHAR2(2),
    PENALES             VARCHAR2(2),
    PENALES_LOCAL       NUMBER,
    PENALES_VISITANTE   NUMBER,

    CONSTRAINT PK_PARTIDO PRIMARY KEY (ID_PARTIDO),

    CONSTRAINT UQ_PARTIDO UNIQUE (ANIO, NUM_PARTIDO),

    CONSTRAINT FK_PARTIDO_MUN FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO),

    CONSTRAINT FK_PARTIDO_LOCAL FOREIGN KEY (ID_LOCAL)
        REFERENCES SELECCION(ID_SELECCION),

    CONSTRAINT FK_PARTIDO_VISIT FOREIGN KEY (ID_VISITANTE)
        REFERENCES SELECCION(ID_SELECCION)
);

-- ============================================================
-- 6. POSICION_GRUPO
-- ============================================================
CREATE TABLE POSICION_GRUPO (
    ID_POSICION_GRUPO   NUMBER      NOT NULL,

    ANIO                NUMBER(4)   NOT NULL,
    ID_GRUPO            VARCHAR2(5) NOT NULL,

    ID_SELECCION        NUMBER      NOT NULL,

    PTS                 NUMBER,
    PJ                  NUMBER,
    PG                  NUMBER,
    PE                  NUMBER,
    PP                  NUMBER,
    GF                  NUMBER,
    GC                  NUMBER,
    DIFERENCIA          NUMBER,
    CLASIFICADO         VARCHAR2(5),  -- aqui va ir si o no

    CONSTRAINT PK_POSICION_GRUPO PRIMARY KEY (ID_POSICION_GRUPO),

    -- CLAVE FORÁNEA COMPUESTA
    CONSTRAINT FK_POSGRP_GRUPO 
        FOREIGN KEY (ANIO, ID_GRUPO)
        REFERENCES GRUPO(ANIO, ID_GRUPO),

    CONSTRAINT FK_POSGRP_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    -- evita duplicados (una selección no puede repetirse en el mismo grupo)
    CONSTRAINT UQ_POSICION UNIQUE (ANIO, ID_GRUPO, ID_SELECCION)
);


-- ============================================================
-- 7. GOL (ID_JUGADOR nullable → se llena si el jugador existe)
-- ============================================================

CREATE TABLE GOL (
    ID_GOL          NUMBER      NOT NULL,

    ID_PARTIDO      NUMBER      NOT NULL,
    ID_SELECCION    NUMBER      NOT NULL,
    ID_JUGADOR      NUMBER, -- puede ser NULL (autogol o desconocido)

    MINUTO          NUMBER      NOT NULL,

    ES_PENAL        VARCHAR2(2), -- sí, no
    ES_AUTOGOL      VARCHAR2(20), --sí, no

    CONSTRAINT PK_GOL PRIMARY KEY (ID_GOL),

    CONSTRAINT FK_GOL_PARTIDO 
        FOREIGN KEY (ID_PARTIDO)
        REFERENCES PARTIDO(ID_PARTIDO),

    CONSTRAINT FK_GOL_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    CONSTRAINT FK_GOL_JUG 
        FOREIGN KEY (ID_JUGADOR)
        REFERENCES JUGADOR_PAIS(ID_JUGADOR)
);


-- ============================================================
-- 8. GOLEADOR (ID_JUGADOR nullable)
-- ============================================================
CREATE TABLE GOLEADOR (
    ID_GOLEADOR     NUMBER      NOT NULL,

    ANIO            NUMBER(4)   NOT NULL,
    ID_SELECCION    NUMBER      NOT NULL,
    ID_JUGADOR      NUMBER, 

    GOLES           NUMBER,
    PARTIDOS        NUMBER,
    PROMEDIO        NUMBER(5,2),

    CONSTRAINT PK_GOLEADOR PRIMARY KEY (ID_GOLEADOR),

    CONSTRAINT FK_GOLEADOR_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    CONSTRAINT FK_GOLEADOR_JUG 
        FOREIGN KEY (ID_JUGADOR)
        REFERENCES JUGADOR_PAIS(ID_JUGADOR)
);

-- ============================================================
-- 9. POSICION_FINAL
-- ============================================================
CREATE TABLE POSICION_FINAL (
    ID_POSICION_FINAL   NUMBER      NOT NULL,

    ANIO                NUMBER(4)   NOT NULL,
    POSICION            NUMBER      NOT NULL,
    ID_SELECCION        NUMBER      NOT NULL,

    CONSTRAINT PK_POSICION_FINAL 
        PRIMARY KEY (ID_POSICION_FINAL),

    -- relación con mundial
    CONSTRAINT FK_POSFIN_MUN 
        FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO),

    CONSTRAINT FK_POSFIN_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    -- una posición solo puede existir una vez por mundial
    CONSTRAINT UQ_POSICION 
        UNIQUE (ANIO, POSICION),

    -- una selección solo puede aparecer una vez por mundial
    CONSTRAINT UQ_SELECCION 
        UNIQUE (ANIO, ID_SELECCION)
);

-- ============================================================
-- 10. tipo de premio
-- ============================================================
CREATE TABLE TIPO_PREMIO (
    ID_TIPO_PREMIO NUMBER        NOT NULL,
    NOMBRE         VARCHAR2(100) NOT NULL,

    CONSTRAINT PK_TIPO_PREMIO PRIMARY KEY (ID_TIPO_PREMIO),
    CONSTRAINT UQ_TIPO_PREMIO UNIQUE (NOMBRE)
);

CREATE TABLE PREMIO (
    ID_PREMIO       NUMBER      NOT NULL,

    ANIO            NUMBER(4)   NOT NULL,
    ID_TIPO_PREMIO  NUMBER      NOT NULL,

    ID_JUGADOR      NUMBER,     -- NULL si es premio a selección
    ID_SELECCION    NUMBER,     -- siempre debe existir

    CONSTRAINT PK_PREMIO 
        PRIMARY KEY (ID_PREMIO),

    --  relación con mundial
    CONSTRAINT FK_PREMIO_MUN 
        FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO),

    CONSTRAINT FK_PREMIO_TIPO 
        FOREIGN KEY (ID_TIPO_PREMIO)
        REFERENCES TIPO_PREMIO(ID_TIPO_PREMIO),

    CONSTRAINT FK_PREMIO_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    CONSTRAINT FK_PREMIO_JUG 
        FOREIGN KEY (ID_JUGADOR)
        REFERENCES JUGADOR_PAIS(ID_JUGADOR),

    -- evita duplicados del mismo premio en un mundial
    CONSTRAINT UQ_PREMIO UNIQUE (ANIO, ID_TIPO_PREMIO)
);

-- ============================================================
-- 11. EQUIPO_IDEAL (ID_JUGADOR nullable)
-- ============================================================
CREATE TABLE EQUIPO_IDEAL (
    ID_EQUIPO_IDEAL NUMBER      NOT NULL,

    ANIO            NUMBER(4)   NOT NULL,
    POSICION        VARCHAR2(50) NOT NULL,
    ID_JUGADOR      NUMBER      NOT NULL,
    ID_SELECCION    NUMBER      NOT NULL,

    CONSTRAINT PK_EQUIPO_IDEAL 
        PRIMARY KEY (ID_EQUIPO_IDEAL),

    CONSTRAINT FK_EQIDEAL_MUN 
        FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO),

    CONSTRAINT FK_EQIDEAL_JUG 
        FOREIGN KEY (ID_JUGADOR)
        REFERENCES JUGADOR_PAIS(ID_JUGADOR),

    CONSTRAINT FK_EQIDEAL_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    --  un jugador no puede repetirse en el mismo mundial
    CONSTRAINT UQ_EQIDEAL_JUG UNIQUE (ANIO, ID_JUGADOR),

    --  una posición solo puede asignarse una vez por mundial
    CONSTRAINT UQ_EQIDEAL_POS UNIQUE (ANIO, POSICION)
);

-- ============================================================
-- 12. TARJETA (ID_JUGADOR nullable)
-- ============================================================
CREATE TABLE TARJETA (
    ID_TARJETA      NUMBER      NOT NULL,

    ANIO            NUMBER(4)   NOT NULL,
    ID_JUGADOR      NUMBER      NOT NULL,
    ID_SELECCION    NUMBER      NOT NULL,

    AMARILLAS       NUMBER      DEFAULT 0,
    ROJAS           NUMBER      DEFAULT 0,

    CONSTRAINT PK_TARJETA 
        PRIMARY KEY (ID_TARJETA),

    CONSTRAINT FK_TARJETA_MUN 
        FOREIGN KEY (ANIO)
        REFERENCES MUNDIAL(ANIO),

    CONSTRAINT FK_TARJETA_JUG 
        FOREIGN KEY (ID_JUGADOR)
        REFERENCES JUGADOR_PAIS(ID_JUGADOR),

    CONSTRAINT FK_TARJETA_SEL 
        FOREIGN KEY (ID_SELECCION)
        REFERENCES SELECCION(ID_SELECCION),

    -- un jugador solo tiene un registro por mundial
    CONSTRAINT UQ_TARJETA UNIQUE (ANIO, ID_JUGADOR)
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IDX_PARTIDO_ANIO    ON PARTIDO(ANIO);
CREATE INDEX IDX_PARTIDO_LOCAL   ON PARTIDO(ID_LOCAL);
CREATE INDEX IDX_PARTIDO_VISIT   ON PARTIDO(ID_VISITANTE);
CREATE INDEX IDX_GOL_PARTIDO     ON GOL(ID_PARTIDO);
CREATE INDEX IDX_GOL_SEL         ON GOL(ID_SELECCION);
CREATE INDEX IDX_GOL_JUG         ON GOL(ID_JUGADOR);
CREATE INDEX IDX_POSGRP_GRUPO    ON POSICION_GRUPO(ID_GRUPO);
CREATE INDEX IDX_POSGRP_SEL      ON POSICION_GRUPO(ID_SELECCION);
CREATE INDEX IDX_GOLEADOR_ANIO   ON GOLEADOR(ANIO);
CREATE INDEX IDX_GOLEADOR_JUG    ON GOLEADOR(ID_JUGADOR);
CREATE INDEX IDX_TARJETA_ANIO    ON TARJETA(ANIO);
CREATE INDEX IDX_TARJETA_JUG     ON TARJETA(ID_JUGADOR);
CREATE INDEX IDX_JUGADOR_SEL     ON JUGADOR_PAIS(ID_SELECCION);
CREATE INDEX IDX_JUGADOR_NOMBRE  ON JUGADOR_PAIS(NOMBRE);

COMMIT;

SELECT TABLE_NAME FROM USER_TABLES
WHERE TABLE_NAME IN (
    'SELECCION','JUGADOR_PAIS','MUNDIAL','GRUPO','PARTIDO',
    'POSICION_GRUPO','GOL','GOLEADOR','POSICION_FINAL',
    'PREMIO','EQUIPO_IDEAL','TARJETA'
)
ORDER BY TABLE_NAME;