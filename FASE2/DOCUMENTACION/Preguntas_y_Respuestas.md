# Preguntas y Respuestas - Informe Técnico de Backups

---

## 📚 CONCEPTOS BÁSICOS

### P1: ¿Cuál es la diferencia entre un Full Backup y un Incremental Backup?

**R:** 
- **Full Backup (Nivel 0):** Respaldo completo que copia toda la base de datos en su totalidad. Ocupa ~570 MB por archivo. Es independiente y no requiere otros backups para restaurar.
- **Incremental Backup (Nivel 1):** Respaldo que solo copia los bloques de datos que han cambiado desde el último backup. Ocupa ~11 MB por archivo. Requiere un Full Backup base para ser restaurado.

**Analogía:** Full es una fotografía completa; Incremental solo registra lo que cambió desde la última foto.

---

### P2: ¿Qué es RMAN y por qué se usa en Oracle?

**R:** 
RMAN (Recovery Manager) es la herramienta oficial de Oracle para realizar backups y recuperación. Se usa porque:
- Realiza backups a nivel de bloques de datos (más eficiente que volcados de texto)
- Permite comprimir backups y deduplicar datos
- Ofrece catálogo central para gestionar todos los backups
- Realiza validación automática de integridad
- Permite restauraciones de punto en el tiempo (Point-in-Time Recovery)
- En nuestro proyecto la usamos desde línea de comandos: `RMAN TARGET /`

---

### P3: ¿Por qué es obligatorio el modo ARCHIVELOG para hacer backups?

**R:** 
El modo ARCHIVELOG permite que los archive logs (registros de transacciones) se guarden automáticamente. Sin esto:
- No se pueden restaurar backups incrementales
- No se puede hacer Point-in-Time Recovery
- Se pierde capacidad de recuperación ante fallos

Activamos ARCHIVELOG con: `ALTER DATABASE ARCHIVELOG;`

---

### P4: ¿Qué significa RTO y RPO?

**R:** 
- **RPO (Recovery Point Objective):** Punto al cual se puede recuperar. En nuestro proyecto es **Diario** (podemos recuperar hasta los datos de hace 1 día).
- **RTO (Recovery Time Objective):** Tiempo máximo para que el sistema esté operativo nuevamente. En nuestro proyecto es **4 segundos** (meta típica: < 1 hora).

En nuestras pruebas alcanzamos ambos objetivos perfectamente.

---

## 🔧 IMPLEMENTACIÓN Y CONFIGURACIÓN

### P5: ¿Cuáles fueron los pasos para configurar RMAN en tu proyecto?

**R:** 
1. **Verificar ARCHIVELOG:** `ARCHIVE LOG LIST;`
2. **Activar ARCHIVELOG:** `ALTER DATABASE ARCHIVELOG;`
3. **Configurar destino de logs:** `ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=C:\ORACLE_BASE\archives...'`
4. **Arrancar RMAN:** `RMAN TARGET /`
5. **Conectar a BD:** Automáticamente conecta a XEPDB1
6. **Crear directorios:** C:\BACKUPS\PROYECTO2\ con subdirectorios para FULL y INCREMENTAL
7. **Ejecutar backups:** Con comandos RUN { } para asignar canales y ejecutar backups

---

### P6: ¿Cómo configuraste los triggers de auditoría?

**R:** 
Configuré 14 triggers (uno por tabla principal). Cada trigger:
- **Se activa:** Después de INSERT, UPDATE o DELETE
- **Captura:** El tipo de operación (INSERT/UPDATE/DELETE)
- **Registra en:** Tabla LOG_[TABLA] con timestamp y secuencia
- **Formato:** `CREATE OR REPLACE TRIGGER TRG_[TABLA]_LOG AFTER INSERT OR UPDATE OR DELETE ON PROYECTO2BASES2.[TABLA]`

**Ejemplo:** TRG_PARTIDO_LOG registra cambios en tabla PARTIDO en LOG_PARTIDO

---

### P7: ¿Cuántos triggers implementaste y cuál era su función?

**R:** 
Se implementaron **14 triggers**, uno para cada tabla:
1. TRG_SELECCION_LOG
2. TRG_MUNDIAL_LOG
3. TRG_PARTIDO_LOG ← Principal
4. TRG_JUGADOR_PAIS_LOG
5. TRG_GOL_LOG ← Principal
6. TRG_DETALLE_JUGADOR_LOG
7. TRG_EQUIPO_IDEAL_LOG
8. TRG_GOLEADOR_LOG
9. TRG_POSICION_GRUPO_LOG
10. TRG_POSICION_FINAL_LOG
11. TRG_GRUPO_LOG
12. TRG_PREMIO_LOG
13. TRG_TARJETA_LOG
14. TRG_TIPO_PREMIO_LOG

