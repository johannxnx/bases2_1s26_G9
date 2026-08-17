#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script para diagnosticar el matching de jugadores."""

import os
import csv as _csv

DATA_DIR = "data"

def _leer(nombre, carpeta=DATA_DIR):
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(_csv.DictReader(f))

def _match_jugador(nombre, jugador_idx_exacto, jugador_idx_invertido):
    """
    Busca el id_jugador dado un nombre.
    Soporta múltiples formatos:
      - "Nombre Apellido" (HTML)
      - "Apellido, Nombre" (CSV con coma)
    """
    if not nombre:
        return None
    
    n = nombre.strip().lower()
    
    # 1. Buscar directo (ya en el índice exacto)
    if n in jugador_idx_exacto:
        return jugador_idx_exacto[n]
    if n in jugador_idx_invertido:
        return jugador_idx_invertido[n]
    
    # 2. Si tiene coma, es formato "Apellido, Nombre" - convertir a "Nombre Apellido"
    if "," in n:
        partes = [p.strip() for p in n.split(",", 1)]
        invertido = f"{partes[1]} {partes[0]}".lower()
        if invertido in jugador_idx_exacto:
            return jugador_idx_exacto[invertido]
        if invertido in jugador_idx_invertido:
            return jugador_idx_invertido[invertido]
    
    # 3. Si NO tiene coma pero tiene espacios, es "Nombre Apellido" - intentar invertir a "Apellido Nombre"
    if " " in n and "," not in n:
        partes = n.rsplit(" ", 1)  # Últimas 2 palabras
        if len(partes) == 2:
            invertido = f"{partes[1]}, {partes[0]}".lower()
            if invertido in jugador_idx_exacto:
                return jugador_idx_exacto[invertido]
            if invertido in jugador_idx_invertido:
                return jugador_idx_invertido[invertido]
    
    return None


# Construir índices
_jug_exacto    = {}
_jug_invertido = {}
for _i, _r in enumerate(_leer("jugadores_pais"), 1):
    _nom = (_r.get("nombre") or _r.get("NOMBRE","")).strip()
    _id  = int(_r.get("id_jugador") or _r.get("ID JUGADOR") or _i)
    
    if not _nom:
        continue
    
    _nom_lower = _nom.lower()
    
    # Índice 1: Nombre EXACTO como está en el CSV
    _jug_exacto[_nom_lower] = _id
    
    # Índice 2: Si tiene coma, guardar también sin comas y parseado
    if "," in _nom_lower:
        _partes = _nom_lower.split(",", 1)
        _apellido = _partes[0].strip()
        _nombre = _partes[1].strip()
        
        # Guardar como "Apellido Nombre" (sin coma)
        _sin_coma = f"{_apellido} {_nombre}"
        _jug_invertido[_sin_coma] = _id
        
        # Guardar como "Nombre Apellido" (invertido)
        _invertido = f"{_nombre} {_apellido}"
        _jug_invertido[_invertido] = _id

# Test con "Enner Valencia"
test_nombre = "Enner Valencia"
print(f"Buscando: '{test_nombre}'")
print(f"ID encontrado: {_match_jugador(test_nombre, _jug_exacto, _jug_invertido)}")
print()

# Debug: Mostrar lo que hay en los índices para Valencia
print("Contenido de índices para Valencia/Enner:")
for key in _jug_exacto:
    if "valencia" in key or "enner" in key:
        print(f"  Exacto: '{key}' → {_jug_exacto[key]}")
for key in _jug_invertido:
    if "valencia" in key or "enner" in key:
        print(f"  Invertido: '{key}' → {_jug_invertido[key]}")
