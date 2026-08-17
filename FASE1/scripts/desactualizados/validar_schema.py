#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para validar que los archivos CSV coinciden con el esquema SQL.
"""

import csv
import os
from collections import defaultdict

CSV_DIR = "data/normalizado"

# Columnas esperadas según el script SQL documentado
SQL_SCHEMA = {
    "seleccion": ["ID_SELECCION", "NOMBRE"],
    "jugador_pais": ["ID_JUGADOR", "NOMBRE", "ID_SELECCION", "SELECCION"],
    "mundial": ["ID_MUNDIAL", "ANIO", "ID_ORGANIZADOR", "ORGANIZADOR", 
                "ID_CAMPEON", "CAMPEON", "NUM_SELECCIONES", "NUM_PARTIDOS", 
                "GOLES", "PROMEDIO_GOL"],
    "grupo": ["ID_GRUPO", "ANIO", "NOMBRE"],  # En el SQL falta SELECCIONES
    "partido": ["ID_PARTIDO", "ANIO", "NUM_PARTIDO", "FECHA", "ETAPA",
                "ID_LOCAL", "LOCAL", "ID_VISITANTE", "VISITANTE",
                "GOLES_LOCAL", "GOLES_VISITANTE", "TIEMPO_EXTRA", "PENALES",
                "PENALES_LOCAL", "PENALES_VISITANTE"],
    "posicion_grupo": ["ID_POSICION_GRUPO", "ID_GRUPO", "ANIO", "GRUPO",
                       "ID_SELECCION", "PAIS", "PTS", "PJ", "PG", "PE", "PP",
                       "GF", "GC", "DIFERENCIA", "CLASIFICADO"],
    "gol": ["ID_GOL", "ID_PARTIDO", "ANIO", "NUM_PARTIDO", "ID_SELECCION",
            "EQUIPO", "ID_JUGADOR", "JUGADOR", "MINUTO", "ES_PENAL"],
    "goleador": ["ID_GOLEADOR", "ANIO", "ID_SELECCION", "PAIS",
                 "ID_JUGADOR", "JUGADOR", "GOLES", "PARTIDOS", "PROMEDIO"],
    "posicion_final": ["ID_POSICION_FINAL", "ANIO", "POSICION", 
                       "ID_SELECCION", "PAIS"],
    "premio": ["ID_PREMIO", "ANIO", "TIPO_PREMIO", "ID_JUGADOR",
               "JUGADOR", "ID_SELECCION", "PAIS"],
    "equipo_ideal": ["ID_EQUIPO_IDEAL", "ANIO", "POSICION", "ID_JUGADOR",
                     "JUGADOR", "ID_SELECCION", "PAIS"],
    "tarjeta": ["ID_TARJETA", "ANIO", "ID_SELECCION", "PAIS", "ID_JUGADOR",
                "JUGADOR", "AMARILLAS", "ROJAS"],
}

def get_csv_columns(filename):
    """Lee los encabezados del CSV."""
    filepath = os.path.join(CSV_DIR, f"{filename}.csv")
    if not os.path.exists(filepath):
        return None, f"No existe {filepath}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), None

def normalize_col(col):
    """Normaliza nombres de columnas para comparación."""
    return col.lower().strip()

def compare_schemas():
    """Compara esquemas SQL con CSVs generados."""
    print("=" * 70)
    print("VALIDACIÓN DE ESQUEMA: SQL vs CSV")
    print("=" * 70)
    print()
    
    issues = []
    all_ok = True
    
    for table_name, expected_cols in SQL_SCHEMA.items():
        csv_cols, error = get_csv_columns(table_name)
        
        if error:
            print(f"[ERROR] {table_name.upper()}")
            print(f"   Error: {error}")
            all_ok = False
            issues.append((table_name, "No existe archivo"))
            print()
            continue
        
        # Normalizar para comparación
        expected_norm = [normalize_col(c) for c in expected_cols]
        csv_norm = [normalize_col(c) for c in csv_cols]
        
        # Buscar diferencias
        missing = set(expected_norm) - set(csv_norm)
        extra = set(csv_norm) - set(expected_norm)
        
        if not missing and not extra:
            print(f"[OK] {table_name.upper()}")
            print(f"   Columnas: {len(csv_cols)} (coinciden con SQL)")
        else:
            print(f"[WARNING] {table_name.upper()}")
            all_ok = False
            
            if missing:
                print(f"   Columnas faltantes en CSV: {missing}")
                issues.append((table_name, f"Faltan: {missing}"))
            if extra:
                print(f"   Columnas extras en CSV: {extra}")
                issues.append((table_name, f"Extra: {extra}"))
        
        print(f"   SQL:     {expected_cols}")
        print(f"   CSV:     {csv_cols}")
        print()
    
    # Resumen
    print("=" * 70)
    if all_ok:
        print("[OK] TODOS LOS ESQUEMAS COINCIDEN")
    else:
        print(f"[WARNING] ENCONTRADOS {len(issues)} PROBLEMAS")
        print()
        for table, issue in issues:
            print(f"  - {table}: {issue}")
    
    print("=" * 70)
    return all_ok

if __name__ == "__main__":
    compare_schemas()
