from math import radians, cos, sin, sqrt, atan2
import numpy as np

RADIO_TIERRA = 6371  #radio en kilometros es importante para calcular bien con polyline

def distancia_km(p1, p2):
    lat1, lon1 = p1
    lat2, lon2 = p2

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return RADIO_TIERRA * c


def calcular_costo_peajes(polyline, peajes, radio=0.3):
    
    total = 0
    peajes_usados = []

    for punto in polyline:
        lat_ruta, lon_ruta = punto[1], punto[0]

        for p in peajes:
            if p.id in peajes_usados:
                continue

            d = distancia_km(
                (lat_ruta, lon_ruta),
                (float(p.latitud), float(p.longitud))
            )

            if d <= radio:
                total += float(p.categoriai)
                peajes_usados.append(p.id)

    return total



def filtrar_peajes_en_ruta(polyline, peajes, radio_metros=500):
    if not polyline or not peajes:
        return []

    # Convertir polyline a array numpy — formato [lon, lat]
    puntos = np.array(polyline, dtype=float)  # shape (N, 2)
    lats = puntos[:, 1]
    lons = puntos[:, 0]

    # 1 grado ≈ 111km en Colombia
    radio_grados = radio_metros / 111_000

    peajes_en_ruta = []

    for peaje in peajes:
        plat = float(peaje.latitud)
        plon = float(peaje.longitud)

        # Bounding box — descarta el 95%+ de peajes sin calcular distancia
        if not (
            np.any(np.abs(lats - plat) <= radio_grados) and
            np.any(np.abs(lons - plon) <= radio_grados)
        ):
            continue

        # Distancia euclidiana vectorizada contra todos los puntos
        dlat = lats - plat
        dlon = (lons - plon) * np.cos(np.radians(plat))  # corregir longitud
        distancias = np.sqrt(dlat**2 + dlon**2)

        if np.min(distancias) <= radio_grados:
            peajes_en_ruta.append(peaje)

    return peajes_en_ruta

def calcular_costo_acpm(distancia_km, rendimiento_km_l=3.5, precio_litro=9500):
    litros = distancia_km / rendimiento_km_l
    return litros * precio_litro


def costos_generales_envio(envio):
    """
    Calcula los costos adicionales del envío:
    - Carga y descarga
    - Escolta
    - Viáticos
    """
    return {
        "valor_carga": float(envio.valor_carga or 0),
        "valor_descarga": float(envio.valor_descarga or 0),
        "escolta": float(envio.escolta or 0),
        "viaticos": float(envio.viaticos or 0),
        "total": float(
            (envio.valor_carga or 0) +
            (envio.valor_descarga or 0) +
            (envio.escolta or 0) +
            (envio.viaticos or 0)
        )
    }