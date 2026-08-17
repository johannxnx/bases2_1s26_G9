RUN {
  # 1. Seteamos el tiempo al punto después del tercer Full Backup
  SET UNTIL TIME "to_date('2026-04-14 01:03:00', 'YYYY-MM-DD HH24:MI:SS')";

  # 2. Cerramos la PDB para el reemplazo de archivos
  SQL "ALTER PLUGGABLE DATABASE XEPDB1 CLOSE IMMEDIATE";

  # 3. Restauramos los archivos del tercer Full Backup (Etiqueta: FULL_DIA3_COMPLETO)
  RESTORE PLUGGABLE DATABASE XEPDB1;

  # 4. Recuperamos hasta el tiempo definido
  RECOVER PLUGGABLE DATABASE XEPDB1;

  # 5. Abrimos la base de datos con RESETLOGS
  ALTER PLUGGABLE DATABASE XEPDB1 OPEN RESETLOGS;
}