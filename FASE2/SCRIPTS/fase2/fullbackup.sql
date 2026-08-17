# Comentario: Este script debe ejecutarse en la consola RMAN (Recovery Manager de Oracle)

# Inicia un bloque RUN en RMAN que agrupa múltiples comandos de backup
RUN {
    # Asigna un canal de comunicación (c1) para las operaciones de backup usando discos
    # Los canales son necesarios para que RMAN pueda ejecutar operaciones de backup/restore
    ALLOCATE CHANNEL c1 DEVICE TYPE DISK;
    
    # Inicia un backup completo de la base de datos pluggable XEPDB1
    # "PLUGGABLE DATABASE" indica que es una PDB (no una CDB de múltiples bases de datos)
    BACKUP PLUGGABLE DATABASE XEPDB1 
    
    # Define la ruta y formato del archivo de backup que se createará
    # %U genera un nombre único para evitar conflictos de archivos
    # Los archivos se guardarán en C:\BACKUPS\ con extensión .bkp
    FORMAT 'C:\BACKUPS\FULL_%U.bkp' 
    
    # Asigna una etiqueta identificadora al backup para facilitar su seguimiento y recuperación
    # X debe reemplazarse con 1, 2 o 3 para identificar qué backup es (día 1, 2 o 3)
    TAG 'BACKUP_FULL_CARGA_X'; # Cambiar X por 1, 2 o 3
    
    # Libera (cierra) el canal de comunicación c1 para liberar recursos del sistema
    RELEASE CHANNEL c1;

# Cierra el bloque RUN de RMAN
}