**Función:** Auditoría automática de cambios con timestamp y tipo de operación.

---

### P8: ¿Dónde se almacenan los backups en tu sistema?

**R:** 
En la ruta: `C:\BACKUPS\PROYECTO2\` con la siguiente estructura:

```
C:\BACKUPS\PROYECTO2\
├── FULL_BACKUPS\          → Full Backups (570 MB c/u)
├── INCREMENTAL_BACKUPS\   → Incremental Backups (11 MB c/u)
└── ARCHIVE_LOGS\          → Copias de archive logs
```

---

### P9: ¿Cuáles fueron los directorios creados para los backups?

**R:** 
```
C:\BACKUPS\PROYECTO2\
├── FULL_BACKUPS\           (Full Backups diarios)
├── INCREMENTAL_BACKUPS\    (Backups incrementales diarios)
└── ARCHIVE_LOGS\           (Registro de cambios)

C:\ORACLE_BASE\
├── oradata\                (Datafiles de la BD)
├── archives\               (Archive logs)
└── diag\                   (Logs de diagnóstico)
```

Total: 6 directorios principales para gestión integral.

---

## 📊 RESULTADOS Y MÉTRICAS

### P10: ¿Cuánto espacio ocupó cada Full Backup?

**R:** 
**~570 MB por archivo**

Desglose:
- Día 1: 570 MB (después de cargar 400+ partidos y 3000+ goles)
- Día 2: 570 MB (después de cargar 150 partidos adicionales)
- Día 3: 570 MB (después de actualizar nombres a mayúsculas)

Total para 3 días: **~1,710 MB**

---

### P11: ¿Cuánto espacio ocuparon los backups incrementales?

**R:** 
**~11 MB promedio por backup incremental (Nivel 1)**

Desglose:
- Día 1 Nivel 0: 570 MB (base)
- Día 2 Nivel 1: 11 MB (solo cambios)
- Día 3 Nivel 1: 11 MB (solo cambios)

Total incremental + 1 Full: **~592 MB**

---

### P12: ¿Cuál fue el ahorro de espacio usando incrementales vs full?

**R:** 
**65.3% de ahorro total**

Cálculo:
- Full por 3 días: 1,710 MB
- Incremental (1 full + 2 level 1): 592 MB
- Diferencia: 1,118 MB ahorrados
- Porcentaje: (1,118 / 1,710) × 100 = **65.3%**

A mayor volumen de datos, mayor diferencia.

---

### P13: ¿Cuánto tiempo tardó restaurar un backup full?

**R:** 
**4-5 segundos en promedio**

Desglose:
| Día | RESTORE | RECOVER | Total |
|-----|---------|---------|-------|
| Día 1 | 4s | 1s | **5s** |
| Día 2 | 4s | 1s | **5s** |
| Día 3 | 5s | 1s | **6s** |

**Nota:** El tiempo aumentó ligeramente en Día 3 porque la BD creció más.

---

### P14: ¿Cuánto tiempo tardó restaurar un backup incremental?

**R:** 
**3-4 segundos en promedio (constante)**

Desglose:
| Día | RESTORE | RECOVER | Total |
|-----|---------|---------|-------|
| Carga 1 | 3s | 1s | **4s** |
| Carga 2 | 3s | 1s | **4s** |
| Carga 3 | 3s | 1s | **4s** |

**Nota:** Se mantuvo constante incluso cuando la BD creció.

---

### P15: ¿Por qué el backup incremental fue más rápido al final?

**R:** 
Porque el tiempo no depende del tamaño total de la BD, sino de:
1. **Cantidad de bloques modificados** (siempre ~11 MB)
2. **Velocidad de I/O del disco** (bottleneck, no compresión)
3. **Logs aplicados** (~1 segundo siempre)

Mientras Full creció de 5s a 6s (570 MB → más overhead), Incremental se mantuvo en 4s porque solo restaura cambios.

---

## 📈 ANÁLISIS COMPARATIVO

### P16: ¿En qué caso usarías Full Backup sobre Incremental?

**R:** 
Full Backup es mejor para:
- **BD pequeñas a medianas** (< 5 GB)
- **Cuando hay espacio en disco abundante**
- **Necesidad de simplicidad operacional** (1 paso para restaurar)
- **Baja frecuencia de cambios** (cambios mínimos)
- **Emergencias críticas** (punto de reinicio rápido)

**Ejemplo:** Una BD académica pequeña que cambia poco.

---

### P17: ¿En qué caso usarías Incremental sobre Full?

**R:** 
Incremental es mejor para:
- **BD grandes** (> 10 GB)
- **Cambios masivos y frecuentes** (miles de registros diarios)
- **Espacio limitado en almacenamiento** (NAS, Cloud)
- **Ambientes de producción con alto volumen** (servidores empresariales)
- **Eficiencia de ancho de banda** (transferencias a backup externo)

**Ejemplo:** Base de datos de banco con millones de transacciones diarias.

---

### P18: ¿Cuál es la tabla comparativa más importante?

**R:** 
La **Tabla 10.1 - Comparativa Técnica Integral**, que muestra:

| Aspecto | Full | Incremental |
|--------|------|-------------|
| Tamaño Promedio | 570 MB | 11 MB |
| Tiempos Restauración | 3-5 seg | 4 seg |
| Espacio 3 días | 1.7 GB | 592 MB |
| Eficiencia Espacio | 0% | 94% ahorro |
| Complejidad | Baja | Alta |
| Casos Óptimos | BD < 1/2 GB | BD > 10 GB |

Esta tabla resume TODO lo necesario para tomar decisiones.

---

### P19: ¿Por qué el tiempo incremental se mantuvo constante?

**R:** 
Porque:
1. **Restaura solo cambios:** ~11 MB siempre (no crece con la BD)
2. **Velocidad I/O es constante:** Si el disco opera a 100 MB/s, 11 MB tarda siempre igual
3. **Overhead mínimo:** Menos archivos que procesar que en Full
4. **Logs de cambios:** Siempre ~1 segundo (pocas transacciones por día)

**Matemática:** 11 MB ÷ 100 MB/s ≈ 0.11s + overhead = 3s constantes

---

### P20: ¿Cómo cambió el tiempo de Full Backup conforme creció la BD?

**R:** 
**Aumentó del 5 segundos al 6 segundos**

| Carga | Tamaño BD | RESTORE | RECOVER | Total |
|-------|-----------|---------|---------|-------|
| 1 | Base | 4s | 1s | 5s |
| 2 | +150 registros | 4s | 1s | 5s |
| 3 | +actualización | 5s | 1s | **6s** |

**Razón:** A más datos (570 MB → más dados), más tiempo en I/O. El overhead crece con el volumen.

**Conclusión:** Full es menos escalable que Incremental conforme crece la BD.

---

## 🔧 PROCEDIMIENTOS Y COMANDOS

### P21: ¿Cuáles son los pasos para restaurar un backup completo?

**R:** 
```bash
RMAN> RESTORE PLUGGABLE DATABASE XEPDB1;
RMAN> RECOVER PLUGGABLE DATABASE XEPDB1;
RMAN> ALTER PLUGGABLE DATABASE XEPDB1 OPEN RESETLOGS;
```

**Desglose:**
1. **RESTORE:** Copia los archivos del backup al almacenamiento (4-5s)
2. **RECOVER:** Aplica los archive logs para reconstruir transacciones (1s)
3. **OPEN RESETLOGS:** Abre la BD y reinicia los números de log

**Tiempo total:** 5-6 segundos

---

### P22: ¿Cuál es el procedimiento Point-in-Time Recovery?

**R:** 
```sql
RUN {
   SET UNTIL TIME "to_date('2026-04-14 01:05:00', 'YYYY-MM-DD HH24:MI:SS')";
   SQL "ALTER PLUGGABLE DATABASE XEPDB1 CLOSE IMMEDIATE";
   RESTORE PLUGGABLE DATABASE XEPDB1;
   RECOVER PLUGGABLE DATABASE XEPDB1;
   ALTER PLUGGABLE DATABASE XEPDB1 OPEN RESETLOGS;
}
```

**¿Qué hace?** Restaura la BD a un momento específico en el pasado.

**Casos de uso:** Si se eliminó un registro importante por error a las 01:05, restaurar a esa hora y antes.

---

### P23: ¿Qué comando RMAN usaste para el backup full?

**R:** 
```bash
RMAN> RUN {
   ALLOCATE CHANNEL c1 DEVICE TYPE DISK;
   BACKUP PLUGGABLE DATABASE XEPDB1 
   FORMAT 'C:\BACKUPS\FULL_%U.bkp' 
   TAG 'BACKUP_FULL_CARGA_X';
   RELEASE CHANNEL c1;
}
```

**Desglose:**
- **ALLOCATE CHANNEL:** Asigna 1 canal de I/O
- **BACKUP:** Ejecuta el respaldo
- **FORMAT:** Define ubicación y nombre (`%U` = ID único)
- **TAG:** Etiqueta para identificar (ej: BACKUP_FULL_CARGA_1)
- **RELEASE:** Libera el canal

---

### P24: ¿Cómo se ejecuta un backup incremental nivel 1?

**R:** 
```bash
RMAN> RUN {
   ALLOCATE CHANNEL c1 DEVICE TYPE DISK;
   BACKUP INCREMENTAL LEVEL 1 PLUGGABLE DATABASE XEPDB1 
   FORMAT 'C:\BACKUPS\INCR_%U.bkp' 
   TAG 'INCREMENTAL_DIA_X';
   RELEASE CHANNEL c1;
}
```

**Diferencias con Full:**
- **INCREMENTAL LEVEL 1:** En lugar de PLUGGABLE DATABASE
- **Solo copia bloques modificados** desde último backup
- **Mucho más rápido** (11 MB vs 570 MB)

---

### P25: ¿Cómo validar que un backup se realizó correctamente?

**R:** 
```bash
RMAN> LIST BACKUP SUMMARY;
RMAN> LIST BACKUP OF PLUGGABLE DATABASE XEPDB1;
RMAN> VALIDATE BACKUPSET;
```

**En nuestro proyecto validamos:**
- ✅ Directorios creados correctamente
- ✅ Archivos de backup en C:\BACKUPS\PROYECTO2\
- ✅ Etiquetas RMAN registradas (TAG20260414T002848, etc.)
- ✅ Restauración exitosa en 100% de casos
- ✅ COUNT(*) coincidentes después de restaurar

---

## 🎯 ESTRATEGIA Y RECOMENDACIONES

### P26: ¿Qué estrategia de backup recomendaste para PROYECTO2BASES2?

**R:** 
**Estrategia Híbrida (Full + Incremental)**

```
PLAN PROPUESTO:
Lunes-Viernes:
└─ FULL BACKUP cada lunes 23:00
└─ INCREMENTAL LEVEL 1 martes-viernes 23:00
└─ Rotación: 2 full backups + 5 incrementales

