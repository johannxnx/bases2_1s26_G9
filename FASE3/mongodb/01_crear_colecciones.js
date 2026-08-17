/*
  Script de creacion de colecciones para MongoDB
  Proyecto Fase 3 - Mundiales de Futbol

  Proposito:
  1. Crear la base de datos del proyecto en MongoDB.
  2. Crear las colecciones principales definidas para el modelo documental:
     - selecciones
     - jugadores
     - mundiales
  3. Definir validadores con JSON Schema para controlar la estructura basica
     de los documentos.
  4. Crear indices para evitar duplicados y acelerar consultas frecuentes.

  Nota:
  Este script no inserta datos. Solo prepara la estructura de la base de datos.

  Ejecutar con:
  mongosh "mongodb://localhost:27017/mundiales_futbol" .\01_crear_colecciones.js
*/

// Nombre de la base de datos que se utilizara en el proyecto.
const dbName = "mundiales_futbol";

// Obtiene una referencia a la base de datos. Si no existe, MongoDB la crea
// cuando se inserten datos o se creen colecciones.
const database = db.getSiblingDB(dbName);

// Funcion auxiliar:
// Si la coleccion ya existe, la elimina y la vuelve a crear.
// Esto facilita repetir pruebas sin dejar restos de ejecuciones anteriores.
function recreateCollection(name, options) {
  const exists = database.getCollectionInfos({ name }).length > 0;
  if (exists) {
    database[name].drop();
  }
  database.createCollection(name, options);
}

// -------------------------------------------------------------------------
// COLECCION: selecciones
// -------------------------------------------------------------------------
// Guarda el catalogo maestro de selecciones nacionales.
// Esta coleccion viene principalmente de la tabla SELECCION del modelo SQL,
// pero se extiende con datos derivados utiles para consultas:
// - participaciones en mundiales
// - anios en que fue sede
// - anios en que fue campeon
recreateCollection("selecciones", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_seleccion", "nombre"],
      properties: {
        id_seleccion: { bsonType: ["int", "long"], description: "Identificador unico de la seleccion" },
        nombre: { bsonType: "string", description: "Nombre de la seleccion" },
        participaciones: {
          bsonType: ["array"],
          items: { bsonType: ["int", "long"] },
          description: "Anios de participacion en mundiales"
        },
        sedes: {
          bsonType: ["array"],
          items: { bsonType: ["int", "long"] },
          description: "Anios en los que fue organizador"
        },
        total_participaciones: { bsonType: ["int", "long"] },
        fue_campeon: { bsonType: "bool" },
        anios_campeon: {
          bsonType: ["array"],
          items: { bsonType: ["int", "long"] }
        }
      }
    }
  }
});

// -------------------------------------------------------------------------
// COLECCION: jugadores
// -------------------------------------------------------------------------
// Guarda el catalogo maestro de jugadores.
// Se basa en la informacion de JUGADOR_PAIS y se complementa con
// DETALLE_JUGADOR, que en MongoDB se modela como un arreglo llamado
// "participaciones".
//
// Esto permite guardar en un solo documento:
// - datos generales del jugador
// - la informacion especifica de cada mundial en el que participo
recreateCollection("jugadores", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id_jugador", "nombre", "id_seleccion", "seleccion"],
      properties: {
        id_jugador: { bsonType: ["int", "long"], description: "Identificador unico del jugador" },
        nombre: { bsonType: "string" },
        id_seleccion: { bsonType: ["int", "long"] },
        seleccion: { bsonType: "string" },
        altura: { bsonType: ["string", "null"] },
        fecha_nacimiento: { bsonType: ["string", "null"] },
        nacionalidad: { bsonType: ["string", "null"] },
        participaciones: {
          bsonType: ["array"],
          description: "Detalle del jugador por mundial",
          items: {
            bsonType: "object",
            required: ["anio"],
            properties: {
              anio: { bsonType: ["int", "long"] },
              camiseta: { bsonType: ["string", "null"] },
              posicion: { bsonType: ["string", "null"] },
              jugo: { bsonType: ["int", "long", "null"] },
              jugo_titular: { bsonType: ["int", "long", "null"] },
              capitan: { bsonType: ["int", "long", "null"] },
              no_jugo: { bsonType: ["int", "long", "null"] },
              goles: { bsonType: ["int", "long", "null"] },
              prom_goles: { bsonType: ["double", "int", "long", "null"] },
              tarjeta_amarilla: { bsonType: ["int", "long", "null"] },
              tarjeta_roja: { bsonType: ["int", "long", "null"] },
              pg: { bsonType: ["int", "long", "null"] },
              pe: { bsonType: ["int", "long", "null"] },
              pp: { bsonType: ["int", "long", "null"] },
              pos_final: { bsonType: ["int", "long", "null"] }
            }
          }
        }
      }
    }
  }
});

