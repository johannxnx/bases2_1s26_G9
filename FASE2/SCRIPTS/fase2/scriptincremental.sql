# BLOQUE 1: Backup Incremental de Nivel 0 (copia base inicial para incrementales posteriores)
# Este es el primer backup incremental que debe ejecutarse antes de los de nivel 1

# Abre el primer bloque RUN que contiene un backup incremental de nivel 0
RUN {
    # BACKUP INCREMENTAL LEVEL 0: Crea un backup de nivel cero (snapshot completo pero con marca incremental)
    # El nivel 0 actúa como base para futuros backups incrementales diferenciales
    # Es más eficiente que un backup completo porque solo almacena datos modificados desde el inicio
    BACKUP INCREMENTAL LEVEL 0 
    
    # Especifica que el backup es de la base de datos pluggable XEPDB1
    PLUGGABLE DATABASE XEPDB1 
    
    # Etiqueta el backup con una identificación única para este nivel base (N0 = Nivel 0)
    TAG 'INCREMENTAL_BASE_N0';

# Cierra el primer bloque RUN
}

# BLOQUE 2: Backup Incremental de Nivel 1 (solo cambios desde el último backup de nivel 0)
# Este backup debe ejecutarse después del nivel 0 y captura solo los cambios realizados

# Abre el segundo bloque RUN que contiene un backup incremental de nivel 1
RUN {
    # BACKUP INCREMENTAL LEVEL 1: Backup diferencial que captura solo datos modificados
    # desde el último backup de nivel 0, usando menos espacio que un backup completo
    BACKUP INCREMENTAL LEVEL 1 
    
    # Especifica que el backup es de la base de datos pluggable XEPDB1
    PLUGGABLE DATABASE XEPDB1 
    
    # Etiqueta distintiva del backup incremental identificando por día
    # X debe reemplazarse con 1, 2 o 3 según el día en que se ejecute el backup
    TAG 'INCREMENTAL_DIA_X'; # Cambiar X según el día

# Cierra el segundo bloque RUN
}

