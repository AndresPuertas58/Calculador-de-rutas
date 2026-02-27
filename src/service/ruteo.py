import requests
from models.ruta_envio import RutaEnvio
from models.envio import Envio
import json

GRAPHOPPER_URL = "http://localhost:8989/route"

def obtener_ruta(origen, destino):
    lat1, lon1 = float(origen[0]), float(origen[1])
    lat2, lon2 = float(destino[0]), float(destino[1])

    params = {
        "point": [
            f"{lat1},{lon1}",
            f"{lat2},{lon2}"
        ],
        "profile": "car",
        "points_encoded": "false"
    }

    response = requests.get(GRAPHOPPER_URL, params=params)
    data = response.json()

    # 🔥 DEBUG REAL (esto es lo que NECESITO VER)
    print("GRAPHOPPER RESPONSE:", data)

    if "paths" not in data or not data["paths"]:
        raise Exception(f"GraphHopper no devolvió ruta: {data}")

    path = data["paths"][0]

    return {
        "distancia_km": path["distance"] / 1000,
        "tiempo_seg": path["time"] / 1000,
        "polyline": path["points"]["coordinates"]
    }

def guardar_ruta_envio(
    db,
    envio_id,
    camion_id,
    ruta,
    costo_acpm,
    costo_peajes,
    tipo_opcion="optima",   
    asignada=False          
):
    ruta_db = RutaEnvio(
        envio_id=envio_id,
        camion_id=camion_id,
        polyline=json.dumps(ruta["polyline"]),
        distancia_km=ruta["distancia_km"],
        tiempo_seg=ruta["tiempo_seg"],
        costo_acpm=costo_acpm,
        costo_peajes=costo_peajes,
        costo_total=costo_acpm + costo_peajes,
        tipo_opcion=tipo_opcion,  
        asignada=asignada         
    )

    db.add(ruta_db)
    db.commit()
    db.refresh(ruta_db)

    return ruta_db