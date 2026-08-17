RUN {
  # Seteamos el tiempo al punto de seguridad (Día 1 antes del desastre)
  SET UNTIL TIME "to_date('2026-04-14 00:30:00', 'YYYY-MM-DD HH24:MI:SS')";

  # Forzamos que la PDB esté cerrada por si acaso
  SQL "ALTER PLUGGABLE DATABASE XEPDB1 CLOSE IMMEDIATE";

  # Restauramos y Recuperamos
  RESTORE PLUGGABLE DATABASE XEPDB1;
  RECOVER PLUGGABLE DATABASE XEPDB1;

  # Abrimos con RESETLOGS para consolidar el viaje al pasado
  ALTER PLUGGABLE DATABASE XEPDB1 OPEN RESETLOGS;
}