Fin de Semana:
└─ Backup extendido viernes
└─ Sin ejecutables hasta lunes

Archivado:
└─ Full mensual → NAS/Cloud
└─ Retención: 1 año
```

**¿Por qué?** Balancea simplicidad, ahorro de espacio y rapidez.

---

### P27: ¿Por qué usarías FULL backup los lunes?

**R:** 
Porque:
1. **Punto de reinicio lógico:** Inicia la semana con copia completa
2. **Simplicidad:** Si falla otro backup, el lunes es base segura
3. **Emergencias críticas:** Si algo se corrompe, restaura lunes sin dependencias
4. **Predecible:** Al inicio de semana laboral = mejor momento

**Beneficio:** Restauración simple en emergencias (1 paso, no cadena).

---

### P28: ¿Por qué usarías INCREMENTAL de martes a viernes?

**R:** 
Porque:
1. **Captura cambios diarios:** Cada día carga ~150-200 registros nuevos
2. **Sin duplicación:** Solo registra lo que cambió desde lunes
3. **Ahorro de 60-70%:** En lugar de 570 MB × 4 = 2,280 MB, ocupa ~44 MB
4. **Velocidad:** Más rápido hacer backup (11 MB en segundos)

**Beneficio:** Máxima eficiencia en espacio y tiempo.

---

### P29: ¿Cuál es el plan de archivado a largo plazo?

**R:** 
```
Archivado Mensual:
├─ Fin de mes: Copiar FULL backup a NAS/Cloud storage
├─ Etiquetado: BACKUP_FULL_[MES]_[AÑO]
├─ Retención: Mínimo 1 año (auditoría)
├─ Verificación: VALIDATE BACKUPSET mensualmente
└─ Offsite: Almacenamiento externo para recuperación ante desastre
```

**¿Por qué?** 
- Cumplimiento normativo (auditoría)
- Recuperación ante desastre (incendio, robo en datacenter)
- Histórico de 1 año por ley

---

### P30: ¿Cuántos backups deberías mantener en rotación?

**R:** 
**2 Full Backups + 5 Incrementales**

**Desglose:**
- **2 Full:** Respaldo anterior + actual (si uno se corrompe, hay otro)
- **5 Incremental:** Martes, Miércoles, Jueves, Viernes + anterior

**Ventajas:**
- ✅ Redundancia (2 full = seguridad)
- ✅ Histórico de semana (5 diarios)
- ✅ Espacio manejable (~600 MB)
- ✅ Recuperación a cualquier día de la semana

**Si un full se corrompe:** Tienes el otro para restaurar toda la BD.

---

## ✅ VALIDACIÓN Y RECUPERABILIDAD

### P31: ¿Cómo validaste que los datos restaurados fueron correctos?

**R:** 
Ejecuté 5 validaciones después de cada restauración:

```sql
-- 1. Validar que todas las tablas tengan datos
SELECT table_name, num_rows FROM user_tables WHERE num_rows > 0;

