"""
Módulo: Fletes — Cálculo de Costos y Peajes
Responsabilidad: Toda la matemática financiera del viaje.

Variables clave:
    - PRECIO_DIESEL:    precio por litro del diésel en Colombia (COP)
    - CONSUMO_POR_KM:   litros consumidos por kilómetro
    - UMBRAL_PEAJE_GR:  radio de detección de peajes en grados (~500m)
"""
import math
import os
from models.database import Peaje

# ─── Constantes de costos ─────────────────────────────────────────────────────
PRECIO_DIESEL = float(os.getenv('DIESEL_PRICE', 10885))   # COP por litro
CONSUMO_POR_KM = 0.35                                      # litros/km
UMBRAL_PEAJE_GR = 0.0045                                   # ~500 metros en grados
# ─────────────────────────────────────────────────────────────────────────────


def calcular_costo_combustible(dist_total_km: float) -> float:
    """Calcula el costo de combustible para la distancia total (vacío + cargado)."""
    return dist_total_km * CONSUMO_POR_KM * PRECIO_DIESEL


def detectar_peajes_en_ruta(puntos: list) -> tuple:
    """
    Detecta peajes a lo largo de una ruta usando geofencing.

    Args:
        puntos: lista de [lon, lat] del trayecto de GraphHopper

    Returns:
        (lista_peajes, costo_total)
    """
    if not puntos:
        return [], 0

    lats = [p[1] for p in puntos]
    lons = [p[0] for p in puntos]
    min_lat, max_lat = min(lats) - 0.01, max(lats) + 0.01
    min_lon, max_lon = min(lons) - 0.01, max(lons) + 0.01

    candidatos = Peaje.query.filter(
        Peaje.latitud.between(min_lat, max_lat),
        Peaje.longitud.between(min_lon, max_lon)
    ).all()

    peajes_en_ruta = []
    costo_total = 0

    for peaje in candidatos:
        p_lat = float(peaje.latitud)
        p_lon = float(peaje.longitud)
        cerca = any(
            math.sqrt((p_lat - pt[1])**2 + (p_lon - pt[0])**2) < UMBRAL_PEAJE_GR
            for pt in puntos
        )
        if cerca:
            peajes_en_ruta.append({
                "nombre": peaje.nombrepeaje,
                "costo": int(peaje.categoriaiv or 0),
                "lat": p_lat,
                "lon": p_lon
            })
            costo_total += int(peaje.categoriaiv or 0)

    return peajes_en_ruta, costo_total


def calcular_costos_fijos(flete) -> dict:
    """
    Extrae y suma los costos fijos de un flete (cargue, descargue, escolta, viáticos).
    """
    val_cargue = float(flete.valor_cargue or 0)
    val_descargue = float(flete.valor_descargue or 0)
    val_escolta = float(flete.valor_escolta or 0)
    val_viaticos = float(flete.viaticos_estimados or 0)
    val_poliza = float(flete.valor_poliza or 0)
    return {
        "valor_cargue": val_cargue,
        "valor_descargue": val_descargue,
        "valor_escolta": val_escolta,
        "viaticos_estimados": val_viaticos,
        "valor_poliza": val_poliza,
        "total": val_cargue + val_descargue + val_escolta + val_viaticos + val_poliza
    }