// -------------------------------------------------------------------------
// COLECCION: mundiales
// -------------------------------------------------------------------------
// Esta es la coleccion principal del modelo NoSQL.
// Se guarda un documento por cada mundial, y dentro de ese documento se
// embebe la mayor parte de la informacion del torneo.
//
// Tablas del modelo SQL representadas aqui:
// - MUNDIAL
// - GRUPO
// - POSICION_GRUPO
// - POSICION_FINAL
// - PARTIDO
// - GOL
// - GOLEADOR
// - PREMIO
// - EQUIPO_IDEAL
// - TARJETA
//
// Ventaja:
// Permite consultar casi toda la informacion de un mundial leyendo un solo
// documento, lo cual encaja muy bien con el requerimiento de consultar por anio.
recreateCollection("mundiales", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["anio", "organizador", "campeon"],
      properties: {
        anio: { bsonType: ["int", "long"], description: "Anio del mundial" },
        organizador: {
          bsonType: "object",
          required: ["id_seleccion", "nombre"],
          properties: {
            id_seleccion: { bsonType: ["int", "long"] },
            nombre: { bsonType: "string" }
          }
        },
        campeon: {
          bsonType: "object",
          required: ["id_seleccion", "nombre"],
          properties: {
            id_seleccion: { bsonType: ["int", "long"] },
            nombre: { bsonType: "string" }
          }
        },
        num_selecciones: { bsonType: ["int", "long", "null"] },
        num_partidos: { bsonType: ["int", "long", "null"] },
        goles: { bsonType: ["int", "long", "null"] },
        promedio_gol: { bsonType: ["double", "int", "long", "null"] },
        grupos: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            required: ["id_grupo"],
            properties: {
              id_grupo: { bsonType: "string" },
              selecciones: {
                bsonType: ["array"],
                items: { bsonType: "string" }
              }
            }
          }
        },
        posiciones_grupo: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            required: ["id_grupo", "id_seleccion"],
            properties: {
              id_grupo: { bsonType: "string" },
              id_seleccion: { bsonType: ["int", "long"] },
              seleccion: { bsonType: ["string", "null"] },
              pts: { bsonType: ["int", "long", "null"] },
              pj: { bsonType: ["int", "long", "null"] },
              pg: { bsonType: ["int", "long", "null"] },
              pe: { bsonType: ["int", "long", "null"] },
              pp: { bsonType: ["int", "long", "null"] },
              gf: { bsonType: ["int", "long", "null"] },
              gc: { bsonType: ["int", "long", "null"] },
              diferencia: { bsonType: ["int", "long", "null"] },
              clasificado: { bsonType: ["string", "null"] }
            }
          }
        },
        posiciones_finales: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            required: ["posicion", "id_seleccion"],
            properties: {
              posicion: { bsonType: ["int", "long"] },
              id_seleccion: { bsonType: ["int", "long"] },
              seleccion: { bsonType: ["string", "null"] }
            }
          }
        },
        partidos: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            required: ["id_partido", "num_partido", "local", "visitante"],
            properties: {
              id_partido: { bsonType: ["int", "long"] },
              num_partido: { bsonType: ["int", "long"] },
              fecha: { bsonType: ["string", "null"] },
              etapa: { bsonType: ["string", "null"] },
              local: {
                bsonType: "object",
                required: ["id_seleccion", "nombre"],
                properties: {
                  id_seleccion: { bsonType: ["int", "long"] },
                  nombre: { bsonType: "string" },
                  goles: { bsonType: ["int", "long", "null"] }
                }
              },
              visitante: {
                bsonType: "object",
                required: ["id_seleccion", "nombre"],
                properties: {
                  id_seleccion: { bsonType: ["int", "long"] },
                  nombre: { bsonType: "string" },
                  goles: { bsonType: ["int", "long", "null"] }
                }
              },
              tiempo_extra: { bsonType: ["string", "null"] },
              penales: { bsonType: ["string", "null"] },
              penales_local: { bsonType: ["int", "long", "null"] },
              penales_visitante: { bsonType: ["int", "long", "null"] },
              goles_detalle: {
                bsonType: ["array"],
                items: {
                  bsonType: "object",
                  properties: {
                    id_gol: { bsonType: ["int", "long"] },
                    minuto: { bsonType: ["int", "long", "null"] },
                    id_seleccion: { bsonType: ["int", "long", "null"] },
                    seleccion: { bsonType: ["string", "null"] },
                    id_jugador: { bsonType: ["int", "long", "null"] },
                    jugador: { bsonType: ["string", "null"] },
                    es_penal: { bsonType: ["string", "bool", "null"] },
                    es_autogol: { bsonType: ["string", "bool", "null"] }
                  }
                }
              }
            }
          }
        },
        goleadores: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            properties: {
              id_jugador: { bsonType: ["int", "long", "null"] },
              jugador: { bsonType: ["string", "null"] },
              id_seleccion: { bsonType: ["int", "long", "null"] },
              seleccion: { bsonType: ["string", "null"] },
              goles: { bsonType: ["int", "long", "null"] },
              partidos: { bsonType: ["int", "long", "null"] },
              promedio: { bsonType: ["double", "int", "long", "null"] }
            }
          }
        },
        premios: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            properties: {
              id_tipo_premio: { bsonType: ["int", "long", "null"] },
              premio: { bsonType: ["string", "null"] },
              id_jugador: { bsonType: ["int", "long", "null"] },
              jugador: { bsonType: ["string", "null"] },
              id_seleccion: { bsonType: ["int", "long", "null"] },
              seleccion: { bsonType: ["string", "null"] }
            }
          }
        },
        equipo_ideal: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            properties: {
              posicion: { bsonType: ["string", "null"] },
              id_jugador: { bsonType: ["int", "long", "null"] },
              jugador: { bsonType: ["string", "null"] },
              id_seleccion: { bsonType: ["int", "long", "null"] },
              seleccion: { bsonType: ["string", "null"] }
            }
          }
        },
        tarjetas: {
          bsonType: ["array"],
          items: {
            bsonType: "object",
            properties: {
              id_jugador: { bsonType: ["int", "long", "null"] },
              jugador: { bsonType: ["string", "null"] },
              id_seleccion: { bsonType: ["int", "long", "null"] },
              seleccion: { bsonType: ["string", "null"] },
              amarillas: { bsonType: ["int", "long", "null"] },
              rojas: { bsonType: ["int", "long", "null"] }
            }
          }
        }
      }
    }
  }
});