-- 2. Verificar triggers de auditoría activos
SELECT trigger_name, status FROM user_triggers;

-- 3. Contar registros en tablas críticas
SELECT COUNT(*) as PARTIDO_COUNT FROM PARTIDO;
SELECT COUNT(*) as GOL_COUNT FROM GOL;

-- 4. Validar integridad referencial
SELECT COUNT(*) FROM partido WHERE id_seleccion_local IS NULL;

-- 5. Revisar fragmentación
SELECT fragmentation_percentage FROM user_segments WHERE segment_name LIKE 'PARTIDO%';
```

**Resultado:** 100% coincidencia en todos los casos.

---

### P32: ¿Qué tablas validaste después de cada restauración?

**R:** 
**Tablas principales validadas:**

| Tabla | Registros Día 1 | Registros Día 2 | Registros Día 3 |
|-------|-----------------|-----------------|-----------------|
| MUNDIAL | 24 | 24 | 24 |
| SELECCION | 32 | 32 | 32 (mayúsculas) |
| PARTIDO | 400+ | 550+ | 550+ |
| GOL | 3000+ | 4500+ | 4500+ |
| JUGADOR_PAIS | 8000+ | 8000+ | 8000+ |

**Validación:** Todas coincidieron exactamente después de restaurar.

---

### P33: ¿Cuántos registros tenía cada tabla al final?

**R:** 
**Estado final después de Día 3:**

| Tabla | Cantidad |
|-------|----------|
| MUNDIAL | 24 registros |
| SELECCION | 32 registros (en MAYÚSCULAS) |
| GRUPO | X registros |
| PARTIDO | 550+ registros |
| GOL | 4500+ registros |
| JUGADOR_PAIS | 8000+ registros |
| TARJETA | X registros |
| PREMIO | X registros |

**Total:** ~13,000+ registros en toda la BD (~600 MB).

---

### P34: ¿Cómo verificaste la integridad referencial?

**R:** 
Con la consulta:
```sql
SELECT COUNT(*) FROM partido 
WHERE id_seleccion_local IS NULL OR id_seleccion_visitante IS NULL;
```

**Resultado:** 0 registros (ningún partido sin selección).

**Otras validaciones:**
- ✅ Todos los goles referenciaban partidos válidos
- ✅ Todos los jugadores tenían país válido
- ✅ Sin registros huérfanos después de restauración

---

### P35: ¿Qué tablas de LOG creaste para auditoría?

**R:** 
**14 tablas LOG creadas (una por tabla principal):**

1. LOG_SELECCION → Audita cambios en SELECCION
2. LOG_MUNDIAL → Audita cambios en MUNDIAL
3. LOG_PARTIDO → Audita cambios en PARTIDO ⭐
4. LOG_JUGADOR_PAIS → Audita cambios en JUGADOR_PAIS
5. LOG_GOL → Audita cambios en GOL ⭐
6. LOG_DETALLE_JUGADOR
7. LOG_EQUIPO_IDEAL
8. LOG_GOLEADOR
9. LOG_POSICION_GRUPO
10. LOG_POSICION_FINAL
11. LOG_GRUPO
12. LOG_PREMIO
13. LOG_TARJETA
14. LOG_TIPO_PREMIO

**Cada LOG registra:** ID, FECHA_REGISTRO, OPERACION (INSERT/UPDATE/DELETE), CANTIDAD, DESCRIPCION

---

## 🔐 SEGURIDAD Y MÉTRICAS

### P36: ¿Cuál fue el porcentaje de disponibilidad alcanzado?

**R:** 
**100% de disponibilidad**

Evidencia:
- ✅ 3 Full Backups creados exitosamente (100%)
- ✅ 3 Incremental Backups creados exitosamente (100%)
- ✅ 9 Restauraciones totales (3 Full + 3 Incremental × 3 intentos)
- ✅ 0 fallos en toda la ejecución
- ✅ RMAN conectado y operativo durante todo el proyecto

---

### P37: ¿Cuál fue el porcentaje de integridad de datos?

**R:** 
**100% de integridad**

Validaciones:
- ✅ PARTIDO: 100% de coincidencia (550+ registros)
- ✅ GOL: 100% de coincidencia (4500+ registros)
- ✅ SELECCION: 100% con nombres en MAYÚSCULAS
- ✅ Integridad referencial: 0 registros huérfanos
- ✅ Triggers de auditoría: Activos en todas las tablas

**Métrica:** 0 corruptelas, 0 pérdidas, 0 inconsistencias.

---

### P38: ¿Cómo garantizas redundancia ante corrupción de backups?

**R:** 
Con la estrategia **2 Full Backups + 5 Incrementales:**

```
Si Full Backup 1 se corrompe:
  → Usar Full Backup 2
  → Restaurar desde día lunes anterior
  
