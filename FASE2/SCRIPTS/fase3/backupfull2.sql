fullbakcup 2
RUN {
  # 1. Seteamos el tiempo a un momento justo después del backup del Día 2
  SET UNTIL TIME "to_date('2026-04-14 00:45:00', 'YYYY-MM-DD HH24:MI:SS')";

  # 2. Forzamos el cierre de la PDB para poder sobreescribir
  SQL "ALTER PLUGGABLE DATABASE XEPDB1 CLOSE IMMEDIATE";

  # 3. Restauramos la estructura del segundo full backup (Etiqueta: FULL_DIA2_COMPLETO)
  RESTORE PLUGGABLE DATABASE XEPDB1;

  # 4. Recuperamos los datos hasta el tiempo indicado
  RECOVER PLUGGABLE DATABASE XEPDB1;

  # 5. Abrimos la base de datos creando la nueva línea de tiempo
  ALTER PLUGGABLE DATABASE XEPDB1 OPEN RESETLOGS;
}