// -------------------------------------------------------------------------
// INDICES DE LA COLECCION selecciones
// -------------------------------------------------------------------------
// uk_seleccion_id:
// Evita que existan dos selecciones con el mismo identificador.
database.selecciones.createIndex({ id_seleccion: 1 }, { unique: true, name: "uk_seleccion_id" });

// uk_seleccion_nombre:
// Evita nombres repetidos y ayuda en consultas por pais/seleccion.
database.selecciones.createIndex({ nombre: 1 }, { unique: true, name: "uk_seleccion_nombre" });

// idx_seleccion_participaciones:
// Acelera busquedas por anios de participacion.
database.selecciones.createIndex({ participaciones: 1 }, { name: "idx_seleccion_participaciones" });

// idx_seleccion_sedes:
// Acelera consultas sobre selecciones que fueron organizadoras.
database.selecciones.createIndex({ sedes: 1 }, { name: "idx_seleccion_sedes" });

// -------------------------------------------------------------------------
// INDICES DE LA COLECCION jugadores
// -------------------------------------------------------------------------
// uk_jugador_id:
// Evita duplicar jugadores con el mismo id.
database.jugadores.createIndex({ id_jugador: 1 }, { unique: true, name: "uk_jugador_id" });

// idx_jugador_nombre:
// Permite buscar jugadores por nombre con mayor rapidez.
database.jugadores.createIndex({ nombre: 1 }, { name: "idx_jugador_nombre" });

// idx_jugador_seleccion:
// Facilita listar jugadores por seleccion.
database.jugadores.createIndex({ id_seleccion: 1 }, { name: "idx_jugador_seleccion" });

// idx_jugador_participacion_anio:
// Facilita consultar jugadores que participaron en un mundial especifico.
database.jugadores.createIndex({ "participaciones.anio": 1 }, { name: "idx_jugador_participacion_anio" });

// -------------------------------------------------------------------------
// INDICES DE LA COLECCION mundiales
// -------------------------------------------------------------------------
// uk_mundial_anio:
// Garantiza que exista solo un documento por cada mundial.
database.mundiales.createIndex({ anio: 1 }, { unique: true, name: "uk_mundial_anio" });

// idx_mundial_organizador:
// Permite consultar rapidamente mundiales organizados por una seleccion.
database.mundiales.createIndex({ "organizador.id_seleccion": 1 }, { name: "idx_mundial_organizador" });

// idx_mundial_campeon:
// Permite consultar rapidamente mundiales ganados por una seleccion.
database.mundiales.createIndex({ "campeon.id_seleccion": 1 }, { name: "idx_mundial_campeon" });

// idx_mundial_partido_local:
// Acelera la busqueda de partidos donde una seleccion fue local.
database.mundiales.createIndex({ "partidos.local.id_seleccion": 1 }, { name: "idx_mundial_partido_local" });

// idx_mundial_partido_visitante:
// Acelera la busqueda de partidos donde una seleccion fue visitante.
database.mundiales.createIndex({ "partidos.visitante.id_seleccion": 1 }, { name: "idx_mundial_partido_visitante" });

// idx_mundial_partido_fecha:
// Acelera filtros por fecha de partido.
database.mundiales.createIndex({ "partidos.fecha": 1 }, { name: "idx_mundial_partido_fecha" });

// idx_mundial_partido_etapa:
// Acelera filtros por etapa del torneo.
database.mundiales.createIndex({ "partidos.etapa": 1 }, { name: "idx_mundial_partido_etapa" });

// Mensajes finales para confirmar que el script termino correctamente.
print("Base de datos configurada correctamente: " + dbName);
print("Colecciones creadas: mundiales, jugadores, selecciones");