Si Incremental se corrompe:
  → Usar Full Backup más reciente
  → Perder máximo 1 día de cambios
```

**Ventajas:**
- ✅ 2 copias de datos completos
- ✅ Redundancia en almacenamiento
- ✅ Verificación automática (VALIDATE BACKUPSET)
- ✅ Rotación mensual a offsite

---

### P39: ¿Qué pasa si un backup se corrompe?

**R:** 
1. **Detectar:** `VALIDATE BACKUPSET;` identifica corrupción
2. **Alternativa 1:** Restaurar desde backup anterior (2 Full disponibles)
3. **Alternativa 2:** Restaurar desde offsite (copias de 1 mes)
4. **Impacto:** Máximo 1 día de datos (si es incremental)
5. **Procedimiento:** Sin interrupciones, cambio de backup y reintentar RESTORE

**Resultado:** Sistema sigue funcionando con datos de hace 1 día máximo.

---

### P40: ¿Por qué es importante mantener 2 full backups?

**R:** 
Por varias razones críticas:

| Razón | Beneficio |
|-------|----------|
| **Redundancia** | Si uno se corrompe, hay respaldo |
| **Validación cruzada** | Comparar integridad entre dos |
| **Sin ventana crítica** | Siempre hay copia disponible |
| **Recuperación rápida** | No esperar a crear nuevo full |
| **Auditoría** | Histórico de 2 backups |
| **Seguridad ante fallos de I/O** | No confiar en un solo copy |

**Analogía:** Es como tener 2 extinguidores en lugar de 1.

---

## 📝 DATOS ESPECÍFICOS DEL PROYECTO

### P41: ¿Cuántos partidos cargaste en día 1?

**R:** 
**400+ partidos**

Con la siguiente información:
- Incluyen datos de múltiples mundiales
- Cada partido tiene selección local y visitante
- Rango de fechas: históricas (1930 - 2022)
- Enlazados con 3000+ goles

---

### P42: ¿Cuántos goles cargaste en día 1?

**R:** 
**3000+ goles**

Desglose:
- Día 1: 3000+ goles
- Día 2: Incremento a 4500+ goles
- Día 3: Se mantuvieron los 4500+ (sin nuevos goles, solo UPDATE de nombres)

**Ratio:** ~7-8 goles por partido (válido estadísticamente)

---

### P43: ¿Cuántos registros hay en tabla SELECCION?

**R:** 
**32 registros (selecciones nacionales)**

Representan:
- 32 países/selecciones
- Día 3: Actualización a MAYÚSCULAS de nombres
- Válidos para mundiales 1930-2022

**Ejemplo:** ARGENTINA, BRASIL, ALEMANIA, etc.

---

### P44: ¿Qué cambios hiciste en día 3?

**R:** 
**Actualización de nombres a MAYÚSCULAS**

```sql
UPDATE SELECCION SET NOMBRE = UPPER(NOMBRE);
```

**Detalles:**
- Tabla afectada: SELECCION (32 registros)
- Operación: UPDATE
- Cambio: Nombres de selecciones a mayúsculas
- Tiempo: ~1 segundo
- Validación: SELECT COUNT(*) confirmó 32 registros

**Propósito:** Simular cambios en producción para probar backups.

---

### P45: ¿Cuáles eran las tablas principales del proyecto?

**R:** 
**2 tablas principales respaldadas:**

| Tabla | Propósito |
|-------|----------|
| **PARTIDO** | Registra partidos de mundiales (400-550 registros) |
| **GOL** | Registra goles anotados (3000-4500 registros) |

**Tablas de soporte:**

| Tabla | Propósito |
|-------|----------|
| MUNDIAL | Datos de campeonatos (24 registros) |
| SELECCION | Equipos nacionales (32 registros) |
| JUGADOR_PAIS | Jugadores por país (8000+ registros) |
| TARJETA | Tarjetas amarillas/rojas |
| PREMIO | Premios (Balón de Oro, etc.) |
| GRUPO | Grupos de mundiales |
| POSICION_GRUPO | Clasificaciones por grupo |
| POSICION_FINAL | Posiciones finales |
| GOLEADOR | Máximos goleadores |
| EQUIPO_IDEAL | Once del torneo |
| DETALLE_JUGADOR | Detalles de jugadores |
| TIPO_PREMIO | Tipos de premios |

---

## 🎓 TEORÍA Y JUSTIFICACIÓN

### P46: ¿Por qué es importante hacer backups?

**R:** 
Por múltiples razones críticas:

1. **Recuperación ante fallos:** Corrupción de datos, fallos de hardware, malware
2. **Cumplimiento legal:** Normas de auditoría y protección de datos
3. **Continuidad empresarial:** Minimizar tiempo de inactividad
4. **Pérdida accidental:** Borrado erróneo de datos importantes
5. **Desastre natural:** Incendio, inundación, terremoto
6. **Recuperación de punto en tiempo:** Volver a momento antes de error
7. **Verdad histórica:** Mantener histórico de años

**En nuestro proyecto:** Demostramos que 3 full + 3 incrementales = 100% recuperable.

---

### P47: ¿Cuál es el bottleneck en la restauración?

**R:** 
**Velocidad de I/O del disco**

Evidencia matemática:
```
Full Backup: 570 MB
Velocidad disco típica: 100-150 MB/s
Tiempo teórico: 570 ÷ 100 = 5.7 segundos ≈ 5-6 segundos ✓

Incremental: 11 MB
Tiempo teórico: 11 ÷ 100 = 0.11 segundos ≈ 3-4 segundos ✓
(+ overhead de RMAN ~3 segundos)
```

**NO es bottleneck:**
- ✗ Compresión (no usamos)
- ✗ Red (backups locales)
- ✗ CPU (Oracle optimizado)

**Conclusión:** El cuello de botella es el disco, no el software.

---

### P48: ¿Cómo afecta la velocidad de I/O al tiempo de restauración?

**R:** 
Directamente proporcional:

```
Scenario A: Disco rápido (SSD 500 MB/s)
Full: 570 MB ÷ 500 = 1.14s
Incremental: 11 MB ÷ 500 = 0.02s
Tiempo TOTAL: 2-3 segundos

Scenario B: Disco lento (HDD 50 MB/s)
Full: 570 MB ÷ 50 = 11.4s
Incremental: 11 MB ÷ 50 = 0.22s
Tiempo TOTAL: 12-13 segundos
```

**En nuestro proyecto:** Usamos HDD estándar → 5-6 segundos.

**Recomendación:** Usar SSD para datacenter crítico.

---

### P49: ¿Qué ventaja tiene RMAN sobre mysqldump?

**R:** 
**RMAN >> mysqldump**

| Aspecto | RMAN | mysqldump |
|--------|------|-----------|
| **Formato** | Binario (bloques) | Texto (SQL) |
| **Tamaño** | 570 MB | 2000+ MB |
| **Velocidad** | 5s | 30+ minutos |
| **Integridad** | Validación automática | Manual |
| **Recuperación** | Directa | Reparse SQL |
| **Point-in-Time** | Sí | No |
| **Compresión** | Nativa | Manual |
| **Catálogo** | Central RMAN | Ninguno |

**Conclusión:** RMAN es profesional, mysqldump es para desarrollo.

---

### P50: ¿Por qué los bloques modificados son importantes en incrementales?

**R:** 
Porque:

1. **Eficiencia de espacio:** Solo copia lo que cambió (11 MB vs 570 MB)
2. **Velocidad:** Menos datos = transferencia más rápida
3. **I/O reducido:** Menos lecturas de disco
4. **Cadena mínima:** Incrementales pequeños = más fácil de validar
5. **Escalabilidad:** A más datos en BD, más ahorros

**Ejemplo:**
```
Día 1: Cargamos 400 partidos → BD llena → Full 570 MB
Día 2: Agregamos 150 partidos → Solo esos 150 cambian → Incremental 11 MB
Día 3: Actualizamos 32 selecciones → Solo esos 32 cambian → Incremental 11 MB

Sin incrementales:
Día 2: 570 MB nuevamente
Día 3: 570 MB nuevamente
TOTAL: 1,710 MB

Con incrementales:
Día 2: 11 MB
Día 3: 11 MB
TOTAL: 592 MB ← 65% de ahorro
```

**Por eso son importantes:** Máxima eficiencia a máxima recuperabilidad.

---

## 📋 PREGUNTAS CAPCIOSAS/AVANZADAS

### P51: ¿Qué pasaría si durante una restauración se corta la luz?

**R:** 
La restauración se interrumpiría, pero:
1. **RMAN lo detecta:** Status = INCOMPLETE
2. **Se puede reintentar:** `RECOVER PLUGGABLE DATABASE XEPDB1;`
3. **Idempotencia:** RMAN no repite trabajo (controla secuencias)
4. **Rollback automático:** Transacciones inconsistentes se revierten

**Solución:** UPS (Uninterruptible Power Supply) para datacenter.

---

### P52: ¿Por qué validaste con COUNT(*) y no con checksums?

**R:** 
Ambos son válidos, pero COUNT(*) es:
- ✅ Simple y rápido
- ✅ Suficiente para volumen de datos
- ✅ Visual (comparar números)
- ✅ Accesible sin herramientas especiales

RMAN internamente usa:
- ✅ Checksums de bloques
- ✅ Validación VALIDATE BACKUPSET
- ✅ Comparación bit a bit

**Conclusión:** COUNT(*) para auditoría visual, RMAN para validación técnica.

---

### P53: ¿Podrías haber usado LEVEL 2 o LEVEL 3 incremental?

**R:** 
**Técnicamente sí, pero no lo hicimos porque:**

- **LEVEL 1:** Copia bloques modificados desde último Level 0 (simple)
- **LEVEL 2:** Copia bloques modificados desde último Level 1 (más complejo)
- **LEVEL 3:** Copia bloques modificados desde último Level 2 (aún más)

**Ventaja de LEVEL 2+:** Más granularidad = compresión extra.

**Desventaja:** Cadena de dependencias más larga → riesgo de error.

**En nuestro proyecto:** LEVEL 1 es suficiente porque:
- BD pequeña (600 MB)
- Solo 150 cambios diarios
- Cadena de 2 pasos = seguridad

---

### P54: ¿Cómo hubiera sido diferente el proyecto con BD de 100 GB?

**R:** 
**Cambios dramáticos:**

| Métrica | 600 MB | 100 GB |
|---------|--------|--------|
| **Full Backup** | 570 MB | 95 GB |
| **Full tiempo** | 5s | 950s (16 min) |
| **Incremental** | 11 MB | 200 MB |
| **Incremental tiempo** | 4s | 30s |
| **Ahorro** | 65% | 98%+ |
| **Espacio 1 mes** | 3 GB | 19 GB (Full) vs 6.2 GB (Incr) |

**Conclusión:** A mayor escala, más crítico el incremental.

---

### P55: ¿Qué hubiera pasado sin triggers de auditoría?

**R:** 
Hubiera perdido:
- ✗ Historial de cuándo cambiaron datos
- ✗ Quién hizo INSERT/UPDATE/DELETE (sin conexión)
- ✗ Validación de coherencia
- ✗ Auditoría legal

**Pero los backups hubieran funcionado igual** (triggers no afectan backups).

**Razón de incluirlos:** Cumplimiento normativo y trazabilidad.

---

## 🏆 RESUMEN EJECUTIVO

### P56: Si debas presentar esto en 2 minutos, ¿qué dirías?

**R:** 
> "Realizamos un proyecto experimental de backups en Oracle Database 21c comparando dos estrategias:
>
> **Full Backup (Nivel 0):** Copia completa, ~570 MB, 5-6 segundos para restaurar.
>
> **Incremental Backup (Nivel 1):** Solo cambios, ~11 MB, 4 segundos para restaurar.
>
> **Resultado:** Incremental es 65% más eficiente en espacio y 20% más rápido al crecer la BD.
>
> **Recomendación:** Estrategia híbrida (Full semanal + Incremental diario) para máxima protección con mínimo espacio.
>
> **Validación:** 100% recuperabilidad, 100% integridad, RTO de 4 segundos."

**Duración:** Exactamente 2 minutos. 🎯

---

**FIN DEL DOCUMENTO**

---

